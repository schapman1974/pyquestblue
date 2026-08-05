from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
from pydantic import ValidationError

from questblue import (
    AsyncQuestBlue,
    BackupListResponse,
    BackupRequest,
    BackupSchedule,
    BackupScheduleRequest,
    MassTextConfig,
    QubeConfig,
    QubeTDRConfig,
    QubeV2Config,
    QuestBlue,
    QuestBlueAPIError,
    QuestBlueResponseError,
    SBCConfig,
    ServerIPRequest,
    ServerListRequest,
    ServerListResponse,
    ServerMessageResponse,
    ServerOrderRequest,
    ServerOrderResponse,
    ServerSoftware,
    ServerStatus,
    ServerType,
    ServerUpgradeRequest,
    ThreeCXConfig,
    UpgradeServerType,
    VitalPBXConfig,
    VodiaConfig,
    WarningResponse,
)


def order_request() -> ServerOrderRequest:
    return ServerOrderRequest(
        server_type=ServerType.SMALL,
        params=ServerSoftware(
            three_cx=ThreeCXConfig(
                email="ops@example.test",
                admin_email="admin@example.test",
                admin_password="private",
                license_email="license@example.test",
            ),
            note="production PBX",
        ),
    )


def handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/server" and request.method == "POST":
        assert request.url.params["server_type"] == "small"
        assert "3cx" in json.loads(request.content)
        return httpx.Response(200, json={"data": {"server_id": 101}})
    if path == "/server" and request.method == "GET":
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "allowed_ip": ["192.0.2.1", "2001:db8::1"],
                        "ordered_by": "2026-08-01",
                        "server_id": 101,
                        "status": "provisioning",
                        "type": "small",
                    }
                ],
                "total": 1,
            },
        )
    if path == "/server/listbackups":
        return httpx.Response(
            200, json={"data": [{"backup_id": 9, "name": "nightly", "type": "manual"}], "total": 1}
        )
    if path in ("/server/restorebackup", "/server/removebackup"):
        return httpx.Response(200, json={"message": "accepted"})
    return httpx.Response(200)


def client(custom_handler: Any = handler) -> QuestBlue:
    http = httpx.Client(
        base_url="https://example.test", transport=httpx.MockTransport(custom_handler)
    )
    return QuestBlue("user", "password", "key", http_client=http)


def async_client(custom_handler: Any = handler) -> AsyncQuestBlue:
    http = httpx.AsyncClient(
        base_url="https://example.test", transport=httpx.MockTransport(custom_handler)
    )
    return AsyncQuestBlue("user", "password", "key", http_client=http)


def test_all_sync_server_operations() -> None:
    qb = client()
    created = qb.servers.create(order_request())
    listed = qb.servers.list(ServerListRequest(server_id=[101]))
    assert qb.servers.delete(101) is None
    assert qb.servers.add_ip(ServerIPRequest(server_id=101, ip_address="192.0.2.2")) is None
    assert qb.servers.remove_ip(101) is None
    assert (
        qb.servers.upgrade(
            ServerUpgradeRequest(server_id=101, server_type=UpgradeServerType.MEDIUM)
        )
        is None
    )
    assert (
        qb.servers.manage_backup_schedule(
            BackupScheduleRequest(server_id=101, schedule=BackupSchedule.DAILY)
        )
        is None
    )
    backups = qb.servers.list_backups(101)
    restored = qb.servers.restore_backup(BackupRequest(server_id=101, backup_id=9))
    removed = qb.servers.remove_backup(BackupRequest(server_id=101, backup_id=9))
    assert isinstance(created, ServerOrderResponse) and created.data.server_id == 101
    assert isinstance(listed, ServerListResponse)
    assert listed.data[0].status == ServerStatus("provisioning")
    assert isinstance(backups, BackupListResponse) and backups.data[0].backup_id == 9
    assert isinstance(restored, ServerMessageResponse)
    assert isinstance(removed, ServerMessageResponse)
    assert "192.0.2.1" not in repr(listed)


