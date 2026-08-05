from __future__ import annotations

from typing import Any, Dict, List

import httpx
import pytest
from pydantic import ValidationError

from examples.sip_trunk import create_static_trunk, registration_status
from questblue import (
    AsyncQuestBlue,
    BlockAction,
    BlockCallerRequest,
    BlockedCallersRequest,
    BlockedCallersResponse,
    QuestBlue,
    QuestBlueAPIError,
    QuestBlueResponseError,
    QuestBlueServerError,
    RegistrationStatus,
    SIPRegion,
    SIPTrunkCreateRequest,
    SIPTrunkInventoryResponse,
    SIPTrunkListRequest,
    SIPTrunkStatusResponse,
    SIPTrunkUpdateRequest,
    TrunkToggle,
    WarningResponse,
    YesNo,
)


def response(request: httpx.Request) -> httpx.Response:
    payloads: Dict[str, Any] = {
        "/siptrunk": {
            "data": {"pbx1": ["online"]},
            "current_page": 1,
            "total": 1,
            "total_pages": 1,
        },
        "/siptrunk/statuschecker": {"data": {"pbx1": ["1.2.3.4"]}, "res": "online", "total": 1},
        "/siptrunk/blockedcallers": {
            "data": [
                {
                    "did": "15551234567",
                    "ip_address": "1.2.3.4",
                    "status": "blocked",
                    "trunk": "pbx1",
                }
            ],
            "current_page": 1,
            "total": 1,
            "total_pages": 1,
        },
    }
    if request.method == "GET":
        return httpx.Response(200, json=payloads[request.url.path])
    if request.url.path.endswith("blockcaller"):
        return httpx.Response(200, json={})
    return httpx.Response(200)


def client(handler: Any = response, max_retries: int = 2) -> QuestBlue:
    return QuestBlue(
        "u",
        "p",
        "k",
        max_retries=max_retries,
        http_client=httpx.Client(base_url="https://test", transport=httpx.MockTransport(handler)),
    )


def test_all_sync_sip_operations_and_parameters() -> None:
    seen: List[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return response(request)

    qb = client(handler)
    assert isinstance(
        qb.sip_trunks.list(SIPTrunkListRequest(trunk="pbx1", per_page=50)),
        SIPTrunkInventoryResponse,
    )
    assert (
        qb.sip_trunks.create(
            SIPTrunkCreateRequest(
                trunk="pbx1",
                ip_address="pbx.example.com",
                region=SIPRegion.US_NY,
                concurrent_max="20",
                allow_rtp_proxy=YesNo.YES,
            )
        )
        is None
    )
    assert (
        qb.sip_trunks.update(
            SIPTrunkUpdateRequest(trunk="pbx1", password="secret12", status=TrunkToggle.ON)
        )
        is None
    )
    assert qb.sip_trunks.delete("pbx1") is None
    status = qb.sip_trunks.status("pbx1")
    assert isinstance(status, SIPTrunkStatusResponse) and status.res is RegistrationStatus.ONLINE
    assert (
        qb.sip_trunks.block_caller(
            BlockCallerRequest(trunk=["pbx1", "pbx2"], did=15551234567, action=BlockAction.BLOCK)
        )
        is None
    )
    assert isinstance(
        qb.sip_trunks.blocked_callers(BlockedCallersRequest(trunk=["pbx1"], per_page=50)),
        BlockedCallersResponse,
    )
    queries = {(r.method, r.url.path): dict(r.url.params) for r in seen}
    assert queries[("POST", "/siptrunk")]["ip_address"] == "pbx.example.com"
    assert queries[("PUT", "/siptrunk")]["status"] == "on"
    assert queries[("POST", "/siptrunk/blockcaller")]["trunk"] == "pbx1,pbx2"


async def test_all_async_sip_operations_have_parity() -> None:
    http = httpx.AsyncClient(base_url="https://test", transport=httpx.MockTransport(response))
    qb = AsyncQuestBlue("u", "p", "k", http_client=http)
    assert isinstance(await qb.sip_trunks.list(), SIPTrunkInventoryResponse)
    assert (
        await qb.sip_trunks.create(SIPTrunkCreateRequest(trunk="pbx1", password="secret12")) is None
    )
    assert (
        await qb.sip_trunks.update(SIPTrunkUpdateRequest(trunk="pbx1", status=TrunkToggle.OFF))
        is None
    )
    assert await qb.sip_trunks.delete("pbx1") is None
    assert isinstance(await qb.sip_trunks.status("pbx1"), SIPTrunkStatusResponse)
    assert (
        await qb.sip_trunks.block_caller(
            BlockCallerRequest(trunk="pbx1", did=15551234567, action=BlockAction.UNBLOCK)
        )
        is None
    )
    assert isinstance(await qb.sip_trunks.blocked_callers(), BlockedCallersResponse)
    await http.aclose()


@pytest.mark.parametrize(
    "factory",
    [
        lambda: SIPTrunkCreateRequest(trunk="bad-name", password="secret12"),
        lambda: SIPTrunkCreateRequest(trunk="pbx1"),
        lambda: SIPTrunkCreateRequest(trunk="pbx1", password="x"),
        lambda: SIPTrunkCreateRequest(trunk="pbx1", ip_address="bad host!"),
        lambda: SIPTrunkCreateRequest(trunk="pbx1", ip_address="1.2.3.4", inter_limit=1001),
        lambda: BlockedCallersRequest(per_page=4),
    ],
)
def test_sip_validation(factory: Any) -> None:
    with pytest.raises((ValidationError, ValueError)):
        factory()


@pytest.mark.parametrize("value", ["online", "offline", "error", "provider-added-state"])
def test_registration_status_variants_remain_readable(value: str) -> None:
    result = SIPTrunkStatusResponse(res=value)
    assert result.res.value == value


def test_optional_address_and_inventory_pagination() -> None:
    assert SIPTrunkUpdateRequest(trunk="pbx1", ip_address=None).ip_address is None
    inventory = SIPTrunkInventoryResponse(current_page=1, total_pages=2)
    assert inventory.next_page() == 2


def test_warnings_errors_retry_safety_and_examples() -> None:
    warning = client(lambda _: httpx.Response(202, json={"warning": ["caveat"]}))
    assert isinstance(
        warning.sip_trunks.create(SIPTrunkCreateRequest(trunk="pbx1", password="secret12")),
        WarningResponse,
    )
    assert isinstance(warning.sip_trunks.status("pbx1"), WarningResponse)
    error = client(lambda _: httpx.Response(206, json={"error": "trunk rejected"}))
    with pytest.raises(QuestBlueAPIError, match="trunk rejected"):
        error.sip_trunks.delete("pbx1")
    malformed = client(lambda _: httpx.Response(200, json={"unexpected": True}))
    with pytest.raises(QuestBlueResponseError, match="body for an empty SIP trunk response"):
        malformed.sip_trunks.delete("pbx1")
    attempts = 0

    def uncertain(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503)

    unsafe = client(uncertain, 10)
    with pytest.raises(QuestBlueServerError):
        unsafe.sip_trunks.update(SIPTrunkUpdateRequest(trunk="pbx1", status=TrunkToggle.OFF))
    assert attempts == 1
    qb = client()
    assert registration_status(qb, "pbx1").res is RegistrationStatus.ONLINE
    with pytest.raises(ValueError, match="confirm_routing_change"):
        create_static_trunk(qb, "pbx1", "1.2.3.4")
    create_static_trunk(qb, "pbx1", "1.2.3.4", confirm_routing_change=True)
