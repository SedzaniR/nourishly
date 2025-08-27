"""
Utility functions for recipe processing and data extraction.

This module provides common functionality that can be reused across
different recipe providers and services.
"""

import re
from typing import Optional, Any, Callable


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
        self, method: Callable[[], Any], default_value: Any = None
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
        except Exception:
            return default_value