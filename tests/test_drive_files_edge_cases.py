"""Edge case tests for Drive file operations."""

from unittest.mock import MagicMock, patch

import pytest

from gemini_drive_connector.drive.files import DriveFileHandler


def test_fetch_all_files_max_pages_reached() -> None:
    """Test fetch_all_files when max pages is reached."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    mock_response = {
        "files": [{"id": "1", "name": "file1.pdf"}],
        "nextPageToken": "token123",
    }

    with patch.object(handler, "_get_max_pages", return_value=2):
        with patch.object(handler, "_fetch_page", return_value=mock_response):
            with patch.object(handler, "_check_page_limit") as mock_check:
                files = handler._fetch_all_files("query")
                # Should stop after max pages
                assert len(files) == 2
                mock_check.assert_called_once_with(2)


def test_download_to_buffer_exceeds_max_chunks() -> None:
    """Test download_to_buffer when max chunks exceeded."""
    mock_service = MagicMock()
    handler = DriveFileHandler(mock_service)

    mock_request = MagicMock()
    mock_downloader = MagicMock()
    mock_downloader.next_chunk.return_value = (None, False)  # Never done

    with patch("gemini_drive_connector.drive.files.MediaIoBaseDownload", return_value=mock_downloader):
        with patch.object(handler, "_get_max_chunks", return_value=5):
            with patch.object(handler, "_download_next_chunk", return_value=False):
                with patch.object(handler, "_validate_chunk_count", side_effect=ValueError("Exceeded")):
                    with pytest.raises(ValueError, match="Exceeded"):
                        handler._download_to_buffer(mock_request)

