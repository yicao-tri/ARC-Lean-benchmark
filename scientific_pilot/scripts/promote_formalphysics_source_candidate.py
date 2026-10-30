#!/usr/bin/env python3
"""Create, never overwrite, a reviewable FormalPhysics-eligible source lock.

The input gate receipt must be a PASS bound to the input source lock. The
result is still only a candidate: the Phase 0 freeze and independent review
remain mandatory.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from pilot_common import load_json, sha256_file, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-lock", type=Path, required=True)
    parser.add_argument("--formalphysics-gate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    lock = load_json(args.source_lock)
    gate = load_json(args.formalphysics_gate)
    lock_sha = sha256_file(args.source_lock)
    if gate.get("status") != "PASS" or gate.get("source_lock_sha256") != lock_sha:
        raise SystemExit("FormalPhysics gate must PASS and bind to this exact pre-clearance source lock")
    source = next((row for row in lock.get("sources", []) if row.get("source_id") == "formalphysics_v2_formalscience"), None)
    if source is None:
        raise SystemExit("source lock lacks formalphysics_v2_formalscience")
    source["phase1_use"] = "eligible_pending_phase0_freeze_and_independent_review"
    source["formalphysics_preclearance_gate_sha256"] = sha256_file(args.formalphysics_gate)
    source["formalphysics_preclearance_manifest_sha256"] = gate.get("manifest_sha256")
    lock["status"] = "CANDIDATE_FORMALPHYSICS_GATE_PASSED_NOT_PHASE0_FROZEN"
    lock["derived_from_source_lock_sha256"] = lock_sha
    write_json(args.output, lock)
    print(f"wrote candidate source lock {args.output}; rerun the FormalPhysics verifier against it before any Phase 0 freeze")


if __name__ == "__main__":
    main()
