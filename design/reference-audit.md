# Reference-site decomposition and reproduction audit

Reference: <https://zzigak.github.io/mpmworlds/>

This document records visual and interaction patterns only. No reference media,
paper text, or downloadable assets are copied into this repository.

## Page logic

1. A 52 px sticky navigation bar exposes the article's argument as anchors.
2. A wide two-column hero places the research proposition and contributions on
   the left and one square visual summary on the right.
3. Narrow, prose-width sections introduce the task and comparison before the
   page expands again for interactive evidence.
4. Evidence is organized by question rather than by implementation detail:
   “when A wins”, “when B wins”, complementary cases, sensitivity, aggregate
   metrics, and finally inspectable source artifacts.
5. The first evidence example is large. Additional examples live in horizontal
   snap carousels with explicit previous/next controls.
6. Metric chips annotate why an example matters. Controls remain adjacent to
   the media they affect.
7. Quantitative summaries appear after qualitative evidence, and the page ends
   with inspectable code/data rather than a marketing call-to-action.

## Measured desktop visual grammar

- Browser viewport inspected: 1280 × 720.
- Body: system sans-serif, 18 px, 1.58 line height, white background,
  `#333333` foreground.
- Global content width: up to 1720 px; prose width: 960 px.
- Hero: two equal columns, 48 px gap, 56 px top padding; title 38 px/600.
- Navigation: white, 1 px lower rule, horizontally scrollable links.
- Cards: near-white fill, 2 px black outline, 8 px radius, hard 5 px black
  shadow; hover increases shadow.
- Section rhythm: 48–64 px vertical padding and 1 px separators.
- Responsive breakpoints: hero collapses below 900 px; cards become two-up
  below 900 px and 85%-width horizontal cards below 600 px.

## Reproduction decision

The reusable implementation keeps the information architecture, responsive
grid, sticky navigation, evidence cards, carousels, metric chips, and the
qualitative-to-quantitative-to-artifact sequence. It deliberately changes the
palette to Morandi blue/green/rose and replaces all reference content with
ARC-Lean content. This is a structural reproduction, not a copy of another
paper's expressive content.

## Acceptance checklist

- [x] Sticky navigation and active-section indicator.
- [x] Two-column desktop hero and one-column mobile hero.
- [x] Separate wide evidence and narrow prose containers.
- [x] Hard-outline evidence cards and horizontal snap interaction.
- [x] Metric chips and local controls.
- [x] Quantitative summary after interactive examples.
- [x] Inspectable artifact/code panel at the end.
- [x] Keyboard-focus states and reduced-motion behavior.
- [x] No copied reference text, figures, videos, or scripts.

