#!/usr/bin/env python3
"""Generate and validate QuestBlue operation coverage from source code."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPEC = ROOT / "spec" / "questblue-openapi-2.3.2.json"
DEFAULT_RESOURCES = ROOT / "src" / "questblue" / "_resources.py"
DEFAULT_CLIENT = ROOT / "src" / "questblue" / "_client.py"
DEFAULT_TESTS = ROOT / "tests"
DEFAULT_DOCS = (ROOT / "README.md", ROOT / "ROADMAP.md")
DEFAULT_OUTPUT = ROOT / "coverage" / "api-coverage.json"
HTTP_METHODS = frozenset(("DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT", "TRACE"))

Operation = Tuple[str, str]


def _literal_string(node: ast.AST) -> Optional[str]:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def documented_operations(spec: Mapping[str, Any]) -> Dict[Operation, Dict[str, Any]]:
    result: Dict[Operation, Dict[str, Any]] = {}
    for path, path_item in spec.get("paths", {}).items():
        if not isinstance(path_item, Mapping):
            continue
        for method, operation in path_item.items():
            normalized_method = str(method).upper()
            if normalized_method not in HTTP_METHODS or not isinstance(operation, Mapping):
                continue
            result[(normalized_method, str(path))] = dict(operation)
    return result


def resource_attribute_map(tree: ast.Module) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not (
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "client"
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
        ):
            continue
        result[node.value.func.id] = target.attr
    return result


def sdk_operations(resources_path: Path) -> Dict[Operation, Dict[str, str]]:
    tree = ast.parse(resources_path.read_text(encoding="utf-8"), filename=str(resources_path))
    attributes = resource_attribute_map(tree)
    result: Dict[Operation, Dict[str, str]] = {}
    for class_node in (node for node in tree.body if isinstance(node, ast.ClassDef)):
        resource_name = attributes.get(class_node.name)
        if resource_name is None:
            continue
        for function in (
            node
            for node in class_node.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ):
            for call in (node for node in ast.walk(function) if isinstance(node, ast.Call)):
                if not (
                    isinstance(call.func, ast.Attribute)
                    and call.func.attr == "_request"
                    and len(call.args) >= 2
                ):
                    continue
                method = _literal_string(call.args[0])
                path = _literal_string(call.args[1])
                if method in HTTP_METHODS and path is not None:
                    result[(method, path)] = {
                        "resource": resource_name,
                        "method": function.name,
                    }
    return result


def _attribute_chain(node: ast.AST) -> list[str]:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return list(reversed(parts))


def tested_methods(test_dir: Path) -> Set[Tuple[str, str]]:
    result: Set[Tuple[str, str]] = set()
    for path in sorted(test_dir.glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for call in (node for node in ast.walk(tree) if isinstance(node, ast.Call)):
            chain = _attribute_chain(call.func)
            if len(chain) >= 3:
                result.add((chain[-2], chain[-1]))
    return result


def documented_methods(doc_paths: Iterable[Path]) -> Set[Tuple[str, str]]:
    text = "\n".join(path.read_text(encoding="utf-8") for path in doc_paths if path.exists())
    result: Set[Tuple[str, str]] = set()
    for match in re.finditer(r"\bqb\.([a-z_]+)\.([a-z_]+)\b", text):
        result.add((match.group(1), match.group(2)))
    return result


def sync_async_parity(client_path: Path) -> bool:
    tree = ast.parse(client_path.read_text(encoding="utf-8"), filename=str(client_path))
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
    for name in ("QuestBlue", "AsyncQuestBlue"):
        class_node = classes.get(name)
        if class_node is None:
            return False
        if not any(
            isinstance(call.func, ast.Name) and call.func.id == "install_resources"
            for call in (node for node in ast.walk(class_node) if isinstance(node, ast.Call))
        ):
            return False
    return True


def build_report(
    *,
    spec_path: Path,
    resources_path: Path,
    client_path: Path,
    tests_path: Path,
    doc_paths: Iterable[Path],
) -> Dict[str, Any]:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    expected = documented_operations(spec)
    implemented = sdk_operations(resources_path)
    tests = tested_methods(tests_path)
    docs = documented_methods(doc_paths)
    parity = sync_async_parity(client_path)
    missing = sorted(set(expected) - set(implemented))
    extra = sorted(set(implemented) - set(expected))
    entries = []
    for operation_key in sorted(expected, key=lambda value: (value[1], value[0])):
        method, path = operation_key
        upstream = expected[operation_key]
        sdk = implemented.get(operation_key)
        sdk_key = (sdk["resource"], sdk["method"]) if sdk else None
        entries.append(
            {
                "documented": sdk_key in docs if sdk_key else False,
                "method": method,
                "operation_id": upstream.get("operationId"),
                "path": path,
                "request_model": None,
                "response_model": None,
                "sdk_method": f"{sdk['resource']}.{sdk['method']}" if sdk else None,
                "sync_async": parity and sdk is not None,
                "unit_tested": sdk_key in tests if sdk_key else False,
            }
        )
    return {
        "api_version": spec.get("info", {}).get("version"),
        "generated_from": str(spec_path.relative_to(ROOT)),
        "operations": entries,
        "summary": {
            "documented_operations": len(expected),
            "extra_sdk_operations": len(extra),
            "mapped_operations": len(expected) - len(missing),
            "missing_sdk_operations": len(missing),
            "sync_async_parity": parity,
        },
        "unmapped": [{"method": method, "path": path} for method, path in missing],
        "undocumented_sdk_operations": [{"method": method, "path": path} for method, path in extra],
    }


def render(report: Mapping[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    result.add_argument("--resources", type=Path, default=DEFAULT_RESOURCES)
    result.add_argument("--client", type=Path, default=DEFAULT_CLIENT)
    result.add_argument("--tests", type=Path, default=DEFAULT_TESTS)
    result.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    result.add_argument("--check", action="store_true", help="Verify report and invariants")
    return result


def main(argv: Optional[list[str]] = None) -> int:
    args = parser().parse_args(argv)
    report = build_report(
        spec_path=args.spec,
        resources_path=args.resources,
        client_path=args.client,
        tests_path=args.tests,
        doc_paths=DEFAULT_DOCS,
    )
    output = render(report)
    summary = report["summary"]
    valid = (
        summary["missing_sdk_operations"] == 0
        and summary["extra_sdk_operations"] == 0
        and summary["sync_async_parity"]
    )
    if args.check:
        current = args.output.read_text(encoding="utf-8") if args.output.exists() else None
        if current != output:
            print(f"Coverage report is stale; run: python {Path(__file__).relative_to(ROOT)}")
            return 1
        if not valid:
            print("API coverage invariants failed", file=sys.stderr)
            return 1
        print(
            f"API coverage verified: {summary['mapped_operations']}/"
            f"{summary['documented_operations']} operations mapped; sync/async parity holds."
        )
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
