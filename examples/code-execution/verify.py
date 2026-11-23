#!/usr/bin/env python3
"""Recompute script_sha256 and result_sha256 for the live Cloudflare example.

No network, no secrets. Run from this directory:

  python3 verify.py

Expected digests match the public proof pages linked in README.md.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

EXPECTED_SCRIPT_SHA256 = (
    "3a925ca724b4a3c398fb49d78e92069a0458199fcff35feda02fec8775f1a7da"
)
EXPECTED_RESULT_SHA256 = (
    "9d3d17537dba554d367f0724ead85641960552380fbb343d2f4d3c3eba794ee6"
)

# Live outcome result object (canonical JSON hashed below).
RESULT = {
    "ddos_phase": "ddos_l7",
    "ddos_rule_count": 148,
    "source": "zone_managed_rulesets",
    "waf_phase": "http_request_firewall_managed",
    "waf_rule_count": 42,
}

HERE = Path(__file__).resolve().parent
SCRIPT_PATH = HERE / "cloudflare_live.py"


def main() -> None:
    script_bytes = SCRIPT_PATH.read_bytes()
    script_sha256 = hashlib.sha256(script_bytes).hexdigest()

    canonical = json.dumps(RESULT, sort_keys=True, separators=(",", ":"))
    result_sha256 = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    assert script_sha256 == EXPECTED_SCRIPT_SHA256, (
        f"script_sha256 mismatch: got {script_sha256}"
    )
    assert result_sha256 == EXPECTED_RESULT_SHA256, (
        f"result_sha256 mismatch: got {result_sha256}"
    )
    assert canonical == (
        '{"ddos_phase":"ddos_l7","ddos_rule_count":148,'
        '"source":"zone_managed_rulesets",'
        '"waf_phase":"http_request_firewall_managed","waf_rule_count":42}'
    )

    print("ok", script_sha256, result_sha256)


if __name__ == "__main__":
    main()
