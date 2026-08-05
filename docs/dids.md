# Voice DID API

The Voice DID resource covers all nine operations under `/did` in QuestBlue API 2.3.2. Request
models validate documented constraints before network access and response models preserve unknown
fields.

## Discovery and inventory

```python
from questblue import DIDAvailabilityRequest, DIDListRequest, DIDTier, DIDType

inventory = qb.dids.list(DIDListRequest(did="*456*", per_page=50, page=1))
states = qb.dids.states()
centers = qb.dids.rate_centers("NC", DIDTier.TIER_1)
available = qb.dids.available(
    DIDAvailabilityRequest(
        did_type=DIDType.LOCAL,
        state="NC",
        ratecenter="CARY",
        total_list=10,
    )
)
```

`DIDListRequest` accepts `did`, `per_page`, and `page`. Wildcard searches must contain at least
three digits, `per_page` is 5–200, and pages begin at one. Iterate typed pages without losing raw DID
configuration fields:

```python
for page in qb.dids.pages(DIDListRequest(per_page=200)):
    if hasattr(page, "warning"):
        break
    for did, configuration in page.data.items():
        print(did, configuration)
```

`DIDAvailabilityRequest` accepts `did_type`, `tier`, `state`, `ratecenter`, `zip`, `code`, `mask`,
and `total_list`. Local discovery requires a ZIP, mask, or state/rate-center pair. Toll-free
discovery requires a mask or legacy two-digit `code`. `total_list` must be positive.

## Ordering and configuration

Ordering provisions inventory and may immediately incur charges:

```python
from questblue import AccountToggle, DIDOrderRequest, DIDTier

request = DIDOrderRequest(
    did=[15551234567, 15551234568],
    tier=DIDTier.TIER_1,
    route2trunk="primary",
    cnam=AccountToggle.ON,
    note="Customer main lines",
    pin=1234,
    lidb="Example Co",
)

# Billable: confirm pricing and account before executing.
warning = qb.dids.order(request)
```

`DIDOrderRequest` supports `did`, `tier`, `route2trunk`, `cnam`, `note`, `pin`, `lidb`, all E911
registration fields, and all DLDA directory-listing fields. An array of DIDs is serialized as the
comma-separated representation expected by QuestBlue. Notes are limited to 100 characters, PINs
to four–six digits, and LIDB names to 4–15 alphanumeric characters (spaces allowed).

`DIDUpdateRequest` requires `did` and supports:

- routing: `route2trunk`, legacy `forw2did`, and nested `failover` values;
- identity: `cnam`, `note`, `pin`, and `lidb`;
- E911: `e911`, `e911_call_alert`, `e911_name`, `e911_city`, `e911_state`, `e911_zip`,
  `e911_address`, `e911_unittype`, and `e911_unitnumber`;
- DLDA: `dlda`, `dlda_type`, `dlda_firstname`, `dlda_lastname`, `dlda_streetnum`,
  `dlda_streetname`, `dlda_city`, `dlda_state`, `dlda_zip`, `dlda_email`, and `dlda_phone`.

The upstream schema describes E911/DLDA ZIP values inconsistently as six characters; the SDK
accepts 5–10 characters to support ordinary ZIP and ZIP+4 formats without inventing a provider
guarantee. QuestBlue marks direct forwarding and failover parameters as legacy in favor of trunk
forwarding.

## Destructive and lifecycle operations

```python
qb.dids.update(DIDUpdateRequest(did=15551234567, route2trunk="secondary"))
qb.dids.move_to_fax(15551234567)
qb.dids.delete(15551234567)
fraud = qb.dids.validate_fraud([15557654321, 15559876543])
```

Ordering, updating, moving, and deleting are single-attempt operations and are never retried. A
timeout can have an uncertain outcome. Re-read inventory before manually repeating an action.
Moving a DID to fax changes its product role; deleting may release the number. Both should require
an application-level confirmation and audit record.

Fraud validation accepts one number or up to 100 numbers and returns `FraudValidationResponse`.

The pinned Voice DID operations do not expose an SMS-permission parameter. SMS-capable DID
inventory and `smsv2` permission/settings fields are separate upstream operations and are tracked
under QB-008; the SDK does not invent a `/did` parameter that QuestBlue has not documented.

## Async parity

Every operation and page iterator has the same async contract:

```python
inventory = await qb.dids.list(DIDListRequest(per_page=200))
async for page in qb.dids.pages(DIDListRequest(per_page=200)):
    print(page)
```

## Operation reference

| SDK method | HTTP operation | Request | Response |
| --- | --- | --- | --- |
| `qb.dids.list()` | `GET /did` | `DIDListRequest` | `DIDInventoryResponse` |
| `qb.dids.order()` | `POST /did` | `DIDOrderRequest` | empty or `WarningResponse` |
| `qb.dids.update()` | `PUT /did` | `DIDUpdateRequest` | empty or `WarningResponse` |
| `qb.dids.delete()` | `DELETE /did` | `DIDDeleteRequest` | empty |
| `qb.dids.states()` | `GET /did/states` | — | `DIDStatesResponse` |
| `qb.dids.rate_centers()` | `GET /did/ratecenters` | `DIDRateCentersRequest` | `DIDRateCentersResponse` |
| `qb.dids.available()` | `GET /did/available` | `DIDAvailabilityRequest` | `AvailableDIDsResponse` |
| `qb.dids.move_to_fax()` | `PUT /did/move2fax` | `DIDMoveToFaxRequest` | empty |
| `qb.dids.validate_fraud()` | `POST /did/fraudvalidate` | `DIDFraudValidationRequest` | `FraudValidationResponse` |

## Sandbox verification status

QuestBlue does not publish a sandbox endpoint or test-mode flag. The opt-in lifecycle test under
`tests/live/` is disabled unless dedicated sandbox credentials, a base URL, and an explicit billing
acknowledgment are supplied. It must never run against ordinary production credentials. Live order,
inventory, update, and deletion verification remains pending the sandbox/subaccount work in QB-015.
