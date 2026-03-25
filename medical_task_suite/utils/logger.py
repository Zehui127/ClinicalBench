"""
Logger Configuration for Medical Task Suite

This module provides logging configuration and utilities for the
medical task suite interfaces.
"""

import logging
import sys
from typing import Optional


# Default log format
DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def setup_logging(
    level: str = 'INFO',
    log_format: Optional[str] = None,
    log_file: Optional[str] = None,
    name: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log message format (uses default if None)
        log_file: Optional file path for file logging
        name: Optional logger name (uses root logger if None)

    Returns:
        Configured logger instance
    """
    # Convert level string to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Get or create logger
    logger = logging.getLogger(name) if name else logging.getLogger()

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    logger.setLevel(numeric_level)

    # Create formatter
    formatter = logging.Formatter(
        log_format or DEFAULT_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (typically __name__ of the module)
        level: Optional log level

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)

    if level:
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(numeric_level)

    # Add default handler if logger has no handlers
    if not logger.handlers:
        setup_logging(level=level or 'INFO', name=name)

    return logger


class LoggerMixin:
    """
    Mixin class to add logging capabilities to any class.

    Usage:
        class MyClass(LoggerMixin):
            def __init__(self):
                super().__init__()
                self.logger.info("Initialized")
    """

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        return get_logger(self.__class__.__name__)


def log_function_call(logger: Optional[logging.Logger] = None):
    """
    Decorator to log function calls.

    Usage:
        @log_function_call()
        def my_function(arg1, arg2):
            return arg1 + arg2
    """
    import functools

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_logger = logger or get_logger(func.__module__)
            func_logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")

            try:
                result = func(*args, **kwargs)
                func_logger.debug(f"{func.__name__} returned successfully")
                return result
            except Exception as e:
                func_logger.error(f"{func.__name__} raised {type(e).__name__}: {e}")
                raise

        return wrapper

    return decorator
