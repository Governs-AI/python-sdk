# SPDX-License-Identifier: MIT
# Copyright (c) 2024 GovernsAI. All rights reserved.
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


def _unwrap(data: Dict[str, Any]) -> Dict[str, Any]:
    """The platform nests the record under `confirmation`; accept both forms."""
    inner = data.get("confirmation")
    return inner if isinstance(inner, dict) else data


# Statuses after which nothing changes. `consumed` = approved and used once.
FINAL_STATUSES = ("approved", "denied", "expired", "cancelled", "consumed")


@dataclass
class ConfirmationResponse:
    """Response model for confirmation operations."""
    correlation_id: str
    confirmation_url: str
    status: str
    expires_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfirmationResponse":
        """Create from the platform's `/confirmation/create` response."""
        record = _unwrap(data)
        return cls(
            correlation_id=record["correlationId"],
            confirmation_url=data.get("confirmationUrl") or record.get("confirmationUrl", ""),
            status=record["status"],
            expires_at=record.get("expiresAt"),
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
    """Status model for confirmation tracking.

    status is one of pending, approved, denied, expired, cancelled, consumed.
    """
    correlation_id: str
    status: str
    approved: bool
    approved_at: Optional[str] = None
    rejected_at: Optional[str] = None
    expires_at: Optional[str] = None
    request_type: Optional[str] = None
    request_payload: Optional[Dict[str, Any]] = None

    @property
    def is_final(self) -> bool:
        return self.status in FINAL_STATUSES

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfirmationStatus":
        """Create from `GET /api/v1/confirmation/:id` (nested or flat)."""
        record = _unwrap(data)
        status = record["status"]
        return cls(
            correlation_id=record["correlationId"],
            status=status,
            approved=bool(record.get("approved", status in ("approved", "consumed"))),
            approved_at=record.get("approvedAt"),
            rejected_at=record.get("rejectedAt"),
            expires_at=record.get("expiresAt"),
            request_type=record.get("requestType"),
            request_payload=record.get("requestPayload"),
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
            "requestType": self.request_type,
            "requestPayload": self.request_payload,
        }
