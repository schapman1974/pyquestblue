# Contract testing

QuestBlue does not document a sandbox mode. pyquestblue therefore separates offline confidence from
production verification and never treats an ordinary customer account as a test sandbox.

## Safety classes

| Class | CI policy | Required controls |
| --- | --- | --- |
| Unit | Every push/PR | No network; synthetic values |
| Recorded | Every push/PR | Sanitized deterministic JSON fixtures only |
| Live read-only | Weekly/manual protected workflow | Dedicated subaccount, environment approval, explicit acknowledgment |
| Live reversible | Manual only | Capture before-state, rollback in `finally`, dedicated resource |
| Live billable | Manual only | Cost approval, exact resource scope, cleanup where possible |
| Live compliance-sensitive | Manual only | Authorized synthetic/legal test identity and compliance review |
| Live destructive | Manual only | Backup, exact-ID confirmation, recovery plan, human approval |

The machine-readable status is published in
[`contracts/verification-matrix.json`](../contracts/verification-matrix.json). `verified` means the
listed evidence currently runs in CI; every live row remains explicitly unverified until a protected
run succeeds with credentials. A green ordinary CI run does not imply live-provider verification.

## Recorded fixtures

Fixtures under `tests/fixtures/contracts/` contain only synthetic values. They are parsed directly by
public response models in `tests/test_recorded_contracts.py`. `scripts/check_contract_fixtures.py`
rejects sensitive key names, non-example email domains, non-fictional North American numbers,
public IP addresses, and missing matrix evidence. CI runs this check before the test suite.

When recording a new response:

1. Capture locally; never upload the raw response.
2. Replace account/customer identifiers, names, phones, emails, IPs, URLs, message bodies, file IDs,
   and request IDs with documented synthetic values.
3. Remove authentication headers and any secret/token/password field entirely.
4. Minimize the fixture to fields needed to preserve the response shape.
5. Run `python scripts/check_contract_fixtures.py` and inspect the diff manually.

## Live read-only workflow

The weekly workflow uses the protected GitHub environment `questblue-live-readonly`. Configure that
environment with approval rules and these secrets: `QUESTBLUE_LIVE_USERNAME`,
`QUESTBLUE_LIVE_PASSWORD`, `QUESTBLUE_LIVE_SECURITY_KEY`, and `QUESTBLUE_LIVE_BASE_URL`. Credentials
must belong to a dedicated least-privilege subaccount containing no customer PII. The URL gate
accepts only HTTPS on `api.questblue.com` or `api2.questblue.com`.

No live workflow uploads artifacts or prints payloads. The read-only suite checks account response
shapes and inventory only. Billable, compliance-sensitive, and destructive tests are deliberately
excluded from schedules and require a separately reviewed manual procedure.

The DID lifecycle test requires the exact
`QUESTBLUE_RUN_LIVE_BILLABLE_DID=YES_I_ACCEPT_PRODUCTION_BILLING` acknowledgment plus the dedicated
live-subaccount settings and ZIP. It is never included in a scheduled workflow.
