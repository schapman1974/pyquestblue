"""Inspectable, journaled composite workflows for the simple facade."""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable, Mapping, Optional, Sequence, Tuple, Union
from uuid import uuid4

from questblue._exceptions import QuestBlueTimeoutError

from ._errors import ConfirmationRequiredError, PolicyDeniedError
from ._integration import (
    AuditEvent,
    AuditHook,
    OperationContext,
    PolicyHook,
    PolicyRequest,
    policy_decision,
)
from ._provision import (
    AsyncEnterpriseFaxProvisioning,
    AsyncFaxProvisioning,
    AsyncNumberProvisioning,
    AsyncPortingProvisioning,
    AsyncServerProvisioning,
    AsyncVoiceProvisioning,
    EnterpriseFaxProvisioning,
    FaxProvisioning,
    NumberProvisioning,
    PortingProvisioning,
    ServerProvisioning,
    VoiceProvisioning,
)
from ._read import AsyncEnterpriseFaxReads, EnterpriseFaxReads
from ._results import (
    OperationResult,
    PlannedOperation,
    Risk,
    WorkflowResult,
    WorkflowStatus,
    WorkflowStep,
)

JournalHook = Callable[[WorkflowStep], Any]
SyncCall = Callable[[], Any]
AsyncCall = Callable[[], Awaitable[Any]]


def _confirmed(risk: Risk, confirmations: Mapping[str, bool]) -> bool:
    names = {
        Risk.BILLABLE: "confirm_billable",
        Risk.ROUTING_CHANGE: "confirm_routing_change",
        Risk.COMPLIANCE_SENSITIVE: "confirm_compliance",
        Risk.DESTINATION_CONFIRMATION: "destination_confirmed",
        Risk.DESTRUCTIVE: "confirm_destructive",
    }
    name = names.get(risk)
    return name is None or confirmations.get(name, False)


def _recovery(name: str, uncertain: bool) -> str:
    action = "verify provider state before retrying" if uncertain else "inspect provider state"
    return f"Workflow stopped at {name}; {action}. Completed steps were not rolled back."


@dataclass(frozen=True, repr=False)
class WorkflowPlan:
    """A synchronous plan whose execution records every attempted provider call."""

    operations: Tuple[PlannedOperation, ...]
    correlation_id: str
    _calls: Tuple[SyncCall, ...] = field(repr=False)
    _hook: Optional[JournalHook] = field(default=None, repr=False)
    context: OperationContext = field(default_factory=OperationContext)
    _policy_hook: Optional[PolicyHook] = field(default=None, repr=False)
    _audit_hook: Optional[AuditHook] = field(default=None, repr=False)

    @property
    def risks(self) -> Tuple[Risk, ...]:
        return tuple(dict.fromkeys(operation.risk for operation in self.operations))

    def execute(
        self,
        *,
        confirm_billable: bool = False,
        confirm_routing_change: bool = False,
        confirm_compliance: bool = False,
        destination_confirmed: bool = False,
        confirm_destructive: bool = False,
    ) -> WorkflowResult[Any]:
        confirmations = locals()
        for operation in self.operations:
            decision = policy_decision(
                self._policy_hook(PolicyRequest(operation, self.context))
                if self._policy_hook
                else True
            )
            if self._policy_hook and not decision.allowed:
                raise PolicyDeniedError(operation.name, decision.reason)
            if (
                not _confirmed(operation.risk, confirmations)
                and operation.risk not in decision.confirmed_risks
            ):
                raise ConfirmationRequiredError(operation.risk.value)
        steps: list[WorkflowStep] = []
        identifiers: dict[str, str] = {}
        raw: list[Any] = []
        for operation, call in zip(self.operations, self._calls, strict=True):
            started = WorkflowStep(
                operation.name, operation.risk, WorkflowStatus.PLANNED, self.correlation_id
            )
            if self._hook:
                self._hook(started)
            if self._audit_hook:
                self._audit_hook(
                    AuditEvent(operation.name, operation.risk, WorkflowStatus.PLANNED, self.context)
                )
            try:
                result = call()
                if not isinstance(result, OperationResult):
                    raise TypeError("workflow execution unexpectedly returned a plan")
            except Exception as exc:
                uncertain = isinstance(exc, QuestBlueTimeoutError)
                failed = WorkflowStep(
                    operation.name,
                    operation.risk,
                    WorkflowStatus.UNCERTAIN if uncertain else WorkflowStatus.FAILED,
                    self.correlation_id,
                )
                steps.append(failed)
                if self._hook:
                    self._hook(failed)
                if self._audit_hook:
                    self._audit_hook(
                        AuditEvent(
                            operation.name,
                            operation.risk,
                            failed.status,
                            self.context,
                            recovery=_recovery(operation.name, uncertain),
                            handoff="reconcile" if uncertain else "dead-letter",
                        )
                    )
                return WorkflowResult(
                    status=WorkflowStatus.UNCERTAIN
                    if uncertain
                    else (WorkflowStatus.PARTIAL if len(steps) > 1 else WorkflowStatus.FAILED),
                    steps=tuple(steps),
                    identifiers=identifiers,
                    failed_step=None if uncertain else operation.name,
                    uncertain_step=operation.name if uncertain else None,
                    recovery=_recovery(operation.name, uncertain),
                    error=exc,
                    raw=tuple(raw),
                )
            completed = WorkflowStep(
                operation.name,
                operation.risk,
                WorkflowStatus.SUCCEEDED,
                self.correlation_id,
                result.identifiers,
                result.warnings,
                result.raw,
            )
            steps.append(completed)
            identifiers.update(result.identifiers)
            raw.append(result.raw)
            if self._hook:
                self._hook(completed)
            if self._audit_hook:
                self._audit_hook(
                    AuditEvent(
                        operation.name,
                        operation.risk,
                        WorkflowStatus.SUCCEEDED,
                        self.context,
                        result.identifiers,
                        result.warnings,
                    )
                )
        return WorkflowResult(
            status=WorkflowStatus.SUCCEEDED,
            value=True,
            steps=tuple(steps),
            identifiers=identifiers,
            raw=tuple(raw),
        )


