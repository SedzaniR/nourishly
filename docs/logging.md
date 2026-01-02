# Logging System Documentation

## Overview

The Nourishly project uses Python's standard `logging` module configured through Django's `LOGGING` settings. This provides a simple, standard approach to logging that integrates seamlessly with Django and follows Python best practices.

## Features

- **Standard Python Logging**: Uses Python's built-in `logging` module
- **Django Integration**: Configured through Django's `LOGGING` settings
- **Multiple Output Handlers**: Console and file logging with rotation
- **App-Specific Loggers**: Separate loggers for different Django apps
- **Convenience Functions**: Optional helper functions for quick logging
- **Automatic Middleware Integration**: Request logging and security monitoring

## Quick Start

### Recommended: Standard Python Logging

The recommended approach is to use Python's standard logging with `logging.getLogger(__name__)`:

```python
import logging

logger = logging.getLogger(__name__)

# Simple logging
logger.info("User logged in successfully")
logger.error("Failed to connect to database")
logger.debug("Processing request data")
```

### Alternative: Convenience Functions

For backward compatibility, convenience functions are still available:

```python
from core.logger import log_info, log_error, log_debug

# Simple logging
log_info("User logged in successfully")
log_error("Failed to connect to database")
log_debug("Processing request data")
```

**Note**: The convenience functions are maintained for backward compatibility but using standard `logging.getLogger(__name__)` is recommended for new code.

### Using f-strings for Complete Messages

All log messages should be complete and self-contained using f-strings:

```python
import logging

logger = logging.getLogger(__name__)

# Good: Complete message with all context
logger.info(f"Recipe scraped successfully from {url} - Title: {recipe_data.title} (provider: {provider})")
logger.error(f"Failed to fetch sitemap {sitemap_url} - Error: {str(e)}")

# Avoid: Incomplete messages that require extra fields
logger.info("Recipe scraped", extra={"extra_fields": {"url": url, "title": title}})
```

## Configuration

### Django LOGGING Settings

All logging configuration is handled through Django's `LOGGING` settings in `nourishly/settings/base.py`:

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "nourishly.log",
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "formatter": "default",
            "encoding": "utf-8",
            "level": "INFO",
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "nourishly_error.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "default",
            "encoding": "utf-8",
            "level": "ERROR",
        },
    },
    "root": {
        "handlers": ["console", "file", "error_file"],
        "level": "INFO",
    },
    "loggers": {
        "django.request": {
            "handlers": ["error_file"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        # Third-party noise reduction
        "urllib3": {"level": "ERROR"},
        "botocore": {"level": "ERROR"},
        "requests": {"level": "ERROR"},
        "paramiko": {"level": "ERROR"},
        "huggingface_hub": {"level": "ERROR"},
    },
}
```

### Environment-Based Configuration

The logging configuration is environment-agnostic and uses the same settings across all environments. Log levels can be adjusted per logger in the `LOGGING` configuration.

## Usage Examples

### In Django Views

```python
import logging
from django.http import JsonResponse

logger = logging.getLogger(__name__)

def my_view(request):
    try:
        logger.info(f"View accessed - User: {request.user.id if request.user.is_authenticated else 'anonymous'}, IP: {request.META.get('REMOTE_ADDR')}")
        
        # Your view logic here
        data = {"message": "Success"}
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"View error occurred - Error: {str(e)}", exc_info=True)
        return JsonResponse({"error": "Internal error"}, status=500)
```

### In Django Models

```python
import logging
from django.db import models

logger = logging.getLogger(__name__)

