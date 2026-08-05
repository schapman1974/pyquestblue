"""A modern Python SDK for the QuestBlue telecommunications API."""

from ._client import DEFAULT_BASE_URL, SECONDARY_BASE_URL, AsyncQuestBlue, QuestBlue
from ._exceptions import (
    QuestBlueAPIError,
    QuestBlueAuthenticationError,
    QuestBlueConfigurationError,
    QuestBlueConnectionError,
    QuestBlueError,
    QuestBlueRateLimitError,
    QuestBlueServerError,
)

__all__ = [
    "DEFAULT_BASE_URL",
    "SECONDARY_BASE_URL",
    "AsyncQuestBlue",
    "QuestBlue",
    "QuestBlueAPIError",
    "QuestBlueAuthenticationError",
    "QuestBlueConfigurationError",
    "QuestBlueConnectionError",
    "QuestBlueError",
    "QuestBlueRateLimitError",
    "QuestBlueServerError",
]

__version__ = "0.1.0"
