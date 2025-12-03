"""Error handling utilities for consistent error patterns."""

from collections.abc import Callable
from typing import TypeVar

from loguru import logger  # type: ignore[import-untyped]

T = TypeVar("T")


def handle_api_error(
    operation: str, exc: Exception, error_message: str | None = None
) -> RuntimeError:
    """Create a consistent RuntimeError for API operations.

    Args:
        operation: Name of the operation that failed
        exc: The original exception
        error_message: Optional custom error message

    Returns:
        RuntimeError with consistent formatting
    """
    message = error_message or f"Failed to {operation}"
    logger.error(f"{message}: {exc}")
    result = RuntimeError(f"{message}: {exc}")
    result.__cause__ = exc
    return result


def safe_execute(
    operation: str,
    func: Callable[[], T],
    error_message: str | None = None,
) -> T:
    """Execute a function with consistent error handling.

    Args:
        operation: Name of the operation
        func: Function to execute
        error_message: Optional custom error message

    Returns:
        Result of the function

    Raises:
        RuntimeError: If function execution fails
    """
    try:
        return func()
    except Exception as error:
        raise handle_api_error(operation, error, error_message) from error


def handle_file_error(operation: str, file_name: str, exc: Exception) -> RuntimeError:
    """Create a consistent RuntimeError for file operations.

    Args:
        operation: Name of the file operation
        file_name: Name of the file
        exc: The original exception

    Returns:
        RuntimeError with consistent formatting
    """
    message = f"Failed to {operation} file: {file_name}"
    logger.error(f"{message}: {exc}")
    result = RuntimeError(f"{message}: {exc}")
    result.__cause__ = exc
    return result
