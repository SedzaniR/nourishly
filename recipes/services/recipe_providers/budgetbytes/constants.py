"""BudgetBytes recipe provider constants."""

# Base URLs and configuration
BUDGET_BYTES_BASE_URL: str = "https://www.budgetbytes.com"
BUDGET_BYTES_DOMAIN: str = "budgetbytes.com"
BUDGET_BYTES_RATE_LIMIT: float = 2.0

# Sitemap configuration
BUDGET_BYTES_SITEMAP_URLS = [
    "https://www.budgetbytes.com/post-sitemap.xml",
    "https://www.budgetbytes.com/post-sitemap2.xml"
]

BUDGET_BYTES_SITEMAP_NAMESPACE = {
    "sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"
}

# Category URLs for recipe discovery
BUDGET_BYTES_CATEGORY_URLS = [
    "https://www.budgetbytes.com/category/recipes/main-dish/",
    "https://www.budgetbytes.com/category/recipes/side-dish/",
    "https://www.budgetbytes.com/category/recipes/breakfast/",
    "https://www.budgetbytes.com/category/recipes/appetizer/",
    "https://www.budgetbytes.com/category/recipes/dessert/",
    "https://www.budgetbytes.com/category/recipes/soup/",
    "https://www.budgetbytes.com/category/recipes/salad/",
]

# Recipe URL patterns
BUDGET_BYTES_RECIPE_PATTERNS = [
    r"budgetbytes\.com/[^/]+/$",  # Single recipe pages like /recipe-name/
    r"budgetbytes\.com/[a-z0-9-]+/$",  # Recipe slugs (letters, numbers, hyphens)
]

# Excluded URL patterns (non-recipe pages)
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
