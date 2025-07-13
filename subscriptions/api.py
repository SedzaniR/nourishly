from ninja import Router, Schema
from ninja.errors import HttpError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from typing import List, Optional
from datetime import datetime, timedelta

from .models import Plan, Subscription
from .selectors import PlanSelector, SubscriptionSelector, PaymentSelector, FeatureSelector
from core.logger import log_info, log_error

router = Router()


# Schema definitions
class PlanSchema(Schema):
    id: int
    name: str
    slug: str
    description: str
    price: float
    currency: str
    billing_cycle: str
    max_recipes: Optional[int]
    max_meal_plans: Optional[int]
    ai_meal_planning: bool
    nutrition_analytics: bool
    priority_support: bool
    custom_goals: bool
    is_popular: bool
    trial_days: int
    yearly_price: float
    monthly_equivalent_price: float


class SubscriptionSchema(Schema):
    id: int
    plan: PlanSchema
    status: str
    start_date: datetime
    end_date: Optional[datetime]
    trial_end: Optional[datetime]
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    is_active: bool
    is_trialing: bool
    days_remaining: int


class PaymentSchema(Schema):
    id: int
    amount: float
    currency: str
    status: str
    paid_at: Optional[datetime]
    description: str


class CreateSubscriptionSchema(Schema):
    plan_id: int
    payment_method_id: Optional[str] = None


class CancelSubscriptionSchema(Schema):
    at_period_end: bool = True


class SubscriptionStatusSchema(Schema):
    has_active_subscription: bool
    current_subscription: Optional[SubscriptionSchema]
    available_plans: List[PlanSchema]


# API Endpoints
@router.get("/plans", response=List[PlanSchema])
def list_plans(request):
    """Get all active subscription plans."""
    try:
        plans = PlanSelector.get_active_plans()
        
        log_info(
            "Plans requested",
            user_id=getattr(request.user, 'id', None),
            plans_count=plans.count()
        )
        
        return plans
    except Exception as e:
        log_error("Failed to fetch plans", error=str(e))
        raise HttpError(500, "Failed to fetch subscription plans")


@router.get("/plans/{plan_id}", response=PlanSchema)
def get_plan(request, plan_id: int):
    """Get a specific subscription plan."""
    try:
        plan = PlanSelector.get_plan_by_id(plan_id)
        if not plan:
            raise HttpError(404, "Plan not found")
        
        log_info(
            "Plan details requested",
            user_id=getattr(request.user, 'id', None),
            plan_id=plan_id,
            plan_name=plan.name
        )
        
        return plan
    except HttpError:
        raise
    except Exception as e:
        log_error("Failed to fetch plan", plan_id=plan_id, error=str(e))
        raise HttpError(404, "Plan not found")


@router.get("/subscriptions", response=List[SubscriptionSchema])
def list_user_subscriptions(request):
    """Get all subscriptions for the current user."""
    if not request.user.is_authenticated:
        raise HttpError(401, "Authentication required")
    
    try:
        subscriptions = SubscriptionSelector.get_user_subscriptions(request.user)
        
        log_info(
            "User subscriptions requested",
            user_id=request.user.id,
            username=request.user.username,
            subscriptions_count=subscriptions.count()
        )
        
        return subscriptions
    except Exception as e:
        log_error(
            "Failed to fetch user subscriptions",
            user_id=request.user.id,
            error=str(e)
        )
        raise HttpError(500, "Failed to fetch subscriptions")


@router.get("/subscriptions/current", response=SubscriptionSchema)
def get_current_subscription(request):
    """Get the current active subscription for the user."""
    if not request.user.is_authenticated:
        raise HttpError(401, "Authentication required")
    
    try:
        subscription = SubscriptionSelector.get_user_active_subscription(request.user)
        
        if not subscription:
            raise HttpError(404, "No active subscription found")
        
        log_info(
            "Current subscription requested",
            user_id=request.user.id,
            username=request.user.username,
            subscription_id=subscription.pk,
            plan_name=subscription.plan.name
        )
        
        return subscription
    except HttpError:
        raise
    except Exception as e:
        log_error(
            "Failed to fetch current subscription",
            user_id=request.user.id,
            error=str(e)
        )
        raise HttpError(500, "Failed to fetch current subscription")


