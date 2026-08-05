# ADR 0001: Tenant isolation and provider credentials

- Status: Accepted
- Date: 2026-08-05
- Decision owners: pyquestblue maintainers

## Context

QuestBlue 2.3.2 authenticates with HTTP Basic credentials plus a `Security-Key`. It publishes no
reseller hierarchy, delegated token, credential scope, general role, tenant-owner field, or
cross-account inventory transfer. A white-label portal must therefore not infer that provider
authentication supplies end-user identity or tenant authorization.

## Decision

Provider credentials are backend-only secrets. Browser and mobile clients authenticate only to the
white-label application and never receive a QuestBlue username, password, Security-Key, raw Basic
header, or a directly usable provider URL.

Each application tenant has an explicit immutable binding to a provider-account reference. The
binding stores a secret-manager reference, not plaintext credentials. Every job, webhook, cache key,
resource binding, usage record, and audit event carries the internal tenant ID. Authorization occurs
before creating or selecting a QuestBlue client and before every billable, compliance-sensitive, or
destructive operation.

The application uses separate provider credentials per tenant/subaccount if QuestBlue supports
them. If only shared account credentials are available, isolation is enforced in the control plane:

- resource identifiers are bound to exactly one tenant and ownership is checked before use;
- tenant-scoped repositories require a tenant key and deny unscoped queries;
- caches and idempotency keys include tenant ID and operation identity;
- queues carry signed internal envelopes with tenant ID, actor, policy decision, and correlation ID;
- logs and transport hooks exclude credentials, query values, and content payloads;
- secret access and mutations create immutable audit records;
- credential rotation is atomic and does not rewrite historical audit data.

Provider callbacks enter a quarantined ingestion boundary. They are verified by application-owned
controls, durably stored, mapped to a tenant using pre-established resource bindings, and only then
dispatched. Payload data is never trusted to choose a credential or tenant by itself.

## Consequences

The core SDK remains stateless and multi-tenant-framework neutral. A separate optional control-plane
package may define ports and workflow primitives but cannot weaken the application authorization
boundary. Applications need a database, secret manager, identity provider, durable queue, and audit
store. Shared provider credentials reduce upstream isolation and must be documented as residual risk.

No “impersonate tenant,” “act as customer,” or delegated-access API will be added until QuestBlue
publishes or contractually supplies the corresponding semantics. Provider capability answers may
lead to a superseding ADR, not silent changes to this boundary.

## Rejected alternatives

- Sending QuestBlue credentials to a browser: exposes account-wide authority and cannot enforce RBAC.
- Treating a DID, trunk name, email, or callback payload as tenant identity: identifiers can be
  reassigned, malformed, or attacker-controlled.
- One global client hidden behind UI checks only: background jobs and internal calls could bypass UI
  policy and cross tenant boundaries.
- Building billing directly from transient callbacks: the callback contract lacks delivery and
  ordering guarantees and is not an authoritative rated ledger.
