from __future__ import annotations

import json
from decimal import Decimal

import httpx
import pytest

from questblue import (
    AsyncQuestBlue,
    CallHistoryRequest,
    EnterpriseFaxUploadRequest,
    EnterpriseFaxUploadResponse,
    QuestBlue,
    QuestBlueAPIError,
    QuestBlueAuthenticationError,
    QuestBlueConfigurationError,
    QuestBlueRateLimitError,
    SendMessageRequest,
    SendMessageResponse,
)
from questblue._client import redact_headers


def test_client_sends_both_authentication_layers_and_decodes_json() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["security-key"] == "key"
        assert request.headers["authorization"].startswith("Basic ")
        assert request.url.path == "/account/getbalance"
        return httpx.Response(200, json={"data": {"balance": "12.50", "allowed_credit": "5.00"}})

    http = httpx.Client(
        base_url="https://api.questblue.test",
        transport=httpx.MockTransport(handler),
    )
    client = QuestBlue("user", "password", "key", http_client=http)

    balance = client.account.balance()
    assert balance.data.balance == Decimal("12.50")  # type: ignore[union-attr]


def test_resource_encodes_lists_boole_and_omits_none() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/callhistory"
        assert request.url.params["trunk"] == "primary,backup"
        assert request.url.params["summary_only"] == "on"
        return httpx.Response(200, json={"data": []})

    http = httpx.Client(base_url="https://example.test", transport=httpx.MockTransport(handler))
    client = QuestBlue("user", "password", "key", http_client=http)

    client.reports.call_history(CallHistoryRequest(trunk=["primary", "backup"], summary_only="on"))


def test_sms_convenience_method_uses_documented_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/smsv2"
        assert dict(request.url.params) == {
            "did": "15551234567",
            "did_to": "15557654321",
            "msg": "hello",
            "file_url": "https://example.test/a.png,https://example.test/b.png",
        }
        return httpx.Response(200, json={"data": [{"msg_id": "abc"}]})

    http = httpx.Client(base_url="https://example.test", transport=httpx.MockTransport(handler))
    client = QuestBlue("user", "password", "key", http_client=http)

    result = client.sms.send(
        SendMessageRequest(
            did=15551234567,
            did_to=15557654321,
            msg="hello",
            file_url=["https://example.test/a.png", "https://example.test/b.png"],
        )
    )
    assert isinstance(result, SendMessageResponse)
    assert result.data[0].msg_id == "abc"


def test_enterprise_fax_upload_is_json_with_base64_data() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/fax2/upload"
        assert request.headers["content-type"] == "application/json"
        assert json.loads(request.content) == {"file": "aGVsbG8=", "filename": "hello.txt"}
        return httpx.Response(200, json={"file_id": "file-1"})

    http = httpx.Client(base_url="https://example.test", transport=httpx.MockTransport(handler))
    client = QuestBlue("user", "password", "key", http_client=http)

    result = client.enterprise_fax.upload(
        EnterpriseFaxUploadRequest.from_bytes(b"hello", "hello.txt")
    )
    assert isinstance(result, EnterpriseFaxUploadResponse)
    assert result.file_id == "file-1"


@pytest.mark.parametrize(
    ("status_code", "error_type"),
    [(401, QuestBlueAuthenticationError), (429, QuestBlueRateLimitError), (206, QuestBlueAPIError)],
)
def test_api_errors_include_questblue_message(
    status_code: int, error_type: type[Exception]
) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json={"error": "not today"})

    http = httpx.Client(base_url="https://example.test", transport=httpx.MockTransport(handler))
    client = QuestBlue("user", "password", "key", max_retries=0, http_client=http)

    with pytest.raises(error_type, match="not today"):
        client.dids.list()


def test_retry_recovers_from_server_error(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503, json={"error": "busy"}, headers={"retry-after": "0"})
        return httpx.Response(200, json={"data": [], "total": 0})

    monkeypatch.setattr("questblue._client.time.sleep", lambda _: None)
    http = httpx.Client(base_url="https://example.test", transport=httpx.MockTransport(handler))
    client = QuestBlue("user", "password", "key", max_retries=1, http_client=http)

    assert client.dids.states().total == 0  # type: ignore[union-attr]
    assert attempts == 2


def test_credentials_can_come_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QUESTBLUE_USERNAME", "user")
    monkeypatch.setenv("QUESTBLUE_PASSWORD", "password")
    monkeypatch.setenv("QUESTBLUE_SECURITY_KEY", "key")
    http = httpx.Client(
        base_url="https://example.test",
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"data": []})),
    )
    client = QuestBlue(http_client=http)
    assert client.account.details().data == []  # type: ignore[union-attr]


def test_missing_credentials_are_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("QUESTBLUE_USERNAME", "QUESTBLUE_PASSWORD", "QUESTBLUE_SECURITY_KEY"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(QuestBlueConfigurationError):
        QuestBlue()


def test_sensitive_headers_are_redacted() -> None:
    assert redact_headers(
        {"Authorization": "Basic secret", "Security-Key": "secret", "Accept": "application/json"}
    ) == {
        "Authorization": "[REDACTED]",
        "Security-Key": "[REDACTED]",
        "Accept": "application/json",
    }


async def test_async_client() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/did/available"
        return httpx.Response(200, json={"data": ["15551234567"], "total": 1})

    http = httpx.AsyncClient(
        base_url="https://example.test", transport=httpx.MockTransport(handler)
    )
    client = AsyncQuestBlue("user", "password", "key", http_client=http)

    from questblue import DIDAvailabilityRequest, DIDType

    result = await client.dids.available(DIDAvailabilityRequest(did_type=DIDType.LOCAL, zip=27513))
    assert result.data == ["15551234567"]  # type: ignore[union-attr]
    await http.aclose()
