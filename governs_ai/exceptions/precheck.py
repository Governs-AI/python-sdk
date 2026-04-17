# SPDX-License-Identifier: MIT
# Copyright (c) 2024 GovernsAI. All rights reserved.
"""
Precheck-specific exceptions.
"""

from typing import Any, Dict, Optional

from .base import GovernsAIError


class PrecheckError(GovernsAIError):
    """Exception raised for precheck-related errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        retryable: bool = False,
    ):
        """Initialize precheck error."""
        super().__init__(message, status_code, response_data, retryable)


class PrecheckValidationError(PrecheckError):
    """Exception raised for precheck validation errors."""

    def __init__(self, message: str, field: Optional[str] = None):
        """Initialize precheck validation error."""
        super().__init__(message, retryable=False)
        self.field = field


class PrecheckPolicyError(PrecheckError):
    """Exception raised for policy-related precheck errors."""

    def __init__(self, message: str, policy_name: Optional[str] = None):
        """Initialize precheck policy error."""
        super().__init__(message, retryable=False)
        self.policy_name = policy_name
