"""Full workflow tests for Drive file operations."""

from io import BytesIO
from unittest.mock import MagicMock, Mock, patch

import pytest
from googleapiclient.errors import HttpError

from gemini_drive_connector.drive.files import DriveFileHandler


def test_list_files_full_workflow() -> None:
    """Test full list_files workflow."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    mock_files = [{"id": "1", "name": "test.pdf"}]
    with patch.object(handler, "_build_query", return_value="query"):
        with patch.object(handler, "_fetch_all_files", return_value=mock_files):
            result = handler.list_files("folder123", ["application/pdf"])
            assert len(result) == 1
            handler._build_query.assert_called_once_with("folder123", ["application/pdf"])


def test_download_file_full_workflow() -> None:
    """Test full download_file workflow."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    with patch.object(handler, "_validate_file_size"):
        with patch.object(handler, "_download_content", return_value=b"file content"):
            result = handler.download_file("file123")
            assert result == b"file content"
            handler._validate_file_size.assert_called_once_with("file123")


def test_download_to_buffer_full_workflow() -> None:
    """Test full download_to_buffer workflow."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    mock_request = MagicMock()
    mock_downloader = MagicMock()
    mock_downloader.next_chunk.return_value = (None, True)  # done = True

    with patch("gemini_drive_connector.drive.files.MediaIoBaseDownload", return_value=mock_downloader):
        with patch.object(handler, "_get_max_chunks", return_value=100):
            with patch.object(handler, "_download_next_chunk", return_value=True):
                with patch.object(handler, "_validate_chunk_count"):
                    buffer = handler._download_to_buffer(mock_request)
                    assert isinstance(buffer, BytesIO)


def test_download_to_buffer_multiple_chunks() -> None:
    """Test download_to_buffer with multiple chunks."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    mock_request = MagicMock()
    mock_downloader = MagicMock()
    mock_downloader.next_chunk.side_effect = [
        (None, False),  # First chunk, not done
        (None, False),  # Second chunk, not done
        (None, True),   # Third chunk, done
    ]

    with patch("gemini_drive_connector.drive.files.MediaIoBaseDownload", return_value=mock_downloader):
        with patch.object(handler, "_get_max_chunks", return_value=100):
            with patch.object(handler, "_validate_chunk_count"):
                buffer = handler._download_to_buffer(mock_request)
                assert isinstance(buffer, BytesIO)


def test_fetch_page_with_http_error() -> None:
    """Test _fetch_page with HTTP error."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    error = HttpError(Mock(status=404), b"Not Found")
    handler._files_api.list.return_value.execute.side_effect = error

    with pytest.raises(FileNotFoundError):
        handler._fetch_page("query", None)

