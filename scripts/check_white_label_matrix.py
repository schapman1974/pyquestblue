"""Validate the evidence and provenance of the white-label capability matrix."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Mapping, Set, Tuple, cast

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "contracts" / "white-label-capabilities.json"
METADATA_PATH = ROOT / "spec" / "metadata.json"
METHODS = frozenset(("delete", "get", "head", "options", "patch", "post", "put", "trace"))
VALID_STATUSES = frozenset(("supported", "partial", "absent", "unknown"))


def _load(path: Path) -> Dict[str, Any]:
    return cast(Dict[str, Any], json.loads(path.read_text()))


def _operations(spec: Mapping[str, Any]) -> Set[Tuple[str, str]]:
    result: Set[Tuple[str, str]] = set()
    for path, item in spec["paths"].items():
        for method in item:
            if method in METHODS:
                result.add((method.upper(), path))
    return result


def validate() -> list[str]:
    """Return every matrix validation error."""
    errors: list[str] = []
    matrix = _load(MATRIX_PATH)
    metadata = _load(METADATA_PATH)
    spec_path = ROOT / "spec" / metadata["spec_file"]
    spec = _load(spec_path)
    source = matrix.get("source", {})
    normalized = json.dumps(spec, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    operations = _operations(spec)
    for key, actual in (
        ("api_version", metadata["api_version"]),
        ("sha256", digest),
        ("operation_count", len(operations)),
        ("url", metadata["source"]),
    ):
        if source.get(key) != actual:
            errors.append(f"source.{key} does not match pinned contract provenance")

    capabilities = matrix.get("capabilities", [])
    ids = {item.get("id") for item in capabilities}
    if len(ids) != len(capabilities) or None in ids:
        errors.append("capability IDs must be present and unique")
    for capability in capabilities:
        if capability.get("status") not in VALID_STATUSES:
            errors.append(f"{capability.get('id')}: invalid status")
        if not capability.get("summary") or not capability.get("evidence"):
            errors.append(f"{capability.get('id')}: summary and evidence are required")
        for evidence in capability.get("evidence", []):
            pieces = evidence.split(" ", 1)
            if len(pieces) == 2 and pieces[0].lower() in METHODS:
                operation = (pieces[0], pieces[1])
                if operation not in operations:
                    errors.append(f"{capability.get('id')}: unknown operation {evidence}")

    question_ids: set[str] = set()
    for question in matrix.get("provider_questions", []):
        question_id = question.get("id")
        if not question_id or question_id in question_ids:
            errors.append("provider question IDs must be present and unique")
        question_ids.add(question_id)
        if question.get("capability") not in ids or not question.get("question"):
            errors.append(f"{question_id}: invalid capability or empty question")
    return errors


def main() -> int:
    """Validate the matrix for CI."""
    errors = validate()
    if errors:
        for error in errors:
            print(error)
        return 1
    matrix = _load(MATRIX_PATH)
    print(
        f"Verified {len(matrix['capabilities'])} white-label capabilities and "
        f"{len(matrix['provider_questions'])} provider questions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
