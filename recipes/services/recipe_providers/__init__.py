"""Recipe provider services for sourcing recipes from external APIs and sources."""

# Import and expose the utils package
from . import utils

# Re-export commonly used utilities for convenience
from .utils import (
    parse_quantity,
    extract_name_and_notes,
    is_recipe_provider_url,
    parse_time_duration,
    extract_macros,
    extract_dietary_restrictions,
    extract_tags,
)

__all__ = [
    'utils',
    'parse_quantity',
    'extract_name_and_notes',
    'is_recipe_provider_url',
    'parse_time_duration',
    'extract_macros',
    'extract_dietary_restrictions',
    'extract_tags',
] 