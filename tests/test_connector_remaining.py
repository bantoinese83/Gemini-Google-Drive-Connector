"""Tests for remaining connector coverage."""

from unittest.mock import MagicMock, patch


from gemini_drive_connector import GeminiDriveConnector, GeminiDriveConnectorConfig


def test_connector_profiling_enabled_import() -> None:
    """Test connector with profiling enabled (imports PerformanceProfiler)."""
    config = GeminiDriveConnectorConfig(api_key="test-key")

    # This tests the PROFILING_ENABLED=True branch
    with patch("gemini_drive_connector.connector.PROFILING_ENABLED", True):
        with patch("gemini_drive_connector.connector.GeminiClient"):
            with patch("gemini_drive_connector.connector.GeminiFileStore"):
                with patch("gemini_drive_connector.connector.GeminiChat"):
                    # Import PerformanceProfiler when enabled
                    with patch("gemini_drive_connector.connector.PerformanceProfiler"):
                        connector = GeminiDriveConnector(config)
                        assert connector.config is config


def test_process_file_safely_unexpected_error() -> None:
    """Test process_file_safely with unexpected error."""
    config = GeminiDriveConnectorConfig(api_key="test-key")

    with patch("gemini_drive_connector.connector.GeminiClient"):
        with patch("gemini_drive_connector.connector.GeminiFileStore"):
            with patch("gemini_drive_connector.connector.GeminiChat"):
                connector = GeminiDriveConnector(config)

                mock_file_handler = MagicMock()

                # Test with unexpected error (not in expected list)
                with patch.object(connector, "_process_file", side_effect=TypeError("Unexpected")):
                    # Should not raise, but log exception
                    connector._process_file_safely(mock_file_handler, "file123", "test.pdf", "application/pdf")

