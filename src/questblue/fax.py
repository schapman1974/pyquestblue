"""Typed models, file helpers, and validation for QuestBlue Fax.Pro operations."""

from __future__ import annotations

import base64
import binascii
import re
from enum import Enum
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Mapping, Optional, Type, TypeVar, Union
from urllib.parse import urlsplit

from pydantic import ConfigDict, Field, field_validator, model_validator

from ._exceptions import QuestBlueResponseError
from .models import OpenStringEnum, QuestBlueModel, WarningResponse

MAX_FAX_FILE_SIZE = 8 * 1024 * 1024
SUPPORTED_FAX_EXTENSIONS = frozenset(
    {
        ".jpeg",
        ".jpg",
        ".gif",
        ".png",
        ".tif",
        ".tiff",
        ".pdf",
        ".doc",
        ".rtf",
        ".ods",
        ".xls",
        ".csv",
        ".ppt",
        ".txt",
        ".rar",
        ".zip",
        ".7z",
    }
)


class FaxModel(QuestBlueModel):
    """Fax model that suppresses document and account values in validation errors."""

    model_config = ConfigDict(hide_input_in_errors=True)


class FaxTier(str, Enum):
    TIER_0 = "0"
    TIER_1 = "1"
    TIER_1B = "1b"
    TIER_2 = "2"
    TIER_3 = "3"


class FaxDIDType(str, Enum):
    LOCAL = "local"
    TOLL_FREE = "tf"


class FaxToggle(str, Enum):
    ON = "on"
    OFF = "off"


class FaxYesNo(str, Enum):
    YES = "yes"
    NO = "no"


class PauseAction(str, Enum):
    PAUSE = "pause"
    UNPAUSE = "unpause"


class UnsetAccount(str, Enum):
    ON = "on"


