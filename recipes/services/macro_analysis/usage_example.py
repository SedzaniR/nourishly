"""
Usage examples for the macro analysis system.

This file demonstrates how to use the macro analysis services
in your Django application. Remove this file in production.
"""

from typing import List
from recipes.services.macro_analysis import (
    analyze_ingredient,
    analyze_recipe,
    analyze_food,
    search_foods,
    get_analyzer,
    MacroAnalysisManager,
    MacroAnalysisFactory,
    MacroAnalysisProvider,
    MacroAnalysisStatus,
    AnalysisType,
)


def ingredient_analysis_example():
    """Example of analyzing individual ingredients (per 100g)."""
    print("=== Ingredient Analysis Example ===")

    # Analyze a single ingredient - returns nutrition per 100g
    result = analyze_ingredient("chicken breast", quantity=100)

    if result.status == MacroAnalysisStatus.SUCCESS:
        macros = result.macro_nutrients
        print(f"Ingredient: {result.food_name}")
        print(f"Analysis Type: {result.analysis_type.value}")
        print(f"Calories per 100g: {macros.calories}")
        print(f"Protein per 100g: {macros.protein}g")
        print(f"Carbs per 100g: {macros.carbohydrates}g")
        print(f"Fat per 100g: {macros.fat}g")
        print(f"Source: {result.source}")
        print(f"Confidence: {result.confidence}")
    else:
        print(f"Analysis failed: {result.error_message}")


def recipe_analysis_example():
    """Example of analyzing a complete recipe."""
    print("\n=== Recipe Analysis Example ===")

    # Example recipe text
    recipe_text = """
    Grilled Chicken Salad Recipe:
    - 6 oz chicken breast
    - 2 cups mixed greens
    - 1 medium tomato
    - 1/2 cup cucumber
    - 2 tbsp olive oil
    - 1 tbsp balsamic vinegar
    - Salt and pepper to taste
    """

    # Analyze the entire recipe - returns total nutrition
    result = analyze_recipe(recipe_text, servings=2)

    if result.status == MacroAnalysisStatus.SUCCESS:
        macros = result.macro_nutrients
        print(f"Recipe Analysis Type: {result.analysis_type.value}")
        print(f"Total recipe calories: {macros.calories:.1f}")
        print(f"Total protein: {macros.protein:.1f}g")
        print(f"Total carbs: {macros.carbohydrates:.1f}g")
        print(f"Total fat: {macros.fat:.1f}g")

        if result.servings:
            per_serving = result.per_serving_macros
            if per_serving:
                print(f"\nPer serving ({result.servings} servings):")
                print(f"Calories: {per_serving.calories:.1f}")
                print(f"Protein: {per_serving.protein:.1f}g")
                print(f"Carbs: {per_serving.carbohydrates:.1f}g")
                print(f"Fat: {per_serving.fat:.1f}g")

        if result.recipe_ingredients:
            print(f"\nDetected ingredients ({len(result.recipe_ingredients)}):")
            for ingredient in result.recipe_ingredients:
                print(
                    f"  - {ingredient.name}: {ingredient.macro_nutrients.calories:.1f} cal"
                )

        print(f"Source: {result.source}")
        print(f"Confidence: {result.confidence}")
    else:
        print(f"Recipe analysis failed: {result.error_message}")


def compare_ingredient_vs_recipe_example():
    """Example comparing ingredient analysis vs recipe analysis."""
    print("\n=== Ingredient vs Recipe Comparison ===")

    # Analyze cheese as an ingredient (per 100g)
    ingredient_result = analyze_ingredient("cheddar cheese", quantity=100)

    # Analyze a simple recipe with cheese
    recipe_result = analyze_recipe("1 cup shredded cheddar cheese mixed with herbs")

    print("Ingredient Analysis (per 100g):")
    if ingredient_result.status == MacroAnalysisStatus.SUCCESS:
        macros = ingredient_result.macro_nutrients
        print(
            f"  Cheddar cheese: {macros.calories:.1f} cal, {macros.protein:.1f}g protein"
        )
    else:
        print(f"  Failed: {ingredient_result.error_message}")

    print("\nRecipe Analysis (total):")
    if recipe_result.status == MacroAnalysisStatus.SUCCESS:
        macros = recipe_result.macro_nutrients
        print(
            f"  Cheese recipe: {macros.calories:.1f} cal, {macros.protein:.1f}g protein"
        )
    else:
        print(f"  Failed: {recipe_result.error_message}")


