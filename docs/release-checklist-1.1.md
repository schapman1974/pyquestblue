# 1.1 release checklist

- [x] Preserve the complete public typed 1.0 API and all 103 pinned operations.
- [x] Add no-model-import sync/async quickstarts and recipes for every simple service and workflow.
- [x] Machine-check 67 simple helpers, six workflows, their typed mappings, and sync/async parity.
- [x] Pass strict typing, lint, formatting, compiled samples, strict docs, and at least 90% branch
  coverage locally.
- [x] Require Linux CPython 3.10–3.14 CI, macOS/Windows compatibility, dependency audit, and CodeQL.
- [x] Build reproducible wheel and source artifacts and validate them with Twine.
- [x] Document white-label policy, tenant, audit, queue, persistence, and responsibility boundaries.
- [ ] Publish the protected `v1.1.0` GitHub release from the green `main` commit.
- [ ] Verify artifact attestation, PyPI publication and clean install, and versioned documentation.

The final two items execute only after the release PR is merged: publishing the GitHub release
triggers the protected PyPI and versioned-documentation workflows.
