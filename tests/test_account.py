from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict

import httpx
import pytest
from pydantic import ValidationError

from examples.account import (
    async_current_balance,
    configure_inventory_callback,
    current_balance,
    rates_for_country,
)
from questblue import (
    AccountActionResponse,
    AccountBalanceResponse,
    AccountDetailsResponse,
    AccountToggle,
    AsyncQuestBlue,
    CallbackSection,
    CallbackStatusResponse,
    CountryListResponse,
    InternationalRatesResponse,
    InternationalTollFreeRatesResponse,
    PaymentMode,
    QuestBlue,
    QuestBlueAPIError,
    QuestBlueResponseError,
    QuestBlueServerError,
    ServiceRates,
    WarningResponse,
)


def account_response(request: httpx.Request) -> httpx.Response:
    payloads: Dict[str, Any] = {
        "/account/getbalance": {
            "data": {"balance": "12.50", "allowed_credit": "5.00", "future_field": "kept"}
        },
        "/account/getaccoundetails": {
            "data": [
                {
                    "balance": "12.50",
                    "minimum_balance": "25",
                    "reload_amount": "50",
                    "payment_method": "future-payment-rail",
                    "low_balance_alert_amount": "15",
                    "balance_autorefill": "on",
                    "balance_notify": "off",
                }
            ]
        },
        "/account/rates": {
            "local_did_cost": "0.50",
            "inbound_call_rate": "0.01",
            "vps_server_rate": "25.00",
            "ccrf": "0.002",
        },
        "/account/countrylist": {"data": [{"country_id": 44, "country_name": "United Kingdom"}]},
        "/account/countryrate": {
            "data": [{"destination": "United Kingdom", "code": "44", "rate": "0.02"}]
        },
        "/account/ratezone2": {
            "data": [{"destination": "Zone Two", "code": "999", "rate": "0.03"}]
        },
        "/account/nonusintfrate": {
            "data": [{"origin": "United Kingdom", "code": "44800", "rate": "0.04"}]
        },
        "/account/setlowbalancealert": {"data": ""},
        "/account/setdailybalancealert": {"data": ""},
        "/account/callbackstatus": {
            "data": [{"url": "https://example.test/events", "sections": "did,sms,trunk"}]
        },
    }
    return (
        httpx.Response(200, json=payloads[request.url.path])
        if request.url.path in payloads
        else httpx.Response(200)
    )


def make_client() -> QuestBlue:
    http = httpx.Client(
        base_url="https://example.test", transport=httpx.MockTransport(account_response)
    )
    return QuestBlue("user", "password", "key", http_client=http)


def test_all_sync_account_reads_return_typed_models() -> None:
    client = make_client()

    balance = client.account.balance()
    details = client.account.details()
    rates = client.account.rates()
    countries = client.account.countries()
    country_rates = client.account.country_rate(44)
    zone_rates = client.account.zone_2_rates()
    toll_free_rates = client.account.international_toll_free_rates()
    callback = client.account.callback_status()

    assert isinstance(balance, AccountBalanceResponse)
    assert balance.data.balance == Decimal("12.50")
    assert balance.data.extra_fields == {"future_field": "kept"}
    assert isinstance(details, AccountDetailsResponse)
    assert details.data[0].payment_method.value == "future-payment-rail"
    assert isinstance(rates, ServiceRates)
    assert rates.inbound_call_rate == Decimal("0.01")
    assert isinstance(countries, CountryListResponse)
    assert countries.data[0].country_id == 44
    assert isinstance(country_rates, InternationalRatesResponse)
    assert country_rates.data[0].code == "44"
    assert isinstance(zone_rates, InternationalRatesResponse)
    assert isinstance(toll_free_rates, InternationalTollFreeRatesResponse)
    assert isinstance(callback, CallbackStatusResponse)


def test_all_sync_account_mutations_send_documented_parameters() -> None:
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path in (
            "/account/setlowbalancealert",
            "/account/setdailybalancealert",
        ):
            return httpx.Response(200, json={"data": ""})
        return httpx.Response(200)

    http = httpx.Client(base_url="https://example.test", transport=httpx.MockTransport(handler))
    client = QuestBlue("user", "password", "key", http_client=http)

    assert client.account.set_auto_refill(AccountToggle.ON) is None
    assert client.account.set_balance_reload(25, 50) is None
    assert client.account.refill_balance(10, mode=PaymentMode.ACH) is None
    low = client.account.set_low_balance_alert(15)
    daily = client.account.set_daily_balance_alert(AccountToggle.OFF)
    assert (
        client.account.configure_callback(
            "https://example.test/events", [CallbackSection.DID, CallbackSection.SMS]
        )
        is None
    )

    assert isinstance(low, AccountActionResponse)
    assert isinstance(daily, AccountActionResponse)
    assert [
        (request.method, request.url.path, dict(request.url.params)) for request in requests
    ] == [
        ("PUT", "/account/setautorefill", {"autorefill": "on"}),
        ("PUT", "/account/setbalancereload", {"min_balance": "25", "reload_amount": "50"}),
        ("PUT", "/account/refillbalance", {"amount": "10", "Mode": "ach"}),
        ("PUT", "/account/setlowbalancealert", {"low_balance_alert_amount": "15"}),
        ("PUT", "/account/setdailybalancealert", {"action": "off"}),
        (
            "POST",
            "/account/callbackconfig",
            {"url": "https://example.test/events", "sections": "did,sms"},
        ),
    ]


