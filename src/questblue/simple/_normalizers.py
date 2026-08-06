"""Deterministic input normalization shared by sync and async helpers."""

from __future__ import annotations

import os
import re
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import (
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

EnumT = TypeVar("EnumT", bound=Enum)
ValueT = TypeVar("ValueT")
DateValue = Union[date, datetime]
PathValue = Union[str, os.PathLike[str]]
_PHONE_SEPARATORS = re.compile(r"[\s().-]")


def normalize_phone(value: Union[str, int]) -> int:
    """Return a 7-15 digit telephone number as an integer."""
    if isinstance(value, bool):
        raise ValueError("phone number must be a string or integer")
    text = str(value).strip()
    if text.startswith("+"):
        text = text[1:]
    digits = _PHONE_SEPARATORS.sub("", text)
    if not digits.isascii() or not digits.isdigit() or not 7 <= len(digits) <= 15:
        raise ValueError("phone number must contain 7 to 15 digits without an extension")
    if digits.startswith("0"):
        raise ValueError("phone number must not begin with zero")
    return int(digits)


def normalize_enum(
    enum_type: Type[EnumT],
    value: Union[EnumT, str],
    *,
    aliases: Optional[Mapping[str, Union[EnumT, str]]] = None,
) -> EnumT:
    """Resolve an enum member by exact value/name or an explicit friendly alias."""
    if isinstance(value, enum_type):
        return value
    if not isinstance(value, str) or not value:
        raise ValueError(f"value must be a non-empty string or {enum_type.__name__}")
    key = value.casefold()
    lookup: Dict[str, EnumT] = {}
    for member in enum_type:
        lookup[str(member.value).casefold()] = member
        lookup[member.name.casefold()] = member
    for alias, target in (aliases or {}).items():
        if isinstance(target, enum_type):
            lookup[alias.casefold()] = target
        else:
            target_key = str(target).casefold()
            if target_key not in lookup:
                raise ValueError(f"alias {alias!r} targets an unknown {enum_type.__name__} value")
            lookup[alias.casefold()] = lookup[target_key]
    try:
        return lookup[key]
    except KeyError as exc:
        choices = ", ".join(str(member.value) for member in enum_type)
        raise ValueError(
            f"unknown {enum_type.__name__} value {value!r}; expected one of: {choices}"
        ) from exc


def normalize_date_range(
    start: DateValue,
    end: DateValue,
    *,
    require_timezone: bool = False,
) -> Tuple[DateValue, DateValue]:
    """Validate an ordered, consistently typed date or datetime range."""
    if isinstance(start, datetime) != isinstance(end, datetime):
        raise ValueError("start and end must both be dates or both be datetimes")
    if isinstance(start, datetime):
        datetime_end = cast(datetime, end)
        start_aware = start.tzinfo is not None and start.utcoffset() is not None
        end_aware = datetime_end.tzinfo is not None and datetime_end.utcoffset() is not None
        if start_aware != end_aware:
            raise ValueError("start and end must use consistent timezone awareness")
        if require_timezone and not start_aware:
            raise ValueError("start and end must be timezone-aware datetimes")
    if end < start:
        raise ValueError("end must be greater than or equal to start")
    return start, end


def normalize_path(
    value: PathValue,
    *,
    allowed_extensions: Optional[Iterable[str]] = None,
    max_bytes: Optional[int] = None,
) -> Path:
    """Resolve and validate an explicit local file path without reading it."""
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise ValueError("file path must identify an existing regular file")
    if allowed_extensions is not None:
        allowed = {extension.lower().lstrip(".") for extension in allowed_extensions}
        if path.suffix.lower().lstrip(".") not in allowed:
            raise ValueError("file extension is not supported")
    if max_bytes is not None and path.stat().st_size > max_bytes:
        raise ValueError(f"file exceeds the maximum size of {max_bytes} bytes")
    return path


def normalize_file(
    value: Union[bytes, bytearray, PathValue],
    *,
    allowed_extensions: Optional[Iterable[str]] = None,
    max_bytes: Optional[int] = None,
) -> Tuple[Optional[str], bytes]:
    """Return an optional filename and immutable file bytes."""
    if isinstance(value, (bytes, bytearray)):
        content = bytes(value)
        if max_bytes is not None and len(content) > max_bytes:
            raise ValueError(f"file exceeds the maximum size of {max_bytes} bytes")
        return None, content
    path = normalize_path(value, allowed_extensions=allowed_extensions, max_bytes=max_bytes)
    return path.name, path.read_bytes()


def normalize_list(value: Union[ValueT, Sequence[ValueT]]) -> List[ValueT]:
    """Return a new list for a scalar or non-string sequence."""
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    if isinstance(value, Sequence):
        return list(value)
    return [value]
