from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

from core.logger import log_info, log_error, log_debug


class MacroAnalysisStatus(Enum):
    """Status of macro analysis operation."""

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
    """Individual nutrient information."""

    name: str
    value: float
    unit: NutrientUnit
    per_100g: bool = True
    confidence: float = 1.0


@dataclass
class MacroNutrients:
    """Essential macro nutrients for a food item."""

    calories: float  # kcal per 100g or total
    protein: float  # grams per 100g or total
    carbohydrates: float  # grams per 100g or total
    fat: float  # grams per 100g or total
    fiber: Optional[float] = None  # grams per 100g or total
    sugar: Optional[float] = None  # grams per 100g or total
    sodium: Optional[float] = None  # mg per 100g or total
    cholesterol: Optional[float] = None  # mg per 100g or total
    saturated_fat: Optional[float] = None  # grams per 100g or total
    monounsaturated_fat: Optional[float] = None  # grams per 100g or total
    polyunsaturated_fat: Optional[float] = None  # grams per 100g or total


@dataclass
class RecipeIngredientResult:
    """Individual ingredient result within a recipe analysis."""

    name: str
    quantity: Optional[float] = None  # Detected quantity in grams
    unit: Optional[str] = None  # Detected unit (cups, tsp, etc.)
    macro_nutrients: Optional[MacroNutrients] = None
    confidence: float = 1.0


@dataclass
class MacroAnalysisResult:
    """Result of macro nutrient analysis."""

    food_name: str
    status: MacroAnalysisStatus
    analysis_type: AnalysisType
    macro_nutrients: Optional[MacroNutrients] = None

    # For recipe analysis
    recipe_ingredients: Optional[List[RecipeIngredientResult]] = None
    total_weight: Optional[float] = None  # Total recipe weight in grams
    servings: Optional[int] = None  # Number of servings

    # Common fields
    additional_nutrients: Optional[List[NutrientInfo]] = None
    source: Optional[str] = None
    confidence: float = 1.0  # Overall confidence in the analysis
    error_message: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

    @property
    def per_serving_macros(self) -> Optional[MacroNutrients]:
        """Calculate macro nutrients per serving for recipes."""
        if (
            self.analysis_type != AnalysisType.RECIPE
            or not self.macro_nutrients
            or not self.servings
            or self.servings <= 0
        ):
            return None

        return MacroNutrients(
            calories=self.macro_nutrients.calories / self.servings,
            protein=self.macro_nutrients.protein / self.servings,
            carbohydrates=self.macro_nutrients.carbohydrates / self.servings,
            fat=self.macro_nutrients.fat / self.servings,
            fiber=(
                self.macro_nutrients.fiber / self.servings
                if self.macro_nutrients.fiber
                else None
            ),
            sugar=(
                self.macro_nutrients.sugar / self.servings
                if self.macro_nutrients.sugar
                else None
            ),
            sodium=(
                self.macro_nutrients.sodium / self.servings
                if self.macro_nutrients.sodium
                else None
            ),
            cholesterol=(
                self.macro_nutrients.cholesterol / self.servings
                if self.macro_nutrients.cholesterol
                else None
            ),
            saturated_fat=(
                self.macro_nutrients.saturated_fat / self.servings
                if self.macro_nutrients.saturated_fat
                else None
            ),
            monounsaturated_fat=(
                self.macro_nutrients.monounsaturated_fat / self.servings
                if self.macro_nutrients.monounsaturated_fat
                else None
            ),
            polyunsaturated_fat=(
                self.macro_nutrients.polyunsaturated_fat / self.servings
                if self.macro_nutrients.polyunsaturated_fat
                else None
            ),
        )


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
