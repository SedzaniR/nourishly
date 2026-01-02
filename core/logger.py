"""
Logging utilities for the Nourishly project.

This module provides convenience functions that wrap Python's standard logging
module. All logging configuration is handled through Django's LOGGING settings.
"""

import logging
from typing import Any


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance using Python's standard logging.

    Args:
        name: Logger name. If None, uses the calling module's name.
              Use '__name__' for module-specific loggers.

    Returns:
        logging.Logger instance
    """
    if name is None:
        import inspect

        frame = inspect.currentframe()
        try:
            # Get the caller's module name
            caller_frame = frame.f_back
            module_name = caller_frame.f_globals.get("__name__", "nourishly")
        finally:
            del frame
        return logging.getLogger(module_name)
    return logging.getLogger(name)


def _log_with_extra(
    level: int, message: str, logger: logging.Logger, **kwargs: Any
) -> None:
    """Internal helper to log with extra context."""
    # Convert kwargs to extra dict for structured logging
    extra = {"extra_fields": kwargs} if kwargs else {}
    logger.log(level, message, extra=extra)


def log_debug(message: str, **kwargs: Any) -> None:
    """Log a debug message with optional context."""
    logger = get_logger("nourishly")
    _log_with_extra(logging.DEBUG, message, logger, **kwargs)


def log_info(message: str, **kwargs: Any) -> None:
    """Log an info message with optional context."""
    logger = get_logger("nourishly")
    _log_with_extra(logging.INFO, message, logger, **kwargs)


def log_warning(message: str, **kwargs: Any) -> None:
    """Log a warning message with optional context."""
    logger = get_logger("nourishly")
    _log_with_extra(logging.WARNING, message, logger, **kwargs)


def log_error(message: str, **kwargs: Any) -> None:
    """Log an error message with optional context."""
    logger = get_logger("nourishly")
    _log_with_extra(logging.ERROR, message, logger, **kwargs)


def log_critical(message: str, **kwargs: Any) -> None:
    """Log a critical message with optional context."""
    logger = get_logger("nourishly")
    _log_with_extra(logging.CRITICAL, message, logger, **kwargs)


def log_exception(message: str, **kwargs: Any) -> None:
    """Log an exception with traceback and optional context."""
    logger = get_logger("nourishly")
    extra = {"extra_fields": kwargs} if kwargs else {}
    logger.exception(message, extra=extra)
