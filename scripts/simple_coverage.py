#!/usr/bin/env python3
"""Generate and verify simple-facade mappings and sync/async parity."""

from __future__ import annotations

import argparse
import ast
import inspect
import json
import sys
import textwrap
from pathlib import Path
from typing import Any

from questblue.simple._provision import PROVISION_SERVICE_TYPES
from questblue.simple._read import READ_SERVICE_TYPES
from questblue.simple._workflows import AsyncWorkflows, Workflows

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "coverage" / "simple-api.json"
API_COVERAGE = ROOT / "coverage" / "api-coverage.json"
RESOURCE_NAMES = {
    "international_numbers": "international_dids",
    "messages": "sms",
    "numbers": "dids",
    "porting": "lnp",
    "voice": "sip_trunks",
}
TYPED_ALIASES = {
    "dids.pages": "dids.list",
    "international_dids.pages": "international_dids.list",
    "reports.iter_call_history": "reports.call_history",
    "reports.iter_fax_history": "reports.fax_history",
}


def public_methods(cls: type[Any]) -> dict[str, Any]:
    return {
        name: method
        for name, method in inspect.getmembers(cls)
        if not name.startswith("_")
        and (inspect.isfunction(method) or inspect.iscoroutinefunction(method))
    }


def raw_calls(method: Any) -> list[str]:
    try:
        tree = ast.parse(textwrap.dedent(inspect.getsource(method)))
    except (OSError, TypeError):
        return []
    calls = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        value = node.func.value
        if (
            isinstance(value, ast.Attribute)
            and isinstance(value.value, ast.Name)
            and value.value.id == "self"
            and value.attr == "raw"
        ):
            calls.add(node.func.attr)
    return sorted(calls)


def entries() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    result = []
    errors = []
    registries = dict(READ_SERVICE_TYPES)
    registries.update(PROVISION_SERVICE_TYPES)
    for service, (sync_class, async_class) in sorted(registries.items()):
        sync = public_methods(sync_class)
        async_ = public_methods(async_class)
        if set(sync) != set(async_):
            errors.append(
                f"{service} parity differs: sync-only={sorted(set(sync) - set(async_))}, "
                f"async-only={sorted(set(async_) - set(sync))}"
            )
        for name in sorted(set(sync) | set(async_)):
            result.append(
                {
                    "async": name in async_,
                    "simple_method": f"{service}.{name}",
                    "sync": name in sync,
                    "typed_operations": [
                        TYPED_ALIASES.get(
                            f"{RESOURCE_NAMES.get(service, service)}.{call}",
                            f"{RESOURCE_NAMES.get(service, service)}.{call}",
                        )
                        for call in raw_calls(sync.get(name))
                    ],
                }
            )
    sync_workflows = public_methods(Workflows)
    async_workflows = public_methods(AsyncWorkflows)
    if set(sync_workflows) != set(async_workflows):
        errors.append(
            "workflow parity differs: "
            f"sync-only={sorted(set(sync_workflows) - set(async_workflows))}, "
            f"async-only={sorted(set(async_workflows) - set(sync_workflows))}"
        )
    workflows = [
        {
            "async": name in async_workflows,
            "simple_method": f"workflows.{name}",
            "sync": name in sync_workflows,
        }
        for name in sorted(set(sync_workflows) | set(async_workflows))
    ]
    return result, workflows, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    helpers, workflows, errors = entries()
    output = (
        json.dumps(
            {
                "entries": helpers,
                "summary": {"sync_async_parity": not errors},
                "workflows": workflows,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != output:
            errors.append("simple coverage report is stale; run python scripts/simple_coverage.py")
        covered = {
            item["sdk_method"]
            for item in json.loads(API_COVERAGE.read_text(encoding="utf-8"))["operations"]
        }
        unknown = sorted(
            operation
            for entry in helpers
            for operation in entry["typed_operations"]
            if operation not in covered
        )
        if unknown:
            errors.append(f"unknown typed mappings: {unknown}")
        if errors:
            print("\n".join(errors), file=sys.stderr)
            return 1
        print(
            f"Simple API coverage verified: {len(helpers)} helpers and {len(workflows)} workflows; "
            "sync/async parity holds."
        )
        return 0
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    OUTPUT.write_text(output, encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
