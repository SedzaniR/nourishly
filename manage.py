#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # Check for --settings argument first
    if '--settings' in sys.argv:
        # Use Django's built-in settings argument
        pass
    else:
        # Auto-detect environment
        if os.environ.get('DJANGO_ENV'):
            environment = os.environ['DJANGO_ENV']
        elif os.environ.get('ENVIRONMENT'):
            environment = os.environ['ENVIRONMENT']
        else:
            environment = 'development'
        
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'nourishly.settings.{environment}')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
