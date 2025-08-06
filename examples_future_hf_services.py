"""
Examples of how to extend the Hugging Face base classes for new services.

This file shows how the base classes can be used to create new Hugging Face services
for different tasks like vision, text generation, etc.
"""

from typing import List, Dict, Any, Optional
from core.services.huggingface.base import (
    BaseHuggingFaceInferenceClient,
    BaseHuggingFaceAPIClient,
)
from core.services.huggingface.constants import (
    DEFAULT_VISION_MODEL_ID,
    HuggingFaceTaskType,
)


class HuggingFaceVisionClient(BaseHuggingFaceInferenceClient):
    """
    Example: Vision client using InferenceClient for image processing.
    """

    def __init__(self, model_id: str = DEFAULT_VISION_MODEL_ID, **kwargs):
        super().__init__(model_id=model_id, **kwargs)

    @property
    def service_name(self) -> str:
        return "Hugging Face Vision Client"

    def classify_image(self, image_data: bytes) -> Dict[str, Any]:
        """Classify an image using the vision model."""
        # This would use self.client.image_classification(image_data)
        # Implementation depends on huggingface_hub version
        return self.client.image_classification(image_data)

    def detect_objects(self, image_data: bytes) -> List[Dict[str, Any]]:
        """Detect objects in an image."""
        return self.client.object_detection(image_data)


class HuggingFaceTextGenerationClient(BaseHuggingFaceAPIClient):
    """
    Example: Text generation client using direct API calls.
    """

    def __init__(self, model_id: str = "gpt2", **kwargs):
        super().__init__(model_id=model_id, **kwargs)

    @property
    def service_name(self) -> str:
        return "Hugging Face Text Generation Client"

    def _get_health_check_payload(self) -> Dict[str, Any]:
        """Return a test payload for health checks."""
        return {"inputs": "Hello world", "parameters": {"max_length": 10}}

    def generate_text(
        self, prompt: str, max_length: int = 100, temperature: float = 0.7
    ) -> str:
        """Generate text based on a prompt."""
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": max_length,
                "temperature": temperature,
                "return_full_text": False,
            },
        }

        result = self._make_api_request(payload)
        if result and isinstance(result, list) and len(result) > 0:
            return result[0].get("generated_text", "")
        return ""

    def complete_text(self, text: str, num_completions: int = 1) -> List[str]:
        """Generate multiple completions for a text."""
        payload = {
            "inputs": text,
            "parameters": {
                "num_return_sequences": num_completions,
                "max_length": len(text) + 50,
            },
        }

        result = self._make_api_request(payload)
        if result and isinstance(result, list):
            return [item.get("generated_text", "") for item in result]
        return []


class HuggingFaceSummarizationClient(BaseHuggingFaceAPIClient):
    """
    Example: Text summarization client using direct API calls.
    """

    def __init__(self, model_id: str = "facebook/bart-large-cnn", **kwargs):
        super().__init__(model_id=model_id, **kwargs)

    @property
    def service_name(self) -> str:
        return "Hugging Face Summarization Client"

    def _get_health_check_payload(self) -> Dict[str, Any]:
        """Return a test payload for health checks."""
        return {"inputs": "This is a test document for summarization health check."}

    def summarize_text(
        self,
        text: str,
        max_length: Optional[int] = None,
        min_length: Optional[int] = None,
    ) -> str:
        """Summarize the given text."""
        payload = {"inputs": text}

        if max_length or min_length:
            payload["parameters"] = {}
            if max_length:
                payload["parameters"]["max_length"] = max_length
            if min_length:
                payload["parameters"]["min_length"] = min_length

        result = self._make_api_request(payload)
        if result and isinstance(result, list) and len(result) > 0:
            return result[0].get("summary_text", "")
        return ""


# Example usage:
if __name__ == "__main__":
    # These are just examples - they would need proper API keys and models

    # Vision client
    # vision_client = HuggingFaceVisionClient()
    # with open("image.jpg", "rb") as f:
    #     image_data = f.read()
    # result = vision_client.classify_image(image_data)

    # Text generation client
    # generator = HuggingFaceTextGenerationClient()
    # text = generator.generate_text("The future of AI is")

    # Summarization client
    # summarizer = HuggingFaceSummarizationClient()
    # summary = summarizer.summarize_text("Your long text here...")

    print("✅ Example Hugging Face service classes defined!")
    print("These show how to extend the base classes for different AI tasks.")
