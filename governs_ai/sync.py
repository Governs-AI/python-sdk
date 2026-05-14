# SPDX-License-Identifier: MIT
"""Synchronous convenience wrapper around the GovernsAI HTTP API.

The full async client (`GovernsAIClient`) is the right tool for production
workloads. This module is the "5-second integration" surface:

    from governs_ai import precheck
    decision = precheck(
        api_key="GAI_...",
        tool="chat",
        raw_text="user input here",
        base_url="http://localhost:8082",
    )
    if decision.decision == "deny":
        ...

Returns a `Decision` dataclass with the same shape the precheck service emits.

This wrapper uses `requests` (already a hard dep in pyproject.toml) so it has
no asyncio. It is safe to call from any Python framework: Flask, FastAPI
handlers (run-in-threadpool), Django views, plain scripts.

For retries and connection pooling at scale, instantiate `SyncClient` once
and reuse it instead of calling `precheck(...)` per request.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests

DEFAULT_BASE_URL = "https://api.governsai.com"
USER_AGENT = "governs-ai-sdk-python (sync)"


class GovernsAPIError(RuntimeError):
    """Raised for any non-2xx response from the precheck service."""

    def __init__(self, status_code: int, message: str, body: Optional[Any] = None):
        super().__init__(f"GovernsAI API error {status_code}: {message}")
        self.status_code = status_code
        self.body = body


@dataclass
class PrecheckDecision:
    """Decision returned by the precheck service.

    Mirrors precheck's `DecisionResponse` (precheck/app/models.py).
    """

    decision: str  # one of: allow | transform | deny | confirm
    raw_text_out: str
    reasons: List[str] = field(default_factory=list)
    policy_id: Optional[str] = None
    ts: Optional[int] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PrecheckDecision":
        return cls(
            decision=data.get("decision", "deny"),
            raw_text_out=data.get("raw_text_out", ""),
            reasons=list(data.get("reasons") or []),
            policy_id=data.get("policy_id"),
            ts=data.get("ts"),
            raw=data,
        )

    @property
    def allowed(self) -> bool:
        return self.decision in ("allow", "transform")

    @property
    def denied(self) -> bool:
        return self.decision == "deny"


class SyncClient:
    """Synchronous client. Construct once, reuse across requests.

    Honors `GOVERNS_AI_API_KEY` and `GOVERNS_AI_BASE_URL` env vars when params
    are omitted, so it slots cleanly into 12-factor apps.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 5.0,
        retries: int = 3,
        backoff_base_ms: int = 100,
    ):
        self.api_key = api_key or os.environ.get("GOVERNS_AI_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "api_key is required (or set GOVERNS_AI_API_KEY env var)"
            )
        self.base_url = (
            base_url
            or os.environ.get("GOVERNS_AI_BASE_URL")
            or DEFAULT_BASE_URL
        ).rstrip("/")
        self.timeout = timeout
        self.retries = max(0, retries)
        self.backoff_base_ms = backoff_base_ms
        self._session = requests.Session()
        self._session.headers.update({
            "X-Governs-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        })

    def precheck(
        self,
        *,
        tool: str,
        raw_text: str,
        scope: Optional[str] = None,
        user_id: Optional[str] = None,
        corr_id: Optional[str] = None,
        policy_config: Optional[Dict[str, Any]] = None,
        tool_config: Optional[Dict[str, Any]] = None,
        budget_context: Optional[Dict[str, Any]] = None,
    ) -> PrecheckDecision:
        """Call POST /api/v1/precheck with retries + simple backoff.

        Retries only on transient failures (network errors, 5xx, 429).
        4xx errors are surfaced immediately via GovernsAPIError.
        """
        payload: Dict[str, Any] = {"tool": tool, "raw_text": raw_text}
        if scope is not None:
            payload["scope"] = scope
        if user_id is not None:
            payload["user_id"] = user_id
        if corr_id is not None:
            payload["corr_id"] = corr_id
        if policy_config is not None:
            payload["policy_config"] = policy_config
        if tool_config is not None:
            payload["tool_config"] = tool_config
        if budget_context is not None:
            payload["budget_context"] = budget_context

        return self._post_with_retry("/api/v1/precheck", payload)

    def postcheck(
        self,
        *,
        tool: str,
        raw_text: str,
        scope: Optional[str] = None,
        corr_id: Optional[str] = None,
    ) -> PrecheckDecision:
        """Call POST /api/v1/postcheck — same shape as precheck."""
        payload: Dict[str, Any] = {"tool": tool, "raw_text": raw_text}
        if scope is not None:
            payload["scope"] = scope
        if corr_id is not None:
            payload["corr_id"] = corr_id
        return self._post_with_retry("/api/v1/postcheck", payload)

    def health(self) -> Dict[str, Any]:
        """GET /api/v1/health — returns the raw payload (no Decision wrap)."""
        url = f"{self.base_url}/api/v1/health"
        resp = self._session.get(url, timeout=self.timeout)
        if not resp.ok:
            raise GovernsAPIError(resp.status_code, resp.text)
        return resp.json()

    def close(self) -> None:
        """Release the underlying TCP pool."""
        self._session.close()

    def __enter__(self) -> "SyncClient":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    # ─── internals ────────────────────────────────────────────────────
    def _post_with_retry(self, path: str, payload: Dict[str, Any]) -> PrecheckDecision:
        url = f"{self.base_url}{path}"
        last_exc: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            try:
                resp = self._session.post(url, json=payload, timeout=self.timeout)
            except requests.RequestException as exc:
                last_exc = exc
                if attempt < self.retries:
                    self._backoff(attempt)
                    continue
                raise GovernsAPIError(0, f"network error: {exc}") from exc

            if 200 <= resp.status_code < 300:
                try:
                    body = resp.json()
                except ValueError:
                    raise GovernsAPIError(resp.status_code, "invalid JSON", resp.text)
                return PrecheckDecision.from_dict(body)

            # 429 / 5xx are retriable
            if resp.status_code == 429 or 500 <= resp.status_code < 600:
                last_exc = GovernsAPIError(resp.status_code, resp.text)
                if attempt < self.retries:
                    self._backoff(attempt)
                    continue

            # 4xx (non-429) — don't retry, surface immediately
            try:
                err_body = resp.json()
            except ValueError:
                err_body = resp.text
            raise GovernsAPIError(resp.status_code, str(err_body), err_body)

        # exhausted retries
        assert last_exc is not None
        raise last_exc  # type: ignore[misc]

    def _backoff(self, attempt: int) -> None:
        # exponential backoff with full jitter, capped at ~3s
        delay_ms = min(self.backoff_base_ms * (2 ** attempt), 3000)
        # jitter 50–100% of delay_ms
        import random
        delay_ms = delay_ms * (0.5 + random.random() * 0.5)
        time.sleep(delay_ms / 1000.0)


# Module-level convenience: one-shot call without instantiating a client.
def precheck(
    *,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    tool: str,
    raw_text: str,
    **kwargs: Any,
) -> PrecheckDecision:
    """One-shot precheck. For repeated calls, prefer `SyncClient(...).precheck()`."""
    with SyncClient(api_key=api_key, base_url=base_url) as client:
        return client.precheck(tool=tool, raw_text=raw_text, **kwargs)
