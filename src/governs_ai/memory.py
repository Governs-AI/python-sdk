"""Context memory client — store, search, and delete semantic memory entries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx


@dataclass
class MemoryResult:
    """A single result from a context memory search.

    Example::

        hits = client.memory.search(query="communication prefs", top_k=5)
        for hit in hits:
            print(hit.content, hit.score)
    """

    memory_id: str
    content: str
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryResult":
        return cls(
            memory_id=data.get("id", data.get("memory_id", "")),
            content=data.get("content", ""),
            score=data.get("score", 0.0),
            metadata=data.get("metadata", {}),
        )


class MemoryClient:
    """Client for GovernsAI context memory (RAG) operations.

    Access via ``GovernsAIClient.memory``.

    Example::

        client = GovernsAIClient(api_key="...", org_id="org-123")
        client.memory.store(content="User prefers weekly summaries")
        hits = client.memory.search(query="communication preferences", top_k=5)
    """

    def __init__(
        self,
        base_url: str,
        headers: Dict[str, str],
        timeout: float,
        org_id: Optional[str],
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = headers
        self._timeout = timeout
        self._org_id = org_id

    def store(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Store a memory entry and return the created record.

        Example::

            result = client.memory.store(
                content="Customer prefers weekly summaries",
                metadata={"source": "chat"},
            )
        """
        payload: Dict[str, Any] = {
            "content": content,
            "content_type": "user_message",
            "metadata": metadata or {},
        }
        if user_id:
            payload["user_id"] = user_id
        if agent_id:
            payload["agent_id"] = agent_id
        with httpx.Client(timeout=self._timeout) as http:
            resp = http.post(
                f"{self._base_url}/api/v1/context/store",
                json=payload,
                headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def async_store(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Async variant of :meth:`store`."""
        payload: Dict[str, Any] = {
            "content": content,
            "content_type": "user_message",
            "metadata": metadata or {},
        }
        if user_id:
            payload["user_id"] = user_id
        if agent_id:
            payload["agent_id"] = agent_id
        async with httpx.AsyncClient(timeout=self._timeout) as http:
            resp = await http.post(
                f"{self._base_url}/api/v1/context/store",
                json=payload,
                headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json()

    def search(
        self,
        query: str,
        top_k: int = 5,
        user_id: Optional[str] = None,
        threshold: Optional[float] = None,
    ) -> List[MemoryResult]:
        """Search context memory by semantic similarity.

        Example::

            hits = client.memory.search(query="billing questions", top_k=3)
        """
        payload: Dict[str, Any] = {"query": query, "limit": top_k}
        if user_id:
            payload["externalUserId"] = user_id
        if threshold is not None:
            payload["threshold"] = threshold
        with httpx.Client(timeout=self._timeout) as http:
            resp = http.post(
                f"{self._base_url}/api/v1/context/search",
                json=payload,
                headers=self._headers,
            )
            resp.raise_for_status()
        data = resp.json()
        items = data if isinstance(data, list) else data.get("results", [])
        return [MemoryResult.from_dict(item) for item in items]

    async def async_search(
        self,
        query: str,
        top_k: int = 5,
        user_id: Optional[str] = None,
        threshold: Optional[float] = None,
    ) -> List[MemoryResult]:
        """Async variant of :meth:`search`."""
        payload: Dict[str, Any] = {"query": query, "limit": top_k}
        if user_id:
            payload["externalUserId"] = user_id
        if threshold is not None:
            payload["threshold"] = threshold
        async with httpx.AsyncClient(timeout=self._timeout) as http:
            resp = await http.post(
                f"{self._base_url}/api/v1/context/search",
                json=payload,
                headers=self._headers,
            )
            resp.raise_for_status()
        data = resp.json()
        items = data if isinstance(data, list) else data.get("results", [])
        return [MemoryResult.from_dict(item) for item in items]

    def delete(self, memory_id: str) -> None:
        """Delete a memory entry by ID.

        Example::

            client.memory.delete(memory_id="mem-abc123")
        """
        with httpx.Client(timeout=self._timeout) as http:
            resp = http.post(
                f"{self._base_url}/api/v1/context/delete",
                json={"memory_id": memory_id},
                headers=self._headers,
            )
            resp.raise_for_status()

    async def async_delete(self, memory_id: str) -> None:
        """Async variant of :meth:`delete`."""
        async with httpx.AsyncClient(timeout=self._timeout) as http:
            resp = await http.post(
                f"{self._base_url}/api/v1/context/delete",
                json={"memory_id": memory_id},
                headers=self._headers,
            )
            resp.raise_for_status()
