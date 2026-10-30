#!/usr/bin/env python3
"""Score actual ARC-LeanBench raw runs and estimate paired effects.

Fixture data are permitted for unit tests only.  The result JSON marks its
input status, so a caller cannot accidentally label fixtures as pilot evidence.
"""
from __future__ import annotations

import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from pilot_common import load_json, read_jsonl, sha256_file, write_json, write_jsonl
from validate_raw_runs import validate as validate_raw_runs
from verify_execution_receipt import verify as verify_execution_receipt


ARM_ORDER = ["A0", "A1", "A2", "A3", "A4", "A5", "A6"]


def _truth(row: dict[str, Any], field: str, default: Any = None) -> Any:
    return row.get(field, default)


def score_one(gold: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    scheduled = True
    completed = run.get("run_status") == "completed"
    decision = run.get("decision")
    gold_error = bool(gold["gold_error"])
    decision_correct = completed and ((gold_error and decision == "error") or (not gold_error and decision == "clean"))
    gold_families = set(gold.get("error_families", []))
    family_correct = (not gold_error and not run.get("error_families")) or (gold_error and set(run.get("error_families", [])) == gold_families)
    id_gold = _truth(gold, "identifiability", "not_applicable")
    boundary_gold = _truth(gold, "claim_boundary", "not_applicable")
    semantic_gold = _truth(gold, "semantic_alignment", "not_applicable")
    localization_gold = _truth(gold, "localization", "not_applicable")
    repair_gold = _truth(gold, "repair", "not_applicable")
    identifiability_correct = id_gold == "not_applicable" or run.get("identifiability") == id_gold
    boundary_correct = boundary_gold == "not_applicable" or run.get("claim_boundary") == boundary_gold
    semantic_alignment_correct = semantic_gold == "not_applicable" or run.get("semantic_alignment") == semantic_gold
    localization_correct = localization_gold == "not_applicable" or run.get("localization") == localization_gold
    repair_correct = repair_gold == "not_applicable" or run.get("repair") == repair_gold
    joint_correct = decision_correct and family_correct and identifiability_correct and boundary_correct and semantic_alignment_correct
    return {
        "item_id": gold["item_id"],
        "parent_cluster_id": gold["parent_cluster_id"],
        "source_id": gold["source_id"],
        "primary_error_family": gold.get("primary_error_family", "clean" if not gold_error else "unclassified"),
        "formalizable": bool(gold.get("formalizable", False)),
        "gold_error": gold_error,
        "arm_id": run["arm_id"],
        "replicate": run["replicate"],
        "scheduled": scheduled,
        "completed": completed,
        "decision": decision,
        "decision_correct": decision_correct,
        "family_correct": family_correct,
        "identifiability_correct": identifiability_correct,
        "boundary_correct": boundary_correct,
        "semantic_alignment_correct": semantic_alignment_correct,
        "localization_correct": localization_correct,
        "repair_correct": repair_correct,
        "joint_correct": joint_correct,
        "coverage": completed and decision != "inconclusive",
        "lean_status": run.get("lean_status", "not_requested"),
        "semantic_alignment": run.get("semantic_alignment", "not_applicable"),
        "confidence": float(run.get("confidence", 0.0)),
        "cost_usd": float(run.get("cost_usd", 0.0)),
        "wallclock_seconds": float(run.get("wallclock_seconds", 0.0)),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    positives = [row for row in rows if row["gold_error"]]
    negatives = [row for row in rows if not row["gold_error"]]
    sensitivity = sum(row["decision_correct"] for row in positives) / len(positives) if positives else None
    specificity = sum(row["decision_correct"] for row in negatives) / len(negatives) if negatives else None
    balanced = (sensitivity + specificity) / 2 if sensitivity is not None and specificity is not None else None
    eligible_semantic = [row for row in rows if row["semantic_alignment"] != "not_applicable"]
    return {
        "n": n,
        "n_error": len(positives),
        "n_clean": len(negatives),
        "sensitivity": sensitivity,
        "specificity": specificity,
        "balanced_audit_accuracy": balanced,
        "decision_accuracy": sum(row["decision_correct"] for row in rows) / n if n else None,
        "joint_audit_accuracy": sum(row["joint_correct"] for row in rows) / n if n else None,
        "coverage": sum(row["coverage"] for row in rows) / n if n else None,
        "formalization_attempt_rate": sum(row["lean_status"] not in {"not_requested", "tool_error"} for row in rows) / n if n else None,
        "kernel_verified_rate": sum(row["lean_status"] == "verified" for row in rows) / n if n else None,
        "semantic_alignment_accuracy": (sum(row["semantic_alignment_correct"] for row in eligible_semantic) / len(eligible_semantic) if eligible_semantic else None),
        "localization_accuracy": (sum(row["localization_correct"] for row in rows) / n if n else None),
        "repair_accuracy": (sum(row["repair_correct"] for row in rows) / n if n else None),
        "false_confidence_rate": sum((row["confidence"] >= 0.8 and not row["decision_correct"]) for row in rows) / n if n else None,
        "mean_cost_usd": mean(row["cost_usd"] for row in rows) if rows else None,
        "mean_wallclock_seconds": mean(row["wallclock_seconds"] for row in rows) if rows else None,
        "lean_status_counts": {status: sum(row["lean_status"] == status for row in rows) for status in ["not_requested", "verified", "formal_failure", "tool_error", "semantic_unverified"]},
    }


def aggregate_item_level(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate scheduled replicates before primary item-level analysis."""
    by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_key[(row["item_id"], row["arm_id"])].append(row)
    output: list[dict[str, Any]] = []
    for (_, _), replicate_rows in by_key.items():
        ordered = sorted(replicate_rows, key=lambda row: row["replicate"])
        threshold = len(ordered) // 2 + 1
        exemplar = dict(ordered[0])
        for field in ("decision_correct", "family_correct", "identifiability_correct", "boundary_correct", "semantic_alignment_correct", "localization_correct", "repair_correct", "joint_correct", "coverage"):
            exemplar[field] = sum(bool(row[field]) for row in ordered) >= threshold
        exemplar["n_replicates"] = len(ordered)
        exemplar["raw_correct_count"] = sum(bool(row["decision_correct"]) for row in ordered)
        exemplar["confidence"] = mean(row["confidence"] for row in ordered)
        exemplar["cost_usd"] = mean(row["cost_usd"] for row in ordered)
        exemplar["wallclock_seconds"] = mean(row["wallclock_seconds"] for row in ordered)
        statuses = [row["lean_status"] for row in ordered]
        exemplar["lean_status"] = next((status for status in ("verified", "formal_failure", "semantic_unverified", "tool_error", "not_requested") if status in statuses), "not_requested")
        output.append(exemplar)
    return output


def _balanced_accuracy(rows: list[dict[str, Any]]) -> float | None:
    positives = [row for row in rows if row["gold_error"]]
    negatives = [row for row in rows if not row["gold_error"]]
    if not positives or not negatives:
        return None
    return (mean(float(row["decision_correct"]) for row in positives) + mean(float(row["decision_correct"]) for row in negatives)) / 2


def paired_effect(rows: list[dict[str, Any]], treated: str, control: str, *, bootstrap_replicates: int, rng_seed: int) -> dict[str, Any]:
    by_key: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        by_key[row["item_id"]][row["arm_id"]] = row
    pairs = [(values[treated], values[control]) for values in by_key.values() if treated in values and control in values]
    if not pairs:
        return {"treated": treated, "control": control, "n_pairs": 0, "effect": None, "ci95": None}
    by_stratum: dict[tuple[str, bool], dict[str, list[tuple[dict[str, Any], dict[str, Any]]]]] = defaultdict(lambda: defaultdict(list))
    for pair in pairs:
        by_stratum[(pair[0]["source_id"], pair[0]["gold_error"])][pair[0]["parent_cluster_id"]].append(pair)

    def estimate(sample: list[tuple[dict[str, Any], dict[str, Any]]]) -> float:
        treated_rows, control_rows = zip(*sample)
        treated_ba = _balanced_accuracy(list(treated_rows))
        control_ba = _balanced_accuracy(list(control_rows))
        if treated_ba is None or control_ba is None:
            raise ValueError("paired balanced accuracy requires both gold-error classes")
        return treated_ba - control_ba

    effect = estimate(pairs)
    rng = random.Random(rng_seed)
    samples: list[float] = []
    for _ in range(bootstrap_replicates):
        resampled: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for cluster_map in by_stratum.values():
            clusters = list(cluster_map)
            for _ in clusters:
                resampled.extend(cluster_map[rng.choice(clusters)])
        samples.append(estimate(resampled))
    samples.sort()
    low = samples[int(0.025 * (len(samples) - 1))]
    high = samples[int(0.975 * (len(samples) - 1))]
    n_clusters = sum(len(cluster_map) for cluster_map in by_stratum.values())
    return {"treated": treated, "control": control, "estimand": "item_level_balanced_audit_accuracy_difference", "n_pairs": len(pairs), "n_clusters": n_clusters, "effect": effect, "ci95": [low, high]}


def evaluate(gold: list[dict[str, Any]], runs: list[dict[str, Any]], *, bootstrap_replicates: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    gold_by_id = {row["item_id"]: row for row in gold}
    if len(gold_by_id) != len(gold):
        raise ValueError("gold item IDs must be unique")
    unknown = [run.get("item_id") for run in runs if run.get("item_id") not in gold_by_id]
    if unknown:
        raise ValueError(f"raw output references unknown items: {unknown[:5]}")
    scored = [score_one(gold_by_id[run["item_id"]], run) for run in runs]
    item_scored = aggregate_item_level(scored)
    arms = {arm: summarize([row for row in item_scored if row["arm_id"] == arm]) for arm in ARM_ORDER}
    raw_run_arms = {arm: summarize([row for row in scored if row["arm_id"] == arm]) for arm in ARM_ORDER}
    families = sorted({row["primary_error_family"] for row in item_scored})
    taxonomy = {
        family: {arm: summarize([row for row in item_scored if row["primary_error_family"] == family and row["arm_id"] == arm]) for arm in ARM_ORDER}
        for family in families
    }
    formalizability = {
        label: {arm: summarize([row for row in item_scored if row["formalizable"] == wanted and row["arm_id"] == arm]) for arm in ARM_ORDER}
        for label, wanted in (("formalizable", True), ("not_formalizable", False))
    }
    effects = [
        paired_effect(item_scored, "A6", "A5", bootstrap_replicates=bootstrap_replicates, rng_seed=1729),
        paired_effect(item_scored, "A3", "A0", bootstrap_replicates=bootstrap_replicates, rng_seed=2718),
    ]
    return scored, item_scored, {"primary_analysis_unit": "source_level_item_majority_over_replicates", "arms": arms, "raw_run_arms": raw_run_arms, "taxonomy": taxonomy, "formalizability": formalizability, "paired_effects": effects}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--run-plan", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--arms", type=Path)
    parser.add_argument("--execution-receipt", type=Path)
    parser.add_argument("--phase0-freeze", type=Path)
    parser.add_argument("--fixture-only", action="store_true", help="mark outputs as fixture-only; cannot be used as pilot evidence")
    args = parser.parse_args()
    plan = load_json(args.run_plan)
    gold, runs = read_jsonl(args.gold), read_jsonl(args.runs)
    schema_path = Path(__file__).resolve().parents[1] / "config" / "output_schema_v1.json"
    if not args.fixture_only and any(value is None for value in (args.manifest, args.arms, args.execution_receipt, args.phase0_freeze)):
        raise SystemExit("actual scoring requires --manifest, --arms, --execution-receipt, and --phase0-freeze")
    arm_contract = load_json(args.arms) if args.arms else None
    raw_validation = validate_raw_runs(
        load_json(schema_path),
        runs,
        expected_run_count=None if args.fixture_only else plan["expected_run_count"],
        manifest=load_json(args.manifest) if args.manifest else None,
        arm_ids=[arm["id"] for arm in arm_contract["arms"]] if arm_contract else None,
        replicates=plan["replicates"] if args.manifest else None,
    )
    if not raw_validation["passed"]:
        raise SystemExit("raw run validation failed: " + "; ".join(raw_validation["errors"]))
    execution_validation = {"status": "FIXTURE_ONLY", "passed": True, "errors": []}
    if not args.fixture_only:
        execution_validation = verify_execution_receipt(
            load_json(args.execution_receipt),
            phase0_freeze=args.phase0_freeze,
            manifest=args.manifest,
            runs=args.runs,
            arms=args.arms,
        )
        if not execution_validation["passed"]:
            raise SystemExit("execution receipt validation failed: " + "; ".join(execution_validation["errors"]))
    scored, item_scored, summary = evaluate(gold, runs, bootstrap_replicates=int(plan["analysis"]["bootstrap_replicates"]))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "scored_runs.jsonl", scored)
    write_jsonl(args.output_dir / "item_scores.jsonl", item_scored)
    summary.update({
        "schema_version": "arc-leanbench-phase1-results-1",
        "input_status": "FIXTURE_ONLY" if args.fixture_only else "RAW_EXECUTION",
        "n_gold_items": len(gold),
        "n_raw_runs": len(runs),
        "expected_run_count": plan["expected_run_count"],
        "run_count_complete": len(runs) == plan["expected_run_count"],
        "raw_validation": raw_validation,
        "execution_validation": execution_validation,
        "execution_receipt_sha256": (sha256_file(args.execution_receipt) if args.execution_receipt else None),
    })
    write_json(args.output_dir / "metrics.json", summary)
    with (args.output_dir / "arm_summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["arm_id", *next(iter(summary["arms"].values())).keys()])
        writer.writeheader()
        for arm, values in summary["arms"].items():
            writer.writerow({"arm_id": arm, **{key: value if not isinstance(value, dict) else str(value) for key, value in values.items()}})
    print(f"wrote score bundle to {args.output_dir}; raw runs={len(runs)}")


if __name__ == "__main__":
    main()
