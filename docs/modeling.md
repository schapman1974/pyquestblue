# Models and pagination

pyquestblue uses Pydantic v2 for its public request and response contract. Pydantic provides runtime
validation, JSON Schema generation, generic envelopes, and Python 3.9 compatibility. Resource
models should inherit from `QuestBlueModel` rather than directly from Pydantic's `BaseModel`.

## Forward compatibility

QuestBlue may add response fields or enum values before a new SDK release. `QuestBlueModel` uses
`extra="allow"`, so new fields remain available through normal attribute access, `model_dump()`, and
the explicit `extra_fields` mapping. `OpenStringEnum` preserves unknown string values rather than
failing an otherwise valid response.

Request models serialize with API aliases through `to_request_params()`. Do not silently discard
unknown response fields, but do not send response models back as request parameters unless the API
explicitly documents that behavior.

## Responses

Use `ResponseEnvelope[T]` for the common `{ "data": ... }` shape, `WarningResponse` for HTTP 202,
and `ErrorResponse` for application errors such as QuestBlue's documented HTTP 206 responses.
`parse_model()` returns a `ParsedResponse[T]` containing both validated data and the exact decoded
payload for troubleshooting or forward-compatible access.

Binary downloads use `BinaryResponse`, which retains bytes, content type, and an optional filename.

## Pagination

`SyncPaginator` and `AsyncPaginator` expose two views:

- Iterating the paginator yields validated items.
- Calling `.pages()` yields `Page[T]` objects with items, normalized metadata, and the raw payload.

```python
from questblue import QuestBlue, QuestBlueModel, model_parser


class CallRecord(QuestBlueModel):
    call_id: str


with QuestBlue() as qb:
    records = qb.paginate(
        "/callhistory",
        params={"period": "today", "per_page": 500},
        item_parser=model_parser(CallRecord),
    )
    for record in records:
        print(record.call_id)
```

Most QuestBlue collections use a list in `data`. For endpoints with a mapping or nested collection,
pass an `item_selector`; resource-specific convenience methods should encapsulate that selector.

## Adding a resource model

1. Derive request and response models from the pinned OpenAPI operation and examples.
2. Inherit from `QuestBlueModel` and use exact upstream aliases.
3. Use open enums for upstream strings that may gain values.
4. Validate constraints that are explicit and stable; preserve unknown values when the provider may
   expand them.
5. Add valid, invalid, unknown-field, serialization, sync, and async tests.
6. Connect the model to the resource method and regenerate `coverage/api-coverage.json`.
