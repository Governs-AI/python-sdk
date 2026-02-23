# SPDX-License-Identifier: MIT
# Copyright (c) 2024 GovernsAI. All rights reserved.
"""
Core GovernsAI client for the Python SDK.
"""

import os
import asyncio
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass, field
from .utils.http import HTTPClient
from .utils.logging import GovernsAILogger, setup_logging
from .models import (
    PrecheckRequest,
    PrecheckResponse,
    BudgetContext,
    UsageRecord,
    ConfirmationRequest,
    ConfirmationResponse,
    HealthStatus,
)
from .clients.precheck import PrecheckClient
from .clients.confirmation import ConfirmationClient
from .clients.budget import BudgetClient
from .clients.tool import ToolClient
from .clients.analytics import AnalyticsClient
from .exceptions import GovernsAIError


@dataclass
class GovernsAIConfig:
    """Configuration for GovernsAI client."""

    api_key: str
    base_url: str = "http://localhost:3002"
    org_id: str = ""
    timeout: int = 30000
    retries: int = 3
    retry_delay: int = 1000
    logger: Optional[Any] = None
    http_client: Optional[HTTPClient] = None

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.api_key:
            raise ValueError("API key is required")
        if not self.org_id:
            raise ValueError("Organization ID is required")


class GovernsAIClient:
    """Main client class for GovernsAI SDK."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        org_id: Optional[str] = None,
        timeout: Optional[int] = None,
        retries: Optional[int] = None,
        retry_delay: Optional[int] = None,
        logger: Optional[Any] = None,
        http_client: Optional[HTTPClient] = None,
        config: Optional[GovernsAIConfig] = None,
    ):
        """
        Initialize GovernsAI client.

        Args:
            api_key: API key for authentication
            base_url: Base URL for the API
            org_id: Organization ID
            timeout: Request timeout in milliseconds
            retries: Number of retries for failed requests
            retry_delay: Delay between retries in milliseconds
            logger: Custom logger instance
            http_client: Custom HTTP client
            config: Complete configuration object
        """
        # Use provided config or create from parameters
        if config:
            self.config = config
        else:
            self.config = GovernsAIConfig(
                api_key=api_key or os.getenv("GOVERNS_API_KEY", ""),
                base_url=base_url or os.getenv("GOVERNS_BASE_URL", "http://localhost:3002"),
                org_id=org_id or os.getenv("GOVERNS_ORG_ID", ""),
                timeout=timeout or int(os.getenv("GOVERNS_TIMEOUT", "30000")),
                retries=retries or int(os.getenv("GOVERNS_RETRIES", "3")),
                retry_delay=retry_delay or int(os.getenv("GOVERNS_RETRY_DELAY", "1000")),
                logger=logger,
                http_client=http_client,
            )

        # Set up logger
        if self.config.logger:
            self.logger = GovernsAILogger(self.config.logger)
        else:
            self.logger = GovernsAILogger()

        # Set up HTTP client
        if self.config.http_client:
            self.http_client = self.config.http_client
        else:
            self.http_client = HTTPClient(
                base_url=self.config.base_url,
                api_key=self.config.api_key,
                timeout=self.config.timeout / 1000,  # Convert to seconds
                retries=self.config.retries,
                retry_delay=self.config.retry_delay / 1000,  # Convert to seconds
            )

        # Initialize feature clients
        self.precheck = PrecheckClient(self.http_client, self.logger)
        self.confirmation = ConfirmationClient(self.http_client, self.logger)
        self.budget = BudgetClient(self.http_client, self.logger)
        self.tools = ToolClient(self.http_client, self.logger)
        self.analytics = AnalyticsClient(self.http_client, self.logger)

    @classmethod
    def from_env(cls) -> "GovernsAIClient":
        """Create client from environment variables."""
        return cls()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the client and clean up resources."""
        if self.http_client:
            await self.http_client.close()

    async def test_connection(self) -> bool:
        """
        Test connection to the GovernsAI API.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            response = await self.http_client.get("/api/v1/health")
            return response.is_success
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False

    async def precheck_request(
        self,
        tool: str,
        scope: str,
        raw_text: str,
        payload: Dict[str, Any],
        tags: list[str],
        user_id: str,
        corr_id: Optional[str] = None,
    ) -> PrecheckResponse:
        """
        Precheck a request for governance compliance.

        Args:
            tool: Tool being used
            scope: Scope of the request
            raw_text: Raw text content
            payload: Request payload
            tags: Tags for categorization
            user_id: User ID
            corr_id: Correlation ID

        Returns:
            PrecheckResponse with decision and reasons
        """
        request = PrecheckRequest(
            tool=tool,
            scope=scope,
            raw_text=raw_text,
            payload=payload,
            tags=tags,
            corr_id=corr_id,
            user_id=user_id,
        )
        return await self.precheck.check_request(request)

    async def get_budget_context(self, user_id: str) -> BudgetContext:
        """
        Get budget context for a user.

        Args:
            user_id: User ID

        Returns:
            BudgetContext with budget information
        """
        return await self.budget.get_budget_context(user_id)

    async def record_usage(self, usage: Union[UsageRecord, Dict[str, Any]]) -> None:
        """
        Record usage for a user.

        Args:
            usage: Usage record or dictionary
        """
        if isinstance(usage, dict):
            usage = UsageRecord.from_dict(usage)
        await self.budget.record_usage(usage)

    async def create_confirmation(
        self,
        request_type: str,
        request_desc: str,
        request_payload: Dict[str, Any],
        reasons: list[str],
        user_id: str,
        correlation_id: Optional[str] = None,
    ) -> ConfirmationResponse:
        """
        Create a confirmation request.

        Args:
            request_type: Type of request
            request_desc: Description of request
            request_payload: Request payload
            reasons: Reasons for confirmation
            user_id: User ID
            correlation_id: Correlation ID

        Returns:
            ConfirmationResponse with confirmation details
        """
        request = ConfirmationRequest(
            request_type=request_type,
            request_desc=request_desc,
            request_payload=request_payload,
            reasons=reasons,
            user_id=user_id,
            correlation_id=correlation_id,
        )
        return await self.confirmation.create_confirmation(request)

    async def get_health_status(self) -> HealthStatus:
        """
        Get health status of the GovernsAI service.

        Returns:
            HealthStatus with service health information
        """
        response = await self.http_client.get("/api/v1/health")
        return HealthStatus.from_dict(response.data)

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        Update client configuration.

        Args:
            new_config: Dictionary with new configuration values
        """
        for key, value in new_config.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def get_config(self) -> GovernsAIConfig:
        """
        Get current client configuration.

        Returns:
            Current configuration
        """
        return self.config
