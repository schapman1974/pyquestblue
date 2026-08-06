"""Errors specific to the ergonomic QuestBlue facade."""

from __future__ import annotations

from questblue._exceptions import QuestBlueError
from questblue.models import WarningResponse


class QuestBlueWarningError(QuestBlueError):
    """A successful HTTP response contained a provider warning instead of data."""

    def __init__(self, warning: WarningResponse) -> None:
        self.warning = warning
        message = "; ".join(warning.warning) or "QuestBlue returned a warning"
        super().__init__(message)


class ConfirmationRequiredError(QuestBlueError):
    """An operation was not run because its risk was not explicitly confirmed."""

    def __init__(self, risk: str) -> None:
        self.risk = risk
        super().__init__(f"The {risk!r} risk must be explicitly confirmed")


class MissingProviderIdentifierError(QuestBlueError):
    """QuestBlue reported success without the identifier needed to continue."""

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        super().__init__(f"QuestBlue did not return the required {identifier}")


class DeliveryTimeoutError(QuestBlueError):
    """A bounded delivery wait ended before a terminal provider status."""

    def __init__(self, message_id: str, attempts: int) -> None:
        self.message_id = message_id
        self.attempts = attempts
        super().__init__(
            f"Message {message_id} did not reach a terminal status after {attempts} checks"
        )
