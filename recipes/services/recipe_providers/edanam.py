import requests
from typing import List, Dict, Any, Optional
from .base import BaseRecipeProvider, RecipeData


class EdamamRecipeProvider(BaseRecipeProvider):
    """Edamam Recipe API provider."""
    
    BASE_URL = "https://api.edamam.com/api/recipes/v2"
    
    @property
    def provider_name(self) -> str:
        return "edamam"
    
    def validate_config(self) -> bool:
        """Validate that API key and app ID are provided."""
        return (
            self.api_key is not None and 
            self.config.get('app_id') is not None
        )
    
    def search_recipes(
        self, 
        query: str, 
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RecipeData]:
        """Search recipes using Edamam API."""
        if not self.is_available():
            return []
        
        params = {
            'type': 'public',
            'q': query,
            'app_id': self.config.get('app_id'),
            'app_key': self.api_key,
            'to': limit
        }
        
        # Add filters if provided
        if filters:
            if 'cuisine_type' in filters:
                params['cuisineType'] = filters['cuisine_type']
            if 'diet' in filters:
                params['diet'] = filters['diet']
            if 'health' in filters:
                params['health'] = filters['health']
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            recipes = []
            for hit in data.get('hits', []):
                recipe_data = self._normalize_recipe_data(hit['recipe'])
                recipes.append(recipe_data)
            
            return recipes
            
        except Exception as e:
            # Log error using the logger
            from core.logger import get_logger
            logger = get_logger()
            logger.error(
                "Failed to search recipes from Edamam",
                provider="edamam",
                query=query,
                error=str(e)
            )
            return []
    
    def get_recipe_by_id(self, recipe_id: str) -> Optional[RecipeData]:
        """Get a specific recipe by ID."""
        if not self.is_available():
            return None
        
        url = f"{self.BASE_URL}/{recipe_id}"
        params = {
            'type': 'public',
            'app_id': self.config.get('app_id'),
            'app_key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'recipe' in data:
                return self._normalize_recipe_data(data['recipe'])
            
            return None
            
        except Exception as e:
            from core.logger import get_logger
            logger = get_logger()
            logger.error(
                "Failed to get recipe by ID from Edamam",
                provider="edamam",
                recipe_id=recipe_id,
                error=str(e)
            )
            return None
    
    def _normalize_recipe_data(self, raw_data: Dict[str, Any]) -> RecipeData:
        """Convert Edamam recipe data to standardized format."""
        return RecipeData(
            title=raw_data.get('label', ''),
            description=raw_data.get('source', ''),
            ingredients=[
                ingredient.get('text', '') 
                for ingredient in raw_data.get('ingredients', [])
            ],
            instructions=[], # Edamam doesn't provide instructions in free tier
            prep_time=None,  # Not available in Edamam
            cook_time=raw_data.get('totalTime'),
            servings=raw_data.get('yield'),
            cuisine_type=raw_data.get('cuisineType', [None])[0] if raw_data.get('cuisineType') else None,
            difficulty_level=None,  # Not available in Edamam
            image_url=raw_data.get('image'),
            source_url=raw_data.get('url'),
            nutrition=self._extract_nutrition(raw_data),
            tags=raw_data.get('healthLabels', []) + raw_data.get('dietLabels', []),
            provider=self.provider_name,
            external_id=raw_data.get('uri', '').split('_')[-1] if raw_data.get('uri') else None
        )
    
    def _extract_nutrition(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract nutrition information from Edamam data."""
        nutrition_data = raw_data.get('totalNutrients', {})
        
        return {
            'calories': nutrition_data.get('ENERC_KCAL', {}).get('quantity'),
            'protein': nutrition_data.get('PROCNT', {}).get('quantity'),
            'fat': nutrition_data.get('FAT', {}).get('quantity'),
            'carbs': nutrition_data.get('CHOCDF', {}).get('quantity'),
            'fiber': nutrition_data.get('FIBTG', {}).get('quantity'),
            'sugar': nutrition_data.get('SUGAR', {}).get('quantity'),
            'sodium': nutrition_data.get('NA', {}).get('quantity'),
        }
