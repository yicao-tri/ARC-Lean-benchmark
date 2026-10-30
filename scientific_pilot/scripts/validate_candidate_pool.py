#!/usr/bin/env python3
"""Validate canonicalized candidate audit units before deterministic selection."""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from build_phase1_manifest import REQUIRED_FIELDS, validate_candidate
from pilot_common import read_jsonl, sha256_file, write_json


def validate(rows: list[dict]) -> dict:
    errors: list[str] = []
    for lineno, row in enumerate(rows, start=1):
        try:
            validate_candidate(row, lineno)
        except ValueError as exc:
            errors.append(str(exc))
    pairs = [(row.get("source_id"), row.get("canonical_id")) for row in rows]
    duplicates = [pair for pair, count in Counter(pairs).items() if count > 1]
    if duplicates:
        errors.append(f"duplicate source/canonical IDs: {duplicates[:5]}")
    return {"passed": not errors, "n_candidates": len(rows), "errors": errors, "required_fields": sorted(REQUIRED_FIELDS)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(read_jsonl(args.input))
    result["input_sha256"] = sha256_file(args.input)
    if args.output:
        write_json(args.output, result)
    print(result)
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
