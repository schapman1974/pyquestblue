from __future__ import annotations

from datetime import date
from typing import Any, Dict, List

import httpx
import pytest
from pydantic import ValidationError

from examples.sms import delivery_status, send_opted_in_message
from questblue import (
    AsyncQuestBlue,
    CarrierLookupRequest,
    CarrierLookupResponse,
    MessageDeliveryStatus,
    MessageDeliveryStatusRequest,
    MessageDeliveryStatusResponse,
    OffnetAction,
    OffnetOrderRequest,
    OffnetStatus,
    OffnetStatusRequest,
    OffnetStatusResponse,
    QuestBlue,
    QuestBlueAPIError,
    QuestBlueResponseError,
    QuestBlueServerError,
    SendMessageRequest,
    SendMessageResponse,
    SMSDirection,
    SMSHistoryPeriod,
    SMSHistoryRequest,
    SMSHistoryResponse,
    SMSInventoryRequest,
    SMSInventoryResponse,
    SMSMessageType,
    SMSMode,
    SMSPostMethod,
    SMSSettingsUpdateRequest,
    SMSSettingsUpdateResponse,
    SMSSortOrder,
    WarningResponse,
)


def response(request: httpx.Request) -> httpx.Response:
    payloads: Dict[str, Any] = {
        "/sms": {
            "data": [
                {
                    "did": "15551234567",
                    "email2forward": "ops@example.test",
                    "sms_enabled": "on",
                    "sms_mode": "Email and XMPP",
                }
            ],
            "current_page": 1,
            "total": 1,
            "total_pages": 1,
        },
        "/sms/history": {
            "data": [
                {
                    "id": "42",
                    "time": "2026-08-05T12:00:00Z",
                    "from": "15551234567",
                    "to": "15557654321",
                    "direction": "out",
                    "msg_type": "mms",
                    "status": "delivered",
                }
            ],
            "current_page": 1,
            "total": 1,
            "total_pages": 1,
        },
        "/sms/deliverystatus": {"data": {"status": "delivered"}},
        "/sms/offnetstatus": {"data": {"status": "processing"}},
        "/smschecktncarrier": {
            "data": [{"carrier": "Example Wireless", "isWireless": "yes", "tn": 15557654321}],
            "total": 1,
        },
    }
    if request.url.path == "/smsv2" and request.method == "POST":
        return httpx.Response(200, json={"data": [{"msg_id": "9001"}]})
    if request.url.path == "/smsv2" and request.method == "PUT":
        return httpx.Response(200, json={"message": "updated", "success": True})
    if request.url.path == "/sms/offnetorder":
        return httpx.Response(200, json={})
    return httpx.Response(200, json=payloads[request.url.path])


def client(handler: Any = response, max_retries: int = 2) -> QuestBlue:
    return QuestBlue(
        "u",
        "p",
        "k",
        max_retries=max_retries,
        http_client=httpx.Client(base_url="https://test", transport=httpx.MockTransport(handler)),
    )


