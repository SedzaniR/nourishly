import time
from typing import Any, Callable
from django.http import HttpRequest, HttpResponse
from django.conf import settings
from .logger import logger


class RequestLoggingMiddleware:
    """
    Middleware to log all HTTP requests with performance metrics.
    """
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Start timing
        start_time = time.time()
        
        # Get user info
        user_id = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = str(getattr(request.user, 'id', 'unknown'))
        
        # Process request
        try:
            response = self.get_response(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Log the request
            logger.log_api_request(
                method=request.method or 'UNKNOWN',
                url=request.path,
                status_code=response.status_code,
                response_time=response_time,
                user_id=user_id
            )
            
            return response
            
        except Exception as e:
            # Calculate response time
            response_time = time.time() - start_time
            
            # Log the error
            logger.error(
                f"Request failed: {request.method} {request.path}",
                method=request.method,
                url=request.path,
                response_time=response_time,
                user_id=user_id,
                error=str(e),
                log_type="api_error"
            )
            
            raise


class DatabaseQueryLoggingMiddleware:
    """
    Middleware to log database query performance.
    Requires django-debug-toolbar or similar for query capture.
    """
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        # This middleware would integrate with Django's database logging
        # For now, it's a placeholder for future implementation
        return self.get_response(request)


class SecurityLoggingMiddleware:
    """
    Middleware to log security-related events.
    """
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Log potential security events
        self._check_security_events(request)
        
        response = self.get_response(request)
        
        # Log response security headers
        self._log_security_headers(response)
        
        return response
    
    def _check_security_events(self, request: HttpRequest) -> None:
        """Check for potential security events in the request."""
        # Check for suspicious headers
        suspicious_headers = [
            'HTTP_X_FORWARDED_FOR',
            'HTTP_X_REAL_IP',
            'HTTP_X_CLIENT_IP',
        ]
        
        for header in suspicious_headers:
            if header in request.META:
                logger.log_security_event(
                    event_type="suspicious_header",
                    details={
                        'header': header,
                        'value': request.META[header],
                        'ip': request.META.get('REMOTE_ADDR'),
                        'user_agent': request.META.get('HTTP_USER_AGENT'),
                    },
                    severity="low"
                )
        
        # Check for failed authentication attempts
        if hasattr(request, 'user') and not request.user.is_authenticated:
            # This is a basic check - you might want more sophisticated logic
            pass
    
    def _log_security_headers(self, response: HttpResponse) -> None:
        """Log security headers in the response."""
        security_headers = [
            'X-Frame-Options',
            'X-Content-Type-Options',
            'X-XSS-Protection',
            'Strict-Transport-Security',
            'Content-Security-Policy',
        ]
        
        for header in security_headers:
            if header in response:
                logger.debug(
                    f"Security header set: {header}",
                    header=header,
                    value=response[header],
                    log_type="security_header"
                ) 