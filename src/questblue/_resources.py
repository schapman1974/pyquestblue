"""Resource-oriented wrappers for every documented QuestBlue API endpoint."""

from __future__ import annotations

from typing import Any, AsyncIterator, BinaryIO, Iterator, List, Mapping, Optional, Union

from . import account as account_models
from . import did as did_models
from . import dlc as dlc_models
from . import enterprise_fax as enterprise_fax_models
from . import fax as fax_models
from . import international_did as international_did_models
from . import lnp as lnp_models
from . import reports as report_models
from . import servers as server_models
from . import sip_trunk as sip_models
from . import sms as sms_models
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
    def list(
        self, request: Optional[sms_models.SMSInventoryRequest] = None
    ) -> Union[sms_models.SMSInventoryResponse, WarningResponse]:
        request = request or sms_models.SMSInventoryRequest()
        return sms_models.parse_sms_response(
            sms_models.SMSInventoryResponse,
            self._request("GET", "/sms", request.to_request_params()),
        )

    def send(
        self, request: sms_models.SendMessageRequest
    ) -> Union[sms_models.SendMessageResponse, WarningResponse]:
        return sms_models.parse_sms_response(
            sms_models.SendMessageResponse,
            self._request("POST", "/smsv2", request.to_request_params()),
        )

    def update(
        self, request: sms_models.SMSSettingsUpdateRequest
    ) -> Union[sms_models.SMSSettingsUpdateResponse, WarningResponse]:
        return sms_models.parse_sms_response(
            sms_models.SMSSettingsUpdateResponse,
            self._request("PUT", "/smsv2", request.to_request_params()),
        )

    def offnet_order(self, request: sms_models.OffnetOrderRequest) -> Optional[WarningResponse]:
        return sms_models.parse_empty_sms_response(
            self._request("POST", "/sms/offnetorder", request.to_request_params())
        )

    def offnet_status(
        self, request: sms_models.OffnetStatusRequest
    ) -> Union[sms_models.OffnetStatusResponse, WarningResponse]:
        return sms_models.parse_sms_response(
            sms_models.OffnetStatusResponse,
            self._request("GET", "/sms/offnetstatus", request.to_request_params()),
        )

    def history(
        self, request: Optional[sms_models.SMSHistoryRequest] = None
    ) -> Union[sms_models.SMSHistoryResponse, WarningResponse]:
        request = request or sms_models.SMSHistoryRequest()
        return sms_models.parse_sms_response(
            sms_models.SMSHistoryResponse,
            self._request("GET", "/sms/history", request.to_request_params()),
        )

    def delivery_status(
        self, request: sms_models.MessageDeliveryStatusRequest
    ) -> Union[sms_models.MessageDeliveryStatusResponse, WarningResponse]:
        return sms_models.parse_sms_response(
            sms_models.MessageDeliveryStatusResponse,
            self._request("GET", "/sms/deliverystatus", request.to_request_params()),
        )

    def carrier(
        self, request: sms_models.CarrierLookupRequest
    ) -> Union[sms_models.CarrierLookupResponse, WarningResponse]:
        return sms_models.parse_sms_response(
            sms_models.CarrierLookupResponse,
            self._request("GET", "/smschecktncarrier", request.to_request_params()),
        )


class AsyncSMS(Resource):
    async def list(
        self, request: Optional[sms_models.SMSInventoryRequest] = None
    ) -> Union[sms_models.SMSInventoryResponse, WarningResponse]:
        request = request or sms_models.SMSInventoryRequest()
        return sms_models.parse_sms_response(
            sms_models.SMSInventoryResponse,
            await self._request("GET", "/sms", request.to_request_params()),
        )

    async def send(
        self, request: sms_models.SendMessageRequest
    ) -> Union[sms_models.SendMessageResponse, WarningResponse]:
        return sms_models.parse_sms_response(
            sms_models.SendMessageResponse,
            await self._request("POST", "/smsv2", request.to_request_params()),
        )

    async def update(
        self, request: sms_models.SMSSettingsUpdateRequest
    ) -> Union[sms_models.SMSSettingsUpdateResponse, WarningResponse]:
        return sms_models.parse_sms_response(
            sms_models.SMSSettingsUpdateResponse,
            await self._request("PUT", "/smsv2", request.to_request_params()),
        )

    async def offnet_order(
        self, request: sms_models.OffnetOrderRequest
    ) -> Optional[WarningResponse]:
        return sms_models.parse_empty_sms_response(
            await self._request("POST", "/sms/offnetorder", request.to_request_params())
        )

    async def offnet_status(
        self, request: sms_models.OffnetStatusRequest
    ) -> Union[sms_models.OffnetStatusResponse, WarningResponse]:
        return sms_models.parse_sms_response(
            sms_models.OffnetStatusResponse,
            await self._request("GET", "/sms/offnetstatus", request.to_request_params()),
        )

    async def history(
        self, request: Optional[sms_models.SMSHistoryRequest] = None
    ) -> Union[sms_models.SMSHistoryResponse, WarningResponse]:
        request = request or sms_models.SMSHistoryRequest()
        return sms_models.parse_sms_response(
            sms_models.SMSHistoryResponse,
            await self._request("GET", "/sms/history", request.to_request_params()),
        )

    async def delivery_status(
        self, request: sms_models.MessageDeliveryStatusRequest
    ) -> Union[sms_models.MessageDeliveryStatusResponse, WarningResponse]:
        return sms_models.parse_sms_response(
            sms_models.MessageDeliveryStatusResponse,
            await self._request("GET", "/sms/deliverystatus", request.to_request_params()),
        )

    async def carrier(
        self, request: sms_models.CarrierLookupRequest
    ) -> Union[sms_models.CarrierLookupResponse, WarningResponse]:
        return sms_models.parse_sms_response(
            sms_models.CarrierLookupResponse,
            await self._request("GET", "/smschecktncarrier", request.to_request_params()),
        )


