"""FastAPI/Starlette request adapter with no mandatory framework dependency."""

from __future__ import annotations

from typing import Any, Optional

from ..webhooks import (
    WebhookEnvelope,
    WebhookKind,
    WebhookVerificationRequired,
    WebhookVerifier,
    parse_webhook,
)


async def parse_fastapi_request(
    request: Any,
    *,
    verifier: Optional[WebhookVerifier] = None,
    allow_unverified: bool = False,
    kind: Optional[WebhookKind] = None,
) -> WebhookEnvelope:
    """Read and parse a FastAPI/Starlette request.

    Install ``pyquestblue[fastapi]`` for FastAPI. A verifier is required unless
    the application explicitly opts into unverified development traffic.
    """

    if verifier is None and not allow_unverified:
        raise WebhookVerificationRequired(
            "provide a webhook verifier or explicitly set allow_unverified=True"
        )
    body = await request.body()
    return parse_webhook(body, headers=request.headers, verifier=verifier, kind=kind)
