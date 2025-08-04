#!/usr/bin/env python3
"""
Simple test script for the Hugging Face API-based cuisine classifier.
Just tests if we can send data to Hugging Face and get results.
"""

import sys
import os

# Add the project root to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))


def test_api_classifier():
    """Test basic API functionality - send data and get results."""

    print("Testing Hugging Face API Connection")
    print("=" * 40)

    try:
        from core.logger import get_logger
        from recipes.services.cuisine_classifiers.huggingface_api import (
            HuggingFaceAPICuisineClassifier,
        )
        from recipes.services.cuisine_classifiers.constants import SUPPORTED_CUISINES

        # Initialize logger (minimal)
        logger = get_logger()
        logger.initialize(
            name="api_test",
            level="ERROR",  # Only show errors
            console_output=True,
            file_output=False,
        )

        # Get API token from environment if available
        api_token = os.getenv("HUGGINGFACE_API_TOKEN")
        if api_token:
            print(f"🔑 Using API token: {api_token[:8]}...")
        else:
            print("🔓 No API token - using free tier")

        # Initialize classifier
        print("Initializing classifier...")
        classifier = HuggingFaceAPICuisineClassifier(api_token=api_token)

        # Test API connection
        print("Testing API connection...")
        if not classifier.is_ready():
            print("❌ API not ready - check internet connection")
            return

        print("✅ API is ready!")

        # Test recipes
        test_recipes = [
            "Spaghetti Carbonara with eggs, pancetta, and parmesan cheese",
            "Pad Thai with rice noodles, fish sauce, and peanuts",
            "Chicken Tikka Masala with curry spices and basmati rice",
        ]

        print("\nTesting recipe classification:")
        print("-" * 40)

        for i, recipe_text in enumerate(test_recipes, 1):
            try:
                print(f"{i}. Testing: {recipe_text[:50]}...")
                result = classifier.classify_recipe(recipe_text)

                print(f"   → {result.primary_cuisine} ({result.confidence:.2f})")

            except Exception as e:
                print(f"   ❌ Error: {e}")

        # Test structured data
        print("\nTesting structured data:")
        print("-" * 40)

        result = classifier.classify_recipe_from_data(
            title="Margherita Pizza",
            ingredients=["pizza dough", "tomato sauce", "mozzarella", "basil"],
        )
        print(f"Margherita Pizza → {result.primary_cuisine} ({result.confidence:.2f})")

        print("\n✅ All tests completed!")

    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_api_classifier()
