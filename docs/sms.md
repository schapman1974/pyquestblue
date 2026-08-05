# SMS, MMS, and Carrier API

All eight documented messaging operations have validated synchronous and asynchronous methods.
Requests use model objects so phone numbers, media URLs, modes, filters, and IDs are checked before
QuestBlue is called.

## Send SMS or MMS

```python
from questblue import SendMessageRequest

result = qb.sms.send(
    SendMessageRequest(
        did=15551234567,
        did_to=15557654321,
        msg="Your requested appointment reminder",
        file_url=["https://cdn.example.com/reminder.jpg"],  # omit for SMS
    )
)
message_id = result.data[0].msg_id
```

Media URLs must be absolute HTTP(S) URLs without embedded credentials. Literal private, loopback,
and reserved IP hosts are rejected because QuestBlue cannot retrieve them as public MMS media.
Multiple URLs serialize using QuestBlue's comma-separated array convention.

`SendMessageRequest`, settings credentials, carrier numbers, and history endpoints suppress message
bodies, phone numbers, URLs, and passwords from model representations and validation diagnostics.
Transport events contain only the endpoint path, never its query string. Explicit `model_dump()`
calls still return the values so applications can send the request; do not log those dictionaries.

## Inventory and inbound settings

```python
from questblue import SMSMode, SMSSettingsUpdateRequest

inventory = qb.sms.list()
qb.sms.update(
    SMSSettingsUpdateRequest(
        did=15551234567,
        sms_mode=SMSMode.URL,
        post2url="https://app.example.com/questblue/inbound",
    )
)
```

The SDK enforces each mode's dependent fields: email needs `forward2email`; XMPP needs a username
and password; `both` needs all three; URL needs `post2url`; chat needs email/password; and Yeastar
needs `secret`. Settings mutations are not retried automatically.

## History, delivery, off-net, and carrier lookup

History accepts preset periods or an inclusive pair of dates. Direction, SMS/MMS type, order,
page, and page size are typed. Delivery and off-net status enums preserve new provider values.

```python
from datetime import date
from questblue import (
    CarrierLookupRequest,
    MessageDeliveryStatusRequest,
    SMSHistoryRequest,
)

history = qb.sms.history(SMSHistoryRequest(period=(date(2026, 8, 1), date(2026, 8, 5)), page=1))
delivery = qb.sms.delivery_status(MessageDeliveryStatusRequest(msg_id=9001))
carriers = qb.sms.carrier(CarrierLookupRequest(tn=[15551234567, 15557654321]))
```

Off-net `add` requests may be billable and `remove` requests disable service. Sending messages is
compliance-sensitive: obtain and retain recipient consent, honor opt-outs, identify the sender when
required, follow quiet-hour and content rules, and complete applicable 10DLC registration. This SDK
does not determine whether a message is legally permitted. Use a QuestBlue-approved test account;
the public API documentation does not identify a general-purpose sandbox.

See `examples/sms.py` for an executable consent-gated send/status workflow.

| SDK method | Operation | Models |
| --- | --- | --- |
| `qb.sms.list()` | `GET /sms` | `SMSInventoryRequest` → `SMSInventoryResponse` |
| `qb.sms.send()` | `POST /smsv2` | `SendMessageRequest` → `SendMessageResponse` |
| `qb.sms.update()` | `PUT /smsv2` | `SMSSettingsUpdateRequest` → `SMSSettingsUpdateResponse` |
| `qb.sms.offnet_order()` | `POST /sms/offnetorder` | `OffnetOrderRequest` → empty/warning |
| `qb.sms.offnet_status()` | `GET /sms/offnetstatus` | `OffnetStatusRequest` → `OffnetStatusResponse` |
| `qb.sms.history()` | `GET /sms/history` | `SMSHistoryRequest` → `SMSHistoryResponse` |
| `qb.sms.delivery_status()` | `GET /sms/deliverystatus` | `MessageDeliveryStatusRequest` → `MessageDeliveryStatusResponse` |
| `qb.sms.carrier()` | `GET /smschecktncarrier` | `CarrierLookupRequest` → `CarrierLookupResponse` |
