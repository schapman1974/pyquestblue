from __future__ import annotations

import json
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any

import httpx
import pytest

from questblue import AsyncQuestBlue, AsyncSimpleQuestBlue, QuestBlue, SimpleQuestBlue
from questblue.models import QuestBlueModel, WarningResponse
from questblue.simple import (
    ConfirmationRequiredError,
    OperationPlan,
    OperationResult,
    PlannedOperation,
    QuestBlueWarningError,
    Risk,
    WorkflowResult,
    WorkflowStatus,
    WorkflowStep,
    json_safe,
    normalize_date_range,
    normalize_enum,
    normalize_file,
    normalize_list,
    normalize_path,
    normalize_phone,
    unwrap_warning,
)


class Color(str, Enum):
    RED = "red"
    BLUE = "blue"


class ExampleModel(QuestBlueModel):
    created: date
    password: str


def raw_client() -> QuestBlue:
    return QuestBlue(
        "user",
        "password",
        "key",
        http_client=httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200))),
    )


def async_raw_client() -> AsyncQuestBlue:
    return AsyncQuestBlue(
        "user",
        "password",
        "key",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(200))),
    )


def test_sync_facade_wraps_raw_resources_without_ownership(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = raw_client()
    closed = False

    def close() -> None:
        nonlocal closed
        closed = True

    monkeypatch.setattr(raw, "close", close)
    with SimpleQuestBlue.wrap(raw) as simple:
        assert simple.raw is raw
        assert simple.account.raw is raw.account
        assert simple.numbers.raw is raw.dids
        assert simple.international_numbers.raw is raw.international_dids
        assert simple.voice.raw is raw.sip_trunks
        assert simple.messages.raw is raw.sms
        assert simple.dlc.raw is raw.dlc
        assert simple.fax.raw is raw.fax
        assert simple.enterprise_fax.raw is raw.enterprise_fax
        assert simple.reports.raw is raw.reports
        assert simple.porting.raw is raw.lnp
        assert simple.servers.raw is raw.servers
        assert simple.workflows.raw is raw
    assert closed is False


def test_sync_facade_owns_constructed_client(monkeypatch: pytest.MonkeyPatch) -> None:
    closed = False

    def close(_: QuestBlue) -> None:
        nonlocal closed
        closed = True

    monkeypatch.setattr(QuestBlue, "close", close)
    simple = SimpleQuestBlue(
        "user",
        "password",
        "key",
        base_url="https://example.test/",
        timeout=7,
        max_retries=4,
        http_client=httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200))),
    )
    assert simple.raw.base_url == "https://example.test"
    assert simple.raw.max_retries == 4
    simple.close()
    assert closed is True


@pytest.mark.asyncio
async def test_async_facade_wraps_raw_resources_without_ownership(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = async_raw_client()
    closed = False

    async def close() -> None:
        nonlocal closed
        closed = True

    monkeypatch.setattr(raw, "close", close)
    async with AsyncSimpleQuestBlue.wrap(raw) as simple:
        assert simple.raw is raw
        assert simple.account.raw is raw.account
        assert simple.numbers.raw is raw.dids
        assert simple.workflows.raw is raw
    assert closed is False
    await raw._http.aclose()


@pytest.mark.asyncio
async def test_async_facade_owns_constructed_client(monkeypatch: pytest.MonkeyPatch) -> None:
    closed = False

    async def close(_: AsyncQuestBlue) -> None:
        nonlocal closed
        closed = True

    monkeypatch.setattr(AsyncQuestBlue, "close", close)
    simple = AsyncSimpleQuestBlue(
        "user",
        "password",
        "key",
        base_url="https://example.test/",
        timeout=7,
        max_retries=4,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(200))),
    )
    assert simple.raw.base_url == "https://example.test"
    assert simple.raw.max_retries == 4
    await simple.close()
    assert closed is True
    await simple.raw._http.aclose()


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("+1 (919) 555-0123", 19195550123),
        (9195550123, 9195550123),
        ("212.555.0199", 2125550199),
    ],
)
def test_normalize_phone(value: str | int, expected: int) -> None:
    assert normalize_phone(value) == expected


@pytest.mark.parametrize("value", [True, "555-12", "0123456789", "9195550123 x4"])
def test_normalize_phone_rejects_ambiguous_values(value: Any) -> None:
    with pytest.raises(ValueError):
        normalize_phone(value)


def test_normalize_enum_accepts_members_values_names_and_aliases() -> None:
    assert normalize_enum(Color, Color.RED) is Color.RED
    assert normalize_enum(Color, "BLUE") is Color.BLUE
    assert normalize_enum(Color, "red") is Color.RED
    assert normalize_enum(Color, "primary", aliases={"primary": Color.BLUE}) is Color.BLUE
    assert normalize_enum(Color, "rouge", aliases={"rouge": "red"}) is Color.RED


def test_normalize_enum_rejects_invalid_values_and_alias_targets() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        normalize_enum(Color, "")
    with pytest.raises(ValueError, match="unknown Color"):
        normalize_enum(Color, "green")
    with pytest.raises(ValueError, match="targets an unknown"):
        normalize_enum(Color, "x", aliases={"x": "green"})


