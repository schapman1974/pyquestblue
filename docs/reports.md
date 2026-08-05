# Reports

`qb.reports` provides typed voice CDR, fax history, and fax download operations for synchronous and
asynchronous clients. Unknown response fields remain available through each model's `extra_fields`
property so report consumers remain forward compatible.

## Voice call history

Use `qb.reports.call_history` with `CallHistoryRequest`. It models named periods, Unix timestamp
ranges, `last_id`, one or more trunks, DID, call direction, country, IANA timezone, successful-only,
summary, call-ID, fax-stat, page, and `per_page` options. Timestamp ranges are checked against the
documented one-month maximum. When `last_id` is supplied, QuestBlue ignores `period` as documented.

Detailed rows parse as `CallDetailRecord`; summary rows parse as `CallSummaryRecord`. The SDK also
models the pagination metadata returned by the live API even though the pinned response schema
only shows `total`.

```python
from questblue import CallHistoryRequest, OnOff, Period

request = CallHistoryRequest(
    period=Period.THIS_MONTH,
    trunk=["primary", "backup"],
    timezone="America/New_York",
    get_id=OnOff.ON,
    per_page=5000,
)
for record in qb.reports.iter_call_history(request):
    print(record.call_type)
```

The async equivalent is `async for record in qb.reports.iter_call_history(request)`.

## Fax history and downloads

`qb.reports.fax_history` accepts DID lists, Fax.Pro or Enterprise service, inbound/outbound
direction, fax ID, today/yesterday or a pair of timezone-aware datetimes, page, and `per_page`.
`qb.reports.iter_fax_history` traverses every reported page.

`qb.reports.download_fax(fax_id)` returns a `FaxDownloadResponse`. QuestBlue returns the document
inside JSON as base64 rather than as a streamed HTTP body. `response.data.iter_bytes()` decodes that
payload incrementally, and `qb.reports.download_fax_to(fax_id, file)` writes chunks directly to a
binary file object. This avoids creating a second full decoded copy in memory, although the encoded
JSON response must still be buffered by the transport.

```python
with open("fax.pdf", "wb") as destination:
    qb.reports.download_fax_to(718736089913419320182796451, destination)
```

Fax documents and report records can contain personal and billing data. Avoid logging request
models, response bodies, phone numbers, call IDs, fax IDs, and decoded content. Validate access at
the application boundary before exposing exports or downloads.

## CSV and pandas

`export_rows(response)` returns ordinary dictionaries. They can be passed directly to
`csv.DictWriter`; pandas users can call `pandas.DataFrame(export_rows(response))` without making
pandas a pyquestblue dependency. See [`examples/reports_export.py`](../examples/reports_export.py)
for an executable standard-library CSV flow.

## Operation map

| Operation | SDK method |
| --- | --- |
| `GET /callhistory` | `qb.reports.call_history` |
| `GET /faxhistory` | `qb.reports.fax_history` |
| `GET /faxdownload` | `qb.reports.download_fax` |

