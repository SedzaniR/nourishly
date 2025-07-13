from django.db.models import Prefetch, Count, Sum
from typing import Optional, List
from datetime import datetime

from .models import Plan, Subscription, Payment, SubscriptionFeature, PlanFeature


class PlanSelector:
    """Database queries for Plan model."""
    
    @staticmethod
    def get_active_plans():
        """Get all active subscription plans.
        
        Returns:
            QuerySet: All active plans ordered by price.
        """
        return Plan.objects.filter(is_active=True).order_by('price')
    
    @staticmethod
    def get_popular_plans():
        """Get popular/recommended plans.
        
        Returns:
            QuerySet: All active and popular plans ordered by price.
        """
        return Plan.objects.filter(is_active=True, is_popular=True).order_by('price')
    
    @staticmethod
    def get_plan_by_id(plan_id: int) -> Optional[Plan]:
        """Get a plan by ID.
        
        Args:
            plan_id: The ID of the plan to retrieve.
            
        Returns:
            Plan or None: The plan if found and active, None otherwise.
        """
        return Plan.objects.filter(id=plan_id, is_active=True).first()
    
    @staticmethod
    def get_plan_by_slug(slug: str) -> Optional[Plan]:
        """Get a plan by slug.
        
        Args:
            slug: The slug of the plan to retrieve.
            
        Returns:
            Plan or None: The plan if found and active, None otherwise.
        """
        return Plan.objects.filter(slug=slug, is_active=True).first()
    
    @staticmethod
    def get_plan_with_features(plan_id: int) -> Optional[Plan]:
        """Get a plan with its features prefetched.
        
        Args:
            plan_id: The ID of the plan to retrieve.
            
        Returns:
            Plan or None: The plan with prefetched features if found and active, None otherwise.
        """
        return Plan.objects.filter(
            id=plan_id, 
            is_active=True
        ).prefetch_related(
            Prefetch(
                'plan_features',
                queryset=PlanFeature.objects.select_related('feature')
            )
        ).first()


class SubscriptionSelector:
    """Database queries for Subscription model."""
    
    @staticmethod
    def get_user_subscriptions(user):
        """Get all subscriptions for a user.
        
        Args:
            user: The user whose subscriptions to retrieve.
            
        Returns:
            QuerySet: All subscriptions for the user ordered by creation date (newest first).
        """
        return Subscription.objects.filter(
            user=user
        ).select_related('plan').order_by('-created_at')
    
    @staticmethod
    def get_user_active_subscription(user) -> Optional[Subscription]:
        """Get the current active subscription for a user.
        
        Args:
            user: The user whose active subscription to retrieve.
            
        Returns:
            Subscription or None: The active subscription if found, None otherwise.
        """
        return Subscription.objects.filter(
            user=user,
            status__in=['active', 'trialing']
        ).select_related('plan').first()
    
    @staticmethod
    def get_subscription_by_id(subscription_id: int, user=None) -> Optional[Subscription]:
        """Get a subscription by ID, optionally filtered by user.
        
        Args:
            subscription_id: The ID of the subscription to retrieve.
            user: Optional user to filter by. If provided, only returns subscription if owned by this user.
            
        Returns:
            Subscription or None: The subscription if found, None otherwise.
        """
        queryset = Subscription.objects.select_related('plan', 'user')
        if user:
            queryset = queryset.filter(user=user)
        return queryset.filter(id=subscription_id).first()
    
    @staticmethod
    def get_subscription_by_external_id(external_id: str) -> Optional[Subscription]:
        """Get a subscription by external payment provider ID.
        
        Args:
            external_id: The external payment provider subscription ID.
            
        Returns:
            Subscription or None: The subscription if found, None otherwise.
        """
        return Subscription.objects.filter(
            external_subscription_id=external_id
        ).select_related('plan', 'user').first()
    
    @staticmethod
    def get_active_subscriptions():
        """Get all active subscriptions across all users.
        
        Returns:
            QuerySet: All active and trialing subscriptions with related data.
        """
        return Subscription.objects.filter(
            status__in=['active', 'trialing']
        ).select_related('plan', 'user')
    
    @staticmethod
    def get_subscriptions_by_plan(plan_id: int):
        """Get all subscriptions for a specific plan.
        
        Args:
            plan_id: The ID of the plan.
            
        Returns:
            QuerySet: All subscriptions for the specified plan with related data.
        """
        return Subscription.objects.filter(
            plan_id=plan_id
        ).select_related('plan', 'user')
    
    @staticmethod
    def get_expiring_subscriptions(days: int = 7):
        """Get subscriptions expiring within the specified days.
        
        Args:
            days: Number of days to look ahead for expiring subscriptions (default: 7).
            
        Returns:
            QuerySet: Subscriptions expiring within the specified days.
        """
        from django.utils import timezone
        from datetime import timedelta
        
        expiry_date = timezone.now() + timedelta(days=days)
        return Subscription.objects.filter(
            status__in=['active', 'trialing'],
            current_period_end__lte=expiry_date
        ).select_related('plan', 'user')
    
    @staticmethod
    def get_trial_subscriptions():
        """Get all subscriptions currently in trial period.
        
        Returns:
            QuerySet: All trialing subscriptions that haven't ended yet.
        """
        from django.utils import timezone
        
        return Subscription.objects.filter(
            status='trialing',
            trial_end__gt=timezone.now()
        ).select_related('plan', 'user')
    
    @staticmethod
    def get_canceled_subscriptions():
        """Get all canceled subscriptions.
        
        Returns:
            QuerySet: All canceled subscriptions with related data.
        """
        return Subscription.objects.filter(
            status='canceled'
        ).select_related('plan', 'user')
    
    @staticmethod
    def get_past_due_subscriptions():
        """Get all past due subscriptions.
        
        Returns:
            QuerySet: All past due subscriptions with related data.
        """
        return Subscription.objects.filter(
            status='past_due'
        ).select_related('plan', 'user')
    
    @staticmethod
    def check_user_has_active_subscription(user) -> bool:
        """Check if user has an active subscription.
        
        Args:
            user: The user to check.
            
        Returns:
            bool: True if user has an active subscription, False otherwise.
        """
        return Subscription.objects.filter(
            user=user,
            status__in=['active', 'trialing']
        ).exists()
    
    @staticmethod
    def get_user_subscription_by_plan(user, plan_id: int) -> Optional[Subscription]:
        """Get user's subscription for a specific plan.
        
        Args:
            user: The user whose subscription to retrieve.
            plan_id: The ID of the plan.
            
        Returns:
            Subscription or None: The subscription if found, None otherwise.
        """
        return Subscription.objects.filter(
            user=user,
            plan_id=plan_id
        ).select_related('plan').first()


