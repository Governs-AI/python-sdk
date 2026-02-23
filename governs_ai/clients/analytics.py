# SPDX-License-Identifier: MIT
# Copyright (c) 2024 GovernsAI. All rights reserved.
"""
Analytics client for dashboard data and usage insights.
"""

import asyncio
from typing import Dict, Any, List, Optional
from ..models.analytics import (
    DecisionAnalytics,
    ToolCallAnalytics,
    SpendAnalytics,
    UsageRecord as AnalyticsUsageRecord,
)
from ..utils.http import HTTPClient
from ..utils.logging import GovernsAILogger
from ..exceptions.analytics import AnalyticsError


class AnalyticsClient:
    """Client for analytics operations."""

    def __init__(self, http_client: HTTPClient, logger: GovernsAILogger):
        """Initialize analytics client."""
        self.http_client = http_client
        self.logger = logger

    async def get_decisions(
        self,
        time_range: str = "30d",
        include_stats: bool = True,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> DecisionAnalytics:
        """
        Get decision analytics.

        Args:
            time_range: Time range for analytics (e.g., "7d", "30d", "90d")
            include_stats: Whether to include statistics
            user_id: Filter by user ID
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            DecisionAnalytics with decision data
        """
        try:
            self.logger.debug(f"Getting decision analytics: {time_range}")
            params = {
                "timeRange": time_range,
                "includeStats": include_stats,
            }
            if user_id:
                params["userId"] = user_id
            if limit is not None:
                params["limit"] = limit
            if offset is not None:
                params["offset"] = offset

            response = await self.http_client.get(
                "/api/v1/decisions",
                params=params,
            )
            return DecisionAnalytics.from_dict(response.data)
        except Exception as e:
            self.logger.error(f"Get decision analytics failed: {str(e)}")
            raise AnalyticsError(f"Get decision analytics failed: {str(e)}")

    async def get_tool_calls(
        self,
        time_range: str = "30d",
        include_stats: bool = True,
        user_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ToolCallAnalytics:
        """
        Get tool call analytics.

        Args:
            time_range: Time range for analytics
            include_stats: Whether to include statistics
            user_id: Filter by user ID
            tool_name: Filter by tool name
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            ToolCallAnalytics with tool call data
        """
        try:
            self.logger.debug(f"Getting tool call analytics: {time_range}")
            params = {
                "timeRange": time_range,
                "includeStats": include_stats,
            }
            if user_id:
                params["userId"] = user_id
            if tool_name:
                params["toolName"] = tool_name
            if limit is not None:
                params["limit"] = limit
            if offset is not None:
                params["offset"] = offset

            response = await self.http_client.get(
                "/api/v1/toolcalls",
                params=params,
            )
            return ToolCallAnalytics.from_dict(response.data)
        except Exception as e:
            self.logger.error(f"Get tool call analytics failed: {str(e)}")
            raise AnalyticsError(f"Get tool call analytics failed: {str(e)}")

    async def get_spend_analytics(
        self,
        time_range: str = "30d",
        user_id: Optional[str] = None,
        provider: Optional[str] = None,
        cost_type: Optional[str] = None,
    ) -> SpendAnalytics:
        """
        Get spend analytics.

        Args:
            time_range: Time range for analytics
            user_id: Filter by user ID
            provider: Filter by provider
            cost_type: Filter by cost type

        Returns:
            SpendAnalytics with spend data
        """
        try:
            self.logger.debug(f"Getting spend analytics: {time_range}")
            params = {"timeRange": time_range}
            if user_id:
                params["userId"] = user_id
            if provider:
                params["provider"] = provider
            if cost_type:
                params["costType"] = cost_type

            response = await self.http_client.get(
                "/api/v1/spend",
                params=params,
            )
            return SpendAnalytics.from_dict(response.data.get("spend", response.data))
        except Exception as e:
            self.logger.error(f"Get spend analytics failed: {str(e)}")
            raise AnalyticsError(f"Get spend analytics failed: {str(e)}")

    async def get_usage_records(
        self,
        time_range: str = "30d",
        user_id: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[AnalyticsUsageRecord]:
        """
        Get usage records.

        Args:
            time_range: Time range for analytics
            user_id: Filter by user ID
            provider: Filter by provider
            model: Filter by model
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of usage records
        """
        try:
            self.logger.debug(f"Getting usage records: {time_range}")
            params = {"timeRange": time_range}
            if user_id:
                params["userId"] = user_id
            if provider:
                params["provider"] = provider
            if model:
                params["model"] = model
            if limit is not None:
                params["limit"] = limit
            if offset is not None:
                params["offset"] = offset

            response = await self.http_client.get(
                "/api/v1/usage",
                params=params,
            )
            return [
                AnalyticsUsageRecord.from_dict(record)
                for record in response.data.get("records", response.data.get("usage", []))
            ]
        except Exception as e:
            self.logger.error(f"Get usage records failed: {str(e)}")
            raise AnalyticsError(f"Get usage records failed: {str(e)}")

    async def get_dashboard_summary(
        self,
        time_range: str = "30d",
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get dashboard summary data.

        Args:
            time_range: Time range for analytics
            user_id: Filter by user ID

        Returns:
            Dashboard summary data
        """
        try:
            self.logger.debug(f"Getting dashboard summary: {time_range}")
            decisions_task = self.get_decisions(
                time_range=time_range,
                include_stats=True,
                user_id=user_id,
                limit=100,
                offset=0,
            )
            tool_calls_task = self.get_tool_calls(
                time_range=time_range,
                include_stats=True,
                user_id=user_id,
                limit=100,
                offset=0,
            )
            spend_task = self.get_spend_analytics(time_range=time_range, user_id=user_id)
            usage_task = self.get_usage_records(
                time_range=time_range,
                user_id=user_id,
                limit=100,
                offset=0,
            )

            decisions, tool_calls, spend, usage = await asyncio.gather(
                decisions_task,
                tool_calls_task,
                spend_task,
                usage_task,
            )

            return {
                "timeRange": time_range,
                "decisions": decisions.to_dict(),
                "toolCalls": tool_calls.to_dict(),
                "spend": spend.to_dict(),
                "usage": [record.to_dict() for record in usage],
            }
        except Exception as e:
            self.logger.error(f"Get dashboard summary failed: {str(e)}")
            raise AnalyticsError(f"Get dashboard summary failed: {str(e)}")
