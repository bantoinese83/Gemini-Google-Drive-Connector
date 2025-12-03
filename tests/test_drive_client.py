"""Tests for Drive client."""

from unittest.mock import MagicMock, patch

from gemini_drive_connector.drive.client import DriveClient
from gemini_drive_connector.drive.auth import DriveAuth


def test_drive_client_initialization() -> None:
    """Test DriveClient initialization."""
    client = DriveClient()
    assert client._auth is not None
    assert isinstance(client._auth, DriveAuth)


def test_drive_client_with_custom_auth() -> None:
    """Test DriveClient with custom auth."""
    custom_auth = DriveAuth("custom_token.json", "custom_creds.json")
    client = DriveClient(custom_auth)
    assert client._auth is custom_auth


def test_drive_client_service_property() -> None:
    """Test DriveClient service property."""
    client = DriveClient()

    mock_service = MagicMock()
    with patch.object(client._auth, "get_service", return_value=mock_service):
        service = client.service
        assert service is mock_service
        # Should cache the service
        service2 = client.service
        assert service2 is mock_service
        assert client._service is mock_service

