# 1.0 security review

Review date: 2026-08-05

## Scope and trust boundaries

The review covers the SDK transport, authentication handling, models, webhook helpers, optional web
framework adapters, release automation, dependencies, and the documented multi-tenant architecture.
QuestBlue and the application using this library remain separate trust boundaries. Applications
must keep provider credentials server-side and enforce tenant authorization before invoking the SDK.

## Findings and controls

- Credentials are supplied explicitly or through environment variables, are redacted from object
  representations, and are sent only through the authenticated HTTP transport. TLS verification is
  enabled by default.
- Safe reads use bounded retries. Mutating, destructive, compliance-sensitive, and billable calls do
  not retry automatically, reducing duplicate provisioning and charges.
- Webhook payloads are typed, but the upstream contract does not define signatures, unique event
  identifiers, delivery ordering, or retries. Deployments must authenticate ingress at their edge,
  limit request size, and implement durable idempotency.
- The tenant-isolation ADR requires server-side credential custody, tenant-scoped authorization,
  audit events, and isolation tests for any rebranded control plane.
- CI enforces strict typing, linting, at least 90% branch coverage, sanitized recorded contracts,
  reproducible artifacts, dependency auditing, CodeQL, and cross-platform tests.
- Releases use separate encrypted API-token secrets in protected TestPyPI and PyPI GitHub
  environments. Tokens are never stored in the repository, and GitHub OIDC produces
  build-provenance attestations for each artifact. Tokens should be project-scoped after the initial
  package creation and rotated on suspected disclosure.
- Repository secret scanning, push protection, private vulnerability reporting, Dependabot security
  updates, and automated security fixes are enabled.

## Dependency review

The pre-release lock included advisories reachable only through Python 3.9 development and optional
integration resolution. Python 3.9 is end-of-life, so 1.0 supports CPython 3.10–3.14 and regenerates
the lock against that range. The merged release candidate must show a clean runtime dependency audit
and the GitHub advisory state must be rechecked before final publication.

## Live-validation status

Unit and sanitized recorded-contract suites are mandatory CI gates. The production read-only suite
is separately gated by an explicit acknowledgement and a dedicated QuestBlue subaccount. Those
credentials are not currently configured, so live validation is deferred rather than reported as a
pass. No destructive, billable, or compliance-sensitive operation is authorized by the release
workflow.

## Residual risks

The provider has no documented sandbox and leaves material webhook-delivery guarantees unspecified.
The pinned OpenAPI contract may also lag undocumented provider behavior. Scheduled drift detection,
preserved unknown response fields, opt-in live validation, and conservative retry defaults reduce
these risks but cannot eliminate them.
