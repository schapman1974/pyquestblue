from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from questblue import AsyncQuestBlue, AsyncSimpleQuestBlue, SimpleQuestBlue
from questblue.lnp import LNPCreateResponse, LNPCreateResult, LNPSubmissionStatus
from questblue.servers import ServerOrderData, ServerOrderResponse
from questblue.simple import ConfirmationRequiredError, OperationPlan, OperationResult
from questblue.simple._provision import (
    AsyncEnterpriseFaxProvisioning,
    AsyncFaxProvisioning,
    AsyncInternationalNumberProvisioning,
    AsyncNumberProvisioning,
    AsyncPortingProvisioning,
    AsyncServerProvisioning,
    AsyncVoiceProvisioning,
    EnterpriseFaxProvisioning,
    FaxProvisioning,
    InternationalNumberProvisioning,
    NumberProvisioning,
    PortingProvisioning,
    ServerProvisioning,
    VoiceProvisioning,
)


def _bill(tmp_path: Path) -> Path:
    path = tmp_path / "bill.pdf"
    path.write_bytes(b"%PDF-1.4\n")
    return path


def _port_args(tmp_path: Path) -> dict[str, object]:
    return {
        "numbers": ["919-555-0100"],
        "bill": _bill(tmp_path),
        "provider_name": "Carrier",
        "company": "Example Co",
        "account_number": "A-1",
        "authorized_contact": "Ada Lovelace",
        "contact_title": "Owner",
        "street_number": "1",
        "street_name": "Main St",
        "city": "Cary",
        "state": "nc",
        "zipcode": "27513",
        "billing_number": "9195550100",
    }


def test_facades_install_provisioning_services() -> None:
    simple = SimpleQuestBlue.wrap(MagicMock())
    assert isinstance(simple.numbers, NumberProvisioning)
    assert isinstance(simple.voice, VoiceProvisioning)
    assert isinstance(simple.servers, ServerProvisioning)

    raw = MagicMock(spec=AsyncQuestBlue)
    for name in (
        "account",
        "dids",
        "international_dids",
        "sip_trunks",
        "sms",
        "dlc",
        "fax",
        "enterprise_fax",
        "reports",
        "lnp",
        "servers",
    ):
        setattr(raw, name, MagicMock())
    async_simple = AsyncSimpleQuestBlue.wrap(raw)
    assert isinstance(async_simple.numbers, AsyncNumberProvisioning)
    assert isinstance(async_simple.servers, AsyncServerProvisioning)


def test_number_voice_and_international_plans_and_execution() -> None:
    raw = MagicMock()
    numbers = NumberProvisioning(raw)
    plan = numbers.buy("+1 919 555 0100", trunk="main", dry_run=True)
    assert isinstance(plan, OperationPlan) and plan.operations[0].name == "dids.order"
    raw.order.assert_not_called()
    with pytest.raises(ConfirmationRequiredError):
        numbers.release("9195550100")
    result = numbers.configure("9195550100", forward_to="9195550101", confirm_routing_change=True)
    assert isinstance(result, OperationResult)
    assert raw.update.call_count == 1
    numbers.move_to_fax("9195550100", confirm_routing_change=True)
    numbers.release("9195550100", confirm_destructive=True)

    international = InternationalNumberProvisioning(raw)
    international.buy(
        country_code="GB", city="London", forward_to="9195550100", trunk=1, dry_run=True
    )
    international.configure(
        "442071234567", forward_to="9195550100", trunk=1, confirm_routing_change=True
    )
    international.release("442071234567", confirm_destructive=True)

    voice = VoiceProvisioning(raw)
    voice.create_registration_trunk("reg", "secret", confirm_routing_change=True)
    voice.create_static_trunk("static", "192.0.2.1", confirm_routing_change=True)
    voice.configure_trunk("reg", password="newsecret", confirm_routing_change=True)
    voice.set_caller_block("reg", "9195550100", confirm_routing_change=True)
    voice.delete_trunk("reg", confirm_destructive=True)


def test_fax_and_enterprise_lifecycle() -> None:
    raw = MagicMock()
    fax = FaxProvisioning(raw)
    fax.buy("9195550100", confirm_billable=True)
    configured = fax.configure(
        "9195550100",
        email="fax@example.com",
        account_name="Ada",
        login="ada",
        password="secret",
        paused=True,
        confirm_routing_change=True,
    )
    assert isinstance(configured, OperationResult) and len(configured.raw) == 2
    fax.move_to_voice("9195550100", confirm_routing_change=True)
    fax.release("9195550100", confirm_destructive=True)

    enterprise = EnterpriseFaxProvisioning(raw)
    enterprise.buy("9195550100", group="sales", confirm_billable=True)
    enterprise.create_group("sales", "Sales", confirm_routing_change=True)
    enterprise.create_user(
        login="ada",
        password="secret",
        group="sales",
        first_name="Ada",
        email="ada@example.com",
        confirm_routing_change=True,
    )
    enterprise.set_permission(
        login="ada",
        number="9195550100",
        allow_send=True,
        confirm_routing_change=True,
    )
    enterprise.delete_group("sales", confirm_destructive=True)
    enterprise.release("9195550100", confirm_destructive=True)


