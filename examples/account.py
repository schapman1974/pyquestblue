"""User Account examples designed to be imported into applications."""

from __future__ import annotations

from decimal import Decimal
from typing import Union

from questblue import (
    AccountBalanceResponse,
    AsyncQuestBlue,
    CallbackSection,
    InternationalRatesResponse,
    QuestBlue,
    WarningResponse,
)


def current_balance(client: QuestBlue) -> Decimal:
    """Read the current balance for monitoring without performing a mutation."""
    result = client.account.balance()
    if isinstance(result, WarningResponse):
        raise RuntimeError("QuestBlue returned a warning: " + "; ".join(result.warning))
    return result.data.balance


def rates_for_country(client: QuestBlue, country_id: int) -> InternationalRatesResponse:
    """Look up international rates for a country ID from ``countries()``."""
    result = client.account.country_rate(country_id)
    if isinstance(result, WarningResponse):
        raise RuntimeError("QuestBlue returned a warning: " + "; ".join(result.warning))
    return result


def configure_inventory_callback(client: QuestBlue, url: str) -> None:
    """Configure inventory callbacks; this changes account configuration."""
    warning = client.account.configure_callback(
        url,
        [CallbackSection.DID, CallbackSection.SMS, CallbackSection.TRUNK],
    )
    if warning is not None:
        raise RuntimeError("QuestBlue returned a warning: " + "; ".join(warning.warning))


async def async_current_balance(client: AsyncQuestBlue) -> Decimal:
    """Async equivalent of :func:`current_balance`."""
    result = await client.account.balance()
    if isinstance(result, WarningResponse):
        raise RuntimeError("QuestBlue returned a warning: " + "; ".join(result.warning))
    return result.data.balance


def require_balance_response(
    result: Union[AccountBalanceResponse, WarningResponse],
) -> AccountBalanceResponse:
    """Narrow a warning-aware result for application code."""
    if isinstance(result, WarningResponse):
        raise RuntimeError("QuestBlue returned a warning: " + "; ".join(result.warning))
    return result
