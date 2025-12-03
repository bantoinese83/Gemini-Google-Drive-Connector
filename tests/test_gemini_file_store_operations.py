"""Tests for Gemini file store operations."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from gemini_drive_connector.gemini.file_store import GeminiFileStore


def test_upload_file() -> None:
    """Test file upload."""
    mock_client = MagicMock()
    mock_store = MagicMock()
    mock_store.name = "test-store"
    mock_uploaded_file = Mock()
    mock_client.files.upload.return_value = mock_uploaded_file

    with patch("gemini_drive_connector.gemini.file_store.safe_execute", return_value=mock_store):
        file_store = GeminiFileStore(mock_client, "test")

        content = b"file content"
        result = file_store.upload_file(content, "test.pdf", "application/pdf")

        assert result is mock_uploaded_file
        mock_client.files.upload.assert_called_once()


def test_import_file() -> None:
    """Test file import."""
    mock_client = MagicMock()
    mock_store = MagicMock()
    mock_store.name = "test-store"
    mock_operation = Mock()
    mock_operation.done = True
    mock_operation.error = None

    with patch("gemini_drive_connector.gemini.file_store.safe_execute", return_value=mock_store):
        file_store = GeminiFileStore(mock_client, "test")

        with patch.object(file_store, "_wait_for_operation"):
            with patch("gemini_drive_connector.gemini.file_store.safe_execute", return_value=mock_operation):
                file_store.import_file("file-name")
                file_store._wait_for_operation.assert_called_once_with(mock_operation, "file-name")


def test_poll_operation_status() -> None:
    """Test operation status polling."""
    mock_client = MagicMock()
    mock_store = MagicMock()
    mock_store.name = "test-store"
    mock_operation = Mock()
    mock_updated_operation = Mock()
    mock_client.operations.get.return_value = mock_updated_operation

    with patch("gemini_drive_connector.gemini.file_store.safe_execute", return_value=mock_store):
        file_store = GeminiFileStore(mock_client, "test")

        result = file_store._poll_operation_status(mock_operation)
        assert result is mock_updated_operation
        mock_client.operations.get.assert_called_once_with(mock_operation)


def test_poll_operation_status_error() -> None:
    """Test operation status polling with error."""
    mock_client = MagicMock()
    mock_store = MagicMock()
    mock_store.name = "test-store"
    mock_operation = Mock()
    mock_client.operations.get.side_effect = Exception("Polling failed")

    with patch("gemini_drive_connector.gemini.file_store.safe_execute", return_value=mock_store):
        file_store = GeminiFileStore(mock_client, "test")

        with pytest.raises(RuntimeError, match="Operation polling failed"):
            file_store._poll_operation_status(mock_operation)

