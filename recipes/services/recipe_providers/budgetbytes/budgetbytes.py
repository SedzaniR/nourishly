import re
import time
import xml.etree.ElementTree as ET
from typing import List, Match, Optional

import requests
from recipe_scrapers import scrape_me
from ingredient_parser import parse_ingredient
from ingredient_parser.dataclasses import ParsedIngredient

from core.logger import log_debug, log_error, log_info, log_warning
from . import constants
from recipes.services.recipe_providers.utils import (
    is_recipe_provider_url,
    parse_time_duration,
    extract_tags,
    extract_dietary_restrictions,
    extract_macros,
)
from recipes import utils as service_utils
from ..base import BaseRecipeProvider, IngredientData, RecipeData


class BudgetBytesScraper(BaseRecipeProvider):
    """
    Budget Bytes recipe scraper using the recipe-scrapers package.

    Simple wrapper around recipe-scrapers for Budget Bytes recipes.
    """

    def __init__(self, **kwargs):
        """Initialize the Budget Bytes scraper.

        Args:
            **kwargs: Additional configuration options including:
                - rate_limit (float): Delay between requests in seconds (default: 2.0)
                - timeout (int): Request timeout in seconds
                - user_agent (str): Custom user agent string
        """
        super().__init__(
            base_url=constants.BUDGET_BYTES_BASE_URL,
            provider_domain=constants.BUDGET_BYTES_DOMAIN,
            rate_limit=kwargs.get("rate_limit", constants.BUDGET_BYTES_RATE_LIMIT),
            **kwargs,
        )
        log_info("Budget Bytes scraper initialized", base_url=self.base_url)

    @property
    def provider_name(self) -> str:
        """Return the provider name.

        Returns:
            str: The provider identifier "BudgetBytes"
        """
        return "BudgetBytes"

    def scrape_recipe_from_url(self, url: str) -> Optional[RecipeData]:
        """Scrape a recipe from a specific Budget Bytes URL using recipe-scrapers.

        Args:
            url (str): The Budget Bytes recipe URL to scrape.

        Returns:
            Optional[RecipeData]: Recipe data object with extracted information,
                or None if scraping failed.

        Raises:
            None: All exceptions are caught and logged, method returns None on failure.

        Example:
            >>> scraper = BudgetBytesScraper()
            >>> recipe = scraper.scrape_recipe_from_url(
            ...     "https://www.budgetbytes.com/thai-curry-fried-rice/"
            ... )
            >>> print(recipe.title if recipe else "Failed to scrape")
        """

        if not is_recipe_provider_url(url,self.provider_name):
            log_error("Invalid Budget Bytes URL", url=url, provider=self.provider_name)
            raise ValueError("Invalid Budget Bytes URL")

        log_info("Starting recipe scrape", url=url, provider=self.provider_name)
        time.sleep(constants.BUDGET_BYTES_RATE_LIMIT)

        scraper: ParsedIngredient = scrape_me(url)
        recipe_data: RecipeData = self._normalize_recipe_data(scraper, url)
        log_info(
            "Recipe scraped successfully",
            url=url,
            title=recipe_data.title,
            provider=self.provider_name,
        )

        return recipe_data

    def discover_recipe_urls(self, start_url: str, limit: int = 10) -> List[str]:
        """Discover recipe URLs from Budget Bytes sitemap.

        Args:
            start_url (str): The Budget Bytes sitemap URL or category URL to start from.
            limit (int, optional): Maximum number of recipe URLs to return. Defaults to 10.

        Returns:
            List[str]: List of discovered recipe URLs from sitemap parsing.

        Example:
            >>> scraper = BudgetBytesScraper()
            >>> urls = scraper.discover_recipe_urls("https://www.budgetbytes.com", limit=50)
            >>> len(urls) <= 50
            True
        """

        log_info(
            "Starting sitemap-based recipe URL discovery",
            limit=limit,
        )
        recipe_urls = self._discover_from_sitemap(limit)

        log_info(
            "Recipe URL discovery completed",
            discovered_count=len(recipe_urls),
            method="sitemap" if recipe_urls else "category_fallback",
        )

        return recipe_urls[:limit]

    def _discover_from_sitemap(self, limit: int) -> List[str]:
        """Discover recipe URLs from Budget Bytes sitemap.

        Args:
            limit (int): Maximum number of recipe URLs to return

        Returns:
            List[str]: List of discovered recipe URLs
        """

        discovered_urls = []

        for sitemap_url in constants.BUDGET_BYTES_SITEMAP_URLS:
            try:
                time.sleep(constants.BUDGET_BYTES_RATE_LIMIT)
                log_info("Attempting to fetch sitemap", sitemap_url=sitemap_url)
                response = requests.get(
                    sitemap_url,
                    timeout=30,
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; Recipe Scraper; +https://nourishly.app)"
                    },
                )

                if response.status_code == 200:
                    log_info("Successfully fetched sitemap", sitemap_url=sitemap_url)
                    discovered_urls = self._parse_sitemap(response.content)

                    if discovered_urls:
                        log_info(
                            "Found URLs in sitemap",
                            total_urls=len(discovered_urls),
                            sitemap_url=sitemap_url,
                        )
                        break
                else:
                    log_warning(
                        f"Sitemap request failed {sitemap_url}",
                        sitemap_url=sitemap_url,
                        status_code=response.status_code,
                    )

            except requests.exceptions.Timeout:
                log_error("Sitemap request timed out", sitemap_url=sitemap_url)
                continue
            except requests.exceptions.RequestException as e:
                log_error(
                    f"Failed to fetch sitemap {sitemap_url}", sitemap_url=sitemap_url, error=str(e)
                )
                continue
            except Exception as e:
                log_error(
                    f"Unexpected error fetching sitemap {sitemap_url}",
                    sitemap_url=sitemap_url,
                    error=str(e),
                )
                continue

        # Filter for recipe URLs and apply limit
        if discovered_urls:
            recipe_urls = self._filter_recipe_urls(discovered_urls)
            log_info(
                "Filtered recipe URLs",
                total_discovered=len(discovered_urls),
                recipes_found=len(recipe_urls),
            )
            return recipe_urls[:limit]

        return []

    def _parse_sitemap(self, xml_content: bytes) -> List[str]:
        """Parse sitemap XML and extract URLs.

        Args:
            xml_content (bytes): Raw XML content from sitemap

        Returns:
            List[str]: List of URLs found in sitemap
        """

        urls = []

        try:
            root = ET.fromstring(xml_content)

            if root.tag.endswith("sitemapindex"):
                log_info("Processing sitemap index")

                # Get all sub-sitemap URLs
                sub_sitemap_urls = []
                for sitemap in root.findall(".//sitemap:loc", constants.BUDGET_BYTES_SITEMAP_NAMESPACE):
                    sub_sitemap_url = sitemap.text
                    if sub_sitemap_url and "post-sitemap" in sub_sitemap_url:
                        sub_sitemap_urls.append(sub_sitemap_url)

                log_info(
                    "Found post sitemaps",
                    count=len(sub_sitemap_urls),
                    urls=sub_sitemap_urls,
                )

            # Handle regular sitemap (contains URLs)
            elif root.tag.endswith("urlset"):
                log_info("Processing regular sitemap")

                for url_elem in root.findall(".//sitemap:url", constants.BUDGET_BYTES_SITEMAP_NAMESPACE):
                    loc_elem = url_elem.find("sitemap:loc", constants.BUDGET_BYTES_SITEMAP_NAMESPACE)
                    if loc_elem is not None and loc_elem.text:
                        urls.append(loc_elem.text)

        except ET.ParseError as e:
            log_error(f"Failed to parse sitemap XML", error=str(e))
        except Exception as e:
            log_error(f"Unexpected error parsing sitemap", error=str(e))

        return urls

    def _filter_recipe_urls(self, urls: List[str]) -> List[str]:
        """Filter URLs to only include recipe pages.

        Args:
            urls (List[str]): List of URLs to filter

        Returns:
            List[str]: Filtered list containing only recipe URLs
        """

        recipe_urls = []

        # Patterns for recipe URLs vs other pages
        

        for url in urls:
            # Skip if URL doesn't contain budgetbytes.com
            if constants.BUDGET_BYTES_DOMAIN not in url:
                continue

            # Check if it should be excluded first
            is_excluded = any(
                re.search(pattern, url, re.IGNORECASE) for pattern in constants.BUDGET_BYTES_EXCLUDED_RECIPE_PATTERNS
            )
            if is_excluded:
                continue

            # Check if it matches recipe pattern
            is_recipe = any(
                re.search(pattern, url, re.IGNORECASE) for pattern in constants.BUDGET_BYTES_RECIPE_PATTERNS
            )

            # Additional heuristic: recipe URLs are typically shorter and don't have multiple path segments
            path_segments = (
                url.replace(constants.BUDGET_BYTES_BASE_URL, "").strip("/").split("/")
            )
            is_simple_path = len(path_segments) == 1 and len(path_segments[0]) > 3

            if (is_recipe or is_simple_path) and not is_excluded:
                recipe_urls.append(url)

        # Remove duplicates while preserving order
        seen = set()
        unique_recipe_urls = []
        for url in recipe_urls:
            if url not in seen:
                seen.add(url)
                unique_recipe_urls.append(url)

        return unique_recipe_urls


    def _normalize_recipe_data(self, scraper, source_url: str) -> RecipeData | None:
        """Convert recipe-scrapers data to standardized RecipeData format.

        Args:
            scraper: Recipe scraper object from recipe-scrapers library.
            source_url (str): The original URL where the recipe was scraped from.

        Returns:
            RecipeData: Normalized recipe data object with all available fields populated.

        Note:
            If normalization fails, returns a minimal RecipeData object with
            scrape_success=False and error details in scrape_errors.
        """
        try:

            recipe_title: str = service_utils.safely_extract_info_from_function_call(scraper.title, "Unknown Recipe")
            if recipe_title == "Unknown Recipe":
                log_error("Failed to extract recipe title", source_url=source_url)
                raise ValueError("Failed to extract recipe title")

            raw_ingredient_list: List[str] = service_utils.safely_extract_info_from_function_call(scraper.ingredients, [])
            print("raw ingredients extract", raw_ingredient_list)
            if not raw_ingredient_list:
                log_error("Failed to extract ingredients", source_url=source_url)
                raise ValueError("Failed to extract raw ingredients")

            instructions: List[str] = service_utils.safely_extract_info_from_function_call(scraper.instructions_list, [])
            if not instructions:
                log_error("Failed to extract instructions", source_url=source_url)
                raise ValueError("Failed to extract instructions")

            structured_ingredients: List[IngredientData] = self._parse_ingredients(
                raw_ingredient_list
            )

            log_debug(
                "Ingredient parsing completed",
                raw_count=len(raw_ingredient_list),
                parsed_count=len(structured_ingredients),
                sample_raw=raw_ingredient_list[:2],
            )

            recipe_data: RecipeData = RecipeData(
                title=recipe_title,
                source_url=source_url,
                description=service_utils.safely_extract_info_from_function_call(scraper.description),
                ingredients=structured_ingredients,
                instructions=instructions,
                prep_time=parse_time_duration(
                    service_utils.safely_extract_info_from_function_call(scraper.prep_time)
                ),
                cook_time=parse_time_duration(
                    service_utils.safely_extract_info_from_function_call(scraper.cook_time)
                ),
                servings=service_utils.safely_extract_info_from_function_call(scraper.yields),
                cuisine_type=service_utils.safely_extract_info_from_function_call(scraper.cuisine),
                image_url=service_utils.safely_extract_info_from_function_call(scraper.image),
                author=service_utils.safely_extract_info_from_function_call(scraper.author),
                rating=service_utils.safely_extract_info_from_function_call(scraper.ratings),
                tags=extract_tags(scraper),
                dietary_restrictions=extract_dietary_restrictions(scraper),
                nutrition=service_utils.safely_extract_info_from_function_call(scraper.nutrients),
                macros=extract_macros(scraper),
            )

            log_info(
                "Recipe data normalized successfully",
                title=recipe_data.title,
                ingredients_count=len(recipe_data.ingredients or []),
                instructions_count=len(recipe_data.instructions or []),
                has_structured_ingredients=True,
            )

            return recipe_data

        except Exception as normalization_exception:
           
            log_error(
                f"Failed to normalize recipe data {normalization_exception}",
                error=str(normalization_exception),
                raw_ingredient_list=raw_ingredient_list,
                source_url=source_url,
            )
            raise Exception(f"Failed to extract recipe informarion {normalization_exception}")

    def _parse_ingredients(self, raw_ingredients: List[str]) -> List[IngredientData]:
        """Parse ingredients into structured IngredientData format.

        Args:
            raw_ingredients (List[str]): List of raw ingredient strings.

        Returns:
            List[IngredientData]: List of parsed ingredients with structured data.

        Note:
            This method uses the ingredient_parser library to parse ingredients.
            Not to be confused with _parse_ingredients private method.
            It removes cost information and converts the ingredient text into a structured format.
            If parsing fails, it falls back to basic parsing.

        The parse_ingredient function returns a ParsedIngredient object with the following structure:
        - name: List[IngredientText] - ingredient names with confidence scores
        - amount: List[IngredientAmount] - quantities and units
        - preparation: IngredientText - preparation instructions
        - size: IngredientText - size descriptors
        - comment: IngredientText - additional notes
        """

        parsed_ingredients: List[IngredientData] = []

        for ingredient_text in raw_ingredients:
            if not ingredient_text:
                log_error(
                    "Empty ingredient text",
                    raw_ingredients=raw_ingredients,
                    ingredient_text=ingredient_text,
                )
                raise ValueError("Cannot process empty ingredients")

            cleaned_ingredient_text = self._remove_cost_info(ingredient_text)

            parsed: Optional[ParsedIngredient] = parse_ingredient(
                cleaned_ingredient_text
            )
            
            if not parsed or (parsed and not (parsed.name)):
                log_info(
                    f"Failed to parse ingredient with ingredient_parser: {cleaned_ingredient_text}",
                    ingredient=cleaned_ingredient_text,
                )
                raise Exception("Failed to extract ingredient information.")
            else:
                ingredient_data = IngredientData(
                    name=parsed.name[0].text if parsed.name else "unknown",
                    quantity=(
                        float(parsed.amount[0].quantity) if parsed.amount else None
                    ),
                    unit=str(parsed.amount[0].unit) if parsed.amount else None,
                    notes=parsed.preparation.text if parsed.preparation else None,
                    original_text=ingredient_text,
                )

            parsed_ingredients.append(ingredient_data)

        return parsed_ingredients

    def _remove_cost_info(self, text: str) -> str:
        """Remove cost information from ingredient text.

        Removes any parenthetical content that contains a dollar sign,
        and cleans up the resulting text formatting.

        Args:
            text (str): Original ingredient text with potential cost info.

        Returns:
            str: Cleaned text with cost information removed.

        Examples:
            >>> scraper._remove_cost_info("2 tomatoes (vine ripe, $1.28)")
            "2 tomatoes (vine ripe)"
            >>> scraper._remove_cost_info("¼ tsp salt ($0.01)")
            "¼ tsp salt"
            >>> scraper._remove_cost_info("butter (room temperature, $1.98*)")
            "butter (room temperature)"
        """

        # Remove any parenthetical content that contains a dollar sign
        # This handles cases like:
        # - ($1.28) -> removed entirely
        # - (vine ripe, $1.28) -> becomes (vine ripe)
        # - (room temperature, $1.98*) -> becomes (room temperature)

        def clean_parentheses(regex_match: Match[str]) -> str:
            parenthetical_content = regex_match.group(1)  # Content inside parentheses
            if "$" in parenthetical_content:
                # Remove the cost part (anything from $ to end or to comma)
                # Split by comma and keep parts that don't contain $
                content_parts = [
                    part.strip() for part in parenthetical_content.split(",")
                ]
                non_cost_parts = [part for part in content_parts if "$" not in part]

                if non_cost_parts:
                    return f"({', '.join(non_cost_parts)})"
                else:
                    return ""  # Remove entire parentheses if only cost info
            else:
                return regex_match.group(0)  # Keep original if no $ sign

        # Find and clean all parenthetical content
        cleaned_text = re.sub(r"\(([^)]*)\)", clean_parentheses, text)

        # Clean up any resulting formatting issues
        cleaned_text = re.sub(r"\s*,\s*\)", ")", cleaned_text)  # Fix ", )" -> ")"
        cleaned_text = re.sub(r"\(\s*\)", "", cleaned_text)  # Remove empty "()"
        cleaned_text = re.sub(r"\s+", " ", cleaned_text.strip())  # Normalize whitespace
        cleaned_text = cleaned_text.rstrip(",").strip()  # Remove trailing commas

        return cleaned_text
