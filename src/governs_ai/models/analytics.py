# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2026 GovernsAI. All rights reserved.
"""
Analytics data models for dashboard data and usage insights.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List


@dataclass
class AnalyticsStats:
    """Statistics for analytics data."""

    total: int
    by_decision: Optional[Dict[str, int]] = None
    by_tool: Optional[Dict[str, int]] = None
    by_user: Optional[Dict[str, int]] = None
    by_provider: Optional[Dict[str, int]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalyticsStats":
        """Create from dictionary."""
        return cls(
            total=data["total"],
            by_decision=data.get("byDecision"),
            by_tool=data.get("byTool"),
            by_user=data.get("byUser"),
            by_provider=data.get("byProvider"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total": self.total,
            "byDecision": self.by_decision,
            "byTool": self.by_tool,
            "byUser": self.by_user,
            "byProvider": self.by_provider,
        }


@dataclass
class DecisionAnalytics:
    """Analytics data for decisions."""

    decisions: List[Dict[str, Any]]
    stats: AnalyticsStats
    time_range: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DecisionAnalytics":
        """Create from dictionary."""
        return cls(
            decisions=data["decisions"],
            stats=AnalyticsStats.from_dict(data["stats"]),
            time_range=data["timeRange"],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "decisions": self.decisions,
            "stats": self.stats.to_dict(),
            "timeRange": self.time_range,
        }


@dataclass
class ToolCallAnalytics:
    """Analytics data for tool calls."""

    tool_calls: List[Dict[str, Any]]
    stats: AnalyticsStats
    time_range: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolCallAnalytics":
        """Create from dictionary."""
        return cls(
            tool_calls=data["toolCalls"],
            stats=AnalyticsStats.from_dict(data["stats"]),
            time_range=data["timeRange"],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "toolCalls": self.tool_calls,
            "stats": self.stats.to_dict(),
            "timeRange": self.time_range,
        }


@dataclass
class SpendAnalytics:
    """Analytics data for spending."""

    total_cost: float
    by_provider: Dict[str, float]
    by_user: Dict[str, float]
    by_cost_type: Dict[str, float]
    time_range: str
    currency: str = "USD"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpendAnalytics":
        """Create from dictionary."""
        return cls(
            total_cost=data["totalCost"],
            by_provider=data["byProvider"],
            by_user=data["byUser"],
            by_cost_type=data["byCostType"],
            time_range=data["timeRange"],
            currency=data.get("currency", "USD"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "totalCost": self.total_cost,
            "byProvider": self.by_provider,
            "byUser": self.by_user,
            "byCostType": self.by_cost_type,
            "timeRange": self.time_range,
            "currency": self.currency,
        }


@dataclass
class UsageRecord:
    """Usage record for analytics."""

    user_id: str
    org_id: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    cost_type: str
    timestamp: str
    tool: Optional[str] = None
    decision: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UsageRecord":
        """Create from dictionary."""
        return cls(
            user_id=data["userId"],
            org_id=data["orgId"],
            provider=data["provider"],
            model=data["model"],
            input_tokens=data["inputTokens"],
            output_tokens=data["outputTokens"],
            cost=data["cost"],
            cost_type=data["costType"],
            timestamp=data["timestamp"],
            tool=data.get("tool"),
            decision=data.get("decision"),
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
            "tool": self.tool,
            "decision": self.decision,
        }
