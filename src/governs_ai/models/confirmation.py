# SPDX-License-Identifier: MIT
# Copyright (c) 2026 GovernsAI. All rights reserved.
"""
Confirmation data models for WebAuthn-based approval workflows.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List


@dataclass
class ConfirmationRequest:
    """Request model for creating confirmations."""

    request_type: str
    request_desc: str
    request_payload: Dict[str, Any]
    reasons: List[str]
    user_id: str
    correlation_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfirmationRequest":
        """Create from dictionary."""
        return cls(
            request_type=data["requestType"],
            request_desc=data["requestDesc"],
            request_payload=data["requestPayload"],
            reasons=data["reasons"],
            user_id=data["userId"],
            correlation_id=data.get("correlationId"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "requestType": self.request_type,
            "requestDesc": self.request_desc,
            "requestPayload": self.request_payload,
            "reasons": self.reasons,
            "userId": self.user_id,
            "correlationId": self.correlation_id,
        }


@dataclass
class ConfirmationResponse:
    """Response model for confirmation operations."""

    correlation_id: str
    confirmation_url: str
    status: str
    expires_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfirmationResponse":
        """Create from dictionary."""
        return cls(
            correlation_id=data["correlationId"],
            confirmation_url=data["confirmationUrl"],
            status=data["status"],
            expires_at=data.get("expiresAt"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "correlationId": self.correlation_id,
            "confirmationUrl": self.confirmation_url,
            "status": self.status,
            "expiresAt": self.expires_at,
        }


@dataclass
class ConfirmationStatus:
    """Status model for confirmation tracking."""

    correlation_id: str
    status: str
    approved: bool
    approved_at: Optional[str] = None
    rejected_at: Optional[str] = None
    expires_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfirmationStatus":
        """Create from dictionary."""
        return cls(
            correlation_id=data["correlationId"],
            status=data["status"],
            approved=data["approved"],
            approved_at=data.get("approvedAt"),
            rejected_at=data.get("rejectedAt"),
            expires_at=data.get("expiresAt"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "correlationId": self.correlation_id,
            "status": self.status,
            "approved": self.approved,
            "approvedAt": self.approved_at,
            "rejectedAt": self.rejected_at,
            "expiresAt": self.expires_at,
        }
