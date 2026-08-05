"""Resource-oriented wrappers for every documented QuestBlue API endpoint."""

from __future__ import annotations

import base64
from typing import Any, AsyncIterator, Iterator, List, Mapping, Optional, Union

from . import account as account_models
from . import did as did_models
from . import international_did as international_did_models
from . import sip_trunk as sip_models
from .models import WarningResponse


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
    def balance(
        self,
    ) -> Union[account_models.AccountBalanceResponse, WarningResponse]:
        payload = self._request("GET", "/account/getbalance")
        return account_models.parse_account_response(account_models.AccountBalanceResponse, payload)

    def details(
        self,
    ) -> Union[account_models.AccountDetailsResponse, WarningResponse]:
        payload = self._request("GET", "/account/getaccoundetails")
        return account_models.parse_account_response(account_models.AccountDetailsResponse, payload)

    def rates(self) -> Union[account_models.ServiceRates, WarningResponse]:
        payload = self._request("GET", "/account/rates")
        return account_models.parse_account_response(account_models.ServiceRates, payload)

    def countries(self) -> Union[account_models.CountryListResponse, WarningResponse]:
        payload = self._request("GET", "/account/countrylist")
        return account_models.parse_account_response(account_models.CountryListResponse, payload)

    def country_rate(
        self, country_id: int
    ) -> Union[account_models.InternationalRatesResponse, WarningResponse]:
        request = account_models.CountryRateRequest(country_id=country_id)
        payload = self._request("GET", "/account/countryrate", request.to_request_params())
        return account_models.parse_account_response(
            account_models.InternationalRatesResponse, payload
        )

    def zone_2_rates(
        self,
    ) -> Union[account_models.InternationalRatesResponse, WarningResponse]:
        payload = self._request("GET", "/account/ratezone2")
        return account_models.parse_account_response(
            account_models.InternationalRatesResponse, payload
        )

    def international_toll_free_rates(
        self,
    ) -> Union[account_models.InternationalTollFreeRatesResponse, WarningResponse]:
        payload = self._request("GET", "/account/nonusintfrate")
        return account_models.parse_account_response(
            account_models.InternationalTollFreeRatesResponse, payload
        )

    def set_auto_refill(
        self, autorefill: account_models.AccountToggle
    ) -> Optional[WarningResponse]:
        request = account_models.SetAutorefillRequest(autorefill=autorefill)
        payload = self._request("PUT", "/account/setautorefill", request.to_request_params())
        return account_models.parse_empty_account_response(payload)

    def set_balance_reload(
        self,
        min_balance: account_models.MinimumBalance,
        reload_amount: account_models.ReloadAmount,
    ) -> Optional[WarningResponse]:
        request = account_models.SetBalanceReloadRequest(
            min_balance=min_balance, reload_amount=reload_amount
        )
        payload = self._request("PUT", "/account/setbalancereload", request.to_request_params())
        return account_models.parse_empty_account_response(payload)

    def refill_balance(
        self, amount: int, *, mode: Optional[account_models.PaymentMode] = None
    ) -> Optional[WarningResponse]:
        request = account_models.RefillBalanceRequest(amount=amount, mode=mode)
        payload = self._request("PUT", "/account/refillbalance", request.to_request_params())
        return account_models.parse_empty_account_response(payload)

    def set_low_balance_alert(
        self, low_balance_alert_amount: int
    ) -> Union[account_models.AccountActionResponse, WarningResponse]:
        request = account_models.SetLowBalanceAlertRequest(
            low_balance_alert_amount=low_balance_alert_amount
        )
        payload = self._request("PUT", "/account/setlowbalancealert", request.to_request_params())
        return account_models.parse_account_response(account_models.AccountActionResponse, payload)

    def set_daily_balance_alert(
        self, action: account_models.AccountToggle
    ) -> Union[account_models.AccountActionResponse, WarningResponse]:
        request = account_models.SetDailyBalanceAlertRequest(action=action)
        payload = self._request("PUT", "/account/setdailybalancealert", request.to_request_params())
        return account_models.parse_account_response(account_models.AccountActionResponse, payload)

    def configure_callback(
        self, url: str, sections: account_models.CallbackSections
    ) -> Optional[WarningResponse]:
        request = account_models.CallbackConfigRequest.from_values(url, sections)
        payload = self._request("POST", "/account/callbackconfig", request.to_request_params())
        return account_models.parse_empty_account_response(payload)

    def callback_status(
        self,
    ) -> Union[account_models.CallbackStatusResponse, WarningResponse]:
        payload = self._request("GET", "/account/callbackstatus")
        return account_models.parse_account_response(account_models.CallbackStatusResponse, payload)


