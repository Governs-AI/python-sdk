# SPDX-License-Identifier: MIT
# Copyright (c) 2024 GovernsAI. All rights reserved.
"""
GovernsAI Python SDK

A comprehensive Python SDK for integrating AI governance capabilities into your applications.
"""

from .client import GovernsAIClient, GovernsAIConfig
from .clients.precheck import PrecheckClient
from .clients.confirmation import ConfirmationClient
from .clients.budget import BudgetClient
from .clients.tool import ToolClient
from .clients.analytics import AnalyticsClient
from .clients.context import ContextClient
from .clients.documents import DocumentClient
from .models import (
    PrecheckRequest,
    PrecheckResponse,
    BudgetContext,
    UsageRecord,
    ConfirmationRequest,
    ConfirmationResponse,
    HealthStatus,
    Decision,
    SaveContextInput,
    SaveContextResponse,
    ContextLLMResponse,
    ConversationSummary,
    ConversationItem,
    MemoryRecord,
    MemorySearchMetadata,
    MemorySearchResponse,
    ResolvedUserDetails,
    ResolvedUser,
    DocumentUploadResponse,
    DocumentChunk,
    DocumentRecord,
    DocumentDetails,
    DocumentListPagination,
    DocumentListResponse,
    DocumentSearchSource,
    DocumentSearchResult,
    DocumentSearchResponse,
)
from .exceptions import (
    GovernsAIError,
    PrecheckError,
    ConfirmationError,
    BudgetError,
    ToolError,
    AnalyticsError,
)

__version__ = "1.0.0"
__author__ = "GovernsAI"
__email__ = "support@governs.ai"

__all__ = [
    # Main client
    "GovernsAIClient",
    "GovernsAIConfig",
    # Feature clients
    "PrecheckClient",
    "ConfirmationClient",
    "BudgetClient",
    "ToolClient",
    "AnalyticsClient",
    "ContextClient",
    "DocumentClient",
    # Data models
    "PrecheckRequest",
    "PrecheckResponse",
    "BudgetContext",
    "UsageRecord",
    "ConfirmationRequest",
    "ConfirmationResponse",
    "HealthStatus",
    "Decision",
    "SaveContextInput",
    "SaveContextResponse",
    "ContextLLMResponse",
    "ConversationSummary",
    "ConversationItem",
    "MemoryRecord",
    "MemorySearchMetadata",
    "MemorySearchResponse",
    "ResolvedUserDetails",
    "ResolvedUser",
    "DocumentUploadResponse",
    "DocumentChunk",
    "DocumentRecord",
    "DocumentDetails",
    "DocumentListPagination",
    "DocumentListResponse",
    "DocumentSearchSource",
    "DocumentSearchResult",
    "DocumentSearchResponse",
    # Exceptions
    "GovernsAIError",
    "PrecheckError",
    "ConfirmationError",
    "BudgetError",
    "ToolError",
    "AnalyticsError",
]
