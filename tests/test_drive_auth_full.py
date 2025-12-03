"""Full workflow tests for Drive authentication."""

from unittest.mock import MagicMock, patch

import pytest

from gemini_drive_connector.drive.auth import DriveAuth


def test_get_service_with_valid_credentials() -> None:
    """Test get_service with valid existing credentials."""
    auth = DriveAuth()

    mock_creds = MagicMock()
    mock_creds.valid = True
    mock_service = MagicMock()

    with patch.object(auth, "_load_or_refresh_credentials", return_value=mock_creds):
        with patch.object(auth, "_save_token"):
            with patch.object(auth, "_build_service", return_value=mock_service):
                service = auth.get_service()
                assert service is mock_service
                auth._save_token.assert_called_once_with(mock_creds)


def test_get_service_with_invalid_credentials() -> None:
    """Test get_service when credentials need refresh."""
    auth = DriveAuth()

    mock_creds_invalid = MagicMock()
    mock_creds_invalid.valid = False
    mock_creds_new = MagicMock()
    mock_service = MagicMock()

    with patch.object(auth, "_load_or_refresh_credentials", return_value=mock_creds_invalid):
        with patch.object(auth, "_authenticate", return_value=mock_creds_new):
            with patch.object(auth, "_save_token"):
                with patch.object(auth, "_build_service", return_value=mock_service):
                    service = auth.get_service()
                    assert service is mock_service
                    auth._authenticate.assert_called_once()


def test_get_service_with_no_credentials() -> None:
    """Test get_service when no credentials exist."""
    auth = DriveAuth()

    mock_creds_new = MagicMock()
    mock_service = MagicMock()

    with patch.object(auth, "_load_or_refresh_credentials", return_value=None):
        with patch.object(auth, "_authenticate", return_value=mock_creds_new):
            with patch.object(auth, "_save_token"):
                with patch.object(auth, "_build_service", return_value=mock_service):
                    service = auth.get_service()
                    assert service is mock_service


def test_load_credentials_from_file_success() -> None:
    """Test loading credentials from file successfully."""
    auth = DriveAuth()

    mock_creds = MagicMock()
    mock_creds.valid = True

    with patch("os.path.exists", return_value=True):
        with patch("gemini_drive_connector.drive.auth.Credentials") as mock_credentials_class:
            mock_credentials_class.from_authorized_user_file.return_value = mock_creds
            result = auth._load_credentials_from_file()
            assert result is mock_creds


def test_load_credentials_from_file_corrupted() -> None:
    """Test loading credentials from corrupted file."""
    auth = DriveAuth()

    with patch("os.path.exists", return_value=True):
        with patch("gemini_drive_connector.drive.auth.Credentials") as mock_credentials_class:
            mock_credentials_class.from_authorized_user_file.side_effect = ValueError("Corrupted")
            with patch.object(auth, "_remove_corrupted_token_file"):
                result = auth._load_credentials_from_file()
                assert result is None


def test_load_or_refresh_credentials_flow() -> None:
    """Test full credential loading and refresh flow."""
    auth = DriveAuth()

    # Test: No token file
    with patch.object(auth, "_token_file_exists", return_value=False):
        result = auth._load_or_refresh_credentials()
        assert result is None

    # Test: Valid credentials
    mock_creds_valid = MagicMock()
    mock_creds_valid.valid = True
    with patch.object(auth, "_token_file_exists", return_value=True):
        with patch.object(auth, "_load_credentials_from_file", return_value=mock_creds_valid):
            result = auth._load_or_refresh_credentials()
            assert result is mock_creds_valid

    # Test: Expired credentials that can be refreshed
    mock_creds_expired = MagicMock()
    mock_creds_expired.valid = False
    mock_creds_refreshed = MagicMock()
    with patch.object(auth, "_token_file_exists", return_value=True):
        with patch.object(auth, "_load_credentials_from_file", return_value=mock_creds_expired):
            with patch.object(auth, "_refresh_credentials_if_needed", return_value=mock_creds_refreshed):
                result = auth._load_or_refresh_credentials()
                assert result is mock_creds_refreshed


def test_authenticate_credentials_file_not_found() -> None:
    """Test authenticate when credentials file doesn't exist."""
    auth = DriveAuth()

    with patch("os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError, match="Credentials file not found"):
            auth._authenticate()


def test_authenticate_success() -> None:
    """Test successful authentication."""
    auth = DriveAuth()

    mock_creds = MagicMock()
    mock_flow = MagicMock()
    mock_flow.run_local_server.return_value = mock_creds

    with patch("os.path.exists", return_value=True):
        with patch.object(auth, "_validate_credentials_file"):
            with patch("gemini_drive_connector.drive.auth.InstalledAppFlow") as mock_flow_class:
                mock_flow_class.from_client_secrets_file.return_value = mock_flow
                with patch("gemini_drive_connector.drive.auth.safe_execute", return_value=mock_creds):
                    result = auth._authenticate()
                    assert result is mock_creds


def test_save_token_success() -> None:
    """Test successful token save."""
    auth = DriveAuth()

    mock_creds = MagicMock()
    mock_creds.to_json.return_value = '{"token": "test"}'

    with patch("builtins.open", create=True) as mock_open:
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        auth._save_token(mock_creds)
        mock_file.write.assert_called_once()


def test_save_token_failure() -> None:
    """Test token save failure."""
    auth = DriveAuth()

    mock_creds = MagicMock()
    mock_creds.to_json.return_value = '{"token": "test"}'

    with patch("builtins.open", create=True, side_effect=OSError("Permission denied")):
        # Should not raise, but log warning
        auth._save_token(mock_creds)

