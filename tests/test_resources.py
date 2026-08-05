from __future__ import annotations

from typing import Any

import pytest

from questblue import LNPCheckRequest
from questblue._resources import (
    DLC,
    LNP,
    SMS,
    Account,
    DIDs,
    EnterpriseFax,
    Fax,
    InternationalDIDs,
    Reports,
    Servers,
    SIPTrunks,
)


class Recorder:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, Any, Any]] = []

    def request(self, method: str, path: str, *, params: Any = None, json: Any = None) -> dict:
        self.calls.append((method, path, params, json))
        if path == "/did/states":
            return {"data": [], "total": 0}
        if path == "/didinter/countrylist":
            return {"data": [], "total": 0}
        if path == "/sms/history":
            return {"data": [], "total": 0, "total_pages": 0, "current_page": 1}
        if path == "/lnp/check":
            return {"data": {"foc_days": 3}}
        if path == "/server/listbackups":
            return {"data": [], "total": 0}
        return {}


@pytest.mark.parametrize(
    ("resource_type", "method_name", "expected"),
    [
        (Account, "callback_status", ("GET", "/account/callbackstatus")),
        (DIDs, "states", ("GET", "/did/states")),
        (InternationalDIDs, "countries", ("GET", "/didinter/countrylist")),
        (SIPTrunks, "blocked_callers", ("GET", "/siptrunk/blockedcallers")),
        (SMS, "history", ("GET", "/sms/history")),
        (DLC, "list_brands", ("GET", "/dlc/brand")),
        (Fax, "states", ("GET", "/fax/states")),
        (EnterpriseFax, "list_users", ("GET", "/fax2/user")),
        (Reports, "fax_history", ("GET", "/faxhistory")),
        (LNP, "check", ("GET", "/lnp/check")),
        (Servers, "list_backups", ("GET", "/server/listbackups")),
    ],
)
def test_resource_groups_route_to_expected_endpoints(
    resource_type: type[Any], method_name: str, expected: tuple[str, str]
) -> None:
    recorder = Recorder()
    resource = resource_type(recorder)
    if resource_type is LNP:
        getattr(resource, method_name)(LNPCheckRequest(number2port=[15551234567]))
    elif resource_type is Servers:
        getattr(resource, method_name)(1)
    else:
        getattr(resource, method_name)()
    assert recorder.calls[0][:2] == expected
