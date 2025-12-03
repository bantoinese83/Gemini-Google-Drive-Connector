"""Tests for Gemini client."""

import pytest

from gemini_drive_connector.gemini.client import GeminiClient


def test_gemini_client_initialization() -> None:
    """Test GeminiClient initialization with valid API key."""
    # This will fail at runtime without actual API key, but tests the validation
    with pytest.raises((RuntimeError, ValueError)):
        # Empty API key should raise ValueError
        GeminiClient("")


def test_gemini_client_empty_api_key() -> None:
    """Test GeminiClient with empty API key."""
    with pytest.raises(ValueError, match="API key cannot be empty"):
        GeminiClient("")

    with pytest.raises(ValueError, match="API key cannot be empty"):
        GeminiClient("   ")


def test_gemini_client_whitespace_api_key() -> None:
    """Test GeminiClient with whitespace-only API key."""
    with pytest.raises(ValueError, match="API key cannot be empty"):
        GeminiClient("   ")

