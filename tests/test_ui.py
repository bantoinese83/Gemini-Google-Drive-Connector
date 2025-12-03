"""Tests for UI utilities."""

import pytest

from gemini_drive_connector.utils.ui import spinner_context


def test_spinner_context_success() -> None:
    """Test spinner_context with successful operation."""
    with spinner_context("Testing...", "Success!") as spinner:
        assert spinner is not None
        # Spinner should succeed when exiting context


def test_spinner_context_failure() -> None:
    """Test spinner_context with exception."""
    with pytest.raises(ValueError), spinner_context("Testing...") as spinner:
        assert spinner is not None
        raise ValueError("Test error")
            # Spinner should fail when exception is raised

