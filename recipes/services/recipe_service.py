from typing import List, Dict, Any, Optional, Type
from django.conf import settings
from .recipe_providers.base import BaseRecipeProvider, RecipeData
from .recipe_providers.edanam import EdamamRecipeProvider
from core.logger import get_logger


class RecipeService:
    """
    Main service for recipe operations that orchestrates multiple providers.
    """
    
    def __init__(self):
        self.logger = get_logger()
        self._providers: Dict[str, BaseRecipeProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all available recipe providers."""
        provider_configs = getattr(settings, 'RECIPE_PROVIDERS', {})
        
        # Initialize Edamam provider if configured
        edamam_config = provider_configs.get('edamam', {})
        if edamam_config.get('enabled', False):
            try:
                edamam_provider = EdamamRecipeProvider(
                    api_key=edamam_config.get('api_key'),
                    app_id=edamam_config.get('app_id')
                )
                if edamam_provider.is_available():
                    self._providers['edamam'] = edamam_provider
                    self.logger.info("Edamam recipe provider initialized successfully")
                else:
                    self.logger.warning("Edamam provider configuration invalid")
            except Exception as e:
                self.logger.error(
                    "Failed to initialize Edamam provider",
                    error=str(e)
                )
        
        # Add other providers here as they're implemented
        # spoonacular_config = provider_configs.get('spoonacular', {})
        # if spoonacular_config.get('enabled', False):
        #     ...
        
        self.logger.info(
            "Recipe service initialized",
            active_providers=list(self._providers.keys())
        )
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names."""
        return list(self._providers.keys())
    
    def search_recipes(
        self,
        query: str,
        provider: Optional[str] = None,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RecipeData]:
        """
        Search for recipes across providers.
        
        Args:
            query: Search term
            provider: Specific provider to use (None for all)
            limit: Maximum number of results
            filters: Search filters
            
        Returns:
            List of recipe data from providers
        """
        if not query.strip():
            return []
        
        recipes = []
        
        # Use specific provider if requested
        if provider:
            if provider in self._providers:
                try:
                    provider_recipes = self._providers[provider].search_recipes(
                        query, limit, filters
                    )
                    recipes.extend(provider_recipes)
                    
                    self.logger.info(
                        "Recipe search completed",
                        provider=provider,
                        query=query,
                        results_count=len(provider_recipes)
                    )
                except Exception as e:
                    self.logger.error(
                        "Recipe search failed",
                        provider=provider,
                        query=query,
                        error=str(e)
                    )
            else:
                self.logger.warning(
                    "Requested provider not available",
                    provider=provider,
                    available_providers=list(self._providers.keys())
                )
        else:
            # Search across all providers
            for provider_name, provider_instance in self._providers.items():
                try:
                    provider_recipes = provider_instance.search_recipes(
                        query, limit, filters
                    )
                    recipes.extend(provider_recipes)
                    
                    self.logger.debug(
                        "Provider search completed",
                        provider=provider_name,
                        query=query,
                        results_count=len(provider_recipes)
                    )
                except Exception as e:
                    self.logger.error(
                        "Provider search failed",
                        provider=provider_name,
                        query=query,
                        error=str(e)
                    )
        
        self.logger.info(
            "Recipe search completed",
            query=query,
            total_results=len(recipes),
            providers_used=provider or "all"
        )
        
        return recipes
    
    def get_recipe_by_id(
        self,
        recipe_id: str,
        provider: str
    ) -> Optional[RecipeData]:
        """
        Get a specific recipe by ID from a provider.
        
        Args:
            recipe_id: Provider-specific recipe ID
            provider: Provider name
            
        Returns:
            Recipe data or None if not found
        """
        if provider not in self._providers:
            self.logger.warning(
                "Provider not available for recipe lookup",
                provider=provider,
                recipe_id=recipe_id
            )
            return None
        
        try:
            recipe = self._providers[provider].get_recipe_by_id(recipe_id)
            
            if recipe:
                self.logger.info(
                    "Recipe retrieved successfully",
                    provider=provider,
                    recipe_id=recipe_id,
                    recipe_title=recipe.title
                )
            else:
                self.logger.info(
                    "Recipe not found",
                    provider=provider,
                    recipe_id=recipe_id
                )
            
            return recipe
            
        except Exception as e:
            self.logger.error(
                "Failed to retrieve recipe",
                provider=provider,
                recipe_id=recipe_id,
                error=str(e)
            )
            return None
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers."""
        status = {}
        
        for provider_name, provider_instance in self._providers.items():
            status[provider_name] = {
                'available': provider_instance.is_available(),
                'name': provider_instance.provider_name,
                'config_valid': provider_instance.validate_config()
            }
        
        return status


# Global instance
recipe_service = RecipeService() 