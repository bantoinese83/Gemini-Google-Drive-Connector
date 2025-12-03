"""Full workflow tests for connector."""

from unittest.mock import patch


from gemini_drive_connector import GeminiDriveConnector, GeminiDriveConnectorConfig


def test_connector_with_profiling_enabled() -> None:
    """Test connector initialization with profiling enabled."""
    config = GeminiDriveConnectorConfig(api_key="test-key")

    with patch("gemini_drive_connector.connector.PROFILING_ENABLED", True):
        with patch("gemini_drive_connector.connector.GeminiClient"):
            with patch("gemini_drive_connector.connector.GeminiFileStore"):
                with patch("gemini_drive_connector.connector.GeminiChat"):
                    with patch("gemini_drive_connector.connector.PerformanceProfiler"):
                        connector = GeminiDriveConnector(config)
                        assert connector.config is config


def test_sync_folder_to_store_empty_files() -> None:
    """Test sync when folder has no files."""
    config = GeminiDriveConnectorConfig(api_key="test-key")

    with patch("gemini_drive_connector.connector.GeminiClient"):
        with patch("gemini_drive_connector.connector.GeminiFileStore"):
            with patch("gemini_drive_connector.connector.GeminiChat"):
                connector = GeminiDriveConnector(config)

                with patch.object(connector, "_ensure_drive_client_initialized"):
                    with patch.object(connector, "_create_file_handler") as mock_create_handler:
                        with patch.object(connector, "_list_files_in_folder", return_value=[]):
                            # Should return early without processing
                            connector.sync_folder_to_store("folder123")
                            mock_create_handler.assert_called_once()


def test_sync_folder_to_store_with_files() -> None:
    """Test sync when folder has files."""
    config = GeminiDriveConnectorConfig(api_key="test-key")
    mock_files = [{"id": "1", "name": "test.pdf", "mimeType": "application/pdf"}]

    with patch("gemini_drive_connector.connector.GeminiClient"):
        with patch("gemini_drive_connector.connector.GeminiFileStore"):
            with patch("gemini_drive_connector.connector.GeminiChat"):
                connector = GeminiDriveConnector(config)

                with patch.object(connector, "_ensure_drive_client_initialized"):
                    with patch.object(connector, "_create_file_handler"):
                        with patch.object(connector, "_list_files_in_folder", return_value=mock_files):
                            with patch.object(connector, "_process_all_files") as mock_process:
                                connector.sync_folder_to_store("folder123")
                                mock_process.assert_called_once_with(mock_files, connector._create_file_handler.return_value)

