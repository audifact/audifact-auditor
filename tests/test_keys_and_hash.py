"""Unit tests with no live network or monorepo app imports."""

from __future__ import annotations

import hashlib
import json

from audifact_auditor.signatures import compute_anchor_export_hash
from audifact_auditor.keys import find_signing_key, load_signing_keys_file


def test_find_signing_key():
    keys = [{"key_id": "a", "public_key": "aa"}, {"key_id": "b", "public_key": "bb"}]
    assert find_signing_key(keys, "b")["public_key"] == "bb"


def test_find_signing_key_missing():
    try:
        find_signing_key([], "x")
        assert False, "expected raise"
    except Exception as e:
        assert "not found" in str(e)


def test_compute_anchor_export_hash_stable():
    data = {
        "version": 1,
        "snapshot_seq": 2,
        "anchors": [
            {
                "anchor_type": "calendar",
                "anchor_status": "anchored",
                "proof_path": "ots/000000000002.ots",
                "btc_block_height": None,
                "btc_block_hash": None,
                "created_at": "2026-01-01T00:00:00+00:00",
            }
        ],
    }
    h1 = compute_anchor_export_hash(data)
    h2 = compute_anchor_export_hash(data)
    assert h1 == h2
    assert len(h1) == 64
    # known canonical form
    payload = {
        "version": 1,
        "snapshot_seq": 2,
        "anchors": data["anchors"],
    }
    expected = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert h1 == expected


def test_load_signing_keys_file(tmp_path):
    p = tmp_path / "keys.json"
    p.write_text(json.dumps({"keys": [{"key_id": "k1", "algorithm": "ed25519"}]}))
    keys = load_signing_keys_file(p)
    assert keys[0]["key_id"] == "k1"


def test_no_app_imports():
    """Package modules must not import monorepo app.*"""
    import audifact_auditor
    import audifact_auditor.cli as cli
    import audifact_auditor.keys as keys
    import audifact_auditor.ots as ots
    import audifact_auditor.signatures as signatures
    import audifact_auditor.verify_ledger as verify_ledger
    import audifact_auditor.verify_snapshot as verify_snapshot

    for mod in (audifact_auditor, cli, keys, ots, signatures, verify_ledger, verify_snapshot):
        for name in dir(mod):
            pass  # load only
        src = getattr(mod, "__file__", "") or ""
        text = open(src).read() if src.endswith(".py") else ""
        assert "from app." not in text
        assert "import app" not in text
