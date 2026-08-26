from audifact_auditor.cli import build_parser, main


def test_parser_verify():
    p = build_parser()
    args = p.parse_args(["verify", "./public_ledger", "--base-url", "https://audifact.io"])
    assert args.command == "verify"
    assert args.ledger_dir == "./public_ledger"
    assert args.base_url == "https://audifact.io"


def test_cli_missing_keys_exits_2():
    try:
        main(["verify", "/tmp/nope"])
        assert False, "expected SystemExit"
    except SystemExit as e:
        assert e.code == 2
