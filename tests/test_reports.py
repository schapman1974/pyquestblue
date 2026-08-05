from __future__ import annotations

import base64
import io
from datetime import datetime, timezone
from typing import Any

import httpx
import pytest
from pydantic import ValidationError

from questblue import (
    AsyncQuestBlue,
    CallDetailRecord,
    CallDirection,
    CallHistoryRequest,
    CallHistoryResponse,
    CallSummaryRecord,
    FaxDirection,
    FaxDownloadResponse,
    FaxHistoryPeriod,
    FaxHistoryRequest,
    FaxHistoryResponse,
    FaxService,
    OnOff,
    Period,
    QuestBlue,
    QuestBlueAPIError,
    QuestBlueResponseError,
    TimestampRange,
    WarningResponse,
    export_rows,
)


def call_page(page: int = 1) -> dict[str, Any]:
    if page == 1:
        return {
            "data": [
                {
                    "call_type": "Inbound Call",
                    "call_status": "ok",
                    "call_id": 101,
                    "did": "15551234567",
                    "did_to": "15557654321",
                    "trunk": "primary",
                    "start_time": "2026-08-01T12:00:00Z",
                    "call_duration_min": "1.25",
                    "billed_min": "2",
                    "cost": "0.02",
                    "future_field": "kept",
                }
            ],
            "total": 2,
            "total_pages": 2,
            "current_page": 1,
        }
    return {
        "data": [
            {
                "call_type": "Outbound Call",
                "call_status": "ok",
                "call_id": 102,
                "call_duration_min": "2.0",
            }
        ],
        "total": 2,
        "total_pages": 2,
        "current_page": 2,
    }


def fax_page(page: int = 1) -> dict[str, Any]:
    return {
        "data": [
            {
                "did_from": "15551234567",
                "did_to": "15557654321",
                "fax_id": f"fax-{page}",
                "send_time": "2026-08-01T12:00:00Z",
                "service": "enterprise",
                "status": "processing",
                "type": "out",
            }
        ],
        "current_page": page,
        "total": 2,
        "total_pages": 2,
    }


def handler(request: httpx.Request) -> httpx.Response:
    page = int(request.url.params.get("page", "1"))
    if request.url.path == "/callhistory":
        if request.url.params.get("summary_only") == "on":
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "call_number": 25,
                            "call_type": "Outbound Local Call",
                            "cost": "0.12",
                            "total_duration_min": "10.00",
                        }
                    ],
                    "total": 1,
                },
            )
        return httpx.Response(200, json=call_page(page))
    if request.url.path == "/faxhistory":
        return httpx.Response(200, json=fax_page(page))
    if request.url.path == "/faxdownload":
        return httpx.Response(
            200, json={"data": {"fax_base64": base64.b64encode(b"%PDF-report").decode()}}
        )
    raise AssertionError(request.url.path)


def client(custom_handler: Any = handler) -> QuestBlue:
    http = httpx.Client(
        base_url="https://example.test", transport=httpx.MockTransport(custom_handler)
    )
    return QuestBlue("user", "password", "key", http_client=http)


def async_client(custom_handler: Any = handler) -> AsyncQuestBlue:
    http = httpx.AsyncClient(
        base_url="https://example.test", transport=httpx.MockTransport(custom_handler)
    )
    return AsyncQuestBlue("user", "password", "key", http_client=http)


def test_call_history_filters_summary_and_detailed_variants() -> None:
    qb = client()
    request = CallHistoryRequest(
        timezone="America/New_York",
        last_id=100,
        trunk=["primary", "backup"],
        period=TimestampRange(start=1_754_000_000, end=1_754_086_400),
        success_call_only=OnOff.ON,
        did=15551234567,
        type=CallDirection.INBOUND,
        country_id=1,
        per_page=5000,
        get_id=OnOff.ON,
        get_fax=OnOff.OFF,
    )
    response = qb.reports.call_history(request)
    assert isinstance(response, CallHistoryResponse)
    assert isinstance(response.data[0], CallDetailRecord)
    assert response.data[0].extra_fields == {"future_field": "kept"}
    assert response.next_page(5000) == 2
    summary = qb.reports.call_history(CallHistoryRequest(summary_only=OnOff.ON))
    assert isinstance(summary, CallHistoryResponse)
    assert isinstance(summary.data[0], CallSummaryRecord)
    assert summary.data[0].call_number == 25


def test_report_query_serialization_and_periods() -> None:
    call = CallHistoryRequest(
        period=TimestampRange(start=100, end=200), trunk=["a", "b"], timezone="UTC"
    )
    assert call.to_request_params()["period"] == [100, 200]
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    end = datetime(2026, 8, 2, tzinfo=timezone.utc)
    fax = FaxHistoryRequest(
        did=[15551234567, 15557654321],
        service=FaxService.PRO,
        type=FaxDirection.IN,
        fax_id="fax-1",
        period=(start, end),
        per_page=1000,
        page=2,
    )
    assert fax.to_request_params()["period"] == [start.isoformat(), end.isoformat()]


