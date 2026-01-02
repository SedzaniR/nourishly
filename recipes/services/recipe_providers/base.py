from abc import ABC, abstractmethod
from optparse import Option
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import logging

from recipe_scrapers import SCRAPERS, scrape_me

logger = logging.getLogger(__name__)


@dataclass
class MacroNutrition:
    """
    Structured nutritional macro information for recipes.

    This provides a standardized way to store nutritional data that can be
    extracted from recipe websites or calculated from ingredients.

    Attributes:
        calories: Total calories per serving
        protein: Protein in grams per serving
        carbohydrates: Total carbohydrates in grams per serving
        fat: Total fat in grams per serving
        fiber: Dietary fiber in grams per serving
        sugar: Total sugars in grams per serving
        sodium: Sodium in milligrams per serving
        saturated_fat: Saturated fat in grams per serving
        cholesterol: Cholesterol in milligrams per serving

    Example:
        ```python
        macros = MacroNutrition(
            calories=250,
            protein=15.2,
            carbohydrates=30.5,
            fat=8.1,
            fiber=3.2,
            sodium=580
        )
        ```
    """

    calories: Optional[float] = None
    protein: Optional[float] = None  # grams
    carbohydrates: Optional[float] = None  # grams
    fat: Optional[float] = None  # grams
    fiber: Optional[float] = None  # grams
    sugar: Optional[float] = None  # grams
    sodium: Optional[float] = None  # milligrams
    saturated_fat: Optional[float] = None  # grams
    cholesterol: Optional[float] = None  # milligrams


@dataclass
class IngredientData:
    """
    Structured ingredient data with quantity, unit, and name components.

    This allows for precise ingredient parsing and better recipe analysis.

    Attributes:
        name: The ingredient name (e.g., "tomatoes", "sea salt")
        quantity: Numeric quantity (e.g., 2, 0.25, 1.5)
        unit: Unit of measurement (e.g., "cups", "tsp", "pieces", "lbs")
        notes: Additional preparation notes (e.g., "diced", "room temperature")
        original_text: Original unparsed ingredient text for reference

    Example:
        ```python
        ingredient = IngredientData(
            name="tomatoes",
            quantity=2.0,
            unit="pieces",
            notes="vine ripe",
            original_text="2 tomatoes (vine ripe, $1.28)"
        )
        ```
    """

    name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    notes: Optional[str] = None
    original_text: Optional[str] = None


@dataclass
class RecipeData:
    """
    Standardized recipe data structure for all recipe scrapers.

    This class provides a unified data structure that all recipe scrapers
    must return, ensuring consistency across different recipe websites and sources.

    Attributes:
        title: The name/title of the recipe.
        description: A brief description or summary of the recipe.
        ingredients: List of structured ingredient data or simple strings (for backward compatibility).
        instructions: Step-by-step cooking instructions.
        preparation_time: Preparation time in minutes.
        cooking_time: Cooking time in minutes.
        servings: Number of servings the recipe yields.
        cuisine_type: Type of cuisine (e.g., "Italian", "Mexican", "Asian").
        image_url: URL to an image of the prepared dish.
        source_url: Original URL where the recipe was scraped.
        nutrition: Dictionary containing nutritional information.
        tags: List of tags for categorization (e.g., "vegetarian", "gluten-free").
        dietary_restrictions: List of dietary restrictions or guidelines (e.g., "vegetarian", "gluten-free", "dairy-free").


    Example:
        ```python
        # Using structured ingredients
        recipe = RecipeData(
            title="Chocolate Chip Cookies",
            description="Classic homemade chocolate chip cookies",
            ingredients=[
                IngredientData(name="flour", quantity=2, unit="cups"),
                IngredientData(name="sugar", quantity=1, unit="cup"),
                IngredientData(name="butter", quantity=0.5, unit="cup")
            ],
            instructions=["Mix ingredients", "Bake at 350°F for 12 minutes"],
            prep_time=15,
            cook_time=12,
            servings=24,
            source_url="https://example.com/chocolate-chip-cookies",
            macros=MacroNutrition(
                calories=180,
                protein=2.1,
                carbohydrates=24.5,
                fat=8.2,
                fiber=0.8,
                sugar=12.3,
                sodium=95
            )
        )

        # Or using simple strings (backward compatibility)
        recipe = RecipeData(
            title="Simple Recipe",
            ingredients=["2 cups flour", "1 cup sugar"],
            source_url="https://example.com/simple-recipe"
        )
        ```
    """

    title: str
    source_url: str

    # Recipe content
    description: Optional[str] = None
    ingredients: Optional[Union[List[IngredientData], List[str]]] = None
    instructions: Optional[List[str]] = None
    prep_time: Optional[int] = None  # minutes
    cook_time: Optional[int] = None  # minutes
    servings: Optional[int] = None
    cuisine_type: Optional[str] = None
    difficulty_level: Optional[str] = None
    image_url: Optional[str] = None
    nutrition: Optional[Dict[str, Any]] = None
    macros: Optional[MacroNutrition] = None
    tags: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None

    # Additional metadata
    author: Optional[str] = None
    rating: Optional[float] = None
    provider: Optional[str] = None

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
        if self.dietary_restrictions is None:
            self.dietary_restrictions = []


