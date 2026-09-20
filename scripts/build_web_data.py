#!/usr/bin/env python3
"""Build browser-safe, claim-bounded data from frozen ARC-Lean artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "data/frozen"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    with (FROZEN / "icml_two_regime_pilot_v0.4.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    public = json.loads((FROZEN / "public_deep_case_pilot_v0.1.json").read_text())
    seed = json.loads((FROZEN / "claim_closure_seed_v0.1.json").read_text())
    wanted = [
        "H1-POISSON-TRANSPORT-CLOSURE",
        "POLETAYEV-2022-PROCESSING-DEFECT-CAUSE",
        "GUAN-2026-PATH-ENTROPY-ALONE-UNIVERSAL",
    ]
    cases = []
    pool = {item["claim_id"]: item for item in [*seed["claims"], *public["claims"]]}
    for case_id in wanted:
        item = pool[case_id]
        evidence_summary = item.get("empirical_decision", {}).get("evidence_summary")
        if not evidence_summary:
            evidence_summary = (
                f"Observed: {', '.join(item['observed_variables'])}. "
                f"Still required: {', '.join(item['required_measurements'][len(item['observed_variables']):])}."
            )
        closure_items = item.get("closure_experiments") or []
        closure = closure_items[0].get("intervention_or_condition") if closure_items else None
        if not closure:
            closure = "; ".join(item.get("closure_measurements", [])) or "No additional closure experiment is required."
        cases.append(
            {
                "id": item["claim_id"],
                "title": item["title"],
                "claim": item["claim_text"],
                "scope": item["query_scope"],
                "decision": item["expected"]["decision"],
                "identifiability": item["expected"]["identifiability"],
                "ceiling": item["expected"]["promotion_ceiling"],
                "evidence_summary": evidence_summary,
                "mechanisms": item["competing_mechanisms"][:2],
                "closure": closure,
                "formal": item.get("formal_receipt", {}).get("status", "not_applicable"),
            }
        )
    retrieval = json.loads((FROZEN / "public_micro_rag_pilot_v0.1.json").read_text())
    payload = {
        "schema_version": "arc-lean-beyond-pdf-data-0.1",
        "label_status": "system_deep_case_not_expert_gold",
        "scope_warning": "Pilot estimates are descriptive; they do not estimate sealed-test generalization.",
        "table": rows,
        "cases": cases,
        "retrieval": retrieval["retrieval_metrics"],
        "source_hashes": {
            path.name: sha256(path)
            for path in sorted(FROZEN.iterdir())
            if path.is_file()
        },
    }
    body = "window.ARC_DATA = " + json.dumps(payload, indent=2, sort_keys=True) + ";\n"
    outputs = [
        ROOT / "site/assets/arc-data.js",
        ROOT / "web/assets/arc-data.js",
        ROOT / "submission_folder/assets/html/submission/arc-data.js",
    ]
    for output in outputs:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(body)
    print(json.dumps({"cases": len(cases), "methods": len(rows), "outputs": len(outputs)}))


if __name__ == "__main__":
    main()
