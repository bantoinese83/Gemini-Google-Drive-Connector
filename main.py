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
    config = GeminiDriveConnectorConfig(
        api_key=GEMINI_API_KEY,
        model=GEMINI_MODEL,
        file_store_display_name=FILE_STORE_DISPLAY_NAME,
        allowed_mime_types=DEFAULT_MIME_TYPES,
    )
    return GeminiDriveConnector(config)


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


def _parse_command() -> str:
    """Parse command from command line arguments.

    Returns:
        Command string

    Exits:
        If no command is provided
    """
    if len(sys.argv) < 2:
        logger.error("No command provided")
        print('Usage:\n  python main.py sync\n  python main.py ask "your question here"')
        sys.exit(1)
    return sys.argv[1]


def _parse_question() -> str:
    """Parse question from command line arguments.

    Returns:
        Question string

    Exits:
        If no question is provided or question is empty
    """
    if len(sys.argv) < 3:
        logger.error("No question provided")
        print('Provide a question, e.g. python main.py ask "What are the key risks?"')
        sys.exit(1)

    question = " ".join(sys.argv[2:])
    if not question.strip():
        logger.error("Question is empty")
        print("Error: Question cannot be empty")
        sys.exit(1)

    return question


def _handle_sync_command() -> None:
    """Handle sync command."""
    cmd_sync()


def _handle_ask_command() -> None:
    """Handle ask command."""
    question = _parse_question()
    cmd_ask(question)


def _handle_unknown_command(command: str) -> None:
    """Handle unknown command.

    Args:
        command: Unknown command string
    """
    logger.error(f"Unknown command: {command}")
    print(f"Unknown command: {command}")
    sys.exit(1)


def _route_command(command: str) -> None:
    """Route command to appropriate handler.

    Args:
        command: Command string
    """
    if command == "sync":
        _handle_sync_command()
    elif command == "ask":
        _handle_ask_command()
    else:
        _handle_unknown_command(command)


def _handle_keyboard_interrupt() -> None:
    """Handle keyboard interrupt."""
    logger.warning("Operation interrupted by user")
    print("\nOperation interrupted by user")
    sys.exit(130)  # Standard exit code for SIGINT


def _handle_expected_error(error: Exception) -> None:
    """Handle expected errors.

    Args:
        error: Exception that occurred
    """
    logger.exception("Command failed")
    print(f"Error: {error}")
    sys.exit(1)


def _handle_unexpected_error(error: Exception) -> None:
    """Handle unexpected errors.

    Args:
        error: Exception that occurred
    """
    logger.exception("Unexpected error occurred")
    print(f"Unexpected error: {error}")
    sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    command = _parse_command()

    try:
        _route_command(command)
    except KeyboardInterrupt:
        _handle_keyboard_interrupt()
    except (RuntimeError, FileNotFoundError, ValueError, PermissionError) as error:
        _handle_expected_error(error)
    except Exception as error:
        _handle_unexpected_error(error)


if __name__ == "__main__":
    main()
