# Fax.Pro API

All twelve documented Fax.Pro operations have validated synchronous and asynchronous methods.
They cover geographic discovery, available numbers, inventory CRUD, document sending, account
pause/unpause, email permissions, and migration back to voice inventory.

## Discover and order a Fax DID

```python
from questblue import FaxAvailabilityRequest, FaxDIDType, FaxOrderRequest, FaxTier

available = qb.fax.available(
    FaxAvailabilityRequest(
        did_type=FaxDIDType.LOCAL,
        tier=FaxTier.TIER_1B,
        state="NC",
        ratecenter="RALEIGH",
    )
)
qb.fax.create(FaxOrderRequest(did=int(available.data[0])))
```

Local discovery requires a ZIP, NPA, or state/rate-center pair. Toll-free discovery requires a
two-digit code and a supported tier. Ordering a number is billable. Deleting a Fax DID or moving it
to voice is destructive and can remove Fax.Pro routing/account behavior; reconcile inventory after
an uncertain timeout. Mutations are attempted once and are never automatically retried.

The account fields `fax_name`, `fax_login`, `fax_password`, and `fax_email` must be supplied as a
complete set. `unset_acc=UnsetAccount.ON` removes the Fax.Pro account and cannot be combined with
account fields. PINs, passwords, email addresses, ATA addresses, document bodies, and fax numbers
are hidden from default model and validation diagnostics.

## Send a validated document

```python
from questblue import FaxSendRequest

request = FaxSendRequest.from_path(
    "invoice.pdf",
    did_from=15551234567,
    did_to=15557654321,
)
sent = qb.fax.send(request)
print(sent.data.fax_id)
```

`from_path`, `from_file`, and `from_bytes` encode content as required by QuestBlue and reject files
before network activity. The 8MB limit and these extensions are enforced: JPEG/JPG, GIF, PNG,
TIF/TIFF, PDF, DOC, RTF, ODS, XLS, CSV, PPT, TXT, RAR, ZIP, and 7Z. Filenames must be basenames.
Verify recipients and document contents before sending; fax transmission can expose regulated or
confidential information and may incur charges.

## Email permissions

```python
from questblue import FaxEmailPermissionRequest, FaxYesNo

qb.fax.set_email_permission(
    FaxEmailPermissionRequest(
        did=15551234567,
        email="sender@example.com",
        allow_send=FaxYesNo.YES,
        allow_receive=FaxYesNo.NO,
    )
)
```

Email send permission authorizes that address to originate faxes. Grant the least privilege needed,
periodically audit permissions, and remove stale addresses. See `examples/fax.py` for executable
sending and permission helpers.

| SDK method | Operation | Models |
| --- | --- | --- |
| `qb.fax.states()` | `GET /fax/states` | `FaxStatesResponse` |
| `qb.fax.rate_centers()` | `GET /fax/ratecenters` | `FaxRateCentersRequest` → `FaxRateCentersResponse` |
| `qb.fax.available()` | `GET /fax/available` | `FaxAvailabilityRequest` → `AvailableFaxDIDsResponse` |
| `qb.fax.list()` | `GET /fax` | `FaxListRequest` → `FaxInventoryResponse` |
| `qb.fax.create()` | `POST /fax` | `FaxOrderRequest` → empty/warning |
| `qb.fax.update()` | `PUT /fax` | `FaxUpdateRequest` → empty/warning |
| `qb.fax.delete()` | `DELETE /fax` | `FaxDeleteRequest` → empty/warning |
| `qb.fax.send()` | `POST /fax/send` | `FaxSendRequest` → `FaxSendResponse` |
| `qb.fax.pause()` | `PUT /fax/pause` | `FaxPauseRequest` → empty/warning |
| `qb.fax.move_to_voice()` | `PUT /fax/move2voice` | `FaxMoveToVoiceRequest` → empty/warning |
| `qb.fax.set_email_permission()` | `POST /fax/email` | `FaxEmailPermissionRequest` → empty/warning |
| `qb.fax.delete_email_permission()` | `DELETE /fax/email` | `FaxEmailPermissionDeleteRequest` → empty/warning |
