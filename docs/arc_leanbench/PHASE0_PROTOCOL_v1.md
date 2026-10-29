# ARC-LeanBench Phase 0 protocol (v1)

**Status:** frozen only after all fields marked `PENDING LOCAL CAPTURE` below
are filled, hash-recorded, independently reviewed, and committed.  Until then,
this is a protocol draft, not an executed experiment.

## 1. Scope and unit of analysis

An audit unit contains: (a) a canonical source item; (b) a candidate answer,
derivation, formal target, or scientific claim; (c) a clean/error label and
error family; (d) provenance; and (e) a cluster identifier for its original
problem/paper. The primary unit is the **source-level audit unit**, not an
individual injected variant or model sample.

Phase 1 consists of exactly 120 units: 30 per stratum.  The selection target is
15 error units and 15 clean controls per stratum; every deviation is a
pre-run amendment with an item-level reason, never a silent substitution.

## 2. Primary and secondary endpoints

### Primary endpoint

`balanced_audit_accuracy`: mean of item-level sensitivity and item-level
specificity. For item \(i\), arm \(a\), and its three predeclared replicates,
the decision score \(D_{i,a}=1\) only if at least two scheduled replicates make
the correct binary decision. A timeout, malformed output, tool error, and
abstention count as incorrect. Thus the primary estimand is source-item level;
raw replicate behavior is reported as a secondary reliability/coverage outcome.

### Secondary endpoints

- raw-run sensitivity/specificity and replicate agreement;
- joint audit accuracy: decision, error family, identifiability and claim
  boundary all correct where applicable;
- localization and useful-repair rate;
- abstention, tool completion, formalization, and semantic-alignment coverage;
- Lean status distribution;
- tokens, wall-clock time, tool time, and cost per scheduled run;
- false-confidence rate: a confident clean/valid verdict on a gold-invalid or
  semantic-mismatch unit.

## 3. Arms and fairness contract

The canonical arm definitions are in `config/arms_v1.json`.  Each arm uses the
same base model revision, system prompt, item evidence packet, JSON schema,
three seed values, token cap, wall-clock cap, and maximum tool-call budget.
Only the pre-approved capability column differs.  The runner records every
config and prompt SHA-256 beside each output.

`A6 - A5` is the primary Lean conditional-on-ARC contrast; `A3 - A0` is the
direct-LLM contrast.  The study may report unequal-budget best effort only as a
clearly labelled secondary analysis; it cannot replace the fixed-budget result.

## 4. Sampling and partitions

### Development pilot

Phase 1 is a development pilot selected by deterministic hash ranking from
declared source pools.  Its selected records may be inspected for harness and
rubric development, so it is **not sealed**.

### Later sealed study

Phase 2 uses a separate root-source/paper/proof-cluster holdout.  The full
manifest stays outside the development repository under an evaluator-controlled
location; the public/private repository receives only its checksum, count,
and selection-script hash.  The firewall check rejects overlap on canonical ID,
original theorem/paper, source file, and parent cluster.

## 5. Leakage and contamination policy

- No gold answer, proof, expert label, or outcome reference appears in an arm
  prompt, tool context, or retrieval corpus.
- Each item declares an evidence allow-list.  Tools cannot browse outside it
  during a fixed run.
- No per-item prompt, tool configuration, or manual proof rescue is allowed.
- Public-benchmark exposure and model-training contamination are recorded as a
  limitation, not concealed with a “sealed” label.
- Source terms govern data use and redistribution.  An unknown or incompatible
  licence blocks that source from the executable manifest.
- A model name is insufficient: provider, immutable model revision/digest,
  serving stack, sampling parameters, and date are recorded.

## 6. Gold-label and adjudication plan

The rubric is in `docs/arc_leanbench/GOLD_RUBRIC_v1.md`.  Before result
scoring, two qualified annotators independently label at least 20% of units
and every primary field in every unit.  They are blind to arm identity.
Disagreements are adjudicated with a recorded rationale; agreement/confusion is
reported.  An AI/subagent review does not substitute for domain-expert gold.

## 7. Lean interpretation and source-specific environments

The study deliberately uses **separate source environments**, because the
current upstream resources are not toolchain-compatible:

| Source | Declared upstream environment | Phase 0 requirement |
| --- | --- | --- |
| miniF2F Lean 4 | Lean `v4.27.0`, pinned Mathlib in upstream manifest | capture clean `lake build` receipt |
| PhysLib v2 / Lean4PHYS | Lean `v4.28.0`, Mathlib `v4.28.0` | capture clean `lake build` receipt |
| FormalPhysics via FormalScience | upstream dataset is available, but its checked-in repository does not supply the referenced `FSLean` environment | obtain or construct a versioned, licensed compatibility environment and capture it before selection |
| SciBench / ARC claims | no canonical Lean project | only formalize claims against a separately pinned target environment; report semantic alignment |

Every Lean-enabled raw result includes command, working-directory fingerprint,
toolchain/Mathlib/PhysLib versions, formal input hash, stdout/stderr hash,
exit status, and latency.  A compile pass is never auto-scored as scientific
validity.

## 8. Run and analysis plan

Run 120 × 7 arms × 3 scheduled replicates = **2,520 raw records**. A timeout,
tool error, malformed JSON, or abstention remains in the denominator. The
result verifier emits per-run and per-item records, then estimates paired
item-level balanced-accuracy contrasts `A6−A5` and `A3−A0` with a
source-stratum × error-status preserving, parent-cluster bootstrap. Raw-run
effects are secondary. The 120-unit pilot balances error versus clean only;
H2/H4 error-family and formalizability heterogeneity results are explicitly
exploratory/descriptive here and become confirmatory only after Phase 2 quotas
are frozen.

Required Phase 1 reports are: a multi-arm taxonomy result, paired effect plus
coverage/cost display, item-level failure map, source/attrition table, and
three independently adjudicated cases (Lean-rescued, no-increment,
Lean-certified-but-scientifically-insufficient).

## 9. Amendment rule

Any change after a freeze to sources, sample list, rubric, model, toolchain,
prompt, arm, score, or budget creates `protocol_v{n+1}` and a new manifest
hash.  The report names the change, rationale, affected records, and whether
any outcome was inspected before the change.  Historic outputs are retained;
they are never overwritten.

## 10. Completion gate

Phase 0 passes only after the independent reviewer finds executable evidence
for source locks, environment receipts, exact 120-unit manifest, partition
checks, prompt/arm hashes, rubric/gold plan, evaluator fixtures, and release
provenance.  Phase 1 passes only after actual raw runs, blind score records,
reproducible figures, and a review verdict exist.  Neither phase can be passed
from prose, reference results, or mock fixtures.
