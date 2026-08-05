# International DID API

The international DID resource covers all six `/didinter` operations in QuestBlue API 2.3.2 with
validated request and response models, sync/async parity, and typed page iteration.

## Country and city discovery

```python
countries = qb.international_dids.countries()
cities = qb.international_dids.cities("GB")
```

Country codes are normalized to two uppercase letters without using a closed country enum, so new
provider-supported destinations do not require an SDK release. Country results preserve the
upstream list-of-mappings shape; city results are a list of names with a total count.

The upstream 2.3.2 schema declares a required `did` query parameter on
`GET /didinter/countrylist`, but describes it as “DID to move.” That conflicts with the operation's
country-discovery purpose and the existing no-argument behavior. `InternationalCountriesRequest`
models the positive integer but keeps it optional until QuestBlue confirms the contract.

## Inventory and pagination

```python
from questblue import InternationalDIDListRequest

request = InternationalDIDListRequest(did="*456*", per_page=50)
inventory = qb.international_dids.list(request)

for page in qb.international_dids.pages(request):
    print(page.current_page, page.data)
```

`InternationalDIDListRequest` accepts `did`, `per_page`, and `page`. Wildcards require at least
three digits, page sizes are 5–200, and pages begin at one. Inventory preserves the documented
mapping of DID strings to configuration-value arrays.

## Ordering and lifecycle

```python
from questblue import InternationalDIDOrderRequest, InternationalDIDUpdateRequest

order = InternationalDIDOrderRequest(
    country_code="GB",
    city="London",
    forward2did=15551234567,
    route2trunk=7,
)
ordered = qb.international_dids.order(order)  # Billable

qb.international_dids.update(
    InternationalDIDUpdateRequest(
        did=442071234567,
        forward2did=15557654321,
        route2trunk=8,
    )
)
qb.international_dids.delete(442071234567)  # May release the number
```

The order contract requires `country_code`, `city`, `forward2did`, and `route2trunk`, and returns
the ordered DID array. Update requires `did`, `forward2did`, and `route2trunk`. The upstream schema
types trunk identifiers as integers and marks direct forwarding as legacy in favor of trunk
routing; the SDK follows that schema without guessing undocumented routing identifiers.

Ordering can incur immediate recurring and usage charges. Updating changes live call routing, and
deleting may release the number. These mutations are always single-attempt and never automatically
retried. After a timeout, inspect inventory before deciding whether to repeat an operation.

QuestBlue does not publish a sandbox endpoint. Applications should require explicit confirmations,
pricing review, tenant authorization, and audit records before lifecycle mutations. Live lifecycle
contract verification remains dependent on QB-015's approved sandbox/subaccount strategy.

## Async parity

```python
countries = await qb.international_dids.countries()
inventory = await qb.international_dids.list(InternationalDIDListRequest(per_page=200))
async for page in qb.international_dids.pages():
    print(page)
```

## Operation reference

| SDK method | HTTP operation | Request | Response |
| --- | --- | --- | --- |
| `qb.international_dids.countries()` | `GET /didinter/countrylist` | `InternationalCountriesRequest` | `InternationalCountriesResponse` |
| `qb.international_dids.cities()` | `GET /didinter/citylist` | `InternationalCitiesRequest` | `InternationalCitiesResponse` |
| `qb.international_dids.list()` | `GET /didinter` | `InternationalDIDListRequest` | `InternationalDIDInventoryResponse` |
| `qb.international_dids.order()` | `POST /didinter` | `InternationalDIDOrderRequest` | `InternationalDIDOrderResponse` |
| `qb.international_dids.update()` | `PUT /didinter` | `InternationalDIDUpdateRequest` | empty |
| `qb.international_dids.delete()` | `DELETE /didinter` | `InternationalDIDDeleteRequest` | empty |

HTTP 202 warnings are returned as `WarningResponse`; HTTP 206 and other errors raise the typed
transport exceptions.
