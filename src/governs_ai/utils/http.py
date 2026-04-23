# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2026 GovernsAI. All rights reserved.
"""
HTTP client utilities for the GovernsAI Python SDK.
"""

import aiohttp
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass
from ..exceptions.base import (
    NetworkError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
)


@dataclass
class HTTPResponse:
    """HTTP response wrapper."""

    status_code: int
    data: Dict[str, Any]
    headers: Dict[str, str]
    url: str

    @property
    def is_success(self) -> bool:
        """Check if response is successful."""
        return 200 <= self.status_code < 300

    @property
    def is_client_error(self) -> bool:
        """Check if response is a client error."""
        return 400 <= self.status_code < 500

    @property
    def is_server_error(self) -> bool:
        """Check if response is a server error."""
        return 500 <= self.status_code < 600


class HTTPClient:
    """HTTP client for GovernsAI API requests."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 30,
        retries: int = 3,
        retry_delay: float = 1.0,
        session: Optional[aiohttp.ClientSession] = None,
    ):
        """Initialize HTTP client."""
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay
        self.session = session or aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout)
        )

    async def close(self):
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    def _get_headers(
        self,
        additional_headers: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = "application/json",
    ) -> Dict[str, str]:
        """Get default headers for requests."""
        headers = {
            "X-Governs-Key": self.api_key,
            "User-Agent": "governs-ai-python-sdk/1.0.0",
        }
        if content_type is not None:
            headers["Content-Type"] = content_type
        if additional_headers:
            headers.update(additional_headers)
        return headers

    def _handle_response_error(self, response: HTTPResponse) -> None:
        """Handle HTTP response errors."""
        if response.is_success:
            return

        if response.status_code == 401:
            raise AuthenticationError("Invalid API key", response.status_code)
        elif response.status_code == 403:
            raise AuthorizationError("Insufficient permissions", response.status_code)
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                "Rate limit exceeded",
                retry_after=int(retry_after) if retry_after else None,
            )
        elif response.is_client_error:
            error_msg = response.data.get("message", "Client error")
            raise NetworkError(
                f"Client error: {error_msg}", status_code=response.status_code
            )
        elif response.is_server_error:
            error_msg = response.data.get("message", "Server error")
            raise NetworkError(
                f"Server error: {error_msg}", status_code=response.status_code
            )

    async def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        form_data: Optional[aiohttp.FormData] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> HTTPResponse:
        """Make HTTP request."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_headers = self._get_headers(
            headers,
            content_type=None if form_data is not None else "application/json",
        )

        try:
            async with self.session.request(
                method=method,
                url=url,
                json=data if form_data is None else None,
                data=form_data,
                params=params,
                headers=request_headers,
            ) as response:
                # Parse response data
                try:
                    response_data = await response.json()
                except aiohttp.ContentTypeError:
                    response_data = {"message": await response.text()}

                # Create response wrapper
                http_response = HTTPResponse(
                    status_code=response.status,
                    data=response_data,
                    headers=dict(response.headers),
                    url=str(response.url),
                )

                # Handle errors
                self._handle_response_error(http_response)

                return http_response

        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error: {str(e)}", original_error=e)
        except asyncio.TimeoutError as e:
            raise NetworkError(f"Request timeout: {str(e)}", original_error=e)

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> HTTPResponse:
        """Make GET request."""
        return await self.request("GET", endpoint, params=params, headers=headers)

    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> HTTPResponse:
        """Make POST request."""
        return await self.request(
            "POST", endpoint, data=data, params=params, headers=headers
        )

    async def post_form_data(
        self,
        endpoint: str,
        form_data: aiohttp.FormData,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> HTTPResponse:
        """Make POST request with multipart/form-data payload."""
        return await self.request(
            "POST",
            endpoint,
            form_data=form_data,
            params=params,
            headers=headers,
        )

    async def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> HTTPResponse:
        """Make PUT request."""
        return await self.request(
            "PUT", endpoint, data=data, params=params, headers=headers
        )

    async def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> HTTPResponse:
        """Make DELETE request."""
        return await self.request("DELETE", endpoint, params=params, headers=headers)