@dataclass(frozen=True, repr=False)
class AsyncWorkflowPlan:
    """Async counterpart to :class:`WorkflowPlan`."""

    operations: Tuple[PlannedOperation, ...]
    correlation_id: str
    _calls: Tuple[AsyncCall, ...] = field(repr=False)
    _hook: Optional[JournalHook] = field(default=None, repr=False)
    context: OperationContext = field(default_factory=OperationContext)
    _policy_hook: Optional[PolicyHook] = field(default=None, repr=False)
    _audit_hook: Optional[AuditHook] = field(default=None, repr=False)

    @property
    def risks(self) -> Tuple[Risk, ...]:
        return tuple(dict.fromkeys(operation.risk for operation in self.operations))

    async def _emit(self, step: WorkflowStep) -> None:
        if self._hook:
            result = self._hook(step)
            if inspect.isawaitable(result):
                await result

    async def _audit(self, event: AuditEvent) -> None:
        if self._audit_hook:
            result = self._audit_hook(event)
            if inspect.isawaitable(result):
                await result

    async def execute(
        self,
        *,
        confirm_billable: bool = False,
        confirm_routing_change: bool = False,
        confirm_compliance: bool = False,
        destination_confirmed: bool = False,
        confirm_destructive: bool = False,
    ) -> WorkflowResult[Any]:
        confirmations = locals()
        for operation in self.operations:
            decision = policy_decision(
                self._policy_hook(PolicyRequest(operation, self.context))
                if self._policy_hook
                else True
            )
            if self._policy_hook and not decision.allowed:
                raise PolicyDeniedError(operation.name, decision.reason)
            if (
                not _confirmed(operation.risk, confirmations)
                and operation.risk not in decision.confirmed_risks
            ):
                raise ConfirmationRequiredError(operation.risk.value)
        steps: list[WorkflowStep] = []
        identifiers: dict[str, str] = {}
        raw: list[Any] = []
        for operation, call in zip(self.operations, self._calls, strict=True):
            await self._emit(
                WorkflowStep(
                    operation.name, operation.risk, WorkflowStatus.PLANNED, self.correlation_id
                )
            )
            await self._audit(
                AuditEvent(operation.name, operation.risk, WorkflowStatus.PLANNED, self.context)
            )
            try:
                result = await call()
                if not isinstance(result, OperationResult):
                    raise TypeError("workflow execution unexpectedly returned a plan")
            except Exception as exc:
                uncertain = isinstance(exc, QuestBlueTimeoutError)
                failed = WorkflowStep(
                    operation.name,
                    operation.risk,
                    WorkflowStatus.UNCERTAIN if uncertain else WorkflowStatus.FAILED,
                    self.correlation_id,
                )
                steps.append(failed)
                await self._emit(failed)
                await self._audit(
                    AuditEvent(
                        operation.name,
                        operation.risk,
                        failed.status,
                        self.context,
                        recovery=_recovery(operation.name, uncertain),
                        handoff="reconcile" if uncertain else "dead-letter",
                    )
                )
                return WorkflowResult(
                    status=WorkflowStatus.UNCERTAIN
                    if uncertain
                    else (WorkflowStatus.PARTIAL if len(steps) > 1 else WorkflowStatus.FAILED),
                    steps=tuple(steps),
                    identifiers=identifiers,
                    failed_step=None if uncertain else operation.name,
                    uncertain_step=operation.name if uncertain else None,
                    recovery=_recovery(operation.name, uncertain),
                    error=exc,
                    raw=tuple(raw),
                )
            completed = WorkflowStep(
                operation.name,
                operation.risk,
                WorkflowStatus.SUCCEEDED,
                self.correlation_id,
                result.identifiers,
                result.warnings,
                result.raw,
            )
            steps.append(completed)
            identifiers.update(result.identifiers)
            raw.append(result.raw)
            await self._emit(completed)
            await self._audit(
                AuditEvent(
                    operation.name,
                    operation.risk,
                    WorkflowStatus.SUCCEEDED,
                    self.context,
                    result.identifiers,
                    result.warnings,
                )
            )
        return WorkflowResult(
            status=WorkflowStatus.SUCCEEDED,
            value=True,
            steps=tuple(steps),
            identifiers=identifiers,
            raw=tuple(raw),
        )


