import logging
from django.core.management.base import BaseCommand

from core.services.huggingface.huggingface_api import HuggingFaceAPICuisineClassifier
from core.services.huggingface.huggingface_client import HuggingFaceInferenceClient
from recipes.services.macro_analysis.api_ninja import ApiNinjaMacroAnalyzer
from recipes.models import Recipe
from recipes.services.recipe_providers.budgetbytes import BudgetBytesScraper
from recipes.services.recipe_storage import RecipeStorageService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Discover recipe URLs from Budget Bytes"

    def handle(self, *args, **options):
        logger.info("Starting budget bytes recipe discovery")

        budget_bytes_scraper = BudgetBytesScraper()
        huggingface_api_client = HuggingFaceAPICuisineClassifier()
        macro_analysis_service = ApiNinjaMacroAnalyzer()
        embedding_client = HuggingFaceInferenceClient()
        recipe_storage_service = RecipeStorageService(embedding_client=embedding_client)
        discovered_recipes_urls = budget_bytes_scraper.discover_recipe_urls()
        for url in discovered_recipes_urls:
            logger.info(f"Discovered recipe URL: {url}")
            recipe_data = budget_bytes_scraper.process_recipe_from_url(url)
            if recipe_data:
                logger.info(f"Recipe data: {recipe_data}")
                if not recipe_data.cuisine_type:
                    recipe_data.cuisine_type = huggingface_api_client.classify_recipe(
                        recipe_data.title
                    )
                    logger.info(
                        f"Cuisine type classified from huggingface: {recipe_data.cuisine_type}"
                    )
                if not recipe_data.macros:
                    logger.info(
                        "No macros found, using macros from macro analysis service"
                    )
                    recipe_data.macros = macro_analysis_service.analyze_recipe(
                        recipe_data.title
                    )
                    logger.info(
                        f"Macros found from macro analysis service: {recipe_data.macros}"
                    )

                # we may need to use other services to supplement the information
                # we need to decide which information is important enough to be supplemented

                logger.info("Recipe data found, creating recipe")
                stored_recipe = recipe_storage_service.store_recipe(recipe_data)
                if stored_recipe:
                    logger.info(
                        f"Recipe stored: {stored_recipe.title} ({stored_recipe.id})"
                    )
                else:
                    logger.error("Failed to store recipe data")
                quit()
        logger.info("Budget bytes recipe discovery completed")
