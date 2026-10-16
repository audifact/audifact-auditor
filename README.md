# audifact-auditor

Independent verification of [Audifact](https://audifact.io) **public ledger** artifacts:

- Signed snapshot chain (`public_ledger/00000000000N.json`)
- Snapshot Ed25519 signatures
- Anchor export signatures + OpenTimestamps (OTS) digests
- `manifest.json` tip consistency

This package does **not** depend on the private Audifact server codebase.  
It is the verify-side counterpart to [audifact-sdk](https://github.com/audifact/audifact-sdk) (which **writes** events).

**Public repo:** https://github.com/audifact/audifact-auditor  
**Site docs:** [Verify OTS anchors](https://audifact.io/docs/verify-ots) (includes auditor CLI) · [FAQ](https://audifact.io/faq)

## Requirements

- Python 3.10+
- Network access to `https://audifact.io` (or a local `public_ledger/` copy)

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "git+https://github.com/audifact/audifact-auditor.git@v0.1.1"
```

Local (monorepo nested checkout):

```bash
cd auditor
pip install -e .
```

## Quick start

```bash
# 1) Download the published public ledger (snapshots + anchors + OTS proofs)
audifact-auditor fetch ./public_ledger

# Smoke-test with a short chain (optional):
# audifact-auditor fetch ./public_ledger --max-seq 5

# 2) Verify the full tree (keys fetched from the site)
audifact-auditor verify ./public_ledger --base-url https://audifact.io

# Offline keys (also included in the fetch)
audifact-auditor verify ./public_ledger --keys ./public_ledger/signing_keys.json

# Single snapshot
audifact-auditor verify-snapshot ./public_ledger/000000000002.json \
  --base-url https://audifact.io
```

Published files are also browsable at https://audifact.io/public_ledger/ (e.g. `manifest.json`, `000000000649.json`).

Exit code `0` = verified. Non-zero = failure (message on stderr/stdout).

## What is checked

1. Snapshot files present, sequential `snapshot_seq`, filename `NNNNNNNNNNNN.json`
2. `prev_snapshot_hash` chain and `ledger_hash` present
3. Ed25519 signature over `ledger_hash` with published signing key
4. If `anchors/NNNNNNNNNNNN.json` exists: export signature + OTS file digests match `sha256(ledger_hash_bytes)`
5. Bitcoin anchors (if present): height in export matches OTS tree
6. `manifest.json` tip matches latest snapshot

## Not in scope (v0.1)

- Recomputing per-event hash chains from the private DB
- Ingest / API keys (use **audifact-sdk** for writes)

## License

MIT
