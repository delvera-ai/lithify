# Phase 0b: task-12 causal test (pre-registration, revised)

Status: **revised per owner decision, not yet run.** Runs wait on the harness-injection PR (Phase 1 item 1 slice),
which must be merged first. Budget cap: **$5** (`--limit-usd 5`, `--total-cap` and `--budget-glob "*-r2-*"` on every
run).

## Question

Does the optimizer skill make the held-out task 12 (sqlglot#7549, Spark `LATERAL VIEW EXPLODE` optimizer crash)
pass, under the same executor and conditions as A2–A5, and is any effect specific to the skill's content?

Reference: task 12 never passed in five A runs (A1–A5), so the starter harness is 0/5 on it.

## Reconstruction of harness@12: not recoverable exactly (unchanged)

The owner's plan asked for C's harness as it stood before task 12. The routes checked:

1. **Round-1 C clone (git history).** Not on disk.
2. **Per-task `applied.diff`.** Records code and `.lithify/state.json` only, not harness files.
3. **Library.** `library/` holds one entry, not enough to rebuild the harness.
4. **Round-1 session directories.** No work directory under `/private/tmp/claude-501` contains the task-12 text.
5. **Round-1 source.** `r2-noise-scratch/round1-source/.lithify/harness` is the starter harness, with empty history.

The approximate fallback is used. The stand-in for harness@12 is the round-1 C **final** harness
(`raw/sqlglot-adaptive-feedback-claude_claude-haiku-5-5/final-harness/`).

Contamination checks, as the owner asked:
- No file in the final harness mentions EXPLODE, LATERAL or UNNEST (`grep -ril` finds nothing).
- Tasks 19 (`20261026-202726-postgres-dialect-when-an-unnest`) and 47 (`20261027-105620-optimizer-sqlglot-optimizer-qual`)
  record `promoted: []` and `proposal: null` in their per-task `state.json`. Neither produced a C adoption.

## Arms (5 runs each, 20 runs total)

| arm | harness | role |
|---|---|---|
| (c) | starter harness + only `skills/sqlglot-optimizer-rewrites` (final version) | **primary**: is the skill alone sufficient? |
| (d) | starter harness + only `skills/sqlglot-optimizer-placebo` | **control**: placebo skill with the same trigger and similar length |
| (a) | full final C harness | secondary, approximate |
| (b) | (a) minus `skills/sqlglot-optimizer-rewrites` | secondary, approximate |

- **Starter harness:** the round-1 starter (`round1-source/.lithify/harness`). The starter-harness reference is
  A1–A5 at 0/5, not new runs.
- **Placebo skill:** `eval/round2/placebo/sqlglot-optimizer-placebo/SKILL.md`, written by a separate agent session
  that did not read the real skill body and had only the frontmatter trigger and a length target. It has generic
  optimizer advice and no node-copying, alias-column or EXPLODE/LATERAL/UNNEST content. Frozen before any run.
  SHA-256 `6c53d7165196dbd578e72334231804a5dc2b9337e5d5f8c926ef81843cc94f09`, 6,309 bytes. Any edit to it after
  this point voids the test.

## Conditions

- Executor `claude@claude-haiku-5-5`, editor roles on the CLI default (`claude`).
- **Build:** the new build. The harness-injection PR is merged to `main` first, and the build is that commit. The
  build is recorded per run. The owner's reference is A2–A5 at `89020d7`, so the build is not identical to A2–A5:
  this will be stated as a deviation unless the new commit only adds test-visible injection code.
- `--k 0 --no-escalate`, timeout 900 s, one task (task 12, holdout of PR #7549, extracted from its merge commit).
- Each run in its own clone and state, with the arm's harness injected by `--harness-dir`.
- Record per run: holdout pass, skills read (from the trajectory), files changed, cost, and the harness content hash
  written to `outcome.json`.

## Decision rule (fixed in advance)

- **Skill sufficient:** (c) passes in at least 3/5 runs and (d) passes in at most 1/5.
- **Placebo effect:** (c) and (d) both pass in at least 3/5 runs.
- **Anything else:** inconclusive.

The secondary arms (a) and (b) are reported as approximate. They do not enter the decision rule.

## Cost

Baseline cost is $0.0324 per task on average (round 2, Phase 0). Twenty single-task runs should cost about $1 at
most, under the $5 cap. Any cap stop is reported as a deviation.

## Recording

Results go in `eval/results/<date>-r2-task12/`. The ledger in `eval/LEDGER.md` gets one line per run. The report goes
to tracking issue #29.
