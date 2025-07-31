from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

from core.logger import log_info, log_error, log_debug


class MacroAnalysisStatus(Enum):
    """

    Status of macro analysis operation.
    SUCCESS: The analysis was successful.
    FAILED: The analysis failed.
    PARTIAL: The analysis was successful, but some nutrients were not found.
    NOT_FOUND: The analysis failed because the food item was not found in the database.

    """

    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    NOT_FOUND = "not_found"


class NutrientUnit(Enum):
    """Units for nutritional values."""

    GRAMS = "g"
    MILLIGRAMS = "mg"
    MICROGRAMS = "μg"
    CALORIES = "kcal"
    INTERNATIONAL_UNITS = "IU"


class AnalysisType(Enum):
    """Type of macro analysis being performed."""

    INGREDIENT = "ingredient"  # Single ingredient analysis (per 100g)
    RECIPE = "recipe"  # Full recipe analysis (total macros)


@dataclass
class NutrientInfo:
    """
    Individual nutrient information. This is a generic nutrient info class that can be used for any nutrient.
    The per_100g flag is used to indicate if the value is per 100g of the food item. This is a useful data class abstraction
    for usage in standalone nutrition analysis for one food item. e.g.

    """

    name: str
    value: float
    unit: NutrientUnit
    per_100g: bool = True
    confidence: float = 1.0


@dataclass
class MacroNutrients:
    """
    This represents the current macro nutrients that are being analyzed for a food item.
    This is a useful data class abstraction for usage in nutrition analysis for only macro analysis.
    The macros are not per 100g, but rather the total macros for the food item.

    """

    calories: float = 0
    protein: float = 0
    carbohydrates: float = 0
    fat: float = 0
    fiber: float = 0
    sugar: float = 0
    sodium: float = 0
    cholesterol: float = 0
    saturated_fat: float = 0
    monounsaturated_fat: float = 0
    polyunsaturated_fat: float = 0


@dataclass
class RecipeIngredientResult:
    """
    Individual ingredient result within a recipe analysis.
    This is a useful data class abstraction for usage in nutrition analysis for recipe analysis.
    The macros are not per 100g, but rather the total macros for the food item.
    """

    name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    macro_nutrients: Optional[MacroNutrients] = None
    confidence: float = 1.0


@dataclass
class MacroAnalysisResult:
    """
    Result of macro nutrient analysis.

    food_name: The name of the food item or recipe that is being analyzed.
    status: The status of the analysis.
    analysis_type: The type of analysis being performed.
    macro_nutrients: The macro nutrients for the food item, aggregated if multiple ingredients are present in the recipe.
    recipe_ingredients: The ingredients in the recipe. with their quantity, unit, and macro nutrients. This is useful if a user wants to know the macro nutrients for each ingredient in the recipe
    total_weight: The total weight of the recipe in grams.
    servings: The number of servings in the recipe.
    additional_nutrients: Any additional nutrients that were found in the analysis.
    source: The source of the analysis.
    confidence: The confidence in the analysis.
    error_message: The error message if the analysis failed.
    raw_data: The raw data from the analysis. This is useful for debugging and for future reference.

    """

    food_name: str
    status: MacroAnalysisStatus
    analysis_type: AnalysisType
    macro_nutrients: Optional[MacroNutrients] = None

    # For recipe analysis
    recipe_ingredients: Optional[List[RecipeIngredientResult]] = None
    total_weight: Optional[float] = None
    servings: Optional[int] = None

    # Common fields
    additional_nutrients: Optional[List[NutrientInfo]] = None
    source: Optional[str] = None
    confidence: float = 1.0
    error_message: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


