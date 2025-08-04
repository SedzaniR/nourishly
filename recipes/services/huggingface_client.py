from huggingface_hub import InferenceClient
import os

HF_API_KEY = os.getenv("HUGGINGFACE_API_TOKEN")
HF_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"

# Singleton client
hf_client = InferenceClient(api_key=HF_API_KEY)


def generate_embedding(text: str, model_id: str = HF_MODEL_ID) -> list[float]:
    return hf_client.feature_extraction(model=HF_MODEL_ID, inputs=text)
