#!/usr/bin/env python3
"""Fetch, normalize, compare, and pin QuestBlue's OpenAPI contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Set, Tuple, cast
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = "https://docs.questblue.com/openapispec.json"
DEFAULT_SPEC_DIR = ROOT / "spec"
DEFAULT_METADATA = DEFAULT_SPEC_DIR / "metadata.json"
HTTP_METHODS = frozenset(("delete", "get", "head", "options", "patch", "post", "put", "trace"))

Operation = Tuple[str, str]


class ContractError(RuntimeError):
    """The upstream or pinned OpenAPI contract is invalid."""


def load_source(source: str) -> Dict[str, Any]:
    """Load JSON from an HTTPS URL or local path."""
    parsed = urlparse(source)
    if parsed.scheme == "https":
        request = urllib.request.Request(source, headers={"User-Agent": "pyquestblue-spec-tool"})
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read()
    elif parsed.scheme:
        raise ContractError("Remote OpenAPI sources must use HTTPS")
    else:
        payload = Path(source).read_bytes()
    try:
        document = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"Unable to parse OpenAPI JSON from {source}: {exc}") from exc
    validate_contract(document)
    return cast(Dict[str, Any], document)


def validate_contract(document: Any) -> None:
    """Validate the minimum shape required by the maintenance tools."""
    if not isinstance(document, dict):
        raise ContractError("OpenAPI document must be a JSON object")
    if not isinstance(document.get("openapi"), str):
        raise ContractError("OpenAPI document is missing its openapi version")
    info = document.get("info")
    if not isinstance(info, dict) or not isinstance(info.get("version"), str):
        raise ContractError("OpenAPI document is missing info.version")
    if not isinstance(document.get("paths"), dict):
        raise ContractError("OpenAPI document is missing paths")


def normalize(document: Mapping[str, Any]) -> str:
    """Return the canonical JSON representation."""
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def digest(normalized: str) -> str:
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def operations(document: Mapping[str, Any]) -> Set[Operation]:
    result: Set[Operation] = set()
    paths = document.get("paths", {})
    if not isinstance(paths, Mapping):
        return result
    for path, path_item in paths.items():
        if not isinstance(path, str) or not isinstance(path_item, Mapping):
            continue
        for method in path_item:
            if isinstance(method, str) and method.lower() in HTTP_METHODS:
                result.add((method.upper(), path))
    return result


def operation_documents(document: Mapping[str, Any]) -> Dict[Operation, Any]:
    result: Dict[Operation, Any] = {}
    paths = document.get("paths", {})
    if not isinstance(paths, Mapping):
        return result
    for path, path_item in paths.items():
        if not isinstance(path, str) or not isinstance(path_item, Mapping):
            continue
        for method, operation in path_item.items():
            if isinstance(method, str) and method.lower() in HTTP_METHODS:
                result[(method.upper(), path)] = operation
    return result


def schema_names(document: Mapping[str, Any]) -> Set[str]:
    components = document.get("components", {})
    if not isinstance(components, Mapping):
        return set()
    schemas = components.get("schemas", {})
    return {str(name) for name in schemas} if isinstance(schemas, Mapping) else set()


def schema_documents(document: Mapping[str, Any]) -> Dict[str, Any]:
    components = document.get("components", {})
    if not isinstance(components, Mapping):
        return {}
    schemas = components.get("schemas", {})
    if not isinstance(schemas, Mapping):
        return {}
    return {str(name): schema for name, schema in schemas.items()}


def _format_operations(values: Iterable[Operation]) -> list[Dict[str, str]]:
    return [{"method": method, "path": path} for method, path in sorted(values)]


def semantic_diff(old: Optional[Mapping[str, Any]], new: Mapping[str, Any]) -> Dict[str, Any]:
    """Summarize review-relevant changes between two contracts."""
    old = old or {}
    old_operations = operations(old)
    new_operations = operations(new)
    old_operation_documents = operation_documents(old)
    new_operation_documents = operation_documents(new)
    old_schemas = schema_names(old)
    new_schemas = schema_names(new)
    old_schema_documents = schema_documents(old)
    new_schema_documents = schema_documents(new)
    old_info = old.get("info", {}) if isinstance(old.get("info", {}), Mapping) else {}
    new_info = new.get("info", {}) if isinstance(new.get("info", {}), Mapping) else {}
    return {
        "api_version": {"from": old_info.get("version"), "to": new_info.get("version")},
        "operations": {
            "added": _format_operations(new_operations - old_operations),
            "changed": _format_operations(
                operation
                for operation in old_operations & new_operations
                if old_operation_documents[operation] != new_operation_documents[operation]
            ),
            "removed": _format_operations(old_operations - new_operations),
            "total_before": len(old_operations),
            "total_after": len(new_operations),
        },
        "schemas": {
            "added": sorted(new_schemas - old_schemas),
            "changed": sorted(
                schema
                for schema in old_schemas & new_schemas
                if old_schema_documents[schema] != new_schema_documents[schema]
            ),
            "removed": sorted(old_schemas - new_schemas),
            "total_before": len(old_schemas),
            "total_after": len(new_schemas),
        },
    }


def read_pinned(metadata_path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[Path]]:
    if not metadata_path.exists():
        return None, None
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    spec_file = metadata.get("spec_file")
    if not isinstance(spec_file, str):
        raise ContractError(f"{metadata_path} is missing spec_file")
    path = metadata_path.parent / spec_file
    if not path.exists():
        raise ContractError(f"Pinned OpenAPI file does not exist: {path}")
    document = json.loads(path.read_text(encoding="utf-8"))
    validate_contract(document)
    expected_digest = metadata.get("sha256")
    actual_digest = digest(normalize(document))
    if expected_digest != actual_digest:
        raise ContractError(
            f"Pinned OpenAPI checksum mismatch for {path}: "
            f"metadata has {expected_digest!r}, calculated {actual_digest}"
        )
    return document, path


def update_contract(
    *,
    source: str,
    spec_dir: Path,
    metadata_path: Path,
    check: bool,
    retrieved_at: Optional[str] = None,
) -> Tuple[bool, Dict[str, Any]]:
    """Check or update the pinned contract, returning (changed, semantic diff)."""
    new_document = load_source(source)
    old_document, _old_path = read_pinned(metadata_path)
    new_normalized = normalize(new_document)
    old_normalized = normalize(old_document) if old_document is not None else None
    changed = old_normalized != new_normalized
    changes = semantic_diff(old_document, new_document)
    if check or not changed:
        return changed, changes

    info = new_document["info"]
    api_version = str(info["version"])
    spec_dir.mkdir(parents=True, exist_ok=True)
    spec_path = spec_dir / f"questblue-openapi-{api_version}.json"
    spec_path.write_text(new_normalized, encoding="utf-8")
    metadata = {
        "api_version": api_version,
        "openapi_version": str(new_document["openapi"]),
        "retrieved_at": retrieved_at or datetime.now(timezone.utc).date().isoformat(),
        "sha256": digest(new_normalized),
        "source": source,
        "spec_file": spec_path.name,
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(normalize(metadata), encoding="utf-8")
    return changed, changes


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--source", default=DEFAULT_SOURCE, help="HTTPS URL or local JSON file")
    result.add_argument("--spec-dir", type=Path, default=DEFAULT_SPEC_DIR)
    result.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    result.add_argument("--check", action="store_true", help="Report drift without writing files")
    result.add_argument("--retrieved-at", help=argparse.SUPPRESS)
    return result


def main(argv: Optional[list[str]] = None) -> int:
    args = parser().parse_args(argv)
    try:
        changed, changes = update_contract(
            source=args.source,
            spec_dir=args.spec_dir,
            metadata_path=args.metadata,
            check=args.check,
            retrieved_at=args.retrieved_at,
        )
    except (ContractError, OSError) as exc:
        print(f"OpenAPI contract error: {exc}", file=sys.stderr)
        return 2
    if changed:
        print(json.dumps(changes, indent=2, sort_keys=True))
        if args.check:
            print("QuestBlue OpenAPI drift detected.", file=sys.stderr)
            return 1
        print("QuestBlue OpenAPI contract updated.")
    else:
        print("QuestBlue OpenAPI contract is current.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
