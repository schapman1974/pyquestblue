"""Typed models and file helpers for QuestBlue iFax Enterprise operations."""

from __future__ import annotations

import base64
import binascii
import re
from pathlib import Path
from typing import Any, BinaryIO, List, Mapping, Optional, Type, TypeVar, Union
from urllib.parse import urlsplit

from pydantic import ConfigDict, Field, field_validator, model_validator

from ._exceptions import QuestBlueResponseError
from .fax import (
    MAX_FAX_FILE_SIZE,
    FaxDIDStatus,
    FaxTier,
    FaxToggle,
    FaxYesNo,
    PauseAction,
    _validate_email,
    _validate_file_content,
    _validate_filename,
    _validate_phone,
)
from .models import QuestBlueModel, WarningResponse


class EnterpriseFaxModel(QuestBlueModel):
    model_config = ConfigDict(hide_input_in_errors=True)


class EnterpriseFaxListRequest(EnterpriseFaxModel):
    did: Optional[str] = None
    per_page: int = Field(default=25, ge=5, le=200)
    page: int = Field(default=1, ge=1)

    @field_validator("did")
    @classmethod
    def validate_search(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and len(re.sub(r"\D", "", value)) < 3:
            raise ValueError("did search must contain at least three digits")
        return value


class EnterpriseFaxDIDConfiguration(EnterpriseFaxModel):
    note: Optional[str] = None
    pin: Optional[int] = Field(default=None, ge=1000, le=999999, repr=False)
    sname: Optional[str] = Field(default=None, max_length=24)
    cnam: Optional[FaxToggle] = None
    post2url: Optional[str] = Field(default=None, repr=False)
    ata_mac_address: Optional[str] = Field(default=None, repr=False)

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
        if value is None or value == "empty":
            return value
        compact = re.sub(r"[:-]", "", value)
        if not re.fullmatch(r"[0-9A-Fa-f]{12}", compact):
            raise ValueError("ata_mac_address must contain 12 hexadecimal characters")
        return compact.upper()


class EnterpriseFaxOrderRequest(EnterpriseFaxDIDConfiguration):
    did: int = Field(repr=False)
    tier: FaxTier = FaxTier.TIER_1B

    @field_validator("did")
    @classmethod
    def validate_did(cls, value: int) -> int:
        return _validate_phone(value)


class EnterpriseFaxUpdateRequest(EnterpriseFaxDIDConfiguration):
    did: int = Field(repr=False)

    @field_validator("did")
    @classmethod
    def validate_did(cls, value: int) -> int:
        return _validate_phone(value)

    @model_validator(mode="after")
    def validate_update(self) -> EnterpriseFaxUpdateRequest:
        if not self.model_dump(exclude={"did"}, exclude_none=True):
            raise ValueError("enterprise Fax DID update requires at least one changed field")
        return self


class EnterpriseFaxDeleteRequest(EnterpriseFaxModel):
    did: int = Field(repr=False)

    @field_validator("did")
    @classmethod
    def validate_did(cls, value: int) -> int:
        return _validate_phone(value)


class EnterpriseFaxDIDRecord(EnterpriseFaxModel):
    did: str = Field(repr=False)
    did_type: str
    note: str
    sname: str
    status: FaxDIDStatus


class EnterpriseFaxInventoryResponse(EnterpriseFaxModel):
    data: List[EnterpriseFaxDIDRecord] = Field(default_factory=list)
    current_page: int = Field(default=1, ge=1)
    total: int = Field(default=0, ge=0)
    total_pages: int = Field(default=1, ge=0)

    def next_page(self) -> Optional[int]:
        return self.current_page + 1 if self.current_page < self.total_pages else None


class EnterpriseFaxEmailListRequest(EnterpriseFaxModel):
    did: Optional[int] = Field(default=None, repr=False)
    email: Optional[str] = Field(default=None, repr=False)

    @field_validator("did")
    @classmethod
    def validate_did(cls, value: Optional[int]) -> Optional[int]:
        return _validate_phone(value) if value is not None else None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: Optional[str]) -> Optional[str]:
        return _validate_email(value) if value is not None else None


class EnterpriseFaxEmailPermissionRequest(EnterpriseFaxDeleteRequest):
    email: str = Field(repr=False)
    allow_send: FaxToggle = FaxToggle.OFF
    allow_receive: FaxToggle = FaxToggle.OFF

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _validate_email(value)


