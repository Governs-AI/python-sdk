"""
Precheck client for request validation and governance compliance.
"""

import json
from typing import Dict, Any, List, Optional
from ..models.precheck import PrecheckRequest, PrecheckResponse
from ..utils.http import HTTPClient
from ..utils.logging import GovernsAILogger
from ..exceptions.precheck import PrecheckError


class PrecheckClient:
    """Client for precheck operations."""

    def __init__(self, http_client: HTTPClient, logger: GovernsAILogger):
        """Initialize precheck client."""
        self.http_client = http_client
        self.logger = logger

    async def check_request(self, request: PrecheckRequest) -> PrecheckResponse:
        """
        Check a request for governance compliance.

        Args:
            request: PrecheckRequest to validate

        Returns:
            PrecheckResponse with decision and reasons
        """
        try:
            self.logger.debug(f"Prechecking request: {request.tool}")
            response = await self.http_client.post(
                "/precheck",
                data=request.to_dict(),
            )
            return PrecheckResponse.from_dict(response.data)
        except Exception as e:
            self.logger.error(f"Precheck request failed: {str(e)}")
            raise PrecheckError(f"Precheck request failed: {str(e)}")

    async def check_tool_call(
        self,
        tool: str,
        args: Dict[str, Any],
        scope: str,
        user_id: str,
        corr_id: Optional[str] = None,
    ) -> PrecheckResponse:
        """
        Check a tool call for governance compliance.

        Args:
            tool: Tool name
            args: Tool arguments
            scope: Scope of the call
            user_id: User ID
            corr_id: Correlation ID

        Returns:
            PrecheckResponse with decision and reasons
        """
        request = PrecheckRequest(
            tool=tool,
            scope=scope,
            raw_text=f"Tool call: {tool}",
            payload={"args": args},
            tags=["tool_call"],
            corr_id=corr_id,
            user_id=user_id,
        )
        return await self.check_request(request)

    async def check_chat_message(
        self,
        messages: List[Dict[str, Any]],
        provider: str,
        user_id: str,
        corr_id: Optional[str] = None,
    ) -> PrecheckResponse:
        """
        Check a chat message for governance compliance.

        Args:
            messages: List of chat messages
            provider: AI provider
            user_id: User ID
            corr_id: Correlation ID

        Returns:
            PrecheckResponse with decision and reasons
        """
        # Extract the last user message
        last_message = None
        for message in reversed(messages):
            if message.get("role") == "user":
                last_message = message
                break

        if not last_message:
            raise PrecheckError("No user message found in chat")

        request = PrecheckRequest(
            tool="model.chat",
            scope="net.external",
            raw_text=last_message.get("content", ""),
            payload={"messages": messages, "provider": provider},
            tags=["chat", "model"],
            corr_id=corr_id,
            user_id=user_id,
        )
        return await self.check_request(request)

    async def check_file_upload(
        self,
        filename: str,
        file_size: int,
        mime_type: str,
        user_id: str,
        corr_id: Optional[str] = None,
    ) -> PrecheckResponse:
        """
        Check a file upload for governance compliance.

        Args:
            filename: Name of the file
            file_size: Size of the file in bytes
            mime_type: MIME type of the file
            user_id: User ID
            corr_id: Correlation ID

        Returns:
            PrecheckResponse with decision and reasons
        """
        request = PrecheckRequest(
            tool="file.upload",
            scope="net.external",
            raw_text=f"File upload: {filename}",
            payload={
                "filename": filename,
                "fileSize": file_size,
                "mimeType": mime_type,
            },
            tags=["file", "upload"],
            corr_id=corr_id,
            user_id=user_id,
        )
        return await self.check_request(request)
