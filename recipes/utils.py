"""
Utility functions for recipe processing and data extraction.

This module provides common functionality that can be reused across
different recipe providers and services.
"""

import re
from typing import Optional, Any, Callable

import logging

logger = logging.getLogger(__name__)


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


def safely_extract_info_from_function_call(
    method: Callable[[], Any], default_value: Any = None
) -> Any:
    """Safely extract data from recipe-scrapers methods.

    Args:
        method (Callable[[], Any]): Recipe-scrapers method to call (e.g., scraper.title).
        default_value (Any): Default value to return if extraction fails or returns None.

    Returns:
        Any: Extracted data from the method call, or default value on failure.

    Note:
        This wrapper prevents exceptions from recipe-scrapers methods
        from breaking the entire scraping process.
    """
    try:
        extraction_result: Any = method()
        return extraction_result if extraction_result is not None else default_value
    except Exception as e:
        logger.error(
            f"Failed to extract data from method {method.__name__} with default value {default_value} and error {str(e)}",
        )
        return default_value


def parse_time_string(time_str: Optional[str]) -> Optional[int]:
    """Parse time strings (e.g., "30 minutes", "1 hour 15 min") to minutes.

    Args:
        time_str: Time string to parse.

    Returns:
        Time in minutes, or None if parsing fails.
    """
    if not time_str:
        return None

    # Common time patterns
    time_str = time_str.lower()

    # Extract hours and minutes
    hour_match = re.search(r"(\d+)\s*h(?:our)?s?", time_str)
    minute_match = re.search(r"(\d+)\s*m(?:in)?(?:ute)?s?", time_str)

    total_minutes = 0

    if hour_match:
        total_minutes += int(hour_match.group(1)) * 60

    if minute_match:
        total_minutes += int(minute_match.group(1))

    # If no specific pattern found, try to extract just numbers
    if total_minutes == 0:
        number_match = re.search(r"(\d+)", time_str)
        if number_match:
            total_minutes = int(number_match.group(1))

    return total_minutes if total_minutes > 0 else None
