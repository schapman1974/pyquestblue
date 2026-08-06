"""Application-owned policy, context, and audit contracts for white-label embedding."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Callable, Dict, FrozenSet, Mapping, Optional, Union, cast

from ._results import PlannedOperation, Risk, WorkflowStatus, json_safe


@dataclass(frozen=True)
class OperationContext:
    """Opaque application metadata; pyquestblue never sends it to QuestBlue."""

    correlation_id: Optional[str] = None
    tenant_id: Optional[str] = None
    actor_id: Optional[str] = None
    reason: Optional[str] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def with_correlation(self, correlation_id: str) -> OperationContext:
        return replace(self, correlation_id=correlation_id)

    def to_dict(self) -> Dict[str, Any]:
        return cast(Dict[str, Any], json_safe(self))


@dataclass(frozen=True)
class PolicyRequest:
    """Versioned pre-execution request presented to application policy."""

    operation: PlannedOperation
    context: OperationContext
    version: str = "1"

    def to_dict(self) -> Dict[str, Any]:
        return cast(Dict[str, Any], json_safe(self))


@dataclass(frozen=True)
class PolicyDecision:
    """Explicit authorization and optional confirmation grants from the application."""

    allowed: bool = False
    confirmed_risks: FrozenSet[Risk] = frozenset()
    reason: Optional[str] = None


PolicyHook = Callable[[PolicyRequest], Optional[Union[bool, PolicyDecision]]]


@dataclass(frozen=True)
class AuditEvent:
    """Versioned, JSON-safe workflow event suitable for an audit or queue hook."""

    operation: str
    risk: Risk
    status: WorkflowStatus
    context: OperationContext
    identifiers: Mapping[str, str] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    recovery: Optional[str] = None
    handoff: Optional[str] = None
    version: str = "1"

    def to_dict(self) -> Dict[str, Any]:
        return cast(Dict[str, Any], json_safe(self))


AuditHook = Callable[[AuditEvent], Any]


def policy_decision(value: Optional[Union[bool, PolicyDecision]]) -> PolicyDecision:
    """Normalize policy output; missing output denies by default."""
    if isinstance(value, PolicyDecision):
        return value
    return PolicyDecision(allowed=value is True)
