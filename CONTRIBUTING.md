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
   pytest
   python -m build
   twine check dist/*
   ```

5. Open a pull request linked to the issue.
6. Obtain an approving review and passing CI before merge.

Never use a production credential for ordinary tests. Live contract tests must use the approved
sandbox/subaccount, redact sensitive content, and clearly separate billable or destructive actions.

