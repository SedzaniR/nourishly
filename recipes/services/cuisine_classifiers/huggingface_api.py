"""
Hugging Face Inference API-based cuisine classifier.

This classifier uses the Hugging Face Inference API to classify recipe cuisine types
without loading models locally, saving memory and computational resources.
"""

import os
import time
from functools import lru_cache
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv

from core.logger import get_logger

from .base import (
    BaseCuisineClassifier,
    ConfidenceLevel,
    CuisineClassification,
)
from .constants import (
    DEFAULT_API_MAX_RETRIES,
    DEFAULT_API_RATE_LIMIT_DELAY,
    DEFAULT_API_RETRY_DELAY,
    DEFAULT_API_TIMEOUT,
    DEFAULT_HUGGINGFACE_MODEL,
)

logger = get_logger()
load_dotenv()


class HuggingFaceAPICuisineClassifier(BaseCuisineClassifier):
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

    HUGGINGFACE_MODEL_BASE_URL = "https://api-inference.huggingface.co/models"

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
        # Use passed api_token or fall back to environment variable
        if api_token is None:
            api_token = os.environ.get("HUGGINGFACE_API_TOKEN")

        self.api_token = api_token  # Can be None for free tier
        self.model_name = model_name or DEFAULT_HUGGINGFACE_MODEL
        super().__init__(api_identifier=f"hf_api:{self.model_name}", **kwargs)

        # API configuration
        self.api_url = f"{self.HUGGINGFACE_MODEL_BASE_URL}/{self.model_name}"
        self.headers = {}
        if self.api_token:
            self.headers["Authorization"] = f"Bearer {self.api_token}"

        # Rate limiting and retry configuration
        self.rate_limit_delay = kwargs.get(
            "rate_limit_delay", DEFAULT_API_RATE_LIMIT_DELAY
        )
        self.max_retries = kwargs.get("max_retries", DEFAULT_API_MAX_RETRIES)
        self.retry_delay = kwargs.get("retry_delay", DEFAULT_API_RETRY_DELAY)
        self.timeout = kwargs.get("timeout", DEFAULT_API_TIMEOUT)

        # Track last request time for rate limiting
        self._last_request_time = 0

        logger.info(
            "Initialized Hugging Face API classifier",
            model_name=self.model_name,
            has_api_token=bool(self.api_token),
        )

    @property
    def classifier_name(self) -> str:
        return f"HuggingFace API ({self.model_name})"

    def _rate_limit(self) -> None:
        """Implement rate limiting between API requests."""

        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            logger.debug("Rate limiting API request", sleep_time=sleep_time)
            time.sleep(sleep_time)
        else:
            self._last_request_time = time.time()

    def _make_api_request(self, payload: Dict, retry_count: int = 0) -> Optional[Dict]:
        """
        Make a request to the Hugging Face Inference API with retry logic.

        Args:
            payload: Request payload
            retry_count: Current retry attempt

        Returns:
            API response data, or None if the request fails
        """
        self._rate_limit()

        try:
            response = requests.post(
                self.api_url, headers=self.headers, json=payload, timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 503:
                # Model is loading, wait and retry
                if retry_count < self.max_retries:
                    wait_time = self.retry_delay * (retry_count + 1)
                    logger.warning(
                        "Model is loading, retrying",
                        retry_count=retry_count,
                        wait_time=wait_time,
                    )
                    time.sleep(wait_time)
                    return self._make_api_request(payload, retry_count + 1)
                else:
                    logger.error(
                        "Model failed to load after maximum retries",
                        error_details={"max_retries": self.max_retries},
                    )
                    return None
            elif response.status_code == 429:
                # Rate limited, wait and retry
                if retry_count < self.max_retries:
                    wait_time = (
                        self.retry_delay * (retry_count + 1) * 2
                    )  # Longer wait for rate limits
                    logger.warning(
                        "Rate limited, retrying",
                        retry_count=retry_count,
                        wait_time=wait_time,
                    )
                    time.sleep(wait_time)
                    return self._make_api_request(payload, retry_count + 1)
                else:
                    logger.error(
                        "Rate limit exceeded, maximum retries reached",
                        error_details={
                            "max_retries": self.max_retries,
                            "rate_limited": True,
                        },
                    )
                    return None
            else:
                error_msg = f"API request failed with status {response.status_code}: {response.text}"
                logger.error(
                    "Hugging Face API request failed",
                    status_code=response.status_code,
                    error_text=error_msg,
                )
                return None

        except requests.exceptions.Timeout:
            if retry_count < self.max_retries:
                logger.warning("API request timeout, retrying", retry_count=retry_count)
                time.sleep(self.retry_delay)
                return self._make_api_request(payload, retry_count + 1)
            else:
                logger.error(
                    "API request timeout after maximum retries",
                    error_details={
                        "timeout": self.timeout,
                        "max_retries": self.max_retries,
                    },
                )
                return None
        except requests.exceptions.RequestException as e:
            logger.error("API request exception", error=str(e), retry_count=retry_count)
            if retry_count < self.max_retries:
                time.sleep(self.retry_delay)
                return self._make_api_request(payload, retry_count + 1)
            else:
                logger.error(
                    "API request failed after maximum retries",
                    error_details={
                        "original_error": str(e),
                        "max_retries": self.max_retries,
                    },
                )
                return None
        except Exception as e:
            logger.error("API request exception", error=str(e), retry_count=retry_count)
            return None

    def is_ready(self) -> bool:
        """
        Check if the API is accessible and the model is ready.

        Returns:
            True if the API is ready, False otherwise
        """
        try:
            test_payload = {
                "inputs": "test",
                "parameters": {"candidate_labels": ["Italian", "Chinese"]},
            }
            result = self._make_api_request(test_payload)
            return bool(result)
        except Exception as e:
            logger.error(
                "Hugging Face API not ready", error=str(e), model_name=self.model_name
            )
            return False

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
                model_name=self.model_name,
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
