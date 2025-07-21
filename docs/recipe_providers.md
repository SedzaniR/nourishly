# Recipe Provider System Documentation

## Overview

The Recipe Provider System is a flexible architecture that allows Nourishly to integrate with multiple recipe APIs and data sources through a unified interface. This system ensures consistency across different recipe providers while maintaining the flexibility to support various external APIs.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Core Components](#core-components)
- [Data Structures](#data-structures)
- [Base Classes](#base-classes)
- [Implementation Guide](#implementation-guide)
- [Usage Examples](#usage-examples)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

## Architecture Overview

The provider system follows the **Strategy Pattern** with an abstract base class that defines the interface for all recipe providers. This design allows:

- **Unified Interface**: All providers implement the same methods
- **Extensibility**: Easy to add new recipe sources
- **Maintainability**: Changes to one provider don't affect others
- **Testing**: Mock providers can be easily created for testing

```
┌─────────────────────────────────────────┐
│           RecipeService                 │
│    (Orchestrates multiple providers)    │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│         BaseRecipeProvider              │
│         (Abstract Interface)            │
└─────────────────┬───────────────────────┘
                  │
         ┌────────┼────────┐
         ▼        ▼        ▼
┌─────────────┐ ┌──────────┐ ┌─────────────┐
│Spoonacular  │ │  Edamam  │ │   Custom    │
│  Provider   │ │ Provider │ │  Provider   │
└─────────────┘ └──────────┘ └─────────────┘
```

## Core Components

### 1. RecipeData Class
The standardized data structure that all providers must return.

### 2. BaseRecipeProvider Class
Abstract base class defining the interface for all recipe providers.

### 3. Concrete Providers
Specific implementations for different recipe APIs (Spoonacular, Edamam, etc.).

## Data Structures

### RecipeData

Standardized recipe data structure for all recipe providers.

This class provides a unified data structure that all recipe providers must return, ensuring consistency across different recipe APIs and sources.

**Attributes:**

| Field | Type | Description |
|-------|------|-------------|
| `title` | `str` | The name/title of the recipe (required) |
| `description` | `Optional[str]` | A brief description or summary of the recipe |
| `ingredients` | `Optional[List[str]]` | List of ingredients with quantities and descriptions |
| `instructions` | `Optional[List[str]]` | Step-by-step cooking instructions |
| `prep_time` | `Optional[int]` | Preparation time in minutes |
| `cook_time` | `Optional[int]` | Cooking time in minutes |
| `servings` | `Optional[int]` | Number of servings the recipe yields |
| `cuisine_type` | `Optional[str]` | Type of cuisine (e.g., "Italian", "Mexican", "Asian") |
| `difficulty_level` | `Optional[str]` | Difficulty rating (e.g., "easy", "medium", "hard") |
| `image_url` | `Optional[str]` | URL to an image of the prepared dish |
| `source_url` | `Optional[str]` | Original URL where the recipe was found |
| `nutrition` | `Optional[Dict[str, Any]]` | Dictionary containing nutritional information |
| `tags` | `Optional[List[str]]` | List of tags for categorization (e.g., "vegetarian", "gluten-free") |
| `provider` | `Optional[str]` | Name of the provider that supplied this recipe |
| `external_id` | `Optional[str]` | Provider-specific unique identifier for the recipe |

**Example:**

```python
recipe = RecipeData(
    title="Chocolate Chip Cookies",
    description="Classic homemade chocolate chip cookies",
    ingredients=["2 cups flour", "1 cup sugar", "1/2 cup butter"],
    instructions=["Mix ingredients", "Bake at 350°F for 12 minutes"],
    prep_time=15,
    cook_time=12,
    servings=24,
    cuisine_type="American",
    difficulty_level="easy"
)
```

**Automatic Initialization:**

The `__post_init__` method ensures that list fields (`ingredients`, `instructions`, `tags`) are never `None`, making them safer to work with throughout the application.

## Base Classes

### BaseRecipeProvider

Abstract base class for all recipe providers.

This class defines the interface that all recipe providers must implement to ensure consistent behavior across different recipe APIs and data sources. Each provider should inherit from this class and implement the required abstract methods.

The provider system allows the application to support multiple recipe sources (e.g., Spoonacular, Edamam, custom APIs) through a unified interface.

**Attributes:**

- `api_key`: API key for the provider service (if required)
- `config`: Additional configuration parameters specific to the provider

## Required Abstract Methods

All concrete provider implementations **must** implement the following abstract methods:

### 1. provider_name (property)

```python
@property
@abstractmethod
def provider_name(self) -> str:
```

Returns the name of this provider. This should be a unique identifier for the provider that can be used for logging, debugging, and provider selection.

**Returns:** A string representing the provider name (e.g., "spoonacular", "edamam").

### 2. search_recipes

```python
@abstractmethod
def search_recipes(
    self, 
    query: str, 
    limit: int = 10,
    filters: Optional[Dict[str, Any]] = None
) -> List[RecipeData]:
```

Search for recipes using the provider's API. This method should search the provider's database for recipes matching the given query and return a list of standardized RecipeData objects.

**Parameters:**

- `query`: Search term or phrase to find recipes (e.g., "chicken pasta")
- `limit`: Maximum number of results to return. Defaults to 10
- `filters`: Additional search filters such as:
  - `cuisine`: str (e.g., "italian", "mexican")
  - `diet`: str (e.g., "vegetarian", "vegan", "gluten-free")
  - `max_prep_time`: int (maximum preparation time in minutes)
  - `max_cook_time`: int (maximum cooking time in minutes)
  - `difficulty`: str (e.g., "easy", "medium", "hard")

**Returns:** A list of RecipeData objects matching the search criteria. Returns empty list if no recipes found.

**Raises:**
- `ProviderError`: If the API request fails or returns an error
- `ValidationError`: If the query or filters are invalid

**Example:**

```python
recipes = provider.search_recipes(
    query="chicken pasta",
    limit=5,
    filters={"cuisine": "italian", "diet": "vegetarian"}
)
```

### 3. get_recipe_by_id

```python
@abstractmethod
def get_recipe_by_id(self, recipe_id: str) -> Optional[RecipeData]:
```

Get a specific recipe by its provider-specific ID. This method retrieves detailed information for a specific recipe using the provider's unique identifier.

**Parameters:**

- `recipe_id`: Provider-specific recipe identifier. The format depends on the provider (e.g., numeric ID, UUID, slug)

**Returns:** A RecipeData object with detailed recipe information, or None if the recipe is not found or no longer available.

**Raises:**
- `ProviderError`: If the API request fails or returns an error
- `ValidationError`: If the recipe_id format is invalid

**Example:**

```python
recipe = provider.get_recipe_by_id("12345")
if recipe:
    print(f"Found recipe: {recipe.title}")
```

### 4. _normalize_recipe_data

```python
@abstractmethod
def _normalize_recipe_data(self, raw_data: Dict[str, Any]) -> RecipeData:
```

Convert provider-specific data to standardized RecipeData format. This method must be implemented by each provider to transform their API response format into the standardized RecipeData structure. It handles field mapping, data type conversion, and any necessary data cleaning or validation.

**Parameters:**

- `raw_data`: Raw recipe data as returned by the provider's API. The structure depends on the specific provider

**Returns:** A RecipeData object with normalized and validated data.

**Raises:**
- `ValueError`: If the raw data is missing required fields or contains invalid data that cannot be normalized

**Note:** This is a protected method intended for internal use by the provider. Each provider implementation must override this method with their specific data transformation logic.

**Example:**

```python
def _normalize_recipe_data(self, raw_data: Dict[str, Any]) -> RecipeData:
    return RecipeData(
        title=raw_data.get('title', ''),
        description=raw_data.get('summary'),
        ingredients=raw_data.get('extendedIngredients', []),
        # ... other field mappings
        provider=self.provider_name
    )
```

## Optional Methods (With Default Implementations)

### validate_config

```python
def validate_config(self) -> bool:
```

Validate provider configuration including API keys and settings. This method checks whether the provider is properly configured and ready to make API requests. It should verify API keys, required configuration parameters, and any other prerequisites.

**Returns:** True if the provider is properly configured and ready to use, False otherwise.

**Example:**

```python
if provider.validate_config():
    recipes = provider.search_recipes("pasta")
else:
    print("Provider not properly configured")
```

### is_available

```python
def is_available(self) -> bool:
```

Check if the provider is currently available and functional. This method performs a health check to ensure the provider's API is accessible and responding. It typically checks configuration and may perform a simple test request.

**Returns:** True if the provider is available and can handle requests, False if there are connectivity issues or the service is down.

**Note:** This method may make a network request, so it could be slow. Consider caching the result for a short period in production.

**Example:**

```python
if provider.is_available():
    # Safe to make requests
    recipes = provider.search_recipes("dinner")
else:
    # Use fallback provider or show error
    print("Provider currently unavailable")
```

## Implementation Guide

### Creating a New Provider

To create a new recipe provider, follow these steps:

1. **Create a new class** that inherits from `BaseRecipeProvider`
2. **Implement all abstract methods**
3. **Override optional methods** if needed
4. **Test your implementation**

**Example Implementation:**

```python
from typing import List, Dict, Any, Optional
from .base import BaseRecipeProvider, RecipeData

class MyRecipeProvider(BaseRecipeProvider):
    """Custom recipe provider implementation."""
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key, **kwargs)
        self.base_url = kwargs.get('base_url', 'https://api.example.com')
    
    @property
    def provider_name(self) -> str:
        return "my_provider"
    
    def search_recipes(
        self, 
        query: str, 
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RecipeData]:
        """Search for recipes using the provider's API."""
        # Make API request
        # Process response
        # Return normalized data
        pass
    
    def get_recipe_by_id(self, recipe_id: str) -> Optional[RecipeData]:
        """Get a specific recipe by ID."""
        # Make API request
        # Process response
        # Return normalized data
        pass
    
    def _normalize_recipe_data(self, raw_data: Dict[str, Any]) -> RecipeData:
        """Convert API response to RecipeData format."""
        return RecipeData(
            title=raw_data.get('name', ''),
            description=raw_data.get('description'),
            ingredients=raw_data.get('ingredients', []),
            instructions=raw_data.get('steps', []),
            prep_time=raw_data.get('prep_minutes'),
            cook_time=raw_data.get('cook_minutes'),
            servings=raw_data.get('serves'),
            cuisine_type=raw_data.get('cuisine'),
            difficulty_level=raw_data.get('difficulty'),
            image_url=raw_data.get('image'),
            source_url=raw_data.get('url'),
            nutrition=raw_data.get('nutrition_facts', {}),
            tags=raw_data.get('tags', []),
            provider=self.provider_name,
            external_id=str(raw_data.get('id'))
        )
    
    def validate_config(self) -> bool:
        """Validate provider configuration."""
        return self.api_key is not None and len(self.api_key) > 0
```

## Usage Examples

### Basic Usage

```python
# Initialize provider
provider = MyRecipeProvider(api_key="your-api-key")

# Check if available
if provider.is_available():
    # Search for recipes
    recipes = provider.search_recipes("pasta", limit=5)
    
    # Get specific recipe
    recipe = provider.get_recipe_by_id("123")
    
    if recipe:
        print(f"Recipe: {recipe.title}")
        print(f"Prep time: {recipe.prep_time} minutes")
```

### Advanced Search with Filters

```python
# Search with dietary filters
vegetarian_recipes = provider.search_recipes(
    query="dinner",
    limit=10,
    filters={
        "diet": "vegetarian",
        "cuisine": "italian",
        "max_prep_time": 30,
        "difficulty": "easy"
    }
)
```

### Error Handling

```python
try:
    recipes = provider.search_recipes("chicken")
except ProviderError as e:
    print(f"Provider error: {e}")
except ValidationError as e:
    print(f"Validation error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Error Handling

### Common Exceptions

- **`ProviderError`**: Raised when API requests fail or return errors
- **`ValidationError`**: Raised when input parameters are invalid
- **`ValueError`**: Raised when data normalization fails

### Best Practices

1. **Always check availability** before making requests
2. **Handle exceptions gracefully** with fallback behavior
3. **Validate inputs** before processing
4. **Log errors** for debugging and monitoring

## Best Practices

### Provider Implementation

1. **Follow the interface contract** exactly
2. **Handle rate limiting** appropriately
3. **Cache responses** when possible
4. **Validate and sanitize** all input data
5. **Provide meaningful error messages**
6. **Log important events** for debugging

### Data Normalization

1. **Handle missing fields** gracefully
2. **Validate data types** during conversion
3. **Sanitize text content** (remove HTML, etc.)
4. **Normalize units** (convert to consistent formats)
5. **Set provider name** in all returned data

### Configuration

1. **Use environment variables** for API keys
2. **Implement proper validation** for configuration
3. **Provide sensible defaults** where possible
4. **Document configuration options** clearly

### Testing

1. **Mock external API calls** in tests
2. **Test error conditions** thoroughly
3. **Validate data normalization** with real examples
4. **Test configuration validation**

## Conclusion

The Recipe Provider System provides a robust, extensible architecture for integrating multiple recipe sources into Nourishly. By following the abstract interface and implementing the required methods, new providers can be easily added while maintaining consistency across the application.

For more specific implementation examples, check the existing providers in the `recipes/services/recipe_providers/` directory. 