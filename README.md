# pyquestblue

A modern, typed Python SDK for the [QuestBlue telecommunications API](https://docs.questblue.com/).
It supports synchronous and asynchronous applications and provides resource-oriented access to the
full documented QuestBlue 2.3.2 surface: accounts, voice and international DIDs, SIP trunks, SMS/MMS,
10DLC, Fax.Pro, iFax Enterprise, reports, number portability, and VoIP servers.

> Status: **0.1 alpha**. The transport and complete endpoint map are ready. Rich request/response
> models and live-account contract tests are the next development layer.

## Install

```bash
pip install pyquestblue
```

For local development:

```bash
git clone https://github.com/schapman1974/pyquestblue.git
cd pyquestblue
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
```

## Quick start

QuestBlue uses HTTP Basic authentication plus a `Security-Key` header. Credentials can be passed
directly or loaded from `QUESTBLUE_USERNAME`, `QUESTBLUE_PASSWORD`, and
`QUESTBLUE_SECURITY_KEY`.

```python
from questblue import DIDAvailabilityRequest, DIDType, QuestBlue

with QuestBlue("username", "password", "security-key") as qb:
    balance = qb.account.balance()
    available = qb.dids.available(
        DIDAvailabilityRequest(did_type=DIDType.LOCAL, zip=27513, total_list=10)
    )
    trunks = qb.sip_trunks.list(per_page=100)
```

Send an SMS/MMS:

```python
result = qb.sms.send(
    did=15551234567,
    did_to=15557654321,
    msg="Hello from pyquestblue",
    file_url=["https://example.com/image.png"],
)
```

Retrieve call history:

```python
calls = qb.reports.call_history(
    period="thismonth",
    trunk=["primary", "backup"],
    timezone="America/New_York",
    per_page=5000,
)
```

Async applications use the same resource layout:

```python
from questblue import AsyncQuestBlue, DIDListRequest

async with AsyncQuestBlue() as qb:
    inventory = await qb.dids.list(DIDListRequest(per_page=200))
```

Typed models preserve new upstream fields instead of dropping them, and paginators offer both item
iteration and raw page access:

```python
from questblue import QuestBlueModel, model_parser


class CallRecord(QuestBlueModel):
    call_id: str


records = qb.paginate(
    "/callhistory",
    params={"period": "today", "per_page": 500},
    item_parser=model_parser(CallRecord),
)
for record in records:
    print(record.call_id)
```

See [`docs/modeling.md`](docs/modeling.md) for validation, forward compatibility, raw payloads, and
custom pagination selectors.

See [`docs/transport.md`](docs/transport.md) for retry safety, per-request controls, raw responses,
transport errors, structured logging, and OpenTelemetry hooks.

See [`docs/account.md`](docs/account.md) for typed balance, rates, refill, alert, and callback
operations, including explicit safeguards around billable balance changes.

See [`docs/dids.md`](docs/dids.md) for typed Voice DID discovery, ordering, E911/DLDA configuration,
pagination, fraud validation, and destructive-operation safeguards.

See [`docs/international-dids.md`](docs/international-dids.md) for country/city discovery,
international inventory pagination, ordering, routing updates, and release safeguards.

See [`docs/sip-trunks.md`](docs/sip-trunks.md) for registration/static trunks, routing controls,
status troubleshooting, channel options, and blocked callers.

Every resource method accepts the parameter names from QuestBlue's API documentation. List values
are serialized as comma-separated values, matching QuestBlue's generated Node client. For an API
addition that has not yet received a convenience method, the authenticated transport remains usable:

```python
result = qb.request("GET", "/new-endpoint", params={"example": "value"})
```

## Resource map

| SDK resource | QuestBlue areas |
| --- | --- |
| `qb.account` | balance, details, rates, refill, alerts, callbacks |
| `qb.dids` | inventory, availability, ordering, configuration, fraud validation |
| `qb.international_dids` | countries, cities, inventory, ordering |
| `qb.sip_trunks` | trunks, registration status, blocked callers |
| `qb.sms` | SMS/MMS, settings, history, delivery, off-net orders, carrier checks |
| `qb.dlc` | 10DLC brands and campaigns |
| `qb.fax` | Fax.Pro inventory, sending, email permissions |
| `qb.enterprise_fax` | iFax Enterprise accounts, groups, users, permissions, files |
| `qb.reports` | voice CDRs, fax history, fax downloads |
| `qb.lnp` | portability checks and LNP request lifecycle |
| `qb.servers` | server inventory, IPs, upgrades, backup lifecycle |

## API coverage contract

The normalized QuestBlue OpenAPI 2.3.2 contract is pinned under [`spec/`](spec/). A deterministic
coverage report under [`coverage/`](coverage/) maps every upstream HTTP operation to its SDK method,
sync/async availability, request/response model status, unit tests, and documentation. CI rejects
missing or extra operations, broken sync/async parity, or a stale report.

```bash
python scripts/api_coverage.py --check
python scripts/update_openapi.py --check  # compares against the live QuestBlue contract
```

## Errors and retries

The client retries safe reads after connection failures, HTTP 408/409/429 responses, and server
errors with bounded exponential backoff. Mutating and potentially billable requests are never
retried automatically. QuestBlue's documented HTTP 206 error responses are raised as exceptions.
Catch `QuestBlueAPIError` for API failures or a narrower transport class. The complete contract is
documented in [`docs/transport.md`](docs/transport.md).

## Publishing

- Every push and pull request is tested on Python 3.9 through 3.13.
- **Publish to TestPyPI** is a manual GitHub Actions workflow.
- Publishing a GitHub Release triggers **Publish to PyPI**.
- Both publishing workflows use PyPI Trusted Publishing (OIDC), so repository API tokens are not
  stored as secrets.

Before the first release, create `testpypi` and `pypi` GitHub environments and configure this
repository as a Trusted Publisher on each package index. TestPyPI and PyPI require separate
publisher registrations.

## White-label platform direction

The SDK is intentionally UI-framework neutral so it can power a fully rebranded customer portal.
That portal should sit behind your own backend rather than exposing QuestBlue credentials in a
browser. The major platform layers will be tenant/customer mapping, roles and permissions, branded
catalog and pricing, ordering/provisioning workflows, usage and billing, audit logs, webhook/event
processing, and support tooling. See [`ROADMAP.md`](ROADMAP.md) for the staged build-out.

## Security

Never expose QuestBlue credentials to frontend code or commit them to source control. Use scoped
secrets in a backend service and rotate them if they are disclosed. Please report SDK security issues
privately to the repository owner.

## License

MIT
