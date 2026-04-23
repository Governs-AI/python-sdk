# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2026 GovernsAI. All rights reserved.
"""
Document client for OCR + chunking + vector search operations.
"""

import json
import os
from typing import Any, Dict, Optional, Tuple, Union

import aiohttp

from ..exceptions import GovernsAIError
from ..models.documents import (
    DocumentDetails,
    DocumentListResponse,
    DocumentSearchResponse,
    DocumentUploadResponse,
)
from ..utils.http import HTTPClient
from ..utils.logging import GovernsAILogger


class DocumentClient:
    """Client for document APIs."""

    def __init__(self, http_client: HTTPClient, logger: GovernsAILogger):
        self.http_client = http_client
        self.logger = logger

    async def upload_document(
        self,
        file: Union[bytes, bytearray, memoryview, str, Any],
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
        external_user_id: Optional[str] = None,
        external_source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        scope: Optional[str] = None,
        visibility: Optional[str] = None,
        email: Optional[str] = None,
        name: Optional[str] = None,
        processing_mode: Optional[str] = None,
    ) -> DocumentUploadResponse:
        """Upload a document for OCR and RAG indexing."""
        form_data = aiohttp.FormData()
        file_payload, inferred_name = self._normalize_file(file, filename)

        form_data.add_field(
            "file",
            file_payload,
            filename=inferred_name,
            content_type=content_type,
        )
        form_data.add_field("filename", inferred_name)

        if content_type:
            form_data.add_field("contentType", content_type)
        if external_user_id:
            form_data.add_field("externalUserId", external_user_id)
        if external_source:
            form_data.add_field("externalSource", external_source)
        if metadata is not None:
            form_data.add_field("metadata", json.dumps(metadata))
        if scope:
            form_data.add_field("scope", scope)
        if visibility:
            form_data.add_field("visibility", visibility)
        if email:
            form_data.add_field("email", email)
        if name:
            form_data.add_field("name", name)
        if processing_mode:
            form_data.add_field("processingMode", processing_mode)

        try:
            response = await self.http_client.post_form_data(
                "/api/v1/documents", form_data
            )
            return DocumentUploadResponse.from_dict(response.data)
        except Exception as exc:
            self.logger.error(f"Document upload failed: {exc}")
            raise GovernsAIError(f"Document upload failed: {exc}")

    async def get_document(
        self,
        document_id: str,
        include_chunks: Optional[bool] = None,
        include_content: Optional[bool] = None,
    ) -> DocumentDetails:
        """Get a document and optionally include chunks/content."""
        params: Dict[str, Any] = {}
        if include_chunks is not None:
            params["includeChunks"] = include_chunks
        if include_content is not None:
            params["includeContent"] = include_content

        try:
            response = await self.http_client.get(
                f"/api/v1/documents/{document_id}", params=params
            )
            payload = response.data.get("document", response.data)
            return DocumentDetails.from_dict(payload)
        except Exception as exc:
            self.logger.error(f"Get document failed: {exc}")
            raise GovernsAIError(f"Get document failed: {exc}")

    async def list_documents(
        self,
        user_id: Optional[str] = None,
        external_user_id: Optional[str] = None,
        external_source: Optional[str] = None,
        status: Optional[str] = None,
        content_type: Optional[str] = None,
        include_archived: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> DocumentListResponse:
        """List documents with optional filters."""
        params = {
            "userId": user_id,
            "externalUserId": external_user_id,
            "externalSource": external_source,
            "status": status,
            "contentType": content_type,
            "includeArchived": include_archived,
            "limit": limit,
            "offset": offset,
        }
        params = {key: value for key, value in params.items() if value is not None}

        try:
            response = await self.http_client.get("/api/v1/documents", params=params)
            return DocumentListResponse.from_dict(response.data)
        except Exception as exc:
            self.logger.error(f"List documents failed: {exc}")
            raise GovernsAIError(f"List documents failed: {exc}")

    async def search_documents(self, params: Dict[str, Any]) -> DocumentSearchResponse:
        """Vector-search across document chunks."""
        try:
            response = await self.http_client.post(
                "/api/v1/documents/search", data=params
            )
            return DocumentSearchResponse.from_dict(response.data)
        except Exception as exc:
            self.logger.error(f"Search documents failed: {exc}")
            raise GovernsAIError(f"Search documents failed: {exc}")

    async def delete_document(self, document_id: str) -> Dict[str, Any]:
        """Delete a document and associated chunks."""
        try:
            response = await self.http_client.delete(f"/api/v1/documents/{document_id}")
            return response.data
        except Exception as exc:
            self.logger.error(f"Delete document failed: {exc}")
            raise GovernsAIError(f"Delete document failed: {exc}")

    def _normalize_file(
        self,
        file: Union[bytes, bytearray, memoryview, str, Any],
        filename: Optional[str],
    ) -> Tuple[bytes, str]:
        """Normalize supported file inputs to bytes + filename."""
        if isinstance(file, str):
            if not os.path.isfile(file):
                raise GovernsAIError(f"Document path does not exist: {file}")
            with open(file, "rb") as file_handle:
                content = file_handle.read()
            inferred_name = filename or os.path.basename(file)
            return content, inferred_name

        if isinstance(file, (bytes, bytearray, memoryview)):
            return bytes(file), filename or "document"

        if hasattr(file, "read") and callable(file.read):
            content = file.read()
            if isinstance(content, str):
                content = content.encode("utf-8")
            if not isinstance(content, (bytes, bytearray, memoryview)):
                raise GovernsAIError("File-like object must return bytes from read()")

            inferred_name = filename or getattr(file, "name", None) or "document"
            return bytes(content), os.path.basename(str(inferred_name))

        raise GovernsAIError(
            (
                "Unsupported file type. Use bytes, bytearray, memoryview, "
                "file path, or file-like object."
            )
        )
