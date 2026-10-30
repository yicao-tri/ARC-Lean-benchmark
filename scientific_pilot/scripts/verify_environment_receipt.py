#!/usr/bin/env python3
"""Verify that a fresh environment receipt satisfies the frozen source lock."""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from pilot_common import load_json, sha256_file, write_json


SHA256 = re.compile(r"^[0-9a-f]{64}$")


def git_head(source_receipt: dict[str, Any]) -> str | None:
    for record in source_receipt.get("commands", []):
        if record.get("argv") == ["git", "rev-parse", "HEAD"] and record.get("returncode") == 0:
            return str(record.get("stdout", "")).strip()
    return None


def git_clean(source_receipt: dict[str, Any]) -> bool:
    for record in source_receipt.get("commands", []):
        if record.get("argv") == ["git", "status", "--short"] and record.get("returncode") == 0:
            return not bool(str(record.get("stdout", "")).strip())
    return False


def verify(lock: dict[str, Any], receipt: dict[str, Any], lock_sha: str) -> dict[str, Any]:
    errors: list[str] = []
    if receipt.get("source_lock_sha256") != lock_sha:
        errors.append("receipt source lock SHA does not match the proposed freeze")
    by_id = {row.get("source_id"): row for row in receipt.get("sources", [])}
    for source in lock["sources"]:
        if "EXCLUDED" in source.get("phase1_use", ""):
            continue
        if source["source_id"] not in by_id:
            errors.append(f"receipt missing source {source['source_id']}")
            continue
        observed = by_id[source["source_id"]]
        if not observed.get("exists"):
            errors.append(f"source unavailable: {source['source_id']}")
            continue
        if source.get("controlled_private_source"):
            receipt_sha = source.get("controlled_provenance_receipt_sha256")
            if not isinstance(receipt_sha, str) or not SHA256.fullmatch(receipt_sha):
                errors.append(f"controlled source lacks a private provenance-receipt SHA-256: {source['source_id']}")
            if not git_clean(observed):
                errors.append(f"controlled source working tree not clean or status unavailable: {source['source_id']}")
            # Exact identity and data-path comparison happens in the controlled
            # provenance receipt; public locks deliberately do not disclose it.
            continue
        head = git_head(observed)
        if head != source["commit"]:
            errors.append(f"commit mismatch for {source['source_id']}: expected {source['commit']}, observed {head}")
        if not git_clean(observed):
            errors.append(f"working tree not clean or status unavailable for {source['source_id']}")
        pools = source.get("selection_pool")
        pools = pools if isinstance(pools, list) else [pools] if pools else []
        for relative in pools:
            observed_file = observed.get("files", {}).get(relative, {})
            if not observed_file.get("exists"):
                errors.append(f"missing selection file {source['source_id']}:{relative}")
            else:
                expected_hashes = source.get("required_local_sha256")
                expected = expected_hashes.get(relative) if isinstance(expected_hashes, dict) else expected_hashes
                if not expected:
                    errors.append(f"lock has no locally captured SHA-256 for {source['source_id']}:{relative}")
                elif observed_file.get("sha256") != expected:
                    errors.append(f"local SHA-256 mismatch for {source['source_id']}:{relative}")
        if source["source_id"] in {"minif2f_lean4", "physlib_v2"}:
            build = observed.get("build")
            if not build or build.get("returncode") != 0:
                errors.append(f"missing successful fresh lake build receipt for {source['source_id']}")
            if not observed.get("toolchain_command") or observed["toolchain_command"].get("returncode") != 0:
                errors.append(f"missing Lean/Lake version receipt for {source['source_id']}")
        if "BLOCKED" in source.get("phase1_use", ""):
            errors.append(f"source remains blocked: {source['source_id']}")
    return {"status": "PASS" if not errors else "FAIL", "passed": not errors, "errors": errors}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-lock", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    outcome = verify(load_json(args.source_lock), load_json(args.receipt), sha256_file(args.source_lock))
    if args.output:
        write_json(args.output, outcome)
    print(outcome)
    raise SystemExit(0 if outcome["passed"] else 1)


if __name__ == "__main__":
    main()
