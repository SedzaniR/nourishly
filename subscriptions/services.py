from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from typing import Optional, Dict, Any, List
from decimal import Decimal

from .selectors import PlanSelector, SubscriptionSelector, FeatureSelector
from .models import Plan, Subscription, Payment
from core.logger import log_info


class SubscriptionService:
    """Service class for subscription-related business logic."""
    
    @staticmethod
    def create_subscription(user, plan: Plan, external_customer_id: Optional[str] = None) -> Subscription:
        """
        Create a new subscription for a user.
        
        Args:
            user: User instance
            plan: Plan instance
            external_customer_id: Optional external payment provider customer ID
            
        Returns:
            Created Subscription instance
        """
        with transaction.atomic():
            # Check if user already has an active subscription
            if SubscriptionSelector.check_user_has_active_subscription(user):
                raise ValueError("User already has an active subscription")
            
            # Calculate dates
            now = timezone.now()
            start_date = now
            
            # Set trial end if plan has trial days
            trial_end = None
            if plan.trial_days > 0:
                trial_end = now + timedelta(days=plan.trial_days)
                status = 'trialing'
            else:
                status = 'active'
            
            # Calculate billing period
            period_end = SubscriptionService._calculate_period_end(now, plan.billing_cycle)
            
            # Create subscription
            subscription = Subscription.objects.create(
                user=user,
                plan=plan,
                status=status,
                start_date=start_date,
                trial_end=trial_end,
                current_period_start=start_date,
                current_period_end=period_end,
                external_customer_id=external_customer_id
            )
            
            log_info(
                "Subscription created via service",
                user_id=user.id,
                username=user.username,
                subscription_id=subscription.pk,
                plan_name=plan.name,
                status=status
            )
            
            return subscription
    
    @staticmethod
    def cancel_subscription(subscription: Subscription, at_period_end: bool = True) -> Subscription:
        """
        Cancel a subscription.
        
        Args:
            subscription: Subscription instance to cancel
            at_period_end: Whether to cancel at period end or immediately
            
        Returns:
            Updated Subscription instance
        """
        with transaction.atomic():
            if subscription.status in ['canceled', 'unpaid']:
                raise ValueError("Subscription is already canceled or unpaid")
            
            if at_period_end:
                subscription.cancel_at_period_end = True
                subscription.status = 'active'  # Keep active until period ends
            else:
                subscription.status = 'canceled'
                subscription.canceled_at = timezone.now()
                subscription.end_date = timezone.now()
            
            subscription.save()
            
            log_info(
                "Subscription canceled via service",
                user_id=subscription.user.id,
                username=subscription.user.username,
                subscription_id=subscription.pk,
                at_period_end=at_period_end
            )
            
            return subscription
    
    @staticmethod
    def get_user_subscription_status(user) -> Dict[str, Any]:
        """
        Get comprehensive subscription status for a user.
        
        Args:
            user: User instance
            
        Returns:
            Dictionary with subscription status information
        """
        current_subscription = SubscriptionSelector.get_user_active_subscription(user)
        available_plans = PlanSelector.get_active_plans()
        
        return {
            "has_active_subscription": current_subscription is not None,
            "current_subscription": current_subscription,
            "available_plans": available_plans
        }
    
    @staticmethod
    def check_feature_access(user, feature_slug: str) -> bool:
        """
        Check if a user has access to a specific feature.
        
        Args:
            user: User instance
            feature_slug: Feature slug to check
            
        Returns:
            True if user has access, False otherwise
        """
        # Get user's active subscription
        subscription = SubscriptionSelector.get_user_active_subscription(user)
        
        if not subscription:
            return False
        
        # Check if feature is enabled in the plan
        plan_feature = FeatureSelector.get_plan_feature(subscription.plan.id, feature_slug)
        
        if not plan_feature:
            return False
        
        # Check feature value based on type
        feature = plan_feature.feature
        value = plan_feature.value
        
        if feature.feature_type == 'boolean':
            return value.get('enabled', False)
        elif feature.feature_type == 'numeric':
            # For numeric features, we'd need to check current usage
            # This is a simplified version
            return True
        elif feature.feature_type == 'unlimited':
            return True
        
        return False
    
    @staticmethod
    def get_user_limits(user) -> Dict[str, Any]:
        """
        Get current usage limits for a user based on their subscription.
        
        Args:
            user: User instance
            
        Returns:
            Dictionary with current limits
        """
        subscription = SubscriptionSelector.get_user_active_subscription(user)
        
        if not subscription:
            return {
                "max_recipes": 0,
                "max_meal_plans": 0,
                "ai_meal_planning": False,
                "nutrition_analytics": False,
                "priority_support": False,
                "custom_goals": False
            }
        
        plan = subscription.plan
        
        return {
            "max_recipes": plan.max_recipes,
            "max_meal_plans": plan.max_meal_plans,
            "ai_meal_planning": plan.ai_meal_planning,
            "nutrition_analytics": plan.nutrition_analytics,
            "priority_support": plan.priority_support,
            "custom_goals": plan.custom_goals
        }
    
    @staticmethod
    def _calculate_period_end(start_date, billing_cycle: str):
        """Calculate the end of the billing period."""
        if billing_cycle == 'monthly':
            return start_date + timedelta(days=30)
        elif billing_cycle == 'quarterly':
            return start_date + timedelta(days=90)
        else:  # yearly
            return start_date + timedelta(days=365)


