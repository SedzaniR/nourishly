from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from core.base_models import TimeStampedModel
from core.logger import log_info


class Plan(TimeStampedModel):
    """
    Subscription plan model defining different tiers of service.
    """

    name = models.CharField(
        max_length=100, help_text="Plan name (e.g., 'Basic', 'Premium')"
    )
    slug = models.SlugField(unique=True, help_text="URL-friendly identifier")
    description = models.TextField(help_text="Plan description and features")

    # Pricing
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Monthly price in USD",
    )
    currency = models.CharField(
        max_length=3, default="USD", help_text="Currency code (USD, EUR, etc.)"
    )

    # Billing cycle
    billing_cycle = models.CharField(
        max_length=20,
        choices=[
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("yearly", "Yearly"),
        ],
        default="monthly",
        help_text="Billing frequency",
    )

    # Features and limits
    max_recipes = models.IntegerField(
        null=True,
        blank=True,
        help_text="Maximum number of recipes user can save (null = unlimited)",
    )
    max_meal_plans = models.IntegerField(
        null=True,
        blank=True,
        help_text="Maximum number of meal plans (null = unlimited)",
    )
    ai_meal_planning = models.BooleanField(
        default=False, help_text="Access to AI-powered meal planning"
    )
    nutrition_analytics = models.BooleanField(
        default=False, help_text="Advanced nutrition analytics and insights"
    )
    priority_support = models.BooleanField(
        default=False, help_text="Priority customer support"
    )
    custom_goals = models.BooleanField(
        default=False, help_text="Custom nutrition goals and tracking"
    )

    # Status
    is_active = models.BooleanField(
        default=True, help_text="Whether this plan is available for new subscriptions"
    )
    is_popular = models.BooleanField(
        default=False, help_text="Mark as popular/recommended plan"
    )

    # Trial settings
    trial_days = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(365)],
        help_text="Number of free trial days",
    )

    class Meta:
        db_table = "subscription_plans"
        ordering = ["price"]
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"

    def __str__(self):
        return f"{self.name} - ${self.price}/{self.billing_cycle}"

    def save(self, *args, **kwargs):
        """Override save to add logging."""
        is_new = self.pk is None

        if is_new:
            log_info(
                "Creating new subscription plan",
                plan_name=self.name,
                plan_slug=self.slug,
                price=self.price,
            )
        else:
            log_info(
                "Updating subscription plan",
                plan_name=self.name,
                plan_slug=self.slug,
                price=self.price,
            )

        super().save(*args, **kwargs)

    @property
    def yearly_price(self):
        """Calculate yearly price based on billing cycle."""
        if self.billing_cycle == "yearly":
            return self.price
        elif self.billing_cycle == "quarterly":
            return self.price * 4
        else:  # monthly
            return self.price * 12

    @property
    def monthly_equivalent_price(self):
        """Calculate monthly equivalent price."""
        if self.billing_cycle == "monthly":
            return self.price
        elif self.billing_cycle == "quarterly":
            return self.price / 3
        else:  # yearly
            return self.price / 12


