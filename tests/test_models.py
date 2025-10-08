"""
Tests for data models.
"""

import pytest
from governs_ai.models import (
    PrecheckRequest,
    PrecheckResponse,
    Decision,
    BudgetContext,
    UsageRecord,
    ConfirmationRequest,
    ConfirmationResponse,
    HealthStatus,
)


class TestPrecheckRequest:
    """Test cases for PrecheckRequest."""

    def test_creation(self):
        """Test PrecheckRequest creation."""
        request = PrecheckRequest(
            tool="model.chat",
            scope="net.external",
            raw_text="Hello",
            payload={"messages": []},
            tags=["test"],
            user_id="user-123"
        )

        assert request.tool == "model.chat"
        assert request.scope == "net.external"
        assert request.raw_text == "Hello"
        assert request.user_id == "user-123"

    def test_to_dict(self):
        """Test PrecheckRequest to_dict."""
        request = PrecheckRequest(
            tool="model.chat",
            scope="net.external",
            raw_text="Hello",
            payload={"messages": []},
            tags=["test"],
            user_id="user-123"
        )

        data = request.to_dict()
        assert data["tool"] == "model.chat"
        assert data["scope"] == "net.external"
        assert data["rawText"] == "Hello"
        assert data["userId"] == "user-123"

    def test_from_dict(self):
        """Test PrecheckRequest from_dict."""
        data = {
            "tool": "model.chat",
            "scope": "net.external",
            "rawText": "Hello",
            "payload": {"messages": []},
            "tags": ["test"],
            "userId": "user-123"
        }

        request = PrecheckRequest.from_dict(data)
        assert request.tool == "model.chat"
        assert request.scope == "net.external"
        assert request.raw_text == "Hello"
        assert request.user_id == "user-123"


class TestPrecheckResponse:
    """Test cases for PrecheckResponse."""

    def test_creation(self):
        """Test PrecheckResponse creation."""
        response = PrecheckResponse(
            decision=Decision.ALLOW,
            reasons=[],
            metadata={"test": "value"}
        )

        assert response.decision == Decision.ALLOW
        assert response.reasons == []
        assert response.metadata == {"test": "value"}

    def test_string_decision(self):
        """Test PrecheckResponse with string decision."""
        response = PrecheckResponse(
            decision="allow",
            reasons=[]
        )

        assert response.decision == Decision.ALLOW

    def test_from_dict(self):
        """Test PrecheckResponse from_dict."""
        data = {
            "decision": "allow",
            "reasons": ["Policy check passed"],
            "metadata": {"test": "value"},
            "requiresConfirmation": False,
            "confirmationUrl": None
        }

        response = PrecheckResponse.from_dict(data)
        assert response.decision == Decision.ALLOW
        assert response.reasons == ["Policy check passed"]
        assert response.metadata == {"test": "value"}
        assert response.requires_confirmation is False


class TestBudgetContext:
    """Test cases for BudgetContext."""

    def test_creation(self):
        """Test BudgetContext creation."""
        context = BudgetContext(
            monthly_limit=1000.0,
            current_spend=250.0,
            remaining_budget=750.0,
            currency="USD"
        )

        assert context.monthly_limit == 1000.0
        assert context.current_spend == 250.0
        assert context.remaining_budget == 750.0
        assert context.currency == "USD"

    def test_from_dict(self):
        """Test BudgetContext from_dict."""
        data = {
            "monthlyLimit": 1000.0,
            "currentSpend": 250.0,
            "remainingBudget": 750.0,
            "currency": "USD",
            "periodStart": "2024-01-01",
            "periodEnd": "2024-01-31"
        }

        context = BudgetContext.from_dict(data)
        assert context.monthly_limit == 1000.0
        assert context.current_spend == 250.0
        assert context.remaining_budget == 750.0
        assert context.currency == "USD"
        assert context.period_start == "2024-01-01"
        assert context.period_end == "2024-01-31"


class TestUsageRecord:
    """Test cases for UsageRecord."""

    def test_creation(self):
        """Test UsageRecord creation."""
        record = UsageRecord(
            user_id="user-123",
            org_id="org-456",
            provider="openai",
            model="gpt-4",
            input_tokens=100,
            output_tokens=50,
            cost=0.15,
            cost_type="external"
        )

        assert record.user_id == "user-123"
        assert record.org_id == "org-456"
        assert record.provider == "openai"
        assert record.model == "gpt-4"
        assert record.input_tokens == 100
        assert record.output_tokens == 50
        assert record.cost == 0.15
        assert record.cost_type == "external"
        assert record.timestamp is not None

    def test_from_dict(self):
        """Test UsageRecord from_dict."""
        data = {
            "userId": "user-123",
            "orgId": "org-456",
            "provider": "openai",
            "model": "gpt-4",
            "inputTokens": 100,
            "outputTokens": 50,
            "cost": 0.15,
            "costType": "external",
            "timestamp": "2024-01-01T00:00:00Z"
        }

        record = UsageRecord.from_dict(data)
        assert record.user_id == "user-123"
        assert record.org_id == "org-456"
        assert record.provider == "openai"
        assert record.model == "gpt-4"
        assert record.input_tokens == 100
        assert record.output_tokens == 50
        assert record.cost == 0.15
        assert record.cost_type == "external"
        assert record.timestamp == "2024-01-01T00:00:00Z"


class TestHealthStatus:
    """Test cases for HealthStatus."""

    def test_creation(self):
        """Test HealthStatus creation."""
        status = HealthStatus(
            status="healthy",
            services={"api": "healthy", "db": "healthy"},
            version="1.0.0"
        )

        assert status.status == "healthy"
        assert status.services["api"] == "healthy"
        assert status.services["db"] == "healthy"
        assert status.version == "1.0.0"

    def test_from_dict(self):
        """Test HealthStatus from_dict."""
        data = {
            "status": "healthy",
            "services": {"api": "healthy", "db": "healthy"},
            "timestamp": "2024-01-01T00:00:00Z",
            "version": "1.0.0"
        }

        status = HealthStatus.from_dict(data)
        assert status.status == "healthy"
        assert status.services["api"] == "healthy"
        assert status.services["db"] == "healthy"
        assert status.timestamp == "2024-01-01T00:00:00Z"
        assert status.version == "1.0.0"
