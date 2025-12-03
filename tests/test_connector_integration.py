"""Integration tests for connector operations."""

from unittest.mock import MagicMock, Mock, patch


from gemini_drive_connector import GeminiDriveConnector, GeminiDriveConnectorConfig


def test_list_files_in_folder_success() -> None:
    """Test listing files in folder successfully."""
    config = GeminiDriveConnectorConfig(api_key="test-key")
    mock_files = [{"id": "1", "name": "test.pdf", "mimeType": "application/pdf"}]

    with patch("gemini_drive_connector.connector.GeminiClient"):
        with patch("gemini_drive_connector.connector.GeminiFileStore"):
            with patch("gemini_drive_connector.connector.GeminiChat"):
                connector = GeminiDriveConnector(config)

                mock_drive_client = MagicMock()
                mock_service = MagicMock()
                mock_drive_client.service = mock_service
                connector._drive_client = mock_drive_client

                mock_file_handler = MagicMock()
                mock_file_handler.list_files.return_value = mock_files

                with patch("gemini_drive_connector.connector.DriveFileHandler", return_value=mock_file_handler):
                    with patch("gemini_drive_connector.connector.spinner_context"):
                        with patch("gemini_drive_connector.connector.PerformanceProfiler"):
                            files = connector._list_files_in_folder("folder123", mock_file_handler)
                            assert len(files) == 1
                            assert files[0]["id"] == "1"


def test_list_files_in_folder_empty() -> None:
    """Test listing files when folder is empty."""
    config = GeminiDriveConnectorConfig(api_key="test-key")

    with patch("gemini_drive_connector.connector.GeminiClient"):
        with patch("gemini_drive_connector.connector.GeminiFileStore"):
            with patch("gemini_drive_connector.connector.GeminiChat"):
                connector = GeminiDriveConnector(config)

                mock_file_handler = MagicMock()
                mock_file_handler.list_files.return_value = []

                mock_spinner = MagicMock()

                with patch("gemini_drive_connector.connector.spinner_context", return_value=MagicMock(__enter__=lambda x: mock_spinner, __exit__=lambda *args: None)):
                    with patch("gemini_drive_connector.connector.PerformanceProfiler"):
                        files = connector._list_files_in_folder("folder123", mock_file_handler)
                        assert files == []
                        mock_spinner.fail.assert_called_once()


def test_process_all_files() -> None:
    """Test processing all files."""
    config = GeminiDriveConnectorConfig(api_key="test-key")
    mock_files = [
        {"id": "1", "name": "file1.pdf", "mimeType": "application/pdf"},
        {"id": "2", "name": "file2.txt", "mimeType": "text/plain"},
    ]

    with patch("gemini_drive_connector.connector.GeminiClient"):
        with patch("gemini_drive_connector.connector.GeminiFileStore"):
            with patch("gemini_drive_connector.connector.GeminiChat"):
                connector = GeminiDriveConnector(config)

                mock_file_handler = MagicMock()

                with patch.object(connector, "_process_file_safely") as mock_process:
                    connector._process_all_files(mock_files, mock_file_handler)
                    assert mock_process.call_count == 2


def test_process_file_safely_success() -> None:
    """Test safe file processing with success."""
    config = GeminiDriveConnectorConfig(api_key="test-key")

    with patch("gemini_drive_connector.connector.GeminiClient"):
        with patch("gemini_drive_connector.connector.GeminiFileStore"):
            with patch("gemini_drive_connector.connector.GeminiChat"):
                connector = GeminiDriveConnector(config)

                mock_file_handler = MagicMock()

                with patch.object(connector, "_process_file") as mock_process:
                    connector._process_file_safely(mock_file_handler, "file123", "test.pdf", "application/pdf")
                    mock_process.assert_called_once()


