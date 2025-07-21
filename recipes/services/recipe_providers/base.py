from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class RecipeData:
    
    """
    Standardized recipe data structure for all recipe providers.
    
    This class provides a unified data structure that all recipe providers
    must return, ensuring consistency across different recipe APIs and sources.
    
    Attributes:
        title: The name/title of the recipe.
        description: A brief description or summary of the recipe.
        ingredients: List of ingredients with quantities and descriptions.
        instructions: Step-by-step cooking instructions.
        prep_time: Preparation time in minutes.
        cook_time: Cooking time in minutes.
        servings: Number of servings the recipe yields.
        cuisine_type: Type of cuisine (e.g., "Italian", "Mexican", "Asian").
        difficulty_level: Difficulty rating (e.g., "easy", "medium", "hard").
        image_url: URL to an image of the prepared dish.
        source_url: Original URL where the recipe was found.
        nutrition: Dictionary containing nutritional information.
        tags: List of tags for categorization (e.g., "vegetarian", "gluten-free").
        provider: Name of the provider that supplied this recipe.
        external_id: Provider-specific unique identifier for the recipe.
        
    Example:
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
    """
    title: str
    description: Optional[str] = None
    ingredients: Optional[List[str]] = None
    instructions: Optional[List[str]] = None
    prep_time: Optional[int] = None  # minutes
    cook_time: Optional[int] = None  # minutes
    servings: Optional[int] = None
    cuisine_type: Optional[str] = None
    difficulty_level: Optional[str] = None
    image_url: Optional[str] = None
    source_url: Optional[str] = None
    nutrition: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    provider: Optional[str] = None
    external_id: Optional[str] = None

    def __post_init__(self):
        """Initialize empty lists for optional list fields if None.
        
        This ensures that list fields are never None, making them safer
        to work with throughout the application.
        """
        if self.ingredients is None:
            self.ingredients = []
        if self.instructions is None:
            self.instructions = []
        if self.tags is None:
            self.tags = []


class BaseRecipeProvider(ABC):
    """Abstract base class for all recipe providers.
    
    This class defines the interface that all recipe providers must implement
    to ensure consistent behavior across different recipe APIs and data sources.
    Each provider should inherit from this class and implement the required
    abstract methods.
    
    The provider system allows the application to support multiple recipe
    sources (e.g., Spoonacular, Edamam, custom APIs) through a unified interface.
    
    Attributes:
        api_key: API key for the provider service (if required).
        config: Additional configuration parameters specific to the provider.
        
    Example:
        ```python
        class MyRecipeProvider(BaseRecipeProvider):
            @property
            def provider_name(self) -> str:
                return "MyProvider"
                
            def search_recipes(self, query: str, limit: int = 10, 
                             filters: Optional[Dict[str, Any]] = None) -> List[RecipeData]:
                # Implementation here
                pass
        ```
    """
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize the recipe provider.
        
        Args:
            api_key: API key for the provider service. Some providers may not
                require an API key.
            **kwargs: Additional configuration parameters that may be needed
                by specific providers (e.g., base_url, timeout, rate_limits).
        """
        self.api_key = api_key
        self.config = kwargs
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider.
        
        This should be a unique identifier for the provider that can be
        used for logging, debugging, and provider selection.
        
        Returns:
            A string representing the provider name (e.g., "spoonacular", "edamam").
        """
        pass
    
    @abstractmethod
    def search_recipes(
        self, 
        query: str, 
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RecipeData]:
        """Search for recipes using the provider's API.
        
        This method should search the provider's database for recipes matching
        the given query and return a list of standardized RecipeData objects.
        
        Args:
            query: Search term or phrase to find recipes (e.g., "chicken pasta").
            limit: Maximum number of results to return. Defaults to 10.
            filters: Additional search filters such as:
                - cuisine: str (e.g., "italian", "mexican")
                - diet: str (e.g., "vegetarian", "vegan", "gluten-free")
                - max_prep_time: int (maximum preparation time in minutes)
                - max_cook_time: int (maximum cooking time in minutes)
                - difficulty: str (e.g., "easy", "medium", "hard")
                
        Returns:
            A list of RecipeData objects matching the search criteria.
            Returns empty list if no recipes found.
            
        Raises:
            ProviderError: If the API request fails or returns an error.
            ValidationError: If the query or filters are invalid.
            
        Example:
            ```python
            recipes = provider.search_recipes(
                query="chicken pasta",
                limit=5,
                filters={"cuisine": "italian", "diet": "vegetarian"}
            )
            ```
        """
        pass
    
    @abstractmethod
    def get_recipe_by_id(self, recipe_id: str) -> Optional[RecipeData]:
        """Get a specific recipe by its provider-specific ID.
        
        This method retrieves detailed information for a specific recipe
        using the provider's unique identifier.
        
        Args:
            recipe_id: Provider-specific recipe identifier. The format
                depends on the provider (e.g., numeric ID, UUID, slug).
                
        Returns:
            A RecipeData object with detailed recipe information, or None
            if the recipe is not found or no longer available.
            
        Raises:
            ProviderError: If the API request fails or returns an error.
            ValidationError: If the recipe_id format is invalid.
            
        Example:
            ```python
            recipe = provider.get_recipe_by_id("12345")
            if recipe:
                print(f"Found recipe: {recipe.title}")
            ```
        """
        pass
    
    def validate_config(self) -> bool:
        """Validate provider configuration including API keys and settings.
        
        This method checks whether the provider is properly configured
        and ready to make API requests. It should verify API keys,
        required configuration parameters, and any other prerequisites.
        
        Returns:
            True if the provider is properly configured and ready to use,
            False otherwise.
            
        Example:
            ```python
            if provider.validate_config():
                recipes = provider.search_recipes("pasta")
            else:
                print("Provider not properly configured")
            ```
        """
        return True
    
    def is_api_available(self) -> bool:
        """Check if the provider is currently available and functional.
        
        This method performs a health check to ensure the provider's
        API is accessible and responding. The default implementation
        only checks configuration, but providers can override this
        to perform more sophisticated availability checks.
        
        Returns:
            True if the provider is available and can handle requests,
            False if there are connectivity issues or the service is down.
            
        Note:
            This method may make a network request, so it could be slow.
            Consider caching the result for a short period in production.
            
        Example:
            ```python
            if provider.is_api_available():
                # Safe to make requests
                recipes = provider.search_recipes("dinner")
            else:
                # Use fallback provider or show error
                print("Provider currently unavailable")
            ```
            
        Override Example:
            ```python
            def is_api_available(self) -> bool:
                # Check config first
                if not self.validate_config():
                    return False
                
                # Then check API health
                try:
                    response = requests.get(f"{self.base_url}/health")
                    return response.status_code == 200
                except requests.RequestException:
                    return False
            ```
        """
        return self.validate_config()
    
    @abstractmethod
    def _normalize_recipe_data(self, raw_data: Dict[str, Any]) -> RecipeData:
        """Convert provider-specific data to standardized RecipeData format.
        
        This method must be implemented by each provider to transform
        their API response format into the standardized RecipeData structure.
        It handles field mapping, data type conversion, and any necessary
        data cleaning or validation.
        
        Args:
            raw_data: Raw recipe data as returned by the provider's API.
                The structure depends on the specific provider.
                
        Returns:
            A RecipeData object with normalized and validated data.
            
        Raises:
            ValueError: If the raw data is missing required fields or
                contains invalid data that cannot be normalized.
            
        Note:
            This is a protected method intended for internal use by the provider.
            Each provider implementation must override this method with
            their specific data transformation logic.
            
        Example:
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
        """
        pass
