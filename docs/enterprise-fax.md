# iFax Enterprise

The `qb.enterprise_fax` resource covers all 21 iFax Enterprise operations with typed request and
response models. The same methods are available on `AsyncQuestBlue` and are awaited normally.

## Account-to-send workflow

Provisioning normally follows this order: create a group with `qb.enterprise_fax.create_group`,
create a user with `qb.enterprise_fax.create_user`, order a DID with
`qb.enterprise_fax.create`, and grant the user access with
`qb.enterprise_fax.set_permission`. Inspect the resulting state with
`qb.enterprise_fax.list_groups`, `qb.enterprise_fax.list_users`,
`qb.enterprise_fax.list`, and `qb.enterprise_fax.list_permissions`.

Upload each attachment with `qb.enterprise_fax.upload`, retain every returned `file_id`, then pass
the complete list to `qb.enterprise_fax.send`. The executable
[`examples/enterprise_fax.py`](https://github.com/schapman1974/pyquestblue/blob/main/examples/enterprise_fax.py)
demonstrates the full flow and makes
both billable provisioning and the final destination explicit.

```python
from pathlib import Path

from questblue import EnterpriseFaxSendRequest, EnterpriseFaxUploadRequest

uploads = [
    qb.enterprise_fax.upload(EnterpriseFaxUploadRequest.from_path(path))
    for path in (Path("cover.pdf"), Path("invoice.pdf"))
]
result = qb.enterprise_fax.send(
    EnterpriseFaxSendRequest(
        did_from=15551234567,
        did_to=15557654321,
        file_id=[upload.file_id for upload in uploads],
    )
)
```

`EnterpriseFaxUploadRequest.from_bytes`, `.from_file`, and `.from_path` validate the filename,
supported file type, non-empty content, and documented 8 MiB limit before making a request. File
objects are read only through the limit plus one byte so oversized input is rejected without
loading the remainder. Base64 document bodies, credentials, phone numbers, email addresses, and
file IDs are hidden from model representations and validation errors.

## Operation map

| Area | SDK methods |
| --- | --- |
| DID accounts | `qb.enterprise_fax.list`, `qb.enterprise_fax.create`, `qb.enterprise_fax.update`, `qb.enterprise_fax.delete`, `qb.enterprise_fax.pause` |
| Email access | `qb.enterprise_fax.list_emails`, `qb.enterprise_fax.set_email_permission`, `qb.enterprise_fax.delete_email_permission` |
| Groups | `qb.enterprise_fax.list_groups`, `qb.enterprise_fax.create_group`, `qb.enterprise_fax.update_group`, `qb.enterprise_fax.delete_group` |
| Users | `qb.enterprise_fax.list_users`, `qb.enterprise_fax.create_user`, `qb.enterprise_fax.update_user`, `qb.enterprise_fax.delete_user` |
| DID permissions | `qb.enterprise_fax.list_permissions`, `qb.enterprise_fax.set_permission`, `qb.enterprise_fax.delete_permission` |
| Documents | `qb.enterprise_fax.upload`, `qb.enterprise_fax.send` |

## Operational safeguards

- Ordering a DID can create charges. Review the account and rate first and require an explicit
  application-level confirmation before calling `create`.
- Apply least privilege to user and email permissions. In particular, enable delete access only
  where the workflow truly requires it.
- Treat uploaded files and fax metadata as confidential. Do not log serialized requests, file IDs,
  credentials, destinations, or API response bodies containing document details.
- `delete`, `delete_group`, `delete_user`, `delete_permission`, and
  `delete_email_permission` are destructive. Confirm the target and dependencies first.
- Use `update_group` and `update_user` for lifecycle changes, and `pause` when service should be
  suspended without deleting the DID.
