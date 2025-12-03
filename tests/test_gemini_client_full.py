"""Full workflow tests for Gemini client."""

from unittest.mock import MagicMock, patch


from gemini_drive_connector.gemini.client import GeminiClient


def test_gemini_client_property() -> None:
    """Test client property access."""
    with patch("gemini_drive_connector.gemini.client.genai") as mock_genai:
        mock_client_instance = MagicMock()
        mock_genai.Client.return_value = mock_client_instance

        with patch.object(GeminiClient, "_create_client", return_value=mock_client_instance):
            client = GeminiClient("test-key")
            assert client.client is mock_client_instance


def test_gemini_client_create_success() -> None:
    """Test successful client creation."""
    with patch("gemini_drive_connector.gemini.client.genai") as mock_genai:
        mock_client_instance = MagicMock()
        mock_genai.Client.return_value = mock_client_instance

        with patch("gemini_drive_connector.gemini.client.safe_execute", return_value=mock_client_instance):
            client = GeminiClient("test-key")
            # Client should be created during initialization
            assert client._client is mock_client_instance

