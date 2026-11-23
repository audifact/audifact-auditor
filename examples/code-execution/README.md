# Code execution example (live Cloudflare)

Attested script bytes and digest checks for Audifact’s
[`code_execution`](https://audifact.io/docs/code-execution) convention example.

## Files

| File | Role |
|------|------|
| `cloudflare_live.py` | Exact attested `SCRIPT` UTF-8 bytes (no secrets; token and zone from env) |
| `verify.py` | Recomputes and asserts `script_sha256` and `result_sha256` |

## Digests

- **script_sha256** = SHA-256 of the UTF-8 bytes of `cloudflare_live.py`  
  → `3a925ca724b4a3c398fb49d78e92069a0458199fcff35feda02fec8775f1a7da`
- **result_sha256** = SHA-256 of UTF-8  
  `json.dumps(result, sort_keys=True, separators=(",", ":"))` (no trailing newline)  
  → `9d3d17537dba554d367f0724ead85641960552380fbb343d2f4d3c3eba794ee6`

Canonical result JSON:

```text
{"ddos_phase":"ddos_l7","ddos_rule_count":148,"source":"zone_managed_rulesets","waf_phase":"http_request_firewall_managed","waf_rule_count":42}
```

## Verify (no credentials)

```bash
cd examples/code-execution
python3 verify.py
# ok 3a925ca7… 9d3d1753…

# Or:
sha256sum cloudflare_live.py
```

## Live proof pair (success)

First live Cloudflare test for `code_execution`. Direct HTTPS GETs
(`runtime_provider=direct`), not Cloudflare Code Mode. Zone id/name are
private on the receipt; public proofs show hashes, status, and timing only.

- Decision: https://audifact.io/e/89ef64e20285314aa462a86087fdb79ae9d8d9225598627d9614f90c4aeee3a1
- Outcome: https://audifact.io/e/e30f062bceabf1dd6c8ea8427dfc8f11a55eec6a75b561efa6db867e5697c223

## Failed attempts (ledger records misses)

Two earlier tries hit Cloudflare `10003` (no zone phase entrypoint) and were
logged as real failures (`outcome_value` 0.0, `status: error`). Each attempt
used a different `script_sha256` — the ledger shows the script changing between
tries, not only retries of the same bytes.

- https://audifact.io/e/40c727127d499f4e3d3fd8fbacfc8f2aac01caaf3feaf19d4071b41a48a93477
- https://audifact.io/e/19003d491286fe7827a9fdec73bb39608240bf606cf83a5dcb87c6236d5490a4

## Running the script (optional)

Requires a Cloudflare API token with read access to zone rulesets, plus the
zone id:

```bash
export CLOUDFLARE_API_TOKEN=…
export CLOUDFLARE_ZONE_ID=…
python3 cloudflare_live.py
```

This only prints the JSON result. Logging to Audifact is a separate
`log_decision` / `log_outcome` step (see https://audifact.io/docs/code-execution).
