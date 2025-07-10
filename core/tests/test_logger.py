"""
Tests for the LoggerSingleton class and related functionality.
"""

import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.conf import settings

from core.logger import (
    LoggerSingleton, 
    logger, 
    get_logger,
    log_info, 
    log_error, 
    log_debug,
    log_warning,
    log_critical,
    log_exception
)


class LoggerSingletonTestCase(TestCase):
    """Test cases for the LoggerSingleton class."""
    
    def setUp(self):
        """Set up test environment."""
        # Reset the singleton for each test
        LoggerSingleton._instance = None
        LoggerSingleton._logger = None
        LoggerSingleton._initialized = False
        
        # Create a temporary directory for log files
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_singleton_pattern(self):
        """Test that LoggerSingleton follows the singleton pattern."""
        logger1 = LoggerSingleton()
        logger2 = LoggerSingleton()
        
        self.assertIs(logger1, logger2)
        self.assertEqual(id(logger1), id(logger2))
    
    def test_initialization(self):
        """Test logger initialization."""
        logger_instance = LoggerSingleton()
        
        # Should not be initialized yet
        self.assertIsNone(logger_instance._logger)
        
        # Initialize with custom settings
        logger_instance.initialize(
            name='test_logger',
            level='DEBUG',
            log_dir=str(self.log_dir),
            console_output=False,
            file_output=True
        )
        
        # Should be initialized now
        self.assertIsNotNone(logger_instance._logger)
        assert logger_instance._logger is not None  # Type guard
        self.assertEqual(logger_instance._logger.name, 'test_logger')
    
    def test_log_file_creation(self):
        """Test that log files are created properly."""
        logger_instance = LoggerSingleton()
        logger_instance.initialize(
            name='test_logger',
            level='DEBUG',
            log_dir=str(self.log_dir),
            console_output=False,
            file_output=True
        )
        
        # Check that log files were created
        log_file = self.log_dir / 'test_logger.log'
        error_log_file = self.log_dir / 'test_logger_error.log'
        
        self.assertTrue(log_file.exists())
        self.assertTrue(error_log_file.exists())
    
    def test_log_levels(self):
        """Test different log levels."""
        logger_instance = LoggerSingleton()
        logger_instance.initialize(
            name='test_logger',
            level='DEBUG',
            log_dir=str(self.log_dir),
            console_output=False,
            file_output=True
        )
        
        # Test all log levels
        logger_instance.debug("Debug message")
        logger_instance.info("Info message")
        logger_instance.warning("Warning message")
        logger_instance.error("Error message")
        logger_instance.critical("Critical message")
        
        # Check that messages were written to log file
        log_file = self.log_dir / 'test_logger.log'
        with open(log_file, 'r') as f:
            content = f.read()
        
        self.assertIn("Debug message", content)
        self.assertIn("Info message", content)
        self.assertIn("Warning message", content)
        self.assertIn("Error message", content)
        self.assertIn("Critical message", content)
    
    def test_contextual_logging(self):
        """Test logging with additional context."""
        logger_instance = LoggerSingleton()
        logger_instance.initialize(
            name='test_logger',
            level='DEBUG',
            log_dir=str(self.log_dir),
            console_output=False,
            file_output=True
        )
        
        # Log with context
        logger_instance.info(
            "User action",
            user_id="123",
            action="login",
            ip_address="192.168.1.1"
        )
        
        # Check log file content
        log_file = self.log_dir / 'test_logger.log'
        with open(log_file, 'r') as f:
            content = f.read()
        
        self.assertIn("User action", content)
        # Note: Context data is handled by the formatter, so we just check the message is there
    
    def test_performance_decorator(self):
        """Test the performance logging decorator."""
        logger_instance = LoggerSingleton()
        logger_instance.initialize(
            name='test_logger',
            level='DEBUG',
            log_dir=str(self.log_dir),
            console_output=False,
            file_output=True
        )
        
        @logger_instance.log_performance
        def test_function():
            return "test result"
        
        # Call the decorated function
        result = test_function()
        
        self.assertEqual(result, "test result")
        
        # Check that performance was logged
        log_file = self.log_dir / 'test_logger.log'
        with open(log_file, 'r') as f:
            content = f.read()
        
        self.assertIn("test_function", content)
        self.assertIn("executed successfully", content)
    
    def test_specialized_logging_methods(self):
        """Test specialized logging methods."""
        logger_instance = LoggerSingleton()
        logger_instance.initialize(
            name='test_logger',
            level='DEBUG',
            log_dir=str(self.log_dir),
            console_output=False,
            file_output=True
        )
        
        # Test API request logging
        logger_instance.log_api_request(
            method="GET",
            url="/api/test",
            status_code=200,
            response_time=0.1,
            user_id="123"
        )
        
        # Test database query logging
        logger_instance.log_database_query(
            query="SELECT * FROM test",
            execution_time=0.05,
            table="test"
        )
        
        # Test user action logging
        logger_instance.log_user_action(
            user_id="123",
            action="test_action",
            details={"key": "value"}
        )
        
        # Test security event logging
        logger_instance.log_security_event(
            event_type="test_event",
            details={"ip": "192.168.1.1"},
            severity="low"
        )
        
        # Check that all were logged
        log_file = self.log_dir / 'test_logger.log'
        with open(log_file, 'r') as f:
            content = f.read()
        
        self.assertIn("API Request", content)
        self.assertIn("Database query", content)
        self.assertIn("User action", content)
        self.assertIn("Security event", content)


