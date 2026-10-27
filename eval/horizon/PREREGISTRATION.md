# Horizon experiment: pre-registration

Committed **before** any live run of this experiment. The analysis below is fixed: results are
reported against it whatever they show, and any deviation is listed in the report as a deviation.

## Question

Does lithify's adaptive lifecycle make a coding agent more capable on a real, complex codebase
over a long horizon, as measured by hidden tests, compared with the same agent without lithify?

The 0.1.0 evaluation could not answer this. On humanize and tenacity the plain agent already passed
almost every hidden test (ceiling). And lithify only learned when the *existing* tests failed, so a
task that passed its gates but was wrong (tenacity #640) never fed back into the harness.

## Design

- **Repository:** [tobymao/sqlglot](https://github.com/tobymao/sqlglot) (MIT): a SQL parser and
  transpiler across 30+ dialects with strong non-local conventions (tokenizer, parser and generator
  per dialect), about 1,400 tests in about 50 s, and a maintained `AGENTS.md`. Every arm starts with it.
- **Tasks:** merged human PRs since 2026-04-01 that change source and tests, selected by
  `eval/pr_select.py` (same filters as 0.1.0). The oldest ~20% form the development set (harness
  debugging only); the **first 60 evaluation PRs in merge order** are the horizon. Task texts are
  redacted by hand as in 0.1.0 (`eval/prs/sqlglot/tasks/`).
- **Executor:** `claude@claude-haiku-5-5`; editor roles on Claude Code's default model. Gates are the
  existing suite only. The holdout is the PR's own tests, run post-hoc on the applied patch, and is
  never a gate.
- **Arms** (each with its own clone; `.lithify/` carried across tasks; adopt-all policy):
  - **A — baseline:** `--k 0 --no-escalate`; the starter harness never changes.
  - **B — adaptive:** lithify's schedule, `max_k = 2`; learns only from gate failures.
  - **C — adaptive + feedback:** B, plus, after a task is scored, if its delivered work failed the
    holdout, that output is passed to `lithify feedback` (post-delivery learning) and the resulting
    proposal is adopted. Feedback reaches lithify only after the task's score is final, so it cannot
    improve that task, and any gain of C over A comes from the harness carried forward.
- **Code:** the same lithify build for all arms (recorded in every result row).

## Stage gate (headroom)

Arm A runs first (about $3). **Continue to B and C only if A fails ≥ 15 of the 60 holdouts (≥ 25%).**
Otherwise stop and report: the repository is too easy to show capability gains.

## Hypotheses and analysis

- **H1 (primary): capability gain over the horizon.** On evaluation tasks **31–60**, C's holdout pass
  rate exceeds A's by **≥ 10 percentage points**, with a one-sided exact McNemar test on the paired
  outcomes at **p < 0.05**.
- **H2: the gain comes from the lifecycle.** C − A on tasks 31–60 is larger than C − A on tasks
  1–30 (descriptive; reported with both differences and their Wilson intervals).
- **H3: feedback adds over today's lithify.** On tasks 31–60, C's pass rate exceeds B's (one-sided
  exact McNemar; reported, not required for H1).
- **H4: cost stays bounded.** C's mean cost per task over tasks 31–60 is **≤ $1.00**. (This replaces
  an earlier informal "≤ 3× baseline" bound. Each feedback step costs about 50 executions, so that
  bound would fail whenever A fails more than ~10% of tasks. The change is made before any data.)
- **Secondary, descriptive:** first-pass rate, k and S trajectories, always-on harness size,
  adopted components, rolling 10-task pass rate per arm, tokens per task.

## Validity rules

- Tasks interrupted by an agent-CLI limit are discarded unrecorded and resumed (`--resume`).
  Nothing else is excluded after the fact.
- **Leak audit:** every adopted harness edit is audited (`eval/audit.py` plus manual tagging). An
  edit that copies a specific expected value from a past holdout is tagged. A sensitivity analysis
  re-scores H1 treating any later task whose pass used such a copied fact as a failure.
- **Safety:** zero pipeline invariant violations (`eval/audit.py`).

## Budget and stop rules

Total **$100**: A ≤ $5, B ≤ $25, C ≤ $60, development-set debugging ≤ $10. Each arm stops cleanly at
its cap. If a cap stops an arm before task 60, H1 is evaluated on the tasks all arms completed, and
the report says so.
