# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/) and Semantic Versioning.

## [1.0.0] - 2026-08-05

### Added

- Typed synchronous and asynchronous coverage for all 103 operations in the pinned QuestBlue 2.3.2
  contract.
- Account, DID, international DID, SIP trunk, SMS/MMS, 10DLC, Fax.Pro, iFax Enterprise, report,
  number-portability, and VoIP-server resources.
- Typed transport errors, safe-read retry behavior, pagination, webhook parsing, framework recipes,
  contract fixtures, API coverage enforcement, and white-label architecture guidance.
- Cross-platform CI, CodeQL, dependency auditing, reproducible-build checks, protected package-index
  publishing, and GitHub artifact attestations.

### Changed

- The supported interpreter range is CPython 3.10 through 3.14. Python 3.9 is end-of-life and its
  dependency resolution prevented the release toolchain from receiving current security fixes.

### Known upstream limitations

- QuestBlue does not document a sandbox or webhook authentication, retry, ordering, and unique-ID
  guarantees. Live tests therefore require explicit approval and a dedicated provider subaccount.

[1.0.0]: https://github.com/schapman1974/pyquestblue/releases/tag/v1.0.0
