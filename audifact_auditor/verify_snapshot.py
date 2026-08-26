"""Verify a single public snapshot file."""

from __future__ import annotations

import json
from pathlib import Path

from audifact_auditor.keys import load_keys
from audifact_auditor.signatures import verify_snapshot_signature


def load_json(path: str | Path) -> dict:
    try:
        return json.loads(Path(path).read_text())
    except Exception as e:
        raise Exception(f"could not read {path}: {e}") from e


def verify_snapshot_file(snapshot_path: str | Path, keys_source: str) -> dict:
    """
    Verify one snapshot JSON against keys (URL base or keys file path).

    Returns summary dict on success; raises Exception on failure.
    """
    snapshot = load_json(snapshot_path)
    keys = load_keys(keys_source)
    key_id = verify_snapshot_signature(snapshot, keys)
    return {
        "snapshot_seq": snapshot.get("snapshot_seq"),
        "ledger_hash": snapshot.get("ledger_hash"),
        "signing_key": key_id,
        "status": "ok",
    }
