from django.apps import AppConfig
from django.conf import settings


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        """
        Initialize the logger when the app is ready.
        This is a workaround to ensure the logger is initialized after the settings are loaded.
        This is because the logger is initialized in the settings file, but the settings file is loaded before the app is ready.
        It is in this app because it is a core app and needs to be initialized before other apps are loaded.
        """
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