def test_all_sync_sms_operations_and_parameters() -> None:
    seen: List[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return response(request)

    qb = client(handler)
    assert isinstance(
        qb.sms.list(SMSInventoryRequest(did="*4567", per_page=50)), SMSInventoryResponse
    )
    assert isinstance(
        qb.sms.send(
            SendMessageRequest(
                did=15551234567,
                did_to=15557654321,
                msg="consented message",
                file_url=["https://cdn.example.test/one.jpg", "https://cdn.example.test/two.jpg"],
            )
        ),
        SendMessageResponse,
    )
    assert isinstance(
        qb.sms.update(
            SMSSettingsUpdateRequest(
                did=15551234567,
                sms_mode=SMSMode.BOTH,
                forward2email="ops@example.test",
                xmpp_name="ops",
                xmpp_passwd="secret",
                post2urlmethod=SMSPostMethod.JSON,
            )
        ),
        SMSSettingsUpdateResponse,
    )
    assert qb.sms.offnet_order(OffnetOrderRequest(did=15551234567, action=OffnetAction.ADD)) is None
    assert isinstance(
        qb.sms.offnet_status(OffnetStatusRequest(did=15551234567)), OffnetStatusResponse
    )
    assert isinstance(
        qb.sms.history(
            SMSHistoryRequest(
                period=(date(2026, 8, 1), date(2026, 8, 5)),
                direction=SMSDirection.OUTBOUND,
                order=SMSSortOrder.DESCENDING,
                msg_type=SMSMessageType.MMS,
                per_page=100,
                page=2,
            )
        ),
        SMSHistoryResponse,
    )
    assert isinstance(
        qb.sms.delivery_status(MessageDeliveryStatusRequest(msg_id=9001)),
        MessageDeliveryStatusResponse,
    )
    assert isinstance(
        qb.sms.carrier(CarrierLookupRequest(tn=[15551234567, 15557654321])),
        CarrierLookupResponse,
    )

    queries = {(item.method, item.url.path): dict(item.url.params) for item in seen}
    assert queries[("POST", "/smsv2")]["file_url"] == (
        "https://cdn.example.test/one.jpg,https://cdn.example.test/two.jpg"
    )
    assert queries[("PUT", "/smsv2")]["post2urlmethod"] == "json"
    assert queries[("GET", "/sms/history")]["period"] == "2026-08-01,2026-08-05"
    assert queries[("GET", "/sms/history")]["page"] == "2"
    assert queries[("GET", "/smschecktncarrier")]["tn"] == "15551234567,15557654321"


async def test_all_async_sms_operations_have_parity() -> None:
    http = httpx.AsyncClient(base_url="https://test", transport=httpx.MockTransport(response))
    qb = AsyncQuestBlue("u", "p", "k", http_client=http)
    assert isinstance(await qb.sms.list(), SMSInventoryResponse)
    assert isinstance(
        await qb.sms.send(SendMessageRequest(did=15551234567, did_to=15557654321, msg="hello")),
        SendMessageResponse,
    )
    assert isinstance(
        await qb.sms.update(SMSSettingsUpdateRequest(did=15551234567, sms_mode=SMSMode.NONE)),
        SMSSettingsUpdateResponse,
    )
    assert (
        await qb.sms.offnet_order(OffnetOrderRequest(did=15551234567, action=OffnetAction.REMOVE))
        is None
    )
    assert isinstance(
        await qb.sms.offnet_status(OffnetStatusRequest(did=15551234567)), OffnetStatusResponse
    )
    assert isinstance(await qb.sms.history(), SMSHistoryResponse)
    assert isinstance(
        await qb.sms.delivery_status(MessageDeliveryStatusRequest(msg_id=9001)),
        MessageDeliveryStatusResponse,
    )
    assert isinstance(
        await qb.sms.carrier(CarrierLookupRequest(tn=15551234567)), CarrierLookupResponse
    )
    await http.aclose()


@pytest.mark.parametrize(
    "factory",
    [
        lambda: SMSInventoryRequest(did="*12"),
        lambda: SMSInventoryRequest(per_page=4),
        lambda: SendMessageRequest(did=5551234, did_to=15557654321, msg="hello"),
        lambda: SendMessageRequest(did=15551234567, did_to=15557654321, msg=""),
        lambda: SendMessageRequest(
            did=15551234567, did_to=15557654321, msg="hello", file_url=["/private.jpg"]
        ),
        lambda: SendMessageRequest(
            did=15551234567,
            did_to=15557654321,
            msg="hello",
            file_url=["http://127.0.0.1/private.jpg"],
        ),
        lambda: SendMessageRequest(
            did=15551234567,
            did_to=15557654321,
            msg="hello",
            file_url=["http://localhost/private.jpg"],
        ),
        lambda: SMSSettingsUpdateRequest(did=15551234567, sms_mode=SMSMode.EMAIL),
        lambda: SMSSettingsUpdateRequest(did=15551234567, sms_mode=SMSMode.XMPP),
        lambda: SMSSettingsUpdateRequest(did=15551234567, sms_mode=SMSMode.URL),
        lambda: SMSSettingsUpdateRequest(did=15551234567, sms_mode=SMSMode.CHAT),
        lambda: SMSSettingsUpdateRequest(did=15551234567, sms_mode=SMSMode.YEASTAR),
        lambda: SMSSettingsUpdateRequest(
            did=15551234567, sms_mode=SMSMode.EMAIL, forward2email="bad-email"
        ),
        lambda: CarrierLookupRequest(tn=[]),
        lambda: MessageDeliveryStatusRequest(msg_id=0),
        lambda: SMSHistoryRequest(period=(date(2026, 8, 5), date(2026, 8, 1))),
        lambda: SMSHistoryRequest(per_page=501),
    ],
)
def test_sms_validation(factory: Any) -> None:
    with pytest.raises((ValidationError, ValueError)):
        factory()


def test_sensitive_diagnostics_redact_messages_destinations_and_credentials() -> None:
    request = SendMessageRequest(
        did=15551234567,
        did_to=15557654321,
        msg="private body",
        file_url=["https://cdn.example.test/private.jpg"],
    )
    diagnostic = repr(request)
    assert "private body" not in diagnostic
    assert "15557654321" not in diagnostic
    assert "private.jpg" not in diagnostic
    with pytest.raises(ValidationError) as invalid:
        SendMessageRequest(did=15551234567, did_to=7654321, msg="private body")
    assert "7654321" not in str(invalid.value)
    assert "private body" not in str(invalid.value)
    settings = SMSSettingsUpdateRequest(
        did=15551234567,
        sms_mode=SMSMode.XMPP,
        xmpp_name="private-user",
        xmpp_passwd="private-password",
    )
    assert "private-user" not in repr(settings)
    assert "private-password" not in repr(settings)
    history = client().sms.history()
    assert isinstance(history, SMSHistoryResponse)
    assert "15557654321" not in repr(history)


@pytest.mark.parametrize("value", ["sent", "delivered", "failed", "provider-added"])
def test_delivery_statuses_are_forward_compatible(value: str) -> None:
    assert MessageDeliveryStatus(value).value == value


@pytest.mark.parametrize(
    "value",
    ["unavailable", "disabled", "received", "processing", "failed", "enabled", "future"],
)
def test_offnet_statuses_are_forward_compatible(value: str) -> None:
    assert OffnetStatus(value).value == value


def test_history_preserves_provider_response_variants() -> None:
    history = SMSHistoryResponse.model_validate(
        {
            "data": [
                {
                    "id": "43",
                    "time": "2026-08-05T12:00:00Z",
                    "from": "15551234567",
                    "to": "15557654321",
                    "direction": "inbound",
                    "msg_type": "provider-added-type",
                    "status": "provider-added-status",
                }
            ],
            "current_page": 1,
            "total": 1,
            "total_pages": 1,
        }
    )
    assert history.data[0].direction.value == "inbound"
    assert history.data[0].msg_type.value == "provider-added-type"
    assert history.data[0].status.value == "provider-added-status"


def test_pagination_contract_shapes_and_examples() -> None:
    qb = client()
    inventory = qb.sms.list()
    history = qb.sms.history()
    assert isinstance(inventory, SMSInventoryResponse) and inventory.next_page() is None
    assert isinstance(history, SMSHistoryResponse) and history.next_page() is None
    assert SMSInventoryResponse(current_page=1, total_pages=2).next_page() == 2
    assert SMSHistoryResponse(data=[], current_page=1, total=2, total_pages=2).next_page() == 2
    preset = SMSHistoryRequest(period=SMSHistoryPeriod.TODAY)
    assert preset.to_request_params()["period"] == "today"
    url_settings = SMSSettingsUpdateRequest(
        did=15551234567,
        sms_mode=SMSMode.URL,
        post2url="https://app.example.test/inbound",
    )
    assert url_settings.post2url == "https://app.example.test/inbound"
    public_ip_media = SendMessageRequest(
        did=15551234567,
        did_to=15557654321,
        msg="hello",
        file_url=["https://8.8.8.8/public.jpg"],
    )
    assert public_ip_media.file_url == ["https://8.8.8.8/public.jpg"]
    assert delivery_status(qb, 9001).data.status is MessageDeliveryStatus.DELIVERED
    with pytest.raises(ValueError, match="confirm_recipient_opt_in"):
        send_opted_in_message(qb, 15551234567, 15557654321, "hello")
    assert (
        send_opted_in_message(
            qb,
            15551234567,
            15557654321,
            "hello",
            confirm_recipient_opt_in=True,
        )
        == "9001"
    )


def test_warnings_errors_malformed_responses_and_mutation_retry_safety() -> None:
    warning = client(lambda _: httpx.Response(202, json={"warning": ["carrier pending"]}))
    assert isinstance(warning.sms.list(), WarningResponse)
    assert isinstance(
        warning.sms.offnet_order(OffnetOrderRequest(did=15551234567, action=OffnetAction.ADD)),
        WarningResponse,
    )
    error = client(lambda _: httpx.Response(206, json={"error": "message rejected"}))
    with pytest.raises(QuestBlueAPIError, match="message rejected"):
        error.sms.send(SendMessageRequest(did=15551234567, did_to=15557654321, msg="private body"))
    malformed = client(lambda _: httpx.Response(200, json={"unexpected": True}))
    with pytest.raises(QuestBlueResponseError, match="body for an empty SMS response"):
        malformed.sms.offnet_order(OffnetOrderRequest(did=15551234567, action=OffnetAction.ADD))
    attempts = 0

    def uncertain(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503)

    unsafe = client(uncertain, max_retries=10)
    with pytest.raises(QuestBlueServerError):
        unsafe.sms.update(SMSSettingsUpdateRequest(did=15551234567, sms_mode=SMSMode.NONE))
    assert attempts == 1
