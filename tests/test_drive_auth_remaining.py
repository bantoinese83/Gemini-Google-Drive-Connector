"""Tests for remaining Drive auth coverage."""

from unittest.mock import MagicMock, patch


from gemini_drive_connector.drive.auth import DriveAuth


def test_load_or_refresh_credentials_no_creds_loaded() -> None:
    """Test _load_or_refresh_credentials when loading returns None."""
    auth = DriveAuth()

    with patch.object(auth, "_token_file_exists", return_value=True):
        with patch.object(auth, "_load_credentials_from_file", return_value=None):
            result = auth._load_or_refresh_credentials()
            assert result is None


def test_authenticate_do_authenticate() -> None:
    """Test _do_authenticate internal method."""
    auth = DriveAuth()

    mock_creds = MagicMock()
    mock_flow = MagicMock()
    mock_flow.run_local_server.return_value = mock_creds

    with patch("gemini_drive_connector.drive.auth.InstalledAppFlow") as mock_flow_class:
        mock_flow_class.from_client_secrets_file.return_value = mock_flow
        result = auth._do_authenticate()
        assert result is mock_creds


def test_build_service() -> None:
    """Test _build_service method."""
    auth = DriveAuth()

    mock_creds = MagicMock()
    mock_service = MagicMock()

    with patch("gemini_drive_connector.drive.auth.build", return_value=mock_service):
        with patch("gemini_drive_connector.drive.auth.safe_execute", return_value=mock_service):
            result = auth._build_service(mock_creds)
            assert result is mock_service