class AsyncAccount(Resource):
    async def balance(
        self,
    ) -> Union[account_models.AccountBalanceResponse, WarningResponse]:
        payload = await self._request("GET", "/account/getbalance")
        return account_models.parse_account_response(account_models.AccountBalanceResponse, payload)

    async def details(
        self,
    ) -> Union[account_models.AccountDetailsResponse, WarningResponse]:
        payload = await self._request("GET", "/account/getaccoundetails")
        return account_models.parse_account_response(account_models.AccountDetailsResponse, payload)

    async def rates(self) -> Union[account_models.ServiceRates, WarningResponse]:
        payload = await self._request("GET", "/account/rates")
        return account_models.parse_account_response(account_models.ServiceRates, payload)

    async def countries(self) -> Union[account_models.CountryListResponse, WarningResponse]:
        payload = await self._request("GET", "/account/countrylist")
        return account_models.parse_account_response(account_models.CountryListResponse, payload)

    async def country_rate(
        self, country_id: int
    ) -> Union[account_models.InternationalRatesResponse, WarningResponse]:
        request = account_models.CountryRateRequest(country_id=country_id)
        payload = await self._request("GET", "/account/countryrate", request.to_request_params())
        return account_models.parse_account_response(
            account_models.InternationalRatesResponse, payload
        )

    async def zone_2_rates(
        self,
    ) -> Union[account_models.InternationalRatesResponse, WarningResponse]:
        payload = await self._request("GET", "/account/ratezone2")
        return account_models.parse_account_response(
            account_models.InternationalRatesResponse, payload
        )

    async def international_toll_free_rates(
        self,
    ) -> Union[account_models.InternationalTollFreeRatesResponse, WarningResponse]:
        payload = await self._request("GET", "/account/nonusintfrate")
        return account_models.parse_account_response(
            account_models.InternationalTollFreeRatesResponse, payload
        )

    async def set_auto_refill(
        self, autorefill: account_models.AccountToggle
    ) -> Optional[WarningResponse]:
        request = account_models.SetAutorefillRequest(autorefill=autorefill)
        payload = await self._request("PUT", "/account/setautorefill", request.to_request_params())
        return account_models.parse_empty_account_response(payload)

    async def set_balance_reload(
        self,
        min_balance: account_models.MinimumBalance,
        reload_amount: account_models.ReloadAmount,
    ) -> Optional[WarningResponse]:
        request = account_models.SetBalanceReloadRequest(
            min_balance=min_balance, reload_amount=reload_amount
        )
        payload = await self._request(
            "PUT", "/account/setbalancereload", request.to_request_params()
        )
        return account_models.parse_empty_account_response(payload)

    async def refill_balance(
        self, amount: int, *, mode: Optional[account_models.PaymentMode] = None
    ) -> Optional[WarningResponse]:
        request = account_models.RefillBalanceRequest(amount=amount, mode=mode)
        payload = await self._request("PUT", "/account/refillbalance", request.to_request_params())
        return account_models.parse_empty_account_response(payload)

    async def set_low_balance_alert(
        self, low_balance_alert_amount: int
    ) -> Union[account_models.AccountActionResponse, WarningResponse]:
        request = account_models.SetLowBalanceAlertRequest(
            low_balance_alert_amount=low_balance_alert_amount
        )
        payload = await self._request(
            "PUT", "/account/setlowbalancealert", request.to_request_params()
        )
        return account_models.parse_account_response(account_models.AccountActionResponse, payload)

    async def set_daily_balance_alert(
        self, action: account_models.AccountToggle
    ) -> Union[account_models.AccountActionResponse, WarningResponse]:
        request = account_models.SetDailyBalanceAlertRequest(action=action)
        payload = await self._request(
            "PUT", "/account/setdailybalancealert", request.to_request_params()
        )
        return account_models.parse_account_response(account_models.AccountActionResponse, payload)

    async def configure_callback(
        self, url: str, sections: account_models.CallbackSections
    ) -> Optional[WarningResponse]:
        request = account_models.CallbackConfigRequest.from_values(url, sections)
        payload = await self._request(
            "POST", "/account/callbackconfig", request.to_request_params()
        )
        return account_models.parse_empty_account_response(payload)

    async def callback_status(
        self,
    ) -> Union[account_models.CallbackStatusResponse, WarningResponse]:
        payload = await self._request("GET", "/account/callbackstatus")
        return account_models.parse_account_response(account_models.CallbackStatusResponse, payload)


