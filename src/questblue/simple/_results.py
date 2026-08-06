"""JSON-safe results and plans for simple operations and workflows."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Generic, Iterator, Mapping, Optional, Sequence, Tuple, TypeVar, cast

from pydantic import BaseModel

ValueT = TypeVar("ValueT")
_SENSITIVE_KEYS = frozenset(
    ("authorization", "body", "content", "message", "password", "security_key")
)


class Risk(str, Enum):
    """Risk classifications applied to every facade operation."""

    READ_ONLY = "read-only"
    ROUTING_CHANGE = "routing-change"
    CONSENT_REQUIRED = "consent-required"
    DESTINATION_CONFIRMATION = "destination-confirmation"
    COMPLIANCE_SENSITIVE = "compliance-sensitive"
    BILLABLE = "billable"
    DESTRUCTIVE = "destructive"
    UNCERTAIN_OUTCOME = "uncertain-outcome"


class WorkflowStatus(str, Enum):
    """Outcome of an attempted multi-step workflow."""

    PLANNED = "planned"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"
    UNCERTAIN = "uncertain"


def _sensitive(key: str) -> bool:
    lowered = key.casefold().replace("-", "_")
    return (
        lowered in _SENSITIVE_KEYS
        or lowered.endswith(("_body", "_content", "_password"))
        or "secret" in lowered
        or "token" in lowered
    )


def json_safe(value: Any, *, redact: bool = True) -> Any:
    """Convert SDK values into JSON-compatible primitives with safe redaction."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Enum):
        return json_safe(value.value, redact=redact)
    if isinstance(value, Path):
        return "[REDACTED]" if redact else str(value)
    if isinstance(value, (bytes, bytearray, memoryview)):
        return "[REDACTED]" if redact else bytes(value).hex()
    if isinstance(value, BaseModel):
        return json_safe(value.model_dump(mode="json", by_alias=True), redact=redact)
    if is_dataclass(value) and not isinstance(value, type):
        return json_safe(asdict(value), redact=redact)
    if isinstance(value, Mapping):
        return {
            str(key): "[REDACTED]"
            if redact and _sensitive(str(key))
            else json_safe(item, redact=redact)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        return [json_safe(item, redact=redact) for item in value]
    return str(value)


@dataclass(frozen=True, repr=False)
class OperationResult(Generic[ValueT]):
    """Result of one mutation, including provider evidence and warnings."""

    value: Optional[ValueT] = None
    identifiers: Mapping[str, str] = field(default_factory=dict)
    warnings: Tuple[str, ...] = ()
    raw: Any = field(default=None, repr=False)

    def to_dict(self, *, include_raw: bool = True) -> Dict[str, Any]:
        result = {
            "value": json_safe(self.value),
            "identifiers": json_safe(self.identifiers),
            "warnings": list(self.warnings),
        }
        if include_raw:
            result["raw"] = json_safe(self.raw)
        return result

    def __repr__(self) -> str:
        return f"OperationResult({self.to_dict(include_raw=False)!r})"


@dataclass(frozen=True, repr=False)
class SimpleRecord:
    """Immutable ergonomic view that retains its exact typed provider record."""

    raw: Any = field(repr=False)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.raw, name)

    def to_dict(self) -> Dict[str, Any]:
        return cast(Dict[str, Any], json_safe(self.raw))

    def __repr__(self) -> str:
        return f"SimpleRecord({self.to_dict()!r})"


@dataclass(frozen=True, repr=False)
class SimpleCollection(Sequence[ValueT], Generic[ValueT]):
    """Immutable automatically collected values plus every typed response page."""

    items: Tuple[ValueT, ...]
    raw: Tuple[Any, ...] = field(default_factory=tuple, repr=False)

    def __getitem__(self, index: Any) -> Any:
        return self.items[index]

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self) -> Iterator[ValueT]:
        return iter(self.items)

    def to_dict(self) -> Dict[str, Any]:
        return {"items": json_safe(self.items), "raw": json_safe(self.raw)}

    def __repr__(self) -> str:
        return f"SimpleCollection(items={json_safe(self.items)!r})"


@dataclass(frozen=True, repr=False)
class WorkflowStep:
    """One journaled workflow step."""

    name: str
    risk: Risk
    status: WorkflowStatus
    identifiers: Mapping[str, str] = field(default_factory=dict)
    warnings: Tuple[str, ...] = ()
    raw: Any = field(default=None, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        return cast(Dict[str, Any], json_safe(self))

    def __repr__(self) -> str:
        return f"WorkflowStep({self.to_dict()!r})"


@dataclass(frozen=True, repr=False)
class WorkflowResult(Generic[ValueT]):
    """Complete evidence for a multi-step workflow outcome."""

    status: WorkflowStatus
    value: Optional[ValueT] = None
    steps: Tuple[WorkflowStep, ...] = ()
    identifiers: Mapping[str, str] = field(default_factory=dict)
    warnings: Tuple[str, ...] = ()
    failed_step: Optional[str] = None
    uncertain_step: Optional[str] = None
    recovery: Optional[str] = None
    raw: Tuple[Any, ...] = field(default_factory=tuple, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        return cast(Dict[str, Any], json_safe(self))

    def __repr__(self) -> str:
        data = self.to_dict()
        data.pop("raw", None)
        return f"WorkflowResult({data!r})"


@dataclass(frozen=True, repr=False)
class PlannedOperation:
    """A normalized provider call that has not run."""

    name: str
    risk: Risk
    arguments: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return cast(Dict[str, Any], json_safe(self))

    def __repr__(self) -> str:
        return f"PlannedOperation({self.to_dict()!r})"


@dataclass(frozen=True, repr=False)
class OperationPlan:
    """Inspectable sequence of normalized operations requiring execution."""

    operations: Tuple[PlannedOperation, ...]

    @property
    def risks(self) -> Tuple[Risk, ...]:
        return tuple(dict.fromkeys(operation.risk for operation in self.operations))

    def to_dict(self) -> Dict[str, Any]:
        return cast(Dict[str, Any], json_safe(self))

    def __repr__(self) -> str:
        return f"OperationPlan({self.to_dict()!r})"