class Recipe(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        if is_new:
            logger.info(f"Creating new recipe - Title: {self.title}, Author ID: {self.author.id}")
        else:
            logger.info(f"Updating recipe - ID: {self.pk}, Title: {self.title}")
        
        super().save(*args, **kwargs)
```

### In Django Management Commands

```python
import logging
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

class MyCommand(BaseCommand):
    help = 'My custom management command'
    
    def handle(self, *args, **options):
        logger.info("Management command started")
        
        try:
            # Command logic here
            self.stdout.write(self.style.SUCCESS('Command completed'))
            
        except Exception as e:
            logger.error(f"Management command failed - Error: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(f'Command failed: {e}'))
```

### In Service Classes

```python
import logging

logger = logging.getLogger(__name__)

class RecipeService:
    def process_recipe(self, url: str):
        logger.info(f"Starting recipe processing - URL: {url}")
        
        try:
            # Process recipe
            result = self._scrape_recipe(url)
            logger.info(f"Recipe processed successfully - URL: {url}, Title: {result.title}")
            return result
            
        except Exception as e:
            logger.error(f"Recipe processing failed - URL: {url}, Error: {str(e)}", exc_info=True)
            raise
```

## Error Handling and Exception Logging

### Exception Logging with Traceback

```python
import logging

logger = logging.getLogger(__name__)

try:
    # Risky operation
    result = 10 / 0
except ZeroDivisionError as e:
    logger.error(f"Division by zero error - Dividend: 10, Divisor: 0, Error: {str(e)}", exc_info=True)
    raise
```

### Error Logging Without Exceptions

```python
import logging

logger = logging.getLogger(__name__)

def handle_api_error(response):
    if response.status_code != 200:
        logger.error(
            f"API request failed - Endpoint: {response.url}, Status: {response.status_code}, "
            f"Response: {response.text[:500]}"
        )
```

## Log Files and Rotation

### Log File Structure

The logger creates the following log files in the `logs/` directory:

- `nourishly.log` - General application logs (INFO level and above)
- `nourishly_error.log` - Error-level logs only (ERROR and CRITICAL)

### Log Rotation

Log files are automatically rotated when they reach 10MB. The system keeps 5 backup files.

### Log Format

The default log format is:
```
[2024-01-15 10:30:45] INFO [recipes.services.recipe_providers.budgetbytes:91] Recipe scraped successfully from https://example.com - Title: Thai Curry (provider: BudgetBytes)
```

Format breakdown:
- `[2024-01-15 10:30:45]` - Timestamp
- `INFO` - Log level
- `[recipes.services.recipe_providers.budgetbytes:91]` - Logger name and line number
- `Recipe scraped successfully...` - Log message

## Middleware Integration

The logging system includes middleware that automatically logs:

- All HTTP requests with performance metrics
- Security events and suspicious activity
- Response headers and status codes

### Request Logging Middleware

Automatically logs every HTTP request with:
- Request method and URL
- Response status code
- Response time
- User ID (if authenticated)

### Security Logging Middleware

Monitors and logs:
- Suspicious headers
- Failed authentication attempts
- Security header presence in responses

## Best Practices

### 1. Use Appropriate Log Levels

- **DEBUG**: Detailed information for debugging (typically not used in production)
- **INFO**: General information about application flow
- **WARNING**: Something unexpected happened but the application can continue
- **ERROR**: An error occurred that prevented a specific operation
- **CRITICAL**: A critical error that may prevent the application from running

### 2. Use f-strings for Complete Messages

```python
# Good: Complete, self-contained message
logger.info(f"User action completed - User ID: {user.id}, Action: {action}, Recipe ID: {recipe.id}")

# Avoid: Incomplete message requiring extra fields
logger.info("User action completed", extra={"extra_fields": {"user_id": user.id}})
```

### 3. Include Relevant Context in Messages

```python
# Good: All context in the message
logger.info(f"Recipe created - Title: {recipe.title}, Author: {recipe.author.username}, Category: {recipe.category}")

# Avoid: Vague messages
logger.info("Recipe created")  # Too vague
```

### 4. Don't Log Sensitive Information

```python
# Good
logger.info(f"User logged in - User ID: {user.id}, IP: {request.META.get('REMOTE_ADDR')}")

# Avoid
logger.info(f"User logged in - Password: {user.password}, Token: {token}")  # Sensitive data
```

### 5. Use exc_info=True for Exceptions

```python
try:
    result = risky_operation()
except Exception as e:
    # Good: Includes full traceback
    logger.error(f"Operation failed - Error: {str(e)}", exc_info=True)
    raise
```

### 6. Use Module-Specific Loggers

```python
# Good: Logger named after the module
logger = logging.getLogger(__name__)

# Avoid: Using a generic logger name
logger = logging.getLogger("nourishly")  # Less specific
```

## Migration from Old Logger

If you're migrating from the old singleton logger:

1. **Replace convenience function imports** (optional - they still work):
   ```python
   # Old
   from core.logger import log_info, log_error
   
   # New (recommended)
   import logging
   logger = logging.getLogger(__name__)
   ```

2. **Replace logger method calls**:
   ```python
   # Old
   log_info("Message", key="value")
   
   # New
   logger.info(f"Message - Key: {value}")
   ```

3. **Remove specialized method calls**:
   ```python
   # Old (no longer available)
   logger.log_api_request(...)
   logger.log_database_query(...)
   logger.log_user_action(...)
   
   # New: Use standard logging with f-strings
   logger.info(f"API Request: {method} {url} - Status: {status_code}, Time: {response_time}s")
   ```

4. **Update error handling**:
   ```python
   # Old
   log_exception("Error occurred", error=str(e))
   
   # New
   logger.error(f"Error occurred - Error: {str(e)}", exc_info=True)
   ```

## Troubleshooting

### Common Issues

1. **Logs not appearing**: 
   - Check Django's `LOGGING` configuration in settings
   - Verify the logger name matches a configured logger
   - Check log file permissions

2. **Permission errors**: 
   - Ensure the `logs/` directory exists and is writable
   - Check file permissions on log files

3. **Large log files**: 
   - Adjust rotation settings in `LOGGING` configuration
   - Increase log level to reduce verbosity
   - Review what's being logged

4. **Performance impact**: 
   - Use appropriate log levels in production (INFO or higher)
   - Avoid logging in tight loops
   - Use DEBUG level only in development

### Testing Logging

```python
import logging
from unittest.mock import patch

def test_logging():
    with patch('logging.getLogger') as mock_get_logger:
        mock_logger = mock_get_logger.return_value
        # Your code that logs
        logger = logging.getLogger(__name__)
        logger.info("Test message")
        mock_logger.info.assert_called_once()
```

## Conclusion

The logging system uses Python's standard `logging` module configured through Django, providing a simple, maintainable approach to application logging. By using `logging.getLogger(__name__)` and f-strings for complete messages, you'll have clear, readable logs that are easy to monitor and debug.
