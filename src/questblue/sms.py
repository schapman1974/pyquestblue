"""Typed models and validation for QuestBlue SMS, MMS, and carrier operations."""

from __future__ import annotations

import ipaddress
import re
from datetime import date, datetime
from enum import Enum
from typing import Any, List, Mapping, Optional, Tuple, Type, TypeVar, Union
from urllib.parse import urlsplit

from pydantic import ConfigDict, Field, field_serializer, field_validator, model_validator

from ._exceptions import QuestBlueResponseError
from .models import OnOff, OpenStringEnum, QuestBlueModel, ResponseEnvelope, WarningResponse, YesNo


class SMSModel(QuestBlueModel):
    """Messaging model that suppresses PII values in validation diagnostics."""

    model_config = ConfigDict(hide_input_in_errors=True)


class SMSMode(str, Enum):
    EMAIL = "email"
    XMPP = "xmpp"
    BOTH = "both"
    URL = "url"
    CHAT = "chat"
    NONE = "none"
    THREE_CX = "3cx"
    YEASTAR = "yeastar"


class SMSPostMethod(str, Enum):
    FORM = "form"
    JSON = "json"
    XML = "xml"


class SMSDirection(str, Enum):
    INBOUND = "in"
    OUTBOUND = "out"
    ALL = ""


class SMSMessageType(str, Enum):
    SMS = "sms"
    MMS = "mms"
    ALL = ""


class SMSHistoryPeriod(str, Enum):
    THIS_HOUR = "thishour"
    PREVIOUS_HOUR = "previoushour"
    TODAY = "today"
    YESTERDAY = "yesterday"


class SMSSortOrder(str, Enum):
    ASCENDING = "asc"
    DESCENDING = "desc"


class OffnetAction(str, Enum):
    ADD = "add"
    REMOVE = "remove"


class MessageDeliveryStatus(OpenStringEnum):
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


class SMSRecordDirection(OpenStringEnum):
    INBOUND = "in"
    OUTBOUND = "out"
    INBOUND_LONG = "inbound"
    OUTBOUND_LONG = "outbound"


class SMSRecordType(OpenStringEnum):
    SMS = "sms"
    MMS = "mms"


class OffnetStatus(OpenStringEnum):
    UNAVAILABLE = "unavailable"
    DISABLED = "disabled"
    RECEIVED = "received"
    PROCESSING = "processing"
    FAILED = "failed"
    ENABLED = "enabled"


def _validate_us_number(value: int) -> int:
    digits = str(value)
    if len(digits) == 10 or (len(digits) == 11 and digits.startswith("1")):
        return value
    raise ValueError("phone number must contain 10 US digits or 11 digits beginning with 1")


def _validate_email(value: str) -> str:
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
        raise ValueError("value must be a valid email address")
    return value


def _validate_http_url(value: str, *, public_media: bool = False) -> str:
    parsed = urlsplit(value)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username:
        raise ValueError("URL must be an absolute HTTP(S) URL without credentials")
    if public_media:
        if parsed.hostname.lower() == "localhost":
            raise ValueError("media URL must use a publicly reachable host")
        try:
            address = ipaddress.ip_address(parsed.hostname)
        except ValueError:
            pass
        else:
            if not address.is_global:
                raise ValueError("media URL must use a publicly reachable host")
    return value


