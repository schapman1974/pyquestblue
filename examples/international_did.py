"""International DID discovery and guarded lifecycle examples."""

from __future__ import annotations

from typing import Optional

from questblue import (
    InternationalCitiesResponse,
    InternationalDIDOrderRequest,
    InternationalDIDOrderResponse,
    QuestBlue,
    WarningResponse,
)


def cities_for_country(client: QuestBlue, country_code: str) -> InternationalCitiesResponse:
    result = client.international_dids.cities(country_code)
    if isinstance(result, WarningResponse):
        raise RuntimeError("QuestBlue returned a warning: " + "; ".join(result.warning))
    return result


def order_international_did(
    client: QuestBlue,
    request: InternationalDIDOrderRequest,
    *,
    confirm_billable: bool = False,
) -> InternationalDIDOrderResponse:
    if not confirm_billable:
        raise ValueError("set confirm_billable=True after reviewing international DID pricing")
    result = client.international_dids.order(request)
    if isinstance(result, WarningResponse):
        raise RuntimeError("QuestBlue returned a warning: " + "; ".join(result.warning))
    return result


def remove_international_did(
    client: QuestBlue, did: int, *, confirm_release: bool = False
) -> Optional[WarningResponse]:
    if not confirm_release:
        raise ValueError("set confirm_release=True after confirming the DID may be released")
    return client.international_dids.delete(did)
