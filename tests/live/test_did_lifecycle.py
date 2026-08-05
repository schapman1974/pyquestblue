"""Explicitly gated QuestBlue sandbox DID lifecycle contract test."""

from __future__ import annotations

import os

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

pytestmark = pytest.mark.live


def test_sandbox_did_order_inventory_update_delete_lifecycle() -> None:
    if os.getenv("QUESTBLUE_RUN_SANDBOX_DID_LIFECYCLE") != "YES_I_ACCEPT_SANDBOX_BILLING":
        pytest.skip("sandbox DID lifecycle requires explicit billing acknowledgment")

    required = (
        "QUESTBLUE_SANDBOX_USERNAME",
        "QUESTBLUE_SANDBOX_PASSWORD",
        "QUESTBLUE_SANDBOX_SECURITY_KEY",
        "QUESTBLUE_SANDBOX_BASE_URL",
        "QUESTBLUE_SANDBOX_ZIP",
    )
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        pytest.skip("missing dedicated sandbox settings: " + ", ".join(missing))

    with QuestBlue(
        os.environ["QUESTBLUE_SANDBOX_USERNAME"],
        os.environ["QUESTBLUE_SANDBOX_PASSWORD"],
        os.environ["QUESTBLUE_SANDBOX_SECURITY_KEY"],
        base_url=os.environ["QUESTBLUE_SANDBOX_BASE_URL"],
        max_retries=0,
    ) as client:
        available = client.dids.available(
            DIDAvailabilityRequest(
                did_type=DIDType.LOCAL,
                zip=int(os.environ["QUESTBLUE_SANDBOX_ZIP"]),
                total_list=1,
            )
        )
        assert isinstance(available, AvailableDIDsResponse)
        assert available.data
        did = int(available.data[0])

        ordered = False
        try:
            client.dids.order(DIDOrderRequest(did=did, note="pyquestblue sandbox contract test"))
            ordered = True
            inventory = client.dids.list(DIDListRequest(did=str(did)))
            assert not hasattr(inventory, "warning")
            assert str(did) in inventory.data  # type: ignore[union-attr]
            client.dids.update(DIDUpdateRequest(did=did, note="pyquestblue sandbox verified"))
        finally:
            if ordered:
                client.dids.delete(did)
