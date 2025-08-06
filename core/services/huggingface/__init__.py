"""
Hugging Face services for the Nourishly application.

This module provides base classes and implementations for different types of 
Hugging Face interactions:

1. InferenceClient-based services (for embeddings, vision, etc.)
2. API-based services (for classification, text generation, etc.)

Base Classes:
- BaseHuggingFaceInferenceClient: For huggingface_hub.InferenceClient operations
- BaseHuggingFaceAPIClient: For direct API calls with requests

Implementations:
- HuggingFaceInferenceClient: Embedding and feature extraction
- HuggingFaceAPICuisineClassifier: Cuisine classification

Example Usage:
    # Embedding client
    from core.services.huggingface import HuggingFaceInferenceClient
    embedding_client = HuggingFaceInferenceClient()
    embeddings = embedding_client.generate_embedding("Your text here")
    
    # Cuisine classifier
    from core.services.huggingface import HuggingFaceAPICuisineClassifier
    classifier = HuggingFaceAPICuisineClassifier()
    result = classifier.classify_recipe("Spaghetti with tomato sauce")
"""

from .base import BaseHuggingFaceInferenceClient, BaseHuggingFaceAPIClient
from .huggingface_client import HuggingFaceInferenceClient
from .huggingface_api import HuggingFaceAPICuisineClassifier
from .constants import (
    PREFERRED_SENTENCE_TRANSFORMERS_MODEL_ID,
    DEFAULT_VISION_MODEL_ID,
    DEFAULT_CLASSIFICATION_MODEL_ID,
    HuggingFaceTaskType,
)

__all__ = [
    # Base classes
    "BaseHuggingFaceInferenceClient",
    "BaseHuggingFaceAPIClient",
    # Implementations
    "HuggingFaceInferenceClient",
    "HuggingFaceAPICuisineClassifier",
    # Constants
    "PREFERRED_SENTENCE_TRANSFORMERS_MODEL_ID",
    "DEFAULT_VISION_MODEL_ID",
    "DEFAULT_CLASSIFICATION_MODEL_ID",
    "HuggingFaceTaskType",
]
