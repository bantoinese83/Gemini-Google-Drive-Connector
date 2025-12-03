"""CLI entry point for Gemini Drive Connector.

This module provides command-line interface for syncing Google Drive folders
to Gemini File Search stores and querying them.
"""

import os
import sys

from dotenv import load_dotenv
from loguru import logger  # type: ignore[import-untyped]

from gemini_drive_connector import GeminiDriveConnector, GeminiDriveConnectorConfig

# Configure loguru
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | <level>{message}</level>"
    ),
    level="INFO",
    colorize=True,
)

load_dotenv()

# Default MIME types for common document formats
DEFAULT_MIME_TYPES = [
    "application/vnd.google-apps.document",
    "text/plain",
    "application/pdf",
]

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
FILE_STORE_DISPLAY_NAME = os.getenv("FILE_STORE_DISPLAY_NAME", "drive-connector-store")
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")


def get_connector() -> GeminiDriveConnector:
    """Create and return a configured GeminiDriveConnector instance."""
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not set in environment or .env")
        raise RuntimeError("GEMINI_API_KEY is not set in environment or .env")

    logger.debug(f"Creating connector with model: {GEMINI_MODEL}, store: {FILE_STORE_DISPLAY_NAME}")
    cfg = GeminiDriveConnectorConfig(
        api_key=GEMINI_API_KEY,
        model=GEMINI_MODEL,
        file_store_display_name=FILE_STORE_DISPLAY_NAME,
        allowed_mime_types=DEFAULT_MIME_TYPES,
    )
    return GeminiDriveConnector(cfg)


def cmd_sync() -> None:
    """Sync Google Drive folder to Gemini File Search store."""
    if not DRIVE_FOLDER_ID:
        logger.error("DRIVE_FOLDER_ID is not set in environment or .env")
        raise RuntimeError("DRIVE_FOLDER_ID is not set in environment or .env")

    logger.info(f"Starting sync for folder ID: {DRIVE_FOLDER_ID}")
    connector = get_connector()
    connector.sync_folder_to_store(DRIVE_FOLDER_ID)


def cmd_ask(question: str) -> None:
    """Ask a question over the indexed Drive content."""
    if not question or not question.strip():
        logger.error("Question cannot be empty")
        raise ValueError("Question cannot be empty")

    connector = get_connector()
    answer = connector.ask(question)
    logger.info("Answer received")
    print(answer)


def main() -> None:
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        logger.error("No command provided")
        print('Usage:\n  python main.py sync\n  python main.py ask "your question here"')
        sys.exit(1)

    cmd = sys.argv[1]

    try:
        if cmd == "sync":
            cmd_sync()
        elif cmd == "ask":
            if len(sys.argv) < 3:
                logger.error("No question provided")
                print('Provide a question, e.g. python main.py ask "What are the key risks?"')
                sys.exit(1)
            question = " ".join(sys.argv[2:])
            if not question.strip():
                logger.error("Question is empty")
                print("Error: Question cannot be empty")
                sys.exit(1)
            cmd_ask(question)
        else:
            logger.error(f"Unknown command: {cmd}")
            print(f"Unknown command: {cmd}")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("Operation interrupted by user")
        print("\nOperation interrupted by user")
        sys.exit(130)  # Standard exit code for SIGINT
    except (RuntimeError, FileNotFoundError, ValueError, PermissionError) as e:
        logger.exception("Command failed")
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error occurred")
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
