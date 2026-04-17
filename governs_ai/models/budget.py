# SPDX-License-Identifier: MIT
# Copyright (c) 2024 GovernsAI. All rights reserved.
"""
Budget data models for usage tracking and budget enforcement.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


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
            monthly_limit=data.get("monthly_limit", data.get("monthlyLimit")),
            current_spend=data.get("current_spend", data.get("currentSpend")),
            remaining_budget=data.get("remaining_budget", data.get("remainingBudget")),
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
class BudgetResult:
    """Result of a budget_check() call.

    Example::

        result = await client.budget_check(
            org_id="org-123", user_id="user-456", estimated_tokens=1000
        )
        if not result.allowed:
            raise RuntimeError("Budget exceeded")
        if result.warning_threshold_hit:
            logger.warning("Less than 10% budget remaining")
    """
    allowed: bool
    remaining_tokens: int
    limit: int
    warning_threshold_hit: bool = False
    reason: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BudgetResult":
        """Create from dict; auto-computes warning_threshold_hit when < 10% budget remains."""
        limit = int(data.get("limit", data.get("monthly_limit", 0)))
        remaining = int(
            data.get("remaining_tokens",
            data.get("remaining_budget",
            data.get("remainingBudget", 0)))
        )
        warning = limit > 0 and (remaining / limit) < 0.10
        return cls(
            allowed=data.get("allowed", remaining > 0),
            remaining_tokens=remaining,
            limit=limit,
            warning_threshold_hit=data.get("warningThresholdHit", warning),
            reason=data.get("reason"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "allowed": self.allowed,
            "remainingTokens": self.remaining_tokens,
            "limit": self.limit,
            "warningThresholdHit": self.warning_threshold_hit,
            "reason": self.reason,
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
            self.timestamp = datetime.utcnow().isoformat() + "Z"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UsageRecord":
        """Create from dictionary."""
        return cls(
            user_id=data.get("user_id", data.get("userId")),
            org_id=data.get("org_id", data.get("orgId")),
            provider=data["provider"],
            model=data["model"],
            input_tokens=data.get("input_tokens", data.get("inputTokens")),
            output_tokens=data.get("output_tokens", data.get("outputTokens")),
            cost=data["cost"],
            cost_type=data.get("cost_type", data.get("costType")),
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
