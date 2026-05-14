# SPDX-License-Identifier: MIT
"""Async convenience wrapper — for asyncio apps (FastAPI, aiohttp, etc.).

Mirrors `sync.SyncClient` but uses `httpx.AsyncClient` so it can be awaited
without blocking the event loop. Identical Decision dataclass + retry semantics.

    from governs_ai import AsyncClient
    async with AsyncClient(api_key='GAI_...', base_url='http://localhost:8082') as c:
        d = await c.precheck(tool='chat', raw_text='hi')
        if d.denied:
            raise HTTPException(status_code=403)
"""
from __future__ import annotations

import asyncio
import os
import random
from typing import Any, Dict, Optional

import aiohttp

from .sync import (
    DEFAULT_BASE_URL,
    GovernsAPIError,
    PrecheckDecision,
    USER_AGENT,
)


class AsyncClient:
    """asyncio variant of SyncClient. Same retry/error model."""

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
            raise ValueError("api_key is required (or set GOVERNS_AI_API_KEY env var)")
        self.base_url = (
            base_url or os.environ.get("GOVERNS_AI_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.timeout = timeout
        self.retries = max(0, retries)
        self.backoff_base_ms = backoff_base_ms
        self._client = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout),
            headers={
                "X-Governs-Key": self.api_key,
                "Content-Type": "application/json",
                "User-Agent": USER_AGENT + " (async)",
            },
        )

    async def precheck(
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
        return await self._post_with_retry("/api/v1/precheck", payload)

    async def postcheck(
        self, *, tool: str, raw_text: str, scope: Optional[str] = None, corr_id: Optional[str] = None,
    ) -> PrecheckDecision:
        payload: Dict[str, Any] = {"tool": tool, "raw_text": raw_text}
        if scope is not None:
            payload["scope"] = scope
        if corr_id is not None:
            payload["corr_id"] = corr_id
        return await self._post_with_retry("/api/v1/postcheck", payload)

    async def health(self) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/health"
        async with self._client.get(url) as resp:
            text = await resp.text()
            if resp.status >= 400:
                raise GovernsAPIError(resp.status, text)
            import json as _json
            return _json.loads(text)

    async def close(self) -> None:
        await self._client.close()

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, *_exc) -> None:
        await self.close()

    async def _post_with_retry(self, path: str, payload: Dict[str, Any]) -> PrecheckDecision:
        import json as _json

        url = f"{self.base_url}{path}"
        last_exc: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            try:
                async with self._client.post(url, json=payload) as resp:
                    text = await resp.text()
                    status = resp.status
            except aiohttp.ClientError as exc:
                last_exc = exc
                if attempt < self.retries:
                    await self._backoff(attempt)
                    continue
                raise GovernsAPIError(0, f"network error: {exc}") from exc

            if 200 <= status < 300:
                try:
                    body = _json.loads(text)
                except Exception:
                    raise GovernsAPIError(status, "invalid JSON", text)
                return PrecheckDecision.from_dict(body)

            if status == 429 or 500 <= status < 600:
                last_exc = GovernsAPIError(status, text)
                if attempt < self.retries:
                    await self._backoff(attempt)
                    continue

            try:
                err_body = _json.loads(text)
            except Exception:
                err_body = text
            raise GovernsAPIError(status, str(err_body), err_body)

        assert last_exc is not None
        raise last_exc  # type: ignore[misc]

    async def _backoff(self, attempt: int) -> None:
        delay_ms = min(self.backoff_base_ms * (2 ** attempt), 3000)
        delay_ms = delay_ms * (0.5 + random.random() * 0.5)
        await asyncio.sleep(delay_ms / 1000.0)
