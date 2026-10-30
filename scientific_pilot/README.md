# ARC-LeanBench Phase 0 / Phase 1 harness

This directory is the executable protocol layer for the planned
ARC-LeanBench scientific-claim audit study. It is intentionally distinct from
the existing ARC diagnostic pilot. No file here is evidence that the 120-item
study has been executed.

## Current status

`NOT RUN / NOT PASSED`.

The harness is ready for local source capture and validation, but its source
lock explicitly blocks FormalPhysics until an appropriate licence/permission
and independently provenance-locked, buildable Lean environment are recorded.
`docs/arc_leanbench/FORMALPHYSICS_SOURCE_GATE_V1.md` defines that additional
gate. The remote execution environment
also must capture local source hashes, model digest, prompt hashes, and actual
Lean build receipts before a Phase 0 freeze can pass.

## Workflow

```mermaid
flowchart LR
    C["Canonicalize candidate units"] --> M["Freeze 120-item manifest"]
    M --> R["Run A0–A6 × 3"]
    R --> S["Blind score raw outputs"]
    S --> F["Render pilot figures"]
    F --> G["Independent review gate"]
```

## First commands on the experiment host

Run these from the repository root after setting portable root variables (do
not commit a personal absolute path to the public repository):

```bash
export ARC_PROJECT_ROOT="/absolute/path/to/your/ARC"
export ARC_RESOURCE_ROOT="$ARC_PROJECT_ROOT/resourses"
export ARC_CONTROLLED_CLAIMS_ROOT="/controlled/path/not-published"
```

Then capture the standard sources:

```bash
bash scientific_pilot/scripts/bootstrap_phase0_sources.sh "$ARC_RESOURCE_ROOT"

python3 scientific_pilot/scripts/capture_environment.py \
  --source-lock scientific_pilot/config/sources.lock.json \
  --output scientific_pilot/receipts/environment_receipt_v1.json \
  --run-build

python3 scientific_pilot/scripts/capture_model.py \
  --model-lock scientific_pilot/config/model.lock.json \
  --output scientific_pilot/receipts/model_receipt_v1.json

python3 scientific_pilot/scripts/validate_phase0.py --strict \
  --output scientific_pilot/receipts/phase0_validation_v1.json
```

Both commands are expected to fail until every required resource is locally
available, legal for the intended use, hash-pinned, and buildable. Do not work
around a failure by editing the receipt or hand-writing a successful result.

The FormalPhysics stratum has a separate source gate. It requires two clean
FSLean/evaluation-environment builds and a fixed selected-corpus compile
receipt before its source-lock status can be promoted; follow
`docs/arc_leanbench/FORMALPHYSICS_SOURCE_GATE_V1.md`. That gate cannot be
cleared with the PhysLib build receipt.

After reviewing the capture receipt, create a *new versioned candidate lock*
with observed local hashes; do not overwrite the draft lock:

```bash
python3 scientific_pilot/scripts/pin_source_hashes.py \
  --source-lock scientific_pilot/config/sources.lock.json \
  --receipt scientific_pilot/receipts/environment_receipt_v1.json \
  --output scientific_pilot/config/sources.lock.v2.candidate.json

python3 scientific_pilot/scripts/pin_model_lock.py \
  --model-lock scientific_pilot/config/model.lock.json \
  --receipt scientific_pilot/receipts/model_receipt_v1.json \
  --full-model-digest '<full immutable local model digest>' \
  --output scientific_pilot/config/model.lock.v2.candidate.json
```

Once source adapters create a validated candidate pool, validate it and freeze
the development-pilot manifest:

```bash
python3 scientific_pilot/scripts/validate_candidate_pool.py \
  --input scientific_pilot/inputs/candidate_units_v1.jsonl

python3 scientific_pilot/scripts/build_phase1_manifest.py \
  --candidates scientific_pilot/inputs/candidate_units_v1.jsonl \
  --source-lock scientific_pilot/config/sources.lock.json \
  --output scientific_pilot/manifests/phase1_120_v1.json \
  --source-target minif2f_lean4=30 \
  --source-target formalphysics_v2_formalscience=30 \
  --source-target scibench_quantitative=30 \
  --source-target arc_controlled_claims=30
```

The runner—not included until a model endpoint and the source environments are
captured—must emit all 2,520 scheduled raw records in the output schema. Score
and render only actual raw records:

```bash
python3 scientific_pilot/scripts/score_phase1.py \
  --gold scientific_pilot/gold/phase1_gold_v1.jsonl \
  --runs scientific_pilot/raw/phase1_runs_v1.jsonl \
  --run-plan scientific_pilot/config/run_plan_v1.json \
  --manifest scientific_pilot/manifests/phase1_120_v1.json \
  --arms scientific_pilot/config/arms_v1.json \
  --execution-receipt scientific_pilot/receipts/phase1_execution_v1.json \
  --phase0-freeze scientific_pilot/receipts/phase0_freeze_v1.json \
  --output-dir scientific_pilot/results/phase1_v1

python3 scientific_pilot/scripts/render_phase1_figures.py \
  --results-dir scientific_pilot/results/phase1_v1 \
  --execution-receipt scientific_pilot/receipts/phase1_execution_v1.json \
  --phase0-freeze scientific_pilot/receipts/phase0_freeze_v1.json \
  --manifest scientific_pilot/manifests/phase1_120_v1.json \
  --runs scientific_pilot/raw/phase1_runs_v1.jsonl \
  --arms scientific_pilot/config/arms_v1.json \
  --output-dir scientific_pilot/figures/phase1_v1
```

## Tests

```bash
python3 -m unittest discover -s scientific_pilot/tests -v
```

The test data are fixtures. The renderer refuses fixture-only or incomplete
result bundles unless a test-only override is supplied.
