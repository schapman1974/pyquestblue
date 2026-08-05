from __future__ import annotations

from typing import Any, Dict, List

import httpx
import pytest
from pydantic import ValidationError

from examples.did import find_local_dids, order_dids
from questblue import (
    AccountToggle,
    AsyncQuestBlue,
    AvailableDIDsResponse,
    DIDAvailabilityRequest,
    DIDInventoryResponse,
    DIDListRequest,
    DIDOrderRequest,
    DIDRateCentersResponse,
    DIDStatesResponse,
    DIDTier,
    DIDType,
    DIDUpdateRequest,
    DirectoryListingType,
    FraudValidationResponse,
    QuestBlue,
    QuestBlueAPIError,
    QuestBlueResponseError,
    QuestBlueServerError,
    WarningResponse,
    YesNo,
)


def did_response(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/did" and request.method == "GET":
        page = int(request.url.params.get("page", "1"))
        return httpx.Response(
            200,
            json={
                "data": {f"1555123456{page}": ["primary", "cnam:on"]},
                "current_page": page,
                "total": 2,
                "total_pages": 2,
            },
        )
    payloads: Dict[str, Any] = {
        "/did/states": {"data": ["NC", "NY"], "total": 2},
        "/did/ratecenters": {"data": {"CARY": "Cary"}, "total": 1},
        "/did/available": {"data": ["15551234567"], "total": 1},
        "/did/fraudvalidate": {"data": [{"15557654321": "low"}]},
    }
    if request.url.path in payloads:
        return httpx.Response(200, json=payloads[request.url.path])
    return httpx.Response(200)


def make_client(handler: Any = did_response, *, max_retries: int = 2) -> QuestBlue:
    return QuestBlue(
        "user",
        "password",
        "key",
        max_retries=max_retries,
        http_client=httpx.Client(
            base_url="https://example.test", transport=httpx.MockTransport(handler)
        ),
    )


def test_all_sync_did_operations_are_typed_and_serialized() -> None:
    requests: List[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return did_response(request)

    client = make_client(handler)
    inventory = client.dids.list(DIDListRequest(did="*456*", per_page=50, page=1))
    states = client.dids.states()
    centers = client.dids.rate_centers("nc", DIDTier.TIER_1)
    available = client.dids.available(
        DIDAvailabilityRequest(did_type=DIDType.LOCAL, state="nc", ratecenter="CARY", total_list=10)
    )
    assert (
        client.dids.order(
            DIDOrderRequest(
                did=[15551234567, 15551234568],
                tier=DIDTier.TIER_1,
                route2trunk="primary",
                cnam=AccountToggle.ON,
                note="customer line",
                pin=1234,
                lidb="Example Co",
                e911_name="Example Company",
                e911_city="Cary",
                e911_state="nc",
                e911_zip="27513",
                e911_address="1 Main St",
                dlda=YesNo.YES,
                dlda_type=DirectoryListingType.BUSINESS,
                dlda_firstname="Example Company",
            )
        )
        is None
    )
    assert (
        client.dids.update(
            DIDUpdateRequest(
                did=15551234567,
                route2trunk="secondary",
                failover=[["15557654321", "15559876543"]],
                e911=YesNo.YES,
                e911_call_alert=[["ops@example.test", "15557654321"]],
            )
        )
        is None
    )
    assert client.dids.delete(15551234567) is None
    assert client.dids.move_to_fax(15551234568) is None
    fraud = client.dids.validate_fraud([15557654321, 15559876543])

    assert isinstance(inventory, DIDInventoryResponse)
    assert inventory.next_page() == 2
    assert isinstance(states, DIDStatesResponse)
    assert isinstance(centers, DIDRateCentersResponse)
    assert isinstance(available, AvailableDIDsResponse)
    assert isinstance(fraud, FraudValidationResponse)
    queries = {(request.method, request.url.path): dict(request.url.params) for request in requests}
    assert queries[("GET", "/did")]["did"] == "*456*"
    assert queries[("GET", "/did")]["per_page"] == "50"
    assert queries[("GET", "/did/ratecenters")] == {"state": "NC", "tier": "1"}
    assert queries[("GET", "/did/available")] == {
        "type": "local",
        "state": "NC",
        "ratecenter": "CARY",
        "total_list": "10",
    }
    assert queries[("POST", "/did")]["did"] == "15551234567,15551234568"
    assert queries[("POST", "/did")]["pin"] == "1234"
    assert queries[("PUT", "/did")]["failover"] == "15557654321,15559876543"
    assert queries[("DELETE", "/did")] == {"did": "15551234567"}
    assert queries[("PUT", "/did/move2fax")] == {"did": "15551234568"}
    assert queries[("POST", "/did/fraudvalidate")]["tn"] == "15557654321,15559876543"


def test_sync_page_iteration_preserves_typed_pages() -> None:
    client = make_client()

    pages = list(client.dids.pages(DIDListRequest(per_page=5)))

    assert [page.current_page for page in pages if isinstance(page, DIDInventoryResponse)] == [1, 2]


def test_did_examples_are_executable_and_guard_billable_ordering() -> None:
    client = make_client()

    assert find_local_dids(client, 27513).data == ["15551234567"]
    with pytest.raises(ValueError, match="confirm_billable"):
        order_dids(client, DIDOrderRequest(did=15551234567))
    assert order_dids(client, DIDOrderRequest(did=15551234567), confirm_billable=True) is None


async def test_all_async_did_operations_and_pages_have_parity() -> None:
    http = httpx.AsyncClient(
        base_url="https://example.test", transport=httpx.MockTransport(did_response)
    )
    client = AsyncQuestBlue("user", "password", "key", http_client=http)

    assert isinstance(await client.dids.list(), DIDInventoryResponse)
    assert isinstance(await client.dids.states(), DIDStatesResponse)
    assert isinstance(await client.dids.rate_centers("NC", DIDTier.TIER_1), DIDRateCentersResponse)
    assert isinstance(
        await client.dids.available(
            DIDAvailabilityRequest(did_type=DIDType.TOLL_FREE, mask="*800*")
        ),
        AvailableDIDsResponse,
    )
    assert await client.dids.order(DIDOrderRequest(did=15551234567)) is None
    assert await client.dids.update(DIDUpdateRequest(did=15551234567)) is None
    assert await client.dids.delete(15551234567) is None
    assert await client.dids.move_to_fax(15551234567) is None
    assert isinstance(await client.dids.validate_fraud(15557654321), FraudValidationResponse)
    pages = [page async for page in client.dids.pages(DIDListRequest(per_page=5))]
    assert len(pages) == 2
    await http.aclose()


@pytest.mark.parametrize(
    "factory",
    [
        lambda: DIDListRequest(did="*12"),
        lambda: DIDListRequest(per_page=4),
        lambda: DIDAvailabilityRequest(did_type=DIDType.LOCAL, state="NC"),
        lambda: DIDAvailabilityRequest(did_type=DIDType.TOLL_FREE),
        lambda: DIDAvailabilityRequest(did_type=DIDType.TOLL_FREE, mask="*12"),
        lambda: DIDAvailabilityRequest(did_type=DIDType.TOLL_FREE, code=80, state="N"),
        lambda: DIDOrderRequest(did=[]),
        lambda: DIDOrderRequest(did=15551234567, pin=123),
        lambda: DIDOrderRequest(did=15551234567, lidb="bad!"),
        lambda: DIDOrderRequest(did=15551234567, e911_state="N"),
        lambda: DIDUpdateRequest(did=0),
        lambda: client_rate_centers_request(),
        lambda: client_fraud_request(),
    ],
)
def test_did_request_validation(factory: Any) -> None:
    with pytest.raises((ValidationError, ValueError)):
        factory()


def client_rate_centers_request() -> None:
    make_client().dids.rate_centers("N", DIDTier.TIER_1)


def client_fraud_request() -> None:
    make_client().dids.validate_fraud(list(range(1, 102)))


def test_explicit_optional_did_fields_accept_none() -> None:
    request = DIDAvailabilityRequest(did_type=DIDType.TOLL_FREE, code=80, state=None)
    order = DIDOrderRequest(did=15551234567, e911_state=None)

    assert request.state is None
    assert order.e911_state is None


def test_did_warning_and_error_responses() -> None:
    warning_client = make_client(
        lambda _: httpx.Response(202, json={"warning": ["provisioned with warning"]})
    )
    assert isinstance(warning_client.dids.order(DIDOrderRequest(did=15551234567)), WarningResponse)
    assert isinstance(warning_client.dids.states(), WarningResponse)

    error_client = make_client(lambda _: httpx.Response(206, json={"error": "DID rejected"}))
    with pytest.raises(QuestBlueAPIError, match="DID rejected"):
        error_client.dids.update(DIDUpdateRequest(did=15551234567))

    malformed_client = make_client(lambda _: httpx.Response(200, json={"unexpected": True}))
    with pytest.raises(QuestBlueResponseError, match="empty DID response"):
        malformed_client.dids.delete(15551234567)


@pytest.mark.parametrize("operation", ["order", "update", "delete", "move_to_fax"])
def test_billable_and_destructive_did_operations_are_not_retried(operation: str) -> None:
    attempts = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503, json={"error": "uncertain"})

    client = make_client(handler, max_retries=10)
    with pytest.raises(QuestBlueServerError):
        if operation == "order":
            client.dids.order(DIDOrderRequest(did=15551234567))
        elif operation == "update":
            client.dids.update(DIDUpdateRequest(did=15551234567))
        elif operation == "delete":
            client.dids.delete(15551234567)
        else:
            client.dids.move_to_fax(15551234567)
    assert attempts == 1
