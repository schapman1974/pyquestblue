# pyquestblue

A modern, typed Python SDK for the [QuestBlue telecommunications API](https://docs.questblue.com/).
It supports synchronous and asynchronous applications and provides resource-oriented access to the
full documented QuestBlue 2.3.2 surface: accounts, voice and international DIDs, SIP trunks, SMS/MMS,
10DLC, Fax.Pro, iFax Enterprise, reports, number portability, and VoIP servers.

> Status: **stable 1.1**. All 103 pinned QuestBlue 2.3.2 operations have typed sync/async coverage;
> production contract verification remains explicitly credential-gated.

Versioned, searchable documentation is published at
[schapman1974.github.io/pyquestblue](https://schapman1974.github.io/pyquestblue/).

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

The simple facade accepts normal Python values—no request-model imports required:

```python
from questblue import SimpleQuestBlue

with SimpleQuestBlue() as qb:
    balance = qb.account.balance()
    numbers = qb.numbers.search(zip_code="27513", limit=5)
    calls = qb.reports.calls(period="today")
```

Search only returns candidates; it never purchases one. Billable and routing operations require an
explicit confirmation:

```python
with SimpleQuestBlue() as qb:
    plan = qb.numbers.buy(
        "+1 919 555 0100",
        trunk="main",
        dry_run=True,
    )

    purchased = qb.numbers.buy(
        "+1 919 555 0100",
        trunk="main",
        confirm_billable=True,
    )
    print(purchased.raw)  # original typed QuestBlue response
```

Send a consented SMS and wait for its provider status:

```python
with SimpleQuestBlue() as qb:
    sent = qb.messages.send(
        from_number="+1 919 555 0100",
        to="+1 919 555 0101",
        text="Your service is ready",
        recipient_opted_in=True,
    )
    status = qb.messages.wait_for_delivery(sent.identifiers["message_id"], attempts=5, interval=1.0)
```

Multi-step provisioning is inspectable before execution and keeps a correlated step journal:

```python
events = []

with SimpleQuestBlue() as qb:
    workflow = qb.workflows.voice_number(
        "+1 919 555 0100",
        "main",
        password="generated-secret",
        correlation_id="order-42",
        journal_hook=events.append,
    )
    print(workflow.operations)
    result = workflow.execute(confirm_routing_change=True, confirm_billable=True)
```

Async applications use the same helpers and workflow names:

```python
from questblue import AsyncSimpleQuestBlue

async with AsyncSimpleQuestBlue() as qb:
    inventory = await qb.numbers.list(per_page=200)
```

Use [`docs/simple-api.md`](docs/simple-api.md) for the complete helper guide and
[`docs/simple-api-contract.md`](docs/simple-api-contract.md) for the helper-to-provider mapping.
The lower-level typed API remains available through `QuestBlue`, `simple.raw`, or a service's `.raw`
property; see the [API reference](docs/api-reference.md) when you need exact provider control.

## Resource map

| Simple service | Common helpers |
| --- | --- |
| `qb.account` | `balance`, `details`, `rates`, alert/callback/refill configuration |
| `qb.numbers` | `search`, `list`, `buy`, `configure`, `move_to_fax`, `release` |
| `qb.international_numbers` | `countries`, `cities`, `list`, `buy`, `configure`, `release` |
| `qb.voice` | trunk listing/status, create/configure/delete trunk, caller blocking |
| `qb.messages` | `send`, `history`, delivery waiting, carrier and off-net helpers |
| `qb.dlc` | brand and campaign reads and lifecycle helpers |
| `qb.fax` | `search`, `list`, `buy`, `configure`, `send`, email access, release |
| `qb.enterprise_fax` | number, group, user, permission, upload, and send helpers |
| `qb.reports` | call/fax history, downloads, and CSV exports |
| `qb.porting` | portability checks, listing, and draft-only LNP creation |
| `qb.servers` | server provisioning, IP, backup, restore, and release helpers |
| `qb.workflows` | voice/fax onboarding, enterprise fax, LNP draft, and server plans |

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

- Every push and pull request is tested on Python 3.10 through 3.14.
- Publishing a GitHub Release triggers **Publish to PyPI**.
- Publishing uses a PyPI API token stored as an encrypted secret in the protected `pypi` GitHub
  environment. Build-provenance attestations continue to use GitHub OIDC.

Before the first release, add `PYPI_API_TOKEN` to the `pypi` GitHub environment. Never place the
token in source, workflow files, command-line arguments, issue comments, or chat messages.

## White-label platform direction

The SDK is intentionally UI-framework neutral so it can power a fully rebranded customer portal.
That portal should sit behind your own backend rather than exposing QuestBlue credentials in a
browser. The major platform layers will be tenant/customer mapping, roles and permissions, branded
catalog and pricing, ordering/provisioning workflows, usage and billing, audit logs, webhook/event
processing, and support tooling. The evidence-backed
[`white-label capability analysis`](docs/white-label.md),
[`tenant-isolation ADR`](docs/adr/0001-tenant-isolation.md), and
[`follow-on backlog`](docs/white-label-backlog.md) define what belongs in the SDK, an optional
control plane, or the application. See [`ROADMAP.md`](ROADMAP.md) for the staged build-out.

## Security

Never expose QuestBlue credentials to frontend code or commit them to source control. Use scoped
secrets in a backend service and rotate them if they are disclosed. Please report SDK security issues
privately to the repository owner.

## License

MIT
