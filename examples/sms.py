"""Consent-aware SMS/MMS sending and delivery-status examples."""

from typing import List, Optional

from questblue import (
    MessageDeliveryStatusRequest,
    MessageDeliveryStatusResponse,
    QuestBlue,
    SendMessageRequest,
    WarningResponse,
)


def send_opted_in_message(
    client: QuestBlue,
    sender: int,
    destination: int,
    message: str,
    *,
    media_urls: Optional[List[str]] = None,
    confirm_recipient_opt_in: bool = False,
) -> str:
    if not confirm_recipient_opt_in:
        raise ValueError("set confirm_recipient_opt_in=True only after recording consent")
    result = client.sms.send(
        SendMessageRequest(
            did=sender,
            did_to=destination,
            msg=message,
            file_url=media_urls,
        )
    )
    if isinstance(result, WarningResponse):
        raise RuntimeError("QuestBlue warning: " + "; ".join(result.warning))
    if not result.data:
        raise RuntimeError("QuestBlue returned no message ID")
    return result.data[0].msg_id


def delivery_status(client: QuestBlue, message_id: int) -> MessageDeliveryStatusResponse:
    result = client.sms.delivery_status(MessageDeliveryStatusRequest(msg_id=message_id))
    if isinstance(result, WarningResponse):
        raise RuntimeError("QuestBlue warning: " + "; ".join(result.warning))
    return result
