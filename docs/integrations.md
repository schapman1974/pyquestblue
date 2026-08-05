# Webhooks and integration boundaries

QuestBlue 2.3.2 publishes two JSON callback shapes: inbound SMS/MMS messages and outbound message
delivery status. Both are modeled by pyquestblue, and fields added by QuestBlue remain available in
`event.extra_fields`.

## Authentication and delivery contract

The public contract says to return HTTP 200 after receiving a callback. It does **not** document a
signature header, authentication algorithm, retry schedule, ordering guarantee, event identifier,
or duplicate-delivery guarantee. These behaviors remain unknown as of August 5, 2026. Accordingly:

- `parse_webhook()` parses data but reports `verified=False` unless a verifier was supplied.
- Framework helpers reject requests without an application verifier by default.
- `WebhookEnvelope.fingerprint` is a SHA-256 digest of the exact body for deduplication; the body is
  excluded from the envelope representation.
- Persist or durably enqueue an accepted event before returning 200. Treat callbacks as potentially
  duplicated and out of order until QuestBlue confirms otherwise.

A verifier is an application callback that receives headers and exact body bytes and raises when a
request is not trusted. Because QuestBlue defines no native signature, use controls you own, such as
mTLS at the edge, an allowlisted private ingress, or a secret enforced by your reverse proxy. Do not
describe these controls as QuestBlue signature verification.

```python
from questblue import parse_webhook


def receive(request_body):
    envelope = parse_webhook(request_body)
    if already_processed(envelope.fingerprint):
        return 200
    durably_enqueue(envelope)
    return 200
```

## FastAPI and Django

Framework support is optional:

```bash
pip install 'pyquestblue[fastapi]'
# or
pip install 'pyquestblue[django]'
```

```python
from fastapi import FastAPI, Request, Response
from questblue.integrations.fastapi import parse_fastapi_request

app = FastAPI()


@app.post("/hooks/questblue")
async def questblue_hook(request: Request) -> Response:
    envelope = await parse_fastapi_request(request, verifier=verify_at_ingress)
    await queue.put(envelope)
    return Response(status_code=200)
```

The Django equivalent is `questblue.integrations.django.parse_django_request()`. Both adapters pass
only headers and exact body bytes to the verifier and do not log either value. For local fixtures,
`allow_unverified=True` is an explicit opt-out; never enable it on a public endpoint.

## White-label architecture

Keep QuestBlue credentials in a backend service, with one client boundary per tenant/account. The
SDK remains intentionally independent from application storage and queues:

| Concern | Recommended boundary |
| --- | --- |
| Observability | `transport_hook`; events contain method/path/status and allowlisted headers only |
| Webhook ingestion | Verify, fingerprint, durably enqueue, acknowledge; process asynchronously |
| Caching | Cache safe reads in the service layer, keyed by tenant plus sanitized request identity |
| Rate limiting | Apply tenant and global budgets before SDK calls; honor SDK 429 exceptions |
| CRM/support | Consume normalized domain events from a queue, not raw transport hooks |
| Billing | Reconcile typed reports to an immutable internal ledger; never infer charges from callbacks |
| Exports | Use report `export_rows()` and perform PII access control in the application |
| Automation | Use explicit workflows with audit records and approvals for billable/destructive calls |

Transport hooks intentionally receive no query values, request bodies, response bodies,
authorization header, or Security-Key. Webhook payloads necessarily contain customer content; send
them only to handlers designed for that data classification and redact them from logs and errors.
