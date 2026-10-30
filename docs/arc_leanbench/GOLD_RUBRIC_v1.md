# ARC-LeanBench gold-label rubric (v1)

Annotators work blind to experimental arm and model output.  They label the
candidate analysis, not the source author or a model's style.

| Field | Allowed values | Decision rule |
| --- | --- | --- |
| `gold_error` | `true`, `false` | Does the candidate contain a material error relative to the allowed evidence and stated task? |
| `severity` | `clean`, `minor`, `major` | Major changes a scientific/mathematical conclusion; minor does not; clean has no material error. |
| `error_families` | controlled taxonomy list | Include all material families; use `none` for clean controls. |
| `localization` | span / step ID / `not_localizable` | Identify the earliest material failure; do not infer a later error when earlier failure is unresolved. |
| `identifiability` | `identified`, `non_identified`, `not_applicable`, `uncertain` | Is the stated conclusion unique under the declared observables and assumptions? |
| `claim_boundary` | `supported`, `overclaim`, `underclaim`, `inconclusive` | Does the conclusion stay within available evidence and assumptions? |
| `semantic_alignment` | `aligned`, `misaligned`, `unverified`, `not_applicable` | Is the formal target faithful to the scientific claim/observable? |
| `repair` | `verified_useful`, `plausible_unverified`, `not_needed`, `not_possible` | Does a repair correct the original material error without adding unsupported conclusions? |

## Taxonomy

- `G1_logic_contradiction`, `G2_invalid_inference`, `G3_missing_boundary`,
  `G4_math_or_symbolic_error`, `G5_specification_mismatch`;
- `S1_physical_law_or_dimension`, `S2_non_identifiability`,
  `S3_causal_overclaim`, `S4_evidence_insufficiency`,
  `S5_uncertainty_or_statistics`, `S6_model_world_mismatch`,
  `S7_non_discriminating_experiment`.

Two annotators label independently.  The adjudicator resolves every primary
field disagreement, preserves both originals, and records a rationale tied to
the allowed source evidence.  The reporting script prints raw agreement and a
confusion table; it does not claim a reliability coefficient when the sample is
too small or class distribution makes it misleading.
