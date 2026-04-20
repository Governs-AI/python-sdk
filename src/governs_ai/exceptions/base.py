# SPDX-License-Identifier: MIT
# Copyright (c) 2026 GovernsAI. All rights reserved.
"""
Base exception classes for the GovernsAI Python SDK.
"""

from typing import Optional, Dict, Any


class GovernsAIError(Exception):
    """Base exception for all GovernsAI SDK errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        retryable: bool = False,
    ):
        """Initialize the exception."""
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        self.retryable = retryable

    def __str__(self) -> str:
        """Return string representation."""
        base_msg = f"GovernsAI Error: {self.message}"
        if self.status_code:
            base_msg += f" (Status: {self.status_code})"
        return base_msg


class NetworkError(GovernsAIError):
    """Network-related errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        original_error: Optional[Exception] = None,
    ):
        """Initialize network error."""
        super().__init__(message, status_code=status_code, retryable=True)
        self.original_error = original_error


class AuthenticationError(GovernsAIError):
    """Authentication-related errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        """Initialize authentication error."""
        super().__init__(message, status_code=status_code, retryable=False)


class AuthorizationError(GovernsAIError):
    """Authorization-related errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        """Initialize authorization error."""
        super().__init__(message, status_code=status_code, retryable=False)


class RateLimitError(GovernsAIError):
    """Rate limiting errors."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        """Initialize rate limit error."""
        super().__init__(message, retryable=True)
        self.retry_after = retry_after


class ValidationError(GovernsAIError):
    """Validation errors."""

    def __init__(self, message: str, field: Optional[str] = None):
        """Initialize validation error."""
        super().__init__(message, retryable=False)
        self.field = field
