"""
Examples of how to use the LoggerSingleton throughout the Django project.

This file demonstrates various logging patterns and best practices.
"""

from core.logger import (
    logger, 
    get_logger, 
    log_debug, 
    log_info, 
    log_warning, 
    log_error, 
    log_critical, 
    log_exception
)


def example_basic_logging():
    """Example of basic logging usage."""
    
    # Basic logging with different levels
    log_debug("This is a debug message")
    log_info("This is an info message")
    log_warning("This is a warning message")
    log_error("This is an error message")
    log_critical("This is a critical message")
    
    # Using the logger instance directly
    logger.info("Direct logger usage")
    logger.warning("Another warning message")


def example_contextual_logging():
    """Example of logging with additional context."""
    
    # Log with user context
    log_info(
        "User logged in successfully",
        user_id="12345",
        username="john_doe",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0..."
    )
    
    # Log with business context
    log_info(
        "Recipe created successfully",
        recipe_id="recipe_789",
        recipe_name="Chicken Curry",
        author_id="user_123",
        category="main_dish",
        cooking_time=45
    )
    
    # Log with performance metrics
    log_info(
        "Database query executed",
        query="SELECT * FROM recipes WHERE category = 'main_dish'",
        execution_time=0.0234,
        rows_returned=15,
        table="recipes"
    )


def example_error_logging():
    """Example of error logging with exception handling."""
    
    try:
        # Simulate some operation that might fail
        result = 10 / 0
    except ZeroDivisionError as e:
        # Log the exception with context
        log_exception(
            "Division by zero error occurred",
            operation="division",
            dividend=10,
            divisor=0,
            error_type="ZeroDivisionError"
        )
    
    # Log errors without exceptions
    log_error(
        "Failed to connect to external API",
        api_endpoint="https://api.edamam.com/recipes",
        status_code=500,
        retry_count=3,
        timeout=30
    )


def example_performance_logging():
    """Example of using the performance logging decorator."""
    
    @logger.log_performance
    def slow_operation():
        """A slow operation that will be logged."""
        import time
        time.sleep(0.1)  # Simulate slow operation
        return "Operation completed"
    
    # This will automatically log the execution time
    result = slow_operation()


def example_api_logging():
    """Example of API request logging."""
    
    # Log API requests (typically done in middleware)
    logger.log_api_request(
        method="POST",
        url="/api/recipes/",
        status_code=201,
        response_time=0.234,
        user_id="user_123"
    )
    
    # Log API errors
    logger.log_api_request(
        method="GET",
        url="/api/recipes/999/",
        status_code=404,
        response_time=0.045,
        user_id="user_123"
    )


def example_database_logging():
    """Example of database query logging."""
    
    # Log database queries (typically done in database middleware)
    logger.log_database_query(
        query="SELECT * FROM recipes WHERE id = %s",
        execution_time=0.0123,
        table="recipes"
    )
    
    # Log slow queries
    logger.log_database_query(
        query="SELECT r.*, u.username FROM recipes r JOIN users u ON r.author_id = u.id",
        execution_time=1.234,
        table="recipes,users"
    )


def example_user_action_logging():
    """Example of user action logging for audit purposes."""
    
    # Log user actions
    logger.log_user_action(
        user_id="user_123",
        action="recipe_create",
        details={
            "recipe_name": "Spaghetti Carbonara",
            "category": "pasta",
            "ingredients_count": 8,
            "cooking_time": 30
        }
    )
    
    # Log user login/logout
    logger.log_user_action(
        user_id="user_123",
        action="user_login",
        details={
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0...",
            "login_method": "password"
        }
    )


def example_security_logging():
    """Example of security event logging."""
    
    # Log security events
    logger.log_security_event(
        event_type="failed_login",
        details={
            "username": "john_doe",
            "ip_address": "192.168.1.100",
            "attempt_count": 3,
            "user_agent": "Mozilla/5.0..."
        },
        severity="medium"
    )
    
    # Log suspicious activity
    logger.log_security_event(
        event_type="suspicious_request",
        details={
            "ip_address": "192.168.1.100",
            "request_path": "/admin/",
            "user_agent": "Bot/1.0",
            "headers": {"X-Forwarded-For": "10.0.0.1"}
        },
        severity="high"
    )