class DLC(Resource):
    def list_brands(
        self, request: Optional[dlc_models.BrandListRequest] = None
    ) -> Union[dlc_models.BrandListResponse, WarningResponse]:
        request = request or dlc_models.BrandListRequest()
        return dlc_models.parse_dlc_response(
            dlc_models.BrandListResponse,
            self._request("GET", "/dlc/brand", request.to_request_params()),
        )

    def create_brand(
        self, request: dlc_models.BrandCreateRequest
    ) -> Union[dlc_models.BrandCreateResponse, WarningResponse]:
        return dlc_models.parse_dlc_response(
            dlc_models.BrandCreateResponse,
            self._request("POST", "/dlc/brand", request.to_request_params()),
        )

    def update_brand(
        self, request: dlc_models.BrandUpdateRequest
    ) -> Union[dlc_models.BrandUpdateResponse, WarningResponse]:
        return dlc_models.parse_dlc_response(
            dlc_models.BrandUpdateResponse,
            self._request("PUT", "/dlc/brand", request.to_request_params()),
        )

    def delete_brand(self, brand_id: int) -> Optional[WarningResponse]:
        request = dlc_models.BrandDeleteRequest(id=brand_id)
        return dlc_models.parse_empty_dlc_response(
            self._request("DELETE", "/dlc/brand", request.to_request_params())
        )

    def list_campaigns(
        self, request: Optional[dlc_models.CampaignListRequest] = None
    ) -> Union[dlc_models.CampaignListResponse, WarningResponse]:
        request = request or dlc_models.CampaignListRequest()
        return dlc_models.parse_dlc_response(
            dlc_models.CampaignListResponse,
            self._request("GET", "/dlc/campaign", request.to_request_params()),
        )

    def create_campaign(
        self, request: dlc_models.CampaignCreateRequest
    ) -> Union[dlc_models.CampaignCreateResponse, WarningResponse]:
        return dlc_models.parse_dlc_response(
            dlc_models.CampaignCreateResponse,
            self._request("POST", "/dlc/campaign", request.to_request_params()),
        )

    def update_campaign(
        self, request: dlc_models.CampaignUpdateRequest
    ) -> Optional[WarningResponse]:
        return dlc_models.parse_empty_dlc_response(
            self._request("PUT", "/dlc/campaign", request.to_request_params())
        )

    def delete_campaign(self, campaign_id: int) -> Optional[WarningResponse]:
        request = dlc_models.CampaignDeleteRequest(id=campaign_id)
        return dlc_models.parse_empty_dlc_response(
            self._request("DELETE", "/dlc/campaign", request.to_request_params())
        )


class AsyncDLC(Resource):
    async def list_brands(
        self, request: Optional[dlc_models.BrandListRequest] = None
    ) -> Union[dlc_models.BrandListResponse, WarningResponse]:
        request = request or dlc_models.BrandListRequest()
        return dlc_models.parse_dlc_response(
            dlc_models.BrandListResponse,
            await self._request("GET", "/dlc/brand", request.to_request_params()),
        )

    async def create_brand(
        self, request: dlc_models.BrandCreateRequest
    ) -> Union[dlc_models.BrandCreateResponse, WarningResponse]:
        return dlc_models.parse_dlc_response(
            dlc_models.BrandCreateResponse,
            await self._request("POST", "/dlc/brand", request.to_request_params()),
        )

    async def update_brand(
        self, request: dlc_models.BrandUpdateRequest
    ) -> Union[dlc_models.BrandUpdateResponse, WarningResponse]:
        return dlc_models.parse_dlc_response(
            dlc_models.BrandUpdateResponse,
            await self._request("PUT", "/dlc/brand", request.to_request_params()),
        )

    async def delete_brand(self, brand_id: int) -> Optional[WarningResponse]:
        request = dlc_models.BrandDeleteRequest(id=brand_id)
        return dlc_models.parse_empty_dlc_response(
            await self._request("DELETE", "/dlc/brand", request.to_request_params())
        )

    async def list_campaigns(
        self, request: Optional[dlc_models.CampaignListRequest] = None
    ) -> Union[dlc_models.CampaignListResponse, WarningResponse]:
        request = request or dlc_models.CampaignListRequest()
        return dlc_models.parse_dlc_response(
            dlc_models.CampaignListResponse,
            await self._request("GET", "/dlc/campaign", request.to_request_params()),
        )

    async def create_campaign(
        self, request: dlc_models.CampaignCreateRequest
    ) -> Union[dlc_models.CampaignCreateResponse, WarningResponse]:
        return dlc_models.parse_dlc_response(
            dlc_models.CampaignCreateResponse,
            await self._request("POST", "/dlc/campaign", request.to_request_params()),
        )

    async def update_campaign(
        self, request: dlc_models.CampaignUpdateRequest
    ) -> Optional[WarningResponse]:
        return dlc_models.parse_empty_dlc_response(
            await self._request("PUT", "/dlc/campaign", request.to_request_params())
        )

    async def delete_campaign(self, campaign_id: int) -> Optional[WarningResponse]:
        request = dlc_models.CampaignDeleteRequest(id=campaign_id)
        return dlc_models.parse_empty_dlc_response(
            await self._request("DELETE", "/dlc/campaign", request.to_request_params())
        )


