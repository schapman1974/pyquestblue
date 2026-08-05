#!/usr/bin/env python3
"""Reject secrets/customer data and broken evidence links in contract fixtures."""

from __future__ import annotations

import ipaddress
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterator, Tuple

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "contracts"
MATRIX = ROOT / "contracts" / "verification-matrix.json"
SENSITIVE_KEYS = re.compile(r"(?:password|security.?key|authorization|secret|token|api.?key)", re.I)
EMAIL = re.compile(r"^[^@\s]+@([^@\s]+)$")
PHONE = re.compile(r"^1?\d{10}$")


def values(value: Any, path: str = "$") -> Iterator[Tuple[str, Any]]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield from values(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from values(item, f"{path}[{index}]")
    else:
        yield path, value


def label(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def check_fixture(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    for location, value in values(payload):
        key = location.rsplit(".", 1)[-1]
        if SENSITIVE_KEYS.search(key):
            errors.append(f"{label(path)}:{location}: sensitive key")
        if not isinstance(value, str):
            continue
        email = EMAIL.fullmatch(value)
        if email and email.group(1) not in {"example.com", "example.test", "example.org"}:
            errors.append(f"{label(path)}:{location}: non-synthetic email")
        if PHONE.fullmatch(value) and not value.lstrip("1").startswith("20255501"):
            errors.append(f"{label(path)}:{location}: non-synthetic phone number")
        try:
            address = ipaddress.ip_address(value)
        except ValueError:
            continue
        if not (address.is_private or address.is_reserved):
            errors.append(f"{label(path)}:{location}: public IP address")
    return errors


def main() -> int:
    errors: list[str] = []
    fixture_paths = sorted(FIXTURES.glob("*.json"))
    if not fixture_paths:
        errors.append("no recorded contract fixtures found")
    for path in fixture_paths:
        errors.extend(check_fixture(path))
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    for entry in matrix.get("classes", []):
        for evidence in entry.get("evidence", []):
            if not (ROOT / evidence).exists():
                errors.append(f"verification matrix evidence does not exist: {evidence}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Verified {len(fixture_paths)} sanitized contract fixtures and evidence matrix.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
