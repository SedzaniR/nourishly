"""Macro analysis services package."""

from typing import Dict, List, Optional, Type, Union
from django.conf import settings

from .base import (
    BaseMacroAnalyzer,
    MacroAnalysisResult,
    MacroAnalysisStatus,
    AnalysisType,
)
from .api_ninja import ApiNinjaMacroAnalyzer
from .constants import MacroAnalysisProvider, PROVIDER_CONFIDENCE_LEVELS
from core.logger import log_info, log_error, log_warning


class MacroAnalysisFactory:
    """Factory for creating macro analysis providers."""

    _providers: Dict[MacroAnalysisProvider, Type[BaseMacroAnalyzer]] = {
        MacroAnalysisProvider.API_NINJA: ApiNinjaMacroAnalyzer,
        # Add more providers here as they are implemented
        # MacroAnalysisProvider.USDA: UsdaMacroAnalyzer,
    }

    @classmethod
    def get_analyzer(
        self, provider: Union[MacroAnalysisProvider, str], **kwargs
    ) -> BaseMacroAnalyzer:
        """Get a macro analyzer instance for the specified provider.

        Args:
            provider: The provider to use for analysis.
            **kwargs: Additional arguments to pass to the analyzer.

        Returns:
            BaseMacroAnalyzer: Configured analyzer instance.

        Raises:
            ValueError: If the provider is not supported.
        """
        if isinstance(provider, str):
            try:
                provider = MacroAnalysisProvider(provider)
            except ValueError:
                available = [p.value for p in MacroAnalysisProvider]
                raise ValueError(
                    f"Unknown provider '{provider}'. Available: {available}"
                )

        if provider not in self._providers:
            available = [p.value for p in self._providers.keys()]
            raise ValueError(
                f"Provider '{provider.value}' not implemented. Available: {available}"
            )

        analyzer_class = self._providers[provider]

        log_info(f"Creating {provider.value} macro analyzer", provider=provider.value)

        return analyzer_class(**kwargs)

    @classmethod
    def get_available_providers(cls) -> List[MacroAnalysisProvider]:
        """Get list of available providers.

        Returns:
            List[MacroAnalysisProvider]: List of available providers.
        """
        return list(cls._providers.keys())

    @classmethod
    def register_provider(
        cls, provider: MacroAnalysisProvider, analyzer_class: Type[BaseMacroAnalyzer]
    ) -> None:
        """Register a new macro analysis provider.

        Args:
            provider: The provider enum value.
            analyzer_class: The analyzer class to register.
        """
        cls._providers[provider] = analyzer_class
        log_info(f"Registered macro analysis provider", provider=provider.value)


