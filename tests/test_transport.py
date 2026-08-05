from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from typing import List

import httpx
import pytest

from questblue import (
    AsyncQuestBlue,
    QuestBlue,
    QuestBlueAPIError,
    QuestBlueAuthenticationError,
    QuestBlueConfigurationError,
    QuestBlueConnectionError,
    QuestBlueRateLimitError,
    QuestBlueResponseError,
    QuestBlueServerError,
    QuestBlueTimeoutError,
    TransportEvent,
)


def _client(handler: httpx.MockTransport) -> QuestBlue:
    http = httpx.Client(base_url="https://example.test", transport=handler)
    return QuestBlue("user", "password", "security-secret", http_client=http)


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_mutations_are_never_retried(method: str) -> None:
    attempts = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503, json={"error": "busy"})

    client = _client(httpx.MockTransport(handler))

    with pytest.raises(QuestBlueServerError):
        client.request(method, "/billable", max_retries=20)

    assert attempts == 1


def test_mutation_connection_failure_is_never_retried() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ConnectError("uncertain outcome", request=request)

    client = _client(httpx.MockTransport(handler))

    with pytest.raises(QuestBlueConnectionError):
        client.request("POST", "/billable", max_retries=20)

    assert attempts == 1


def test_request_overrides_headers_timeout_retries_and_returns_raw_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        assert request.headers["x-correlation-id"] == "trace-1"
        assert request.extensions["timeout"]["read"] == 3.5
        if attempts == 1:
            return httpx.Response(429, headers={"retry-after": "0"})
        return httpx.Response(200, json={"ok": True}, headers={"x-request-id": "request-1"})

    monkeypatch.setattr("questblue._client.time.sleep", lambda _: None)
    client = _client(httpx.MockTransport(handler))

    response = client.request(
        "GET",
        "/status",
        headers={"X-Correlation-ID": "trace-1"},
        timeout=3.5,
        max_retries=1,
        raw_response=True,
    )

    assert isinstance(response, httpx.Response)
    assert response.json() == {"ok": True}
    assert attempts == 2


@pytest.mark.parametrize("header", ["Authorization", "Security-Key", "security-key"])
def test_authentication_headers_cannot_be_overridden(header: str) -> None:
    client = _client(httpx.MockTransport(lambda _: httpx.Response(200)))

    with pytest.raises(QuestBlueConfigurationError, match="managed by the client"):
        client.request("GET", "/status", headers={header: "attacker"})


def test_request_retry_override_can_disable_client_retries() -> None:
    attempts = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503)

    http = httpx.Client(base_url="https://example.test", transport=httpx.MockTransport(handler))
    client = QuestBlue("user", "password", "key", max_retries=4, http_client=http)

    with pytest.raises(QuestBlueServerError):
        client.request("GET", "/status", max_retries=0)

    assert attempts == 1


def test_timeout_has_a_specific_error_and_preserves_cause() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("content that must not be logged", request=request)

    client = _client(httpx.MockTransport(handler))

    with pytest.raises(QuestBlueTimeoutError) as caught:
        client.request("GET", "/status", max_retries=0)

    assert isinstance(caught.value.__cause__, httpx.ReadTimeout)


def test_connection_failure_has_a_specific_error_and_preserves_cause() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("content that must not be logged", request=request)

    client = _client(httpx.MockTransport(handler))

    with pytest.raises(QuestBlueConnectionError) as caught:
        client.request("GET", "/status", max_retries=0)

    assert type(caught.value) is QuestBlueConnectionError
    assert isinstance(caught.value.__cause__, httpx.ConnectError)


def test_malformed_declared_json_has_a_specific_error() -> None:
    client = _client(
        httpx.MockTransport(
            lambda _: httpx.Response(
                200, text="{broken", headers={"content-type": "application/json"}
            )
        )
    )

    with pytest.raises(QuestBlueResponseError, match="malformed JSON"):
        client.request("GET", "/status")


def test_empty_success_response_decodes_to_none() -> None:
    client = _client(httpx.MockTransport(lambda _: httpx.Response(204)))

    assert client.request("GET", "/status") is None


def test_binary_success_response_decodes_to_bytes() -> None:
    client = _client(
        httpx.MockTransport(
            lambda _: httpx.Response(
                200, content=b"%PDF-data", headers={"content-type": "application/pdf"}
            )
        )
    )

    assert client.request("GET", "/faxdownload") == b"%PDF-data"


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (400, QuestBlueAPIError),
        (401, QuestBlueAuthenticationError),
        (403, QuestBlueAuthenticationError),
        (429, QuestBlueRateLimitError),
        (500, QuestBlueServerError),
    ],
)
def test_http_error_classes(status: int, expected: type[QuestBlueAPIError]) -> None:
    client = _client(httpx.MockTransport(lambda _: httpx.Response(status, json={"error": "no"})))

    with pytest.raises(expected):
        client.request("GET", "/status", max_retries=0)


