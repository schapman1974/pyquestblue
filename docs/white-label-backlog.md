# White-label follow-on backlog

This backlog turns the gap analysis into independently deliverable slices. It is architectural work
outside the pyquestblue 1.0 core unless noted. Items marked “provider-gated” should not be implemented
against guessed QuestBlue behavior.

| ID | Slice | Target | Gate / acceptance |
| --- | --- | --- | --- |
| WL-001 | Tenant/account binding model and ownership repository | Optional control plane | ADR 0001 invariants; all reads/writes require tenant ID; concurrency and cross-tenant denial tests |
| WL-002 | Secret-manager credential provider and rotation | Optional control plane | No plaintext persistence/logging; atomic rotation; audit trail; provider Q3 informs per-subaccount model |
| WL-003 | Application authorization contract | Application/reference guide | Operation/risk-level policy before client selection; deny-by-default examples; actor and reason auditing |
| WL-004 | Supplier-rate importer and versioned customer catalog ports | Optional control plane | Provider costs are immutable inputs; effective-dated price books; no floating-point money |
| WL-005 | Provisioning workflow/outbox and reconciliation | Optional control plane | Durable state machine, uncertain-outcome handling, idempotency, compensations, provider polling |
| WL-006 | Usage ingestion and rating boundary | Optional control plane | Immutable source records, dedupe keys, late corrections, tenant attribution; provider Q9 is a production gate |
| WL-007 | Billing/tax/payment adapters | Application integrations | External system of record, PCI-safe tokens, invoice/credit/refund events; provider Q7/Q8 mapping |
| WL-008 | Branded notification and domain configuration | Application | Tenant-owned templates/assets/domains; accessibility and legal-text versioning; provider Q5 mapping if available |
| WL-009 | CRM/help-desk event adapters | Application integrations | Sanitized domain events, tenant/PII policy, retry/DLQ; provider case IDs optional after Q12 |
| WL-010 | Webhook inbox and tenant router | Optional control plane | Verify before parse, durable inbox, fingerprint dedupe, resource-binding lookup, replay and quarantine tests |
| WL-011 | Reseller/subaccount resources | pyquestblue core, provider-gated | Versioned QuestBlue contract and fixtures answering Q1-Q4; typed sync/async parity and lifecycle safeguards |
| WL-012 | Billing/account event resources | pyquestblue core, provider-gated | Versioned schemas answering Q7-Q10; authentication, retry, ordering, and dedupe contract |
| WL-013 | Approved sandbox fixture factory | Test infrastructure, provider-gated | Written non-production rules answering Q11; cost ceiling, cleanup, synthetic data, emergency stop |
| WL-014 | Threat model and isolation test kit | Optional control plane | Credential, cache, queue, webhook, IDOR, confused-deputy, log-redaction, and backup-restore scenarios |

Provider answers are recorded as evidence revisions in `contracts/white-label-capabilities.json`. A
capability changes from absent/unknown only when supported by a published contract, written partner
contract, or sanitized verified fixture. Core-SDK proposals then receive normal GitHub issues with
the evidence attached; speculative endpoint work does not.
