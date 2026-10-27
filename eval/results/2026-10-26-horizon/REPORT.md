# Horizon experiment on sqlglot: results against the pre-registration

- **Pre-registration:** [`eval/horizon/PREREGISTRATION.md`](../../horizon/PREREGISTRATION.md), committed `5defb42` before any live run. Horizon list frozen in `f964993`.
- **Code:** lithify `main` (#27 `lithify feedback` included), installed non-editably. Same build for every arm.
- **Spend:** A $2.06, B $5.21, C $50.93, dev smoke $0.03, so **$58.23 of $100**. No limit hits. B and C were stopped once, between tasks, by a stale global $150 cap and resumed exactly where they stopped (`3b828e2`).
- **Tasks:** 60 consecutive sqlglot PRs (#7492 → #7796, merged 2026-04 to 2026-06), hidden check = the PR's own tests, post-hoc only.

## Pre-registered hypotheses

| | criterion | result | verdict |
|---|---|---|---|
| Stage gate | A fails ≥ 15/60 | A failed **25/60** | met: headroom exists |
| **H1 (primary)** | C − A ≥ 10 points on tasks 31–60, one-sided exact McNemar p < 0.05 | **+6.7 points** (19/30 vs 17/30), discordant 2 wins / 0 losses, **p = 0.25** | **not met** |
| H2 | C − A larger on 31–60 than on 1–30 | +10.0 (1–30) → +6.7 (31–60) | **not supported** |
| H3 | C > B on 31–60 | +6.7 points, 2 / 0, p = 0.25 | not significant |
| H4 | C ≤ $1.00 per task on 31–60 | **$0.795** per task | met |
| Leak audit | no win relies on a copied hidden-test expectation | 0 of 33 new expected strings in C's wins appear in C's harness or library (one generic call-signature fragment from the task text itself) | clean; H1 unchanged in the sensitivity analysis |
| Safety | 0 pipeline invariant violations | 0 / 180 task checks; no installs or venvs; git writes = `git stash` only | clean |

## Results (all 60 tasks completed by every arm; 95% Wilson intervals)

| arm | all 60 | tasks 1–30 | tasks 31–60 | pass per 10-task block | explored (k > 0) | cost | always-on harness |
|---|---|---|---|---|---|---|---|
| A baseline | 35 [0.46, 0.70] | 18 | 17 | 6 6 6 6 6 5 | 0 | $2.06 | 185 → 185 |
| B adaptive | 38 [0.51, 0.74] | 21 | 17 | 7 7 7 7 6 4 | 6 | $5.21 | 185 → 369 |
| C adaptive + feedback | **40** [0.54, 0.77] | 21 | 19 | 6 8 7 7 7 5 | 46 | $50.93 | 185 → **2,822** |

**Exploratory (not pre-registered; several comparisons were made):** over all 60 tasks, C beat A on 5 tasks and lost none (+8.3 points, one-sided p = 0.031). B beat A on 4 and lost 1 (p = 0.19). C never lost a task to the baseline.

## What the data say

1. **The headroom is real, and the gates are blind to it.** 23 of A's 25 failures *passed sqlglot's own test suite*: the agent shipped plausible but wrong output (exact transpilation conventions, AST shapes). Lithify without feedback (B) learns only from gate failures, so it explored on 6 of 60 tasks and tied the baseline on 31–60.
2. **Post-delivery feedback helps a little and never hurt**, but there is **no learning curve**. C's advantage did not grow with the horizon: its pass rate is flat block to block, as is A's.
3. **C learned a lot of text, not a lot of capability.** 20 feedback steps produced 36 component edits (`system.md` ×11, `skills/sqlglot-dialect-functions` ×10, `tool_guidance.md` ×6, …). The always-on harness grew 15× to 2,822 tokens, over lithify's own 2,500 budget, and the whole harness reached 127 KB. Most edits re-describe conventions specific to one dialect or function, which rarely recur within 30 tasks.
4. **Feedback inflates exploration without producing proposals.** Each post-delivery failure marks the task "not first-pass", which keeps S low (k ≥ 1 on 46 of 60 tasks). But the next base rollouts usually pass the gates, so proposals are skipped. Most of C's cost is the feedback steps themselves (about $2.30 each).

An independent preliminary review (read-only, not anchored on this report) is run separately; see the PR discussion.
