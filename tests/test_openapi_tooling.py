from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.api_coverage import ROOT, build_report, render
from scripts.update_openapi import ContractError, digest, normalize, semantic_diff, update_contract


def minimal_spec(*, version: str = "1.0.0", include_post: bool = False) -> dict:
    path_item = {"get": {"operationId": "listThings", "responses": {"200": {}}}}
    if include_post:
        path_item["post"] = {"operationId": "createThing", "responses": {"200": {}}}
    return {
        "openapi": "3.1.0",
        "info": {"title": "Test", "version": version},
        "paths": {"/things": path_item},
        "components": {"schemas": {"Thing": {"type": "object"}}},
    }


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_normalization_is_deterministic() -> None:
    first = normalize({"z": 1, "a": {"y": 2, "b": 3}})
    second = normalize({"a": {"b": 3, "y": 2}, "z": 1})
    assert first == second
    assert first.endswith("\n")
    assert digest(first) == digest(second)


def test_semantic_diff_reports_operations_schemas_and_version() -> None:
    old = minimal_spec()
    new = minimal_spec(version="1.1.0", include_post=True)
    new["components"]["schemas"]["Warning"] = {"type": "object"}

    result = semantic_diff(old, new)

    assert result["api_version"] == {"from": "1.0.0", "to": "1.1.0"}
    assert result["operations"]["added"] == [{"method": "POST", "path": "/things"}]
    assert result["operations"]["changed"] == []
    assert result["schemas"]["added"] == ["Warning"]


def test_semantic_diff_detects_changes_within_existing_operations_and_schemas() -> None:
    old = minimal_spec()
    new = minimal_spec()
    new["paths"]["/things"]["get"]["summary"] = "Updated behavior"
    new["components"]["schemas"]["Thing"]["description"] = "Updated schema"

    result = semantic_diff(old, new)

    assert result["operations"]["changed"] == [{"method": "GET", "path": "/things"}]
    assert result["schemas"]["changed"] == ["Thing"]


def test_update_check_uses_local_source_without_network(tmp_path: Path) -> None:
    spec = minimal_spec()
    source = tmp_path / "source.json"
    spec_dir = tmp_path / "spec"
    metadata = spec_dir / "metadata.json"
    write_json(source, spec)

    changed, _ = update_contract(
        source=str(source),
        spec_dir=spec_dir,
        metadata_path=metadata,
        check=False,
        retrieved_at="2026-01-01",
    )
    assert changed is True
    pinned = spec_dir / "questblue-openapi-1.0.0.json"
    assert pinned.read_text(encoding="utf-8") == normalize(spec)
    assert json.loads(metadata.read_text())["retrieved_at"] == "2026-01-01"

    changed, diff = update_contract(
        source=str(source), spec_dir=spec_dir, metadata_path=metadata, check=True
    )
    assert changed is False
    assert diff["operations"]["added"] == []

    write_json(source, minimal_spec(version="1.1.0", include_post=True))
    changed, diff = update_contract(
        source=str(source), spec_dir=spec_dir, metadata_path=metadata, check=True
    )
    assert changed is True
    assert diff["operations"]["added"] == [{"method": "POST", "path": "/things"}]


def test_update_rejects_an_invalid_contract(tmp_path: Path) -> None:
    source = tmp_path / "invalid.json"
    write_json(source, {"hello": "world"})
    with pytest.raises(ContractError, match="openapi version"):
        update_contract(
            source=str(source),
            spec_dir=tmp_path / "spec",
            metadata_path=tmp_path / "spec" / "metadata.json",
            check=True,
        )


def test_update_rejects_a_pinned_checksum_mismatch(tmp_path: Path) -> None:
    spec = minimal_spec()
    source = tmp_path / "source.json"
    spec_dir = tmp_path / "spec"
    metadata = spec_dir / "metadata.json"
    write_json(source, spec)
    update_contract(
        source=str(source),
        spec_dir=spec_dir,
        metadata_path=metadata,
        check=False,
        retrieved_at="2026-01-01",
    )
    pinned = spec_dir / "questblue-openapi-1.0.0.json"
    pinned.write_text(normalize(minimal_spec(version="tampered")), encoding="utf-8")

    with pytest.raises(ContractError, match="checksum mismatch"):
        update_contract(source=str(source), spec_dir=spec_dir, metadata_path=metadata, check=True)


def test_repository_coverage_maps_every_pinned_operation() -> None:
    report = build_report(
        spec_path=ROOT / "spec" / "questblue-openapi-2.3.2.json",
        resources_path=ROOT / "src" / "questblue" / "_resources.py",
        client_path=ROOT / "src" / "questblue" / "_client.py",
        tests_path=ROOT / "tests",
        doc_paths=(ROOT / "README.md", ROOT / "ROADMAP.md"),
    )

    assert report["summary"] == {
        "documented_operations": 103,
        "extra_sdk_operations": 0,
        "mapped_operations": 103,
        "missing_sdk_operations": 0,
        "sync_async_parity": True,
    }
    assert report["unmapped"] == []
    assert report["undocumented_sdk_operations"] == []
    account_operations = [
        operation for operation in report["operations"] if operation["path"].startswith("/account")
    ]
    assert len(account_operations) == 14
    assert all(operation["response_model"] for operation in account_operations)
    assert all(operation["unit_tested"] for operation in account_operations)
    did_operations = [
        operation
        for operation in report["operations"]
        if operation["path"] == "/did" or operation["path"].startswith("/did/")
    ]
    assert len(did_operations) == 9
    assert all(operation["response_model"] for operation in did_operations)
    assert all(operation["unit_tested"] for operation in did_operations)
    assert render(report).endswith("\n")


def test_coverage_report_detects_missing_and_extra_operations(tmp_path: Path) -> None:
    resources = tmp_path / "_resources.py"
    source = (ROOT / "src" / "questblue" / "_resources.py").read_text(encoding="utf-8")
    resources.write_text(
        source.replace('"/account/getbalance"', '"/not-in-spec"'), encoding="utf-8"
    )

    report = build_report(
        spec_path=ROOT / "spec" / "questblue-openapi-2.3.2.json",
        resources_path=resources,
        client_path=ROOT / "src" / "questblue" / "_client.py",
        tests_path=ROOT / "tests",
        doc_paths=(),
    )

    assert report["summary"]["missing_sdk_operations"] == 1
    assert report["summary"]["extra_sdk_operations"] == 1
    assert report["unmapped"] == [{"method": "GET", "path": "/account/getbalance"}]


def test_coverage_report_detects_sync_async_parity_failure(tmp_path: Path) -> None:
    client = tmp_path / "_client.py"
    source = (ROOT / "src" / "questblue" / "_client.py").read_text(encoding="utf-8")
    client.write_text(
        source.replace("        install_resources(self)\n", "        pass\n", 1),
        encoding="utf-8",
    )

    report = build_report(
        spec_path=ROOT / "spec" / "questblue-openapi-2.3.2.json",
        resources_path=ROOT / "src" / "questblue" / "_resources.py",
        client_path=client,
        tests_path=ROOT / "tests",
        doc_paths=(),
    )

    assert report["summary"]["sync_async_parity"] is False
