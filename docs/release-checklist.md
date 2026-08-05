# 1.0 release checklist

- [x] Map all 103 pinned QuestBlue 2.3.2 operations to typed sync and async methods.
- [x] Pass lint, formatting, strict typing, unit tests, sanitized recorded contracts, documentation,
  90% branch coverage, reproducible builds, dependency audit, and CodeQL.
- [x] Test CPython 3.10–3.14 on Linux, macOS, and Windows.
- [x] Complete the migration guide, API reference, changelog, security review, and support policy.
- [x] Explicitly defer the approved live read-only suite until dedicated subaccount secrets are
  configured.

The live suite is deliberately opt-in. Missing credentials are a recorded deferral, not a simulated
pass; unit and sanitized recorded-contract suites remain mandatory.

- [x] Confirm the OpenAPI checksum has not drifted.
- [x] Run every required gate and merge the green `1.0.0` release PR.
- [ ] Publish the GitHub release from the protected `main` commit.
- [ ] Confirm protected-environment publication to PyPI, artifact attestations, release attachments,
  and a clean PyPI installation.
- [ ] Publish versioned documentation and close the 1.0 milestone.
