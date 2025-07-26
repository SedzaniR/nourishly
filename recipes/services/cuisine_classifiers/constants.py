"""
Constants for cuisine classification services.
"""

# Confidence thresholds for cuisine classification
LOW_CONFIDENCE_CUISINE_CLASSIFIER_THRESHOLD = 0.6
MEDIUM_CONFIDENCE_CUISINE_CLASSIFIER_THRESHOLD = 0.8

# Default model configuration
DEFAULT_HUGGINGFACE_MODEL = "facebook/bart-large-mnli"
DEFAULT_MAX_LENGTH = 512
DEFAULT_BATCH_SIZE = 8

# API configuration
DEFAULT_API_RATE_LIMIT_DELAY = 1.0  # seconds between API requests
DEFAULT_API_MAX_RETRIES = 3
DEFAULT_API_RETRY_DELAY = 2.0  # seconds
DEFAULT_API_TIMEOUT = 30.0  # seconds

# Supported cuisine types
SUPPORTED_CUISINES = [
    "Italian",
    "Chinese",
    "Mexican",
    "Indian",
    "Japanese",
    "French",
    "Thai",
    "Mediterranean",
    "American",
    "Korean",
    "Vietnamese",
    "Spanish",
    "Greek",
    "Middle Eastern",
    "German",
    "British",
    "Turkish",
    "Moroccan",
    "Lebanese",
    "Peruvian",
    "Brazilian",
    "Caribbean",
    "African",
    "Russian",
    "Scandinavian",
    "Other",
]
