#!/usr/bin/env python3
"""Validate TMLR layout, anonymity, local assets, hashes, and release inventory."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        ERRORS.append(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.assets: list[str] = []
        self.anchors: set[str] = set()
        self.href_anchors: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.anchors.add(values["id"] or "")
        if tag in {"script", "img", "link"}:
            candidate = values.get("src") or values.get("href")
            if candidate:
                self.assets.append(candidate)
        if tag == "a" and (values.get("href") or "").startswith("#"):
            self.href_anchors.add((values.get("href") or "")[1:])


def check_site() -> None:
    page = ROOT / "site/index.html"
    require(page.is_file(), "site/index.html is missing")
    parser = AssetParser()
    parser.feed(page.read_text())
    for asset in parser.assets:
        if asset.startswith(("http://", "https://", "//")):
            ERRORS.append(f"site uses external runtime asset: {asset}")
        elif not (ROOT / "site" / asset).is_file():
            ERRORS.append(f"site asset is missing: {asset}")
    require(parser.href_anchors <= parser.anchors, f"broken site anchors: {sorted(parser.href_anchors - parser.anchors)}")
    require({"problem", "method", "demo", "results", "lean", "benchmark", "roadmap", "artifacts"} <= parser.anchors, "required narrative sections are missing")


def check_submission() -> None:
    submission = ROOT / "submission_folder/submission.md"
    text = submission.read_text()
    require(text.startswith("---\n"), "submission front matter is missing")
    require("layout: distill" in text, "submission layout must be distill")
    require("name: Anonymous" in text, "review submission must be anonymous")
    lowered = text.lower()
    for forbidden in ["yicao", "github.com/yicao", "nasicon", "nleis"]:
        require(forbidden not in lowered, f"submission leaks identity or companion-case term: {forbidden}")
    iframe = ROOT / "submission_folder/assets/html/submission/arc_audit_demo.html"
    require(iframe.is_file(), "interactive submission figure is missing")
    for name in ["public_pilot_map.svg", "ceiling_ablation.svg"]:
        require((ROOT / "submission_folder/assets/img/submission" / name).is_file(), f"submission figure missing: {name}")
    bib = (ROOT / "submission_folder/assets/bibliography/submission.bib").read_text()
    cite_keys = set(re.findall(r'<d-cite key="([^"]+)"', text))
    bib_keys = set(re.findall(r"@[A-Za-z]+\{([^,]+),", bib))
    require(cite_keys <= bib_keys, f"missing bibliography keys: {sorted(cite_keys - bib_keys)}")


def check_protected_base() -> None:
    manifest_path = ROOT / "evidence/tmlr_do_not_modify_manifest.json"
    require(manifest_path.is_file(), "protected author-kit manifest is missing")
    if not manifest_path.is_file():
        return
    manifest = json.loads(manifest_path.read_text())
    for record in manifest["files"]:
        path = ROOT / record["path"]
        require(path.is_file(), f"protected author-kit file missing: {record['path']}")
        if path.is_file():
            require(digest(path) == record["sha256"], f"protected author-kit file changed: {record['path']}")


def check_evidence() -> None:
    data_js = (ROOT / "site/assets/arc-data.js").read_text()
    payload = json.loads(data_js.removeprefix("window.ARC_DATA = ").removesuffix(";\n"))
    require(len(payload["table"]) == 16, "browser data must contain 16 method rows")
    require(len(payload["cases"]) == 3, "browser demo must contain three non-overlap cases")
    require(payload["retrieval"]["source_recall_at_4"] == 1, "published retrieval recall@4 changed")
    provenance = json.loads((ROOT / "evidence/provenance.json").read_text())
    require(len(provenance["source_artifacts"]) >= 7, "provenance source inventory is incomplete")
    for record in provenance["source_artifacts"]:
        path = ROOT / record["path"]
        require(path.is_file() and digest(path) == record["sha256"], f"source hash mismatch: {record['path']}")
    require((ROOT / "dist/submission_folder.zip").is_file(), "OpenReview submission ZIP is missing")
    archive = ROOT / "dist/submission_folder.zip"
    if archive.is_file():
        with zipfile.ZipFile(archive) as handle:
            names = set(handle.namelist())
        for required in [
            "submission_folder/submission.md",
            "submission_folder/assets/img/submission/",
            "submission_folder/assets/gif/submission/",
            "submission_folder/assets/html/submission/",
            "submission_folder/assets/bibliography/submission.bib",
        ]:
            require(required in names, f"submission ZIP is missing required path: {required}")


def main() -> None:
    check_site()
    check_submission()
    check_protected_base()
    check_evidence()
    if ERRORS:
        print("PACKAGE VALIDATION FAILED", file=sys.stderr)
        for error in ERRORS:
            print(f"- {error}", file=sys.stderr)
        raise SystemExit(1)
    print("PACKAGE VALIDATION PASSED: site, TMLR submission, protected base, evidence, and ZIP")


if __name__ == "__main__":
    main()
