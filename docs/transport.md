# HTTP transport contract

`QuestBlue` and `AsyncQuestBlue` intentionally share the same request behavior. The transport is
conservative because many QuestBlue operations provision, send, refill, or otherwise bill for a
service.

## Retry safety

Only `GET`, `HEAD`, and `OPTIONS` requests are eligible for automatic retry. Retryable responses
are HTTP 408, 409, 429, and 5xx, plus connection and timeout failures. The client honors a numeric
or HTTP-date `Retry-After` value, capped at 60 seconds, and otherwise uses capped exponential
backoff.

`POST`, `PUT`, `PATCH`, and `DELETE` requests are always attempted exactly once, even if the client
or request has a nonzero retry count. This protects ordering, sending, refill, and destructive
operations when the first result is uncertain. QuestBlue API 2.3.2 does not document an
idempotency header or guarantee, so the SDK does not invent one or offer an unsafe mutation-retry
switch. Callers can attach a provider-confirmed future header through `headers`, but that alone does
not enable mutation retries.

## Request-level controls

The low-level `request` method supports controls for an individual call:

```python
response = client.request(
    "GET",
    "/callhistory",
    params={"page": 1},
    headers={"X-Correlation-ID": "billing-import-42"},
    timeout=15.0,
    max_retries=1,
    raw_response=True,
)

print(response.status_code, response.headers.get("x-request-id"))
payload = response.json()
```

`max_retries=0` disables retries for a read. `timeout` accepts seconds or an `httpx.Timeout` object.
`raw_response=True` returns the buffered `httpx.Response`; unsuccessful responses still raise a
typed exception whose `response` attribute provides the same access. `Authorization` and
`Security-Key` cannot be overridden.

Async cancellation is not converted into a connection error and is never retried. The original
`asyncio.CancelledError` propagates to the task owner.

## Errors and decoding

- `QuestBlueAuthenticationError`: HTTP 401 or 403
- `QuestBlueRateLimitError`: HTTP 429 after safe retries are exhausted
- `QuestBlueServerError`: HTTP 5xx after safe retries are exhausted
- `QuestBlueAPIError`: other HTTP errors and QuestBlue's application-error HTTP 206
- `QuestBlueTimeoutError`: an HTTPX timeout; subclass of `QuestBlueConnectionError`
- `QuestBlueConnectionError`: another HTTPX request failure
- `QuestBlueResponseError`: a successful response declared as JSON but containing malformed JSON

An empty successful body decodes to `None`. Binary media returns `bytes`, and other non-JSON media
returns text.

## Structured logging and tracing

The `questblue.transport` logger emits DEBUG records with a structured dictionary in the
`questblue` record attribute. Pass `transport_hook` to receive the same `TransportEvent` values and
bridge them to OpenTelemetry or another telemetry system:

```python
from opentelemetry import trace
from questblue import QuestBlue, TransportEvent


def record_transport(event: TransportEvent) -> None:
    attributes = {
        "questblue.method": event.method,
        "questblue.path": event.path,
        "questblue.attempt": event.attempt,
    }
    if event.status_code is not None:
        attributes["http.response.status_code"] = event.status_code
    trace.get_current_span().add_event(event.name, attributes)


client = QuestBlue(transport_hook=record_transport)
```

Events contain the HTTP method, URL path, attempt data, status, request ID, and redacted headers.
They never contain URL query values, request/response bodies, credentials, SMS content, fax data,
or arbitrary custom-header values. A telemetry-hook failure is logged and does not change request
behavior.
