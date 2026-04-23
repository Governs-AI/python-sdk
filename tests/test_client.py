import json
from unittest.mock import patch

import pytest

from governs_ai.client import GovernsAIClient, PrecheckError


@pytest.fixture
def client():
    return GovernsAIClient(api_key="test-key", org_id="test-org")


def test_client_init(client):
    assert client.api_key == "test-key"
    assert client.org_id == "test-org"
    assert client.base_url == "https://api.governs.ai"


def test_precheck_payload(client, httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url="https://api.governs.ai/api/v1/precheck",
        json={"decision": "allow", "reasons": []},
        status_code=200,
    )

    result = client.precheck(content="Hello", tool="test-tool")

    assert result.decision == "allow"

    # Verify request payload
    request = httpx_mock.get_request()
    assert request is not None
    data = json.loads(request.read().decode())
    assert data["tool"] == "test-tool"
    assert data["raw_text"] == "Hello"
    assert data["org_id"] == "test-org"


@pytest.mark.asyncio
async def test_async_precheck_payload(client, httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url="https://api.governs.ai/api/v1/precheck",
        json={"decision": "allow", "reasons": []},
        status_code=200,
    )

    result = await client.async_precheck(content="Hello", tool="test-tool")
    assert result.decision == "allow"

    # Verify request payload
    request = httpx_mock.get_request()
    assert request is not None
    data = json.loads(request.read().decode())
    assert data["tool"] == "test-tool"


def test_precheck_retry_on_5xx(client, httpx_mock):
    # Add two 500 errors and then a success
    httpx_mock.add_response(status_code=500)
    httpx_mock.add_response(status_code=500)
    httpx_mock.add_response(status_code=200, json={"decision": "allow"})

    with patch("time.sleep"):
        result = client.precheck(content="Hello", tool="test-tool")

    assert result.decision == "allow"
    assert len(httpx_mock.get_requests()) == 3


@pytest.mark.asyncio
async def test_async_precheck_retry_on_5xx(client, httpx_mock):
    # Add two 500 errors and then a success
    httpx_mock.add_response(status_code=500)
    httpx_mock.add_response(status_code=500)
    httpx_mock.add_response(status_code=200, json={"decision": "allow"})

    with patch("asyncio.sleep"):
        result = await client.async_precheck(content="Hello", tool="test-tool")

    assert result.decision == "allow"
    assert len(httpx_mock.get_requests()) == 3


def test_precheck_max_retries_exceeded(client, httpx_mock):
    # Add four 500 errors (max_retries is 3, so 4 attempts total)
    for _ in range(4):
        httpx_mock.add_response(status_code=500)

    with patch("time.sleep"):
        with pytest.raises(PrecheckError) as excinfo:
            client.precheck(content="Hello", tool="test-tool")

    assert "Max retries exceeded" in str(excinfo.value)
    assert len(httpx_mock.get_requests()) == 4


def test_precheck_result_fields_populated_from_response(client, httpx_mock):
    """PrecheckResult fields should all be populated from the response JSON."""
    httpx_mock.add_response(
        method="POST",
        url="https://api.governs.ai/api/v1/precheck",
        json={
            "decision": "redact",
            "redacted_content": "Hello [REDACTED]",
            "reasons": ["policy.pii", "policy.secret"],
        },
        status_code=200,
    )

    result = client.precheck(content="Hello 123-45-6789", tool="model.chat")

    assert result.decision == "redact"
    assert result.redacted_content == "Hello [REDACTED]"
    assert result.reasons == ["policy.pii", "policy.secret"]
    assert result.latency_ms > 0


