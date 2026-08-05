from __future__ import annotations

from typing import Any, Dict, List

import httpx
import pytest
from pydantic import ValidationError

from examples.international_did import (
    cities_for_country,
    order_international_did,
    remove_international_did,
)
from questblue import (
    AsyncQuestBlue,
    InternationalCitiesResponse,
    InternationalCountriesRequest,
    InternationalCountriesResponse,
    InternationalDIDInventoryResponse,
    InternationalDIDListRequest,
    InternationalDIDOrderRequest,
    InternationalDIDOrderResponse,
    InternationalDIDUpdateRequest,
    QuestBlue,
    QuestBlueAPIError,
    QuestBlueResponseError,
    QuestBlueServerError,
    WarningResponse,
)


def international_response(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/didinter" and request.method == "GET":
        page = int(request.url.params.get("page", "1"))
        return httpx.Response(
            200,
            json={
                "data": {f"4420712345{page}": ["London", "route:7"]},
                "current_page": page,
                "total": 2,
                "total_pages": 2,
            },
        )
    payloads: Dict[str, Any] = {
        "/didinter/countrylist": {"data": [{"GB": "United Kingdom"}], "total": 1},
        "/didinter/citylist": {"data": ["London"], "total": 1},
    }
    if request.url.path in payloads:
        return httpx.Response(200, json=payloads[request.url.path])
    if request.url.path == "/didinter" and request.method == "POST":
        return httpx.Response(200, json={"did": [442071234567]})
    return httpx.Response(200)


def make_client(handler: Any = international_response, *, max_retries: int = 2) -> QuestBlue:
    return QuestBlue(
        "user",
        "password",
        "key",
        max_retries=max_retries,
        http_client=httpx.Client(
            base_url="https://example.test", transport=httpx.MockTransport(handler)
        ),
    )


def test_all_sync_international_did_operations_are_typed_and_serialized() -> None:
    requests: List[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return international_response(request)

    client = make_client(handler)
    countries = client.international_dids.countries()
    countries_with_spec_parameter = client.international_dids.countries(
        InternationalCountriesRequest(did=442071234567)
    )
    cities = client.international_dids.cities("gb")
    inventory = client.international_dids.list(
        InternationalDIDListRequest(did="*456*", per_page=50)
    )
    ordered = client.international_dids.order(
        InternationalDIDOrderRequest(
            country_code="gb", city="London", forward2did=15551234567, route2trunk=7
        )
    )
    assert (
        client.international_dids.update(
            InternationalDIDUpdateRequest(did=442071234567, forward2did=15557654321, route2trunk=8)
        )
        is None
    )
    assert client.international_dids.delete(442071234567) is None

    assert isinstance(countries, InternationalCountriesResponse)
    assert isinstance(countries_with_spec_parameter, InternationalCountriesResponse)
    assert isinstance(cities, InternationalCitiesResponse)
    assert isinstance(inventory, InternationalDIDInventoryResponse)
    assert isinstance(ordered, InternationalDIDOrderResponse)
    assert ordered.did == [442071234567]
    queries = [(request.method, request.url.path, dict(request.url.params)) for request in requests]
    assert ("GET", "/didinter/countrylist", {}) in queries
    assert ("GET", "/didinter/countrylist", {"did": "442071234567"}) in queries
    assert ("GET", "/didinter/citylist", {"country_code": "GB"}) in queries
    assert ("GET", "/didinter", {"per_page": "50", "page": "1", "did": "*456*"}) in queries
    assert (
        "POST",
        "/didinter",
        {
            "country_code": "GB",
            "city": "London",
            "forward2did": "15551234567",
            "route2trunk": "7",
        },
    ) in queries


def test_sync_international_page_iteration() -> None:
    pages = list(make_client().international_dids.pages(InternationalDIDListRequest(per_page=5)))
    assert [
        page.current_page for page in pages if isinstance(page, InternationalDIDInventoryResponse)
    ] == [1, 2]


async def test_all_async_international_did_operations_have_parity() -> None:
    http = httpx.AsyncClient(
        base_url="https://example.test", transport=httpx.MockTransport(international_response)
    )
    client = AsyncQuestBlue("user", "password", "key", http_client=http)

    assert isinstance(await client.international_dids.countries(), InternationalCountriesResponse)
    assert isinstance(await client.international_dids.cities("GB"), InternationalCitiesResponse)
    assert isinstance(await client.international_dids.list(), InternationalDIDInventoryResponse)
    order = InternationalDIDOrderRequest(
        country_code="GB", city="London", forward2did=15551234567, route2trunk=7
    )
    assert isinstance(await client.international_dids.order(order), InternationalDIDOrderResponse)
    update = InternationalDIDUpdateRequest(did=442071234567, forward2did=15557654321, route2trunk=8)
    assert await client.international_dids.update(update) is None
    assert await client.international_dids.delete(442071234567) is None
    pages = [
        page
        async for page in client.international_dids.pages(InternationalDIDListRequest(per_page=5))
    ]
    assert len(pages) == 2
    await http.aclose()


@pytest.mark.parametrize(
    "factory",
    [
        lambda: InternationalDIDListRequest(did="*12"),
        lambda: make_client().international_dids.cities("GBR"),
        lambda: InternationalDIDOrderRequest(
            country_code="GB", city="", forward2did=15551234567, route2trunk=7
        ),
        lambda: InternationalDIDOrderRequest(
            country_code="1", city="London", forward2did=15551234567, route2trunk=7
        ),
        lambda: InternationalDIDUpdateRequest(did=0, forward2did=15551234567, route2trunk=7),
        lambda: InternationalCountriesRequest(did=0),
    ],
)
def test_international_did_validation(factory: Any) -> None:
    with pytest.raises((ValidationError, ValueError)):
        factory()


def test_warning_error_and_mutation_retry_safety() -> None:
    warning_client = make_client(
        lambda _: httpx.Response(202, json={"warning": ["international warning"]})
    )
    assert isinstance(warning_client.international_dids.countries(), WarningResponse)
    assert isinstance(
        warning_client.international_dids.update(
            InternationalDIDUpdateRequest(did=442071234567, forward2did=15557654321, route2trunk=8)
        ),
        WarningResponse,
    )

    error_client = make_client(
        lambda _: httpx.Response(206, json={"error": "international DID rejected"})
    )
    with pytest.raises(QuestBlueAPIError, match="international DID rejected"):
        error_client.international_dids.delete(442071234567)

    malformed_client = make_client(lambda _: httpx.Response(200, json={"unexpected": True}))
    with pytest.raises(QuestBlueResponseError, match="empty international DID response"):
        malformed_client.international_dids.delete(442071234567)

    attempts = 0

    def uncertain(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503, json={"error": "uncertain"})

    unsafe_client = make_client(uncertain, max_retries=10)
    with pytest.raises(QuestBlueServerError):
        unsafe_client.international_dids.order(
            InternationalDIDOrderRequest(
                country_code="GB", city="London", forward2did=15551234567, route2trunk=7
            )
        )
    assert attempts == 1


def test_international_did_examples_are_executable_and_guarded() -> None:
    client = make_client()
    assert cities_for_country(client, "gb").data == ["London"]
    request = InternationalDIDOrderRequest(
        country_code="GB", city="London", forward2did=15551234567, route2trunk=7
    )
    with pytest.raises(ValueError, match="confirm_billable"):
        order_international_did(client, request)
    assert order_international_did(client, request, confirm_billable=True).did
    with pytest.raises(ValueError, match="confirm_release"):
        remove_international_did(client, 442071234567)
    assert remove_international_did(client, 442071234567, confirm_release=True) is None
