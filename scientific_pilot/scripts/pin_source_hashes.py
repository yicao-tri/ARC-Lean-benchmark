#!/usr/bin/env python3
"""Create a proposed next source lock from a verified local capture receipt.

It never edits the frozen input lock. Review the output, then version it as a
new lock/protocol amendment before running anything.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from pilot_common import load_json, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-lock", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    lock, receipt = load_json(args.source_lock), load_json(args.receipt)
    receipts = {row["source_id"]: row for row in receipt.get("sources", [])}
    for source in lock["sources"]:
        observed = receipts.get(source["source_id"])
        if not observed or not observed.get("exists"):
            continue
        pools = source.get("selection_pool")
        pools = pools if isinstance(pools, list) else [pools] if pools else []
        if pools:
            source["required_local_sha256"] = {relative: observed["files"].get(relative, {}).get("sha256") for relative in pools}
        source["observed_local_commit"] = next((str(command.get("stdout", "")).strip() for command in observed.get("commands", []) if command.get("argv") == ["git", "rev-parse", "HEAD"]), None)
    lock["status"] = "CANDIDATE_LOCAL_HASHES_CAPTURED_NOT_FROZEN"
    lock["derived_from_receipt"] = str(args.receipt)
    write_json(args.output, lock)
    print(f"wrote proposed lock {args.output}; review and version it before use")


if __name__ == "__main__":
    main()