def example_structured_logging():
    """Example of structured logging with JSON format."""
    
    # Enable JSON logging (set json_format=True in logger.initialize())
    log_info(
        "Structured log entry",
        event_type="user_registration",
        user_id="new_user_456",
        registration_method="email",
        source="web_form",
        metadata={
            "referrer": "https://google.com",
            "utm_source": "organic",
            "utm_medium": "search"
        }
    )


def example_logger_in_django_views():
    """Example of using logger in Django views."""
    
    from django.http import JsonResponse
    from django.views.decorators.http import require_http_methods
    
    @require_http_methods(["GET"])
    def example_view(request):
        """Example Django view with logging."""
        
        # Log request details
        log_info(
            "View accessed",
            view_name="example_view",
            user_id=getattr(request.user, 'id', None),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        
        try:
            # Simulate some business logic
            data = {"message": "Hello, World!"}
            
            # Log successful response
            log_info(
                "View response generated successfully",
                view_name="example_view",
                response_size=len(str(data))
            )
            
            return JsonResponse(data)
            
        except Exception as e:
            # Log error
            log_exception(
                "View error occurred",
                view_name="example_view",
                error_type=type(e).__name__
            )
            
            return JsonResponse(
                {"error": "Internal server error"}, 
                status=500
            )


def example_logger_in_django_models():
    """Example of using logger in Django models."""
    
    from django.db import models
    from django.contrib.auth.models import User
    
    class Recipe(models.Model):
        """Example model with logging."""
        
        title = models.CharField(max_length=200)
        author = models.ForeignKey(User, on_delete=models.CASCADE)
        created_at = models.DateTimeField(auto_now_add=True)
        
        def save(self, *args, **kwargs):
            """Override save to add logging."""
            
            is_new = self.pk is None
            
            # Log before saving
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
                    recipe_title=self.title,
                    author_id=self.author.id
                )
            
            # Call parent save
            super().save(*args, **kwargs)
            
            # Log after saving
            if is_new:
                log_info(
                    "Recipe created successfully",
                    recipe_id=self.pk,
                    recipe_title=self.title
                )
            else:
                log_info(
                    "Recipe updated successfully",
                    recipe_id=self.pk,
                    recipe_title=self.title
                )


def example_logger_in_django_management_commands():
    """Example of using logger in Django management commands."""
    
    from django.core.management.base import BaseCommand
    
    class ExampleCommand(BaseCommand):
        """Example management command with logging."""
        
        help = 'Example command that demonstrates logging'
        
        def add_arguments(self, parser):
            parser.add_argument(
                '--dry-run',
                action='store_true',
                help='Run without making changes',
            )
        
        def handle(self, *args, **options):
            """Handle the command execution."""
            
            log_info(
                "Management command started",
                command="example_command",
                dry_run=options['dry_run']
            )
            
            try:
                # Simulate command execution
                processed_items = 0
                
                for i in range(10):
                    # Simulate processing
                    processed_items += 1
                    
                    if processed_items % 5 == 0:
                        log_info(
                            "Processing progress",
                            command="example_command",
                            processed_items=processed_items,
                            total_items=10
                        )
                
                log_info(
                    "Management command completed successfully",
                    command="example_command",
                    processed_items=processed_items
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully processed {processed_items} items')
                )
                
            except Exception as e:
                log_exception(
                    "Management command failed",
                    command="example_command",
                    error_type=type(e).__name__
                )
                
                self.stdout.write(
                    self.style.ERROR(f'Command failed: {e}')
                )


# Example usage in a real Django app
if __name__ == "__main__":
    # These examples show how to use the logger
    example_basic_logging()
    example_contextual_logging()
    example_error_logging()
    example_performance_logging() 