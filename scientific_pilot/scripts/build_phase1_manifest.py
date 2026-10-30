#!/usr/bin/env python3
"""Freeze a balanced, deterministic 120-item Phase 1 development manifest.

This script consumes canonicalized candidate units.  Source adapters must make
those candidates first; no LLM outcome may influence selection.  It refuses to
silently substitute an item if an expected stratum is incomplete.
"""
from __future__ import annotations

import argparse
import hashlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from pilot_common import load_json, read_jsonl, sha256_file, write_json

REQUIRED_FIELDS = {
    "item_id",
    "source_id",
    "canonical_id",
    "parent_cluster_id",
    "source_file_id",
    "paper_or_proof_id",
    "gold_error",
    "severity",
    "error_families",
    "formalizable",
    "content_sha256",
    "candidate_text",
    "source_content_pointer",
}


def stable_rank(seed: str, row: dict[str, Any]) -> str:
    token = f"{seed}\0{row['source_id']}\0{row['canonical_id']}".encode()
    return hashlib.sha256(token).hexdigest()


def validate_candidate(row: dict[str, Any], lineno: int) -> None:
    missing = REQUIRED_FIELDS - set(row)
    if missing:
        raise ValueError(f"candidate line {lineno} missing {sorted(missing)}")
    if not isinstance(row["gold_error"], bool):
        raise ValueError(f"candidate {row['canonical_id']} gold_error must be boolean")
    if row["severity"] not in {"clean", "minor", "major"}:
        raise ValueError(f"candidate {row['canonical_id']} has invalid severity")
    if row["gold_error"] == (row["severity"] == "clean"):
        raise ValueError(f"candidate {row['canonical_id']} has inconsistent error/severity")
    expected_item_id = f"{row['source_id']}::{row['canonical_id']}"
    if row["item_id"] != expected_item_id:
        raise ValueError(f"candidate {row['canonical_id']} item_id must be {expected_item_id!r}")


def choose(rows: list[dict[str, Any]], *, seed: str, n_error: int, n_clean: int) -> list[dict[str, Any]]:
    by_kind = {True: [], False: []}
    for row in rows:
        by_kind[row["gold_error"]].append(row)
    selected: list[dict[str, Any]] = []
    for truth, target in ((True, n_error), (False, n_clean)):
        candidates = sorted(by_kind[truth], key=lambda row: stable_rank(seed, row))
        if len(candidates) < target:
            label = "error" if truth else "clean"
            raise ValueError(f"need {target} {label} candidates; found {len(candidates)}")
        selected.extend(candidates[:target])
    return sorted(selected, key=lambda row: (row["source_id"], stable_rank(seed, row)))


def build(candidates: list[dict[str, Any]], source_targets: dict[str, int], *, seed: str, source_lock: Path, allowed_sources: set[str] | None = None) -> dict[str, Any]:
    for lineno, row in enumerate(candidates, start=1):
        validate_candidate(row, lineno)
    ids = [(row["source_id"], row["canonical_id"]) for row in candidates]
    if len(ids) != len(set(ids)):
        duplicates = [key for key, count in Counter(ids).items() if count > 1]
        raise ValueError(f"duplicate canonical candidates: {duplicates[:5]}")

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        grouped[row["source_id"]].append(row)
    selected: list[dict[str, Any]] = []
    for source_id, target in source_targets.items():
        if allowed_sources is not None and source_id not in allowed_sources:
            raise ValueError(f"source {source_id} is not eligible for Phase 1 under the source lock")
        if target % 2:
            raise ValueError(f"target for {source_id} must be even for balanced pilot")
        if source_id not in grouped:
            raise ValueError(f"no candidates for required source {source_id}")
        picked = choose(grouped[source_id], seed=seed, n_error=target // 2, n_clean=target // 2)
        for row in picked:
            material = dict(row)
            material["selection_rank"] = stable_rank(seed, row)
            selected.append(material)

    if len(selected) != sum(source_targets.values()):
        raise AssertionError("selection count changed unexpectedly")
    parent_by_source: set[tuple[str, str]] = set()
    for row in selected:
        key = (row["source_id"], row["parent_cluster_id"])
        if key in parent_by_source:
            # Multiple candidates may share a parent only when the protocol explicitly
            # declares it.  Phase 1 uses one unit per parent to simplify clustering.
            raise ValueError(f"parent-cluster collision in selected manifest: {key}")
        parent_by_source.add(key)

    return {
        "schema_version": "arc-leanbench-phase1-manifest-1",
        "purpose": "development_pilot_not_sealed",
        "selection_seed": seed,
        "source_lock_sha256": sha256_file(source_lock),
        "selection_script_sha256": sha256_file(Path(__file__)),
        "counts": {source: sum(1 for row in selected if row["source_id"] == source) for source in source_targets},
        "items": selected,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--source-lock", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", default="arc-leanbench-phase1-v1")
    parser.add_argument(
        "--source-target",
        action="append",
        default=[],
        metavar="SOURCE=N",
        help="required once for each source, e.g. minif2f_lean4=30",
    )
    args = parser.parse_args()
    source_targets: dict[str, int] = {}
    for value in args.source_target:
        source, count = value.split("=", 1)
        source_targets[source] = int(count)
    if not source_targets:
        raise SystemExit("at least one --source-target is required")
    lock = load_json(args.source_lock)
    known = {entry["source_id"] for entry in lock["sources"]}
    unknown = set(source_targets) - known
    if unknown:
        raise SystemExit(f"targets missing from source lock: {sorted(unknown)}")
    allowed = {entry["source_id"] for entry in lock["sources"] if "BLOCKED" not in entry.get("phase1_use", "") and "EXCLUDED" not in entry.get("phase1_use", "")}
    manifest = build(read_jsonl(args.candidates), source_targets, seed=args.seed, source_lock=args.source_lock, allowed_sources=allowed)
    write_json(args.output, manifest)
    print(f"wrote {args.output} with {len(manifest['items'])} frozen development-pilot units")


if __name__ == "__main__":
    main()