class PaymentSelector:
    """Database queries for Payment model."""
    
    @staticmethod
    def get_user_payments(user):
        """Get all payments for a user.
        
        Args:
            user: The user whose payments to retrieve.
            
        Returns:
            QuerySet: All payments for the user ordered by creation date (newest first).
        """
        return Payment.objects.filter(
            subscription__user=user
        ).select_related('subscription__plan').order_by('-created_at')
    
    @staticmethod
    def get_subscription_payments(subscription_id: int):
        """Get all payments for a specific subscription.
        
        Args:
            subscription_id: The ID of the subscription.
            
        Returns:
            QuerySet: All payments for the specified subscription ordered by creation date.
        """
        return Payment.objects.filter(
            subscription_id=subscription_id
        ).select_related('subscription__plan').order_by('-created_at')
    
    @staticmethod
    def get_payment_by_id(payment_id: int) -> Optional[Payment]:
        """Get a payment by ID.
        
        Args:
            payment_id: The ID of the payment to retrieve.
            
        Returns:
            Payment or None: The payment if found, None otherwise.
        """
        return Payment.objects.filter(
            id=payment_id
        ).select_related('subscription__plan', 'subscription__user').first()
    
    @staticmethod
    def get_payment_by_external_id(external_id: str) -> Optional[Payment]:
        """Get a payment by external payment provider ID.
        
        Args:
            external_id: The external payment provider payment ID.
            
        Returns:
            Payment or None: The payment if found, None otherwise.
        """
        return Payment.objects.filter(
            external_payment_id=external_id
        ).select_related('subscription__plan', 'subscription__user').first()
    
    @staticmethod
    def get_successful_payments():
        """Get all successful payments.
        
        Returns:
            QuerySet: All successful payments with related data.
        """
        return Payment.objects.filter(
            status='succeeded'
        ).select_related('subscription__plan', 'subscription__user')
    
    @staticmethod
    def get_failed_payments():
        """Get all failed payments.
        
        Returns:
            QuerySet: All failed payments with related data.
        """
        return Payment.objects.filter(
            status='failed'
        ).select_related('subscription__plan', 'subscription__user')
    
    @staticmethod
    def get_payments_by_date_range(start_date: datetime, end_date: datetime):
        """Get payments within a date range.
        
        Args:
            start_date: Start of the date range.
            end_date: End of the date range.
            
        Returns:
            QuerySet: All payments created within the specified date range.
        """
        return Payment.objects.filter(
            created_at__range=(start_date, end_date)
        ).select_related('subscription__plan', 'subscription__user')