def _id(value: Optional[str]) -> str:
    return value or str(uuid4())


class Workflows:
    def __init__(
        self,
        raw: Any,
        *,
        context: Optional[OperationContext] = None,
        policy_hook: Optional[PolicyHook] = None,
        audit_hook: Optional[AuditHook] = None,
    ) -> None:
        self.raw = raw
        self.context = context or OperationContext()
        self.policy_hook = policy_hook
        self.audit_hook = audit_hook
        self.numbers = NumberProvisioning(raw.dids)
        self.voice = VoiceProvisioning(raw.sip_trunks)
        self.fax = FaxProvisioning(raw.fax)
        self.enterprise = EnterpriseFaxProvisioning(raw.enterprise_fax)
        self.enterprise_reads = EnterpriseFaxReads(raw.enterprise_fax)
        self.porting = PortingProvisioning(raw.lnp)
        self.servers = ServerProvisioning(raw.servers)

    def _integration(
        self, correlation_id: str
    ) -> tuple[OperationContext, Optional[PolicyHook], Optional[AuditHook]]:
        return self.context.with_correlation(correlation_id), self.policy_hook, self.audit_hook

    def voice_number(
        self,
        number: Union[str, int],
        trunk: str,
        *,
        password: Optional[str] = None,
        ip_address: Optional[str] = None,
        correlation_id: Optional[str] = None,
        journal_hook: Optional[JournalHook] = None,
    ) -> WorkflowPlan:
        if (password is None) == (ip_address is None):
            raise ValueError("provide exactly one of password or ip_address")

        def create() -> OperationResult[Any]:
            if password is not None:
                result = self.voice.create_registration_trunk(
                    trunk, password, confirm_routing_change=True
                )
            else:
                result = self.voice.create_static_trunk(
                    trunk, ip_address or "", confirm_routing_change=True
                )
            assert isinstance(result, OperationResult)
            return result

        cid = _id(correlation_id)
        return WorkflowPlan(
            (
                PlannedOperation("sip_trunks.create", Risk.ROUTING_CHANGE, {"trunk": trunk}),
                PlannedOperation("dids.order", Risk.BILLABLE, {"did": number, "trunk": trunk}),
            ),
            cid,
            (create, lambda: self.numbers.buy(number, trunk=trunk, confirm_billable=True)),
            journal_hook,
            *self._integration(cid),
        )

    def fax_number(
        self,
        number: Union[str, int],
        *,
        email: Optional[str] = None,
        account_name: Optional[str] = None,
        login: Optional[str] = None,
        password: Optional[str] = None,
        correlation_id: Optional[str] = None,
        journal_hook: Optional[JournalHook] = None,
    ) -> WorkflowPlan:
        cid = _id(correlation_id)
        return WorkflowPlan(
            (PlannedOperation("fax.create", Risk.BILLABLE, {"did": number, "email": email}),),
            cid,
            (
                lambda: self.fax.buy(
                    number,
                    email=email,
                    account_name=account_name,
                    login=login,
                    password=password,
                    confirm_billable=True,
                ),
            ),
            journal_hook,
            *self._integration(cid),
        )

    def onboard_enterprise_fax(
        self,
        number: Union[str, int],
        *,
        group: str,
        group_name: str,
        login: str,
        password: str,
        first_name: str,
        email: Optional[str] = None,
        correlation_id: Optional[str] = None,
        journal_hook: Optional[JournalHook] = None,
    ) -> WorkflowPlan:
        operations = (
            PlannedOperation("enterprise_fax.create_group", Risk.ROUTING_CHANGE, {"group": group}),
            PlannedOperation("enterprise_fax.create_user", Risk.ROUTING_CHANGE, {"login": login}),
            PlannedOperation("enterprise_fax.create", Risk.BILLABLE, {"did": number}),
            PlannedOperation(
                "enterprise_fax.set_permission",
                Risk.ROUTING_CHANGE,
                {"login": login, "did": number},
            ),
        )
        calls = (
            lambda: self.enterprise.create_group(group, group_name, confirm_routing_change=True),
            lambda: self.enterprise.create_user(
                login=login,
                password=password,
                group=group,
                first_name=first_name,
                email=email,
                confirm_routing_change=True,
            ),
            lambda: self.enterprise.buy(number, group=group, confirm_billable=True),
            lambda: self.enterprise.set_permission(
                login=login,
                number=number,
                allow_send=True,
                allow_inbound_list=True,
                allow_outbound_list=True,
                confirm_routing_change=True,
            ),
        )
        cid = _id(correlation_id)
        return WorkflowPlan(operations, cid, calls, journal_hook, *self._integration(cid))

    def send_enterprise_fax(
        self,
        *,
        from_number: Union[str, int],
        to: Union[str, int],
        files: Sequence[Union[str, Path]],
        correlation_id: Optional[str] = None,
        journal_hook: Optional[JournalHook] = None,
    ) -> WorkflowPlan:
        cid = _id(correlation_id)
        return WorkflowPlan(
            (
                PlannedOperation(
                    "enterprise_fax.upload_and_send",
                    Risk.DESTINATION_CONFIRMATION,
                    {"from": from_number, "to": to, "files": files},
                ),
            ),
            cid,
            (
                lambda: self.enterprise_reads.send(
                    from_number=from_number, to=to, files=files, destination_confirmed=True
                ),
            ),
            journal_hook,
            *self._integration(cid),
        )

    def porting_draft(
        self,
        *,
        correlation_id: Optional[str] = None,
        journal_hook: Optional[JournalHook] = None,
        **fields: Any,
    ) -> WorkflowPlan:
        cid = _id(correlation_id)
        return WorkflowPlan(
            (PlannedOperation("lnp.create", Risk.COMPLIANCE_SENSITIVE, fields),),
            cid,
            (lambda: self.porting.create_draft(**fields, confirm_compliance=True),),
            journal_hook,
            *self._integration(cid),
        )

    def provision_server(
        self,
        *,
        server_type: str,
        product: str,
        email: str,
        ip_address: Optional[str] = None,
        backup_schedule: Optional[str] = None,
        correlation_id: Optional[str] = None,
        journal_hook: Optional[JournalHook] = None,
    ) -> WorkflowPlan:
        state: dict[str, int] = {}

        def create() -> OperationResult[Any]:
            result = self.servers.provision(
                server_type=server_type,
                product=product,
                email=email,
                confirm_billable=True,
            )
            assert isinstance(result, OperationResult) and isinstance(result.value, int)
            state["server_id"] = result.value
            return result

        arguments = {
            "server_type": server_type,
            "product": product,
            "email": email,
            "next_ip": ip_address,
            "next_backup_schedule": backup_schedule,
        }
        operations = [PlannedOperation("servers.create", Risk.BILLABLE, arguments)]
        calls: list[SyncCall] = [create]
        if ip_address is not None:
            operations.append(
                PlannedOperation("servers.add_ip", Risk.ROUTING_CHANGE, {"ip": ip_address})
            )
            calls.append(
                lambda: self.servers.add_ip(
                    state["server_id"], ip_address, confirm_routing_change=True
                )
            )
        if backup_schedule is not None:
            operations.append(
                PlannedOperation(
                    "servers.manage_backup_schedule",
                    Risk.ROUTING_CHANGE,
                    {"schedule": backup_schedule},
                )
            )
            calls.append(
                lambda: self.servers.schedule_backups(
                    state["server_id"], backup_schedule, confirm_routing_change=True
                )
            )
        cid = _id(correlation_id)
        return WorkflowPlan(
            tuple(operations), cid, tuple(calls), journal_hook, *self._integration(cid)
        )


