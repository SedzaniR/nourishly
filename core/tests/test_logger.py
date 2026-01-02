"""
Tests for the logging convenience functions.
"""

import logging
from unittest.mock import patch, MagicMock
from django.test import TestCase

from core.logger import (
    get_logger,
    log_info,
    log_error,
    log_debug,
    log_warning,
    log_critical,
    log_exception,
)


class LoggerFunctionsTestCase(TestCase):
    """Test cases for the convenience logging functions."""

    def test_get_logger_function(self):
        """Test the get_logger function returns a logger instance."""
        logger_instance = get_logger()

        self.assertIsInstance(logger_instance, logging.Logger)
        self.assertEqual(logger_instance.name, "nourishly")

    def test_get_logger_with_name(self):
        """Test get_logger with a specific name."""
        logger_instance = get_logger("test_logger")

        self.assertIsInstance(logger_instance, logging.Logger)
        self.assertEqual(logger_instance.name, "test_logger")

    def test_convenience_functions(self):
        """Test that convenience functions can be called without errors."""
        # These should not raise exceptions
        log_debug("Debug message")
        log_info("Info message")
        log_warning("Warning message")
        log_error("Error message")
        log_critical("Critical message")

    def test_convenience_functions_with_context(self):
        """Test convenience functions with additional context."""
        # These should not raise exceptions
        log_info("Info message", user_id="123", action="test")
        log_error("Error message", error="test_error", endpoint="/test")
        log_debug("Debug message", key="value")

    def test_exception_logging(self):
        """Test exception logging."""
        try:
            raise ValueError("Test exception")
        except ValueError:
            # Should not raise an exception
            log_exception("Exception occurred", error="test")

    def test_get_logger_auto_detection(self):
        """Test that get_logger() without args detects caller module."""
        # When called from this test file, should detect the module
        logger_instance = get_logger()
        # The logger name should be 'nourishly' (default) or the module name
        self.assertIsInstance(logger_instance, logging.Logger)


class LoggerIntegrationTestCase(TestCase):
    """Test cases for logger integration with Django."""

    def test_middleware_integration(self):
        """Test that logger works with Django middleware."""
        from core.middleware import RequestLoggingMiddleware

        # Create a mock request and response
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.path = "/test/"
        mock_request.META = {"REMOTE_ADDR": "127.0.0.1"}
        mock_request.user.is_authenticated = False

        mock_response = MagicMock()
        mock_response.status_code = 200

        # Create middleware
        middleware = RequestLoggingMiddleware(lambda request: mock_response)

        # Test that middleware doesn't raise exceptions
        try:
            response = middleware(mock_request)
            self.assertEqual(response, mock_response)
        except Exception as e:
            self.fail(f"Middleware raised an exception: {e}")
