# SPDX-License-Identifier: MIT
"""Unit tests for governs_ai.async_client.AsyncClient.

Uses aiohttp's built-in test server (no external mock dep needed).
"""
from __future__ import annotations

import asyncio
import pytest

from aiohttp import web

from governs_ai import AsyncClient, GovernsAPIError, PrecheckDecision


@pytest.fixture
async def server(aiohttp_server):
    calls = {"precheck": 0, "fail_modes": []}

    async def precheck_handler(request):
        calls["precheck"] += 1
        # check the API key got through
        assert request.headers.get("X-Governs-Key") == "GAI_test"
        body = await request.json()
        # Honor fail_modes for retry tests
        if calls["fail_modes"]:
            mode = calls["fail_modes"].pop(0)
            if mode == "5xx":
                return web.json_response({"error": "down"}, status=503)
            if mode == "429":
                return web.json_response({"error": "slow down"}, status=429)
            if mode == "4xx":
                return web.json_response({"error": "bad"}, status=400)
        return web.json_response({
            "decision": "transform",
            "raw_text_out": f"redacted: {body['raw_text']}",
            "reasons": ["pii.email"],
            "policy_id": "p-1",
            "ts": 12345,
        })

    async def health_handler(request):
        return web.json_response({"ok": True, "service": "test"})

    app = web.Application()
    app.router.add_post("/api/v1/precheck", precheck_handler)
    app.router.add_get("/api/v1/health", health_handler)
    s = await aiohttp_server(app)
    s.calls = calls  # type: ignore[attr-defined]
    return s


@pytest.mark.asyncio
async def test_precheck_returns_decision(server):
    async with AsyncClient(api_key="GAI_test", base_url=str(server.make_url("")).rstrip("/")) as c:
        d = await c.precheck(tool="chat", raw_text="hello jane@example.com")
        assert isinstance(d, PrecheckDecision)
        assert d.decision == "transform"
        assert "redacted:" in d.raw_text_out
        assert d.reasons == ["pii.email"]


@pytest.mark.asyncio
async def test_health(server):
    async with AsyncClient(api_key="GAI_test", base_url=str(server.make_url("")).rstrip("/")) as c:
        h = await c.health()
        assert h == {"ok": True, "service": "test"}


@pytest.mark.asyncio
async def test_5xx_retries_then_succeeds(server):
    server.calls["fail_modes"] = ["5xx", "5xx"]  # first two attempts fail, third wins
    async with AsyncClient(api_key="GAI_test", base_url=str(server.make_url("")).rstrip("/"),
                           retries=2, backoff_base_ms=1) as c:
        d = await c.precheck(tool="chat", raw_text="x")
        assert d.decision == "transform"
        assert server.calls["precheck"] == 3


@pytest.mark.asyncio
async def test_429_retries(server):
    server.calls["fail_modes"] = ["429", "429"]
    async with AsyncClient(api_key="GAI_test", base_url=str(server.make_url("")).rstrip("/"),
                           retries=2, backoff_base_ms=1) as c:
        d = await c.precheck(tool="chat", raw_text="x")
        assert d.decision == "transform"
        assert server.calls["precheck"] == 3


@pytest.mark.asyncio
async def test_4xx_raises_no_retry(server):
    server.calls["fail_modes"] = ["4xx"]
    async with AsyncClient(api_key="GAI_test", base_url=str(server.make_url("")).rstrip("/"),
                           retries=3, backoff_base_ms=1) as c:
        with pytest.raises(GovernsAPIError) as ei:
            await c.precheck(tool="chat", raw_text="x")
        assert ei.value.status_code == 400
        assert server.calls["precheck"] == 1  # no retry


@pytest.mark.asyncio
async def test_api_key_required():
    with pytest.raises(ValueError, match="api_key is required"):
        AsyncClient(api_key="")


@pytest.mark.asyncio
async def test_env_var_pickup(monkeypatch):
    monkeypatch.setenv("GOVERNS_AI_API_KEY", "GAI_env")
    monkeypatch.setenv("GOVERNS_AI_BASE_URL", "http://envtest")
    c = AsyncClient()
    assert c.api_key == "GAI_env"
    assert c.base_url == "http://envtest"
    await c.close()