def test_porting_always_builds_a_draft_and_preserves_response(tmp_path: Path) -> None:
    raw = MagicMock()
    raw.create.return_value = LNPCreateResponse(data=[LNPCreateResult(id="lnp-42")])
    service = PortingProvisioning(raw)
    plan = service.create_draft(**_port_args(tmp_path), dry_run=True)
    assert isinstance(plan, OperationPlan)
    assert plan.operations[0].arguments["status"] == LNPSubmissionStatus.DRAFT.value
    raw.create.assert_not_called()
    result = service.create_draft(**_port_args(tmp_path), confirm_compliance=True)
    assert isinstance(result, OperationResult) and result.value == "lnp-42"
    assert raw.create.call_args.args[0].status is LNPSubmissionStatus.DRAFT


def test_server_lifecycle_plans_and_executes_once() -> None:
    raw = MagicMock()
    raw.create.return_value = ServerOrderResponse(data=ServerOrderData(server_id=42))
    service = ServerProvisioning(raw)
    plan = service.provision(
        server_type="small", product="vital-pbx", email="ops@example.com", dry_run=True
    )
    assert isinstance(plan, OperationPlan)
    created = service.provision(
        server_type="small",
        product="vital-pbx",
        email="ops@example.com",
        confirm_billable=True,
    )
    assert isinstance(created, OperationResult) and created.value == 42
    assert raw.create.call_count == 1
    service.add_ip(42, "192.0.2.1", confirm_routing_change=True)
    service.schedule_backups(42, "daily", confirm_routing_change=True)
    service.restore(42, 7, confirm_destructive=True)
    service.remove_backup(42, 7, confirm_destructive=True)
    service.release(42, confirm_destructive=True)


@pytest.mark.asyncio
async def test_async_provisioning_parity(tmp_path: Path) -> None:
    raw = MagicMock()
    for name in (
        "order",
        "update",
        "move_to_fax",
        "delete",
        "create",
        "block_caller",
        "pause",
        "move_to_voice",
        "create_user",
        "set_permission",
        "create_group",
        "delete_group",
        "add_ip",
        "manage_backup_schedule",
        "restore_backup",
        "remove_backup",
    ):
        setattr(raw, name, AsyncMock(return_value=None))

    numbers = AsyncNumberProvisioning(raw)
    await numbers.buy("9195550100", confirm_billable=True)
    await numbers.configure("9195550100", trunk="main", confirm_routing_change=True)
    await numbers.move_to_fax("9195550100", confirm_routing_change=True)
    await numbers.release("9195550100", confirm_destructive=True)

    international = AsyncInternationalNumberProvisioning(raw)
    await international.buy(
        country_code="GB", city="London", forward_to="9195550100", trunk=1, dry_run=True
    )
    await international.configure("442071234567", forward_to="9195550100", trunk=1, dry_run=True)
    await international.release("442071234567", dry_run=True)

    voice = AsyncVoiceProvisioning(raw)
    await voice.create_registration_trunk("reg", "secret", dry_run=True)
    await voice.create_static_trunk("static", "192.0.2.1", dry_run=True)
    await voice.configure_trunk("reg", password="secret", dry_run=True)
    await voice.set_caller_block("reg", "9195550100", dry_run=True)
    await voice.delete_trunk("reg", dry_run=True)

    fax = AsyncFaxProvisioning(raw)
    await fax.buy("9195550100", dry_run=True)
    await fax.configure("9195550100", paused=False, confirm_routing_change=True)
    await fax.move_to_voice("9195550100", dry_run=True)
    await fax.release("9195550100", dry_run=True)

    enterprise = AsyncEnterpriseFaxProvisioning(raw)
    await enterprise.buy("9195550100", dry_run=True)
    await enterprise.create_group("sales", "Sales", dry_run=True)
    await enterprise.create_user(
        login="ada", password="secret", group="sales", first_name="Ada", dry_run=True
    )
    await enterprise.set_permission(login="ada", number="9195550100", dry_run=True)
    await enterprise.delete_group("sales", dry_run=True)
    await enterprise.release("9195550100", dry_run=True)

    raw.create.return_value = LNPCreateResponse(data=[LNPCreateResult(id="lnp-async")])
    porting = AsyncPortingProvisioning(raw)
    result = await porting.create_draft(**_port_args(tmp_path), confirm_compliance=True)
    assert isinstance(result, OperationResult) and result.value == "lnp-async"

    raw.create.return_value = ServerOrderResponse(data=ServerOrderData(server_id=44))
    servers = AsyncServerProvisioning(raw)
    await servers.provision(
        server_type="small",
        product="vital-pbx",
        email="ops@example.com",
        confirm_billable=True,
    )
    await servers.add_ip(44, "192.0.2.1", dry_run=True)
    await servers.schedule_backups(44, "weekly", dry_run=True)
    await servers.restore(44, 7, dry_run=True)
    await servers.remove_backup(44, 7, dry_run=True)
    await servers.release(44, dry_run=True)