class EnterpriseFaxEmailPermissionDeleteRequest(EnterpriseFaxDeleteRequest):
    email: str = Field(repr=False)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _validate_email(value)


class EnterpriseFaxEmailPermission(EnterpriseFaxModel):
    did: str = Field(repr=False)
    email: str = Field(repr=False)
    sname: str
    allow_send: FaxYesNo
    allow_receive: FaxYesNo


class EnterpriseFaxEmailListResponse(EnterpriseFaxModel):
    data: List[EnterpriseFaxEmailPermission] = Field(default_factory=list)
    current_page: int = Field(default=1, ge=1)
    total: int = Field(default=0, ge=0)
    total_pages: int = Field(default=1, ge=0)


class EnterpriseFaxGroupListRequest(EnterpriseFaxModel):
    sname: Optional[str] = Field(default=None, min_length=1, max_length=24)


class EnterpriseFaxGroupCreateRequest(EnterpriseFaxModel):
    sname: str = Field(min_length=1, max_length=24)
    name: str = Field(min_length=1, max_length=128)


class EnterpriseFaxGroupUpdateRequest(EnterpriseFaxModel):
    sname: str = Field(min_length=1, max_length=24)
    sname_new: str = Field(min_length=1, max_length=24)
    name_new: str = Field(min_length=1, max_length=128)


class EnterpriseFaxGroupDeleteRequest(EnterpriseFaxModel):
    sname: str = Field(min_length=1, max_length=24)


class EnterpriseFaxGroup(EnterpriseFaxModel):
    sname: str
    name: str


class EnterpriseFaxGroupListResponse(EnterpriseFaxModel):
    data: List[EnterpriseFaxGroup] = Field(default_factory=list)
    total: int = Field(default=0, ge=0)


class EnterpriseFaxUserListRequest(EnterpriseFaxModel):
    sname: Optional[str] = Field(default=None, max_length=24)
    fax_login: Optional[str] = Field(default=None, max_length=36, repr=False)


class EnterpriseFaxUserCreateRequest(EnterpriseFaxModel):
    fax_login: str = Field(min_length=1, max_length=36, repr=False)
    fax_password: str = Field(min_length=1, max_length=64, repr=False)
    sname: str = Field(min_length=1, max_length=24)
    fax_name: str = Field(min_length=1, max_length=48, repr=False)
    fax_lname: Optional[str] = Field(default=None, max_length=48, repr=False)
    fax_email: Optional[str] = Field(default=None, repr=False)
    is_admin: FaxToggle = FaxToggle.OFF

    @field_validator("fax_email")
    @classmethod
    def validate_email(cls, value: Optional[str]) -> Optional[str]:
        return _validate_email(value) if value is not None else None


class EnterpriseFaxUserUpdateRequest(EnterpriseFaxModel):
    fax_login: str = Field(min_length=1, max_length=36, repr=False)
    fax_login_new: Optional[str] = Field(default=None, min_length=1, max_length=36, repr=False)
    fax_password: Optional[str] = Field(default=None, min_length=1, max_length=64, repr=False)
    fax_name: Optional[str] = Field(default=None, min_length=1, max_length=48, repr=False)
    fax_lname: Optional[str] = Field(default=None, max_length=48, repr=False)
    fax_email: Optional[str] = Field(default=None, repr=False)
    is_admin: Optional[FaxToggle] = None

    @field_validator("fax_email")
    @classmethod
    def validate_email(cls, value: Optional[str]) -> Optional[str]:
        return _validate_email(value) if value is not None else None

    @model_validator(mode="after")
    def validate_update(self) -> EnterpriseFaxUserUpdateRequest:
        if not self.model_dump(exclude={"fax_login"}, exclude_none=True):
            raise ValueError("enterprise fax user update requires at least one changed field")
        return self


class EnterpriseFaxUserDeleteRequest(EnterpriseFaxModel):
    fax_login: str = Field(min_length=1, max_length=36, repr=False)


class EnterpriseFaxUser(EnterpriseFaxModel):
    fax_lname: str = Field(repr=False)
    fax_name: str = Field(repr=False)
    is_admin: FaxToggle
    login: str = Field(repr=False)
    password: str = Field(repr=False)
    sname: str


class EnterpriseFaxUserListResponse(EnterpriseFaxModel):
    data: List[EnterpriseFaxUser] = Field(default_factory=list)
    current_page: int = Field(default=1, ge=1)
    total: int = Field(default=0, ge=0)
    total_pages: int = Field(default=1, ge=0)


