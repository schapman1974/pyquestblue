# Compatibility, releases, and maintenance

## Versioning and public API

pyquestblue follows Semantic Versioning. Version 1.0 freezes the documented public surface:

- patch releases contain compatible bug, security, documentation, and typing fixes;
- minor releases add compatible features and may introduce deprecations;
- major releases may remove deprecated APIs or otherwise break compatibility.

The public API consists of documented names exported by `questblue`, documented resource methods,
exceptions, models, and optional integration helpers. Private modules and names beginning with an
underscore are not compatibility promises. Upstream QuestBlue additions may appear as preserved
extra model fields or open-enum values without requiring an SDK release.

## Deprecation policy

Deprecations emit `DeprecationWarning`, appear in release notes and migration docs, and include the
replacement. After 1.0, a deprecated API remains available for at least one minor release and three
months before removal in a major release. Security, privacy, provider removal, or provably unsafe
behavior may require faster removal; the release notes will explain the exception.

## Release process

Every release is made from a reviewed, green commit on `main`:

1. Confirm the pinned OpenAPI contract and 100% operation map are current.
2. Run linting, typing, documentation compilation, at least 90% branch coverage, all supported
   Python versions, cross-platform compatibility, dependency audit, and CodeQL.
3. Build twice with a fixed `SOURCE_DATE_EPOCH` and compare artifact digests.
4. Update the version, changelog, and migration guidance; publish a signed GitHub release tag.
5. The protected `pypi` environment sends the artifacts to PyPI using its encrypted, scoped API
   token. GitHub OIDC records build-provenance attestations, and the versioned documentation workflow
   publishes the matching docs.
6. Verify installation from PyPI and the GitHub attestation, then announce the release.

A failed or partially published release is never overwritten because package indexes are immutable;
publish a new patch version after correcting the problem.

## Platform support

CPython 3.10 through 3.14 are tested. Linux runs the complete quality and packaging gate; macOS and
Windows run the full behavioral suite on every supported interpreter. Other Python implementations
and operating systems may work but are not release blockers until added to the matrix.

See
[SUPPORT.md](https://github.com/schapman1974/pyquestblue/blob/main/SUPPORT.md)
for issue support and
[SECURITY.md](https://github.com/schapman1974/pyquestblue/blob/main/SECURITY.md)
for private vulnerability reporting and response targets.
