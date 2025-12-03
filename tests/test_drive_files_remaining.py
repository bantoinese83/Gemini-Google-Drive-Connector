"""Tests for remaining Drive files coverage."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from googleapiclient.errors import HttpError

from gemini_drive_connector.drive.files import DriveFileHandler


def test_fetch_page_http_error_handling() -> None:
    """Test _fetch_page HTTP error handling path."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    error = HttpError(Mock(status=404), b"Not Found")
    handler._files_api.list.return_value.execute.side_effect = error

    # Should raise FileNotFoundError after handling
    with pytest.raises(FileNotFoundError):
        handler._fetch_page("query", None)


def test_download_content_http_error() -> None:
    """Test _download_content with HTTP error."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    error = HttpError(Mock(status=403), b"Forbidden")

    with patch.object(handler, "_create_download_request", side_effect=error):
        with pytest.raises(PermissionError):
            handler._download_content("file123")


def test_validate_file_size_http_error() -> None:
    """Test _validate_file_size with HTTP error."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    error = HttpError(Mock(status=404), b"Not Found")
    handler._files_api.get.return_value.execute.side_effect = error

    with pytest.raises(FileNotFoundError):
        handler._validate_file_size("file123")