class DIDs(Resource):
    def list(
        self, request: Optional[did_models.DIDListRequest] = None
    ) -> Union[did_models.DIDInventoryResponse, WarningResponse]:
        request = request or did_models.DIDListRequest()
        payload = self._request("GET", "/did", request.to_request_params())
        return did_models.parse_did_response(did_models.DIDInventoryResponse, payload)

    def pages(
        self, request: Optional[did_models.DIDListRequest] = None
    ) -> Iterator[Union[did_models.DIDInventoryResponse, WarningResponse]]:
        request = request or did_models.DIDListRequest()
        page = request.page
        while True:
            result = self.list(request.model_copy(update={"page": page}))
            yield result
            if isinstance(result, WarningResponse):
                return
            next_page = result.next_page()
            if next_page is None:
                return
            page = next_page

    def order(self, request: did_models.DIDOrderRequest) -> Optional[WarningResponse]:
        payload = self._request("POST", "/did", request.to_request_params())
        return did_models.parse_empty_did_response(payload)

    def update(self, request: did_models.DIDUpdateRequest) -> Optional[WarningResponse]:
        payload = self._request("PUT", "/did", request.to_request_params())
        return did_models.parse_empty_did_response(payload)

    def delete(self, did: int) -> Optional[WarningResponse]:
        request = did_models.DIDDeleteRequest(did=did)
        payload = self._request("DELETE", "/did", request.to_request_params())
        return did_models.parse_empty_did_response(payload)

    def states(self) -> Union[did_models.DIDStatesResponse, WarningResponse]:
        payload = self._request("GET", "/did/states")
        return did_models.parse_did_response(did_models.DIDStatesResponse, payload)

    def rate_centers(
        self, state: str, tier: did_models.DIDTier
    ) -> Union[did_models.DIDRateCentersResponse, WarningResponse]:
        request = did_models.DIDRateCentersRequest(state=state, tier=tier)
        payload = self._request("GET", "/did/ratecenters", request.to_request_params())
        return did_models.parse_did_response(did_models.DIDRateCentersResponse, payload)

    def available(
        self, request: did_models.DIDAvailabilityRequest
    ) -> Union[did_models.AvailableDIDsResponse, WarningResponse]:
        payload = self._request("GET", "/did/available", request.to_request_params())
        return did_models.parse_did_response(did_models.AvailableDIDsResponse, payload)

    def move_to_fax(self, did: int) -> Optional[WarningResponse]:
        request = did_models.DIDMoveToFaxRequest(did=did)
        payload = self._request("PUT", "/did/move2fax", request.to_request_params())
        return did_models.parse_empty_did_response(payload)

    def validate_fraud(
        self, tn: Union[int, List[int]]
    ) -> Union[did_models.FraudValidationResponse, WarningResponse]:
        request = did_models.DIDFraudValidationRequest(tn=tn)
        payload = self._request("POST", "/did/fraudvalidate", request.to_request_params())
        return did_models.parse_did_response(did_models.FraudValidationResponse, payload)


