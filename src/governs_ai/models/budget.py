# SPDX-License-Identifier: MIT
# Copyright (c) 2026 GovernsAI. All rights reserved.
"""
Budget data models for usage tracking and budget enforcement.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class BudgetContext:
    """Budget context for a user."""

    monthly_limit: float
    current_spend: float
    remaining_budget: float
    currency: str = "USD"
    period_start: Optional[str] = None
    period_end: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BudgetContext":
        """Create from dictionary."""
        return cls(
            monthly_limit=float(
                data.get("monthly_limit", data.get("monthlyLimit", 0.0)) or 0.0
            ),
            current_spend=float(
                data.get("current_spend", data.get("currentSpend", 0.0)) or 0.0
            ),
            remaining_budget=float(
                data.get("remaining_budget", data.get("remainingBudget", 0.0)) or 0.0
            ),
            currency=data.get("currency", "USD"),
            period_start=data.get("period_start", data.get("periodStart")),
            period_end=data.get("period_end", data.get("periodEnd")),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "monthlyLimit": self.monthly_limit,
            "currentSpend": self.current_spend,
            "remainingBudget": self.remaining_budget,
            "currency": self.currency,
            "periodStart": self.period_start,
            "periodEnd": self.period_end,
        }


@dataclass
class BudgetStatus:
    """Budget status for a user."""

    allowed: bool
    reason: Optional[str] = None
    remaining_budget: Optional[float] = None
    estimated_cost: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BudgetStatus":
        """Create from dictionary."""
        return cls(
            allowed=data["allowed"],
            reason=data.get("reason"),
            remaining_budget=data.get("remaining_budget", data.get("remainingBudget")),
            estimated_cost=data.get("estimated_cost", data.get("estimatedCost")),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "remainingBudget": self.remaining_budget,
            "estimatedCost": self.estimated_cost,
        }


@dataclass
class UsageRecord:
    """Usage record for tracking AI operations."""

    user_id: str
    org_id: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    cost_type: str  # "internal" | "external"
    timestamp: Optional[str] = None

    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = (
                datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UsageRecord":
        """Create from dictionary."""
        return cls(
            user_id=str(data.get("user_id", data.get("userId", "")) or ""),
            org_id=str(data.get("org_id", data.get("orgId", "")) or ""),
            provider=str(data["provider"]),
            model=str(data["model"]),
            input_tokens=int(data.get("input_tokens", data.get("inputTokens", 0)) or 0),
            output_tokens=int(
                data.get("output_tokens", data.get("outputTokens", 0)) or 0
            ),
            cost=float(data["cost"]),
            cost_type=str(data.get("cost_type", data.get("costType", "")) or ""),
            timestamp=data.get("timestamp"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "userId": self.user_id,
            "orgId": self.org_id,
            "provider": self.provider,
            "model": self.model,
            "inputTokens": self.input_tokens,
            "outputTokens": self.output_tokens,
            "cost": self.cost,
            "costType": self.cost_type,
            "timestamp": self.timestamp,
        }
