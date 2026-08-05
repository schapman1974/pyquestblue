"""Export typed QuestBlue call history with only the Python standard library."""

import csv
from pathlib import Path
from typing import Any, Dict, Iterable

from questblue import (
    CallHistoryRequest,
    CallHistoryResponse,
    Period,
    QuestBlue,
    export_rows,
)


def write_csv(rows: Iterable[Dict[str, Any]], destination: Path) -> None:
    materialized = list(rows)
    fieldnames = sorted({key for row in materialized for key in row})
    with destination.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(materialized)


def export_current_month(client: QuestBlue, destination: Path) -> None:
    records = list(
        client.reports.iter_call_history(
            CallHistoryRequest(period=Period.THIS_MONTH, per_page=5000)
        )
    )
    # The same dictionaries can be passed to pandas.DataFrame when pandas is installed.
    write_csv(export_rows(CallHistoryResponse(data=records, total=len(records))), destination)
