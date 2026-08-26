# Changelog

## 0.1.0

### Added

- Standalone public-ledger verifier (no Audifact server monorepo required).
- CLI: `audifact-auditor verify` and `audifact-auditor verify-snapshot`.
- Online signing-key fetch via `GET {base}/ledger/signing-keys`.
- Offline keys via `signing_keys.json`.
- Snapshot Ed25519 signature checks, chain continuity, manifest, OTS digest, optional Bitcoin height checks.