@pytest.mark.asyncio
async def test_all_async_server_operations() -> None:
    qb = async_client()
    assert isinstance(await qb.servers.create(order_request()), ServerOrderResponse)
    assert isinstance(await qb.servers.list(), ServerListResponse)
    assert await qb.servers.delete(101) is None
    assert await qb.servers.add_ip(ServerIPRequest(server_id=101, ip_address="192.0.2.2")) is None
    assert await qb.servers.remove_ip(101) is None
    assert (
        await qb.servers.upgrade(ServerUpgradeRequest(server_id=101, server_type="large")) is None
    )
    assert (
        await qb.servers.manage_backup_schedule(
            BackupScheduleRequest(server_id=101, schedule="weekly")
        )
        is None
    )
    assert isinstance(await qb.servers.list_backups(101), BackupListResponse)
    request = BackupRequest(server_id=101, backup_id=9)
    assert isinstance(await qb.servers.restore_backup(request), ServerMessageResponse)
    assert isinstance(await qb.servers.remove_backup(request), ServerMessageResponse)


def test_all_software_shapes_and_alias_serialization() -> None:
    software = ServerSoftware(
        masstext=MassTextConfig(
            email="ops@example.test",
            domain_name="sms.example.test",
            password="p",
            inbound_trunk_name="main",
            username="u",
        ),
        qube=QubeConfig(email="ops@example.test", inbound_trunk_name="main", password="p"),
        qube_tdr=QubeTDRConfig(
            email="ops@example.test",
            domain_name="tdr.example.test",
            password="p",
            inbound_trunk_name="main",
        ),
        qubev2=QubeV2Config(email="ops@example.test", domain_name="v2.example.test", password="p"),
        sbc=SBCConfig(email="ops@example.test", inbound_trunk_name="main", sbcuser_password="p"),
        vital_pbx=VitalPBXConfig(email="ops@example.test"),
        vodia=VodiaConfig(
            email="ops@example.test",
            company="Example",
            did="15551234567",
            inbound_trunk_name="main",
            password="p",
        ),
    )
    payload = software.to_request_params()
    assert "qube-tdr" in payload and "vital-pbx" in payload
    assert "password=" not in repr(software)


@pytest.mark.parametrize(
    "factory",
    [
        lambda: ServerSoftware(note="nothing configured"),
        lambda: VitalPBXConfig(email="bad"),
        lambda: ThreeCXConfig(email="ok@example.test", admin_email="bad"),
        lambda: ThreeCXConfig(email="ok@example.test", license_email="bad"),
        lambda: ServerListRequest(server_id=[]),
        lambda: ServerListRequest(server_id=[0]),
        lambda: ServerIPRequest(server_id=1, ip_address="not-an-ip"),
        lambda: ServerIPRequest(server_id=1, ip_address="192.0.2.1", note="x" * 65),
        lambda: ServerUpgradeRequest(server_id=1, server_type="small"),
        lambda: BackupScheduleRequest(server_id=0, schedule="daily"),
        lambda: BackupRequest(server_id=1, backup_id=0),
        lambda: ServerListResponse.model_validate(
            {
                "data": [
                    {
                        "allowed_ip": ["bad"],
                        "ordered_by": "2026-01-01",
                        "server_id": 1,
                        "status": "active",
                        "type": "small",
                    }
                ]
            }
        ),
    ],
)
def test_server_validation(factory: Any) -> None:
    with pytest.raises((ValidationError, ValueError)):
        factory()


def test_server_warnings_errors_and_malformed_responses() -> None:
    warning = client(lambda request: httpx.Response(202, json={"warning": ["pending"]}))
    assert isinstance(warning.servers.create(order_request()), WarningResponse)
    result = warning.servers.add_ip(ServerIPRequest(server_id=1, ip_address="192.0.2.1"))
    assert isinstance(result, WarningResponse)
    failed = client(lambda request: httpx.Response(206, json={"error": "upgrade unavailable"}))
    with pytest.raises(QuestBlueAPIError, match="upgrade unavailable"):
        failed.servers.upgrade(ServerUpgradeRequest(server_id=1, server_type="medium"))
    malformed = client(lambda request: httpx.Response(200, json={"data": "wrong"}))
    with pytest.raises(QuestBlueResponseError):
        malformed.servers.list()
