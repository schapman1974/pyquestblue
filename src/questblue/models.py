"""Shared public models and validation primitives for QuestBlue resources."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Generic, Mapping, Optional, Tuple, Type, TypeVar, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

DataT = TypeVar("DataT")
ModelT = TypeVar("ModelT", bound="QuestBlueModel")
RequestValue = Union[str, int, float, bool, list[Any], Tuple[Any, ...], None]


class QuestBlueModel(BaseModel):
    """Base model that remains compatible with fields QuestBlue adds later."""

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        validate_assignment=True,
    )

    @property
    def extra_fields(self) -> Mapping[str, Any]:
        """Fields not yet known to this SDK release."""
        return self.model_extra or {}

    def to_request_params(self) -> Dict[str, Any]:
        """Serialize a request model using API aliases and JSON-compatible values."""
        return self.model_dump(mode="json", by_alias=True, exclude_none=True)


class OpenStringEnum(str, Enum):
    """String enum that preserves unknown values introduced by QuestBlue."""

    @classmethod
    def _missing_(cls, value: object) -> Optional[OpenStringEnum]:
        if not isinstance(value, str):
            return None
        member = str.__new__(cls, value)
        safe_name = re.sub(r"\W+", "_", value).strip("_").upper() or "EMPTY"
        member._name_ = f"UNKNOWN_{safe_name}"
        member._value_ = value
        return member


class OnOff(OpenStringEnum):
    ON = "on"
    OFF = "off"


class YesNo(OpenStringEnum):
    YES = "yes"
    NO = "no"


class Period(OpenStringEnum):
    THIS_MONTH = "thismonth"
    PREVIOUS_MONTH = "previousmonth"
    THIS_HOUR = "thishour"
    PREVIOUS_HOUR = "previoushour"
    TODAY = "today"
    YESTERDAY = "yesterday"


class TimestampRange(QuestBlueModel):
    """Inclusive Unix timestamp range used by reporting endpoints."""

    start: int = Field(ge=0)
    end: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_order(self) -> TimestampRange:
        if self.end < self.start:
            raise ValueError("end must be greater than or equal to start")
        return self

    def to_query_value(self) -> list[int]:
        return [self.start, self.end]


class ResponseEnvelope(QuestBlueModel, Generic[DataT]):
    """Common QuestBlue response shape containing a data field."""

    data: Optional[DataT] = None


class WarningResponse(QuestBlueModel):
    """QuestBlue's non-fatal HTTP 202 warning shape."""

    warning: list[str] = Field(default_factory=list)


class ErrorResponse(QuestBlueModel):
    """Common application-error body, including QuestBlue HTTP 206 responses."""

    error: str


class PageMetadata(QuestBlueModel):
    """Pagination metadata shared by collection endpoints."""

    total: Optional[int] = Field(default=None, ge=0)
    total_pages: Optional[int] = Field(default=None, ge=0)
    current_page: int = Field(default=1, ge=1)
    per_page: Optional[int] = Field(default=None, ge=1)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any], *, requested_page: int) -> PageMetadata:
        values = {
            "total": payload.get("total"),
            "total_pages": payload.get("total_pages"),
            "current_page": payload.get("current_page", payload.get("page", requested_page)),
            "per_page": payload.get("per_page"),
        }
        return cls.model_validate(values)

    def next_page(self, item_count: int) -> Optional[int]:
        """Return the next page number, or None when this is the final page."""
        if self.total_pages is not None:
            return self.current_page + 1 if self.current_page < self.total_pages else None
        if self.total is not None and self.per_page is not None:
            consumed = self.current_page * self.per_page
            return self.current_page + 1 if consumed < self.total else None
        if self.per_page is not None and item_count < self.per_page:
            return None
        return self.current_page + 1 if item_count else None


@dataclass(frozen=True)
class ParsedResponse(Generic[DataT]):
    """Validated data paired with the exact decoded upstream payload."""

    data: DataT
    raw: Any


@dataclass(frozen=True)
class BinaryResponse:
    """Binary response content plus useful transport metadata."""

    content: bytes
    content_type: Optional[str] = None
    filename: Optional[str] = None

    @classmethod
    def from_content(
        cls,
        content: bytes,
        *,
        content_type: Optional[str] = None,
        content_disposition: Optional[str] = None,
    ) -> BinaryResponse:
        filename = None
        if content_disposition:
            match = re.search(r'filename\*?=(?:UTF-8\'\')?["\']?([^"\';]+)', content_disposition)
            if match:
                filename = match.group(1)
        return cls(content=content, content_type=content_type, filename=filename)


def parse_model(model: Type[ModelT], payload: Any) -> ParsedResponse[ModelT]:
    """Validate a payload while retaining the exact decoded response."""
    return ParsedResponse(data=model.model_validate(payload), raw=payload)


def model_parser(model: Type[ModelT]) -> Callable[[Any], ModelT]:
    """Create an item parser suitable for a paginator."""

    def parse(value: Any) -> ModelT:
        return model.model_validate(value)

    return parse
