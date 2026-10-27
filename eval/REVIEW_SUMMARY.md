# lithify: evaluation summary for independent review

**Package date:** 2026-10-27. **Repository:** `delvera-ai/lithify` (public), branch `eval/horizon-sqlglot` (draft PR #28). The archive is a `git archive` of that branch head plus this file. Everything below cites a path inside the archive.

**Who did the work:** the evaluation was designed, run, and analysed by an AI agent (Claude Code), with the owner approving each budget and design decision. Task texts were written by that agent. One independent read-only agent reviewed the final experiment without seeing its report. Treat all of this as unaudited until you have checked it yourself.

---

## 1. What lithify is and what was claimed

lithify (`README.md`, `docs/architecture.md`, `src/lithify/`) wraps a coding agent (Claude Code, Codex, Antigravity) in a self-improving *harness*: project instructions, skills, and memory rendered into `CLAUDE.md`/`AGENTS.md`/skills. Each task runs through the following stages:

1. **Propose → Probe → Compose:** candidate harness edits are tested against each other on the task, in disposable git worktrees.
2. **Gates:** the deterministic gates are the repository's tests, lint, and typecheck.
3. **Blind selector:** chooses among the deliverables that pass the gates.
4. **Reflector:** attributes each harness edit as *helped*, *hurt*, *no observed effect*, or *confounded*.
5. **Promotion:** edits that helped are promoted into the live harness.

A **dynamic exploration width k** is set from a stability score:

- Explore widely (k = `max_k`) while the harness keeps failing.
- Explore narrowly (k = 1) while it is improving.
- Run once (k = 0) once it is stable.

Two claims were tested:

1. **Cost:** after warm-up, lithify costs about what a plain agent run costs, unlike a fixed-k optimiser that pays for exploration on every task.
2. **Quality:** tasks run through lithify pass hidden acceptance checks more often than a plain agent does. Later, this became the question of whether the harness *improves capability over a horizon*.

**Summary of findings:**

- Claim 1 is supported.
- Claim 2 is **not** supported. On real pull requests, no quality difference was statistically meaningful.
- On the one repository with real headroom (sqlglot), the best variant passed 5 more hidden checks than the baseline across 60 tasks and never did worse, but the pre-registered test failed (p = 0.25). An independent review found no causal link between the learned harness and the wins.

---

## 2. Experiments run (chronological)

Spend is in USD on Claude, recorded in `eval/LEDGER.md`. Codex runs used a ChatGPT plan, cost $0, and token counts are recorded instead.

| # | Experiment | Where | Design | Result | Spend |
|---|---|---|---|---|---|
| 1 | Simulation sweep | `results/2026-10-23-sim-sweep/` | Mock agent, 14 tasks × 10 orders × noise {0, 0.1, 0.2} × {baseline, static, adaptive} | Adaptive never delivered less than static (30/30 cells). Token ratio adaptive/static: 0.75 → 0.85 → 0.92 as noise rises | $0 |
| 2 | Adapter conformance | `results/2026-10-23-conformance/` | 1 live task per CLI | Claude ✓; Codex ✓ after a fix (it rejected `--full-auto`); Antigravity untestable (quota) | $1.85 |
| 3 | Validators fixture pilot | `results/2026-10-23-validators-pilot/` | 8 tasks needing an undocumented audit convention; adaptive, holdout as gate | 8/8 delivered; first-pass 7/8. One exploration step learned the convention ($4.21), then every task passed first time | $4.86 |
| 4 | PR replay dev set (humanize) | `results/2026-10-23-pr-replay-dev/` | 2 dev PRs × 3 strategies | Found that the test-edit gate rejects correct solutions to behaviour-changing tasks (issue #15) | $9.03 |
| 5 | PR replay pilot (humanize, 10 PRs) | `results/2026-10-23-pr-replay-pilot/` | Baseline / static (k = 1 every task) / adaptive; holdout post-hoc | All three 10/10. Cost: baseline $0.09, static $21.90, adaptive $0.27 | $22.26 |
| 6 | PR replay full (tenacity, 22 PRs) | `results/2026-10-23-pr-replay-full/` | Same 3 strategies, Claude Haiku executor | Baseline 21/22 ($0.43), adaptive 21/22 ($0.81), static 21/21 ($65.51, stopped at its cap before PR 22) | $66.75 + superseded |
| 7 | Codex replications | `results/2026-10-23-pr-replay-codex/` | Baseline vs adaptive, Codex executor: tenacity 22, humanize 15 | Tenacity 21/22 vs **22/22**; humanize 14/15 vs **15/15** (37/37 vs 35/37) | $0 |
| 8 | Reflector fix, live check | `results/2026-10-23-reflector-check/` | Validators task, `auto_adopt = true`, after fixing the reflector prompt | Edit rated *helped* and auto-promoted; next task first-pass. Before the fix nothing was ever promoted (#13) | $0 |
| 9 | **Horizon (sqlglot, 60 PRs), pre-registered** | `results/2026-10-26-horizon/`, `eval/horizon/PREREGISTRATION.md` | A baseline / B adaptive / C adaptive + post-delivery feedback; Haiku; holdout post-hoc | A 35/60, B 38/60, C 40/60. Primary test **not met** (see §3) | $58.23 |

**Invalid or aborted data, kept and labelled:**

- `results/2026-10-23-pr-replay-aborted/`: the operator stopped live runs after a faulty process check. Excluded; spend counted.
- `results/2026-10-23-pr-replay-full/superseded/`: a Claude subscription limit silently turned sessions into empty failures. Excluded; spend counted; re-run.

The runner now detects limits and resumes cleanly.

**Totals:** about $127 for the 0.1.0 evaluation (experiments 1–8) and $58 for the horizon experiment.

---

## 3. The decisive experiment: horizon on sqlglot

**Pre-registered** (`eval/horizon/PREREGISTRATION.md`, commit `5defb42`, before any live run; horizon list frozen in `f964993`).

**Setup:**

- 60 consecutive merged sqlglot PRs (#7492 → #7796).
- Hidden check: the PR's own tests, run only after delivery.
- Each arm carries its own harness across tasks.

**Arms:**

- **C (adaptive + feedback):** after a task is scored, if the delivered work failed the hidden tests, that output is sent to `lithify feedback`, and the resulting proposal is adopted. This happens only after scoring, so any gain must come from the harness carried forward.

**Results** (from `results/2026-10-26-horizon/REPORT.md`):

| Hypothesis | Criterion | Result | Verdict |
|---|---|---|---|
| Stage gate | Baseline fails ≥ 15/60 | 25/60 | met (headroom exists) |
| **H1** | C − A ≥ 10 points on tasks 31–60, one-sided exact McNemar p < 0.05 | +6.7 points (19/30 vs 17/30), 2 wins / 0 losses, **p = 0.25** | **not met** |
| H2 | Gain larger on 31–60 than on 1–30 | +10.0 → +6.7 | not supported |
| H3 | C > B on 31–60 | +6.7, p = 0.25 | not significant |
| H4 | C ≤ $1.00 per task on 31–60 | $0.795 | met |
| Leak audit | Tag edits that copy past hidden-test expectations | 2 skills copy them; inert (no later task reused them, and no win depends on them) | leaks present |
| Safety | 0 invariant violations | 0 / 180 | clean |

**Exploratory (not pre-registered):**

- Over all 60 tasks, C beat the baseline on 5 and lost none (p = 0.031).
- B tied the baseline on 31–60.

**Process deviation, recorded:** B and C were stopped once, between tasks, by a stale global budget cap, then resumed from the exact task (`3b828e2`).

---

## 4. Why the experiment failed to show a capability gain (justified)

Each point cites its evidence. The independent review verified points 3–5.

1. **Ceiling effect on the first two repositories.** On humanize and tenacity the plain Haiku agent passed 10/10 and 21/22 hidden checks (`results/2026-10-23-pr-replay-{pilot,full}/`), so there was nothing left to improve. Only cost could be compared.

2. **lithify's learning signal is blind to the failures that matter.**
   - On sqlglot, **23 of the baseline's 25 failures passed the repository's own test suite**. The agent shipped plausible but wrong output.
   - lithify explores and learns only when gates fail. B explored on 6 of 60 tasks, all before task 21, and tied the baseline where it counted.
   - Tenacity #640 shows the same pattern: adaptive delivered a wrong answer the gates accepted, and never found out.

3. **The learned knowledge did not transfer, and the wins are not traceable to it.**
   - C ran 20 feedback steps and made 36 component edits (`system.md` ×11; one skill ×10).
   - For each of C's five wins, the trajectories show either an unrelated skill, no skill, a wrong memory path, or that B also passed without C's skills.
   - C read its 23 KB dialect skill on three late tasks and failed all three.
   - Most edits encode one-off, dialect-specific conventions that rarely recur within 30 tasks.

4. **Many tasks are under-specified for any harness.**
   - About 15 of the baseline's 25 failures hinge on exact output strings the task never states (e.g. `ENUM(` with no space).
   - About 5 test syntax the task never mentions.
   - Only the expected string itself helps here, so the post-hoc skills copied those strings. That produced the two leaks.
   - Task texts follow the PRs' own descriptions, which is realistic. But it means a large share of the "headroom" is not learnable capability.

5. **The mechanism worked against itself.**
   - Post-delivery feedback lowers stability, which raises k.
   - `skip_when_base_passes` then skips the probe, because the base rollout passes the gates.
   - Result: k ≥ 1 on 46 of 60 tasks, but **every task 31–60 ran exactly one execution**.
   - Feedback proposals were adopted **without being tested**, so nothing filtered them. The always-on harness grew 15× (185 → 2,822 tokens, past lithify's own 2,500-token budget). The whole harness reached 127 KB, including a stray `SKILL.md.orig` that validation did not catch.

6. **The evaluation was under-powered.**
   - One seed, 30 paired tasks in the primary window.
   - Same-configuration noise (A vs B after task 20, both at k = 0) is about 3 discordant tasks in 40. C's +2 is inside it.
   - A 10-point effect could not be resolved reliably at this n.

**What did hold up:**

- **Cost:** once its harness passes, adaptive costs what a plain run costs. On tenacity, static costs 156× adaptive per task after warm-up.
- **Safety:** no pipeline commit, push, branch, or leftover worktree in any live run.
- **Never worse:** adaptive with feedback never failed a task the baseline passed.
- **In-context learning works when the signal is clean:** the validators fixture, where a gate exposes the convention, shows it.
- **Lithify's own failure modes became tested fixes**, each merged with regression tests: #10, #12, #19, #21, #22, #27.

---

## 5. Recommendations

### Product, ranked by expected impact

1. **Validate before adopting (feedback and proposals).** Replay the failed task, plus 2–3 earlier tasks in the same area, with and without the edit. Adopt only if the hidden or spec check flips with no regression. This addresses points 3 and 5 (bloat, leaks, no causal link).
   *Test:* re-run C on sqlglot 31–60 and compare adopted count, harness size, and pass rate.
2. **Learn rules, not answers.** Classify each post-delivery failure as a *convention gap* (format or naming of an otherwise correct change) or a *capability gap*. Convention gaps should become general, checkable rules, for example "generators emit `NAME(` with no space; compare neighbouring `*_sql` methods", or a script that diffs against sibling dialect output. Never store literal expected values; add a validator rule that rejects them.
   *Test:* leak tags reach 0, and the share of later failures that are format diffs falls.
3. **Make feedback produce real exploration.** When stability drops because of post-delivery failures, `skip_when_base_passes` must not cancel the step. Run k rollouts and choose with a self-written spec test derived from the task, or a judge. Today the gates cannot distinguish the rollouts.
   *Test:* executions > 1 on tasks 31–60 (currently 0), pass rate, cost against H4.
4. **Size budgets and targeted retrieval for skills.**
   - Cap each skill (about 4 KB) and its description (about 300 characters).
   - Split omnibus skills.
   - Have `lithify validate` warn on on-demand skill size and stray files (`*.orig`).
   - Fix the memory path agents look for.
   - Log which skill was read before the decisive edit, so attribution becomes measurable.
5. **Do not record eval-environment facts as project knowledge.** Every run's harness absorbed facts like "ruff is not installed" and "uv is not on PATH". Filter them, or keep them in a run-local scratch area.

### Evaluation, required before any quality claim

6. **Choose tasks where the hidden check is learnable from the repository.** Flag or drop tasks whose tests check syntax the task never names. Prefer repositories with recurring conventions over one-off feature surface.
7. **Power:** at least 2–3 seeds per arm on the primary window, so run-to-run noise can be measured. Aim for at least 100 paired tasks to resolve 10-point effects. Report noise-adjusted differences.
8. **An executor with more headroom on the target repository,** and a matched control that gets the same number of extra attempts without harness carry-over. That separates *learning* from *best-of-n*.

---

## 6. File index

| Path | What |
|---|---|
| `eval/REVIEW_SUMMARY.md` | This document |
| `eval/LEDGER.md` | Every spend line, including aborted and superseded runs |
| `eval/RELEASE_READINESS.md` | 0.1.0 go/no-go (written before the horizon experiment) |
| `eval/horizon/PREREGISTRATION.md` | Hypotheses and analysis plan, committed before data |
| `eval/results/<date>-<experiment>/` | `results*.csv` (one row per task), `REPORT.md`, `raw/` evidence: task text, trajectories, gate reports, patches, hidden-test output, adopted harness, library |
| `eval/prs/<repo>/` | `prs.json` (selected PRs), `selection*.log`, `source/` (PR and issue text), `tasks/` (hand-written task texts), `drafts/` |
| `eval/pr_select.py`, `eval/pr_replay.py`, `eval/repos.py`, `eval/evalkit.py` | PR selection and replay harness |
| `eval/run_sequence.py`, `eval/fixtures/validators/` | Validators fixture and runner |
| `eval/sim_sweep.py`, `eval/audit.py`, `eval/draft_tasks.py` | Simulation sweep, safety and leak audit, task drafting |
| `src/lithify/`, `tests/` | lithify at the evaluated version |
| `docs/benchmarking.md` | Evaluation protocol and pitfalls |

**Known limitations of this package:**

- All analysis was done by AI agents.
- Task texts were written by the evaluating agent from PR descriptions, so wording choices could favour or hurt any arm equally, but were not blinded.
- There is a single seed per configuration.
- Antigravity was not evaluated.
- Raw trajectories are redacted (home paths, username, secret-shaped strings).


## Round-2 recovery: accounting and environment caveats (2026-10-27)

Round 1 is inconclusive, not evidence of no effect. The original primary test
was underpowered; shared baseline noise correlates the arm comparisons. Missing
per-task harness snapshots also prevent excluding an effect of always-on text.
The earlier claims that there was no causal link, or that most exact-string
failures were unlearnable, are not established by the available evidence.

The old Claude adapter retained only the last `result` event per process.
Background-notification turns can replace the substantive result, so per-turn
usage may be incomplete. Treat affected historical costs conservatively as lower
bounds, but do not infer missing dollars merely from a notification ending:
total_cost_usd and modelUsage are cumulative within a session. Comparing each
archived rollout's run.json to the surviving session's final cost-state found
all 199 costs match within CSV rounding (absolute difference <= $0.000051).
Thus this audit found no dollar undercount in archived rollouts. Editor-role
costs and authoritative invoices are outside this check. These are CLI cost
estimates, not authoritative billing records; the calibration measures the same
reported metric. Contract reference:
https://code.claude.com/docs/en/agent-sdk/cost-tracking#track-costs-in-streaming-input-mode

Read-only audit of all 199 archived rollout trajectories, matched by task id,
rollout label, and exact final assistant text to surviving local session logs:

| arm | archived rollout sessions | final turn responds to a task notification |
|---|---:|---:|
| A baseline | 60 | 2 (#7729 at position 45; #7771 at 53) |
| B adaptive | 65 | 3 (#7565 at 17; #7659 at 34; #7684 at 40) |
| C adaptive + feedback | 74 | 0 |

The classification requires the immediately preceding user message to begin
with `<task-notification>`; mentioning background execution alone does not count.
It includes a substantive final answer when that answer follows a notification.
Editor-role sessions without archived trajectories are outside this count;
zero flagged C rollouts does not establish complete accounting for C.
Evidence and per-call token/context metadata:
`eval/round2/ROUND1_SESSION_AUDIT.json`; reproducible audit script:
`eval/round2/audit_round1_sessions.py` (requires surviving local session logs).
No missing result events or missing dollar costs were reconstructed or invented.

The session metadata contradicts the static environment document: A reports
Claude Code 2.1.310, B/C 2.1.310–2.1.311, rather than 2.1.309. The surviving session logs also contain cost-state records with modelUsage.
The task-1 baseline cost-state reports claude-haiku-5-5, $0.02944021, and
22 unique assistant calls (context sizes 32,289–63,442 tokens). Its aggregate
usage matches the archived CSV: 52,150 input plus cache-write tokens,
1,083,661 cache-read tokens, and 16,356 output tokens. Thus the recorded
low task-1 cost is not explained by missing task-1 token usage. The audit JSON
retains this billing evidence for comparison with calibration; no correction
is applied to the frozen original CSVs.


The completed round-2 calibration (#7492, same unchanged task text) passed its
holdout at reported cost $0.04137888, 1.40744× the original recorded $0.0294,
under the 3× stop threshold. CLI 2.1.310 and modelUsage's claude-haiku-5-5
identifier match the baseline evidence. Forty calls emitted four results;
adding cumulative costs would wrongly report $0.15148946. Complete per-turn
usage is 57,187 input/cache-write, 2,197,168 cache-read, 15,956 output tokens.
The raw timestamps/recorded wall time include a large unexplained delay
(2,705.6 seconds vs 175.5), so this does not establish comparable throughput.
All 60 zero-token horizon oracles pass the base-fail/merge-pass/suite-pass
preflight. No replicates or plan/budget changes followed. See
`eval/results/2026-10-27-r2-calibration/REPORT.md` and the preflight report.
Round-2 cumulative ledger spend is $3.6681, including the invalid earlier run.
