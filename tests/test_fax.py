from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List

import httpx
import pytest
from pydantic import ValidationError

from examples.fax import allow_email_to_send, send_fax
from questblue import (
    MAX_FAX_FILE_SIZE,
    AsyncQuestBlue,
    AvailableFaxDIDsResponse,
    FaxAvailabilityRequest,
    FaxDIDStatus,
    FaxDIDType,
    FaxEmailPermissionDeleteRequest,
    FaxEmailPermissionRequest,
    FaxInventoryResponse,
    FaxListRequest,
    FaxOrderRequest,
    FaxPauseRequest,
    FaxRateCentersResponse,
    FaxSendRequest,
    FaxSendResponse,
    FaxStatesResponse,
    FaxTier,
    FaxToggle,
    FaxUpdateRequest,
    FaxYesNo,
    PauseAction,
    QuestBlue,
    QuestBlueAPIError,
    QuestBlueResponseError,
    QuestBlueServerError,
    UnsetAccount,
    WarningResponse,
)


def response(request: httpx.Request) -> httpx.Response:
    payloads: Dict[str, Any] = {
        "/fax/states": {"data": ["NC", "NY"], "total": 2},
        "/fax/ratecenters": {"data": {"RALEIGH": "Raleigh"}, "total": 1},
        "/fax/available": {"data": ["15551234567"], "total": 1},
        "/fax/send": {"data": {"fax_id": 9001}},
    }
    if request.url.path == "/fax" and request.method == "GET":
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "did": "15551234567",
                        "did_type": "local",
                        "fax_login": "fax-user",
                        "fax_name": "Fax User",
                        "is_full": "yes",
                        "note": "primary",
                        "report_att": "no",
                        "status": "active",
                    }
                ],
                "current_page": 1,
                "total": 1,
                "total_pages": 1,
            },
        )
    if request.url.path in payloads:
        return httpx.Response(200, json=payloads[request.url.path])
    return httpx.Response(200)


def client(handler: Any = response, max_retries: int = 2) -> QuestBlue:
    return QuestBlue(
        "u",
        "p",
        "k",
        max_retries=max_retries,
        http_client=httpx.Client(base_url="https://test", transport=httpx.MockTransport(handler)),
    )


def order_request() -> FaxOrderRequest:
    return FaxOrderRequest(
        did=15551234567,
        tier=FaxTier.TIER_1B,
        cnam=FaxToggle.ON,
        note="primary",
        pin=1234,
        fax_name="Fax User",
        fax_login="fax-user",
        fax_password="private-password",
        fax_email="fax@example.test",
        is_full=FaxYesNo.YES,
        report_att=FaxYesNo.NO,
        post2url="https://app.example.test/fax",
        ata_mac_address="00:11:22:33:44:55",
    )


