"""Django request adapter with no mandatory framework dependency."""

from __future__ import annotations

from typing import Any, Mapping, Optional, cast

from ..webhooks import (
    WebhookEnvelope,
    WebhookKind,
    WebhookVerificationRequired,
    WebhookVerifier,
    parse_webhook,
)


def _headers(request: Any) -> Mapping[str, str]:
    headers = getattr(request, "headers", None)
    if headers is not None:
        return cast(Mapping[str, str], headers)
    return {
        key[5:].replace("_", "-"): str(value)
        for key, value in getattr(request, "META", {}).items()
        if key.startswith("HTTP_")
    }


def parse_django_request(
    request: Any,
    *,
    verifier: Optional[WebhookVerifier] = None,
    allow_unverified: bool = False,
    kind: Optional[WebhookKind] = None,
) -> WebhookEnvelope:
    """Read and parse a Django ``HttpRequest`` callback."""

    if verifier is None and not allow_unverified:
        raise WebhookVerificationRequired(
            "provide a webhook verifier or explicitly set allow_unverified=True"
        )
    return parse_webhook(request.body, headers=_headers(request), verifier=verifier, kind=kind)
