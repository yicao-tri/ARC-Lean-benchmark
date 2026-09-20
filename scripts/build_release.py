#!/usr/bin/env python3
"""Build the static project page, evidence manifest, and TMLR submission ZIP."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(script: str) -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT, check=True)


def copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def main() -> None:
    run("build_web_data.py")
    run("render_web_figures.py")

    for name in ["arc.css", "arc.js"]:
        copy_file(ROOT / "web/assets" / name, ROOT / "site/assets" / name)
        copy_file(ROOT / "web/assets" / name, ROOT / "submission_folder/assets/html/submission" / name)

    site_artifacts = ROOT / "site/artifacts"
    site_artifacts.mkdir(parents=True, exist_ok=True)
    publish = [
        "icml_two_regime_pilot_v0.4.csv",
        "public_micro_rag_pilot_v0.1.json",
        "seed_promotion_ceiling_ablation_v0.1.json",
        "public_promotion_ceiling_ablation_v0.1.json",
        "path_entropy_lean_receipt.json",
    ]
    for name in publish:
        copy_file(ROOT / "data/frozen" / name, site_artifacts / name)

    sources = sorted(path for path in (ROOT / "data/frozen").iterdir() if path.is_file())
    outputs = sorted(
        [ROOT / "site/index.html", ROOT / "site/assets/arc.css", ROOT / "site/assets/arc.js"]
        + list((ROOT / "site/assets").glob("*.svg"))
        + list((ROOT / "submission_folder/assets/img/submission").glob("*.svg"))
    )
    provenance = {
        "schema_version": "arc-lean-web-provenance-0.1",
        "source_artifacts": [{"path": str(path.relative_to(ROOT)), "sha256": digest(path), "bytes": path.stat().st_size} for path in sources],
        "web_outputs": [{"path": str(path.relative_to(ROOT)), "sha256": digest(path), "bytes": path.stat().st_size} for path in outputs],
        "supported_claims": [
            "the website values reproduce the frozen two-regime pilot artifacts",
            "retrieval recall and audit performance are reported as separate quantities",
            "the ceiling ablation changes only the promotion rule while reference identifiability and decision remain fixed",
        ],
        "does_not_support": [
            "sealed-test generalization",
            "independent expert accuracy",
            "population-level inference or stochastic uncertainty",
            "empirical truth of a material mechanism from a Lean receipt",
        ],
    }
    (ROOT / "evidence").mkdir(exist_ok=True)
    manifest = json.dumps(provenance, indent=2, sort_keys=True) + "\n"
    (ROOT / "evidence/provenance.json").write_text(manifest)
    (site_artifacts / "provenance.json").write_text(manifest)

    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    archive = dist / "submission_folder.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as handle:
        for path in sorted((ROOT / "submission_folder").rglob("*")):
            if path.name != ".DS_Store":
                handle.write(path, path.relative_to(ROOT))
    print(json.dumps({"submission_zip": str(archive), "sha256": digest(archive), "source_count": len(sources), "output_count": len(outputs)}, indent=2))


if __name__ == "__main__":
    main()
