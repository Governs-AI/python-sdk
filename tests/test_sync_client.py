# SPDX-License-Identifier: MIT
"""Unit tests for governs_ai.sync — the synchronous convenience client.

Uses `requests-mock` (built into newer requests via responses) or a plain
monkeypatched session for portability. We use unittest.mock.patch on
the underlying session for zero external test deps.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from governs_ai.sync import (
    PrecheckDecision,
    GovernsAPIError,
    SyncClient,
    precheck as oneshot_precheck,
)


def _ok_response(payload):
    r = MagicMock(spec=requests.Response)
    r.status_code = 200
    r.ok = True
    r.json.return_value = payload
    r.text = json.dumps(payload)
    return r


def _err_response(status, body):
    r = MagicMock(spec=requests.Response)
    r.status_code = status
    r.ok = False
    if isinstance(body, dict):
        r.json.return_value = body
        r.text = json.dumps(body)
    else:
        r.json.side_effect = ValueError("not json")
        r.text = body
    return r


def test_api_key_required():
    with pytest.raises(ValueError, match="api_key is required"):
        SyncClient(api_key="")


def test_api_key_from_env(monkeypatch):
    monkeypatch.setenv("GOVERNS_AI_API_KEY", "GAI_envkey")
    c = SyncClient()
    assert c.api_key == "GAI_envkey"


def test_base_url_from_env(monkeypatch):
    monkeypatch.setenv("GOVERNS_AI_API_KEY", "GAI_envkey")
    monkeypatch.setenv("GOVERNS_AI_BASE_URL", "http://localhost:8082")
    c = SyncClient()
    assert c.base_url == "http://localhost:8082"


def test_precheck_returns_decision():
    c = SyncClient(api_key="GAI_test", base_url="http://t")
    with patch.object(c._session, "post", return_value=_ok_response({
        "decision": "transform",
        "raw_text_out": "redacted",
        "reasons": ["pii.email"],
        "policy_id": "p-1",
        "ts": 12345,
    })) as mock_post:
        d = c.precheck(tool="chat", raw_text="hi jane@example.com")
        assert isinstance(d, PrecheckDecision)
        assert d.decision == "transform"
        assert d.raw_text_out == "redacted"
        assert d.allowed is True
        assert d.denied is False
        assert d.reasons == ["pii.email"]
        assert d.policy_id == "p-1"
        # verify request shape
        call = mock_post.call_args
        assert call.args[0].endswith("/api/v1/precheck")
        body = call.kwargs["json"]
        assert body == {"tool": "chat", "raw_text": "hi jane@example.com"}


def test_precheck_passes_optional_fields():
    c = SyncClient(api_key="GAI_test", base_url="http://t")
    with patch.object(c._session, "post", return_value=_ok_response({
        "decision": "allow", "raw_text_out": "x"
    })) as mock_post:
        c.precheck(
            tool="chat",
            raw_text="x",
            scope="user.write",
            user_id="u1",
            corr_id="c1",
            policy_config={"defaults": {"pii": "redact"}},
        )
        body = mock_post.call_args.kwargs["json"]
        assert body["scope"] == "user.write"
        assert body["user_id"] == "u1"
        assert body["corr_id"] == "c1"
        assert body["policy_config"] == {"defaults": {"pii": "redact"}}


def test_deny_decision_helpers():
    d = PrecheckDecision.from_dict({"decision": "deny", "raw_text_out": "", "reasons": ["x"]})
    assert d.denied
    assert not d.allowed


def test_4xx_raises_immediately_no_retry():
    c = SyncClient(api_key="GAI_test", base_url="http://t", retries=3)
    with patch.object(c._session, "post", return_value=_err_response(400, {"error": "bad"})) as mock_post:
        with pytest.raises(GovernsAPIError) as ei:
            c.precheck(tool="chat", raw_text="x")
        assert ei.value.status_code == 400
        # 4xx should NOT retry
        assert mock_post.call_count == 1


def test_5xx_retries_then_fails():
    c = SyncClient(api_key="GAI_test", base_url="http://t", retries=2, backoff_base_ms=1)
    with patch.object(c._session, "post", return_value=_err_response(503, {"error": "down"})) as mock_post:
        with pytest.raises(GovernsAPIError) as ei:
            c.precheck(tool="chat", raw_text="x")
        assert ei.value.status_code == 503
        # 2 retries + 1 initial = 3 calls
        assert mock_post.call_count == 3


def test_429_retries():
    c = SyncClient(api_key="GAI_test", base_url="http://t", retries=2, backoff_base_ms=1)
    with patch.object(c._session, "post", return_value=_err_response(429, "rate limited")) as mock_post:
        with pytest.raises(GovernsAPIError):
            c.precheck(tool="chat", raw_text="x")
        assert mock_post.call_count == 3


def test_5xx_then_ok_succeeds():
    c = SyncClient(api_key="GAI_test", base_url="http://t", retries=2, backoff_base_ms=1)
    responses = [
        _err_response(503, {"error": "down"}),
        _ok_response({"decision": "allow", "raw_text_out": "ok"}),
    ]
    with patch.object(c._session, "post", side_effect=responses):
        d = c.precheck(tool="chat", raw_text="x")
        assert d.decision == "allow"


def test_network_error_retries():
    c = SyncClient(api_key="GAI_test", base_url="http://t", retries=2, backoff_base_ms=1)
    with patch.object(c._session, "post", side_effect=requests.ConnectionError("boom")) as mock_post:
        with pytest.raises(GovernsAPIError):
            c.precheck(tool="chat", raw_text="x")
        assert mock_post.call_count == 3  # retried


def test_oneshot_precheck_uses_context_manager(monkeypatch):
    captured = {}
    real_precheck = SyncClient.precheck

    def fake_precheck(self, **kwargs):
        captured.update(kwargs)
        return PrecheckDecision.from_dict({"decision": "allow", "raw_text_out": "ok"})

    monkeypatch.setattr(SyncClient, "precheck", fake_precheck)
    monkeypatch.setattr(SyncClient, "close", lambda self: None)

    d = oneshot_precheck(api_key="GAI_x", base_url="http://t", tool="chat", raw_text="hi")
    assert d.decision == "allow"
    assert captured["tool"] == "chat"
    assert captured["raw_text"] == "hi"


def test_auth_header_set():
    c = SyncClient(api_key="GAI_secret", base_url="http://t")
    assert c._session.headers["X-Governs-Key"] == "GAI_secret"
    assert c._session.headers["Content-Type"] == "application/json"
