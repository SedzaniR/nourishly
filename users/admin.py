from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin interface for the custom User model."""
    
    list_display = [
        'username', 'email', 'full_name', 'age', 'bmi_display', 
        'activity_level', 'profile_completed', 'is_active', 'date_joined'
    ]
    list_filter = [
        'is_active', 'is_staff', 'is_superuser', 'profile_completed', 
        'email_verified', 'activity_level', 'measurement_unit', 'profile_visibility'
    ]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    # Fieldsets for editing
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {
            'fields': (
                'first_name', 'last_name', 'email', 'date_of_birth', 'gender',
                'height', 'weight', 'activity_level'
            )
        }),
        ('Nutrition Goals', {
            'fields': (
                'daily_calorie_goal', 'protein_goal', 'carb_goal', 'fat_goal'
            ),
            'classes': ('collapse',)
        }),
        ('Dietary Preferences', {
            'fields': (
                'dietary_restrictions', 'allergies', 'preferred_cuisines'
            ),
            'classes': ('collapse',)
        }),
        ('App Settings', {
            'fields': (
                'measurement_unit', 'timezone', 'profile_visibility'
            ),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 'email_verified', 
                'profile_completed', 'groups', 'user_permissions'
            )
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    # Fieldsets for adding new users
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['last_login', 'date_joined', 'created_at', 'updated_at']
    
    def full_name(self, obj):
        """Display full name."""
        return obj.full_name
    full_name.short_description = 'Full Name'
    
    def age(self, obj):
        """Display age."""
        return obj.age or '-'
    age.short_description = 'Age'
    
    def bmi_display(self, obj):
        """Display BMI with category."""
        bmi = obj.get_bmi()
        if bmi is None:
            return '-'
        
        category = obj.get_bmi_category()
        color_map = {
            'underweight': 'orange',
            'normal': 'green',
            'overweight': 'orange',
            'obese': 'red'
        }
        color = color_map.get(category, 'black')
        
        return format_html(
            '<span style="color: {};">{:.1f} ({})</span>',
            color, bmi, category
        )
    bmi_display.short_description = 'BMI'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related()
