# SPDX-License-Identifier: MIT
# Copyright (c) 2024 GovernsAI. All rights reserved.
"""ConfirmationClient against the platform's real routes and response shapes."""

from unittest.mock import AsyncMock

import pytest

from governs_ai.clients.confirmation import ConfirmationClient
from governs_ai.exceptions.confirmation import ConfirmationRejectedError
from governs_ai.models.confirmation import ConfirmationRequest, ConfirmationStatus
from governs_ai.utils.http import HTTPResponse
from governs_ai.utils.logging import GovernsAILogger


def _resp(data, status=200):
    return HTTPResponse(status_code=status, data=data, headers={}, url="")


def _record(status):
    return {
        "confirmation": {
            "correlationId": "corr-1",
            "status": status,
            "requestType": "tool_call",
            "requestPayload": {"tool": "payment_process", "args": {"amount": 5}},
            "expiresAt": "2026-10-25T10:00:00Z",
        }
    }


@pytest.fixture
def http():
    return AsyncMock()


@pytest.mark.asyncio
async def test_create_posts_to_platform_route(http):
    http.post.return_value = _resp(
        {
            "success": True,
            "confirmation": {"correlationId": "corr-1", "status": "pending"},
            "confirmationUrl": "http://localhost:3002/confirm/corr-1",
        }
    )
    client = ConfirmationClient(http, GovernsAILogger())
    created = await client.create_confirmation(
        ConfirmationRequest(
            request_type="tool_call",
            request_desc="Run payment_process",
            request_payload={"tool": "payment_process"},
            reasons=["tool-specific.confirm"],
            user_id="u1",
            correlation_id="corr-1",
        )
    )
    assert http.post.call_args.args[0] == "/api/v1/confirmation/create"
    assert created.correlation_id == "corr-1"
    assert created.confirmation_url.endswith("/confirm/corr-1")


@pytest.mark.asyncio
async def test_status_unwraps_nested_record(http):
    http.get.return_value = _resp(_record("approved"))
    client = ConfirmationClient(http, GovernsAILogger())
    status = await client.get_confirmation_status("corr-1")
    assert http.get.call_args.args[0] == "/api/v1/confirmation/corr-1"
    assert status.approved is True
    assert status.is_final
    assert status.request_payload["tool"] == "payment_process"


@pytest.mark.asyncio
async def test_poll_raises_on_denied(http):
    http.get.return_value = _resp(_record("denied"))
    client = ConfirmationClient(http, GovernsAILogger())
    with pytest.raises(ConfirmationRejectedError):
        await client.poll_confirmation("corr-1", max_duration=1000, poll_interval=10)


@pytest.mark.asyncio
async def test_consume_and_cancel_routes(http):
    http.post.return_value = _resp(_record("consumed"))
    client = ConfirmationClient(http, GovernsAILogger())
    consumed = await client.consume_confirmation("corr-1")
    assert http.post.call_args.args[0] == "/api/v1/confirmation/corr-1/consume"
    assert consumed.status == "consumed"

    http.post.return_value = _resp({"success": True})
    assert await client.cancel_confirmation("corr-1") is True
    assert http.post.call_args.args[0] == "/api/v1/confirmation/cancel"
    assert http.post.call_args.kwargs["data"] == {"correlationId": "corr-1"}


def test_pending_is_not_final():
    assert not ConfirmationStatus.from_dict(_record("pending")).is_final
