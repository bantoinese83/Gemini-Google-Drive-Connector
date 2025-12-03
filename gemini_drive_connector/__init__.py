"""Gemini Drive Connector package.

This package provides functionality to connect Google Drive folders with
Gemini File Search stores, enabling AI-powered chat over Drive content.
"""

from gemini_drive_connector.config.settings import GeminiDriveConnectorConfig
from gemini_drive_connector.connector import GeminiDriveConnector

__all__ = ["GeminiDriveConnector", "GeminiDriveConnectorConfig"]