class AsyncDIDs(Resource):
    async def list(
        self, request: Optional[did_models.DIDListRequest] = None
    ) -> Union[did_models.DIDInventoryResponse, WarningResponse]:
        request = request or did_models.DIDListRequest()
        payload = await self._request("GET", "/did", request.to_request_params())
        return did_models.parse_did_response(did_models.DIDInventoryResponse, payload)

    async def pages(
        self, request: Optional[did_models.DIDListRequest] = None
    ) -> AsyncIterator[Union[did_models.DIDInventoryResponse, WarningResponse]]:
        request = request or did_models.DIDListRequest()
        page = request.page
        while True:
            result = await self.list(request.model_copy(update={"page": page}))
            yield result
            if isinstance(result, WarningResponse):
                return
            next_page = result.next_page()
            if next_page is None:
                return
            page = next_page

    async def order(self, request: did_models.DIDOrderRequest) -> Optional[WarningResponse]:
        payload = await self._request("POST", "/did", request.to_request_params())
        return did_models.parse_empty_did_response(payload)

    async def update(self, request: did_models.DIDUpdateRequest) -> Optional[WarningResponse]:
        payload = await self._request("PUT", "/did", request.to_request_params())
        return did_models.parse_empty_did_response(payload)

    async def delete(self, did: int) -> Optional[WarningResponse]:
        request = did_models.DIDDeleteRequest(did=did)
        payload = await self._request("DELETE", "/did", request.to_request_params())
        return did_models.parse_empty_did_response(payload)

    async def states(self) -> Union[did_models.DIDStatesResponse, WarningResponse]:
        payload = await self._request("GET", "/did/states")
        return did_models.parse_did_response(did_models.DIDStatesResponse, payload)

    async def rate_centers(
        self, state: str, tier: did_models.DIDTier
    ) -> Union[did_models.DIDRateCentersResponse, WarningResponse]:
        request = did_models.DIDRateCentersRequest(state=state, tier=tier)
        payload = await self._request("GET", "/did/ratecenters", request.to_request_params())
        return did_models.parse_did_response(did_models.DIDRateCentersResponse, payload)

    async def available(
        self, request: did_models.DIDAvailabilityRequest
    ) -> Union[did_models.AvailableDIDsResponse, WarningResponse]:
        payload = await self._request("GET", "/did/available", request.to_request_params())
        return did_models.parse_did_response(did_models.AvailableDIDsResponse, payload)

    async def move_to_fax(self, did: int) -> Optional[WarningResponse]:
        request = did_models.DIDMoveToFaxRequest(did=did)
        payload = await self._request("PUT", "/did/move2fax", request.to_request_params())
        return did_models.parse_empty_did_response(payload)

    async def validate_fraud(
        self, tn: Union[int, List[int]]
    ) -> Union[did_models.FraudValidationResponse, WarningResponse]:
        request = did_models.DIDFraudValidationRequest(tn=tn)
        payload = await self._request("POST", "/did/fraudvalidate", request.to_request_params())
        return did_models.parse_did_response(did_models.FraudValidationResponse, payload)


class InternationalDIDs(Resource):
    def countries(
        self, request: Optional[international_did_models.InternationalCountriesRequest] = None
    ) -> Union[international_did_models.InternationalCountriesResponse, WarningResponse]:
        request = request or international_did_models.InternationalCountriesRequest()
        payload = self._request("GET", "/didinter/countrylist", request.to_request_params())
        return international_did_models.parse_international_did_response(
            international_did_models.InternationalCountriesResponse, payload
        )

    def cities(
        self, country_code: str
    ) -> Union[international_did_models.InternationalCitiesResponse, WarningResponse]:
        request = international_did_models.InternationalCitiesRequest(country_code=country_code)
        payload = self._request("GET", "/didinter/citylist", request.to_request_params())
        return international_did_models.parse_international_did_response(
            international_did_models.InternationalCitiesResponse, payload
        )

    def list(
        self, request: Optional[international_did_models.InternationalDIDListRequest] = None
    ) -> Union[international_did_models.InternationalDIDInventoryResponse, WarningResponse]:
        request = request or international_did_models.InternationalDIDListRequest()
        payload = self._request("GET", "/didinter", request.to_request_params())
        return international_did_models.parse_international_did_response(
            international_did_models.InternationalDIDInventoryResponse, payload
        )

    def pages(
        self, request: Optional[international_did_models.InternationalDIDListRequest] = None
    ) -> Iterator[
        Union[international_did_models.InternationalDIDInventoryResponse, WarningResponse]
    ]:
        request = request or international_did_models.InternationalDIDListRequest()
        page = request.page
        while True:
            result = self.list(request.model_copy(update={"page": page}))
            yield result
            if isinstance(result, WarningResponse):
                return
            next_page = result.next_page()
            if next_page is None:
                return
            page = next_page

    def order(
        self, request: international_did_models.InternationalDIDOrderRequest
    ) -> Union[international_did_models.InternationalDIDOrderResponse, WarningResponse]:
        payload = self._request("POST", "/didinter", request.to_request_params())
        return international_did_models.parse_international_did_response(
            international_did_models.InternationalDIDOrderResponse, payload
        )

    def update(
        self, request: international_did_models.InternationalDIDUpdateRequest
    ) -> Optional[WarningResponse]:
        payload = self._request("PUT", "/didinter", request.to_request_params())
        return international_did_models.parse_empty_international_did_response(payload)

    def delete(self, did: int) -> Optional[WarningResponse]:
        request = international_did_models.InternationalDIDDeleteRequest(did=did)
        payload = self._request("DELETE", "/didinter", request.to_request_params())
        return international_did_models.parse_empty_international_did_response(payload)


