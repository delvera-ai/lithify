# 3C pilot: PR replay on humanize

- **Date:** 2026-10-23. **Code:** lithify `main` at `a0ab822` (lithify installed non-editably in a scratch tool venv) plus the eval scripts on this branch.
- **Spend:** $22.26 (baseline $0.09, static $21.90, adaptive $0.27).
- **Repository:** [python-humanize/humanize](https://github.com/python-humanize/humanize) (MIT). The pilot uses the first 10 PRs of the evaluation split in merge order: #250, #286, #297, #318, #320, #328, #329, #354, #334, #392 (merged 2025-04 to 2026-09). One stream, merge order, no shuffling.
- **Configuration:** executor `claude@claude-haiku-5-5`; every editor role on Claude Code's default model; `max_k = 2` (adaptive); gates are the repository's existing test suite only. **The holdout is post-hoc only:** the PR's own test files are copied in after delivery, run against the applied patch, and removed, so no strategy ever sees them. Adoption: `--adopt all` (`auto_adopt = false`; every proposal adopted after the task; see #13).

## Protocol

`eval/pr_select.py` keeps a merged, human-authored PR only if, at its base, the existing suite passes and the PR's test files fail; at the merge commit the PR's tests pass; and the base's existing tests still pass against the merged source. Of 107 humanize PRs since 2023-06, 19 qualify (`eval/prs/humanize/selection.log`). The oldest 4 form the development set and are used only to debug the harness (`../2026-10-23-pr-replay-dev/`). 5 PRs were excluded because they change behaviour that existing tests pin. lithify's default test-edit gate makes those undeliverable for every strategy (#15).

Task texts (`eval/prs/humanize/tasks/`) were written by hand from each PR's title, body and linked issues (`source/`). They describe behaviour and the public API the tests use, with implementation hints removed. Every expected output quoted in a task was checked against the merge commit. `eval/pr_replay.py` gives each strategy its own clone. Every task resets the code to the PR's base and carries the strategy's `.lithify/` forward.

## Results

| strategy | holdout pass (95% Wilson) | first-pass | executions | role sessions | cost | cost/task | wall |
|---|---|---|---|---|---|---|---|
| baseline | 10/10 [0.72, 1.00] | 10/10 | 10 | 0 | $0.09 | $0.009 | 7 min |
| static | 10/10 [0.72, 1.00] | 10/10 | 34 | 48 | $21.90 | $2.19 | 62 min |
| adaptive | 10/10 [0.72, 1.00] | 10/10 | 12 | 1 | $0.27 | $0.027 | 7 min |

**Quality: no difference, and none was detectable.** Plain Haiku with the starter harness solved every task, so this set has no headroom. With n = 10 at a ceiling, the intervals are identical and wide.

**Cost: clear separation.** Static paid for a full Propose→Probe→Compose step on every task: $1.58–2.97 each, 81× adaptive in total. Adaptive's cost is 3× baseline's in absolute terms ($0.27 vs $0.09), and $0.18 of that is one blind-selector session at task 1. From task 3 onwards (k ≤ 1, then k = 0 from task 5) adaptive cost exactly what baseline did, $0.01 per task.

Cumulative cost (USD):

| after task | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.01 | 0.01 | 0.02 | 0.03 | 0.04 | 0.05 | 0.06 | 0.07 | 0.08 | 0.09 |
| static | 1.89 | 3.46 | 6.26 | 7.25 | 9.60 | 12.57 | 14.92 | 17.05 | 19.83 | 21.90 |
| adaptive | 0.18 | 0.19 | 0.21 | 0.21 | 0.22 | 0.23 | 0.24 | 0.25 | 0.26 | 0.27 |

**k and S:**
- adaptive: k = 2 2 1 1 0 0 0 0 0 0. Every base passed, so proposals were always skipped, and S rose 0.2 → 1.0 by task 5.
- static: k = 1 throughout. S peaked at 0.91, then fell to 0.76–0.78 as its own harness churn grew.

**Always-on harness:**
- baseline and adaptive: unchanged at 189 tokens.
- static: 189 → 973 tokens after 6 adoptions (3 skills, a 6 KB helper script, system.md, memory.md, tool_guidance.md).

## Safety and failure audit (pilot)

- **Invariants** (checked after every task): HEAD and branches unchanged by `lithify run`; one worktree (main) remaining; for all 30 tasks.
- **Test-edit flags:** one, static #286 `dom-1`. It changed `pytest.raises(Exception)` to `pytest.raises(FileNotFoundError)` in an existing test. That is a **strengthening** edit flagged as a weakening: a false positive of the same class as the append-only case fixed during development (the gate counts any rewritten line). No harm resulted, because other candidates passed and were selected.
- **Adopted harness edits** (static only):
  - Repository conventions (lazy stdlib imports in `number.py`/`time.py`, the ruff PT006 parametrize style) and a reproduce-before-fix procedure: **acceptable**.
  - `tool_guidance.md` and `memory.md` facts about the eval environment ("ruff is not installed", the scratch interpreter path): **not acceptable** as repository knowledge. Same class as 3B's "host is macOS".
  - Nothing instructs the agent to edit or skip tests.
  - None of the growth changed an outcome (all strategies 10/10). Taxonomy: *harness edit did not address the evaluated behaviour*.
- **Failures:** none on the evaluation set. On the development set, #142 failed for every strategy because the test-edit gate rejected every correct candidate (#15).

## What this means

- The **cost** claim holds on real PRs. Once the harness passes, adaptive costs the same as a plain run, while a fixed-k optimiser pays about $2 per task forever.
- The **quality** claim cannot be tested on this repository with this executor: there are no failures to fix. The full run needs tasks where the baseline fails, such as harder repositories, larger PRs, or tasks that hinge on unwritten conventions.
