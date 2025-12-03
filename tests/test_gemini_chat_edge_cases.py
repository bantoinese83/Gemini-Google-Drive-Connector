"""Edge case tests for Gemini chat."""

from unittest.mock import MagicMock, patch

import pytest

from gemini_drive_connector.gemini.chat import GeminiChat


def test_gemini_chat_ask_api_error() -> None:
    """Test ask method with API error."""
    mock_client = MagicMock()
    mock_chat = MagicMock()
    mock_chat.send_message.side_effect = Exception("API Error")

    with patch.object(GeminiChat, "_create_chat", return_value=mock_chat):
        chat = GeminiChat(mock_client, "gemini-2.5-flash", "store-name")

        with pytest.raises(RuntimeError, match="Failed to query Gemini"):
            chat.ask("What is the answer?")


def test_gemini_chat_do_create_chat() -> None:
    """Test _do_create_chat internal method."""
    mock_client = MagicMock()
    mock_chat = MagicMock()
    mock_client.chats.create.return_value = mock_chat

    with patch.object(GeminiChat, "_create_chat", return_value=mock_chat):
        chat = GeminiChat(mock_client, "gemini-2.5-flash", "store-name")

        result = chat._do_create_chat("store-name")
        assert result is mock_chat
        mock_client.chats.create.assert_called_once()

