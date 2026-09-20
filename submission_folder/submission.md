---
layout: distill
title: "ARC-Lean: Auditing When Scientific Evidence Identifies a Claim"
description: "A claim-identifiability audit system that separates empirical decision, competing-model identification, trusted deduction, and safe scientific promotion."
htmlwidgets: true

# Keep anonymous throughout review.
authors:
  - name: Anonymous
    affiliations:
      name: Anonymous

bibliography: submission.bib

toc:
  - name: Why Scientific Claims Overreach
  - name: ARC-Lean
    subsections:
      - name: Claim and evidence graph
      - name: Countermodels and identifiability
      - name: Trusted deduction in Lean
      - name: Promotion ceilings and closure
  - name: Interactive Claim Audit
  - name: Pilot Benchmark
  - name: Results
  - name: What Lean Does—and Does Not—Prove
  - name: Definitive Evaluation Protocol
  - name: Limitations and Submission Gaps
  - name: Reproducibility
---

Scientific papers often establish that an observation is reproducible, a model
predicts held-out measurements, or an intervention changes an outcome. These
are important results, but they do not automatically establish that the
scientific target is uniquely determined by the evidence. Several mechanisms
may remain observationally equivalent, or a conclusion may require assumptions
that are absent from the stated scope. This distinction is central to causal
identification <d-cite key="pearl2009causality"></d-cite> and inverse problems,
but it is rarely measured as a first-class output of AI-for-science systems.

We introduce **ARC-Lean**, a claim-identifiability audit system. ARC-Lean
separates four objects that conventional support/refute evaluation conflates:

1. the empirical decision in a declared evidence scope;
2. whether the target is identified over a declared admissible model class;
3. the strongest assertion licensed by the evidence, called the *promotion
   ceiling*; and
4. a measurement or intervention that would separate live alternatives.

Lean 4 <d-cite key="moura2021lean4"></d-cite> is used as trusted deductive
bookkeeping for conditional obligations. It never promotes a scientific
conclusion beyond the empirical premises encoded by the audit.

> **Status of the evidence on this page.** The current results are a
> descriptive engineering and public-case pilot. Public-case labels are system
> audit labels rather than independent expert gold. They validate executable
> interfaces and component contrasts, not population-level generalization.

## Why Scientific Claims Overreach

Suppose a measurement map sends an admissible scientific world to an observed
record, while a target map extracts the mechanistic or causal quantity claimed
by the paper. The target is identified only when every pair of admissible worlds
with the same observation has the same target:

$$
h(w_1)=h(w_2) \Longrightarrow \theta(w_1)=\theta(w_2).
$$

A predictive model may achieve low held-out error while this implication is
false. Retrieval may find the right paper while a language model fails to
reason about the implied equivalence class. A correct supported/falsified label
may still be paired with a conclusion that exceeds what the evidence licenses.

This motivates an evaluation target different from fact verification: the
system must return the empirical decision *and* the identification status *and*
the maximal safe assertion.

## ARC-Lean

### Claim and evidence graph

ARC-Lean represents each audit as a typed graph containing the claim, target,
observed variables, required measurements, assumptions, evidence artifacts,
decision rule, candidate mechanisms, formal receipts, and proposed closure
experiments. Evidence artifacts are content hashed. Missing assumptions and
out-of-scope targets remain explicit rather than being completed silently by a
language model.

### Countermodels and identifiability

For a potentially non-identified claim, the system searches for two admissible
worlds that match the declared observation while disagreeing on the target. A
numeric or symbolic witness is stronger than a prose-only alternative because
its equivalence and disagreement conditions can be executed.

The declared model class is part of the claim. Non-identifiability in a broad
class does not imply non-identifiability under a justified narrower class;
conversely, a proof in an unrealistically narrow class does not establish
scientific uniqueness.

### Trusted deduction in Lean

When an audit yields an exact obligation, ARC-Lean translates the obligation
into a small Lean theorem. The kernel checks that the conclusion follows from
the encoded definitions and witnesses. The receipt records the theorem,
toolchain, source hash, and verification result.

### Promotion ceilings and closure

ARC-Lean maps the audit state to a partial order of permitted assertions. A
bounded reproduction can license source-scoped support; an unresolved
countermodel may license compatibility only; a successful counterexample can
license bounded falsification without licensing a universal negation.

For unresolved claims, the system proposes a closure experiment containing the
intervention or condition, measured variables, predictions under competing
mechanisms, a decision rule, feasibility, and cost tier.

## Interactive Claim Audit

The interactive figure below contains one engineering claim and two current
public-pilot examples from solid-state ionics. Select a claim and toggle between
the full ARC audit and a decision-only promotion rule. The latter demonstrates
how a correct empirical decision can still encourage an unsupported
mechanistic promotion.

<figure style="text-align:center;margin:24px 0;">
  <iframe
    src="{{ 'assets/html/submission/arc_audit_demo.html' | relative_url }}"
    width="100%"
    height="940"
    style="border:0;overflow:hidden;border-radius:14px;"
    title="Interactive ARC-Lean claim audit">
  </iframe>
  <figcaption>Interactive audit. Public examples are system-labeled pilot cases,
  not independent expert gold.</figcaption>
</figure>

