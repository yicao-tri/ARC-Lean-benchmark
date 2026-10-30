# Source decisions and licensing log (v1)

This log records what was verified before Phase 0, and what remains a blocker.
It is intentionally more conservative than a list of attractive benchmarks.

| Source | Pinned upstream state | What it contributes | Phase 1 decision |
| --- | --- | --- | --- |
| Google DeepMind miniF2F | `f0a20e14c1eeccd859d51bb4c2b3ee487889c303`; Apache-2.0; Lean 4.27 | Formal/general-reasoning positive control | Candidate, pending local hash and build receipt |
| FormalScience / FormalPhysics v2 | `89b1e0ee60a346039107279dd109d00dfe8e8252`; `src/app_data/formal_qa_data.json` | Formal physics and semantic-drift stratum | **Blocked**: no `LICENSE` was found in the upstream root, and no independently verifiable FSLean environment has been captured for the pinned commit; obtain written permission/licence and a separately provenance-locked, buildable environment before use |
| SciBench | `e14e0ca3d3db0f02928a18d435b9c3d15656a7c5`; MIT | Physics/chemistry quantitative audit tasks | Candidate, pending local hash and candidate authoring |
| ARC controlled claims | access-controlled project claim pool; exact identity is retained in a private provenance receipt | Identifiability and claim-boundary stress cases | Candidate, pending parent-cluster firewall, new blinded gold labels, and controlled-source receipt review |
| PhysLib v2 | Lean4PHYS `cae90192085dda428a47af46766f7c738d9624f2`; Apache-2.0 | Source-specific Lean vocabulary and checking environment | Allowed dependency after fresh clean build receipt |
| LeanPhysBench v0 | same Lean4PHYS commit; CC BY-NC-4.0 with additional model-evaluation terms | Possible later formal-physics benchmark | Not selected; requires usage compatibility confirmation for the exact model and organisation |

## Consequences for the 4 × 30 pilot

The requested 30 FormalPhysics items remain part of the *design*, but the
manifest must not be created until the blocker is cleared.  We will not silently
replace the source with LeanPhysBench or rename a different dataset as
FormalPhysics.  If the blocker remains, the preregistered options are:

1. obtain written permission from the FormalScience authors and create a
   compatibility environment with a recorded toolchain/Mathlib lock; or
2. issue a protocol amendment before any runs that replaces this stratum with a
   new, explicitly licensed dataset, and names it accurately throughout.

## FormalPhysics source-gate supplement

The user has chosen the first option. This does **not** remove the block by
assertion: `FORMALPHYSICS_SOURCE_GATE_V1.md` defines the F0 evidence package,
and `verify_formalphysics_source_gate.py` must issue a machine-readable PASS.
Permission evidence itself remains in access-controlled provenance; the public
repository stores only its cryptographic inventory and redistribution decision.

## Retrieved source facts

- miniF2F's pinned `lean-toolchain` is `leanprover/lean4:v4.27.0`; its pinned
  Mathlib revision is `a3a10db0e9d66acbebf76c5e6a135066525ac900`.
- PhysLib v2 declares Lean `v4.28.0` and Mathlib `v4.28.0`.  It therefore must
  not be treated as one environment with miniF2F.
- FormalScience describes `formal_qa_data.json` as the dataset previously
  called `FormalPhysics_v2.json`, with `question`, `answer`, and
  `formal_answer` fields.  That identity is recorded; it is not inferred from
  a non-existent repository.
- SciBench is a public textbook-based benchmark.  Its public availability and
  likely training-data exposure are a contamination limitation, so Phase 1
  remains a development pilot rather than a benchmark-generalisation result.

## Resource infrastructure action

Set `ARC_PROJECT_ROOT` and `ARC_RESOURCE_ROOT` on the experiment host before
running the capture tools. The bootstrap helper pins a missing miniF2F or
FormalScience clone to the source-lock commits; it never upgrades an existing
repository to a moving branch. It does not supply the separately governed
FormalPhysics evaluation environment.
