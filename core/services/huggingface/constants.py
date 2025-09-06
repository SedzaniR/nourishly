# Embedding Models
PREFERRED_SENTENCE_TRANSFORMERS_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"

# Vision Models
DEFAULT_VISION_MODEL_ID = "google/vit-base-patch16-224"

# Classification Models
DEFAULT_CLASSIFICATION_MODEL_ID = "facebook/bart-large-mnli"
HUGGINGFACE_API_BASE_URL = "https://api-inference.huggingface.co/models"
# API Configuration
DEFAULT_API_TIMEOUT = 30
DEFAULT_API_MAX_RETRIES = 3
DEFAULT_API_RETRY_DELAY = 1.0
DEFAULT_API_RATE_LIMIT_DELAY = 0.1


# Common task types
class HuggingFaceTaskType:
    FEATURE_EXTRACTION = "feature-extraction"
    TEXT_CLASSIFICATION = "text-classification"
    IMAGE_CLASSIFICATION = "image-classification"
    OBJECT_DETECTION = "object-detection"
    TEXT_GENERATION = "text-generation"
    SUMMARIZATION = "summarization"
