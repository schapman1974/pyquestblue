"""HTTP clients for the QuestBlue API."""

from __future__ import annotations

import asyncio
import os
import time
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, Mapping, Optional, Tuple, TypeVar

import httpx

from ._exceptions import (
    QuestBlueAPIError,
    QuestBlueAuthenticationError,
    QuestBlueConfigurationError,
    QuestBlueConnectionError,
    QuestBlueRateLimitError,
    QuestBlueServerError,
)
from .pagination import AsyncPaginator, ItemSelector, SyncPaginator

if TYPE_CHECKING:
    from ._resources import (
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

DEFAULT_BASE_URL = "https://api.questblue.com"
SECONDARY_BASE_URL = "https://api2.questblue.com"
DEFAULT_TIMEOUT = 60.0
_RETRY_STATUSES = frozenset((408, 409, 429))
_SENSITIVE_HEADERS = frozenset(("authorization", "security-key"))
PageItemT = TypeVar("PageItemT")


def _credentials(
    username: Optional[str], password: Optional[str], security_key: Optional[str]
) -> Tuple[str, str, str]:
    values = (
        username or os.getenv("QUESTBLUE_USERNAME"),
        password or os.getenv("QUESTBLUE_PASSWORD"),
        security_key or os.getenv("QUESTBLUE_SECURITY_KEY"),
    )
    if not all(values):
        raise QuestBlueConfigurationError(
            "username, password, and security_key are required (or set "
            "QUESTBLUE_USERNAME, QUESTBLUE_PASSWORD, and QUESTBLUE_SECURITY_KEY)"
        )
    return values[0], values[1], values[2]  # type: ignore[return-value]


def _encode_value(value: Any) -> str:
    if isinstance(value, Enum):
        value = value.value
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (list, tuple, set)):
        return ",".join(_encode_value(item) for item in value)
    return str(value)


def _query(params: Optional[Mapping[str, Any]]) -> Dict[str, str]:
    return {key: _encode_value(value) for key, value in (params or {}).items() if value is not None}


def _retry_delay(response: Optional[httpx.Response], attempt: int) -> float:
    if response is not None:
        retry_after = response.headers.get("retry-after")
        if retry_after:
            try:
                return max(0.0, min(float(retry_after), 60.0))
            except ValueError:
                try:
                    parsed = parsedate_to_datetime(retry_after)
                    now = datetime.now(parsed.tzinfo)
                    return float(max(0.0, min((parsed - now).total_seconds(), 60.0)))
                except (TypeError, ValueError, OverflowError):
                    pass
    return float(min(0.5 * (2**attempt), 8.0))


def _should_retry(response: httpx.Response) -> bool:
    return response.status_code in _RETRY_STATUSES or response.status_code >= 500


def _parse(response: httpx.Response) -> Any:
    if not response.content:
        return None
    content_type = response.headers.get("content-type", "").lower()
    if "json" in content_type:
        return response.json()
    try:
        return response.json()
    except ValueError:
        if content_type.startswith(("application/pdf", "application/octet-stream", "image/")):
            return response.content
        return response.text


def _error(response: httpx.Response) -> QuestBlueAPIError:
    body = _parse(response)
    message = f"QuestBlue API request failed with HTTP {response.status_code}"
    if isinstance(body, Mapping):
        detail = body.get("error") or body.get("message") or body.get("detail")
        if detail:
            message = f"{message}: {detail}"
    request_id = response.headers.get("x-request-id") or response.headers.get("request-id")
    kwargs = {
        "status_code": response.status_code,
        "request_id": request_id,
        "response": response,
        "body": body,
    }
    if response.status_code in (401, 403):
        return QuestBlueAuthenticationError(message, **kwargs)
    if response.status_code == 429:
        return QuestBlueRateLimitError(message, **kwargs)
    if response.status_code >= 500:
        return QuestBlueServerError(message, **kwargs)
    return QuestBlueAPIError(message, **kwargs)


