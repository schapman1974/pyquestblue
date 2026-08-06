from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from questblue import SimpleQuestBlue
from questblue.simple import (
    AuditEvent,
    OperationContext,
    OperationResult,
    PlannedOperation,
    PolicyDecision,
    PolicyDeniedError,
    Risk,
    WorkflowPlan,
    WorkflowStatus,
)


def _raw() -> SimpleNamespace:
    return SimpleNamespace(
        account=MagicMock(),
        dids=MagicMock(),
        international_dids=MagicMock(),
        sip_trunks=MagicMock(),
        sms=MagicMock(),
        dlc=MagicMock(),
        fax=MagicMock(),
        enterprise_fax=MagicMock(),
        reports=MagicMock(),
        lnp=MagicMock(),
        servers=MagicMock(),
    )


def test_configured_policy_denies_by_default_before_io() -> None:
    raw = _raw()
    simple = SimpleQuestBlue.wrap(raw, policy_hook=lambda request: None)
    plan = simple.workflows.voice_number("9195550100", "main", password="secret")
    with pytest.raises(PolicyDeniedError):
        plan.execute(confirm_routing_change=True, confirm_billable=True)
    raw.sip_trunks.create.assert_not_called()
    raw.dids.order.assert_not_called()


def test_policy_can_authorize_and_confirm_risks_without_sending_context_upstream() -> None:
    raw = _raw()
    requests = []

    def policy(request):
        requests.append(request)
        return PolicyDecision(
            allowed=True, confirmed_risks=frozenset({Risk.ROUTING_CHANGE, Risk.BILLABLE})
        )

    context = OperationContext(
        tenant_id="tenant-a",
        actor_id="user-7",
        reason="customer order",
        metadata={"access_token": "never-log"},
    )
    simple = SimpleQuestBlue.wrap(raw, operation_context=context, policy_hook=policy)
    result = simple.workflows.voice_number(
        "9195550100", "main", password="secret", correlation_id="order-42"
    ).execute()
    assert result.status is WorkflowStatus.SUCCEEDED
    assert {request.context.tenant_id for request in requests} == {"tenant-a"}
    request_params = raw.dids.order.call_args.args[0].to_request_params()
    assert "tenant_id" not in request_params and "actor_id" not in request_params


def test_audit_events_are_versioned_redacted_and_include_dlq_handoff() -> None:
    events: list[AuditEvent] = []

    def fail() -> OperationResult[bool]:
        raise ValueError("rejected")

    context = OperationContext(
        correlation_id="c-1",
        tenant_id="tenant-a",
        metadata={"password": "secret", "body": "private", "file_content": b"data"},
    )
    result = WorkflowPlan(
        (PlannedOperation("send", Risk.DESTINATION_CONFIRMATION, {"body": "private"}),),
        "c-1",
        (fail,),
        None,
        context,
        lambda request: True,
        events.append,
    ).execute(destination_confirmed=True)
    assert result.status is WorkflowStatus.FAILED
    assert events[-1].handoff == "dead-letter"
    serialized = events[-1].to_dict()
    assert serialized["version"] == "1"
    assert serialized["context"]["metadata"] == {
        "password": "[REDACTED]",
        "body": "[REDACTED]",
        "file_content": "[REDACTED]",
    }
    assert "private" not in repr(serialized)


def test_concurrent_tenant_contexts_do_not_cross() -> None:
    def execute(tenant: str) -> tuple[str, str]:
        events: list[AuditEvent] = []
        context = OperationContext(tenant_id=tenant)
        plan = WorkflowPlan(
            (PlannedOperation("provision", Risk.BILLABLE),),
            tenant,
            (lambda: OperationResult(value=True),),
            None,
            context,
            lambda request: PolicyDecision(True, frozenset({Risk.BILLABLE})),
            events.append,
        )
        result = plan.execute()
        assert result.status is WorkflowStatus.SUCCEEDED
        return events[-1].context.tenant_id or "", events[-1].context.correlation_id or ""

    with ThreadPoolExecutor(max_workers=2) as pool:
        values = list(pool.map(execute, ("tenant-a", "tenant-b")))
    assert values == [("tenant-a", ""), ("tenant-b", "")]
