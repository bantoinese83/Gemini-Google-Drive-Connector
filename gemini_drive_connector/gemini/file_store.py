"""Gemini File Search store operations."""

import time
from typing import TYPE_CHECKING

from loguru import logger  # type: ignore[import-untyped]

from gemini_drive_connector.config.settings import (
    INITIAL_POLL_INTERVAL,
    MAX_POLL_ATTEMPTS,
    MAX_POLL_INTERVAL,
    POLL_INTERVAL,
)
from gemini_drive_connector.utils.errors import handle_api_error, safe_execute

if TYPE_CHECKING:
    from google import genai


class GeminiFileStore:
    """Manages Gemini File Search store operations."""

    def __init__(self, client: "genai.Client", display_name: str) -> None:
        """Initialize file store.

        Args:
            client: Gemini client instance
            display_name: Display name for the file store

        Raises:
            RuntimeError: If store creation fails
        """
        self.client = client
        self.display_name = display_name
        self._store = self._create_store()

    @property
    def store(self) -> "genai.types.FileSearchStore":
        """Get file search store instance."""
        return self._store

    @property
    def name(self) -> str:
        """Get store name."""
        store_name = self._store.name
        if not store_name:
            raise RuntimeError("File search store name is not available")
        return store_name

    def _create_store(self) -> "genai.types.FileSearchStore":
        """Create a new File Search store."""
        store = safe_execute(
            "create file search store",
            lambda: self.client.file_search_stores.create(
                config={"display_name": self.display_name}
            ),
            "Failed to create file search store",
        )
        logger.debug(f"Created file search store: {store.name}")
        return store

    def upload_file(self, content: bytes, display_name: str, mime_type: str) -> "genai.types.File":
        """Upload a file to Gemini with optimized memory handling.

        Uses BytesIO for efficient memory management during upload.

        Args:
            content: File content as bytes
            display_name: Display name for the file
            mime_type: MIME type of the file

        Returns:
            Uploaded file object
        """
        # Convert bytes to BytesIO for type compatibility and memory efficiency
        import io

        # BytesIO is more memory-efficient than keeping raw bytes for large files
        file_obj = io.BytesIO(content)
        # Reset position to start of stream
        file_obj.seek(0)
        return self.client.files.upload(
            file=file_obj,  # type: ignore[arg-type]
            config={"display_name": display_name, "mime_type": mime_type},
        )

    def import_file(self, file_name: str) -> None:
        """Import a file into the File Search store.

        Args:
            file_name: Name of the uploaded file to import

        Raises:
            RuntimeError: If import fails
            TimeoutError: If import operation times out
        """
        op = safe_execute(
            f"start importing file {file_name}",
            lambda: self.client.file_search_stores.import_file(
                file_search_store_name=self.name,
                file_name=file_name,
            ),
            f"Failed to start importing file {file_name}",
        )

        self._wait_for_operation(op, file_name)

    def _wait_for_operation(self, operation: "genai.types.Operation", file_name: str) -> None:
        """Wait for import operation to complete with exponential backoff.

        Uses exponential backoff to reduce API calls and improve efficiency.
        Starts with shorter intervals and increases gradually.

        Args:
            operation: Operation object to monitor
            file_name: Name of file being imported (for error messages)

        Raises:
            TimeoutError: If operation times out
            RuntimeError: If operation fails
        """
        poll_attempts = 0
        current_interval = INITIAL_POLL_INTERVAL

        while not operation.done and poll_attempts < MAX_POLL_ATTEMPTS:
            time.sleep(current_interval)
            operation = self._poll_operation_status(operation)
            poll_attempts += 1
            current_interval = self._calculate_next_poll_interval(poll_attempts, current_interval)

        self._validate_operation_completion(operation, file_name)

    def _poll_operation_status(self, operation: "genai.types.Operation") -> "genai.types.Operation":
        """Poll for operation status update.

        Args:
            operation: Current operation object

        Returns:
            Updated operation object
        """
        try:
            return self.client.operations.get(operation)
        except Exception as e:
            raise handle_api_error("check operation status", e, "Operation polling failed") from e

    def _calculate_next_poll_interval(self, poll_attempts: int, current_interval: float) -> float:
        """Calculate next polling interval with exponential backoff.

        Args:
            poll_attempts: Number of polling attempts made
            current_interval: Current polling interval in seconds

        Returns:
            Next polling interval in seconds
        """
        if poll_attempts > 3:  # Start backoff after initial quick checks
            return min(current_interval * 1.5, MAX_POLL_INTERVAL)  # 1.5x multiplier, capped
        return current_interval

    def _validate_operation_completion(
        self, operation: "genai.types.Operation", file_name: str
    ) -> None:
        """Validate that operation completed successfully.

        Args:
            operation: Operation object to validate
            file_name: Name of file being imported (for error messages)

        Raises:
            TimeoutError: If operation timed out
            RuntimeError: If operation failed
        """
        if not operation.done:
            timeout_seconds = MAX_POLL_ATTEMPTS * POLL_INTERVAL
            raise TimeoutError(
                f"Indexing operation for {file_name} timed out after {timeout_seconds} seconds"
            )

        if hasattr(operation, "error") and operation.error:
            raise RuntimeError(f"Indexing operation failed for {file_name}: {operation.error}")