class SMSInventoryRequest(SMSModel):
    did: Optional[str] = None
    per_page: int = Field(default=25, ge=5, le=200)
    page: int = Field(default=1, ge=1)

    @field_validator("did")
    @classmethod
    def validate_search(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and len(re.sub(r"\D", "", value)) < 3:
            raise ValueError("did search must contain at least three digits")
        return value


class SendMessageRequest(SMSModel):
    did: int = Field(repr=False)
    did_to: int = Field(repr=False)
    msg: str = Field(min_length=1, repr=False)
    file_url: Optional[List[str]] = Field(default=None, min_length=1, repr=False)

    @field_validator("did", "did_to")
    @classmethod
    def validate_number(cls, value: int) -> int:
        return _validate_us_number(value)

    @field_validator("file_url")
    @classmethod
    def validate_media_urls(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return None
        return [_validate_http_url(url, public_media=True) for url in value]


class SMSSettingsUpdateRequest(SMSModel):
    did: int = Field(repr=False)
    sms_mode: SMSMode
    forward2email: Optional[str] = Field(default=None, repr=False)
    xmpp_name: Optional[str] = Field(default=None, repr=False)
    xmpp_passwd: Optional[str] = Field(default=None, repr=False)
    post2url: Optional[str] = Field(default=None, repr=False)
    post2urlmethod: SMSPostMethod = SMSPostMethod.FORM
    chat_email: Optional[str] = Field(default=None, repr=False)
    chat_passwd: Optional[str] = Field(default=None, repr=False)
    secret: Optional[str] = Field(default=None, repr=False)

    @field_validator("did")
    @classmethod
    def validate_number(cls, value: int) -> int:
        return _validate_us_number(value)

    @field_validator("forward2email", "chat_email")
    @classmethod
    def validate_email(cls, value: Optional[str]) -> Optional[str]:
        return _validate_email(value) if value is not None else None

    @field_validator("post2url")
    @classmethod
    def validate_post_url(cls, value: Optional[str]) -> Optional[str]:
        return _validate_http_url(value) if value is not None else None

    @model_validator(mode="after")
    def validate_mode_fields(self) -> SMSSettingsUpdateRequest:
        if self.sms_mode in (SMSMode.EMAIL, SMSMode.BOTH) and not self.forward2email:
            raise ValueError("forward2email is required for email and both modes")
        if self.sms_mode in (SMSMode.XMPP, SMSMode.BOTH) and not (
            self.xmpp_name and self.xmpp_passwd
        ):
            raise ValueError("xmpp_name and xmpp_passwd are required for xmpp and both modes")
        if self.sms_mode is SMSMode.URL and not self.post2url:
            raise ValueError("post2url is required for url mode")
        if self.sms_mode is SMSMode.CHAT and not (self.chat_email and self.chat_passwd):
            raise ValueError("chat_email and chat_passwd are required for chat mode")
        if self.sms_mode is SMSMode.YEASTAR and not self.secret:
            raise ValueError("secret is required for yeastar mode")
        return self


class OffnetOrderRequest(SMSModel):
    did: int = Field(repr=False)
    action: OffnetAction

    @field_validator("did")
    @classmethod
    def validate_number(cls, value: int) -> int:
        return _validate_us_number(value)


class OffnetStatusRequest(SMSModel):
    did: int = Field(repr=False)

    @field_validator("did")
    @classmethod
    def validate_number(cls, value: int) -> int:
        return _validate_us_number(value)


class MessageDeliveryStatusRequest(SMSModel):
    msg_id: int = Field(gt=0)


class CarrierLookupRequest(SMSModel):
    tn: Union[int, List[int]] = Field(repr=False)

    @field_validator("tn")
    @classmethod
    def validate_numbers(cls, value: Union[int, List[int]]) -> Union[int, List[int]]:
        values = value if isinstance(value, list) else [value]
        if not values:
            raise ValueError("tn must contain at least one phone number")
        for number in values:
            _validate_us_number(number)
        return value


class SMSHistoryRequest(SMSModel):
    period: Optional[Union[SMSHistoryPeriod, Tuple[date, date]]] = None
    direction: Optional[SMSDirection] = None
    order: Optional[SMSSortOrder] = None
    msg_type: Optional[SMSMessageType] = None
    per_page: int = Field(default=25, ge=5, le=500)
    page: int = Field(default=1, ge=1)

    @field_validator("period")
    @classmethod
    def validate_period(
        cls, value: Optional[Union[SMSHistoryPeriod, Tuple[date, date]]]
    ) -> Optional[Union[SMSHistoryPeriod, Tuple[date, date]]]:
        if isinstance(value, tuple) and value[1] < value[0]:
            raise ValueError("period end date must be on or after its start date")
        return value

    @field_serializer("period")
    def serialize_period(self, value: Optional[Union[SMSHistoryPeriod, Tuple[date, date]]]) -> Any:
        if isinstance(value, tuple):
            return [item.isoformat() for item in value]
        return value.value if value is not None else None


class SMSDIDSettings(SMSModel):
    did: str = Field(repr=False)
    email2forward: str
    sms_enabled: OnOff
    sms_mode: str


class SMSInventoryResponse(ResponseEnvelope[List[SMSDIDSettings]], SMSModel):
    data: List[SMSDIDSettings] = Field(default_factory=list)
    current_page: int = Field(default=1, ge=1)
    total: int = Field(default=0, ge=0)
    total_pages: int = Field(default=1, ge=0)

    def next_page(self) -> Optional[int]:
        return self.current_page + 1 if self.current_page < self.total_pages else None


class SentMessage(SMSModel):
    msg_id: str


class SendMessageResponse(ResponseEnvelope[List[SentMessage]], SMSModel):
    data: List[SentMessage] = Field(default_factory=list)


class SMSSettingsUpdateResponse(SMSModel):
    message: str
    success: bool


class MessageDelivery(SMSModel):
    status: MessageDeliveryStatus


class MessageDeliveryStatusResponse(ResponseEnvelope[MessageDelivery], SMSModel):
    data: MessageDelivery


class OffnetOrderStatus(SMSModel):
    status: OffnetStatus


class OffnetStatusResponse(ResponseEnvelope[OffnetOrderStatus], SMSModel):
    data: OffnetOrderStatus


class CarrierRecord(SMSModel):
    carrier: str
    is_wireless: YesNo = Field(alias="isWireless")
    tn: int = Field(repr=False)


class CarrierLookupResponse(ResponseEnvelope[List[CarrierRecord]], SMSModel):
    data: List[CarrierRecord] = Field(default_factory=list)
    total: int = Field(default=0, ge=0)


class SMSHistoryRecord(SMSModel):
    id: str
    time: datetime
    from_number: str = Field(alias="from", repr=False)
    to_number: str = Field(alias="to", repr=False)
    direction: SMSRecordDirection
    msg_type: SMSRecordType
    status: MessageDeliveryStatus


class SMSHistoryResponse(ResponseEnvelope[List[SMSHistoryRecord]], SMSModel):
    data: List[SMSHistoryRecord] = Field(default_factory=list)
    current_page: int = Field(ge=1)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)

    def next_page(self) -> Optional[int]:
        return self.current_page + 1 if self.current_page < self.total_pages else None


SMSModelT = TypeVar("SMSModelT", bound=QuestBlueModel)


def parse_sms_response(model: Type[SMSModelT], payload: Any) -> Union[SMSModelT, WarningResponse]:
    if isinstance(payload, Mapping) and "warning" in payload:
        return WarningResponse.model_validate(payload)
    return model.model_validate(payload)


def parse_empty_sms_response(payload: Any) -> Optional[WarningResponse]:
    if payload is None or payload == "" or payload == {}:
        return None
    if isinstance(payload, Mapping) and "warning" in payload:
        return WarningResponse.model_validate(payload)
    raise QuestBlueResponseError("QuestBlue returned a body for an empty SMS response")