class BaseMacroAnalyzer(ABC):
    """Abstract base class for macro nutrient analysis services."""

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """Initialize the macro analyzer.

        Args:
            api_key: API key for the service (if required).
            timeout: Request timeout in seconds.
        """
        self.api_key = api_key
        self.timeout = timeout
        self.service_name = self.__class__.__name__

    @abstractmethod
    def analyze_ingredient(
        self, ingredient_name: str, quantity: Optional[float] = 100
    ) -> MacroAnalysisResult:
        """Analyze macro nutrients for a single ingredient.

        Args:
            ingredient_name: Name of the ingredient to analyze.
            quantity: Quantity in grams (default: 100g).

        Returns:
            MacroAnalysisResult: Analysis result with macro nutrients per 100g.
        """
        pass

    @abstractmethod
    def analyze_recipe(
        self, recipe_text: str, servings: Optional[int] = None
    ) -> MacroAnalysisResult:
        """Analyze macro nutrients for an entire recipe.

        Args:
            recipe_text: Full recipe text with ingredients and quantities.
            servings: Number of servings (if known).

        Returns:
            MacroAnalysisResult: Analysis result with total recipe macros.
        """
        pass

    @abstractmethod
    def search_foods(self, query: str, limit: int = 10) -> List[str]:
        """Search for available foods in the database.

        Args:
            query: Search query for food items.
            limit: Maximum number of results to return.

        Returns:
            List[str]: List of matching food names.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the analysis service is available.

        Returns:
            bool: True if service is available, False otherwise.
        """
        pass

    def analyze_multiple_ingredients(
        self, ingredient_names: List[str]
    ) -> List[MacroAnalysisResult]:
        """Analyze multiple ingredients in batch.

        Args:
            ingredient_names: List of ingredient names to analyze.

        Returns:
            List[MacroAnalysisResult]: List of analysis results.
        """
        log_info(
            "Starting batch ingredient analysis",
            service=self.service_name,
            ingredient_count=len(ingredient_names),
        )

        results = []

        for ingredient_name in ingredient_names:
            try:
                result = self.analyze_ingredient(ingredient_name)
                results.append(result)

                log_debug(
                    "Ingredient analysis completed",
                    service=self.service_name,
                    ingredient_name=ingredient_name,
                    status=result.status.value,
                )

            except Exception as e:
                log_error(
                    "Ingredient analysis failed",
                    service=self.service_name,
                    ingredient_name=ingredient_name,
                    error=str(e),
                )

                results.append(
                    MacroAnalysisResult(
                        food_name=ingredient_name,
                        status=MacroAnalysisStatus.FAILED,
                        analysis_type=AnalysisType.INGREDIENT,
                        error_message=str(e),
                    )
                )

        log_info(
            "Batch ingredient analysis completed",
            service=self.service_name,
            total_ingredients=len(ingredient_names),
            successful_analyses=len(
                [r for r in results if r.status == MacroAnalysisStatus.SUCCESS]
            ),
        )

        return results

    def analyze_multiple_recipes(
        self, recipe_texts: List[str]
    ) -> List[MacroAnalysisResult]:
        """Analyze multiple recipes in batch.

        Args:
            recipe_texts: List of recipe texts to analyze.

        Returns:
            List[MacroAnalysisResult]: List of analysis results.
        """
        log_info(
            "Starting batch recipe analysis",
            service=self.service_name,
            recipe_count=len(recipe_texts),
        )

        results = []

        for recipe_text in recipe_texts:
            try:
                result = self.analyze_recipe(recipe_text)
                results.append(result)

                log_debug(
                    "Recipe analysis completed",
                    service=self.service_name,
                    recipe_name=(
                        recipe_text[:50] + "..."
                        if len(recipe_text) > 50
                        else recipe_text
                    ),
                    status=result.status.value,
                )

            except Exception as e:
                log_error(
                    "Recipe analysis failed",
                    service=self.service_name,
                    recipe_text=(
                        recipe_text[:50] + "..."
                        if len(recipe_text) > 50
                        else recipe_text
                    ),
                    error=str(e),
                )

                results.append(
                    MacroAnalysisResult(
                        food_name=(
                            recipe_text[:50] + "..."
                            if len(recipe_text) > 50
                            else recipe_text
                        ),
                        status=MacroAnalysisStatus.FAILED,
                        analysis_type=AnalysisType.RECIPE,
                        error_message=str(e),
                    )
                )

        log_info(
            "Batch recipe analysis completed",
            service=self.service_name,
            total_recipes=len(recipe_texts),
            successful_analyses=len(
                [r for r in results if r.status == MacroAnalysisStatus.SUCCESS]
            ),
        )

        return results

    def _log_analysis_request(
        self, food_name: str, quantity: float, analysis_type: AnalysisType
    ) -> None:
        """Log an analysis request.

        Args:
            food_name: Name of the food being analyzed.
            quantity: Quantity being analyzed.
            analysis_type: Type of analysis being performed.
        """
        log_info(
            "Macro analysis request",
            service=self.service_name,
            food_name=food_name,
            quantity=quantity,
            analysis_type=analysis_type.value,
        )

    def _log_analysis_result(self, result: MacroAnalysisResult) -> None:
        """Log an analysis result.

        Args:
            result: The analysis result to log.
        """
        if result.status == MacroAnalysisStatus.SUCCESS:
            log_info(
                "Macro analysis successful",
                service=self.service_name,
                food_name=result.food_name,
                analysis_type=result.analysis_type.value,
                calories=(
                    result.macro_nutrients.calories if result.macro_nutrients else None
                ),
                confidence=result.confidence,
            )
        else:
            log_error(
                "Macro analysis failed",
                service=self.service_name,
                food_name=result.food_name,
                analysis_type=result.analysis_type.value,
                status=result.status.value,
                error=result.error_message,
            )

    def _create_error_result(
        self, food_name: str, error_message: str, analysis_type: AnalysisType
    ) -> MacroAnalysisResult:
        """Create an error result.

        Args:
            food_name: Name of the food that failed analysis.
            error_message: Error message describing the failure.
            analysis_type: Type of analysis that failed.

        Returns:
            MacroAnalysisResult: Error result object.
        """
        return MacroAnalysisResult(
            food_name=food_name,
            status=MacroAnalysisStatus.FAILED,
            analysis_type=analysis_type,
            error_message=error_message,
            source=self.service_name,
        )
