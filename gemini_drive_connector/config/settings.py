"""Configuration settings and constants."""

from dataclasses import dataclass

# Constants for edge case handling
MAX_FILE_SIZE_MB = 100  # Maximum file size in MB
MAX_POLL_ATTEMPTS = 60  # Maximum polling attempts (3 minutes at 3s intervals)
POLL_INTERVAL = 3  # Seconds between polling attempts
INITIAL_POLL_INTERVAL = 1  # Initial polling interval for exponential backoff
MAX_POLL_INTERVAL = 10  # Maximum polling interval for exponential backoff

# Performance optimization constants
CHUNK_SIZE = 1024 * 1024  # 1MB chunks for file operations
MAX_CONCURRENT_FILES = 3  # Maximum concurrent file processing
PROFILING_ENABLED = False  # Enable performance profiling (set to True for debugging)


@dataclass
class GeminiDriveConnectorConfig:
    """Configuration for GeminiDriveConnector.

    Attributes:
        api_key: Gemini API key for authentication
        model: Gemini model name to use (default: gemini-2.5-flash)
        file_store_display_name: Display name for the File Search store
        allowed_mime_types: Optional list of MIME types to filter files
    """

    api_key: str
    model: str = "gemini-2.5-flash"
    file_store_display_name: str = "drive-connector-store"
    allowed_mime_types: list[str] | None = None
