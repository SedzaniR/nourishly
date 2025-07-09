from ninja import Router
from django.http import JsonResponse

router = Router()

@router.get("/health")
def health_check(request):
    """Health check endpoint"""
    return {"status": "healthy", "service": "nourishly-api"}
