# Local Number Portability

`qb.lnp` models all five QuestBlue portability operations, their warning/error variants, lifecycle
states, contact and service fields, and cross-field rules. Sync and async clients share the same
request and response models.

Check numbers with `qb.lnp.check`, create a draft or submitted request with `qb.lnp.create`, inspect
orders with `qb.lnp.list`, change eligible draft/submitted orders with `qb.lnp.update`, and remove an
active order with `qb.lnp.delete`.

```python
from questblue import LNPBillUpload, LNPCreateRequest, LNPSubmissionStatus

bill = LNPBillUpload.from_path("current-bill.pdf")
request = LNPCreateRequest.with_bill(
    bill,
    number2port=[15551234567],
    provider_name="Current Carrier",
    account_no="account-number",
    authorize_contact="Jane Customer",
    contact_title="Owner",
    street_no="123",
    street_name="Main Street",
    city="Cary",
    state="NC",
    zipcode="27513",
    billing_telephone_no="5551234567",
    company="Example LLC",
    status=LNPSubmissionStatus.DRAFT,
)
created = qb.lnp.create(request)
```

Bill helpers accept bytes, binary file objects, or paths. They reject empty files, files over the
documented 5 MiB limit, directory-bearing filenames, and extensions other than GIF, JPG/JPEG, PNG,
or PDF before sending a request. Account numbers, contacts, addresses, telephone numbers, PINs,
SSN fragments, bill content, filenames, request IDs, and results are hidden from representations and
validation errors.

Validation also enforces partial-port remaining services, business company names, wireless PIN/SSN
requirements, the wireless FOC-date restriction, voice-only trunks, ten-digit billing numbers,
two-letter states, paired bill fields, and on-the-hour activation times.

## Production safeguards

QuestBlue does not document a sandbox for these operations. Unit and contract tests therefore use
mocked/recorded responses; do not submit test data to the production endpoint. Creating with
`submitted` can initiate a real port. Prefer `draft`, review every number and authorization record,
then require an application-level confirmation before submitting. Deleting an active request and
changing a submitted request may be irreversible or operationally disruptive.

Treat every LNP payload as sensitive customer data. Do not log serialized models, query strings,
response bodies, or bill files, and restrict stored fixtures to synthetic values.

## Operation map

| Operation | SDK method |
| --- | --- |
| `GET /lnp/check` | `qb.lnp.check` |
| `POST /lnp` | `qb.lnp.create` |
| `GET /lnp` | `qb.lnp.list` |
| `PUT /lnp` | `qb.lnp.update` |
| `DELETE /lnp` | `qb.lnp.delete` |

