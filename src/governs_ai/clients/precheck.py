# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2026 GovernsAI. All rights reserved.
"""
Precheck client for request validation and governance compliance.
"""

import asyncio
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
            enriched_request = await self._enrich_request(request)
            response = await self.http_client.post(
                "/api/v1/precheck",
                data=enriched_request.to_dict(),
            )
            return PrecheckResponse.from_dict(response.data)
        except Exception as e:
            self.logger.error(f"Precheck request failed: {str(e)}")
            raise PrecheckError(f"Precheck request failed: {str(e)}")

    async def _enrich_request(self, request: PrecheckRequest) -> PrecheckRequest:
        """Enrich request with platform policy/tool/budget context when missing."""
        needs_policy = request.policy_config is None
        needs_tool = request.tool_config is None and bool(request.tool)
        needs_budget = request.budget_context is None

        if not (needs_policy or needs_tool or needs_budget):
            return request

        enriched: Dict[str, Any] = request.to_dict()
        tasks = []

        if needs_policy:
            tasks.append(self._attach_policy_config(enriched))
        if needs_tool:
            tasks.append(self._attach_tool_config(enriched, request.tool))
        if needs_budget:
            tasks.append(self._attach_budget_context(enriched))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        return PrecheckRequest.from_dict(enriched)

    async def _attach_policy_config(self, enriched: Dict[str, Any]) -> None:
        """Attach transformed policy config from platform API."""
        try:
            response = await self.http_client.get("/api/v1/policies")
            raw_policy = response.data
            if isinstance(raw_policy, dict) and isinstance(
                raw_policy.get("policies"), list
            ):
                raw_policy = (raw_policy.get("policies") or [None])[0]
            transformed = self._transform_policy_config(raw_policy)
            if transformed:
                enriched["policy_config"] = transformed
        except Exception:
            # Best-effort enrichment; precheck request should still proceed.
            pass

    async def _attach_tool_config(self, enriched: Dict[str, Any], tool: str) -> None:
        """Attach tool metadata when available."""
        try:
            response = await self.http_client.get(f"/api/v1/tools/{tool}/metadata")
            metadata = (
                response.data.get("metadata")
                if isinstance(response.data, dict)
                else None
            )
            if isinstance(metadata, dict):
                enriched["tool_config"] = metadata
        except Exception:
            pass

    async def _attach_budget_context(self, enriched: Dict[str, Any]) -> None:
        """Attach current budget context when available."""
        try:
            response = await self.http_client.get("/api/v1/budget/context")
            if isinstance(response.data, dict):
                enriched["budget_context"] = response.data
        except Exception:
            pass

    def _transform_policy_config(self, raw_policy: Any) -> Optional[Dict[str, Any]]:
        """Transform platform policy shape to precheck request schema."""
        if not isinstance(raw_policy, dict):
            return None

        policy: Dict[str, Any] = {}
        policy["version"] = raw_policy.get("version", "v1")

        if raw_policy.get("model"):
            policy["model"] = raw_policy.get("model")

        defaults = raw_policy.get("defaults")
        if isinstance(defaults, dict):
            policy["defaults"] = {
                "ingress": defaults.get("ingress", {}),
                "egress": defaults.get("egress", {}),
            }

        tool_access = raw_policy.get("tool_access", raw_policy.get("toolAccess"))
        if isinstance(tool_access, dict):
            policy["tool_access"] = tool_access

        deny_tools = raw_policy.get("deny_tools", raw_policy.get("denyTools"))
        if isinstance(deny_tools, list):
            policy["deny_tools"] = deny_tools

        allow_tools = raw_policy.get("allow_tools", raw_policy.get("allowTools"))
        if isinstance(allow_tools, list):
            policy["allow_tools"] = allow_tools

        network_scopes = raw_policy.get(
            "network_scopes", raw_policy.get("networkScopes")
        )
        if isinstance(network_scopes, list):
            policy["network_scopes"] = network_scopes

        network_tools = raw_policy.get("network_tools", raw_policy.get("networkTools"))
        if isinstance(network_tools, list):
            policy["network_tools"] = network_tools

        on_error = raw_policy.get("on_error", raw_policy.get("onError"))
        if isinstance(on_error, str):
            policy["on_error"] = on_error

        return policy

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
