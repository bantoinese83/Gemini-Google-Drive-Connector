"""Integration tests for Drive file operations."""

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from gemini_drive_connector.drive.files import DriveFileHandler


def test_fetch_all_files_single_page() -> None:
    """Test fetching files with single page."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    mock_response = {
        "files": [{"id": "1", "name": "file1.pdf"}],
        "nextPageToken": None,
    }

    with patch.object(handler, "_fetch_page", return_value=mock_response):
        files = handler._fetch_all_files("query")
        assert len(files) == 1
        assert files[0]["id"] == "1"


def test_fetch_all_files_multiple_pages() -> None:
    """Test fetching files with multiple pages."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    mock_response_page1 = {
        "files": [{"id": "1", "name": "file1.pdf"}],
        "nextPageToken": "token123",
    }
    mock_response_page2 = {
        "files": [{"id": "2", "name": "file2.pdf"}],
        "nextPageToken": None,
    }

    with patch.object(
        handler, "_fetch_page", side_effect=[mock_response_page1, mock_response_page2]
    ):
        files = handler._fetch_all_files("query")
        assert len(files) == 2


def test_fetch_all_files_with_exception() -> None:
    """Test fetch_all_files with exception handling."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    with patch.object(handler, "_fetch_page", side_effect=FileNotFoundError("Not found")):
        with pytest.raises(FileNotFoundError):
            handler._fetch_all_files("query")


def test_fetch_all_files_unexpected_error() -> None:
    """Test fetch_all_files with unexpected error."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    with patch.object(handler, "_fetch_page", side_effect=KeyError("Unexpected")):
        with pytest.raises(RuntimeError, match="Failed to list files"):
            handler._fetch_all_files("query")


def test_check_page_limit_reached() -> None:
    """Test page limit check when limit is reached."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    with patch.object(handler, "_get_max_pages", return_value=100):
        handler._check_page_limit(100)  # Should log warning but not raise


def test_download_content_success() -> None:
    """Test successful file content download."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    mock_request = MagicMock()
    mock_buffer = BytesIO(b"file content")
    mock_downloader = MagicMock()
    mock_downloader.next_chunk.return_value = (None, True)  # done = True

    with patch.object(handler, "_create_download_request", return_value=mock_request):
        with patch.object(handler, "_download_to_buffer", return_value=mock_buffer):
            with patch.object(handler, "_read_buffer_content", return_value=b"file content"):
                content = handler._download_content("file123")
                assert content == b"file content"


def test_download_next_chunk_success() -> None:
    """Test successful chunk download."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    mock_downloader = MagicMock()
    mock_downloader.next_chunk.return_value = (None, True)  # done = True

    result = handler._download_next_chunk(mock_downloader)
    assert result is True


def test_download_next_chunk_failure() -> None:
    """Test chunk download failure."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    mock_downloader = MagicMock()
    mock_downloader.next_chunk.side_effect = Exception("Download failed")

    with pytest.raises(RuntimeError, match="Failed to download file"):
        handler._download_next_chunk(mock_downloader)


def test_read_buffer_content() -> None:
    """Test reading content from buffer."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    buffer = BytesIO(b"test content")
    content = handler._read_buffer_content(buffer)
    assert content == b"test content"


def test_validate_file_size_empty_file() -> None:
    """Test file size validation for empty file."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    mock_metadata = {"size": "0", "name": "empty.txt"}
    handler._files_api.get.return_value.execute.return_value = mock_metadata

    # Should not raise, but log warning
    handler._validate_file_size("file123")


def test_validate_file_size_too_large() -> None:
    """Test file size validation for file that's too large."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    # Create a file that's too large (101MB)
    large_size = 101 * 1024 * 1024
    mock_metadata = {"size": str(large_size), "name": "large.pdf"}
    handler._files_api.get.return_value.execute.return_value = mock_metadata

    with pytest.raises(ValueError, match="too large"):
        handler._validate_file_size("file123")

