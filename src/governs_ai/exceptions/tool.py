# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2026 GovernsAI. All rights reserved.
"""
Tool-specific exceptions.
"""

from typing import Optional, Dict, Any
from .base import GovernsAIError


class ToolError(GovernsAIError):
    """Exception raised for tool-related errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        retryable: bool = False,
    ):
        """Initialize tool error."""
        super().__init__(message, status_code, response_data, retryable)


class ToolNotFoundError(ToolError):
    """Exception raised when tool is not found."""

    def __init__(self, message: str, tool_name: Optional[str] = None):
        """Initialize tool not found error."""
        super().__init__(message, retryable=False)
        self.tool_name = tool_name


class ToolExecutionError(ToolError):
    """Exception raised when tool execution fails."""

    def __init__(
        self,
        message: str,
        tool_name: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        """Initialize tool execution error."""
        super().__init__(message, retryable=False)
        self.tool_name = tool_name
        self.original_error = original_error


class ToolValidationError(ToolError):
    """Exception raised for tool validation errors."""

    def __init__(self, message: str, field: Optional[str] = None):
        """Initialize tool validation error."""
        super().__init__(message, retryable=False)
        self.field = field
