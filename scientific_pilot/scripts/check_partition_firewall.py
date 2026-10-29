#!/usr/bin/env python3
"""Reject leakage between development and evaluator-controlled sealed manifests."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from pilot_common import load_json, write_json


FIELDS = ("item_id", "canonical_id", "parent_cluster_id", "source_file_id", "paper_or_proof_id")


def check(dev: dict[str, Any], sealed: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if dev.get("purpose") != "development_pilot_not_sealed":
        errors.append("development manifest purpose boundary is incorrect")
    if sealed.get("purpose") != "sealed_evaluation":
        errors.append("sealed manifest purpose boundary is incorrect")
    dev_rows = dev.get("items", [])
    sealed_rows = sealed.get("items", [])
    overlaps: dict[str, list[str]] = {}
    for field in FIELDS:
        dev_values = {str(row.get(field)) for row in dev_rows if row.get(field) is not None}
        sealed_values = {str(row.get(field)) for row in sealed_rows if row.get(field) is not None}
        overlap = sorted(dev_values & sealed_values)
        if overlap:
            overlaps[field] = overlap
            errors.append(f"{field} overlaps between development and sealed: {overlap[:5]}")
    return {"status": "PASS" if not errors else "FAIL", "passed": not errors, "n_development": len(dev_rows), "n_sealed": len(sealed_rows), "overlaps": overlaps, "errors": errors}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--development-manifest", type=Path, required=True)
    parser.add_argument("--sealed-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = check(load_json(args.development_manifest), load_json(args.sealed_manifest))
    if args.output:
        write_json(args.output, result)
    print(result)
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
