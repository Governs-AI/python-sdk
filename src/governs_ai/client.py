import asyncio
import time
from typing import Any, Dict, List, Optional, Union

import httpx

from .types import PrecheckResult


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
