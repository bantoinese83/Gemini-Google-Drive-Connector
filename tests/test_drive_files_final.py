"""Final tests for Drive files to reach 100% coverage."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from googleapiclient.errors import HttpError

from gemini_drive_connector.drive.files import DriveFileHandler


def test_fetch_page_never_reached_raise() -> None:
    """Test _fetch_page raise statement (never reached but satisfies type checker)."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    error = HttpError(Mock(status=404), b"Not Found")
    handler._files_api.list.return_value.execute.side_effect = error

    # The raise statement after _handle_http_error is never reached
    # but we can test the path by ensuring _handle_http_error is called
    with pytest.raises(FileNotFoundError):
        handler._fetch_page("query", None)


def test_download_content_never_reached_raise() -> None:
    """Test _download_content raise statement (never reached but satisfies type checker)."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    error = HttpError(Mock(status=403), b"Forbidden")

    with patch.object(handler, "_create_download_request", side_effect=error):
        # The raise statement after _handle_http_error is never reached
        with pytest.raises(PermissionError):
            handler._download_content("file123")


def test_create_download_request() -> None:
    """Test _create_download_request method."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    mock_request = MagicMock()
    handler._files_api.get_media.return_value = mock_request

    result = handler._create_download_request("file123")
    assert result is mock_request
    handler._files_api.get_media.assert_called_once_with(fileId="file123")

