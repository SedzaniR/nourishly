import re
from fractions import Fraction
from typing import Optional, Tuple, Any, List
from urllib.parse import ParseResult, urlparse

from recipes.utils import parse_time_string
from recipes.services.recipe_providers import constants


def parse_quantity(quantity_str: str) -> Optional[float]:
        """Parse quantity string to float, handling fractions and mixed numbers.

        Args:
            quantity_str (str): Quantity string like "2", "1/2", "1 1/2", "¼"

        Returns:
            Optional[float]: Parsed quantity or None if parsing fails.
        """

        try:
            for unicode_fraction, fraction_value in constants.UNICODE_FRACTIONS.items():
                if unicode_fraction in quantity_str:
                    # Handle mixed numbers like "1¼"
                    number_parts = quantity_str.split(unicode_fraction)
                    if number_parts[0].strip():
                        return float(number_parts[0].strip()) + fraction_value
                    else:
                        return fraction_value

            # Handle mixed numbers like "1 1/2"
            mixed_number_match = re.match(r"(\d+)\s+(\d+)/(\d+)", quantity_str.strip())
            if mixed_number_match:
                whole_number = int(mixed_number_match.group(1))
                fraction_part = Fraction(
                    int(mixed_number_match.group(2)), int(mixed_number_match.group(3))
                )
                return float(whole_number + fraction_part)

            # Handle simple fractions like "1/2"
            if "/" in quantity_str:
                return float(Fraction(quantity_str.strip()))

            # Handle decimal numbers
            return float(quantity_str.strip())

        except (ValueError, ZeroDivisionError):
            return None


def extract_name_and_notes(text: str) -> Tuple[str, Optional[str]]:
        """Extract ingredient name and preparation notes from text.

        Args:
            text (str): Text containing ingredient name and possibly notes in parentheses.

        Returns:
            Tuple[str, Optional[str]]: (ingredient_name, preparation_notes)
        """

        # Look for notes in parentheses
        parentheses_match = re.search(r"\(([^)]+)\)", text)
        if parentheses_match:
            preparation_notes = parentheses_match.group(1).strip()
            ingredient_name = re.sub(r"\([^)]+\)", "", text).strip()
            return ingredient_name, preparation_notes if preparation_notes else None

        return text.strip(), None

def is_recipe_provider_url(url: str,recipe_provider_domain:str) -> bool:
        """Check if the URL is from Budget Bytes website.

        Args:
            url (str): URL to validate.

        Returns:
            bool: True if URL is from budgetbytes.com domain, False otherwise.

        Note:
            This validation ensures the scraper only processes Budget Bytes URLs
            and prevents accidental scraping of other websites.
        """
        try:
            parsed: ParseResult = urlparse(url)
            return recipe_provider_domain.lower() in parsed.netloc.lower()
        except:
            return False

def parse_time_duration(duration: Any) -> Optional[int]:
        """Parse time duration to minutes.

        Args:
            duration (Any): Time duration from recipe-scrapers (timedelta object or string).

        Returns:
            Optional[int]: Duration in minutes, or None if parsing fails.

        Note:
            recipe-scrapers typically returns timedelta objects, but this method
            also handles string fallback for compatibility.
        """
        if not duration:
            return None

   
        if hasattr(duration, "total_seconds"):
            return int(duration.total_seconds() / 60)

        return parse_time_string(str(duration))