def test_sync_iterators_and_fax_download_to_file() -> None:
    qb = client()
    calls = list(qb.reports.iter_call_history(CallHistoryRequest(per_page=5)))
    faxes = list(qb.reports.iter_fax_history(FaxHistoryRequest(per_page=5)))
    assert [record.call_id for record in calls if isinstance(record, CallDetailRecord)] == [
        101,
        102,
    ]
    assert [record.fax_id for record in faxes] == ["fax-1", "fax-2"]
    response = qb.reports.download_fax(123)
    assert isinstance(response, FaxDownloadResponse)
    assert b"".join(response.data.iter_bytes(chunk_size=3)) == b"%PDF-report"
    destination = io.BytesIO()
    assert qb.reports.download_fax_to(123, destination) == len(b"%PDF-report")
    assert destination.getvalue() == b"%PDF-report"


@pytest.mark.asyncio
async def test_async_reports_parity_and_iteration() -> None:
    qb = async_client()
    calls = await qb.reports.call_history(CallHistoryRequest(period=Period.TODAY))
    faxes = await qb.reports.fax_history(FaxHistoryRequest(period=FaxHistoryPeriod.YESTERDAY))
    download = await qb.reports.download_fax(123)
    assert isinstance(calls, CallHistoryResponse)
    assert isinstance(faxes, FaxHistoryResponse)
    assert isinstance(download, FaxDownloadResponse)
    assert len([record async for record in qb.reports.iter_call_history()]) == 2
    assert len([record async for record in qb.reports.iter_fax_history()]) == 2
    destination = io.BytesIO()
    assert await qb.reports.download_fax_to(123, destination) == len(b"%PDF-report")


@pytest.mark.parametrize(
    "factory",
    [
        lambda: CallHistoryRequest(timezone="Mars/Olympus_Mons"),
        lambda: CallHistoryRequest(trunk=[]),
        lambda: CallHistoryRequest(trunk=[""]),
        lambda: CallHistoryRequest(per_page=4),
        lambda: CallHistoryRequest(period=TimestampRange(start=0, end=32 * 24 * 60 * 60)),
        lambda: FaxHistoryRequest(did=[]),
        lambda: FaxHistoryRequest(did=[0]),
        lambda: FaxHistoryRequest(per_page=1001),
        lambda: FaxHistoryRequest(
            period=(
                datetime(2026, 8, 2, tzinfo=timezone.utc),
                datetime(2026, 8, 1, tzinfo=timezone.utc),
            )
        ),
    ],
)
def test_report_request_validation(factory: Any) -> None:
    with pytest.raises(ValidationError):
        factory()


def test_download_validation_chunking_and_export_rows() -> None:
    with pytest.raises(ValidationError):
        FaxDownloadResponse.model_validate({"data": {"fax_base64": "invalid"}})
    response = FaxDownloadResponse.model_validate({"data": {"fax_base64": "YQ=="}})
    with pytest.raises(ValueError, match="positive"):
        list(response.data.iter_bytes(0))
    call_response = CallHistoryResponse.model_validate(call_page())
    rows = export_rows(call_response)
    assert rows[0]["call_type"] == "Inbound Call"
    assert "15551234567" not in repr(call_response)
    assert CallHistoryRequest(timezone=None).timezone is None
    assert CallHistoryResponse(data=[call_response.data[0]], total=2).next_page(1) == 2
    assert CallHistoryResponse(data=[], total=0).next_page(1) is None


def test_warnings_errors_and_malformed_responses() -> None:
    warning = client(lambda request: httpx.Response(202, json={"warning": ["not ready"]}))
    result = warning.reports.call_history()
    assert isinstance(result, WarningResponse)
    assert list(warning.reports.iter_call_history()) == []
    with pytest.raises(ValueError, match="warning"):
        warning.reports.download_fax_to(123, io.BytesIO())

    malformed = client(lambda request: httpx.Response(200, json={"data": "wrong"}))
    with pytest.raises(QuestBlueResponseError):
        malformed.reports.call_history()

    failed = client(lambda request: httpx.Response(206, json={"error": "bad filter"}))
    with pytest.raises(QuestBlueAPIError, match="bad filter"):
        failed.reports.fax_history()


@pytest.mark.asyncio
async def test_async_warning_iterators_and_download_guard() -> None:
    qb = async_client(lambda request: httpx.Response(202, json={"warning": ["not ready"]}))
    assert [record async for record in qb.reports.iter_call_history()] == []
    assert [record async for record in qb.reports.iter_fax_history()] == []
    with pytest.raises(ValueError, match="warning"):
        await qb.reports.download_fax_to(123, io.BytesIO())
