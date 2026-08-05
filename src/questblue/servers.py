"""Typed models for QuestBlue VoIP server operations."""

from __future__ import annotations

import ipaddress
import re
from datetime import date
from enum import Enum
from typing import Any, List, Mapping, Optional, Type, TypeVar, Union

from pydantic import ConfigDict, Field, field_validator, model_validator

from ._exceptions import QuestBlueResponseError
from .models import OpenStringEnum, QuestBlueModel, WarningResponse


class ServerModel(QuestBlueModel):
    model_config = ConfigDict(hide_input_in_errors=True, populate_by_name=True)


class ServerType(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"
    ENTERPRISE_PLUS_PLUS = "enterpriseplusplus"


class UpgradeServerType(str, Enum):
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"
    ENTERPRISE_PLUS_PLUS = "enterpriseplusplus"


class BackupSchedule(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    NONE = "none"


class ServerStatus(OpenStringEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


def _email(value: str) -> str:
    if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value) is None:
        raise ValueError("email must be a valid email address")
    return value


class EmailConfig(ServerModel):
    email: str = Field(repr=False)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _email(value)


class ThreeCXConfig(EmailConfig):
    admin_email: Optional[str] = Field(default=None, repr=False)
    admin_password: Optional[str] = Field(default=None, repr=False)
    inbound_trunk_name: Optional[str] = None
    license_company_name: Optional[str] = Field(default=None, repr=False)
    license_contact_name: Optional[str] = Field(default=None, repr=False)
    license_email: Optional[str] = Field(default=None, repr=False)
    license_key: Optional[str] = Field(default=None, repr=False)
    license_phone: Optional[str] = Field(default=None, repr=False)

    @field_validator("admin_email", "license_email")
    @classmethod
    def validate_optional_email(cls, value: Optional[str]) -> Optional[str]:
        return _email(value) if value is not None else None


class DomainConfig(EmailConfig):
    domain_name: str
    password: str = Field(repr=False)


class MassTextConfig(DomainConfig):
    inbound_trunk_name: str
    username: str = Field(repr=False)


class QubeConfig(EmailConfig):
    inbound_trunk_name: str
    password: str = Field(repr=False)


class QubeTDRConfig(DomainConfig):
    inbound_trunk_name: str


class QubeV2Config(DomainConfig):
    pass


class SBCConfig(EmailConfig):
    inbound_trunk_name: str
    sbcuser_password: str = Field(repr=False)


class VitalPBXConfig(EmailConfig):
    pass


class VodiaConfig(EmailConfig):
    company: str = Field(repr=False)
    did: str = Field(repr=False)
    inbound_trunk_name: str
    password: str = Field(repr=False)


class ServerSoftware(ServerModel):
    three_cx: Optional[ThreeCXConfig] = Field(default=None, alias="3cx")
    masstext: Optional[MassTextConfig] = None
    note: Optional[str] = Field(default=None, max_length=255)
    qube: Optional[QubeConfig] = None
    qube_tdr: Optional[QubeTDRConfig] = Field(default=None, alias="qube-tdr")
    qubev2: Optional[QubeV2Config] = None
    sbc: Optional[SBCConfig] = None
    vital_pbx: Optional[VitalPBXConfig] = Field(default=None, alias="vital-pbx")
    vodia: Optional[VodiaConfig] = None

    @model_validator(mode="after")
    def validate_product(self) -> ServerSoftware:
        if not self.model_dump(exclude={"note"}, exclude_none=True):
            raise ValueError("at least one server software configuration is required")
        return self


class ServerOrderRequest(ServerModel):
    server_type: ServerType
    params: ServerSoftware


class ServerOrderData(ServerModel):
    server_id: int = Field(gt=0, repr=False)


class ServerOrderResponse(ServerModel):
    data: ServerOrderData


class ServerListRequest(ServerModel):
    server_id: Optional[List[int]] = Field(default=None, repr=False)

    @field_validator("server_id")
    @classmethod
    def validate_ids(cls, value: Optional[List[int]]) -> Optional[List[int]]:
        if value is not None and (not value or any(item <= 0 for item in value)):
            raise ValueError("server_id must contain positive IDs")
        return value


class ServerRecord(ServerModel):
    allowed_ip: List[str] = Field(default_factory=list, repr=False)
    ordered_by: date
    server_id: int = Field(gt=0, repr=False)
    status: ServerStatus
    type: ServerType

    @field_validator("allowed_ip")
    @classmethod
    def validate_ips(cls, value: List[str]) -> List[str]:
        for item in value:
            ipaddress.ip_address(item)
        return value


class ServerListResponse(ServerModel):
    data: List[ServerRecord] = Field(default_factory=list)
    total: int = Field(default=0, ge=0)


class ServerIDRequest(ServerModel):
    server_id: int = Field(gt=0, repr=False)


class ServerIPRequest(ServerIDRequest):
    ip_address: str = Field(repr=False)
    note: Optional[str] = Field(default=None, max_length=64)

    @field_validator("ip_address")
    @classmethod
    def validate_ip(cls, value: str) -> str:
        return str(ipaddress.ip_address(value))


class ServerUpgradeRequest(ServerIDRequest):
    server_type: UpgradeServerType


class BackupScheduleRequest(ServerIDRequest):
    schedule: BackupSchedule


class BackupRequest(ServerIDRequest):
    backup_id: int = Field(gt=0, repr=False)


class BackupRecord(ServerModel):
    backup_id: int = Field(gt=0, repr=False)
    name: str
    type: str


class BackupListResponse(ServerModel):
    data: List[BackupRecord] = Field(default_factory=list)
    total: int = Field(default=0, ge=0)


class ServerMessageResponse(ServerModel):
    message: str


ServerModelT = TypeVar("ServerModelT", bound=QuestBlueModel)


def parse_server_response(
    model: Type[ServerModelT], payload: Any
) -> Union[ServerModelT, WarningResponse]:
    if isinstance(payload, Mapping) and "warning" in payload:
        return WarningResponse.model_validate(payload)
    try:
        return model.model_validate(payload)
    except (TypeError, ValueError) as exc:
        raise QuestBlueResponseError("QuestBlue returned an invalid server response") from exc


def parse_empty_server_response(payload: Any) -> Optional[WarningResponse]:
    if payload is None or payload == {} or payload == "":
        return None
    result = parse_server_response(WarningResponse, payload)
    return result if isinstance(result, WarningResponse) else None
