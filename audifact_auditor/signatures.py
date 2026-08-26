"""Ed25519 snapshot and anchor-export signature verification."""

from __future__ import annotations

import hashlib
import json

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from audifact_auditor.keys import find_signing_key


def compute_anchor_export_hash(anchor_data: dict) -> str:
    payload = {
        "version": anchor_data["version"],
        "snapshot_seq": anchor_data["snapshot_seq"],
        "anchors": anchor_data["anchors"],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_snapshot_signature(snapshot: dict, keys: list) -> str:
    """Verify snapshot_signature over ledger_hash. Returns signing key_id."""
    key_id = snapshot.get("snapshot_signing_key_id")
    if not key_id:
        raise Exception("snapshot missing snapshot_signing_key_id")

    key = find_signing_key(keys, key_id)

    if key.get("algorithm") != "ed25519":
        raise Exception(f"unsupported algorithm: {key.get('algorithm')}")

    # status intentionally ignored - historical snapshots remain valid after revocation.

    ledger_hash = snapshot.get("ledger_hash")
    signature_hex = snapshot.get("snapshot_signature")

    if not ledger_hash:
        raise Exception("snapshot missing ledger_hash")
    if not signature_hex:
        raise Exception("snapshot missing snapshot_signature")

    try:
        VerifyKey(bytes.fromhex(key["public_key"])).verify(
            ledger_hash.encode("utf-8"),
            bytes.fromhex(signature_hex),
        )
    except (ValueError, BadSignatureError) as e:
        raise Exception("snapshot signature invalid") from e

    return key_id


def verify_anchor_export_signature(anchor_doc: dict, keys: list) -> str:
    """Verify anchor export hash + signature. Returns signing key_id."""
    key_id = anchor_doc.get("signing_key_id")
    if not key_id:
        raise Exception("anchor export missing signing_key_id")

    key = find_signing_key(keys, key_id)

    if key.get("algorithm") != "ed25519":
        raise Exception(
            f"unsupported anchor export signature algorithm: {key.get('algorithm')}"
        )

    stored_hash = anchor_doc.get("anchor_export_hash")
    if not stored_hash:
        raise Exception("anchor export missing anchor_export_hash")

    expected_hash = compute_anchor_export_hash(anchor_doc)
    if expected_hash != stored_hash:
        raise Exception("anchor export hash mismatch")

    signature_hex = anchor_doc.get("signature")
    if not signature_hex:
        raise Exception("anchor export missing signature")

    try:
        VerifyKey(bytes.fromhex(key["public_key"])).verify(
            stored_hash.encode("utf-8"),
            bytes.fromhex(signature_hex),
        )
    except (ValueError, BadSignatureError) as e:
        raise Exception("anchor export signature invalid") from e

    return key_id
