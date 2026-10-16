"""CLI entrypoint: audifact-auditor"""

from __future__ import annotations

import argparse
import sys

from audifact_auditor import __version__
from audifact_auditor.fetch import fetch_public_ledger
from audifact_auditor.verify_ledger import verify_public_ledger
from audifact_auditor.verify_snapshot import verify_snapshot_file


def _ok(msg: str) -> None:
    print(f"✅ {msg}")


def _fail(msg: str) -> None:
    print(f"❌ FAIL: {msg}", file=sys.stderr)


def _keys_source(args: argparse.Namespace) -> str:
    if args.keys:
        return args.keys
    if args.base_url:
        return args.base_url.rstrip("/")
    _fail("provide --keys PATH or --base-url URL")
    raise SystemExit(2)


def cmd_verify(args: argparse.Namespace) -> int:
    try:
        summary = verify_public_ledger(args.ledger_dir, _keys_source(args))
    except Exception as e:
        _fail(str(e))
        return 1

    _ok(f"snapshots_checked={summary['snapshots_checked']}")
    _ok(f"latest_snapshot_seq={summary['latest_snapshot_seq']}")
    _ok(f"latest_ledger_hash={summary['latest_ledger_hash']}")
    _ok(f"anchor_exports_checked={summary['anchor_exports_checked']}")
    _ok(f"anchors_checked={summary['anchors_checked']}")
    _ok(f"anchor_proofs_checked={summary['anchor_proofs_checked']}")
    _ok(f"anchor_digest_verified={summary['anchor_digest_verified']}")
    _ok(f"calendar_anchors={summary['calendar_anchors']}")
    _ok(f"bitcoin_anchors={summary['bitcoin_anchors']}")
    _ok(f"btc_anchors_verified={summary['btc_anchors_verified']}")
    _ok("manifest verified")
    _ok("public ledger chain verified")
    return 0


def cmd_verify_snapshot(args: argparse.Namespace) -> int:
    try:
        summary = verify_snapshot_file(args.snapshot, _keys_source(args))
    except Exception as e:
        _fail(str(e))
        return 1

    _ok(f"snapshot_seq={summary['snapshot_seq']}")
    _ok(f"ledger_hash={summary['ledger_hash']}")
    _ok(f"signing_key={summary['signing_key']}")
    _ok("snapshot signature verified")
    return 0


def cmd_fetch(args: argparse.Namespace) -> int:
    try:
        summary = fetch_public_ledger(
            args.dest,
            base_url=args.base_url,
            max_seq=args.max_seq,
        )
    except Exception as e:
        _fail(str(e))
        return 1

    _ok(f"dest={summary['dest']}")
    _ok(f"snapshots_downloaded={summary['snapshots_downloaded']}")
    _ok(f"anchors_downloaded={summary['anchors_downloaded']}")
    _ok(f"ots_downloaded={summary['ots_downloaded']}")
    _ok(f"latest_snapshot_seq={summary['latest_snapshot_seq']}")
    if summary.get("latest_ledger_hash"):
        _ok(f"latest_ledger_hash={summary['latest_ledger_hash']}")
    _ok("public ledger fetched")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="audifact-auditor",
        description="Independently verify Audifact public ledger artifacts.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_verify = sub.add_parser(
        "verify",
        help="Verify a full public_ledger directory",
    )
    p_verify.add_argument(
        "ledger_dir",
        help="Path to public_ledger (snapshots + optional anchors/ots)",
    )
    p_verify.add_argument(
        "--base-url",
        help="Site base URL for GET /ledger/signing-keys (e.g. https://audifact.io)",
    )
    p_verify.add_argument(
        "--keys",
        help="Path to signing_keys.json (offline)",
    )
    p_verify.set_defaults(func=cmd_verify)

    p_snap = sub.add_parser(
        "verify-snapshot",
        help="Verify a single snapshot JSON file",
    )
    p_snap.add_argument("snapshot", help="Path to 00000000000N.json")
    p_snap.add_argument("--base-url", help="Site base URL for signing keys")
    p_snap.add_argument("--keys", help="Path to signing_keys.json")
    p_snap.set_defaults(func=cmd_verify_snapshot)

    p_fetch = sub.add_parser(
        "fetch",
        help="Download public_ledger/ from a hosted Audifact site",
    )
    p_fetch.add_argument(
        "dest",
        help="Directory to write (created if missing)",
    )
    p_fetch.add_argument(
        "--base-url",
        default="https://audifact.io",
        help="Site base URL (default: https://audifact.io)",
    )
    p_fetch.add_argument(
        "--max-seq",
        type=int,
        default=None,
        help="Stop after this snapshot_seq (for smoke tests)",
    )
    p_fetch.set_defaults(func=cmd_fetch)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
