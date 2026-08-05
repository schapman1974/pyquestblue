"""Voice DID discovery and guarded ordering examples."""

from __future__ import annotations

from typing import Optional

from questblue import (
    AvailableDIDsResponse,
    DIDAvailabilityRequest,
    DIDOrderRequest,
    DIDType,
    QuestBlue,
    WarningResponse,
)


def find_local_dids(client: QuestBlue, zip_code: int, *, limit: int = 10) -> AvailableDIDsResponse:
    result = client.dids.available(
        DIDAvailabilityRequest(did_type=DIDType.LOCAL, zip=zip_code, total_list=limit)
    )
    if isinstance(result, WarningResponse):
        raise RuntimeError("QuestBlue returned a warning: " + "; ".join(result.warning))
    return result


def order_dids(
    client: QuestBlue, request: DIDOrderRequest, *, confirm_billable: bool = False
) -> Optional[WarningResponse]:
    """Order DIDs only after the caller explicitly acknowledges billing."""
    if not confirm_billable:
        raise ValueError("set confirm_billable=True after reviewing the DID order")
    return client.dids.order(request)
