from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Database - Use PostgreSQL for development
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "nourishly_dev",
        "USER": "sedzaniragau",  # Your macOS username
        "PASSWORD": "nMDyHqTmxUE6aZv",  # No password for local development
        "HOST": "localhost",
        "PORT": "5432",
    }
}

# Development-specific settings
if DEBUG:
    try:
        import django_debug_toolbar  # type: ignore

        INSTALLED_APPS += ["django_debug_toolbar"]
        MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
        INTERNAL_IPS = ["127.0.0.1"]
    except ImportError:
        pass  # Debug toolbar not installed
