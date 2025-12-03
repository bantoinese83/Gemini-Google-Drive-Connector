"""Google Drive file operations."""

import io
from typing import TYPE_CHECKING

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from loguru import logger  # type: ignore[import-untyped]

from gemini_drive_connector.config.settings import MAX_FILE_SIZE_MB
from gemini_drive_connector.utils.validation import validate_file_id, validate_folder_id

if TYPE_CHECKING:
    from googleapiclient.discovery import Resource


class DriveFileHandler:
    """Handles file listing and downloading from Google Drive."""

    def __init__(self, drive_service: "Resource") -> None:
        """Initialize file handler.

        Args:
            drive_service: Authorized Drive service resource
        """
        self.drive_service = drive_service
        self._files_api = drive_service.files()

    def list_files(
        self, folder_id: str, mime_types: list[str] | None = None
    ) -> list[dict[str, str]]:
        """List non-trashed files in a Drive folder.

        Args:
            folder_id: Google Drive folder ID
            mime_types: Optional list of MIME types to filter

        Returns:
            List of file metadata dictionaries

        Raises:
            ValueError: If folder_id is empty
            FileNotFoundError: If folder doesn't exist
            PermissionError: If access is denied
            RuntimeError: If listing fails
        """
        validate_folder_id(folder_id)

        query = self._build_query(folder_id, mime_types)
        return self._fetch_all_files(query)

    def download_file(self, file_id: str) -> bytes:
        """Download file content from Drive.

        Args:
            file_id: Google Drive file ID

        Returns:
            File content as bytes

        Raises:
            ValueError: If file_id is empty or file is too large
            FileNotFoundError: If file doesn't exist
            PermissionError: If access is denied
            RuntimeError: If download fails
        """
        validate_file_id(file_id)

        self._validate_file_size(file_id)
        return self._download_content(file_id)

    def _build_query(self, folder_id: str, mime_types: list[str] | None) -> str:
        """Build Drive API query string efficiently.

        Uses list comprehension and join for optimal string building.
        """
        query_parts: list[str] = [f"'{folder_id}' in parents", "trashed = false"]
        if mime_types:
            # Use list comprehension for better performance than repeated string concatenation
            mime_conditions = [f"mimeType = '{mime_type}'" for mime_type in mime_types]
            mime_query = " or ".join(mime_conditions)
            query_parts.append(f"({mime_query})")
        return " and ".join(query_parts)

    def _fetch_all_files(self, query: str) -> list[dict[str, str]]:
        """Fetch all files matching query with pagination.

        Optimized to pre-allocate list capacity when possible and use efficient list operations.
        """
        files: list[dict[str, str]] = []
        page_token: str | None = None
        page_count = 0

        try:
            while page_count < self._get_max_pages():
                resp = self._fetch_page(query, page_token)
                page_files = self._extract_files_from_response(resp)
                files.extend(page_files)

                page_token = self._get_next_page_token(resp)
                if not page_token:
                    break

                page_count += 1

            self._check_page_limit(page_count)

        except (FileNotFoundError, PermissionError, RuntimeError):
            raise
        except Exception as error:
            logger.error(f"Unexpected error listing files: {error}")
            raise RuntimeError(f"Failed to list files: {error}") from error

        return files

    def _get_max_pages(self) -> int:
        """Get maximum number of pages to fetch."""
        return 100

    def _fetch_page(self, query: str, page_token: str | None) -> dict:
        """Fetch a single page of files.

        Args:
            query: Drive API query string
            page_token: Token for pagination

        Returns:
            API response dictionary
        """
        try:
            return self._files_api.list(
                q=query,  # Drive API query parameter
                spaces="drive",
                fields="nextPageToken, files(id, name, mimeType, size)",
                pageToken=page_token,
            ).execute()
        except HttpError as error:
            self._handle_http_error(error, "list files")
            raise  # Never reached, but satisfies type checker

    def _extract_files_from_response(self, response: dict) -> list[dict[str, str]]:
        """Extract file list from API response.

        Args:
            response: API response dictionary

        Returns:
            List of file metadata dictionaries
        """
        return response.get("files", [])

    def _get_next_page_token(self, response: dict) -> str | None:
        """Extract next page token from API response.

        Args:
            response: API response dictionary

        Returns:
            Next page token or None if no more pages
        """
        return response.get("nextPageToken")

    def _check_page_limit(self, page_count: int) -> None:
        """Check if page limit was reached and log warning if so.

        Args:
            page_count: Number of pages fetched
        """
        max_pages = self._get_max_pages()
        if page_count >= max_pages:
            logger.warning(f"Reached maximum page limit ({max_pages}), some files may be missing")

    def _validate_file_size(self, file_id: str) -> None:
        """Validate file size before download."""
        try:
            file_metadata = self._files_api.get(fileId=file_id, fields="size, name").execute()
            file_size_bytes = int(file_metadata.get("size", 0))
            file_name = file_metadata.get("name", "unknown")

            if file_size_bytes == 0:
                logger.warning(f"File {file_name} is empty")

            file_size_megabytes = file_size_bytes / (1024 * 1024)
            if file_size_megabytes > MAX_FILE_SIZE_MB:
                raise ValueError(
                    f"File {file_name} is too large ({file_size_megabytes:.1f}MB). "
                    f"Maximum size is {MAX_FILE_SIZE_MB}MB"
                )
        except HttpError as error:
            self._handle_http_error(error, "get file metadata")

    def _download_content(self, file_id: str) -> bytes:
        """Download file content with optimized memory usage.

        Uses efficient chunked downloading to minimize memory footprint.
        """
        try:
            request = self._create_download_request(file_id)
            buffer = self._download_to_buffer(request)
            return self._read_buffer_content(buffer)

        except HttpError as error:
            self._handle_http_error(error, "download file")
            raise  # Never reached, but satisfies type checker

    def _create_download_request(self, file_id: str):
        """Create download request for file.

        Args:
            file_id: Google Drive file ID

        Returns:
            Media download request object
        """
        return self._files_api.get_media(fileId=file_id)

    def _download_to_buffer(self, request) -> io.BytesIO:
        """Download file content to buffer in chunks.

        Args:
            request: Media download request object

        Returns:
            BytesIO buffer containing file content
        """
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        max_chunks = self._get_max_chunks()
        chunk_count = 0

        while chunk_count < max_chunks:
            if self._download_next_chunk(downloader):
                break
            chunk_count += 1

        self._validate_chunk_count(chunk_count, max_chunks)
        return buffer

    def _get_max_chunks(self) -> int:
        """Get maximum number of chunks for download."""
        return MAX_FILE_SIZE_MB  # Simplified calculation

    def _download_next_chunk(self, downloader: MediaIoBaseDownload) -> bool:
        """Download next chunk and return True if download is complete.

        Args:
            downloader: Media downloader instance

        Returns:
            True if download is complete, False otherwise
        """
        try:
            _, is_download_complete = downloader.next_chunk()
            return is_download_complete
        except Exception as error:
            logger.error(f"Download chunk failed: {error}")
            raise RuntimeError(f"Failed to download file: {error}") from error

    def _validate_chunk_count(self, chunk_count: int, max_chunks: int) -> None:
        """Validate that chunk count doesn't exceed maximum.

        Args:
            chunk_count: Number of chunks downloaded
            max_chunks: Maximum allowed chunks

        Raises:
            ValueError: If chunk count exceeds maximum
        """
        if chunk_count >= max_chunks:
            raise ValueError("File download exceeded size limit")

    def _read_buffer_content(self, buffer: io.BytesIO) -> bytes:
        """Read content from buffer.

        Args:
            buffer: BytesIO buffer containing file content

        Returns:
            File content as bytes
        """
        buffer.seek(0)
        return buffer.read()

    def _handle_http_error(self, error: HttpError, operation: str) -> None:
        """Handle HTTP errors with appropriate exceptions."""
        if error.resp.status == 404:
            raise FileNotFoundError(f"Resource not found during {operation}") from error
        if error.resp.status == 403:
            raise PermissionError(f"Permission denied during {operation}") from error
        logger.error(f"Drive API error during {operation}: {error}")
        raise RuntimeError(f"Failed to {operation}: {error}") from error
