import uuid
from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from typing import Optional

from core.base_models import TimeStampedModel


class Recipe(TimeStampedModel):
    """Main recipe model containing recipe details and metadata."""
    
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(
        max_length=255, 
        unique=True, 
        null=True
    )
    source_url = models.URLField(max_length=500)
    source_site = models.CharField(max_length=100)
    image_url = models.URLField(
        max_length=500
    )
    instructions = models.JSONField()
    preparation_time = models.PositiveIntegerField(
        blank=True, 
        null=True,
        help_text="Preparation time in minutes"
    )
    cooking_time = models.PositiveIntegerField(
        blank=True, 
        null=True,
        help_text="Cooking time in minutes"
    )
    servings = models.PositiveIntegerField(
        blank=True, 
        null=True,
        help_text="Number of servings"
    )
    
    # Rating and reviews
    rating = models.FloatField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="Average rating (0-5 stars)"
    )
    review_count = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Number of reviews/ratings"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['source_site']),
            models.Index(fields=['created_at']),
            models.Index(fields=['rating']),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs) -> None:
        """Auto-generate slug from title if not provided."""
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    @property
    def total_time(self) -> Optional[int]:
        """Calculate total cooking time."""
        if self.preparation_time and self.cooking_time:
            return self.preparation_time + self.cooking_time
        return None

    @property
    def rating_display(self) -> str:
        """Return formatted rating string for display."""
        if self.rating is None:
            return "No rating"
        
        stars = "★" * int(self.rating) + "☆" * (5 - int(self.rating))
        review_text = f" ({self.review_count} reviews)" if self.review_count else ""
        return f"{self.rating:.1f}/5 {stars}{review_text}"

    @property
    def has_good_rating(self) -> bool:
        """Check if recipe has a good rating (4+ stars)."""
        return self.rating is not None and self.rating >= 4.0



class RecipeVector(TimeStampedModel):
    """Vector embeddings for recipe semantic search and recommendations."""
    
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    recipe = models.OneToOneField(
        Recipe,
        on_delete=models.CASCADE,
        related_name='vector'
    )
    # Placeholder for vector field - replace with pgvector field when available
    # embedding = VectorField(dimensions=768)  # Example for pgvector
    embedding = models.TextField(
        help_text="JSON serialized vector embedding (placeholder for pgvector)"
    )
    embedding_version = models.CharField(
        max_length=50,
        help_text="Version of the embedding model used"
    )

    class Meta:
        indexes = [
            models.Index(fields=['embedding_version']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self) -> str:
        return f"Vector for {self.recipe.title}"


class Ingredient(TimeStampedModel):
    """Catalog of ingredients with categorization and nutritional information."""
    
    class Category(models.TextChoices):
        PROTEIN = 'protein', 'Protein'
        DAIRY = 'dairy', 'Dairy'
        GRAINS = 'grains', 'Grains'
        VEGETABLES = 'vegetables', 'Vegetables'
        FRUITS = 'fruits', 'Fruits'
        HERBS_SPICES = 'herbs_spices', 'Herbs & Spices'
        OILS_FATS = 'oils_fats', 'Oils & Fats'
        NUTS_SEEDS = 'nuts_seeds', 'Nuts & Seeds'
        SWEETENERS = 'sweeteners', 'Sweeteners'
        BEVERAGES = 'beverages', 'Beverages'
        OTHER = 'other', 'Other'

    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    name = models.CharField(max_length=255, unique=True)
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER
    )
    
    # Nutritional information per 100g
    calories_per_100g = models.FloatField(
        blank=True,
        null=True,
        help_text="Calories per 100 grams"
    )
    protein_per_100g = models.FloatField(
        blank=True,
        null=True,
        help_text="Protein in grams per 100 grams"
    )
    carbohydrates_per_100g = models.FloatField(
        blank=True,
        null=True,
        help_text="Total carbohydrates in grams per 100 grams"
    )
    fat_per_100g = models.FloatField(
        blank=True,
        null=True,
        help_text="Total fat in grams per 100 grams"
    )
    fiber_per_100g = models.FloatField(
        blank=True,
        null=True,
        help_text="Dietary fiber in grams per 100 grams"
    )
    sugar_per_100g = models.FloatField(
        blank=True,
        null=True,
        help_text="Total sugars in grams per 100 grams"
    )

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
        ]

    def __str__(self) -> str:
        return self.name


class RecipeIngredient(models.Model):
    """Through model for Recipe-Ingredient many-to-many relationship with quantities."""
    
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    quantity = models.FloatField(
        help_text="Quantity of ingredient needed"
    )
    unit = models.CharField(
        max_length=50,
        help_text="Unit of measurement (e.g., 'cups', 'grams', 'pieces')"
    )
    note = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about preparation or substitutions"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['recipe', 'ingredient']
        ordering = ['id']
        indexes = [
            models.Index(fields=['recipe', 'ingredient']),
        ]

    def __str__(self) -> str:
        return f"{self.quantity} {self.unit} {self.ingredient.name} for {self.recipe.title}"


class IngredientAllergen(TimeStampedModel):
    """Allergen information for ingredients."""
    
    class AllergenType(models.TextChoices):
        DAIRY = 'dairy', 'Dairy'
        EGGS = 'eggs', 'Eggs'
        FISH = 'fish', 'Fish'
        SHELLFISH = 'shellfish', 'Shellfish'
        TREE_NUTS = 'tree_nuts', 'Tree Nuts'
        PEANUTS = 'peanuts', 'Peanuts'
        WHEAT = 'wheat', 'Wheat'
        SOYBEANS = 'soybeans', 'Soybeans'
        SESAME = 'sesame', 'Sesame'
        GLUTEN = 'gluten', 'Gluten'
        OTHER = 'other', 'Other'

    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='allergens'
    )
    allergen_name = models.CharField(
        max_length=20,
        choices=AllergenType.choices
    )

    class Meta:
        unique_together = ['ingredient', 'allergen_name']
        ordering = ['allergen_name']
        indexes = [
            models.Index(fields=['allergen_name']),
            models.Index(fields=['ingredient', 'allergen_name']),
        ]

    def __str__(self) -> str:
        return f"{self.ingredient.name} - {self.get_allergen_name_display()}"






