#!/usr/bin/env python3
"""Verify the non-confidential FormalPhysics F0 source-gate evidence bundle.

The verifier intentionally validates evidence structure and cryptographic
bindings. It does not certify that a permission grant is genuine; that remains
an independent human-review decision using the controlled original document.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from pilot_common import load_json, read_jsonl, sha256_file, write_json


FORMAL_SOURCE = "formalphysics_v2_formalscience"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
GIT_OR_SHA256 = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


def need(mapping: dict[str, Any], fields: list[str], label: str, errors: list[str]) -> None:
    for field in fields:
        value = mapping.get(field)
        if value is None or value == "":
            errors.append(f"{label} missing {field}")


def valid_sha(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256.fullmatch(value))


def valid_git_or_sha(value: Any) -> bool:
    return isinstance(value, str) and bool(GIT_OR_SHA256.fullmatch(value))


def load_object(path: Path, label: str, errors: list[str]) -> dict[str, Any]:
    try:
        value = load_json(path)
    except (OSError, ValueError) as exc:
        errors.append(f"cannot load {label}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label} must be a JSON object")
        return {}
    return value


def verification(
    *,
    source_lock_path: Path,
    authorization_path: Path,
    source_identity_path: Path,
    fslean_identity_path: Path,
    environment_lock_path: Path,
    build_a_path: Path,
    build_b_path: Path,
    corpus_path: Path,
    adapter_path: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    lock = load_object(source_lock_path, "source lock", errors)
    authorization = load_object(authorization_path, "authorization inventory", errors)
    source = load_object(source_identity_path, "source identity", errors)
    fslean = load_object(fslean_identity_path, "FSLean identity", errors)
    environment = load_object(environment_lock_path, "environment lock", errors)
    build_a = load_object(build_a_path, "clean build A", errors)
    build_b = load_object(build_b_path, "clean build B", errors)
    adapter = load_object(adapter_path, "adapter review", errors)
    manifest = load_object(manifest_path, "manifest", errors)
    try:
        corpus = read_jsonl(corpus_path)
    except (OSError, ValueError) as exc:
        errors.append(f"cannot load corpus receipts: {exc}")
        corpus = []

    locked = next((entry for entry in lock.get("sources", []) if entry.get("source_id") == FORMAL_SOURCE), None)
    if locked is None:
        errors.append("source lock lacks formalphysics_v2_formalscience")
        locked = {}
    if "BLOCKED" in str(locked.get("phase1_use", "")):
        warnings.append("pre-clearance source lock still blocks FormalPhysics; create a reviewed candidate lock from this PASS receipt and rerun this verifier before a Phase 0 freeze")

    need(authorization, ["source_id", "dataset_identifier", "document_sha256", "issued_on", "issuer_role", "custodian", "authorized_evaluator", "permitted_uses", "redistribution_disposition", "attribution_requirements", "conditions_or_expiry"], "authorization inventory", errors)
    if authorization.get("source_id") != FORMAL_SOURCE:
        errors.append("authorization inventory has wrong source_id")
    if "formal_qa_data.json" not in str(authorization.get("dataset_identifier", "")):
        errors.append("authorization inventory does not identify the exact FormalPhysics v2 dataset")
    if not valid_sha(authorization.get("document_sha256")):
        errors.append("authorization inventory document_sha256 is not a SHA-256")
    uses = set(authorization.get("permitted_uses", [])) if isinstance(authorization.get("permitted_uses"), list) else set()
    missing_uses = {"research", "automated_llm_evaluation", "controlled_audit_variants"} - uses
    if missing_uses:
        errors.append(f"authorization inventory omits permitted uses: {sorted(missing_uses)}")
    if authorization.get("redistribution_disposition") not in {"allowed", "controlled_access_only", "prohibited"}:
        errors.append("authorization inventory must declare redistribution_disposition")
    elif authorization.get("redistribution_disposition") != "allowed":
        warnings.append("FormalPhysics raw material is controlled; public outputs must contain only permitted metadata/aggregates")

    need(source, ["origin_url", "source_commit", "source_tree", "working_tree_clean", "recursive_submodule_status", "dataset_path", "dataset_git_blob", "dataset_sha256", "dataset_bytes", "parsed_item_count"], "source identity", errors)
    if source.get("source_commit") != locked.get("commit"):
        errors.append("FormalScience commit does not match source lock")
    if not valid_git_or_sha(source.get("source_tree")) or len(str(source.get("source_tree"))) != 40:
        errors.append("source identity source_tree is not a Git tree SHA")
    if not source.get("working_tree_clean"):
        errors.append("FormalScience source clone is not clean")
    if source.get("dataset_path") != locked.get("selection_pool"):
        errors.append("source identity does not identify the locked formal_qa_data.json pool")
    expected_blob = locked.get("selection_pool_git_blob")
    if expected_blob and source.get("dataset_git_blob") != expected_blob:
        errors.append("FormalPhysics dataset Git blob does not match the locked source identity")
    if not valid_git_or_sha(source.get("dataset_git_blob")) or len(str(source.get("dataset_git_blob"))) != 40:
        errors.append("source identity dataset_git_blob is not a Git blob SHA")
    if not valid_sha(source.get("dataset_sha256")):
        errors.append("source identity dataset_sha256 is not a SHA-256")
    if not isinstance(source.get("dataset_bytes"), int) or source.get("dataset_bytes", 0) <= 0:
        errors.append("source identity lacks positive dataset byte count")
    if not isinstance(source.get("parsed_item_count"), int) or source.get("parsed_item_count", 0) < 30:
        errors.append("source identity has fewer than 30 parseable records")
    if not isinstance(source.get("recursive_submodule_status"), dict) or source["recursive_submodule_status"].get("returncode") != 0:
        errors.append("source identity lacks successful recursive submodule capture")

    need(fslean, ["artifact_kind", "artifact_id", "origin_or_controlled_artifact_id", "commit_or_archive_sha256", "license_or_permission_reference", "retrieved_at", "custodian"], "FSLean identity", errors)
    if fslean.get("artifact_kind") not in {"upstream_fslean", "compatibility_environment"}:
        errors.append("FSLean artifact_kind must identify upstream_fslean or compatibility_environment")
    if not fslean.get("working_tree_clean"):
        errors.append("FSLean/evaluation environment is not clean")
    if not valid_git_or_sha(fslean.get("commit_or_archive_sha256")):
        errors.append("FSLean identity needs a commit or archive SHA")
    if fslean.get("artifact_kind") == "compatibility_environment" and "eval" not in str(fslean.get("artifact_id", "")).lower():
        errors.append("compatibility environment must be explicitly named as an evaluation environment")

    need(environment, ["environment_id", "lean_toolchain", "lakefile_sha256", "lake_manifest_sha256", "lean_version", "lake_version", "elan_version", "mathlib_revision", "dependency_lock_sha256"], "environment lock", errors)
    if environment.get("environment_id") != fslean.get("artifact_id"):
        errors.append("environment lock is not bound to the FSLean/evaluation artifact")
    for field in ("lakefile_sha256", "lake_manifest_sha256", "dependency_lock_sha256"):
        if not valid_sha(environment.get(field)):
            errors.append(f"environment lock {field} is not a SHA-256")
    if "4.28" in str(environment.get("lean_toolchain")):
        errors.append("FormalPhysics environment appears to be PhysLib's Lean 4.28 environment, not its separately captured environment")

    environment_sha = sha256_file(environment_lock_path)
    for label, build in (("A", build_a), ("B", build_b)):
        need(build, ["worktree_id", "argv", "cwd_fingerprint", "environment_lock_sha256", "returncode", "stdout_sha256", "stderr_sha256", "elapsed_seconds", "platform"], f"clean build {label}", errors)
        if build.get("argv") != ["lake", "build"]:
            errors.append(f"clean build {label} must record exactly ['lake', 'build']")
        if build.get("returncode") != 0:
            errors.append(f"clean build {label} did not succeed")
        if build.get("environment_lock_sha256") != environment_sha:
            errors.append(f"clean build {label} is not bound to the environment lock")
        for field in ("cwd_fingerprint", "stdout_sha256", "stderr_sha256"):
            if not valid_sha(build.get(field)):
                errors.append(f"clean build {label} {field} is not a SHA-256")
    if build_a.get("worktree_id") == build_b.get("worktree_id"):
        errors.append("clean build A and B use the same worktree_id")
    if build_a.get("cwd_fingerprint") == build_b.get("cwd_fingerprint"):
        errors.append("clean build A and B need distinct clean worktree fingerprints")

    need(adapter, ["adapter_sha256", "semantic_neutrality_reviewed", "reviewer", "reviewed_item_count", "alignment_records_reference", "forbidden_changes_absent"], "adapter review", errors)
    if not valid_sha(adapter.get("adapter_sha256")):
        errors.append("adapter review adapter_sha256 is not a SHA-256")
    if not adapter.get("semantic_neutrality_reviewed") or not adapter.get("forbidden_changes_absent"):
        errors.append("adapter has not passed its semantic-boundary review")
    if not isinstance(adapter.get("reviewed_item_count"), int) or adapter.get("reviewed_item_count", 0) < 10:
        errors.append("adapter review covers fewer than 10 selected items")

    items = [item for item in manifest.get("items", []) if item.get("source_id") == FORMAL_SOURCE]
    selected_ids = {str(item.get("item_id")) for item in items}
    if len(items) != 30 or len(selected_ids) != 30:
        errors.append("manifest must contain exactly 30 distinct FormalPhysics items")
    by_id: dict[str, list[dict[str, Any]]] = {}
    for row in corpus:
        if row.get("item_id") in selected_ids:
            by_id.setdefault(str(row["item_id"]), []).append(row)
    missing = selected_ids - set(by_id)
    duplicated = {item_id for item_id, rows in by_id.items() if len(rows) != 1}
    if missing:
        errors.append(f"corpus receipts missing selected items: {sorted(missing)[:5]}")
    if duplicated:
        errors.append(f"corpus receipts must have exactly one row per selected item: {sorted(duplicated)[:5]}")
    required_corpus = ["item_id", "source_record_sha256", "formal_answer_sha256", "adapter_sha256", "parse_status", "argv", "cwd_fingerprint", "stdout_sha256", "stderr_sha256", "returncode", "lean_status", "contains_sorry", "contains_unresolved_metavariables", "introduced_axioms"]
    for item_id, rows in by_id.items():
        if len(rows) != 1:
            continue
        row = rows[0]
        need(row, required_corpus, f"corpus receipt {item_id}", errors)
        if row.get("parse_status") != "parsed":
            errors.append(f"corpus receipt {item_id} is not parsable")
        if row.get("adapter_sha256") != adapter.get("adapter_sha256"):
            errors.append(f"corpus receipt {item_id} uses an unreviewed adapter")
        if not isinstance(row.get("argv"), list) or row["argv"][:2] != ["lake", "env"] or "lean" not in row["argv"]:
            errors.append(f"corpus receipt {item_id} does not record a lake env lean invocation")
        if row.get("contains_sorry") or row.get("contains_unresolved_metavariables") or row.get("introduced_axioms"):
            errors.append(f"corpus receipt {item_id} contains a prohibited proof escape hatch")
        if row.get("lean_status") == "verified" and row.get("returncode") != 0:
            errors.append(f"corpus receipt {item_id} claims verified without a zero Lean exit code")
        if row.get("lean_status") != "verified" and not row.get("predeclared_formal_failure_reason"):
            errors.append(f"corpus receipt {item_id} has non-verified status without a predeclared failure reason")
        for field in ("source_record_sha256", "formal_answer_sha256", "cwd_fingerprint", "stdout_sha256", "stderr_sha256"):
            if not valid_sha(row.get(field)):
                errors.append(f"corpus receipt {item_id} {field} is not a SHA-256")

    inputs = {
        "source_lock_sha256": sha256_file(source_lock_path),
        "authorization_inventory_sha256": sha256_file(authorization_path),
        "source_identity_sha256": sha256_file(source_identity_path),
        "fslean_identity_sha256": sha256_file(fslean_identity_path),
        "environment_lock_sha256": environment_sha,
        "build_a_sha256": sha256_file(build_a_path),
        "build_b_sha256": sha256_file(build_b_path),
        "corpus_receipts_sha256": sha256_file(corpus_path),
        "adapter_review_sha256": sha256_file(adapter_path),
        "manifest_sha256": sha256_file(manifest_path),
    }
    return {
        "schema_version": "arc-leanbench-formalphysics-source-gate-receipt-1",
        "status": "PASS" if not errors else "FAIL",
        "passed": not errors,
        "source_id": FORMAL_SOURCE,
        **inputs,
        "formalphysics_item_count": len(items),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-lock", type=Path, required=True)
    parser.add_argument("--authorization-inventory", type=Path, required=True)
    parser.add_argument("--source-identity", type=Path, required=True)
    parser.add_argument("--fslean-identity", type=Path, required=True)
    parser.add_argument("--environment-lock", type=Path, required=True)
    parser.add_argument("--build-a", type=Path, required=True)
    parser.add_argument("--build-b", type=Path, required=True)
    parser.add_argument("--corpus-receipts", type=Path, required=True)
    parser.add_argument("--adapter-review", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verification(
        source_lock_path=args.source_lock,
        authorization_path=args.authorization_inventory,
        source_identity_path=args.source_identity,
        fslean_identity_path=args.fslean_identity,
        environment_lock_path=args.environment_lock,
        build_a_path=args.build_a,
        build_b_path=args.build_b,
        corpus_path=args.corpus_receipts,
        adapter_path=args.adapter_review,
        manifest_path=args.manifest,
    )
    write_json(args.output, result)
    print(f"wrote {args.output}: {result['status']}")
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
