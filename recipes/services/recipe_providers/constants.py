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