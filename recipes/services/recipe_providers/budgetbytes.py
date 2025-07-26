import time
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable, Tuple, Union, Match
from urllib.parse import ParseResult, urlparse

from recipe_scrapers import scrape_me, SCRAPERS

from recipes.services.recipe_providers import constants
from .base import BaseRecipeProvider, RecipeData, IngredientData, MacroNutrition
from core.logger import log_info, log_error, log_debug
from recipes.utils import extract_numeric_value_from_string


class BudgetBytesScraper(BaseRecipeProvider):
    """
    Budget Bytes recipe scraper using the recipe-scrapers package.

    Simple wrapper around recipe-scrapers for Budget Bytes recipes.
    """

    BASE_URL: str = "https://www.budgetbytes.com"
    DEFAULT_RATE_LIMIT: float = 2.0

    def __init__(self, **kwargs):
        """Initialize the Budget Bytes scraper.

        Args:
            **kwargs: Additional configuration options including:
                - rate_limit (float): Delay between requests in seconds (default: 2.0)
                - timeout (int): Request timeout in seconds
                - user_agent (str): Custom user agent string
        """
        super().__init__(
            base_url=self.BASE_URL,
            rate_limit=kwargs.get("rate_limit", self.DEFAULT_RATE_LIMIT),
            **kwargs,
        )
        log_info("Budget Bytes scraper initialized", base_url=self.base_url)

    @property
    def provider_name(self) -> str:
        """Return the provider name.

        Returns:
            str: The provider identifier "BudgetBytes"
        """
        return "BudgetBytes"

    def scrape_recipe_from_url(self, url: str) -> Optional[RecipeData]:
        """Scrape a recipe from a Budget Bytes URL using recipe-scrapers.

        Args:
            url (str): The Budget Bytes recipe URL to scrape.

        Returns:
            Optional[RecipeData]: Recipe data object with extracted information,
                or None if scraping failed.

        Raises:
            None: All exceptions are caught and logged, method returns None on failure.

        Example:
            >>> scraper = BudgetBytesScraper()
            >>> recipe = scraper.scrape_recipe_from_url(
            ...     "https://www.budgetbytes.com/thai-curry-fried-rice/"
            ... )
            >>> print(recipe.title if recipe else "Failed to scrape")
        """

        if not self._is_budget_bytes_url(url):
            log_error("Invalid Budget Bytes URL", url=url, provider=self.provider_name)
            return None

        log_info("Starting recipe scrape", url=url, provider=self.provider_name)
        time.sleep(self.rate_limit)

        try:
            scraper: Any = scrape_me(url)
            recipe_data: RecipeData = self._normalize_recipe_data(scraper, url)
            log_info(
                "Recipe scraped successfully",
                url=url,
                title=recipe_data.title,
                provider=self.provider_name,
            )

            return recipe_data

        except Exception as scraping_exception:
            log_error(
                "Failed to scrape recipe",
                url=url,
                error=str(scraping_exception),
                provider=self.provider_name,
            )
            return None

    def discover_recipe_urls(self, start_url: str, limit: int = 10) -> List[str]:
        """Discover recipe URLs from Budget Bytes category pages.

        Args:
            start_url (str): The Budget Bytes category or search URL to start from.
            limit (int, optional): Maximum number of recipe URLs to return. Defaults to 10.

        Returns:
            List[str]: List of discovered recipe URLs. Currently returns empty list.

        Note:
            This is a basic implementation. For production use, consider implementing
            proper pagination and sitemap parsing.

        Todo:
            Implement actual URL discovery using sitemap or page crawling.
        """
        log_info("URL discovery not fully implemented", start_url=start_url)
        # For now, return empty list - focus on single recipe scraping
        return []

    def validate_scraping_config(self) -> bool:
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
                "budgetbytes" in site.lower() for site in supported_sites
            )

            log_info(
                "Scraper configuration validated",
                is_supported=is_supported,
                total_supported_sites=len(supported_sites),
            )

            return is_supported

        except Exception as validation_exception:
            log_error(
                "Scraper configuration validation failed",
                error=str(validation_exception),
            )
            return False

    def is_site_accessible(self) -> bool:
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
            # Simple test scrape to check accessibility
            TEST_URL: str = f"{self.base_url}/recipe/basic-meatballs/"
            scraper: Any = scrape_me(TEST_URL)

            # If we can get a title, site is accessible
            title: str = scraper.title()
            is_accessible: bool = bool(title)

            log_info(
                "Site accessibility check",
                is_accessible=is_accessible,
                site=self.base_url,
            )

            return is_accessible

        except Exception as accessibility_exception:
            log_error(
                "Site accessibility check failed",
                error=str(accessibility_exception),
                site=self.base_url,
            )
            return False

    def extract_structured_data(self, html_content: str) -> Optional[Dict[str, Any]]:
        """Extract structured data from HTML content.

        Args:
            html_content (str): Raw HTML content of a recipe page.

        Returns:
            Optional[Dict[str, Any]]: Always returns None since recipe-scrapers
                handles structured data extraction internally.

        Note:
            This method is part of the BaseRecipeProvider interface but is not
            needed for this implementation since recipe-scrapers handles
            structured data extraction automatically.
        """
        # recipe-scrapers handles this automatically
        log_info("Structured data extraction handled by recipe-scrapers")
        return None

    def _normalize_recipe_data(self, scraper, source_url: str) -> RecipeData:
        """Convert recipe-scrapers data to standardized RecipeData format.

        Args:
            scraper: Recipe scraper object from recipe-scrapers library.
            source_url (str): The original URL where the recipe was scraped from.

        Returns:
            RecipeData: Normalized recipe data object with all available fields populated.

        Note:
            If normalization fails, returns a minimal RecipeData object with
            scrape_success=False and error details in scrape_errors.
        """
        try:
            # Extract all data using recipe-scrapers methods
            recipe_title: str = self._safe_extract(scraper.title, "Unknown Recipe")

            # Extract and parse ingredients into structured data
            raw_ingredient_list: List[str] = self._safe_extract(scraper.ingredients, [])
            structured_ingredients: List[IngredientData] = self._parse_ingredients(
                raw_ingredient_list
            )

            log_debug(
                "Ingredient parsing completed",
                raw_count=len(raw_ingredient_list),
                parsed_count=len(structured_ingredients),
                sample_raw=raw_ingredient_list[:2] if raw_ingredient_list else [],
                sample_parsed=(
                    [
                        f"{ingredient.quantity or ''} {ingredient.unit or ''} {ingredient.name}".strip()
                        for ingredient in structured_ingredients[:2]
                    ]
                    if structured_ingredients
                    else []
                ),
            )

            # Create RecipeData object
            recipe_data: RecipeData = RecipeData(
                title=recipe_title,
                source_url=source_url,
                # Recipe content - let recipe-scrapers handle the extraction
                description=self._safe_extract(scraper.description),
                ingredients=structured_ingredients,
                instructions=self._safe_extract(scraper.instructions_list, []),
                prep_time=self._parse_time_duration(
                    self._safe_extract(scraper.prep_time)
                ),
                cook_time=self._parse_time_duration(
                    self._safe_extract(scraper.cook_time)
                ),
                servings=self._safe_extract(scraper.yields),
                cuisine_type=self._safe_extract(scraper.cuisine),
                image_url=self._safe_extract(scraper.image),
                # Additional metadata
                author=self._safe_extract(scraper.author),
                rating=self._safe_extract(scraper.ratings),
                # Extract tags from category
                tags=self._extract_tags(scraper),
                # Store raw nutrition data from recipe-scrapers
                nutrition=self._safe_extract(scraper.nutrients),
                # Extract structured macros
                macros=self._extract_macros(scraper),
            )

            log_info(
                "Recipe data normalized successfully",
                title=recipe_data.title,
                ingredients_count=len(recipe_data.ingredients or []),
                instructions_count=len(recipe_data.instructions or []),
                has_structured_ingredients=True,
            )

            return recipe_data

        except Exception as normalization_exception:

            log_error(
                "Failed to normalize recipe data",
                error=str(normalization_exception),
                source_url=source_url,
            )

            # Return minimal RecipeData object on error
            return RecipeData(
                title="Unknown Recipe",
                source_url=source_url,
                provider=self.provider_name,
                scraped_at=datetime.now().isoformat(),
                scrape_success=False,
                scrape_errors=[str(normalization_exception)],
            )

    def _safe_extract(
        self, method: Callable[[], Any], default_value: Any = None
    ) -> Any:
        """Safely extract data from recipe-scrapers methods.

        Args:
            method (Callable[[], Any]): Recipe-scrapers method to call (e.g., scraper.title).
            default_value (Any): Default value to return if extraction fails or returns None.

        Returns:
            Any: Extracted data from the method call, or default value on failure.

        Note:
            This wrapper prevents exceptions from recipe-scrapers methods
            from breaking the entire scraping process.
        """
        try:
            extraction_result: Any = method()
            return extraction_result if extraction_result is not None else default_value
        except Exception:
            return default_value

    def _parse_time_duration(self, duration: Any) -> Optional[int]:
        """Parse time duration to minutes.

        Args:
            duration (Any): Time duration from recipe-scrapers (timedelta object or string).

        Returns:
            Optional[int]: Duration in minutes, or None if parsing fails.

        Note:
            recipe-scrapers typically returns timedelta objects, but this method
            also handles string fallback for compatibility.
        """
        if not duration:
            return None

        # recipe-scrapers returns timedelta objects
        if hasattr(duration, "total_seconds"):
            return int(duration.total_seconds() / 60)

        # Fallback to string parsing
        return self._parse_time_string(str(duration))

    def _parse_ingredients(self, raw_ingredients: List[str]) -> List[IngredientData]:
        """Parse Budget Bytes ingredients into structured IngredientData objects.

        Budget Bytes ingredients include cost information and follow patterns like:
        '2 tomatoes (vine ripe, $1.28)' -> IngredientData(name="tomatoes", quantity=2, notes="vine ripe")
        '¼ tsp sea salt ($0.01)' -> IngredientData(name="sea salt", quantity=0.25, unit="tsp")

        Args:
            raw_ingredients (List[str]): Raw ingredient list from recipe-scrapers.

        Returns:
            List[IngredientData]: Structured ingredient data with quantity, unit, and name parsed.

        Example:
            >>> raw = ['2 tomatoes (vine ripe, $1.28)', '¼ tsp salt ($0.01)']
            >>> parsed = scraper._parse_ingredients(raw)
            >>> print(f"{parsed[0].quantity} {parsed[0].unit or 'pieces'} {parsed[0].name}")
            2.0 pieces tomatoes
        """
        import re
        from fractions import Fraction

        parsed_ingredients = []

        for ingredient_text in raw_ingredients:
            if not ingredient_text:
                continue

            # Clean cost information - remove any content containing $ sign
            cleaned = self._remove_cost_info(ingredient_text)

            if not cleaned:
                continue

            # Use the same cleaned text for original reference
            clean_original = cleaned

            # Parse quantity, unit, and ingredient name
            ingredient_data = self._parse_ingredient_components(cleaned, clean_original)
            if ingredient_data:
                parsed_ingredients.append(ingredient_data)

        return parsed_ingredients

    def _remove_cost_info(self, text: str) -> str:
        """Remove cost information from ingredient text.

        Removes any parenthetical content that contains a dollar sign,
        and cleans up the resulting text formatting.

        Args:
            text (str): Original ingredient text with potential cost info.

        Returns:
            str: Cleaned text with cost information removed.

        Examples:
            >>> scraper._remove_cost_info("2 tomatoes (vine ripe, $1.28)")
            "2 tomatoes (vine ripe)"
            >>> scraper._remove_cost_info("¼ tsp salt ($0.01)")
            "¼ tsp salt"
            >>> scraper._remove_cost_info("butter (room temperature, $1.98*)")
            "butter (room temperature)"
        """
        import re

        # Remove any parenthetical content that contains a dollar sign
        # This handles cases like:
        # - ($1.28) -> removed entirely
        # - (vine ripe, $1.28) -> becomes (vine ripe)
        # - (room temperature, $1.98*) -> becomes (room temperature)

        def clean_parentheses(regex_match: Match[str]) -> str:
            parenthetical_content = regex_match.group(1)  # Content inside parentheses
            if "$" in parenthetical_content:
                # Remove the cost part (anything from $ to end or to comma)
                # Split by comma and keep parts that don't contain $
                content_parts = [
                    part.strip() for part in parenthetical_content.split(",")
                ]
                non_cost_parts = [part for part in content_parts if "$" not in part]

                if non_cost_parts:
                    return f"({', '.join(non_cost_parts)})"
                else:
                    return ""  # Remove entire parentheses if only cost info
            else:
                return regex_match.group(0)  # Keep original if no $ sign

        # Find and clean all parenthetical content
        cleaned_text = re.sub(r"\(([^)]*)\)", clean_parentheses, text)

        # Clean up any resulting formatting issues
        cleaned_text = re.sub(r"\s*,\s*\)", ")", cleaned_text)  # Fix ", )" -> ")"
        cleaned_text = re.sub(r"\(\s*\)", "", cleaned_text)  # Remove empty "()"
        cleaned_text = re.sub(r"\s+", " ", cleaned_text.strip())  # Normalize whitespace
        cleaned_text = cleaned_text.rstrip(",").strip()  # Remove trailing commas

        return cleaned_text

    def _parse_ingredient_components(
        self, cleaned_text: str, clean_original_text: str
    ) -> Optional[IngredientData]:
        """Parse a single ingredient into quantity, unit, name, and notes.

        Args:
            cleaned_text (str): Cleaned ingredient text without cost info.
            clean_original_text (str): Original ingredient text with cost info removed.

        Returns:
            Optional[IngredientData]: Parsed ingredient data or None if parsing fails.
        """
        import re
        from fractions import Fraction

        try:
            # Common measurement units (plural forms first for proper regex matching)

            # Pattern to match quantity (including fractions) and unit
            quantity_pattern = r"^(\d+(?:\.\d+)?(?:\s*/\s*\d+)?|\d*\s*[¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞]|\d+\s+\d+/\d+)\s*"
            unit_pattern = (
                r"("
                + "|".join(re.escape(unit) for unit in constants.COMMON_UNITS)
                + r")\s*"
            )

            # Try to match quantity and unit at the beginning
            quantity_and_unit_match = re.match(
                quantity_pattern + unit_pattern, cleaned_text, re.IGNORECASE
            )

            if quantity_and_unit_match:
                quantity_string = quantity_and_unit_match.group(1).strip()
                unit_string = quantity_and_unit_match.group(2).strip()
                remaining_text = cleaned_text[quantity_and_unit_match.end() :].strip()
            else:
                # Try quantity without unit
                quantity_only_match = re.match(quantity_pattern, cleaned_text)
                if quantity_only_match:
                    quantity_string = quantity_only_match.group(1).strip()
                    unit_string = None
                    remaining_text = cleaned_text[quantity_only_match.end() :].strip()
                else:
                    # No quantity found, treat as whole ingredient
                    quantity_string = None
                    unit_string = None
                    remaining_text = cleaned_text

            # Parse quantity
            parsed_quantity = None
            if quantity_string:
                parsed_quantity = self._parse_quantity(quantity_string)

            # Extract ingredient name and notes
            ingredient_name, preparation_notes = self._extract_name_and_notes(
                remaining_text
            )

            return IngredientData(
                name=ingredient_name or remaining_text or "unknown ingredient",
                quantity=parsed_quantity,
                unit=unit_string,
                notes=preparation_notes,
                original_text=clean_original_text,
            )

        except Exception as parsing_exception:
            log_debug(
                f"Failed to parse ingredient: {cleaned_text}",
                error=str(parsing_exception),
            )
            # Return basic ingredient data on parse failure
            return IngredientData(name=cleaned_text, original_text=clean_original_text)

    def _parse_quantity(self, quantity_str: str) -> Optional[float]:
        """Parse quantity string to float, handling fractions and mixed numbers.

        Args:
            quantity_str (str): Quantity string like "2", "1/2", "1 1/2", "¼"

        Returns:
            Optional[float]: Parsed quantity or None if parsing fails.
        """
        import re
        from fractions import Fraction

        try:

            for unicode_fraction, fraction_value in constants.UNICODE_FRACTIONS.items():
                if unicode_fraction in quantity_str:
                    # Handle mixed numbers like "1¼"
                    number_parts = quantity_str.split(unicode_fraction)
                    if number_parts[0].strip():
                        return float(number_parts[0].strip()) + fraction_value
                    else:
                        return fraction_value

            # Handle mixed numbers like "1 1/2"
            mixed_number_match = re.match(r"(\d+)\s+(\d+)/(\d+)", quantity_str.strip())
            if mixed_number_match:
                whole_number = int(mixed_number_match.group(1))
                fraction_part = Fraction(
                    int(mixed_number_match.group(2)), int(mixed_number_match.group(3))
                )
                return float(whole_number + fraction_part)

            # Handle simple fractions like "1/2"
            if "/" in quantity_str:
                return float(Fraction(quantity_str.strip()))

            # Handle decimal numbers
            return float(quantity_str.strip())

        except (ValueError, ZeroDivisionError):
            return None

    def _extract_name_and_notes(self, text: str) -> Tuple[str, Optional[str]]:
        """Extract ingredient name and preparation notes from text.

        Args:
            text (str): Text containing ingredient name and possibly notes in parentheses.

        Returns:
            Tuple[str, Optional[str]]: (ingredient_name, preparation_notes)
        """
        import re

        # Look for notes in parentheses
        parentheses_match = re.search(r"\(([^)]+)\)", text)
        if parentheses_match:
            preparation_notes = parentheses_match.group(1).strip()
            ingredient_name = re.sub(r"\([^)]+\)", "", text).strip()
            return ingredient_name, preparation_notes if preparation_notes else None

        return text.strip(), None

    def _extract_tags(self, scraper: Any) -> List[str]:
        """Extract tags from recipe-scrapers data.

        Args:
            scraper (Any): Recipe scraper object from recipe-scrapers library.

        Returns:
            List[str]: List of tags extracted from category and cuisine fields,
                with duplicates and empty values removed.
        """
        extracted_tags = []

        # Extract from category
        recipe_category = self._safe_extract(scraper.category)
        if recipe_category:
            extracted_tags.append(recipe_category)

        # Extract from cuisine
        cuisine_type = self._safe_extract(scraper.cuisine)
        if cuisine_type:
            extracted_tags.append(cuisine_type)

        # Remove duplicates and None values
        return [tag for tag in extracted_tags if tag and tag.strip()]

    def _extract_macros(self, scraper: Any) -> Optional[MacroNutrition]:
        """Extract nutritional macro information from recipe scraper.

        Uses the reusable extract_numeric_value utility to parse nutrition strings.

        Args:
            scraper (Any): Recipe scraper object from recipe-scrapers library.

        Returns:
            Optional[MacroNutrition]: Structured macro nutrition data, or None if unavailable.
        """
        try:
            # Get nutrition data directly from recipe-scrapers
            nutrients = scraper.nutrients()
            if not nutrients:
                return None

            # Use utility to extract numbers from strings like "211 kcal", "13 g"
            macros = MacroNutrition(
                calories=extract_numeric_value_from_string(nutrients.get("calories")),
                protein=extract_numeric_value_from_string(
                    nutrients.get("proteinContent")
                ),
                carbohydrates=extract_numeric_value_from_string(
                    nutrients.get("carbohydrateContent")
                ),
                fat=extract_numeric_value_from_string(nutrients.get("fatContent")),
                fiber=extract_numeric_value_from_string(nutrients.get("fiberContent")),
                sugar=extract_numeric_value_from_string(nutrients.get("sugarContent")),
                sodium=extract_numeric_value_from_string(
                    nutrients.get("sodiumContent")
                ),
                saturated_fat=extract_numeric_value_from_string(
                    nutrients.get("saturatedFatContent")
                ),
                cholesterol=extract_numeric_value_from_string(
                    nutrients.get("cholesterolContent")
                ),
            )

            # Return only if we got at least one value
            if any(
                getattr(macros, field) is not None
                for field in [
                    "calories",
                    "protein",
                    "carbohydrates",
                    "fat",
                    "fiber",
                    "sugar",
                    "sodium",
                ]
            ):
                log_debug(
                    "Macros extracted", calories=macros.calories, protein=macros.protein
                )
                return macros

            return None

        except Exception as e:
            log_error("Failed to extract macros", error=str(e))
            return None

    def _is_budget_bytes_url(self, url: str) -> bool:
        """Check if the URL is from Budget Bytes website.

        Args:
            url (str): URL to validate.

        Returns:
            bool: True if URL is from budgetbytes.com domain, False otherwise.

        Note:
            This validation ensures the scraper only processes Budget Bytes URLs
            and prevents accidental scraping of other websites.
        """
        try:
            parsed: ParseResult = urlparse(url)
            return "budgetbytes.com" in parsed.netloc.lower()
        except:
            return False
