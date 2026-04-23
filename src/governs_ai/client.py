import asyncio
import random
import time
from typing import Any, Dict, List, Optional

import httpx

from .memory import MemoryClient
from .types import BudgetResult, PrecheckResult

_DEFAULT_RETRY_INITIAL_DELAY = 1.0
_DEFAULT_RETRY_BACKOFF_FACTOR = 2.0
_DEFAULT_RETRY_MAX_DELAY = 30.0
# Per-call precheck overrides consumed via **kwargs; anything else is forwarded
# into the request body for forward compatibility.
_PRECHECK_CONFIG_KEYS = frozenset(
    {
        "timeout",
        "max_retries",
        "retry_initial_delay",
        "retry_backoff_factor",
        "retry_max_delay",
        "jitter",
        "scope",
        "user_id",
        "corr_id",
        "tags",
        "payload",
    }
)


def _is_retryable_status(status_code: int) -> bool:
    return status_code >= 500 or status_code == 429


def _compute_retry_delay(
    attempt: int,
    initial: float,
    factor: float,
    max_delay: float,
    jitter: bool,
) -> float:
    """Exponential backoff with optional jitter, capped at ``max_delay``."""
    delay = min(initial * (factor**attempt), max_delay)
    if jitter:
        delay *= random.uniform(0.5, 1.5)
    return min(delay, max_delay)


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
        self,
        content: str,
        tool: str,
        org_id: Optional[str],
        *,
        scope: str = "net.external",
        user_id: Optional[str] = None,
        corr_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        extra_payload: Optional[Dict[str, Any]] = None,
        extras: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "tool": tool,
            "raw_text": content,
            "org_id": org_id or self.org_id,
            "scope": scope,
        }
        if user_id is not None:
            payload["user_id"] = user_id
        if corr_id is not None:
            payload["corr_id"] = corr_id
        if tags is not None:
            payload["tags"] = tags
        if extra_payload is not None:
            payload["payload"] = extra_payload
        if extras:
            # Unknown kwargs pass through so the SDK tolerates server schema growth.
            payload.update(extras)
        return payload

    def _resolve_retry_config(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Pop retry/config kwargs, falling back to client defaults."""
        return {
            "timeout": kwargs.pop("timeout", self.timeout),
            "max_retries": kwargs.pop("max_retries", self.max_retries),
            "retry_initial_delay": kwargs.pop(
                "retry_initial_delay", _DEFAULT_RETRY_INITIAL_DELAY
            ),
            "retry_backoff_factor": kwargs.pop(
                "retry_backoff_factor", _DEFAULT_RETRY_BACKOFF_FACTOR
            ),
            "retry_max_delay": kwargs.pop("retry_max_delay", _DEFAULT_RETRY_MAX_DELAY),
            "jitter": kwargs.pop("jitter", False),
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
        **kwargs: Any,
    ) -> PrecheckResult:
        """Check a content/tool request for governance compliance.

        Args:
            content: Raw user-facing text to evaluate.
            tool: Tool identifier (e.g. ``"model.chat"``).
            org_id: Organization owning the request. Falls back to the
                client-level ``org_id``.

        Keyword Args:
            timeout: Per-call timeout override (seconds).
            max_retries: Override the client-level retry ceiling.
            retry_initial_delay: First-attempt backoff delay in seconds
                (default 1.0).
            retry_backoff_factor: Multiplier applied per retry (default 2.0).
            retry_max_delay: Upper bound on a single backoff sleep (default 30.0).
            jitter: Multiply backoff by ``uniform(0.5, 1.5)`` when True.
            scope: Override the ``scope`` field (default ``"net.external"``).
            user_id, corr_id, tags, payload: Optional request body fields.
            Any other kwargs are forwarded into the request body verbatim.

        Returns:
            :class:`PrecheckResult` with decision, redacted_content, reasons,
            and client-measured ``latency_ms``.

        Raises:
            PrecheckError: On non-retryable 4xx or exhausted retries.
        """
        retry = self._resolve_retry_config(kwargs)
        payload = self._get_payload(
            content,
            tool,
            org_id,
            scope=kwargs.pop("scope", "net.external"),
            user_id=kwargs.pop("user_id", None),
            corr_id=kwargs.pop("corr_id", None),
            tags=kwargs.pop("tags", None),
            extra_payload=kwargs.pop("payload", None),
            extras={k: v for k, v in kwargs.items() if k not in _PRECHECK_CONFIG_KEYS},
        )
        start_time = time.time()

        last_error_msg = "Unknown error"
        for attempt in range(retry["max_retries"] + 1):
            try:
                with httpx.Client(timeout=retry["timeout"]) as client:
                    response = client.post(
                        f"{self.base_url}/api/v1/precheck",
                        json=payload,
                        headers=self.headers,
                    )

                    if _is_retryable_status(response.status_code):
                        last_error_msg = (
                            f"HTTP {response.status_code} {response.reason_phrase}"
                        )
                        if attempt < retry["max_retries"]:
                            time.sleep(
                                _compute_retry_delay(
                                    attempt,
                                    retry["retry_initial_delay"],
                                    retry["retry_backoff_factor"],
                                    retry["retry_max_delay"],
                                    retry["jitter"],
                                )
                            )
                            continue
                        else:
                            break

                    latency_ms = (time.time() - start_time) * 1000
                    return self._parse_response(response, latency_ms)
            except (httpx.RequestError, httpx.TimeoutException) as e:
                last_error_msg = str(e)
                if attempt < retry["max_retries"]:
                    time.sleep(
                        _compute_retry_delay(
                            attempt,
                            retry["retry_initial_delay"],
                            retry["retry_backoff_factor"],
                            retry["retry_max_delay"],
                            retry["jitter"],
                        )
                    )
                    continue

        raise PrecheckError(f"Max retries exceeded: {last_error_msg}")

    async def async_precheck(
        self,
        content: str,
        tool: str,
        org_id: Optional[str] = None,
        **kwargs: Any,
    ) -> PrecheckResult:
        """Async counterpart of :meth:`precheck` accepting the same kwargs."""
        retry = self._resolve_retry_config(kwargs)
        payload = self._get_payload(
            content,
            tool,
            org_id,
            scope=kwargs.pop("scope", "net.external"),
            user_id=kwargs.pop("user_id", None),
            corr_id=kwargs.pop("corr_id", None),
            tags=kwargs.pop("tags", None),
            extra_payload=kwargs.pop("payload", None),
            extras={k: v for k, v in kwargs.items() if k not in _PRECHECK_CONFIG_KEYS},
        )
        start_time = time.time()

        last_error_msg = "Unknown error"
        for attempt in range(retry["max_retries"] + 1):
            try:
                async with httpx.AsyncClient(timeout=retry["timeout"]) as client:
                    response = await client.post(
                        f"{self.base_url}/api/v1/precheck",
                        json=payload,
                        headers=self.headers,
                    )

                    if _is_retryable_status(response.status_code):
                        last_error_msg = (
                            f"HTTP {response.status_code} {response.reason_phrase}"
                        )
                        if attempt < retry["max_retries"]:
                            await asyncio.sleep(
                                _compute_retry_delay(
                                    attempt,
                                    retry["retry_initial_delay"],
                                    retry["retry_backoff_factor"],
                                    retry["retry_max_delay"],
                                    retry["jitter"],
                                )
                            )
                            continue
                        else:
                            break

                    latency_ms = (time.time() - start_time) * 1000
                    return self._parse_response(response, latency_ms)
            except (httpx.RequestError, httpx.TimeoutException) as e:
                last_error_msg = str(e)
                if attempt < retry["max_retries"]:
                    await asyncio.sleep(
                        _compute_retry_delay(
                            attempt,
                            retry["retry_initial_delay"],
                            retry["retry_backoff_factor"],
                            retry["retry_max_delay"],
                            retry["jitter"],
                        )
                    )
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
