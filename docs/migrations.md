# Migration guides

## Upgrading to 1.0

pyquestblue 1.0 requires CPython 3.10 or newer. Python 3.9 reached end of life and was removed so
the supported build and optional-integration dependency graph can receive current security fixes.

The synchronous `QuestBlue` and asynchronous `AsyncQuestBlue` clients expose matching typed
resource methods. Requests and responses use `QuestBlueModel`, which accepts provider-added fields
and preserves unknown response data in `extra_fields`. Safe reads use bounded retries for transport
errors, HTTP 408/409/429, and server errors; mutating or billable requests are not retried
automatically.

Inbound and status callbacks are parsed by the webhook helpers. QuestBlue's public 2.3.2 contract
does not specify a callback signature, retry schedule, ordering guarantee, or unique event ID, so
applications must authenticate callback ingress at their own edge and implement idempotency using
their own durable identifiers. QuestBlue does not document a sandbox; use recorded fixtures for
ordinary development and a dedicated approved subaccount for opt-in live tests.

## From raw `requests` or `httpx`

Replace hand-built authentication headers and query serialization with one `QuestBlue` client.
Replace dictionaries with request models and handle `WarningResponse` explicitly. Temporary gaps can
still use `qb.request`, but typed resource methods should be the migration target.

```python
from questblue import DIDListRequest, QuestBlue, WarningResponse

with QuestBlue() as qb:
    result = qb.dids.list(DIDListRequest(did="*0100", per_page=100))
    if isinstance(result, WarningResponse):
        raise RuntimeError(result.warning)
```

Lists are serialized as comma-separated query values, dates/enums use their documented values, and
HTTP 206 application errors raise `QuestBlueAPIError`.

## From AlexM2202/Quest-API

The legacy project centers on report scripts, global credentials, direct `requests.get` calls, and
manual page loops. Move credentials into a `QuestBlue` instance, use `CallHistoryRequest`, and replace
page loops with `qb.reports.iter_call_history`. Use `export_rows` with `csv.DictWriter` or an optional
pandas `DataFrame`. Typed records retain unknown provider fields through `extra_fields`.

## From `ekmillard/questblue-api-node`

Resource nesting maps directly: the Node reports/fax/SMS/DID areas become `qb.reports`, `qb.fax`,
`qb.sms`, and `qb.dids`. JavaScript parameter objects become Pydantic request models. Await methods on
`AsyncQuestBlue`; use ordinary calls on `QuestBlue`. Python returns `WarningResponse` unions for HTTP
202 warning shapes and raises typed exceptions for HTTP/transport failures.

Node array query values and pyquestblue list fields use the same comma-separated encoding. Python
enums are string enums, so stored literal values remain portable between implementations.