def test_normalize_date_range_preserves_dates_and_aware_datetimes() -> None:
    dates = (date(2026, 1, 1), date(2026, 1, 2))
    assert normalize_date_range(*dates) == dates
    instants = (
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        datetime(2026, 1, 2, tzinfo=timezone.utc),
    )
    assert normalize_date_range(*instants, require_timezone=True) == instants


def test_normalize_date_range_rejects_mixed_naive_and_reversed_values() -> None:
    with pytest.raises(ValueError, match="both"):
        normalize_date_range(date(2026, 1, 1), datetime(2026, 1, 2))
    with pytest.raises(ValueError, match="timezone-aware"):
        normalize_date_range(datetime(2026, 1, 1), datetime(2026, 1, 2), require_timezone=True)
    with pytest.raises(ValueError, match="consistent timezone"):
        normalize_date_range(
            datetime(2026, 1, 1),
            datetime(2026, 1, 2, tzinfo=timezone.utc),
        )
    with pytest.raises(ValueError, match="greater"):
        normalize_date_range(date(2026, 1, 2), date(2026, 1, 1))


def test_normalize_path_and_file(tmp_path: Path) -> None:
    source = tmp_path / "fax.PDF"
    source.write_bytes(b"abc")
    assert normalize_path(source, allowed_extensions={"pdf"}, max_bytes=3) == source.resolve()
    assert normalize_file(source, allowed_extensions={".pdf"}) == ("fax.PDF", b"abc")
    assert normalize_file(bytearray(b"abc"), max_bytes=3) == (None, b"abc")


def test_normalize_path_and_file_reject_invalid_input(tmp_path: Path) -> None:
    source = tmp_path / "fax.txt"
    source.write_bytes(b"four")
    with pytest.raises(ValueError, match="existing"):
        normalize_path(tmp_path / "missing.pdf")
    with pytest.raises(ValueError, match="extension"):
        normalize_path(source, allowed_extensions={"pdf"})
    with pytest.raises(ValueError, match="maximum"):
        normalize_path(source, max_bytes=3)
    with pytest.raises(ValueError, match="maximum"):
        normalize_file(b"four", max_bytes=3)


def test_normalize_list_copies_sequences_and_preserves_scalar_strings() -> None:
    original = [1, 2]
    normalized = normalize_list(original)
    assert normalized == original
    assert normalized is not original
    assert normalize_list("value") == ["value"]
    assert normalize_list(3) == [3]


def test_warnings_are_never_silently_discarded() -> None:
    warning = WarningResponse(warning=["check destination", "try later"])
    with pytest.raises(QuestBlueWarningError, match="check destination") as caught:
        unwrap_warning(warning)
    assert caught.value.warning is warning
    result = object()
    assert unwrap_warning(result) is result
    empty = QuestBlueWarningError(WarningResponse())
    assert str(empty) == "QuestBlue returned a warning"


def test_confirmation_error_retains_risk() -> None:
    error = ConfirmationRequiredError(Risk.BILLABLE.value)
    assert error.risk == "billable"
    assert "billable" in str(error)


def test_json_safe_results_redact_sensitive_values() -> None:
    model = ExampleModel(created=date(2026, 8, 5), password="do-not-leak")
    result = OperationResult(
        value=Decimal("12.50"),
        identifiers={"message_id": "abc"},
        warnings=("notice",),
        raw={
            "model": model,
            "content": b"private",
            "path": Path("/private/file"),
            "when": datetime(2026, 8, 5, tzinfo=timezone.utc),
        },
    )
    data = result.to_dict()
    assert data["value"] == "12.50"
    assert data["identifiers"] == {"message_id": "abc"}
    assert data["raw"]["content"] == "[REDACTED]"
    assert data["raw"]["model"]["password"] == "[REDACTED]"
    assert data["raw"]["path"] == "[REDACTED]"
    json.dumps(data)
    assert "raw" not in result.to_dict(include_raw=False)
    assert json_safe(b"abc", redact=False) == "616263"
    assert json_safe(Path("file"), redact=False) == "file"
    assert "do-not-leak" not in repr(result)


def test_plans_and_workflows_are_immutable_json_safe_records() -> None:
    operation = PlannedOperation(
        name="send_message",
        risk=Risk.CONSENT_REQUIRED,
        arguments={"message_body": "secret"},
    )
    plan = OperationPlan((operation, operation))
    assert plan.risks == (Risk.CONSENT_REQUIRED,)
    assert operation.to_dict()["arguments"]["message_body"] == "[REDACTED]"
    assert plan.to_dict()["operations"][0]["risk"] == "consent-required"
    assert "secret" not in repr(operation)
    assert "secret" not in repr(plan)

    step = WorkflowStep("send", Risk.CONSENT_REQUIRED, WorkflowStatus.SUCCEEDED, raw=b"x")
    workflow = WorkflowResult(
        status=WorkflowStatus.PARTIAL,
        steps=(step,),
        failed_step="configure",
        recovery="inspect account",
        raw=({"security_key": "secret"},),
    )
    assert step.to_dict()["raw"] == "[REDACTED]"
    assert workflow.to_dict()["raw"][0]["security_key"] == "[REDACTED]"
    assert "secret" not in repr(step)
    assert "secret" not in repr(workflow)
    json.dumps(workflow.to_dict())
