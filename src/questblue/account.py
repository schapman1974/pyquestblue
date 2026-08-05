"""Typed models and validation for QuestBlue User Account operations."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Any, List, Literal, Mapping, Optional, Sequence, Type, TypeVar, Union
from urllib.parse import urlsplit

from pydantic import Field, field_validator

from ._exceptions import QuestBlueResponseError
from .models import OnOff, OpenStringEnum, QuestBlueModel, ResponseEnvelope, WarningResponse

MinimumBalance = Literal[
    5, 25, 30, 35, 40, 45, 50, 100, 150, 200, 250, 300, 350, 400, 500, 600, 700, 800, 900, 1000
]
ReloadAmount = Literal[25, 50, 60, 70, 80, 90, 100, 200, 300, 400, 500, 1000, 1500, 2000, 2500]


class AccountToggle(str, Enum):
    """Validated on/off value accepted by account mutations."""

    ON = "on"
    OFF = "off"


class PaymentMode(str, Enum):
    """Legacy refill payment mode retained by the upstream contract."""

    CREDIT_CARD = "cc"
    ACH = "ach"
    ALL = "all"


class PaymentMethod(OpenStringEnum):
    """Payment method reported by QuestBlue."""

    CREDIT_CARD = "cc"
    ACH = "ach"


class CallbackSection(str, Enum):
    """Inventory area accepted by account callback configuration."""

    LNP = "lnp"
    DID = "did"
    FAX = "fax"
    SMS = "sms"
    TRUNK = "trunk"
    SERVER = "server"


CallbackSections = Union[str, Sequence[CallbackSection]]


class AccountBalance(QuestBlueModel):
    balance: Decimal
    allowed_credit: Decimal


class AccountBalanceResponse(ResponseEnvelope[AccountBalance]):
    data: AccountBalance


class AccountDetails(QuestBlueModel):
    balance: Decimal
    minimum_balance: Decimal
    reload_amount: Decimal
    payment_method: PaymentMethod
    low_balance_alert_amount: Decimal
    balance_autorefill: OnOff
    balance_notify: OnOff


class AccountDetailsResponse(ResponseEnvelope[List[AccountDetails]]):
    data: List[AccountDetails]


class ServiceRates(QuestBlueModel):
    local_did_cost: Decimal
    inbound_call_rate: Decimal
    vps_server_rate: Decimal
    ccrf: Decimal


class Country(QuestBlueModel):
    country_id: int
    country_name: str


class CountryListResponse(ResponseEnvelope[List[Country]]):
    data: List[Country]


class InternationalRate(QuestBlueModel):
    destination: str
    code: str
    rate: Decimal


class InternationalRatesResponse(ResponseEnvelope[List[InternationalRate]]):
    data: List[InternationalRate]


class InternationalTollFreeRate(QuestBlueModel):
    origin: str
    code: str
    rate: Decimal


class InternationalTollFreeRatesResponse(ResponseEnvelope[List[InternationalTollFreeRate]]):
    data: List[InternationalTollFreeRate]


class CallbackConfiguration(QuestBlueModel):
    url: Optional[str] = None
    sections: Optional[str] = None


class CallbackStatusResponse(ResponseEnvelope[List[CallbackConfiguration]]):
    data: List[CallbackConfiguration] = Field(default_factory=list)


class AccountActionResponse(ResponseEnvelope[str]):
    """Success envelope returned by account alert mutations."""


class CountryRateRequest(QuestBlueModel):
    country_id: int = Field(gt=0)


class RefillBalanceRequest(QuestBlueModel):
    amount: int = Field(ge=10)
    mode: Optional[PaymentMode] = Field(default=None, serialization_alias="Mode")


class SetAutorefillRequest(QuestBlueModel):
    autorefill: AccountToggle


class SetBalanceReloadRequest(QuestBlueModel):
    min_balance: MinimumBalance
    reload_amount: ReloadAmount


class SetLowBalanceAlertRequest(QuestBlueModel):
    low_balance_alert_amount: int = Field(ge=0)


class SetDailyBalanceAlertRequest(QuestBlueModel):
    action: AccountToggle


class CallbackConfigRequest(QuestBlueModel):
    url: str
    sections: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        if value == "":
            return value
        parsed = urlsplit(value)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("url must be empty or an absolute HTTP(S) URL")
        return value

    @field_validator("sections")
    @classmethod
    def validate_sections(cls, value: str) -> str:
        if value == "":
            return value
        sections = [section.strip() for section in value.split(",")]
        for section in sections:
            CallbackSection(section)
        return ",".join(sections)

    @classmethod
    def from_values(cls, url: str, sections: CallbackSections) -> CallbackConfigRequest:
        if isinstance(sections, str):
            serialized = sections
        else:
            serialized = ",".join(section.value for section in sections)
        return cls(url=url, sections=serialized)


AccountModelT = TypeVar("AccountModelT", bound=QuestBlueModel)


def parse_account_response(
    model: Type[AccountModelT], payload: Any
) -> Union[AccountModelT, WarningResponse]:
    """Validate an account response while retaining upstream warning semantics."""
    if isinstance(payload, Mapping) and "warning" in payload:
        return WarningResponse.model_validate(payload)
    return model.model_validate(payload)


def parse_empty_account_response(payload: Any) -> Optional[WarningResponse]:
    """Validate an operation documented to return an empty success body."""
    if payload is None or payload == "" or payload == {}:
        return None
    if isinstance(payload, Mapping) and "warning" in payload:
        return WarningResponse.model_validate(payload)
    raise QuestBlueResponseError("QuestBlue returned a body for an empty account response")
