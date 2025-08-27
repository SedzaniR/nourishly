import re
from fractions import Fraction
from typing import Optional, Tuple, Any, List
from urllib.parse import ParseResult, urlparse

from core.logger import log_debug, log_error
from recipes.services.recipe_providers.base import MacroNutrition
from recipes.utils import extract_numeric_value_from_string, safely_extract_info_from_function_call
from recipes.services.recipe_providers import constants

def parse_quantity(quantity_str: str) -> Optional[float]:
        """Parse quantity string to float, handling fractions and mixed numbers.

        Args:
            quantity_str (str): Quantity string like "2", "1/2", "1 1/2", "¼"

        Returns:
            Optional[float]: Parsed quantity or None if parsing fails.
        """

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


def extract_name_and_notes(text: str) -> Tuple[str, Optional[str]]:
        """Extract ingredient name and preparation notes from text.

        Args:
            text (str): Text containing ingredient name and possibly notes in parentheses.

        Returns:
            Tuple[str, Optional[str]]: (ingredient_name, preparation_notes)
        """

        # Look for notes in parentheses
        parentheses_match = re.search(r"\(([^)]+)\)", text)
        if parentheses_match:
            preparation_notes = parentheses_match.group(1).strip()
            ingredient_name = re.sub(r"\([^)]+\)", "", text).strip()
            return ingredient_name, preparation_notes if preparation_notes else None

        return text.strip(), None

def is_recipe_provider_url(url: str,recipe_provider_domain:str) -> bool:
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
            return recipe_provider_domain in parsed.netloc.lower()
        except:
            return False

def extract_macros(scraper: Any) -> Optional[MacroNutrition]:
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
            for field in constants.MACROS_TO_EXTRACT
        ):
            log_debug(
                "Macros extracted", calories=macros.calories, protein=macros.protein
            )
            return macros

        return None

    except Exception as e:
        log_error("Failed to extract macros", error=str(e))
        return None


def extract_dietary_restrictions(scraper: Any) -> List[str]:
    """Extract dietary restrictions from recipe-scrapers data.

    Args:
        scraper (Any): Recipe scraper object from recipe-scrapers library.

    Returns:
        List[str]: List of dietary restrictions extracted from the recipe,
            with duplicates and empty values removed.

    Note:
        Uses the dietary_restrictions() method from recipe-scrapers which
        extracts dietary guidelines or restrictions for the recipe.
    """
    try:
        restrictions = safely_extract_info_from_function_call(scraper.dietary_restrictions)

        if not restrictions:
            return []

        if isinstance(restrictions, str):
            restriction_list = [
                restriction.strip().lower()
                for restriction in re.split(r"[,;&|]", restrictions)
                if restriction.strip()
            ]
            return restriction_list
        elif isinstance(restrictions, list):
            return [
                restriction.strip().lower()
                for restriction in restrictions
                if restriction and restriction.strip()
            ]
        else:
            return []

    except Exception:
        # If dietary_restrictions method fails, return empty list
        return []

def extract_tags(scraper: Any) -> List[str]:
    """Extract tags from recipe-scrapers data.

    Args:
        scraper (Any): Recipe scraper object from recipe-scrapers library.

    Returns:
        List[str]: List of tags extracted from category and cuisine fields,
            with duplicates and empty values removed.
    """
    extracted_tags = []

    # Extract from category
    recipe_category = safely_extract_info_from_function_call(scraper.category)
    if recipe_category:
        extracted_tags.append(recipe_category)

    # Extract from cuisine
    cuisine_type = safely_extract_info_from_function_call(scraper.cuisine)
    if cuisine_type:
        extracted_tags.append(cuisine_type)

    # Remove duplicates and None values
    return [tag for tag in extracted_tags if tag and tag.strip()]

def parse_time_duration(self, duration: Any) -> Optional[int]:
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

   
        if hasattr(duration, "total_seconds"):
            return int(duration.total_seconds() / 60)

        return self._parse_time_string(str(duration))