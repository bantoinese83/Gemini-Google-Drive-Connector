"""Tests for main connector."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from gemini_drive_connector import GeminiDriveConnector, GeminiDriveConnectorConfig
from gemini_drive_connector.drive.files import DriveFileHandler


def test_connector_initialization() -> None:
    """Test connector initialization."""
    config = GeminiDriveConnectorConfig(api_key="test-key")
    with patch("gemini_drive_connector.connector.GeminiClient"):
        with patch("gemini_drive_connector.connector.GeminiFileStore"):
            with patch("gemini_drive_connector.connector.GeminiChat"):
                connector = GeminiDriveConnector(config)
                assert connector.config is config
                assert connector._drive_client is None


def test_ensure_drive_client_initialized() -> None:
    """Test drive client initialization."""
    config = GeminiDriveConnectorConfig(api_key="test-key")
    with patch("gemini_drive_connector.connector.GeminiClient"):
        with patch("gemini_drive_connector.connector.GeminiFileStore"):
            with patch("gemini_drive_connector.connector.GeminiChat"):
                connector = GeminiDriveConnector(config)
                assert connector._drive_client is None

                with patch("gemini_drive_connector.connector.DriveClient") as mock_drive_client:
                    mock_client_instance = MagicMock()
                    mock_drive_client.return_value = mock_client_instance
                    connector._ensure_drive_client_initialized()
                    assert connector._drive_client is not None


def test_create_file_handler() -> None:
    """Test file handler creation."""
    config = GeminiDriveConnectorConfig(api_key="test-key")
    with patch("gemini_drive_connector.connector.GeminiClient"):
        with patch("gemini_drive_connector.connector.GeminiFileStore"):
            with patch("gemini_drive_connector.connector.GeminiChat"):
                connector = GeminiDriveConnector(config)

                mock_service = MagicMock()
                mock_drive_client = MagicMock()
                mock_drive_client.service = mock_service
                connector._drive_client = mock_drive_client

                handler = connector._create_file_handler()
                assert isinstance(handler, DriveFileHandler)


def test_create_file_handler_no_client() -> None:
    """Test file handler creation when drive client is None."""
    config = GeminiDriveConnectorConfig(api_key="test-key")
    with patch("gemini_drive_connector.connector.GeminiClient"):
        with patch("gemini_drive_connector.connector.GeminiFileStore"):
            with patch("gemini_drive_connector.connector.GeminiChat"):
                connector = GeminiDriveConnector(config)
                connector._drive_client = None

                with pytest.raises(RuntimeError, match="Drive client must be initialized"):
                    connector._create_file_handler()


def test_validate_uploaded_file_name() -> None:
    """Test uploaded file name validation."""
    config = GeminiDriveConnectorConfig(api_key="test-key")
    with patch("gemini_drive_connector.connector.GeminiClient"):
        with patch("gemini_drive_connector.connector.GeminiFileStore"):
            with patch("gemini_drive_connector.connector.GeminiChat"):
                connector = GeminiDriveConnector(config)

                mock_file = Mock()
                mock_file.name = "uploaded-file-name"
                result = connector._validate_uploaded_file_name(mock_file, "original-name")
                assert result == "uploaded-file-name"


def test_validate_uploaded_file_name_none() -> None:
    """Test uploaded file name validation when name is None."""
    config = GeminiDriveConnectorConfig(api_key="test-key")
    with patch("gemini_drive_connector.connector.GeminiClient"):
        with patch("gemini_drive_connector.connector.GeminiFileStore"):
            with patch("gemini_drive_connector.connector.GeminiChat"):
                connector = GeminiDriveConnector(config)

                mock_file = Mock()
                mock_file.name = None
                with pytest.raises(RuntimeError, match="has no name attribute"):
                    connector._validate_uploaded_file_name(mock_file, "original-name")


def test_ask_delegates_to_chat() -> None:
    """Test that ask method delegates to chat."""
    config = GeminiDriveConnectorConfig(api_key="test-key")
    mock_chat = MagicMock()
    mock_chat.ask.return_value = "Answer"

    with patch("gemini_drive_connector.connector.GeminiClient"):
        with patch("gemini_drive_connector.connector.GeminiFileStore"):
            with patch("gemini_drive_connector.connector.GeminiChat", return_value=mock_chat):
                connector = GeminiDriveConnector(config)
                connector._chat = mock_chat

                answer = connector.ask("Question?")
                assert answer == "Answer"
                mock_chat.ask.assert_called_once_with("Question?")