class EnterpriseFaxPermissionListRequest(EnterpriseFaxModel):
    fax_login: Optional[str] = Field(default=None, max_length=36, repr=False)
    did: Optional[int] = Field(default=None, repr=False)

    @field_validator("did")
    @classmethod
    def validate_did(cls, value: Optional[int]) -> Optional[int]:
        return _validate_phone(value) if value is not None else None


class EnterpriseFaxPermissionRequest(EnterpriseFaxModel):
    fax_login: str = Field(min_length=1, max_length=36, repr=False)
    did: int = Field(repr=False)
    allow_send: FaxToggle
    allow_delete: FaxToggle
    allow_list_in: FaxToggle
    allow_list_out: FaxToggle

    @field_validator("did")
    @classmethod
    def validate_did(cls, value: int) -> int:
        return _validate_phone(value)


class EnterpriseFaxPermissionDeleteRequest(EnterpriseFaxModel):
    fax_login: str = Field(min_length=1, max_length=36, repr=False)
    did: int = Field(repr=False)

    @field_validator("did")
    @classmethod
    def validate_did(cls, value: int) -> int:
        return _validate_phone(value)


class EnterpriseFaxPermission(EnterpriseFaxModel):
    fax_login: str = Field(repr=False)
    did: str = Field(repr=False)
    allow_send: FaxToggle
    allow_delete: FaxToggle
    allow_list_in: FaxToggle
    allow_list_out: FaxToggle
    create_date: str


class EnterpriseFaxPermissionListResponse(EnterpriseFaxModel):
    data: List[EnterpriseFaxPermission] = Field(default_factory=list)
    current_page: int = Field(default=1, ge=1)
    total: int = Field(default=0, ge=0)
    total_pages: int = Field(default=1, ge=0)


class EnterpriseFaxUploadRequest(EnterpriseFaxModel):
    file: str = Field(min_length=1, repr=False)
    filename: str

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, value: str) -> str:
        return _validate_filename(value)

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
    def from_bytes(cls, content: bytes, filename: str) -> EnterpriseFaxUploadRequest:
        _validate_filename(filename)
        _validate_file_content(content)
        return cls(file=base64.b64encode(content).decode("ascii"), filename=filename)

    @classmethod
    def from_file(cls, file: BinaryIO, filename: str) -> EnterpriseFaxUploadRequest:
        return cls.from_bytes(file.read(MAX_FAX_FILE_SIZE + 1), filename)

    @classmethod
    def from_path(cls, path: Union[str, Path]) -> EnterpriseFaxUploadRequest:
        source = Path(path)
        with source.open("rb") as file:
            return cls.from_file(file, source.name)


class EnterpriseFaxUploadResponse(EnterpriseFaxModel):
    file_id: str = Field(min_length=1)


class EnterpriseFaxSendRequest(EnterpriseFaxModel):
    did_from: int = Field(repr=False)
    did_to: int = Field(repr=False)
    file_id: List[str] = Field(min_length=1, repr=False)

    @field_validator("did_from", "did_to")
    @classmethod
    def validate_number(cls, value: int) -> int:
        return _validate_phone(value)

    @field_validator("file_id")
    @classmethod
    def validate_file_ids(cls, value: List[str]) -> List[str]:
        if any(not item.strip() for item in value):
            raise ValueError("file_id values must not be empty")
        return value


class EnterpriseFaxSendResponse(EnterpriseFaxModel):
    fax_id: int = Field(gt=0)


class EnterpriseFaxPauseRequest(EnterpriseFaxDeleteRequest):
    action: PauseAction


EnterpriseFaxModelT = TypeVar("EnterpriseFaxModelT", bound=QuestBlueModel)


def parse_enterprise_fax_response(
    model: Type[EnterpriseFaxModelT], payload: Any
) -> Union[EnterpriseFaxModelT, WarningResponse]:
    if isinstance(payload, Mapping) and "warning" in payload:
        return WarningResponse.model_validate(payload)
    return model.model_validate(payload)


def parse_empty_enterprise_fax_response(payload: Any) -> Optional[WarningResponse]:
    if payload is None or payload == "" or payload == {}:
        return None
    if isinstance(payload, Mapping) and "warning" in payload:
        return WarningResponse.model_validate(payload)
    raise QuestBlueResponseError("QuestBlue returned a body for an empty iFax Enterprise response")
