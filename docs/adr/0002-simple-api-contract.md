# ADR 0002: Simple API and workflow contract

- Status: Accepted
- Date: 2026-08-05
- Decision owners: pyquestblue maintainers

## Context

The stable 1.0 API intentionally mirrors all 103 QuestBlue 2.3.2 operations with explicit Pydantic
request and response models. That surface is complete and appropriate when callers need exact
provider control, but common tasks require users to learn model names, provider enum spellings,
warning unions, and which calls must be combined.

pyquestblue needs an easier entry point without weakening validation, hiding charges, inventing
provider guarantees, or breaking the typed API. The simple layer must also work behind a white-label
backend without pretending to supply authentication, tenant isolation, pricing, billing, or durable
workflow storage.

## Decision

### Additive facade

Add a `questblue.simple` package exporting `SimpleQuestBlue` and `AsyncSimpleQuestBlue`. The existing
`QuestBlue` and `AsyncQuestBlue` clients remain unchanged and authoritative.

The facade groups methods by user intent:

- `account`
- `numbers` and `international_numbers`
- `voice`
- `messages`
- `dlc`
- `fax` and `enterprise_fax`
- `reports`
- `porting`
- `servers`
- `workflows`

Constructing a simple client with credentials creates and owns the matching typed client. A
`wrap(client)` constructor borrows an existing typed client and does not close it. Context-manager
exit closes only an owned client. The `raw` property exposes the exact borrowed or owned typed client.

### Explicit primitive inputs

Public helpers use named parameters rather than accepting an unrestricted `**kwargs` mapping. They
accept ordinary Python values such as strings, integers, `date`/`datetime`, `PathLike`, bytes, and
sequences. Callers may also pass the corresponding public enum where useful. Internally every helper
constructs the existing typed request model, which remains the final validation and serialization
authority.

Normalization is deterministic:

- telephone strings may contain a leading `+` and visual separators; extensions and ambiguous
  international forms are rejected;
- enum strings match documented values or an explicitly documented friendly alias, never fuzzy
  guesses;
- a scalar or non-string sequence is normalized to a new list without mutating caller data;
- timezone-aware datetimes remain absolute, dates remain dates, and naive datetimes are rejected
  where an instant is required;
- paths are expanded only to an explicit local path, checked with the existing size/type validators,
  and never included in logs or events;
- `None` means “not supplied”; empty strings and empty collections are not silently converted to
  `None`.

No helper silently drops an unknown argument or provider field.

### Return contract

The facade removes request-model construction, not useful result information:

- scalar projections return the natural value, such as `Decimal` for a balance or `str` for a
  message ID;
- collections return simple immutable records, each retaining the original typed record through a
  `raw` attribute;
- individual mutations return `OperationResult[T]` with `value`, provider identifiers, warnings,
  and the raw typed response;
- multi-step operations return `WorkflowResult[T]` with a status, ordered step journal, completed
  provider identifiers, warnings, raw responses, failed or uncertain step, and recovery guidance;
- `OperationPlan` describes normalized intended calls and risk classifications without executing
  network mutations.

Result objects are JSON-safe through an explicit serialization method. Their `repr` and default
events redact credentials, message bodies, file contents, authentication material, and fields marked
sensitive by the typed models.

### Warnings and errors

The simple facade has non-union success returns. A QuestBlue `WarningResponse` raises
`QuestBlueWarningError`, which retains the original warning object. Existing authentication,
transport, timeout, rate-limit, server, API, pagination, and response exceptions propagate with
their original causes and metadata.

Input normalization or confirmation failures occur before network I/O. Workflow failures retain the
underlying exception and return or expose the complete journal. Cancellation is never converted into
success. A timeout after a mutation is classified as an uncertain outcome because QuestBlue does not
document idempotency.

### Risk and confirmation

Every helper and plan step has one risk classification: read-only, routing change, consent required,
destination confirmation, compliance sensitive, billable, destructive, or uncertain outcome.

Read-only work runs directly. All other categories require a named confirmation argument or an
application confirmation-policy decision. There is no process-wide “disable safety” switch.
Confirming one category does not confirm another, and a plan cannot reuse a confirmation after its
normalized operations change.

Inventory search never purchases the first result automatically. LNP helpers default to a draft and
never submit implicitly. Mutating calls are attempted once unless QuestBlue publishes an idempotency
contract.

### Composite workflows

A workflow first creates an inspectable `OperationPlan`. Execution records a journal entry before
and after each typed call. It never claims database-style atomicity.

Compensation is automated only when the inverse operation is documented, non-billable, safe after
the observed state transition, and explicitly enabled. Otherwise the workflow stops and returns a
partial or uncertain result with provider identifiers and reconciliation guidance. The SDK offers
journal persistence hooks but owns no application database, queue, lock, or tenant repository.

### Sync and async parity

Sync and async facades expose the same service names, method names, parameters, normalization,
results, plans, risks, and error semantics. Shared pure functions build requests and interpret
responses; only execution adapters differ. CI maintains a machine-readable parity and abstraction
coverage report.

Async polling and workflows are cancellation-safe and use non-blocking waits. Sync implementations
must not call `asyncio.run`, and async implementations must not delegate blocking I/O to the event
loop.

### White-label boundary

An opaque operation context may carry correlation, tenant, actor, and reason values to application
hooks. These values are never authorization by themselves and are never sent to QuestBlue unless a
documented upstream field explicitly requires one.

The application authenticates users, resolves tenants, authorizes resource ownership, stores
credentials and journals, applies pricing/billing policy, and persists audit records. This preserves
ADR 0001.

## Consequences

The simple layer can evolve additively in 1.x while the typed API preserves provider fidelity.
Applications gain concise primitives and inspectable workflows, but advanced or newly published
provider behavior remains immediately reachable through `raw`.

Each convenience requires mapping tests in addition to the underlying operation tests. The library
must maintain two user-facing surfaces and prevent them from drifting. Some one-call helpers will
remain intentionally explicit because safety is more important than minimizing line count.

## Rejected alternatives

- Replacing typed resources with primitive arguments: breaks 1.0 and loses the exact provider API.
- Accepting arbitrary dictionaries or `**kwargs`: hides misspellings and makes discovery worse.
- Returning only dictionaries: discards validation, discoverability, and raw typed evidence.
- Automatically ordering search results: creates hidden billable behavior.
- Automatic rollback of every workflow: QuestBlue does not provide transactional or idempotency
  guarantees.
- Putting tenant authorization in the facade: the public provider contract has no tenant identity or
  scoped credential semantics.
