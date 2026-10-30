#!/usr/bin/env python3
"""Ensure primary Lean contrasts differ only in the declared Lean endpoint."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from pilot_common import load_json, sha256_file, write_json


def validate(contract: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    arms = {arm["id"]: arm for arm in contract.get("arms", [])}
    for expected in ("A0", "A3", "A5", "A6"):
        if expected not in arms:
            errors.append(f"missing primary-contrast arm {expected}")
    if errors:
        return {"status": "FAIL", "passed": False, "errors": errors}
    def module_delta(left: str, right: str) -> tuple[set[str], set[str]]:
        return set(arms[left]["modules"]) - set(arms[right]["modules"]), set(arms[right]["modules"]) - set(arms[left]["modules"])
    added, removed = module_delta("A3", "A0")
    if added != {"lean_formal_check"} or removed:
        errors.append(f"A3 vs A0 must add only lean_formal_check; added={sorted(added)}, removed={sorted(removed)}")
    added, removed = module_delta("A6", "A5")
    if added != {"lean_formal_check"} or removed:
        errors.append(f"A6 vs A5 must add only lean_formal_check; added={sorted(added)}, removed={sorted(removed)}")
    for key in ("temperature", "top_p", "max_output_tokens", "max_wallclock_seconds", "max_tool_calls", "seeds", "evidence_visibility"):
        if key not in contract.get("shared_contract", {}):
            errors.append(f"shared contract lacks {key}")
    return {"status": "PASS" if not errors else "FAIL", "passed": not errors, "errors": errors}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arms", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(load_json(args.arms))
    result["arms_sha256"] = sha256_file(args.arms)
    if args.output:
        write_json(args.output, result)
    print(result)
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
