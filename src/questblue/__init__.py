"""A modern Python SDK for the QuestBlue telecommunications API."""

from ._client import DEFAULT_BASE_URL, SECONDARY_BASE_URL, AsyncQuestBlue, QuestBlue
from ._exceptions import (
    QuestBlueAPIError,
    QuestBlueAuthenticationError,
    QuestBlueConfigurationError,
    QuestBlueConnectionError,
    QuestBlueError,
    QuestBluePaginationError,
    QuestBlueRateLimitError,
    QuestBlueServerError,
)
from .models import (
    BinaryResponse,
    ErrorResponse,
    OnOff,
    OpenStringEnum,
    PageMetadata,
    ParsedResponse,
    Period,
    QuestBlueModel,
    ResponseEnvelope,
    TimestampRange,
    WarningResponse,
    YesNo,
    model_parser,
    parse_model,
)
from .pagination import AsyncPaginator, Page, SyncPaginator, parse_page

__all__ = [
    "DEFAULT_BASE_URL",
    "SECONDARY_BASE_URL",
    "AsyncPaginator",
    "AsyncQuestBlue",
    "BinaryResponse",
    "ErrorResponse",
    "OnOff",
    "OpenStringEnum",
    "Page",
    "PageMetadata",
    "ParsedResponse",
    "Period",
    "QuestBlue",
    "QuestBlueAPIError",
    "QuestBlueAuthenticationError",
    "QuestBlueConfigurationError",
    "QuestBlueConnectionError",
    "QuestBlueError",
    "QuestBlueModel",
    "QuestBluePaginationError",
    "QuestBlueRateLimitError",
    "QuestBlueServerError",
    "ResponseEnvelope",
    "SyncPaginator",
    "TimestampRange",
    "WarningResponse",
    "YesNo",
    "model_parser",
    "parse_model",
    "parse_page",
]

__version__ = "0.1.0"
