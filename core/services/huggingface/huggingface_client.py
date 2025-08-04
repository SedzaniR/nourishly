import os

from huggingface_hub import InferenceClient

from .constants import PREFERRED_SENTENCE_TRANSFORMERS_MODEL_ID


HF_API_KEY = os.getenv("HUGGINGFACE_API_TOKEN")


# Singleton client


class HuggingFaceInferenceClient:
    def __init__(self, model_id: str = PREFERRED_SENTENCE_TRANSFORMERS_MODEL_ID):
        self.model_id = model_id
        self.hf_client = InferenceClient(model=self.model_id, api_key=HF_API_KEY)

    def generate_embedding(self, text: str) -> list[float]:
        response = self.hf_client.feature_extraction(text)
        return response.data
