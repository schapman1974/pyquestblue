"""Typed models and export helpers for QuestBlue reporting operations."""

from __future__ import annotations

import base64
import re
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    BinaryIO,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import ConfigDict, Field, field_serializer, field_validator, model_validator

from ._exceptions import QuestBlueResponseError
from .models import OnOff, OpenStringEnum, Period, QuestBlueModel, TimestampRange, WarningResponse


class ReportModel(QuestBlueModel):
    model_config = ConfigDict(hide_input_in_errors=True)


class CallDirection(OpenStringEnum):
    IN = "in"
    OUT = "out"
    OUTBOUND = "outbound"
    OUTBOUND_TOLL_FREE = "outbound_tf"
    OUTBOUND_ZONE_2 = "outbound_zone2"
    OUTBOUND_FAX = "outbound_fax"
    OUTBOUND_FAX_TOLL_FREE = "outbound_fax_tf"
    OUTBOUND_ENTERPRISE_FAX = "outbound_enter_fax"
    OUTBOUND_INFORMATION = "outbound_info"
    INBOUND = "inbound"
    INBOUND_TOLL_FREE = "inbound_tf"
    INBOUND_FAX = "inbound_fax"
    INBOUND_ENTERPRISE_FAX = "inbound_enter_fax"
    INBOUND_NON_US_TOLL_FREE = "inbound_tf_nous_tf"


class FaxService(str, Enum):
    PRO = "pro"
    ENTERPRISE = "enterprise"


class FaxDirection(str, Enum):
    OUT = "out"
    IN = "in"


class FaxHistoryPeriod(str, Enum):
    TODAY = "today"
    YESTERDAY = "yesterday"


