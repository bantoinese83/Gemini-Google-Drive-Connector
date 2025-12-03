"""Tests for remaining Gemini chat coverage."""

from unittest.mock import MagicMock, patch


from gemini_drive_connector.gemini.chat import GeminiChat


def test_gemini_chat_create_chat_internal() -> None:
    """Test _create_chat method."""
    mock_client = MagicMock()
    mock_chat = MagicMock()

    with patch.object(GeminiChat, "_do_create_chat", return_value=mock_chat):
        with patch("gemini_drive_connector.gemini.chat.safe_execute", return_value=mock_chat):
            # Create instance without calling _create_chat in __init__
            chat = GeminiChat.__new__(GeminiChat)
            chat.client = mock_client
            chat.model = "gemini-2.5-flash"

            result = chat._create_chat("store-name")
            assert result is mock_chat