class FeatureSelector:
    """Database queries for SubscriptionFeature and PlanFeature models."""
    
    @staticmethod
    def get_all_features():
        """Get all subscription features.
        
        Returns:
            QuerySet: All features ordered by category and name.
        """
        return SubscriptionFeature.objects.all().order_by('category', 'name')
    
    @staticmethod
    def get_features_by_category(category: str):
        """Get features by category.
        
        Args:
            category: The category of features to retrieve.
            
        Returns:
            QuerySet: All features in the specified category ordered by name.
        """
        return SubscriptionFeature.objects.filter(
            category=category
        ).order_by('name')
    
    @staticmethod
    def get_feature_by_slug(slug: str) -> Optional[SubscriptionFeature]:
        """Get a feature by slug.
        
        Args:
            slug: The slug of the feature to retrieve.
            
        Returns:
            SubscriptionFeature or None: The feature if found, None otherwise.
        """
        return SubscriptionFeature.objects.filter(slug=slug).first()
    
    @staticmethod
    def get_plan_features(plan_id: int):
        """Get all features for a specific plan.
        
        Args:
            plan_id: The ID of the plan.
            
        Returns:
            QuerySet: All features for the specified plan with related feature data.
        """
        return PlanFeature.objects.filter(
            plan_id=plan_id
        ).select_related('feature').order_by('feature__category', 'feature__name')
    
    @staticmethod
    def get_plan_feature(plan_id: int, feature_slug: str) -> Optional[PlanFeature]:
        """Get a specific feature for a plan.
        
        Args:
            plan_id: The ID of the plan.
            feature_slug: The slug of the feature.
            
        Returns:
            PlanFeature or None: The plan feature if found, None otherwise.
        """
        return PlanFeature.objects.filter(
            plan_id=plan_id,
            feature__slug=feature_slug
        ).select_related('feature').first()


class SubscriptionAnalyticsSelector:
    """Database queries for subscription analytics and reporting."""
    
    @staticmethod
    def get_subscription_count_by_plan() -> dict:
        """Get subscription count grouped by plan.
        
        Returns:
            dict: Dictionary mapping plan names to subscription counts.
        """
        return dict(
            Subscription.objects.filter(
                status__in=['active', 'trialing']
            ).values('plan__name').annotate(
                count=Count('id')
            ).values_list('plan__name', 'count')
        )
    
    @staticmethod
    def get_revenue_by_period(start_date: datetime, end_date: datetime) -> dict:
        """Get revenue data for a specific period.
        
        Args:
            start_date: Start of the period.
            end_date: End of the period.
            
        Returns:
            dict: Dictionary containing total_revenue and payment_count.
        """
        return Payment.objects.filter(
            status='succeeded',
            created_at__range=(start_date, end_date)
        ).aggregate(
            total_revenue=Sum('amount'),
            payment_count=Count('id')
        )
    
    @staticmethod
    def get_user_subscription_stats(user) -> dict:
        """Get subscription statistics for a user.
        
        Args:
            user: The user whose statistics to retrieve.
            
        Returns:
            dict: Dictionary containing subscription and payment statistics.
        """
        subscriptions = Subscription.objects.filter(user=user)
        
        return {
            'total_subscriptions': subscriptions.count(),
            'active_subscriptions': subscriptions.filter(
                status__in=['active', 'trialing']
            ).count(),
            'canceled_subscriptions': subscriptions.filter(
                status='canceled'
            ).count(),
            'total_payments': Payment.objects.filter(
                subscription__user=user,
                status='succeeded'
            ).count(),
            'total_spent': Payment.objects.filter(
                subscription__user=user,
                status='succeeded'
            ).aggregate(total=Sum('amount'))['total'] or 0
        }
    
    @staticmethod
    def get_plan_popularity_stats() -> List[dict]:
        """Get popularity statistics for all plans.
        
        Returns:
            List[dict]: List of dictionaries containing plan popularity data.
        """
        return list(
            Plan.objects.filter(is_active=True).annotate(
                subscription_count=Count('subscriptions'),
                avg_subscription_duration=Count('subscriptions__current_period_end')
            ).values(
                'name', 'price', 'subscription_count'
            ).order_by('-subscription_count')
        ) 