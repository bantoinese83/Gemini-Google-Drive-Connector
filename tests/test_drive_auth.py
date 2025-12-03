"""Tests for Drive authentication."""

import json
from unittest.mock import MagicMock, patch

import pytest

from gemini_drive_connector.drive.auth import DriveAuth


def test_drive_auth_initialization() -> None:
    """Test DriveAuth initialization."""
    auth = DriveAuth()
    assert auth.token_path == "token.json"
    assert auth.credentials_path == "credentials.json"

    # Test custom paths
    auth_custom = DriveAuth("custom_token.json", "custom_creds.json")
    assert auth_custom.token_path == "custom_token.json"
    assert auth_custom.credentials_path == "custom_creds.json"


def test_token_file_exists() -> None:
    """Test token file existence check."""
    auth = DriveAuth()

    # Test with non-existent file
    with patch("os.path.exists", return_value=False):
        assert auth._token_file_exists() is False

    # Test with existing file
    with patch("os.path.exists", return_value=True):
        assert auth._token_file_exists() is True


def test_remove_corrupted_token_file() -> None:
    """Test removal of corrupted token file."""
    auth = DriveAuth()

    with patch("os.remove") as mock_remove:
        auth._remove_corrupted_token_file()
        mock_remove.assert_called_once_with(auth.token_path)


def test_validate_credentials_file_valid() -> None:
    """Test credentials file validation with valid JSON."""
    auth = DriveAuth()

    with patch("builtins.open", create=True) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = '{"test": "data"}'
        mock_open.return_value.__enter__.return_value = mock_open.return_value

        with patch("json.load", return_value={"test": "data"}):
            # Should not raise
            auth._validate_credentials_file()


def test_validate_credentials_file_invalid_json() -> None:
    """Test credentials file validation with invalid JSON."""
    auth = DriveAuth()

    with patch("builtins.open", create=True):
        with patch("json.load", side_effect=json.JSONDecodeError("Error", "doc", 0)):
            with pytest.raises(ValueError, match="Invalid credentials file format"):
                auth._validate_credentials_file()


def test_refresh_credentials_if_needed_no_refresh_token() -> None:
    """Test refresh when no refresh token available."""
    auth = DriveAuth()

    mock_creds = MagicMock()
    mock_creds.expired = True
    mock_creds.refresh_token = None

    result = auth._refresh_credentials_if_needed(mock_creds)
    assert result is None


def test_refresh_credentials_if_needed_not_expired() -> None:
    """Test refresh when credentials not expired."""
    auth = DriveAuth()

    mock_creds = MagicMock()
    mock_creds.expired = False
    mock_creds.refresh_token = "token"

    result = auth._refresh_credentials_if_needed(mock_creds)
    assert result is None


def test_refresh_credentials_if_needed_success() -> None:
    """Test successful credential refresh."""
    auth = DriveAuth()

    mock_creds = MagicMock()
    mock_creds.expired = True
    mock_creds.refresh_token = "refresh_token"

    with patch("google.auth.transport.requests.Request"):
        mock_creds.refresh.return_value = None
        result = auth._refresh_credentials_if_needed(mock_creds)
        assert result is mock_creds


def test_refresh_credentials_if_needed_failure() -> None:
    """Test credential refresh failure."""
    auth = DriveAuth()

    mock_creds = MagicMock()
    mock_creds.expired = True
    mock_creds.refresh_token = "refresh_token"
    mock_creds.refresh.side_effect = Exception("Refresh failed")

    with patch("google.auth.transport.requests.Request"):
        result = auth._refresh_credentials_if_needed(mock_creds)
        assert result is None

