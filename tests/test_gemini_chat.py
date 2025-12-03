"""Tests for Gemini chat operations."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from gemini_drive_connector.gemini.chat import GeminiChat


def test_gemini_chat_initialization() -> None:
    """Test GeminiChat initialization."""
    mock_client = MagicMock()
    mock_chat = MagicMock()

    with patch.object(GeminiChat, "_create_chat", return_value=mock_chat):
        chat = GeminiChat(mock_client, "gemini-2.5-flash", "store-name")
        assert chat.client is mock_client
        assert chat.model == "gemini-2.5-flash"
        assert chat._chat is mock_chat


def test_gemini_chat_ask_validation() -> None:
    """Test ask method input validation."""
    mock_client = MagicMock()
    mock_chat = MagicMock()

    with patch.object(GeminiChat, "_create_chat", return_value=mock_chat):
        chat = GeminiChat(mock_client, "gemini-2.5-flash", "store-name")

        # Empty prompt should raise ValueError
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            chat.ask("")

        # Whitespace-only prompt should raise ValueError
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            chat.ask("   ")


def test_gemini_chat_ask_success() -> None:
    """Test ask method with successful response."""
    mock_client = MagicMock()
    mock_chat = MagicMock()
    mock_response = Mock()
    mock_response.text = "This is the answer"

    with patch.object(GeminiChat, "_create_chat", return_value=mock_chat):
        chat = GeminiChat(mock_client, "gemini-2.5-flash", "store-name")
        mock_chat.send_message.return_value = mock_response

        answer = chat.ask("What is the answer?")
        assert answer == "This is the answer"
        mock_chat.send_message.assert_called_once_with("What is the answer?")


def test_gemini_chat_ask_empty_response() -> None:
    """Test ask method with empty response."""
    mock_client = MagicMock()
    mock_chat = MagicMock()
    mock_response = Mock()
    mock_response.text = ""

    with patch.object(GeminiChat, "_create_chat", return_value=mock_chat):
        chat = GeminiChat(mock_client, "gemini-2.5-flash", "store-name")
        mock_chat.send_message.return_value = mock_response

        answer = chat.ask("What is the answer?")
        assert answer == "No response received from Gemini."


def test_gemini_chat_ask_no_text_attribute() -> None:
    """Test ask method when response has no text attribute."""
    mock_client = MagicMock()
    mock_chat = MagicMock()
    mock_response = Mock()
    del mock_response.text  # Remove text attribute

    with patch.object(GeminiChat, "_create_chat", return_value=mock_chat):
        chat = GeminiChat(mock_client, "gemini-2.5-flash", "store-name")
        mock_chat.send_message.return_value = mock_response

        answer = chat.ask("What is the answer?")
        assert answer == "No response received from Gemini."

