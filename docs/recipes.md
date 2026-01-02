# Recipes App Documentation

The recipes app provides comprehensive recipe management, scraping, analysis, and classification services. It includes models for recipes, ingredients, nutritional information, and dietary restrictions, along with services for scraping recipes from external sources, analyzing nutritional content, and classifying cuisine types.

## 📋 Table of Contents

- [Overview](#overview)
- [Models](#models)
- [Services](#services)
  - [Recipe Providers](#recipe-providers)
  - [Macro Analysis](#macro-analysis)
  - [Cuisine Classification](#cuisine-classification)
- [Usage Examples](#usage-examples)
- [Management Commands](#management-commands)
- [Architecture Patterns](#architecture-patterns)

## Overview

The recipes app is organized into three main service domains:

1. **Recipe Providers** - Scraping and extracting recipes from external sources (Budget Bytes, etc.)
2. **Macro Analysis** - Nutritional analysis using external APIs (API Ninja, USDA), in case the recipe_scrapers module is unable to extract the macros information.
3. **Cuisine Classification** - AI-powered cuisine type detection using Hugging Face models,in case the recipe_scrapers module does not provide the classification.

All services are backend-only (no API endpoints currently exposed) and can be used programmatically or via management commands.

## Models

### Recipe

The main recipe model containing recipe details and metadata.

**Key Fields:**
- `id` (UUID) - Primary key
- `title` (CharField) - Recipe title
- `slug` (SlugField) - URL-friendly identifier
- `source_url` (URLField) - Original recipe URL
- `source_site` (CharField) - Source website name
- `image_url` (URLField) - Recipe image URL
- `instructions` (JSONField) - Step-by-step instructions
- `preparation_time` (PositiveIntegerField) - Prep time in minutes
- `cooking_time` (PositiveIntegerField) - Cooking time in minutes
- `servings` (PositiveIntegerField) - Number of servings
- `cuisine_type` (CharField) - Type of cuisine
- `rating` (FloatField) - Average rating (0-5)
- `review_count` (PositiveIntegerField) - Number of reviews
- `embedding` (ArrayField) - Vector embedding for semantic search

**Properties:**
- `total_time` - Calculated total cooking time
- `rating_display` - Formatted rating string
- `has_good_rating` - Check if rating is 4+ stars
- `dietary_restrictions_list` - List of dietary restriction names
- `is_vegetarian()`, `is_vegan()`, `is_gluten_free()` - Dietary restriction checks

**Example:**
```python
from recipes.models import Recipe

recipe = Recipe.objects.create(
    title="Chocolate Chip Cookies",
    source_url="https://example.com/cookies",
    source_site="Example Site",
    image_url="https://example.com/cookies.jpg",
    instructions=["Mix ingredients", "Bake at 350°F"],
    preparation_time=15,
    cooking_time=12,
    servings=24,
    cuisine_type="American"
)

print(recipe.total_time)  # 27
print(recipe.rating_display)  # "4.5/5 ★★★★☆ (10 reviews)"
```

### Ingredient

Catalog of ingredients with categorization and nutritional information.

**Key Fields:**
- `id` (UUID) - Primary key
- `name` (CharField) - Ingredient name (unique)
- `category` (CharField) - Ingredient category (choices: PROTEIN, DAIRY, GRAINS, etc.)
- `calories_per_100g` (FloatField) - Calories per 100g
- `protein_per_100g` (FloatField) - Protein per 100g
- `carbohydrates_per_100g` (FloatField) - Carbs per 100g
- `fat_per_100g` (FloatField) - Fat per 100g
- `fiber_per_100g` (FloatField) - Fiber per 100g
- `sugar_per_100g` (FloatField) - Sugar per 100g

**Categories:**
- PROTEIN, DAIRY, GRAINS, VEGETABLES, FRUITS
- HERBS_SPICES, OILS_FATS, NUTS_SEEDS
- SWEETENERS, BEVERAGES, OTHER

### RecipeIngredient

Through model linking recipes to ingredients with quantities.

**Key Fields:**
- `recipe` (ForeignKey) - Related recipe
- `ingredient` (ForeignKey) - Related ingredient
- `quantity` (FloatField) - Quantity needed
- `unit` (CharField) - Unit of measurement (e.g., "cups", "grams")
- `note` (TextField) - Additional preparation notes
- `original_text` (TextField) - Original ingredient text

### RecipeNutrition

Macro nutrition information for a recipe.

**Key Fields:**
- `recipe` (ForeignKey) - Related recipe
- `calories` (FloatField) - Calories per serving
- `protein` (FloatField) - Protein per serving
- `carbohydrates` (FloatField) - Carbs per serving
- `fat` (FloatField) - Fat per serving
- `fiber` (FloatField) - Fiber per serving
- `sugar` (FloatField) - Sugar per serving
- `sodium` (FloatField) - Sodium per serving
- Additional fields for cholesterol, saturated/mono/polyunsaturated fats

### DietaryRestriction

Dietary restrictions and guidelines (vegetarian, gluten-free, etc.).

**Restriction Types:**
- VEGETARIAN, VEGAN, GLUTEN_FREE, DAIRY_FREE
- NUT_FREE, EGG_FREE, SOY_FREE
- KETO, PALEO, LOW_CARB, LOW_SODIUM
- DIABETIC_FRIENDLY, HALAL, KOSHER, OTHER

### Other Models

- **RecipeVector** - Vector embeddings for semantic search
- **Tag** - Recipe tags for categorization
- **RecipeTag** - Many-to-many relationship between recipes and tags
- **IngredientAllergen** - Allergen information for ingredients
- **RecipeDietaryRestriction** - Many-to-many relationship with confidence scoring

## Services

### Recipe Providers

Recipe providers handle scraping and extracting recipes from external sources.

#### BaseRecipeProvider

Abstract base class for all recipe providers.

**Key Methods:**
- `process_recipe_from_url(url: str) -> Optional[RecipeData]` - Scrape recipe from URL
- `discover_recipe_urls(start_url: str, limit: int = 10) -> List[str]` - Discover recipe URLs
- `validate_scraping_config() -> bool` - Validate provider configuration

#### BudgetBytesScraper

Scraper for Budget Bytes recipes using the `recipe-scrapers` package.

**Features:**
- Extracts recipe title, description, ingredients, instructions
- Parses preparation and cooking times
- Extracts nutritional information
- Identifies dietary restrictions
- Parses ingredients with quantities and units
- Rate limiting to respect website policies

**Example:**
```python
from recipes.services.recipe_providers.budgetbytes import BudgetBytesScraper

scraper = BudgetBytesScraper()

# Scrape a single recipe
recipe_data = scraper.process_recipe_from_url(
    "https://www.budgetbytes.com/thai-curry-fried-rice/"
)

if recipe_data:
    print(f"Title: {recipe_data.title}")
    print(f"Ingredients: {len(recipe_data.ingredients)}")
    print(f"Prep time: {recipe_data.preparation_time} minutes")

# Discover recipe URLs
urls = scraper.discover_recipe_urls(
    "https://www.budgetbytes.com/recipes/",
    limit=20
)
```

#### RecipeData Structure

Standardized data structure returned by all recipe providers:

```python
@dataclass
class RecipeData:
    title: str
    source_url: str
    description: Optional[str] = None
    ingredients: List[IngredientData] = None
    instructions: List[str] = None
    preparation_time: Optional[int] = None
    cooking_time: Optional[int] = None
    servings: Optional[int] = None
    cuisine_type: Optional[str] = None
    image_url: Optional[str] = None
    macros: Optional[MacroNutrition] = None
    tags: List[str] = None
    dietary_restrictions: List[str] = None
```

#### IngredientData Structure

Structured ingredient information:

```python
@dataclass
class IngredientData:
    name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    note: Optional[str] = None
    original_text: Optional[str] = None
```

### Macro Analysis

Nutritional analysis services for recipes and ingredients.

#### Providers

- **API Ninja** - Full API access with comprehensive nutrient data
- **USDA** - Comprehensive nutritional database (planned)

#### MacroAnalysisManager

Manager for coordinating multiple macro analysis providers with fallback support.

**Features:**
- Automatic provider selection based on availability
- Fallback to alternative providers on failure
- Batch analysis support
- Provider confidence scoring

**Example:**
```python
from recipes.services.macro_analysis import (
    analyze_recipe,
    analyze_ingredient,
    MacroAnalysisProvider
)

# Analyze a recipe
result = analyze_recipe(
    recipe_text="2 cups flour, 1 cup sugar, 3 eggs",
    servings=12,
    provider=MacroAnalysisProvider.API_NINJA
)

if result.success:
    print(f"Calories: {result.calories}")
    print(f"Protein: {result.protein}g")
    print(f"Carbs: {result.carbohydrates}g")
    print(f"Fat: {result.fat}g")

# Analyze a single ingredient
ingredient_result = analyze_ingredient(
    ingredient_name="chicken breast",
    quantity=200,  # grams
    provider=MacroAnalysisProvider.API_NINJA
)
```

#### MacroAnalysisResult

Result structure from macro analysis:

```python
@dataclass
class MacroAnalysisResult:
    success: bool
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbohydrates: Optional[float] = None
    fat: Optional[float] = None
    fiber: Optional[float] = None
    sugar: Optional[float] = None
    sodium: Optional[float] = None
    provider: Optional[str] = None
    confidence: Optional[float] = None
    error_message: Optional[str] = None
    raw_data: Optional[Dict] = None
```

#### ApiNinjaMacroAnalyzer

Implementation using API Ninja nutrition API.

**Configuration:**
- Requires `API_NINJA_KEY` environment variable
- Base URL: `https://api.api-ninjas.com/v1/nutrition`
- Rate limit: 60 requests/minute, 1000 requests/hour

**Example:**
```python
from recipes.services.macro_analysis.api_ninja import ApiNinjaMacroAnalyzer

analyzer = ApiNinjaMacroAnalyzer(api_key="your-api-key")

# Check availability
if analyzer.is_available():
    result = analyzer.analyze_recipe(
        recipe_text="1 cup rice, 200g chicken breast",
        servings=2
    )
```

### Cuisine Classification

AI-powered cuisine type detection using Hugging Face models.

#### BaseCuisineClassifier

Abstract base class for cuisine classification.

**Key Methods:**
- `classify_recipe(recipe_text: str) -> CuisineClassification` - Classify cuisine from text
- `classify_batch(recipe_texts: List[str]) -> List[CuisineClassification]` - Batch classification
- `classify_recipe_from_data(title: str, ingredients: List[str]) -> CuisineClassification` - Classify from structured data
- `is_ready() -> bool` - Check if classifier is available

#### CuisineClassification Result

Structured classification result:

```python
@dataclass
class CuisineClassification:
    primary_cuisine: str
    confidence: float  # 0.0 to 1.0
    confidence_level: ConfidenceLevel  # LOW, MEDIUM, HIGH
    alternatives: Optional[List[Dict]] = None
    reasoning: Optional[str] = None
```

**Confidence Levels:**
- **LOW** - < 0.6 confidence
- **MEDIUM** - 0.6 to 0.8 confidence
- **HIGH** - > 0.8 confidence

**Supported Cuisines:**
Italian, Chinese, Mexican, Indian, Japanese, French, Thai, Mediterranean, American, Korean, Vietnamese, Spanish, Greek, Middle Eastern, German, British, Turkish, Moroccan, Lebanese, Peruvian, Brazilian, Caribbean, African, Russian, Scandinavian, Other

**Example:**
```python
from core.services.huggingface.huggingface_api import HuggingFaceAPICuisineClassifier

classifier = HuggingFaceAPICuisineClassifier()

# Classify from recipe text
classification = classifier.classify_recipe(
    "Pasta with tomato sauce, basil, and parmesan cheese"
)

print(f"Cuisine: {classification.primary_cuisine}")
print(f"Confidence: {classification.confidence:.2%}")
print(f"Level: {classification.confidence_level.value}")

# Classify from structured data
classification = classifier.classify_recipe_from_data(
    title="Pad Thai",
    ingredients=["rice noodles", "fish sauce", "tamarind", "peanuts"]
)
```

## Usage Examples

### Complete Recipe Workflow

```python
from recipes.services.recipe_providers.budgetbytes import BudgetBytesScraper
from recipes.services.macro_analysis import analyze_recipe
from core.services.huggingface.huggingface_api import HuggingFaceAPICuisineClassifier
from recipes.models import Recipe, RecipeIngredient, Ingredient

# Initialize services
scraper = BudgetBytesScraper()
macro_analyzer = analyze_recipe
cuisine_classifier = HuggingFaceAPICuisineClassifier()

# Scrape recipe
recipe_data = scraper.process_recipe_from_url(
    "https://www.budgetbytes.com/thai-curry-fried-rice/"
)

if recipe_data:
    # Classify cuisine if not provided
    if not recipe_data.cuisine_type:
        classification = cuisine_classifier.classify_recipe_from_data(
            title=recipe_data.title,
            ingredients=[ing.name for ing in recipe_data.ingredients]
        )
        recipe_data.cuisine_type = classification.primary_cuisine
    
    # Analyze macros if not provided
    if not recipe_data.macros:
        recipe_text = f"{recipe_data.title}. Ingredients: {', '.join([ing.name for ing in recipe_data.ingredients])}"
        macro_result = macro_analyzer(recipe_text, servings=recipe_data.servings)
        if macro_result.success:
            recipe_data.macros = macro_result
    
    # Create recipe in database
    recipe = Recipe.objects.create(
        title=recipe_data.title,
        source_url=recipe_data.source_url,
        source_site="Budget Bytes",
        image_url=recipe_data.image_url,
        instructions=recipe_data.instructions,
        preparation_time=recipe_data.preparation_time,
        cooking_time=recipe_data.cooking_time,
        servings=recipe_data.servings,
        cuisine_type=recipe_data.cuisine_type
    )
    
    # Add ingredients
    for ing_data in recipe_data.ingredients:
        ingredient, created = Ingredient.objects.get_or_create(
            name=ing_data.name,
            defaults={'category': 'OTHER'}
        )
        
        RecipeIngredient.objects.create(
            recipe=recipe,
            ingredient=ingredient,
            quantity=ing_data.quantity or 1.0,
            unit=ing_data.unit or "unit",
            original_text=ing_data.original_text
        )
```

### Batch Recipe Discovery

```python
from recipes.services.recipe_providers.budgetbytes import BudgetBytesScraper

scraper = BudgetBytesScraper()

# Discover recipe URLs
urls = scraper.discover_recipe_urls(
    "https://www.budgetbytes.com/recipes/",
    limit=50
)

print(f"Discovered {len(urls)} recipe URLs")

# Process each recipe
for url in urls:
    recipe_data = scraper.process_recipe_from_url(url)
    if recipe_data:
        # Process recipe_data...
        pass
```

## Management Commands

### budget_bytes_recipe_discovery

Discover and process recipes from Budget Bytes.

**Usage:**
```bash
python manage.py budget_bytes_recipe_discovery
```

**Features:**
- Discovers recipe URLs from Budget Bytes
- Scrapes recipe data
- Classifies cuisine using Hugging Face
- Analyzes macros using API Ninja
- Creates recipes in database (currently in development)

**Note:** This command is currently in development and includes a `quit()` statement for testing purposes.

## Architecture Patterns

### Service Layer Pattern

All business logic is encapsulated in service classes:

```python
# ✅ Correct - Use services
from recipes.services.recipe_providers.budgetbytes import BudgetBytesScraper
scraper = BudgetBytesScraper()
recipe_data = scraper.process_recipe_from_url(url)

# ❌ Incorrect - Direct model manipulation
recipe = Recipe.objects.create(...)  # Should use service layer
```

### Provider Pattern

Services use a provider pattern for extensibility:

```python
# Macro analysis with provider selection
from recipes.services.macro_analysis import MacroAnalysisProvider, analyze_recipe

result = analyze_recipe(
    recipe_text="...",
    provider=MacroAnalysisProvider.API_NINJA  # Explicit provider
)

# Or let manager choose automatically
result = analyze_recipe(recipe_text="...")  # Auto-selects best available
```

### Factory Pattern

Services use factories for creating instances:

```python
from recipes.services.macro_analysis import MacroAnalysisFactory

analyzer = MacroAnalysisFactory.get_analyzer(
    MacroAnalysisProvider.API_NINJA,
    api_key="your-key"
)
```

### Error Handling

All services return structured results with error information:

```python
result = analyze_recipe(recipe_text="...")

if result.success:
    # Use result data
    print(result.calories)
else:
    # Handle error
    print(f"Error: {result.error_message}")
```

## Configuration

### Environment Variables

Required for full functionality:

```bash
# API Ninja (for macro analysis)
API_NINJA_KEY=your-api-ninja-key

# Hugging Face (for cuisine classification)
HUGGINGFACE_API_TOKEN=your-huggingface-token

# USDA (for macro analysis - optional)
USDA_API_KEY=your-usda-api-key
```

### Rate Limiting

Services implement rate limiting to respect external API limits:

- **Budget Bytes Scraper**: 2.0 seconds between requests (configurable)
- **API Ninja**: 60 requests/minute, 1000 requests/hour
- **Hugging Face**: Configurable delay between requests

## Best Practices

1. **Always check service availability** before making requests:
   ```python
   if analyzer.is_available():
       result = analyzer.analyze_recipe(...)
   ```

2. **Handle errors gracefully** - All services return structured results with error information

3. **Use batch operations** when processing multiple items for better performance

4. **Respect rate limits** - Services handle rate limiting automatically, but be mindful of usage

5. **Cache results** when possible - Recipe data doesn't change frequently

6. **Validate input** - Services validate input, but validate before calling services

## Future Enhancements

- Additional recipe providers (AllRecipes, Food Network, etc.)
- USDA macro analysis implementation
- Recipe recommendation engine using embeddings
- Batch processing improvements
- API endpoints for recipe management
- Recipe search and filtering
- Meal planning integration

