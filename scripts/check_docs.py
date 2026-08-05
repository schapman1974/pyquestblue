#!/usr/bin/env python3
"""Compile documentation samples and enforce public-operation reference coverage."""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
COVERAGE = ROOT / "coverage" / "api-coverage.json"
PYTHON_BLOCK = re.compile(r"```python\n(.*?)```", re.DOTALL)


def main() -> int:
    errors: list[str] = []
    snippets = 0
    for path in sorted(DOCS.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for index, source in enumerate(PYTHON_BLOCK.findall(text), start=1):
            snippets += 1
            try:
                compile(
                    source,
                    f"{path.relative_to(ROOT)}:python-block-{index}",
                    "exec",
                    flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
                )
            except SyntaxError as exc:
                errors.append(str(exc))
    report = json.loads(COVERAGE.read_text(encoding="utf-8"))
    undocumented = [
        operation["sdk_method"]
        for operation in report["operations"]
        if operation["sdk_method"] and not operation["documented"]
    ]
    if undocumented:
        errors.append("undocumented public operations: " + ", ".join(undocumented))
    if snippets == 0:
        errors.append("no Python documentation samples found")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Compiled {snippets} Python samples; all public operations are documented.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