class Fax(Resource):
    def states(self) -> Union[fax_models.FaxStatesResponse, WarningResponse]:
        return fax_models.parse_fax_response(
            fax_models.FaxStatesResponse, self._request("GET", "/fax/states")
        )

    def rate_centers(self, state: str) -> Union[fax_models.FaxRateCentersResponse, WarningResponse]:
        request = fax_models.FaxRateCentersRequest(state=state)
        return fax_models.parse_fax_response(
            fax_models.FaxRateCentersResponse,
            self._request("GET", "/fax/ratecenters", request.to_request_params()),
        )

    def available(
        self, request: fax_models.FaxAvailabilityRequest
    ) -> Union[fax_models.AvailableFaxDIDsResponse, WarningResponse]:
        return fax_models.parse_fax_response(
            fax_models.AvailableFaxDIDsResponse,
            self._request("GET", "/fax/available", request.to_request_params()),
        )

    def create(self, request: fax_models.FaxOrderRequest) -> Optional[WarningResponse]:
        return fax_models.parse_empty_fax_response(
            self._request("POST", "/fax", request.to_request_params())
        )

    def list(
        self, request: Optional[fax_models.FaxListRequest] = None
    ) -> Union[fax_models.FaxInventoryResponse, WarningResponse]:
        request = request or fax_models.FaxListRequest()
        return fax_models.parse_fax_response(
            fax_models.FaxInventoryResponse,
            self._request("GET", "/fax", request.to_request_params()),
        )

    def update(self, request: fax_models.FaxUpdateRequest) -> Optional[WarningResponse]:
        return fax_models.parse_empty_fax_response(
            self._request("PUT", "/fax", request.to_request_params())
        )

    def delete(self, did: int) -> Optional[WarningResponse]:
        request = fax_models.FaxDeleteRequest(did=did)
        return fax_models.parse_empty_fax_response(
            self._request("DELETE", "/fax", request.to_request_params())
        )

    def send(
        self, request: fax_models.FaxSendRequest
    ) -> Union[fax_models.FaxSendResponse, WarningResponse]:
        return fax_models.parse_fax_response(
            fax_models.FaxSendResponse,
            self._request("POST", "/fax/send", request.to_request_params()),
        )

    def move_to_voice(self, did: int) -> Optional[WarningResponse]:
        request = fax_models.FaxMoveToVoiceRequest(did=did)
        return fax_models.parse_empty_fax_response(
            self._request("PUT", "/fax/move2voice", request.to_request_params())
        )

    def pause(self, request: fax_models.FaxPauseRequest) -> Optional[WarningResponse]:
        return fax_models.parse_empty_fax_response(
            self._request("PUT", "/fax/pause", request.to_request_params())
        )

    def set_email_permission(
        self, request: fax_models.FaxEmailPermissionRequest
    ) -> Optional[WarningResponse]:
        return fax_models.parse_empty_fax_response(
            self._request("POST", "/fax/email", request.to_request_params())
        )

    def delete_email_permission(
        self, request: fax_models.FaxEmailPermissionDeleteRequest
    ) -> Optional[WarningResponse]:
        return fax_models.parse_empty_fax_response(
            self._request("DELETE", "/fax/email", request.to_request_params())
        )


class AsyncFax(Resource):
    async def states(self) -> Union[fax_models.FaxStatesResponse, WarningResponse]:
        return fax_models.parse_fax_response(
            fax_models.FaxStatesResponse, await self._request("GET", "/fax/states")
        )

    async def rate_centers(
        self, state: str
    ) -> Union[fax_models.FaxRateCentersResponse, WarningResponse]:
        request = fax_models.FaxRateCentersRequest(state=state)
        return fax_models.parse_fax_response(
            fax_models.FaxRateCentersResponse,
            await self._request("GET", "/fax/ratecenters", request.to_request_params()),
        )

    async def available(
        self, request: fax_models.FaxAvailabilityRequest
    ) -> Union[fax_models.AvailableFaxDIDsResponse, WarningResponse]:
        return fax_models.parse_fax_response(
            fax_models.AvailableFaxDIDsResponse,
            await self._request("GET", "/fax/available", request.to_request_params()),
        )

    async def create(self, request: fax_models.FaxOrderRequest) -> Optional[WarningResponse]:
        return fax_models.parse_empty_fax_response(
            await self._request("POST", "/fax", request.to_request_params())
        )

    async def list(
        self, request: Optional[fax_models.FaxListRequest] = None
    ) -> Union[fax_models.FaxInventoryResponse, WarningResponse]:
        request = request or fax_models.FaxListRequest()
        return fax_models.parse_fax_response(
            fax_models.FaxInventoryResponse,
            await self._request("GET", "/fax", request.to_request_params()),
        )

    async def update(self, request: fax_models.FaxUpdateRequest) -> Optional[WarningResponse]:
        return fax_models.parse_empty_fax_response(
            await self._request("PUT", "/fax", request.to_request_params())
        )

    async def delete(self, did: int) -> Optional[WarningResponse]:
        request = fax_models.FaxDeleteRequest(did=did)
        return fax_models.parse_empty_fax_response(
            await self._request("DELETE", "/fax", request.to_request_params())
        )

    async def send(
        self, request: fax_models.FaxSendRequest
    ) -> Union[fax_models.FaxSendResponse, WarningResponse]:
        return fax_models.parse_fax_response(
            fax_models.FaxSendResponse,
            await self._request("POST", "/fax/send", request.to_request_params()),
        )

    async def move_to_voice(self, did: int) -> Optional[WarningResponse]:
        request = fax_models.FaxMoveToVoiceRequest(did=did)
        return fax_models.parse_empty_fax_response(
            await self._request("PUT", "/fax/move2voice", request.to_request_params())
        )

    async def pause(self, request: fax_models.FaxPauseRequest) -> Optional[WarningResponse]:
        return fax_models.parse_empty_fax_response(
            await self._request("PUT", "/fax/pause", request.to_request_params())
        )

    async def set_email_permission(
        self, request: fax_models.FaxEmailPermissionRequest
    ) -> Optional[WarningResponse]:
        return fax_models.parse_empty_fax_response(
            await self._request("POST", "/fax/email", request.to_request_params())
        )

    async def delete_email_permission(
        self, request: fax_models.FaxEmailPermissionDeleteRequest
    ) -> Optional[WarningResponse]:
        return fax_models.parse_empty_fax_response(
            await self._request("DELETE", "/fax/email", request.to_request_params())
        )


