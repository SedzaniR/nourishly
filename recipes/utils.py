"""
Utility functions for recipe processing and data extraction.

This module provides common functionality that can be reused across
different recipe providers and services.
"""

import re
from typing import Optional, Any


def extract_numeric_value_from_string(value: Any) -> Optional[float]:
    """Extract numeric value from various data types and formats.

    Handles common nutrition data formats like:
    - "211 kcal" → 211.0
    - "13 g" → 13.0
    - "638 mg" → 638.0
    - "1.5" → 1.5
    - 42 → 42.0

    Args:
        value: The value to extract a number from (string, int, float, or None)

    Returns:
        Optional[float]: Extracted numeric value, or None if no number found

    Example:
        >>> extract_numeric_value_from_string("211 kcal")
        211.0
        >>> extract_numeric_value_from_string("13 g")
        13.0
        >>> extract_numeric_value_from_string(42)
        42.0
        >>> extract_numeric_value_from_string("no numbers here")
        None
    """
    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        # Extract first decimal/integer number found
        match = re.search(r"(\d+(?:\.\d+)?)", value)
        return float(match.group(1)) if match else None

    return None
