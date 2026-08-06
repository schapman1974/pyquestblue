# Simple API

The additive simple clients accept ordinary Python values, validate them before I/O, and delegate
every request to the complete typed client. Use `.raw` on a client, service, record, or collection
when you need provider-specific fields or an operation not yet covered by a convenience helper.

## Account and inventory

```python
from questblue import SimpleQuestBlue

with SimpleQuestBlue() as qb:
    balance = qb.account.balance()
    numbers = qb.numbers.list(number="919", per_page=100)
```

Collection helpers fetch all available pages by default where the typed API exposes pagination.
Pass `all_pages=False` and `page=` to number or fax inventory helpers to inspect one provider page;
the typed pages used to build a collection remain available through `result.raw`.

## Discovery

Inventory search never purchases a result:

```python
with SimpleQuestBlue() as qb:
    candidates = qb.numbers.search(zip_code="27513", limit=5)
    fax_candidates = qb.fax.search(number_type="local", zip_code="27513")
```

## History

Call and fax history are automatically collected and return immutable records whose `.raw`
property retains provider-added fields:

```python
with SimpleQuestBlue() as qb:
    calls = qb.reports.calls(period="today", number="+1 919 555 0100")
    faxes = qb.reports.faxes(numbers="+1 919 555 0100", period="today")
```

The same service and method names are available from `AsyncSimpleQuestBlue`; only `await` changes.

## Sending communications safely

Message and fax mutations require a named acknowledgement. Confirmations are scoped to the single
call and cannot disable safety globally:

```python
with SimpleQuestBlue() as qb:
    sent = qb.messages.send(
        from_number="+1 919 555 0100",
        to="+1 919 555 0101",
        text="Your service is ready",
        recipient_opted_in=True,
    )
    fax = qb.fax.send(
        from_number="+1 919 555 0100",
        to="+1 919 555 0101",
        file="invoice.pdf",
        destination_confirmed=True,
    )
```

`wait_for_delivery()` uses a caller-controlled attempt count and interval. It stops on QuestBlue's
documented delivered or failed states and raises `DeliveryTimeoutError` when the bound is exhausted;
it does not imply a delivery guarantee. File paths and contents are validated before any upload or
send request, and enterprise fax uploads preserve their provider file IDs in the operation result.

## Provisioning with explicit confirmation

Provisioning helpers accept primitive values but keep the typed request models as the final
validation authority. Every billable, routing, compliance-sensitive, or destructive operation has
a matching confirmation keyword. Use `dry_run=True` to inspect the normalized operation without
calling QuestBlue:

```python
with SimpleQuestBlue() as qb:
    plan = qb.numbers.buy(
        "+1 919 555 0100",
        trunk="main",
        dry_run=True,
    )
    print(plan.operations)

    purchased = qb.numbers.buy(
        "+1 919 555 0100",
        trunk="main",
        confirm_billable=True,
    )
    print(purchased.raw)  # original typed provider response
```

Inventory selection is always a separate read: `numbers.search()` and `fax.search()` never buy a
number. Likewise, `porting.create_draft()` always sends `status="draft"`; the simple layer never
submits an LNP request. Server, SIP trunk, Fax.Pro, enterprise-fax, international DID, backup, and
number lifecycle helpers follow the same one-call confirmation and dry-run contract.
