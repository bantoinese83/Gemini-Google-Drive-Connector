"""Tests for validation utilities."""

import pytest

from gemini_drive_connector.utils.validation import (
    validate_api_key,
    validate_file_id,
    validate_folder_id,
    validate_not_empty,
    validate_prompt,
)


def test_validate_not_empty() -> None:
    """Test validate_not_empty function."""
    # Valid non-empty string
    validate_not_empty("test", "Value")

    # Empty string should raise ValueError
    with pytest.raises(ValueError, match="Value cannot be empty"):
        validate_not_empty("", "Value")

    # Whitespace-only string should raise ValueError
    with pytest.raises(ValueError, match="Value cannot be empty"):
        validate_not_empty("   ", "Value")


def test_validate_api_key() -> None:
    """Test validate_api_key function."""
    # Valid API key
    validate_api_key("test-key-123")

    # Empty API key should raise ValueError
    with pytest.raises(ValueError, match="API key cannot be empty"):
        validate_api_key("")

    # Whitespace-only API key should raise ValueError
    with pytest.raises(ValueError, match="API key cannot be empty"):
        validate_api_key("   ")


def test_validate_file_id() -> None:
    """Test validate_file_id function."""
    # Valid file ID
    validate_file_id("file123")

    # Empty file ID should raise ValueError
    with pytest.raises(ValueError, match="File ID cannot be empty"):
        validate_file_id("")


def test_validate_folder_id() -> None:
    """Test validate_folder_id function."""
    # Valid folder ID
    validate_folder_id("folder123")

    # Empty folder ID should raise ValueError
    with pytest.raises(ValueError, match="Folder ID cannot be empty"):
        validate_folder_id("")


def test_validate_prompt() -> None:
    """Test validate_prompt function."""
    # Valid prompt
    validate_prompt("What is the meaning of life?")

    # Empty prompt should raise ValueError
    with pytest.raises(ValueError, match="Prompt cannot be empty"):
        validate_prompt("")

    # Whitespace-only prompt should raise ValueError
    with pytest.raises(ValueError, match="Prompt cannot be empty"):
        validate_prompt("   ")

