# SPDX-License-Identifier: MIT
# Copyright (c) 2024 GovernsAI. All rights reserved.
"""
Confirmation client for WebAuthn-based approval workflows.
"""

import asyncio
from typing import Dict, Any, Optional
from ..models.confirmation import (
    ConfirmationRequest,
    ConfirmationResponse,
    ConfirmationStatus,
)
from ..utils.http import HTTPClient
from ..utils.logging import GovernsAILogger
from ..exceptions.confirmation import (
    ConfirmationError,
    ConfirmationTimeoutError,
    ConfirmationExpiredError,
    ConfirmationRejectedError,
)


class ConfirmationClient:
    """Client for confirmation operations."""

    def __init__(self, http_client: HTTPClient, logger: GovernsAILogger):
        """Initialize confirmation client."""
        self.http_client = http_client
        self.logger = logger

    async def create_confirmation(self, request: ConfirmationRequest) -> ConfirmationResponse:
        """
        Create a confirmation request.

        Args:
            request: ConfirmationRequest to create

        Returns:
            ConfirmationResponse with confirmation details
        """
        try:
            self.logger.debug(f"Creating confirmation: {request.request_type}")
            response = await self.http_client.post(
                "/api/v1/confirmation/create",
                data=request.to_dict(),
            )
            return ConfirmationResponse.from_dict(response.data)
        except Exception as e:
            self.logger.error(f"Confirmation creation failed: {str(e)}")
            raise ConfirmationError(f"Confirmation creation failed: {str(e)}")

    async def get_confirmation_status(self, correlation_id: str) -> ConfirmationStatus:
        """
        Get the status of a confirmation request.

        Args:
            correlation_id: Correlation ID of the confirmation

        Returns:
            ConfirmationStatus with current status
        """
        try:
            self.logger.debug(f"Getting confirmation status: {correlation_id}")
            response = await self.http_client.get(
                f"/api/v1/confirmation/{correlation_id}",
            )
            return ConfirmationStatus.from_dict(response.data)
        except Exception as e:
            self.logger.error(f"Get confirmation status failed: {str(e)}")
            raise ConfirmationError(f"Get confirmation status failed: {str(e)}")

    async def poll_confirmation(
        self,
        correlation_id: str,
        max_duration: int = 300000,  # 5 minutes
        poll_interval: int = 5000,   # 5 seconds
    ) -> ConfirmationStatus:
        """
        Poll for confirmation approval.

        Args:
            correlation_id: Correlation ID of the confirmation
            max_duration: Maximum duration to poll in milliseconds
            poll_interval: Interval between polls in milliseconds

        Returns:
            ConfirmationStatus with final status

        Raises:
            ConfirmationTimeoutError: If confirmation times out
            ConfirmationExpiredError: If confirmation expires
            ConfirmationRejectedError: If confirmation is rejected
        """
        start_time = asyncio.get_event_loop().time()
        max_duration_seconds = max_duration / 1000
        poll_interval_seconds = poll_interval / 1000

        while True:
            try:
                status = await self.get_confirmation_status(correlation_id)
                
                if status.status == "approved":
                    self.logger.info(f"Confirmation approved: {correlation_id}")
                    return status

                if status.status in ("denied", "cancelled", "consumed", "rejected"):
                    self.logger.warning(f"Confirmation rejected: {correlation_id}")
                    raise ConfirmationRejectedError(
                        f"Confirmation was rejected: {correlation_id}",
                        correlation_id=correlation_id,
                    )
                
                if status.status == "expired":
                    self.logger.warning(f"Confirmation expired: {correlation_id}")
                    raise ConfirmationExpiredError(
                        f"Confirmation expired: {correlation_id}",
                        correlation_id=correlation_id,
                    )

                # Check if we've exceeded max duration
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= max_duration_seconds:
                    self.logger.error(f"Confirmation timeout: {correlation_id}")
                    raise ConfirmationTimeoutError(
                        f"Confirmation timed out after {max_duration}ms: {correlation_id}",
                        correlation_id=correlation_id,
                    )

                # Wait before next poll
                await asyncio.sleep(poll_interval_seconds)

            except (ConfirmationRejectedError, ConfirmationExpiredError, ConfirmationTimeoutError):
                # Re-raise these specific errors
                raise
            except Exception as e:
                self.logger.error(f"Poll confirmation failed: {str(e)}")
                raise ConfirmationError(f"Poll confirmation failed: {str(e)}")

    async def consume_confirmation(self, correlation_id: str) -> ConfirmationStatus:
        """
        Claim an approved confirmation for exactly one execution.

        Call this right before running the approved action: it moves the
        confirmation from approved to consumed atomically, and a second call
        fails, so one approval cannot authorise two runs.

        Args:
            correlation_id: Correlation ID of the confirmation

        Returns:
            ConfirmationStatus with status "consumed"
        """
        try:
            self.logger.debug(f"Consuming confirmation: {correlation_id}")
            response = await self.http_client.post(
                f"/api/v1/confirmation/{correlation_id}/consume",
                data={},
            )
            return ConfirmationStatus.from_dict(response.data)
        except Exception as e:
            self.logger.error(f"Consume confirmation failed: {str(e)}")
            raise ConfirmationError(f"Consume confirmation failed: {str(e)}")

    async def cancel_confirmation(self, correlation_id: str) -> bool:
        """
        Cancel a confirmation request.

        Args:
            correlation_id: Correlation ID of the confirmation

        Returns:
            True if cancellation was successful
        """
        try:
            self.logger.debug(f"Cancelling confirmation: {correlation_id}")
            response = await self.http_client.post(
                "/api/v1/confirmation/cancel",
                data={"correlationId": correlation_id},
            )
            return response.is_success
        except Exception as e:
            self.logger.error(f"Cancel confirmation failed: {str(e)}")
            raise ConfirmationError(f"Cancel confirmation failed: {str(e)}")
