"""OpenTimestamps helpers (optional Bitcoin height from proof tree)."""

from __future__ import annotations

from pathlib import Path

import opentimestamps.core.serialize as ots_serialize
from opentimestamps.core.timestamp import DetachedTimestampFile


def load_ots_digest(proof_file: Path) -> str:
    try:
        ctx = ots_serialize.BytesDeserializationContext(proof_file.read_bytes())
        detached = DetachedTimestampFile.deserialize(ctx)
        return detached.file_digest.hex()
    except Exception as e:
        raise Exception(f"could not parse OTS proof {proof_file}: {e}") from e


def bitcoin_timestamp_status(proof_path: Path) -> dict:
    """Extract BTC block height from OTS attestation tree, if present."""
    try:
        ots_data = proof_path.read_bytes()
        ctx = ots_serialize.BytesDeserializationContext(ots_data)
        detached = DetachedTimestampFile.deserialize(ctx)

        def find_bitcoin_block(ts):
            for attestation in ts.attestations:
                height = getattr(attestation, "height", None)
                if isinstance(height, int) and height > 0:
                    return height
            for _, child in ts.ops.items():
                result = find_bitcoin_block(child)
                if result:
                    return result
            return None

        btc_block = find_bitcoin_block(detached.timestamp)
        status = "bitcoin_anchored" if btc_block else "calendar_anchored"
        return {
            "status": status,
            "bitcoin_block": btc_block,
        }
    except Exception as e:
        raise Exception(f"could not read OTS status for {proof_path}: {e}") from e
