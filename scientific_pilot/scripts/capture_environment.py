#!/usr/bin/env python3
"""Capture local source, dependency, and Lean build receipts without fabrication.

Run this on the experiment host after the repositories named in sources.lock
are present.  It records command output and failures; a missing `lake` or a
failed build stays a failure rather than being replaced with a user assertion.
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pilot_common import load_json, sha256_file, write_json


def command(argv: list[str], cwd: Path | None = None) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    try:
        completed = subprocess.run(argv, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        return {
            "argv": argv,
            "cwd": str(cwd) if cwd else None,
            "started_at": started,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    except FileNotFoundError as exc:
        return {"argv": argv, "cwd": str(cwd) if cwd else None, "started_at": started, "returncode": None, "stdout": "", "stderr": str(exc)}


def source_receipt(source: dict[str, Any], *, run_build: bool) -> dict[str, Any]:
    configured_path = str(source["local_path"])
    resolved_path = os.path.expandvars(configured_path)
    root = Path(resolved_path)
    receipt: dict[str, Any] = {
        "source_id": source["source_id"],
        "configured_path": configured_path,
        "path": str(root),
        "unresolved_path_variables": "${" in resolved_path or "$" in resolved_path,
        "exists": root.exists(),
        "commands": [],
        "files": {},
        "build": None,
    }
    if not root.exists():
        return receipt
    receipt["commands"].append(command(["git", "rev-parse", "HEAD"], root))
    receipt["commands"].append(command(["git", "status", "--short"], root))
    pool = source.get("selection_pool")
    pools = pool if isinstance(pool, list) else [pool] if pool else []
    for relative in pools:
        target = root / relative
        receipt["files"][relative] = {"exists": target.exists(), "sha256": sha256_file(target) if target.exists() else None}
    toolchain = root / "lean-toolchain"
    manifest = root / "lake-manifest.json"
    receipt["files"]["lean-toolchain"] = {"exists": toolchain.exists(), "sha256": sha256_file(toolchain) if toolchain.exists() else None}
    receipt["files"]["lake-manifest.json"] = {"exists": manifest.exists(), "sha256": sha256_file(manifest) if manifest.exists() else None}
    receipt["toolchain_command"] = command(["lake", "--version"], root) if (root / "lakefile.lean").exists() else None
    if run_build and (root / "lakefile.lean").exists():
        receipt["build"] = command(["lake", "build"], root)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-lock", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-build", action="store_true")
    parser.add_argument("--include-excluded", action="store_true", help="also inspect sources not selected for Phase 1")
    args = parser.parse_args()
    lock = load_json(args.source_lock)
    receipt = {
        "schema_version": "arc-leanbench-environment-receipt-1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "host": {"platform": platform.platform(), "python": sys.version, "lake_on_path": shutil.which("lake"), "lean_on_path": shutil.which("lean")},
        "source_lock_sha256": sha256_file(args.source_lock),
        "run_build": args.run_build,
        "sources": [
            source_receipt(source, run_build=args.run_build)
            for source in lock["sources"]
            if args.include_excluded or "EXCLUDED" not in source.get("phase1_use", "")
        ],
    }
    write_json(args.output, receipt)
    failures = [source["source_id"] for source in receipt["sources"] if not source["exists"]]
    failed_builds = [source["source_id"] for source in receipt["sources"] if source["build"] and source["build"]["returncode"] != 0]
    print(f"wrote {args.output}; missing={failures}; failed_builds={failed_builds}")
    raise SystemExit(1 if failures or failed_builds else 0)


if __name__ == "__main__":
    main()
