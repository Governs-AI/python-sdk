import asyncio
import time
from typing import Any, Dict, Optional

import httpx

from .memory import MemoryClient
from .types import BudgetResult, PrecheckResult


class GovernsAIError(Exception):
    """Base error for GovernsAI SDK"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Any] = None,
        retryable: bool = False,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response = response
        self.retryable = retryable


class PrecheckError(GovernsAIError):
    """Error during precheck operation"""

    pass


class GovernsAIClient:
    """
    Main SDK client for GovernsAI.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.governs.ai",
        org_id: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.org_id = org_id
        self.timeout = timeout
        self.max_retries = max_retries
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-Governs-Key": self.api_key,
            "Content-Type": "application/json",
            "X-SDK-Language": "python",
        }
        self.memory = MemoryClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=self.timeout,
            org_id=self.org_id,
        )

    def __repr__(self):
        return f"<GovernsAIClient(base_url='{self.base_url}', org_id='{self.org_id}')>"

    def _get_payload(
        self, content: str, tool: str, org_id: Optional[str]
    ) -> Dict[str, Any]:
        return {
            "tool": tool,
            "raw_text": content,
            "org_id": org_id or self.org_id,
            "scope": "net.external",
        }

    def _parse_response(
        self, response: httpx.Response, latency_ms: float
    ) -> PrecheckResult:
        if response.status_code >= 400:
            try:
                error_data = response.json()
                message = error_data.get("error") or error_data.get("message")
            except Exception:
                message = None

            if not message:
                message = f"HTTP {response.status_code} {response.reason_phrase}"

            retryable = response.status_code >= 500 or response.status_code == 429
            raise PrecheckError(
                message,
                status_code=response.status_code,
                response=response,
                retryable=retryable,
            )

        data = response.json()
        return PrecheckResult(
            decision=data.get("decision", "deny"),
            redacted_content=data.get("redacted_content")
            or data.get("content", {}).get("raw_text"),
            reasons=data.get("reasons", []),
            latency_ms=latency_ms,
        )

    def precheck(
        self,
        content: str,
        tool: str,
        org_id: Optional[str] = None,
    ) -> PrecheckResult:
        """
        Check a request for governance compliance.
        """
        payload = self._get_payload(content, tool, org_id)
        start_time = time.time()

        last_error_msg = "Unknown error"
        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        f"{self.base_url}/api/v1/precheck",
                        json=payload,
                        headers=self.headers,
                    )

                    if response.status_code >= 500 or response.status_code == 429:
                        last_error_msg = (
                            f"HTTP {response.status_code} {response.reason_phrase}"
                        )
                        if attempt < self.max_retries:
                            time.sleep(2**attempt)
                            continue
                        else:
                            break

                    latency_ms = (time.time() - start_time) * 1000
                    return self._parse_response(response, latency_ms)
            except (httpx.RequestError, httpx.TimeoutException) as e:
                last_error_msg = str(e)
                if attempt < self.max_retries:
                    time.sleep(2**attempt)
                    continue

        raise PrecheckError(f"Max retries exceeded: {last_error_msg}")

    async def async_precheck(
        self,
        content: str,
        tool: str,
        org_id: Optional[str] = None,
    ) -> PrecheckResult:
        """
        Async version of precheck.
        """
        payload = self._get_payload(content, tool, org_id)
        start_time = time.time()

        last_error_msg = "Unknown error"
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/api/v1/precheck",
                        json=payload,
                        headers=self.headers,
                    )

                    if response.status_code >= 500 or response.status_code == 429:
                        last_error_msg = (
                            f"HTTP {response.status_code} {response.reason_phrase}"
                        )
                        if attempt < self.max_retries:
                            await asyncio.sleep(2**attempt)
                            continue
                        else:
                            break

                    latency_ms = (time.time() - start_time) * 1000
                    return self._parse_response(response, latency_ms)
            except (httpx.RequestError, httpx.TimeoutException) as e:
                last_error_msg = str(e)
                if attempt < self.max_retries:
                    await asyncio.sleep(2**attempt)
                    continue

        raise PrecheckError(f"Max retries exceeded: {last_error_msg}")

    # ------------------------------------------------------------------
    # 1.4c — record_usage()
    # ------------------------------------------------------------------

    def record_usage(
        self,
        org_id: str,
        user_id: str,
        tokens: int,
        model: str,
        *,
        provider: str = "openai",
    ) -> None:
        """Record token usage for a model request.

        Example::

            client.record_usage(
                org_id="org-1", user_id="user-123",
                tokens=180, model="gpt-4o-mini",
            )
        """
        payload: Dict[str, Any] = {
            "orgId": org_id or self.org_id,
            "userId": user_id,
            "inputTokens": tokens,
            "outputTokens": 0,
            "model": model,
            "provider": provider,
        }
        with httpx.Client(timeout=self.timeout) as http:
            resp = http.post(
                f"{self.base_url}/api/v1/usage",
                json=payload,
                headers=self.headers,
            )
            if resp.status_code >= 400:
                raise GovernsAIError(
                    f"record_usage failed with HTTP {resp.status_code}: {resp.text}",
                    status_code=resp.status_code,
                )

    async def async_record_usage(
        self,
        org_id: str,
        user_id: str,
        tokens: int,
        model: str,
        *,
        provider: str = "openai",
    ) -> None:
        """Async variant of :meth:`record_usage`."""
        payload: Dict[str, Any] = {
            "orgId": org_id or self.org_id,
            "userId": user_id,
            "inputTokens": tokens,
            "outputTokens": 0,
            "model": model,
            "provider": provider,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            resp = await http.post(
                f"{self.base_url}/api/v1/usage",
                json=payload,
                headers=self.headers,
            )
            if resp.status_code >= 400:
                raise GovernsAIError(
                    f"record_usage failed with HTTP {resp.status_code}: {resp.text}",
                    status_code=resp.status_code,
                )

    # ------------------------------------------------------------------
    # 1.4c — budget_check()
    # ------------------------------------------------------------------

    def budget_check(
        self,
        org_id: str,
        user_id: str,
        estimated_tokens: int = 0,
    ) -> BudgetResult:
        """Check whether the user/org is within budget.

        Example::

            budget = client.budget_check(
                org_id="org-1",
                user_id="u1",
                estimated_tokens=500,
            )
            if not budget.allowed:
                raise RuntimeError("Budget exceeded")
        """
        params: Dict[str, Any] = {
            "orgId": org_id or self.org_id,
            "userId": user_id,
            "estimatedTokens": estimated_tokens,
        }
        with httpx.Client(timeout=self.timeout) as http:
            resp = http.get(
                f"{self.base_url}/api/v1/budget/context",
                params=params,
                headers=self.headers,
            )
            if resp.status_code >= 400:
                raise GovernsAIError(
                    f"budget_check failed with HTTP {resp.status_code}: {resp.text}",
                    status_code=resp.status_code,
                )
        data = resp.json()
        limit = data.get("limit", data.get("monthly_limit", 0))
        remaining = data.get("remaining_tokens", data.get("remaining", limit))
        allowed = data.get("allowed", remaining > 0)
        warning_threshold_hit = limit > 0 and (remaining / limit) < 0.10
        return BudgetResult(
            allowed=allowed,
            remaining_tokens=int(remaining),
            limit=int(limit),
            warning_threshold_hit=warning_threshold_hit,
            reason=data.get("reason", ""),
        )

    async def async_budget_check(
        self,
        org_id: str,
        user_id: str,
        estimated_tokens: int = 0,
    ) -> BudgetResult:
        """Async variant of :meth:`budget_check`."""
        params: Dict[str, Any] = {
            "orgId": org_id or self.org_id,
            "userId": user_id,
            "estimatedTokens": estimated_tokens,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            resp = await http.get(
                f"{self.base_url}/api/v1/budget/context",
                params=params,
                headers=self.headers,
            )
            if resp.status_code >= 400:
                raise GovernsAIError(
                    f"budget_check failed with HTTP {resp.status_code}: {resp.text}",
                    status_code=resp.status_code,
                )
        data = resp.json()
        limit = data.get("limit", data.get("monthly_limit", 0))
        remaining = data.get("remaining_tokens", data.get("remaining", limit))
        allowed = data.get("allowed", remaining > 0)
        warning_threshold_hit = limit > 0 and (remaining / limit) < 0.10
        return BudgetResult(
            allowed=allowed,
            remaining_tokens=int(remaining),
            limit=int(limit),
            warning_threshold_hit=warning_threshold_hit,
            reason=data.get("reason", ""),
        )
