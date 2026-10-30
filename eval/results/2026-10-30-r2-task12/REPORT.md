# Task 12 causal test: report

**Status: closed.** Decision: harness@12 is not reconstructed. No source for it exists on disk (no round-1 C
clone, `applied.diff` has no harness files, the library holds one entry, and no session directory has the task
text). The four arms below are the pre-registered approximate set, and their results are reported as such.

## Setup

- Build: lithify e8468122 (PR #32). CLI pinned to 2.1.310. Holdout: sqlglot PR #7549 (task 12 in the horizon order).
- Arms, five replicates each, 20 runs total, $2.60 of the $5 cap:
  - (c) `c_skill`: starter + final `sqlglot-optimizer-rewrites` skill (primary arm)
  - (d) `d_placebo`: starter + frozen placebo skill (control)
  - (a) `a_full`: full final C harness (approximate)
  - (b) `b_minus`: (a) without the skill (approximate)
- Raw results: `results-task12-<arm>-r<n>.csv` in this directory. Holdout pass is the `holdout_pass` column.

## Results (holdout passes, from the raw CSVs)

| arm | r1 | r2 | r3 | r4 | r5 | passes |
|---|---|---|---|---|---|---|
| (c) starter + skill | 0 | 0 | 0 | 0 | 0 | 0/5 |
| (d) starter + placebo | 0 | 0 | 1 | 0 | 0 | 1/5 |
| (a) full harness (approx.) | 0 | 0 | 0 | 0 | 0 | 0/5 |
| (b) minus skill (approx.) | 0 | 0 | 0 | 0 | 0 | 0/5 |

All 20 runs delivered with one execution each, so every failure is a holdout failure, not a non-delivery.

## Task 12 across all non-round-1-C runs

Task 12 (position 12 in `eval/results/2026-10-29-r2-noise/per_task.csv`, sqlglot#7549):

| source | passes |
|---|---|
| Phase 0 A1–A5 | 0/5 |
| Phase 0 B1–B3 | 0/3 |
| Task-12 arms (a, b, c, d) | 1/20 |
| **Total** | **1/28** |

Round-1 C (C1) passed once. It is excluded from the total above, as it is the run whose result the test was
designed to check.

## Reading

- Task 12 is a **rare-pass task, not a never-pass task**. Under the Phase 2 rule below, its baseline rate is
  consistent with ≤ ~0.3, not zero.
- Round-1 C's single pass is consistent with luck. The only pass in the task-12 arms is a placebo run (d, r3),
  so it does not support the skill either.
- The final skill did not make task 12 pass in any of 5 runs (arm c). Arm (a) is 0/5 as well, so the full harness
  does not reproduce the round-1 pass.
- **No mechanism has been identified for C's +0.092 on tasks 31–60** (the window reported in
  `eval/results/2026-10-29-r2-noise/REPORT.md`).

## Correction to the earlier reading on #29

The earlier interpretation on #29 that task 12 shows a feedback-learned skill transferring is **withdrawn**. The data
do not support it: the skill arm is 0/5, and the only task-12 pass is a placebo run.

## Carried into Phase 2 (preregistration rule)

- A task with a 0/5 baseline is treated as "rate ≤ ~0.3", **not "never"**.
- Any single-task win is replicated before it is interpreted.
