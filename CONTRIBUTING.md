# Contributing

All development after the initial repository bootstrap happens through pull requests into `main`.
Direct pushes to `main` are protected.

## Workflow

1. Create or select a GitHub issue from the roadmap.
2. Create a focused branch such as `feat/qb-005-voice-dids`.
3. Add tests with the implementation and update user-facing documentation.
4. Run the local quality gate:

   ```bash
   python -m pip install -e '.[dev]'
   ruff check .
   ruff format --check .
   mypy
   python scripts/api_coverage.py --check
   pytest
   python -m build
   twine check dist/*
   ```

5. Open a pull request linked to the issue.
6. Obtain an approving review and passing CI before merge.

Never use a production credential for ordinary tests. Live contract tests must use the approved
sandbox/subaccount, redact sensitive content, and clearly separate billable or destructive actions.

## OpenAPI contract

The pinned upstream contract lives in [`spec/`](spec/). Check for upstream changes with
`python scripts/update_openapi.py --check`. When it changes, update it with
`python scripts/update_openapi.py`, regenerate `coverage/api-coverage.json`, and review the semantic
operation/schema diff as part of the pull request.

## Models and pagination

Public models inherit from `QuestBlueModel`, preserve unknown response fields, and use open enums
where QuestBlue may introduce values. Resource-specific models and pagination helpers follow the
design and test checklist in [`docs/modeling.md`](docs/modeling.md).

## HTTP transport

Read [`docs/transport.md`](docs/transport.md) before changing retries, error mapping, request
overrides, decoding, or telemetry. Mutating operations must remain single-attempt unless QuestBlue
publishes and we verify an idempotency guarantee.
