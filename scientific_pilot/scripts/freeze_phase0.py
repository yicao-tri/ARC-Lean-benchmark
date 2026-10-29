#!/usr/bin/env python3
"""Create an immutable Phase 0 freeze receipt only when all gates pass.

This command cannot turn a pending protocol into a pass: it delegates to the
strict validator and environment verifier, checks the model receipt/lock and
checks the exact manifest.  The caller should commit its output unchanged.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pilot_common import load_json, repo_root, sha256_file, write_json
from validate_phase0 import validate as validate_phase0
from verify_environment_receipt import verify


TARGETS = {
    "minif2f_lean4": 30,
    "formalphysics_v2_formalscience": 30,
    "scibench_quantitative": 30,
    "arc_controlled_claims": 30,
}


def validate_manifest(manifest: dict[str, Any], source_lock_sha: str) -> list[str]:
    errors: list[str] = []
    if manifest.get("purpose") != "development_pilot_not_sealed":
        errors.append("manifest does not clearly identify the development-pilot boundary")
    if manifest.get("source_lock_sha256") != source_lock_sha:
        errors.append("manifest source-lock SHA mismatch")
    items = manifest.get("items", [])
    if len(items) != 120:
        errors.append(f"manifest has {len(items)} rather than 120 items")
    ids = [(row.get("source_id"), row.get("canonical_id")) for row in items]
    if len(ids) != len(set(ids)):
        errors.append("manifest contains duplicate source/canonical IDs")
    for source, target in TARGETS.items():
        values = [row for row in items if row.get("source_id") == source]
        if len(values) != target:
            errors.append(f"{source} has {len(values)} rather than {target} units")
            continue
        if sum(bool(row.get("gold_error")) for row in values) != 15:
            errors.append(f"{source} lacks the frozen 15 error / 15 clean allocation")
        parents = [row.get("parent_cluster_id") for row in values]
        if len(parents) != len(set(parents)):
            errors.append(f"{source} contains parent-cluster collisions")
    return errors


def validate_model(lock: dict[str, Any], receipt: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if lock.get("status") != "FROZEN":
        errors.append("model lock status is not FROZEN")
    if not lock.get("model_digest") or not lock.get("model_file_sha256"):
        errors.append("model lock lacks immutable digest/model-file SHA")
    if receipt.get("model_show_sha256") != lock.get("model_file_sha256"):
        errors.append("model receipt/model lock SHA mismatch")
    if receipt.get("model_show", {}).get("returncode") != 0:
        errors.append("model receipt lacks successful model inspection")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=repo_root(Path(__file__)))
    parser.add_argument("--environment-receipt", type=Path, required=True)
    parser.add_argument("--model-receipt", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root
    lock_path = root / "scientific_pilot" / "config" / "sources.lock.json"
    model_lock_path = root / "scientific_pilot" / "config" / "model.lock.json"
    preflight = validate_phase0(root, strict=True)
    environment = verify(load_json(lock_path), load_json(args.environment_receipt), sha256_file(lock_path))
    manifest_errors = validate_manifest(load_json(args.manifest), sha256_file(lock_path))
    model_errors = validate_model(load_json(model_lock_path), load_json(args.model_receipt))
    errors = [*preflight["errors"], *environment["errors"], *manifest_errors, *model_errors]
    receipt = {
        "schema_version": "arc-leanbench-phase0-freeze-1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if not errors else "FAIL",
        "protocol_artifacts": preflight["artifacts"],
        "source_lock_sha256": sha256_file(lock_path),
        "model_lock_sha256": sha256_file(model_lock_path),
        "environment_receipt_sha256": sha256_file(args.environment_receipt),
        "model_receipt_sha256": sha256_file(args.model_receipt),
        "manifest_sha256": sha256_file(args.manifest),
        "errors": errors,
        "warnings": preflight["warnings"],
    }
    write_json(args.output, receipt)
    print(f"wrote {args.output}: {receipt['status']}")
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
