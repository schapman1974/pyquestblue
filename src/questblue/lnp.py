"""Typed models and bill helpers for QuestBlue number portability."""

from __future__ import annotations

import base64
import re
from datetime import date, datetime, time
from enum import Enum
from pathlib import Path
from typing import Any, BinaryIO, List, Mapping, Optional, Type, TypeVar, Union

from pydantic import ConfigDict, Field, field_validator, model_validator

from ._exceptions import QuestBlueResponseError
from .models import OpenStringEnum, QuestBlueModel, WarningResponse, YesNo

MAX_LNP_BILL_SIZE = 5 * 1024 * 1024
SUPPORTED_LNP_BILL_EXTENSIONS = frozenset((".gif", ".jpg", ".jpeg", ".png", ".pdf"))


class LNPModel(QuestBlueModel):
    model_config = ConfigDict(hide_input_in_errors=True)


class DIDMode(str, Enum):
    VOICE = "voice"
    FAX = "fax"


class ServiceLocation(str, Enum):
    BUSINESS = "business"
    RESIDENTIAL = "residential"


class LNPSubmissionStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"


class LNPStatus(OpenStringEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING = "pending"
    FOC = "foc"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


def _phone(value: int) -> int:
    digits = str(value)
    if len(digits) == 10 or (len(digits) == 11 and digits.startswith("1")):
        return value
    raise ValueError("number must contain 10 US digits or 11 digits beginning with 1")


def _filename(value: str) -> str:
    if Path(value).name != value or Path(value).suffix.lower() not in SUPPORTED_LNP_BILL_EXTENSIONS:
        raise ValueError("bill filename must be a GIF, JPG, PNG, or PDF basename")
    return value


def _content(value: bytes) -> bytes:
    if not value:
        raise ValueError("bill file must not be empty")
    if len(value) > MAX_LNP_BILL_SIZE:
        raise ValueError("bill file must not exceed 5MB")
    return value


class LNPBillUpload(LNPModel):
    bill_file: str = Field(min_length=1, repr=False)
    bill_filename: str = Field(repr=False)

    @field_validator("bill_filename")
    @classmethod
    def validate_filename(cls, value: str) -> str:
        return _filename(value)

    @field_validator("bill_file")
    @classmethod
    def validate_file(cls, value: str) -> str:
        if len(value) % 4 or re.fullmatch(r"[A-Za-z0-9+/]*={0,2}", value) is None:
            raise ValueError("bill_file must contain valid base64")
        if len(value) > 4 * ((MAX_LNP_BILL_SIZE + 2) // 3):
            raise ValueError("bill file must not exceed 5MB")
        return value

    @classmethod
    def from_bytes(cls, content: bytes, filename: str) -> LNPBillUpload:
        return cls(
            bill_file=base64.b64encode(_content(content)).decode("ascii"),
            bill_filename=_filename(filename),
        )

    @classmethod
    def from_file(cls, file: BinaryIO, filename: str) -> LNPBillUpload:
        return cls.from_bytes(file.read(MAX_LNP_BILL_SIZE + 1), filename)

    @classmethod
    def from_path(cls, path: Union[str, Path]) -> LNPBillUpload:
        source = Path(path)
        with source.open("rb") as file:
            return cls.from_file(file, source.name)


class LNPCheckRequest(LNPModel):
    number2port: List[int] = Field(min_length=1, repr=False)

    @field_validator("number2port")
    @classmethod
    def validate_numbers(cls, value: List[int]) -> List[int]:
        return [_phone(item) for item in value]


class LNPCheckData(LNPModel):
    foc_days: int = Field(ge=0)


class LNPCheckResponse(LNPModel):
    data: LNPCheckData


class LNPListRequest(LNPModel):
    number2port: Optional[str] = Field(default=None, repr=False)
    id: Optional[List[int]] = Field(default=None, repr=False)
    per_page: int = Field(default=10, ge=1, le=200)
    page: int = Field(default=1, ge=1)

    @field_validator("number2port")
    @classmethod
    def validate_search(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and len(re.sub(r"\D", "", value)) < 3:
            raise ValueError("number2port search must contain at least three digits")
        return value

    @field_validator("id")
    @classmethod
    def validate_ids(cls, value: Optional[List[int]]) -> Optional[List[int]]:
        if value is not None and (not value or any(item <= 0 for item in value)):
            raise ValueError("id must contain positive request IDs")
        return value


class LNPRequestRecord(LNPModel):
    id: str = Field(repr=False)
    number2port: str = Field(repr=False)
    status: LNPStatus
    account_no: Optional[str] = Field(default=None, repr=False)
    authorize_contact: Optional[str] = Field(default=None, repr=False)
    billing_telephone_no: Optional[str] = Field(default=None, repr=False)
    city: Optional[str] = Field(default=None, repr=False)
    company: Optional[str] = Field(default=None, repr=False)
    contact_title: Optional[str] = Field(default=None, repr=False)
    created_by: Optional[datetime] = None
    did_mode: Optional[DIDMode] = None
    dir_prefix: Optional[str] = None
    dir_suffix: Optional[str] = None
    foc_date: Optional[datetime] = None
    lidb_list: Optional[YesNo] = None
    location: Optional[ServiceLocation] = None
    partial_port: Optional[YesNo] = None
    provider_name: Optional[str] = Field(default=None, repr=False)
    service_unit: Optional[str] = Field(default=None, repr=False)
    street_name: Optional[str] = Field(default=None, repr=False)
    street_no: Optional[str] = Field(default=None, repr=False)
    trunk: Optional[str] = None
    wireless_no: Optional[YesNo] = None
    zipcode: Optional[str] = Field(default=None, repr=False)


class LNPListResponse(LNPModel):
    data: List[LNPRequestRecord] = Field(default_factory=list)
    total: int = Field(default=0, ge=0)
    total_pages: int = Field(default=0, ge=0)
    current_page: int = Field(default=1, ge=1)

    def next_page(self) -> Optional[int]:
        return self.current_page + 1 if self.current_page < self.total_pages else None


class LNPFields(LNPModel):
    foc_date: Optional[date] = None
    activate_time: Optional[time] = None
    trunk: Optional[str] = None
    partial_port: Optional[YesNo] = None
    extra_services: Optional[str] = None
    location: Optional[ServiceLocation] = None
    company: Optional[str] = Field(default=None, max_length=100, repr=False)
    wireless_no: Optional[YesNo] = None
    pincode: Optional[int] = Field(default=None, ge=0, repr=False)
    ssn: Optional[int] = Field(default=None, ge=0, le=9999, repr=False)
    lidb_list: Optional[YesNo] = None
    provider_name: Optional[str] = Field(default=None, max_length=255, repr=False)
    account_no: Optional[str] = Field(default=None, repr=False)
    authorize_contact: Optional[str] = Field(default=None, max_length=25, repr=False)
    contact_title: Optional[str] = Field(default=None, max_length=50, repr=False)
    street_no: Optional[str] = Field(default=None, max_length=50, repr=False)
    dir_prefix: Optional[str] = Field(default=None, max_length=10)
    street_name: Optional[str] = Field(default=None, max_length=100, repr=False)
    dir_suffix: Optional[str] = Field(default=None, max_length=10)
    service_unit: Optional[str] = Field(default=None, max_length=100, repr=False)
    city: Optional[str] = Field(default=None, max_length=100, repr=False)
    state: Optional[str] = Field(default=None, repr=False)
    zipcode: Optional[str] = Field(default=None, max_length=20, repr=False)
    billing_telephone_no: Optional[str] = Field(default=None, repr=False)
    port_out_pin: Optional[str] = Field(default=None, min_length=4, max_length=10, repr=False)
    bill_file: Optional[str] = Field(default=None, repr=False)
    bill_filename: Optional[str] = Field(default=None, repr=False)
    status: Optional[LNPSubmissionStatus] = None

    @field_validator("activate_time")
    @classmethod
    def validate_activation(cls, value: Optional[time]) -> Optional[time]:
        if value is not None and (value.minute or value.second or value.microsecond):
            raise ValueError("activate_time must be on the hour")
        return value

    @field_validator("state")
    @classmethod
    def validate_state(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and re.fullmatch(r"[A-Za-z]{2}", value) is None:
            raise ValueError("state must be a two-letter abbreviation")
        return value.upper() if value is not None else None

    @field_validator("billing_telephone_no")
    @classmethod
    def validate_billing_number(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and re.fullmatch(r"\d{10}", value) is None:
            raise ValueError("billing_telephone_no must contain exactly 10 digits")
        return value

    @model_validator(mode="after")
    def validate_related_fields(self) -> LNPFields:
        if self.partial_port == YesNo.YES and not self.extra_services:
            raise ValueError("extra_services is required for a partial port")
        if self.location == ServiceLocation.BUSINESS and not self.company:
            raise ValueError("company is required for a business location")
        if self.wireless_no == YesNo.YES and (self.pincode is None or self.ssn is None):
            raise ValueError("pincode and ssn are required for a wireless number")
        if self.wireless_no == YesNo.YES and self.foc_date is not None:
            raise ValueError("foc_date is not available for wireless numbers")
        if (self.bill_file is None) != (self.bill_filename is None):
            raise ValueError("bill_file and bill_filename must be provided together")
        if self.bill_file is not None:
            LNPBillUpload(bill_file=self.bill_file, bill_filename=self.bill_filename or "")
        return self


class LNPCreateRequest(LNPFields):
    number2port: List[int] = Field(min_length=1, repr=False)
    did_mode: DIDMode = DIDMode.VOICE
    partial_port: Optional[YesNo] = YesNo.NO
    location: Optional[ServiceLocation] = ServiceLocation.BUSINESS
    wireless_no: Optional[YesNo] = YesNo.NO
    lidb_list: Optional[YesNo] = YesNo.NO
    provider_name: str = Field(max_length=255, repr=False)
    account_no: str = Field(repr=False)
    authorize_contact: str = Field(max_length=25, repr=False)
    contact_title: str = Field(max_length=50, repr=False)
    street_no: str = Field(max_length=50, repr=False)
    street_name: str = Field(max_length=100, repr=False)
    city: str = Field(max_length=100, repr=False)
    zipcode: str = Field(max_length=20, repr=False)
    billing_telephone_no: str = Field(repr=False)
    bill_file: str = Field(repr=False)
    bill_filename: str = Field(repr=False)
    status: Optional[LNPSubmissionStatus] = LNPSubmissionStatus.SUBMITTED

    @field_validator("number2port")
    @classmethod
    def validate_numbers(cls, value: List[int]) -> List[int]:
        return [_phone(item) for item in value]

    @model_validator(mode="after")
    def validate_mode(self) -> LNPCreateRequest:
        if self.did_mode == DIDMode.FAX and self.trunk:
            raise ValueError("trunk is only valid for voice ports")
        return self

    @classmethod
    def with_bill(cls, bill: LNPBillUpload, **fields: Any) -> LNPCreateRequest:
        return cls(bill_file=bill.bill_file, bill_filename=bill.bill_filename, **fields)


class LNPCreateResult(LNPModel):
    id: str = Field(repr=False)


class LNPCreateResponse(LNPModel):
    data: List[LNPCreateResult] = Field(default_factory=list)


class LNPUpdateRequest(LNPFields):
    id: int = Field(gt=0, repr=False)

    @model_validator(mode="after")
    def validate_changes(self) -> LNPUpdateRequest:
        if not self.model_dump(exclude={"id"}, exclude_none=True):
            raise ValueError("LNP update requires at least one changed field")
        return self


class LNPDeleteRequest(LNPModel):
    id: int = Field(gt=0, repr=False)


LNPModelT = TypeVar("LNPModelT", bound=QuestBlueModel)


def parse_lnp_response(model: Type[LNPModelT], payload: Any) -> Union[LNPModelT, WarningResponse]:
    if isinstance(payload, Mapping) and "warning" in payload:
        return WarningResponse.model_validate(payload)
    if isinstance(payload, Mapping) and "error" in payload:
        raise QuestBlueResponseError("QuestBlue returned an LNP error: " + str(payload["error"]))
    try:
        return model.model_validate(payload)
    except (TypeError, ValueError) as exc:
        raise QuestBlueResponseError("QuestBlue returned an invalid LNP response") from exc


def parse_empty_lnp_response(payload: Any) -> Optional[WarningResponse]:
    if payload is None or payload == {} or payload == "":
        return None
    result = parse_lnp_response(WarningResponse, payload)
    return result if isinstance(result, WarningResponse) else None
