# Cursor Rules for Nourishly

This directory contains cursor rules that help AI assistants understand the project structure, coding conventions, and best practices for the Nourishly Django project.

## Rules Structure

### `.cursor/rules/django.mdc`
**Main Django project rules** - Comprehensive guide covering:
- Architecture patterns (selectors, services, API layers)
- Code style and conventions
- File structure
- Logging standards
- Database patterns
- Security practices
- Testing guidelines
- Performance guidelines
- Common patterns and examples

### `.cursor/rules/api.mdc`
**Django Ninja API development rules** - Specific patterns for:
- API structure and router setup
- Schema definitions
- Endpoint patterns (GET, POST, PUT, DELETE)
- Error handling and HTTP status codes
- Authentication and authorization
- Logging patterns
- Response patterns
- Query parameters and pagination
- File uploads

### `.cursor/rules/models.mdc`
**Django model development rules** - Detailed guidance for:
- Model structure and inheritance
- Field definitions and types
- Relationships (ForeignKey, ManyToMany, OneToOne)
- Model methods and properties
- Validation patterns
- Meta options
- Manager methods
- Best practices

## How to Use

### For AI Assistants
These rules are automatically applied when working with the project. The AI will:
- Follow the established patterns and conventions
- Use the correct file structure
- Apply proper error handling and logging
- Follow the selectors pattern for database queries
- Use appropriate Django Ninja patterns for APIs

### For Developers
1. **Read the rules** to understand project conventions
2. **Follow the patterns** when writing new code
3. **Update rules** when establishing new patterns
4. **Reference examples** when implementing similar functionality

## Key Patterns

### Selectors Pattern
All database queries go through selector classes:
```python
# ✅ Correct - Use selectors
data = UserSelector.get_by_id(user_id)

# ❌ Incorrect - Direct model queries in services/API
data = User.objects.get(id=user_id)
```

### Service Layer
Business logic goes in service classes:
```python
# ✅ Correct - Use services for business logic
result = UserService.create_user(data)

# ❌ Incorrect - Business logic in API endpoints
user = User.objects.create(**data)
```

### Logging
Use the centralized logging system:
```python
# ✅ Correct - Use core logger
from core.logger import log_info, log_error

log_info("Operation completed", user_id=user.id)
log_error("Operation failed", error=str(e))

# ❌ Incorrect - Direct logging
import logging
logging.info("message")
```

### API Endpoints
Follow Django Ninja patterns:
```python
@router.get("/endpoint", response=ResponseSchema)
def endpoint(request):
    """Endpoint description."""
    if not request.user.is_authenticated:
        raise HttpError(401, "Authentication required")
    
    try:
        data = Selector.get_data(request.user)
        return data
    except Exception as e:
        log_error("Endpoint failed", error=str(e))
        raise HttpError(500, "Internal server error")
```

## File Organization

### App Structure
Each Django app should follow this structure:
```
app/
├── __init__.py
├── admin.py          # Django admin configuration
├── api.py            # Django Ninja API endpoints
├── apps.py           # Django app configuration
├── models.py         # Django models
├── selectors.py      # Database query selectors
├── services.py       # Business logic services
├── tests.py          # Tests
└── views.py          # Traditional Django views (if needed)
```

### Project Structure
```
nourishly/
├── api/              # Main API router
├── core/             # Shared utilities, base models, logging
├── subscriptions/    # Subscription management
├── users/            # User management
├── recipes/          # Recipe management
├── planner/          # Meal planning
├── classify/         # AI classification
└── nourishly/        # Project settings
```

## Best Practices Summary

1. **Always use selectors for database queries**
2. **Log all important operations**
3. **Use proper error handling**
4. **Follow Django conventions**
5. **Write comprehensive tests**
6. **Use type hints everywhere**
7. **Document your code**
8. **Optimize for performance**
9. **Follow security best practices**
10. **Keep code DRY and maintainable**

## Updating Rules

When adding new patterns or conventions:

1. **Update the appropriate rule file**
2. **Add examples** for clarity
3. **Include best practices** and anti-patterns
4. **Test the rules** with AI assistants
5. **Document changes** in this README

## Contributing

When contributing to the project:

1. **Read the cursor rules** first
2. **Follow established patterns**
3. **Use the provided examples** as templates
4. **Ask for clarification** if patterns are unclear
5. **Suggest improvements** to the rules when appropriate

## Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django Ninja Documentation](https://django-ninja.rest-framework.com/)
- [PEP 8 Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [PEP 257 Docstring Conventions](https://www.python.org/dev/peps/pep-0257/) 