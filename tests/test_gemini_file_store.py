"""Tests for Gemini file store operations."""

from unittest.mock import MagicMock, patch

import pytest

from gemini_drive_connector.gemini.file_store import GeminiFileStore


def test_gemini_file_store_initialization() -> None:
    """Test GeminiFileStore initialization."""
    mock_client = MagicMock()
    mock_store = MagicMock()
    mock_store.name = "test-store"

    with patch("gemini_drive_connector.gemini.file_store.safe_execute", return_value=mock_store):
        file_store = GeminiFileStore(mock_client, "test-display-name")
        assert file_store.client is mock_client
        assert file_store.display_name == "test-display-name"


def test_gemini_file_store_name_property() -> None:
    """Test name property."""
    mock_client = MagicMock()
    mock_store = MagicMock()
    mock_store.name = "test-store-name"

    with patch("gemini_drive_connector.gemini.file_store.safe_execute", return_value=mock_store):
        file_store = GeminiFileStore(mock_client, "test")
        assert file_store.name == "test-store-name"


def test_gemini_file_store_name_property_none() -> None:
    """Test name property when store name is None."""
    mock_client = MagicMock()
    mock_store = MagicMock()
    mock_store.name = None

    with patch("gemini_drive_connector.gemini.file_store.safe_execute", return_value=mock_store):
        file_store = GeminiFileStore(mock_client, "test")
        with pytest.raises(RuntimeError, match="File search store name is not available"):
            _ = file_store.name


def test_calculate_next_poll_interval() -> None:
    """Test poll interval calculation."""
    mock_client = MagicMock()
    mock_store = MagicMock()
    mock_store.name = "test"

    with patch("gemini_drive_connector.gemini.file_store.safe_execute", return_value=mock_store):
        file_store = GeminiFileStore(mock_client, "test")

        # First few attempts should not increase interval
        interval = file_store._calculate_next_poll_interval(1, 1.0)
        assert interval == 1.0

        interval = file_store._calculate_next_poll_interval(3, 1.0)
        assert interval == 1.0

        # After 3 attempts, should increase with backoff
        interval = file_store._calculate_next_poll_interval(4, 1.0)
        assert interval == 1.5  # 1.0 * 1.5

        # Should cap at MAX_POLL_INTERVAL
        interval = file_store._calculate_next_poll_interval(10, 20.0)
        from gemini_drive_connector.config.settings import MAX_POLL_INTERVAL
        assert interval <= MAX_POLL_INTERVAL


def test_validate_operation_completion_success() -> None:
    """Test operation completion validation for success."""
    mock_client = MagicMock()
    mock_store = MagicMock()
    mock_store.name = "test"

    with patch("gemini_drive_connector.gemini.file_store.safe_execute", return_value=mock_store):
        file_store = GeminiFileStore(mock_client, "test")

        mock_operation = MagicMock()
        mock_operation.done = True
        mock_operation.error = None

        # Should not raise
        file_store._validate_operation_completion(mock_operation, "test.txt")


def test_validate_operation_completion_timeout() -> None:
    """Test operation completion validation for timeout."""
    mock_client = MagicMock()
    mock_store = MagicMock()
    mock_store.name = "test"

    with patch("gemini_drive_connector.gemini.file_store.safe_execute", return_value=mock_store):
        file_store = GeminiFileStore(mock_client, "test")

        mock_operation = MagicMock()
        mock_operation.done = False

        with pytest.raises(TimeoutError, match="timed out"):
            file_store._validate_operation_completion(mock_operation, "test.txt")


def test_validate_operation_completion_error() -> None:
    """Test operation completion validation for error."""
    mock_client = MagicMock()
    mock_store = MagicMock()
    mock_store.name = "test"

    with patch("gemini_drive_connector.gemini.file_store.safe_execute", return_value=mock_store):
        file_store = GeminiFileStore(mock_client, "test")

        mock_operation = MagicMock()
        mock_operation.done = True
        mock_operation.error = "Operation failed"

        with pytest.raises(RuntimeError, match="Indexing operation failed"):
            file_store._validate_operation_completion(mock_operation, "test.txt")