class AsyncWorkflows:
    def __init__(
        self,
        raw: Any,
        *,
        context: Optional[OperationContext] = None,
        policy_hook: Optional[PolicyHook] = None,
        audit_hook: Optional[AuditHook] = None,
    ) -> None:
        self.raw = raw
        self.context = context or OperationContext()
        self.policy_hook = policy_hook
        self.audit_hook = audit_hook
        self.numbers = AsyncNumberProvisioning(raw.dids)
        self.voice = AsyncVoiceProvisioning(raw.sip_trunks)
        self.fax = AsyncFaxProvisioning(raw.fax)
        self.enterprise = AsyncEnterpriseFaxProvisioning(raw.enterprise_fax)
        self.enterprise_reads = AsyncEnterpriseFaxReads(raw.enterprise_fax)
        self.porting = AsyncPortingProvisioning(raw.lnp)
        self.servers = AsyncServerProvisioning(raw.servers)

    def _integration(
        self, correlation_id: str
    ) -> tuple[OperationContext, Optional[PolicyHook], Optional[AuditHook]]:
        return self.context.with_correlation(correlation_id), self.policy_hook, self.audit_hook

    def voice_number(
        self,
        number: Union[str, int],
        trunk: str,
        *,
        password: Optional[str] = None,
        ip_address: Optional[str] = None,
        correlation_id: Optional[str] = None,
        journal_hook: Optional[JournalHook] = None,
    ) -> AsyncWorkflowPlan:
        if (password is None) == (ip_address is None):
            raise ValueError("provide exactly one of password or ip_address")

        async def create() -> OperationResult[Any]:
            if password is not None:
                return await self.voice.create_registration_trunk(
                    trunk, password, confirm_routing_change=True
                )  # type: ignore[return-value]
            return await self.voice.create_static_trunk(
                trunk, ip_address or "", confirm_routing_change=True
            )  # type: ignore[return-value]

        async def buy() -> OperationResult[Any]:
            return await self.numbers.buy(number, trunk=trunk, confirm_billable=True)  # type: ignore[return-value]

        cid = _id(correlation_id)
        return AsyncWorkflowPlan(
            (
                PlannedOperation("sip_trunks.create", Risk.ROUTING_CHANGE, {"trunk": trunk}),
                PlannedOperation("dids.order", Risk.BILLABLE, {"did": number, "trunk": trunk}),
            ),
            cid,
            (create, buy),
            journal_hook,
            *self._integration(cid),
        )

    def fax_number(
        self,
        number: Union[str, int],
        *,
        email: Optional[str] = None,
        account_name: Optional[str] = None,
        login: Optional[str] = None,
        password: Optional[str] = None,
        correlation_id: Optional[str] = None,
        journal_hook: Optional[JournalHook] = None,
    ) -> AsyncWorkflowPlan:
        async def buy() -> OperationResult[Any]:
            return await self.fax.buy(
                number,
                email=email,
                account_name=account_name,
                login=login,
                password=password,
                confirm_billable=True,
            )  # type: ignore[return-value]

        cid = _id(correlation_id)
        return AsyncWorkflowPlan(
            (PlannedOperation("fax.create", Risk.BILLABLE, {"did": number, "email": email}),),
            cid,
            (buy,),
            journal_hook,
            *self._integration(cid),
        )

    def onboard_enterprise_fax(
        self,
        number: Union[str, int],
        *,
        group: str,
        group_name: str,
        login: str,
        password: str,
        first_name: str,
        email: Optional[str] = None,
        correlation_id: Optional[str] = None,
        journal_hook: Optional[JournalHook] = None,
    ) -> AsyncWorkflowPlan:
        async def group_call() -> OperationResult[Any]:
            return await self.enterprise.create_group(
                group, group_name, confirm_routing_change=True
            )  # type: ignore[return-value]

        async def user_call() -> OperationResult[Any]:
            return await self.enterprise.create_user(
                login=login,
                password=password,
                group=group,
                first_name=first_name,
                email=email,
                confirm_routing_change=True,
            )  # type: ignore[return-value]

        async def did_call() -> OperationResult[Any]:
            return await self.enterprise.buy(number, group=group, confirm_billable=True)  # type: ignore[return-value]

        async def permission_call() -> OperationResult[Any]:
            return await self.enterprise.set_permission(
                login=login,
                number=number,
                allow_send=True,
                allow_inbound_list=True,
                allow_outbound_list=True,
                confirm_routing_change=True,
            )  # type: ignore[return-value]

        operations = (
            PlannedOperation("enterprise_fax.create_group", Risk.ROUTING_CHANGE, {"group": group}),
            PlannedOperation("enterprise_fax.create_user", Risk.ROUTING_CHANGE, {"login": login}),
            PlannedOperation("enterprise_fax.create", Risk.BILLABLE, {"did": number}),
            PlannedOperation(
                "enterprise_fax.set_permission",
                Risk.ROUTING_CHANGE,
                {"login": login, "did": number},
            ),
        )
        cid = _id(correlation_id)
        return AsyncWorkflowPlan(
            operations,
            cid,
            (group_call, user_call, did_call, permission_call),
            journal_hook,
            *self._integration(cid),
        )

    def send_enterprise_fax(
        self,
        *,
        from_number: Union[str, int],
        to: Union[str, int],
        files: Sequence[Union[str, Path]],
        correlation_id: Optional[str] = None,
        journal_hook: Optional[JournalHook] = None,
    ) -> AsyncWorkflowPlan:
        async def send() -> OperationResult[Any]:
            return await self.enterprise_reads.send(
                from_number=from_number, to=to, files=files, destination_confirmed=True
            )

        cid = _id(correlation_id)
        return AsyncWorkflowPlan(
            (
                PlannedOperation(
                    "enterprise_fax.upload_and_send",
                    Risk.DESTINATION_CONFIRMATION,
                    {"from": from_number, "to": to, "files": files},
                ),
            ),
            cid,
            (send,),
            journal_hook,
            *self._integration(cid),
        )

    def porting_draft(
        self,
        *,
        correlation_id: Optional[str] = None,
        journal_hook: Optional[JournalHook] = None,
        **fields: Any,
    ) -> AsyncWorkflowPlan:
        async def create() -> OperationResult[Any]:
            return await self.porting.create_draft(**fields, confirm_compliance=True)  # type: ignore[return-value]

        cid = _id(correlation_id)
        return AsyncWorkflowPlan(
            (PlannedOperation("lnp.create", Risk.COMPLIANCE_SENSITIVE, fields),),
            cid,
            (create,),
            journal_hook,
            *self._integration(cid),
        )

    def provision_server(
        self,
        *,
        server_type: str,
        product: str,
        email: str,
        ip_address: Optional[str] = None,
        backup_schedule: Optional[str] = None,
        correlation_id: Optional[str] = None,
        journal_hook: Optional[JournalHook] = None,
    ) -> AsyncWorkflowPlan:
        state: dict[str, int] = {}

        async def create() -> OperationResult[Any]:
            result = await self.servers.provision(
                server_type=server_type, product=product, email=email, confirm_billable=True
            )
            assert isinstance(result, OperationResult) and isinstance(result.value, int)
            state["server_id"] = result.value
            return result

        arguments = {
            "server_type": server_type,
            "product": product,
            "email": email,
            "next_ip": ip_address,
            "next_backup_schedule": backup_schedule,
        }
        operations = [PlannedOperation("servers.create", Risk.BILLABLE, arguments)]
        calls: list[AsyncCall] = [create]
        if ip_address is not None:

            async def add_ip() -> Any:
                return await self.servers.add_ip(
                    state["server_id"], ip_address, confirm_routing_change=True
                )

            operations.append(
                PlannedOperation("servers.add_ip", Risk.ROUTING_CHANGE, {"ip": ip_address})
            )
            calls.append(add_ip)
        if backup_schedule is not None:

            async def schedule() -> Any:
                return await self.servers.schedule_backups(
                    state["server_id"], backup_schedule, confirm_routing_change=True
                )

            operations.append(
                PlannedOperation(
                    "servers.manage_backup_schedule",
                    Risk.ROUTING_CHANGE,
                    {"schedule": backup_schedule},
                )
            )
            calls.append(schedule)
        cid = _id(correlation_id)
        return AsyncWorkflowPlan(
            tuple(operations), cid, tuple(calls), journal_hook, *self._integration(cid)
        )
