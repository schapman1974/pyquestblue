"""Typed models and validation for QuestBlue 10DLC brand and campaign operations."""

from __future__ import annotations

import re
from enum import Enum, IntEnum
from typing import Any, List, Mapping, Optional, Type, TypeVar, Union
from urllib.parse import urlsplit

from pydantic import ConfigDict, Field, field_validator, model_validator

from ._exceptions import QuestBlueResponseError
from .models import OpenStringEnum, QuestBlueModel, WarningResponse


class DLCModel(QuestBlueModel):
    """10DLC model that suppresses registration data in validation diagnostics."""

    model_config = ConfigDict(hide_input_in_errors=True)


class BrandLegalType(IntEnum):
    PUBLICLY_TRADED = 1
    PRIVATE = 2
    NON_PROFIT = 3
    GOVERNMENT = 4


class LEINumberType(str, Enum):
    DUNS = "duns"
    GIIN = "giin"
    LEI = "lei"


class CampaignType(str, Enum):
    STANDARD = "standard"
    SPECIAL = "special"


class StandardCampaignType(IntEnum):
    TWO_FACTOR_AUTHENTICATION = 1
    ACCOUNT_NOTIFICATION = 2
    CUSTOMER_CARE = 3
    DELIVERY_NOTIFICATION = 4
    FRAUD_ALERT_MESSAGING = 5
    HIGHER_EDUCATION = 6
    LOW_VOLUME_MIXED = 7
    MARKETING = 8
    MIXED = 9
    POLLING_AND_VOTING = 10
    PUBLIC_SERVICE_ANNOUNCEMENT = 11
    SECURITY_ALERT = 12


class SpecialCampaignType(IntEnum):
    AGENTS_AND_FRANCHISES = 1
    CARRIER_EXEMPTIONS = 2
    CHARITY = 3
    EMERGENCY = 4
    K12_EDUCATION = 5
    POLITICAL = 6
    PROXY = 7
    SOCIAL = 8
    SOLE_PROPRIETOR = 9
    SWEEPSTAKE = 10


class DLCYesNo(str, Enum):
    YES = "yes"
    NO = "no"


class HelpReply(str, Enum):
    YES = "yes"


class BrandStatus(OpenStringEnum):
    APPROVED = "Approved"
    PENDING = "Pending"
    REJECTED = "Rejected"


class CampaignStatus(OpenStringEnum):
    SUBMITTED = "Submitted"
    APPROVED = "Approved"
    PENDING = "Pending"
    REJECTED = "Rejected"


def _validate_ids(value: Union[int, List[int]]) -> Union[int, List[int]]:
    values = value if isinstance(value, list) else [value]
    if not values or any(identifier <= 0 for identifier in values):
        raise ValueError("id must contain one or more positive identifiers")
    return value


def _validate_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username:
        raise ValueError("url must be an absolute HTTP(S) URL without credentials")
    return value


def _validate_campaign_dids(value: Union[str, int, List[int]]) -> Union[str, int, List[int]]:
    if isinstance(value, str):
        values = [item for item in re.split(r"[\s,]+", value.strip()) if item]
        if not values or any(not item.isdigit() for item in values):
            raise ValueError(
                "campaign_did must contain phone numbers separated by commas or spaces"
            )
        numbers = [int(item) for item in values]
    elif isinstance(value, list):
        if not value:
            raise ValueError("campaign_did must contain at least one phone number")
        numbers = value
    else:
        numbers = [value]
    for number in numbers:
        digits = str(number)
        if len(digits) != 10 and not (len(digits) == 11 and digits.startswith("1")):
            raise ValueError(
                "campaign DIDs must contain 10 US digits or 11 digits beginning with 1"
            )
    return value


class BrandListRequest(DLCModel):
    id: Optional[Union[int, List[int]]] = None

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: Optional[Union[int, List[int]]]) -> Optional[Union[int, List[int]]]:
        return _validate_ids(value) if value is not None else None


class BrandCreateRequest(DLCModel):
    company_name: str = Field(min_length=1)
    legal_type: BrandLegalType
    vertical_type: int = Field(gt=0)
    tax_number: str = Field(min_length=1, repr=False)
    lei_number_type: Optional[LEINumberType] = None
    lei_number: Optional[str] = Field(default=None, min_length=1, repr=False)
    contact: str = Field(min_length=1, repr=False)
    address: str = Field(min_length=1, repr=False)
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        return _validate_url(value)

    @model_validator(mode="after")
    def validate_lei_pair(self) -> BrandCreateRequest:
        if (self.lei_number is None) != (self.lei_number_type is None):
            raise ValueError("lei_number and lei_number_type must be provided together")
        return self


class BrandUpdateRequest(DLCModel):
    id: int = Field(gt=0)
    company_name: Optional[str] = Field(default=None, min_length=1)
    legal_type: Optional[BrandLegalType] = None
    vertical_type: Optional[int] = Field(default=None, gt=0)
    tax_number: Optional[str] = Field(default=None, min_length=1, repr=False)
    lei_number_type: Optional[LEINumberType] = None
    lei_number: Optional[str] = Field(default=None, min_length=1, repr=False)
    contact: Optional[str] = Field(default=None, min_length=1, repr=False)
    address: Optional[str] = Field(default=None, min_length=1, repr=False)
    url: Optional[str] = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: Optional[str]) -> Optional[str]:
        return _validate_url(value) if value is not None else None

    @model_validator(mode="after")
    def validate_update(self) -> BrandUpdateRequest:
        values = self.model_dump(exclude={"id"}, exclude_none=True)
        if not values:
            raise ValueError("brand update requires at least one changed field")
        if self.lei_number is not None and self.lei_number_type is None:
            raise ValueError("lei_number_type is required when lei_number is provided")
        return self