class Subscription(TimeStampedModel):
    """
    User subscription model tracking active subscriptions.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        help_text="User who owns this subscription",
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="subscriptions",
        help_text="Subscription plan",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "Active"),
            ("canceled", "Canceled"),
            ("past_due", "Past Due"),
            ("unpaid", "Unpaid"),
            ("trialing", "Trialing"),
            ("paused", "Paused"),
        ],
        default="active",
        help_text="Current subscription status",
    )

    # Dates
    start_date = models.DateTimeField(help_text="When subscription started")
    end_date = models.DateTimeField(
        null=True, blank=True, help_text="When subscription ends (null = ongoing)"
    )
    trial_end = models.DateTimeField(
        null=True, blank=True, help_text="When trial period ends"
    )
    canceled_at = models.DateTimeField(
        null=True, blank=True, help_text="When subscription was canceled"
    )

    # Billing
    current_period_start = models.DateTimeField(
        help_text="Start of current billing period"
    )
    current_period_end = models.DateTimeField(help_text="End of current billing period")
    cancel_at_period_end = models.BooleanField(
        default=False, help_text="Cancel at end of current period"
    )

    # External references (payment provider agnostic)
    external_subscription_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
        help_text="External payment provider subscription ID",
    )
    external_customer_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="External payment provider customer ID",
    )

    class Meta:
        db_table = "subscriptions"
        ordering = ["-created_at"]
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"

    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({self.status})"

    def save(self, *args, **kwargs):
        """Override save to add logging."""
        is_new = self.pk is None

        if is_new:
            log_info(
                "Creating new subscription",
                user_id=self.user.id,
                username=self.user.username,
                plan_name=self.plan.name,
                status=self.status,
            )
        else:
            log_info(
                "Updating subscription",
                user_id=self.user.id,
                username=self.user.username,
                plan_name=self.plan.name,
                status=self.status,
            )

        super().save(*args, **kwargs)

    @property
    def is_active(self):
        """Check if subscription is currently active."""
        return self.status in ["active", "trialing"]

    @property
    def is_trialing(self):
        """Check if subscription is in trial period."""
        if not self.trial_end:
            return False
        from django.utils import timezone

        return timezone.now() < self.trial_end

    @property
    def days_remaining(self):
        """Calculate days remaining in current period."""
        from django.utils import timezone

        now = timezone.now()
        if self.current_period_end > now:
            return (self.current_period_end - now).days
        return 0

    def cancel(self, at_period_end=True):
        """Cancel the subscription."""
        from django.utils import timezone

        if at_period_end:
            self.cancel_at_period_end = True
            self.status = "active"  # Keep active until period ends
        else:
            self.status = "canceled"
            self.canceled_at = timezone.now()
            self.end_date = timezone.now()

        self.save()

        log_info(
            "Subscription canceled",
            user_id=self.user.id,
            username=self.user.username,
            plan_name=self.plan.name,
            at_period_end=at_period_end,
        )


class Payment(TimeStampedModel):
    """
    Payment model tracking individual payments for subscriptions.
    """

    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name="payments",
        help_text="Subscription this payment is for",
    )

    # Payment details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Payment amount",
    )
    currency = models.CharField(
        max_length=3, default="USD", help_text="Payment currency"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("succeeded", "Succeeded"),
            ("failed", "Failed"),
            ("canceled", "Canceled"),
            ("refunded", "Refunded"),
        ],
        default="pending",
        help_text="Payment status",
    )

    # Dates
    paid_at = models.DateTimeField(
        null=True, blank=True, help_text="When payment was completed"
    )

    # External references (payment provider agnostic)
    external_payment_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
        help_text="External payment provider payment ID",
    )
    external_invoice_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="External payment provider invoice ID",
    )

    # Metadata
    description = models.CharField(
        max_length=255, blank=True, help_text="Payment description"
    )
    metadata = models.JSONField(
        default=dict, blank=True, help_text="Additional payment metadata"
    )

    class Meta:
        db_table = "subscription_payments"
        ordering = ["-created_at"]
        verbose_name = "Payment"
        verbose_name_plural = "Payments"

    def __str__(self):
        return f"{self.subscription.user.username} - ${self.amount} ({self.status})"

    def save(self, *args, **kwargs):
        """Override save to add logging."""
        is_new = self.pk is None

        if is_new:
            log_info(
                "Creating new payment",
                user_id=self.subscription.user.id,
                username=self.subscription.user.username,
                amount=self.amount,
                status=self.status,
            )
        else:
            log_info(
                "Updating payment",
                user_id=self.subscription.user.id,
                username=self.subscription.user.username,
                amount=self.amount,
                status=self.status,
            )

        super().save(*args, **kwargs)


class SubscriptionFeature(TimeStampedModel):
    """
    Model to define features available in subscription plans.
    This allows for flexible feature management.
    """

    name = models.CharField(max_length=100, unique=True, help_text="Feature name")
    slug = models.SlugField(unique=True, help_text="URL-friendly identifier")
    description = models.TextField(help_text="Feature description")

    # Feature type
    feature_type = models.CharField(
        max_length=20,
        choices=[
            ("boolean", "Boolean (on/off)"),
            ("numeric", "Numeric (with limits)"),
            ("unlimited", "Unlimited"),
        ],
        default="boolean",
        help_text="Type of feature",
    )

    # Default values
    default_value = models.JSONField(
        default=dict, help_text="Default value for this feature"
    )

    # Category
    category = models.CharField(
        max_length=50,
        choices=[
            ("core", "Core Features"),
            ("analytics", "Analytics"),
            ("planning", "Meal Planning"),
            ("social", "Social Features"),
            ("support", "Support"),
        ],
        default="core",
        help_text="Feature category",
    )

    class Meta:
        db_table = "subscription_features"
        ordering = ["category", "name"]
        verbose_name = "Subscription Feature"
        verbose_name_plural = "Subscription Features"

    def __str__(self):
        return f"{self.name} ({self.category})"


class PlanFeature(TimeStampedModel):
    """
    Junction table linking plans to features with specific values.
    """

    plan = models.ForeignKey(
        Plan,
        on_delete=models.CASCADE,
        related_name="plan_features",
        help_text="Subscription plan",
    )
    feature = models.ForeignKey(
        SubscriptionFeature,
        on_delete=models.CASCADE,
        related_name="plan_features",
        help_text="Feature",
    )

    # Feature value for this plan
    value = models.JSONField(default=dict, help_text="Feature value for this plan")

    class Meta:
        db_table = "plan_features"
        unique_together = ["plan", "feature"]
        verbose_name = "Plan Feature"
        verbose_name_plural = "Plan Features"

    def __str__(self):
        return f"{self.plan.name} - {self.feature.name}"
