from django.apps import AppConfig
from django.conf import settings


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        """Initialize the logger when the app is ready."""
        if not settings.DEBUG or 'runserver' in settings.DEBUG:
            # Initialize the logger singleton
            from .logger import logger
            
            # Configure logger based on environment
            if hasattr(settings, 'LOGGING_LEVEL'):
                log_level = settings.LOGGING_LEVEL
            else:
                log_level = 'DEBUG' if settings.DEBUG else 'INFO'
            
            logger.initialize(
                name='nourishly',
                level=log_level,
                console_output=True,
                file_output=True,
                json_format=False  # Set to True for structured logging
            )
