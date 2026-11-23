import hashlib
import json
import os
import urllib.error
import urllib.request

ZONE_ID = os.environ["CLOUDFLARE_ZONE_ID"]
TOKEN = os.environ["CLOUDFLARE_API_TOKEN"]
BASE = "https://api.cloudflare.com/client/v4"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}
WANT_PHASES = ("ddos_l7", "http_request_firewall_managed")


def cf_get(call: str, path: str) -> dict:
    req = urllib.request.Request(f"{BASE}{path}", headers=HEADERS, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            http_status = resp.status
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        http_status = exc.code
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            payload = {
                "success": False,
                "errors": [{"message": raw[:300].decode("utf-8", errors="replace")}],
            }
        if exc.code in (401, 403):
            raise SystemExit(
                json.dumps(
                    {
                        "error": "auth_error",
                        "status": exc.code,
                        "call": call,
                        "path": path,
                        "errors": payload.get("errors"),
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
            ) from None
        raise SystemExit(
            json.dumps(
                {
                    "error": "http_error",
                    "status": exc.code,
                    "call": call,
                    "path": path,
                    "errors": payload.get("errors"),
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        ) from None

    sha = hashlib.sha256(raw).hexdigest()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(
            json.dumps(
                {
                    "error": "invalid_json_body",
                    "call": call,
                    "path": path,
                    "raw_response_sha256": sha,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        ) from None
    return {
        "call": call,
        "path": path,
        "http_status": http_status,
        "raw": raw,
        "raw_response_sha256": sha,
        "payload": payload,
    }


listed = cf_get("list_zone_rulesets", f"/zones/{ZONE_ID}/rulesets")
list_payload = listed["payload"]
if not list_payload.get("success"):
    raise SystemExit(
        json.dumps(
            {
                "error": "list_rulesets_failed",
                "errors": list_payload.get("errors"),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )

by_phase = {}
for item in list_payload.get("result") or []:
    phase = item.get("phase")
    if phase in WANT_PHASES and phase not in by_phase:
        by_phase[phase] = item

missing = [p for p in WANT_PHASES if p not in by_phase]
if missing:
    raise SystemExit(
        json.dumps(
            {
                "error": "managed_rulesets_missing",
                "missing_phases": missing,
                "listed_phases": sorted(
                    {
                        i.get("phase")
                        for i in (list_payload.get("result") or [])
                        if i.get("phase")
                    }
                ),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )

captured = [listed]
details = {}
for phase in sorted(WANT_PHASES):
    item = by_phase[phase]
    call = f"ruleset_{phase}"
    detail = cf_get(call, f"/zones/{ZONE_ID}/rulesets/{item['id']}")
    captured.append(detail)
    payload = detail["payload"]
    if not payload.get("success") or payload.get("result") is None:
        raise SystemExit(
            json.dumps(
                {
                    "error": "ruleset_fetch_failed",
                    "phase": phase,
                    "errors": payload.get("errors"),
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )
    details[phase] = payload["result"]

ddos = details["ddos_l7"]
waf = details["http_request_firewall_managed"]

# Sorted list of per-call body digests (bound into result_sha256).
raw_response_sha256 = sorted(
    (
        {"call": row["call"], "sha256": row["raw_response_sha256"]}
        for row in captured
    ),
    key=lambda item: item["call"],
)

result = {
    "ddos_phase": ddos.get("phase"),
    "ddos_rule_count": len(ddos.get("rules") or []),
    "waf_phase": waf.get("phase"),
    "waf_rule_count": len(waf.get("rules") or []),
    "source": "zone_managed_rulesets",
    "raw_response_sha256": raw_response_sha256,
}

raw_responses = [
    {
        "call": row["call"],
        "path": row["path"],
        "http_status": row["http_status"],
        "sha256": row["raw_response_sha256"],
        "body_utf8": row["raw"].decode("utf-8"),
    }
    for row in sorted(captured, key=lambda item: item["call"])
]

print(
    json.dumps(
        {"result": result, "raw_responses": raw_responses},
        sort_keys=True,
        separators=(",", ":"),
    )
)
