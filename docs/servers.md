# VoIP servers

`qb.servers` covers all ten QuestBlue server operations with equivalent synchronous and asynchronous
methods. Typed models cover inventory, ordering parameters for every documented software family,
IP allowlists, upgrades, schedules, backup inventory, restore, and removal.

Order with `qb.servers.create` and inspect inventory with `qb.servers.list`. The order body supports
3CX, MassText, QuBe, QuBe TDR, QuBe v2, SBC, VitalPBX, and Vodia configuration through
`ServerSoftware`. API aliases such as `3cx`, `qube-tdr`, and `vital-pbx` are serialized exactly as
documented. Email addresses, passwords, license/customer data, DIDs, IPs, server IDs, and backup IDs
are suppressed from representations and validation errors.

```python
from questblue import ServerOrderRequest, ServerSoftware, ServerType, VitalPBXConfig

result = qb.servers.create(
    ServerOrderRequest(
        server_type=ServerType.SMALL,
        params=ServerSoftware(vital_pbx=VitalPBXConfig(email="ops@example.com")),
    )
)
```

`qb.servers.add_ip` validates IPv4 and IPv6 addresses. `qb.servers.remove_ip` follows the pinned API
contract, which accepts only `server_id`; QuestBlue does not expose an address selector on that
operation. Use `qb.servers.upgrade` only with the documented upgrade targets. Manage enrollment with
`qb.servers.manage_backup_schedule` and inspect backups with `qb.servers.list_backups`.

## Safety

Server creation, upgrades, and backup enrollment can be billable. Require an application-level
confirmation after displaying the selected configuration and current rates. Server deletion,
`qb.servers.restore_backup`, and `qb.servers.remove_backup` can destroy or replace production data;
confirm the exact server/backup IDs and capture current inventory first. Restrict IP changes to
trusted operators and avoid logging allowlists or credentials.

See
[`examples/server_lifecycle.py`](https://github.com/schapman1974/pyquestblue/blob/main/examples/server_lifecycle.py)
for guarded provisioning and
restore helpers.

## Operation map

| Operation | SDK method |
| --- | --- |
| `POST /server` | `qb.servers.create` |
| `GET /server` | `qb.servers.list` |
| `DELETE /server` | `qb.servers.delete` |
| `PUT /server/addip` | `qb.servers.add_ip` |
| `DELETE /server/deleip` | `qb.servers.remove_ip` |
| `POST /server/upgrade` | `qb.servers.upgrade` |
| `POST /server/managebackupschedule` | `qb.servers.manage_backup_schedule` |
| `GET /server/listbackups` | `qb.servers.list_backups` |
| `POST /server/restorebackup` | `qb.servers.restore_backup` |
| `DELETE /server/removebackup` | `qb.servers.remove_backup` |
