"""
Hugging Face Inference API-based cuisine classifier.

This classifier uses the Hugging Face Inference API to classify recipe cuisine types
without loading models locally, saving memory and computational resources.
"""

from functools import lru_cache
from typing import Dict, List, Optional, Any

from .base import BaseHuggingFaceAPIClient
from core.logger import get_logger

logger = get_logger()

from recipes.services.cuisine_classifiers.base import (
    BaseCuisineClassifier,
    ConfidenceLevel,
    CuisineClassification,
)
from recipes.services.cuisine_classifiers.constants import (
    DEFAULT_API_MAX_RETRIES,
    DEFAULT_API_RATE_LIMIT_DELAY,
    DEFAULT_API_RETRY_DELAY,
    DEFAULT_API_TIMEOUT,
    DEFAULT_HUGGINGFACE_MODEL,
)


class HuggingFaceAPICuisineClassifier(BaseHuggingFaceAPIClient, BaseCuisineClassifier):
    """
    Hugging Face Inference API-based cuisine classifier.

    This classifier uses Hugging Face's hosted Inference API to classify
    recipe cuisine types without loading models locally.

    Memory Requirements: ~5MB RAM (99% reduction vs local model)
    Dependencies: requests only

    Features:
    - No local model loading (saves memory)
    - Automatic rate limiting
    - Retry logic for robustness
    - Uses Hugging Face's hosted Inference API

    Example:
        ```python
        classifier = HuggingFaceAPICuisineClassifier(api_token="your_token")
        result = classifier.classify_recipe("Spaghetti with tomato sauce and basil")
        print(f"Cuisine: {result.primary_cuisine}")
        ```
    """

    def __init__(
        self,
        api_token: Optional[str] = None,
        model_name: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the Hugging Face API cuisine classifier.

        Args:
            api_token: Hugging Face API token (optional for public models)
            model_name: Name of the Hugging Face model to use
            **kwargs: Additional configuration
        """
        model_id = model_name or DEFAULT_HUGGINGFACE_MODEL

        # Initialize the API client
        BaseHuggingFaceAPIClient.__init__(
            self,
            model_id=model_id,
            api_token=api_token,
            timeout=kwargs.get("timeout", DEFAULT_API_TIMEOUT),
            max_retries=kwargs.get("max_retries", DEFAULT_API_MAX_RETRIES),
            retry_delay=kwargs.get("retry_delay", DEFAULT_API_RETRY_DELAY),
            rate_limit_delay=kwargs.get(
                "rate_limit_delay", DEFAULT_API_RATE_LIMIT_DELAY
            ),
            **kwargs,
        )

        # Initialize the cuisine classifier
        BaseCuisineClassifier.__init__(
            self, api_identifier=f"hf_api:{model_id}", **kwargs
        )

    @property
    def classifier_name(self) -> str:
        return f"HuggingFace API ({self.model_id})"

    @property
    def service_name(self) -> str:
        return "Hugging Face Cuisine Classifier"

    def _get_health_check_payload(self) -> Dict[str, Any]:
        """Return a test payload for health checks."""
        return {
            "inputs": "test",
            "parameters": {"candidate_labels": ["Italian", "Chinese"]},
        }

    def classify_recipe(self, recipe_text: str) -> CuisineClassification:
        """
        Classify a single recipe's cuisine type using the API.

        Args:
            recipe_text: Combined text from recipe title and ingredients

        Returns:
            CuisineClassification with predicted cuisine and confidence
        """
        if not self.validate_recipe_text(recipe_text):
            return CuisineClassification(
                primary_cuisine="Other",
                confidence=0.0,
                confidence_level=ConfidenceLevel.LOW,
                reasoning="Empty or invalid recipe text",
            )

        try:
            payload = {
                "inputs": recipe_text,
                "parameters": {"candidate_labels": self.supported_cuisines},
            }
            result = self._make_api_request(payload)
            if not result:
                logger.error("API request failed, returning default classification")
                return CuisineClassification(
                    primary_cuisine="Other",
                    confidence=0.0,
                    confidence_level=ConfidenceLevel.LOW,
                    reasoning="API request failed",
                )

            # Extract results
            if isinstance(result, dict) and "labels" in result and "scores" in result:
                primary_cuisine = result["labels"][0]
                confidence = result["scores"][0]

                # Build alternatives list
                alternatives = []
                for label, score in zip(
                    result["labels"][1:6], result["scores"][1:6]
                ):  # Top 5
                    alternatives.append({"cuisine": label, "confidence": float(score)})

                # Simple reasoning
                reasoning = (
                    f"Classified as {primary_cuisine} based on recipe content analysis"
                )

                logger.debug(
                    "Recipe classified via API",
                    predicted_cuisine=primary_cuisine,
                    confidence=confidence,
                )

                return CuisineClassification(
                    primary_cuisine=primary_cuisine,
                    confidence=float(confidence),
                    confidence_level=ConfidenceLevel.HIGH,  # Will be auto-calculated
                    alternatives=alternatives,
                    reasoning=reasoning,
                )
            else:
                logger.error("Unexpected API response format", response=result)
                return CuisineClassification(
                    primary_cuisine="Other",
                    confidence=0.0,
                    confidence_level=ConfidenceLevel.LOW,
                    reasoning="Unexpected API response format",
                )

        except Exception as e:
            logger.error(
                "Recipe cuisine classification failed via API",
                error=str(e),
                recipe_text_length=len(recipe_text) if recipe_text else 0,
                model_id=self.model_id,
            )
            return CuisineClassification(
                primary_cuisine="Other",
                confidence=0.0,
                confidence_level=ConfidenceLevel.LOW,
                reasoning=f"API classification error: {str(e)}",
            )

    def classify_batch(self, recipe_texts: List[str]) -> List[CuisineClassification]:
        """
        Classify multiple recipes.

        Note: API doesn't support batch requests, so we process them sequentially
        with appropriate rate limiting.

        Args:
            recipe_texts: List of recipe texts to classify

        Returns:
            List of CuisineClassification objects
        """
        results = []
        logger.info(
            "Starting batch classification via API", batch_size=len(recipe_texts)
        )

        for i, recipe_text in enumerate(recipe_texts):
            try:
                result = self.classify_recipe(recipe_text)
                results.append(result)

                # Log progress for large batches
                if len(recipe_texts) > 10 and (i + 1) % 10 == 0:
                    logger.debug(
                        "Batch classification progress",
                        completed=i + 1,
                        total=len(recipe_texts),
                    )

            except Exception as e:
                logger.error(
                    "Failed to classify recipe in batch", index=i, error=str(e)
                )
                # Add error result to maintain list consistency
                results.append(
                    CuisineClassification(
                        primary_cuisine="Other",
                        confidence=0.0,
                        confidence_level=ConfidenceLevel.LOW,
                        reasoning=f"Batch classification error: {str(e)}",
                    )
                )

        logger.info(
            "Completed batch classification via API",
            total_recipes=len(recipe_texts),
            successful=len([r for r in results if r.confidence > 0]),
        )

        return results

    @lru_cache(maxsize=100)
    def _cached_classification(self, recipe_text: str) -> CuisineClassification:
        """
        Cached version of classification for frequently used recipes.
        Especially useful for API-based classification to reduce API calls.

        Args:
            recipe_text: Recipe text to classify

        Returns:
            Cached classification result
        """
        return self.classify_recipe(recipe_text)
