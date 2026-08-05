# Framework recipes

Create one long-lived client per process or application lifespan. Do not create a new HTTP client for
every request, and never expose QuestBlue credentials to a browser.

## FastAPI

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from questblue import AsyncQuestBlue


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncQuestBlue() as client:
        app.state.questblue = client
        yield


app = FastAPI(lifespan=lifespan)


@app.get("/telephony/balance")
async def balance(request: Request):
    return await request.app.state.questblue.account.balance()
```

## Django

Create a process-level `QuestBlue` service object, close it during worker shutdown, and call it from a
view or service layer. Keep credentials in the deployment secret store rather than Django settings
committed to source control.

```python
from questblue import QuestBlue

questblue = QuestBlue()


def current_balance():
    return questblue.account.balance()
```

## Celery and other workers

Create the client after the worker process forks. Pass IDs and filenames into tasks—not client
objects, credentials, full fax documents, or LNP payloads. Use the synchronous client for ordinary
Celery tasks and close it on worker shutdown.

## Web applications and white-label portals

Place pyquestblue behind a backend-for-frontend policy layer. Authenticate the portal user, resolve
their tenant/subaccount, authorize the exact operation, apply billable/destructive confirmations,
then call the SDK. Redact payloads before logging and persist provider IDs only where required.

