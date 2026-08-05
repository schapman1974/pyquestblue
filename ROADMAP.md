# Roadmap to 100% QuestBlue API Coverage

This roadmap turns the current transport and endpoint foundation into a production-grade Python SDK
for every operation in QuestBlue API 2.3.2. Work packages below are designed to map directly to
GitHub issues and pull requests.

## What “100% coverage” means

An operation is complete only when all of the following are true:

- A discoverable sync method and async equivalent exist.
- Every documented parameter is typed, documented, serialized correctly, and validated where safe.
- Every documented success, warning, error, empty, and binary response has a typed representation.
- Unit tests cover URL, verb, authentication, parameter encoding, response parsing, and errors.
- A recorded or live contract test verifies the implementation against QuestBlue behavior.
- Public documentation includes at least one realistic example and links to the upstream operation.
- Mutating operations document billing, compliance, irreversibility, and idempotency considerations.

The current foundation maps all 65 documented paths and all 103 HTTP operations. The work remaining
is primarily schema fidelity, validation, contract verification, developer ergonomics, and
production hardening.

## Milestone v0.2.0 — Typed API coverage

### QB-001: Pin the upstream OpenAPI contract and detect drift

- Store a normalized copy of the upstream QuestBlue OpenAPI document with provenance and version.
- Add a reproducible update command and semantic diff report.
- Fail CI when documented operations disappear from the SDK or sync/async parity breaks.
- Produce a machine-readable coverage report by path, operation, request, response, test, and docs.

### QB-002: Build the shared model, validation, and pagination layer

- Select and document the public modeling strategy with Python 3.10 compatibility.
- Implement reusable response envelopes, warnings, pagination metadata, enums, dates, and binary data.
- Add auto-pagination without hiding raw page access.
- Preserve unknown fields for forward compatibility and provide raw-response escape hatches.

### QB-003: Harden the HTTP transport contract

- Define retry safety for reads versus billable mutations.
- Add idempotency support when QuestBlue confirms server behavior.
- Support per-request timeout, retry, headers, and raw response access.
- Add structured logging/OpenTelemetry hooks with credential and message-content redaction.
- Test connection failures, timeouts, retry headers, malformed JSON, empty responses, and cancellation.

### QB-004: Complete typed User Account coverage

- Model all 14 account operations: balance, account details, rates, countries, refills, alerts, and
  callback configuration/status.
- Explicitly protect refill and autorefill operations from accidental retries.
- Add examples for balance monitoring, rate lookup, and callback configuration.

### QB-005: Complete typed Voice DID coverage

- Model inventory, states, rate centers, availability, ordering, updating, deletion, voice-to-fax,
  and fraud validation.
- Cover array ordering, wildcard searches, `total_list`, E911, CNAM/LIDB, DLDA, SMS permissions, and
  port-out PIN constraints.
- Add safe ordering examples and sandbox contract tests.

### QB-006: Complete typed International DID coverage

- Model country/city discovery and the complete international DID lifecycle.
- Validate country-, city-, and routing-specific identifiers without blocking unknown future values.
- Add discovery, ordering, update, and removal examples.

### QB-007: Complete typed SIP Trunk coverage

- Model trunk CRUD, registration status, blocked callers, and caller blocking/unblocking.
- Cover IP/FQDN registration modes, routing options, failover, codecs, and concurrent-channel fields.
- Add PBX provisioning and troubleshooting examples.

### QB-008: Complete typed SMS/MMS and carrier coverage

- Model SMS inventory/settings, SMS/MMS sending, history, delivery status, off-net orders/status,
  and carrier lookup.
- Validate media URL handling, message identifiers, telephone numbers, filters, and pagination.
- Document compliance-sensitive behavior and prevent message bodies from appearing in logs.

### QB-009: Complete typed 10DLC coverage

- Model brand and campaign CRUD with all registration enums and lifecycle states.
- Preserve upstream validation/warning detail.
- Add compliant brand/campaign workflow examples without presenting legal advice.

### QB-010: Complete typed Fax.Pro coverage

