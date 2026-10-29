from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scientific_pilot" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_phase1_manifest import build
from check_partition_firewall import check as check_partition_firewall
from score_phase1 import evaluate, score_one
from validate_arm_contract import validate as validate_arm_contract
from validate_candidate_pool import validate as validate_candidates
from validate_phase0 import validate as validate_phase0
from validate_raw_runs import validate as validate_raw_runs


def gold(item_id: str, is_error: bool, *, family: str = "G2_invalid_inference") -> dict:
    return {
        "item_id": item_id,
        "parent_cluster_id": f"cluster-{item_id}",
        "source_id": "minif2f_lean4",
        "gold_error": is_error,
        "severity": "major" if is_error else "clean",
        "error_families": [family] if is_error else [],
        "primary_error_family": family if is_error else "clean",
        "formalizable": True,
        "identifiability": "not_applicable",
        "claim_boundary": "not_applicable",
    }


def run(item_id: str, decision: str, *, arm: str = "A0", status: str = "completed", lean: str = "not_requested", semantic: str = "not_applicable") -> dict:
    return {
        "item_id": item_id,
        "arm_id": arm,
        "replicate": 0,
        "decision": decision,
        "run_status": status,
        "error_families": ["G2_invalid_inference"] if decision == "error" else [],
        "identifiability": "not_applicable",
        "claim_boundary": "not_applicable",
        "lean_status": lean,
        "semantic_alignment": semantic,
        "cost_usd": 0.01,
        "input_tokens": 10,
        "output_tokens": 10,
        "tool_input_tokens": 0,
        "tool_output_tokens": 0,
        "tool_cost_usd": 0.0,
        "tool_wallclock_seconds": 0.0,
        "wallclock_seconds": 1.0,
        "config_sha256": "cfg",
        "prompt_sha256": "prompt",
        "started_at": "2026-01-01T00:00:00Z",
        "finished_at": "2026-01-01T00:00:01Z",
        "tool_receipts": [],
    }


class ScoreFixtureTests(unittest.TestCase):
    def test_tp(self) -> None:
        self.assertTrue(score_one(gold("tp", True), run("tp", "error"))["decision_correct"])

    def test_tn(self) -> None:
        self.assertTrue(score_one(gold("tn", False), run("tn", "clean"))["decision_correct"])

    def test_fp(self) -> None:
        self.assertFalse(score_one(gold("fp", False), run("fp", "error"))["decision_correct"])

    def test_fn(self) -> None:
        self.assertFalse(score_one(gold("fn", True), run("fn", "clean"))["decision_correct"])

    def test_abstain_counts_in_primary_and_not_coverage(self) -> None:
        value = score_one(gold("abstain", True), run("abstain", "inconclusive"))
        self.assertFalse(value["decision_correct"])
        self.assertFalse(value["coverage"])

    def test_malformed_counts_as_failure(self) -> None:
        value = score_one(gold("malformed", False), run("malformed", "clean", status="malformed"))
        self.assertFalse(value["decision_correct"])

    def test_timeout_counts_as_failure(self) -> None:
        value = score_one(gold("timeout", True), run("timeout", "error", status="timeout"))
        self.assertFalse(value["decision_correct"])

    def test_lean_semantic_mismatch_is_separate(self) -> None:
        value = score_one(gold("semantic", True), run("semantic", "error", arm="A6", lean="verified", semantic="misaligned"))
        self.assertEqual(value["lean_status"], "verified")
        self.assertEqual(value["semantic_alignment"], "misaligned")

    def test_lean_tool_error_is_separate(self) -> None:
        value = score_one(gold("tool", True), run("tool", "inconclusive", arm="A6", status="tool_error", lean="tool_error", semantic="unverified"))
        self.assertEqual(value["lean_status"], "tool_error")
        self.assertFalse(value["decision_correct"])

    def test_raw_schema_rejects_missing_tool_receipts(self) -> None:
        schema = json.loads((ROOT / "scientific_pilot" / "config" / "output_schema_v1.json").read_text())
        malformed = run("schema", "error")
        del malformed["tool_receipts"]
        result = validate_raw_runs(schema, [malformed])
        self.assertFalse(result["passed"])
        self.assertIn("tool_receipts", result["errors"][0])

    def test_raw_schedule_rejects_missing_cell(self) -> None:
        schema = json.loads((ROOT / "scientific_pilot" / "config" / "output_schema_v1.json").read_text())
        manifest = {"items": [{"item_id": "schedule"}]}
        result = validate_raw_runs(schema, [run("schedule", "error", arm="A0")], manifest=manifest, arm_ids=["A0", "A1"], replicates=1)
        self.assertFalse(result["passed"])
        self.assertTrue(any("missing scheduled" in error for error in result["errors"]))

    def test_paired_effect(self) -> None:
        golds = [gold("x", True), gold("y", False)]
        runs = [run("x", "clean", arm="A5"), run("x", "error", arm="A6"), run("y", "error", arm="A5"), run("y", "clean", arm="A6")]
        _, _, summary = evaluate(golds, runs, bootstrap_replicates=20)
        self.assertEqual(summary["paired_effects"][0]["n_pairs"], 2)
        self.assertGreater(summary["paired_effects"][0]["effect"], 0)


