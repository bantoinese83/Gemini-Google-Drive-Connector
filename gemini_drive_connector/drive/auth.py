"""Google Drive authentication and service setup."""

import contextlib
import json
import os
from typing import TYPE_CHECKING

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from loguru import logger  # type: ignore[import-untyped]

from gemini_drive_connector.utils.errors import safe_execute

if TYPE_CHECKING:
    from googleapiclient.discovery import Resource

DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
TOKEN_PATH = "token.json"
CREDENTIALS_PATH = "credentials.json"


class DriveAuth:
    """Handles Google Drive authentication and service creation."""

    def __init__(
        self, token_path: str = TOKEN_PATH, credentials_path: str = CREDENTIALS_PATH
    ) -> None:
        """Initialize Drive authentication.

        Args:
            token_path: Path to store OAuth token
            credentials_path: Path to OAuth credentials file
        """
        self.token_path = token_path
        self.credentials_path = credentials_path

    def get_service(self) -> "Resource":
        """Get authorized Google Drive v3 service.

        Returns:
            Authorized Drive service resource

        Raises:
            FileNotFoundError: If credentials file is missing
            ValueError: If credentials file is invalid
            RuntimeError: If service initialization fails
        """
        creds = self._load_or_refresh_credentials()

        if not creds or not creds.valid:
            creds = self._authenticate()

        self._save_token(creds)
        return self._build_service(creds)

    def _load_or_refresh_credentials(self) -> Credentials | None:
        """Load credentials from token file or refresh if expired."""
        if not self._token_file_exists():
            return None

        creds = self._load_credentials_from_file()
        if not creds:
            return None

        if creds.valid:
            return creds

        return self._refresh_credentials_if_needed(creds)

    def _token_file_exists(self) -> bool:
        """Check if token file exists.

        Returns:
            True if token file exists, False otherwise
        """
        return os.path.exists(self.token_path)

    def _load_credentials_from_file(self) -> Credentials | None:
        """Load credentials from token file.

        Returns:
            Credentials object or None if loading fails
        """
        try:
            return Credentials.from_authorized_user_file(self.token_path, DRIVE_SCOPES)
        except (json.JSONDecodeError, ValueError, KeyError) as error:
            logger.warning(f"Token file corrupted, will re-authenticate: {error}")
            self._remove_corrupted_token_file()
            return None

    def _remove_corrupted_token_file(self) -> None:
        """Remove corrupted token file."""
        with contextlib.suppress(OSError):
            os.remove(self.token_path)

    def _refresh_credentials_if_needed(self, creds: Credentials) -> Credentials | None:
        """Refresh credentials if they are expired and have refresh token.

        Args:
            creds: Credentials object to refresh

        Returns:
            Refreshed credentials or None if refresh fails
        """
        if not (creds.expired and creds.refresh_token):
            return None

        try:
            creds.refresh(Request())
            return creds
        except Exception as error:
            logger.warning(f"Token refresh failed, will re-authenticate: {error}")
            return None

    def _authenticate(self) -> Credentials:
        """Perform OAuth authentication flow.

        Returns:
            Valid credentials

        Raises:
            FileNotFoundError: If credentials file is missing
            ValueError: If credentials file is invalid
            RuntimeError: If OAuth flow fails
        """
        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(
                f"Credentials file not found: {self.credentials_path}. "
                "Please download OAuth client credentials from Google Cloud Console."
            )

        self._validate_credentials_file()

        return safe_execute(
            "complete OAuth flow",
            lambda: self._do_authenticate(),
            "Failed to complete OAuth flow",
        )

    def _do_authenticate(self) -> Credentials:
        """Internal method to perform authentication (without error handling)."""
        flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, DRIVE_SCOPES)
        return flow.run_local_server(port=0)

    def _validate_credentials_file(self) -> None:
        """Validate credentials file format.

        Raises:
            ValueError: If credentials file is invalid
        """
        try:
            with open(self.credentials_path, encoding="utf-8") as credentials_file:
                json.load(credentials_file)
        except (json.JSONDecodeError, OSError) as error:
            raise ValueError(
                f"Invalid credentials file format: {self.credentials_path}. {error}"
            ) from error

    def _save_token(self, creds: Credentials) -> None:
        """Save credentials token to file."""
        try:
            with open(self.token_path, "w", encoding="utf-8") as token_file:
                token_file.write(creds.to_json())
        except OSError as error:
            logger.warning(f"Failed to save token file: {error}")

    def _build_service(self, creds: Credentials) -> "Resource":
        """Build Drive service from credentials.

        Raises:
            RuntimeError: If service build fails
        """
        return safe_execute(
            "initialize Drive service",
            lambda: build("drive", "v3", credentials=creds),
            "Failed to initialize Drive service",
        )
