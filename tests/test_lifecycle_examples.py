from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from examples.lnp_draft import create_draft
from examples.reports_export import export_current_month
from examples.server_lifecycle import provision_vital_pbx, restore
from questblue import QuestBlue, ServerMessageResponse, ServerOrderResponse


def handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/lnp":
        return httpx.Response(200, json={"data": [{"id": "1001"}]})
    if request.url.path == "/callhistory":
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "call_type": "Inbound Call",
                        "call_status": "ok",
                        "call_id": 1001,
                        "call_duration_min": "1.0",
                    }
                ],
                "total": 1,
                "total_pages": 1,
                "current_page": 1,
            },
        )
    if request.url.path == "/server" and request.method == "POST":
        return httpx.Response(200, json={"data": {"server_id": 1001}})
    if request.url.path == "/server/restorebackup":
        return httpx.Response(200, json={"message": "accepted"})
    raise AssertionError(f"unexpected example request: {request.method} {request.url.path}")


@pytest.fixture
def client() -> QuestBlue:
    http = httpx.Client(base_url="https://example.test", transport=httpx.MockTransport(handler))
    return QuestBlue("user", "password", "key", http_client=http)


def test_lnp_draft_example_is_guarded_and_executable(client: QuestBlue, tmp_path: Path) -> None:
    bill = tmp_path / "bill.pdf"
    bill.write_bytes(b"synthetic bill")
    with pytest.raises(ValueError, match="no documented sandbox"):
        create_draft(client, bill)
    result = create_draft(client, bill, confirm_production_draft=True)
    assert result.data[0].id == "1001"  # type: ignore[union-attr]


def test_report_export_example_is_executable(client: QuestBlue, tmp_path: Path) -> None:
    destination = tmp_path / "calls.csv"
    export_current_month(client, destination)
    content = destination.read_text(encoding="utf-8")
    assert "call_type" in content
    assert "Inbound Call" in content


def test_server_lifecycle_examples_are_guarded_and_executable(client: QuestBlue) -> None:
    with pytest.raises(ValueError, match="review pricing"):
        provision_vital_pbx(client, "ops@example.test")
    ordered = provision_vital_pbx(client, "ops@example.test", confirm_billable_order=True)
    assert isinstance(ordered, ServerOrderResponse)
    with pytest.raises(ValueError, match="confirm the destructive restore"):
        restore(client, 1001, 9)
    restored = restore(client, 1001, 9, confirm_destructive_restore=True)
    assert isinstance(restored, ServerMessageResponse)
