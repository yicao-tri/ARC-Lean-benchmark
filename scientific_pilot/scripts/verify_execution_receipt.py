#!/usr/bin/env python3
"""Bind actual raw outputs to a passed Phase 0 freeze before scoring/plotting."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from pilot_common import load_json, sha256_file, write_json


def verify(receipt: dict[str, Any], *, phase0_freeze: Path, manifest: Path, runs: Path, arms: Path) -> dict[str, Any]:
    errors: list[str] = []
    freeze = load_json(phase0_freeze)
    if freeze.get("status") != "PASS":
        errors.append("Phase 0 freeze receipt is not PASS")
    expected = {
        "phase0_freeze_sha256": sha256_file(phase0_freeze),
        "manifest_sha256": sha256_file(manifest),
        "raw_runs_sha256": sha256_file(runs),
        "arms_sha256": sha256_file(arms),
    }
    for field, value in expected.items():
        if receipt.get(field) != value:
            errors.append(f"execution receipt mismatch for {field}")
    if receipt.get("status") != "EXECUTED":
        errors.append("execution receipt status is not EXECUTED")
    if not receipt.get("runner_commit"):
        errors.append("execution receipt lacks runner commit")
    return {"status": "PASS" if not errors else "FAIL", "passed": not errors, "errors": errors, "expected": expected}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--phase0-freeze", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--arms", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(load_json(args.receipt), phase0_freeze=args.phase0_freeze, manifest=args.manifest, runs=args.runs, arms=args.arms)
    if args.output:
        write_json(args.output, result)
    print(result)
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
