# Logging System Documentation

## Overview

The Nourishly project uses a centralized logging system built around a singleton logger that provides comprehensive logging capabilities across the entire Django application. This system ensures consistent logging patterns, structured data, and easy monitoring.

## Features

- **Singleton Pattern**: Ensures only one logger instance across the entire application
- **Configurable Log Levels**: Support for DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Multiple Output Handlers**: Console and file logging with rotation
- **Structured Logging**: Support for JSON format with contextual data
- **Performance Monitoring**: Built-in decorators for function timing
- **Specialized Logging Methods**: API requests, database queries, user actions, security events
- **Automatic Middleware Integration**: Request logging and security monitoring

## Quick Start

### Basic Usage

```python
from core.logger import log_info, log_error, log_debug

# Simple logging
log_info("User logged in successfully")
log_error("Failed to connect to database")
log_debug("Processing request data")
```

### Using the Logger Instance

```python
from core.logger import logger

# Direct logger usage
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")
```

### Contextual Logging

```python
from core.logger import log_info

# Log with additional context
log_info(
    "Recipe created successfully",
    recipe_id="recipe_123",
    recipe_name="Chicken Curry",
    author_id="user_456",
    category="main_dish"
)
```

## Configuration

### Environment-Based Configuration

The logger is automatically configured based on your Django environment:

- **Development**: DEBUG level, console and file output
- **Production**: INFO level, file output only, JSON format
- **Testing**: WARNING level, console output only

### Manual Configuration

You can manually configure the logger in your Django settings:

```python
# In your Django settings
LOGGING_LEVEL = 'DEBUG'  # or 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
LOGGING_JSON_FORMAT = True  # Enable structured JSON logging
LOGGING_FILE_OUTPUT = True  # Enable file logging
LOGGING_CONSOLE_OUTPUT = True  # Enable console logging
```

### Custom Configuration

```python
from core.logger import logger

# Initialize with custom settings
logger.initialize(
    name='my_app',
    level='DEBUG',
    log_dir='/custom/log/path',
    max_bytes=20 * 1024 * 1024,  # 20MB
    backup_count=10,
    console_output=True,
    file_output=True,
    json_format=True
)
```

## Specialized Logging Methods

### API Request Logging

```python
from core.logger import logger

# Log API requests (typically done in middleware)
logger.log_api_request(
    method="POST",
    url="/api/recipes/",
    status_code=201,
    response_time=0.234,
    user_id="user_123"
)
```

### Database Query Logging

```python
from core.logger import logger

# Log database queries
logger.log_database_query(
    query="SELECT * FROM recipes WHERE id = %s",
    execution_time=0.0123,
    table="recipes"
)
```

### User Action Logging

```python
from core.logger import logger

# Log user actions for audit purposes
logger.log_user_action(
    user_id="user_123",
    action="recipe_create",
    details={
        "recipe_name": "Spaghetti Carbonara",
        "category": "pasta",
        "ingredients_count": 8
    }
)
```

### Security Event Logging

```python
from core.logger import logger

# Log security events
logger.log_security_event(
    event_type="failed_login",
    details={
        "username": "john_doe",
        "ip_address": "192.168.1.100",
        "attempt_count": 3
    },
    severity="medium"
)
```

## Performance Monitoring

### Function Performance Decorator

```python
from core.logger import logger

@logger.log_performance
def slow_operation():
    """This function's execution time will be automatically logged."""
    import time
    time.sleep(0.1)  # Simulate slow operation
    return "Operation completed"

# Usage
result = slow_operation()
```

### Manual Performance Logging

```python
import time
from core.logger import log_info

def manual_performance_logging():
    start_time = time.time()
    
    # Your operation here
    result = perform_operation()
    
    execution_time = time.time() - start_time
    log_info(
        "Operation completed",
        operation="data_processing",
        execution_time=execution_time,
        result_count=len(result)
    )
    
    return result
```

## Error Handling and Exception Logging

### Exception Logging

```python
from core.logger import log_exception

try:
    # Risky operation
    result = 10 / 0
except ZeroDivisionError as e:
    log_exception(
        "Division by zero error occurred",
        operation="division",
        dividend=10,
        divisor=0,
        error_type="ZeroDivisionError"
    )
    raise
```

### Error Logging Without Exceptions

```python
from core.logger import log_error

def handle_api_error(response):
    if response.status_code != 200:
        log_error(
            "API request failed",
            endpoint=response.url,
            status_code=response.status_code,
            response_text=response.text[:500]  # First 500 chars
        )
```

## Django Integration

### In Django Views

```python
from django.http import JsonResponse
from core.logger import log_info, log_error

def my_view(request):
    try:
        log_info(
            "View accessed",
            view_name="my_view",
            user_id=getattr(request.user, 'id', None),
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Your view logic here
        data = {"message": "Success"}
        
        return JsonResponse(data)
        
    except Exception as e:
        log_error(
            "View error occurred",
            view_name="my_view",
            error=str(e)
        )
        return JsonResponse({"error": "Internal error"}, status=500)
```

### In Django Models

