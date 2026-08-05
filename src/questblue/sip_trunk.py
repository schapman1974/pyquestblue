"""Typed models for QuestBlue SIP Trunk operations."""

from __future__ import annotations

import ipaddress
import re
from enum import Enum
from typing import Any, List, Mapping, Optional, Type, TypeVar, Union

from pydantic import Field, field_validator, model_validator

from ._exceptions import QuestBlueResponseError
from .models import OpenStringEnum, QuestBlueModel, WarningResponse, YesNo


class SIPRegion(str, Enum):
    US = "us"
    US_CA = "us-ca"
    US_FL = "us-fl"
    US_IL = "us-il"
    US_NY = "us-ny"
    AU = "au"
    CA = "ca"
    FR = "fr"
    DE = "de"
    MX = "mx"
    PL = "pl"
    SG = "sg"
    UK = "uk"


class TrunkToggle(str, Enum):
    ON = "on"
    OFF = "off"


class BlockAction(str, Enum):
    BLOCK = "block"
    UNBLOCK = "unblock"


class RegistrationStatus(OpenStringEnum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"


class SIPTrunkListRequest(QuestBlueModel):
    trunk: Optional[str] = None
    per_page: int = Field(default=25, ge=5, le=200)
    page: int = Field(default=1, ge=1)


class SIPTrunkConfigurationRequest(QuestBlueModel):
    trunk: str = Field(min_length=1, max_length=30, pattern=r"^[A-Za-z0-9]+$")
    password: Optional[str] = Field(
        default=None, min_length=4, max_length=38, pattern=r"^[A-Za-z0-9]+$"
    )
    ip_address: Optional[str] = None
    region: Optional[SIPRegion] = None
    did: Optional[int] = Field(default=None, gt=0)
    inter_call: Optional[str] = Field(default=None, pattern=r"^off$")
    inter_limit: Optional[int] = Field(default=None, ge=1, le=1000)
    tn2forward: Optional[int] = Field(default=None, gt=0)
    concurrent_max: Optional[str] = None
    allow_e164_rewrite: Optional[YesNo] = None
    allow_rtp_proxy: Optional[YesNo] = None

    @field_validator("ip_address")
    @classmethod
    def validate_address(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        try:
            ipaddress.ip_address(value)
        except ValueError:
            if not re.fullmatch(
                r"(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)*[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?",
                value,
            ):
                raise ValueError("ip_address must be an IP address or FQDN") from None
        return value


class SIPTrunkCreateRequest(SIPTrunkConfigurationRequest):
    @model_validator(mode="after")
    def validate_registration(self) -> SIPTrunkCreateRequest:
        if self.password is None and self.ip_address is None:
            raise ValueError(
                "create requires password for registration or ip_address for static routing"
            )
        return self


class SIPTrunkUpdateRequest(SIPTrunkConfigurationRequest):
    status: Optional[TrunkToggle] = None


class SIPTrunkDeleteRequest(QuestBlueModel):
    trunk: str = Field(min_length=1, max_length=30)


class SIPTrunkStatusRequest(QuestBlueModel):
    trunk: str = Field(min_length=1, max_length=30)


class BlockCallerRequest(QuestBlueModel):
    trunk: Union[str, List[str]]
    did: int = Field(gt=0)
    action: BlockAction


class BlockedCallersRequest(QuestBlueModel):
    trunk: Optional[Union[str, List[str]]] = None
    did: Optional[int] = Field(default=None, gt=0)
    per_page: int = Field(default=25, ge=5, le=200)
    page: int = Field(default=1, ge=1)


class SIPTrunkInventoryResponse(QuestBlueModel):
    data: Mapping[str, List[str]] = Field(default_factory=dict)
    current_page: int = Field(default=1, ge=1)
    total: int = Field(default=0, ge=0)
    total_pages: int = Field(default=1, ge=0)

    def next_page(self) -> Optional[int]:
        return self.current_page + 1 if self.current_page < self.total_pages else None


class SIPTrunkStatusResponse(QuestBlueModel):
    data: Mapping[str, List[str]] = Field(default_factory=dict)
    res: RegistrationStatus
    total: int = Field(default=0, ge=0)


class BlockedCaller(QuestBlueModel):
    did: str
    ip_address: str
    status: str
    trunk: str


class BlockedCallersResponse(QuestBlueModel):
    data: List[BlockedCaller] = Field(default_factory=list)
    current_page: int = Field(default=1, ge=1)
    total: int = Field(default=0, ge=0)
    total_pages: int = Field(default=1, ge=0)


SIPModelT = TypeVar("SIPModelT", bound=QuestBlueModel)


def parse_sip_response(model: Type[SIPModelT], payload: Any) -> Union[SIPModelT, WarningResponse]:
    if isinstance(payload, Mapping) and "warning" in payload:
        return WarningResponse.model_validate(payload)
    return model.model_validate(payload)


def parse_empty_sip_response(payload: Any) -> Optional[WarningResponse]:
    if payload is None or payload == "" or payload == {}:
        return None
    if isinstance(payload, Mapping) and "warning" in payload:
        return WarningResponse.model_validate(payload)
    raise QuestBlueResponseError("QuestBlue returned a body for an empty SIP trunk response")
