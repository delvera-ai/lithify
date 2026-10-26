# 3C full run: PR replay on tenacity (+ Codex replications)

- **Dates:** 2026-10-23/24.
- **Code:** lithify `main` at `a0ab822`, installed non-editably in a scratch tool venv; it is identical for every strategy. The Codex humanize replication uses the same tool venv.
- **Spend (Claude):** baseline $0.43, adaptive $0.81, static $65.51. Codex runs on the ChatGPT plan, $0.
- **Repository:** [jd/tenacity](https://github.com/jd/tenacity) (Apache-2.0), 22 evaluation PRs merged 2026-02 to 2026-10, in merge order, one stream. Protocol as in the pilot ([`../2026-10-23-pr-replay-pilot/REPORT.md`](../2026-10-23-pr-replay-pilot/REPORT.md), `docs/benchmarking.md`): post-hoc holdout only, existing suite as the gate, `max_k = 2`, adopt-all.
- **Contamination note:** several tenacity PRs in this window were themselves written with AI assistance (co-author trailers), and all were merged in 2026. Memorisation risk is lower than for older history but not zero.

## Validity

- **Superseded first run.** The Claude session limit was hit partway through static's task 7. Every later session returned only the limit notice, so those tasks recorded empty failures. Baseline's last task was hit as well. Those rows are kept in `superseded/`, with their spend counted, and are excluded. `eval/pr_replay.py` now detects limit signatures, discards the affected task and stops; `--resume` continues with the strategy's state exactly as it was before that task. lithify itself now does the same (#21).
- **Earlier aborted attempt.** An operator error killed live runs (`../2026-10-23-pr-replay-aborted/`). Those rows are excluded and their spend is counted.
- **Static stopped at its $65 cap** before the last PR (#741), so static is reported on PRs 1–21. Paired comparisons below use those same 21 PRs.
- **The static re-run was interrupted once by the session limit** (at task 16) and resumed from that task. Nothing was recorded for the interrupted attempt.

## Results (Claude Haiku executor; 95% Wilson intervals)

| strategy | PRs | holdout pass | first-pass | executions | role sessions | cost | always-on harness |
|---|---|---|---|---|---|---|---|
| baseline | 22 | 21/22 [0.78, 0.99] | 22/22 | 22 | 0 | $0.43 | 186 → 186 |
| adaptive | 22 | 21/22 [0.78, 0.99] | 22/22 | 24 | 2 | $0.81 | 186 → 186 |
| static | 21 | **21/21** [0.85, 1.00] | 20/21 | 82 | 105 | $65.51 | 186 → **1,656** |

On the common PRs 1–21: **static 21/21, adaptive 20/21, baseline 20/21**. The only failure for adaptive and baseline is **#640** (reraise the underlying exception when `TryAgain` wraps a cause). Static passed it. This is the one real-PR case where paying for exploration on every task fixed something the others missed. It's a single task, so it is not statistically meaningful.

**Cost per task from task 5 on:** static $3.23, adaptive $0.021, so **static costs 156× adaptive**. Adaptive explored at k = 2 on tasks 1–2 and k = 1 on 3–4. Both bases passed, so it skipped proposals; it was at k = 0 from task 5. Its only role sessions were two blind selections.

Static's cost rose from about $2 to about $3.50 per task, tracking its harness growth (every session reads it). Summed task wall time: baseline and adaptive 37 min each; static 744 min (about 12.4 h), about 35 min per task.

### Codex replications (executor and all roles on Codex's default model)

| repository | strategy | holdout pass | input tokens (cached excluded) | k |
|---|---|---|---|---|
| tenacity (22) | baseline | 21/22 [0.78, 0.99] (failed #640) | 454,805 | 0 × 22 |
| tenacity (22) | adaptive | **22/22** [0.85, 1.00] | 494,834 (+9%) | 2 2 1 1, then 0 |
| humanize (15) | baseline | 14/15 [0.70, 0.99] (failed #286) | 256,189 | 0 × 15 |
| humanize (15) | adaptive | **15/15** [0.80, 1.00] | 560,068 (+119%) | 2 2 2 1 1, then 0 |

Across the Codex runs, adaptive passed 37/37 and baseline 35/37. Adaptive won 2 PRs outright and lost none. The pattern is consistent, but with two discordant pairs it is not significant.

## Safety and failure audit (`eval/audit.py`)

- **Pipeline invariants:** after every task in every strategy, HEAD and branches were unchanged by `lithify run` and only the main worktree remained. **0 violations.**
- **Agent git use inside probes:** `git stash` only. No commit, push or branch.
- **Writes outside the probe worktree (Claude executor only):** venvs under `/tmp` and network `pip install`s (adaptive 8, baseline 3 trajectories). One static-run agent ran `pip install` against the shared gate environment; it failed only because that environment has no pip. Codex's `workspace-write` sandbox prevented every such write in the Codex runs. The README safety model now states this.
- **Test-edit flags:** none in these runs.
- **Adopted harness edits** (static only; adaptive and baseline adopted nothing):
  - Repository conventions (the change contract across sync and async retry modules, deprecation patterns, override marking), plus helper scripts (`check_changed.py`, `list_overrides.py`, `run_tests.py`): **acceptable**.
  - Eval-environment facts in `tool_guidance.md`/`memory.md`/scripts ("`uv` not on PATH", "a `/tmp` venv dies in ensurepip", zsh quoting, the scratch interpreter path): **not acceptable** as repository knowledge. This is the third run in which static absorbed them.
  - Task-specific behaviour recorded as permanent knowledge (`TryAgain`/`retry_never` semantics from #640): **borderline**. It is true library behaviour, but derived from one task.
  - **Size:** the harness reached 76 KB, including a 39.7 KB skill. `lithify validate` budgets only always-on text, so on-demand skills of any size pass. **Gap:** add a per-skill size warning.
  - No edit tells the agent to edit or skip tests; the guardrail is intact.
- **Failure taxonomy:**
  - **#640 (adaptive, baseline, Codex baseline):** *harness did not cover the evaluated behaviour*. The base harness had no knowledge of `TryAgain` semantics, and adaptive never explored on #640, because its base rollout passed the existing suite. That is the cost of trusting gates that don't test the change. Static, exploring anyway, carried the knowledge.
  - **humanize #286 (Codex baseline):** same class; Codex adaptive passed it after early exploration.
  - **Superseded and aborted rows:** *outcome variance from external causes* (subscription limit, operator error), excluded from comparison.

## What this means

- **Cost claim: supported, strongly.** Adaptive costs about what a plain agent costs once its first tasks pass (1:156 against static on tenacity).
- **Quality: not separable on these repositories.** Static (21/21) and adaptive with Codex (37/37) each rescued one or two PRs the plain agent missed. That's suggestive, but the intervals overlap.
- **Adaptive's blind spot is visible.** `skip_when_base_passes` trusts the gates, and a task whose risk the existing tests don't cover (#640) is never explored. The planned ablation (adaptive with `skip_when_base_passes = false`) would measure this trade directly; it was not run (budget).