async def test_all_async_account_operations_have_typed_parity() -> None:
    http = httpx.AsyncClient(
        base_url="https://example.test", transport=httpx.MockTransport(account_response)
    )
    client = AsyncQuestBlue("user", "password", "key", http_client=http)

    assert isinstance(await client.account.balance(), AccountBalanceResponse)
    assert isinstance(await client.account.details(), AccountDetailsResponse)
    assert isinstance(await client.account.rates(), ServiceRates)
    assert isinstance(await client.account.countries(), CountryListResponse)
    assert isinstance(await client.account.country_rate(44), InternationalRatesResponse)
    assert isinstance(await client.account.zone_2_rates(), InternationalRatesResponse)
    assert isinstance(
        await client.account.international_toll_free_rates(),
        InternationalTollFreeRatesResponse,
    )
    assert await client.account.set_auto_refill(AccountToggle.ON) is None
    assert await client.account.set_balance_reload(25, 50) is None
    assert await client.account.refill_balance(10, mode=PaymentMode.CREDIT_CARD) is None
    assert isinstance(await client.account.set_low_balance_alert(15), AccountActionResponse)
    assert isinstance(
        await client.account.set_daily_balance_alert(AccountToggle.ON), AccountActionResponse
    )
    assert (
        await client.account.configure_callback(
            "https://example.test/events", [CallbackSection.DID]
        )
        is None
    )
    assert isinstance(await client.account.callback_status(), CallbackStatusResponse)
    await http.aclose()


@pytest.mark.parametrize(
    "call",
    [
        lambda client: client.account.country_rate(0),
        lambda client: client.account.refill_balance(9),
        lambda client: client.account.set_balance_reload(10, 50),  # type: ignore[arg-type]
        lambda client: client.account.set_balance_reload(25, 55),  # type: ignore[arg-type]
        lambda client: client.account.set_low_balance_alert(-1),
        lambda client: client.account.configure_callback("not-a-url", [CallbackSection.DID]),
        lambda client: client.account.configure_callback("https://example.test", "did,unknown"),
    ],
)
def test_account_request_validation(call: Any) -> None:
    with pytest.raises((ValidationError, ValueError)):
        call(make_client())


def test_warning_empty_and_error_responses() -> None:
    def warning(_: httpx.Request) -> httpx.Response:
        return httpx.Response(202, json={"warning": ["processed with caveat"]})

    warning_client = QuestBlue(
        "user",
        "password",
        "key",
        http_client=httpx.Client(
            base_url="https://example.test", transport=httpx.MockTransport(warning)
        ),
    )
    assert isinstance(warning_client.account.balance(), WarningResponse)
    assert isinstance(
        warning_client.account.configure_callback("", ""),
        WarningResponse,
    )

    def error(_: httpx.Request) -> httpx.Response:
        return httpx.Response(206, json={"error": "account rejected"})

    error_client = QuestBlue(
        "user",
        "password",
        "key",
        http_client=httpx.Client(
            base_url="https://example.test", transport=httpx.MockTransport(error)
        ),
    )
    with pytest.raises(QuestBlueAPIError, match="account rejected") as caught:
        error_client.account.details()
    assert caught.value.error is not None
    assert caught.value.error.error == "account rejected"


def test_empty_account_operation_rejects_an_undocumented_body() -> None:
    client = QuestBlue(
        "user",
        "password",
        "key",
        http_client=httpx.Client(
            base_url="https://example.test",
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"unexpected": True})),
        ),
    )

    with pytest.raises(QuestBlueResponseError, match="empty account response"):
        client.account.refill_balance(10)


def test_refill_is_not_retried_after_an_uncertain_server_response() -> None:
    attempts = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503, json={"error": "uncertain"})

    client = QuestBlue(
        "user",
        "password",
        "key",
        max_retries=10,
        http_client=httpx.Client(
            base_url="https://example.test", transport=httpx.MockTransport(handler)
        ),
    )

    with pytest.raises(QuestBlueServerError):
        client.account.refill_balance(10)
    assert attempts == 1


def test_account_examples_are_executable() -> None:
    client = make_client()

    assert current_balance(client) == Decimal("12.50")
    assert rates_for_country(client, 44).data[0].rate == Decimal("0.02")
    configure_inventory_callback(client, "https://example.test/events")


async def test_async_account_example_is_executable() -> None:
    http = httpx.AsyncClient(
        base_url="https://example.test", transport=httpx.MockTransport(account_response)
    )
    client = AsyncQuestBlue("user", "password", "key", http_client=http)

    assert await async_current_balance(client) == Decimal("12.50")
    await http.aclose()
