# pyquestblue

pyquestblue is a typed, synchronous and asynchronous Python SDK covering all 103 operations in the
pinned QuestBlue OpenAPI 2.3.2 contract.

## Install

```bash
pip install pyquestblue
```

Credentials can be passed directly or loaded from `QUESTBLUE_USERNAME`, `QUESTBLUE_PASSWORD`, and
`QUESTBLUE_SECURITY_KEY`.

## Synchronous quickstart

```python
from questblue import DIDListRequest, QuestBlue

with QuestBlue() as qb:
    balance = qb.account.balance()
    dids = qb.dids.list(DIDListRequest(per_page=100))
```

## Asynchronous quickstart

```python
from questblue import AsyncQuestBlue, DIDListRequest


async def inventory() -> None:
    async with AsyncQuestBlue() as qb:
        dids = await qb.dids.list(DIDListRequest(per_page=100))
        print(dids)
```

Start with the resource page for your API area. The transport guide covers errors, timeouts,
retries, tracing, and raw responses; the modeling guide covers forward compatibility and pagination.

