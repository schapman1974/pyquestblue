"""Guard billable provisioning and destructive server restore operations."""

from questblue import (
    BackupRequest,
    QuestBlue,
    ServerOrderRequest,
    ServerOrderResponse,
    ServerSoftware,
    ServerType,
    VitalPBXConfig,
    WarningResponse,
)


def provision_vital_pbx(
    client: QuestBlue, email: str, *, confirm_billable_order: bool = False
) -> ServerOrderResponse:
    if not confirm_billable_order:
        raise ValueError("review pricing and set confirm_billable_order=True")
    result = client.servers.create(
        ServerOrderRequest(
            server_type=ServerType.SMALL,
            params=ServerSoftware.model_validate({"vital-pbx": VitalPBXConfig(email=email)}),
        )
    )
    if isinstance(result, WarningResponse):
        raise RuntimeError("QuestBlue warning: " + "; ".join(result.warning))
    return result


def restore(
    client: QuestBlue,
    server_id: int,
    backup_id: int,
    *,
    confirm_destructive_restore: bool = False,
) -> object:
    if not confirm_destructive_restore:
        raise ValueError("verify server and backup IDs, then confirm the destructive restore")
    return client.servers.restore_backup(BackupRequest(server_id=server_id, backup_id=backup_id))
