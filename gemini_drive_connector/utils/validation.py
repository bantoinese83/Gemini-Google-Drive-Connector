"""Validation utilities for common input checks."""


def validate_not_empty(value: str, field_name: str = "Value") -> None:
    """Validate that a string value is not empty or whitespace-only.

    Args:
        value: String value to validate
        field_name: Name of the field for error message

    Raises:
        ValueError: If value is empty or whitespace-only
    """
    if not value or not value.strip():
        raise ValueError(f"{field_name} cannot be empty")


def validate_file_id(file_id: str) -> None:
    """Validate a Google Drive file ID.

    Args:
        file_id: File ID to validate

    Raises:
        ValueError: If file_id is empty
    """
    validate_not_empty(file_id, "File ID")


def validate_folder_id(folder_id: str) -> None:
    """Validate a Google Drive folder ID.

    Args:
        folder_id: Folder ID to validate

    Raises:
        ValueError: If folder_id is empty
    """
    validate_not_empty(folder_id, "Folder ID")


def validate_api_key(api_key: str) -> None:
    """Validate a Gemini API key.

    Args:
        api_key: API key to validate

    Raises:
        ValueError: If api_key is empty
    """
    validate_not_empty(api_key, "API key")


def validate_prompt(prompt: str) -> None:
    """Validate a query prompt.

    Args:
        prompt: Prompt to validate

    Raises:
        ValueError: If prompt is empty
    """
    validate_not_empty(prompt, "Prompt")