- Model state/rate-center/availability lookup, fax inventory CRUD, sending, pause, email permissions,
  and fax-to-voice migration.
- Add file validation and response models for outbound fax workflows.
- Cover empty and HTTP 206 error responses.

### QB-011: Complete typed iFax Enterprise coverage

- Model account, group, user, permission, pause, upload, and send operations.
- Add safe path/file-like upload helpers with size/type checks and streaming-friendly behavior.
- Test base64 encoding, multiple-file sending, permissions, and lifecycle operations.

### QB-012: Complete typed Reports coverage

- Model voice call history, fax history, and fax downloads.
- Support every period/filter/timezone option and robust iteration through large result sets.
- Add streaming/binary downloads and CSV/pandas-friendly export examples.
- Verify the `last_id`, summary, trunk, and call-ID behaviors called out in upstream changelogs.

### QB-013: Complete typed Local Number Portability coverage

- Model portability checking and the complete LNP request lifecycle.
- Add phone-bill upload helpers, sensitive-data redaction, and field/cross-field validation.
- Clearly identify PII, irreversible actions, status transitions, and sandbox requirements.

### QB-014: Complete typed VoIP Server coverage

- Model server inventory/order/removal, IP allowlists, upgrades, and all backup operations.
- Validate schedules, backup identifiers, server types, and upgrade parameters.
- Document potentially destructive and billable actions prominently.

## Milestone v0.3.0 — Verified integration readiness

### QB-015: Establish live and recorded contract testing

- Obtain or document a dedicated QuestBlue sandbox/subaccount strategy.
- Separate read-only, reversible, billable, compliance-sensitive, and destructive test suites.
- Record sanitized fixtures for ordinary CI and schedule credentialed live smoke tests.
- Publish a contract-test matrix showing verified and unverified behaviors.

### QB-016: Complete documentation and executable examples

- Build versioned documentation with one page per resource and searchable request/response fields.
- Add sync and async quickstarts, pagination, errors, retries, uploads, and framework recipes.
- Validate every code sample in CI.
- Add migration guidance from raw `requests`, the existing Python report project, and the Node client.

### QB-017: Add integration extension points

- Define webhook/callback event models after confirming QuestBlue payload and authentication behavior.
- Add FastAPI and Django webhook helpers without coupling the core SDK to either framework.
- Add pluggable observability, caching, rate limiting, and export hooks.
- Document integration boundaries for CRM, billing, help-desk, and automation systems.

## Milestone v1.0.0 — Stable production SDK

### QB-018: Production hardening and compatibility policy

- Reach at least 90% branch coverage and 100% operation-contract coverage.
- Add security scanning, dependency updates, build reproducibility, and artifact attestations.
- Define semantic-versioning, deprecation, support, release, and vulnerability-response policies.
- Validate supported Python versions on Linux, macOS, and Windows.

### QB-019: Validate white-label platform API gaps

- Determine how QuestBlue represents resellers, subaccounts, end customers, roles, and ownership.
- Confirm whether branded pricing, margins, invoices, taxes, credits, and payment flows exist upstream.
- Document which white-label features belong in the SDK, an optional control-plane package, or the
  application layer.
- Produce an architecture decision record for tenant isolation and backend-only credential storage.

### QB-020: Release pyquestblue 1.0

- Close or explicitly defer every API coverage gap.
- Run the complete unit, recorded contract, and approved live contract suites.
- Complete API reference, changelog, upgrade guide, and security review.
- Publish a release candidate to TestPyPI, verify installation, then publish the signed 1.0 release.

## Questions requiring QuestBlue or live-account confirmation

- Sandbox availability and rules for non-billable provisioning tests
- Published rate limits, retry headers, and concurrency limits
- Idempotency guarantees for ordering and other billable mutations
- Callback payload schema, authentication, delivery ordering, and retry behavior
- Subaccount/reseller/customer hierarchy and delegated credential capabilities
- Branding, pricing, invoicing, payment, tax, and user-auth APIs absent from version 2.3.2
- SMS consent/compliance workflow and 10DLC lifecycle edge cases
- Whether HTTP 202 and 206 semantics are consistent across all endpoint families
