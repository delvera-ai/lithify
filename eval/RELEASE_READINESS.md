# lithify 0.1.0 — release readiness

**Date:** 2026-10-24. **Evidence:** `eval/results/`, `eval/LEDGER.md`, tracking issue #6.
**Spend:** $126.77 of the $150 evaluation budget (Claude); Codex runs on the owner's ChatGPT plan ($0).

## Recommendation: **GO for a 0.1.0 alpha**, with the claims scoped as below

The release is ready **if the README makes only the claims the evidence supports**: the docs PR
that adds this file does exactly that.

- **Ready to claim:** the cost claim. Once the harness passes, adaptive costs about the same as
  a plain agent run, while a fixed-k optimiser (static) pays about $2–3.50 per task forever.
- **Not ready to claim:** that lithify makes agents pass hidden tests more often than a plain agent.
  On real PRs the plain agent already passed almost everything (ceiling effect). Adaptive was never
  worse and slightly better with Codex, but no difference is statistically meaningful.

Do not market quality improvements for 0.1.0. Do say: safe defaults, an evidence-gated harness,
and cost close to a plain run.

## Criteria

| criterion | status | evidence |
|---|---|---|
| CI green on Linux and macOS, Python 3.11–3.13; `claude plugin validate .` passes | **met** | Ruleset 25715160 requires all 6 `test` jobs, `plugin` (strict validate, Claude Code 2.1.309) and `sim-sweep`; every merge to `main` since #5 passed them |
| All three adapters pass conformance on current CLI versions, or the README states which are unsupported | **met, with Antigravity unverified** | claude 2.1.309 ✓ and codex 0.163.0 ✓ end to end (`eval/results/2026-10-23-conformance/`); codex needed #12. agy 1.4.3: adapter fixed against a captured error envelope (#12), plugin install ✓, but no successful live run (quota). README now says agy is unverified |
| Every install path in the README verified from a clean environment | **met, one documented gap** | `uv tool install git+…` ✓, Claude Code marketplace and plugin ✓, Codex marketplace + `codex plugin add` ✓, `agy plugin install` ✓ (`eval/results/2026-10-23-validators-pilot/REPORT.md`). The Claude SessionStart hook prints the hint ✓. The Codex plugin hook does **not** run under `codex exec` 0.163.0 (`plugin_hooks: removed`); the README documents a user-level hook workaround. Release build: the wheel and sdist install in a clean container and `lithify demo` from the wheel matches the README |
| Adaptive holdout pass rate not meaningfully worse than static; cost per task after warm-up clearly below static's | **met** | See the results table. Holdout: adaptive 10/10 vs static 10/10 (humanize); 20/21 vs 21/21 on the 21 tenacity PRs both ran (adaptive missed only #640). Cost per task from task 5 on: adaptive ≈ $0.02 vs static ≈ $3 (**≈ 1:150**) |
| Zero safety-audit violations; every harness edit audited | **met for the pipeline; agents' machine-level writes documented** | `eval/audit.py`: 0 invariant violations across every live task (no commit, push, branch or leftover worktree by the pipeline). No agent ran `git commit` or `git push` in a probe (31 `git stash` only). Claude-executor agents wrote outside the worktree (`/tmp` venvs, network `pip install`); one tried to install into the gate environment and failed only because it had no pip. Codex's sandbox prevented this. Documented in the README safety model. Adopted harness edits are audited in the 3C reports; none instructs the agent to edit or skip tests |
| No open `release-blocker` issues | **met** | No issues carry the label. Open: #15 (enhancement, partly addressed by #22), #6 (tracking) |

## Results (95% Wilson intervals; post-hoc holdout = the PR's own tests, never a gate)

| repository (evaluation PRs) | executor | baseline | static | adaptive |
|---|---|---|---|---|
| humanize (10) | Claude Haiku | 10/10 [0.72, 1.00] · $0.09 | 10/10 [0.72, 1.00] · $21.90 | 10/10 [0.72, 1.00] · $0.27 |
| tenacity (22) | Claude Haiku | 21/22 [0.78, 0.99] · $0.43 | 21/21 [0.85, 1.00] · $65.51 (first 21 PRs; stopped at its $65 cap) | 21/22 [0.78, 0.99] · $0.81 |
| tenacity (22) | Codex | 21/22 [0.78, 0.99] | — | 22/22 [0.85, 1.00] (+9% tokens) |
| humanize (15) | Codex | 14/15 [0.70, 0.99] | — | 15/15 [0.80, 1.00] (+119% tokens) |

Fixture (`eval/fixtures/validators`, an unwritten audit convention): adaptive delivered 8/8 with
first-pass 7/8. One exploration step learned the convention ($4.21), and every later task passed
first time at about $0.01–0.20.

## Known gaps: triage

| gap | decision | reason / evidence |
|---|---|---|
| CLI coverage 0% | **fixed** (#23) | in-process tests: `cli.py` 83%, total 86% |
| `auto_adopt` never promoted (reflector prompt) | **fixed** (#19) | verified live: `helped`, then auto-promoted (`eval/results/2026-10-23-reflector-check/`) |
| Agent limits recorded as empty failures | **fixed** (#21) | the task stops with `LimitReached` |
| Test-edit gate discards correct behaviour-changing work | **mitigated** (#22); rest deferred in #15 | work saved as `needs-review.patch` |
| Default `max_k = 3` | **changed to 2** (#25) | all quality data was measured at 2; k=2 cost 2.3× k=1 for the same outcome on the one live exploration task |
| Stability thresholds (0.4 / 0.8 / window 10) | **unchanged (deferred)** | Too little development-set signal to tune on. Live adaptive runs reached k = 0 by task 5 on real PRs; on the fixture S peaked at 0.76 (below cruise) because one failure stays in the window. Revisit with more failing tasks |
| Middleware hooks (C8) not rendered | **documented (deferred)** | no evaluation scenario exercised hooks |
| Antigravity has no tool trajectory | **unmeasured (deferred)** | agy quota exhausted during evaluation |
| Untracked files not copied into probes | **documented** | also affects gitignored generated files (`_version.py` in both PR-replay repos) |
| Role sessions use executor permission flags | **deferred** | read-only flags for `select`/`reflect` would need live verification per CLI. Codex's sandbox already confines writes |
| Blind selector runs between bases of one harness | **deferred, recommended for 0.2** | about $0.18 per task, about 90% of those tasks' cost (validators pilot tasks 2–4) |

## Remaining owner actions (not done by the agent)

1. Configure PyPI trusted publishing for workflow `release.yml`, environment `pypi`
   (the environment already requires the owner's review and only deploys `v*` tags).
2. Bump the version if needed (`pyproject.toml`, `plugin.json`, `.claude-plugin/plugin.json`,
   `.codex-plugin/plugin.json`), merge, then tag `v0.1.0`.
3. Optionally submit to the Claude Code and Codex plugin directories.
4. Optionally merge or close the four Dependabot GitHub-Actions bumps (#1–#4).
