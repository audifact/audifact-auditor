# Code execution example (live Cloudflare)

Attested script bytes and digest checks for Audifact’s
[`code_execution`](https://audifact.io/docs/code-execution) convention example.

Each Cloudflare GET’s **raw response body** is hashed (`raw_response_sha256`).
Those digests are included in the result object (sorted by `call`), so they are
covered by `result_sha256`. The bodies themselves stay private on the ledger.

## Files

| File | Role |
|------|------|
| `cloudflare_live.py` | Current attested `SCRIPT` UTF-8 bytes (raw-response binding) |
| `cloudflare_live_v1.py` | Prior attested script (summary counts only; sha256 `3a925ca7…`) |
| `verify.py` | Recomputes and asserts `script_sha256` and `result_sha256` |

## Digests (current)

- **script_sha256** = SHA-256 of the UTF-8 bytes of `cloudflare_live.py`  
  → `7ff25ab44dbbe71a2b2bc2600041250ef292ab1c74daba54bd5c9bedeefd1da6`
- **result_sha256** = SHA-256 of UTF-8  
  `json.dumps(result, sort_keys=True, separators=(",", ":"))` (no trailing newline)  
  → `7a7f68196f834e6d6356221863a16a9aa2b8d0f75b2ccfb8a1590c47221d4d2b`

`verify.py` confirms the published result matches the receipt. Raw responses stay
private and are bound by their hashes inside `result.raw_response_sha256`.

## Verify (no credentials)

```bash
cd examples/code-execution
python3 verify.py
# ok 7ff25ab4… 7a7f6819…

sha256sum cloudflare_live.py
```

## Live proof pair (current success)

Direct HTTPS GETs (`runtime_provider=direct`), not Cloudflare Code Mode. Zone
id/name and raw response bodies are private; public proofs show hashes, status,
and timing only.

- Decision: https://audifact.io/e/8671a4c2af59939f7b21170aac74b952c1c740fccd2b04205585e7706cf83e40
- Outcome: https://audifact.io/e/dafd8e20cb01c33bb2b521083603876c5ffb1d00d00a7f98a33dcb286ec0def2

## Prior attempts

### Earlier success (v1 script, no raw-response binding)

- Decision: https://audifact.io/e/89ef64e20285314aa462a86087fdb79ae9d8d9225598627d9614f90c4aeee3a1
- Outcome: https://audifact.io/e/e30f062bceabf1dd6c8ea8427dfc8f11a55eec6a75b561efa6db867e5697c223
- Script file: `cloudflare_live_v1.py` (`3a925ca7…`)

### Failed attempts (`10003` entrypoint misses)

Logged as real failures (`outcome_value` 0.0). Each attempt used a different
`script_sha256` — the ledger shows the script changing between tries.

- https://audifact.io/e/40c727127d499f4e3d3fd8fbacfc8f2aac01caaf3feaf19d4071b41a48a93477
- https://audifact.io/e/19003d491286fe7827a9fdec73bb39608240bf606cf83a5dcb87c6236d5490a4

## Running the script (optional)

```bash
export CLOUDFLARE_API_TOKEN=…
export CLOUDFLARE_ZONE_ID=…
python3 cloudflare_live.py
```

Prints a JSON envelope `{"result":..., "raw_responses":...}`. Logging to
Audifact is a separate `log_decision` / `log_outcome` step (see
https://audifact.io/docs/code-execution).
