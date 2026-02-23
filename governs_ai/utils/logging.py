# SPDX-License-Identifier: MIT
# Copyright (c) 2024 GovernsAI. All rights reserved.
"""
Logging utilities for the GovernsAI Python SDK.
"""

import logging
import sys
from typing import Optional


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    logger_name: str = "governs_ai",
) -> logging.Logger:
    """
    Set up logging for the GovernsAI SDK.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string for log messages
        logger_name: Name of the logger

    Returns:
        Configured logger instance
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    # Create formatter
    formatter = logging.Formatter(format_string)
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str = "governs_ai") -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Name of the logger

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class GovernsAILogger:
    """Custom logger for GovernsAI SDK."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize with optional logger."""
        self.logger = logger or get_logger()

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, extra=kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(message, extra=kwargs)

    def log_request(self, method: str, url: str, status_code: int, duration: float):
        """Log HTTP request."""
        self.info(
            f"HTTP {method} {url} - {status_code} ({duration:.3f}s)",
            method=method,
            url=url,
            status_code=status_code,
            duration=duration,
        )

    def log_error(self, error: Exception, context: Optional[str] = None):
        """Log error with context."""
        error_msg = f"Error: {str(error)}"
        if context:
            error_msg = f"{context} - {error_msg}"
        self.error(error_msg, error_type=type(error).__name__, context=context)
