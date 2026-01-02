import os
import requests
from typing import List, Optional, Dict, Any

from .base import (
    BaseMacroAnalyzer,
    MacroAnalysisResult,
    MacroAnalysisStatus,
    MacroNutrients,
    NutrientInfo,
    NutrientUnit,
    AnalysisType,
    RecipeIngredientResult,
)
from .constants import API_NINJA_BASE_URL

from core.logger import log_info, log_error, log_debug


class ApiNinjaMacroAnalyzer(BaseMacroAnalyzer):
    """API Ninja implementation for macro nutrient analysis.

    API Ninja supports both individual ingredient analysis and full recipe analysis
    using natural language processing to extract nutrition information from text.
    """

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """Initialize API Ninja analyzer.

        Args:
            api_key: API Ninja API key. If not provided, will use environment variable.
            timeout: Request timeout in seconds.
        """
        if not api_key:
            api_key = os.environ.get("API_NINJA_KEY")
        log_info("Initializing API NINJA Nutrition API")
        super().__init__(api_key=api_key, timeout=timeout)

    def analyze_ingredient(
        self, ingredient_name: str, quantity: Optional[float] = 100
    ) -> MacroAnalysisResult:
        """Analyze macro nutrients for a single ingredient using API Ninja.

        Args:
            ingredient_name: Name of the ingredient to analyze.
            quantity: Quantity in grams (default: 100g).

        Returns:
            MacroAnalysisResult: Analysis result with macro nutrients per 100g.
        """
        self._log_analysis_request(ingredient_name, quantity, AnalysisType.INGREDIENT)

        if not self.api_key:
            error_msg = "API Ninja API key not provided"
            log_error("API Ninja analysis failed", error=error_msg)
            return self._create_error_result(
                ingredient_name, error_msg, AnalysisType.INGREDIENT
            )

        try:
            # For ingredient analysis, we want data per 100g
            # API Ninja returns data scaled to the specified quantity
            # With API Ninja, we can't just pass the ingredient name, we need to pass the quantity
            # and the ingredient name otherwise it is scaled to 100g
            query = f"{quantity} {ingredient_name}"

            result = self._make_api_request(query)

            if result["status"] != MacroAnalysisStatus.SUCCESS:
                return MacroAnalysisResult(
                    food_name=ingredient_name,
                    status=result["status"],
                    analysis_type=AnalysisType.INGREDIENT,
                    error_message=result.get("error_message"),
                    source="API Ninja",
                )

            data = result["data"]

            if not data:
                return MacroAnalysisResult(
                    food_name=ingredient_name,
                    status=MacroAnalysisStatus.NOT_FOUND,
                    analysis_type=AnalysisType.INGREDIENT,
                    error_message=f"No nutrition data found for '{ingredient_name}'",
                    source="API Ninja",
                )

            # Parse the first result for single ingredient
            nutrition_data = data[0] if isinstance(data, list) else data

            # API Ninja returns data for the requested quantity
            macro_nutrients = self._parse_nutrition_data(nutrition_data)

            # Adjust confidence based on available data
            has_premium_fields = (
                "calories" in nutrition_data and "protein_g" in nutrition_data
            )
            confidence = (
                0.8 if has_premium_fields else 0.5
            )  # Lower confidence for free tier

            analysis_result = MacroAnalysisResult(
                food_name=ingredient_name,
                status=MacroAnalysisStatus.SUCCESS,
                analysis_type=AnalysisType.INGREDIENT,
                macro_nutrients=macro_nutrients,
                source="API Ninja (Free)" if not has_premium_fields else "API Ninja",
                confidence=confidence,
                raw_data=nutrition_data,
            )

            self._log_analysis_result(analysis_result)
            return analysis_result

        except Exception as e:
            error_msg = (
                f"Unexpected error during API Ninja ingredient analysis: {str(e)}"
            )
            log_error(
                "API Ninja unexpected error", food_name=ingredient_name, error=str(e)
            )
            return self._create_error_result(
                ingredient_name, error_msg, AnalysisType.INGREDIENT
            )

    def analyze_recipe(
        self, recipe_text: str, servings: Optional[int] = None
    ) -> MacroAnalysisResult:
        """Analyze macro nutrients for an entire recipe using API Ninja.

        Args:
            recipe_text: Full recipe text with ingredients and quantities.
            servings: Number of servings (if known).

        Returns:
            MacroAnalysisResult: Analysis result with total recipe macros.
        """
        self._log_analysis_request(
            recipe_text,
            0,
            AnalysisType.RECIPE,
        )

        if not self.api_key:
            error_msg = "API Ninja API key not provided"
            log_error("API Ninja recipe analysis failed", error=error_msg)
            return self._create_error_result(
                recipe_text, error_msg, AnalysisType.RECIPE
            )

        try:
            # API Ninja can process full recipe text with natural language processing
            result = self._make_api_request(recipe_text)

            if result["status"] != MacroAnalysisStatus.SUCCESS:
                return MacroAnalysisResult(
                    food_name=(
                        recipe_text[:50] + "..."
                        if len(recipe_text) > 50
                        else recipe_text
                    ),
                    status=result["status"],
                    analysis_type=AnalysisType.RECIPE,
                    error_message=result.get("error_message"),
                    source="API Ninja",
                )

            data = result["data"]

            if not data:
                return MacroAnalysisResult(
                    food_name=(
                        recipe_text[:50] + "..."
                        if len(recipe_text) > 50
                        else recipe_text
                    ),
                    status=MacroAnalysisStatus.NOT_FOUND,
                    analysis_type=AnalysisType.RECIPE,
                    error_message="No nutrition data found for recipe",
                    source="API Ninja",
                )

            # Parse individual ingredients from API response
            recipe_ingredients = []
            total_calories = 0
            total_protein = 0
            total_carbs = 0
            total_fat = 0
            total_fiber = 0
            total_sugar = 0
            total_sodium = 0
            total_cholesterol = 0
            total_saturated_fat = 0
            total_weight = 0

            for item in data:
                # Parse individual ingredient
                ingredient_macros = self._parse_nutrition_data(item)

                ingredient_result = RecipeIngredientResult(
                    name=item.get("name", "Unknown"),
                    quantity=item.get("serving_size_g"),
                    macro_nutrients=ingredient_macros,
                    confidence=0.8,
                )
                recipe_ingredients.append(ingredient_result)

                # Sum up totals
                # total_calories += ingredient_macros.calories
                # total_protein += ingredient_macros.protein
                total_carbs += ingredient_macros.carbohydrates
                total_fat += ingredient_macros.fat

                if ingredient_macros.fiber:
                    total_fiber += ingredient_macros.fiber
                if ingredient_macros.sugar:
                    total_sugar += ingredient_macros.sugar
                if ingredient_macros.sodium:
                    total_sodium += ingredient_macros.sodium
                if ingredient_macros.cholesterol:
                    total_cholesterol += ingredient_macros.cholesterol
                if ingredient_macros.saturated_fat:
                    total_saturated_fat += ingredient_macros.saturated_fat

                if item.get("serving_size_g") and not isinstance(
                    item.get("serving_size_g"), str
                ):
                    total_weight += item.get("serving_size_g")

            # Create total recipe macros
            total_macros = MacroNutrients(
                calories=total_calories,
                protein=total_protein,
                carbohydrates=total_carbs,
                fat=total_fat,
                fiber=total_fiber if total_fiber > 0 else None,
                sugar=total_sugar if total_sugar > 0 else None,
                sodium=total_sodium if total_sodium > 0 else None,
                cholesterol=total_cholesterol if total_cholesterol > 0 else None,
                saturated_fat=total_saturated_fat if total_saturated_fat > 0 else None,
                monounsaturated_fat=None,  # API Ninja doesn't provide breakdown
                polyunsaturated_fat=None,
            )

            # Check if any ingredient has premium data to adjust confidence
            has_premium_data = any(
                "calories" in item and "protein_g" in item for item in data
            )
            confidence = 0.8 if has_premium_data else 0.5

            analysis_result = MacroAnalysisResult(
                food_name=(
                    recipe_text[:50] + "..." if len(recipe_text) > 50 else recipe_text
                ),
                status=MacroAnalysisStatus.SUCCESS,
                analysis_type=AnalysisType.RECIPE,
                macro_nutrients=total_macros,
                recipe_ingredients=recipe_ingredients,
                total_weight=total_weight if total_weight > 0 else None,
                servings=servings,
                source="API Ninja (Free)" if not has_premium_data else "API Ninja",
                confidence=confidence,
                raw_data=data,
            )

            self._log_analysis_result(analysis_result)
            return analysis_result

        except Exception as e:
            error_msg = f"Unexpected error during API Ninja recipe analysis: {str(e)}"
            log_error(
                "API Ninja recipe error", recipe_text=recipe_text[:100], error=str(e)
            )
            return self._create_error_result(
                recipe_text, error_msg, AnalysisType.RECIPE
            )

    def search_foods(self, query: str, limit: int = 10) -> List[str]:
        """Search for available foods in the API Ninja database.

        Note: API Ninja doesn't have a dedicated search endpoint,
        so this will attempt to analyze the query and return it if successful.

        Args:
            query: Search query for food items.
            limit: Maximum number of results to return (unused for API Ninja).

        Returns:
            List[str]: List of matching food names.
        """
        log_info("Searching foods in API Ninja", query=query)

        # API Ninja doesn't have a search endpoint, so we try to analyze the query
        result = self.analyze_ingredient(query)

        if result.status == MacroAnalysisStatus.SUCCESS:
            return [result.food_name]
        else:
            return []

    def is_available(self) -> bool:
        """Check if the API Ninja service is available.

        Returns:
            bool: True if service is available, False otherwise.
        """
        if not self.api_key:
            log_error("API Ninja availability check failed", reason="No API key")
            return False

        try:
            # Test with a simple food item
            headers = {"X-Api-Key": self.api_key, "Content-Type": "application/json"}

            params = {"query": "apple"}

            response = requests.get(
                API_NINJA_BASE_URL,
                headers=headers,
                params=params,
                timeout=5,  # Short timeout for availability check
            )

            is_available = response.status_code in [
                200,
                404,
            ]  # 404 is also valid (food not found)

            log_info(
                "API Ninja availability check",
                available=is_available,
                status_code=response.status_code,
            )
            return is_available

        except Exception as e:
            log_error("API Ninja availability check failed", error=str(e))
            return False

    def _make_api_request(self, query: str) -> Dict[str, Any]:
        """Make a request to the API Ninja nutrition endpoint.

        Args:
            query: Query text to send to API Ninja.

        Returns:
            Dict containing status, data, and potential error message.
        """
        try:
            headers = {"X-Api-Key": self.api_key, "Content-Type": "application/json"}
            params = {"query": query}

            log_debug(
                "Making API Ninja request",
                query=query[:100] + "..." if len(query) > 100 else query,
                url=API_NINJA_BASE_URL,
            )

            response = requests.get(
                API_NINJA_BASE_URL, headers=headers, params=params, timeout=self.timeout
            )

            if response.status_code == 404:
                return {
                    "status": MacroAnalysisStatus.NOT_FOUND,
                    "error_message": f"No nutrition data found in API Ninja database",
                }

            response.raise_for_status()
            data = response.json()

            return {
                "status": MacroAnalysisStatus.SUCCESS,
                "data": data,
            }

        except requests.exceptions.Timeout:
            error_msg = f"API Ninja request timed out after {self.timeout} seconds"
            log_error("API Ninja timeout", timeout=self.timeout)
            return {
                "status": MacroAnalysisStatus.FAILED,
                "error_message": error_msg,
            }

        except requests.exceptions.RequestException as e:
            error_msg = f"API Ninja request failed: {str(e)}"
            log_error("API Ninja request error", error=str(e))
            return {
                "status": MacroAnalysisStatus.FAILED,
                "error_message": error_msg,
            }

    def _parse_nutrition_data(self, nutrition_data: Dict[str, Any]) -> MacroNutrients:
        """Parse API Ninja nutrition data into our standard format.

        Args:
            nutrition_data: Raw nutrition data from API Ninja.

        Returns:
            MacroNutrients: Parsed macro nutrients.
        """

        def safe_get(key: str, default: float = 0.0) -> float:
            """Safely get a value from nutrition data."""
            value = nutrition_data.get(key, default)

            if value is None or (isinstance(value, str) and not value.isdigit()):
                value = default
            return float(value)

        # Handle premium fields that may not be available in free tier
        calories = safe_get("calories") if "calories" in nutrition_data else 0.0
        protein = safe_get("protein_g") if "protein_g" in nutrition_data else 0.0

        return MacroNutrients(
            calories=calories,
            protein=protein,
            carbohydrates=safe_get("carbohydrates_total_g"),
            fat=safe_get("fat_total_g"),
            fiber=safe_get("fiber_g") if "fiber_g" in nutrition_data else None,
            sugar=safe_get("sugar_g") if "sugar_g" in nutrition_data else None,
            sodium=safe_get("sodium_mg") if "sodium_mg" in nutrition_data else None,
            cholesterol=(
                safe_get("cholesterol_mg")
                if "cholesterol_mg" in nutrition_data
                else None
            ),
            saturated_fat=(
                safe_get("fat_saturated_g")
                if "fat_saturated_g" in nutrition_data
                else None
            ),
            # API Ninja doesn't provide mono/polyunsaturated fat breakdown
            monounsaturated_fat=None,
            polyunsaturated_fat=None,
        )

    def get_detailed_nutrients(self, food_name: str) -> List[NutrientInfo]:
        """Get detailed nutrient information beyond basic macros.

        Args:
            food_name: Name of the food to analyze.

        Returns:
            List[NutrientInfo]: List of detailed nutrient information.
        """
        result = self.analyze_ingredient(food_name)

        if result.status != MacroAnalysisStatus.SUCCESS or not result.raw_data:
            return []

        nutrients = []
        raw_data = result.raw_data

        # Map API Ninja fields to our nutrient info
        nutrient_mapping = {
            "potassium_mg": ("Potassium", NutrientUnit.MILLIGRAMS),
            "serving_size_g": ("Serving Size", NutrientUnit.GRAMS),
        }

        for api_key, (name, unit) in nutrient_mapping.items():
            if api_key in raw_data and raw_data[api_key] is not None:
                nutrients.append(
                    NutrientInfo(
                        name=name,
                        value=float(raw_data[api_key]),
                        unit=unit,
                        per_100g=True,
                        confidence=0.8,
                    )
                )

        return nutrients
