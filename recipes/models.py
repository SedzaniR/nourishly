import uuid
from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from typing import Optional, List

from core.base_models import TimeStampedModel


class Recipe(TimeStampedModel):
    """Main recipe model containing recipe details and metadata."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, null=True)
    source_url = models.URLField(max_length=500)
    source_site = models.CharField(max_length=100)
    image_url = models.URLField(max_length=500)
    instructions = models.JSONField()
    preparation_time = models.PositiveIntegerField(
        blank=True, null=True, help_text="Preparation time in minutes"
    )
    cooking_time = models.PositiveIntegerField(
        blank=True, null=True, help_text="Cooking time in minutes"
    )
    servings = models.PositiveIntegerField(
        blank=True, null=True, help_text="Number of servings"
    )

    # Recipe categorization
    cuisine_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Type of cuisine (e.g., 'Italian', 'Mexican', 'Asian')",
    )

    # Rating and reviews
    rating = models.FloatField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="Average rating (0-5 stars)",
    )
    review_count = models.PositiveIntegerField(
        blank=True, null=True, help_text="Number of reviews/ratings"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["source_site"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["rating"]),
            models.Index(fields=["cuisine_type"]),
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

    @property
    def dietary_restrictions_list(self) -> List[str]:
        """Get list of dietary restriction names for this recipe."""
        return list(
            self.recipe_dietary_restrictions.values_list(
                "dietary_restriction__name", flat=True
            )
        )

    @property
    def dietary_restrictions_display(self) -> List[str]:
        """Get list of dietary restriction display names for this recipe."""
        return list(
            self.recipe_dietary_restrictions.values_list(
                "dietary_restriction__display_name", flat=True
            )
        )

    def has_dietary_restriction(self, restriction_name: str) -> bool:
        """Check if recipe has a specific dietary restriction."""
        return self.recipe_dietary_restrictions.filter(
            dietary_restriction__name=restriction_name
        ).exists()

    def is_vegetarian(self) -> bool:
        """Check if recipe is vegetarian."""
        return self.has_dietary_restriction("vegetarian")

    def is_vegan(self) -> bool:
        """Check if recipe is vegan."""
        return self.has_dietary_restriction("vegan")

    def is_gluten_free(self) -> bool:
        """Check if recipe is gluten-free."""
        return self.has_dietary_restriction("gluten_free")


class RecipeVector(TimeStampedModel):
    """Vector embeddings for recipe semantic search and recommendations."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipe = models.OneToOneField(
        Recipe, on_delete=models.CASCADE, related_name="vector"
    )
    # Placeholder for vector field - replace with pgvector field when available
    # embedding = VectorField(dimensions=768)  # Example for pgvector
    embedding = models.TextField(
        help_text="JSON serialized vector embedding (placeholder for pgvector)"
    )
    embedding_version = models.CharField(
        max_length=50, help_text="Version of the embedding model used"
    )

    class Meta:
        indexes = [
            models.Index(fields=["embedding_version"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"Vector for {self.recipe.title}"


class Ingredient(TimeStampedModel):
    """Catalog of ingredients with categorization and nutritional information."""

    class Category(models.TextChoices):
        PROTEIN = "protein", "Protein"
        DAIRY = "dairy", "Dairy"
        GRAINS = "grains", "Grains"
        VEGETABLES = "vegetables", "Vegetables"
        FRUITS = "fruits", "Fruits"
        HERBS_SPICES = "herbs_spices", "Herbs & Spices"
        OILS_FATS = "oils_fats", "Oils & Fats"
        NUTS_SEEDS = "nuts_seeds", "Nuts & Seeds"
        SWEETENERS = "sweeteners", "Sweeteners"
        BEVERAGES = "beverages", "Beverages"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    category = models.CharField(
        max_length=20, choices=Category.choices, default=Category.OTHER
    )

    # Nutritional information per 100g
    calories_per_100g = models.FloatField(
        blank=True, null=True, help_text="Calories per 100 grams"
    )
    protein_per_100g = models.FloatField(
        blank=True, null=True, help_text="Protein in grams per 100 grams"
    )
    carbohydrates_per_100g = models.FloatField(
        blank=True, null=True, help_text="Total carbohydrates in grams per 100 grams"
    )
    fat_per_100g = models.FloatField(
        blank=True, null=True, help_text="Total fat in grams per 100 grams"
    )
    fiber_per_100g = models.FloatField(
        blank=True, null=True, help_text="Dietary fiber in grams per 100 grams"
    )
    sugar_per_100g = models.FloatField(
        blank=True, null=True, help_text="Total sugars in grams per 100 grams"
    )

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self) -> str:
        return self.name


class RecipeIngredient(models.Model):
    """Through model for Recipe-Ingredient many-to-many relationship with quantities."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="recipe_ingredients"
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, related_name="recipe_ingredients"
    )
    quantity = models.FloatField(help_text="Quantity of ingredient needed")
    unit = models.CharField(
        max_length=50, help_text="Unit of measurement (e.g., 'cups', 'grams', 'pieces')"
    )
    note = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about preparation or substitutions",
    )
    original_text = models.TextField(
        blank=True, null=True, help_text="Original text of the ingredient"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["recipe", "ingredient"]
        ordering = ["id"]
        indexes = [
            models.Index(fields=["recipe", "ingredient"]),
        ]

    def __str__(self) -> str:
        return f"{self.quantity} {self.unit} {self.ingredient.name} for {self.recipe.title}"


class IngredientAllergen(TimeStampedModel):
    """Allergen information for ingredients."""

    class AllergenType(models.TextChoices):
        DAIRY = "dairy", "Dairy"
        EGGS = "eggs", "Eggs"
        FISH = "fish", "Fish"
        SHELLFISH = "shellfish", "Shellfish"
        TREE_NUTS = "tree_nuts", "Tree Nuts"
        PEANUTS = "peanuts", "Peanuts"
        WHEAT = "wheat", "Wheat"
        SOYBEANS = "soybeans", "Soybeans"
        SESAME = "sesame", "Sesame"
        GLUTEN = "gluten", "Gluten"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, related_name="allergens"
    )
    allergen_name = models.CharField(max_length=20, choices=AllergenType.choices)

    class Meta:
        unique_together = ["ingredient", "allergen_name"]
        ordering = ["allergen_name"]
        indexes = [
            models.Index(fields=["allergen_name"]),
            models.Index(fields=["ingredient", "allergen_name"]),
        ]

    def __str__(self) -> str:
        return f"{self.ingredient.name} - {self.get_allergen_name_display()}"


class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)


class RecipeTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipe = models.ForeignKey(
        "Recipe", on_delete=models.CASCADE, related_name="recipe_tags"
    )
    tag = models.ForeignKey(
        "Tag", on_delete=models.CASCADE, related_name="tagged_recipes"
    )


class DietaryRestriction(TimeStampedModel):
    """Dietary restrictions and guidelines (vegetarian, gluten-free, etc.)."""

    class RestrictionType(models.TextChoices):
        VEGETARIAN = "vegetarian", "Vegetarian"
        VEGAN = "vegan", "Vegan"
        GLUTEN_FREE = "gluten_free", "Gluten-Free"
        DAIRY_FREE = "dairy_free", "Dairy-Free"
        NUT_FREE = "nut_free", "Nut-Free"
        EGG_FREE = "egg_free", "Egg-Free"
        SOY_FREE = "soy_free", "Soy-Free"
        KETO = "keto", "Ketogenic"
        PALEO = "paleo", "Paleo"
        LOW_CARB = "low_carb", "Low-Carb"
        LOW_SODIUM = "low_sodium", "Low-Sodium"
        DIABETIC_FRIENDLY = "diabetic_friendly", "Diabetic-Friendly"
        HALAL = "halal", "Halal"
        KOSHER = "kosher", "Kosher"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=30,
        choices=RestrictionType.choices,
        unique=True,
        help_text="Type of dietary restriction or guideline",
    )
    display_name = models.CharField(
        max_length=50, help_text="Human-readable name for display"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Detailed description of the dietary restriction",
    )

    class Meta:
        ordering = ["display_name"]
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self) -> str:
        return self.display_name

    def save(self, *args, **kwargs) -> None:
        """Auto-populate display_name from choices if not provided."""
        if not self.display_name:
            self.display_name = self.get_name_display()
        super().save(*args, **kwargs)


class RecipeDietaryRestriction(models.Model):
    """Through model for Recipe-DietaryRestriction many-to-many relationship."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipe = models.ForeignKey(
        "Recipe", on_delete=models.CASCADE, related_name="recipe_dietary_restrictions"
    )
    dietary_restriction = models.ForeignKey(
        "DietaryRestriction",
        on_delete=models.CASCADE,
        related_name="restricted_recipes",
    )
    confidence = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Confidence level (0.0-1.0) for auto-detected restrictions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["recipe", "dietary_restriction"]
        ordering = ["dietary_restriction__display_name"]
        indexes = [
            models.Index(fields=["recipe", "dietary_restriction"]),
            models.Index(fields=["dietary_restriction"]),
        ]

    def __str__(self) -> str:
        return f"{self.recipe.title} - {self.dietary_restriction.display_name}"
