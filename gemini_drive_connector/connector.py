"""Main connector that orchestrates Drive and Gemini operations."""

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

        # Initialize Drive client
        with spinner_context("Connecting to Google Drive...", "Connected to Google Drive"):
            if self._drive_client is None:
                self._drive_client = DriveClient()

        # List files
        with spinner_context("Listing files in folder...") as spinner:
            file_handler = DriveFileHandler(self._drive_client.service)
            with PerformanceProfiler("list_files"):
                files = file_handler.list_files(
                    folder_id=folder_id, mime_types=self.config.allowed_mime_types
                )

            if not files:
                spinner.fail(f"No files found in folder {folder_id}")
                logger.warning(f"No files found in folder {folder_id}")
                return

            spinner.succeed(f"Found {len(files)} file(s) to process")

        # Process each file
        for idx, file_info in enumerate(files, 1):
            file_id = file_info["id"]
            name = file_info["name"]
            mime_type = file_info.get("mimeType", "application/octet-stream")

            logger.info(f"Processing file {idx}/{len(files)}: {name} ({mime_type})")

            try:
                self._process_file(file_handler, file_id, name, mime_type)
            except (
                OSError,
                ValueError,
                KeyError,
                AttributeError,
                TimeoutError,
                FileNotFoundError,
                PermissionError,
            ) as e:
                logger.error(f"Error processing {name}: {e}")
                continue
            except Exception as e:
                logger.exception(f"Unexpected error processing {name}: {e}")
                continue

        logger.success(f"Finished syncing {len(files)} file(s) into File Search store")

    def _process_file(
        self, file_handler: DriveFileHandler, file_id: str, name: str, mime_type: str
    ) -> None:
        """Process a single file: download, upload, and index.

        Optimized to minimize memory usage by processing in stages.
        """
        # Download with profiling
        with (
            spinner_context(f"Downloading {name}...", f"Downloaded {name}"),
            PerformanceProfiler(f"download_{name}"),
        ):
            content = file_handler.download_file(file_id)

        # Upload to Gemini with profiling
        with (
            spinner_context(f"Uploading {name} to File Search store...", f"Uploaded {name}"),
            PerformanceProfiler(f"upload_{name}"),
        ):
            uploaded = self._file_store.upload_file(content, name, mime_type)

        # Validate uploaded file name
        uploaded_name = uploaded.name
        if not uploaded_name:
            raise RuntimeError(f"Uploaded file {name} has no name attribute")

        # Index with profiling
        with (
            spinner_context(f"Indexing {name}...", f"Indexed {name}"),
            PerformanceProfiler(f"index_{name}"),
        ):
            self._file_store.import_file(uploaded_name)

        # Explicitly clear content from memory after processing
        del content

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
