"""Edge case tests for connector."""

from unittest.mock import patch


from gemini_drive_connector import GeminiDriveConnector, GeminiDriveConnectorConfig


def test_connector_profiling_disabled_path() -> None:
    """Test connector with profiling disabled."""
    config = GeminiDriveConnectorConfig(api_key="test-key")

    with patch("gemini_drive_connector.connector.PROFILING_ENABLED", False):
        with patch("gemini_drive_connector.connector.GeminiClient"):
            with patch("gemini_drive_connector.connector.GeminiFileStore"):
                with patch("gemini_drive_connector.connector.GeminiChat"):
                    connector = GeminiDriveConnector(config)
                    # Should use nullcontext instead of PerformanceProfiler
                    assert connector.config is config

