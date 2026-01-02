from typing import List

from .base import BaseHuggingFaceInferenceClient
from .constants import PREFERRED_SENTENCE_TRANSFORMERS_MODEL_ID


class HuggingFaceInferenceClient(BaseHuggingFaceInferenceClient):
    """
    Hugging Face client for generating embeddings and feature extraction.

    This client specializes in embedding generation using sentence transformers
    and other feature extraction models.
    """

    def __init__(
        self, model_id: str = PREFERRED_SENTENCE_TRANSFORMERS_MODEL_ID, **kwargs
    ):
        """
        Initialize the embedding client.

        Args:
            model_id: Model ID for embedding generation
            **kwargs: Additional configuration passed to base class
        """
        super().__init__(model_id=model_id, **kwargs)

    @property
    def service_name(self) -> str:
        return "Hugging Face Embedding Client"

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embeddings for the given text.

        Args:
            text: Input text to generate embeddings for

        Returns:
            List of float values representing the text embedding
        """
        response = self.client.feature_extraction(text)
        return response
