"""Tests for Drive file operations."""

from unittest.mock import MagicMock, Mock

import pytest
from googleapiclient.errors import HttpError

from gemini_drive_connector.drive.files import DriveFileHandler


def test_drive_file_handler_initialization() -> None:
    """Test DriveFileHandler initialization."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)
    assert handler.drive_service is mock_service
    assert handler._files_api is not None


def test_build_query() -> None:
    """Test query building."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    # Test query with folder ID only
    query = handler._build_query("folder123", None)
    assert "folder123" in query
    assert "trashed = false" in query

    # Test query with MIME types
    query = handler._build_query("folder123", ["application/pdf", "text/plain"])
    assert "folder123" in query
    assert "application/pdf" in query
    assert "text/plain" in query
    assert "mimeType" in query


def test_extract_files_from_response() -> None:
    """Test file extraction from API response."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    response = {"files": [{"id": "1", "name": "test.pdf"}]}
    files = handler._extract_files_from_response(response)
    assert len(files) == 1
    assert files[0]["id"] == "1"

    # Test empty response
    empty_response = {"files": []}
    files = handler._extract_files_from_response(empty_response)
    assert len(files) == 0

    # Test missing files key
    no_files_response = {}
    files = handler._extract_files_from_response(no_files_response)
    assert len(files) == 0


def test_get_next_page_token() -> None:
    """Test next page token extraction."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    # Response with next page token
    response = {"nextPageToken": "token123"}
    token = handler._get_next_page_token(response)
    assert token == "token123"

    # Response without next page token
    response_no_token = {}
    token = handler._get_next_page_token(response_no_token)
    assert token is None


def test_get_max_pages() -> None:
    """Test max pages getter."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)
    assert handler._get_max_pages() == 100


def test_get_max_chunks() -> None:
    """Test max chunks getter."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)
    # Should return MAX_FILE_SIZE_MB
    max_chunks = handler._get_max_chunks()
    assert max_chunks > 0


def test_validate_chunk_count() -> None:
    """Test chunk count validation."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    # Valid chunk count
    handler._validate_chunk_count(5, 10)

    # Invalid chunk count (exceeds max)
    with pytest.raises(ValueError, match="File download exceeded size limit"):
        handler._validate_chunk_count(10, 10)


def test_list_files_validation() -> None:
    """Test list_files input validation."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    # Empty folder ID should raise ValueError
    with pytest.raises(ValueError, match="Folder ID cannot be empty"):
        handler.list_files("", None)


def test_download_file_validation() -> None:
    """Test download_file input validation."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    # Empty file ID should raise ValueError
    with pytest.raises(ValueError, match="File ID cannot be empty"):
        handler.download_file("")


def test_handle_http_error_404() -> None:
    """Test HTTP error handling for 404."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    error = HttpError(Mock(status=404), b"Not Found")
    with pytest.raises(FileNotFoundError, match="Resource not found"):
        handler._handle_http_error(error, "test operation")


def test_handle_http_error_403() -> None:
    """Test HTTP error handling for 403."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    error = HttpError(Mock(status=403), b"Forbidden")
    with pytest.raises(PermissionError, match="Permission denied"):
        handler._handle_http_error(error, "test operation")


def test_handle_http_error_generic() -> None:
    """Test HTTP error handling for generic errors."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    error = HttpError(Mock(status=500), b"Internal Server Error")
    with pytest.raises(RuntimeError, match="Failed to test operation"):
        handler._handle_http_error(error, "test operation")

