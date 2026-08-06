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
