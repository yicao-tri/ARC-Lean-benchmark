#!/usr/bin/env python3
"""Capture non-confidential FormalPhysics F0 technical evidence on the experiment host.

This tool records observed failures rather than manufacturing a successful
receipt. It deliberately leaves authorization content and raw corpus text out
of its outputs. Run it twice from distinct clean FSLean/evaluation worktrees.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pilot_common import load_json, sha256_file, write_json


def run(argv: list[str], cwd: Path | None = None) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    began = time.monotonic()
    try:
        result = subprocess.run(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        return {
            "argv": argv,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "started_at": started,
            "elapsed_seconds": round(time.monotonic() - began, 6),
        }
    except FileNotFoundError as exc:
        return {
            "argv": argv,
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
            "started_at": started,
            "elapsed_seconds": round(time.monotonic() - began, 6),
        }


def successful_stdout(record: dict[str, Any]) -> str | None:
    return str(record["stdout"]).strip() if record.get("returncode") == 0 else None


def directory_fingerprint(root: Path) -> str | None:
    """Hash tracked-looking inputs, excluding generated Lean build state."""
    if not root.is_dir():
        return None
    digest = hashlib.sha256()
    excluded = {".git", ".lake", "build", "__pycache__"}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in excluded for part in relative.parts) or not path.is_file():
            continue
        digest.update(str(relative).encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256_file(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def worktree_fingerprint(root: Path) -> str | None:
    """Record a privacy-preserving identity for a particular clean checkout."""
    if not root.exists():
        return None
    return hashlib.sha256(str(root.resolve()).encode("utf-8")).hexdigest()


def file_record(root: Path, relative: str) -> dict[str, Any]:
    path = root / relative
    return {"exists": path.is_file(), "sha256": sha256_file(path) if path.is_file() else None, "bytes": path.stat().st_size if path.is_file() else None}


def source_identity(root: Path, dataset_relative: str) -> dict[str, Any]:
    commands = {
        "origin": run(["git", "remote", "get-url", "origin"], root),
        "commit": run(["git", "rev-parse", "HEAD"], root),
        "tree": run(["git", "rev-parse", "HEAD^{tree}"], root),
        "status": run(["git", "status", "--porcelain"], root),
        "submodules": run(["git", "submodule", "status", "--recursive"], root),
        "blob": run(["git", "rev-parse", f"HEAD:{dataset_relative}"], root),
    }
    data = file_record(root, dataset_relative)
    parsed_item_count: int | None = None
    parse_error: str | None = None
    if data["exists"]:
        try:
            value = json.loads((root / dataset_relative).read_text(encoding="utf-8"))
            parsed_item_count = len(value) if isinstance(value, list) else None
            if parsed_item_count is None:
                parse_error = "dataset JSON root is not a list"
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            parse_error = str(exc)
    return {
        "schema_version": "arc-leanbench-formalphysics-source-identity-1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "origin_url": successful_stdout(commands["origin"]),
        "source_commit": successful_stdout(commands["commit"]),
        "source_tree": successful_stdout(commands["tree"]),
        "working_tree_clean": commands["status"].get("returncode") == 0 and not bool(successful_stdout(commands["status"])),
        "recursive_submodule_status": commands["submodules"],
        "dataset_path": dataset_relative,
        "dataset_git_blob": successful_stdout(commands["blob"]),
        "dataset_sha256": data["sha256"],
        "dataset_bytes": data["bytes"],
        "parsed_item_count": parsed_item_count,
        "parse_error": parse_error,
        "commands": commands,
    }


def fslean_material(root: Path, *, artifact_kind: str, artifact_id: str, artifact_origin: str, permission_ref: str, custodian: str, archive_sha256: str | None) -> tuple[dict[str, Any], dict[str, Any]]:
    commands = {
        "origin": run(["git", "remote", "get-url", "origin"], root),
        "commit": run(["git", "rev-parse", "HEAD"], root),
        "tree": run(["git", "rev-parse", "HEAD^{tree}"], root),
        "status": run(["git", "status", "--porcelain"], root),
        "lake": run(["lake", "--version"], root),
        "lean": run(["lean", "--version"], root),
        "elan": run(["elan", "--version"], root),
        "mathlib": run(["git", "-C", ".lake/packages/mathlib", "rev-parse", "HEAD"], root),
    }
    toolchain = file_record(root, "lean-toolchain")
    lakefile = file_record(root, "lakefile.lean")
    manifest = file_record(root, "lake-manifest.json")
    git_commit = successful_stdout(commands["commit"])
    identity = {
        "schema_version": "arc-leanbench-formalphysics-fslean-identity-1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "artifact_kind": artifact_kind,
        "artifact_id": artifact_id,
        "origin_or_controlled_artifact_id": artifact_origin,
        "commit_or_archive_sha256": git_commit or archive_sha256,
        "license_or_permission_reference": permission_ref,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "custodian": custodian,
        "working_tree_clean": commands["status"].get("returncode") == 0 and not bool(successful_stdout(commands["status"])),
        "tree_fingerprint": directory_fingerprint(root),
        "commands": commands,
    }
    environment = {
        "schema_version": "arc-leanbench-formalphysics-environment-lock-1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "environment_id": artifact_id,
        "lean_toolchain": (root / "lean-toolchain").read_text(encoding="utf-8").strip() if toolchain["exists"] else None,
        "lakefile_sha256": lakefile["sha256"],
        "lake_manifest_sha256": manifest["sha256"],
        "lean_version": successful_stdout(commands["lean"]),
        "lake_version": successful_stdout(commands["lake"]),
        "elan_version": successful_stdout(commands["elan"]),
        "mathlib_revision": successful_stdout(commands["mathlib"]),
        "dependency_lock_sha256": manifest["sha256"],
        "files": {"lean-toolchain": toolchain, "lakefile.lean": lakefile, "lake-manifest.json": manifest},
    }
    return identity, environment


def build_receipt(root: Path, *, worktree_id: str, run_build: bool) -> dict[str, Any]:
    record = run(["lake", "build"], root) if run_build else {"argv": ["lake", "build"], "returncode": None, "stdout": "", "stderr": "not requested", "elapsed_seconds": 0.0}
    return {
        "schema_version": "arc-leanbench-formalphysics-clean-build-1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "worktree_id": worktree_id,
        "argv": record["argv"],
        "cwd_fingerprint": worktree_fingerprint(root),
        "environment_lock_sha256": None,
        "returncode": record["returncode"],
        "stdout_sha256": hashlib.sha256(str(record["stdout"]).encode("utf-8")).hexdigest(),
        "stderr_sha256": hashlib.sha256(str(record["stderr"]).encode("utf-8")).hexdigest(),
        "elapsed_seconds": record["elapsed_seconds"],
        "platform": platform.platform(),
        "stdout": record["stdout"],
        "stderr": record["stderr"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-lock", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--fslean-root", type=Path, required=True)
    parser.add_argument("--worktree-id", required=True)
    parser.add_argument("--source-identity-output", type=Path, required=True)
    parser.add_argument("--fslean-identity-output", type=Path, required=True)
    parser.add_argument("--environment-lock-output", type=Path, required=True)
    parser.add_argument("--build-receipt-output", type=Path, required=True)
    parser.add_argument("--run-build", action="store_true")
    parser.add_argument("--fslean-artifact-kind", choices=("upstream_fslean", "compatibility_environment"), default="compatibility_environment")
    parser.add_argument("--fslean-artifact-id", default="formalphysics_eval_env_v1")
    parser.add_argument("--fslean-origin-or-controlled-artifact-id", required=True)
    parser.add_argument("--fslean-license-or-permission-reference", required=True)
    parser.add_argument("--fslean-custodian", required=True)
    parser.add_argument("--fslean-archive-sha256")
    args = parser.parse_args()

    lock = load_json(args.source_lock)
    source = next((row for row in lock.get("sources", []) if row.get("source_id") == "formalphysics_v2_formalscience"), None)
    if source is None:
        raise SystemExit("source lock has no formalphysics_v2_formalscience record")
    dataset_relative = str(source["selection_pool"])
    source_value = source_identity(args.source_root, dataset_relative)
    fslean_value, environment = fslean_material(
        args.fslean_root,
        artifact_kind=args.fslean_artifact_kind,
        artifact_id=args.fslean_artifact_id,
        artifact_origin=args.fslean_origin_or_controlled_artifact_id,
        permission_ref=args.fslean_license_or_permission_reference,
        custodian=args.fslean_custodian,
        archive_sha256=args.fslean_archive_sha256,
    )
    write_json(args.source_identity_output, source_value)
    write_json(args.fslean_identity_output, fslean_value)
    write_json(args.environment_lock_output, environment)
    build = build_receipt(args.fslean_root, worktree_id=args.worktree_id, run_build=args.run_build)
    build["environment_lock_sha256"] = sha256_file(args.environment_lock_output)
    for path, value in ((args.build_receipt_output, build),):
        write_json(path, value)
    failed = not (
        source_value.get("source_commit") == source.get("commit")
        and source_value.get("working_tree_clean")
        and source_value.get("dataset_sha256")
        and fslean_value.get("commit_or_archive_sha256")
        and fslean_value.get("working_tree_clean")
        and build.get("returncode") == 0
    )
    print(f"wrote FormalPhysics F0 technical receipts; build_returncode={build['returncode']}")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
