# Phase 1 pre-run checklist

Complete and hash this checklist before the first scheduled model invocation.
The experiment lead and the independent reviewer record a date and initials in
the committed receipt; a blank checkbox is a run blocker.

- [ ] `sources.lock.json` has only allowed Phase 1 sources; every selected
  source file has a local SHA-256 and matching commit receipt.
- [ ] Source licence/permission decisions and required attributions are recorded.
- [ ] Source-specific Lean environments built cleanly and their toolchain,
  Mathlib, PhysLib, command, stdout, and stderr receipts are captured.
- [ ] `phase1_120_v1.json` has exactly 120 units, 30 per source, 15 error / 15
  clean controls per source, no duplicate canonical IDs, and no parent-cluster
  collisions.
- [ ] Development and sealed partitions pass the canonical-ID, source-file,
  parent-cluster, and paper/proof overlap checks.
- [ ] Base model digest/runtime and all A0–A6 config/prompt hashes are frozen.
- [ ] Tool and wall-clock/token budgets have been dry-run tested without
  inspecting pilot outcomes.
- [ ] Gold rubric has two qualified blind annotators assigned; at least 20% of
  items are preassigned for double coding and the adjudicator is assigned.
- [ ] The runner records every requested raw run, including timeout, malformed,
  model, and tool failures. No per-item rescue path is enabled.
- [ ] The independent reviewer has checked the freeze receipt and given a
  written Phase 0 PASS.
