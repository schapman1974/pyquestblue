from __future__ import annotations

import base64
from datetime import date, time
from pathlib import Path
from typing import Any

import httpx
import pytest
from pydantic import ValidationError

from questblue import (
    MAX_LNP_BILL_SIZE,
    AsyncQuestBlue,
    DIDMode,
    LNPBillUpload,
    LNPCheckRequest,
    LNPCheckResponse,
    LNPCreateRequest,
    LNPCreateResponse,
    LNPListRequest,
    LNPListResponse,
    LNPStatus,
    LNPUpdateRequest,
    QuestBlue,
    QuestBlueResponseError,
    ServiceLocation,
    WarningResponse,
    YesNo,
)


def create_request(**overrides: Any) -> LNPCreateRequest:
    values = {
        "number2port": [15551234567],
        "provider_name": "Current Carrier",
        "account_no": "private-account",
        "authorize_contact": "Jane Customer",
        "contact_title": "President",
        "street_no": "123",
        "street_name": "Main Street",
        "city": "Cary",
        "state": "nc",
        "zipcode": "27513",
        "billing_telephone_no": "5551234567",
        "company": "Example LLC",
        "bill_file": base64.b64encode(b"bill").decode(),
        "bill_filename": "bill.pdf",
    }
    values.update(overrides)
    return LNPCreateRequest(**values)


def response(request: httpx.Request) -> httpx.Response:
    if request.method == "GET" and request.url.path == "/lnp/check":
        return httpx.Response(200, json={"data": {"foc_days": 3}})
    if request.method == "POST":
        return httpx.Response(200, json={"data": [{"id": "12345"}]})
    if request.method == "GET":
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "12345",
                        "number2port": "15551234567",
                        "status": "carrier_review",
                        "account_no": "private-account",
                        "authorize_contact": "Jane Customer",
                        "billing_telephone_no": "5551234567",
                        "city": "Cary",
                        "company": "Example LLC",
                        "contact_title": "President",
                        "created_by": "2026-08-01T12:00:00Z",
                        "did_mode": "voice",
                        "foc_date": "2026-08-10T12:00:00Z",
                        "lidb_list": "no",
                        "location": "business",
                        "partial_port": "no",
                        "provider_name": "Carrier",
                        "street_name": "Main",
                        "street_no": "123",
                        "wireless_no": "no",
                        "zipcode": "27513",
                    }
                ],
                "total": 1,
                "total_pages": 1,
                "current_page": 1,
            },
        )
    return httpx.Response(200)


def client(handler: Any = response) -> QuestBlue:
    http = httpx.Client(base_url="https://example.test", transport=httpx.MockTransport(handler))
    return QuestBlue("user", "password", "key", http_client=http)


def async_client(handler: Any = response) -> AsyncQuestBlue:
    http = httpx.AsyncClient(
        base_url="https://example.test", transport=httpx.MockTransport(handler)
    )
    return AsyncQuestBlue("user", "password", "key", http_client=http)


def test_all_sync_lnp_lifecycle_operations() -> None:
    qb = client()
    checked = qb.lnp.check(LNPCheckRequest(number2port=[15551234567, 15557654321]))
    created = qb.lnp.create(create_request())
    listed = qb.lnp.list(LNPListRequest(number2port="*4567", id=[12345], per_page=200))
    assert qb.lnp.update(LNPUpdateRequest(id=12345, status="draft")) is None
    assert qb.lnp.delete(12345) is None
    assert isinstance(checked, LNPCheckResponse) and checked.data.foc_days == 3
    assert isinstance(created, LNPCreateResponse) and created.data[0].id == "12345"
    assert isinstance(listed, LNPListResponse)
    assert listed.data[0].status == LNPStatus("carrier_review")
    assert listed.next_page() is None
    assert "private-account" not in repr(listed)


