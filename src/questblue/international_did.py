"""Typed models for QuestBlue International DID operations."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Optional, Type, TypeVar, Union

from pydantic import Field, field_validator

from ._exceptions import QuestBlueResponseError
from .did import DIDInventoryResponse, DIDListRequest
from .models import QuestBlueModel, ResponseEnvelope, WarningResponse


class InternationalDIDListRequest(DIDListRequest):
    """Wildcard and page controls for international DID inventory."""


class InternationalCountriesRequest(QuestBlueModel):
    """Country discovery parameters.

    The upstream contract marks ``did`` required but describes it as a DID to move,
    which is inconsistent with a country-list operation. It remains optional until
    QuestBlue confirms that behavior.
    """

    did: Optional[int] = Field(default=None, gt=0)


class InternationalCitiesRequest(QuestBlueModel):
    country_code: str

    @field_validator("country_code")
    @classmethod
    def validate_country_code(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z]{2}", value):
            raise ValueError("country_code must contain two letters")
        return value.upper()


class InternationalDIDOrderRequest(InternationalCitiesRequest):
    city: str = Field(min_length=1)
    forward2did: int = Field(gt=0)
    route2trunk: int = Field(gt=0)


class InternationalDIDUpdateRequest(QuestBlueModel):
    did: int = Field(gt=0)
    forward2did: int = Field(gt=0)
    route2trunk: int = Field(gt=0)


class InternationalDIDDeleteRequest(QuestBlueModel):
    did: int = Field(gt=0)


class InternationalDIDInventoryResponse(DIDInventoryResponse):
    """Paged international DID inventory and configuration values."""


class InternationalCountriesResponse(ResponseEnvelope[List[Dict[str, str]]]):
    data: List[Dict[str, str]]
    total: int = Field(ge=0)


class InternationalCitiesResponse(ResponseEnvelope[List[str]]):
    data: List[str]
    total: int = Field(ge=0)


class InternationalDIDOrderResponse(QuestBlueModel):
    did: List[int] = Field(default_factory=list)


InternationalDIDModelT = TypeVar("InternationalDIDModelT", bound=QuestBlueModel)


def parse_international_did_response(
    model: Type[InternationalDIDModelT], payload: Any
) -> Union[InternationalDIDModelT, WarningResponse]:
    if isinstance(payload, Mapping) and "warning" in payload:
        return WarningResponse.model_validate(payload)
    return model.model_validate(payload)


def parse_empty_international_did_response(payload: Any) -> Optional[WarningResponse]:
    if payload is None or payload == "" or payload == {}:
        return None
    if isinstance(payload, Mapping) and "warning" in payload:
        return WarningResponse.model_validate(payload)
    raise QuestBlueResponseError(
        "QuestBlue returned a body for an empty international DID response"
    )
