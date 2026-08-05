from __future__ import annotations

import json
from pathlib import Path

from scripts.check_contract_fixtures import check_fixture, main


def write(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_repository_contract_fixture_evidence_is_sanitized() -> None:
    assert main() == 0


def test_fixture_check_rejects_secrets_and_customer_identifiers(tmp_path: Path) -> None:
    path = tmp_path / "unsafe.json"
    write(
        path,
        {
            "security_key": "secret",
            "email": "person@customer.invalid",
            "phone": "19195551234",
            "ip": "8.8.8.8",
        },
    )
    errors = check_fixture(path)
    assert len(errors) == 4


def test_fixture_check_allows_documentation_values(tmp_path: Path) -> None:
    path = tmp_path / "safe.json"
    write(
        path,
        {
            "email": "person@example.test",
            "phone": "12025550100",
            "ip": "192.0.2.1",
        },
    )
    assert check_fixture(path) == []
