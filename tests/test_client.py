"""
Tests for the GovernsAI client.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from governs_ai import GovernsAIClient, GovernsAIConfig
from governs_ai.models import PrecheckRequest, PrecheckResponse, Decision


class TestGovernsAIClient:
    """Test cases for GovernsAIClient."""

    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client for testing."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.data = {"status": "healthy"}
        mock_client.get.return_value = mock_response
        return mock_client

    @pytest.fixture
    def client(self, mock_http_client):
        """Create a test client."""
        config = GovernsAIConfig(
            api_key="test-key",
            org_id="test-org",
            http_client=mock_http_client,
        )
        return GovernsAIClient(config=config)

    def test_default_base_url_is_production(self):
        """Default base URL should target managed API, not localhost."""
        config = GovernsAIConfig(api_key="test-key", org_id="test-org")
        assert config.base_url == "https://api.governsai.com"

    @pytest.mark.asyncio
    async def test_test_connection_success(self, client, mock_http_client):
        """Test successful connection test."""
        result = await client.test_connection()
        assert result is True
        mock_http_client.get.assert_called_once_with("/api/v1/health")

    @pytest.mark.asyncio
    async def test_test_connection_failure(self, client, mock_http_client):
        """Test failed connection test."""
        mock_http_client.get.side_effect = Exception("Connection failed")
        result = await client.test_connection()
        assert result is False

    @pytest.mark.asyncio
    async def test_precheck_request(self, client, mock_http_client):
        """Test precheck request."""
        # Mock precheck response
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.data = {
            "decision": "allow",
            "reasons": [],
            "requiresConfirmation": False
        }
        mock_http_client.post.return_value = mock_response

        result = await client.precheck_request(
            tool="model.chat",
            scope="net.external",
            raw_text="Hello",
            payload={"messages": []},
            tags=["test"],
            user_id="user-123"
        )

        assert isinstance(result, PrecheckResponse)
        assert result.decision == Decision.ALLOW
        mock_http_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_budget_context(self, client, mock_http_client):
        """Test get budget context."""
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.data = {
            "monthlyLimit": 1000.0,
            "currentSpend": 250.0,
            "remainingBudget": 750.0,
            "currency": "USD"
        }
        mock_http_client.get.return_value = mock_response

        result = await client.get_budget_context("user-123")

        assert result.monthly_limit == 1000.0
        assert result.current_spend == 250.0
        assert result.remaining_budget == 750.0
        assert result.currency == "USD"

    @pytest.mark.asyncio
    async def test_record_usage(self, client, mock_http_client):
        """Test record usage."""
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_http_client.post.return_value = mock_response

        usage_data = {
            "user_id": "user-123",
            "org_id": "org-456",
            "provider": "openai",
            "model": "gpt-4",
            "input_tokens": 100,
            "output_tokens": 50,
            "cost": 0.15,
            "cost_type": "external"
        }

        await client.record_usage(usage_data)

        mock_http_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_health_status(self, client, mock_http_client):
        """Test get health status."""
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.data = {
            "status": "healthy",
            "services": {"api": "healthy", "db": "healthy"},
            "version": "1.0.0"
        }
        mock_http_client.get.return_value = mock_response

        result = await client.get_health_status()

        assert result.status == "healthy"
        assert "api" in result.services
        assert result.version == "1.0.0"

    def test_update_config(self, client):
        """Test update configuration."""
        new_config = {"timeout": 60000, "retries": 5}
        client.update_config(new_config)
        
        assert client.config.timeout == 60000
        assert client.config.retries == 5

    def test_get_config(self, client):
        """Test get configuration."""
        config = client.get_config()
        assert isinstance(config, GovernsAIConfig)
        assert config.api_key == "test-key"
        assert config.org_id == "test-org"

    def test_context_and_document_clients_available(self, client):
        """Feature parity clients should be initialized on main client."""
        assert client.context is not None
        assert client.documents is not None
