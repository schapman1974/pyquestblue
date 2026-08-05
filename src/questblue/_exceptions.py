"""Exceptions raised by the QuestBlue SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping, Optional

if TYPE_CHECKING:
    from .models import ErrorResponse


class QuestBlueError(Exception):
    """Base class for all SDK errors."""


class QuestBlueConfigurationError(QuestBlueError):
    """The client was configured with invalid or missing credentials."""


class QuestBlueConnectionError(QuestBlueError):
    """The QuestBlue API could not be reached."""


class QuestBlueTimeoutError(QuestBlueConnectionError):
    """A QuestBlue request exceeded its configured timeout."""


class QuestBlueResponseError(QuestBlueError):
    """QuestBlue returned a response that could not be decoded as declared."""


class QuestBluePaginationError(QuestBlueError):
    """QuestBlue returned unsafe or inconsistent pagination metadata."""


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
        self.error: Optional[ErrorResponse] = None
        if isinstance(body, Mapping) and isinstance(body.get("error"), str):
            from .models import ErrorResponse

            self.error = ErrorResponse.model_validate(body)

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