def specific_provider_example():
    """Example of using a specific provider for different analysis types."""
    print("\n=== Provider-Specific Analysis ===")

    # API Ninja is excellent for recipe analysis
    recipe_result = analyze_recipe(
        "2 slices of bread with 2 tbsp peanut butter and 1 tbsp honey",
        provider=MacroAnalysisProvider.API_NINJA,
    )

    if recipe_result.status == MacroAnalysisStatus.SUCCESS:
        print(f"API Ninja recipe analysis successful:")
        print(f"  Total calories: {recipe_result.macro_nutrients.calories:.1f}")
    else:
        print(f"API Ninja recipe analysis failed: {recipe_result.error_message}")

    # Single ingredient analysis
    ingredient_result = analyze_ingredient(
        "salmon", quantity=100, provider=MacroAnalysisProvider.API_NINJA
    )

    if ingredient_result.status == MacroAnalysisStatus.SUCCESS:
        print(f"API Ninja ingredient analysis successful:")
        print(f"  Salmon (100g): {ingredient_result.macro_nutrients.calories:.1f} cal")
    else:
        print(
            f"API Ninja ingredient analysis failed: {ingredient_result.error_message}"
        )


def batch_analysis_example():
    """Example of analyzing multiple items at once."""
    print("\n=== Batch Analysis Example ===")

    # Batch ingredient analysis
    ingredients = ["apple", "banana", "spinach", "quinoa"]

    manager = MacroAnalysisManager()
    results = manager.analyze_multiple_ingredients(ingredients)

    print("Batch ingredient analysis (per 100g):")
    for result in results:
        if result.status == MacroAnalysisStatus.SUCCESS:
            macros = result.macro_nutrients
            print(f"  {result.food_name}: {macros.calories:.1f} cal")
        else:
            print(f"  {result.food_name}: Failed - {result.error_message}")

    # Batch recipe analysis
    recipes = [
        "1 cup oatmeal with banana and honey",
        "grilled chicken salad with olive oil",
        "pasta with tomato sauce and cheese",
    ]

    recipe_results = manager.analyze_multiple_recipes(recipes)

    print("\nBatch recipe analysis (total):")
    for result in recipe_results:
        if result.status == MacroAnalysisStatus.SUCCESS:
            macros = result.macro_nutrients
            recipe_name = (
                result.food_name[:30] + "..."
                if len(result.food_name) > 30
                else result.food_name
            )
            print(f"  {recipe_name}: {macros.calories:.1f} cal")
        else:
            recipe_name = (
                result.food_name[:30] + "..."
                if len(result.food_name) > 30
                else result.food_name
            )
            print(f"  {recipe_name}: Failed")


def legacy_analyze_food_example():
    """Example of using the legacy analyze_food method."""
    print("\n=== Legacy analyze_food Method ===")

    # The legacy method tries to determine if input is ingredient or recipe

    # This should be detected as an ingredient
    result1 = analyze_food("chicken breast")
    print(f"'chicken breast' detected as: {result1.analysis_type.value}")

    # This should be detected as a recipe
    result2 = analyze_food("2 cups rice with 1 cup vegetables and olive oil")
    print(f"'2 cups rice with...' detected as: {result2.analysis_type.value}")

    # Force ingredient analysis with quantity
    result3 = analyze_food("brown rice", quantity=100)
    print(f"'brown rice' (100g) detected as: {result3.analysis_type.value}")


