from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from questblue import QuestBlueTimeoutError
from questblue.simple import (
    AsyncWorkflowPlan,
    ConfirmationRequiredError,
    OperationResult,
    PlannedOperation,
    Risk,
    WorkflowPlan,
    WorkflowStatus,
)
from questblue.simple._workflows import AsyncWorkflows, Workflows


def _raw() -> SimpleNamespace:
    return SimpleNamespace(
        dids=MagicMock(),
        sip_trunks=MagicMock(),
        fax=MagicMock(),
        enterprise_fax=MagicMock(),
        lnp=MagicMock(),
        servers=MagicMock(),
    )


def test_sync_plan_requires_all_risk_confirmations_and_journals_steps() -> None:
    events = []
    plan = WorkflowPlan(
        (
            PlannedOperation("create-trunk", Risk.ROUTING_CHANGE),
            PlannedOperation("buy-number", Risk.BILLABLE),
        ),
        "correlation-1",
        (
            lambda: OperationResult(value=True, identifiers={"trunk": "main"}, raw="one"),
            lambda: OperationResult(value=True, identifiers={"number": "9195550100"}, raw="two"),
        ),
        events.append,
    )
    assert plan.risks == (Risk.ROUTING_CHANGE, Risk.BILLABLE)
    with pytest.raises(ConfirmationRequiredError):
        plan.execute(confirm_routing_change=True)
    result = plan.execute(confirm_routing_change=True, confirm_billable=True)
    assert result.status is WorkflowStatus.SUCCEEDED
    assert result.identifiers == {"trunk": "main", "number": "9195550100"}
    assert [event.status for event in events] == [
        WorkflowStatus.PLANNED,
        WorkflowStatus.SUCCEEDED,
        WorkflowStatus.PLANNED,
        WorkflowStatus.SUCCEEDED,
    ]
    assert all(event.correlation_id == "correlation-1" for event in events)


def test_fault_injection_reports_partial_and_uncertain_without_rollback() -> None:
    def fail() -> OperationResult[bool]:
        raise ValueError("provider rejected step")

    partial = WorkflowPlan(
        (
            PlannedOperation("one", Risk.ROUTING_CHANGE),
            PlannedOperation("two", Risk.ROUTING_CHANGE),
        ),
        "c",
        (lambda: OperationResult(value=True, raw="one"), fail),
    ).execute(confirm_routing_change=True)
    assert partial.status is WorkflowStatus.PARTIAL
    assert partial.failed_step == "two" and isinstance(partial.error, ValueError)
    assert "not rolled back" in (partial.recovery or "")

    def timeout() -> OperationResult[bool]:
        raise QuestBlueTimeoutError("unknown provider outcome")

    uncertain = WorkflowPlan((PlannedOperation("mutate", Risk.BILLABLE),), "c", (timeout,)).execute(
        confirm_billable=True
    )
    assert uncertain.status is WorkflowStatus.UNCERTAIN
    assert uncertain.uncertain_step == "mutate"


def test_workflow_builders_are_inspectable_and_never_search_inventory(tmp_path) -> None:
    raw = _raw()
    service = Workflows(raw)
    assert [
        op.name for op in service.voice_number("9195550100", "main", password="secret").operations
    ] == ["sip_trunks.create", "dids.order"]
    with pytest.raises(ValueError):
        service.voice_number("9195550100", "main")
    assert service.fax_number("9195550100").operations[0].name == "fax.create"
    assert (
        len(
            service.onboard_enterprise_fax(
                "9195550100",
                group="sales",
                group_name="Sales",
                login="ada",
                password="secret",
                first_name="Ada",
            ).operations
        )
        == 4
    )
    file = tmp_path / "fax.pdf"
    file.write_bytes(b"%PDF")
    assert service.send_enterprise_fax(
        from_number="9195550100", to="9195550101", files=[file]
    ).risks == (Risk.DESTINATION_CONFIRMATION,)
    assert service.porting_draft(numbers=["9195550100"]).operations[0].name == "lnp.create"
    server = service.provision_server(
        server_type="small",
        product="vital-pbx",
        email="ops@example.com",
        ip_address="192.0.2.1",
        backup_schedule="daily",
    )
    assert len(server.operations) == 3
    raw.dids.available.assert_not_called()


@pytest.mark.asyncio
async def test_async_plan_matches_status_and_supports_async_hook() -> None:
    events = []

    async def hook(step) -> None:
        events.append(step)

    async def success() -> OperationResult[bool]:
        return OperationResult(value=True, identifiers={"id": "1"})

    plan = AsyncWorkflowPlan(
        (PlannedOperation("one", Risk.COMPLIANCE_SENSITIVE),), "async-c", (success,), hook
    )
    result = await plan.execute(confirm_compliance=True)
    assert result.status is WorkflowStatus.SUCCEEDED
    assert len(events) == 2


@pytest.mark.asyncio
async def test_async_workflow_builders_and_execution(monkeypatch) -> None:
    service = AsyncWorkflows(_raw())
    monkeypatch.setattr(
        service.voice, "create_registration_trunk", AsyncMock(return_value=OperationResult(True))
    )
    monkeypatch.setattr(service.numbers, "buy", AsyncMock(return_value=OperationResult(True)))
    plan = service.voice_number("9195550100", "main", password="secret")
    result = await plan.execute(confirm_routing_change=True, confirm_billable=True)
    assert result.status is WorkflowStatus.SUCCEEDED
    assert service.fax_number("9195550100").operations[0].name == "fax.create"
    assert (
        len(
            service.onboard_enterprise_fax(
                "9195550100",
                group="sales",
                group_name="Sales",
                login="ada",
                password="secret",
                first_name="Ada",
            ).operations
        )
        == 4
    )
    assert service.send_enterprise_fax(
        from_number="9195550100", to="9195550101", files=[]
    ).risks == (Risk.DESTINATION_CONFIRMATION,)
    assert service.porting_draft(numbers=["9195550100"]).risks == (Risk.COMPLIANCE_SENSITIVE,)
    assert service.provision_server(
        server_type="small", product="vital-pbx", email="ops@example.com"
    ).risks == (Risk.BILLABLE,)
