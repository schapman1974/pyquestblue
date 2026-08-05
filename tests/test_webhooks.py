from __future__ import annotations

import hashlib
import json
from typing import ClassVar, Mapping

import pytest
from pydantic import ValidationError

from questblue import (
    InboundMessageEvent,
    MessageStatusEvent,
    UnknownWebhookEvent,
    WebhookKind,
    WebhookMessageType,
    WebhookVerificationRequired,
    parse_webhook,
)
from questblue.integrations.django import parse_django_request
from questblue.integrations.fastapi import parse_fastapi_request

INBOUND = {
    "from": "15551230000",
    "to": ["15559870000"],
    "type": "MMS",
    "text": "hello",
    "media": ["https://media.example.test/image.jpg"],
    "segments": "1",
    "future_delivery_id": "delivery-1",
}
STATUS = {
    "from": "15559870000",
    "to": "15551230000",
    "status": "delivered",
    "reason": "",
    "segments": "1",
    "future_carrier": "example",
}


def test_parses_inbound_callback_and_preserves_unknown_fields() -> None:
    envelope = parse_webhook(INBOUND)

    assert envelope.kind is WebhookKind.INBOUND_MESSAGE
    assert envelope.verified is False
    assert isinstance(envelope.event, InboundMessageEvent)
    assert envelope.event.from_ == "15551230000"
    assert envelope.event.type is WebhookMessageType.MMS
    assert envelope.event.extra_fields == {"future_delivery_id": "delivery-1"}
    assert "hello" not in repr(envelope)


def test_parses_status_bytes_and_fingerprints_exact_body() -> None:
    body = json.dumps(STATUS).encode()
    envelope = parse_webhook(body)

    assert envelope.kind is WebhookKind.MESSAGE_STATUS
    assert isinstance(envelope.event, MessageStatusEvent)
    assert envelope.event.extra_fields == {"future_carrier": "example"}
    assert envelope.fingerprint == hashlib.sha256(body).hexdigest()


def test_string_and_mapping_have_stable_representation_specific_fingerprints() -> None:
    text = json.dumps(INBOUND, sort_keys=True, separators=(",", ":"))

    assert parse_webhook(INBOUND).fingerprint == parse_webhook(text).fingerprint


def test_unknown_callback_is_forward_compatible() -> None:
    envelope = parse_webhook('{"new_event":"value","sequence":7}')

    assert envelope.kind is WebhookKind.UNKNOWN
    assert isinstance(envelope.event, UnknownWebhookEvent)
    assert envelope.event.extra_fields == {"new_event": "value", "sequence": 7}


def test_explicit_kind_handles_ambiguous_payload() -> None:
    envelope = parse_webhook(STATUS, kind=WebhookKind.UNKNOWN)

    assert isinstance(envelope.event, UnknownWebhookEvent)


@pytest.mark.parametrize("body", [b"{broken", b"\xff"])
def test_malformed_json_is_rejected(body: bytes) -> None:
    with pytest.raises(ValueError, match="valid JSON"):
        parse_webhook(body)


def test_non_object_json_is_rejected() -> None:
    with pytest.raises(ValueError, match="JSON object"):
        parse_webhook("[]")


def test_forced_known_shape_is_validated() -> None:
    with pytest.raises(ValidationError):
        parse_webhook({}, kind=WebhookKind.INBOUND_MESSAGE)


def test_verifier_receives_exact_body_before_parsing() -> None:
    seen: list[tuple[Mapping[str, str], bytes]] = []
    body = b"not-json"

    def verifier(headers: Mapping[str, str], raw: bytes) -> None:
        seen.append((headers, raw))
        raise PermissionError("untrusted")

    with pytest.raises(PermissionError, match="untrusted"):
        parse_webhook(body, headers={"X-Edge": "trusted"}, verifier=verifier)

    assert seen == [({"X-Edge": "trusted"}, body)]


def test_successful_verifier_marks_envelope_verified() -> None:
    def verifier(headers: Mapping[str, str], body: bytes) -> None:
        assert headers == {}
        assert body.startswith(b"{")

    assert parse_webhook(INBOUND, verifier=verifier).verified is True


def test_false_verifier_result_is_rejected() -> None:
    def verifier(_: Mapping[str, str], __: bytes) -> None:
        return False  # type: ignore[return-value]

    with pytest.raises(ValueError, match="verification failed"):
        parse_webhook(INBOUND, verifier=verifier)


class AsyncRequest:
    headers: ClassVar[Mapping[str, str]] = {"X-Edge": "trusted"}

    async def body(self) -> bytes:
        return json.dumps(INBOUND).encode()


@pytest.mark.asyncio
async def test_fastapi_adapter_requires_verification_by_default() -> None:
    with pytest.raises(WebhookVerificationRequired):
        await parse_fastapi_request(AsyncRequest())


@pytest.mark.asyncio
async def test_fastapi_adapter_parses_verified_request() -> None:
    def verifier(headers: Mapping[str, str], _: bytes) -> None:
        assert headers["X-Edge"] == "trusted"

    envelope = await parse_fastapi_request(AsyncRequest(), verifier=verifier)

    assert envelope.verified is True


@pytest.mark.asyncio
async def test_fastapi_adapter_allows_explicit_unverified_fixture() -> None:
    envelope = await parse_fastapi_request(AsyncRequest(), allow_unverified=True)

    assert envelope.verified is False


class DjangoRequest:
    body = json.dumps(STATUS).encode()
    headers: ClassVar[Mapping[str, str]] = {"X-Edge": "trusted"}


def test_django_adapter_requires_verification_by_default() -> None:
    with pytest.raises(WebhookVerificationRequired):
        parse_django_request(DjangoRequest())


def test_django_adapter_parses_verified_request() -> None:
    envelope = parse_django_request(DjangoRequest(), verifier=lambda headers, _: headers["X-Edge"])

    assert envelope.verified is True
    assert envelope.kind is WebhookKind.MESSAGE_STATUS


def test_django_adapter_supports_legacy_meta_headers_and_explicit_kind() -> None:
    class LegacyRequest:
        body = json.dumps({"future": "event"}).encode()
        META: ClassVar[Mapping[str, str]] = {
            "HTTP_X_EDGE": "trusted",
            "CONTENT_LENGTH": "10",
        }

    envelope = parse_django_request(
        LegacyRequest(),
        verifier=lambda headers, _: headers["X-EDGE"],
        kind=WebhookKind.UNKNOWN,
    )

    assert envelope.verified is True


def test_django_adapter_allows_explicit_unverified_fixture() -> None:
    envelope = parse_django_request(DjangoRequest(), allow_unverified=True)

    assert envelope.verified is False
