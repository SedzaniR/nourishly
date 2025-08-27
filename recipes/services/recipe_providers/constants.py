from ast import Str


COMMON_UNITS = [
    "tablespoons",
    "tablespoon",
    "teaspoons",
    "teaspoon",
    "milliliters",
    "milliliter",
    "kilograms",
    "kilogram",
    "packages",
    "package",
    "bottles",
    "bottle",
    "gallons",
    "gallon",
    "pounds",
    "pound",
    "ounces",
    "ounce",
    "quarts",
    "quart",
    "liters",
    "liter",
    "sticks",
    "stick",
    "cloves",
    "clove",
    "pieces",
    "piece",
    "slices",
    "slice",
    "pints",
    "pint",
    "grams",
    "gram",
    "cups",
    "cup",
    "cans",
    "can",
    "bags",
    "bag",
    "jars",
    "jar",
    "lbs",
    "tbsp",
    "tsp",
    "oz",
    "lb",
    "ml",
    "kg",
    "g",
    "l",
    "c",
]

UNICODE_FRACTIONS = {
    "¼": 0.25,
    "½": 0.5,
    "¾": 0.75,
    "⅐": 1 / 7,
    "⅑": 1 / 9,
    "⅒": 0.1,
    "⅓": 1 / 3,
    "⅔": 2 / 3,
    "⅕": 0.2,
    "⅖": 0.4,
    "⅗": 0.6,
    "⅘": 0.8,
    "⅙": 1 / 6,
    "⅚": 5 / 6,
    "⅛": 0.125,
    "⅜": 0.375,
    "⅝": 0.625,
    "⅞": 0.875,
}

BUDGET_BYTES_BASE_URL: str = "https://www.budgetbytes.com"
BUDGET_BYTES_DOMAIN:str = "budgetbytes.com"
BUDGET_BYTES_RATE_LIMIT: float = 2.0

BUDGET_BYTES_SITEMAP_URLS = [
    "https://www.budgetbytes.com/post-sitemap.xml",

]

MACROS_TO_EXTRACT = [
    "calories",
    "protein",
    "carbohydrates",
    "fat",
    "fiber",
    "sugar",
    "sodium",
]

BUDGET_BYTES_SITEMAP_NAMESPACE = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}

BUDGET_BYTES_CATEGORY_URLS = [
            "https://www.budgetbytes.com/category/recipes/main-dish/",
            "https://www.budgetbytes.com/category/recipes/side-dish/",
            "https://www.budgetbytes.com/category/recipes/breakfast/",
            "https://www.budgetbytes.com/category/recipes/appetizer/",
            "https://www.budgetbytes.com/category/recipes/dessert/",
            "https://www.budgetbytes.com/category/recipes/soup/",
            "https://www.budgetbytes.com/category/recipes/salad/",
        ]

BUDGET_BYTES_RECIPE_PATTERNS = [
            r"budgetbytes\.com/[^/]+/$",  # Single recipe pages like /recipe-name/
            r"budgetbytes\.com/[a-z0-9-]+/$",  # Recipe slugs (letters, numbers, hyphens)
        ]

BUDGET_BYTES_EXCLUDED_RECIPE_PATTERNS = [
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