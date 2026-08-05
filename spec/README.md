# QuestBlue OpenAPI contract

This directory pins the upstream contract used to develop and test pyquestblue. Provenance and the
active file are recorded in [`metadata.json`](metadata.json). The upstream source is
`https://docs.questblue.com/openapispec.json`.

The JSON is normalized with recursively sorted object keys, two-space indentation, UTF-8 encoding,
and one trailing newline. This keeps updates reviewable and reproducible.

## Check for upstream drift

```bash
python scripts/update_openapi.py --check
```

The command exits successfully when the live contract matches the pinned copy. When it differs, it
prints a semantic JSON summary of API-version, operation, and schema changes and exits nonzero. A
scheduled GitHub workflow runs the same check weekly.

## Update the pinned contract

```bash
python scripts/update_openapi.py
python scripts/api_coverage.py
```

Review the normalized contract, semantic changes, metadata, and regenerated coverage report in the
same pull request. Old versioned contract files are intentionally retained for historical diffs.

Tests can pass a local JSON file through `--source`; they never require network access.
