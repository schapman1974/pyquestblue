"""Credentialed, read-only smoke tests for a dedicated QuestBlue subaccount."""

from __future__ import annotations

import pytest

from questblue import (
    AccountBalanceResponse,
    AccountDetailsResponse,
    DIDInventoryResponse,
    QuestBlue,
    ServerListResponse,
)

pytestmark = [pytest.mark.live, pytest.mark.live_read_only]


def test_live_account_and_inventory_reads(live_read_only_client: QuestBlue) -> None:
    balance = live_read_only_client.account.balance()
    details = live_read_only_client.account.details()
    dids = live_read_only_client.dids.list()
    servers = live_read_only_client.servers.list()
    assert isinstance(balance, AccountBalanceResponse)
    assert isinstance(details, AccountDetailsResponse)
    assert isinstance(dids, DIDInventoryResponse)
    assert isinstance(servers, ServerListResponse)