class EnterpriseFax(Resource):
    def list(
        self, request: Optional[enterprise_fax_models.EnterpriseFaxListRequest] = None
    ) -> Union[enterprise_fax_models.EnterpriseFaxInventoryResponse, WarningResponse]:
        request = request or enterprise_fax_models.EnterpriseFaxListRequest()
        return enterprise_fax_models.parse_enterprise_fax_response(
            enterprise_fax_models.EnterpriseFaxInventoryResponse,
            self._request("GET", "/fax2", request.to_request_params()),
        )

    def create(
        self, request: enterprise_fax_models.EnterpriseFaxOrderRequest
    ) -> Optional[WarningResponse]:
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            self._request("POST", "/fax2", request.to_request_params())
        )

    def update(
        self, request: enterprise_fax_models.EnterpriseFaxUpdateRequest
    ) -> Optional[WarningResponse]:
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            self._request("PUT", "/fax2", request.to_request_params())
        )

    def delete(self, did: int) -> Optional[WarningResponse]:
        request = enterprise_fax_models.EnterpriseFaxDeleteRequest(did=did)
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            self._request("DELETE", "/fax2", request.to_request_params())
        )

    def list_emails(
        self, request: Optional[enterprise_fax_models.EnterpriseFaxEmailListRequest] = None
    ) -> Union[enterprise_fax_models.EnterpriseFaxEmailListResponse, WarningResponse]:
        request = request or enterprise_fax_models.EnterpriseFaxEmailListRequest()
        return enterprise_fax_models.parse_enterprise_fax_response(
            enterprise_fax_models.EnterpriseFaxEmailListResponse,
            self._request("GET", "/fax2/email", request.to_request_params()),
        )

    def set_email_permission(
        self, request: enterprise_fax_models.EnterpriseFaxEmailPermissionRequest
    ) -> Optional[WarningResponse]:
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            self._request("POST", "/fax2/email", request.to_request_params())
        )

    def delete_email_permission(
        self, request: enterprise_fax_models.EnterpriseFaxEmailPermissionDeleteRequest
    ) -> Optional[WarningResponse]:
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            self._request("DELETE", "/fax2/email", request.to_request_params())
        )

    def list_groups(
        self, request: Optional[enterprise_fax_models.EnterpriseFaxGroupListRequest] = None
    ) -> Union[enterprise_fax_models.EnterpriseFaxGroupListResponse, WarningResponse]:
        request = request or enterprise_fax_models.EnterpriseFaxGroupListRequest()
        return enterprise_fax_models.parse_enterprise_fax_response(
            enterprise_fax_models.EnterpriseFaxGroupListResponse,
            self._request("GET", "/fax2/group", request.to_request_params()),
        )

    def create_group(
        self, request: enterprise_fax_models.EnterpriseFaxGroupCreateRequest
    ) -> Optional[WarningResponse]:
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            self._request("POST", "/fax2/group", request.to_request_params())
        )

    def update_group(
        self, request: enterprise_fax_models.EnterpriseFaxGroupUpdateRequest
    ) -> Optional[WarningResponse]:
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            self._request("PUT", "/fax2/group", request.to_request_params())
        )

    def delete_group(self, sname: str) -> Optional[WarningResponse]:
        request = enterprise_fax_models.EnterpriseFaxGroupDeleteRequest(sname=sname)
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            self._request("DELETE", "/fax2/group", request.to_request_params())
        )

    def list_users(
        self, request: Optional[enterprise_fax_models.EnterpriseFaxUserListRequest] = None
    ) -> Union[enterprise_fax_models.EnterpriseFaxUserListResponse, WarningResponse]:
        request = request or enterprise_fax_models.EnterpriseFaxUserListRequest()
        return enterprise_fax_models.parse_enterprise_fax_response(
            enterprise_fax_models.EnterpriseFaxUserListResponse,
            self._request("GET", "/fax2/user", request.to_request_params()),
        )

    def create_user(
        self, request: enterprise_fax_models.EnterpriseFaxUserCreateRequest
    ) -> Optional[WarningResponse]:
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            self._request("POST", "/fax2/user", request.to_request_params())
        )

    def update_user(
        self, request: enterprise_fax_models.EnterpriseFaxUserUpdateRequest
    ) -> Optional[WarningResponse]:
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            self._request("PUT", "/fax2/user", request.to_request_params())
        )

    def delete_user(self, fax_login: str) -> Optional[WarningResponse]:
        request = enterprise_fax_models.EnterpriseFaxUserDeleteRequest(fax_login=fax_login)
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            self._request("DELETE", "/fax2/user", request.to_request_params())
        )

    def list_permissions(
        self, request: Optional[enterprise_fax_models.EnterpriseFaxPermissionListRequest] = None
    ) -> Union[enterprise_fax_models.EnterpriseFaxPermissionListResponse, WarningResponse]:
        request = request or enterprise_fax_models.EnterpriseFaxPermissionListRequest()
        return enterprise_fax_models.parse_enterprise_fax_response(
            enterprise_fax_models.EnterpriseFaxPermissionListResponse,
            self._request("GET", "/fax2/permit", request.to_request_params()),
        )

    def set_permission(
        self, request: enterprise_fax_models.EnterpriseFaxPermissionRequest
    ) -> Optional[WarningResponse]:
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            self._request("POST", "/fax2/permit", request.to_request_params())
        )

    def delete_permission(
        self, request: enterprise_fax_models.EnterpriseFaxPermissionDeleteRequest
    ) -> Optional[WarningResponse]:
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            self._request("DELETE", "/fax2/permit", request.to_request_params())
        )

    def upload(
        self, request: enterprise_fax_models.EnterpriseFaxUploadRequest
    ) -> Union[enterprise_fax_models.EnterpriseFaxUploadResponse, WarningResponse]:
        return enterprise_fax_models.parse_enterprise_fax_response(
            enterprise_fax_models.EnterpriseFaxUploadResponse,
            self._request("POST", "/fax2/upload", json=request.to_request_params()),
        )

    def send(
        self, request: enterprise_fax_models.EnterpriseFaxSendRequest
    ) -> Union[enterprise_fax_models.EnterpriseFaxSendResponse, WarningResponse]:
        return enterprise_fax_models.parse_enterprise_fax_response(
            enterprise_fax_models.EnterpriseFaxSendResponse,
            self._request("POST", "/fax2/send", request.to_request_params()),
        )

    def pause(
        self, request: enterprise_fax_models.EnterpriseFaxPauseRequest
    ) -> Optional[WarningResponse]:
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            self._request("PUT", "/fax2/pause", request.to_request_params())
        )


