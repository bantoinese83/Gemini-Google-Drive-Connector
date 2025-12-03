"""Tests for error handling utilities."""

import pytest

from gemini_drive_connector.utils.errors import (
    handle_api_error,
    handle_file_error,
    safe_execute,
)


def test_handle_api_error() -> None:
    """Test handle_api_error function."""
    original_error = ValueError("Test error")
    result = handle_api_error("test operation", original_error)

    assert isinstance(result, RuntimeError)
    assert "test operation" in str(result)
    assert result.__cause__ is original_error


def test_handle_api_error_with_custom_message() -> None:
    """Test handle_api_error with custom error message."""
    original_error = ValueError("Test error")
    result = handle_api_error("test operation", original_error, "Custom message")

    assert isinstance(result, RuntimeError)
    assert "Custom message" in str(result)
    assert result.__cause__ is original_error


def test_handle_file_error() -> None:
    """Test handle_file_error function."""
    original_error = ValueError("Test error")
    result = handle_file_error("download", "test.txt", original_error)

    assert isinstance(result, RuntimeError)
    assert "download" in str(result)
    assert "test.txt" in str(result)
    assert result.__cause__ is original_error


def test_safe_execute_success() -> None:
    """Test safe_execute with successful execution."""
    def success_func() -> str:
        return "success"

    result = safe_execute("test operation", success_func)
    assert result == "success"


def test_safe_execute_failure() -> None:
    """Test safe_execute with failure."""
    def failing_func() -> str:
        raise ValueError("Test error")

    with pytest.raises(RuntimeError, match="Failed to test operation"):
        safe_execute("test operation", failing_func)


def test_safe_execute_with_custom_error_message() -> None:
    """Test safe_execute with custom error message."""
    def failing_func() -> str:
        raise ValueError("Test error")

    with pytest.raises(RuntimeError, match="Custom error message"):
        safe_execute("test operation", failing_func, "Custom error message")

