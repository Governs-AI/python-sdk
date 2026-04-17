# SPDX-License-Identifier: MIT
# Copyright (c) 2024 GovernsAI. All rights reserved.
"""Unit tests for record_usage() and budget_check()."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from governs_ai.models.budget import BudgetResult, UsageRecord
from governs_ai.client import GovernsAIClient, GovernsAIConfig


def _make_client() -> GovernsAIClient:
    with patch("governs_ai.client.HTTPClient"):
        client = GovernsAIClient(
            api_key="test-key", org_id="org-123", base_url="https://api.test"
        )
    return client


class TestBudgetResult:
    """Unit tests for BudgetResult model."""

    def test_from_dict_allowed(self):
        result = BudgetResult.from_dict({
            "allowed": True,
            "remaining_tokens": 9000,
            "limit": 10000,
        })
        assert result.allowed is True
        assert result.remaining_tokens == 9000
        assert result.limit == 10000
        assert result.warning_threshold_hit is False

    def test_from_dict_denied_when_budget_exceeded(self):
        result = BudgetResult.from_dict({
            "allowed": False,
            "remaining_tokens": 0,
            "limit": 10000,
            "reason": "over_budget",
        })
        assert result.allowed is False
        assert result.reason == "over_budget"

    def test_warning_threshold_hit_when_below_10_percent(self):
        result = BudgetResult.from_dict({
            "allowed": True,
            "remaining_tokens": 500,
            "limit": 10000,
        })
        assert result.warning_threshold_hit is True

    def test_warning_threshold_not_hit_at_exactly_10_percent(self):
        result = BudgetResult.from_dict({
            "allowed": True,
            "remaining_tokens": 1000,
            "limit": 10000,
        })
        # 1000/10000 == 0.10, not < 0.10
        assert result.warning_threshold_hit is False

    def test_from_dict_camelcase_keys(self):
        result = BudgetResult.from_dict({
            "allowed": True,
            "remainingBudget": 8000,
            "limit": 10000,
        })
        assert result.remaining_tokens == 8000


class TestBudgetCheckMethod:
    """Unit tests for GovernsAIClient.budget_check()."""

    @pytest.mark.asyncio
    async def test_budget_check_allowed(self):
        client = _make_client()
        mock_response = MagicMock()
        mock_response.data = {
            "allowed": True,
            "remaining_tokens": 9000,
            "limit": 10000,
        }
        client.budget.http_client.get = AsyncMock(return_value=mock_response)

        result = await client.budget_check(
            org_id="org-123", user_id="user-456", estimated_tokens=500
        )

        assert isinstance(result, BudgetResult)
        assert result.allowed is True
        assert result.warning_threshold_hit is False
        client.budget.http_client.get.assert_called_once_with(
            "/api/v1/budget/context",
            params={"orgId": "org-123", "userId": "user-456", "estimatedTokens": 500},
        )

    @pytest.mark.asyncio
    async def test_budget_check_denied_when_over_budget(self):
        client = _make_client()
        mock_response = MagicMock()
        mock_response.data = {
            "allowed": False,
            "remaining_tokens": 0,
            "limit": 10000,
            "reason": "over_budget",
        }
        client.budget.http_client.get = AsyncMock(return_value=mock_response)

        result = await client.budget_check(
            org_id="org-123", user_id="user-456", estimated_tokens=1000
        )
        assert result.allowed is False
        assert result.reason == "over_budget"

    @pytest.mark.asyncio
    async def test_budget_check_warning_threshold_hit(self):
        """warning_threshold_hit=True when remaining < 10% of limit."""
        client = _make_client()
        mock_response = MagicMock()
        mock_response.data = {
            "allowed": True,
            "remaining_tokens": 500,
            "limit": 10000,
        }
        client.budget.http_client.get = AsyncMock(return_value=mock_response)

        result = await client.budget_check(
            org_id="org-123", user_id="user-456", estimated_tokens=100
        )
        assert result.allowed is True
        assert result.warning_threshold_hit is True

    @pytest.mark.asyncio
    async def test_async_budget_check_is_alias(self):
        client = _make_client()
        mock_response = MagicMock()
        mock_response.data = {"allowed": True, "remaining_tokens": 5000, "limit": 10000}
        client.budget.http_client.get = AsyncMock(return_value=mock_response)

        result = await client.async_budget_check(
            org_id="org-123", user_id="user-456", estimated_tokens=200
        )
        assert isinstance(result, BudgetResult)


class TestRecordUsageMethod:
    """Unit tests for GovernsAIClient.record_usage()."""

    @pytest.mark.asyncio
    async def test_record_usage_correct_payload(self):
        client = _make_client()
        client.budget.record_usage = AsyncMock()

        record = UsageRecord(
            user_id="user-123",
            org_id="org-456",
            provider="openai",
            model="gpt-4o-mini",
            input_tokens=100,
            output_tokens=80,
            cost=0.0017,
            cost_type="external",
        )
        await client.record_usage(record)
        client.budget.record_usage.assert_called_once_with(record)

    @pytest.mark.asyncio
    async def test_record_usage_dict_converted_to_usage_record(self):
        client = _make_client()
        client.budget.record_usage = AsyncMock()

        await client.record_usage({
            "userId": "user-123",
            "orgId": "org-456",
            "provider": "openai",
            "model": "gpt-4",
            "inputTokens": 50,
            "outputTokens": 30,
            "cost": 0.001,
            "costType": "external",
        })
        call_arg = client.budget.record_usage.call_args[0][0]
        assert isinstance(call_arg, UsageRecord)
        assert call_arg.user_id == "user-123"
        assert call_arg.model == "gpt-4"

    @pytest.mark.asyncio
    async def test_async_record_usage_is_alias(self):
        client = _make_client()
        client.budget.record_usage = AsyncMock()

        await client.async_record_usage(
            UsageRecord(
                user_id="u", org_id="o", provider="openai", model="gpt-4",
                input_tokens=10, output_tokens=5, cost=0.0001, cost_type="external",
            )
        )
        assert client.budget.record_usage.call_count == 1
