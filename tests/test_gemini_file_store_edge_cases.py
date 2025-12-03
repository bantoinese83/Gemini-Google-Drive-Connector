"""Edge case tests for Gemini file store."""

from unittest.mock import MagicMock, patch


from gemini_drive_connector.gemini.file_store import GeminiFileStore


def test_file_store_store_property() -> None:
    """Test store property access."""
    mock_client = MagicMock()
    mock_store = MagicMock()
    mock_store.name = "test-store"

    with patch("gemini_drive_connector.gemini.file_store.safe_execute", return_value=mock_store):
        file_store = GeminiFileStore(mock_client, "test")
        assert file_store.store is mock_store

