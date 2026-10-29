#!/usr/bin/env python3
"""Validate scheduled raw run records before they can be scored."""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from pilot_common import load_json, read_jsonl, write_json


def validate(schema: dict[str, Any], rows: list[dict[str, Any]], *, expected_run_count: int | None = None, manifest: dict[str, Any] | None = None, arm_ids: list[str] | None = None, replicates: int | None = None) -> dict[str, Any]:
    errors: list[str] = []
    required = set(schema.get("required", []))
    properties = schema.get("properties", {})
    keys: list[tuple[str, str, int]] = []
    for lineno, row in enumerate(rows, start=1):
        missing = required - set(row)
        if missing:
            errors.append(f"line {lineno}: missing {sorted(missing)}")
            continue
        for field, spec in properties.items():
            if "enum" in spec and row.get(field) not in spec["enum"]:
                errors.append(f"line {lineno}: {field}={row.get(field)!r} is outside enum")
        keys.append((str(row["item_id"]), str(row["arm_id"]), int(row["replicate"])))
    duplicate = [key for key, count in Counter(keys).items() if count > 1]
    if duplicate:
        errors.append(f"duplicate scheduled run keys: {duplicate[:5]}")
    if expected_run_count is not None and len(rows) != expected_run_count:
        errors.append(f"expected {expected_run_count} raw records; found {len(rows)}")
    if manifest is not None:
        if arm_ids is None or replicates is None:
            raise ValueError("manifest schedule validation requires arm_ids and replicates")
        expected_keys = {
            (str(item["item_id"]), arm_id, replicate)
            for item in manifest.get("items", [])
            for arm_id in arm_ids
            for replicate in range(replicates)
        }
        observed = set(keys)
        missing = sorted(expected_keys - observed)
        unexpected = sorted(observed - expected_keys)
        if missing:
            errors.append(f"missing scheduled run keys: {missing[:5]} (total={len(missing)})")
        if unexpected:
            errors.append(f"unexpected scheduled run keys: {unexpected[:5]} (total={len(unexpected)})")
    return {"status": "PASS" if not errors else "FAIL", "passed": not errors, "n_rows": len(rows), "errors": errors}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--expected-run-count", type=int)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--arms", type=Path)
    parser.add_argument("--replicates", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    arm_ids = [row["id"] for row in load_json(args.arms)["arms"]] if args.arms else None
    result = validate(load_json(args.schema), read_jsonl(args.runs), expected_run_count=args.expected_run_count, manifest=load_json(args.manifest) if args.manifest else None, arm_ids=arm_ids, replicates=args.replicates)
    if args.output:
        write_json(args.output, result)
    print(result)
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
