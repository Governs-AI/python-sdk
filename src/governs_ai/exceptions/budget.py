# SPDX-License-Identifier: MIT
# Copyright (c) 2026 GovernsAI. All rights reserved.
"""
Budget-specific exceptions.
"""

from typing import Optional, Dict, Any
from .base import GovernsAIError


class BudgetError(GovernsAIError):
    """Exception raised for budget-related errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        retryable: bool = False,
    ):
        """Initialize budget error."""
        super().__init__(message, status_code, response_data, retryable)


class BudgetExceededError(BudgetError):
    """Exception raised when budget is exceeded."""

    def __init__(
        self,
        message: str,
        user_id: Optional[str] = None,
        remaining_budget: Optional[float] = None,
    ):
        """Initialize budget exceeded error."""
        super().__init__(message, retryable=False)
        self.user_id = user_id
        self.remaining_budget = remaining_budget


class BudgetValidationError(BudgetError):
    """Exception raised for budget validation errors."""

    def __init__(self, message: str, field: Optional[str] = None):
        """Initialize budget validation error."""
        super().__init__(message, retryable=False)
        self.field = field
