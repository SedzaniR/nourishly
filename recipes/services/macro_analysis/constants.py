"""Constants for macro analysis services."""

from enum import Enum


class MacroAnalysisProvider(Enum):
    """Available macro analysis providers."""

    API_NINJA = "api_ninja"
    USDA = "usda"


# Default confidence levels for different providers
PROVIDER_CONFIDENCE_LEVELS = {
    MacroAnalysisProvider.API_NINJA: 0.8,  # Full API access with all nutrients
    MacroAnalysisProvider.USDA: 0.9,
}

# Default timeout for API requests (seconds)
DEFAULT_REQUEST_TIMEOUT = 30

# Maximum number of items to analyze in a single batch request
MAX_BATCH_SIZE = 50

# Minimum required fields for a valid macro analysis
REQUIRED_MACRO_FIELDS = ["calories", "protein", "carbohydrates", "fat"]

# Macro nutrient calorie values per gram
MACRO_CALORIES_PER_GRAM = {
    "protein": 4.0,
    "carbohydrates": 4.0,
    "fat": 9.0,
    "alcohol": 7.0,
}

# Rate limiting for API requests
RATE_LIMIT_REQUESTS_PER_MINUTE = 60
RATE_LIMIT_REQUESTS_PER_HOUR = 1000
API_NINJA_BASE_URL = "https://api.api-ninjas.com/v1/nutrition"
