"""Full workflow tests for Gemini file store."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from gemini_drive_connector.gemini.file_store import GeminiFileStore


def test_wait_for_operation_success() -> None:
    """Test waiting for operation to complete successfully."""
    mock_client = MagicMock()
    mock_store = MagicMock()
    mock_store.name = "test-store"

    mock_operation = Mock()
    mock_operation.done = False
    mock_operation.error = None

    mock_updated_operation = Mock()
    mock_updated_operation.done = True
    mock_updated_operation.error = None

    with patch("gemini_drive_connector.gemini.file_store.safe_execute", return_value=mock_store):
        file_store = GeminiFileStore(mock_client, "test")

        with patch.object(file_store, "_poll_operation_status", return_value=mock_updated_operation):
            with patch("time.sleep"):
                file_store._wait_for_operation(mock_operation, "test.txt")
                # Should complete without raising


def test_wait_for_operation_timeout() -> None:
    """Test waiting for operation that times out."""
    mock_client = MagicMock()
    mock_store = MagicMock()
    mock_store.name = "test-store"

    mock_operation = Mock()
    mock_operation.done = False

    with patch("gemini_drive_connector.gemini.file_store.safe_execute", return_value=mock_store):
        file_store = GeminiFileStore(mock_client, "test")

        with patch.object(file_store, "_poll_operation_status", return_value=mock_operation):
            with patch("time.sleep"):
                # Simulate max attempts reached
                with patch.object(file_store, "_validate_operation_completion", side_effect=TimeoutError("Timeout")):
                    with pytest.raises(TimeoutError):
                        file_store._wait_for_operation(mock_operation, "test.txt")


def test_wait_for_operation_with_backoff() -> None:
    """Test operation waiting with exponential backoff."""
    mock_client = MagicMock()
    mock_store = MagicMock()
    mock_store.name = "test-store"

    mock_operation = Mock()
    mock_operation.done = False

    mock_updated_operation = Mock()
    mock_updated_operation.done = True
    mock_updated_operation.error = None

    with patch("gemini_drive_connector.gemini.file_store.safe_execute", return_value=mock_store):
        file_store = GeminiFileStore(mock_client, "test")

        call_count = 0

        def poll_side_effect(op):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                result = Mock()
                result.done = False
                return result
            result = Mock()
            result.done = True
            result.error = None
            return result

        with patch.object(file_store, "_poll_operation_status", side_effect=poll_side_effect):
            with patch("time.sleep") as mock_sleep:
                file_store._wait_for_operation(mock_operation, "test.txt")
                # Should have called sleep multiple times
                assert mock_sleep.call_count > 0

