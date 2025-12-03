"""Tests for remaining Gemini client coverage."""

from unittest.mock import MagicMock, patch


from gemini_drive_connector.gemini.client import GeminiClient


def test_gemini_client_create_client_success() -> None:
    """Test _create_client method."""
    with patch("gemini_drive_connector.gemini.client.genai") as mock_genai:
        mock_client_instance = MagicMock()
        mock_genai.Client.return_value = mock_client_instance

        with patch("gemini_drive_connector.gemini.client.safe_execute", return_value=mock_client_instance):
            client = GeminiClient("test-key")
            # Client should be created
            assert client._client is mock_client_instance


def test_gemini_client_do_create_client() -> None:
    """Test _do_create_client internal method."""
    with patch("gemini_drive_connector.gemini.client.genai") as mock_genai:
        mock_client_instance = MagicMock()
        mock_genai.Client.return_value = mock_client_instance

        client = GeminiClient.__new__(GeminiClient)
        client.api_key = "test-key"

        result = client._do_create_client()
        assert result is mock_client_instance
        mock_genai.Client.assert_called_once_with(api_key="test-key")