def test_process_file_safely_with_error() -> None:
    """Test safe file processing with error."""
    config = GeminiDriveConnectorConfig(api_key="test-key")

    with patch("gemini_drive_connector.connector.GeminiClient"):
        with patch("gemini_drive_connector.connector.GeminiFileStore"):
            with patch("gemini_drive_connector.connector.GeminiChat"):
                connector = GeminiDriveConnector(config)

                mock_file_handler = MagicMock()

                with patch.object(connector, "_process_file", side_effect=ValueError("Test error")):
                    # Should not raise, but log error
                    connector._process_file_safely(mock_file_handler, "file123", "test.pdf", "application/pdf")


def test_process_file_full_workflow() -> None:
    """Test full file processing workflow."""
    config = GeminiDriveConnectorConfig(api_key="test-key")

    with patch("gemini_drive_connector.connector.GeminiClient"):
        with patch("gemini_drive_connector.connector.GeminiFileStore") as mock_file_store_class:
            with patch("gemini_drive_connector.connector.GeminiChat"):
                connector = GeminiDriveConnector(config)

                mock_file_handler = MagicMock()
                mock_file_handler.download_file.return_value = b"file content"

                mock_uploaded_file = Mock()
                mock_uploaded_file.name = "uploaded-name"
                mock_file_store_instance = MagicMock()
                mock_file_store_instance.upload_file.return_value = mock_uploaded_file
                connector._file_store = mock_file_store_instance

                with patch.object(connector, "_download_file", return_value=b"content"):
                    with patch.object(connector, "_upload_file_to_store", return_value=mock_uploaded_file):
                        with patch.object(connector, "_validate_uploaded_file_name", return_value="uploaded-name"):
                            with patch.object(connector, "_index_file"):
                                connector._process_file(mock_file_handler, "file123", "test.pdf", "application/pdf")


def test_download_file() -> None:
    """Test file download method."""
    config = GeminiDriveConnectorConfig(api_key="test-key")

    with patch("gemini_drive_connector.connector.GeminiClient"):
        with patch("gemini_drive_connector.connector.GeminiFileStore"):
            with patch("gemini_drive_connector.connector.GeminiChat"):
                connector = GeminiDriveConnector(config)

                mock_file_handler = MagicMock()
                mock_file_handler.download_file.return_value = b"file content"

                with patch("gemini_drive_connector.connector.spinner_context"):
                    with patch("gemini_drive_connector.connector.PerformanceProfiler"):
                        content = connector._download_file(mock_file_handler, "file123", "test.pdf")
                        assert content == b"file content"


def test_upload_file_to_store() -> None:
    """Test file upload to store."""
    config = GeminiDriveConnectorConfig(api_key="test-key")

    with patch("gemini_drive_connector.connector.GeminiClient"):
        with patch("gemini_drive_connector.connector.GeminiFileStore") as mock_file_store_class:
            with patch("gemini_drive_connector.connector.GeminiChat"):
                connector = GeminiDriveConnector(config)

                mock_uploaded_file = Mock()
                mock_file_store_instance = MagicMock()
                mock_file_store_instance.upload_file.return_value = mock_uploaded_file
                connector._file_store = mock_file_store_instance

                with patch("gemini_drive_connector.connector.spinner_context"):
                    with patch("gemini_drive_connector.connector.PerformanceProfiler"):
                        result = connector._upload_file_to_store(b"content", "test.pdf", "application/pdf")
                        assert result is mock_uploaded_file


def test_index_file() -> None:
    """Test file indexing."""
    config = GeminiDriveConnectorConfig(api_key="test-key")

    with patch("gemini_drive_connector.connector.GeminiClient"):
        with patch("gemini_drive_connector.connector.GeminiFileStore") as mock_file_store_class:
            with patch("gemini_drive_connector.connector.GeminiChat"):
                connector = GeminiDriveConnector(config)

                mock_file_store_instance = MagicMock()
                connector._file_store = mock_file_store_instance

                with patch("gemini_drive_connector.connector.spinner_context"):
                    with patch("gemini_drive_connector.connector.PerformanceProfiler"):
                        connector._index_file("uploaded-name", "test.pdf")
                        mock_file_store_instance.import_file.assert_called_once_with("uploaded-name")

