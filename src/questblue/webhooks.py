"""Framework-neutral models and parsing for QuestBlue messaging webhooks."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional, Protocol, Union

from pydantic import Field

from .models import OpenStringEnum, QuestBlueModel


class WebhookKind(str, Enum):
    """Webhook shapes published in the QuestBlue 2.3.2 contract."""

    INBOUND_MESSAGE = "inbound_message"
    MESSAGE_STATUS = "message_status"
    UNKNOWN = "unknown"


class WebhookMessageType(OpenStringEnum):
    """Published inbound message types, open to future provider values."""

    SMS = "SMS"
    MMS = "MMS"


class WebhookEvent(QuestBlueModel):
    """Base callback model that preserves fields added by QuestBlue."""


class InboundMessageEvent(WebhookEvent):
    """An inbound SMS or MMS callback."""

    from_: str = Field(alias="from")
    to: list[str]
    type: WebhookMessageType
    text: Optional[str] = None
    media: list[str] = Field(default_factory=list)
    segments: Optional[str] = None


class MessageStatusEvent(WebhookEvent):
    """An outbound message delivery-status callback."""

    from_: str = Field(alias="from")
    to: str
    status: str
    reason: Optional[str] = None
    segments: Optional[str] = None


class UnknownWebhookEvent(WebhookEvent):
    """A forward-compatible callback whose shape is not yet published."""


WebhookEventType = Union[InboundMessageEvent, MessageStatusEvent, UnknownWebhookEvent]


class WebhookVerifier(Protocol):
    """Application-defined callback verifier.

    QuestBlue does not publish a callback signature scheme. Implementations can
    enforce a reverse-proxy secret, mTLS identity, IP policy, or another control
    owned by the receiving application. They must raise on verification failure.
    """

    def __call__(self, headers: Mapping[str, str], body: bytes) -> Optional[bool]:
        """Verify the exact request bytes or raise an exception."""


class WebhookVerificationRequired(ValueError):
    """Raised when a framework helper is used without an explicit verifier."""


@dataclass(frozen=True)
class WebhookEnvelope:
    """A parsed event plus content-free processing metadata."""

    kind: WebhookKind
    fingerprint: str
    verified: bool
    event: WebhookEventType = field(repr=False)


def _body_bytes(body: Union[bytes, str, Mapping[str, Any]]) -> bytes:
    if isinstance(body, bytes):
        return body
    if isinstance(body, str):
        return body.encode("utf-8")
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _payload(body: Union[bytes, str, Mapping[str, Any]]) -> Mapping[str, Any]:
    if isinstance(body, Mapping):
        return body
    try:
        value = json.loads(_body_bytes(body))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("QuestBlue webhook body must be valid JSON") from exc
    if not isinstance(value, Mapping):
        raise ValueError("QuestBlue webhook body must be a JSON object")
    return value


def _kind(payload: Mapping[str, Any], requested: Optional[WebhookKind]) -> WebhookKind:
    if requested is not None:
        return requested
    if "status" in payload and isinstance(payload.get("to"), str):
        return WebhookKind.MESSAGE_STATUS
    if "type" in payload and isinstance(payload.get("to"), list):
        return WebhookKind.INBOUND_MESSAGE
    return WebhookKind.UNKNOWN


def parse_webhook(
    body: Union[bytes, str, Mapping[str, Any]],
    *,
    headers: Optional[Mapping[str, str]] = None,
    verifier: Optional[WebhookVerifier] = None,
    kind: Optional[WebhookKind] = None,
) -> WebhookEnvelope:
    """Verify and parse a QuestBlue callback without discarding unknown fields.

    The returned ``verified`` flag is true only when the supplied verifier
    completes successfully. Parsing alone makes no authenticity claim.
    """

    raw = _body_bytes(body)
    verified = verifier is not None
    if verifier is not None:
        result = verifier(headers or {}, raw)
        if result is False:
            raise ValueError("QuestBlue webhook verification failed")
    payload = _payload(body)
    resolved_kind = _kind(payload, kind)
    model: type[WebhookEvent]
    if resolved_kind is WebhookKind.INBOUND_MESSAGE:
        model = InboundMessageEvent
    elif resolved_kind is WebhookKind.MESSAGE_STATUS:
        model = MessageStatusEvent
    else:
        model = UnknownWebhookEvent
    event = model.model_validate(payload)
    return WebhookEnvelope(
        kind=resolved_kind,
        fingerprint=hashlib.sha256(raw).hexdigest(),
        verified=verified,
        event=event,
    )
