"""Reusable synchronous and asynchronous QuestBlue pagination."""

from __future__ import annotations

from dataclasses import dataclass
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Generic,
    Iterable,
    Iterator,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    cast,
)

from ._exceptions import QuestBluePaginationError
from .models import PageMetadata

ItemT = TypeVar("ItemT")
Payload = Mapping[str, Any]
ItemParser = Callable[[Any], ItemT]
ItemSelector = Callable[[Payload], Iterable[Any]]
SyncPageFetcher = Callable[[int], Payload]
AsyncPageFetcher = Callable[[int], Awaitable[Payload]]


def _identity(value: Any) -> Any:
    return value


def _default_items(payload: Payload) -> Iterable[Any]:
    data = payload.get("data", [])
    if data is None:
        return ()
    if isinstance(data, Sequence) and not isinstance(data, (str, bytes, bytearray)):
        return data
    raise TypeError(
        "Paginated response data is not a sequence; provide an item_selector for this endpoint"
    )


@dataclass(frozen=True)
class Page(Generic[ItemT]):
    """One validated page while preserving the raw decoded response."""

    items: Tuple[ItemT, ...]
    metadata: PageMetadata
    raw: Payload

    @property
    def current_page(self) -> int:
        return self.metadata.current_page

    @property
    def total_pages(self) -> Optional[int]:
        return self.metadata.total_pages

    @property
    def total(self) -> Optional[int]:
        return self.metadata.total


def parse_page(
    payload: Payload,
    *,
    requested_page: int,
    item_parser: Optional[ItemParser[ItemT]] = None,
    item_selector: Optional[ItemSelector] = None,
) -> Page[ItemT]:
    parse_item = item_parser or cast(ItemParser[ItemT], _identity)
    select_items = item_selector or _default_items
    raw_items = select_items(payload)
    items = tuple(parse_item(item) for item in raw_items)
    metadata = PageMetadata.from_payload(payload, requested_page=requested_page)
    return Page(items=items, metadata=metadata, raw=payload)


class SyncPaginator(Generic[ItemT]):
    """Lazy synchronous iterator over QuestBlue collection pages and items."""

    def __init__(
        self,
        fetch_page: SyncPageFetcher,
        *,
        start_page: int = 1,
        max_pages: int = 10_000,
        item_parser: Optional[ItemParser[ItemT]] = None,
        item_selector: Optional[ItemSelector] = None,
    ) -> None:
        if start_page < 1:
            raise ValueError("start_page must be at least 1")
        if max_pages < 1:
            raise ValueError("max_pages must be at least 1")
        self._fetch_page = fetch_page
        self._start_page = start_page
        self._max_pages = max_pages
        self._item_parser = item_parser
        self._item_selector = item_selector

    def pages(self) -> Iterator[Page[ItemT]]:
        requested_page = self._start_page
        seen = set()
        for _ in range(self._max_pages):
            if requested_page in seen:
                raise QuestBluePaginationError(
                    f"QuestBlue pagination repeated page {requested_page}"
                )
            seen.add(requested_page)
            payload = self._fetch_page(requested_page)
            page = parse_page(
                payload,
                requested_page=requested_page,
                item_parser=self._item_parser,
                item_selector=self._item_selector,
            )
            yield page
            next_page = page.metadata.next_page(len(page.items))
            if next_page is None:
                return
            requested_page = next_page
        raise QuestBluePaginationError(f"QuestBlue pagination exceeded max_pages={self._max_pages}")

    def __iter__(self) -> Iterator[ItemT]:
        for page in self.pages():
            yield from page.items


class AsyncPaginator(Generic[ItemT]):
    """Lazy asynchronous iterator over QuestBlue collection pages and items."""

    def __init__(
        self,
        fetch_page: AsyncPageFetcher,
        *,
        start_page: int = 1,
        max_pages: int = 10_000,
        item_parser: Optional[ItemParser[ItemT]] = None,
        item_selector: Optional[ItemSelector] = None,
    ) -> None:
        if start_page < 1:
            raise ValueError("start_page must be at least 1")
        if max_pages < 1:
            raise ValueError("max_pages must be at least 1")
        self._fetch_page = fetch_page
        self._start_page = start_page
        self._max_pages = max_pages
        self._item_parser = item_parser
        self._item_selector = item_selector

    async def pages(self) -> AsyncIterator[Page[ItemT]]:
        requested_page = self._start_page
        seen = set()
        for _ in range(self._max_pages):
            if requested_page in seen:
                raise QuestBluePaginationError(
                    f"QuestBlue pagination repeated page {requested_page}"
                )
            seen.add(requested_page)
            payload = await self._fetch_page(requested_page)
            page = parse_page(
                payload,
                requested_page=requested_page,
                item_parser=self._item_parser,
                item_selector=self._item_selector,
            )
            yield page
            next_page = page.metadata.next_page(len(page.items))
            if next_page is None:
                return
            requested_page = next_page
        raise QuestBluePaginationError(f"QuestBlue pagination exceeded max_pages={self._max_pages}")

    def __aiter__(self) -> AsyncIterator[ItemT]:
        return self._items()

    async def _items(self) -> AsyncIterator[ItemT]:
        async for page in self.pages():
            for item in page.items:
                yield item