class ManifestTests(unittest.TestCase):
    def candidates(self) -> list[dict]:
        values = []
        for source in ("minif2f_lean4", "formalphysics_v2_formalscience", "scibench_quantitative", "arc_controlled_claims"):
            for index in range(40):
                is_error = index < 20
                values.append({
                    "item_id": f"{source}::{source}-{index}",
                    "source_id": source,
                    "canonical_id": f"{source}-{index}",
                    "parent_cluster_id": f"{source}-parent-{index}",
                    "source_file_id": f"{source}.json",
                    "paper_or_proof_id": f"{source}-paper-{index}",
                    "gold_error": is_error,
                    "severity": "major" if is_error else "clean",
                    "error_families": ["G2_invalid_inference"] if is_error else [],
                    "formalizable": True,
                    "content_sha256": f"hash-{source}-{index}",
                    "candidate_text": "candidate",
                    "source_content_pointer": "local://source",
                })
        return values

    def test_candidate_pool(self) -> None:
        result = validate_candidates(self.candidates())
        self.assertTrue(result["passed"])

    def test_deterministic_balanced_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory) / "lock.json"
            lock.write_text(json.dumps({"sources": []}), encoding="utf-8")
            target = {"minif2f_lean4": 30, "formalphysics_v2_formalscience": 30, "scibench_quantitative": 30, "arc_controlled_claims": 30}
            manifest = build(self.candidates(), target, seed="fixed", source_lock=lock)
        self.assertEqual(len(manifest["items"]), 120)
        self.assertEqual(sum(row["gold_error"] for row in manifest["items"]), 60)

    def test_blocked_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory) / "lock.json"
            lock.write_text(json.dumps({"sources": []}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not eligible"):
                build(
                    self.candidates(),
                    {"formalphysics_v2_formalscience": 30},
                    seed="fixed",
                    source_lock=lock,
                    allowed_sources=set(),
                )

    def test_phase0_validator_refuses_blocked_source(self) -> None:
        result = validate_phase0(ROOT, strict=True)
        self.assertFalse(result["passed"])
        self.assertTrue(any("blocked" in error for error in result["errors"]))

    def test_partition_firewall_detects_parent_overlap(self) -> None:
        shared = {"item_id": "a", "canonical_id": "c", "parent_cluster_id": "same-parent", "source_file_id": "f", "paper_or_proof_id": "p"}
        result = check_partition_firewall({"purpose": "development_pilot_not_sealed", "items": [shared]}, {"purpose": "sealed_evaluation", "items": [{**shared, "item_id": "b", "canonical_id": "d"}]})
        self.assertFalse(result["passed"])
        self.assertIn("parent_cluster_id", result["overlaps"])

    def test_arm_contract_has_matched_lean_deltas(self) -> None:
        arms = json.loads((ROOT / "scientific_pilot" / "config" / "arms_v1.json").read_text())
        result = validate_arm_contract(arms)
        self.assertTrue(result["passed"], result["errors"])


if __name__ == "__main__":
    unittest.main()
