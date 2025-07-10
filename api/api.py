from ninja import NinjaAPI
from django.conf import settings

api = NinjaAPI(
    title="Nourishly API",
    version="1.0.0",
    description="Nutrition and meal planning API",
    docs_url="/docs" if settings.DEBUG else None,
)

# Import and include app routers
# from recipes.api import router as recipes_router
# from planner.api import router as planner_router
# from users.api import router as users_router
# from classify.api import router as classify_router

# api.add_router("/recipes/", recipes_router)
# api.add_router("/planner/", planner_router)
# api.add_router("/users/", users_router)
# api.add_router("/classify/", classify_router) 