class PaymentService:
    """Service class for payment-related business logic."""
    
    @staticmethod
    def create_payment(
        subscription: Subscription,
        amount: Decimal,
        currency: str = 'USD',
        external_payment_id: Optional[str] = None,
        external_invoice_id: Optional[str] = None,
        description: str = ""
    ) -> Payment:
        """
        Create a new payment record.
        
        Args:
            subscription: Subscription instance
            amount: Payment amount
            currency: Payment currency
            external_payment_id: Optional external payment provider payment ID
            external_invoice_id: Optional external payment provider invoice ID
            description: Payment description
            
        Returns:
            Created Payment instance
        """
        payment = Payment.objects.create(
            subscription=subscription,
            amount=amount,
            currency=currency,
            external_payment_id=external_payment_id,
            external_invoice_id=external_invoice_id,
            description=description
        )
        
        log_info(
            "Payment created via service",
            user_id=subscription.user.id,
            username=subscription.user.username,
            payment_id=payment.pk,
            amount=amount,
            currency=currency
        )
        
        return payment
    
    @staticmethod
    def mark_payment_succeeded(payment: Payment, paid_at=None) -> Payment:
        """
        Mark a payment as succeeded.
        
        Args:
            payment: Payment instance
            paid_at: When payment was completed (defaults to now)
            
        Returns:
            Updated Payment instance
        """
        payment.status = 'succeeded'
        payment.paid_at = paid_at or timezone.now()
        payment.save()
        
        log_info(
            "Payment marked as succeeded",
            user_id=payment.subscription.user.id,
            username=payment.subscription.user.username,
            payment_id=payment.pk,
            amount=payment.amount
        )
        
        return payment
    
    @staticmethod
    def mark_payment_failed(payment: Payment) -> Payment:
        """
        Mark a payment as failed.
        
        Args:
            payment: Payment instance
            
        Returns:
            Updated Payment instance
        """
        payment.status = 'failed'
        payment.save()
        
        log_info(
            "Payment marked as failed",
            user_id=payment.subscription.user.id,
            username=payment.subscription.user.username,
            payment_id=payment.pk,
            amount=payment.amount
        )
        
        return payment


class PlanService:
    """Service class for plan-related business logic."""
    
    @staticmethod
    def get_active_plans():
        """Get all active subscription plans."""
        return PlanSelector.get_active_plans()
    
    @staticmethod
    def get_popular_plans():
        """Get popular/recommended plans."""
        return PlanSelector.get_popular_plans()
    
    @staticmethod
    def calculate_yearly_savings(plan: Plan) -> Optional[Decimal]:
        """
        Calculate yearly savings compared to monthly billing.
        
        Args:
            plan: Plan instance
            
        Returns:
            Yearly savings amount or None if not applicable
        """
        if plan.billing_cycle == 'monthly':
            return None
        
        monthly_equivalent = plan.monthly_equivalent_price
        yearly_cost = plan.yearly_price
        monthly_yearly_cost = monthly_equivalent * 12
        
        savings = monthly_yearly_cost - yearly_cost
        
        return savings if savings > 0 else None
    
    @staticmethod
    def get_plan_features(plan: Plan) -> List[Dict[str, Any]]:
        """
        Get all features for a plan.
        
        Args:
            plan: Plan instance
            
        Returns:
            List of feature dictionaries
        """
        plan_features = FeatureSelector.get_plan_features(plan.pk)
        
        features = []
        for plan_feature in plan_features:
            features.append({
                "name": plan_feature.feature.name,
                "slug": plan_feature.feature.slug,
                "description": plan_feature.feature.description,
                "category": plan_feature.feature.category,
                "feature_type": plan_feature.feature.feature_type,
                "value": plan_feature.value
            })
        
        return features 