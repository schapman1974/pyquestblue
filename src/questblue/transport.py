"""Public primitives for transport configuration and observability."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable, Dict, Mapping, Optional


@dataclass(frozen=True)
class TransportEvent:
    """A content-free event emitted during an HTTP request.

    Events intentionally exclude query values and request/response bodies so they
    can be sent to structured logs or translated into OpenTelemetry span events.
    """

    name: str
    method: str
    path: str
    attempt: int
    max_attempts: int
    headers: Mapping[str, str]
    status_code: Optional[int] = None
    request_id: Optional[str] = None
    retry_delay: Optional[float] = None
    error_type: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        """Return a structured-logging-friendly representation."""
        return asdict(self)


TransportHook = Callable[[TransportEvent], None]
