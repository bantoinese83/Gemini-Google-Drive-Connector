"""Main connector that orchestrates Drive and Gemini operations."""

from halo import Halo  # type: ignore[import-untyped]
from loguru import logger  # type: ignore[import-untyped]

from gemini_drive_connector.config.settings import GeminiDriveConnectorConfig
from gemini_drive_connector.drive.client import DriveClient
from gemini_drive_connector.drive.files import DriveFileHandler
from gemini_drive_connector.gemini.chat import GeminiChat
from gemini_drive_connector.gemini.client import GeminiClient
from gemini_drive_connector.gemini.file_store import GeminiFileStore


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
        with Halo(text="Connecting to Google Drive...", spinner="dots") as spinner:
            if self._drive_client is None:
                self._drive_client = DriveClient()
            spinner.succeed("Connected to Google Drive")

        # List files
        with Halo(text="Listing files in folder...", spinner="dots") as spinner:
            file_handler = DriveFileHandler(self._drive_client.service)
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
        """Process a single file: download, upload, and index."""
        # Download
        with Halo(text=f"Downloading {name}...", spinner="dots") as spinner:
            content = file_handler.download_file(file_id)
            spinner.succeed(f"Downloaded {name}")

        # Upload to Gemini
        with Halo(text=f"Uploading {name} to File Search store...", spinner="dots") as spinner:
            uploaded = self._file_store.upload_file(content, name, mime_type)
            spinner.succeed(f"Uploaded {name}")

        # Validate uploaded file name
        uploaded_name = uploaded.name
        if not uploaded_name:
            raise RuntimeError(f"Uploaded file {name} has no name attribute")

        # Index
        with Halo(text=f"Indexing {name}...", spinner="dots") as spinner:
            self._file_store.import_file(uploaded_name)
            spinner.succeed(f"Indexed {name}")

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
