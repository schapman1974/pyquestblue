"""Typed models and validation for QuestBlue Voice DID operations."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Type, TypeVar, Union

from pydantic import Field, field_validator, model_validator

from ._exceptions import QuestBlueResponseError
from .account import AccountToggle
from .models import QuestBlueModel, ResponseEnvelope, WarningResponse, YesNo


class DIDTier(str, Enum):
    TIER_0 = "0"
    TIER_1 = "1"
    TIER_1B = "1b"
    TIER_2 = "2"


class DIDType(str, Enum):
    LOCAL = "local"
    TOLL_FREE = "tf"


class DirectoryListingType(str, Enum):
    BUSINESS = "business"
    RESIDENTIAL = "residential"


class E911UnitType(str, Enum):
    UNIT = "unit"
    SUITE = "suite"
    APARTMENT = "apt"


class DIDListRequest(QuestBlueModel):
    did: Optional[str] = None
    per_page: int = Field(default=25, ge=5, le=200)
    page: int = Field(default=1, ge=1)

    @field_validator("did")
    @classmethod
    def validate_search(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and len(re.sub(r"\D", "", value)) < 3:
            raise ValueError("did search must contain at least three digits")
        return value


class DIDAvailabilityRequest(QuestBlueModel):
    did_type: DIDType = Field(serialization_alias="type")
    tier: Optional[DIDTier] = None
    state: Optional[str] = None
    ratecenter: Optional[str] = None
    zip: Optional[int] = Field(default=None, ge=10000, le=99999)
    code: Optional[int] = Field(default=None, ge=10, le=99)
    mask: Optional[str] = None
    total_list: int = Field(default=100, ge=1)

    @field_validator("state")
    @classmethod
    def validate_state(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not re.fullmatch(r"[A-Za-z]{2}", value):
            raise ValueError("state must be a two-letter abbreviation")
        return value.upper()

    @field_validator("mask")
    @classmethod
    def validate_mask(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and len(re.sub(r"\D", "", value)) < 3:
            raise ValueError("mask must contain at least three digits")
        return value

    @model_validator(mode="after")
    def validate_discovery_filters(self) -> DIDAvailabilityRequest:
        if (
            self.did_type is DIDType.LOCAL
            and self.zip is None
            and self.mask is None
            and (not self.state or not self.ratecenter)
        ):
            raise ValueError("local discovery requires zip, mask, or state and ratecenter")
        if self.did_type is DIDType.TOLL_FREE and self.mask is None and self.code is None:
            raise ValueError("toll-free discovery requires mask or code")
        return self


class DIDConfigurationRequest(QuestBlueModel):
    route2trunk: Optional[str] = None
    cnam: Optional[AccountToggle] = None
    note: Optional[str] = Field(default=None, max_length=100)
    pin: Optional[int] = None
    lidb: Optional[str] = Field(default=None, min_length=4, max_length=15)
    e911_name: Optional[str] = None
    e911_city: Optional[str] = None
    e911_state: Optional[str] = None
    e911_zip: Optional[str] = Field(default=None, min_length=5, max_length=10)
    e911_address: Optional[str] = None
    e911_unittype: Optional[E911UnitType] = None
    e911_unitnumber: Optional[str] = None
    dlda: Optional[YesNo] = None
    dlda_type: Optional[DirectoryListingType] = None
    dlda_firstname: Optional[str] = None
    dlda_lastname: Optional[str] = None
    dlda_streetnum: Optional[str] = None
    dlda_streetname: Optional[str] = None
    dlda_city: Optional[str] = None
    dlda_state: Optional[str] = None
    dlda_zip: Optional[str] = Field(default=None, min_length=5, max_length=10)
    dlda_email: Optional[str] = None
    dlda_phone: Optional[str] = None

    @field_validator("pin")
    @classmethod
    def validate_pin(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and not 1000 <= value <= 999999:
            raise ValueError("pin must contain four to six digits")
        return value

    @field_validator("lidb")
    @classmethod
    def validate_lidb(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not re.fullmatch(r"[A-Za-z0-9 ]+", value):
            raise ValueError("lidb must be alphanumeric")
        return value

    @field_validator("e911_state", "dlda_state")
    @classmethod
    def validate_optional_state(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not re.fullmatch(r"[A-Za-z]{2}", value):
            raise ValueError("state must be a two-letter abbreviation")
        return value.upper()


class DIDOrderRequest(DIDConfigurationRequest):
    did: Union[int, List[int]]
    tier: Optional[DIDTier] = None

    @field_validator("did")
    @classmethod
    def validate_dids(cls, value: Union[int, List[int]]) -> Union[int, List[int]]:
        values = value if isinstance(value, list) else [value]
        if not values or any(did <= 0 for did in values):
            raise ValueError("did must contain one or more positive numbers")
        return value


class DIDUpdateRequest(DIDConfigurationRequest):
    did: int = Field(gt=0)
    forw2did: Optional[int] = Field(default=None, gt=0)
    failover: Optional[List[List[str]]] = None
    e911: Optional[YesNo] = None
    e911_call_alert: Optional[List[List[str]]] = None


class DIDDeleteRequest(QuestBlueModel):
    did: int = Field(gt=0)


class DIDMoveToFaxRequest(QuestBlueModel):
    did: int = Field(gt=0)


class DIDRateCentersRequest(QuestBlueModel):
    state: str
    tier: DIDTier

    @field_validator("state")
    @classmethod
    def validate_state(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z]{2}", value):
            raise ValueError("state must be a two-letter abbreviation")
        return value.upper()


class DIDFraudValidationRequest(QuestBlueModel):
    tn: Union[int, List[int]]

    @field_validator("tn")
    @classmethod
    def validate_numbers(cls, value: Union[int, List[int]]) -> Union[int, List[int]]:
        values = value if isinstance(value, list) else [value]
        if not values or len(values) > 100 or any(number <= 0 for number in values):
            raise ValueError("tn must contain between one and 100 positive numbers")
        return value


class DIDInventoryResponse(QuestBlueModel):
    data: Dict[str, List[str]] = Field(default_factory=dict)
    current_page: int = Field(default=1, ge=1)
    total: int = Field(default=0, ge=0)
    total_pages: int = Field(default=1, ge=0)

    def next_page(self) -> Optional[int]:
        return self.current_page + 1 if self.current_page < self.total_pages else None


class DIDStatesResponse(ResponseEnvelope[List[str]]):
    data: List[str]
    total: int = Field(ge=0)


class DIDRateCentersResponse(ResponseEnvelope[Dict[str, str]]):
    data: Dict[str, str]
    total: int = Field(ge=0)


class AvailableDIDsResponse(ResponseEnvelope[List[str]]):
    data: List[str]
    total: int = Field(ge=0)


class FraudValidationResponse(ResponseEnvelope[List[Dict[str, str]]]):
    data: List[Dict[str, str]]


DIDModelT = TypeVar("DIDModelT", bound=QuestBlueModel)


def parse_did_response(model: Type[DIDModelT], payload: Any) -> Union[DIDModelT, WarningResponse]:
    if isinstance(payload, Mapping) and "warning" in payload:
        return WarningResponse.model_validate(payload)
    return model.model_validate(payload)


def parse_empty_did_response(payload: Any) -> Optional[WarningResponse]:
    if payload is None or payload == "" or payload == {}:
        return None
    if isinstance(payload, Mapping) and "warning" in payload:
        return WarningResponse.model_validate(payload)
    raise QuestBlueResponseError("QuestBlue returned a body for an empty DID response")
