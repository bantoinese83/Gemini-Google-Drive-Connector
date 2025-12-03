"""Gemini chat/query operations."""

from typing import TYPE_CHECKING

from google.genai import types as gtypes
from loguru import logger  # type: ignore[import-untyped]

from gemini_drive_connector.utils.errors import handle_api_error, safe_execute
from gemini_drive_connector.utils.validation import validate_prompt

if TYPE_CHECKING:
    from google import genai


class GeminiChat:
    """Handles chat queries over indexed content."""

    def __init__(self, client: "genai.Client", model: str, file_search_store_name: str) -> None:
        """Initialize chat instance.

        Args:
            client: Gemini client instance
            model: Model name to use
            file_search_store_name: Name of the File Search store

        Raises:
            RuntimeError: If chat creation fails
        """
        self.client = client
        self.model = model
        self._chat = self._create_chat(file_search_store_name)

    def ask(self, prompt: str) -> str:
        """Ask a question over the indexed content.

        Args:
            prompt: Question to ask

        Returns:
            Answer from Gemini

        Raises:
            ValueError: If prompt is empty
            RuntimeError: If query fails
        """
        validate_prompt(prompt)

        logger.info(f"Processing question: {prompt[:50]}...")

        try:
            resp = self._chat.send_message(prompt)
        except Exception as e:
            raise handle_api_error("query Gemini", e) from e

        answer = getattr(resp, "text", "") or ""

        if not answer:
            logger.warning("Received empty response from Gemini")
            return "No response received from Gemini."

        logger.debug(f"Response length: {len(answer)} characters")
        return answer

    def _create_chat(self, file_search_store_name: str) -> "genai.types.Chat":
        """Create chat instance bound to file search store."""
        return safe_execute(
            "create chat",
            lambda: self._do_create_chat(file_search_store_name),
            "Failed to create chat",
        )

    def _do_create_chat(self, file_search_store_name: str) -> "genai.types.Chat":
        """Internal method to create chat (without error handling)."""
        file_search_tool = gtypes.Tool(
            file_search=gtypes.FileSearch(file_search_store_names=[file_search_store_name])
        )
        return self.client.chats.create(
            model=self.model,
            config=gtypes.GenerateContentConfig(tools=[file_search_tool]),
        )
