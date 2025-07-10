from ninja import Router
from django.http import JsonResponse
from core.logger import logger, log_info, log_error

router = Router()

@router.get("/health")
def health_check(request):
    """Health check endpoint"""
    try:
        log_info("Health check requested", endpoint="/health", user_ip=request.META.get('REMOTE_ADDR'))
        return {"status": "healthy", "service": "nourishly-api"}
    except Exception as e:
        log_error("Health check failed", error=str(e), endpoint="/health")
        return {"status": "unhealthy", "service": "nourishly-api", "error": str(e)}
