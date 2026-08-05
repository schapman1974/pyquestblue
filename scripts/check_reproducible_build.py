"""Build the project twice and verify byte-for-byte reproducibility."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[1]


def _source_date_epoch() -> str:
    return subprocess.check_output(
        ["git", "log", "-1", "--pretty=%ct"], cwd=ROOT, text=True
    ).strip()


def _build(output: Path, epoch: str) -> Dict[str, str]:
    environment = {**os.environ, "SOURCE_DATE_EPOCH": epoch}
    subprocess.run(
        [sys.executable, "-m", "build", "--outdir", str(output)],
        cwd=ROOT,
        env=environment,
        check=True,
    )
    return {
        artifact.name: hashlib.sha256(artifact.read_bytes()).hexdigest()
        for artifact in sorted(output.iterdir())
        if artifact.is_file()
    }


def main() -> int:
    """Return nonzero when repeated builds do not produce identical artifacts."""
    epoch = _source_date_epoch()
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        first = _build(root / "first", epoch)
        second = _build(root / "second", epoch)
    if not first or first != second:
        print("Build artifacts are not reproducible", file=sys.stderr)
        print(f"first: {first}", file=sys.stderr)
        print(f"second: {second}", file=sys.stderr)
        return 1
    print(f"Verified {len(first)} reproducible artifacts at SOURCE_DATE_EPOCH={epoch}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