@router.post("/subscriptions", response=SubscriptionSchema)
def create_subscription(request, data: CreateSubscriptionSchema):
    """Create a new subscription for the user."""
    if not request.user.is_authenticated:
        raise HttpError(401, "Authentication required")
    
    try:
        # Check if user already has an active subscription
        if SubscriptionSelector.check_user_has_active_subscription(request.user):
            raise HttpError(400, "User already has an active subscription")
        
        # Get the plan
        plan = get_object_or_404(Plan, id=data.plan_id, is_active=True)
        
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
        if plan.billing_cycle == 'monthly':
            period_end = now + timedelta(days=30)
        elif plan.billing_cycle == 'quarterly':
            period_end = now + timedelta(days=90)
        else:  # yearly
            period_end = now + timedelta(days=365)
        
        # Create subscription
        subscription = Subscription.objects.create(
            user=request.user,
            plan=plan,
            status=status,
            start_date=start_date,
            trial_end=trial_end,
            current_period_start=start_date,
            current_period_end=period_end,
            external_customer_id=getattr(request.user, 'external_customer_id', None)
        )
        
        log_info(
            "Subscription created",
            user_id=request.user.id,
            username=request.user.username,
            subscription_id=subscription.pk,
            plan_name=plan.name,
            status=status
        )
        
        return subscription
        
    except HttpError:
        raise
    except Exception as e:
        log_error(
            "Failed to create subscription",
            user_id=request.user.id,
            plan_id=data.plan_id,
            error=str(e)
        )
        raise HttpError(500, "Failed to create subscription")


@router.post("/subscriptions/{subscription_id}/cancel")
def cancel_subscription(request, subscription_id: int, data: CancelSubscriptionSchema):
    """Cancel a subscription."""
    if not request.user.is_authenticated:
        raise HttpError(401, "Authentication required")
    
    try:
        subscription = get_object_or_404(
            Subscription,
            id=subscription_id,
            user=request.user
        )
        
        if subscription.status in ['canceled', 'unpaid']:
            raise HttpError(400, "Subscription is already canceled or unpaid")
        
        subscription.cancel(at_period_end=data.at_period_end)
        
        log_info(
            "Subscription canceled",
            user_id=request.user.id,
            username=request.user.username,
            subscription_id=subscription_id,
            at_period_end=data.at_period_end
        )
        
        return {"message": "Subscription canceled successfully"}
        
    except HttpError:
        raise
    except Exception as e:
        log_error(
            "Failed to cancel subscription",
            user_id=request.user.id,
            subscription_id=subscription_id,
            error=str(e)
        )
        raise HttpError(500, "Failed to cancel subscription")


@router.get("/payments", response=List[PaymentSchema])
def list_payments(request):
    """Get payment history for the current user."""
    if not request.user.is_authenticated:
        raise HttpError(401, "Authentication required")
    
    try:
        payments = PaymentSelector.get_user_payments(request.user)
        
        log_info(
            "Payment history requested",
            user_id=request.user.id,
            username=request.user.username,
            payments_count=payments.count()
        )
        
        return payments
    except Exception as e:
        log_error(
            "Failed to fetch payment history",
            user_id=request.user.id,
            error=str(e)
        )
        raise HttpError(500, "Failed to fetch payment history")


@router.get("/status", response=SubscriptionStatusSchema)
def get_subscription_status(request):
    """Get comprehensive subscription status for the user."""
    if not request.user.is_authenticated:
        raise HttpError(401, "Authentication required")
    
    try:
        # Get current subscription
        current_subscription = SubscriptionSelector.get_user_active_subscription(request.user)
        
        # Get available plans
        available_plans = PlanSelector.get_active_plans()
        
        log_info(
            "Subscription status requested",
            user_id=request.user.id,
            username=request.user.username,
            has_active_subscription=current_subscription is not None
        )
        
        return {
            "has_active_subscription": current_subscription is not None,
            "current_subscription": current_subscription,
            "available_plans": available_plans
        }
        
    except Exception as e:
        log_error(
            "Failed to fetch subscription status",
            user_id=request.user.id,
            error=str(e)
        )
        raise HttpError(500, "Failed to fetch subscription status")


@router.get("/features", response=List[dict])
def list_features(request):
    """Get all available subscription features."""
    try:
        features = FeatureSelector.get_all_features()
        
        # Group features by category
        features_by_category = {}
        for feature in features:
            if feature.category not in features_by_category:
                features_by_category[feature.category] = []
            features_by_category[feature.category].append({
                "id": feature.pk,
                "name": feature.name,
                "slug": feature.slug,
                "description": feature.description,
                "feature_type": feature.feature_type,
                "default_value": feature.default_value
            })
        
        log_info(
            "Features requested",
            user_id=getattr(request.user, 'id', None),
            features_count=features.count()
        )
        
        return features_by_category
        
    except Exception as e:
        log_error("Failed to fetch features", error=str(e))
        raise HttpError(500, "Failed to fetch features") 