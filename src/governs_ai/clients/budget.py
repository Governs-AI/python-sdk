# SPDX-License-Identifier: MIT
# Copyright (c) 2026 GovernsAI. All rights reserved.
"""
Budget client for usage tracking and budget enforcement.
"""

from typing import Dict, Any, Optional
from ..models.budget import BudgetContext, UsageRecord, BudgetStatus
from ..utils.http import HTTPClient
from ..utils.logging import GovernsAILogger
from ..exceptions.budget import BudgetError


class BudgetClient:
    """Client for budget operations."""

    def __init__(self, http_client: HTTPClient, logger: GovernsAILogger):
        """Initialize budget client."""
        self.http_client = http_client
        self.logger = logger

    async def get_budget_context(self, user_id: str) -> BudgetContext:
        """
        Get budget context for a user.

        Args:
            user_id: User ID

        Returns:
            BudgetContext with budget information
        """
        try:
            self.logger.debug(f"Getting budget context for user: {user_id}")
            response = await self.http_client.get(
                "/api/v1/budget/context",
                params={"userId": user_id},
            )
            return BudgetContext.from_dict(response.data)
        except Exception as e:
            self.logger.error(f"Get budget context failed: {str(e)}")
            raise BudgetError(f"Get budget context failed: {str(e)}")

    async def check_budget(
        self,
        estimated_cost: float,
        user_id: str,
    ) -> BudgetStatus:
        """
        Check if a user has sufficient budget for an operation.

        Args:
            estimated_cost: Estimated cost of the operation
            user_id: User ID

        Returns:
            BudgetStatus with budget check result
        """
        try:
            self.logger.debug(
                f"Checking budget for user: {user_id}, cost: {estimated_cost}"
            )
            response = await self.http_client.get(
                "/api/v1/budget/status",
                params={
                    "userId": user_id,
                    "estimatedCost": estimated_cost,
                },
            )
            status_payload = response.data.get("status", response.data)
            if isinstance(status_payload, dict) and "allowed" in status_payload:
                return BudgetStatus.from_dict(status_payload)

            # Fallback to local check when endpoint shape differs.
            context = await self.get_budget_context(user_id)
            allowed = context.remaining_budget >= estimated_cost
            return BudgetStatus(
                allowed=allowed,
                reason=None if allowed else "Insufficient budget remaining",
                remaining_budget=context.remaining_budget,
                estimated_cost=estimated_cost,
            )
        except Exception as e:
            self.logger.error(f"Check budget failed: {str(e)}")
            raise BudgetError(f"Check budget failed: {str(e)}")

    async def record_usage(self, usage: UsageRecord) -> None:
        """
        Record usage for a user.

        Args:
            usage: UsageRecord to record
        """
        try:
            self.logger.debug(f"Recording usage for user: {usage.user_id}")
            response = await self.http_client.post(
                "/api/v1/usage",
                data=usage.to_dict(),
            )
            if not response.is_success:
                raise BudgetError(f"Record usage failed: {response.data}")
        except Exception as e:
            self.logger.error(f"Record usage failed: {str(e)}")
            raise BudgetError(f"Record usage failed: {str(e)}")

    async def get_usage_history(
        self,
        user_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> list[Dict[str, Any]]:
        """
        Get usage history for a user.

        Args:
            user_id: User ID
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of usage records
        """
        try:
            self.logger.debug(f"Getting usage history for user: {user_id}")
            params: Dict[str, Any] = {}
            if limit is not None:
                params["limit"] = limit
            if offset is not None:
                params["offset"] = offset
            params["userId"] = user_id

            response = await self.http_client.get(
                "/api/v1/usage",
                params=params,
            )
            return response.data.get("records", response.data.get("usage", []))
        except Exception as e:
            self.logger.error(f"Get usage history failed: {str(e)}")
            raise BudgetError(f"Get usage history failed: {str(e)}")

    async def update_budget_limit(
        self,
        user_id: str,
        monthly_limit: float,
        currency: str = "USD",
    ) -> bool:
        """
        Update budget limit for a user.

        Args:
            user_id: User ID
            monthly_limit: New monthly limit
            currency: Currency for the limit

        Returns:
            True if update was successful
        """
        try:
            self.logger.debug(f"Updating budget limit for user: {user_id}")
            response = await self.http_client.request(
                "PATCH",
                f"/api/v1/spend/budget-limits/{user_id}",
                data={
                    "monthlyLimit": monthly_limit,
                    "currency": currency,  # Kept for backward-compatible payloads.
                },
            )
            return response.is_success
        except Exception as e:
            self.logger.error(f"Update budget limit failed: {str(e)}")
            raise BudgetError(f"Update budget limit failed: {str(e)}")