def test_all_sync_fax_operations_and_fields() -> None:
    seen: List[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return response(request)

    qb = client(handler)
    assert isinstance(qb.fax.states(), FaxStatesResponse)
    assert isinstance(qb.fax.rate_centers("nc"), FaxRateCentersResponse)
    assert isinstance(
        qb.fax.available(
            FaxAvailabilityRequest(
                did_type=FaxDIDType.LOCAL,
                tier=FaxTier.TIER_1B,
                state="nc",
                ratecenter="RALEIGH",
            )
        ),
        AvailableFaxDIDsResponse,
    )
    assert qb.fax.create(order_request()) is None
    assert isinstance(qb.fax.list(FaxListRequest(did="*4567", per_page=50)), FaxInventoryResponse)
    assert (
        qb.fax.update(
            FaxUpdateRequest(
                did=15551234567,
                note="updated",
                pin=4567,
                cnam=FaxToggle.OFF,
                is_full=FaxYesNo.NO,
                report_att=FaxYesNo.YES,
                post2url="empty",
                ata_mac_address="001122334455",
            )
        )
        is None
    )
    assert qb.fax.delete(15551234567) is None
    assert isinstance(
        qb.fax.send(
            FaxSendRequest.from_bytes(
                b"fax document", "document.pdf", did_from=15551234567, did_to=15557654321
            )
        ),
        FaxSendResponse,
    )
    assert qb.fax.move_to_voice(15551234567) is None
    assert qb.fax.pause(FaxPauseRequest(did=15551234567, action=PauseAction.PAUSE)) is None
    assert (
        qb.fax.set_email_permission(
            FaxEmailPermissionRequest(
                did=15551234567,
                email="sender@example.test",
                allow_send=FaxYesNo.YES,
                allow_receive=FaxYesNo.NO,
            )
        )
        is None
    )
    assert (
        qb.fax.delete_email_permission(
            FaxEmailPermissionDeleteRequest(did=15551234567, email="sender@example.test")
        )
        is None
    )

    queries = {(item.method, item.url.path): dict(item.url.params) for item in seen}
    assert queries[("GET", "/fax/ratecenters")]["state"] == "NC"
    assert queries[("GET", "/fax/available")]["type"] == "local"
    assert queries[("POST", "/fax")]["ata_mac_address"] == "001122334455"
    assert queries[("POST", "/fax/send")]["file"] == base64.b64encode(b"fax document").decode()
    assert queries[("PUT", "/fax/pause")]["action"] == "pause"
    assert queries[("POST", "/fax/email")]["allow_send"] == "yes"


async def test_all_async_fax_operations_have_parity() -> None:
    http = httpx.AsyncClient(base_url="https://test", transport=httpx.MockTransport(response))
    qb = AsyncQuestBlue("u", "p", "k", http_client=http)
    assert isinstance(await qb.fax.states(), FaxStatesResponse)
    assert isinstance(await qb.fax.rate_centers("NY"), FaxRateCentersResponse)
    assert isinstance(
        await qb.fax.available(FaxAvailabilityRequest(did_type=FaxDIDType.TOLL_FREE, code=83)),
        AvailableFaxDIDsResponse,
    )
    assert await qb.fax.create(FaxOrderRequest(did=15551234567)) is None
    assert isinstance(await qb.fax.list(), FaxInventoryResponse)
    assert await qb.fax.update(FaxUpdateRequest(did=15551234567, unset_acc=UnsetAccount.ON)) is None
    assert await qb.fax.delete(15551234567) is None
    request = FaxSendRequest.from_file(
        BytesIO(b"fax"), "fax.txt", did_from=15551234567, did_to=15557654321
    )
    assert isinstance(await qb.fax.send(request), FaxSendResponse)
    assert await qb.fax.move_to_voice(15551234567) is None
    assert await qb.fax.pause(FaxPauseRequest(did=15551234567, action=PauseAction.UNPAUSE)) is None
    assert (
        await qb.fax.set_email_permission(
            FaxEmailPermissionRequest(did=15551234567, email="sender@example.test")
        )
        is None
    )
    assert (
        await qb.fax.delete_email_permission(
            FaxEmailPermissionDeleteRequest(did=15551234567, email="sender@example.test")
        )
        is None
    )
    await http.aclose()


@pytest.mark.parametrize(
    "factory",
    [
        lambda: FaxAvailabilityRequest(did_type=FaxDIDType.LOCAL),
        lambda: FaxAvailabilityRequest(did_type=FaxDIDType.LOCAL, state="N", ratecenter="X"),
        lambda: FaxAvailabilityRequest(did_type=FaxDIDType.TOLL_FREE),
        lambda: FaxAvailabilityRequest(did_type=FaxDIDType.TOLL_FREE, tier=FaxTier.TIER_2, code=83),
        lambda: FaxListRequest(did="*12"),
        lambda: FaxListRequest(per_page=4),
        lambda: FaxOrderRequest(did=5551234),
        lambda: FaxOrderRequest(did=15551234567, fax_name="incomplete"),
        lambda: FaxOrderRequest(did=15551234567, fax_email="bad-email"),
        lambda: FaxOrderRequest(did=15551234567, post2url="not-a-url"),
        lambda: FaxOrderRequest(did=15551234567, ata_mac_address="bad-mac"),
        lambda: FaxUpdateRequest(did=15551234567),
        lambda: FaxUpdateRequest(did=15551234567, unset_acc=UnsetAccount.ON, fax_name="conflict"),
        lambda: FaxUpdateRequest(did=15551234567, fax_name="incomplete"),
        lambda: FaxEmailPermissionRequest(did=15551234567, email="bad-email"),
        lambda: FaxSendRequest(
            file="not-base64", filename="fax.pdf", did_from=15551234567, did_to=15557654321
        ),
        lambda: FaxSendRequest.from_bytes(b"", "fax.pdf", did_from=15551234567, did_to=15557654321),
        lambda: FaxSendRequest.from_bytes(
            b"fax", "fax.exe", did_from=15551234567, did_to=15557654321
        ),
        lambda: FaxSendRequest.from_bytes(
            b"fax", "folder/fax.pdf", did_from=15551234567, did_to=15557654321
        ),
        lambda: FaxSendRequest.from_bytes(
            b"x" * (MAX_FAX_FILE_SIZE + 1),
            "fax.pdf",
            did_from=15551234567,
            did_to=15557654321,
        ),
    ],
)
def test_fax_validation(factory: Any) -> None:
    with pytest.raises((ValidationError, ValueError)):
        factory()


def test_file_path_helper_and_sensitive_diagnostics(tmp_path: Path) -> None:
    path = tmp_path / "fax.pdf"
    path.write_bytes(b"fax file")
    request = FaxSendRequest.from_path(path, did_from=15551234567, did_to=15557654321)
    assert base64.b64decode(request.file) == b"fax file"
    assert request.filename == "fax.pdf"
    assert "fax file" not in repr(request)
    assert "15557654321" not in repr(request)
    order = order_request()
    assert "private-password" not in repr(order)
    assert "fax@example.test" not in repr(order)
    assert FaxOrderRequest(did=15551234567, ata_mac_address=None).ata_mac_address is None


@pytest.mark.parametrize("status", ["active", "paused", "pending", "provider-added"])
def test_fax_status_is_forward_compatible(status: str) -> None:
    assert FaxDIDStatus(status).value == status


def test_pagination_and_examples(tmp_path: Path) -> None:
    assert FaxInventoryResponse(current_page=1, total_pages=2).next_page() == 2
    assert FaxInventoryResponse(current_page=2, total_pages=2).next_page() is None
    path = tmp_path / "fax.pdf"
    path.write_bytes(b"fax")
    qb = client()
    with pytest.raises(ValueError, match="confirm_destination"):
        send_fax(qb, path, 15551234567, 15557654321)
    assert isinstance(
        send_fax(qb, path, 15551234567, 15557654321, confirm_destination=True),
        FaxSendResponse,
    )
    assert allow_email_to_send(qb, 15551234567, "sender@example.test") is None


def test_warnings_errors_empty_bodies_and_retry_safety() -> None:
    warning = client(lambda _: httpx.Response(202, json={"warning": ["provisioning delayed"]}))
    assert isinstance(warning.fax.states(), WarningResponse)
    assert isinstance(warning.fax.create(FaxOrderRequest(did=15551234567)), WarningResponse)
    error = client(lambda _: httpx.Response(206, json={"error": "fax rejected"}))
    with pytest.raises(QuestBlueAPIError, match="fax rejected"):
        error.fax.send(
            FaxSendRequest.from_bytes(b"fax", "fax.pdf", did_from=15551234567, did_to=15557654321)
        )
    malformed = client(lambda _: httpx.Response(200, json={"unexpected": True}))
    with pytest.raises(QuestBlueResponseError, match=r"body for an empty Fax\.Pro response"):
        malformed.fax.delete(15551234567)

    attempts = 0

    def uncertain(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503)

    unsafe = client(uncertain, max_retries=10)
    with pytest.raises(QuestBlueServerError):
        unsafe.fax.move_to_voice(15551234567)
    assert attempts == 1