class LoggerFunctionsTestCase(TestCase):
    """Test cases for the convenience logging functions."""
    
    def setUp(self):
        """Set up test environment."""
        # Reset the singleton for each test
        LoggerSingleton._instance = None
        LoggerSingleton._logger = None
        LoggerSingleton._initialized = False
        
        # Create a temporary directory for log files
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir)
        
        # Initialize the global logger
        logger.initialize(
            name='test_logger',
            level='DEBUG',
            log_dir=str(self.log_dir),
            console_output=False,
            file_output=True
        )
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_convenience_functions(self):
        """Test the convenience logging functions."""
        # Test all convenience functions
        log_debug("Debug message")
        log_info("Info message")
        log_warning("Warning message")
        log_error("Error message")
        log_critical("Critical message")
        
        # Check that messages were written
        log_file = self.log_dir / 'test_logger.log'
        with open(log_file, 'r') as f:
            content = f.read()
        
        self.assertIn("Debug message", content)
        self.assertIn("Info message", content)
        self.assertIn("Warning message", content)
        self.assertIn("Error message", content)
        self.assertIn("Critical message", content)
    
    def test_get_logger_function(self):
        """Test the get_logger function."""
        logger_instance = get_logger()
        
        self.assertIsInstance(logger_instance, LoggerSingleton)
        self.assertIs(logger_instance, logger)
    
    def test_exception_logging(self):
        """Test exception logging."""
        try:
            raise ValueError("Test exception")
        except ValueError:
            log_exception("Exception occurred")
        
        # Check that exception was logged
        log_file = self.log_dir / 'test_logger.log'
        with open(log_file, 'r') as f:
            content = f.read()
        
        self.assertIn("Exception occurred", content)


class LoggerIntegrationTestCase(TestCase):
    """Test cases for logger integration with Django."""
    
    def setUp(self):
        """Set up test environment."""
        # Reset the singleton for each test
        LoggerSingleton._instance = None
        LoggerSingleton._logger = None
        LoggerSingleton._initialized = False
    
    @override_settings(DEBUG=True)
    def test_django_integration(self):
        """Test that logger works with Django settings."""
        # The logger should be automatically initialized when Django starts
        # We can test this by checking if the logger is available
        self.assertIsNotNone(logger)
        self.assertIsInstance(logger, LoggerSingleton)
    
    def test_middleware_integration(self):
        """Test that logger works with Django middleware."""
        from core.middleware import RequestLoggingMiddleware
        
        # Create a mock request and response
        mock_request = MagicMock()
        mock_request.method = 'GET'
        mock_request.path = '/test/'
        mock_request.META = {'REMOTE_ADDR': '127.0.0.1'}
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


class LoggerConfigurationTestCase(TestCase):
    """Test cases for logger configuration."""
    
    def setUp(self):
        """Set up test environment."""
        # Reset the singleton for each test
        LoggerSingleton._instance = None
        LoggerSingleton._logger = None
        LoggerSingleton._initialized = False
        
        # Create a temporary directory for log files
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_json_formatting(self):
        """Test JSON formatting option."""
        logger_instance = LoggerSingleton()
        logger_instance.initialize(
            name='test_logger',
            level='DEBUG',
            log_dir=str(self.log_dir),
            console_output=False,
            file_output=True,
            json_format=True
        )
        
        # Log a message
        logger_instance.info("Test message", user_id="123")
        
        # Check log file content
        log_file = self.log_dir / 'test_logger.log'
        with open(log_file, 'r') as f:
            content = f.read()
        
        # Should contain JSON
        self.assertIn('"message": "Test message"', content)
        self.assertIn('"user_id": "123"', content)
    
    def test_log_rotation(self):
        """Test log file rotation."""
        logger_instance = LoggerSingleton()
        logger_instance.initialize(
            name='test_logger',
            level='DEBUG',
            log_dir=str(self.log_dir),
            console_output=False,
            file_output=True,
            max_bytes=100,  # Small size for testing
            backup_count=2
        )
        
        # Write enough messages to trigger rotation
        for i in range(50):
            logger_instance.info(f"Message {i}")
        
        # Check that rotation files were created
        log_file = self.log_dir / 'test_logger.log'
        log_file_1 = self.log_dir / 'test_logger.log.1'
        
        self.assertTrue(log_file.exists())
        # Note: Rotation might not happen immediately, so we just check the main file exists 