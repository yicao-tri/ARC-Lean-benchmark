#!/usr/bin/env python3
"""Capture a local model endpoint identity without claiming it is frozen yet."""
from __future__ import annotations

import argparse
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from pilot_common import load_json, sha256_bytes, write_json


def invoke(argv: list[str]) -> dict:
    try:
        result = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        return {"argv": argv, "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
    except FileNotFoundError as exc:
        return {"argv": argv, "returncode": None, "stdout": "", "stderr": str(exc)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-lock", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    lock = load_json(args.model_lock)
    requested = lock["requested_model"]
    output = {
        "schema_version": "arc-leanbench-model-receipt-1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "requested_model": requested,
        "ollama_on_path": shutil.which("ollama"),
        "runtime": invoke(["ollama", "--version"]),
        "model_list": invoke(["ollama", "list"]),
        "model_verbose": invoke(["ollama", "show", requested, "--verbose"]),
        "model_show": invoke(["ollama", "show", requested, "--modelfile"]),
    }
    output["model_show_sha256"] = sha256_bytes(output["model_show"]["stdout"].encode()) if output["model_show"]["returncode"] == 0 else None
    output["model_verbose_sha256"] = sha256_bytes(output["model_verbose"]["stdout"].encode()) if output["model_verbose"]["returncode"] == 0 else None
    write_json(args.output, output)
    success = output["runtime"]["returncode"] == 0 and output["model_show"]["returncode"] == 0 and output["model_verbose"]["returncode"] == 0
    print(f"wrote {args.output}; captured={success}")
    raise SystemExit(0 if success else 1)


if __name__ == "__main__":
    main()
