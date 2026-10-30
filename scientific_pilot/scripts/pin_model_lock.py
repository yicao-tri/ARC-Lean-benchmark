#!/usr/bin/env python3
"""Create a candidate immutable model lock from a captured local receipt."""
from __future__ import annotations

import argparse
from pathlib import Path

from pilot_common import load_json, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-lock", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--full-model-digest", required=True, help="immutable full weights/content digest from the local model store")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    lock, receipt = load_json(args.model_lock), load_json(args.receipt)
    if receipt.get("requested_model") != lock.get("requested_model") or receipt.get("model_show", {}).get("returncode") != 0:
        raise SystemExit("receipt does not prove inspection of the requested model")
    lock.update({
        "status": "CANDIDATE_LOCAL_MODEL_CAPTURED_NOT_FROZEN",
        "model_digest": args.full_model_digest,
        "model_file_sha256": receipt["model_show_sha256"],
        "model_verbose_sha256": receipt.get("model_verbose_sha256"),
        "runtime_version": receipt.get("runtime", {}).get("stdout", "").strip(),
        "captured_at": receipt.get("captured_at"),
    })
    write_json(args.output, lock)
    print(f"wrote candidate model lock {args.output}; review and mark FROZEN only in the committed Phase 0 lock")


if __name__ == "__main__":
    main()
