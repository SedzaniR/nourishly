from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

from .constants import (
    LOW_CONFIDENCE_CUISINE_CLASSIFIER_THRESHOLD,
    MEDIUM_CONFIDENCE_CUISINE_CLASSIFIER_THRESHOLD,
    SUPPORTED_CUISINES,
)


class ConfidenceLevel(Enum):
    """Confidence levels for cuisine classification."""

    LOW = "low"  # < LOW_CONFIDENCE_CUISINE_CLASSIFIER_THRESHOLD
    MEDIUM = "medium"  # LOW_CONFIDENCE_CUISINE_CLASSIFIER_THRESHOLD - MEDIUM_CONFIDENCE_CUISINE_CLASSIFIER_THRESHOLD
    HIGH = "high"  # > MEDIUM_CONFIDENCE_CUISINE_CLASSIFIER_THRESHOLD


@dataclass
class CuisineClassification:
    """
    Structured result from cuisine classification.

    This provides a standardized way to return cuisine classification results
    with confidence scores and alternative predictions from the Hugging Face API.

    Attributes:
        primary_cuisine: The most likely cuisine type
        confidence: Confidence score between 0 and 1
        confidence_level: Human-readable confidence level
        alternatives: List of alternative cuisine predictions with scores
        reasoning: Optional explanation of the classification decision

    Example:
        ```python
        classification = CuisineClassification(
            primary_cuisine="Italian",
            confidence=0.85,
            confidence_level=ConfidenceLevel.HIGH,
            alternatives=[
                {"cuisine": "Mediterranean", "confidence": 0.12},
                {"cuisine": "French", "confidence": 0.03}
            ]
        )
        ```
    """

    primary_cuisine: str
    confidence: float
    confidence_level: ConfidenceLevel
    alternatives: Optional[List[Dict[str, Union[str, float]]]] = None
    reasoning: Optional[str] = None

    def __post_init__(self):
        """Determine confidence level from confidence score."""
        if self.confidence < LOW_CONFIDENCE_CUISINE_CLASSIFIER_THRESHOLD:
            self.confidence_level = ConfidenceLevel.LOW
        elif self.confidence < MEDIUM_CONFIDENCE_CUISINE_CLASSIFIER_THRESHOLD:
            self.confidence_level = ConfidenceLevel.MEDIUM
        else:
            self.confidence_level = ConfidenceLevel.HIGH

        if self.alternatives is None:
            self.alternatives = []


class BaseCuisineClassifier(ABC):
    """
    Base class for Hugging Face API-based cuisine classification.

    This class provides common functionality for cuisine classification using
    the Hugging Face Inference API. All cuisine classification in this system
    uses the API approach to avoid memory constraints.

    Attributes:
        api_identifier: Identifier for the API configuration
        config: Additional configuration parameters
        supported_cuisines: List of cuisine types supported by the classifier
    """

    def __init__(self, api_identifier: Optional[str] = None, **kwargs):
        """
        Initialize the cuisine classifier.

        Args:
            api_identifier: Identifier for the API configuration
            **kwargs: Additional configuration parameters
        """
        self.api_identifier = api_identifier
        self.config = kwargs
        self.supported_cuisines = SUPPORTED_CUISINES

    @abstractmethod
    def classify_recipe(self, recipe_text: str) -> CuisineClassification:
        """
        Classify the cuisine type of a recipe based on its text content.

        Args:
            recipe_text: Combined text from recipe title and ingredients

        Returns:
            CuisineClassification object with the predicted cuisine and confidence
        """
        pass

    @abstractmethod
    def classify_batch(self, recipe_texts: List[str]) -> List[CuisineClassification]:
        """
        Classify multiple recipes in batch.

        Args:
            recipe_texts: List of recipe texts to classify

        Returns:
            List of CuisineClassification objects
        """
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """
        Check if the API is accessible and ready to use.

        Returns:
            True if the classifier is ready, False otherwise
        """
        pass

    def _prepare_recipe_text(self, title: str, ingredients: List[str]) -> str:
        """
        Prepare recipe components into a single text for classification.

        This method focuses on title and ingredients as they are the strongest
        signals for cuisine classification.

        Args:
            title: Recipe title
            ingredients: List of ingredients

        Returns:
            Combined text ready for classification
        """
        text_parts = []

        if title:
            text_parts.append(f"Title: {title}")

        if ingredients:
            # Use more ingredients since they're strong signals
            ingredients_text = ", ".join(ingredients[:15])  # Increased from 10
            text_parts.append(f"Ingredients: {ingredients_text}")

        return ". ".join(text_parts)

    def classify_recipe_from_data(
        self, title: str = "", ingredients: List[str] = None
    ) -> CuisineClassification:
        """
        Classify cuisine from structured recipe data.

        Args:
            title: Recipe title
            ingredients: List of ingredients

        Returns:
            CuisineClassification object
        """
        if ingredients is None:
            ingredients = []

        recipe_text = self._prepare_recipe_text(title, ingredients)
        return self.classify_recipe(recipe_text)

    def get_confidence_threshold(self, level: ConfidenceLevel) -> float:
        """
        Get the confidence threshold for a given confidence level.

        Args:
            level: Confidence level enum

        Returns:
            Confidence threshold value
        """
        thresholds = {
            ConfidenceLevel.LOW: 0.0,
            ConfidenceLevel.MEDIUM: LOW_CONFIDENCE_CUISINE_CLASSIFIER_THRESHOLD,
            ConfidenceLevel.HIGH: MEDIUM_CONFIDENCE_CUISINE_CLASSIFIER_THRESHOLD,
        }
        return thresholds[level]

    def validate_recipe_text(self, recipe_text: str) -> bool:
        """
        Validate that recipe text is suitable for classification.

        Args:
            recipe_text: Text to validate

        Returns:
            True if text is valid for classification
        """
        if not recipe_text or not recipe_text.strip():
            return False

        # Basic validation - at least 3 characters
        if len(recipe_text.strip()) < 3:
            return False

        return True

    def get_classification_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about this classifier.

        Returns:
            Dictionary with classifier metadata
        """
        return {
            "api_identifier": self.api_identifier,
            "supported_cuisines_count": len(self.supported_cuisines),
            "supported_cuisines": self.supported_cuisines,
            "config": self.config,
        }


class ClassificationError(Exception):
    """Exception raised when cuisine classification fails."""

    def __init__(self, message: str, error_details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_details = error_details or {}
