"""Signing key load (HTTP or offline JSON). No monorepo imports."""

from __future__ import annotations

import json
from pathlib import Path

import requests


def load_signing_keys_file(path: str | Path) -> list:
    try:
        data = json.loads(Path(path).read_text())
    except Exception as e:
        raise Exception(f"could not read signing keys file {path}: {e}") from e
    return data.get("keys", [])


def find_signing_key(keys: list, key_id: str) -> dict:
    for key in keys:
        if key.get("key_id") == key_id:
            return key
    raise Exception(f"signing key not found: {key_id}")


def load_keys(source: str) -> list:
    """
    source: http(s) base URL (fetches /ledger/signing-keys) or path to keys JSON.
    """
    if source.startswith("http://") or source.startswith("https://"):
        url = source.rstrip("/") + "/ledger/signing-keys"
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            return r.json().get("keys", [])
        except Exception as e:
            raise Exception(f"could not fetch signing keys from {url}: {e}") from e
    return load_signing_keys_file(source)
