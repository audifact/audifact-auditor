#!/usr/bin/env python3
"""Recompute script_sha256 and result_sha256 for the live Cloudflare example.

No network, no secrets. Run from this directory:

  python3 verify.py

verify.py confirms the published result object matches the receipt's
result_sha256. Raw Cloudflare response bodies stay private on the ledger and
are bound by the per-call digests inside result.raw_response_sha256.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

EXPECTED_SCRIPT_SHA256 = (
    "7ff25ab44dbbe71a2b2bc2600041250ef292ab1c74daba54bd5c9bedeefd1da6"
)
EXPECTED_RESULT_SHA256 = (
    "7a7f68196f834e6d6356221863a16a9aa2b8d0f75b2ccfb8a1590c47221d4d2b"
)

# Live outcome result object (canonical JSON hashed below).
# Includes sorted raw_response_sha256 entries that bind private response bodies.
RESULT = {
    "ddos_phase": "ddos_l7",
    "ddos_rule_count": 148,
    "raw_response_sha256": [
        {
            "call": "list_zone_rulesets",
            "sha256": "e110c26b7f095715623cbaba02dff325f55756a5486a7402672445e62fc41fff",
        },
        {
            "call": "ruleset_ddos_l7",
            "sha256": "503ad6d235041e1d535ee783519219acffcdbec6df3c58e5fbd9d4d31da2c509",
        },
        {
            "call": "ruleset_http_request_firewall_managed",
            "sha256": "36ddb91694ef0550a69df0699ead85013a5b5622911ecbc51622625fc25ecd6c",
        },
    ],
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

    print("ok", script_sha256, result_sha256)


if __name__ == "__main__":
    main()
