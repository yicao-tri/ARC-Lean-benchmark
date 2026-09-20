from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReleaseTests(unittest.TestCase):
    def test_frozen_table_has_expected_rows_and_primary_columns(self) -> None:
        with (ROOT / "data/frozen/icml_two_regime_pilot_v0.4.csv").open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 16)
        self.assertIn("ARC w/o promotion ceiling", {row["method"] for row in rows})
        self.assertIn("public_overclaim_rate", rows[0])

    def test_ceiling_ablation_isolated(self) -> None:
        for name, overclaim in [
            ("seed_promotion_ceiling_ablation_v0.1.json", 3 / 7),
            ("public_promotion_ceiling_ablation_v0.1.json", 1 / 8),
        ]:
            payload = json.loads((ROOT / "data/frozen" / name).read_text())
            metrics = payload["metrics"]
            self.assertEqual(metrics["identifiability_exact_match"], 1)
            self.assertEqual(metrics["decision_exact_match"], 1)
            self.assertEqual(metrics["overclaim_rate"], overclaim)

    def test_micro_rag_retrieval_and_joint_separate(self) -> None:
        payload = json.loads((ROOT / "data/frozen/public_micro_rag_pilot_v0.1.json").read_text())
        self.assertEqual(payload["retrieval_metrics"]["source_recall_at_4"], 1)
        self.assertTrue(all(item["joint_exact_match"] == 0 for item in payload["metrics"].values()))

    def test_submission_is_anonymous_and_excludes_companion_case_names(self) -> None:
        text = (ROOT / "submission_folder/submission.md").read_text().lower()
        self.assertIn("name: anonymous", text)
        self.assertNotIn("yicao", text)
        self.assertNotIn("nasicon", text)
        self.assertNotIn("nleis", text)

    def test_project_site_carries_scope_warning(self) -> None:
        text = (ROOT / "site/index.html").read_text()
        self.assertIn("not independent expert gold", text)
        self.assertIn("400 claims / 200 papers", text)


if __name__ == "__main__":
    unittest.main()
