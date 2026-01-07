"""
Tests for BudgetBytes recipe scraper service.

This module contains comprehensive tests for the BudgetBytesScraper class,
including URL validation, recipe scraping, sitemap parsing, and ingredient parsing.
"""

from django.test import TestCase
from unittest.mock import Mock, patch
import requests

from recipes.services.recipe_providers.budgetbytes.budgetbytes import BudgetBytesScraper
from recipes.services.recipe_providers.base import RecipeData, IngredientData
from recipes.services.recipe_providers.budgetbytes import constants


class BudgetBytesScraperInitializationTestCase(TestCase):
    """Test BudgetBytesScraper initialization and configuration."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        scraper = BudgetBytesScraper()

        self.assertEqual(scraper.base_url, constants.BUDGET_BYTES_BASE_URL)
        self.assertEqual(scraper.provider_domain, constants.BUDGET_BYTES_DOMAIN)
        self.assertEqual(scraper.rate_limit, constants.BUDGET_BYTES_RATE_LIMIT)
        self.assertEqual(scraper.provider_name, "BudgetBytes")


class ProcessRecipeFromUrlTestCase(TestCase):
    """Test process_recipe_from_url method."""

    @patch("recipes.services.recipe_providers.budgetbytes.budgetbytes.scrape_me")
    @patch("recipes.services.recipe_providers.budgetbytes.budgetbytes.time.sleep")
    @patch(
        "recipes.services.recipe_providers.budgetbytes.budgetbytes.is_recipe_provider_url"
    )
    @patch.object(BudgetBytesScraper, "_normalize_recipe_data")
    def test_process_recipe_from_url_returns_recipe_data(
        self, mock_normalize, mock_is_valid_url, mock_sleep, mock_scrape_me
    ):
        """Test that process_recipe_from_url returns a RecipeData object with required fields."""
        test_url = "https://www.budgetbytes.com/test-recipe/"
        mock_is_valid_url.return_value = True

        # Create a minimal valid RecipeData object
        expected_recipe = RecipeData(
            title="Test Recipe",
            source_url=test_url,
            ingredients=[IngredientData(name="test", quantity=1.0, unit="cup")],
            instructions=["Step 1", "Step 2"],
        )
        mock_normalize.return_value = expected_recipe
        mock_scrape_me.return_value = Mock()

        scraper = BudgetBytesScraper()
        result = scraper.process_recipe_from_url(test_url)

        # Verify return type and required fields
        self.assertIsNotNone(result)
        self.assertIsInstance(result, RecipeData)
        self.assertEqual(result.title, "Test Recipe")
        self.assertEqual(result.source_url, test_url)
        self.assertIsNotNone(result.ingredients)
        self.assertIsNotNone(result.instructions)

        # Verify the method was called correctly
        mock_is_valid_url.assert_called_once_with(test_url, "BudgetBytes")
        mock_sleep.assert_called_once_with(constants.BUDGET_BYTES_RATE_LIMIT)
        mock_scrape_me.assert_called_once_with(test_url)
        mock_normalize.assert_called_once()

    @patch(
        "recipes.services.recipe_providers.budgetbytes.budgetbytes.is_recipe_provider_url"
    )
    def test_process_recipe_from_url_invalid_url(self, mock_is_valid_url):
        """Test that invalid URLs raise ValueError."""
        test_url = "https://www.example.com/recipe/"
        mock_is_valid_url.return_value = False

        scraper = BudgetBytesScraper()

        with self.assertRaises(ValueError) as context:
            scraper.process_recipe_from_url(test_url)

        self.assertIn("Invalid Budget Bytes URL", str(context.exception))

    @patch("recipes.services.recipe_providers.budgetbytes.budgetbytes.scrape_me")
    @patch("recipes.services.recipe_providers.budgetbytes.budgetbytes.time.sleep")
    @patch(
        "recipes.services.recipe_providers.budgetbytes.budgetbytes.is_recipe_provider_url"
    )
    @patch.object(BudgetBytesScraper, "_normalize_recipe_data")
    def test_process_recipe_from_url_raises_error_on_normalization_failure(
        self, mock_normalize, mock_is_valid_url, mock_sleep, mock_scrape_me
    ):
        """Test that normalization errors are properly raised."""
        test_url = "https://www.budgetbytes.com/recipe/"
        mock_is_valid_url.return_value = True
        mock_scrape_me.return_value = Mock()
        mock_normalize.side_effect = ValueError("Failed to extract recipe title")

        scraper = BudgetBytesScraper()

        with self.assertRaises(ValueError) as context:
            scraper.process_recipe_from_url(test_url)

        self.assertIn("Failed to extract recipe title", str(context.exception))


class DiscoverRecipeUrlsTestCase(TestCase):
    """Test discover_recipe_urls method."""

    @patch(
        "recipes.services.recipe_providers.budgetbytes.budgetbytes.BudgetBytesScraper._discover_from_sitemap"
    )
    def test_discover_recipe_urls_with_limit(self, mock_discover):
        """Test discover_recipe_urls respects limit parameter."""
        mock_discover.return_value = [
            "https://www.budgetbytes.com/recipe1/",
            "https://www.budgetbytes.com/recipe2/",
            "https://www.budgetbytes.com/recipe3/",
        ]

        scraper = BudgetBytesScraper()
        result = scraper.discover_recipe_urls(limit=2)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "https://www.budgetbytes.com/recipe1/")
        self.assertEqual(result[1], "https://www.budgetbytes.com/recipe2/")

    @patch(
        "recipes.services.recipe_providers.budgetbytes.budgetbytes.BudgetBytesScraper._discover_from_sitemap"
    )
    def test_discover_recipe_urls_empty_result(self, mock_discover):
        """Test discover_recipe_urls handles empty results."""
        mock_discover.return_value = []

        scraper = BudgetBytesScraper()
        result = scraper.discover_recipe_urls(limit=10)

        self.assertEqual(result, [])


class DiscoverFromSitemapTestCase(TestCase):
    """Test _discover_from_sitemap method."""

    @patch("recipes.services.recipe_providers.budgetbytes.budgetbytes.requests.get")
    @patch("recipes.services.recipe_providers.budgetbytes.budgetbytes.time.sleep")
    def test_discover_from_sitemap_success(self, mock_sleep, mock_get):
        """Test successful sitemap discovery."""
        # Mock XML response
        xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://www.budgetbytes.com/recipe1/</loc>
            </url>
            <url>
                <loc>https://www.budgetbytes.com/recipe2/</loc>
            </url>
        </urlset>"""

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = xml_content
        mock_get.return_value = mock_response

        scraper = BudgetBytesScraper()
        result = scraper._discover_from_sitemap(limit=10)

        self.assertEqual(len(result), 2)
        self.assertIn("https://www.budgetbytes.com/recipe1/", result)
        self.assertIn("https://www.budgetbytes.com/recipe2/", result)
        mock_sleep.assert_called()

    @patch("recipes.services.recipe_providers.budgetbytes.budgetbytes.requests.get")
    @patch("recipes.services.recipe_providers.budgetbytes.budgetbytes.time.sleep")
    def test_discover_from_sitemap_timeout(self, mock_sleep, mock_get):
        """Test sitemap discovery handles timeout errors."""
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        scraper = BudgetBytesScraper()
        result = scraper._discover_from_sitemap(limit=10)

        self.assertEqual(result, [])

    @patch("recipes.services.recipe_providers.budgetbytes.budgetbytes.requests.get")
    @patch("recipes.services.recipe_providers.budgetbytes.budgetbytes.time.sleep")
    def test_discover_from_sitemap_request_exception(self, mock_sleep, mock_get):
        """Test sitemap discovery handles request exceptions."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        scraper = BudgetBytesScraper()
        result = scraper._discover_from_sitemap(limit=10)

        self.assertEqual(result, [])


class ParseIngredientsTestCase(TestCase):
    """Test _parse_ingredients method."""

    @patch("recipes.services.recipe_providers.budgetbytes.budgetbytes.parse_ingredient")
    def test_parse_ingredients_success(self, mock_parse_ingredient):
        """Test successful ingredient parsing."""
        # Mock parsed ingredient
        mock_parsed = Mock()
        mock_parsed.name = [Mock(text="flour")]
        mock_parsed.amount = [Mock(quantity=2.0, unit="cups")]
        mock_parsed.preparation = None
        mock_parse_ingredient.return_value = mock_parsed

        scraper = BudgetBytesScraper()
        raw_ingredients = ["2 cups flour ($0.50)"]
        result = scraper._parse_ingredients(raw_ingredients)

        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], IngredientData)
        self.assertEqual(result[0].name, "flour")
        self.assertEqual(result[0].quantity, 2.0)
        self.assertEqual(result[0].unit, "cups")
        self.assertEqual(result[0].original_text, "2 cups flour ($0.50)")

    @patch("recipes.services.recipe_providers.budgetbytes.budgetbytes.parse_ingredient")
    def test_parse_ingredients_with_preparation(self, mock_parse_ingredient):
        """Test ingredient parsing with preparation notes."""
        mock_parsed = Mock()
        mock_parsed.name = [Mock(text="tomatoes")]
        mock_parsed.amount = [Mock(quantity=2.0, unit="pieces")]
        mock_parsed.preparation = Mock(text="diced")
        mock_parse_ingredient.return_value = mock_parsed

        scraper = BudgetBytesScraper()
        raw_ingredients = ["2 tomatoes, diced ($1.28)"]
        result = scraper._parse_ingredients(raw_ingredients)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "tomatoes")
        self.assertEqual(result[0].notes, "diced")

    @patch("recipes.services.recipe_providers.budgetbytes.budgetbytes.parse_ingredient")
    def test_parse_ingredients_empty_list(self, mock_parse_ingredient):
        """Test parsing empty ingredient list raises ValueError."""
        scraper = BudgetBytesScraper()

        with self.assertRaises(ValueError) as context:
            scraper._parse_ingredients([])

        self.assertIn("Cannot process empty ingredients", str(context.exception))

    @patch("recipes.services.recipe_providers.budgetbytes.budgetbytes.parse_ingredient")
    def test_parse_ingredients_empty_string(self, mock_parse_ingredient):
        """Test parsing empty ingredient string raises ValueError."""
        scraper = BudgetBytesScraper()

        with self.assertRaises(ValueError) as context:
            scraper._parse_ingredients([""])

        self.assertIn("Cannot process empty ingredients", str(context.exception))

    @patch("recipes.services.recipe_providers.budgetbytes.budgetbytes.parse_ingredient")
    def test_parse_ingredients_parse_failure(self, mock_parse_ingredient):
        """Test parsing failure raises Exception."""
        mock_parse_ingredient.return_value = None

        scraper = BudgetBytesScraper()

        with self.assertRaises(Exception) as context:
            scraper._parse_ingredients(["2 cups flour"])

        self.assertIn(
            "Failed to extract ingredient information", str(context.exception)
        )

    @patch("recipes.services.recipe_providers.budgetbytes.budgetbytes.parse_ingredient")
    def test_parse_ingredients_no_name(self, mock_parse_ingredient):
        """Test parsing ingredient with no name raises Exception."""
        mock_parsed = Mock()
        mock_parsed.name = []
        mock_parse_ingredient.return_value = mock_parsed

        scraper = BudgetBytesScraper()

        with self.assertRaises(Exception) as context:
            scraper._parse_ingredients(["2 cups flour"])

        self.assertIn(
            "Failed to extract ingredient information", str(context.exception)
        )

    @patch("recipes.services.recipe_providers.budgetbytes.budgetbytes.parse_ingredient")
    def test_parse_ingredients_multiple_ingredients(self, mock_parse_ingredient):
        """Test parsing multiple ingredients returns list of IngredientData."""

        def parse_side_effect(ingredient_text):
            mock_parsed = Mock()
            if "flour" in ingredient_text:
                mock_parsed.name = [Mock(text="flour")]
                mock_parsed.amount = [Mock(quantity=2.0, unit="cups")]
                mock_parsed.preparation = None
            elif "sugar" in ingredient_text:
                mock_parsed.name = [Mock(text="sugar")]
                mock_parsed.amount = [Mock(quantity=1.0, unit="cup")]
                mock_parsed.preparation = None
            return mock_parsed

        mock_parse_ingredient.side_effect = parse_side_effect

        scraper = BudgetBytesScraper()
        raw_ingredients = ["2 cups flour", "1 cup sugar"]
        result = scraper._parse_ingredients(raw_ingredients)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "flour")
        self.assertEqual(result[0].quantity, 2.0)
        self.assertEqual(result[1].name, "sugar")
        self.assertEqual(result[1].quantity, 1.0)

    @patch("recipes.services.recipe_providers.budgetbytes.budgetbytes.parse_ingredient")
    def test_parse_ingredients_no_amount(self, mock_parse_ingredient):
        """Test parsing ingredient with no amount sets quantity and unit to None."""
        mock_parsed = Mock()
        mock_parsed.name = [Mock(text="salt")]
        mock_parsed.amount = []  # No amount
        mock_parsed.preparation = None
        mock_parse_ingredient.return_value = mock_parsed

        scraper = BudgetBytesScraper()
        raw_ingredients = ["salt to taste"]
        result = scraper._parse_ingredients(raw_ingredients)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "salt")
        self.assertIsNone(result[0].quantity)
        self.assertIsNone(result[0].unit)

    @patch("recipes.services.recipe_providers.budgetbytes.budgetbytes.parse_ingredient")
    def test_parse_ingredients_no_unit(self, mock_parse_ingredient):
        """Test parsing ingredient with amount but no unit converts None to string 'None'."""
        mock_parsed = Mock()
        mock_parsed.name = [Mock(text="eggs")]
        mock_parsed.amount = [Mock(quantity=3.0, unit=None)]  # Has quantity but no unit
        mock_parsed.preparation = None
        mock_parse_ingredient.return_value = mock_parsed

        scraper = BudgetBytesScraper()
        raw_ingredients = ["3 eggs"]
        result = scraper._parse_ingredients(raw_ingredients)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "eggs")
        self.assertEqual(result[0].quantity, 3.0)
        # The code does str(parsed.amount[0].unit) which converts None to "None"
        self.assertEqual(result[0].unit, "None")

    @patch("recipes.services.recipe_providers.budgetbytes.budgetbytes.parse_ingredient")
    def test_parse_ingredients_no_preparation(self, mock_parse_ingredient):
        """Test parsing ingredient with no preparation notes sets notes to None."""
        mock_parsed = Mock()
        mock_parsed.name = [Mock(text="butter")]
        mock_parsed.amount = [Mock(quantity=1.0, unit="tbsp")]
        mock_parsed.preparation = None  # No preparation notes
        mock_parse_ingredient.return_value = mock_parsed

        scraper = BudgetBytesScraper()
        raw_ingredients = ["1 tbsp butter"]
        result = scraper._parse_ingredients(raw_ingredients)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "butter")
        self.assertIsNone(result[0].notes)

    @patch("recipes.services.recipe_providers.budgetbytes.budgetbytes.parse_ingredient")
    def test_parse_ingredients_amount_with_none_quantity(self, mock_parse_ingredient):
        """Test parsing ingredient with amount object but quantity is None raises TypeError."""
        mock_parsed = Mock()
        mock_parsed.name = [Mock(text="pepper")]
        # Amount exists but quantity is None
        mock_amount = Mock()
        mock_amount.quantity = None
        mock_amount.unit = "tsp"
        mock_parsed.amount = [mock_amount]
        mock_parsed.preparation = None
        mock_parse_ingredient.return_value = mock_parsed

        scraper = BudgetBytesScraper()
        raw_ingredients = ["pepper to taste"]

        # The code does: float(parsed.amount[0].quantity) which will raise TypeError if quantity is None
        with self.assertRaises(TypeError):
            scraper._parse_ingredients(raw_ingredients)


class RemoveCostInfoTestCase(TestCase):
    """Test _remove_cost_info method."""

    def test_remove_cost_info_simple_cost(self):
        """Test removing simple cost information."""
        scraper = BudgetBytesScraper()

        result = scraper._remove_cost_info("2 tomatoes ($1.28)")
        self.assertEqual(result, "2 tomatoes")

    def test_remove_cost_info_cost_with_notes(self):
        """Test removing cost while preserving other notes."""
        scraper = BudgetBytesScraper()

        result = scraper._remove_cost_info("2 tomatoes (vine ripe, $1.28)")
        self.assertEqual(result, "2 tomatoes (vine ripe)")

    def test_remove_cost_info_cost_only(self):
        """Test removing cost when it's the only parenthetical content."""
        scraper = BudgetBytesScraper()

        result = scraper._remove_cost_info("¼ tsp salt ($0.01)")
        self.assertEqual(result, "¼ tsp salt")

    def test_remove_cost_info_multiple_parentheses(self):
        """Test removing cost from multiple parenthetical sections."""
        scraper = BudgetBytesScraper()

        result = scraper._remove_cost_info("butter (room temperature, $1.98*)")
        self.assertEqual(result, "butter (room temperature)")

    def test_remove_cost_info_no_cost(self):
        """Test text without cost information remains unchanged."""
        scraper = BudgetBytesScraper()

        result = scraper._remove_cost_info("2 cups flour")
        self.assertEqual(result, "2 cups flour")

    def test_remove_cost_info_with_notes_no_cost(self):
        """Test text with notes but no cost preserves notes."""
        scraper = BudgetBytesScraper()

        result = scraper._remove_cost_info("2 tomatoes (diced)")
        self.assertEqual(result, "2 tomatoes (diced)")

    def test_remove_cost_info_complex_formatting(self):
        """Test removing cost from complex formatting."""
        scraper = BudgetBytesScraper()

        result = scraper._remove_cost_info("1 cup sugar (granulated, $2.50, organic)")
        # Should remove $2.50 but keep other notes
        self.assertNotIn("$", result)
        self.assertIn("sugar", result)

    def test_remove_cost_info_empty_parentheses(self):
        """Test handling of empty parentheses after cost removal."""
        scraper = BudgetBytesScraper()

        result = scraper._remove_cost_info("flour ($1.00)")
        self.assertEqual(result, "flour")
        self.assertNotIn("()", result)
