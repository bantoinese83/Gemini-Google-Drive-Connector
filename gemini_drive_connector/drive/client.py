"""Google Drive API client wrapper."""

from typing import TYPE_CHECKING

from gemini_drive_connector.drive.auth import DriveAuth

if TYPE_CHECKING:
    from googleapiclient.discovery import Resource
else:
    Resource = object  # Type stub for runtime


class DriveClient:
    """Wrapper for Google Drive API service with connection caching.

    Caches the service connection to avoid repeated authentication and
    service initialization, improving performance.
    """

    def __init__(self, auth: DriveAuth | None = None) -> None:
        """Initialize Drive client.

        Args:
            auth: DriveAuth instance. If None, creates a new one.
        """
        self._auth = auth or DriveAuth()
        self._service: Resource | None = None

    @property
    def service(self) -> Resource:
        """Get or create Drive service with lazy initialization.

        Uses cached service if available to avoid repeated initialization.
        This improves performance by reusing the authenticated connection.

        Returns:
            Authorized Drive service resource
        """
        if self._service is None:
            self._service = self._auth.get_service()
        return self._service