class FaxDIDStatus(OpenStringEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    PENDING = "pending"


def _validate_state(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z]{2}", value):
        raise ValueError("state must be a two-letter abbreviation")
    return value.upper()


def _validate_phone(value: int) -> int:
    digits = str(value)
    if len(digits) == 10 or (len(digits) == 11 and digits.startswith("1")):
        return value
    raise ValueError("fax number must contain 10 US digits or 11 digits beginning with 1")


def _validate_email(value: str) -> str:
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
        raise ValueError("email must be a valid email address")
    return value


def _validate_filename(value: str) -> str:
    filename = Path(value).name
    if filename != value or not filename:
        raise ValueError("filename must be a basename without directory components")
    if Path(filename).suffix.lower() not in SUPPORTED_FAX_EXTENSIONS:
        raise ValueError("filename extension is not supported by Fax.Pro")
    return value


def _validate_file_content(content: bytes) -> bytes:
    if not content:
        raise ValueError("fax file must not be empty")
    if len(content) > MAX_FAX_FILE_SIZE:
        raise ValueError("fax file must not exceed 8MB")
    return content


class FaxStatesResponse(FaxModel):
    data: List[str] = Field(default_factory=list)
    total: int = Field(default=0, ge=0)


class FaxRateCentersRequest(FaxModel):
    state: str

    @field_validator("state")
    @classmethod
    def validate_state(cls, value: str) -> str:
        return _validate_state(value)


class FaxRateCentersResponse(FaxModel):
    data: Dict[str, str] = Field(default_factory=dict)
    total: int = Field(default=0, ge=0)


class FaxAvailabilityRequest(FaxModel):
    did_type: FaxDIDType = Field(serialization_alias="type")
    tier: FaxTier = FaxTier.TIER_1B
    state: Optional[str] = None
    ratecenter: Optional[str] = None
    zip: Optional[int] = Field(default=None, ge=10000, le=99999)
    npa: Optional[int] = Field(default=None, ge=200, le=999)
    code: Optional[int] = Field(default=None, ge=20, le=99)

    @field_validator("state")
    @classmethod
    def validate_state(cls, value: Optional[str]) -> Optional[str]:
        return _validate_state(value) if value is not None else None

    @model_validator(mode="after")
    def validate_discovery(self) -> FaxAvailabilityRequest:
        if self.did_type is FaxDIDType.TOLL_FREE:
            if self.tier not in (FaxTier.TIER_1, FaxTier.TIER_1B):
                raise ValueError("toll-free Fax DIDs are available only in tiers 1 and 1b")
            if self.code is None:
                raise ValueError("toll-free discovery requires code")
        elif self.zip is None and self.npa is None and not (self.state and self.ratecenter):
            raise ValueError("local discovery requires zip, npa, or state and ratecenter")
        return self


class AvailableFaxDIDsResponse(FaxModel):
    data: List[str] = Field(default_factory=list)
    total: int = Field(default=0, ge=0)


class FaxListRequest(FaxModel):
    did: Optional[str] = None
    per_page: int = Field(default=25, ge=5, le=200)
    page: int = Field(default=1, ge=1)

    @field_validator("did")
    @classmethod
    def validate_search(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and len(re.sub(r"\D", "", value)) < 3:
            raise ValueError("did search must contain at least three digits")
        return value


class FaxConfiguration(FaxModel):
    note: Optional[str] = None
    pin: Optional[int] = Field(default=None, ge=1000, le=999999, repr=False)
    fax_name: Optional[str] = Field(default=None, min_length=1, repr=False)
    fax_login: Optional[str] = Field(default=None, min_length=1, repr=False)
    fax_password: Optional[str] = Field(default=None, min_length=1, repr=False)
    fax_email: Optional[str] = Field(default=None, repr=False)
    cnam: Optional[FaxToggle] = None
    is_full: Optional[FaxYesNo] = None
    report_att: Optional[FaxYesNo] = None
    post2url: Optional[str] = Field(default=None, repr=False)
    ata_mac_address: Optional[str] = Field(default=None, repr=False)

    @field_validator("fax_email")
    @classmethod
    def validate_email(cls, value: Optional[str]) -> Optional[str]:
        return _validate_email(value) if value is not None else None

    @field_validator("post2url")
    @classmethod
    def validate_url(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value == "empty":
            return value
        parsed = urlsplit(value)
        if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username:
            raise ValueError("post2url must be 'empty' or an absolute HTTP(S) URL")
        return value

    @field_validator("ata_mac_address")
    @classmethod
    def validate_mac(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        compact = re.sub(r"[:-]", "", value)
        if not re.fullmatch(r"[0-9A-Fa-f]{12}", compact):
            raise ValueError("ata_mac_address must contain 12 hexadecimal characters")
        return compact.upper()

    def account_fields_complete(self) -> bool:
        values = (self.fax_name, self.fax_login, self.fax_password, self.fax_email)
        return all(values) or not any(values)


class FaxOrderRequest(FaxConfiguration):
    did: int = Field(repr=False)
    tier: FaxTier = FaxTier.TIER_1B
    is_full: Optional[FaxYesNo] = FaxYesNo.NO

    @field_validator("did")
    @classmethod
    def validate_did(cls, value: int) -> int:
        return _validate_phone(value)

    @model_validator(mode="after")
    def validate_account(self) -> FaxOrderRequest:
        if not self.account_fields_complete():
            raise ValueError(
                "fax_name, fax_login, fax_password, and fax_email are required together"
            )
        return self


class FaxUpdateRequest(FaxConfiguration):
    did: int = Field(repr=False)
    unset_acc: Optional[UnsetAccount] = None

    @field_validator("did")
    @classmethod
    def validate_did(cls, value: int) -> int:
        return _validate_phone(value)

    @model_validator(mode="after")
    def validate_update(self) -> FaxUpdateRequest:
        changed = self.model_dump(exclude={"did"}, exclude_none=True)
        if not changed:
            raise ValueError("fax update requires at least one changed field")
        if self.unset_acc is not None and any(
            (self.fax_name, self.fax_login, self.fax_password, self.fax_email)
        ):
            raise ValueError("unset_acc cannot be combined with Fax.Pro account fields")
        if self.unset_acc is None and not self.account_fields_complete():
            raise ValueError(
                "fax_name, fax_login, fax_password, and fax_email are required together"
            )
        return self


class FaxDeleteRequest(FaxModel):
    did: int = Field(repr=False)

    @field_validator("did")
    @classmethod
    def validate_did(cls, value: int) -> int:
        return _validate_phone(value)


class FaxDIDRecord(FaxModel):
    did: str = Field(repr=False)
    did_type: str
    fax_login: str = Field(repr=False)
    fax_name: str = Field(repr=False)
    is_full: FaxYesNo
    note: str
    report_att: FaxYesNo
    status: FaxDIDStatus


class FaxInventoryResponse(FaxModel):
    data: List[FaxDIDRecord] = Field(default_factory=list)
    current_page: int = Field(default=1, ge=1)
    total: int = Field(default=0, ge=0)
    total_pages: int = Field(default=1, ge=0)

    def next_page(self) -> Optional[int]:
        return self.current_page + 1 if self.current_page < self.total_pages else None


class FaxSendRequest(FaxModel):
    file: str = Field(min_length=1, repr=False)
    filename: str
    did_from: int = Field(repr=False)
    did_to: int = Field(repr=False)

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, value: str) -> str:
        return _validate_filename(value)

    @field_validator("did_from", "did_to")
    @classmethod
    def validate_number(cls, value: int) -> int:
        return _validate_phone(value)

    @field_validator("file")
    @classmethod
    def validate_base64_file(cls, value: str) -> str:
        try:
            content = base64.b64decode(value, validate=True)
        except (binascii.Error, ValueError):
            raise ValueError("file must be valid base64") from None
        _validate_file_content(content)
        return value

    @classmethod
    def from_bytes(
        cls, content: bytes, filename: str, *, did_from: int, did_to: int
    ) -> FaxSendRequest:
        _validate_filename(filename)
        _validate_file_content(content)
        return cls(
            file=base64.b64encode(content).decode("ascii"),
            filename=filename,
            did_from=did_from,
            did_to=did_to,
        )

    @classmethod
    def from_file(
        cls, file: BinaryIO, filename: str, *, did_from: int, did_to: int
    ) -> FaxSendRequest:
        return cls.from_bytes(
            file.read(MAX_FAX_FILE_SIZE + 1), filename, did_from=did_from, did_to=did_to
        )

    @classmethod
    def from_path(cls, path: Union[str, Path], *, did_from: int, did_to: int) -> FaxSendRequest:
        source = Path(path)
        with source.open("rb") as file:
            return cls.from_file(file, source.name, did_from=did_from, did_to=did_to)


class SentFax(FaxModel):
    fax_id: int = Field(gt=0)


class FaxSendResponse(FaxModel):
    data: SentFax


class FaxMoveToVoiceRequest(FaxDeleteRequest):
    pass


class FaxPauseRequest(FaxDeleteRequest):
    action: PauseAction


class FaxEmailPermissionRequest(FaxDeleteRequest):
    email: str = Field(repr=False)
    allow_send: FaxYesNo = FaxYesNo.NO
    allow_receive: FaxYesNo = FaxYesNo.NO

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _validate_email(value)


class FaxEmailPermissionDeleteRequest(FaxDeleteRequest):
    email: str = Field(repr=False)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _validate_email(value)


FaxModelT = TypeVar("FaxModelT", bound=QuestBlueModel)


def parse_fax_response(model: Type[FaxModelT], payload: Any) -> Union[FaxModelT, WarningResponse]:
    if isinstance(payload, Mapping) and "warning" in payload:
        return WarningResponse.model_validate(payload)
    return model.model_validate(payload)


def parse_empty_fax_response(payload: Any) -> Optional[WarningResponse]:
    if payload is None or payload == "" or payload == {}:
        return None
    if isinstance(payload, Mapping) and "warning" in payload:
        return WarningResponse.model_validate(payload)
    raise QuestBlueResponseError("QuestBlue returned a body for an empty Fax.Pro response")
