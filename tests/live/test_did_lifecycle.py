"""Explicitly gated, billable DID lifecycle test for a dedicated subaccount."""

from __future__ import annotations

import os
from urllib.parse import urlsplit

import pytest

from questblue import (
    AvailableDIDsResponse,
    DIDAvailabilityRequest,
    DIDListRequest,
    DIDOrderRequest,
    DIDType,
    DIDUpdateRequest,
    QuestBlue,
)

pytestmark = [pytest.mark.live, pytest.mark.live_billable]


def test_live_did_order_inventory_update_delete_lifecycle() -> None:
    if os.getenv("QUESTBLUE_RUN_LIVE_BILLABLE_DID") != "YES_I_ACCEPT_PRODUCTION_BILLING":
        pytest.skip("live DID lifecycle requires explicit production-billing acknowledgment")

    required = (
        "QUESTBLUE_LIVE_USERNAME",
        "QUESTBLUE_LIVE_PASSWORD",
        "QUESTBLUE_LIVE_SECURITY_KEY",
        "QUESTBLUE_LIVE_BASE_URL",
        "QUESTBLUE_LIVE_ZIP",
    )
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        pytest.skip("missing dedicated live-subaccount settings: " + ", ".join(missing))

    base_url = os.environ["QUESTBLUE_LIVE_BASE_URL"]
    parsed = urlsplit(base_url)
    if parsed.scheme != "https" or parsed.hostname not in {
        "api.questblue.com",
        "api2.questblue.com",
    }:
        pytest.fail("live base URL must be an HTTPS QuestBlue API host")

    with QuestBlue(
        os.environ["QUESTBLUE_LIVE_USERNAME"],
        os.environ["QUESTBLUE_LIVE_PASSWORD"],
        os.environ["QUESTBLUE_LIVE_SECURITY_KEY"],
        base_url=base_url,
        max_retries=0,
    ) as client:
        available = client.dids.available(
            DIDAvailabilityRequest(
                did_type=DIDType.LOCAL,
                zip=int(os.environ["QUESTBLUE_LIVE_ZIP"]),
                total_list=1,
            )
        )
        assert isinstance(available, AvailableDIDsResponse)
        assert available.data
        did = int(available.data[0])

        ordered = False
        try:
            client.dids.order(DIDOrderRequest(did=did, note="pyquestblue live contract test"))
            ordered = True
            inventory = client.dids.list(DIDListRequest(did=str(did)))
            assert not hasattr(inventory, "warning")
            assert str(did) in inventory.data  # type: ignore[union-attr]
            client.dids.update(DIDUpdateRequest(did=did, note="pyquestblue live verified"))
        finally:
            if ordered:
                client.dids.delete(did)
