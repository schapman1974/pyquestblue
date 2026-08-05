# Migration guides

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