def test_retry_after_is_honored(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: List[float] = []
    attempts = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503, headers={"retry-after": "1.25"})
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr("questblue._client.time.sleep", sleeps.append)
    client = _client(httpx.MockTransport(handler))

    assert client.request("GET", "/status", max_retries=1) == {"ok": True}
    assert sleeps == [1.25]


def test_http_date_retry_after_is_honored(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: List[float] = []
    attempts = 0
    past = format_datetime(datetime.now(timezone.utc) - timedelta(seconds=1), usegmt=True)

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503, headers={"retry-after": past})
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr("questblue._client.time.sleep", sleeps.append)
    client = _client(httpx.MockTransport(handler))

    assert client.request("GET", "/status", max_retries=1) == {"ok": True}
    assert sleeps == [0.0]


def test_transport_events_never_expose_credentials_query_values_or_content(
    caplog: pytest.LogCaptureFixture,
) -> None:
    events: List[TransportEvent] = []
    client = QuestBlue(
        "user",
        "password-secret",
        "security-secret",
        http_client=httpx.Client(
            base_url="https://example.test",
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"ok": True})),
        ),
        transport_hook=events.append,
    )

    with caplog.at_level("DEBUG", logger="questblue.transport"):
        client.request(
            "POST",
            "/smsv2?msg=query-secret",
            params={"msg": "message-secret"},
            json={"file": "fax-secret"},
            headers={"X-Customer-Note": "header-secret"},
        )

    serialized = repr([event.as_dict() for event in events]) + caplog.text
    assert [event.name for event in events] == ["request", "response"]
    assert events[0].path == "/smsv2"
    for secret in (
        "password-secret",
        "security-secret",
        "query-secret",
        "message-secret",
        "fax-secret",
        "header-secret",
    ):
        assert secret not in serialized
    assert events[0].headers["X-Customer-Note"] == "[REDACTED]"


async def test_async_request_overrides_and_raw_response() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-correlation-id"] == "async-1"
        assert request.extensions["timeout"]["read"] == 2.0
        return httpx.Response(200, json={"ok": True})

    http = httpx.AsyncClient(
        base_url="https://example.test", transport=httpx.MockTransport(handler)
    )
    client = AsyncQuestBlue("user", "password", "key", http_client=http)

    response = await client.request(
        "GET",
        "/status",
        headers={"X-Correlation-ID": "async-1"},
        timeout=2.0,
        raw_response=True,
    )

    assert isinstance(response, httpx.Response)
    assert response.json() == {"ok": True}
    await http.aclose()


async def test_async_mutation_is_never_retried() -> None:
    attempts = 0

    async def handler(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503, json={"error": "busy"})

    http = httpx.AsyncClient(
        base_url="https://example.test", transport=httpx.MockTransport(handler)
    )
    client = AsyncQuestBlue("user", "password", "key", http_client=http)

    with pytest.raises(QuestBlueServerError):
        await client.request("POST", "/billable", max_retries=20)

    assert attempts == 1
    await http.aclose()


async def test_async_safe_read_retries_and_honors_retry_after(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = 0
    sleeps: List[float] = []

    async def handler(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503, headers={"retry-after": "0.25"})
        return httpx.Response(200, json={"ok": True})

    async def record_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr("questblue._client.asyncio.sleep", record_sleep)
    http = httpx.AsyncClient(
        base_url="https://example.test", transport=httpx.MockTransport(handler)
    )
    client = AsyncQuestBlue("user", "password", "key", http_client=http)

    assert await client.request("GET", "/status", max_retries=1) == {"ok": True}
    assert attempts == 2
    assert sleeps == [0.25]
    await http.aclose()


async def test_async_cancellation_propagates_unchanged() -> None:
    events: List[TransportEvent] = []

    async def handler(_: httpx.Request) -> httpx.Response:
        raise asyncio.CancelledError

    http = httpx.AsyncClient(
        base_url="https://example.test", transport=httpx.MockTransport(handler)
    )
    client = AsyncQuestBlue(
        "user", "password", "key", http_client=http, transport_hook=events.append
    )

    with pytest.raises(asyncio.CancelledError):
        await client.request("GET", "/status")

    assert [event.name for event in events] == ["request", "cancelled"]
    await http.aclose()


async def test_async_timeout_has_specific_error() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout", request=request)

    http = httpx.AsyncClient(
        base_url="https://example.test", transport=httpx.MockTransport(handler)
    )
    client = AsyncQuestBlue("user", "password", "key", max_retries=0, http_client=http)

    with pytest.raises(QuestBlueTimeoutError):
        await client.request("GET", "/status")

    await http.aclose()
