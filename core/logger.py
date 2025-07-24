import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from functools import wraps
import time
import traceback


class LoggerSingleton:
    """
    A singleton logger class that provides centralized logging for the entire Django project.

    Features:
    - Singleton pattern ensures only one logger instance
    - Configurable log levels and handlers
    - Structured logging with context
    - Performance monitoring decorators
    - Error tracking with stack traces
    """

    _instance: Optional["LoggerSingleton"] = None
    _logger: Optional[logging.Logger] = None
    _initialized: bool = False

    def __new__(cls) -> "LoggerSingleton":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not self._initialized:
            self._logger = None
            self._initialized = True

    def initialize(
        self,
        name: str = "nourishly",
        level: str = "INFO",
        log_dir: Optional[str] = None,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        console_output: bool = True,
        file_output: bool = True,
        json_format: bool = False,
    ) -> None:
        """
        Initialize the logger with specified configuration.

        Args:
            name: Logger name
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directory for log files (if None, uses project logs directory)
            max_bytes: Maximum size of log file before rotation
            backup_count: Number of backup files to keep
            console_output: Whether to output to console
            file_output: Whether to output to file
            json_format: Whether to use JSON format for structured logging
        """
        if self._logger is not None:
            return  # Already initialized

        # Create logger
        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, level.upper()))

        # Clear any existing handlers
        self._logger.handlers.clear()

        # Create formatters
        if json_format:
            formatter = self._create_json_formatter()
        else:
            formatter = self._create_standard_formatter()

        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, level.upper()))
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)

        # File handler
        if file_output:
            if log_dir is None:
                # Use project logs directory
                project_root = Path(__file__).resolve().parent.parent
                log_dir_path = project_root / "logs"
            else:
                log_dir_path = Path(log_dir)

            # Create logs directory if it doesn't exist
            log_dir_path.mkdir(exist_ok=True)

            # Rotating file handler
            log_file = log_dir_path / f"{name}.log"
            file_handler = logging.handlers.RotatingFileHandler(
                str(log_file),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(getattr(logging, level.upper()))
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)

            # Error log file
            error_log_file = log_dir_path / f"{name}_error.log"
            error_handler = logging.handlers.RotatingFileHandler(
                str(error_log_file),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            self._logger.addHandler(error_handler)

    def _create_standard_formatter(self) -> logging.Formatter:
        """Create a standard text formatter."""
        return logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def _create_json_formatter(self) -> logging.Formatter:
        """Create a JSON formatter for structured logging."""
        import json

        class JSONFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                log_entry = {
                    "timestamp": self.formatTime(record),
                    "level": record.levelname,
                    "logger": record.name,
                    "module": record.module,
                    "line": record.lineno,
                    "message": record.getMessage(),
                }

                # Add extra fields if present
                if hasattr(record, "extra_fields"):
                    extra_fields = getattr(record, "extra_fields", {})
                    if isinstance(extra_fields, dict):
                        log_entry.update(extra_fields)

                return json.dumps(log_entry)

        return JSONFormatter()

    def _get_logger(self) -> logging.Logger:
        """Get the underlying logger instance."""
        if self._logger is None:
            # Initialize with default settings if not already done
            self.initialize()
        assert self._logger is not None  # Type guard
        return self._logger

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message."""
        self._log_with_context(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message."""
        self._log_with_context(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message."""
        self._log_with_context(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message."""
        self._log_with_context(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log a critical message."""
        self._log_with_context(logging.CRITICAL, message, **kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        """Log an exception with traceback."""
        logger = self._get_logger()
        logger.exception(message, extra={"extra_fields": kwargs})

    def _log_with_context(self, level: int, message: str, **kwargs: Any) -> None:
        """Log a message with additional context."""
        import inspect
        import os

        logger = self._get_logger()

        # Get caller information by walking up the stack
        frame = inspect.currentframe()
        try:
            # Walk up the call stack to find the actual caller
            caller_frame = frame.f_back  # Start one level up

            while caller_frame:
                filename = caller_frame.f_code.co_filename

                # Skip frames from the logger module
                if "logger.py" not in filename:
                    # Found a non-logger frame - this is our caller
                    break

                caller_frame = caller_frame.f_back

            if caller_frame:
                filename = caller_frame.f_code.co_filename
                lineno = caller_frame.f_lineno
                module_name = (
                    os.path.basename(filename).replace(".py", "")
                    if filename
                    else "unknown"
                )
            else:
                filename = "unknown"
                lineno = 0
                module_name = "unknown"

        except (AttributeError, TypeError):
            filename = "unknown"
            lineno = 0
            module_name = "unknown"
        finally:
            del frame  # Prevent reference cycles

        # Create a custom LogRecord with proper caller info
        record = logger.makeRecord(
            logger.name, level, filename, lineno, message, (), None
        )
        record.module = module_name
        record.extra_fields = kwargs

        logger.handle(record)

    def log_performance(self, func):
        """Decorator to log function performance."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                self.info(
                    f"Function {func.__name__} executed successfully",
                    function=func.__name__,
                    execution_time=execution_time,
                    status="success",
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                self.error(
                    f"Function {func.__name__} failed",
                    function=func.__name__,
                    execution_time=execution_time,
                    error=str(e),
                    status="error",
                )
                raise

        return wrapper

    def log_api_request(
        self,
        method: str,
        url: str,
        status_code: int,
        response_time: float,
        user_id: Optional[str] = None,
    ):
        """Log API request details."""
        self.info(
            f"API Request: {method} {url} - {status_code}",
            method=method,
            url=url,
            status_code=status_code,
            response_time=response_time,
            user_id=user_id,
            log_type="api_request",
        )

    def log_database_query(
        self, query: str, execution_time: float, table: Optional[str] = None
    ):
        """Log database query performance."""
        self.debug(
            f"Database query executed in {execution_time:.4f}s",
            query=query,
            execution_time=execution_time,
            table=table,
            log_type="database_query",
        )

    def log_user_action(self, user_id: str, action: str, details: Dict[str, Any]):
        """Log user actions for audit purposes."""
        self.info(
            f"User action: {action}",
            user_id=user_id,
            action=action,
            details=details,
            log_type="user_action",
        )

    def log_security_event(
        self, event_type: str, details: Dict[str, Any], severity: str = "medium"
    ):
        """Log security-related events."""
        log_method = getattr(self, severity.lower(), self.warning)
        log_method(
            f"Security event: {event_type}",
            event_type=event_type,
            details=details,
            severity=severity,
            log_type="security_event",
        )


# Global logger instance
logger = LoggerSingleton()


def get_logger(name: Optional[str] = None) -> LoggerSingleton:
    """
    Get the global logger instance.

    Args:
        name: Optional logger name (for future use with multiple loggers)

    Returns:
        LoggerSingleton instance
    """
    return logger


# Convenience functions for quick logging
def log_debug(message: str, **kwargs: Any) -> None:
    """Quick debug logging."""
    logger.debug(message, **kwargs)


def log_info(message: str, **kwargs: Any) -> None:
    """Quick info logging."""
    logger.info(message, **kwargs)


def log_warning(message: str, **kwargs: Any) -> None:
    """Quick warning logging."""
    logger.warning(message, **kwargs)


def log_error(message: str, **kwargs: Any) -> None:
    """Quick error logging."""
    logger.error(message, **kwargs)


def log_critical(message: str, **kwargs: Any) -> None:
    """Quick critical logging."""
    logger.critical(message, **kwargs)


def log_exception(message: str, **kwargs: Any) -> None:
    """Quick exception logging."""
    logger.exception(message, **kwargs)