class AsyncInternationalDIDs(Resource):
    async def countries(
        self, request: Optional[international_did_models.InternationalCountriesRequest] = None
    ) -> Union[international_did_models.InternationalCountriesResponse, WarningResponse]:
        request = request or international_did_models.InternationalCountriesRequest()
        payload = await self._request("GET", "/didinter/countrylist", request.to_request_params())
        return international_did_models.parse_international_did_response(
            international_did_models.InternationalCountriesResponse, payload
        )

    async def cities(
        self, country_code: str
    ) -> Union[international_did_models.InternationalCitiesResponse, WarningResponse]:
        request = international_did_models.InternationalCitiesRequest(country_code=country_code)
        payload = await self._request("GET", "/didinter/citylist", request.to_request_params())
        return international_did_models.parse_international_did_response(
            international_did_models.InternationalCitiesResponse, payload
        )

    async def list(
        self, request: Optional[international_did_models.InternationalDIDListRequest] = None
    ) -> Union[international_did_models.InternationalDIDInventoryResponse, WarningResponse]:
        request = request or international_did_models.InternationalDIDListRequest()
        payload = await self._request("GET", "/didinter", request.to_request_params())
        return international_did_models.parse_international_did_response(
            international_did_models.InternationalDIDInventoryResponse, payload
        )

    async def pages(
        self, request: Optional[international_did_models.InternationalDIDListRequest] = None
    ) -> AsyncIterator[
        Union[international_did_models.InternationalDIDInventoryResponse, WarningResponse]
    ]:
        request = request or international_did_models.InternationalDIDListRequest()
        page = request.page
        while True:
            result = await self.list(request.model_copy(update={"page": page}))
            yield result
            if isinstance(result, WarningResponse):
                return
            next_page = result.next_page()
            if next_page is None:
                return
            page = next_page

    async def order(
        self, request: international_did_models.InternationalDIDOrderRequest
    ) -> Union[international_did_models.InternationalDIDOrderResponse, WarningResponse]:
        payload = await self._request("POST", "/didinter", request.to_request_params())
        return international_did_models.parse_international_did_response(
            international_did_models.InternationalDIDOrderResponse, payload
        )

    async def update(
        self, request: international_did_models.InternationalDIDUpdateRequest
    ) -> Optional[WarningResponse]:
        payload = await self._request("PUT", "/didinter", request.to_request_params())
        return international_did_models.parse_empty_international_did_response(payload)

    async def delete(self, did: int) -> Optional[WarningResponse]:
        request = international_did_models.InternationalDIDDeleteRequest(did=did)
        payload = await self._request("DELETE", "/didinter", request.to_request_params())
        return international_did_models.parse_empty_international_did_response(payload)


