# Independent review gate

The review status is deliberately `NOT PASSED` until executable evidence is
linked below.  This file prevents a roadmap or harness from being described as
an experiment result.

| Gate | Required evidence | Current status |
| --- | --- | --- |
| P0-1 preregistered protocol | protocol SHA, frozen before run | pending |
| P0-2 source / licence lock | commits, files, hashes, access and licence decisions | pending local capture |
| P0-3 environment lock | source-specific clean build receipts | pending local capture |
| P0-4 exact manifest | 120 unique items and deterministic regeneration | pending local capture |
| P0-5 partition firewall | overlap-test transcript and sealed-manifest handling | pending |
| P0-6 leakage policy | prompt and evidence-template SHA log | pending |
| P0-7 gold plan | blinded annotator plan, rubric, adjudication sheet | pending |
| P0-8 arm contract | config and approved-delta diff | pending |
| P0-9 evaluator | 8+ fixture results | pending test run |
| P0-10 release governance | claim boundary and PR mapping | pending |
| P1 raw execution | 2,520 scheduled records or a documented approved amendment | not started |
| P1 gold / scoring | blind scoring and adjudication evidence | not started |
| P1 analysis | reproducible figures, CIs, cost, coverage, cases | not started |
| P1 PR | branch, diff, commands, verdict | not started |

**Automatic failures:** mock/fixture outcomes presented as results; unpinned
versions; no clean controls; compiler success conflated with scientific truth;
hidden exclusions; undeclared unequal budgets; “sealed” language for an
inspectable development set; or an AI reviewer substituted for expert gold.

The independent reviewer supplies a written PASS / CONDITIONAL / FAIL verdict
after inspecting actual artifacts.  A conditional verdict is not a completion
claim.