class MacroAnalysisManager:
    """Manager for coordinating multiple macro analysis providers."""

    def __init__(self, default_provider: Optional[MacroAnalysisProvider] = None):
        """Initialize the manager.

        Args:
            default_provider: Default provider to use if not specified.
        """
        self.default_provider = default_provider or MacroAnalysisProvider.API_NINJA
        self._analyzers: Dict[MacroAnalysisProvider, BaseMacroAnalyzer] = {}

    def get_analyzer(
        self, provider: Optional[MacroAnalysisProvider] = None
    ) -> BaseMacroAnalyzer:
        """Get or create an analyzer for the specified provider.

        Args:
            provider: Provider to get analyzer for. Uses default if None.

        Returns:
            BaseMacroAnalyzer: Configured analyzer instance.
        """
        if provider is None:
            provider = self.default_provider

        if provider not in self._analyzers:
            self._analyzers[provider] = MacroAnalysisFactory.get_analyzer(provider)

        return self._analyzers[provider]

    def analyze_ingredient(
        self,
        ingredient_name: str,
        quantity: float = 100,
        provider: Optional[MacroAnalysisProvider] = None,
        fallback_providers: Optional[List[MacroAnalysisProvider]] = None,
    ) -> MacroAnalysisResult:
        """Analyze a single ingredient with automatic fallback to other providers.

        Args:
            ingredient_name: Name of the ingredient to analyze.
            quantity: Quantity in grams.
            provider: Primary provider to use.
            fallback_providers: List of fallback providers if primary fails.

        Returns:
            MacroAnalysisResult: Analysis result per 100g.
        """
        primary_provider = provider or self.default_provider

        if fallback_providers is None:
            fallback_providers = [
                p
                for p in MacroAnalysisFactory.get_available_providers()
                if p != primary_provider
            ]

        # Try primary provider first
        try:
            analyzer = self.get_analyzer(primary_provider)
            result = analyzer.analyze_ingredient(ingredient_name, quantity)

            if result.status == MacroAnalysisStatus.SUCCESS:
                return result

            log_warning(
                "Primary provider failed, trying fallbacks",
                primary_provider=primary_provider.value,
                status=result.status.value,
                ingredient_name=ingredient_name,
            )

        except Exception as e:
            log_error(
                "Primary provider error, trying fallbacks",
                primary_provider=primary_provider.value,
                error=str(e),
                ingredient_name=ingredient_name,
            )

        # Try fallback providers
        for fallback_provider in fallback_providers:
            try:
                analyzer = self.get_analyzer(fallback_provider)
                result = analyzer.analyze_ingredient(ingredient_name, quantity)

                if result.status == MacroAnalysisStatus.SUCCESS:
                    log_info(
                        "Fallback provider succeeded",
                        fallback_provider=fallback_provider.value,
                        ingredient_name=ingredient_name,
                    )
                    return result

            except Exception as e:
                log_error(
                    "Fallback provider error",
                    fallback_provider=fallback_provider.value,
                    error=str(e),
                    ingredient_name=ingredient_name,
                )
                continue

        # All providers failed
        log_error(
            "All ingredient analysis providers failed", ingredient_name=ingredient_name
        )
        return MacroAnalysisResult(
            food_name=ingredient_name,
            status=MacroAnalysisStatus.FAILED,
            analysis_type=AnalysisType.INGREDIENT,
            error_message="All analysis providers failed",
        )

    def analyze_recipe(
        self,
        recipe_text: str,
        servings: Optional[int] = None,
        provider: Optional[MacroAnalysisProvider] = None,
        fallback_providers: Optional[List[MacroAnalysisProvider]] = None,
    ) -> MacroAnalysisResult:
        """Analyze a recipe with automatic fallback to other providers.

        Args:
            recipe_text: Full recipe text with ingredients and quantities.
            servings: Number of servings (if known).
            provider: Primary provider to use.
            fallback_providers: List of fallback providers if primary fails.

        Returns:
            MacroAnalysisResult: Analysis result with total recipe macros.
        """
        primary_provider = provider or self.default_provider

        if fallback_providers is None:
            fallback_providers = [
                p
                for p in MacroAnalysisFactory.get_available_providers()
                if p != primary_provider
            ]

        # Try primary provider first
        try:
            analyzer = self.get_analyzer(primary_provider)
            result = analyzer.analyze_recipe(recipe_text, servings)

            if result.status == MacroAnalysisStatus.SUCCESS:
                return result

            log_warning(
                "Primary provider failed, trying fallbacks",
                primary_provider=primary_provider.value,
                status=result.status.value,
                recipe_text=(
                    recipe_text[:50] + "..." if len(recipe_text) > 50 else recipe_text
                ),
            )

        except Exception as e:
            log_error(
                "Primary provider error, trying fallbacks",
                primary_provider=primary_provider.value,
                error=str(e),
                recipe_text=(
                    recipe_text[:50] + "..." if len(recipe_text) > 50 else recipe_text
                ),
            )

        # Try fallback providers
        for fallback_provider in fallback_providers:
            try:
                analyzer = self.get_analyzer(fallback_provider)
                result = analyzer.analyze_recipe(recipe_text, servings)

                if result.status == MacroAnalysisStatus.SUCCESS:
                    log_info(
                        "Fallback provider succeeded",
                        fallback_provider=fallback_provider.value,
                        recipe_text=(
                            recipe_text[:50] + "..."
                            if len(recipe_text) > 50
                            else recipe_text
                        ),
                    )
                    return result

            except Exception as e:
                log_error(
                    "Fallback provider error",
                    fallback_provider=fallback_provider.value,
                    error=str(e),
                    recipe_text=(
                        recipe_text[:50] + "..."
                        if len(recipe_text) > 50
                        else recipe_text
                    ),
                )
                continue

        # All providers failed
        log_error("All recipe analysis providers failed", recipe_text=recipe_text[:100])
        return MacroAnalysisResult(
            food_name=(
                recipe_text[:50] + "..." if len(recipe_text) > 50 else recipe_text
            ),
            status=MacroAnalysisStatus.FAILED,
            analysis_type=AnalysisType.RECIPE,
            error_message="All analysis providers failed",
        )

    def search_foods(
        self,
        query: str,
        limit: int = 10,
        provider: Optional[MacroAnalysisProvider] = None,
    ) -> List[str]:
        """Search for foods using the specified provider.

        Args:
            query: Search query.
            limit: Maximum number of results.
            provider: Provider to use for search.

        Returns:
            List[str]: List of matching food names.
        """
        analyzer = self.get_analyzer(provider)
        return analyzer.search_foods(query, limit)

    def check_provider_availability(self) -> Dict[MacroAnalysisProvider, bool]:
        """Check availability of all providers.

        Returns:
            Dict[MacroAnalysisProvider, bool]: Provider availability status.
        """
        availability = {}

        for provider in MacroAnalysisFactory.get_available_providers():
            try:
                analyzer = self.get_analyzer(provider)
                availability[provider] = analyzer.is_available()
            except Exception as e:
                log_error(f"Error checking {provider.value} availability", error=str(e))
                availability[provider] = False

        return availability


