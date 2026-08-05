from __future__ import annotations

import base64
import json
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List

import httpx
import pytest
from pydantic import ValidationError

from examples.enterprise_fax import provision_account, upload_and_send
from questblue import (
    MAX_FAX_FILE_SIZE,
    AsyncQuestBlue,
    EnterpriseFaxEmailListRequest,
    EnterpriseFaxEmailListResponse,
    EnterpriseFaxEmailPermissionDeleteRequest,
    EnterpriseFaxEmailPermissionRequest,
    EnterpriseFaxGroupCreateRequest,
    EnterpriseFaxGroupListRequest,
    EnterpriseFaxGroupListResponse,
    EnterpriseFaxGroupUpdateRequest,
    EnterpriseFaxInventoryResponse,
    EnterpriseFaxListRequest,
    EnterpriseFaxOrderRequest,
    EnterpriseFaxPauseRequest,
    EnterpriseFaxPermissionDeleteRequest,
    EnterpriseFaxPermissionListRequest,
    EnterpriseFaxPermissionListResponse,
    EnterpriseFaxPermissionRequest,
    EnterpriseFaxSendRequest,
    EnterpriseFaxSendResponse,
    EnterpriseFaxUpdateRequest,
    EnterpriseFaxUploadRequest,
    EnterpriseFaxUploadResponse,
    EnterpriseFaxUserCreateRequest,
    EnterpriseFaxUserListRequest,
    EnterpriseFaxUserListResponse,
    EnterpriseFaxUserUpdateRequest,
    FaxDIDStatus,
    FaxTier,
    FaxToggle,
    PauseAction,
    QuestBlue,
    QuestBlueAPIError,
    QuestBlueResponseError,
    QuestBlueServerError,
    WarningResponse,
)


def response(request: httpx.Request) -> httpx.Response:
    payloads: Dict[str, Any] = {
        "/fax2": {
            "data": [
                {
                    "did": "15551234567",
                    "did_type": "local",
                    "note": "main",
                    "sname": "ops",
                    "status": "active",
                }
            ],
            "current_page": 1,
            "total": 1,
            "total_pages": 1,
        },
        "/fax2/email": {
            "data": [
                {
                    "did": "15551234567",
                    "email": "ops@example.test",
                    "sname": "ops",
                    "allow_send": "yes",
                    "allow_receive": "no",
                }
            ],
            "current_page": 1,
            "total": 1,
            "total_pages": 1,
        },
        "/fax2/group": {"data": [{"sname": "ops", "name": "Operations"}], "total": 1},
        "/fax2/user": {
            "data": [
                {
                    "fax_lname": "User",
                    "fax_name": "Fax",
                    "is_admin": "off",
                    "login": "fax-user",
                    "password": "server-secret",
                    "sname": "ops",
                }
            ],
            "current_page": 1,
            "total": 1,
            "total_pages": 1,
        },
        "/fax2/permit": {
            "data": [
                {
                    "fax_login": "fax-user",
                    "did": "15551234567",
                    "allow_send": "on",
                    "allow_delete": "off",
                    "allow_list_in": "on",
                    "allow_list_out": "on",
                    "create_date": "Aug 5, 2026",
                }
            ],
            "current_page": 1,
            "total": 1,
            "total_pages": 1,
        },
    }
    if request.url.path == "/fax2/upload":
        return httpx.Response(200, json={"file_id": "file-1"})
    if request.url.path == "/fax2/send":
        return httpx.Response(200, json={"fax_id": 9001})
    if request.method == "GET":
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


def user_request() -> EnterpriseFaxUserCreateRequest:
    return EnterpriseFaxUserCreateRequest(
        fax_login="fax-user",
        fax_password="private-password",
        sname="ops",
        fax_name="Fax",
        fax_lname="User",
        fax_email="fax@example.test",
        is_admin=FaxToggle.OFF,
    )


def permission_request() -> EnterpriseFaxPermissionRequest:
    return EnterpriseFaxPermissionRequest(
        fax_login="fax-user",
        did=15551234567,
        allow_send=FaxToggle.ON,
        allow_delete=FaxToggle.OFF,
        allow_list_in=FaxToggle.ON,
        allow_list_out=FaxToggle.ON,
    )


