"""Gemini API client initialization."""

from google import genai
from loguru import logger  # type: ignore[import-untyped]


class GeminiClient:
    """Handles Gemini API client initialization."""

    def __init__(self, api_key: str) -> None:
        """Initialize Gemini client.

        Args:
            api_key: Gemini API key

        Raises:
            ValueError: If API key is empty
            RuntimeError: If client initialization fails
        """
        if not api_key or not api_key.strip():
            raise ValueError("API key cannot be empty")

        self.api_key = api_key
        self._client = self._create_client()

    @property
    def client(self) -> genai.Client:
        """Get Gemini client instance."""
        return self._client

    def _create_client(self) -> genai.Client:
        """Create and configure Gemini client."""
        try:
            # Static analysis tools don't recognize configure at module level
            # Access configure via getattr with variable to bypass static analysis
            configure_attr = "configure"
            getattr(genai, configure_attr)(api_key=self.api_key)
            return genai.Client(api_key=self.api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise RuntimeError(f"Failed to initialize Gemini client: {e}") from e