class SIPTrunks(Resource):
    def list(
        self, request: Optional[sip_models.SIPTrunkListRequest] = None
    ) -> Union[sip_models.SIPTrunkInventoryResponse, WarningResponse]:
        request = request or sip_models.SIPTrunkListRequest()
        return sip_models.parse_sip_response(
            sip_models.SIPTrunkInventoryResponse,
            self._request("GET", "/siptrunk", request.to_request_params()),
        )

    def create(self, request: sip_models.SIPTrunkCreateRequest) -> Optional[WarningResponse]:
        return sip_models.parse_empty_sip_response(
            self._request("POST", "/siptrunk", request.to_request_params())
        )

    def update(self, request: sip_models.SIPTrunkUpdateRequest) -> Optional[WarningResponse]:
        return sip_models.parse_empty_sip_response(
            self._request("PUT", "/siptrunk", request.to_request_params())
        )

    def delete(self, trunk: str) -> Optional[WarningResponse]:
        request = sip_models.SIPTrunkDeleteRequest(trunk=trunk)
        return sip_models.parse_empty_sip_response(
            self._request("DELETE", "/siptrunk", request.to_request_params())
        )

    def status(self, trunk: str) -> Union[sip_models.SIPTrunkStatusResponse, WarningResponse]:
        request = sip_models.SIPTrunkStatusRequest(trunk=trunk)
        return sip_models.parse_sip_response(
            sip_models.SIPTrunkStatusResponse,
            self._request("GET", "/siptrunk/statuschecker", request.to_request_params()),
        )

    def block_caller(self, request: sip_models.BlockCallerRequest) -> Optional[WarningResponse]:
        return sip_models.parse_empty_sip_response(
            self._request("POST", "/siptrunk/blockcaller", request.to_request_params())
        )

    def blocked_callers(
        self, request: Optional[sip_models.BlockedCallersRequest] = None
    ) -> Union[sip_models.BlockedCallersResponse, WarningResponse]:
        request = request or sip_models.BlockedCallersRequest()
        return sip_models.parse_sip_response(
            sip_models.BlockedCallersResponse,
            self._request("GET", "/siptrunk/blockedcallers", request.to_request_params()),
        )


class AsyncSIPTrunks(Resource):
    async def list(
        self, request: Optional[sip_models.SIPTrunkListRequest] = None
    ) -> Union[sip_models.SIPTrunkInventoryResponse, WarningResponse]:
        request = request or sip_models.SIPTrunkListRequest()
        return sip_models.parse_sip_response(
            sip_models.SIPTrunkInventoryResponse,
            await self._request("GET", "/siptrunk", request.to_request_params()),
        )

    async def create(self, request: sip_models.SIPTrunkCreateRequest) -> Optional[WarningResponse]:
        return sip_models.parse_empty_sip_response(
            await self._request("POST", "/siptrunk", request.to_request_params())
        )

    async def update(self, request: sip_models.SIPTrunkUpdateRequest) -> Optional[WarningResponse]:
        return sip_models.parse_empty_sip_response(
            await self._request("PUT", "/siptrunk", request.to_request_params())
        )

    async def delete(self, trunk: str) -> Optional[WarningResponse]:
        request = sip_models.SIPTrunkDeleteRequest(trunk=trunk)
        return sip_models.parse_empty_sip_response(
            await self._request("DELETE", "/siptrunk", request.to_request_params())
        )

    async def status(self, trunk: str) -> Union[sip_models.SIPTrunkStatusResponse, WarningResponse]:
        request = sip_models.SIPTrunkStatusRequest(trunk=trunk)
        return sip_models.parse_sip_response(
            sip_models.SIPTrunkStatusResponse,
            await self._request("GET", "/siptrunk/statuschecker", request.to_request_params()),
        )

    async def block_caller(
        self, request: sip_models.BlockCallerRequest
    ) -> Optional[WarningResponse]:
        return sip_models.parse_empty_sip_response(
            await self._request("POST", "/siptrunk/blockcaller", request.to_request_params())
        )

    async def blocked_callers(
        self, request: Optional[sip_models.BlockedCallersRequest] = None
    ) -> Union[sip_models.BlockedCallersResponse, WarningResponse]:
        request = request or sip_models.BlockedCallersRequest()
        return sip_models.parse_sip_response(
            sip_models.BlockedCallersResponse,
            await self._request("GET", "/siptrunk/blockedcallers", request.to_request_params()),
        )


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


def install_resources(client: Any, *, async_client: bool = False) -> None:
    """Attach the complete resource tree to a sync or async client."""
    if async_client:
        client.account = AsyncAccount(client)
        client.dids = AsyncDIDs(client)
        client.international_dids = AsyncInternationalDIDs(client)
        client.sip_trunks = AsyncSIPTrunks(client)
    else:
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
