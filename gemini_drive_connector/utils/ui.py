"""UI utilities for consistent user feedback."""

from collections.abc import Iterator
from contextlib import contextmanager

from halo import Halo  # type: ignore[import-untyped]


@contextmanager
def spinner_context(text: str, success_text: str | None = None) -> Iterator[Halo]:
    """Context manager for spinner operations with consistent success message.

    Args:
        text: Text to display while spinning
        success_text: Text to display on success (defaults to text with checkmark)

    Yields:
        Halo spinner instance
    """
    spinner = Halo(text=text, spinner="dots")
    spinner.start()
    try:
        yield spinner
        spinner.succeed(success_text or text)
    except Exception:
        spinner.fail()
        raise
