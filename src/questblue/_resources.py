"""Resource-oriented wrappers for every documented QuestBlue API endpoint."""

from __future__ import annotations

import base64
from typing import Any, List, Mapping, Optional, Union


class Resource:
    def __init__(self, client: Any) -> None:
        self._client = client

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Mapping[str, Any]] = None,
        *,
        json: Any = None,
    ) -> Any:
        return self._client.request(method, path, params=params, json=json)


class Account(Resource):
    def balance(self) -> Any:
        return self._request("GET", "/account/getbalance")

    def details(self) -> Any:
        return self._request("GET", "/account/getaccoundetails")

    def rates(self, **params: Any) -> Any:
        return self._request("GET", "/account/rates", params)

    def countries(self) -> Any:
        return self._request("GET", "/account/countrylist")

    def country_rate(self, **params: Any) -> Any:
        return self._request("GET", "/account/countryrate", params)

    def zone_2_rates(self, **params: Any) -> Any:
        return self._request("GET", "/account/ratezone2", params)

    def international_toll_free_rates(self, **params: Any) -> Any:
        return self._request("GET", "/account/nonusintfrate", params)

    def set_auto_refill(self, **params: Any) -> Any:
        return self._request("PUT", "/account/setautorefill", params)

    def set_balance_reload(self, **params: Any) -> Any:
        return self._request("PUT", "/account/setbalancereload", params)

    def refill_balance(self, **params: Any) -> Any:
        return self._request("PUT", "/account/refillbalance", params)

    def set_low_balance_alert(self, **params: Any) -> Any:
        return self._request("PUT", "/account/setlowbalancealert", params)

    def set_daily_balance_alert(self, **params: Any) -> Any:
        return self._request("PUT", "/account/setdailybalancealert", params)

    def configure_callback(self, **params: Any) -> Any:
        return self._request("POST", "/account/callbackconfig", params)

    def callback_status(self) -> Any:
        return self._request("GET", "/account/callbackstatus")


class DIDs(Resource):
    def list(self, **params: Any) -> Any:
        return self._request("GET", "/did", params)

    def order(self, did: Union[int, List[int]], **params: Any) -> Any:
        return self._request("POST", "/did", {"did": did, **params})

    def update(self, did: int, **params: Any) -> Any:
        return self._request("PUT", "/did", {"did": did, **params})

    def delete(self, did: int) -> Any:
        return self._request("DELETE", "/did", {"did": did})

    def states(self) -> Any:
        return self._request("GET", "/did/states")

    def rate_centers(self, **params: Any) -> Any:
        return self._request("GET", "/did/ratecenters", params)

    def available(self, **params: Any) -> Any:
        return self._request("GET", "/did/available", params)

    def move_to_fax(self, did: int) -> Any:
        return self._request("PUT", "/did/move2fax", {"did": did})

    def validate_fraud(self, tn: Union[int, List[int]]) -> Any:
        return self._request("POST", "/did/fraudvalidate", {"tn": tn})


class InternationalDIDs(Resource):
    def countries(self) -> Any:
        return self._request("GET", "/didinter/countrylist")

    def cities(self, **params: Any) -> Any:
        return self._request("GET", "/didinter/citylist", params)

    def list(self, **params: Any) -> Any:
        return self._request("GET", "/didinter", params)

    def order(self, **params: Any) -> Any:
        return self._request("POST", "/didinter", params)

    def update(self, **params: Any) -> Any:
        return self._request("PUT", "/didinter", params)

    def delete(self, **params: Any) -> Any:
        return self._request("DELETE", "/didinter", params)


class SIPTrunks(Resource):
    def list(self, **params: Any) -> Any:
        return self._request("GET", "/siptrunk", params)

    def create(self, **params: Any) -> Any:
        return self._request("POST", "/siptrunk", params)

    def update(self, **params: Any) -> Any:
        return self._request("PUT", "/siptrunk", params)

    def delete(self, **params: Any) -> Any:
        return self._request("DELETE", "/siptrunk", params)

    def status(self, **params: Any) -> Any:
        return self._request("GET", "/siptrunk/statuschecker", params)

    def block_caller(self, **params: Any) -> Any:
        return self._request("POST", "/siptrunk/blockcaller", params)

    def blocked_callers(self, **params: Any) -> Any:
        return self._request("GET", "/siptrunk/blockedcallers", params)


