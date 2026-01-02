import logging
from ninja import Router

router = Router()
logger = logging.getLogger(__name__)


@router.get("/health")
def health_check(request):
    """Health check endpoint"""
    try:
        logger.info(
            "Health check requested",
            extra={
                "extra_fields": {
                    "endpoint": "/health",
                    "user_ip": request.META.get("REMOTE_ADDR"),
                }
            },
        )
        return {"status": "healthy", "service": "nourishly-api"}
    except Exception as e:
        logger.error(
            "Health check failed",
            extra={
                "extra_fields": {
                    "error": str(e),
                    "endpoint": "/health",
                }
            },
            exc_info=True,
        )
        return {"status": "unhealthy", "service": "nourishly-api", "error": str(e)}
