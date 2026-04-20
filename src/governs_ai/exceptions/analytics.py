# SPDX-License-Identifier: MIT
# Copyright (c) 2026 GovernsAI. All rights reserved.
"""
Analytics-specific exceptions.
"""

from typing import Optional, Dict, Any
from .base import GovernsAIError


class AnalyticsError(GovernsAIError):
    """Exception raised for analytics-related errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        retryable: bool = False,
    ):
        """Initialize analytics error."""
        super().__init__(message, status_code, response_data, retryable)


class AnalyticsDataError(AnalyticsError):
    """Exception raised for analytics data errors."""

    def __init__(self, message: str, time_range: Optional[str] = None):
        """Initialize analytics data error."""
        super().__init__(message, retryable=False)
        self.time_range = time_range


class AnalyticsQueryError(AnalyticsError):
    """Exception raised for analytics query errors."""

    def __init__(self, message: str, query: Optional[str] = None):
        """Initialize analytics query error."""
        super().__init__(message, retryable=False)
        self.query = query
