from huggingface_hub import InferenceClient
import os

HF_API_KEY = os.getenv("HUGGINGFACE_API_TOKEN")


# Singleton client


def generate_embedding(text: str, model_id: str = None) -> list[float]:

    if model_id is None:
        model_id = "sentence-transformers/all-MiniLM-L6-v2"
    hf_client = InferenceClient(model=model_id, api_key=HF_API_KEY)
    response = hf_client.feature_extraction(text)
    return response.data