class SMS(Resource):
    def list(self, **params: Any) -> Any:
        return self._request("GET", "/sms", params)

    def send(self, did: int, did_to: int, msg: str, **params: Any) -> Any:
        return self._request("POST", "/smsv2", {"did": did, "did_to": did_to, "msg": msg, **params})

    def update(self, **params: Any) -> Any:
        return self._request("PUT", "/smsv2", params)

    def offnet_order(self, **params: Any) -> Any:
        return self._request("POST", "/sms/offnetorder", params)

    def offnet_status(self, **params: Any) -> Any:
        return self._request("GET", "/sms/offnetstatus", params)

    def history(self, **params: Any) -> Any:
        return self._request("GET", "/sms/history", params)

    def delivery_status(self, **params: Any) -> Any:
        return self._request("GET", "/sms/deliverystatus", params)

    def carrier(self, **params: Any) -> Any:
        return self._request("GET", "/smschecktncarrier", params)


class DLC(Resource):
    def list_brands(self, **params: Any) -> Any:
        return self._request("GET", "/dlc/brand", params)

    def create_brand(self, **params: Any) -> Any:
        return self._request("POST", "/dlc/brand", params)

    def update_brand(self, **params: Any) -> Any:
        return self._request("PUT", "/dlc/brand", params)

    def delete_brand(self, **params: Any) -> Any:
        return self._request("DELETE", "/dlc/brand", params)

    def list_campaigns(self, **params: Any) -> Any:
        return self._request("GET", "/dlc/campaign", params)

    def create_campaign(self, **params: Any) -> Any:
        return self._request("POST", "/dlc/campaign", params)

    def update_campaign(self, **params: Any) -> Any:
        return self._request("PUT", "/dlc/campaign", params)

    def delete_campaign(self, **params: Any) -> Any:
        return self._request("DELETE", "/dlc/campaign", params)


class Fax(Resource):
    def states(self) -> Any:
        return self._request("GET", "/fax/states")

    def rate_centers(self, **params: Any) -> Any:
        return self._request("GET", "/fax/ratecenters", params)

    def available(self, **params: Any) -> Any:
        return self._request("GET", "/fax/available", params)

    def create(self, **params: Any) -> Any:
        return self._request("POST", "/fax", params)

    def list(self, **params: Any) -> Any:
        return self._request("GET", "/fax", params)

    def update(self, **params: Any) -> Any:
        return self._request("PUT", "/fax", params)

    def delete(self, **params: Any) -> Any:
        return self._request("DELETE", "/fax", params)

    def send(self, **params: Any) -> Any:
        return self._request("POST", "/fax/send", params)

    def move_to_voice(self, **params: Any) -> Any:
        return self._request("PUT", "/fax/move2voice", params)

    def pause(self, **params: Any) -> Any:
        return self._request("PUT", "/fax/pause", params)

    def set_email_permission(self, **params: Any) -> Any:
        return self._request("POST", "/fax/email", params)

    def delete_email_permission(self, **params: Any) -> Any:
        return self._request("DELETE", "/fax/email", params)