```python
from django.db import models
from core.logger import log_info

class Recipe(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        if is_new:
            log_info(
                "Creating new recipe",
                recipe_title=self.title,
                author_id=self.author.id
            )
        else:
            log_info(
                "Updating recipe",
                recipe_id=self.pk,
                recipe_title=self.title
            )
        
        super().save(*args, **kwargs)
```

### In Django Management Commands

```python
from django.core.management.base import BaseCommand
from core.logger import log_info, log_exception

class MyCommand(BaseCommand):
    help = 'My custom management command'
    
    def handle(self, *args, **options):
        log_info("Management command started", command="my_command")
        
        try:
            # Command logic here
            self.stdout.write(self.style.SUCCESS('Command completed'))
            
        except Exception as e:
            log_exception(
                "Management command failed",
                command="my_command",
                error=str(e)
            )
            self.stdout.write(self.style.ERROR(f'Command failed: {e}'))
```

## Log Files and Rotation

### Log File Structure

The logger creates the following log files in the `logs/` directory:

- `nourishly.log` - General application logs
- `nourishly_error.log` - Error-level logs only
- `django.log` - Django framework logs
- `django_error.log` - Django error logs

### Log Rotation

Log files are automatically rotated when they reach the configured size limit (default: 10MB). The system keeps a configurable number of backup files (default: 5).

### Log Format

#### Standard Format
```
2024-01-15 10:30:45 - nourishly - INFO - views:25 - User logged in successfully
```

#### JSON Format (when enabled)
```json
{
  "timestamp": "2024-01-15 10:30:45",
  "level": "INFO",
  "logger": "nourishly",
  "module": "views",
  "line": 25,
  "message": "User logged in successfully",
  "user_id": "12345",
  "ip_address": "192.168.1.100"
}
```

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
- IP address

### Security Logging Middleware

Monitors and logs:
- Suspicious headers
- Failed authentication attempts
- Security header presence in responses

## Best Practices

### 1. Use Appropriate Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General information about application flow
- **WARNING**: Something unexpected happened but the application can continue
- **ERROR**: An error occurred that prevented a specific operation
- **CRITICAL**: A critical error that may prevent the application from running

### 2. Include Relevant Context

```python
# Good
log_info(
    "User action completed",
    user_id=user.id,
    action="recipe_create",
    recipe_id=recipe.id,
    category=recipe.category
)

# Avoid
log_info("User did something")  # Too vague
```

### 3. Don't Log Sensitive Information

```python
# Good
log_info("User logged in", user_id=user.id, ip_address=request.META.get('REMOTE_ADDR'))

# Avoid
log_info("User logged in", password=user.password, session_token=token)  # Sensitive data
```

### 4. Use Structured Logging for Complex Data

```python
# Good - structured data
log_info(
    "API response received",
    endpoint="/api/recipes",
    status_code=200,
    response_time=0.234,
    data_keys=list(response_data.keys())
)

# Avoid - unstructured
log_info(f"API response: {response_data}")  # May be too long or contain sensitive data
```

### 5. Handle Exceptions Properly

```python
try:
    result = risky_operation()
except SpecificException as e:
    log_exception(
        "Specific operation failed",
        operation="data_processing",
        error_type=type(e).__name__,
        context="user_request"
    )
    # Handle the exception appropriately
    raise
```

## Monitoring and Alerting

### Log Analysis

The structured logging format makes it easy to analyze logs using tools like:

- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Splunk**
- **Grafana + Loki**
- **AWS CloudWatch**

### Setting Up Alerts

Configure alerts for:
- High error rates
- Slow response times
- Security events
- Failed authentication attempts

### Example Alert Queries

```python
# High error rate alert
log_error_count = count(logs where level="ERROR" and timestamp > now() - 5m)
if log_error_count > 10:
    send_alert("High error rate detected")

# Slow API response alert
slow_requests = count(logs where log_type="api_request" and response_time > 1.0)
if slow_requests > 5:
    send_alert("Slow API responses detected")
```

## Troubleshooting

### Common Issues

1. **Logs not appearing**: Check if the logger is properly initialized
2. **Permission errors**: Ensure the logs directory is writable
3. **Large log files**: Adjust rotation settings or log level
4. **Performance impact**: Use appropriate log levels in production

### Debug Mode

Enable debug logging to troubleshoot logging issues:

```python
logger.initialize(level='DEBUG', console_output=True)
```

### Testing Logging

```python
import logging
from unittest.mock import patch

def test_logging():
    with patch('core.logger.logger.info') as mock_log:
        log_info("Test message")
        mock_log.assert_called_once()
```

## Migration from Django's Built-in Logging

If you're migrating from Django's built-in logging:

1. Replace `import logging` with `from core.logger import log_info, log_error`
2. Replace `logging.info()` with `log_info()`
3. Add contextual data to your log calls
4. Update your logging configuration in settings

## Conclusion

The centralized logging system provides a robust foundation for monitoring and debugging your Django application. By following these patterns and best practices, you'll have comprehensive visibility into your application's behavior and performance. 