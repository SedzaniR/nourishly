from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Plan, Subscription, Payment, SubscriptionFeature, PlanFeature


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    """Admin interface for subscription plans."""
    
    list_display = [
        'name', 'slug', 'price_display', 'billing_cycle', 'is_active', 
        'is_popular', 'trial_days', 'subscriber_count'
    ]
    list_filter = [
        'is_active', 'is_popular', 'billing_cycle', 'currency',
        'ai_meal_planning', 'nutrition_analytics', 'priority_support'
    ]
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'currency', 'billing_cycle', 'trial_days')
        }),
        ('Features', {
            'fields': (
                'max_recipes', 'max_meal_plans', 'ai_meal_planning',
                'nutrition_analytics', 'priority_support', 'custom_goals'
            ),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_popular')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def price_display(self, obj):
        """Display price with currency."""
        return f"${obj.price} {obj.currency}"
    price_display.short_description = 'Price'
    
    def subscriber_count(self, obj):
        """Show number of active subscribers."""
        count = obj.subscriptions.filter(status='active').count()
        return count
    subscriber_count.short_description = 'Active Subscribers'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin interface for user subscriptions."""
    
    list_display = [
        'user_link', 'plan_name', 'status', 'start_date', 
        'current_period_end', 'days_remaining', 'is_active_display'
    ]
    list_filter = [
        'status', 'plan__name', 'cancel_at_period_end',
        'start_date', 'current_period_end'
    ]
    search_fields = [
        'user__username', 'user__email', 'user__first_name', 
        'user__last_name', 'external_subscription_id'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'days_remaining', 'is_active_display'
    ]
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('User & Plan', {
            'fields': ('user', 'plan')
        }),
        ('Status & Dates', {
            'fields': (
                'status', 'start_date', 'end_date', 'trial_end', 
                'canceled_at', 'cancel_at_period_end'
            )
        }),
        ('Billing Period', {
            'fields': ('current_period_start', 'current_period_end')
        }),
        ('External Payment Provider', {
            'fields': ('external_subscription_id', 'external_customer_id'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_link(self, obj):
        """Link to user admin."""
        if obj.user:
            url = reverse('admin:users_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return '-'
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'
    
    def plan_name(self, obj):
        """Display plan name."""
        return obj.plan.name
    plan_name.short_description = 'Plan'
    plan_name.admin_order_field = 'plan__name'
    
    def is_active_display(self, obj):
        """Display active status with color."""
        if obj.is_active:
            return format_html(
                '<span style="color: green;">✓ Active</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">✗ Inactive</span>'
            )
    is_active_display.short_description = 'Active'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user', 'plan')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for subscription payments."""
    
    list_display = [
        'user_link', 'subscription_link', 'amount_display', 'status', 
        'paid_at', 'external_payment_id'
    ]
    list_filter = [
        'status', 'currency', 'paid_at', 'subscription__plan__name'
    ]
    search_fields = [
        'subscription__user__username', 'subscription__user__email',
        'external_payment_id', 'external_invoice_id', 'description'
    ]
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'paid_at'
    
    fieldsets = (
        ('Payment Details', {
            'fields': ('subscription', 'amount', 'currency', 'status')
        }),
        ('Timing', {
            'fields': ('paid_at',)
        }),
        ('External Payment Provider', {
            'fields': ('external_payment_id', 'external_invoice_id'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('description', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_link(self, obj):
        """Link to user admin."""
        if obj.subscription.user:
            url = reverse('admin:users_user_change', args=[obj.subscription.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.subscription.user.username)
        return '-'
    user_link.short_description = 'User'
    user_link.admin_order_field = 'subscription__user__username'
    
    def subscription_link(self, obj):
        """Link to subscription admin."""
        url = reverse('admin:subscriptions_subscription_change', args=[obj.subscription.id])
        return format_html('<a href="{}">{}</a>', url, obj.subscription)
    subscription_link.short_description = 'Subscription'
    
    def amount_display(self, obj):
        """Display amount with currency."""
        return f"${obj.amount} {obj.currency}"
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'subscription__user', 'subscription__plan'
        )


@admin.register(SubscriptionFeature)
class SubscriptionFeatureAdmin(admin.ModelAdmin):
    """Admin interface for subscription features."""
    
    list_display = ['name', 'slug', 'feature_type', 'category', 'default_value_display']
    list_filter = ['feature_type', 'category']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Feature Configuration', {
            'fields': ('feature_type', 'category', 'default_value')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def default_value_display(self, obj):
        """Display default value in a readable format."""
        if isinstance(obj.default_value, dict):
            return str(obj.default_value)
        return obj.default_value
    default_value_display.short_description = 'Default Value'


@admin.register(PlanFeature)
class PlanFeatureAdmin(admin.ModelAdmin):
    """Admin interface for plan features."""
    
    list_display = ['plan', 'feature', 'value_display']
    list_filter = ['plan__name', 'feature__category', 'feature__feature_type']
    search_fields = ['plan__name', 'feature__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Plan & Feature', {
            'fields': ('plan', 'feature')
        }),
        ('Configuration', {
            'fields': ('value',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def value_display(self, obj):
        """Display value in a readable format."""
        if isinstance(obj.value, dict):
            return str(obj.value)
        return obj.value
    value_display.short_description = 'Value'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('plan', 'feature')
