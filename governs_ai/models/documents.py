# SPDX-License-Identifier: MIT
# Copyright (c) 2024 GovernsAI. All rights reserved.
"""
Document data models for the GovernsAI Python SDK.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DocumentUploadResponse:
    """Response payload for document uploads."""

    success: bool
    document_id: str
    status: str
    chunk_count: int
    file_hash: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentUploadResponse":
        return cls(
            success=bool(data.get("success", False)),
            document_id=data.get("documentId", data.get("document_id", "")),
            status=data.get("status", "processing"),
            chunk_count=int(data.get("chunkCount", data.get("chunk_count", 0))),
            file_hash=data.get("fileHash", data.get("file_hash", "")),
        )


@dataclass
class DocumentChunk:
    """Single chunk generated from OCR/indexing."""

    id: str
    chunk_index: int
    content: str
    metadata: Dict[str, Any]
    created_at: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentChunk":
        return cls(
            id=data.get("id", ""),
            chunk_index=int(data.get("chunkIndex", data.get("chunk_index", 0))),
            content=data.get("content", ""),
            metadata=data.get("metadata", {}),
            created_at=data.get("createdAt", data.get("created_at", "")),
        )


@dataclass
class DocumentRecord:
    """Base document record returned by list/detail endpoints."""

    id: str
    user_id: str
    org_id: str
    filename: str
    content_type: str
    file_size: int
    file_hash: str
    status: str
    chunk_count: int
    scope: str
    visibility: str
    is_archived: bool
    created_at: str
    updated_at: str
    external_user_id: Optional[str] = None
    external_source: Optional[str] = None
    storage_url: Optional[str] = None
    error_message: Optional[str] = None
    expires_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentRecord":
        return cls(
            id=data.get("id", ""),
            user_id=data.get("userId", data.get("user_id", "")),
            org_id=data.get("orgId", data.get("org_id", "")),
            external_user_id=data.get("externalUserId", data.get("external_user_id")),
            external_source=data.get("externalSource", data.get("external_source")),
            filename=data.get("filename", ""),
            content_type=data.get("contentType", data.get("content_type", "")),
            file_size=int(data.get("fileSize", data.get("file_size", 0))),
            file_hash=data.get("fileHash", data.get("file_hash", "")),
            storage_url=data.get("storageUrl", data.get("storage_url")),
            status=data.get("status", "processing"),
            error_message=data.get("errorMessage", data.get("error_message")),
            chunk_count=int(data.get("chunkCount", data.get("chunk_count", 0))),
            scope=data.get("scope", "user"),
            visibility=data.get("visibility", "private"),
            is_archived=bool(data.get("isArchived", data.get("is_archived", False))),
            created_at=data.get("createdAt", data.get("created_at", "")),
            updated_at=data.get("updatedAt", data.get("updated_at", "")),
            expires_at=data.get("expiresAt", data.get("expires_at")),
        )


@dataclass
class DocumentDetails(DocumentRecord):
    """Expanded document details including content/chunks."""

    content: Optional[str] = None
    chunks: List[DocumentChunk] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentDetails":
        base = DocumentRecord.from_dict(data)
        raw_chunks = data.get("chunks", [])
        return cls(
            **base.__dict__,
            content=data.get("content"),
            chunks=[DocumentChunk.from_dict(chunk) for chunk in raw_chunks if isinstance(chunk, dict)],
        )


@dataclass
class DocumentListPagination:
    """Pagination metadata for document list responses."""

    total: int
    limit: int
    offset: int
    has_more: bool
    total_pages: int
    current_page: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentListPagination":
        return cls(
            total=int(data.get("total", 0)),
            limit=int(data.get("limit", 0)),
            offset=int(data.get("offset", 0)),
            has_more=bool(data.get("hasMore", data.get("has_more", False))),
            total_pages=int(data.get("totalPages", data.get("total_pages", 0))),
            current_page=int(data.get("currentPage", data.get("current_page", 0))),
        )


@dataclass
class DocumentListResponse:
    """List documents response payload."""

    success: bool
    documents: List[DocumentRecord]
    pagination: DocumentListPagination

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentListResponse":
        documents = [
            DocumentRecord.from_dict(item)
            for item in data.get("documents", [])
            if isinstance(item, dict)
        ]
        pagination_data = data.get("pagination") if isinstance(data.get("pagination"), dict) else {}
        return cls(
            success=bool(data.get("success", False)),
            documents=documents,
            pagination=DocumentListPagination.from_dict(pagination_data),
        )


@dataclass
class DocumentSearchSource:
    """Document metadata included with each search hit."""

    filename: str
    content_type: str
    user_id: str
    created_at: str
    external_user_id: Optional[str] = None
    external_source: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentSearchSource":
        return cls(
            filename=data.get("filename", ""),
            content_type=data.get("contentType", data.get("content_type", "")),
            user_id=data.get("userId", data.get("user_id", "")),
            created_at=data.get("createdAt", data.get("created_at", "")),
            external_user_id=data.get("externalUserId", data.get("external_user_id")),
            external_source=data.get("externalSource", data.get("external_source")),
        )


@dataclass
class DocumentSearchResult:
    """Single vector-search result across document chunks."""

    document_id: str
    chunk_id: str
    chunk_index: int
    content: str
    similarity: float
    metadata: Dict[str, Any]
    document: DocumentSearchSource

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentSearchResult":
        document_payload = data.get("document") if isinstance(data.get("document"), dict) else {}
        return cls(
            document_id=data.get("documentId", data.get("document_id", "")),
            chunk_id=data.get("chunkId", data.get("chunk_id", "")),
            chunk_index=int(data.get("chunkIndex", data.get("chunk_index", 0))),
            content=data.get("content", ""),
            similarity=float(data.get("similarity", 0.0)),
            metadata=data.get("metadata", {}),
            document=DocumentSearchSource.from_dict(document_payload),
        )


@dataclass
class DocumentSearchResponse:
    """Vector-search response payload for documents."""

    success: bool
    results: List[DocumentSearchResult]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentSearchResponse":
        return cls(
            success=bool(data.get("success", False)),
            results=[
                DocumentSearchResult.from_dict(item)
                for item in data.get("results", [])
                if isinstance(item, dict)
            ],
        )
