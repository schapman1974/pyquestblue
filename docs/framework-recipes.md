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

The simple workflow client accepts application-owned context, policy, and audit hooks. A configured
policy must explicitly allow every operation; returning `None` or `False` denies before provider
I/O. A `PolicyDecision` may also confirm specific risk categories after the application has applied
its own authorization and consent rules:

```python
from questblue import SimpleQuestBlue
from questblue.simple import OperationContext, PolicyDecision, Risk


def authorize(request):
    allowed = owns_resource(request.context.tenant_id, request.operation)
    return PolicyDecision(allowed, frozenset({Risk.BILLABLE}) if allowed else frozenset())


client = SimpleQuestBlue(
    operation_context=OperationContext(tenant_id="tenant-42", actor_id="user-7"),
    policy_hook=authorize,
    audit_hook=audit_repository.append,
)
```

For FastAPI, build a tenant-scoped facade with `SimpleQuestBlue.wrap()` or
`AsyncSimpleQuestBlue.wrap()` after authentication and tenant resolution. For Django, do the same in
the application service layer after object-level permission checks; do not treat `tenant_id` as an
authorization credential.

Workers should receive a correlation ID and an application workflow-record ID. Recreate the opaque
context in the worker, persist every versioned `AuditEvent`, and place failures whose event has
`handoff="dead-letter"` on the application's DLQ. An uncertain mutation uses `handoff="reconcile"`:
query provider state before retrying because automatic replay could duplicate a charge. Queue
messages should carry provider IDs and secret-manager references, never credentials, message bodies,
fax bytes, or LNP bills.

A durable audit hook can write `event.to_dict()` transactionally with application workflow state.
pyquestblue deliberately supplies the hook contract but owns no database, queue, retry scheduler,
tenant repository, or cross-tenant authorization policy.