The public examples are bounded interpretations of anomalous ion transport
<d-cite key="poletayev2022persistence"></d-cite> and path entropy
<d-cite key="guan2026path"></d-cite>. The engineering example isolates missing
transport laws and boundary conditions. Together they distinguish reproduction
of an observable from identification of its unique physical cause.

## Pilot Benchmark

The current benchmark contains two diagnostic regimes:

- **Engineering seed:** 14 co-designed cases used to test schemas, executable
  witnesses, formal receipts, and ablations.
- **Public scientific pilot:** eight claims linked to public papers and released
  artifacts. These are system-audit labels and are not the sealed test.

Sixteen rows cover simple controls, claim-only and structured-context local
language models, sanitized-artifact models, source-grounded BM25 micro-RAG, and
cumulative ARC variants. Every method reports overclaim, identifiability,
empirical decision, and joint exact match when the output is defined.

**Overclaim** is the primary safety endpoint: the predicted assertion
capabilities must be a subset of the adjudicated promotion ceiling. **Joint
exact** requires identifiability, empirical decision, and promotion ceiling to
all match. Dashes denote unavailable objects, never zeros.

## Results

{% include figure.html path="assets/img/submission/public_pilot_map.svg"
style="max-width:100%;height:auto;" class="img-fluid"
caption="Selected public-pilot methods. Lower is better only for overclaim; higher is better for the other three groups. Eight system-labeled claims; descriptive single-run estimates without uncertainty intervals." %}

Three findings motivate the definitive evaluation.

First, retrieval success is not scientific reasoning. BM25 retrieves a relevant
source within the top four for every public-pilot query, but both local
micro-RAG arms obtain zero joint exact match.

Second, empirical decision can hide unsafe promotion. The 8B
sanitized-artifact arm obtains 100% public decision exact match while producing
50% overclaim and only 50% joint exact match.

Third, the promotion ceiling is an independently necessary component. In the
ablation below, reference identifiability and decision remain at 100%. Replacing
the partial-order ceiling with a decision-only mapping creates 42.9% overclaim
on the engineering seed and 12.5% overclaim on the public pilot.

{% include figure.html path="assets/img/submission/ceiling_ablation.svg"
style="max-width:100%;height:auto;" class="img-fluid"
caption="Isolated promotion-ceiling ablation. Identifiability and empirical decisions are held fixed; only the rule mapping evidence to licensed assertions changes." %}

ARC without Lean and ARC-Full currently tie on public-pilot joint exact match.
This does not establish that formal checking is unnecessary. It shows that
label accuracy on the present cases does not identify a contribution from the
kernel. The definitive evaluation therefore measures invalid obligations
caught, kernel/type failures, and corrupted-assumption stress tests rather than
claiming a label-accuracy benefit that the pilot cannot support.

## What Lean Does—and Does Not—Prove

For two witnesses with the same observation and different targets, a small
kernel-checked theorem can establish that the observation map does not identify
the target over the encoded class. The receipt is valuable because it prevents
silent assumption changes and makes the deductive boundary inspectable.

Lean does **not** establish that either witness is physically realized, that the
encoded model class is scientifically adequate, that a paper was extracted
correctly, or that a mechanism is true in nature. Formal validity and empirical
adequacy are separate axes.

## Definitive Evaluation Protocol

The planned study is train-free or frozen-prompt wherever possible:

| Split | Size | Permitted use |
|---|---:|---|
| Development (2022) | 40 claims / 20 papers | Prompt, parser, schema, error analysis |
| Validation (2023) | 60 claims / 34 papers | Freeze method, retrieval, thresholds |
| Sealed test (2024–2025) | 400 claims / 200 papers | Primary and subgroup evaluation only |
| Evidence-complete deep cases | 8 cases | Certificate and closure evaluation |

The primary contrast is ARC-Full minus a source-matched RAG baseline on
overclaim rate. Uncertainty uses source paper as the bootstrap cluster. Claims
from the same paper are not treated as independent replicates. Stochastic arms
use five paired seeds, and no sequential significance stopping is allowed.

The main table will separately report the temporal paper-disjoint audit, strict
leave-one-materials-theme-out transfer, and evidence-complete certificate and
closure judgments. Closure validity and experiment minimality will be rated by
blinded experts.

## Limitations and Submission Gaps

The current pilot is small and partly co-designed. Public labels are not
independent expert annotations. The micro-RAG corpus contains paper abstracts
and licensed repository READMEs rather than full-text open-corpus retrieval.
Local deterministic models do not represent the strongest contemporary model
family or stochastic variability. Exact rates have no paper-cluster confidence
intervals.

One current public-pilot source overlaps with a separate deep-science companion
project. It will be replaced before the TMLR benchmark is frozen; this page does
not present the companion project's detailed results or figures. The definitive
submission also requires a measurable trusted-checking endpoint for Lean and
blinded expert assessment of proposed closure experiments.

## Reproducibility

The repository is organized as a TMLR Beyond-PDF author-kit project. The
submission-facing package contains only `submission_folder`, with static images
under `assets/img/submission`, interactive figures under
`assets/html/submission`, and this bibliography under `assets/bibliography`.
The companion project root additionally retains frozen source CSV/JSON files,
plotting scripts, a provenance manifest, visual-audit notes, validation tests,
and a separate static project site.

The figures on this page are regenerated from frozen pilot artifacts using the
project's registered scientific plotting primitives. Every displayed result is
descriptive and carries its interpretation boundary in the caption or text.
