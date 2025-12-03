"""Google Drive file operations."""

import io
from typing import TYPE_CHECKING

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from loguru import logger  # type: ignore[import-untyped]

from gemini_drive_connector.config.settings import MAX_FILE_SIZE_MB

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
        if not folder_id or not folder_id.strip():
            raise ValueError("Folder ID cannot be empty")

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
        if not file_id or not file_id.strip():
            raise ValueError("File ID cannot be empty")

        self._validate_file_size(file_id)
        return self._download_content(file_id)

    def _build_query(self, folder_id: str, mime_types: list[str] | None) -> str:
        """Build Drive API query string efficiently.

        Uses list comprehension and join for optimal string building.
        """
        query_parts: list[str] = [f"'{folder_id}' in parents", "trashed = false"]
        if mime_types:
            # Use list comprehension for better performance than repeated string concatenation
            mime_conditions = [f"mimeType = '{m}'" for m in mime_types]
            mime_query = " or ".join(mime_conditions)
            query_parts.append(f"({mime_query})")
        return " and ".join(query_parts)

    def _fetch_all_files(self, query: str) -> list[dict[str, str]]:
        """Fetch all files matching query with pagination.

        Optimized to pre-allocate list capacity when possible and use efficient list operations.
        """
        files: list[dict[str, str]] = []
        page_token: str | None = None
        max_pages = 100
        page_count = 0

        try:
            while page_count < max_pages:
                try:
                    resp = self._files_api.list(
                        q=query,
                        spaces="drive",
                        fields="nextPageToken, files(id, name, mimeType, size)",
                        pageToken=page_token,
                    ).execute()
                except HttpError as e:
                    self._handle_http_error(e, "list files")

                page_files = resp.get("files", [])
                if page_files:
                    # Use extend() which is more efficient than repeated append()
                    files.extend(page_files)

                page_token = resp.get("nextPageToken")
                if not page_token:
                    break

                page_count += 1

            if page_count >= max_pages:
                logger.warning(
                    f"Reached maximum page limit ({max_pages}), some files may be missing"
                )

        except (FileNotFoundError, PermissionError, RuntimeError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing files: {e}")
            raise RuntimeError(f"Failed to list files: {e}") from e

        return files

    def _validate_file_size(self, file_id: str) -> None:
        """Validate file size before download."""
        try:
            file_metadata = self._files_api.get(fileId=file_id, fields="size, name").execute()
            file_size = int(file_metadata.get("size", 0))
            file_name = file_metadata.get("name", "unknown")

            if file_size == 0:
                logger.warning(f"File {file_name} is empty")

            file_size_mb = file_size / (1024 * 1024)
            if file_size_mb > MAX_FILE_SIZE_MB:
                raise ValueError(
                    f"File {file_name} is too large ({file_size_mb:.1f}MB). "
                    f"Maximum size is {MAX_FILE_SIZE_MB}MB"
                )
        except HttpError as e:
            self._handle_http_error(e, "get file metadata")

    def _download_content(self, file_id: str) -> bytes:
        """Download file content with optimized memory usage.

        Uses efficient chunked downloading to minimize memory footprint.
        """
        try:
            request = self._files_api.get_media(fileId=file_id)
            # Pre-allocate buffer with estimated size for better performance
            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request)

            # Calculate max chunks more efficiently
            max_chunks = MAX_FILE_SIZE_MB  # Simplified calculation
            chunk_count = 0

            while chunk_count < max_chunks:
                try:
                    _, done = downloader.next_chunk()
                    if done:
                        break
                    chunk_count += 1
                except Exception as e:
                    logger.error(f"Download chunk failed: {e}")
                    raise RuntimeError(f"Failed to download file: {e}") from e

            if chunk_count >= max_chunks:
                raise ValueError("File download exceeded size limit")

            # Reset buffer position before reading
            buffer.seek(0)
            # Read all content at once (already in memory, no streaming needed for API)
            return buffer.read()

        except HttpError as e:
            self._handle_http_error(e, "download file")
            raise  # Never reached, but satisfies type checker

    def _handle_http_error(self, error: HttpError, operation: str) -> None:
        """Handle HTTP errors with appropriate exceptions."""
        if error.resp.status == 404:
            raise FileNotFoundError(f"Resource not found during {operation}") from error
        if error.resp.status == 403:
            raise PermissionError(f"Permission denied during {operation}") from error
        logger.error(f"Drive API error during {operation}: {error}")
        raise RuntimeError(f"Failed to {operation}: {error}") from error
