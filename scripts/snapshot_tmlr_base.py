#!/usr/bin/env python3
"""Record hashes for the author-kit directory that submissions must not edit."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "tmlr_do_not_modify"


def main() -> None:
    files = []
    for path in sorted(BASE.rglob("*")):
        if path.is_file() and "/_site/" not in str(path) and "/.jekyll-cache/" not in str(path):
            files.append({
                "path": str(path.relative_to(ROOT)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
            })
    output = ROOT / "evidence/tmlr_do_not_modify_manifest.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps({"schema_version": "tmlr-base-manifest-1", "files": files}, indent=2, sort_keys=True) + "\n")
    print(f"Recorded {len(files)} protected author-kit files in {output}")


if __name__ == "__main__":
    main()

