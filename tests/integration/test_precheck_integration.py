"""Integration tests for precheck() — require local precheck service on localhost:8000."""

import os

import pytest

from governs_ai.client import GovernsAIClient


@pytest.fixture
def client():
    return GovernsAIClient(
        api_key=os.getenv("GOVERNS_API_KEY", "dev-key"),
        base_url=os.getenv("GOVERNS_BASE_URL", "http://localhost:8000"),
        org_id=os.getenv("GOVERNS_ORG_ID", "org-dev"),
    )


@pytest.mark.integration
def test_precheck_returns_real_decision(client):
    """precheck() against local service returns a valid decision."""
    result = client.precheck(content="Hello from integration test", tool="model.chat")
    assert result.decision in ("allow", "deny", "transform", "confirm")
    assert isinstance(result.redacted_content, str)
    assert isinstance(result.reasons, list)
    assert result.latency_ms > 0


@pytest.mark.integration
async def test_async_precheck_returns_real_decision(client):
    """async_precheck() against local service returns a valid decision."""
    result = await client.async_precheck(
        content="Hello from async integration test", tool="model.chat"
    )
    assert result.decision in ("allow", "deny", "transform", "confirm")
    assert result.latency_ms > 0
