"""Confirmed primitive-input provisioning services."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Union

from questblue import did as did_models
from questblue import enterprise_fax as enterprise_models
from questblue import fax as fax_models
from questblue import international_did as international_models
from questblue import lnp as lnp_models
from questblue import servers as server_models
from questblue import sip_trunk as sip_models

from ._client import unwrap_warning
from ._errors import ConfirmationRequiredError, MissingProviderIdentifierError
from ._normalizers import normalize_enum, normalize_list, normalize_path, normalize_phone
from ._read import (
    AsyncEnterpriseFaxReads,
    AsyncFaxReads,
    AsyncInternationalNumberReads,
    AsyncNumberReads,
    AsyncPortingReads,
    AsyncServerReads,
    AsyncVoiceReads,
    EnterpriseFaxReads,
    FaxReads,
    InternationalNumberReads,
    NumberReads,
    PortingReads,
    ServerReads,
    VoiceReads,
)
from ._results import OperationPlan, OperationResult, PlannedOperation, Risk

MutationResult = Union[OperationPlan, OperationResult[Any]]


def _phones(value: Any) -> list[int]:
    return [normalize_phone(item) for item in normalize_list(value)]


def _gate(
    name: str,
    risk: Risk,
    arguments: Mapping[str, Any],
    *,
    confirmed: bool,
    dry_run: bool,
) -> Optional[OperationPlan]:
    plan = OperationPlan((PlannedOperation(name=name, risk=risk, arguments=arguments),))
    if dry_run:
        return plan
    if not confirmed:
        raise ConfirmationRequiredError(risk.value)
    return None


def _success(
    raw: Any = None, *, identifiers: Optional[Mapping[str, str]] = None
) -> OperationResult[bool]:
    unwrap_warning(raw)
    return OperationResult(value=True, identifiers=identifiers or {}, raw=raw)


class NumberProvisioning(NumberReads):
    def buy(
        self,
        number: Union[str, int],
        *,
        tier: Optional[Union[did_models.DIDTier, str]] = None,
        trunk: Optional[str] = None,
        confirm_billable: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        did = normalize_phone(number)
        request = did_models.DIDOrderRequest(
            did=did,
            tier=normalize_enum(did_models.DIDTier, tier) if tier is not None else None,
            route2trunk=trunk,
        )
        plan = _gate(
            "dids.order",
            Risk.BILLABLE,
            request.to_request_params(),
            confirmed=confirm_billable,
            dry_run=dry_run,
        )
        return plan or _success(self.raw.order(request), identifiers={"number": str(did)})

    def configure(
        self,
        number: Union[str, int],
        *,
        trunk: Optional[str] = None,
        forward_to: Optional[Union[str, int]] = None,
        note: Optional[str] = None,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        did = normalize_phone(number)
        request = did_models.DIDUpdateRequest(
            did=did,
            route2trunk=trunk,
            forw2did=normalize_phone(forward_to) if forward_to is not None else None,
            note=note,
        )
        plan = _gate(
            "dids.update",
            Risk.ROUTING_CHANGE,
            request.to_request_params(),
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        return plan or _success(self.raw.update(request), identifiers={"number": str(did)})

    def move_to_fax(
        self,
        number: Union[str, int],
        *,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        did = normalize_phone(number)
        plan = _gate(
            "dids.move_to_fax",
            Risk.ROUTING_CHANGE,
            {"did": did},
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        return plan or _success(self.raw.move_to_fax(did), identifiers={"number": str(did)})

    def release(
        self, number: Union[str, int], *, confirm_destructive: bool = False, dry_run: bool = False
    ) -> MutationResult:
        did = normalize_phone(number)
        plan = _gate(
            "dids.delete",
            Risk.DESTRUCTIVE,
            {"did": did},
            confirmed=confirm_destructive,
            dry_run=dry_run,
        )
        return plan or _success(self.raw.delete(did), identifiers={"number": str(did)})


class AsyncNumberProvisioning(AsyncNumberReads):
    async def buy(
        self,
        number: Union[str, int],
        *,
        tier: Optional[Union[did_models.DIDTier, str]] = None,
        trunk: Optional[str] = None,
        confirm_billable: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        did = normalize_phone(number)
        request = did_models.DIDOrderRequest(
            did=did,
            tier=normalize_enum(did_models.DIDTier, tier) if tier is not None else None,
            route2trunk=trunk,
        )
        plan = _gate(
            "dids.order",
            Risk.BILLABLE,
            request.to_request_params(),
            confirmed=confirm_billable,
            dry_run=dry_run,
        )
        return plan or _success(await self.raw.order(request), identifiers={"number": str(did)})

    async def configure(
        self,
        number: Union[str, int],
        *,
        trunk: Optional[str] = None,
        forward_to: Optional[Union[str, int]] = None,
        note: Optional[str] = None,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        did = normalize_phone(number)
        request = did_models.DIDUpdateRequest(
            did=did,
            route2trunk=trunk,
            forw2did=normalize_phone(forward_to) if forward_to is not None else None,
            note=note,
        )
        plan = _gate(
            "dids.update",
            Risk.ROUTING_CHANGE,
            request.to_request_params(),
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        return plan or _success(await self.raw.update(request), identifiers={"number": str(did)})

    async def move_to_fax(
        self,
        number: Union[str, int],
        *,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        did = normalize_phone(number)
        plan = _gate(
            "dids.move_to_fax",
            Risk.ROUTING_CHANGE,
            {"did": did},
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        return plan or _success(await self.raw.move_to_fax(did), identifiers={"number": str(did)})

    async def release(
        self, number: Union[str, int], *, confirm_destructive: bool = False, dry_run: bool = False
    ) -> MutationResult:
        did = normalize_phone(number)
        plan = _gate(
            "dids.delete",
            Risk.DESTRUCTIVE,
            {"did": did},
            confirmed=confirm_destructive,
            dry_run=dry_run,
        )
        return plan or _success(await self.raw.delete(did), identifiers={"number": str(did)})


class InternationalNumberProvisioning(InternationalNumberReads):
    def buy(
        self,
        *,
        country_code: str,
        city: str,
        forward_to: Union[str, int],
        trunk: int,
        confirm_billable: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        request = international_models.InternationalDIDOrderRequest(
            country_code=country_code,
            city=city,
            forward2did=normalize_phone(forward_to),
            route2trunk=trunk,
        )
        plan = _gate(
            "international_dids.order",
            Risk.BILLABLE,
            request.to_request_params(),
            confirmed=confirm_billable,
            dry_run=dry_run,
        )
        if plan:
            return plan
        response = unwrap_warning(self.raw.order(request))
        return OperationResult(value=True, raw=response)

    def configure(
        self,
        number: Union[str, int],
        *,
        forward_to: Union[str, int],
        trunk: int,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        request = international_models.InternationalDIDUpdateRequest(
            did=normalize_phone(number), forward2did=normalize_phone(forward_to), route2trunk=trunk
        )
        plan = _gate(
            "international_dids.update",
            Risk.ROUTING_CHANGE,
            request.to_request_params(),
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        return plan or _success(self.raw.update(request))

    def release(
        self, number: Union[str, int], *, confirm_destructive: bool = False, dry_run: bool = False
    ) -> MutationResult:
        did = normalize_phone(number)
        plan = _gate(
            "international_dids.delete",
            Risk.DESTRUCTIVE,
            {"did": did},
            confirmed=confirm_destructive,
            dry_run=dry_run,
        )
        return plan or _success(self.raw.delete(did))


class AsyncInternationalNumberProvisioning(AsyncInternationalNumberReads):
    async def buy(
        self,
        *,
        country_code: str,
        city: str,
        forward_to: Union[str, int],
        trunk: int,
        confirm_billable: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        request = international_models.InternationalDIDOrderRequest(
            country_code=country_code,
            city=city,
            forward2did=normalize_phone(forward_to),
            route2trunk=trunk,
        )
        plan = _gate(
            "international_dids.order",
            Risk.BILLABLE,
            request.to_request_params(),
            confirmed=confirm_billable,
            dry_run=dry_run,
        )
        if plan:
            return plan
        return OperationResult(value=True, raw=unwrap_warning(await self.raw.order(request)))

    async def configure(
        self,
        number: Union[str, int],
        *,
        forward_to: Union[str, int],
        trunk: int,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        request = international_models.InternationalDIDUpdateRequest(
            did=normalize_phone(number), forward2did=normalize_phone(forward_to), route2trunk=trunk
        )
        plan = _gate(
            "international_dids.update",
            Risk.ROUTING_CHANGE,
            request.to_request_params(),
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        return plan or _success(await self.raw.update(request))

    async def release(
        self, number: Union[str, int], *, confirm_destructive: bool = False, dry_run: bool = False
    ) -> MutationResult:
        did = normalize_phone(number)
        plan = _gate(
            "international_dids.delete",
            Risk.DESTRUCTIVE,
            {"did": did},
            confirmed=confirm_destructive,
            dry_run=dry_run,
        )
        return plan or _success(await self.raw.delete(did))


class VoiceProvisioning(VoiceReads):
    def configure_trunk(
        self,
        trunk: str,
        *,
        password: Optional[str] = None,
        ip_address: Optional[str] = None,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        request = sip_models.SIPTrunkUpdateRequest(
            trunk=trunk, password=password, ip_address=ip_address
        )
        plan = _gate(
            "sip_trunks.update",
            Risk.ROUTING_CHANGE,
            request.to_request_params(),
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        return plan or _success(self.raw.update(request), identifiers={"trunk": trunk})

    def set_caller_block(
        self,
        trunk: Union[str, Sequence[str]],
        number: Union[str, int],
        *,
        blocked: bool = True,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        request = sip_models.BlockCallerRequest(
            trunk=list(trunk) if not isinstance(trunk, str) else trunk,
            did=normalize_phone(number),
            action=sip_models.BlockAction.BLOCK if blocked else sip_models.BlockAction.UNBLOCK,
        )
        plan = _gate(
            "sip_trunks.block_caller",
            Risk.ROUTING_CHANGE,
            request.to_request_params(),
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        return plan or _success(self.raw.block_caller(request))

    def create_registration_trunk(
        self,
        trunk: str,
        password: str,
        *,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        request = sip_models.SIPTrunkCreateRequest(trunk=trunk, password=password)
        plan = _gate(
            "sip_trunks.create",
            Risk.ROUTING_CHANGE,
            request.to_request_params(),
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        return plan or _success(self.raw.create(request), identifiers={"trunk": trunk})

    def create_static_trunk(
        self,
        trunk: str,
        ip_address: str,
        *,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        request = sip_models.SIPTrunkCreateRequest(trunk=trunk, ip_address=ip_address)
        plan = _gate(
            "sip_trunks.create",
            Risk.ROUTING_CHANGE,
            request.to_request_params(),
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        return plan or _success(self.raw.create(request), identifiers={"trunk": trunk})

    def delete_trunk(
        self, trunk: str, *, confirm_destructive: bool = False, dry_run: bool = False
    ) -> MutationResult:
        plan = _gate(
            "sip_trunks.delete",
            Risk.DESTRUCTIVE,
            {"trunk": trunk},
            confirmed=confirm_destructive,
            dry_run=dry_run,
        )
        return plan or _success(self.raw.delete(trunk), identifiers={"trunk": trunk})


class AsyncVoiceProvisioning(AsyncVoiceReads):
    async def configure_trunk(
        self,
        trunk: str,
        *,
        password: Optional[str] = None,
        ip_address: Optional[str] = None,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        request = sip_models.SIPTrunkUpdateRequest(
            trunk=trunk, password=password, ip_address=ip_address
        )
        plan = _gate(
            "sip_trunks.update",
            Risk.ROUTING_CHANGE,
            request.to_request_params(),
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        return plan or _success(await self.raw.update(request), identifiers={"trunk": trunk})

    async def set_caller_block(
        self,
        trunk: Union[str, Sequence[str]],
        number: Union[str, int],
        *,
        blocked: bool = True,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        request = sip_models.BlockCallerRequest(
            trunk=list(trunk) if not isinstance(trunk, str) else trunk,
            did=normalize_phone(number),
            action=sip_models.BlockAction.BLOCK if blocked else sip_models.BlockAction.UNBLOCK,
        )
        plan = _gate(
            "sip_trunks.block_caller",
            Risk.ROUTING_CHANGE,
            request.to_request_params(),
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        return plan or _success(await self.raw.block_caller(request))

    async def create_registration_trunk(
        self,
        trunk: str,
        password: str,
        *,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        request = sip_models.SIPTrunkCreateRequest(trunk=trunk, password=password)
        plan = _gate(
            "sip_trunks.create",
            Risk.ROUTING_CHANGE,
            request.to_request_params(),
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        return plan or _success(await self.raw.create(request), identifiers={"trunk": trunk})

    async def create_static_trunk(
        self,
        trunk: str,
        ip_address: str,
        *,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        request = sip_models.SIPTrunkCreateRequest(trunk=trunk, ip_address=ip_address)
        plan = _gate(
            "sip_trunks.create",
            Risk.ROUTING_CHANGE,
            request.to_request_params(),
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        return plan or _success(await self.raw.create(request), identifiers={"trunk": trunk})

    async def delete_trunk(
        self, trunk: str, *, confirm_destructive: bool = False, dry_run: bool = False
    ) -> MutationResult:
        plan = _gate(
            "sip_trunks.delete",
            Risk.DESTRUCTIVE,
            {"trunk": trunk},
            confirmed=confirm_destructive,
            dry_run=dry_run,
        )
        return plan or _success(await self.raw.delete(trunk), identifiers={"trunk": trunk})


class FaxProvisioning(FaxReads):
    def configure(
        self,
        number: Union[str, int],
        *,
        email: Optional[str] = None,
        account_name: Optional[str] = None,
        login: Optional[str] = None,
        password: Optional[str] = None,
        note: Optional[str] = None,
        paused: Optional[bool] = None,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        did = normalize_phone(number)
        arguments = {
            "did": did,
            "fax_email": email,
            "fax_name": account_name,
            "fax_login": login,
            "fax_password": password,
            "note": note,
            "paused": paused,
        }
        plan = _gate(
            "fax.configure",
            Risk.ROUTING_CHANGE,
            arguments,
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        if plan:
            return plan
        raw = []
        if any(value is not None for value in (email, account_name, login, password, note)):
            raw.append(
                self.raw.update(
                    fax_models.FaxUpdateRequest(
                        did=did,
                        fax_email=email,
                        fax_name=account_name,
                        fax_login=login,
                        fax_password=password,
                        note=note,
                    )
                )
            )
        if paused is not None:
            raw.append(
                self.raw.pause(
                    fax_models.FaxPauseRequest(
                        did=did,
                        action=fax_models.PauseAction.PAUSE
                        if paused
                        else fax_models.PauseAction.UNPAUSE,
                    )
                )
            )
        for value in raw:
            unwrap_warning(value)
        return OperationResult(value=True, raw=tuple(raw))

    def buy(
        self,
        number: Union[str, int],
        *,
        tier: Union[fax_models.FaxTier, str] = fax_models.FaxTier.TIER_1B,
        email: Optional[str] = None,
        account_name: Optional[str] = None,
        login: Optional[str] = None,
        password: Optional[str] = None,
        confirm_billable: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        did = normalize_phone(number)
        request = fax_models.FaxOrderRequest(
            did=did,
            tier=normalize_enum(fax_models.FaxTier, tier),
            fax_email=email,
            fax_name=account_name,
            fax_login=login,
            fax_password=password,
        )
        plan = _gate(
            "fax.create",
            Risk.BILLABLE,
            request.to_request_params(),
            confirmed=confirm_billable,
            dry_run=dry_run,
        )
        return plan or _success(self.raw.create(request), identifiers={"number": str(did)})

    def move_to_voice(
        self,
        number: Union[str, int],
        *,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        did = normalize_phone(number)
        plan = _gate(
            "fax.move_to_voice",
            Risk.ROUTING_CHANGE,
            {"did": did},
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        return plan or _success(self.raw.move_to_voice(did))

    def release(
        self, number: Union[str, int], *, confirm_destructive: bool = False, dry_run: bool = False
    ) -> MutationResult:
        did = normalize_phone(number)
        plan = _gate(
            "fax.delete",
            Risk.DESTRUCTIVE,
            {"did": did},
            confirmed=confirm_destructive,
            dry_run=dry_run,
        )
        return plan or _success(self.raw.delete(did))


class AsyncFaxProvisioning(AsyncFaxReads):
    async def configure(
        self,
        number: Union[str, int],
        *,
        email: Optional[str] = None,
        account_name: Optional[str] = None,
        login: Optional[str] = None,
        password: Optional[str] = None,
        note: Optional[str] = None,
        paused: Optional[bool] = None,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        did = normalize_phone(number)
        arguments = {
            "did": did,
            "fax_email": email,
            "fax_name": account_name,
            "fax_login": login,
            "fax_password": password,
            "note": note,
            "paused": paused,
        }
        plan = _gate(
            "fax.configure",
            Risk.ROUTING_CHANGE,
            arguments,
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        if plan:
            return plan
        raw = []
        if any(value is not None for value in (email, account_name, login, password, note)):
            raw.append(
                await self.raw.update(
                    fax_models.FaxUpdateRequest(
                        did=did,
                        fax_email=email,
                        fax_name=account_name,
                        fax_login=login,
                        fax_password=password,
                        note=note,
                    )
                )
            )
        if paused is not None:
            raw.append(
                await self.raw.pause(
                    fax_models.FaxPauseRequest(
                        did=did,
                        action=fax_models.PauseAction.PAUSE
                        if paused
                        else fax_models.PauseAction.UNPAUSE,
                    )
                )
            )
        for value in raw:
            unwrap_warning(value)
        return OperationResult(value=True, raw=tuple(raw))

    async def buy(
        self,
        number: Union[str, int],
        *,
        tier: Union[fax_models.FaxTier, str] = fax_models.FaxTier.TIER_1B,
        email: Optional[str] = None,
        account_name: Optional[str] = None,
        login: Optional[str] = None,
        password: Optional[str] = None,
        confirm_billable: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        did = normalize_phone(number)
        request = fax_models.FaxOrderRequest(
            did=did,
            tier=normalize_enum(fax_models.FaxTier, tier),
            fax_email=email,
            fax_name=account_name,
            fax_login=login,
            fax_password=password,
        )
        plan = _gate(
            "fax.create",
            Risk.BILLABLE,
            request.to_request_params(),
            confirmed=confirm_billable,
            dry_run=dry_run,
        )
        return plan or _success(await self.raw.create(request), identifiers={"number": str(did)})

    async def move_to_voice(
        self,
        number: Union[str, int],
        *,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        did = normalize_phone(number)
        plan = _gate(
            "fax.move_to_voice",
            Risk.ROUTING_CHANGE,
            {"did": did},
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        return plan or _success(await self.raw.move_to_voice(did))

    async def release(
        self, number: Union[str, int], *, confirm_destructive: bool = False, dry_run: bool = False
    ) -> MutationResult:
        did = normalize_phone(number)
        plan = _gate(
            "fax.delete",
            Risk.DESTRUCTIVE,
            {"did": did},
            confirmed=confirm_destructive,
            dry_run=dry_run,
        )
        return plan or _success(await self.raw.delete(did))


class EnterpriseFaxProvisioning(EnterpriseFaxReads):
    def buy(
        self,
        number: Union[str, int],
        *,
        group: Optional[str] = None,
        tier: Union[fax_models.FaxTier, str] = fax_models.FaxTier.TIER_1B,
        confirm_billable: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        did = normalize_phone(number)
        request = enterprise_models.EnterpriseFaxOrderRequest(
            did=did, sname=group, tier=normalize_enum(fax_models.FaxTier, tier)
        )
        plan = _gate(
            "enterprise_fax.create",
            Risk.BILLABLE,
            request.to_request_params(),
            confirmed=confirm_billable,
            dry_run=dry_run,
        )
        return plan or _success(self.raw.create(request), identifiers={"number": str(did)})

    def create_user(
        self,
        *,
        login: str,
        password: str,
        group: str,
        first_name: str,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        is_admin: bool = False,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        request = enterprise_models.EnterpriseFaxUserCreateRequest(
            fax_login=login,
            fax_password=password,
            sname=group,
            fax_name=first_name,
            fax_lname=last_name,
            fax_email=email,
            is_admin=fax_models.FaxToggle.ON if is_admin else fax_models.FaxToggle.OFF,
        )
        plan = _gate(
            "enterprise_fax.create_user",
            Risk.ROUTING_CHANGE,
            request.to_request_params(),
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        return plan or _success(self.raw.create_user(request), identifiers={"login": login})

    def set_permission(
        self,
        *,
        login: str,
        number: Union[str, int],
        allow_send: bool = False,
        allow_delete: bool = False,
        allow_inbound_list: bool = False,
        allow_outbound_list: bool = False,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        toggle = fax_models.FaxToggle
        request = enterprise_models.EnterpriseFaxPermissionRequest(
            fax_login=login,
            did=normalize_phone(number),
            allow_send=toggle.ON if allow_send else toggle.OFF,
            allow_delete=toggle.ON if allow_delete else toggle.OFF,
            allow_list_in=toggle.ON if allow_inbound_list else toggle.OFF,
            allow_list_out=toggle.ON if allow_outbound_list else toggle.OFF,
        )
        plan = _gate(
            "enterprise_fax.set_permission",
            Risk.ROUTING_CHANGE,
            request.to_request_params(),
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        return plan or _success(self.raw.set_permission(request))

    def release(
        self, number: Union[str, int], *, confirm_destructive: bool = False, dry_run: bool = False
    ) -> MutationResult:
        did = normalize_phone(number)
        plan = _gate(
            "enterprise_fax.delete",
            Risk.DESTRUCTIVE,
            {"did": did},
            confirmed=confirm_destructive,
            dry_run=dry_run,
        )
        return plan or _success(self.raw.delete(did))

    def create_group(
        self,
        short_name: str,
        name: str,
        *,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        request = enterprise_models.EnterpriseFaxGroupCreateRequest(sname=short_name, name=name)
        plan = _gate(
            "enterprise_fax.create_group",
            Risk.ROUTING_CHANGE,
            request.to_request_params(),
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        return plan or _success(self.raw.create_group(request), identifiers={"group": short_name})

    def delete_group(
        self, short_name: str, *, confirm_destructive: bool = False, dry_run: bool = False
    ) -> MutationResult:
        plan = _gate(
            "enterprise_fax.delete_group",
            Risk.DESTRUCTIVE,
            {"sname": short_name},
            confirmed=confirm_destructive,
            dry_run=dry_run,
        )
        return plan or _success(self.raw.delete_group(short_name))


class AsyncEnterpriseFaxProvisioning(AsyncEnterpriseFaxReads):
    async def buy(
        self,
        number: Union[str, int],
        *,
        group: Optional[str] = None,
        tier: Union[fax_models.FaxTier, str] = fax_models.FaxTier.TIER_1B,
        confirm_billable: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        did = normalize_phone(number)
        request = enterprise_models.EnterpriseFaxOrderRequest(
            did=did, sname=group, tier=normalize_enum(fax_models.FaxTier, tier)
        )
        plan = _gate(
            "enterprise_fax.create",
            Risk.BILLABLE,
            request.to_request_params(),
            confirmed=confirm_billable,
            dry_run=dry_run,
        )
        return plan or _success(await self.raw.create(request), identifiers={"number": str(did)})

    async def create_user(
        self,
        *,
        login: str,
        password: str,
        group: str,
        first_name: str,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        is_admin: bool = False,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        request = enterprise_models.EnterpriseFaxUserCreateRequest(
            fax_login=login,
            fax_password=password,
            sname=group,
            fax_name=first_name,
            fax_lname=last_name,
            fax_email=email,
            is_admin=fax_models.FaxToggle.ON if is_admin else fax_models.FaxToggle.OFF,
        )
        plan = _gate(
            "enterprise_fax.create_user",
            Risk.ROUTING_CHANGE,
            request.to_request_params(),
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        return plan or _success(await self.raw.create_user(request), identifiers={"login": login})

    async def set_permission(
        self,
        *,
        login: str,
        number: Union[str, int],
        allow_send: bool = False,
        allow_delete: bool = False,
        allow_inbound_list: bool = False,
        allow_outbound_list: bool = False,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        toggle = fax_models.FaxToggle
        request = enterprise_models.EnterpriseFaxPermissionRequest(
            fax_login=login,
            did=normalize_phone(number),
            allow_send=toggle.ON if allow_send else toggle.OFF,
            allow_delete=toggle.ON if allow_delete else toggle.OFF,
            allow_list_in=toggle.ON if allow_inbound_list else toggle.OFF,
            allow_list_out=toggle.ON if allow_outbound_list else toggle.OFF,
        )
        plan = _gate(
            "enterprise_fax.set_permission",
            Risk.ROUTING_CHANGE,
            request.to_request_params(),
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        return plan or _success(await self.raw.set_permission(request))

    async def release(
        self, number: Union[str, int], *, confirm_destructive: bool = False, dry_run: bool = False
    ) -> MutationResult:
        did = normalize_phone(number)
        plan = _gate(
            "enterprise_fax.delete",
            Risk.DESTRUCTIVE,
            {"did": did},
            confirmed=confirm_destructive,
            dry_run=dry_run,
        )
        return plan or _success(await self.raw.delete(did))

    async def create_group(
        self,
        short_name: str,
        name: str,
        *,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        request = enterprise_models.EnterpriseFaxGroupCreateRequest(sname=short_name, name=name)
        plan = _gate(
            "enterprise_fax.create_group",
            Risk.ROUTING_CHANGE,
            request.to_request_params(),
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        return plan or _success(
            await self.raw.create_group(request), identifiers={"group": short_name}
        )

    async def delete_group(
        self, short_name: str, *, confirm_destructive: bool = False, dry_run: bool = False
    ) -> MutationResult:
        plan = _gate(
            "enterprise_fax.delete_group",
            Risk.DESTRUCTIVE,
            {"sname": short_name},
            confirmed=confirm_destructive,
            dry_run=dry_run,
        )
        return plan or _success(await self.raw.delete_group(short_name))


class PortingProvisioning(PortingReads):
    def create_draft(
        self,
        *,
        numbers: Union[str, int, Sequence[Union[str, int]]],
        bill: Union[str, Path],
        provider_name: str,
        company: str,
        account_number: str,
        authorized_contact: str,
        contact_title: str,
        street_number: str,
        street_name: str,
        city: str,
        zipcode: str,
        billing_number: Union[str, int],
        state: Optional[str] = None,
        trunk: Optional[str] = None,
        confirm_compliance: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        upload = lnp_models.LNPBillUpload.from_path(
            normalize_path(
                bill,
                allowed_extensions=lnp_models.SUPPORTED_LNP_BILL_EXTENSIONS,
                max_bytes=lnp_models.MAX_LNP_BILL_SIZE,
            )
        )
        request = lnp_models.LNPCreateRequest.with_bill(
            upload,
            number2port=_phones(numbers),
            provider_name=provider_name,
            company=company,
            account_no=account_number,
            authorize_contact=authorized_contact,
            contact_title=contact_title,
            street_no=street_number,
            street_name=street_name,
            city=city,
            state=state,
            zipcode=zipcode,
            billing_telephone_no=str(normalize_phone(billing_number)),
            trunk=trunk,
            status=lnp_models.LNPSubmissionStatus.DRAFT,
        )
        plan = _gate(
            "lnp.create",
            Risk.COMPLIANCE_SENSITIVE,
            request.to_request_params(),
            confirmed=confirm_compliance,
            dry_run=dry_run,
        )
        if plan:
            return plan
        response = unwrap_warning(self.raw.create(request))
        if not response.data or not response.data[0].id:
            raise MissingProviderIdentifierError("LNP request ID")
        request_id = response.data[0].id
        return OperationResult(value=request_id, identifiers={"lnp_id": request_id}, raw=response)


class AsyncPortingProvisioning(AsyncPortingReads):
    async def create_draft(self, **kwargs: Any) -> MutationResult:
        request, plan = _porting_request_and_plan(**kwargs)
        if plan:
            return plan
        response = unwrap_warning(await self.raw.create(request))
        if not response.data or not response.data[0].id:
            raise MissingProviderIdentifierError("LNP request ID")
        request_id = response.data[0].id
        return OperationResult(value=request_id, identifiers={"lnp_id": request_id}, raw=response)


def _porting_request_and_plan(
    **kwargs: Any,
) -> tuple[lnp_models.LNPCreateRequest, Optional[OperationPlan]]:
    upload = lnp_models.LNPBillUpload.from_path(
        normalize_path(
            kwargs["bill"],
            allowed_extensions=lnp_models.SUPPORTED_LNP_BILL_EXTENSIONS,
            max_bytes=lnp_models.MAX_LNP_BILL_SIZE,
        )
    )
    request = lnp_models.LNPCreateRequest.with_bill(
        upload,
        number2port=_phones(kwargs["numbers"]),
        provider_name=kwargs["provider_name"],
        company=kwargs["company"],
        account_no=kwargs["account_number"],
        authorize_contact=kwargs["authorized_contact"],
        contact_title=kwargs["contact_title"],
        street_no=kwargs["street_number"],
        street_name=kwargs["street_name"],
        city=kwargs["city"],
        state=kwargs.get("state"),
        zipcode=kwargs["zipcode"],
        billing_telephone_no=str(normalize_phone(kwargs["billing_number"])),
        trunk=kwargs.get("trunk"),
        status=lnp_models.LNPSubmissionStatus.DRAFT,
    )
    return request, _gate(
        "lnp.create",
        Risk.COMPLIANCE_SENSITIVE,
        request.to_request_params(),
        confirmed=kwargs.get("confirm_compliance", False),
        dry_run=kwargs.get("dry_run", False),
    )


def _server_software(
    product: str,
    *,
    email: str,
    password: Optional[str],
    domain_name: Optional[str],
    inbound_trunk_name: Optional[str],
    note: Optional[str],
) -> server_models.ServerSoftware:
    key = product.casefold().replace("-", "_")
    values: dict[str, Any] = {"email": email}
    if password is not None:
        values["password"] = password
    if domain_name is not None:
        values["domain_name"] = domain_name
    if inbound_trunk_name is not None:
        values["inbound_trunk_name"] = inbound_trunk_name
    model_types = {
        "3cx": server_models.ThreeCXConfig,
        "qube": server_models.QubeConfig,
        "qube_tdr": server_models.QubeTDRConfig,
        "qubev2": server_models.QubeV2Config,
        "sbc": server_models.SBCConfig,
        "vital_pbx": server_models.VitalPBXConfig,
    }
    if key not in model_types:
        raise ValueError("product must be one of: 3cx, qube, qube-tdr, qubev2, sbc, vital-pbx")
    return server_models.ServerSoftware.model_validate(
        {key: model_types[key](**values), "note": note}
    )


class ServerProvisioning(ServerReads):
    def schedule_backups(
        self,
        server_id: int,
        schedule: Union[server_models.BackupSchedule, str],
        *,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        request = server_models.BackupScheduleRequest(
            server_id=server_id, schedule=normalize_enum(server_models.BackupSchedule, schedule)
        )
        plan = _gate(
            "servers.manage_backup_schedule",
            Risk.ROUTING_CHANGE,
            request.to_request_params(),
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        return plan or _success(self.raw.manage_backup_schedule(request))

    def restore(
        self,
        server_id: int,
        backup_id: int,
        *,
        confirm_destructive: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        request = server_models.BackupRequest(server_id=server_id, backup_id=backup_id)
        plan = _gate(
            "servers.restore_backup",
            Risk.DESTRUCTIVE,
            request.to_request_params(),
            confirmed=confirm_destructive,
            dry_run=dry_run,
        )
        if plan:
            return plan
        return OperationResult(value=True, raw=unwrap_warning(self.raw.restore_backup(request)))

    def remove_backup(
        self,
        server_id: int,
        backup_id: int,
        *,
        confirm_destructive: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        request = server_models.BackupRequest(server_id=server_id, backup_id=backup_id)
        plan = _gate(
            "servers.remove_backup",
            Risk.DESTRUCTIVE,
            request.to_request_params(),
            confirmed=confirm_destructive,
            dry_run=dry_run,
        )
        if plan:
            return plan
        return OperationResult(value=True, raw=unwrap_warning(self.raw.remove_backup(request)))

    def provision(
        self,
        *,
        server_type: Union[server_models.ServerType, str],
        product: str,
        email: str,
        password: Optional[str] = None,
        domain_name: Optional[str] = None,
        inbound_trunk_name: Optional[str] = None,
        note: Optional[str] = None,
        confirm_billable: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        request = server_models.ServerOrderRequest(
            server_type=normalize_enum(server_models.ServerType, server_type),
            params=_server_software(
                product,
                email=email,
                password=password,
                domain_name=domain_name,
                inbound_trunk_name=inbound_trunk_name,
                note=note,
            ),
        )
        plan = _gate(
            "servers.create",
            Risk.BILLABLE,
            request.to_request_params(),
            confirmed=confirm_billable,
            dry_run=dry_run,
        )
        if plan:
            return plan
        response = unwrap_warning(self.raw.create(request))
        server_id = response.data.server_id
        return OperationResult(
            value=server_id, identifiers={"server_id": str(server_id)}, raw=response
        )

    def add_ip(
        self,
        server_id: int,
        ip_address: str,
        *,
        note: Optional[str] = None,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        request = server_models.ServerIPRequest(
            server_id=server_id, ip_address=ip_address, note=note
        )
        plan = _gate(
            "servers.add_ip",
            Risk.ROUTING_CHANGE,
            request.to_request_params(),
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        return plan or _success(self.raw.add_ip(request), identifiers={"server_id": str(server_id)})

    def release(
        self, server_id: int, *, confirm_destructive: bool = False, dry_run: bool = False
    ) -> MutationResult:
        plan = _gate(
            "servers.delete",
            Risk.DESTRUCTIVE,
            {"server_id": server_id},
            confirmed=confirm_destructive,
            dry_run=dry_run,
        )
        return plan or _success(self.raw.delete(server_id))


class AsyncServerProvisioning(AsyncServerReads):
    async def schedule_backups(
        self,
        server_id: int,
        schedule: Union[server_models.BackupSchedule, str],
        *,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        request = server_models.BackupScheduleRequest(
            server_id=server_id, schedule=normalize_enum(server_models.BackupSchedule, schedule)
        )
        plan = _gate(
            "servers.manage_backup_schedule",
            Risk.ROUTING_CHANGE,
            request.to_request_params(),
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        return plan or _success(await self.raw.manage_backup_schedule(request))

    async def restore(
        self,
        server_id: int,
        backup_id: int,
        *,
        confirm_destructive: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        request = server_models.BackupRequest(server_id=server_id, backup_id=backup_id)
        plan = _gate(
            "servers.restore_backup",
            Risk.DESTRUCTIVE,
            request.to_request_params(),
            confirmed=confirm_destructive,
            dry_run=dry_run,
        )
        if plan:
            return plan
        return OperationResult(
            value=True, raw=unwrap_warning(await self.raw.restore_backup(request))
        )

    async def remove_backup(
        self,
        server_id: int,
        backup_id: int,
        *,
        confirm_destructive: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        request = server_models.BackupRequest(server_id=server_id, backup_id=backup_id)
        plan = _gate(
            "servers.remove_backup",
            Risk.DESTRUCTIVE,
            request.to_request_params(),
            confirmed=confirm_destructive,
            dry_run=dry_run,
        )
        if plan:
            return plan
        return OperationResult(
            value=True, raw=unwrap_warning(await self.raw.remove_backup(request))
        )

    async def provision(
        self,
        *,
        server_type: Union[server_models.ServerType, str],
        product: str,
        email: str,
        password: Optional[str] = None,
        domain_name: Optional[str] = None,
        inbound_trunk_name: Optional[str] = None,
        note: Optional[str] = None,
        confirm_billable: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        request = server_models.ServerOrderRequest(
            server_type=normalize_enum(server_models.ServerType, server_type),
            params=_server_software(
                product,
                email=email,
                password=password,
                domain_name=domain_name,
                inbound_trunk_name=inbound_trunk_name,
                note=note,
            ),
        )
        plan = _gate(
            "servers.create",
            Risk.BILLABLE,
            request.to_request_params(),
            confirmed=confirm_billable,
            dry_run=dry_run,
        )
        if plan:
            return plan
        response = unwrap_warning(await self.raw.create(request))
        server_id = response.data.server_id
        return OperationResult(
            value=server_id, identifiers={"server_id": str(server_id)}, raw=response
        )

    async def add_ip(
        self,
        server_id: int,
        ip_address: str,
        *,
        note: Optional[str] = None,
        confirm_routing_change: bool = False,
        dry_run: bool = False,
    ) -> MutationResult:
        request = server_models.ServerIPRequest(
            server_id=server_id, ip_address=ip_address, note=note
        )
        plan = _gate(
            "servers.add_ip",
            Risk.ROUTING_CHANGE,
            request.to_request_params(),
            confirmed=confirm_routing_change,
            dry_run=dry_run,
        )
        return plan or _success(
            await self.raw.add_ip(request), identifiers={"server_id": str(server_id)}
        )

    async def release(
        self, server_id: int, *, confirm_destructive: bool = False, dry_run: bool = False
    ) -> MutationResult:
        plan = _gate(
            "servers.delete",
            Risk.DESTRUCTIVE,
            {"server_id": server_id},
            confirmed=confirm_destructive,
            dry_run=dry_run,
        )
        return plan or _success(await self.raw.delete(server_id))


PROVISION_SERVICE_TYPES = {
    "numbers": (NumberProvisioning, AsyncNumberProvisioning),
    "international_numbers": (
        InternationalNumberProvisioning,
        AsyncInternationalNumberProvisioning,
    ),
    "voice": (VoiceProvisioning, AsyncVoiceProvisioning),
    "fax": (FaxProvisioning, AsyncFaxProvisioning),
    "enterprise_fax": (EnterpriseFaxProvisioning, AsyncEnterpriseFaxProvisioning),
    "porting": (PortingProvisioning, AsyncPortingProvisioning),
    "servers": (ServerProvisioning, AsyncServerProvisioning),
}
