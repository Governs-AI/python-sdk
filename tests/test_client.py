import json
import time
from unittest.mock import patch

import pytest

from governs_ai.client import GovernsAIClient, PrecheckError
from governs_ai.types import PrecheckResult


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
