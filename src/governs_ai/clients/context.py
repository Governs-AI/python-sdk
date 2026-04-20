# SPDX-License-Identifier: MIT
# Copyright (c) 2026 GovernsAI. All rights reserved.
"""
Context client for memory and retrieval operations.
"""

from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

from ..exceptions import GovernsAIError
from ..models.context import (
    ConversationItem,
    ConversationSummary,
    ContextLLMResponse,
    MemorySearchResponse,
    ResolvedUser,
    ResolvedUserDetails,
    SaveContextInput,
    SaveContextResponse,
)
from ..models.precheck import PrecheckResponse
from ..utils.http import HTTPClient
from ..utils.logging import GovernsAILogger


class ContextClient:
    """Client for context memory and retrieval APIs."""

    def __init__(self, http_client: HTTPClient, logger: GovernsAILogger):
        self.http_client = http_client
        self.logger = logger

    async def save_context_explicit(
        self,
        input_data: Union[SaveContextInput, Dict[str, Any]],
    ) -> SaveContextResponse:
        """Save context explicitly without server-side precheck inference."""
        payload = self._to_save_context_payload(input_data)
        try:
            response = await self.http_client.post("/api/v1/context", data=payload)
            return SaveContextResponse.from_dict(response.data)
        except Exception as exc:
            self.logger.error(f"Save context failed: {exc}")
            raise GovernsAIError(f"Save context failed: {exc}")

    async def store_context(
        self,
        input_data: Union[SaveContextInput, Dict[str, Any]],
    ) -> SaveContextResponse:
        """Store context (server may apply precheck logic)."""
        return await self.save_context_explicit(input_data)

    async def search_context_llm(
        self, input_data: Dict[str, Any]
    ) -> ContextLLMResponse:
        """Search context using LLM-optimized compressed response format."""
        try:
            response = await self.http_client.post(
                "/api/v1/context/search/llm", data=input_data
            )
            return ContextLLMResponse.from_dict(response.data)
        except Exception as exc:
            self.logger.error(f"Context search failed: {exc}")
            raise GovernsAIError(f"Context search failed: {exc}")

    async def search_cross_agent(
        self,
        query: str,
        limit: Optional[int] = None,
        threshold: Optional[float] = None,
        scope: Optional[str] = None,
    ) -> ContextLLMResponse:
        """Search across agents using LLM-optimized response format."""
        payload: Dict[str, Any] = {"query": query}
        if limit is not None:
            payload["limit"] = limit
        if threshold is not None:
            payload["threshold"] = threshold
        if scope:
            payload["scope"] = scope
        return await self.search_context_llm(payload)

    async def get_or_create_conversation(
        self, input_data: Dict[str, Any]
    ) -> ConversationSummary:
        """Get or create a conversation for a given agent."""
        try:
            response = await self.http_client.post(
                "/api/v1/context/conversation", data=input_data
            )
            return ConversationSummary.from_dict(response.data)
        except Exception as exc:
            self.logger.error(f"Get or create conversation failed: {exc}")
            raise GovernsAIError(f"Get or create conversation failed: {exc}")

    async def get_conversation_context(
        self,
        conversation_id: str,
        agent_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[ConversationItem]:
        """Get context entries for a conversation."""
        params: Dict[str, Any] = {}
        if agent_id:
            params["agentId"] = agent_id
        if limit is not None:
            params["limit"] = limit
        suffix = f"?{urlencode(params)}" if params else ""

        try:
            endpoint = f"/api/v1/context/conversation/{conversation_id}{suffix}"
            response = await self.http_client.get(endpoint)
            contexts = (
                response.data.get("contexts", [])
                if isinstance(response.data, dict)
                else []
            )
            return [
                ConversationItem.from_dict(item)
                for item in contexts
                if isinstance(item, dict)
            ]
        except Exception as exc:
            self.logger.error(f"Get conversation context failed: {exc}")
            raise GovernsAIError(f"Get conversation context failed: {exc}")

    async def get_recent_context(
        self,
        user_id: Optional[str] = None,
        limit: int = 20,
        scope: Optional[str] = None,
    ) -> ContextLLMResponse:
        """Retrieve recent context using the LLM response shape."""
        payload: Dict[str, Any] = {
            "query": "recent context",
            "limit": limit,
        }
        if user_id:
            payload["userId"] = user_id
        if scope:
            payload["scope"] = scope
        return await self.search_context_llm(payload)

    async def maybe_save_from_precheck(
        self,
        precheck: Union[PrecheckResponse, Dict[str, Any]],
        agent_id: str,
        fallback_content: Optional[str] = None,
        agent_name: Optional[str] = None,
        conversation_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        scope: Optional[str] = None,
        visibility: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Best-effort helper to persist context from precheck suggestions."""
        payload = (
            precheck.to_dict() if isinstance(precheck, PrecheckResponse) else precheck
        )
        if not isinstance(payload, dict):
            return {"saved": False}

        intent = payload.get("intent") or {}
        has_intent = isinstance(intent, dict) and intent.get("save") is True

        suggested_actions = payload.get("suggestedActions") or []
        save_action: Optional[Dict[str, Any]] = None
        if isinstance(suggested_actions, list):
            for action in suggested_actions:
                if isinstance(action, dict) and action.get("type") == "context.save":
                    save_action = action
                    break

        if not has_intent and save_action is None:
            return {"saved": False}

        content = None
        if isinstance(save_action, dict):
            content = save_action.get("content")
        if not content:
            content = fallback_content
        if not content:
            content = self._extract_content_from_precheck(payload)

        if not content:
            return {"saved": False}

        combined_metadata: Dict[str, Any] = {}
        if isinstance(save_action, dict) and isinstance(
            save_action.get("metadata"), dict
        ):
            combined_metadata.update(save_action["metadata"])
        if isinstance(metadata, dict):
            combined_metadata.update(metadata)

        save_input = SaveContextInput(
            content=content,
            content_type="user_message",
            agent_id=agent_id,
            agent_name=agent_name,
            conversation_id=conversation_id,
            correlation_id=correlation_id,
            metadata=combined_metadata or None,
            scope=scope,
            visibility=visibility,
        )

        try:
            saved = await self.store_context(save_input)
            return {"saved": True, "contextId": saved.context_id}
        except Exception as exc:
            self.logger.error(f"maybe_save_from_precheck failed: {exc}")
            return {"saved": False}

    async def store_memory(self, params: Dict[str, Any]) -> SaveContextResponse:
        """Store memory for an external user identity."""
        payload: Dict[str, Any] = {
            "content": params.get("content"),
            "contentType": params.get("contentType", "user_message"),
            "agentId": params.get("agentId", "external-app"),
            "agentName": params.get("agentName"),
            "externalUserId": params.get("externalUserId"),
            "externalSource": params.get("externalSource", "default"),
            "metadata": params.get("metadata"),
            "scope": params.get("scope", "user"),
            "visibility": params.get("visibility", "private"),
            "email": params.get("email"),
            "name": params.get("name"),
        }
        payload = {key: value for key, value in payload.items() if value is not None}

        try:
            response = await self.http_client.post("/api/v1/context", data=payload)
            return SaveContextResponse.from_dict(response.data)
        except Exception as exc:
            self.logger.error(f"Store memory failed: {exc}")
            raise GovernsAIError(f"Store memory failed: {exc}")

    async def search_memory(self, params: Dict[str, Any]) -> MemorySearchResponse:
        """Search memory for an external user identity."""
        payload: Dict[str, Any] = {
            "query": params.get("query"),
            "externalUserId": params.get("externalUserId"),
            "externalSource": params.get("externalSource", "default"),
            "limit": params.get("limit", 10),
            "threshold": params.get("threshold", 0.5),
            "scope": params.get("scope", "user"),
            "agentId": params.get("agentId"),
            "contentTypes": params.get("contentTypes"),
        }
        payload = {key: value for key, value in payload.items() if value is not None}

        try:
            response = await self.http_client.post(
                "/api/v1/context/search", data=payload
            )
            return MemorySearchResponse.from_dict(response.data)
        except Exception as exc:
            self.logger.error(f"Search memory failed: {exc}")
            raise GovernsAIError(f"Search memory failed: {exc}")

    async def resolve_user(self, params: Dict[str, Any]) -> ResolvedUser:
        """Resolve an external user identifier to a GovernsAI internal user."""
        payload: Dict[str, Any] = {
            "externalUserId": params.get("externalUserId"),
            "externalSource": params.get("externalSource", "default"),
            "email": params.get("email"),
            "name": params.get("name"),
        }
        payload = {key: value for key, value in payload.items() if value is not None}

        try:
            response = await self.http_client.post(
                "/api/v1/users/resolve", data=payload
            )
            return ResolvedUser.from_dict(response.data)
        except Exception as exc:
            self.logger.error(f"Resolve user failed: {exc}")
            raise GovernsAIError(f"Resolve user failed: {exc}")

    async def get_user_by_external_id(
        self,
        external_user_id: str,
        external_source: str = "default",
    ) -> Optional[ResolvedUserDetails]:
        """Look up an external user without auto-creating a user."""
        query = urlencode(
            {"externalUserId": external_user_id, "externalSource": external_source}
        )

        try:
            response = await self.http_client.get(f"/api/v1/users/resolve?{query}")
            user_payload = (
                response.data.get("user") if isinstance(response.data, dict) else None
            )
            if not isinstance(user_payload, dict):
                return None
            return ResolvedUserDetails.from_dict(user_payload)
        except Exception as exc:
            # API returns 404 when no user exists for external id.
            if getattr(exc, "status_code", None) == 404:
                return None
            self.logger.error(f"Get user by external id failed: {exc}")
            raise GovernsAIError(f"Get user by external id failed: {exc}")

    def _to_save_context_payload(
        self, input_data: Union[SaveContextInput, Dict[str, Any]]
    ) -> Dict[str, Any]:
        if isinstance(input_data, SaveContextInput):
            return input_data.to_dict()

        payload = dict(input_data)
        if "content_type" in payload and "contentType" not in payload:
            payload["contentType"] = payload.pop("content_type")
        if "agent_id" in payload and "agentId" not in payload:
            payload["agentId"] = payload.pop("agent_id")
        if "agent_name" in payload and "agentName" not in payload:
            payload["agentName"] = payload.pop("agent_name")
        if "conversation_id" in payload and "conversationId" not in payload:
            payload["conversationId"] = payload.pop("conversation_id")
        if "parent_id" in payload and "parentId" not in payload:
            payload["parentId"] = payload.pop("parent_id")
        if "correlation_id" in payload and "correlationId" not in payload:
            payload["correlationId"] = payload.pop("correlation_id")
        if "expires_at" in payload and "expiresAt" not in payload:
            payload["expiresAt"] = payload.pop("expires_at")
        return payload

    def _extract_content_from_precheck(self, payload: Dict[str, Any]) -> Optional[str]:
        content = payload.get("content")
        if not isinstance(content, dict):
            return None

        messages = content.get("messages")
        if not isinstance(messages, list):
            return None

        fragments: List[str] = []
        for message in messages:
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                fragments.append(message["content"])

        if not fragments:
            return None
        return "\n".join(fragments)
