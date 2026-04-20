"""Unit tests for MemoryClient (context_memory)."""

import json
import pytest
import respx
import httpx

from governs_ai import GovernsAIClient, MemoryResult

BASE = "https://api.governs.ai"


@pytest.fixture
def client():
    return GovernsAIClient(api_key="test-key", org_id="org-test")


@respx.mock
def test_store_sends_correct_payload(client):
    route = respx.post(f"{BASE}/api/v1/context/store").mock(
        return_value=httpx.Response(200, json={"id": "mem-123"})
    )
    client.memory.store(
        content="Customer prefers weekly summaries",
        metadata={"source": "chat"},
    )
    body = json.loads(route.calls[0].request.content)
    assert body["content"] == "Customer prefers weekly summaries"
    assert body["metadata"]["source"] == "chat"


@respx.mock
def test_search_returns_memory_results(client):
    respx.post(f"{BASE}/api/v1/context/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": "mem-1",
                        "content": "Weekly summaries preferred",
                        "score": 0.95,
                    },
                    {
                        "id": "mem-2",
                        "content": "Prefers email over Slack",
                        "score": 0.80,
                    },
                ]
            },
        )
    )
    results = client.memory.search(query="communication preferences", top_k=5)
    assert len(results) == 2
    assert all(isinstance(r, MemoryResult) for r in results)
    assert results[0].memory_id == "mem-1"
    assert results[0].score == 0.95


@respx.mock
def test_search_empty_returns_empty_list(client):
    respx.post(f"{BASE}/api/v1/context/search").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    results = client.memory.search(query="nothing here")
    assert results == []


@respx.mock
def test_delete_sends_correct_id(client):
    route = respx.post(f"{BASE}/api/v1/context/delete").mock(
        return_value=httpx.Response(200, json={})
    )
    client.memory.delete("mem-abc123")
    body = json.loads(route.calls[0].request.content)
    assert body["memory_id"] == "mem-abc123"


@respx.mock
async def test_async_store_sends_correct_payload(client):
    route = respx.post(f"{BASE}/api/v1/context/store").mock(
        return_value=httpx.Response(200, json={"id": "mem-456"})
    )
    await client.memory.async_store(content="async memory entry")
    body = json.loads(route.calls[0].request.content)
    assert body["content"] == "async memory entry"