class AsyncEnterpriseFax(Resource):
    async def list(
        self, request: Optional[enterprise_fax_models.EnterpriseFaxListRequest] = None
    ) -> Union[enterprise_fax_models.EnterpriseFaxInventoryResponse, WarningResponse]:
        request = request or enterprise_fax_models.EnterpriseFaxListRequest()
        return enterprise_fax_models.parse_enterprise_fax_response(
            enterprise_fax_models.EnterpriseFaxInventoryResponse,
            await self._request("GET", "/fax2", request.to_request_params()),
        )

    async def create(
        self, request: enterprise_fax_models.EnterpriseFaxOrderRequest
    ) -> Optional[WarningResponse]:
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            await self._request("POST", "/fax2", request.to_request_params())
        )

    async def update(
        self, request: enterprise_fax_models.EnterpriseFaxUpdateRequest
    ) -> Optional[WarningResponse]:
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            await self._request("PUT", "/fax2", request.to_request_params())
        )

    async def delete(self, did: int) -> Optional[WarningResponse]:
        request = enterprise_fax_models.EnterpriseFaxDeleteRequest(did=did)
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            await self._request("DELETE", "/fax2", request.to_request_params())
        )

    async def list_emails(
        self, request: Optional[enterprise_fax_models.EnterpriseFaxEmailListRequest] = None
    ) -> Union[enterprise_fax_models.EnterpriseFaxEmailListResponse, WarningResponse]:
        request = request or enterprise_fax_models.EnterpriseFaxEmailListRequest()
        return enterprise_fax_models.parse_enterprise_fax_response(
            enterprise_fax_models.EnterpriseFaxEmailListResponse,
            await self._request("GET", "/fax2/email", request.to_request_params()),
        )

    async def set_email_permission(
        self, request: enterprise_fax_models.EnterpriseFaxEmailPermissionRequest
    ) -> Optional[WarningResponse]:
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            await self._request("POST", "/fax2/email", request.to_request_params())
        )

    async def delete_email_permission(
        self, request: enterprise_fax_models.EnterpriseFaxEmailPermissionDeleteRequest
    ) -> Optional[WarningResponse]:
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            await self._request("DELETE", "/fax2/email", request.to_request_params())
        )

    async def list_groups(
        self, request: Optional[enterprise_fax_models.EnterpriseFaxGroupListRequest] = None
    ) -> Union[enterprise_fax_models.EnterpriseFaxGroupListResponse, WarningResponse]:
        request = request or enterprise_fax_models.EnterpriseFaxGroupListRequest()
        return enterprise_fax_models.parse_enterprise_fax_response(
            enterprise_fax_models.EnterpriseFaxGroupListResponse,
            await self._request("GET", "/fax2/group", request.to_request_params()),
        )

    async def create_group(
        self, request: enterprise_fax_models.EnterpriseFaxGroupCreateRequest
    ) -> Optional[WarningResponse]:
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            await self._request("POST", "/fax2/group", request.to_request_params())
        )

    async def update_group(
        self, request: enterprise_fax_models.EnterpriseFaxGroupUpdateRequest
    ) -> Optional[WarningResponse]:
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            await self._request("PUT", "/fax2/group", request.to_request_params())
        )

    async def delete_group(self, sname: str) -> Optional[WarningResponse]:
        request = enterprise_fax_models.EnterpriseFaxGroupDeleteRequest(sname=sname)
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            await self._request("DELETE", "/fax2/group", request.to_request_params())
        )

    async def list_users(
        self, request: Optional[enterprise_fax_models.EnterpriseFaxUserListRequest] = None
    ) -> Union[enterprise_fax_models.EnterpriseFaxUserListResponse, WarningResponse]:
        request = request or enterprise_fax_models.EnterpriseFaxUserListRequest()
        return enterprise_fax_models.parse_enterprise_fax_response(
            enterprise_fax_models.EnterpriseFaxUserListResponse,
            await self._request("GET", "/fax2/user", request.to_request_params()),
        )

    async def create_user(
        self, request: enterprise_fax_models.EnterpriseFaxUserCreateRequest
    ) -> Optional[WarningResponse]:
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            await self._request("POST", "/fax2/user", request.to_request_params())
        )

    async def update_user(
        self, request: enterprise_fax_models.EnterpriseFaxUserUpdateRequest
    ) -> Optional[WarningResponse]:
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            await self._request("PUT", "/fax2/user", request.to_request_params())
        )

    async def delete_user(self, fax_login: str) -> Optional[WarningResponse]:
        request = enterprise_fax_models.EnterpriseFaxUserDeleteRequest(fax_login=fax_login)
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            await self._request("DELETE", "/fax2/user", request.to_request_params())
        )

    async def list_permissions(
        self, request: Optional[enterprise_fax_models.EnterpriseFaxPermissionListRequest] = None
    ) -> Union[enterprise_fax_models.EnterpriseFaxPermissionListResponse, WarningResponse]:
        request = request or enterprise_fax_models.EnterpriseFaxPermissionListRequest()
        return enterprise_fax_models.parse_enterprise_fax_response(
            enterprise_fax_models.EnterpriseFaxPermissionListResponse,
            await self._request("GET", "/fax2/permit", request.to_request_params()),
        )

    async def set_permission(
        self, request: enterprise_fax_models.EnterpriseFaxPermissionRequest
    ) -> Optional[WarningResponse]:
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            await self._request("POST", "/fax2/permit", request.to_request_params())
        )

    async def delete_permission(
        self, request: enterprise_fax_models.EnterpriseFaxPermissionDeleteRequest
    ) -> Optional[WarningResponse]:
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            await self._request("DELETE", "/fax2/permit", request.to_request_params())
        )

    async def upload(
        self, request: enterprise_fax_models.EnterpriseFaxUploadRequest
    ) -> Union[enterprise_fax_models.EnterpriseFaxUploadResponse, WarningResponse]:
        return enterprise_fax_models.parse_enterprise_fax_response(
            enterprise_fax_models.EnterpriseFaxUploadResponse,
            await self._request("POST", "/fax2/upload", json=request.to_request_params()),
        )

    async def send(
        self, request: enterprise_fax_models.EnterpriseFaxSendRequest
    ) -> Union[enterprise_fax_models.EnterpriseFaxSendResponse, WarningResponse]:
        return enterprise_fax_models.parse_enterprise_fax_response(
            enterprise_fax_models.EnterpriseFaxSendResponse,
            await self._request("POST", "/fax2/send", request.to_request_params()),
        )

    async def pause(
        self, request: enterprise_fax_models.EnterpriseFaxPauseRequest
    ) -> Optional[WarningResponse]:
        return enterprise_fax_models.parse_empty_enterprise_fax_response(
            await self._request("PUT", "/fax2/pause", request.to_request_params())
        )


