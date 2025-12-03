"""Main connector that orchestrates Drive and Gemini operations."""

from typing import TYPE_CHECKING

from loguru import logger  # type: ignore[import-untyped]

from gemini_drive_connector.config.settings import (
    PROFILING_ENABLED,
    GeminiDriveConnectorConfig,
)
from gemini_drive_connector.drive.client import DriveClient
from gemini_drive_connector.drive.files import DriveFileHandler
from gemini_drive_connector.gemini.chat import GeminiChat
from gemini_drive_connector.gemini.client import GeminiClient
from gemini_drive_connector.gemini.file_store import GeminiFileStore
from gemini_drive_connector.utils.ui import spinner_context

if TYPE_CHECKING:
    from google import genai

# Conditionally import profiling utilities
if PROFILING_ENABLED:
    from gemini_drive_connector.utils.profiling import PerformanceProfiler
else:
    # Dummy context manager if profiling disabled
    from contextlib import nullcontext

    PerformanceProfiler = nullcontext  # type: ignore[assignment,misc]


class GeminiDriveConnector:
    """
    Connector that:
      - Reads files from a Drive folder
      - Loads them into a Gemini File Search store
      - Exposes a simple ask() API for chat over those files

    To create another knowledge base, instantiate with a new config and sync a
    different Drive folder.
    """

    def __init__(self, config: GeminiDriveConnectorConfig) -> None:
        """Initialize connector.

        Args:
            config: Configuration for the connector

        Raises:
            ValueError: If API key is empty
            RuntimeError: If initialization fails
        """
        self.config = config

        # Initialize Gemini components
        self._gemini_client = GeminiClient(config.api_key)
        self._file_store = GeminiFileStore(
            self._gemini_client.client, config.file_store_display_name
        )
        self._chat = GeminiChat(self._gemini_client.client, config.model, self._file_store.name)

        # Drive components will be initialized on demand
        self._drive_client: DriveClient | None = None

    def sync_folder_to_store(self, folder_id: str) -> None:
        """Load all files from a Drive folder into this File Search store.

        Args:
            folder_id: Google Drive folder ID to sync

        Raises:
            ValueError: If folder_id is empty
            FileNotFoundError: If folder doesn't exist
            PermissionError: If access is denied
            RuntimeError: If sync fails
        """
        logger.info(f"Starting sync for folder: {folder_id}")

        self._ensure_drive_client_initialized()
        file_handler = self._create_file_handler()
        files = self._list_files_in_folder(folder_id, file_handler)

        if not files:
            return

        self._process_all_files(files, file_handler)
        logger.success(f"Finished syncing {len(files)} file(s) into File Search store")

    def _ensure_drive_client_initialized(self) -> None:
        """Initialize Drive client if not already initialized."""
        with spinner_context("Connecting to Google Drive...", "Connected to Google Drive"):
            if self._drive_client is None:
                self._drive_client = DriveClient()

    def _create_file_handler(self) -> DriveFileHandler:
        """Create and return a DriveFileHandler instance.

        Returns:
            DriveFileHandler instance

        Raises:
            RuntimeError: If Drive client is not initialized
        """
        if self._drive_client is None:
            raise RuntimeError("Drive client must be initialized before creating file handler")
        return DriveFileHandler(self._drive_client.service)

    def _list_files_in_folder(
        self, folder_id: str, file_handler: DriveFileHandler
    ) -> list[dict[str, str]]:
        """List files in the specified folder.

        Args:
            folder_id: Google Drive folder ID
            file_handler: DriveFileHandler instance

        Returns:
            List of file metadata dictionaries
        """
        with spinner_context("Listing files in folder...") as spinner:
            with PerformanceProfiler("list_files"):
                files = file_handler.list_files(
                    folder_id=folder_id, mime_types=self.config.allowed_mime_types
                )

            if not files:
                spinner.fail(f"No files found in folder {folder_id}")
                logger.warning(f"No files found in folder {folder_id}")
                return []

            spinner.succeed(f"Found {len(files)} file(s) to process")
            return files

    def _process_all_files(
        self, files: list[dict[str, str]], file_handler: DriveFileHandler
    ) -> None:
        """Process all files in the list.

        Args:
            files: List of file metadata dictionaries
            file_handler: DriveFileHandler instance
        """
        for file_index, file_info in enumerate(files, 1):
            file_id = file_info["id"]
            file_name = file_info["name"]
            mime_type = file_info.get("mimeType", "application/octet-stream")

            logger.info(f"Processing file {file_index}/{len(files)}: {file_name} ({mime_type})")

            self._process_file_safely(file_handler, file_id, file_name, mime_type)

    def _process_file_safely(
        self,
        file_handler: DriveFileHandler,
        file_id: str,
        file_name: str,
        mime_type: str,
    ) -> None:
        """Process a file with error handling.

        Args:
            file_handler: DriveFileHandler instance
            file_id: Google Drive file ID
            file_name: File name
            mime_type: File MIME type
        """
        try:
            self._process_file(file_handler, file_id, file_name, mime_type)
        except (
            OSError,
            ValueError,
            KeyError,
            AttributeError,
            TimeoutError,
            FileNotFoundError,
            PermissionError,
        ) as error:
            logger.error(f"Error processing {file_name}: {error}")
        except Exception as error:
            logger.exception(f"Unexpected error processing {file_name}: {error}")

    def _process_file(
        self,
        file_handler: DriveFileHandler,
        file_id: str,
        file_name: str,
        mime_type: str,
    ) -> None:
        """Process a single file: download, upload, and index.

        Optimized to minimize memory usage by processing in stages.
        """
        file_content = self._download_file(file_handler, file_id, file_name)
        uploaded_file = self._upload_file_to_store(file_content, file_name, mime_type)
        uploaded_file_name = self._validate_uploaded_file_name(uploaded_file, file_name)
        self._index_file(uploaded_file_name, file_name)

        # Explicitly clear content from memory after processing
        del file_content

    def _download_file(self, file_handler: DriveFileHandler, file_id: str, file_name: str) -> bytes:
        """Download file from Drive.

        Args:
            file_handler: DriveFileHandler instance
            file_id: Google Drive file ID
            file_name: File name for logging

        Returns:
            File content as bytes
        """
        with (
            spinner_context(f"Downloading {file_name}...", f"Downloaded {file_name}"),
            PerformanceProfiler(f"download_{file_name}"),
        ):
            return file_handler.download_file(file_id)

    def _upload_file_to_store(
        self, file_content: bytes, file_name: str, mime_type: str
    ) -> "genai.types.File":
        """Upload file to Gemini File Search store.

        Args:
            file_content: File content as bytes
            file_name: File name
            mime_type: File MIME type

        Returns:
            Uploaded file object
        """
        with (
            spinner_context(
                f"Uploading {file_name} to File Search store...", f"Uploaded {file_name}"
            ),
            PerformanceProfiler(f"upload_{file_name}"),
        ):
            return self._file_store.upload_file(file_content, file_name, mime_type)

    def _validate_uploaded_file_name(self, uploaded: "genai.types.File", original_name: str) -> str:
        """Validate and extract uploaded file name.

        Args:
            uploaded: Uploaded file object
            original_name: Original file name for error messages

        Returns:
            Uploaded file name

        Raises:
            RuntimeError: If uploaded file has no name attribute
        """
        uploaded_name = uploaded.name
        if not uploaded_name:
            raise RuntimeError(f"Uploaded file {original_name} has no name attribute")
        return uploaded_name

    def _index_file(self, file_name: str, display_name: str) -> None:
        """Index file in File Search store.

        Args:
            file_name: Name of uploaded file to index
            display_name: Display name for logging
        """
        with (
            spinner_context(f"Indexing {display_name}...", f"Indexed {display_name}"),
            PerformanceProfiler(f"index_{display_name}"),
        ):
            self._file_store.import_file(file_name)

    def ask(self, prompt: str) -> str:
        """Ask a question over the indexed Drive content.

        Args:
            prompt: Question to ask

        Returns:
            Answer from Gemini

        Raises:
            ValueError: If prompt is empty
            RuntimeError: If query fails
        """
        return self._chat.ask(prompt)