def advanced_recipe_analysis_example():
    """Example of advanced recipe analysis with detailed breakdown."""
    print("\n=== Advanced Recipe Analysis ===")

    complex_recipe = """
    Chicken Stir Fry Recipe (Serves 4):
    
    Ingredients:
    - 1 lb chicken breast, diced
    - 2 cups broccoli florets
    - 1 red bell pepper, sliced
    - 1 cup snap peas
    - 2 cloves garlic, minced
    - 1 inch fresh ginger, grated
    - 3 tbsp soy sauce
    - 2 tbsp sesame oil
    - 1 tbsp cornstarch
    - 2 cups cooked brown rice
    
    Instructions:
    1. Heat sesame oil in large wok
    2. Cook chicken until golden
    3. Add vegetables and stir fry 5 minutes
    4. Mix soy sauce and cornstarch, add to wok
    5. Serve over brown rice
    """

    result = analyze_recipe(complex_recipe, servings=4)

    if result.status == MacroAnalysisStatus.SUCCESS:
        print("Complex recipe analysis successful!")

        macros = result.macro_nutrients
        print(f"\nTotal Recipe Nutrition:")
        print(f"  Calories: {macros.calories:.1f}")
        print(f"  Protein: {macros.protein:.1f}g")
        print(f"  Carbohydrates: {macros.carbohydrates:.1f}g")
        print(f"  Fat: {macros.fat:.1f}g")

        if macros.fiber:
            print(f"  Fiber: {macros.fiber:.1f}g")
        if macros.sodium:
            print(f"  Sodium: {macros.sodium:.1f}mg")

        # Per serving breakdown
        per_serving = result.per_serving_macros
        if per_serving:
            print(f"\nPer Serving (4 servings):")
            print(f"  Calories: {per_serving.calories:.1f}")
            print(f"  Protein: {per_serving.protein:.1f}g")
            print(f"  Carbohydrates: {per_serving.carbohydrates:.1f}g")
            print(f"  Fat: {per_serving.fat:.1f}g")

        # Individual ingredients breakdown
        if result.recipe_ingredients:
            print(f"\nIngredient Breakdown:")
            for ingredient in result.recipe_ingredients[:5]:  # Show first 5
                ingredient_macros = ingredient.macro_nutrients
                quantity_info = (
                    f" ({ingredient.quantity}g)" if ingredient.quantity else ""
                )
                print(
                    f"  {ingredient.name}{quantity_info}: {ingredient_macros.calories:.1f} cal"
                )

            if len(result.recipe_ingredients) > 5:
                print(
                    f"  ... and {len(result.recipe_ingredients) - 5} more ingredients"
                )

        if result.total_weight:
            print(f"\nTotal recipe weight: {result.total_weight:.1f}g")

    else:
        print(f"Complex recipe analysis failed: {result.error_message}")


def error_handling_example():
    """Example of proper error handling for different analysis types."""
    print("\n=== Error Handling Example ===")

    # Try to analyze a non-existent ingredient
    result1 = analyze_ingredient("imaginary_super_ingredient_xyz")
    print(f"Non-existent ingredient: {result1.status.value}")

    # Try to analyze a complex recipe that might fail
    result2 = analyze_recipe("some random text that is not a real recipe")
    print(f"Invalid recipe: {result2.status.value}")

    # Handle different error types
    if result1.status == MacroAnalysisStatus.NOT_FOUND:
        print("  Ingredient not found in database")
    elif result1.status == MacroAnalysisStatus.FAILED:
        print(f"  Analysis failed: {result1.error_message}")

    if result2.status == MacroAnalysisStatus.NOT_FOUND:
        print("  Recipe ingredients not found")
    elif result2.status == MacroAnalysisStatus.FAILED:
        print(f"  Recipe analysis failed: {result2.error_message}")


def run_all_examples():
    """Run all usage examples."""
    print("Macro Analysis Usage Examples - Ingredient vs Recipe")
    print("=" * 60)

    ingredient_analysis_example()
    recipe_analysis_example()
    compare_ingredient_vs_recipe_example()
    specific_provider_example()
    batch_analysis_example()
    legacy_analyze_food_example()
    advanced_recipe_analysis_example()
    error_handling_example()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("\nKey Takeaways:")
    print("• Use analyze_ingredient() for single ingredients (nutrition per 100g)")
    print("• Use analyze_recipe() for complete recipes (total nutrition)")
    print("• API Ninja excels at recipe analysis with natural language processing")
    print("• USDA is better for detailed individual ingredient data")
    print("• The system automatically detects and handles both types of analysis")


if __name__ == "__main__":
    # Run examples when executed directly
    # Note: This requires proper Django setup and API keys
    run_all_examples()
