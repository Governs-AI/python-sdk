# SPDX-License-Identifier: MIT
# Copyright (c) 2026 GovernsAI. All rights reserved.
"""
Context memory data models for the GovernsAI Python SDK.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SaveContextInput:
    """Input payload for creating context records."""

    content: str
    content_type: str
    agent_id: str
    agent_name: Optional[str] = None
    conversation_id: Optional[str] = None
    parent_id: Optional[str] = None
    correlation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    scope: Optional[str] = None
    visibility: Optional[str] = None
    expires_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "content": self.content,
            "contentType": self.content_type,
            "agentId": self.agent_id,
            "agentName": self.agent_name,
            "conversationId": self.conversation_id,
            "parentId": self.parent_id,
            "correlationId": self.correlation_id,
            "metadata": self.metadata,
            "scope": self.scope,
            "visibility": self.visibility,
            "expiresAt": self.expires_at,
        }
        return {key: value for key, value in payload.items() if value is not None}


@dataclass
class SaveContextResponse:
    """Response payload for context writes."""

    context_id: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SaveContextResponse":
        return cls(context_id=data.get("contextId", data.get("context_id", "")))


@dataclass
class ContextLLMResponse:
    """LLM-optimized context search response."""

    success: bool
    context: str
    memory_count: int
    high_confidence: int
    medium_confidence: int
    low_confidence: int
    token_estimate: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextLLMResponse":
        return cls(
            success=bool(data.get("success", False)),
            context=data.get("context", ""),
            memory_count=int(data.get("memoryCount", data.get("memory_count", 0))),
            high_confidence=int(
                data.get("highConfidence", data.get("high_confidence", 0))
            ),
            medium_confidence=int(
                data.get("mediumConfidence", data.get("medium_confidence", 0))
            ),
            low_confidence=int(
                data.get("lowConfidence", data.get("low_confidence", 0))
            ),
            token_estimate=int(
                data.get("tokenEstimate", data.get("token_estimate", 0))
            ),
        )


@dataclass
class ConversationSummary:
    """Conversation metadata summary."""

    id: str
    message_count: int
    token_count: int
    scope: str
    title: Optional[str] = None
    last_message_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationSummary":
        return cls(
            id=data.get("id", ""),
            title=data.get("title"),
            message_count=int(data.get("messageCount", data.get("message_count", 0))),
            token_count=int(data.get("tokenCount", data.get("token_count", 0))),
            last_message_at=data.get("lastMessageAt", data.get("last_message_at")),
            scope=data.get("scope", "user"),
        )


@dataclass
class ConversationItem:
    """Single context item in a conversation."""

    id: str
    content: str
    content_type: str
    created_at: str
    agent_id: Optional[str] = None
    parent_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationItem":
        return cls(
            id=data.get("id", ""),
            content=data.get("content", ""),
            content_type=data.get("contentType", data.get("content_type", "")),
            created_at=data.get("createdAt", data.get("created_at", "")),
            agent_id=data.get("agentId", data.get("agent_id")),
            parent_id=data.get("parentId", data.get("parent_id")),
            metadata=data.get("metadata"),
        )


@dataclass
class MemoryRecord:
    """External memory search result item."""

    id: str
    content: str
    content_type: str
    created_at: str
    summary: Optional[str] = None
    agent_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    similarity: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryRecord":
        similarity = data.get("similarity")
        return cls(
            id=data.get("id", ""),
            content=data.get("content", ""),
            content_type=data.get("contentType", data.get("content_type", "")),
            created_at=data.get("createdAt", data.get("created_at", "")),
            summary=data.get("summary"),
            agent_id=data.get("agentId", data.get("agent_id")),
            metadata=data.get("metadata"),
            similarity=float(similarity) if similarity is not None else None,
        )


@dataclass
class MemorySearchMetadata:
    """Metadata included with memory search responses."""

    high_confidence: int = 0
    medium_confidence: int = 0
    low_confidence: int = 0
    token_estimate: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemorySearchMetadata":
        return cls(
            high_confidence=int(
                data.get("highConfidence", data.get("high_confidence", 0))
            ),
            medium_confidence=int(
                data.get("mediumConfidence", data.get("medium_confidence", 0))
            ),
            low_confidence=int(
                data.get("lowConfidence", data.get("low_confidence", 0))
            ),
            token_estimate=int(
                data.get("tokenEstimate", data.get("token_estimate", 0))
            ),
        )


@dataclass
class MemorySearchResponse:
    """Response payload for external memory search."""

    success: bool
    memories: List[MemoryRecord] = field(default_factory=list)
    count: int = 0
    metadata: Optional[MemorySearchMetadata] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemorySearchResponse":
        raw_memories = data.get("memories", [])
        raw_metadata = data.get("metadata")
        return cls(
            success=bool(data.get("success", False)),
            memories=[
                MemoryRecord.from_dict(item)
                for item in raw_memories
                if isinstance(item, dict)
            ],
            count=int(data.get("count", len(raw_memories))),
            metadata=(
                MemorySearchMetadata.from_dict(raw_metadata)
                if isinstance(raw_metadata, dict)
                else None
            ),
        )


@dataclass
class ResolvedUserDetails:
    """User details returned by resolve endpoints."""

    id: str
    email: str
    name: Optional[str]
    external_id: Optional[str]
    external_source: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResolvedUserDetails":
        return cls(
            id=data.get("id", ""),
            email=data.get("email", ""),
            name=data.get("name"),
            external_id=data.get("externalId", data.get("external_id")),
            external_source=data.get("externalSource", data.get("external_source")),
        )


@dataclass
class ResolvedUser:
    """Resolved user wrapper for external user mapping."""

    internal_user_id: str
    created: bool
    user: ResolvedUserDetails

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResolvedUser":
        user_payload: Dict[str, Any]
        if isinstance(data.get("user"), dict):
            user_payload = dict(data["user"])
        else:
            user_payload = {}
        return cls(
            internal_user_id=data.get(
                "internalUserId", data.get("internal_user_id", "")
            ),
            created=bool(data.get("created", False)),
            user=ResolvedUserDetails.from_dict(user_payload),
        )