class QuestBlue:
    """Synchronous client for the QuestBlue API."""

    account: Account
    dids: DIDs
    international_dids: InternationalDIDs
    sip_trunks: SIPTrunks
    sms: SMS
    dlc: DLC
    fax: Fax
    enterprise_fax: EnterpriseFax
    reports: Reports
    lnp: LNP
    servers: Servers

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
    ) -> None:
        username, password, security_key = _credentials(username, password, security_key)
        if max_retries < 0:
            raise QuestBlueConfigurationError("max_retries must be zero or greater")
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self._auth = httpx.BasicAuth(username, password)
        self._headers = {"Accept": "application/json", "Security-Key": security_key}
        self._owns_client = http_client is None
        self._http = http_client or httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
        )
        self._install_resources()

    def _install_resources(self) -> None:
        from ._resources import install_resources

        install_resources(self)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
    ) -> Any:
        """Issue an authenticated API request and return its decoded body."""
        for attempt in range(self.max_retries + 1):
            try:
                if json is not None:
                    response = self._http.request(
                        method,
                        path,
                        params=_query(params),
                        auth=self._auth,
                        headers=self._headers,
                        json=json,
                    )
                else:
                    response = self._http.request(
                        method,
                        path,
                        params=_query(params),
                        auth=self._auth,
                        headers=self._headers,
                    )
            except httpx.RequestError as exc:
                if attempt >= self.max_retries:
                    raise QuestBlueConnectionError(f"Unable to reach QuestBlue: {exc}") from exc
                time.sleep(_retry_delay(None, attempt))
                continue
            if _should_retry(response) and attempt < self.max_retries:
                delay = _retry_delay(response, attempt)
                response.close()
                time.sleep(delay)
                continue
            # QuestBlue documents 206 as an application-level error response.
            if response.status_code == 206 or response.is_error:
                raise _error(response)
            return _parse(response)
        raise AssertionError("unreachable")

    def close(self) -> None:
        if self._owns_client:
            self._http.close()

    def paginate(
        self,
        path: str,
        *,
        method: str = "GET",
        params: Optional[Mapping[str, Any]] = None,
        start_page: int = 1,
        max_pages: int = 10_000,
        item_parser: Optional[Callable[[Any], PageItemT]] = None,
        item_selector: Optional[ItemSelector] = None,
    ) -> SyncPaginator[PageItemT]:
        """Lazily iterate a paginated endpoint while retaining raw page access."""
        base_params = dict(params or {})

        def fetch_page(page: int) -> Mapping[str, Any]:
            payload = self.request(method, path, params={**base_params, "page": page})
            if not isinstance(payload, Mapping):
                raise TypeError("Paginated QuestBlue response must be a JSON object")
            return payload

        return SyncPaginator(
            fetch_page,
            start_page=start_page,
            max_pages=max_pages,
            item_parser=item_parser,
            item_selector=item_selector,
        )

    def __enter__(self) -> "QuestBlue":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


class AsyncQuestBlue:
    """Asynchronous client for the QuestBlue API."""

    account: Account
    dids: DIDs
    international_dids: InternationalDIDs
    sip_trunks: SIPTrunks
    sms: SMS
    dlc: DLC
    fax: Fax
    enterprise_fax: EnterpriseFax
    reports: Reports
    lnp: LNP
    servers: Servers

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
    ) -> None:
        username, password, security_key = _credentials(username, password, security_key)
        if max_retries < 0:
            raise QuestBlueConfigurationError("max_retries must be zero or greater")
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self._auth = httpx.BasicAuth(username, password)
        self._headers = {"Accept": "application/json", "Security-Key": security_key}
        self._owns_client = http_client is None
        self._http = http_client or httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
        )
        self._install_resources()

    def _install_resources(self) -> None:
        from ._resources import install_resources

        install_resources(self)

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
    ) -> Any:
        """Issue an authenticated API request and return its decoded body."""
        for attempt in range(self.max_retries + 1):
            try:
                if json is not None:
                    response = await self._http.request(
                        method,
                        path,
                        params=_query(params),
                        auth=self._auth,
                        headers=self._headers,
                        json=json,
                    )
                else:
                    response = await self._http.request(
                        method,
                        path,
                        params=_query(params),
                        auth=self._auth,
                        headers=self._headers,
                    )
            except httpx.RequestError as exc:
                if attempt >= self.max_retries:
                    raise QuestBlueConnectionError(f"Unable to reach QuestBlue: {exc}") from exc
                await asyncio.sleep(_retry_delay(None, attempt))
                continue
            if _should_retry(response) and attempt < self.max_retries:
                delay = _retry_delay(response, attempt)
                await response.aclose()
                await asyncio.sleep(delay)
                continue
            if response.status_code == 206 or response.is_error:
                raise _error(response)
            return _parse(response)
        raise AssertionError("unreachable")

    async def close(self) -> None:
        if self._owns_client:
            await self._http.aclose()

    def paginate(
        self,
        path: str,
        *,
        method: str = "GET",
        params: Optional[Mapping[str, Any]] = None,
        start_page: int = 1,
        max_pages: int = 10_000,
        item_parser: Optional[Callable[[Any], PageItemT]] = None,
        item_selector: Optional[ItemSelector] = None,
    ) -> AsyncPaginator[PageItemT]:
        """Lazily iterate a paginated endpoint while retaining raw page access."""
        base_params = dict(params or {})

        async def fetch_page(page: int) -> Mapping[str, Any]:
            payload = await self.request(method, path, params={**base_params, "page": page})
            if not isinstance(payload, Mapping):
                raise TypeError("Paginated QuestBlue response must be a JSON object")
            return payload

        return AsyncPaginator(
            fetch_page,
            start_page=start_page,
            max_pages=max_pages,
            item_parser=item_parser,
            item_selector=item_selector,
        )

    async def __aenter__(self) -> "AsyncQuestBlue":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()


def redact_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """Return headers safe for debug logging."""
    return {
        key: "[REDACTED]" if key.lower() in _SENSITIVE_HEADERS else value
        for key, value in headers.items()
    }
