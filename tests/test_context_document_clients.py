"""
Tests for ContextClient and DocumentClient.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from governs_ai.clients.context import ContextClient
from governs_ai.clients.documents import DocumentClient
from governs_ai.models.context import SaveContextInput


@pytest.fixture
def mock_http_client():
    client = AsyncMock()
    client.post = AsyncMock()
    client.get = AsyncMock()
    client.delete = AsyncMock()
    client.post_form_data = AsyncMock()
    return client


@pytest.fixture
def logger():
    return MagicMock()


@pytest.mark.asyncio
async def test_context_save_context_explicit(mock_http_client, logger):
    mock_response = MagicMock()
    mock_response.data = {"contextId": "ctx-123"}
    mock_http_client.post.return_value = mock_response

    context_client = ContextClient(mock_http_client, logger)
    result = await context_client.save_context_explicit(
        SaveContextInput(
            content="remember this",
            content_type="user_message",
            agent_id="agent-1",
        )
    )

    assert result.context_id == "ctx-123"
    mock_http_client.post.assert_called_once_with(
        "/api/v1/context",
        data={
            "content": "remember this",
            "contentType": "user_message",
            "agentId": "agent-1",
        },
    )


@pytest.mark.asyncio
async def test_context_search_memory(mock_http_client, logger):
    mock_response = MagicMock()
    mock_response.data = {
        "success": True,
        "count": 1,
        "memories": [
            {
                "id": "mem-1",
                "content": "User likes blue widgets",
                "contentType": "user_message",
                "createdAt": "2026-02-28T00:00:00Z",
            }
        ],
    }
    mock_http_client.post.return_value = mock_response

    context_client = ContextClient(mock_http_client, logger)
    result = await context_client.search_memory(
        {
            "query": "preferences",
            "externalUserId": "user-1",
            "externalSource": "shopify",
        }
    )

    assert result.success is True
    assert result.count == 1
    assert result.memories[0].id == "mem-1"
    mock_http_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_document_upload_uses_multipart(mock_http_client, logger):
    mock_response = MagicMock()
    mock_response.data = {
        "success": True,
        "documentId": "doc-1",
        "status": "processing",
        "chunkCount": 0,
        "fileHash": "abc123",
    }
    mock_http_client.post_form_data.return_value = mock_response

    document_client = DocumentClient(mock_http_client, logger)
    result = await document_client.upload_document(
        file=b"hello world",
        filename="hello.txt",
        content_type="text/plain",
    )

    assert result.document_id == "doc-1"
    mock_http_client.post_form_data.assert_called_once()
    call_args = mock_http_client.post_form_data.call_args
    assert call_args.args[0] == "/api/v1/documents"


@pytest.mark.asyncio
async def test_document_search(mock_http_client, logger):
    mock_response = MagicMock()
    mock_response.data = {
        "success": True,
        "results": [
            {
                "documentId": "doc-1",
                "chunkId": "chunk-1",
                "chunkIndex": 0,
                "content": "Matching content",
                "similarity": 0.92,
                "metadata": {},
                "document": {
                    "filename": "policy.pdf",
                    "contentType": "application/pdf",
                    "userId": "user-1",
                    "createdAt": "2026-02-28T00:00:00Z",
                },
            }
        ],
    }
    mock_http_client.post.return_value = mock_response

    document_client = DocumentClient(mock_http_client, logger)
    result = await document_client.search_documents({"query": "policy", "limit": 5})

    assert result.success is True
    assert len(result.results) == 1
    assert result.results[0].document_id == "doc-1"
