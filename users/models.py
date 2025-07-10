from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from core.base_models import TimeStampedModel
from core.logger import log_info


class User(AbstractUser, TimeStampedModel):
    
    """
    Custom user model for Nourishly nutrition app.
    
    Extends Django's AbstractUser with nutrition-specific fields
    for tracking user health data, dietary preferences, and goals.
    """
    
    # Basic profile fields
    date_of_birth = models.DateField(null=True, blank=True, help_text="User's date of birth")
    gender = models.CharField(
        max_length=1,
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        null=True,
        blank=True,
        help_text="User's gender for BMR calculations"
    )
    height = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(50), MaxValueValidator(300)],
        help_text="Height in centimeters"
    )
    weight = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(500)],
        help_text="Weight in kilograms"
    )
    
    # Activity and lifestyle
    activity_level = models.CharField(
        max_length=20,
        choices=[
            ('sedentary', 'Sedentary (little or no exercise)'),
            ('lightly_active', 'Lightly Active (light exercise 1-3 days/week)'),
            ('moderately_active', 'Moderately Active (moderate exercise 3-5 days/week)'),
            ('very_active', 'Very Active (hard exercise 6-7 days/week)'),
            ('extremely_active', 'Extremely Active (very hard exercise, physical job)'),
        ],
        default='moderately_active',
        help_text="User's activity level for calorie calculations"
    )
    
    # Dietary preferences and restrictions
    dietary_restrictions = models.JSONField(
        default=list, 
        blank=True,
        help_text="List of dietary restrictions (e.g., ['vegetarian', 'gluten-free'])"
    )
    allergies = models.JSONField(
        default=list, 
        blank=True,
        help_text="List of food allergies (e.g., ['peanuts', 'shellfish'])"
    )
    preferred_cuisines = models.JSONField(
        default=list, 
        blank=True,
        help_text="List of preferred cuisines (e.g., ['italian', 'mediterranean'])"
    )
    
    # Nutrition goals
    daily_calorie_goal = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(800), MaxValueValidator(5000)],
        help_text="Daily calorie goal"
    )
    protein_goal = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(500)],
        help_text="Daily protein goal in grams"
    )
    carb_goal = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1000)],
        help_text="Daily carbohydrate goal in grams"
    )
    fat_goal = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(200)],
        help_text="Daily fat goal in grams"
    )
    
    # App preferences
    measurement_unit = models.CharField(
        max_length=10,
        choices=[
            ('metric', 'Metric (kg, cm, °C)'),
            ('imperial', 'Imperial (lb, in, °F)')
        ],
        default='metric',
        help_text="Preferred measurement system"
    )
    timezone = models.CharField(
        max_length=50, 
        default='UTC',
        help_text="User's timezone"
    )
    
    # Privacy and settings
    profile_visibility = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('friends', 'Friends Only'),
            ('private', 'Private')
        ],
        default='private',
        help_text="Profile visibility setting"
    )
    
    # Verification and status
    email_verified = models.BooleanField(default=False, help_text="Whether email has been verified")
    profile_completed = models.BooleanField(default=False, help_text="Whether profile setup is complete")
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email or self.username
    
    def save(self, *args, **kwargs):
        """Override save to add logging and auto-complete profile."""
        is_new = self.pk is None
        
        # Log user creation/update
        if is_new:
            log_info(
                "Creating new user",
                username=self.username,
                email=self.email,
                user_id=self.pk
            )
        else:
            log_info(
                "Updating user",
                username=self.username,
                email=self.email,
                user_id=self.pk
            )
        
        # Auto-complete profile if basic info is provided
        if not self.profile_completed and self.date_of_birth and self.height and self.weight:
            self.profile_completed = True
        
        super().save(*args, **kwargs)
        
        # Log successful save
        if is_new:
            log_info(
                "User created successfully",
                username=self.username,
                email=self.email,
                user_id=self.pk
            )
        else:
            log_info(
                "User updated successfully",
                username=self.username,
                email=self.email,
                user_id=self.pk
            )
    
    @property
    def full_name(self):
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    @property
    def age(self):
        """Calculate user's age from date of birth."""
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    
    def get_bmi(self):
        """Calculate BMI if height and weight are available."""
        if self.height and self.weight:
            height_m = self.height / 100  # Convert cm to meters
            return round(self.weight / (height_m ** 2), 1)
        return None
    
    def get_bmi_category(self):
        """Get BMI category based on calculated BMI."""
        bmi = self.get_bmi()
        if bmi is None:
            return None
        
        if bmi < 18.5:
            return 'underweight'
        elif bmi < 25:
            return 'normal'
        elif bmi < 30:
            return 'overweight'
        else:
            return 'obese'
    
    def calculate_bmr(self):
        """Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation."""
        if not all([self.age, self.height, self.weight, self.gender]):
            return None
        
        age = self.age
        height = float(self.height)
        weight = float(self.weight)
        
        # Type guard to ensure age is not None
        if age is None:
            return None
        
        if self.gender == 'M':
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:  # Female
            bmr = 10 * weight + 6.25 * height - 5 * age - 161
        
        return round(bmr)
    
    def calculate_tdee(self):
        """Calculate Total Daily Energy Expenditure."""
        bmr = self.calculate_bmr()
        if bmr is None:
            return None
        
        activity_multipliers = {
            'sedentary': 1.2,
            'lightly_active': 1.375,
            'moderately_active': 1.55,
            'very_active': 1.725,
            'extremely_active': 1.9
        }
        
        multiplier = activity_multipliers.get(self.activity_level, 1.55)
        return round(bmr * multiplier)
    
    def has_allergy(self, allergen):
        """Check if user has a specific allergy."""
        return allergen.lower() in [a.lower() for a in self.allergies]
    
    def has_dietary_restriction(self, restriction):
        """Check if user has a specific dietary restriction."""
        return restriction.lower() in [r.lower() for r in self.dietary_restrictions]
    
    def get_nutrition_goals(self):
        """Get user's nutrition goals as a dictionary."""
        return {
            'calories': self.daily_calorie_goal,
            'protein': self.protein_goal,
            'carbs': self.carb_goal,
            'fat': self.fat_goal
        }
    
    def is_profile_complete(self):
        """Check if user has completed their profile setup."""
        required_fields = ['date_of_birth', 'height', 'weight', 'activity_level']
        return all(getattr(self, field) for field in required_fields)
