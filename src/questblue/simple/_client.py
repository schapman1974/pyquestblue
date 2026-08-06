"""Sync and async clients for the ergonomic QuestBlue facade."""

from __future__ import annotations

from typing import Any, Optional, Type, TypeVar, Union

import httpx

from questblue._client import DEFAULT_BASE_URL, DEFAULT_TIMEOUT, AsyncQuestBlue, QuestBlue
from questblue.models import WarningResponse
from questblue.transport import TransportHook

from ._errors import QuestBlueWarningError

ResultT = TypeVar("ResultT")


def unwrap_warning(value: Union[ResultT, WarningResponse]) -> ResultT:
    """Return a typed result or raise while retaining a provider warning."""
    if isinstance(value, WarningResponse):
        raise QuestBlueWarningError(value)
    return value


class SimpleService:
    """Base namespace that exposes its authoritative typed resource."""

    def __init__(self, raw: Any) -> None:
        self.raw = raw


def _install_services(facade: Any, raw: Any) -> None:
    mappings = {
        "account": "account",
        "numbers": "dids",
        "international_numbers": "international_dids",
        "voice": "sip_trunks",
        "messages": "sms",
        "dlc": "dlc",
        "fax": "fax",
        "enterprise_fax": "enterprise_fax",
        "reports": "reports",
        "porting": "lnp",
        "servers": "servers",
    }
    for simple_name, raw_name in mappings.items():
        setattr(facade, simple_name, SimpleService(getattr(raw, raw_name)))
    facade.workflows = SimpleService(raw)


class SimpleQuestBlue:
    """Synchronous primitive-input facade over :class:`questblue.QuestBlue`."""

    account: SimpleService
    numbers: SimpleService
    international_numbers: SimpleService
    voice: SimpleService
    messages: SimpleService
    dlc: SimpleService
    fax: SimpleService
    enterprise_fax: SimpleService
    reports: SimpleService
    porting: SimpleService
    servers: SimpleService
    workflows: SimpleService

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        security_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 2,
        http_client: Optional[httpx.Client] = None,
        transport_hook: Optional[TransportHook] = None,
    ) -> None:
        self._raw = QuestBlue(
            username,
            password,
            security_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            http_client=http_client,
            transport_hook=transport_hook,
        )
        self._owns_raw = True
        _install_services(self, self._raw)

    @classmethod
    def wrap(cls: Type[SimpleQuestBlue], client: QuestBlue) -> SimpleQuestBlue:
        """Borrow an existing typed client without taking ownership."""
        instance = cls.__new__(cls)
        instance._raw = client
        instance._owns_raw = False
        _install_services(instance, client)
        return instance

    @property
    def raw(self) -> QuestBlue:
        return self._raw

    def close(self) -> None:
        if self._owns_raw:
            self._raw.close()

    def __enter__(self) -> SimpleQuestBlue:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


class AsyncSimpleQuestBlue:
    """Asynchronous primitive-input facade over :class:`questblue.AsyncQuestBlue`."""

    account: SimpleService
    numbers: SimpleService
    international_numbers: SimpleService
    voice: SimpleService
    messages: SimpleService
    dlc: SimpleService
    fax: SimpleService
    enterprise_fax: SimpleService
    reports: SimpleService
    porting: SimpleService
    servers: SimpleService
    workflows: SimpleService

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        security_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 2,
        http_client: Optional[httpx.AsyncClient] = None,
        transport_hook: Optional[TransportHook] = None,
    ) -> None:
        self._raw = AsyncQuestBlue(
            username,
            password,
            security_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            http_client=http_client,
            transport_hook=transport_hook,
        )
        self._owns_raw = True
        _install_services(self, self._raw)

    @classmethod
    def wrap(cls: Type[AsyncSimpleQuestBlue], client: AsyncQuestBlue) -> AsyncSimpleQuestBlue:
        """Borrow an existing async typed client without taking ownership."""
        instance = cls.__new__(cls)
        instance._raw = client
        instance._owns_raw = False
        _install_services(instance, client)
        return instance

    @property
    def raw(self) -> AsyncQuestBlue:
        return self._raw

    async def close(self) -> None:
        if self._owns_raw:
            await self._raw.close()

    async def __aenter__(self) -> AsyncSimpleQuestBlue:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()
