from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from questblue.enterprise_fax import EnterpriseFaxSendResponse, EnterpriseFaxUploadResponse
from questblue.fax import FaxSendResponse, SentFax
from questblue.reports import FaxDownloadData, FaxDownloadResponse
from questblue.simple import (
    ConfirmationRequiredError,
    DeliveryTimeoutError,
    MissingProviderIdentifierError,
)
from questblue.simple._read import (
    AsyncEnterpriseFaxReads,
    AsyncFaxReads,
    AsyncMessageReads,
    EnterpriseFaxReads,
    FaxReads,
    MessageReads,
)
from questblue.sms import (
    MessageDelivery,
    MessageDeliveryStatus,
    MessageDeliveryStatusResponse,
    SendMessageResponse,
    SentMessage,
    SMSSettingsUpdateResponse,
)


def document(tmp_path: Path) -> Path:
    path = tmp_path / "document.pdf"
    path.write_bytes(b"pdf")
    return path


def test_message_send_requires_consent_and_returns_id() -> None:
    raw = MagicMock()
    raw.send.return_value = SendMessageResponse(data=[SentMessage(msg_id="42")])
    service = MessageReads(raw)
    with pytest.raises(ConfirmationRequiredError):
        service.send(from_number="9195550100", to="9195550101", text="hello")
    result = service.send(
        from_number="+1 919 555 0100",
        to="919-555-0101",
        text="hello",
        media_urls=["https://example.com/image.png"],
        recipient_opted_in=True,
    )
    assert result.value == "42"
    request = raw.send.call_args.args[0]
    assert request.did == 19195550100 and request.did_to == 9195550101
    assert request.file_url == ["https://example.com/image.png"]
    raw.send.return_value = SendMessageResponse(data=[])
    with pytest.raises(MissingProviderIdentifierError):
        service.send(from_number="9195550100", to="9195550101", text="x", recipient_opted_in=True)
    raw.update.return_value = SMSSettingsUpdateResponse(message="ok", success=True)
    with pytest.raises(ConfirmationRequiredError):
        service.configure(number="9195550100", mode="email")
    assert (
        service.configure(
            number="9195550100",
            mode="email",
            forward_email="owner@example.com",
            confirm_routing_change=True,
        ).value
        is True
    )


def test_sync_delivery_wait_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = MagicMock()
    raw.delivery_status.side_effect = [
        MessageDeliveryStatusResponse(data=MessageDelivery(status="sent")),
        MessageDeliveryStatusResponse(data=MessageDelivery(status="delivered")),
    ]
    sleeps: list[float] = []
    monkeypatch.setattr("questblue.simple._read.time.sleep", sleeps.append)
    result = MessageReads(raw).wait_for_delivery(42, attempts=2, interval=0.25)
    assert result.status is MessageDeliveryStatus.DELIVERED
    assert sleeps == [0.25]
    raw.delivery_status.return_value = MessageDeliveryStatusResponse(
        data=MessageDelivery(status="sent")
    )
    raw.delivery_status.side_effect = None
    with pytest.raises(DeliveryTimeoutError):
        MessageReads(raw).wait_for_delivery(42, attempts=1, interval=0)
    with pytest.raises(ValueError):
        MessageReads(raw).wait_for_delivery(42, attempts=0)


def test_fax_sends_validate_before_io_and_require_destination(tmp_path: Path) -> None:
    raw = MagicMock()
    raw.send.return_value = FaxSendResponse(data=SentFax(fax_id=7))
    service = FaxReads(raw)
    with pytest.raises(ConfirmationRequiredError):
        service.send(from_number="9195550100", to="9195550101", file=document(tmp_path))
    result = service.send(
        from_number="9195550100",
        to="9195550101",
        file=document(tmp_path),
        destination_confirmed=True,
    )
    assert result.value == 7
    with pytest.raises(ValueError):
        service.send(
            from_number="9195550100",
            to="9195550101",
            file=tmp_path / "missing.pdf",
            destination_confirmed=True,
        )
    raw.set_email_permission.return_value = None
    raw.delete_email_permission.return_value = None
    with pytest.raises(ConfirmationRequiredError):
        service.set_email_access(number="9195550100", email="owner@example.com")
    service.set_email_access(
        number="9195550100",
        email="owner@example.com",
        allow_receive=True,
        confirm_routing_change=True,
    )
    service.set_email_access(
        number="9195550100",
        email="owner@example.com",
        remove=True,
        confirm_routing_change=True,
    )


