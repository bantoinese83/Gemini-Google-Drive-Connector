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
        if not os.path.exists(self.token_path):
            return None

        try:
            creds = Credentials.from_authorized_user_file(self.token_path, DRIVE_SCOPES)
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Token file corrupted, will re-authenticate: {e}")
            with contextlib.suppress(OSError):
                os.remove(self.token_path)
            return None

        if creds.valid:
            return creds

        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                return creds
            except Exception as e:
                logger.warning(f"Token refresh failed, will re-authenticate: {e}")
                return None

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

        try:
            flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, DRIVE_SCOPES)
            return flow.run_local_server(port=0)
        except Exception as e:
            logger.error(f"OAuth flow failed: {e}")
            raise RuntimeError(f"Failed to complete OAuth flow: {e}") from e

    def _validate_credentials_file(self) -> None:
        """Validate credentials file format.

        Raises:
            ValueError: If credentials file is invalid
        """
        try:
            with open(self.credentials_path, encoding="utf-8") as f:
                json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            raise ValueError(
                f"Invalid credentials file format: {self.credentials_path}. {e}"
            ) from e

    def _save_token(self, creds: Credentials) -> None:
        """Save credentials token to file."""
        try:
            with open(self.token_path, "w", encoding="utf-8") as token_file:
                token_file.write(creds.to_json())
        except OSError as e:
            logger.warning(f"Failed to save token file: {e}")

    def _build_service(self, creds: Credentials) -> "Resource":
        """Build Drive service from credentials.

        Raises:
            RuntimeError: If service build fails
        """
        try:
            return build("drive", "v3", credentials=creds)
        except Exception as e:
            logger.error(f"Failed to build Drive service: {e}")
            raise RuntimeError(f"Failed to initialize Drive service: {e}") from e