class EnterpriseFax(Resource):
    def list(self, **params: Any) -> Any:
        return self._request("GET", "/fax2", params)

    def create(self, **params: Any) -> Any:
        return self._request("POST", "/fax2", params)

    def update(self, **params: Any) -> Any:
        return self._request("PUT", "/fax2", params)

    def delete(self, **params: Any) -> Any:
        return self._request("DELETE", "/fax2", params)

    def list_emails(self, **params: Any) -> Any:
        return self._request("GET", "/fax2/email", params)

    def set_email_permission(self, **params: Any) -> Any:
        return self._request("POST", "/fax2/email", params)

    def delete_email_permission(self, **params: Any) -> Any:
        return self._request("DELETE", "/fax2/email", params)

    def list_groups(self, **params: Any) -> Any:
        return self._request("GET", "/fax2/group", params)

    def create_group(self, **params: Any) -> Any:
        return self._request("POST", "/fax2/group", params)

    def update_group(self, **params: Any) -> Any:
        return self._request("PUT", "/fax2/group", params)

    def delete_group(self, **params: Any) -> Any:
        return self._request("DELETE", "/fax2/group", params)

    def list_users(self, **params: Any) -> Any:
        return self._request("GET", "/fax2/user", params)

    def create_user(self, **params: Any) -> Any:
        return self._request("POST", "/fax2/user", params)

    def update_user(self, **params: Any) -> Any:
        return self._request("PUT", "/fax2/user", params)

    def delete_user(self, **params: Any) -> Any:
        return self._request("DELETE", "/fax2/user", params)

    def list_permissions(self, **params: Any) -> Any:
        return self._request("GET", "/fax2/permit", params)

    def set_permission(self, **params: Any) -> Any:
        return self._request("POST", "/fax2/permit", params)

    def delete_permission(self, **params: Any) -> Any:
        return self._request("DELETE", "/fax2/permit", params)

    def upload(self, file: bytes, filename: str) -> Any:
        payload = {"file": base64.b64encode(file).decode("ascii"), "filename": filename}
        return self._request("POST", "/fax2/upload", json=payload)

    def send(self, **params: Any) -> Any:
        return self._request("POST", "/fax2/send", params)

    def pause(self, **params: Any) -> Any:
        return self._request("PUT", "/fax2/pause", params)


class Reports(Resource):
    def call_history(self, **params: Any) -> Any:
        return self._request("GET", "/callhistory", params)

    def fax_history(self, **params: Any) -> Any:
        return self._request("GET", "/faxhistory", params)

    def download_fax(self, **params: Any) -> Any:
        return self._request("GET", "/faxdownload", params)


class LNP(Resource):
    def check(self, **params: Any) -> Any:
        return self._request("GET", "/lnp/check", params)

    def create(self, **params: Any) -> Any:
        return self._request("POST", "/lnp", params)

    def list(self, **params: Any) -> Any:
        return self._request("GET", "/lnp", params)

    def update(self, **params: Any) -> Any:
        return self._request("PUT", "/lnp", params)

    def delete(self, **params: Any) -> Any:
        return self._request("DELETE", "/lnp", params)


class Servers(Resource):
    def create(self, **params: Any) -> Any:
        return self._request("POST", "/server", params)

    def list(self, **params: Any) -> Any:
        return self._request("GET", "/server", params)

    def delete(self, **params: Any) -> Any:
        return self._request("DELETE", "/server", params)

    def add_ip(self, **params: Any) -> Any:
        return self._request("PUT", "/server/addip", params)

    def remove_ip(self, **params: Any) -> Any:
        return self._request("DELETE", "/server/deleip", params)

    def upgrade(self, **params: Any) -> Any:
        return self._request("POST", "/server/upgrade", params)

    def manage_backup_schedule(self, **params: Any) -> Any:
        return self._request("POST", "/server/managebackupschedule", params)

    def list_backups(self, **params: Any) -> Any:
        return self._request("GET", "/server/listbackups", params)

    def restore_backup(self, **params: Any) -> Any:
        return self._request("POST", "/server/restorebackup", params)

    def remove_backup(self, **params: Any) -> Any:
        return self._request("DELETE", "/server/removebackup", params)


def install_resources(client: Any) -> None:
    """Attach the complete resource tree to a sync or async client."""
    client.account = Account(client)
    client.dids = DIDs(client)
    client.international_dids = InternationalDIDs(client)
    client.sip_trunks = SIPTrunks(client)
    client.sms = SMS(client)
    client.dlc = DLC(client)
    client.fax = Fax(client)
    client.enterprise_fax = EnterpriseFax(client)
    client.reports = Reports(client)
    client.lnp = LNP(client)
    client.servers = Servers(client)
