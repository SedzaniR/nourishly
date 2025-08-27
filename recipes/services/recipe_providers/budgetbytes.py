from fractions import Fraction
import re
import time
from datetime import datetime
import xml.etree.ElementTree as ET
from typing import Any, Callable, Dict, List, Match, Optional, Tuple
from urllib.parse import ParseResult, urlparse

from bs4 import BeautifulSoup
import requests
from recipe_scrapers import SCRAPERS, scrape_me
from ingredient_parser import parse_ingredient
from ingredient_parser.dataclasses import ParsedIngredient

from core.logger import log_debug, log_error, log_info, log_warning
from recipes.services.recipe_providers import constants
from recipes.utils import extract_numeric_value_from_string

from .base import BaseRecipeProvider, IngredientData, MacroNutrition, RecipeData


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

        if not self._is_budget_bytes_url(url):
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

        if not recipe_urls:
            log_info("Sitemap discovery failed, falling back to category crawling")
            recipe_urls = self._discover_from_categories(start_url, limit)

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

                # Fetch each post sitemap
                for sub_sitemap_url in sub_sitemap_urls:
                    sub_urls = self._fetch_sub_sitemap(sub_sitemap_url)
                    if sub_urls:
                        log_info(
                            "Successfully fetched sub-sitemap",
                            url=sub_sitemap_url,
                            url_count=len(sub_urls),
                        )
                        urls.extend(sub_urls)

                        # Limit sub-sitemap fetching to avoid too many requests
                        if len(urls) > 5000:  # Stop if we have enough URLs
                            break
                    else:
                        log_warning("Failed to fetch sub-sitemap", url=sub_sitemap_url)

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

    def _fetch_sub_sitemap(self, sitemap_url: str) -> List[str]:
        """Fetch and parse a sub-sitemap.

        Args:
            sitemap_url (str): URL of the sub-sitemap to fetch

        Returns:
            List[str]: List of URLs from the sub-sitemap
        """
        try:
            # Rate limiting
            time.sleep(self.rate_limit_delay)

            log_info("Fetching sub-sitemap", sitemap_url=sitemap_url)

            response = requests.get(
                sitemap_url,
                timeout=30,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; Recipe Scraper; +https://nourishly.app)"
                },
            )

            if response.status_code == 200:
                log_info(
                    "Successfully downloaded sub-sitemap",
                    sitemap_url=sitemap_url,
                    size_bytes=len(response.content),
                )
                parsed_urls = self._parse_sitemap(response.content)
                log_info(
                    "Parsed sub-sitemap",
                    sitemap_url=sitemap_url,
                    url_count=len(parsed_urls),
                )
                return parsed_urls
            else:
                log_warning(
                    "Sub-sitemap request failed",
                    sitemap_url=sitemap_url,
                    status_code=response.status_code,
                )
                return []

        except requests.exceptions.Timeout:
            log_error("Sub-sitemap request timed out", sitemap_url=sitemap_url)
            return []
        except requests.exceptions.RequestException as e:
            log_error(
                "Failed to fetch sub-sitemap (RequestException)",
                sitemap_url=sitemap_url,
                error=str(e),
            )
            return []
        except Exception as e:
            log_error(
                "Failed to fetch sub-sitemap (Exception)",
                sitemap_url=sitemap_url,
                error=str(e),
                error_type=type(e).__name__,
            )
            return []

    def _filter_recipe_urls(self, urls: List[str]) -> List[str]:
        """Filter URLs to only include recipe pages.

        Args:
            urls (List[str]): List of URLs to filter

        Returns:
            List[str]: Filtered list containing only recipe URLs
        """

        recipe_urls = []

        # Patterns for recipe URLs vs other pages
        recipe_patterns = [
            r"budgetbytes\.com/[^/]+/$",  # Single recipe pages like /recipe-name/
            r"budgetbytes\.com/[a-z0-9-]+/$",  # Recipe slugs (letters, numbers, hyphens)
        ]

        exclude_patterns = [
            r"budgetbytes\.com/category/",  # Category pages
            r"budgetbytes\.com/tag/",  # Tag pages
            r"budgetbytes\.com/page/",  # Pagination
            r"budgetbytes\.com/author/",  # Author pages
            r"budgetbytes\.com/\d{4}/",  # Date archives (2024/)
            r"budgetbytes\.com/search/",  # Search pages
            r"budgetbytes\.com/index/",  # Index pages
            r"budgetbytes\.com/(about|contact|faq|privacy|terms)",  # Static pages
            r"budgetbytes\.com/(login|register|account)",  # User pages
            r"budgetbytes\.com/extra-bytes/",  # Non-recipe content
            r"budgetbytes\.com/weekly-recap",  # Weekly recap posts
            r"budgetbytes\.com/.*-recap",  # Other recap posts
            r"budgetbytes\.com/.*-challenge",  # Challenge posts
            r"budgetbytes\.com/.*-week-\d+",  # Weekly challenge posts
            r"budgetbytes\.com/feeding-america",  # Special campaign posts
            r"budgetbytes\.com/meal-plans?$",  # Meal plan pages (not recipes)
            r"budgetbytes\.com/.*-meal-plan",  # Weekly meal plan posts
            r"budgetbytes\.com/roundup",  # Recipe roundup posts
            r"budgetbytes\.com/.*-giveaway",  # Giveaway posts
            r"budgetbytes\.com/best-of-",  # Best of compilation posts
            r"budgetbytes\.com/top-\d+",  # Top N recipes posts
            r"budgetbytes\.com/.*-\d{4}/$",  # Year-based compilation posts (e.g., best-of-2023)
            r"budgetbytes\.com/prices-and-portions",  # Non-recipe informational pages
        ]

        for url in urls:
            # Skip if URL doesn't contain budgetbytes.com
            if "budgetbytes.com" not in url:
                continue

            # Check if it should be excluded first
            is_excluded = any(
                re.search(pattern, url, re.IGNORECASE) for pattern in exclude_patterns
            )
            if is_excluded:
                continue

            # Check if it matches recipe pattern
            is_recipe = any(
                re.search(pattern, url, re.IGNORECASE) for pattern in recipe_patterns
            )

            # Additional heuristic: recipe URLs are typically shorter and don't have multiple path segments
            path_segments = (
                url.replace("https://www.budgetbytes.com/", "").strip("/").split("/")
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

    def _discover_from_categories(self, start_url: str, limit: int) -> List[str]:
        """Fallback method to discover recipe URLs by crawling category pages.

        Args:
            start_url (str): Starting URL (not used in this implementation)
            limit (int): Maximum number of recipe URLs to return

        Returns:
            List[str]: List of discovered recipe URLs from category crawling
        """
        log_info("Starting category-based recipe discovery (fallback method)")

        # Main recipe categories on Budget Bytes
        category_urls = [
            "https://www.budgetbytes.com/category/recipes/main-dish/",
            "https://www.budgetbytes.com/category/recipes/side-dish/",
            "https://www.budgetbytes.com/category/recipes/breakfast/",
            "https://www.budgetbytes.com/category/recipes/appetizer/",
            "https://www.budgetbytes.com/category/recipes/dessert/",
            "https://www.budgetbytes.com/category/recipes/soup/",
            "https://www.budgetbytes.com/category/recipes/salad/",
        ]

        discovered_urls = []

        for category_url in category_urls:
            if len(discovered_urls) >= limit:
                break

            try:
                category_recipe_urls = self._crawl_category_page(
                    category_url, limit - len(discovered_urls)
                )
                discovered_urls.extend(category_recipe_urls)

                log_info(
                    "Crawled category page",
                    category_url=category_url,
                    found_recipes=len(category_recipe_urls),
                    total_discovered=len(discovered_urls),
                )

            except Exception as e:
                log_error(
                    "Failed to crawl category page",
                    category_url=category_url,
                    error=str(e),
                )
                continue

        return discovered_urls[:limit]

    def _crawl_category_page(self, category_url: str, limit: int) -> List[str]:
        """Crawl a single category page to extract recipe URLs.

        Args:
            category_url (str): URL of the category page to crawl
            limit (int): Maximum number of recipe URLs to extract

        Returns:
            List[str]: List of recipe URLs found on the category page
        """

        recipe_urls = []

        try:
            # Rate limiting
            time.sleep(self.rate_limit_delay)

            response = requests.get(
                category_url,
                timeout=30,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; Recipe Scraper; +https://nourishly.app)"
                },
            )

            if response.status_code != 200:
                log_warning(
                    "Category page request failed",
                    category_url=category_url,
                    status_code=response.status_code,
                )
                return []

            soup = BeautifulSoup(response.content, "html.parser")

            # Look for recipe links - Budget Bytes typically uses article elements or specific CSS classes
            # This is a generic approach that should work for most WordPress recipe sites
            recipe_links = []

            # Try different selectors that commonly contain recipe links
            selectors = [
                "article h2 a[href]",  # Article titles
                "article h3 a[href]",  # Alternative article titles
                ".recipe-card a[href]",  # Recipe cards
                ".post-title a[href]",  # Post titles
                "h2.entry-title a[href]",  # Entry titles
                ".entry-header a[href]",  # Entry headers
            ]

            for selector in selectors:
                links = soup.select(selector)
                if links:
                    recipe_links.extend(links)
                    break  # Use the first selector that finds links

            # Extract URLs and filter
            for link in recipe_links:
                href = link.get("href")
                if href:
                    # Convert relative URLs to absolute
                    if href.startswith("/"):
                        href = "https://www.budgetbytes.com" + href

                    # Basic filtering - should be a Budget Bytes recipe URL
                    if (
                        href.startswith("https://www.budgetbytes.com/")
                        and "/category/" not in href
                        and "/tag/" not in href
                        and "/page/" not in href
                    ):
                        recipe_urls.append(href)

                        if len(recipe_urls) >= limit:
                            break

        except Exception as e:
            log_error(
                "Failed to crawl category page", category_url=category_url, error=str(e)
            )

        return recipe_urls

    def validate_scraping_config(self) -> bool:
        """Validate the scraper configuration.

        Checks if Budget Bytes is supported by the recipe-scrapers library.

        Returns:
            bool: True if Budget Bytes is supported by recipe-scrapers, False otherwise.

        Example:
            >>> scraper = BudgetBytesScraper()
            >>> if scraper.validate_scraping_config():
            ...     print("Ready to scrape Budget Bytes recipes")
        """
        try:
            # Check if Budget Bytes is supported by recipe-scrapers
            supported_sites: List[str] = SCRAPERS.keys()

            is_supported: bool = any(
                "budgetbytes" in site.lower() for site in supported_sites
            )

            log_info(
                "Scraper configuration validated",
                is_supported=is_supported,
                total_supported_sites=len(supported_sites),
            )

            return is_supported

        except Exception as validation_exception:
            log_error(
                "Scraper configuration validation failed",
                error=str(validation_exception),
            )
            return False

    def is_site_accessible(self) -> bool:
        """Check if Budget Bytes website is accessible for scraping.

        Performs a test scrape of a known Budget Bytes recipe to verify
        the site is accessible and responding properly.

        Returns:
            bool: True if the site is accessible and can be scraped, False otherwise.

        Note:
            This method makes an actual HTTP request to Budget Bytes,
            so it may be slow and should be used sparingly.
        """
        try:
            # Simple test scrape to check accessibility
            TEST_URL: str = f"{self.base_url}/recipe/basic-meatballs/"
            scraper: Any = scrape_me(TEST_URL)

            # If we can get a title, site is accessible
            title: str = scraper.title()
            is_accessible: bool = bool(title)

            log_info(
                "Site accessibility check",
                is_accessible=is_accessible,
                site=self.base_url,
            )

            return is_accessible

        except Exception as accessibility_exception:
            log_error(
                "Site accessibility check failed",
                error=str(accessibility_exception),
                site=self.base_url,
            )
            return False

    def extract_structured_data(self, html_content: str) -> Optional[Dict[str, Any]]:
        """Extract structured data from HTML content.

        Args:
            html_content (str): Raw HTML content of a recipe page.

        Returns:
            Optional[Dict[str, Any]]: Always returns None since recipe-scrapers
                handles structured data extraction internally.

        Note:
            This method is part of the BaseRecipeProvider interface but is not
            needed for this implementation since recipe-scrapers handles
            structured data extraction automatically.
        """
        # recipe-scrapers handles this automatically
        log_info("Structured data extraction handled by recipe-scrapers")
        return None

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

            recipe_title: str = self._safe_extract(scraper.title, "Unknown Recipe")
            if recipe_title == "Unknown Recipe":
                log_error("Failed to extract recipe title", source_url=source_url)
                raise ValueError("Failed to extract recipe title")

            raw_ingredient_list: List[str] = self._safe_extract(scraper.ingredients, [])

            if not raw_ingredient_list:
                log_error("Failed to extract ingredients", source_url=source_url)
                raise ValueError("Failed to extract raw ingredients")

            instructions: List[str] = self._safe_extract(scraper.instructions_list, [])
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
                description=self._safe_extract(scraper.description),
                ingredients=structured_ingredients,
                instructions=instructions,
                prep_time=self._parse_time_duration(
                    self._safe_extract(scraper.prep_time)
                ),
                cook_time=self._parse_time_duration(
                    self._safe_extract(scraper.cook_time)
                ),
                servings=self._safe_extract(scraper.yields),
                cuisine_type=self._safe_extract(scraper.cuisine),
                image_url=self._safe_extract(scraper.image),
                author=self._safe_extract(scraper.author),
                rating=self._safe_extract(scraper.ratings),
                tags=self._extract_tags(scraper),
                dietary_restrictions=self._extract_dietary_restrictions(scraper),
                nutrition=self._safe_extract(scraper.nutrients),
                macros=self._extract_macros(scraper),
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
            return None

    def _safe_extract(
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

    def _parse_time_duration(self, duration: Any) -> Optional[int]:
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

        # recipe-scrapers returns timedelta objects
        if hasattr(duration, "total_seconds"):
            return int(duration.total_seconds() / 60)

        # Fallback to string parsing
        return self._parse_time_string(str(duration))

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

    def _parse_quantity(self, quantity_str: str) -> Optional[float]:
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

    def _extract_name_and_notes(self, text: str) -> Tuple[str, Optional[str]]:
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

    def _extract_tags(self, scraper: Any) -> List[str]:
        """Extract tags from recipe-scrapers data.

        Args:
            scraper (Any): Recipe scraper object from recipe-scrapers library.

        Returns:
            List[str]: List of tags extracted from category and cuisine fields,
                with duplicates and empty values removed.
        """
        extracted_tags = []

        # Extract from category
        recipe_category = self._safe_extract(scraper.category)
        if recipe_category:
            extracted_tags.append(recipe_category)

        # Extract from cuisine
        cuisine_type = self._safe_extract(scraper.cuisine)
        if cuisine_type:
            extracted_tags.append(cuisine_type)

        # Remove duplicates and None values
        return [tag for tag in extracted_tags if tag and tag.strip()]

    def _extract_dietary_restrictions(self, scraper: Any) -> List[str]:
        """Extract dietary restrictions from recipe-scrapers data.

        Args:
            scraper (Any): Recipe scraper object from recipe-scrapers library.

        Returns:
            List[str]: List of dietary restrictions extracted from the recipe,
                with duplicates and empty values removed.

        Note:
            Uses the dietary_restrictions() method from recipe-scrapers which
            extracts dietary guidelines or restrictions for the recipe.
        """
        try:
            restrictions = self._safe_extract(scraper.dietary_restrictions)

            if not restrictions:
                return []

            # Handle different return types from recipe-scrapers
            if isinstance(restrictions, str):
                # If it's a single string, split by common delimiters
                restriction_list = [
                    restriction.strip().lower()
                    for restriction in re.split(r"[,;&|]", restrictions)
                    if restriction.strip()
                ]
                return restriction_list
            elif isinstance(restrictions, list):
                # If it's already a list, clean and normalize
                return [
                    restriction.strip().lower()
                    for restriction in restrictions
                    if restriction and restriction.strip()
                ]
            else:
                return []

        except Exception:
            # If dietary_restrictions method fails, return empty list
            return []

    def _extract_macros(self, scraper: Any) -> Optional[MacroNutrition]:
        """Extract nutritional macro information from recipe scraper.

        Uses the reusable extract_numeric_value utility to parse nutrition strings.

        Args:
            scraper (Any): Recipe scraper object from recipe-scrapers library.

        Returns:
            Optional[MacroNutrition]: Structured macro nutrition data, or None if unavailable.
        """
        try:
            # Get nutrition data directly from recipe-scrapers
            nutrients = scraper.nutrients()
            if not nutrients:
                return None

            # Use utility to extract numbers from strings like "211 kcal", "13 g"
            macros = MacroNutrition(
                calories=extract_numeric_value_from_string(nutrients.get("calories")),
                protein=extract_numeric_value_from_string(
                    nutrients.get("proteinContent")
                ),
                carbohydrates=extract_numeric_value_from_string(
                    nutrients.get("carbohydrateContent")
                ),
                fat=extract_numeric_value_from_string(nutrients.get("fatContent")),
                fiber=extract_numeric_value_from_string(nutrients.get("fiberContent")),
                sugar=extract_numeric_value_from_string(nutrients.get("sugarContent")),
                sodium=extract_numeric_value_from_string(
                    nutrients.get("sodiumContent")
                ),
                saturated_fat=extract_numeric_value_from_string(
                    nutrients.get("saturatedFatContent")
                ),
                cholesterol=extract_numeric_value_from_string(
                    nutrients.get("cholesterolContent")
                ),
            )

            # Return only if we got at least one value
            if any(
                getattr(macros, field) is not None
                for field in constants.MACROS_TO_EXTRACT
            ):
                log_debug(
                    "Macros extracted", calories=macros.calories, protein=macros.protein
                )
                return macros

            return None

        except Exception as e:
            log_error("Failed to extract macros", error=str(e))
            return None

    def _is_budget_bytes_url(self, url: str) -> bool:
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
            return "budgetbytes.com" in parsed.netloc.lower()
        except:
            return False
