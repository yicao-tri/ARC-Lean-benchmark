#!/usr/bin/env python3
"""Validate the protocol contract before an ARC-LeanBench run is allowed."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pilot_common import load_json, repo_root, sha256_file, write_json
from validate_arm_contract import validate as validate_arm_contract


def validate(root: Path, *, strict: bool) -> dict[str, Any]:
    protocol = root / "docs" / "arc_leanbench" / "PHASE0_PROTOCOL_v1.md"
    blueprint = root / "docs" / "arc_leanbench" / "BLUEPRINT_v1.md"
    rubric = root / "docs" / "arc_leanbench" / "GOLD_RUBRIC_v1.md"
    review = root / "docs" / "arc_leanbench" / "REVIEW_GATE.md"
    lock_path = root / "scientific_pilot" / "config" / "sources.lock.json"
    arms_path = root / "scientific_pilot" / "config" / "arms_v1.json"
    run_plan_path = root / "scientific_pilot" / "config" / "run_plan_v1.json"
    schema_path = root / "scientific_pilot" / "config" / "output_schema_v1.json"
    model_lock_path = root / "scientific_pilot" / "config" / "model.lock.json"
    gold_schema_path = root / "scientific_pilot" / "config" / "gold_annotation_schema_v1.json"
    checklist_path = root / "scientific_pilot" / "config" / "pre_run_checklist_v1.md"
    source_decisions = root / "docs" / "arc_leanbench" / "SOURCE_DECISIONS_v1.md"
    required = [protocol, blueprint, rubric, review, source_decisions, lock_path, arms_path, run_plan_path, schema_path, model_lock_path, gold_schema_path, checklist_path]
    errors = [f"missing {path.relative_to(root)}" for path in required if not path.exists()]
    if errors:
        return {"passed": False, "errors": errors, "warnings": [], "artifacts": {}}

    lock = load_json(lock_path)
    arms = load_json(arms_path)
    plan = load_json(run_plan_path)
    schema = load_json(schema_path)
    model_lock = load_json(model_lock_path)
    gold_schema = load_json(gold_schema_path)
    warnings: list[str] = []
    source_ids = {source["source_id"] for source in lock.get("sources", [])}
    required_sources = set(plan.get("strata", {}))
    if missing := required_sources - source_ids:
        errors.append(f"run plan has sources absent from lock: {sorted(missing)}")
    arm_ids = [arm["id"] for arm in arms.get("arms", [])]
    if arm_ids != ["A0", "A1", "A2", "A3", "A4", "A5", "A6"]:
        errors.append(f"arms must be exactly A0–A6 in order; got {arm_ids}")
    arm_result = validate_arm_contract(arms)
    errors.extend(f"arm contract: {message}" for message in arm_result["errors"])
    if plan.get("expected_run_count") != 2520:
        errors.append("expected_run_count must equal 120 × 7 × 3 = 2520")
    if model_lock.get("status") != "FROZEN":
        message = "model lock is not frozen with an immutable local model identity"
        (errors if strict else warnings).append(message)
    if gold_schema.get("minimum_double_coded_fraction", 0) < 0.2:
        errors.append("gold schema must require at least 20% blind double coding")
    required_output = {"item_id", "arm_id", "replicate", "lean_status", "semantic_alignment", "tool_receipts"}
    missing_output = required_output - set(schema.get("required", []))
    if missing_output:
        errors.append(f"output schema misses required audit fields: {sorted(missing_output)}")

    for source in lock.get("sources", []):
        use = source.get("phase1_use", "")
        if source["source_id"] in required_sources and "BLOCKED" in use:
            errors.append(f"required source blocked: {source['source_id']} ({use})")
        if source["source_id"] in required_sources and not source.get("required_local_sha256"):
            message = f"local content SHA-256 not captured: {source['source_id']}"
            (errors if strict else warnings).append(message)
    status = "PASS" if not errors else "FAIL"
    artifacts = {str(path.relative_to(root)): sha256_file(path) for path in required}
    return {"status": status, "passed": not errors, "errors": errors, "warnings": warnings, "artifacts": artifacts}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=repo_root(Path(__file__)))
    parser.add_argument("--strict", action="store_true", help="fail pending local source hashes")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.root, strict=args.strict)
    if args.output:
        write_json(args.output, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
