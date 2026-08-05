# White-label capability and gap analysis

This analysis answers what can be built from QuestBlue's public API today and what still requires a
provider contract or an application-owned control plane. It is based on the current public QuestBlue
OpenAPI 2.3.2 document, checked August 5, 2026: 103 HTTP operations, two messaging webhooks, and the
global Basic-auth plus `Security-Key` security definition. The exact machine-readable evidence is in
`contracts/white-label-capabilities.json`; CI verifies it against the pinned contract checksum and
operation set.

“Absent” means absent from the public 2.3.2 contract, not proof that QuestBlue has no private partner
capability. “Unknown” means the public evidence cannot establish behavior. The live contract drift
check confirmed that the pinned document matches the current published contract on the review date.

## Capability matrix

| Capability | Finding | Contract evidence | Product consequence |
| --- | --- | --- | --- |
| Reseller/subaccount hierarchy | Absent | Account details and balance describe only the authenticated account | Maintain tenant hierarchy internally until QuestBlue confirms a partner API |
| End-customer identity | Absent | Customer/contact fields occur inside E911, LNP, 10DLC, and service records | Application owns organizations, people, consent, and customer lifecycle |
| Roles and permissions | Partial | `/fax2/user` and `/fax2/permit` are iFax-only | Application RBAC must authorize every SDK call; do not generalize fax permissions |
| Resource ownership | Absent | DID, trunk, fax, and server inventory are implicitly account-scoped | Store immutable tenant-to-provider-resource bindings and verify on every mutation |
| Delegated credentials | Absent | Global Basic auth plus `Security-Key`; no scopes or token lifecycle | Credentials stay backend-only and cannot represent an end user |
| Branding | Absent | “Brand” operations are regulatory 10DLC brands, not presentation branding | Application owns domain, theme, templates, legal text, and branded communications |
| Provider rates | Supported | `/account/rates`, `/countryrate`, `/ratezone2`, `/nonusintfrate` | Import as supplier cost inputs, never expose them as an end-customer price book |
| Customer pricing/margins | Absent | No price-book, markup, discount, or quote operations | Control plane owns versioned catalogs and pricing decisions |
| Invoices/tax | Absent | 10DLC `tax_number` is business identity; no billing documents or tax engine | Use a billing/tax system of record outside the SDK |
| Credits | Partial | `/account/getbalance` reads provider balance and allowed credit only | Do not treat provider credit as a customer ledger or wallet |
| Payments | Partial | Account payment-method type is readable and `/refillbalance` funds the provider account | Customer payment methods and transactions belong in a PCI-aware billing provider |
| Usage inputs | Partial | Call, fax, and SMS histories exist without rated ledger/invoice linkage | Ingest immutable usage, rate it internally, and reconcile to provider statements |
| Events | Partial | Inventory callbacks and messaging callbacks only | Use durable ingestion; polling/reconciliation remains necessary |
| Support cases | Absent | No ticket/case resource | Application/help-desk owns cases and maps sanitized provider escalation IDs |
| Sandbox | Unknown | Only `api.questblue.com` and `api2.questblue.com` are published | Obtain a dedicated provider-approved test subaccount before lifecycle testing |

## Questions ready for QuestBlue

The provider discussion should request written answers and example payloads for these items:

1. Is there a reseller/subaccount API outside 2.3.2, including identifiers, lifecycle states, limits,
   and parent-child traversal?
2. Can inventory be assigned or transferred between subaccounts without destructive release and
   reorder operations?
3. Can each subaccount receive scoped, revocable credentials or tokens with read/write and
   product-specific permissions?
4. Are account-wide users, roles, SSO, MFA, or delegated administrators available beyond iFax?
5. Are custom domains, portal/email/SMS branding, templates, and legal-document settings exposed?
6. Can a reseller manage customer price books, markups, discounts, quotes, or committed-rate plans?
7. Are authoritative rated line items, invoices, taxes, exemptions, refunds, credits, and adjustments
   available by API or export?
8. Are tokenized payment methods, ACH mandates, payment intents, receipts, failures, and chargebacks
   available without the reseller handling raw payment credentials?
9. Which IDs, timestamps, rates, surcharges, taxes, and adjustments form the authoritative billable
   usage ledger, and how are late corrections represented?
10. Are account, billing, payment, inventory, and credential events available, with documented
    signatures, retries, ordering, and deduplication?
11. Can QuestBlue provision a non-production reseller hierarchy with non-billable fixtures and safe,
    reversible lifecycle operations?
12. Is there a partner support/escalation API with customer-safe case IDs and status events?

Until those answers are incorporated into a versioned contract, pyquestblue will not invent endpoint
parameters or claim support for private behavior.

## Responsibility boundary

| Layer | Owns |
| --- | --- |
| pyquestblue core | Provider authentication transport, typed 2.3.2 operations, validation, retries, pagination, webhooks, safe observability |
| Optional control plane | Tenant/provider bindings, encrypted credential references, catalog and supplier-cost imports, workflow state, usage ingestion, reconciliation, audit/event ports |
| White-label application | User authentication, RBAC policy, branding/UI, entitlements, customer pricing, invoices/tax/payments, notifications, support experience |
| External systems | Identity provider, secret manager/KMS, queue, database, billing/tax/payment providers, CRM/help desk, observability stack |
| QuestBlue | Provider accounts and inventory, wholesale service delivery, authoritative private partner capabilities, provider statements and support escalation |

The tenant-security decision is recorded in
[ADR 0001](adr/0001-tenant-isolation.md). Proposed implementation slices and their provider-answer
gates are in the [white-label backlog](white-label-backlog.md).
