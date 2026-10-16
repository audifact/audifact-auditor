"""Download a public_ledger tree from a hosted Audifact site."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _get_bytes(url: str, timeout: float = 60.0) -> bytes:
    req = Request(url, headers={"User-Agent": "audifact-auditor"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _get_json(url: str) -> dict:
    return json.loads(_get_bytes(url).decode())


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def fetch_public_ledger(
    dest: str | Path,
    *,
    base_url: str = "https://audifact.io",
    max_seq: int | None = None,
) -> dict:
    """
    Fetch snapshots (+ anchors/ots when present) into dest.

    Expects the site to serve files under ``{base_url}/public_ledger/``.
    Returns a small summary dict.
    """
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    root = base_url.rstrip("/") + "/public_ledger"

    manifest = _get_json(f"{root}/manifest.json")

    try:
        keys_bytes = _get_bytes(f"{root}/signing_keys.json")
        _write(dest / "signing_keys.json", keys_bytes)
    except (HTTPError, URLError):
        # Online verify can still use GET /ledger/signing-keys
        pass

    tip = int(manifest.get("latest_snapshot_seq") or 0)
    if tip < 1:
        raise Exception("manifest.json missing latest_snapshot_seq")
    latest = tip
    if max_seq is not None:
        latest = min(tip, int(max_seq))

    downloaded = 0
    anchors = 0
    ots = 0
    last_ledger_hash = None
    for seq in range(1, latest + 1):
        name = f"{seq:012d}.json"
        data = _get_bytes(f"{root}/{name}")
        _write(dest / name, data)
        downloaded += 1
        try:
            snap = json.loads(data.decode())
            last_ledger_hash = snap.get("ledger_hash") or last_ledger_hash
        except json.JSONDecodeError:
            pass

        try:
            a = _get_bytes(f"{root}/anchors/{name}")
            _write(dest / "anchors" / name, a)
            anchors += 1
        except HTTPError as e:
            if e.code != 404:
                raise

        try:
            o = _get_bytes(f"{root}/ots/{seq:012d}.ots")
            _write(dest / "ots" / f"{seq:012d}.ots", o)
            ots += 1
        except HTTPError as e:
            if e.code != 404:
                raise

    # When --max-seq truncates, rewrite tip fields so local verify succeeds.
    if latest < tip:
        manifest = dict(manifest)
        manifest["latest_snapshot_seq"] = latest
        manifest["latest_snapshot_file"] = f"{latest:012d}.json"
        if last_ledger_hash:
            manifest["latest_ledger_hash"] = last_ledger_hash
        manifest["truncated_fetch"] = True
        manifest["source_latest_snapshot_seq"] = tip

    _write(dest / "manifest.json", json.dumps(manifest, indent=2).encode() + b"\n")

    return {
        "dest": str(dest),
        "latest_snapshot_seq": latest,
        "snapshots_downloaded": downloaded,
        "anchors_downloaded": anchors,
        "ots_downloaded": ots,
        "latest_ledger_hash": manifest.get("latest_ledger_hash"),
    }
