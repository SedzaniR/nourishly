import re
from typing import Optional, Any, List

from core.logger import log_debug, log_error
from recipes.services.recipe_providers.base import MacroNutrition
from recipes.utils import extract_numeric_value_from_string, safely_extract_info_from_function_call
from recipes.services.recipe_providers import constants

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