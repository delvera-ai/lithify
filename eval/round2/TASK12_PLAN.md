# Phase 0b: task-12 causal test (pre-registration, draft)

Status: **drafted, not run.** Runs need a runner change (harness injection) and the owner's confirmation of the
approximation below. Budget cap for this test: **$5** (`--limit-usd 5`, `--total-cap` and `--budget-glob "*-r2-*"`
on every run).

## Question

Does `sqlglot-optimizer-rewrites` (with the rest of the harness) make the held-out task 12 (sqlglot#7549,
Spark `LATERAL VIEW EXPLODE` optimizer crash) pass under the same executor, build and conditions as A2–A5?

Round-1 baseline: task 12 never passed in five A runs (A1–A5). The starter harness is 0/5 on it.

## Reconstruction of harness@12: not recoverable exactly

The owner's plan asks for C's harness as it stood before task 12 (after adoptions at tasks 2, 3, 4, 5 and 11). I
checked each route:

1. **Round-1 C clone (git history).** Not on disk. `~/.cache/lithify-dev/horizon` holds only the round-1 results
   and raw directories.
2. **Saved proposal directories / per-task diffs.** `raw/sqlglot-adaptive-feedback-…/NN-pr…/applied.diff` records
   code and `.lithify/state.json` only. It does not record harness files, so the adoptions at tasks 2–5 and 11
   cannot be replayed from it.
3. **Library.** `library/` holds one entry (`20261026-160938-doris-and-starrocks-dialects-bot`), which is not
   enough to rebuild the harness.
4. **Round-1 session directories.** No work directory under `/private/tmp/claude-501` contains the task-12
   task text (`LATERAL VIEW EXPLODE(items) ci AS ci`).
5. **Round-1 source.** `r2-noise-scratch/round1-source/.lithify/harness` is the starter harness, with an empty
   `state.json` history.

**Fallback (the owner's rule, label "approximate").** Use the round-1 C **final** harness, copied from
`raw/sqlglot-adaptive-feedback-claude_claude-haiku-5-5/final-harness/`, as the stand-in for harness@12. The
final harness includes adoptions made after task 12, so arm (a) is "final harness", not "harness@12". Every
result from this test is labelled approximate.

## Arms (5 runs each, 15 total)

| arm | harness | question |
|---|---|---|
| (a) | final C harness (approximate harness@12) | does the harness pass task 12? |
| (b) | final C harness minus `skills/sqlglot-optimizer-rewrites` | does the pass depend on that skill? |
| (c) | starter harness + only `skills/sqlglot-optimizer-rewrites` | is the skill alone sufficient? |

Starter harness: the round-1 starter harness (`round1-source/.lithify/harness`).

## Conditions

- Executor `claude@claude-haiku-5-5`, editor roles on the CLI default (`claude`), build `89020d7`, as in A2–A5.
- `--k 0 --no-escalate`, timeout 900 s, one task (task 12, holdout of PR #7549, extracted from its merge commit).
- Each run in its own clone and state. Record: holdout pass, skills read (from the trajectory), files changed,
  cost.
- Harness injection is needed: `eval/pr_replay.py` and `eval/round2/run_a_replicates.py` start from the eval
  setup and have no option to start from a supplied harness or skill subset. This change is required before any
  run and goes into a separate PR for review.

## Decision rule (fixed in advance)

- **Causal support:** (a) passes in at least 3/5 runs and (b) passes in at most 1/5.
- **Skill sufficient:** (c) passes in at least 3/5.
- **Anything else:** inconclusive.

Because the arms use an approximate harness, a causal reading is labelled "approximate" in any report. It is not
a confirmatory result for the round-1 harness@12.

## Cost

A baseline runs cost $0.0324 per task on average (round 2, Phase 0). Fifteen single-task runs should cost well
under $1, far below the $5 cap. Any cap stop is reported as a deviation.

## Recording

Each run: arm, run index, holdout pass, skills read, files changed, cost, and the lithify build (`89020d7`). Results
go in `eval/results/<date>-r2-task12/`. The ledger in `eval/LEDGER.md` gets one line per run.
