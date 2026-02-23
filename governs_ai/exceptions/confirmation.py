# SPDX-License-Identifier: MIT
# Copyright (c) 2024 GovernsAI. All rights reserved.
"""
Confirmation-specific exceptions.
"""

from typing import Optional, Dict, Any
from .base import GovernsAIError


class ConfirmationError(GovernsAIError):
    """Exception raised for confirmation-related errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        retryable: bool = False,
    ):
        """Initialize confirmation error."""
        super().__init__(message, status_code, response_data, retryable)


class ConfirmationTimeoutError(ConfirmationError):
    """Exception raised when confirmation times out."""

    def __init__(self, message: str, correlation_id: Optional[str] = None):
        """Initialize confirmation timeout error."""
        super().__init__(message, retryable=False)
        self.correlation_id = correlation_id


class ConfirmationExpiredError(ConfirmationError):
    """Exception raised when confirmation expires."""

    def __init__(self, message: str, correlation_id: Optional[str] = None):
        """Initialize confirmation expired error."""
        super().__init__(message, retryable=False)
        self.correlation_id = correlation_id


class ConfirmationRejectedError(ConfirmationError):
    """Exception raised when confirmation is rejected."""

    def __init__(self, message: str, correlation_id: Optional[str] = None):
        """Initialize confirmation rejected error."""
        super().__init__(message, retryable=False)
        self.correlation_id = correlation_id