class Reports(Resource):
    def call_history(
        self, request: Optional[report_models.CallHistoryRequest] = None
    ) -> Union[report_models.CallHistoryResponse, WarningResponse]:
        request = request or report_models.CallHistoryRequest()
        return report_models.parse_report_response(
            report_models.CallHistoryResponse,
            self._request("GET", "/callhistory", request.to_request_params()),
        )

    def iter_call_history(
        self, request: Optional[report_models.CallHistoryRequest] = None
    ) -> Iterator[report_models.CallHistoryRecord]:
        current = request or report_models.CallHistoryRequest()
        while True:
            response = self.call_history(current)
            if isinstance(response, WarningResponse):
                return
            yield from response.data
            next_page = response.next_page(current.per_page)
            if next_page is None:
                return
            current = current.model_copy(update={"page": next_page})

    def fax_history(
        self, request: Optional[report_models.FaxHistoryRequest] = None
    ) -> Union[report_models.FaxHistoryResponse, WarningResponse]:
        request = request or report_models.FaxHistoryRequest()
        return report_models.parse_report_response(
            report_models.FaxHistoryResponse,
            self._request("GET", "/faxhistory", request.to_request_params()),
        )

    def iter_fax_history(
        self, request: Optional[report_models.FaxHistoryRequest] = None
    ) -> Iterator[report_models.FaxHistoryRecord]:
        current = request or report_models.FaxHistoryRequest()
        while True:
            response = self.fax_history(current)
            if isinstance(response, WarningResponse):
                return
            yield from response.data
            next_page = response.next_page()
            if next_page is None:
                return
            current = current.model_copy(update={"page": next_page})

    def download_fax(
        self, fax_id: int
    ) -> Union[report_models.FaxDownloadResponse, WarningResponse]:
        request = report_models.FaxDownloadRequest(fax_id=fax_id)
        return report_models.parse_report_response(
            report_models.FaxDownloadResponse,
            self._request("GET", "/faxdownload", request.to_request_params()),
        )

    def download_fax_to(self, fax_id: int, destination: BinaryIO) -> int:
        response = self.download_fax(fax_id)
        if isinstance(response, WarningResponse):
            raise ValueError("QuestBlue returned a warning instead of a fax document")
        return response.data.write_to(destination)


