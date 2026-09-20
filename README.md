# ARC-Lean benchmark and TMLR Beyond-PDF package

This repository is the maintained public-facing package for the ARC-Lean
method/benchmark paper. It contains two views of the same claim-bounded
evidence:

- `site/`: a self-contained project website deployed by GitHub Pages;
- `submission_folder/`: the anonymous TMLR Beyond-PDF submission payload.

The current numbers are a first-round diagnostic pilot, not a sealed-test
result. Public-case labels are system-audit labels rather than independent
expert gold.

## Quick start

Build figures, browser data, provenance, and the OpenReview upload ZIP:

```bash
python -m pip install -r requirements.txt
python scripts/build_release.py
python -m unittest discover -s tests -v
python scripts/validate_package.py
```

Preview the project site:

```bash
python -m http.server 8000 --directory site
```

Then open <http://localhost:8000/>.

For an exact TMLR render, install and start Docker, then run:

```bash
python compile_submission.py
```

The official preview URL is
`http://0.0.0.0:8080/tmlr-beyond-pdf/under_review/submission/`.

## Repository map

- `data/frozen/`: compact immutable pilot artifacts copied from the research
  worktree.
- `scripts/build_web_data.py`: converts frozen claim/result records into the
  browser-safe data bundle.
- `scripts/render_web_figures.py`: Plot-Atlas-derived Morandi scientific plots.
- `evidence/provenance.json`: source/output hashes plus supported and unsupported
  claims.
- `design/reference-audit.md`: copyright-clean decomposition of the visual
  reference and reproduction acceptance record.
- `design/reference-reproduction/`: standalone structural reproduction used
  before applying the layout to ARC-Lean.
- `dist/submission_folder.zip`: generated OpenReview Beyond-PDF upload.

## TMLR compliance and anonymity

The official TMLR instructions require the main file to remain
`submission_folder/submission.md`, assets to stay in their prescribed
subdirectories, and `tmlr_do_not_modify/` to remain unchanged. The review
version is anonymous.

The public GitHub URL is identity-bearing. It must **not** be linked from the
anonymous OpenReview submission. The submission ZIP contains no GitHub URL or
author identity. Camera-ready author metadata should be added only after
acceptance.

## Scientific scope boundary

This TMLR line evaluates the audit system: baseline families, overclaim,
identifiability, promotion ceilings, trusted-checking endpoints, and the sealed
benchmark protocol. Detailed NASICON and NLEIS scientific findings belong to a
separate companion materials paper and are not reproduced here. One overlapping
pilot item remains in the provisional aggregate table and must be replaced
before the benchmark freeze.

## Publishing

Pushing `main` triggers `.github/workflows/pages.yml`, validates the package,
and deploys `site/` to GitHub Pages. The workflow requests Pages enablement via
the official `actions/configure-pages` action.

## License

Original project-site and build code is MIT licensed. The official
`tmlr_do_not_modify/` author-kit files are third-party submission infrastructure
and are excluded from that relicensing; see `NOTICE.md`.
