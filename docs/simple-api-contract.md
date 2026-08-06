# Simple API implementation contract

This catalog is the implementation boundary for the additive pyquestblue 1.1 facade. Names may be
refined only by superseding ADR 0002 before their implementation issue merges. Every row must gain
sync and async mapping tests; no row represents a new QuestBlue endpoint.

## Client shape

The intended usage needs no request-model imports:

```text
from questblue import SimpleQuestBlue

with SimpleQuestBlue() as qb:
    balance = qb.account.balance()
    candidates = qb.numbers.search(zip_code="27513", limit=5)
    message_id = qb.messages.send(
        from_number=candidates[0].number,
        to="+15551234567",
        text="Your service is ready.",
        recipient_opted_in=True,
    )
```

Advanced callers retain the complete API through `qb.raw`. `SimpleQuestBlue.wrap(existing)` borrows
a synchronous typed client; `AsyncSimpleQuestBlue.wrap(existing)` does the same for async.

## Read-only helper catalog

| Simple service and helper | Typed operation(s) |
| --- | --- |
| `account.balance` | `account.balance` |
| `account.details` | `account.details` |
| `account.rates` | `account.rates`, `account.country_rate`, `account.zone_2_rates`, `account.international_toll_free_rates` |
| `numbers.search` | `dids.available`; discovery support from `dids.states` and `dids.rate_centers` |
| `numbers.list` | `dids.list`, `dids.pages` |
| `numbers.validate_fraud` | `dids.validate_fraud` |
| `international_numbers.countries` | `international_dids.countries` |
| `international_numbers.cities` | `international_dids.cities` |
| `international_numbers.list` | `international_dids.list`, `international_dids.pages` |
| `voice.trunks` | `sip_trunks.list` |
| `voice.trunk_status` | `sip_trunks.status` |
| `voice.blocked_callers` | `sip_trunks.blocked_callers` |
| `messages.numbers` | `sms.list` |
| `messages.history` | `sms.history` |
| `messages.delivery_status` | `sms.delivery_status` |
| `messages.wait_for_delivery` | bounded calls to `sms.delivery_status` |
| `messages.carrier` | `sms.carrier` |
| `messages.offnet_status` | `sms.offnet_status` |
| `dlc.brands` | `dlc.list_brands` |
| `dlc.campaigns` | `dlc.list_campaigns` |
| `fax.search` | `fax.available`; discovery support from `fax.states` and `fax.rate_centers` |
| `fax.list` | `fax.list` |
| `enterprise_fax.list` | `enterprise_fax.list` |
| `enterprise_fax.groups` | `enterprise_fax.list_groups` |
| `enterprise_fax.users` | `enterprise_fax.list_users` |
| `enterprise_fax.permissions` | `enterprise_fax.list_permissions` and `enterprise_fax.list_emails` |
| `reports.calls` | `reports.call_history`, `reports.iter_call_history` |
| `reports.faxes` | `reports.fax_history`, `reports.iter_fax_history` |
| `reports.download_fax` | `reports.download_fax`, `reports.download_fax_to` |
| `reports.export_calls_csv` | `reports.iter_call_history` plus the standard-library CSV writer |
| `reports.export_faxes_csv` | `reports.iter_fax_history` plus the standard-library CSV writer |
| `porting.check` | `lnp.check` |
| `porting.list` | `lnp.list` |
| `servers.list` | `servers.list` |
| `servers.backups` | `servers.list_backups` |

## Mutation helper catalog