class AsyncReports(Resource):
    async def call_history(
        self, request: Optional[report_models.CallHistoryRequest] = None
    ) -> Union[report_models.CallHistoryResponse, WarningResponse]:
        request = request or report_models.CallHistoryRequest()
        return report_models.parse_report_response(
            report_models.CallHistoryResponse,
            await self._request("GET", "/callhistory", request.to_request_params()),
        )

    async def iter_call_history(
        self, request: Optional[report_models.CallHistoryRequest] = None
    ) -> AsyncIterator[report_models.CallHistoryRecord]:
        current = request or report_models.CallHistoryRequest()
        while True:
            response = await self.call_history(current)
            if isinstance(response, WarningResponse):
                return
            for record in response.data:
                yield record
            next_page = response.next_page(current.per_page)
            if next_page is None:
                return
            current = current.model_copy(update={"page": next_page})

    async def fax_history(
        self, request: Optional[report_models.FaxHistoryRequest] = None
    ) -> Union[report_models.FaxHistoryResponse, WarningResponse]:
        request = request or report_models.FaxHistoryRequest()
        return report_models.parse_report_response(
            report_models.FaxHistoryResponse,
            await self._request("GET", "/faxhistory", request.to_request_params()),
        )

    async def iter_fax_history(
        self, request: Optional[report_models.FaxHistoryRequest] = None
    ) -> AsyncIterator[report_models.FaxHistoryRecord]:
        current = request or report_models.FaxHistoryRequest()
        while True:
            response = await self.fax_history(current)
            if isinstance(response, WarningResponse):
                return
            for record in response.data:
                yield record
            next_page = response.next_page()
            if next_page is None:
                return
            current = current.model_copy(update={"page": next_page})

    async def download_fax(
        self, fax_id: int
    ) -> Union[report_models.FaxDownloadResponse, WarningResponse]:
        request = report_models.FaxDownloadRequest(fax_id=fax_id)
        return report_models.parse_report_response(
            report_models.FaxDownloadResponse,
            await self._request("GET", "/faxdownload", request.to_request_params()),
        )

    async def download_fax_to(self, fax_id: int, destination: BinaryIO) -> int:
        response = await self.download_fax(fax_id)
        if isinstance(response, WarningResponse):
            raise ValueError("QuestBlue returned a warning instead of a fax document")
        return response.data.write_to(destination)


class LNP(Resource):
    def check(
        self, request: lnp_models.LNPCheckRequest
    ) -> Union[lnp_models.LNPCheckResponse, WarningResponse]:
        return lnp_models.parse_lnp_response(
            lnp_models.LNPCheckResponse,
            self._request("GET", "/lnp/check", request.to_request_params()),
        )

    def create(
        self, request: lnp_models.LNPCreateRequest
    ) -> Union[lnp_models.LNPCreateResponse, WarningResponse]:
        return lnp_models.parse_lnp_response(
            lnp_models.LNPCreateResponse,
            self._request("POST", "/lnp", request.to_request_params()),
        )

    def list(
        self, request: Optional[lnp_models.LNPListRequest] = None
    ) -> Union[lnp_models.LNPListResponse, WarningResponse]:
        request = request or lnp_models.LNPListRequest()
        return lnp_models.parse_lnp_response(
            lnp_models.LNPListResponse,
            self._request("GET", "/lnp", request.to_request_params()),
        )

    def update(self, request: lnp_models.LNPUpdateRequest) -> Optional[WarningResponse]:
        return lnp_models.parse_empty_lnp_response(
            self._request("PUT", "/lnp", request.to_request_params())
        )

    def delete(self, request_id: int) -> Optional[WarningResponse]:
        request = lnp_models.LNPDeleteRequest(id=request_id)
        return lnp_models.parse_empty_lnp_response(
            self._request("DELETE", "/lnp", request.to_request_params())
        )


class AsyncLNP(Resource):
    async def check(
        self, request: lnp_models.LNPCheckRequest
    ) -> Union[lnp_models.LNPCheckResponse, WarningResponse]:
        return lnp_models.parse_lnp_response(
            lnp_models.LNPCheckResponse,
            await self._request("GET", "/lnp/check", request.to_request_params()),
        )

    async def create(
        self, request: lnp_models.LNPCreateRequest
    ) -> Union[lnp_models.LNPCreateResponse, WarningResponse]:
        return lnp_models.parse_lnp_response(
            lnp_models.LNPCreateResponse,
            await self._request("POST", "/lnp", request.to_request_params()),
        )

    async def list(
        self, request: Optional[lnp_models.LNPListRequest] = None
    ) -> Union[lnp_models.LNPListResponse, WarningResponse]:
        request = request or lnp_models.LNPListRequest()
        return lnp_models.parse_lnp_response(
            lnp_models.LNPListResponse,
            await self._request("GET", "/lnp", request.to_request_params()),
        )

    async def update(self, request: lnp_models.LNPUpdateRequest) -> Optional[WarningResponse]:
        return lnp_models.parse_empty_lnp_response(
            await self._request("PUT", "/lnp", request.to_request_params())
        )

    async def delete(self, request_id: int) -> Optional[WarningResponse]:
        request = lnp_models.LNPDeleteRequest(id=request_id)
        return lnp_models.parse_empty_lnp_response(
            await self._request("DELETE", "/lnp", request.to_request_params())
        )


