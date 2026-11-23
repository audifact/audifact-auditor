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


def cf_get(path: str) -> dict:
    req = urllib.request.Request(f"{BASE}{path}", headers=HEADERS, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            return {"http_status": resp.status, "payload": payload}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"success": False, "errors": [{"message": raw[:300]}]}
        if exc.code in (401, 403):
            raise SystemExit(
                json.dumps(
                    {
                        "error": "auth_error",
                        "status": exc.code,
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
                    "path": path,
                    "errors": payload.get("errors"),
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        ) from None


listed = cf_get(f"/zones/{ZONE_ID}/rulesets")
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

details = {}
for phase, item in by_phase.items():
    detail = cf_get(f"/zones/{ZONE_ID}/rulesets/{item['id']}")
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
result = {
    "ddos_phase": ddos.get("phase"),
    "ddos_rule_count": len(ddos.get("rules") or []),
    "waf_phase": waf.get("phase"),
    "waf_rule_count": len(waf.get("rules") or []),
    "source": "zone_managed_rulesets",
}
print(json.dumps(result, sort_keys=True, separators=(",", ":")))
