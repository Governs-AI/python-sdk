# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2026 GovernsAI. All rights reserved.
"""
Health status data models for service monitoring.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class HealthStatus:
    """Health status for the GovernsAI service."""

    status: str  # "healthy" | "degraded" | "unhealthy"
    services: Dict[str, str]
    timestamp: Optional[str] = None
    version: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HealthStatus":
        """Create from dictionary."""
        return cls(
            status=data["status"],
            services=data["services"],
            timestamp=data.get("timestamp"),
            version=data.get("version"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status,
            "services": self.services,
            "timestamp": self.timestamp,
            "version": self.version,
        }
