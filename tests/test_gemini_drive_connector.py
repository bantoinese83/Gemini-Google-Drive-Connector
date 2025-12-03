"""Tests for gemini_drive_connector module."""

import pytest

from gemini_drive_connector import GeminiDriveConnector, GeminiDriveConnectorConfig


def test_config_defaults() -> None:
    """Test config default values."""
    config = GeminiDriveConnectorConfig(api_key="test-key")
    assert config.api_key == "test-key"
    assert config.model == "gemini-2.5-flash"
    assert config.file_store_display_name == "drive-connector-store"
    assert config.allowed_mime_types is None


def test_connector_validation() -> None:
    """Test that connector validates API key."""
    # Empty API key should raise ValueError
    config = GeminiDriveConnectorConfig(api_key="")
    with pytest.raises(ValueError, match="API key cannot be empty"):
        GeminiDriveConnector(config)

    # Whitespace-only API key should raise ValueError
    config = GeminiDriveConnectorConfig(api_key="   ")
    with pytest.raises(ValueError, match="API key cannot be empty"):
        GeminiDriveConnector(config)