# Convenience instance for easy importing
default_manager = MacroAnalysisManager()


# Convenience functions for common operations
def analyze_ingredient(
    ingredient_name: str,
    quantity: float = 100,
    provider: Optional[MacroAnalysisProvider] = None,
) -> MacroAnalysisResult:
    """Analyze an ingredient using the default manager.

    Args:
        ingredient_name: Name of the ingredient to analyze.
        quantity: Quantity in grams.
        provider: Provider to use for analysis.

    Returns:
        MacroAnalysisResult: Analysis result per 100g.
    """
    return default_manager.analyze_ingredient(ingredient_name, quantity, provider)


def analyze_recipe(
    recipe_text: str,
    servings: Optional[int] = None,
    provider: Optional[MacroAnalysisProvider] = None,
) -> MacroAnalysisResult:
    """Analyze a recipe using the default manager.

    Args:
        recipe_text: Full recipe text with ingredients and quantities.
        servings: Number of servings (if known).
        provider: Provider to use for analysis.

    Returns:
        MacroAnalysisResult: Analysis result with total recipe macros.
    """
    return default_manager.analyze_recipe(recipe_text, servings, provider)


def search_foods(
    query: str, limit: int = 10, provider: Optional[MacroAnalysisProvider] = None
) -> List[str]:
    """Search for foods using the default manager.

    Args:
        query: Search query.
        limit: Maximum number of results.
        provider: Provider to use for search.

    Returns:
        List[str]: List of matching food names.
    """
    return default_manager.search_foods(query, limit, provider)


def get_analyzer(provider: MacroAnalysisProvider) -> BaseMacroAnalyzer:
    """Get an analyzer instance for the specified provider.

    Args:
        provider: Provider to get analyzer for.

    Returns:
        BaseMacroAnalyzer: Configured analyzer instance.
    """
    return MacroAnalysisFactory.get_analyzer(provider)
