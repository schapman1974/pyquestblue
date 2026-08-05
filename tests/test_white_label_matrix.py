from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import check_white_label_matrix


def test_white_label_matrix_matches_pinned_contract(capsys: pytest.CaptureFixture[str]) -> None:
    assert check_white_label_matrix.main() == 0
    assert "Verified 15 white-label capabilities" in capsys.readouterr().out


def test_white_label_matrix_validator_reports_bad_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    matrix = json.loads(check_white_label_matrix.MATRIX_PATH.read_text())
    matrix["source"]["operation_count"] = 999
    matrix["capabilities"][0]["status"] = "maybe"
    matrix["capabilities"][0]["summary"] = ""
    matrix["capabilities"][0]["evidence"] = ["GET /not-an-operation"]
    matrix["capabilities"][1]["id"] = matrix["capabilities"][0]["id"]
    matrix["provider_questions"][1]["id"] = matrix["provider_questions"][0]["id"]
    matrix["provider_questions"][1]["capability"] = "missing"
    matrix["provider_questions"][1]["question"] = ""
    invalid = tmp_path / "matrix.json"
    invalid.write_text(json.dumps(matrix))
    monkeypatch.setattr(check_white_label_matrix, "MATRIX_PATH", invalid)

    errors = check_white_label_matrix.validate()

    assert "source.operation_count does not match pinned contract provenance" in errors
    assert "capability IDs must be present and unique" in errors
    assert "account_hierarchy: invalid status" in errors
    assert "account_hierarchy: summary and evidence are required" in errors
    assert "account_hierarchy: unknown operation GET /not-an-operation" in errors
    assert "provider question IDs must be present and unique" in errors
    assert "Q1: invalid capability or empty question" in errors
