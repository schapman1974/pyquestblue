# User Account API

The account resource covers all 14 operations in QuestBlue API 2.3.2. Every response is validated,
unknown response fields are preserved, and monetary strings are exposed as `Decimal` values.

## Balance monitoring

```python
from questblue import QuestBlue, WarningResponse

with QuestBlue() as qb:
    result = qb.account.balance()
    if isinstance(result, WarningResponse):
        print(result.warning)
    else:
        print(result.data.balance, result.data.allowed_credit)
```

`qb.account.details()` returns balance thresholds, the reload amount, payment method, and current
alert/autorefill flags. Both balance operations are safe reads and may use the configured retry
policy.

## Rate lookup

Discover a country ID before requesting its rates:

```python
countries = qb.account.countries()
rates = qb.account.country_rate(44)
zone_two = qb.account.zone_2_rates()
toll_free = qb.account.international_toll_free_rates()
service_rates = qb.account.rates()
```

The five methods return typed country, international-rate, toll-free-rate, or service-rate models.
Rate and cost fields are `Decimal`, avoiding binary floating-point surprises.

## Balance and alert configuration

These methods change account settings:

```python
from questblue import AccountToggle, PaymentMode

qb.account.set_auto_refill(AccountToggle.ON)
qb.account.set_balance_reload(25, 50)
qb.account.set_low_balance_alert(15)
qb.account.set_daily_balance_alert(AccountToggle.ON)
```

`qb.account.refill_balance(25, mode=PaymentMode.CREDIT_CARD)` charges a payment method and adds funds
to the account. It is a billable operation. Confirm the amount and account before calling it.

Refills, autorefill changes, alert changes, and all other mutations are attempted exactly once.
They are never retried automatically because QuestBlue does not document idempotency. A timeout or
connection failure can therefore have an uncertain outcome; inspect the account before attempting
the action again.

The legacy `mode` field is included because it remains in the upstream contract, which says it is
no longer in use. Prefer omitting it unless QuestBlue support instructs otherwise. Documented
minimum-balance and reload-amount choices validate locally, and refill amounts must be at least $10.

## Inventory callback configuration

```python
from questblue import CallbackSection

qb.account.configure_callback(
    "https://portal.example.com/hooks/questblue",
    [CallbackSection.DID, CallbackSection.SMS, CallbackSection.TRUNK],
)
status = qb.account.callback_status()
```

Pass `"", ""` to `qb.account.configure_callback()` to unset the callback, matching the upstream
contract. Callback URLs must otherwise be absolute HTTP(S) URLs. The SDK configures the destination
only. QuestBlue's public 2.3.2 contract does not specify callback authentication, retries, ordering,
or duplicate-delivery behavior. The webhook helpers therefore make no authenticity claim and expose
a stable fingerprint for application-level deduplication. See
[Webhooks and integrations](integrations.md) for the explicit trust boundary.

## Async usage

Every method has an async equivalent with the same parameters, models, validation, warnings, and
retry safety:

```python
from questblue import AsyncQuestBlue

async with AsyncQuestBlue() as qb:
    balance = await qb.account.balance()
    rates = await qb.account.country_rate(44)
    callback = await qb.account.callback_status()
```

## Operation reference

| SDK method | HTTP operation | Request model | Success response |
| --- | --- | --- | --- |
| `qb.account.balance()` | `GET /account/getbalance` | — | `AccountBalanceResponse` |
| `qb.account.details()` | `GET /account/getaccoundetails` | — | `AccountDetailsResponse` |
| `qb.account.rates()` | `GET /account/rates` | — | `ServiceRates` |
| `qb.account.countries()` | `GET /account/countrylist` | — | `CountryListResponse` |
| `qb.account.country_rate()` | `GET /account/countryrate` | `CountryRateRequest` | `InternationalRatesResponse` |
| `qb.account.zone_2_rates()` | `GET /account/ratezone2` | — | `InternationalRatesResponse` |
| `qb.account.international_toll_free_rates()` | `GET /account/nonusintfrate` | — | `InternationalTollFreeRatesResponse` |
| `qb.account.set_auto_refill()` | `PUT /account/setautorefill` | `SetAutorefillRequest` | empty |
| `qb.account.set_balance_reload()` | `PUT /account/setbalancereload` | `SetBalanceReloadRequest` | empty |
| `qb.account.refill_balance()` | `PUT /account/refillbalance` | `RefillBalanceRequest` | empty |
| `qb.account.set_low_balance_alert()` | `PUT /account/setlowbalancealert` | `SetLowBalanceAlertRequest` | `AccountActionResponse` |
| `qb.account.set_daily_balance_alert()` | `PUT /account/setdailybalancealert` | `SetDailyBalanceAlertRequest` | `AccountActionResponse` |
| `qb.account.configure_callback()` | `POST /account/callbackconfig` | `CallbackConfigRequest` | empty |
| `qb.account.callback_status()` | `GET /account/callbackstatus` | — | `CallbackStatusResponse` |

Any operation may return `WarningResponse` for an HTTP 202 warning. HTTP 206 and other unsuccessful
responses raise the typed transport exceptions described in [transport.md](transport.md). When an
error body contains QuestBlue's documented `error` string, `QuestBlueAPIError.error` contains a
validated `ErrorResponse` while `QuestBlueAPIError.body` retains the original payload.
