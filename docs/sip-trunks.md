# SIP Trunk API

All seven `/siptrunk` operations have validated synchronous and asynchronous methods.

Create a registration trunk with a 4–38 character alphanumeric password, or a static trunk with an
IP address/FQDN:

```python
from questblue import SIPRegion, SIPTrunkCreateRequest, YesNo

qb.sip_trunks.create(
    SIPTrunkCreateRequest(
        trunk="pbx1",
        ip_address="pbx.example.com",
        region=SIPRegion.US_NY,
        concurrent_max="20",
        allow_rtp_proxy=YesNo.YES,
    )
)
status = qb.sip_trunks.status("pbx1")
```

Create/update fields are `trunk`, `password`, `ip_address`, `region`, `did`, deprecated
`inter_call`, `inter_limit`, `tn2forward`, `concurrent_max`, `allow_e164_rewrite`, and
`allow_rtp_proxy`; update also accepts `status`. Regions follow the upstream list. Registration
status uses a forward-compatible enum so new provider states remain readable.

The pinned QuestBlue schema does not expose codec selection or failover fields on these endpoints.
The SDK deliberately does not invent unsupported query parameters; codec and failover coverage will
be added when QuestBlue documents the controlling endpoint or fields.

Inventory uses `SIPTrunkListRequest(trunk, per_page, page)`. Blocked-caller listing uses
`BlockedCallersRequest(trunk, did, per_page, page)`. Block or unblock one caller on one or more
trunks with `BlockCallerRequest`; trunk arrays serialize as QuestBlue's comma-separated query value.

```python
from questblue import BlockAction, BlockCallerRequest

qb.sip_trunks.block_caller(
    BlockCallerRequest(trunk=["pbx1", "pbx2"], did=15551234567, action=BlockAction.BLOCK)
)
blocked = qb.sip_trunks.blocked_callers()
```

Creating or updating a trunk changes live call routing. Deleting a trunk is destructive and can
strand assigned DIDs. These mutations are never retried automatically; applications should require
confirmation and reconcile state after uncertain timeouts. See `examples/sip_trunk.py` for
executable PBX provisioning and status checks.

| SDK method | Operation | Models |
| --- | --- | --- |
| `qb.sip_trunks.list()` | `GET /siptrunk` | `SIPTrunkListRequest` → `SIPTrunkInventoryResponse` |
| `qb.sip_trunks.create()` | `POST /siptrunk` | `SIPTrunkCreateRequest` → empty |
| `qb.sip_trunks.update()` | `PUT /siptrunk` | `SIPTrunkUpdateRequest` → empty |
| `qb.sip_trunks.delete()` | `DELETE /siptrunk` | `SIPTrunkDeleteRequest` → empty |
| `qb.sip_trunks.status()` | `GET /siptrunk/statuschecker` | `SIPTrunkStatusRequest` → `SIPTrunkStatusResponse` |
| `qb.sip_trunks.block_caller()` | `POST /siptrunk/blockcaller` | `BlockCallerRequest` → empty/warning |
| `qb.sip_trunks.blocked_callers()` | `GET /siptrunk/blockedcallers` | `BlockedCallersRequest` → `BlockedCallersResponse` |
