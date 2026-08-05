"""Offline contract fixtures captured as synthetic QuestBlue response shapes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from questblue import AccountBalanceResponse, CallHistoryResponse, ServerListResponse

pytestmark = pytest.mark.recorded
FIXTURES = Path(__file__).parent / "fixtures" / "contracts"


def fixture(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_recorded_account_balance_contract() -> None:
    response = AccountBalanceResponse.model_validate(fixture("account_balance.json"))
    assert str(response.data.balance) == "125.50"


def test_recorded_detailed_call_history_contract() -> None:
    response = CallHistoryResponse.model_validate(fixture("call_history_detail.json"))
    assert response.data[0].call_type == "Inbound Call"
    assert response.total_pages == 1


def test_recorded_server_inventory_contract() -> None:
    response = ServerListResponse.model_validate(fixture("server_inventory.json"))
    assert response.data[0].allowed_ip == ["192.0.2.10", "2001:db8::10"]
