"""
Precheck data models for request validation and governance compliance.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from enum import Enum


class Decision(Enum):
    """Decision types for precheck responses."""
    ALLOW = "allow"
    DENY = "deny"
    BLOCK = "block"
    CONFIRM = "confirm"
    REDACT = "redact"


@dataclass
class PrecheckRequest:
    """Request model for prechecking AI operations."""
    tool: str
    scope: str
    raw_text: str
    payload: Dict[str, Any]
    tags: List[str]
    corr_id: Optional[str] = None
    user_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {
            "tool": self.tool,
            "scope": self.scope,
            "rawText": self.raw_text,
            "payload": self.payload,
            "tags": self.tags,
            "corrId": self.corr_id,
            "userId": self.user_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PrecheckRequest":
        """Create from dictionary."""
        return cls(
            tool=data["tool"],
            scope=data["scope"],
            raw_text=data["rawText"],
            payload=data["payload"],
            tags=data["tags"],
            corr_id=data.get("corrId"),
            user_id=data.get("userId"),
        )


@dataclass
class PrecheckResponse:
    """Response model for precheck operations."""
    decision: Union[Decision, str]
    reasons: List[str]
    metadata: Optional[Dict[str, Any]] = None
    requires_confirmation: bool = False
    confirmation_url: Optional[str] = None

    def __post_init__(self):
        """Convert string decision to Decision enum if needed."""
        if isinstance(self.decision, str):
            try:
                self.decision = Decision(self.decision)
            except ValueError:
                # If not a valid enum value, keep as string
                pass

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PrecheckResponse":
        """Create from dictionary."""
        return cls(
            decision=data["decision"],
            reasons=data.get("reasons", []),
            metadata=data.get("metadata"),
            requires_confirmation=data.get("requiresConfirmation", False),
            confirmation_url=data.get("confirmationUrl"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "decision": self.decision.value if isinstance(self.decision, Decision) else self.decision,
            "reasons": self.reasons,
            "metadata": self.metadata,
            "requiresConfirmation": self.requires_confirmation,
            "confirmationUrl": self.confirmation_url,
        }
