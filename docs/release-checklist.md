# 1.0 release checklist

## Release candidate

- [x] Map all 103 pinned QuestBlue 2.3.2 operations to typed sync and async methods.
- [ ] Pass lint, formatting, strict typing, unit tests, sanitized recorded contracts, documentation,
  90% branch coverage, reproducible builds, dependency audit, and CodeQL.
- [ ] Test CPython 3.10–3.14 on Linux, macOS, and Windows.
- [x] Complete the migration guide, API reference, changelog, security review, and support policy.
- [ ] Publish `1.0.0rc1` from the protected TestPyPI environment with a GitHub build attestation.
- [ ] Verify a clean installation from TestPyPI.
- [ ] Run the approved live read-only suite when the dedicated subaccount secrets are configured.

The live suite is deliberately opt-in. Missing credentials are a recorded deferral, not a simulated
pass; unit and sanitized recorded-contract suites remain mandatory.

## Final release

- [ ] Resolve release-candidate findings and confirm the OpenAPI checksum has not drifted.
- [ ] Change the version to `1.0.0`, run every required gate, and merge the green release PR.
- [ ] Publish the GitHub release from the protected `main` commit.
- [ ] Confirm OIDC publication to PyPI, artifact attestations, release attachments, and a clean PyPI
  installation.
- [ ] Publish versioned documentation and close the 1.0 milestone.