| Simple service and helper | Typed operation(s) | Required risk gate |
| --- | --- | --- |
| `account.configure_alerts` | low/daily balance alert and balance-reload methods | routing change |
| `account.configure_callbacks` | `account.configure_callback` | routing change |
| `account.configure_refill` | autorefill and `account.refill_balance` methods | billable |
| `numbers.buy` | `dids.order` | billable |
| `numbers.configure` | `dids.update` | routing change; compliance when E911/DLDA changes |
| `numbers.move_to_fax` | `dids.move_to_fax` | routing change |
| `numbers.release` | `dids.delete` | destructive |
| `international_numbers.buy` | `international_dids.order` | billable |
| `international_numbers.configure` | `international_dids.update` | routing change |
| `international_numbers.release` | `international_dids.delete` | destructive |
| `voice.create_registration_trunk` | `sip_trunks.create` | routing change |
| `voice.create_static_trunk` | `sip_trunks.create` | routing change |
| `voice.configure_trunk` | `sip_trunks.update` | routing change |
| `voice.delete_trunk` | `sip_trunks.delete` | destructive |
| `voice.set_caller_block` | `sip_trunks.block_caller` | routing change |
| `messages.send` | `sms.send` | consent required |
| `messages.configure` | `sms.update` | routing change |
| `messages.set_offnet` | `sms.offnet_order` | billable or routing change, based on action |
| `dlc.create_brand` / `update_brand` / `delete_brand` | matching `dlc` brand methods | compliance sensitive; delete is destructive |
| `dlc.create_campaign` / `update_campaign` / `delete_campaign` | matching `dlc` campaign methods | compliance sensitive; delete is destructive |
| `fax.buy` | `fax.create` | billable |
| `fax.configure` | `fax.update`, `fax.pause` | routing change |
| `fax.send` | `fax.send` | destination confirmation |
| `fax.set_email_access` | fax email-permission methods | routing change |
| `fax.move_to_voice` | `fax.move_to_voice` | routing change |
| `fax.release` | `fax.delete` | destructive |
| `enterprise_fax.buy` / `configure` / `release` | matching enterprise-fax DID methods | billable, routing change, or destructive |
| `enterprise_fax.create_group` / `configure_group` / `delete_group` | matching group methods | delete is destructive |
| `enterprise_fax.create_user` / `configure_user` / `delete_user` | matching user methods | delete is destructive |
| `enterprise_fax.set_permission` | enterprise-fax permission and email-permission methods | routing change |
| `enterprise_fax.upload` / `send` | `enterprise_fax.upload`, `enterprise_fax.send` | destination confirmation for send |
| `porting.create_draft` | `lnp.create` with draft status | compliance sensitive |
| `porting.configure` / `delete` | `lnp.update`, `lnp.delete` | compliance sensitive; delete is destructive |
| `servers.provision` | `servers.create` | billable |
| `servers.add_ip` / `remove_ip` | matching server IP methods | routing change |
| `servers.upgrade` | `servers.upgrade` | billable or destructive |
| `servers.schedule_backups` | `servers.manage_backup_schedule` | routing change |
| `servers.restore` / `remove_backup` / `release` | matching server methods | destructive |

## Composite workflow catalog

| Workflow | Ordered typed operations | Required behavior |
| --- | --- | --- |
| `workflows.provision_voice_number` | explicit DID selection; trunk create/update; DID order; DID route update if required | preview, billable plus routing confirmation, partial journal |
| `workflows.provision_fax_number` | explicit DID selection; fax create; optional email permission | preview, billable plus routing confirmation, partial journal |
| `workflows.onboard_enterprise_fax` | group create; user create; DID create; permission set | preview, billable confirmation, provider IDs, recovery guidance |
| `workflows.send_enterprise_fax` | one upload per file; enterprise fax send | destination confirmation, uploaded file IDs on failure |
| `workflows.prepare_porting_draft` | portability check; local bill validation; LNP draft create | compliance confirmation, never implicit submission |
| `workflows.provision_server` | server create; optional IP and backup schedule configuration | billable/routing confirmations and uncertain-outcome handling |

## Before and after

The simple call replaces model construction but delegates to the same typed method:

```text
# Typed 1.0 API
result = qb.sms.send(
    SendMessageRequest(did=19195550100, did_to=15551234567, msg="Hello")
)

# Simple 1.1 API
message_id = simple.messages.send(
    from_number="+1 919 555 0100",
    to="+1 555 123 4567",
    text="Hello",
    recipient_opted_in=True,
)
```

```text
# Typed 1.0 API
request = DIDAvailabilityRequest(did_type=DIDType.LOCAL, zip=27513, total_list=5)
candidates = qb.dids.available(request)

# Simple 1.1 API
candidates = simple.numbers.search(zip_code="27513", limit=5)
```

```text
# Typed 1.0 API requires group, user, DID, and permission request models and calls.

# Simple 1.1 API returns an inspectable plan before any mutation.
plan = simple.workflows.onboard_enterprise_fax(
    number="+1 919 555 0100",
    group="acme",
    user_email="owner@example.com",
)
result = plan.execute(confirm_billable=True)
```

## Implementation gates

- A helper is not complete until sync and async variants, mapping tests, failure tests, and docs land.
- The abstraction coverage report must reject an unknown typed-method mapping or missing parity.
- Simple helpers never count as additional QuestBlue operation coverage; the pinned 103-operation
  contract remains authoritative.
- Any proposed helper whose upstream behavior is undocumented stays out of the implementation until
  evidence is added to the pinned contract or sanitized fixtures.
