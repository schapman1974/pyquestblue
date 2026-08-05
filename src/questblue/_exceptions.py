"""Exceptions raised by the QuestBlue SDK."""

from __future__ import annotations

from typing import Any, Mapping, Optional


class QuestBlueError(Exception):
    """Base class for all SDK errors."""


class QuestBlueConfigurationError(QuestBlueError):
    """The client was configured with invalid or missing credentials."""


class QuestBlueConnectionError(QuestBlueError):
    """The QuestBlue API could not be reached."""


class QuestBlueAPIError(QuestBlueError):
    """QuestBlue returned an unsuccessful API response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        request_id: Optional[str] = None,
        response: Any = None,
        body: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.request_id = request_id
        self.response = response
        self.body = body

    @property
    def details(self) -> Mapping[str, Any]:
        """Return mapping-shaped error data, or an empty mapping."""
        return self.body if isinstance(self.body, Mapping) else {}


class QuestBlueAuthenticationError(QuestBlueAPIError):
    """QuestBlue rejected the supplied credentials."""


class QuestBlueRateLimitError(QuestBlueAPIError):
    """QuestBlue rejected a request because its rate limit was exceeded."""


class QuestBlueServerError(QuestBlueAPIError):
    """QuestBlue returned a server-side error."""