def test_enterprise_fax_uploads_each_file_then_sends(tmp_path: Path) -> None:
    raw = MagicMock()
    raw.upload.side_effect = [
        EnterpriseFaxUploadResponse(file_id="a"),
        EnterpriseFaxUploadResponse(file_id="b"),
    ]
    raw.send.return_value = EnterpriseFaxSendResponse(fax_id=9)
    second = tmp_path / "second.pdf"
    second.write_bytes(b"pdf2")
    service = EnterpriseFaxReads(raw)
    with pytest.raises(ConfirmationRequiredError):
        service.send(from_number="9195550100", to="9195550101", files=[])
    with pytest.raises(ValueError):
        service.send(
            from_number="9195550100", to="9195550101", files=[], destination_confirmed=True
        )
    result = service.send(
        from_number="9195550100",
        to="9195550101",
        files=[document(tmp_path), second],
        destination_confirmed=True,
    )
    assert result.value == 9
    assert raw.send.call_args.args[0].file_id == ["a", "b"]


@pytest.mark.asyncio
async def test_async_communications_have_confirmation_and_polling_parity(tmp_path: Path) -> None:
    messages = MagicMock()
    messages.send = AsyncMock(return_value=SendMessageResponse(data=[SentMessage(msg_id="42")]))
    reads = AsyncMessageReads(messages)
    result = await reads.send(
        from_number="9195550100", to="9195550101", text="hi", recipient_opted_in=True
    )
    assert result.value == "42"
    messages.update = AsyncMock(return_value=SMSSettingsUpdateResponse(message="ok", success=True))
    assert (
        await reads.configure(
            number="9195550100",
            mode="email",
            forward_email="owner@example.com",
            confirm_routing_change=True,
        )
    ).value is True
    messages.delivery_status = AsyncMock(
        return_value=MessageDeliveryStatusResponse(data=MessageDelivery(status="delivered"))
    )
    assert (await reads.wait_for_delivery(42, attempts=1, interval=0)).status == "delivered"
    with pytest.raises(ValueError):
        await reads.wait_for_delivery(42, interval=-1)

    fax = MagicMock()
    fax.send = AsyncMock(return_value=FaxSendResponse(data=SentFax(fax_id=7)))
    assert (
        await AsyncFaxReads(fax).send(
            from_number="9195550100",
            to="9195550101",
            file=document(tmp_path),
            destination_confirmed=True,
        )
    ).value == 7
    fax.set_email_permission = AsyncMock(return_value=None)
    assert (
        await AsyncFaxReads(fax).set_email_access(
            number="9195550100", email="owner@example.com", confirm_routing_change=True
        )
    ).value is True

    enterprise = MagicMock()
    enterprise.upload = AsyncMock(return_value=EnterpriseFaxUploadResponse(file_id="a"))
    enterprise.send = AsyncMock(return_value=EnterpriseFaxSendResponse(fax_id=9))
    assert (
        await AsyncEnterpriseFaxReads(enterprise).send(
            from_number="9195550100",
            to="9195550101",
            files=[document(tmp_path)],
            destination_confirmed=True,
        )
    ).value == 9


@pytest.mark.asyncio
async def test_fax_download_returns_and_optionally_writes_bytes(tmp_path: Path) -> None:
    import base64

    from questblue.simple._read import AsyncReportReads, ReportReads

    response = FaxDownloadResponse(
        data=FaxDownloadData(fax_base64=base64.b64encode(b"fax").decode())
    )
    raw = MagicMock()
    raw.download_fax.return_value = response
    destination = tmp_path / "fax.pdf"
    assert ReportReads(raw).download_fax(7, destination) == b"fax"
    assert destination.read_bytes() == b"fax"

    async_raw = MagicMock()
    async_raw.download_fax = AsyncMock(return_value=response)
    async_destination = tmp_path / "async-fax.pdf"
    assert await AsyncReportReads(async_raw).download_fax(7, async_destination) == b"fax"
    assert async_destination.read_bytes() == b"fax"