class BrandDeleteRequest(DLCModel):
    id: int = Field(gt=0)


class CampaignListRequest(DLCModel):
    id: Optional[Union[int, List[int]]] = None

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: Optional[Union[int, List[int]]]) -> Optional[Union[int, List[int]]]:
        return _validate_ids(value) if value is not None else None


class CampaignConfigurationRequest(DLCModel):
    brand_id: int = Field(gt=0)
    campaign_type: CampaignType
    campaign_type_standard: Optional[StandardCampaignType] = None
    campaign_type_special: Optional[SpecialCampaignType] = None
    company_name: str = Field(min_length=1)
    vertical_type: int = Field(gt=0)
    campaign_description: str = Field(min_length=1, repr=False)
    sample_message: str = Field(min_length=1, repr=False)
    consumer_opt_ins: str = Field(min_length=1, repr=False)
    consumer_opt_outs: str = Field(min_length=1, repr=False)
    reply_help: HelpReply
    campaign_did: Union[str, int, List[int]] = Field(repr=False)
    loan_arrange: DLCYesNo
    embedded_link: DLCYesNo
    embedded_phone: DLCYesNo
    marketing_used: DLCYesNo
    age_gated_contact: DLCYesNo

    @field_validator("campaign_did")
    @classmethod
    def validate_dids(cls, value: Union[str, int, List[int]]) -> Union[str, int, List[int]]:
        return _validate_campaign_dids(value)

    @model_validator(mode="after")
    def validate_campaign_subtype(self) -> CampaignConfigurationRequest:
        if self.campaign_type is CampaignType.STANDARD:
            if self.campaign_type_standard is None or self.campaign_type_special is not None:
                raise ValueError("standard campaigns require only campaign_type_standard")
        elif self.campaign_type_special is None or self.campaign_type_standard is not None:
            raise ValueError("special campaigns require only campaign_type_special")
        return self


class CampaignCreateRequest(CampaignConfigurationRequest):
    pass


class CampaignUpdateRequest(CampaignConfigurationRequest):
    id: int = Field(gt=0)


class CampaignDeleteRequest(DLCModel):
    id: int = Field(gt=0)


class BrandRecord(DLCModel):
    id: Optional[str] = None
    address: Optional[str] = Field(default=None, repr=False)
    company_name: Optional[str] = None
    contact: Optional[str] = Field(default=None, repr=False)
    legal_type: Optional[str] = None
    lei_number: Optional[str] = Field(default=None, repr=False)
    lei_number_type: Optional[str] = None
    status: Optional[BrandStatus] = None
    tax_number: Optional[str] = Field(default=None, repr=False)
    url: Optional[str] = None
    vertical_type: Optional[str] = None


class BrandListResponse(DLCModel):
    data: List[BrandRecord] = Field(default_factory=list)
    current_page: int = Field(default=1, ge=1)
    total: int = Field(default=0, ge=0)
    total_pages: int = Field(default=1, ge=0)

    def next_page(self) -> Optional[int]:
        return self.current_page + 1 if self.current_page < self.total_pages else None


class BrandCreateResponse(BrandListResponse):
    pass


class BrandUpdateResponse(DLCModel):
    data: Any = None


class CampaignRecord(DLCModel):
    id: Optional[str] = None
    age_gated_contact: Optional[DLCYesNo] = None
    brand_id: Optional[str] = None
    campaign_description: Optional[str] = Field(default=None, repr=False)
    campaign_did: Optional[str] = Field(default=None, repr=False)
    campaign_type: Optional[str] = None
    campaign_type_standard: Optional[str] = None
    campaign_type_special: Optional[str] = None
    consumer_opt_ins: Optional[str] = Field(default=None, repr=False)
    consumer_opt_outs: Optional[str] = Field(default=None, repr=False)
    embedded_link: Optional[DLCYesNo] = None
    embedded_phone: Optional[DLCYesNo] = None
    loan_arrange: Optional[DLCYesNo] = None
    marketing_used: Optional[DLCYesNo] = None
    reply_help: Optional[HelpReply] = None
    sample_message: Optional[str] = Field(default=None, repr=False)
    status: Optional[CampaignStatus] = None
    vertical_type: Optional[str] = None


class CampaignListResponse(DLCModel):
    data: List[CampaignRecord] = Field(default_factory=list)
    current_page: int = Field(default=1, ge=1)
    total: int = Field(default=0, ge=0)
    total_pages: int = Field(default=1, ge=0)

    def next_page(self) -> Optional[int]:
        return self.current_page + 1 if self.current_page < self.total_pages else None


class CampaignCreated(DLCModel):
    id: Optional[str] = None


class CampaignCreateResponse(DLCModel):
    data: Optional[CampaignCreated] = None


DLCModelT = TypeVar("DLCModelT", bound=QuestBlueModel)


def parse_dlc_response(model: Type[DLCModelT], payload: Any) -> Union[DLCModelT, WarningResponse]:
    if isinstance(payload, Mapping) and "warning" in payload:
        return WarningResponse.model_validate(payload)
    return model.model_validate(payload)


def parse_empty_dlc_response(payload: Any) -> Optional[WarningResponse]:
    if payload is None or payload == "" or payload == {}:
        return None
    if isinstance(payload, Mapping) and "warning" in payload:
        return WarningResponse.model_validate(payload)
    raise QuestBlueResponseError("QuestBlue returned a body for an empty 10DLC response")