class CallHistoryRequest(ReportModel):
    timezone: Optional[str] = None
    last_id: Optional[int] = Field(default=None, ge=0, repr=False)
    trunk: Optional[List[str]] = None
    period: Optional[Union[Period, TimestampRange]] = None
    success_call_only: OnOff = OnOff.OFF
    did: Optional[int] = Field(default=None, gt=0, repr=False)
    type: Optional[CallDirection] = None
    country_id: Optional[int] = Field(default=None, ge=0)
    summary_only: OnOff = OnOff.OFF
    per_page: int = Field(default=25, ge=5, le=5000)
    get_id: OnOff = OnOff.OFF
    get_fax: OnOff = OnOff.ON
    page: int = Field(default=1, ge=1)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            try:
                ZoneInfo(value)
            except ZoneInfoNotFoundError:
                raise ValueError("timezone must be an IANA timezone identifier") from None
        return value

    @field_validator("trunk")
    @classmethod
    def validate_trunks(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is not None and (not value or any(not item.strip() for item in value)):
            raise ValueError("trunk must contain at least one non-empty name")
        return value

    @model_validator(mode="after")
    def validate_period_range(self) -> CallHistoryRequest:
        if (
            isinstance(self.period, TimestampRange)
            and self.period.end - self.period.start > 31 * 24 * 60 * 60
        ):
            raise ValueError("call history period must not exceed 31 days")
        return self

    @field_serializer("period")
    def serialize_period(self, value: Optional[Union[Period, TimestampRange]]) -> Any:
        return value.to_query_value() if isinstance(value, TimestampRange) else value


class CallSummaryRecord(ReportModel):
    call_number: int = Field(ge=0)
    call_type: str
    cost: str
    total_duration_min: str


class CallDetailRecord(ReportModel):
    call_type: str
    call_status: Optional[str] = None
    call_id: Optional[int] = Field(default=None, repr=False)
    id: Optional[int] = Field(default=None, repr=False)
    did: Optional[str] = Field(default=None, repr=False)
    did_from: Optional[str] = Field(default=None, repr=False)
    did_to: Optional[str] = Field(default=None, repr=False)
    trunk: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    call_duration: Optional[str] = None
    call_duration_min: Optional[str] = None
    billed_min: Optional[str] = None
    cost: Optional[str] = None


CallHistoryRecord = Union[CallSummaryRecord, CallDetailRecord]


class CallHistoryResponse(ReportModel):
    data: List[CallHistoryRecord] = Field(default_factory=list)
    total: int = Field(default=0, ge=0)
    total_pages: Optional[int] = Field(default=None, ge=0)
    current_page: int = Field(default=1, ge=1)

    def next_page(self, requested_per_page: int) -> Optional[int]:
        if self.total_pages is not None:
            return self.current_page + 1 if self.current_page < self.total_pages else None
        return self.current_page + 1 if len(self.data) >= requested_per_page else None


FaxPeriod = Union[FaxHistoryPeriod, Tuple[datetime, datetime]]


class FaxHistoryRequest(ReportModel):
    did: Optional[List[int]] = Field(default=None, repr=False)
    service: Optional[FaxService] = None
    type: Optional[FaxDirection] = None
    fax_id: Optional[str] = Field(default=None, min_length=1, repr=False)
    period: Optional[FaxPeriod] = None
    per_page: int = Field(default=25, ge=5, le=1000)
    page: int = Field(default=1, ge=1)

    @field_validator("did")
    @classmethod
    def validate_dids(cls, value: Optional[List[int]]) -> Optional[List[int]]:
        if value is not None and (not value or any(item <= 0 for item in value)):
            raise ValueError("did must contain at least one positive phone number")
        return value

    @model_validator(mode="after")
    def validate_period_range(self) -> FaxHistoryRequest:
        if isinstance(self.period, tuple) and self.period[1] < self.period[0]:
            raise ValueError("fax history period end must not precede start")
        return self

    @field_serializer("period")
    def serialize_period(self, value: Optional[FaxPeriod]) -> Any:
        if isinstance(value, tuple):
            return [item.isoformat() for item in value]
        return value


class FaxHistoryRecord(ReportModel):
    did_from: str = Field(repr=False)
    did_to: str = Field(repr=False)
    fax_id: str = Field(repr=False)
    send_time: datetime
    service: FaxService
    status: str
    type: FaxDirection


class FaxHistoryResponse(ReportModel):
    data: List[FaxHistoryRecord] = Field(default_factory=list)
    current_page: int = Field(default=1, ge=1)
    total: int = Field(default=0, ge=0)
    total_pages: int = Field(default=0, ge=0)

    def next_page(self) -> Optional[int]:
        return self.current_page + 1 if self.current_page < self.total_pages else None


class FaxDownloadRequest(ReportModel):
    fax_id: int = Field(gt=0, repr=False)


class FaxDownloadData(ReportModel):
    fax_base64: str = Field(min_length=1, repr=False)

    @field_validator("fax_base64")
    @classmethod
    def validate_content(cls, value: str) -> str:
        if len(value) % 4 or re.fullmatch(r"[A-Za-z0-9+/]*={0,2}", value) is None:
            raise ValueError("fax_base64 must contain valid base64")
        return value

    def iter_bytes(self, chunk_size: int = 64 * 1024) -> Iterator[bytes]:
        """Incrementally decode base64 without duplicating it as one bytes object."""
        if chunk_size < 1:
            raise ValueError("chunk_size must be positive")
        encoded_chunk_size = max(4, (chunk_size // 3) * 4)
        for offset in range(0, len(self.fax_base64), encoded_chunk_size):
            yield base64.b64decode(self.fax_base64[offset : offset + encoded_chunk_size])

    def write_to(self, destination: BinaryIO, chunk_size: int = 64 * 1024) -> int:
        written = 0
        for chunk in self.iter_bytes(chunk_size):
            written += destination.write(chunk)
        return written


class FaxDownloadResponse(ReportModel):
    data: FaxDownloadData


ReportModelT = TypeVar("ReportModelT", bound=QuestBlueModel)


def parse_report_response(
    model: Type[ReportModelT], payload: Any
) -> Union[ReportModelT, WarningResponse]:
    if isinstance(payload, Mapping) and "warning" in payload:
        return WarningResponse.model_validate(payload)
    try:
        return model.model_validate(payload)
    except (TypeError, ValueError) as exc:
        raise QuestBlueResponseError("QuestBlue returned an invalid reports response") from exc


def export_rows(response: Union[CallHistoryResponse, FaxHistoryResponse]) -> List[Dict[str, Any]]:
    """Return standard dictionaries suitable for csv.DictWriter or pandas.DataFrame."""
    return [record.model_dump(mode="json") for record in response.data]
