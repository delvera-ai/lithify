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
| Leak audit | tag every adopted edit that copies an expected value from a past holdout; re-score H1 without passes that used one | **2 adopted skills copy past hidden-test expectations** (tagged *not acceptable*): `skills/sqlglot-data-types/SKILL.md` quotes `CAST('a' AS STRING COLLATE foo)` from the COLLATE task's tests (#7630); `skills/sqlglot-upsert-on-conflict/SKILL.md` lists #7760's exact `ON CONFLICT` targets. No later task reused them, and none of C's 5 wins depends on a copied value (0 of 33 new expected strings found) | **leaks present but inert**; H1 unchanged in the sensitivity analysis. (Corrected after the independent review: the first version of this report checked only the wins and called the audit clean.) |
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

## Independent review (read-only agent, not shown this report)

Agreed verdict: no meaningful improvement. Additional findings, verified:

- **C's 5 wins are not traceable to adopted knowledge.** Task 12 loaded a skill about unrelated invariants; task 45 read no skill (the relevant one was adopted at task 46); task 14 looked for `.lithify/memory.md` (wrong path); B also passed tasks 30 and 39 without C's skills. Conversely, C read its 23 KB `sqlglot-dialect-functions` skill (rewritten by feedback 9 times) on tasks 56, 58 and 60 and failed all three.
- **Noise floor:** A and B, both at k = 0 with near-identical harnesses after task 20, still disagree on about 3 of 40 tasks. C's +2 on tasks 31–60 is within that.
- **Most failures are under-specified exact output:** about 15 of A's 25 failures hinge on output conventions the task never states, and about 5 test syntax the task never mentions (tasks 20, 33, 51, 58). Post-hoc skills then copy those strings (the leaks above).
- **Feedback raised k without probing:** `skip_when_base_passes` skipped every proposal on tasks 31–60 (executions = 1 throughout).
- **Hygiene:** a stray `skills/sqlglot-dialect-functions/SKILL.md.orig` (14.5 KB) shipped in the harness; `lithify validate` did not flag it.

Ranked fixes (from the review, to be tested): (1) probe a feedback proposal on a replay of the failed or related past tasks before adopting it; (2) separate convention gaps from capability gaps, writing general rules, never literal expected values; (3) let feedback trigger real re-exploration (k rollouts plus a spec test or judge) instead of being cancelled by `skip_when_base_passes`; (4) per-skill size budgets, targeted retrieval, and stripping stray files; (5) make the evaluation decisive with 2–3 seeds per arm and flags for tasks whose holdout tests unnamed syntax.