@pytest.mark.asyncio
async def test_all_async_lnp_lifecycle_operations() -> None:
    qb = async_client()
    checked = await qb.lnp.check(LNPCheckRequest(number2port=[15551234567]))
    assert isinstance(checked, LNPCheckResponse)
    assert isinstance(await qb.lnp.create(create_request()), LNPCreateResponse)
    assert isinstance(await qb.lnp.list(), LNPListResponse)
    assert await qb.lnp.update(LNPUpdateRequest(id=12345, trunk="primary")) is None
    assert await qb.lnp.delete(12345) is None


def test_bill_helpers_and_sensitive_values(tmp_path: Path) -> None:
    path = tmp_path / "bill.pdf"
    path.write_bytes(b"private bill")
    upload = LNPBillUpload.from_path(path)
    assert base64.b64decode(upload.bill_file) == b"private bill"
    assert upload.bill_file not in repr(upload)
    request = LNPCreateRequest.with_bill(
        upload,
        number2port=[15551234567],
        provider_name="Carrier",
        account_no="secret-account",
        authorize_contact="Jane",
        contact_title="Owner",
        street_no="123",
        street_name="Main",
        city="Cary",
        zipcode="27513",
        billing_telephone_no="5551234567",
        company="Example LLC",
    )
    assert "secret-account" not in repr(request)
    assert create_request(activate_time=time(10)).activate_time == time(10)


@pytest.mark.parametrize(
    "factory",
    [
        lambda: LNPBillUpload.from_bytes(b"", "bill.pdf"),
        lambda: LNPBillUpload.from_bytes(b"x", "bill.txt"),
        lambda: LNPBillUpload.from_bytes(b"x" * (MAX_LNP_BILL_SIZE + 1), "bill.pdf"),
        lambda: LNPBillUpload(bill_file="bad", bill_filename="bill.pdf"),
        lambda: LNPBillUpload(
            bill_file="A" * (4 * ((MAX_LNP_BILL_SIZE + 2) // 3) + 4),
            bill_filename="bill.pdf",
        ),
        lambda: LNPCheckRequest(number2port=[123]),
        lambda: LNPListRequest(number2port="*1"),
        lambda: LNPListRequest(id=[]),
        lambda: LNPUpdateRequest(id=1),
        lambda: create_request(partial_port=YesNo.YES),
        lambda: create_request(location=ServiceLocation.BUSINESS, company=None),
        lambda: create_request(wireless_no=YesNo.YES),
        lambda: create_request(
            wireless_no=YesNo.YES, pincode=1234, ssn=1234, foc_date=date(2026, 8, 10)
        ),
        lambda: create_request(activate_time=time(10, 30)),
        lambda: LNPUpdateRequest(id=1, bill_file="YQ=="),
        lambda: create_request(did_mode=DIDMode.FAX, trunk="voice-only"),
        lambda: create_request(billing_telephone_no="bad"),
        lambda: create_request(state="North Carolina"),
        lambda: create_request(bill_filename="bill.txt"),
    ],
)
def test_lnp_validation(factory: Any) -> None:
    with pytest.raises((ValidationError, ValueError)):
        factory()


def test_lnp_warnings_errors_and_pagination() -> None:
    warning = client(lambda request: httpx.Response(202, json={"warning": ["pending"]}))
    assert isinstance(warning.lnp.create(create_request()), WarningResponse)
    assert isinstance(warning.lnp.update(LNPUpdateRequest(id=1, trunk="new")), WarningResponse)
    error = client(lambda request: httpx.Response(202, json={"error": "not portable"}))
    with pytest.raises(QuestBlueResponseError, match="not portable"):
        error.lnp.check(LNPCheckRequest(number2port=[15551234567]))
    malformed = client(lambda request: httpx.Response(200, json={"data": "bad"}))
    with pytest.raises(QuestBlueResponseError):
        malformed.lnp.list()
    assert LNPListResponse(current_page=1, total_pages=2).next_page() == 2