def test_precheck_forwards_kwargs_into_request_body(client, httpx_mock):
    """Extra kwargs should be forwarded into the precheck request body."""
    httpx_mock.add_response(
        method="POST",
        url="https://api.governs.ai/api/v1/precheck",
        json={"decision": "allow", "reasons": []},
        status_code=200,
    )

    client.precheck(
        content="Hi",
        tool="model.chat",
        org_id="org-override",
        user_id="user-7",
        corr_id="corr-42",
        tags=["unit-test"],
        payload={"messages": [{"role": "user", "content": "Hi"}]},
        scope="net.internal",
        custom_field="pass-through",
    )

    request = httpx_mock.get_request()
    body = json.loads(request.read().decode())
    assert body["tool"] == "model.chat"
    assert body["raw_text"] == "Hi"
    assert body["org_id"] == "org-override"
    assert body["user_id"] == "user-7"
    assert body["corr_id"] == "corr-42"
    assert body["tags"] == ["unit-test"]
    assert body["scope"] == "net.internal"
    assert body["payload"] == {"messages": [{"role": "user", "content": "Hi"}]}
    # Forward-compat: unknown fields pass through unchanged.
    assert body["custom_field"] == "pass-through"


def test_precheck_uses_configurable_backoff(client, httpx_mock):
    """``retry_initial_delay`` and ``retry_backoff_factor`` should drive sleeps."""
    httpx_mock.add_response(status_code=500)
    httpx_mock.add_response(status_code=500)
    httpx_mock.add_response(status_code=200, json={"decision": "allow"})

    with patch("time.sleep") as mock_sleep:
        client.precheck(
            content="Hello",
            tool="test-tool",
            retry_initial_delay=0.25,
            retry_backoff_factor=3.0,
            jitter=False,
        )

    assert mock_sleep.call_count == 2
    delays = [call.args[0] for call in mock_sleep.call_args_list]
    # attempt 0 -> 0.25, attempt 1 -> 0.25 * 3 = 0.75
    assert delays[0] == pytest.approx(0.25)
    assert delays[1] == pytest.approx(0.75)


def test_precheck_max_retries_override_via_kwargs(client, httpx_mock):
    """Per-call ``max_retries`` override should limit attempts."""
    httpx_mock.add_response(status_code=500)
    httpx_mock.add_response(status_code=500)

    with patch("time.sleep"):
        with pytest.raises(PrecheckError):
            client.precheck(
                content="Hello",
                tool="test-tool",
                max_retries=1,
            )

    # max_retries=1 → 2 total attempts.
    assert len(httpx_mock.get_requests()) == 2


def test_precheck_does_not_retry_on_4xx(client, httpx_mock):
    """4xx responses should surface immediately without retry."""
    httpx_mock.add_response(
        status_code=400,
        json={"error": "bad request: missing tool"},
    )

    with patch("time.sleep") as mock_sleep:
        with pytest.raises(PrecheckError) as excinfo:
            client.precheck(content="Hello", tool="test-tool")

    assert len(httpx_mock.get_requests()) == 1
    assert mock_sleep.call_count == 0
    assert excinfo.value.status_code == 400
    assert "bad request" in str(excinfo.value)


def test_precheck_timeout_override_via_kwargs(client, httpx_mock):
    """Per-call ``timeout`` kwarg should not raise on happy path."""
    httpx_mock.add_response(
        method="POST",
        url="https://api.governs.ai/api/v1/precheck",
        json={"decision": "allow", "reasons": []},
        status_code=200,
    )

    result = client.precheck(content="Hi", tool="test-tool", timeout=5.0)
    assert result.decision == "allow"


@pytest.mark.asyncio
async def test_async_precheck_result_fields_populated(client, httpx_mock):
    """Async variant should populate all PrecheckResult fields."""
    httpx_mock.add_response(
        method="POST",
        url="https://api.governs.ai/api/v1/precheck",
        json={
            "decision": "deny",
            "redacted_content": None,
            "reasons": ["policy.denied"],
        },
        status_code=200,
    )

    result = await client.async_precheck(content="Hello", tool="test-tool")

    assert result.decision == "deny"
    assert result.reasons == ["policy.denied"]
    assert result.latency_ms > 0


@pytest.mark.asyncio
async def test_async_precheck_max_retries_exceeded(client, httpx_mock):
    for _ in range(3):
        httpx_mock.add_response(status_code=502)

    with patch("asyncio.sleep"):
        with pytest.raises(PrecheckError) as excinfo:
            await client.async_precheck(
                content="Hello",
                tool="test-tool",
                max_retries=2,
            )

    assert len(httpx_mock.get_requests()) == 3
    assert "Max retries exceeded" in str(excinfo.value)
