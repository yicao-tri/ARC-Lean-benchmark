# Visual QA record

Date: 2026-09-19 (America/Los_Angeles)

## Reference decomposition

The reference page was inspected at a 1280 × 720 browser viewport. Its sticky
navigation, equal-column hero, narrow prose width, wide evidence sections,
outlined cards, metric chips, horizontal evidence carousels, quantitative
summary, and inspectable artifact ending were reproduced independently in
`design/reference-reproduction/index.html`. No reference media or text was
copied.

## ARC-Lean desktop review

- Viewport: 1280 × 720.
- Hero title, deck, actions, scope warning, and identifiability schematic are
  visible without horizontal overflow.
- Morandi sage/rose accents maintain readable contrast against the warm paper
  background.
- Sticky navigation remains legible and active-section state is visible.
- The interactive audit renders three evidence panels and four verdict cells
  without clipping.
- The full 16-row table is populated by the browser data bundle.
- Decision-only mode on the Poisson closure case changes the ceiling from
  `proposal_only` to `compatibility_only` and visibly reports `overclaim risk`.

## ARC-Lean mobile review

- Embedded viewport: 390 × 844 using `tests/fixtures/mobile_preview.html`.
- Hero collapses to one column, title remains readable, and action buttons wrap.
- Navigation scrolls horizontally instead of forcing document-wide overflow.
- Pipeline, demo panels, findings, Lean cards, roadmap, and artifacts collapse
  to one column through explicit responsive rules.
- The wide benchmark table remains locally scrollable by design.

## Scientific figure review

- `public_pilot_map`: PNG and editable SVG inspected. Axes and legend are not
  clipped. The caption states that overclaim has the opposite direction from
  the other three groups and that estimates are descriptive system-label pilot
  values.
- `ceiling_ablation`: PNG and editable SVG inspected. Paired endpoints and
  labels are legible; the caption states the controlled component and non-gold
  status.

## Published GitHub Pages review

- URL: `https://yicao-tri.github.io/ARC-Lean-benchmark/`.
- GitHub Actions run `35485118323` completed successfully for commit
  `afca989cb3750d346db15744a2d7361e918fb15c`.
- The public HTTPS endpoint returned HTTP 200 and loaded its stylesheet, data,
  figures, and JavaScript without path failures.
- A direct browser review confirmed the sticky navigation, Morandi visual
  system, full 16-row table, and the deployed interactive audit.
- On the deployed page, selecting `Decision-only ceiling` for the Poisson case
  changed the visible ceiling to `compatibility only` and the audit status to
  `overclaim risk`, confirming that deployed interactivity is live rather than
  a static screenshot.

## Remaining rendering limitation

The official Docker-based TMLR Jekyll render could not be executed on this host
because Docker is not installed. The package validator covers the prescribed
folder topology, front matter, citations, local iframe assets, anonymity,
protected author-kit hashes, figures, data hashes, and upload ZIP. An exact
TMLR render remains a required pre-submission gate on a Docker-enabled host.
