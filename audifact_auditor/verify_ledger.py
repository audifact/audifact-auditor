"""Verify a full public_ledger directory (chain + anchors + manifest)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from audifact_auditor.keys import load_keys
from audifact_auditor.ots import bitcoin_timestamp_status, load_ots_digest
from audifact_auditor.signatures import (
    verify_anchor_export_signature,
    verify_snapshot_signature,
)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception as e:
        raise Exception(f"could not read {path}: {e}") from e


def resolve_public_proof_file(ledger_dir: Path, proof_path: str) -> Path:
    if not proof_path:
        raise Exception("anchor missing proof_path")
    proof_name = Path(proof_path).name
    proof_file = ledger_dir / "ots" / proof_name
    if not proof_file.exists():
        raise Exception(f"missing proof file {proof_file}")
    return proof_file


def verify_public_ledger(ledger_dir: str | Path, keys_source: str) -> dict:
    """
    Verify public_ledger artifacts.

    keys_source: http(s) base URL or path to signing_keys.json
    Returns a summary dict. Raises Exception on first failure.
    """
    ledger_dir = Path(ledger_dir)
    keys = load_keys(keys_source)

    manifest_path = ledger_dir / "manifest.json"
    if not manifest_path.exists():
        raise Exception("manifest.json missing")
    manifest = load_json(manifest_path)

    anchor_dir = ledger_dir / "anchors"
    files = sorted(p for p in ledger_dir.glob("*.json") if p.stem.isdigit())
    if not files:
        raise Exception(f"no snapshot files found in {ledger_dir}")

    prev_ledger_hash = None
    expected_seq = 1
    checked = 0
    latest_snapshot_file = None

    anchor_files_checked = 0
    anchors_checked = 0
    anchor_proofs_checked = 0
    anchor_digest_verified = 0
    calendar_anchors_found = 0
    bitcoin_anchors_found = 0
    btc_anchors_verified = 0

    for path in files:
        snap = load_json(path)
        seq = snap.get("snapshot_seq")

        if seq != expected_seq:
            raise Exception(
                f"snapshot sequence mismatch in {path.name}: "
                f"expected={expected_seq} found={seq}"
            )

        expected_filename = f"{seq:012d}.json"
        if path.name != expected_filename:
            raise Exception(
                f"snapshot filename mismatch: "
                f"expected={expected_filename} found={path.name}"
            )

        if snap.get("prev_snapshot_hash") != prev_ledger_hash:
            raise Exception(f"prev_snapshot_hash mismatch at snapshot_seq={seq}")

        ledger_hash = snap.get("ledger_hash")
        if not ledger_hash:
            raise Exception(f"missing ledger_hash at snapshot_seq={seq}")

        verify_snapshot_signature(snap, keys)

        anchor_file = anchor_dir / f"{seq:012d}.json"
        if anchor_file.exists():
            anchor_doc = load_json(anchor_file)
            verify_anchor_export_signature(anchor_doc, keys)

            if anchor_doc.get("snapshot_seq") != seq:
                raise Exception(f"anchor snapshot_seq mismatch for snapshot {seq}")

            anchors = anchor_doc.get("anchors", [])
            if not isinstance(anchors, list):
                raise Exception(f"anchors must be a list for snapshot {seq}")

            for anchor in anchors:
                anchor_type = anchor.get("anchor_type")
                proof_path = anchor.get("proof_path")
                proof_file = resolve_public_proof_file(ledger_dir, proof_path)
                anchor_proofs_checked += 1

                actual_digest = load_ots_digest(proof_file)
                expected_digest = hashlib.sha256(
                    bytes.fromhex(ledger_hash)
                ).hexdigest()

                if actual_digest != expected_digest:
                    raise Exception(
                        f"OTS digest mismatch snapshot_seq={seq} "
                        f"expected={expected_digest} actual={actual_digest}"
                    )
                anchor_digest_verified += 1

                if anchor_type == "calendar":
                    calendar_anchors_found += 1
                elif anchor_type == "bitcoin":
                    bitcoin_anchors_found += 1
                    btc_height = anchor.get("btc_block_height")
                    if not isinstance(btc_height, int) or btc_height <= 0:
                        raise Exception(
                            f"invalid bitcoin block height for snapshot {seq}"
                        )
                    proof_status = bitcoin_timestamp_status(proof_file)
                    proof_height = proof_status.get("bitcoin_block")
                    if proof_height != btc_height:
                        raise Exception(
                            f"bitcoin anchor proof mismatch snapshot_seq={seq} "
                            f"export_height={btc_height} proof_height={proof_height}"
                        )
                    btc_anchors_verified += 1
                else:
                    raise Exception(
                        f"unknown anchor_type {anchor_type} for snapshot {seq}"
                    )
                anchors_checked += 1
            anchor_files_checked += 1

        prev_ledger_hash = ledger_hash
        latest_snapshot_file = expected_filename
        expected_seq += 1
        checked += 1

    latest_snapshot_seq = expected_seq - 1
    latest_ledger_hash = prev_ledger_hash

    if manifest.get("latest_snapshot_seq") != latest_snapshot_seq:
        raise Exception(
            "manifest latest_snapshot_seq mismatch "
            f"(manifest={manifest.get('latest_snapshot_seq')} "
            f"actual={latest_snapshot_seq})"
        )
    if manifest.get("latest_snapshot_file") != latest_snapshot_file:
        raise Exception(
            "manifest latest_snapshot_file mismatch "
            f"(manifest={manifest.get('latest_snapshot_file')} "
            f"actual={latest_snapshot_file})"
        )
    if manifest.get("latest_ledger_hash") != latest_ledger_hash:
        raise Exception("manifest latest_ledger_hash mismatch")

    return {
        "status": "ok",
        "snapshots_checked": checked,
        "latest_snapshot_seq": latest_snapshot_seq,
        "latest_ledger_hash": latest_ledger_hash,
        "anchor_exports_checked": anchor_files_checked,
        "anchors_checked": anchors_checked,
        "anchor_proofs_checked": anchor_proofs_checked,
        "anchor_digest_verified": anchor_digest_verified,
        "calendar_anchors": calendar_anchors_found,
        "bitcoin_anchors": bitcoin_anchors_found,
        "btc_anchors_verified": btc_anchors_verified,
    }
