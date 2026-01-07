import logging
from typing import List, Optional, Union
from urllib.parse import urlparse

from django.db import transaction

from core.services.huggingface.huggingface_client import HuggingFaceInferenceClient
from recipes.models import (
    DietaryRestriction,
    Ingredient,
    Recipe,
    RecipeDietaryRestriction,
    RecipeIngredient,
    RecipeNutrition,
    RecipeTag,
    Tag,
)
from recipes.services.recipe_providers.base import (
    IngredientData,
    MacroNutrition,
    RecipeData,
)

logger = logging.getLogger(__name__)


class RecipeStorageService:
    """Persist scraped RecipeData into the database."""

    def __init__(
        self, embedding_client: Optional[HuggingFaceInferenceClient] = None
    ) -> None:
        """
        Initialize the recipe storage service.

        Args:
            embedding_client: Optional HuggingFaceInferenceClient for generating
                recipe embeddings. If not provided, embeddings will not be generated.
        """
        self.embedding_client = embedding_client

    def store_recipe(self, recipe_data: RecipeData) -> Optional[Recipe]:
        if not recipe_data:
            logger.error("No recipe data provided to store.")
            return None

        try:
            with transaction.atomic():
                recipe = self._upsert_recipe(recipe_data)
                self._upsert_ingredients(recipe, recipe_data.ingredients or [])
                self._upsert_tags(recipe, recipe_data.tags or [])
                self._upsert_dietary_restrictions(
                    recipe, recipe_data.dietary_restrictions or []
                )
                if recipe_data.macros:
                    self._upsert_macros(recipe, recipe_data.macros)
                self._generate_and_store_embedding(recipe, recipe_data)
                return recipe
        except Exception as exc:
            logger.error(
                f"Failed to store recipe '{getattr(recipe_data, 'title', 'N/A')}': {exc}"
            )
            return None

    def _upsert_recipe(self, recipe_data: RecipeData) -> Recipe:
        source_site = recipe_data.provider or self._extract_domain(
            recipe_data.source_url
        )
        recipe_defaults = {
            "title": recipe_data.title,
            "description": recipe_data.description,
            "author": recipe_data.author,
            "source_site": source_site,
            "image_url": recipe_data.image_url or "",
            "instructions": recipe_data.instructions or [],
            "preparation_time": recipe_data.prep_time,
            "cooking_time": recipe_data.cook_time,
            "servings": recipe_data.servings,
            "cuisine_type": recipe_data.cuisine_type,
            "rating": recipe_data.rating,
            "difficulty_level": recipe_data.difficulty_level,
        }

        recipe, _created = Recipe.objects.update_or_create(
            source_url=recipe_data.source_url, defaults=recipe_defaults
        )
        return recipe

    def _upsert_ingredients(
        self, recipe: Recipe, ingredients: List[Union[IngredientData, str]]
    ) -> None:
        for ingredient_entry in ingredients:
            if isinstance(ingredient_entry, IngredientData):
                ingredient_name = ingredient_entry.name.strip()
                quantity = ingredient_entry.quantity
                unit = ingredient_entry.unit
                notes = ingredient_entry.notes
                original_text = ingredient_entry.original_text
            else:
                ingredient_name = str(ingredient_entry).strip()
                quantity = None
                unit = None
                notes = None
                original_text = ingredient_entry

            if not ingredient_name:
                logger.warning("Skipping ingredient with empty name.")
                continue

            ingredient, _ = Ingredient.objects.get_or_create(name=ingredient_name)

            recipe_ingredient, created = RecipeIngredient.objects.get_or_create(
                recipe=recipe, ingredient=ingredient
            )
            recipe_ingredient.quantity = (
                quantity if quantity is not None else recipe_ingredient.quantity
            )
            recipe_ingredient.unit = unit or recipe_ingredient.unit or ""
            recipe_ingredient.note = notes or recipe_ingredient.note
            recipe_ingredient.original_text = (
                original_text or recipe_ingredient.original_text
            )
            recipe_ingredient.save()

    def _upsert_tags(self, recipe: Recipe, tags: List[str]) -> None:
        for raw_tag in tags:
            tag_name = (raw_tag or "").strip()
            if not tag_name:
                continue

            tag, _ = Tag.objects.get_or_create(name=tag_name)
            RecipeTag.objects.get_or_create(recipe=recipe, tag=tag)

    def _upsert_dietary_restrictions(
        self, recipe: Recipe, restrictions: List[str]
    ) -> None:
        valid_choices = {
            choice[0]: choice[1]
            for choice in DietaryRestriction.RestrictionType.choices
        }

        for restriction in restrictions:
            normalized = (restriction or "").strip().lower().replace(" ", "_")
            if not normalized:
                continue

            if normalized not in valid_choices:
                logger.warning(
                    f"Skipping unsupported dietary restriction '{restriction}'. Expected one of: {list(valid_choices.keys())}"
                )
                continue

            dietary_restriction, _ = DietaryRestriction.objects.get_or_create(
                name=normalized,
                defaults={"display_name": valid_choices[normalized]},
            )
            RecipeDietaryRestriction.objects.get_or_create(
                recipe=recipe, dietary_restriction=dietary_restriction
            )

    def _upsert_macros(self, recipe: Recipe, macros: MacroNutrition) -> None:
        existing = RecipeNutrition.objects.filter(recipe=recipe).first()

        macro_values = {
            "calories": macros.calories,
            "protein": macros.protein,
            "carbohydrates": macros.carbohydrates,
            "fat": macros.fat,
            "fiber": macros.fiber,
            "sugar": macros.sugar,
            "sodium": macros.sodium,
            "cholesterol": macros.cholesterol,
            "saturated_fat": macros.saturated_fat,
            "monounsaturated_fat": 0.0,
            "polyunsaturated_fat": 0.0,
        }

        required_fields = [
            "calories",
            "protein",
            "carbohydrates",
            "fat",
            "fiber",
            "sugar",
            "sodium",
            "cholesterol",
            "saturated_fat",
        ]

        if any(macro_values[field] is None for field in required_fields):
            logger.warning(
                "Skipping macro nutrition upsert because required macro values are missing."
            )
            return

        if existing:
            for field_name, value in macro_values.items():
                if value is not None:
                    setattr(existing, field_name, value)
            existing.save()
            return

        RecipeNutrition.objects.create(recipe=recipe, **macro_values)

    def _extract_domain(self, url: str) -> str:
        try:
            parsed = urlparse(url)
            return parsed.netloc or "unknown"
        except Exception:
            return "unknown"

    def _generate_and_store_embedding(
        self, recipe: Recipe, recipe_data: RecipeData
    ) -> None:
        """
        Generate and store embedding for a recipe.

        Args:
            recipe: The Recipe model instance to update.
            recipe_data: The source RecipeData containing text to embed.
        """
        if not self.embedding_client:
            logger.debug(
                "No embedding client configured, skipping embedding generation."
            )
            return

        try:
            embedding_text = self._build_embedding_text(recipe_data)
            if not embedding_text:
                logger.warning(
                    f"No text available for embedding generation for recipe '{recipe.title}'."
                )
                return

            embedding = self.embedding_client.generate_embedding(embedding_text)
            if embedding:
                recipe.embedding = embedding
                recipe.save(update_fields=["embedding"])
                logger.info(
                    f"Generated embedding for recipe '{recipe.title}' ({len(embedding)} dimensions)."
                )
            else:
                logger.warning(f"Empty embedding returned for recipe '{recipe.title}'.")
        except Exception as exc:
            logger.error(
                f"Failed to generate embedding for recipe '{recipe.title}': {exc}"
            )

    def _build_embedding_text(self, recipe_data: RecipeData) -> str:
        """
        Build the text string to be embedded from recipe data.

        Combines title, description, and ingredient names into a single
        string optimized for semantic search.

        Args:
            recipe_data: The RecipeData to extract text from.

        Returns:
            Combined text string for embedding generation.
        """
        parts = []

        if recipe_data.title:
            parts.append(recipe_data.title)

        if recipe_data.description:
            parts.append(recipe_data.description)

        if recipe_data.ingredients:
            ingredient_names = []
            for ingredient in recipe_data.ingredients:
                if isinstance(ingredient, IngredientData):
                    ingredient_names.append(ingredient.name)
                else:
                    ingredient_names.append(str(ingredient))
            if ingredient_names:
                parts.append(f"Ingredients: {', '.join(ingredient_names)}")

        return ". ".join(parts)
