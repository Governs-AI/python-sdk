"""
Tests for HTTP client defaults.
"""

from unittest.mock import MagicMock

from governs_ai.utils.http import HTTPClient


def test_default_auth_header_uses_x_governs_key():
    """SDK should send API key via X-Governs-Key header."""
    mock_session = MagicMock()
    mock_session.closed = True

    client = HTTPClient(
        base_url="http://example.com",
        api_key="test-key",
        session=mock_session,
    )

    headers = client._get_headers()

    assert headers["X-Governs-Key"] == "test-key"
    assert "Authorization" not in headers
