from __future__ import annotations

from typing import Any

import httpx
import pytest
from pydantic import ValidationError

from questblue import (
    AsyncPaginator,
    AsyncQuestBlue,
    BinaryResponse,
    OnOff,
    PageMetadata,
    Period,
    QuestBlue,
    QuestBlueModel,
    QuestBluePaginationError,
    ResponseEnvelope,
    SyncPaginator,
    TimestampRange,
    WarningResponse,
    model_parser,
    parse_model,
)


class Widget(QuestBlueModel):
    identifier: int
    name: str


def test_models_preserve_unknown_fields_and_serialize_requests() -> None:
    widget = Widget.model_validate({"identifier": "42", "name": "phone", "future": "value"})

    assert widget.identifier == 42
    assert widget.extra_fields == {"future": "value"}
    assert widget.to_request_params() == {
        "identifier": 42,
        "name": "phone",
        "future": "value",
    }


def test_generic_response_envelope_validates_nested_data_and_keeps_raw_payload() -> None:
    payload = {"data": {"identifier": 7, "name": "fax", "new_field": True}, "trace": "abc"}
    parsed = parse_model(ResponseEnvelope[Widget], payload)

    assert parsed.data.data == Widget(identifier=7, name="fax", new_field=True)
    assert parsed.data.extra_fields == {"trace": "abc"}
    assert parsed.raw is payload


def test_warning_response_defaults_and_preserves_future_fields() -> None:
    warning = WarningResponse.model_validate({"warning": ["partial result"], "code": 20201})
    assert warning.warning == ["partial result"]
    assert warning.extra_fields == {"code": 20201}


def test_open_enums_accept_new_upstream_values_without_losing_them() -> None:
    assert OnOff("on") is OnOff.ON
    future = OnOff("automatic")
    assert future.value == "automatic"
    assert future.name == "UNKNOWN_AUTOMATIC"
    assert Period("nextmonth").value == "nextmonth"


def test_timestamp_range_validates_order_and_serializes_for_query() -> None:
    period = TimestampRange(start=100, end=200)
    assert period.to_query_value() == [100, 200]

    with pytest.raises(ValidationError, match="end must be greater"):
        TimestampRange(start=200, end=100)


def test_binary_response_extracts_filename() -> None:
    response = BinaryResponse.from_content(
        b"pdf",
        content_type="application/pdf",
        content_disposition='attachment; filename="report.pdf"',
    )
    assert response.content == b"pdf"
    assert response.content_type == "application/pdf"
    assert response.filename == "report.pdf"


def test_page_metadata_supports_all_documented_completion_signals() -> None:
    assert PageMetadata(current_page=1, total_pages=2).next_page(25) == 2
    assert PageMetadata(current_page=2, total_pages=2).next_page(25) is None
    assert PageMetadata(current_page=1, total=6, per_page=5).next_page(5) == 2
    assert PageMetadata(current_page=2, total=6, per_page=5).next_page(1) is None
    assert PageMetadata(current_page=1, per_page=5).next_page(4) is None
    assert PageMetadata(current_page=1).next_page(0) is None


def test_sync_paginator_iterates_items_and_exposes_raw_pages() -> None:
    payloads = {
        1: {"data": [{"identifier": 1, "name": "one"}], "current_page": 1, "total_pages": 2},
        2: {
            "data": [{"identifier": 2, "name": "two", "future": "kept"}],
            "current_page": 2,
            "total_pages": 2,
        },
    }
    paginator = SyncPaginator(lambda page: payloads[page], item_parser=model_parser(Widget))

    assert [item.name for item in paginator] == ["one", "two"]
    pages = list(paginator.pages())
    assert pages[1].items[0].extra_fields == {"future": "kept"}
    assert pages[1].raw is payloads[2]


def test_sync_paginator_supports_nonstandard_data_with_selector() -> None:
    paginator = SyncPaginator(
        lambda _: {"data": {"15551234567": ["trunk-a"]}, "total_pages": 1},
        item_selector=lambda payload: payload["data"].items(),
    )
    assert list(paginator) == [("15551234567", ["trunk-a"])]


def test_sync_paginator_rejects_invalid_configuration_and_repeated_pages() -> None:
    with pytest.raises(ValueError, match="start_page"):
        SyncPaginator(lambda _: {}, start_page=0)
    with pytest.raises(ValueError, match="max_pages"):
        SyncPaginator(lambda _: {}, max_pages=0)

    paginator = SyncPaginator(
        lambda _: {"data": [1], "current_page": 1, "total_pages": 2}, max_pages=3
    )
    with pytest.raises(QuestBluePaginationError, match="repeated page"):
        list(paginator)


async def test_async_paginator_iterates_pages_and_items() -> None:
    async def fetch(page: int) -> dict[str, Any]:
        return {"data": [page], "current_page": page, "total_pages": 2}

    paginator = AsyncPaginator(fetch)
    assert [item async for item in paginator] == [1, 2]
    assert [page.current_page async for page in paginator.pages()] == [1, 2]


def test_sync_client_paginator_copies_params_and_sets_page() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        page = int(request.url.params["page"])
        return httpx.Response(
            200,
            json={"data": [{"identifier": page, "name": f"page-{page}"}], "total_pages": 2},
        )

    params = {"per_page": 1}
    http = httpx.Client(base_url="https://example.test", transport=httpx.MockTransport(handler))
    client = QuestBlue("user", "password", "key", http_client=http)

    items = list(client.paginate("/widgets", params=params, item_parser=model_parser(Widget)))
    assert [item.identifier for item in items] == [1, 2]
    assert params == {"per_page": 1}
    assert [request.url.params["page"] for request in requests] == ["1", "2"]


async def test_async_client_paginator() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["page"])
        return httpx.Response(200, json={"data": [page], "total_pages": 2})

    http = httpx.AsyncClient(
        base_url="https://example.test", transport=httpx.MockTransport(handler)
    )
    client = AsyncQuestBlue("user", "password", "key", http_client=http)

    assert [item async for item in client.paginate("/widgets")] == [1, 2]
    await http.aclose()


def test_client_paginator_rejects_non_mapping_payload() -> None:
    http = httpx.Client(
        base_url="https://example.test",
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=[])),
    )
    client = QuestBlue("user", "password", "key", http_client=http)

    with pytest.raises(TypeError, match="JSON object"):
        list(client.paginate("/widgets"))
