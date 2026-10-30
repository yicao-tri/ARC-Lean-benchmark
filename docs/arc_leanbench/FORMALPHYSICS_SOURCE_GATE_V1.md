# FormalPhysics source gate (F0)

**Status:** `BLOCKED_PENDING_EVIDENCE`. This gate determines only whether the
FormalPhysics v2 stratum is eligible for Phase 0 selection. It does not pass
Phase 0, execute Phase 1, or turn a compiling proof into a scientific claim.

## Why this separate gate exists

The locked FormalScience source is
`89b1e0ee60a346039107279dd109d00dfe8e8252`, using
`src/app_data/formal_qa_data.json` (FormalPhysics v2). Its documentation
describes an `FSLean` project and Lean `v4.24.0-rc1`, but a source description
is not a reproducible environment receipt. The FormalPhysics environment must
therefore be independently provenance-locked and must remain isolated from
PhysLib's Lean 4.28 environment.

## Required evidence bundle

Keep confidential permission material out of the public repository. Store it
under controlled access and commit only the non-confidential inventory/hash.

```text
provenance/formalphysics/
  authorization_inventory_v1.json
  source_identity_v1.json
  fslean_identity_v1.json
  environment_lock_v1.json
  build_receipt_clean_A.json
  build_receipt_clean_B.json
  corpus_compile_receipt_v1.jsonl
  adapter_review_v1.json
  formalphysics_source_gate_v1.json
```

| Gate | Acceptance requirement |
| --- | --- |
| F0-L1/L2 | A rights-holder licence or written authorization covers the exact v2 dataset, research use, automated LLM evaluation, controlled audit/error variants, and redistribution limits. Its inventory records a document hash, issuer role, custodian, date, attribution, expiry/conditions, and a public-release disposition. |
| F0-D1/D2 | A clean dedicated clone records origin, exact commit/tree, submodule status, data Git blob, SHA-256, byte count, JSON validity, and item count. Do not substitute `data/FormalPhysics.json` for `src/app_data/formal_qa_data.json`. |
| F0-E1/E2 | FSLean must be author-provided or a separately named `formalphysics_eval_env_v1` compatibility environment. Record its origin/archive hash, right to use, toolchain, lakefile/manifest hashes, resolved Mathlib/dependency identities, and custodian. |
| F0-E3 | Two independently clean worktrees build with `lake build` exit status zero. Capture actual argv, cwd fingerprint, environment-lock hash, stdout/stderr hashes, timing, platform and distinct worktree IDs. |
| F0-T1 | Every selected FormalPhysics item is parsable by one frozen adapter. Each `verified` item has a real zero exit status; a non-verified selected formal-failure item has a predeclared reason. No per-item manual rescue is permitted. |
| F0-T2 | The same environment passes a positive smoke theorem and rejects at least two invalid controls. The adapter forbids `sorry`, unresolved metavariables, and newly introduced unsound axioms. |
| F0-T3 | The adapter only introduces frozen imports/notation/definitions. A qualified reviewer checks semantic alignment for at least 10 selected items and records the result separately from kernel compilation. |
| F0-P1/R1 | The machine verifier produces a hash-bound PASS receipt, and an independent reviewer reruns it from a fresh worktree. |

If permission allows internal evaluation but prohibits redistribution, the
public PR may publish only IDs, hashes, aggregate results, access instructions,
and safe code. It must not publish raw source text, selected records, or model
outputs derived from them.

## Capture and verify

On the mounted experiment host, first set the portable roots and produce the
non-confidential technical receipts. The FSLean/evaluation tree is intentionally
a separate sibling path, not copied into the FormalScience clone.

```bash
export ARC_PROJECT_ROOT="/absolute/path/to/your/ARC"
export ARC_RESOURCE_ROOT="$ARC_PROJECT_ROOT/resourses"

python3 scientific_pilot/scripts/capture_formalphysics_gate_evidence.py \
  --source-lock scientific_pilot/config/sources.lock.json \
  --source-root "$ARC_RESOURCE_ROOT/formal-science-source-gate" \
  --fslean-root "$ARC_RESOURCE_ROOT/formalphysics_eval_env_v1" \
  --worktree-id clean-A \
  --source-identity-output provenance/formalphysics/source_identity_v1.json \
  --fslean-identity-output provenance/formalphysics/fslean_identity_v1.json \
  --environment-lock-output provenance/formalphysics/environment_lock_v1.json \
  --build-receipt-output provenance/formalphysics/build_receipt_clean_A.json \
  --run-build
```

Repeat in a distinct clean worktree with `--worktree-id clean-B`. After the
blinded 30-unit manifest and fixed corpus run exist, verify the evidence:

```bash
python3 scientific_pilot/scripts/verify_formalphysics_source_gate.py \
  --source-lock scientific_pilot/config/sources.lock.v2.candidate.json \
  --authorization-inventory provenance/formalphysics/authorization_inventory_v1.json \
  --source-identity provenance/formalphysics/source_identity_v1.json \
  --fslean-identity provenance/formalphysics/fslean_identity_v1.json \
  --environment-lock provenance/formalphysics/environment_lock_v1.json \
  --build-a provenance/formalphysics/build_receipt_clean_A.json \
  --build-b provenance/formalphysics/build_receipt_clean_B.json \
  --corpus-receipts provenance/formalphysics/corpus_compile_receipt_v1.jsonl \
  --adapter-review provenance/formalphysics/adapter_review_v1.json \
  --manifest scientific_pilot/manifests/phase1_120_v1.json \
  --output provenance/formalphysics/formalphysics_source_gate_v1.json
```

The first verifier pass may be bound to the still-blocked pre-clearance lock;
that is evidence, not a release decision. Create a new candidate lock from it,
then rerun the verifier against the new lock so the final receipt is bound to
the exact lock used by Phase 0:

```bash
python3 scientific_pilot/scripts/promote_formalphysics_source_candidate.py \
  --source-lock scientific_pilot/config/sources.lock.v2.candidate.json \
  --formalphysics-gate provenance/formalphysics/formalphysics_source_gate_preclearance_v1.json \
  --output scientific_pilot/config/sources.lock.v3.formalphysics-candidate.json
```

Only the rerun `PASS` receipt bound to this candidate source lock and manifest
can unblock the source for a proposed Phase 0 freeze. The independent reviewer
then reviews the evidence package; it remains a separate gate from Phase 0
acceptance.