def test_all_sync_enterprise_fax_operations() -> None:
    seen: List[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return response(request)

    qb = client(handler)
    assert isinstance(
        qb.enterprise_fax.list(EnterpriseFaxListRequest(did="*4567", per_page=50)),
        EnterpriseFaxInventoryResponse,
    )
    assert (
        qb.enterprise_fax.create(
            EnterpriseFaxOrderRequest(
                did=15551234567,
                tier=FaxTier.TIER_1B,
                note="main",
                pin=1234,
                sname="ops",
                cnam=FaxToggle.ON,
                post2url="https://app.example.test/fax",
                ata_mac_address="00:11:22:33:44:55",
            )
        )
        is None
    )
    assert (
        qb.enterprise_fax.update(
            EnterpriseFaxUpdateRequest(
                did=15551234567, note="updated", sname="", post2url="empty", ata_mac_address="empty"
            )
        )
        is None
    )
    assert qb.enterprise_fax.delete(15551234567) is None
    assert isinstance(
        qb.enterprise_fax.list_emails(
            EnterpriseFaxEmailListRequest(did=15551234567, email="ops@example.test")
        ),
        EnterpriseFaxEmailListResponse,
    )
    assert (
        qb.enterprise_fax.set_email_permission(
            EnterpriseFaxEmailPermissionRequest(
                did=15551234567,
                email="ops@example.test",
                allow_send=FaxToggle.ON,
                allow_receive=FaxToggle.OFF,
            )
        )
        is None
    )
    assert (
        qb.enterprise_fax.delete_email_permission(
            EnterpriseFaxEmailPermissionDeleteRequest(did=15551234567, email="ops@example.test")
        )
        is None
    )
    assert isinstance(
        qb.enterprise_fax.list_groups(EnterpriseFaxGroupListRequest(sname="ops")),
        EnterpriseFaxGroupListResponse,
    )
    assert (
        qb.enterprise_fax.create_group(
            EnterpriseFaxGroupCreateRequest(sname="ops", name="Operations")
        )
        is None
    )
    assert (
        qb.enterprise_fax.update_group(
            EnterpriseFaxGroupUpdateRequest(sname="ops", sname_new="support", name_new="Support")
        )
        is None
    )
    assert qb.enterprise_fax.delete_group("support") is None
    assert isinstance(
        qb.enterprise_fax.list_users(
            EnterpriseFaxUserListRequest(sname="ops", fax_login="fax-user")
        ),
        EnterpriseFaxUserListResponse,
    )
    assert qb.enterprise_fax.create_user(user_request()) is None
    assert (
        qb.enterprise_fax.update_user(
            EnterpriseFaxUserUpdateRequest(
                fax_login="fax-user",
                fax_login_new="fax-user-2",
                fax_password="new-password",
                fax_name="New",
                fax_lname="User",
                fax_email="new@example.test",
                is_admin=FaxToggle.ON,
            )
        )
        is None
    )
    assert qb.enterprise_fax.delete_user("fax-user-2") is None
    assert isinstance(
        qb.enterprise_fax.list_permissions(
            EnterpriseFaxPermissionListRequest(fax_login="fax-user", did=15551234567)
        ),
        EnterpriseFaxPermissionListResponse,
    )
    assert qb.enterprise_fax.set_permission(permission_request()) is None
    assert (
        qb.enterprise_fax.delete_permission(
            EnterpriseFaxPermissionDeleteRequest(fax_login="fax-user", did=15551234567)
        )
        is None
    )
    assert isinstance(
        qb.enterprise_fax.upload(EnterpriseFaxUploadRequest.from_bytes(b"first", "first.pdf")),
        EnterpriseFaxUploadResponse,
    )
    assert isinstance(
        qb.enterprise_fax.send(
            EnterpriseFaxSendRequest(
                did_from=15551234567, did_to=15557654321, file_id=["file-1", "file-2"]
            )
        ),
        EnterpriseFaxSendResponse,
    )
    assert (
        qb.enterprise_fax.pause(
            EnterpriseFaxPauseRequest(did=15551234567, action=PauseAction.PAUSE)
        )
        is None
    )
    queries = {
        (item.method, item.url.path): dict(item.url.params)
        for item in seen
        if item.url.path != "/fax2/upload"
    }
    assert queries[("POST", "/fax2")]["ata_mac_address"] == "001122334455"
    assert queries[("POST", "/fax2/send")]["file_id"] == "file-1,file-2"
    upload = next(item for item in seen if item.url.path == "/fax2/upload")
    assert upload.headers["content-type"] == "application/json"
    assert base64.b64decode(json.loads(upload.content)["file"]) == b"first"


async def test_all_async_enterprise_fax_operations_have_parity() -> None:
    http = httpx.AsyncClient(base_url="https://test", transport=httpx.MockTransport(response))
    qb = AsyncQuestBlue("u", "p", "k", http_client=http)
    assert isinstance(await qb.enterprise_fax.list(), EnterpriseFaxInventoryResponse)
    assert await qb.enterprise_fax.create(EnterpriseFaxOrderRequest(did=15551234567)) is None
    assert (
        await qb.enterprise_fax.update(EnterpriseFaxUpdateRequest(did=15551234567, note="new"))
        is None
    )
    assert await qb.enterprise_fax.delete(15551234567) is None
    assert isinstance(await qb.enterprise_fax.list_emails(), EnterpriseFaxEmailListResponse)
    assert (
        await qb.enterprise_fax.set_email_permission(
            EnterpriseFaxEmailPermissionRequest(did=15551234567, email="ops@example.test")
        )
        is None
    )
    assert (
        await qb.enterprise_fax.delete_email_permission(
            EnterpriseFaxEmailPermissionDeleteRequest(did=15551234567, email="ops@example.test")
        )
        is None
    )
    assert isinstance(await qb.enterprise_fax.list_groups(), EnterpriseFaxGroupListResponse)
    assert (
        await qb.enterprise_fax.create_group(
            EnterpriseFaxGroupCreateRequest(sname="ops", name="Operations")
        )
        is None
    )
    assert (
        await qb.enterprise_fax.update_group(
            EnterpriseFaxGroupUpdateRequest(sname="ops", sname_new="support", name_new="Support")
        )
        is None
    )
    assert await qb.enterprise_fax.delete_group("support") is None
    assert isinstance(await qb.enterprise_fax.list_users(), EnterpriseFaxUserListResponse)
    assert await qb.enterprise_fax.create_user(user_request()) is None
    assert (
        await qb.enterprise_fax.update_user(
            EnterpriseFaxUserUpdateRequest(fax_login="fax-user", fax_name="New")
        )
        is None
    )
    assert await qb.enterprise_fax.delete_user("fax-user") is None
    assert isinstance(
        await qb.enterprise_fax.list_permissions(), EnterpriseFaxPermissionListResponse
    )
    assert await qb.enterprise_fax.set_permission(permission_request()) is None
    assert (
        await qb.enterprise_fax.delete_permission(
            EnterpriseFaxPermissionDeleteRequest(fax_login="fax-user", did=15551234567)
        )
        is None
    )
    uploaded = await qb.enterprise_fax.upload(
        EnterpriseFaxUploadRequest.from_file(BytesIO(b"fax"), "fax.txt")
    )
    assert isinstance(uploaded, EnterpriseFaxUploadResponse)
    assert isinstance(
        await qb.enterprise_fax.send(
            EnterpriseFaxSendRequest(
                did_from=15551234567, did_to=15557654321, file_id=[uploaded.file_id]
            )
        ),
        EnterpriseFaxSendResponse,
    )
    assert (
        await qb.enterprise_fax.pause(
            EnterpriseFaxPauseRequest(did=15551234567, action=PauseAction.UNPAUSE)
        )
        is None
    )
    await http.aclose()


@pytest.mark.parametrize(
    "factory",
    [
        lambda: EnterpriseFaxListRequest(did="*12"),
        lambda: EnterpriseFaxOrderRequest(did=5551234),
        lambda: EnterpriseFaxOrderRequest(did=15551234567, post2url="bad"),
        lambda: EnterpriseFaxOrderRequest(did=15551234567, ata_mac_address="bad"),
        lambda: EnterpriseFaxUpdateRequest(did=15551234567),
        lambda: EnterpriseFaxEmailPermissionRequest(did=15551234567, email="bad"),
        lambda: EnterpriseFaxGroupCreateRequest(sname="x" * 25, name="Group"),
        lambda: EnterpriseFaxGroupUpdateRequest(sname="ops", sname_new="x" * 25, name_new="Group"),
        lambda: EnterpriseFaxUserCreateRequest(
            fax_login="x" * 37, fax_password="p", sname="ops", fax_name="Fax"
        ),
        lambda: EnterpriseFaxUserCreateRequest(
            fax_login="user", fax_password="p", sname="ops", fax_name="Fax", fax_email="bad"
        ),
        lambda: EnterpriseFaxUserUpdateRequest(fax_login="user"),
        lambda: EnterpriseFaxPermissionRequest(
            fax_login="user",
            did=5551234,
            allow_send=FaxToggle.ON,
            allow_delete=FaxToggle.OFF,
            allow_list_in=FaxToggle.ON,
            allow_list_out=FaxToggle.ON,
        ),
        lambda: EnterpriseFaxUploadRequest(file="bad-base64", filename="fax.pdf"),
        lambda: EnterpriseFaxUploadRequest.from_bytes(b"", "fax.pdf"),
        lambda: EnterpriseFaxUploadRequest.from_bytes(b"fax", "fax.exe"),
        lambda: EnterpriseFaxUploadRequest.from_bytes(b"x" * (MAX_FAX_FILE_SIZE + 1), "fax.pdf"),
        lambda: EnterpriseFaxSendRequest(did_from=15551234567, did_to=15557654321, file_id=[]),
        lambda: EnterpriseFaxSendRequest(did_from=15551234567, did_to=15557654321, file_id=[""]),
    ],
)
def test_enterprise_fax_validation(factory: Any) -> None:
    with pytest.raises((ValidationError, ValueError)):
        factory()


def test_enterprise_fax_inventory_next_page() -> None:
    assert EnterpriseFaxInventoryResponse(current_page=1, total_pages=2).next_page() == 2
    assert EnterpriseFaxInventoryResponse(current_page=2, total_pages=2).next_page() is None


def test_path_helpers_multiple_files_examples_and_sensitive_values(tmp_path: Path) -> None:
    first = tmp_path / "first.pdf"
    first.write_bytes(b"first")
    second = tmp_path / "second.txt"
    second.write_bytes(b"second")
    request = EnterpriseFaxUploadRequest.from_path(first)
    assert base64.b64decode(request.file) == b"first"
    assert base64.b64encode(b"first").decode("ascii") not in repr(request)
    assert "private-password" not in repr(user_request())
    qb = client()
    with pytest.raises(ValueError, match="confirm_billable_provisioning"):
        provision_account(
            qb,
            15551234567,
            group_short_name="ops",
            group_name="Operations",
            login="fax-user",
            password="private",
            first_name="Fax",
        )
    provision_account(
        qb,
        15551234567,
        group_short_name="ops",
        group_name="Operations",
        login="fax-user",
        password="private",
        first_name="Fax",
        confirm_billable_provisioning=True,
    )
    with pytest.raises(ValueError, match="confirm_destination"):
        upload_and_send(qb, [first, second], 15551234567, 15557654321)
    assert (
        upload_and_send(
            qb, [first, second], 15551234567, 15557654321, confirm_destination=True
        ).fax_id
        == 9001
    )


@pytest.mark.parametrize("status", ["active", "paused", "pending", "provider-added"])
def test_enterprise_fax_status_is_forward_compatible(status: str) -> None:
    assert FaxDIDStatus(status).value == status


def test_warnings_errors_malformed_empty_and_retry_safety() -> None:
    warning = client(lambda _: httpx.Response(202, json={"warning": ["pending"]}))
    assert isinstance(warning.enterprise_fax.list(), WarningResponse)
    assert isinstance(
        warning.enterprise_fax.create(EnterpriseFaxOrderRequest(did=15551234567)), WarningResponse
    )
    error = client(lambda _: httpx.Response(206, json={"error": "enterprise fax rejected"}))
    with pytest.raises(QuestBlueAPIError, match="enterprise fax rejected"):
        error.enterprise_fax.upload(EnterpriseFaxUploadRequest.from_bytes(b"fax", "fax.pdf"))
    malformed = client(lambda _: httpx.Response(200, json={"unexpected": True}))
    with pytest.raises(QuestBlueResponseError, match="empty iFax Enterprise response"):
        malformed.enterprise_fax.delete(15551234567)
    attempts = 0

    def uncertain(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503)

    unsafe = client(uncertain, max_retries=10)
    with pytest.raises(QuestBlueServerError):
        unsafe.enterprise_fax.send(
            EnterpriseFaxSendRequest(did_from=15551234567, did_to=15557654321, file_id=["file-1"])
        )
    assert attempts == 1
