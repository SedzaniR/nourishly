import re
from typing import Optional, Any, List
import logging

from recipes.services.recipe_providers.base import MacroNutrition
from recipes.utils import (
    extract_numeric_value_from_string,
    safely_extract_info_from_function_call,
)
from recipes.services.recipe_providers import constants
from recipes.services.recipe_providers.utils import parse_servings
from recipes.services.macro_analysis.api_ninja import ApiNinjaMacroAnalyzer
from recipes.services.macro_analysis.base import MacroAnalysisStatus

logger = logging.getLogger(__name__)


def extract_macros(scraper: Any) -> Optional[MacroNutrition]:
    """Extract nutritional macro information from recipe scraper.

    Uses the reusable extract_numeric_value utility to parse nutrition strings.
    Falls back to the macro analysis service when some macro fields are missing.

    Args:
        scraper (Any): Recipe scraper object from recipe-scrapers library.

    Returns:
        Optional[MacroNutrition]: Structured macro nutrition data, or None if unavailable.
    """
    try:
        nutrients = scraper.nutrients()
        macros = None
        if nutrients:
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
                monounsaturated_fat=extract_numeric_value_from_string(
                    nutrients.get("monounsaturatedFatContent")
                ),
                polyunsaturated_fat=extract_numeric_value_from_string(
                    nutrients.get("polyunsaturatedFatContent")
                ),
            )

        macros = macros or MacroNutrition()
        missing_fields = [
            field
            for field in constants.MACROS_TO_EXTRACT
            if getattr(macros, field) is None
        ]

        if missing_fields:
            analyzer = ApiNinjaMacroAnalyzer()
            if not analyzer or not analyzer.is_available():
                logger.warning(
                    "Macro analysis service unavailable; skipping macro fallback."
                )
            else:
                title = safely_extract_info_from_function_call(scraper.title, "")
                ingredients_list = safely_extract_info_from_function_call(
                    scraper.ingredients, []
                )
                recipe_text_parts = [title] if title else []
                if ingredients_list:
                    recipe_text_parts.append("Ingredients:")
                    recipe_text_parts.extend(ingredients_list)
                recipe_text = (
                    "\n".join(recipe_text_parts) if recipe_text_parts else title
                )

                servings = parse_servings(
                    safely_extract_info_from_function_call(scraper.yields)
                )

                analysis_result = analyzer.analyze_recipe(
                    recipe_text=recipe_text, servings=servings
                )

                if (
                    analysis_result
                    and analysis_result.status == MacroAnalysisStatus.SUCCESS
                    and analysis_result.macro_nutrients
                ):
                    macro_nutrients = analysis_result.macro_nutrients
                    logger.info(f"Macro nutrients analysis result: {analysis_result}")
                    for field in constants.MACROS_TO_EXTRACT:
                        if getattr(macros, field) is None:
                            setattr(
                                macros,
                                field,
                                getattr(macro_nutrients, field, None),
                            )
                    logger.info("Macros supplemented via macro analysis service.")
                else:
                    logger.warning("Macro analysis service returned no macros.")

        if any(
            getattr(macros, field) is not None for field in constants.MACROS_TO_EXTRACT
        ):
            logger.debug(
                f"Macros extracted/supplemented - Calories: {macros.calories}, Protein: {macros.protein}"
            )
            return macros

        return None

    except Exception as e:
        logger.error(f"Failed to extract macros - Error: {str(e)}")
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
        restrictions = safely_extract_info_from_function_call(
            scraper.dietary_restrictions
        )

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
