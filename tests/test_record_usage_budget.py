"""Unit tests for record_usage() and budget_check()."""

import json
import pytest
import respx
import httpx

from governs_ai import GovernsAIClient, BudgetResult

BASE = "https://api.governs.ai"


@pytest.fixture
def client():
    return GovernsAIClient(api_key="test-key", org_id="org-test")


@respx.mock
def test_record_usage_sends_correct_payload(client):
    route = respx.post(f"{BASE}/api/v1/usage").mock(
        return_value=httpx.Response(200, json={"accepted": True})
    )
    client.record_usage(org_id="org-1", user_id="user-123", tokens=100, model="gpt-4o")
    body = json.loads(route.calls[0].request.content)
    assert body["orgId"] == "org-1"
    assert body["userId"] == "user-123"
    assert body["inputTokens"] == 100
    assert body["model"] == "gpt-4o"


@respx.mock
async def test_async_record_usage_sends_correct_payload(client):
    route = respx.post(f"{BASE}/api/v1/usage").mock(
        return_value=httpx.Response(200, json={"accepted": True})
    )
    await client.async_record_usage(
        org_id="org-1", user_id="user-123", tokens=50, model="gpt-4o-mini"
    )
    body = json.loads(route.calls[0].request.content)
    assert body["userId"] == "user-123"
    assert body["inputTokens"] == 50


@respx.mock
def test_record_usage_succeeds_on_204_no_content(client):
    """Platform API returns 204 No Content — SDK must not raise or try to parse body."""
    respx.post(f"{BASE}/api/v1/usage").mock(return_value=httpx.Response(204))
    client.record_usage(org_id="org-1", user_id="user-123", tokens=10, model="gpt-4o")


@respx.mock
async def test_async_record_usage_succeeds_on_204_no_content(client):
    respx.post(f"{BASE}/api/v1/usage").mock(return_value=httpx.Response(204))
    await client.async_record_usage(
        org_id="org-1", user_id="user-123", tokens=10, model="gpt-4o"
    )


@respx.mock
def test_record_usage_forwards_kwargs_to_payload(client):
    """Recognised kwargs are mapped to camelCase platform fields; unknown kwargs pass through."""
    route = respx.post(f"{BASE}/api/v1/usage").mock(return_value=httpx.Response(204))
    client.record_usage(
        org_id="org-1",
        user_id="user-123",
        tokens=100,
        model="gpt-4o",
        output_tokens=50,
        cost=0.0012,
        provider="anthropic",
        tool_id="web_search",
        correlation_id="req-abc",
        metadata={"session": "s1"},
    )
    body = json.loads(route.calls[0].request.content)
    assert body["inputTokens"] == 100
    assert body["outputTokens"] == 50
    assert body["cost"] == 0.0012
    assert body["provider"] == "anthropic"
    assert body["toolId"] == "web_search"
    assert body["correlationId"] == "req-abc"
    assert body["metadata"] == {"session": "s1"}


@respx.mock
def test_budget_check_allowed(client):
    respx.get(f"{BASE}/api/v1/budget/context").mock(
        return_value=httpx.Response(
            200,
            json={
                "allowed": True,
                "remaining_tokens": 9000,
                "limit": 10000,
                "reason": "",
            },
        )
    )
    result = client.budget_check(org_id="org-1", user_id="user-1")
    assert isinstance(result, BudgetResult)
    assert result.allowed is True
    assert result.warning_threshold_hit is False


@respx.mock
def test_budget_check_denied_when_over_budget(client):
    respx.get(f"{BASE}/api/v1/budget/context").mock(
        return_value=httpx.Response(
            200,
            json={
                "allowed": False,
                "remaining_tokens": 0,
                "limit": 10000,
                "reason": "over_budget",
            },
        )
    )
    result = client.budget_check(org_id="org-1", user_id="user-1")
    assert result.allowed is False
    assert result.reason == "over_budget"


@respx.mock
def test_budget_check_warning_threshold_hit(client):
    """warning_threshold_hit=True when remaining < 10% of limit."""
    respx.get(f"{BASE}/api/v1/budget/context").mock(
        return_value=httpx.Response(
            200,
            json={
                "allowed": True,
                "remaining_tokens": 500,
                "limit": 10000,
                "reason": "",
            },
        )
    )
    result = client.budget_check(org_id="org-1", user_id="user-1")
    assert result.allowed is True
    assert result.warning_threshold_hit is True