class Servers(Resource):
    def create(
        self, request: server_models.ServerOrderRequest
    ) -> Union[server_models.ServerOrderResponse, WarningResponse]:
        return server_models.parse_server_response(
            server_models.ServerOrderResponse,
            self._request(
                "POST",
                "/server",
                {"server_type": request.server_type},
                json=request.params.to_request_params(),
            ),
        )

    def list(
        self, request: Optional[server_models.ServerListRequest] = None
    ) -> Union[server_models.ServerListResponse, WarningResponse]:
        request = request or server_models.ServerListRequest()
        return server_models.parse_server_response(
            server_models.ServerListResponse,
            self._request("GET", "/server", request.to_request_params()),
        )

    def delete(self, server_id: int) -> Optional[WarningResponse]:
        request = server_models.ServerIDRequest(server_id=server_id)
        return server_models.parse_empty_server_response(
            self._request("DELETE", "/server", request.to_request_params())
        )

    def add_ip(self, request: server_models.ServerIPRequest) -> Optional[WarningResponse]:
        return server_models.parse_empty_server_response(
            self._request("PUT", "/server/addip", request.to_request_params())
        )

    def remove_ip(self, server_id: int) -> Optional[WarningResponse]:
        request = server_models.ServerIDRequest(server_id=server_id)
        return server_models.parse_empty_server_response(
            self._request("DELETE", "/server/deleip", request.to_request_params())
        )

    def upgrade(self, request: server_models.ServerUpgradeRequest) -> Optional[WarningResponse]:
        return server_models.parse_empty_server_response(
            self._request("POST", "/server/upgrade", request.to_request_params())
        )

    def manage_backup_schedule(
        self, request: server_models.BackupScheduleRequest
    ) -> Optional[WarningResponse]:
        return server_models.parse_empty_server_response(
            self._request("POST", "/server/managebackupschedule", request.to_request_params())
        )

    def list_backups(
        self, server_id: int
    ) -> Union[server_models.BackupListResponse, WarningResponse]:
        request = server_models.ServerIDRequest(server_id=server_id)
        return server_models.parse_server_response(
            server_models.BackupListResponse,
            self._request("GET", "/server/listbackups", request.to_request_params()),
        )

    def restore_backup(
        self, request: server_models.BackupRequest
    ) -> Union[server_models.ServerMessageResponse, WarningResponse]:
        return server_models.parse_server_response(
            server_models.ServerMessageResponse,
            self._request("POST", "/server/restorebackup", request.to_request_params()),
        )

    def remove_backup(
        self, request: server_models.BackupRequest
    ) -> Union[server_models.ServerMessageResponse, WarningResponse]:
        return server_models.parse_server_response(
            server_models.ServerMessageResponse,
            self._request("DELETE", "/server/removebackup", request.to_request_params()),
        )


class AsyncServers(Resource):
    async def create(
        self, request: server_models.ServerOrderRequest
    ) -> Union[server_models.ServerOrderResponse, WarningResponse]:
        return server_models.parse_server_response(
            server_models.ServerOrderResponse,
            await self._request(
                "POST",
                "/server",
                {"server_type": request.server_type},
                json=request.params.to_request_params(),
            ),
        )

    async def list(
        self, request: Optional[server_models.ServerListRequest] = None
    ) -> Union[server_models.ServerListResponse, WarningResponse]:
        request = request or server_models.ServerListRequest()
        return server_models.parse_server_response(
            server_models.ServerListResponse,
            await self._request("GET", "/server", request.to_request_params()),
        )

    async def delete(self, server_id: int) -> Optional[WarningResponse]:
        request = server_models.ServerIDRequest(server_id=server_id)
        return server_models.parse_empty_server_response(
            await self._request("DELETE", "/server", request.to_request_params())
        )

    async def add_ip(self, request: server_models.ServerIPRequest) -> Optional[WarningResponse]:
        return server_models.parse_empty_server_response(
            await self._request("PUT", "/server/addip", request.to_request_params())
        )

    async def remove_ip(self, server_id: int) -> Optional[WarningResponse]:
        request = server_models.ServerIDRequest(server_id=server_id)
        return server_models.parse_empty_server_response(
            await self._request("DELETE", "/server/deleip", request.to_request_params())
        )

    async def upgrade(
        self, request: server_models.ServerUpgradeRequest
    ) -> Optional[WarningResponse]:
        return server_models.parse_empty_server_response(
            await self._request("POST", "/server/upgrade", request.to_request_params())
        )

    async def manage_backup_schedule(
        self, request: server_models.BackupScheduleRequest
    ) -> Optional[WarningResponse]:
        return server_models.parse_empty_server_response(
            await self._request("POST", "/server/managebackupschedule", request.to_request_params())
        )

    async def list_backups(
        self, server_id: int
    ) -> Union[server_models.BackupListResponse, WarningResponse]:
        request = server_models.ServerIDRequest(server_id=server_id)
        return server_models.parse_server_response(
            server_models.BackupListResponse,
            await self._request("GET", "/server/listbackups", request.to_request_params()),
        )

    async def restore_backup(
        self, request: server_models.BackupRequest
    ) -> Union[server_models.ServerMessageResponse, WarningResponse]:
        return server_models.parse_server_response(
            server_models.ServerMessageResponse,
            await self._request("POST", "/server/restorebackup", request.to_request_params()),
        )

    async def remove_backup(
        self, request: server_models.BackupRequest
    ) -> Union[server_models.ServerMessageResponse, WarningResponse]:
        return server_models.parse_server_response(
            server_models.ServerMessageResponse,
            await self._request("DELETE", "/server/removebackup", request.to_request_params()),
        )


def install_resources(client: Any, *, async_client: bool = False) -> None:
    """Attach the complete resource tree to a sync or async client."""
    if async_client:
        client.account = AsyncAccount(client)
        client.dids = AsyncDIDs(client)
        client.international_dids = AsyncInternationalDIDs(client)
        client.sip_trunks = AsyncSIPTrunks(client)
        client.sms = AsyncSMS(client)
        client.dlc = AsyncDLC(client)
        client.fax = AsyncFax(client)
        client.enterprise_fax = AsyncEnterpriseFax(client)
        client.reports = AsyncReports(client)
        client.lnp = AsyncLNP(client)
        client.servers = AsyncServers(client)
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
