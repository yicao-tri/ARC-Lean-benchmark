#!/usr/bin/env python3
"""Render Phase 1 figures only from an actual locked result bundle."""
from __future__ import annotations

import argparse
from pathlib import Path

from pilot_common import load_json, read_jsonl
from verify_execution_receipt import verify as verify_execution_receipt


def require_actual(metrics: dict, allow_fixture: bool) -> None:
    if metrics.get("input_status") != "RAW_EXECUTION" and not allow_fixture:
        raise RuntimeError("refusing to render publication figures from fixture-only results")
    if not metrics.get("run_count_complete") and not allow_fixture:
        raise RuntimeError("refusing to render figures from an incomplete scheduled run set")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--execution-receipt", type=Path)
    parser.add_argument("--phase0-freeze", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--runs", type=Path)
    parser.add_argument("--arms", type=Path)
    parser.add_argument("--allow-fixture", action="store_true")
    args = parser.parse_args()
    metrics = load_json(args.results_dir / "metrics.json")
    require_actual(metrics, args.allow_fixture)
    if not args.allow_fixture:
        if any(value is None for value in (args.execution_receipt, args.phase0_freeze, args.manifest, args.runs, args.arms)):
            raise SystemExit("actual figure rendering requires execution receipt, Phase 0 freeze, manifest, runs, and arms")
        receipt = verify_execution_receipt(load_json(args.execution_receipt), phase0_freeze=args.phase0_freeze, manifest=args.manifest, runs=args.runs, arms=args.arms)
        if not receipt["passed"]:
            raise SystemExit("execution receipt validation failed: " + "; ".join(receipt["errors"]))
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit("matplotlib is required to render figures") from exc
    args.output_dir.mkdir(parents=True, exist_ok=True)
    arms = list(metrics["arms"])
    values = [metrics["arms"][arm]["balanced_audit_accuracy"] or 0 for arm in arms]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(arms, values, color="#557A95")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Balanced audit accuracy")
    ax.set_title("Phase 1 development pilot: multi-arm aggregate")
    fig.tight_layout()
    fig.savefig(args.output_dir / "phase1_multi_arm.png", dpi=240)
    fig.savefig(args.output_dir / "phase1_multi_arm.svg")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    for arm in arms:
        value = metrics["arms"][arm]
        ax.scatter(value["mean_cost_usd"] or 0, value["coverage"] or 0, s=60, label=arm)
        ax.annotate(arm, (value["mean_cost_usd"] or 0, value["coverage"] or 0), xytext=(4, 4), textcoords="offset points")
    ax.set_xlabel("Mean cost (USD / scheduled run)")
    ax.set_ylabel("Coverage")
    ax.set_title("Phase 1 development pilot: coverage–cost")
    fig.tight_layout()
    fig.savefig(args.output_dir / "phase1_coverage_cost.png", dpi=240)
    fig.savefig(args.output_dir / "phase1_coverage_cost.svg")
    plt.close(fig)

    effects = metrics["paired_effects"]
    fig, ax = plt.subplots(figsize=(7, 3.8))
    labels = [f"{effect['treated']} − {effect['control']}" for effect in effects]
    estimates = [effect["effect"] or 0 for effect in effects]
    lows = [estimate - effect["ci95"][0] if effect["ci95"] else 0 for estimate, effect in zip(estimates, effects)]
    highs = [effect["ci95"][1] - estimate if effect["ci95"] else 0 for estimate, effect in zip(estimates, effects)]
    ax.errorbar(estimates, range(len(effects)), xerr=[lows, highs], fmt="o", color="#8A4F7D", capsize=4)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_yticks(range(len(effects)), labels)
    ax.set_xlabel("Paired item-level balanced-audit-accuracy difference (95% CI)")
    ax.set_title("Phase 1 development pilot: prespecified Lean contrasts")
    fig.tight_layout()
    fig.savefig(args.output_dir / "phase1_paired_effects.png", dpi=240)
    fig.savefig(args.output_dir / "phase1_paired_effects.svg")
    plt.close(fig)

    rows = read_jsonl(args.results_dir / "item_scores.jsonl")
    item_ids = sorted({row["item_id"] for row in rows})
    matrix = []
    for item_id in item_ids:
        item_rows = {row["arm_id"]: row for row in rows if row["item_id"] == item_id}
        matrix.append([float(item_rows.get(arm, {}).get("decision_correct", False)) for arm in arms])
    fig, ax = plt.subplots(figsize=(10, max(5, 0.16 * len(item_ids) + 1.5)))
    image = ax.imshow(matrix, vmin=0, vmax=1, cmap="viridis")
    ax.set_xticks(range(len(arms)), arms)
    ax.set_yticks(range(len(item_ids)), item_ids, fontsize=5)
    ax.set_title("Phase 1 item-level audit-correctness map")
    fig.colorbar(image, ax=ax, label="Decision accuracy")
    fig.tight_layout()
    fig.savefig(args.output_dir / "phase1_failure_map.png", dpi=240)
    fig.savefig(args.output_dir / "phase1_failure_map.svg")
    plt.close(fig)
    print(f"rendered figures in {args.output_dir}")


if __name__ == "__main__":
    main()
