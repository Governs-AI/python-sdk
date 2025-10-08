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
from .models import (
    PrecheckRequest,
    PrecheckResponse,
    BudgetContext,
    UsageRecord,
    ConfirmationRequest,
    ConfirmationResponse,
    HealthStatus,
    Decision,
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
    # Data models
    "PrecheckRequest",
    "PrecheckResponse",
    "BudgetContext",
    "UsageRecord",
    "ConfirmationRequest",
    "ConfirmationResponse",
    "HealthStatus",
    "Decision",
    # Exceptions
    "GovernsAIError",
    "PrecheckError",
    "ConfirmationError",
    "BudgetError",
    "ToolError",
    "AnalyticsError",
]
