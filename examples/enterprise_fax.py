"""End-to-end iFax Enterprise account-to-send workflow."""

from pathlib import Path
from typing import List

from questblue import (
    EnterpriseFaxGroupCreateRequest,
    EnterpriseFaxOrderRequest,
    EnterpriseFaxPermissionRequest,
    EnterpriseFaxSendRequest,
    EnterpriseFaxSendResponse,
    EnterpriseFaxUploadRequest,
    EnterpriseFaxUserCreateRequest,
    FaxToggle,
    QuestBlue,
    WarningResponse,
)


def provision_account(
    client: QuestBlue,
    did: int,
    *,
    group_short_name: str,
    group_name: str,
    login: str,
    password: str,
    first_name: str,
    confirm_billable_provisioning: bool = False,
) -> None:
    if not confirm_billable_provisioning:
        raise ValueError("review charges and set confirm_billable_provisioning=True")
    client.enterprise_fax.create_group(
        EnterpriseFaxGroupCreateRequest(sname=group_short_name, name=group_name)
    )
    client.enterprise_fax.create_user(
        EnterpriseFaxUserCreateRequest(
            fax_login=login,
            fax_password=password,
            sname=group_short_name,
            fax_name=first_name,
        )
    )
    client.enterprise_fax.create(EnterpriseFaxOrderRequest(did=did, sname=group_short_name))
    client.enterprise_fax.set_permission(
        EnterpriseFaxPermissionRequest(
            fax_login=login,
            did=did,
            allow_send=FaxToggle.ON,
            allow_delete=FaxToggle.OFF,
            allow_list_in=FaxToggle.ON,
            allow_list_out=FaxToggle.ON,
        )
    )


def upload_and_send(
    client: QuestBlue,
    paths: List[Path],
    sender: int,
    destination: int,
    *,
    confirm_destination: bool = False,
) -> EnterpriseFaxSendResponse:
    if not confirm_destination:
        raise ValueError("verify every attachment and set confirm_destination=True")
    file_ids = []
    for path in paths:
        uploaded = client.enterprise_fax.upload(EnterpriseFaxUploadRequest.from_path(path))
        if isinstance(uploaded, WarningResponse):
            raise RuntimeError("QuestBlue warning: " + "; ".join(uploaded.warning))
        file_ids.append(uploaded.file_id)
    result = client.enterprise_fax.send(
        EnterpriseFaxSendRequest(did_from=sender, did_to=destination, file_id=file_ids)
    )
    if isinstance(result, WarningResponse):
        raise RuntimeError("QuestBlue warning: " + "; ".join(result.warning))
    return result
