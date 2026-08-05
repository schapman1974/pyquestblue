"""Fax.Pro sending and email-permission examples."""

from pathlib import Path
from typing import Union

from questblue import (
    FaxEmailPermissionRequest,
    FaxSendRequest,
    FaxSendResponse,
    FaxYesNo,
    QuestBlue,
    WarningResponse,
)


def send_fax(
    client: QuestBlue,
    path: Union[str, Path],
    sender: int,
    destination: int,
    *,
    confirm_destination: bool = False,
) -> FaxSendResponse:
    if not confirm_destination:
        raise ValueError("verify the destination and set confirm_destination=True")
    result = client.fax.send(FaxSendRequest.from_path(path, did_from=sender, did_to=destination))
    if isinstance(result, WarningResponse):
        raise RuntimeError("QuestBlue warning: " + "; ".join(result.warning))
    return result


def allow_email_to_send(client: QuestBlue, did: int, email: str) -> None:
    result = client.fax.set_email_permission(
        FaxEmailPermissionRequest(
            did=did,
            email=email,
            allow_send=FaxYesNo.YES,
            allow_receive=FaxYesNo.NO,
        )
    )
    if isinstance(result, WarningResponse):
        raise RuntimeError("QuestBlue warning: " + "; ".join(result.warning))
