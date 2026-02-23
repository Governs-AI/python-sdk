"""
Tests for Python PrecheckClient request enrichment.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from governs_ai.clients.precheck import PrecheckClient
from governs_ai.models.precheck import PrecheckRequest, Decision
from governs_ai.utils.logging import GovernsAILogger


def _mock_response(data):
    response = MagicMock()
    response.data = data
    return response


@pytest.mark.asyncio
async def test_check_request_auto_enriches_missing_context():
    """Precheck requests should auto-enrich policy/tool/budget context when missing."""
    mock_http_client = AsyncMock()

    async def get_side_effect(endpoint, params=None, headers=None):
        if endpoint == "/api/v1/policies":
            return _mock_response(
                {
                    "policies": [
                        {
                            "version": "v1",
                            "defaults": {
                                "ingress": {"action": "deny"},
                                "egress": {"action": "allow"},
                            },
                            "toolAccess": {
                                "model.chat": {"direction": "ingress", "action": "allow"}
                            },
                            "denyTools": ["python.exec"],
                            "networkScopes": ["net."],
                            "networkTools": ["web."],
                            "onError": "block",
                        }
                    ]
                }
            )
        if endpoint == "/api/v1/tools/model.chat/metadata":
            return _mock_response({"metadata": {"tool_name": "model.chat", "direction": "ingress"}})
        if endpoint == "/api/v1/budget/context":
            return _mock_response(
                {
                    "monthly_limit": 1000.0,
                    "current_spend": 100.0,
                    "llm_spend": 80.0,
                    "purchase_spend": 20.0,
                    "remaining_budget": 900.0,
                    "budget_type": "organization",
                }
            )
        raise AssertionError(f"Unexpected GET endpoint: {endpoint}")

    mock_http_client.get.side_effect = get_side_effect
    mock_http_client.post.return_value = _mock_response(
        {
            "decision": "deny",
            "reasons": ["policy.violation"],
            "requiresConfirmation": False,
        }
    )

    client = PrecheckClient(mock_http_client, GovernsAILogger())
    request = PrecheckRequest(
        tool="model.chat",
        scope="net.external",
        raw_text="hello",
        payload={"messages": [{"role": "user", "content": "hello"}]},
        tags=["sdk"],
        user_id="user-123",
    )

    response = await client.check_request(request)

    assert response.decision == Decision.DENY
    mock_http_client.post.assert_called_once()
    post_endpoint = mock_http_client.post.call_args.kwargs.get("endpoint") or mock_http_client.post.call_args.args[0]
    post_payload = mock_http_client.post.call_args.kwargs.get("data") or mock_http_client.post.call_args.args[1]

    assert post_endpoint == "/api/v1/precheck"
    assert post_payload["raw_text"] == "hello"
    assert "policy_config" in post_payload
    assert "tool_config" in post_payload
    assert "budget_context" in post_payload
