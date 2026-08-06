"""Read-only primitive-input services shared by the simple facades."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Iterable, List, Optional, Sequence, Tuple, Union, cast

from questblue import did as did_models
from questblue import dlc as dlc_models
from questblue import enterprise_fax as enterprise_fax_models
from questblue import fax as fax_models
from questblue import international_did as international_models
from questblue import lnp as lnp_models
from questblue import reports as report_models
from questblue import servers as server_models
from questblue import sip_trunk as sip_models
from questblue import sms as sms_models
from questblue.models import Period, QuestBlueModel, TimestampRange

from ._client import SimpleService, unwrap_warning
from ._normalizers import normalize_date_range, normalize_enum, normalize_list, normalize_phone
from ._results import SimpleCollection, SimpleRecord


def _items(response: Any) -> List[Any]:
    data = getattr(response, "data", response)
    if isinstance(data, dict):
        return [item for values in data.values() for item in values]
    if isinstance(data, (list, tuple)):
        return list(data)
    return [data]


def _view(value: Any) -> Any:
    return SimpleRecord(value) if isinstance(value, QuestBlueModel) else value


def _phone_values(value: Any) -> List[int]:
    return [normalize_phone(item) for item in normalize_list(value)]


def _id_filter(value: Optional[Union[int, Sequence[int]]]) -> Optional[Union[int, List[int]]]:
    if value is None or isinstance(value, int):
        return value
    return list(value)


def _collection(responses: Iterable[Any]) -> SimpleCollection[Any]:
    raw = tuple(unwrap_warning(response) for response in responses)
    return SimpleCollection(
        tuple(_view(item) for response in raw for item in _items(response)), raw
    )


class AccountReads(SimpleService):
    def balance(self) -> Any:
        response = unwrap_warning(self.raw.balance())
        return response.data.balance

    def details(self) -> SimpleCollection[Any]:
        return _collection((self.raw.details(),))

    def rates(self) -> SimpleRecord:
        return SimpleRecord(unwrap_warning(self.raw.rates()))


class AsyncAccountReads(SimpleService):
    async def balance(self) -> Any:
        response = unwrap_warning(await self.raw.balance())
        return response.data.balance

    async def details(self) -> SimpleCollection[Any]:
        return _collection((await self.raw.details(),))

    async def rates(self) -> SimpleRecord:
        return SimpleRecord(unwrap_warning(await self.raw.rates()))


class NumberReads(SimpleService):
    def search(
        self,
        *,
        number_type: Union[did_models.DIDType, str] = did_models.DIDType.LOCAL,
        tier: Optional[Union[did_models.DIDTier, str]] = None,
        state: Optional[str] = None,
        rate_center: Optional[str] = None,
        zip_code: Optional[Union[str, int]] = None,
        prefix_code: Optional[Union[str, int]] = None,
        contains: Optional[str] = None,
        limit: int = 100,
    ) -> SimpleCollection[Any]:
        request = _number_search_request(
            number_type=number_type,
            tier=tier,
            state=state,
            rate_center=rate_center,
            zip_code=zip_code,
            prefix_code=prefix_code,
            contains=contains,
            limit=limit,
        )
        return _collection((self.raw.available(request),))

    def list(
        self,
        *,
        number: Optional[str] = None,
        per_page: int = 25,
        page: int = 1,
        all_pages: bool = True,
    ) -> SimpleCollection[Any]:
        request = did_models.DIDListRequest(did=number, per_page=per_page, page=page)
        responses = self.raw.pages(request) if all_pages else (self.raw.list(request),)
        return _collection(responses)

    def validate_fraud(
        self, numbers: Union[str, int, Sequence[Union[str, int]]]
    ) -> SimpleCollection[Any]:
        normalized = _phone_values(numbers)
        return _collection((self.raw.validate_fraud(normalized),))


class AsyncNumberReads(SimpleService):
    async def search(self, **kwargs: Any) -> SimpleCollection[Any]:
        request = _number_search_request(**kwargs)
        return _collection((await self.raw.available(request),))

    async def list(
        self,
        *,
        number: Optional[str] = None,
        per_page: int = 25,
        page: int = 1,
        all_pages: bool = True,
    ) -> SimpleCollection[Any]:
        request = did_models.DIDListRequest(did=number, per_page=per_page, page=page)
        if not all_pages:
            return _collection((await self.raw.list(request),))
        responses = []
        async for response in self.raw.pages(request):
            responses.append(response)
        return _collection(responses)

    async def validate_fraud(
        self, numbers: Union[str, int, Sequence[Union[str, int]]]
    ) -> SimpleCollection[Any]:
        normalized = _phone_values(numbers)
        return _collection((await self.raw.validate_fraud(normalized),))


def _number_search_request(**kwargs: Any) -> did_models.DIDAvailabilityRequest:
    number_type = kwargs.get("number_type", did_models.DIDType.LOCAL)
    tier = kwargs.get("tier")
    return did_models.DIDAvailabilityRequest(
        did_type=normalize_enum(did_models.DIDType, number_type),
        tier=normalize_enum(did_models.DIDTier, tier) if tier is not None else None,
        state=kwargs.get("state"),
        ratecenter=kwargs.get("rate_center"),
        zip=int(kwargs["zip_code"]) if kwargs.get("zip_code") is not None else None,
        code=int(kwargs["prefix_code"]) if kwargs.get("prefix_code") is not None else None,
        mask=kwargs.get("contains"),
        total_list=kwargs.get("limit", 100),
    )


class InternationalNumberReads(SimpleService):
    def countries(self, *, number: Optional[Union[str, int]] = None) -> SimpleCollection[Any]:
        request = international_models.InternationalCountriesRequest(
            did=normalize_phone(number) if number is not None else None
        )
        return _collection((self.raw.countries(request),))

    def cities(self, country_code: str) -> SimpleCollection[Any]:
        return _collection((self.raw.cities(country_code),))

    def list(
        self,
        *,
        number: Optional[str] = None,
        per_page: int = 25,
        page: int = 1,
        all_pages: bool = True,
    ) -> SimpleCollection[Any]:
        request = international_models.InternationalDIDListRequest(
            did=number, per_page=per_page, page=page
        )
        return _collection(self.raw.pages(request) if all_pages else (self.raw.list(request),))


class AsyncInternationalNumberReads(SimpleService):
    async def countries(self, *, number: Optional[Union[str, int]] = None) -> SimpleCollection[Any]:
        request = international_models.InternationalCountriesRequest(
            did=normalize_phone(number) if number is not None else None
        )
        return _collection((await self.raw.countries(request),))

    async def cities(self, country_code: str) -> SimpleCollection[Any]:
        return _collection((await self.raw.cities(country_code),))

    async def list(
        self,
        *,
        number: Optional[str] = None,
        per_page: int = 25,
        page: int = 1,
        all_pages: bool = True,
    ) -> SimpleCollection[Any]:
        request = international_models.InternationalDIDListRequest(
            did=number, per_page=per_page, page=page
        )
        if not all_pages:
            return _collection((await self.raw.list(request),))
        responses = []
        async for response in self.raw.pages(request):
            responses.append(response)
        return _collection(responses)


class VoiceReads(SimpleService):
    def trunks(
        self, *, trunk: Optional[str] = None, per_page: int = 25, page: int = 1
    ) -> SimpleCollection[Any]:
        return _collection(
            (
                self.raw.list(
                    sip_models.SIPTrunkListRequest(trunk=trunk, per_page=per_page, page=page)
                ),
            )
        )

    def trunk_status(self, trunk: str) -> SimpleRecord:
        return SimpleRecord(unwrap_warning(self.raw.status(trunk)))

    def blocked_callers(
        self,
        *,
        trunk: Optional[Union[str, Sequence[str]]] = None,
        number: Optional[Union[str, int]] = None,
        per_page: int = 25,
        page: int = 1,
    ) -> SimpleCollection[Any]:
        request = sip_models.BlockedCallersRequest(
            trunk=list(trunk)
            if isinstance(trunk, Sequence) and not isinstance(trunk, str)
            else trunk,
            did=normalize_phone(number) if number is not None else None,
            per_page=per_page,
            page=page,
        )
        return _collection((self.raw.blocked_callers(request),))


class AsyncVoiceReads(SimpleService):
    async def trunks(
        self, *, trunk: Optional[str] = None, per_page: int = 25, page: int = 1
    ) -> SimpleCollection[Any]:
        return _collection(
            (
                await self.raw.list(
                    sip_models.SIPTrunkListRequest(trunk=trunk, per_page=per_page, page=page)
                ),
            )
        )

    async def trunk_status(self, trunk: str) -> SimpleRecord:
        return SimpleRecord(unwrap_warning(await self.raw.status(trunk)))

    async def blocked_callers(self, **kwargs: Any) -> SimpleCollection[Any]:
        request = _blocked_request(**kwargs)
        return _collection((await self.raw.blocked_callers(request),))


def _blocked_request(**kwargs: Any) -> sip_models.BlockedCallersRequest:
    trunk = kwargs.get("trunk")
    return sip_models.BlockedCallersRequest(
        trunk=list(trunk) if isinstance(trunk, Sequence) and not isinstance(trunk, str) else trunk,
        did=normalize_phone(kwargs["number"]) if kwargs.get("number") is not None else None,
        per_page=kwargs.get("per_page", 25),
        page=kwargs.get("page", 1),
    )


class MessageReads(SimpleService):
    def numbers(
        self, *, number: Optional[str] = None, per_page: int = 25, page: int = 1
    ) -> SimpleCollection[Any]:
        return _collection(
            (
                self.raw.list(
                    sms_models.SMSInventoryRequest(did=number, per_page=per_page, page=page)
                ),
            )
        )

    def history(
        self,
        *,
        period: Optional[Union[sms_models.SMSHistoryPeriod, Tuple[date, date], str]] = None,
        direction: Optional[Union[sms_models.SMSDirection, str]] = None,
        per_page: int = 25,
        page: int = 1,
    ) -> SimpleCollection[Any]:
        normalized_period: Any = period
        if isinstance(period, str):
            normalized_period = normalize_enum(sms_models.SMSHistoryPeriod, period)
        if isinstance(period, tuple):
            normalized_period = normalize_date_range(*period)
        request = sms_models.SMSHistoryRequest(
            period=normalized_period,
            direction=normalize_enum(sms_models.SMSDirection, direction)
            if direction is not None
            else None,
            per_page=per_page,
            page=page,
        )
        return _collection((self.raw.history(request),))

    def delivery_status(self, message_id: Union[str, int]) -> SimpleRecord:
        request = sms_models.MessageDeliveryStatusRequest(msg_id=int(message_id))
        return SimpleRecord(unwrap_warning(self.raw.delivery_status(request)).data)

    def carrier(self, numbers: Union[str, int, Sequence[Union[str, int]]]) -> SimpleCollection[Any]:
        request = sms_models.CarrierLookupRequest(tn=_phone_values(numbers))
        return _collection((self.raw.carrier(request),))

    def offnet_status(self, number: Union[str, int]) -> SimpleRecord:
        request = sms_models.OffnetStatusRequest(did=normalize_phone(number))
        return SimpleRecord(unwrap_warning(self.raw.offnet_status(request)).data)


class AsyncMessageReads(SimpleService):
    async def numbers(
        self, *, number: Optional[str] = None, per_page: int = 25, page: int = 1
    ) -> SimpleCollection[Any]:
        return _collection(
            (
                await self.raw.list(
                    sms_models.SMSInventoryRequest(did=number, per_page=per_page, page=page)
                ),
            )
        )

    async def history(self, **kwargs: Any) -> SimpleCollection[Any]:
        request = _message_history_request(**kwargs)
        return _collection((await self.raw.history(request),))

    async def delivery_status(self, message_id: Union[str, int]) -> SimpleRecord:
        result = unwrap_warning(
            await self.raw.delivery_status(
                sms_models.MessageDeliveryStatusRequest(msg_id=int(message_id))
            )
        )
        return SimpleRecord(result.data)

    async def carrier(
        self, numbers: Union[str, int, Sequence[Union[str, int]]]
    ) -> SimpleCollection[Any]:
        request = sms_models.CarrierLookupRequest(tn=_phone_values(numbers))
        return _collection((await self.raw.carrier(request),))

    async def offnet_status(self, number: Union[str, int]) -> SimpleRecord:
        result = unwrap_warning(
            await self.raw.offnet_status(
                sms_models.OffnetStatusRequest(did=normalize_phone(number))
            )
        )
        return SimpleRecord(result.data)


class DLCReads(SimpleService):
    def brands(self, ids: Optional[Union[int, Sequence[int]]] = None) -> SimpleCollection[Any]:
        return _collection((self.raw.list_brands(dlc_models.BrandListRequest(id=_id_filter(ids))),))

    def campaigns(self, ids: Optional[Union[int, Sequence[int]]] = None) -> SimpleCollection[Any]:
        return _collection(
            (self.raw.list_campaigns(dlc_models.CampaignListRequest(id=_id_filter(ids))),)
        )


class AsyncDLCReads(SimpleService):
    async def brands(
        self, ids: Optional[Union[int, Sequence[int]]] = None
    ) -> SimpleCollection[Any]:
        return _collection(
            (await self.raw.list_brands(dlc_models.BrandListRequest(id=_id_filter(ids))),)
        )

    async def campaigns(
        self, ids: Optional[Union[int, Sequence[int]]] = None
    ) -> SimpleCollection[Any]:
        return _collection(
            (await self.raw.list_campaigns(dlc_models.CampaignListRequest(id=_id_filter(ids))),)
        )


class FaxReads(SimpleService):
    def search(
        self,
        *,
        number_type: Union[fax_models.FaxDIDType, str],
        tier: Union[fax_models.FaxTier, str] = fax_models.FaxTier.TIER_1B,
        state: Optional[str] = None,
        rate_center: Optional[str] = None,
        zip_code: Optional[Union[str, int]] = None,
    ) -> SimpleCollection[Any]:
        request = fax_models.FaxAvailabilityRequest(
            did_type=normalize_enum(fax_models.FaxDIDType, number_type),
            tier=normalize_enum(fax_models.FaxTier, tier),
            state=state,
            ratecenter=rate_center,
            zip=int(zip_code) if zip_code is not None else None,
        )
        return _collection((self.raw.available(request),))

    def list(
        self,
        *,
        number: Optional[str] = None,
        per_page: int = 25,
        page: int = 1,
        all_pages: bool = True,
    ) -> SimpleCollection[Any]:
        request = fax_models.FaxListRequest(did=number, per_page=per_page, page=page)
        responses = []
        while True:
            result = unwrap_warning(self.raw.list(request))
            responses.append(result)
            next_page = result.next_page() if all_pages else None
            if next_page is None:
                break
            request = request.model_copy(update={"page": next_page})
        return _collection(responses)


class AsyncFaxReads(SimpleService):
    async def search(self, **kwargs: Any) -> SimpleCollection[Any]:
        request = _fax_search_request(**kwargs)
        return _collection((await self.raw.available(request),))

    async def list(
        self,
        *,
        number: Optional[str] = None,
        per_page: int = 25,
        page: int = 1,
        all_pages: bool = True,
    ) -> SimpleCollection[Any]:
        request = fax_models.FaxListRequest(did=number, per_page=per_page, page=page)
        responses = []
        while True:
            result = unwrap_warning(await self.raw.list(request))
            responses.append(result)
            next_page = result.next_page() if all_pages else None
            if next_page is None:
                break
            request = request.model_copy(update={"page": next_page})
        return _collection(responses)


def _fax_search_request(**kwargs: Any) -> fax_models.FaxAvailabilityRequest:
    return fax_models.FaxAvailabilityRequest(
        did_type=normalize_enum(fax_models.FaxDIDType, kwargs["number_type"]),
        tier=normalize_enum(fax_models.FaxTier, kwargs.get("tier", fax_models.FaxTier.TIER_1B)),
        state=kwargs.get("state"),
        ratecenter=kwargs.get("rate_center"),
        zip=int(kwargs["zip_code"]) if kwargs.get("zip_code") is not None else None,
    )


class EnterpriseFaxReads(SimpleService):
    def list(
        self, *, number: Optional[str] = None, per_page: int = 25, page: int = 1
    ) -> SimpleCollection[Any]:
        return _collection(
            (
                self.raw.list(
                    enterprise_fax_models.EnterpriseFaxListRequest(
                        did=number, per_page=per_page, page=page
                    )
                ),
            )
        )

    def groups(self, short_name: Optional[str] = None) -> SimpleCollection[Any]:
        return _collection(
            (
                self.raw.list_groups(
                    enterprise_fax_models.EnterpriseFaxGroupListRequest(sname=short_name)
                ),
            )
        )

    def users(
        self, *, group: Optional[str] = None, login: Optional[str] = None
    ) -> SimpleCollection[Any]:
        return _collection(
            (
                self.raw.list_users(
                    enterprise_fax_models.EnterpriseFaxUserListRequest(sname=group, fax_login=login)
                ),
            )
        )

    def permissions(
        self, *, login: Optional[str] = None, number: Optional[Union[str, int]] = None
    ) -> SimpleCollection[Any]:
        request = enterprise_fax_models.EnterpriseFaxPermissionListRequest(
            fax_login=login, did=normalize_phone(number) if number is not None else None
        )
        return _collection((self.raw.list_permissions(request),))


class AsyncEnterpriseFaxReads(SimpleService):
    async def list(
        self, *, number: Optional[str] = None, per_page: int = 25, page: int = 1
    ) -> SimpleCollection[Any]:
        return _collection(
            (
                await self.raw.list(
                    enterprise_fax_models.EnterpriseFaxListRequest(
                        did=number, per_page=per_page, page=page
                    )
                ),
            )
        )

    async def groups(self, short_name: Optional[str] = None) -> SimpleCollection[Any]:
        return _collection(
            (
                await self.raw.list_groups(
                    enterprise_fax_models.EnterpriseFaxGroupListRequest(sname=short_name)
                ),
            )
        )

    async def users(
        self, *, group: Optional[str] = None, login: Optional[str] = None
    ) -> SimpleCollection[Any]:
        return _collection(
            (
                await self.raw.list_users(
                    enterprise_fax_models.EnterpriseFaxUserListRequest(sname=group, fax_login=login)
                ),
            )
        )

    async def permissions(
        self, *, login: Optional[str] = None, number: Optional[Union[str, int]] = None
    ) -> SimpleCollection[Any]:
        request = enterprise_fax_models.EnterpriseFaxPermissionListRequest(
            fax_login=login, did=normalize_phone(number) if number is not None else None
        )
        return _collection((await self.raw.list_permissions(request),))


def _message_history_request(**kwargs: Any) -> sms_models.SMSHistoryRequest:
    period = kwargs.get("period")
    if isinstance(period, str):
        period = normalize_enum(sms_models.SMSHistoryPeriod, period)
    if isinstance(period, tuple):
        period = normalize_date_range(*period)
    direction = kwargs.get("direction")
    return sms_models.SMSHistoryRequest(
        period=period,
        direction=normalize_enum(sms_models.SMSDirection, direction)
        if direction is not None
        else None,
        per_page=kwargs.get("per_page", 25),
        page=kwargs.get("page", 1),
    )


class ReportReads(SimpleService):
    def calls(
        self,
        *,
        period: Optional[Union[Period, str, Tuple[datetime, datetime]]] = None,
        number: Optional[Union[str, int]] = None,
        per_page: int = 25,
    ) -> SimpleCollection[Any]:
        normalized: Any = period
        if isinstance(period, str):
            normalized = normalize_enum(Period, period)
        if isinstance(period, tuple):
            start, end = normalize_date_range(*period, require_timezone=True)
            normalized = TimestampRange(
                start=int(cast(datetime, start).timestamp()),
                end=int(cast(datetime, end).timestamp()),
            )
        request = report_models.CallHistoryRequest(
            period=normalized,
            did=normalize_phone(number) if number is not None else None,
            per_page=per_page,
        )
        records = tuple(self.raw.iter_call_history(request))
        return SimpleCollection(tuple(_view(record) for record in records), ())

    def faxes(
        self,
        *,
        numbers: Optional[Union[str, int, Sequence[Union[str, int]]]] = None,
        period: Optional[
            Union[report_models.FaxHistoryPeriod, str, Tuple[datetime, datetime]]
        ] = None,
        per_page: int = 25,
    ) -> SimpleCollection[Any]:
        normalized: Any = period
        if isinstance(period, str):
            normalized = normalize_enum(report_models.FaxHistoryPeriod, period)
        if isinstance(period, tuple):
            normalized = normalize_date_range(*period, require_timezone=True)
        dids = _phone_values(numbers) if numbers is not None else None
        request = report_models.FaxHistoryRequest(did=dids, period=normalized, per_page=per_page)
        records = tuple(self.raw.iter_fax_history(request))
        return SimpleCollection(tuple(_view(record) for record in records), ())


class AsyncReportReads(SimpleService):
    async def calls(self, **kwargs: Any) -> SimpleCollection[Any]:
        request = _call_request(**kwargs)
        records = []
        async for record in self.raw.iter_call_history(request):
            records.append(record)
        return SimpleCollection(tuple(_view(record) for record in records), ())

    async def faxes(self, **kwargs: Any) -> SimpleCollection[Any]:
        request = _fax_history_request(**kwargs)
        records = []
        async for record in self.raw.iter_fax_history(request):
            records.append(record)
        return SimpleCollection(tuple(_view(record) for record in records), ())


def _call_request(**kwargs: Any) -> report_models.CallHistoryRequest:
    period = kwargs.get("period")
    if isinstance(period, str):
        period = normalize_enum(Period, period)
    if isinstance(period, tuple):
        start, end = normalize_date_range(*period, require_timezone=True)
        period = TimestampRange(
            start=int(cast(datetime, start).timestamp()),
            end=int(cast(datetime, end).timestamp()),
        )
    number = kwargs.get("number")
    return report_models.CallHistoryRequest(
        period=period,
        did=normalize_phone(number) if number is not None else None,
        per_page=kwargs.get("per_page", 25),
    )


def _fax_history_request(**kwargs: Any) -> report_models.FaxHistoryRequest:
    period = kwargs.get("period")
    if isinstance(period, str):
        period = normalize_enum(report_models.FaxHistoryPeriod, period)
    if isinstance(period, tuple):
        period = normalize_date_range(*period, require_timezone=True)
    numbers = kwargs.get("numbers")
    dids = _phone_values(numbers) if numbers is not None else None
    return report_models.FaxHistoryRequest(
        did=dids, period=cast(Any, period), per_page=kwargs.get("per_page", 25)
    )


class PortingReads(SimpleService):
    def check(self, numbers: Union[str, int, Sequence[Union[str, int]]]) -> SimpleRecord:
        request = lnp_models.LNPCheckRequest(number2port=_phone_values(numbers))
        return SimpleRecord(unwrap_warning(self.raw.check(request)))

    def list(
        self,
        *,
        number: Optional[str] = None,
        request_ids: Optional[Union[int, Sequence[int]]] = None,
        per_page: int = 10,
        page: int = 1,
    ) -> SimpleCollection[Any]:
        ids = normalize_list(request_ids) if request_ids is not None else None
        return _collection(
            (
                self.raw.list(
                    lnp_models.LNPListRequest(
                        number2port=number, id=ids, per_page=per_page, page=page
                    )
                ),
            )
        )


class AsyncPortingReads(SimpleService):
    async def check(self, numbers: Union[str, int, Sequence[Union[str, int]]]) -> SimpleRecord:
        request = lnp_models.LNPCheckRequest(number2port=_phone_values(numbers))
        return SimpleRecord(unwrap_warning(await self.raw.check(request)))

    async def list(
        self,
        *,
        number: Optional[str] = None,
        request_ids: Optional[Union[int, Sequence[int]]] = None,
        per_page: int = 10,
        page: int = 1,
    ) -> SimpleCollection[Any]:
        ids = normalize_list(request_ids) if request_ids is not None else None
        return _collection(
            (
                await self.raw.list(
                    lnp_models.LNPListRequest(
                        number2port=number, id=ids, per_page=per_page, page=page
                    )
                ),
            )
        )


class ServerReads(SimpleService):
    def list(self, server_ids: Optional[Union[int, Sequence[int]]] = None) -> SimpleCollection[Any]:
        ids = normalize_list(server_ids) if server_ids is not None else None
        return _collection((self.raw.list(server_models.ServerListRequest(server_id=ids)),))

    def backups(self, server_id: int) -> SimpleCollection[Any]:
        return _collection((self.raw.list_backups(server_id),))


class AsyncServerReads(SimpleService):
    async def list(
        self, server_ids: Optional[Union[int, Sequence[int]]] = None
    ) -> SimpleCollection[Any]:
        ids = normalize_list(server_ids) if server_ids is not None else None
        return _collection((await self.raw.list(server_models.ServerListRequest(server_id=ids)),))

    async def backups(self, server_id: int) -> SimpleCollection[Any]:
        return _collection((await self.raw.list_backups(server_id),))


READ_SERVICE_TYPES = {
    "account": (AccountReads, AsyncAccountReads),
    "numbers": (NumberReads, AsyncNumberReads),
    "international_numbers": (InternationalNumberReads, AsyncInternationalNumberReads),
    "voice": (VoiceReads, AsyncVoiceReads),
    "messages": (MessageReads, AsyncMessageReads),
    "dlc": (DLCReads, AsyncDLCReads),
    "fax": (FaxReads, AsyncFaxReads),
    "enterprise_fax": (EnterpriseFaxReads, AsyncEnterpriseFaxReads),
    "reports": (ReportReads, AsyncReportReads),
    "porting": (PortingReads, AsyncPortingReads),
    "servers": (ServerReads, AsyncServerReads),
}