class BaseRecipeProvider(ABC):
    """Abstract base class for all recipe scrapers.

    This class defines the interface that all recipe scrapers must implement
    to ensure consistent behavior across different recipe websites and data sources.
    Each scraper should inherit from this class and implement the required
    abstract methods.

    The scraper system allows the application to support multiple recipe
    websites (e.g., AllRecipes, Food Network, Food.com) through a unified interface.

    Attributes:
        base_url: Base URL of the website being scraped.
        config: Additional configuration parameters specific to the scraper.
        headers: HTTP headers to use when scraping.
        rate_limit: Delay between requests in seconds.

    Example:
        ```python
        class AllRecipesScraper(BaseRecipeProvider):
            @property
            def provider_name(self) -> str:
                return "AllRecipes"

            def scrape_recipe_from_url(self, url: str) -> Optional[RecipeData]:
                # Implementation here
                pass
        ```
    """

    def __init__(
        self,
        provider_domain: str,
        base_url: Optional[str] = None,
        rate_limit: float = 1.0,
        **kwargs,
    ):
        """Initialize the recipe scraper.

        Args:
            base_url: Base URL of the website to scrape. If None, will be
                determined from the provider implementation.
            rate_limit: Minimum delay between requests in seconds to be respectful
                to the target website.
            **kwargs: Additional configuration parameters that may be needed
                by specific scrapers (e.g., timeout, user_agent, proxies).
        """
        self.base_url = base_url
        self.rate_limit = rate_limit
        self.config = kwargs

        # Default headers for web scraping
        self.headers = {
            "User-Agent": kwargs.get(
                "user_agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

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
    def process_recipe_from_url(self, url: str) -> Optional[RecipeData]:
        """Scrape a recipe from a specific URL.

        This is the primary method for extracting recipe data from a given URL.
        It should handle HTML parsing, data extraction, and return a standardized
        RecipeData object.

        Args:
            url: The URL of the recipe page to scrape.

        Returns:
            A RecipeData object with extracted recipe information, or None
            if the recipe could not be scraped or the URL is invalid.

        Raises:
            ScrapingError: If the scraping fails due to network issues or parsing errors.
            ValidationError: If the URL format is invalid or not supported.

        Example:
            ```python
            recipe = scraper.process_recipe_from_url("https://example.com/chocolate-cake")
            if recipe:
                print(f"Scraped recipe: {recipe.title}")
            ```
        """
        pass

    @abstractmethod
    def discover_recipe_urls(self, start_url: str, limit: int = 10) -> List[str]:
        """Discover recipe URLs from a website or category page.

        This method finds recipe URLs on a given page, such as a category page,
        search results, or homepage. Useful for bulk scraping operations.

        Args:
            start_url: The URL to start discovering recipes from (e.g., category page).
            limit: Maximum number of recipe URLs to return. Defaults to 10.

        Returns:
            A list of recipe URLs found on the page.
            Returns empty list if no recipe URLs found.

        Raises:
            ScrapingError: If the page cannot be accessed or parsed.
            ValidationError: If the start_url is invalid.

        Example:
            ```python
            urls = scraper.discover_recipe_urls(
                "https://example.com/recipes/pasta",
                limit=20
            )
            ```
        """
        pass

    @abstractmethod
    def validate_scraping_config(self) -> bool:
        """Validate scraper configuration and settings.

        This method checks whether the scraper is properly configured
        and ready to scrape recipes from the target website.

        Returns:
            True if the scraper is properly configured and ready to use,
            False otherwise.

        Example:
            ```python
            if scraper.validate_scraping_config():
                recipe = scraper.process_recipe_from_url(url)
            else:
                print("Scraper not properly configured")
            ```
        """
        pass

    @abstractmethod
    def is_site_accessible(self) -> bool:
        """Check if the target website is accessible for scraping.

        This method performs basic accessibility checks such as:
        - Website is responding to requests
        - No blocking/rate limiting detected
        - robots.txt compliance (optional)

        Returns:
            True if the site is accessible and can be scraped,
            False if there are connectivity issues or blocking detected.

        Note:
            This method will make a network request, so it could be slow.
            Consider caching the result for a short period in production.

        Example:
            ```python
            if scraper.is_site_accessible():
                # Safe to scrape
                recipe = scraper.process_recipe_from_url(url)
            else:
                # Handle inaccessible site
                print("Site currently inaccessible")
            ```
        """
        pass

    @abstractmethod
    def _normalize_recipe_data(
        self, raw_data: Dict[str, Any], source_url: str
    ) -> RecipeData:
        """Convert scraped data to standardized RecipeData format.

        This method must be implemented by each scraper to transform
        their extracted HTML data into the standardized RecipeData structure.
        It handles field mapping, data type conversion, and any necessary
        data cleaning or validation.

        Args:
            raw_data: Raw recipe data extracted from HTML or structured data.
                The structure depends on the specific website.
            source_url: The URL where the recipe was scraped from.

        Returns:
            A RecipeData object with normalized and validated data.

        Raises:
            ValueError: If the raw data is missing required fields or
                contains invalid data that cannot be normalized.

        Note:
            This is a protected method intended for internal use by the scraper.
            Each scraper implementation must override this method with
            their specific data transformation logic.

        Example:
            ```python
            def _normalize_recipe_data(self, raw_data: Dict[str, Any], source_url: str) -> RecipeData:
                return RecipeData(
                    title=raw_data.get('title', ''),
                    description=raw_data.get('description'),
                    ingredients=raw_data.get('ingredients', []),
                    instructions=raw_data.get('instructions', []),
                    source_url=source_url,
                    provider=self.provider_name,
                    scraped_at=datetime.now().isoformat()
                )
            ```
        """
        pass

    def _clean_text(self, text: Optional[str]) -> Optional[str]:
        """Clean and normalize text content extracted from HTML.

        This utility method cleans up text content by removing extra whitespace,
        HTML entities, and other common issues found in scraped content.

        Args:
            text: Raw text content to clean.

        Returns:
            Cleaned text content, or None if input was None or empty.
        """
        if not text:
            return None

        import html
        import re

        # Decode HTML entities
        text = html.unescape(text)

        # Remove extra whitespace and normalize line breaks
        text = re.sub(r"\s+", " ", text.strip())

        return text if text else None

    def _extract_rating(self, rating_str: Optional[str]) -> Optional[float]:
        """Extract numeric rating from rating strings.

        Args:
            rating_str: Rating string (e.g., "4.5 stars", "4.5/5", "4.5 out of 5").

        Returns:
            Numeric rating, or None if parsing fails.
        """
        if not rating_str:
            return None

        import re

        # Extract decimal number from rating string
        match = re.search(r"(\d+\.?\d*)", rating_str)
        if match:
            try:
                rating = float(match.group(1))
                # Normalize to 5-star scale if needed
                if rating > 5:
                    rating = rating / 2  # Assume 10-star scale
                return rating
            except ValueError:
                pass

        return None

    def is_site_accessible(self, test_url) -> bool:
        """Check if Budget Bytes website is accessible for scraping.

        Performs a test scrape of a known Budget Bytes recipe to verify
        the site is accessible and responding properly.

        Returns:
            bool: True if the site is accessible and can be scraped, False otherwise.

        Note:
            This method makes an actual HTTP request to Budget Bytes,
            so it may be slow and should be used sparingly.
        """
        try:

            scraper: Any = scrape_me(test_url)

            # If we can get a title, site is accessible
            title: str = scraper.title()
            is_accessible: bool = bool(title)

            logger.info(
                f"Site accessibility check - Is accessible: {is_accessible}, Site: {self.base_url}"
            )

            return is_accessible

        except Exception as accessibility_exception:
            logger.error(
                f"Site accessibility check failed - Error: {str(accessibility_exception)}, Site: {self.base_url}"
            )
            return False

    def validate_scraping_config(self, recipe_provider_scraper_name) -> bool:
        """Validate the scraper configuration.

        Checks if Budget Bytes is supported by the recipe-scrapers library.

        Returns:
            bool: True if Budget Bytes is supported by recipe-scrapers, False otherwise.

        Example:
            >>> scraper = BudgetBytesScraper()
            >>> if scraper.validate_scraping_config():
            ...     print("Ready to scrape Budget Bytes recipes")
        """
        try:
            # Check if Budget Bytes is supported by recipe-scrapers
            supported_sites: List[str] = SCRAPERS.keys()

            is_supported: bool = any(
                recipe_provider_scraper_name in site.lower() for site in supported_sites
            )

            logger.info(
                f"Scraper configuration validated - Is supported: {is_supported}, Total supported sites: {len(supported_sites)}"
            )

            return is_supported

        except Exception as validation_exception:
            logger.error(
                f"Scraper configuration validation failed - Error: {str(validation_exception)}"
            )
            return False
