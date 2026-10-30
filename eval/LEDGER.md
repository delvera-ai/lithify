# Evaluation spend ledger

Caps: pilot (3B) $25; total $150. Cost is the sum of `usage.cost` from every `outcome.json` produced, plus any role costs logged by the eval scripts. Codex and Antigravity may not report dollars: their token counts are recorded and the cost estimated (marked `est`).

| date | phase | runs | cost USD | cumulative USD | notes |
|---|---|---|---|---|---|
| 2026-10-23 | 3A sim sweep | 90 simulated | 0.00 | 0.00 | mock agent, no credentials |
| 2026-10-23 | 3B raw CLI captures | 3 (claude, codex, agy) | 0.0027 | 0.0027 | codex: 54,232 in (48,768 cached) / 126 out tokens, $ not reported; agy: quota error, 0 tokens |
| 2026-10-23 | 3B conformance claude | 1 task, k=1 | 1.8548 | 1.8575 | executions $0.033, editor roles ≈ $1.82 |
| 2026-10-23 | 3B conformance codex | 1 task, k=1 | 0.00 (est) | 1.8575 | 133,905 in / 995,584 cached / 9,937 out tokens; Codex reports no $ (ChatGPT plan) |
| 2026-10-23 | 3B pilot sequence (adaptive, claude) | 8 tasks | 4.8639 | 6.7214 | task 1 = $4.21 |
| 2026-10-23 | 3B install/hook checks | 1 claude + 4 codex sessions | 0.0029 | 6.7243 | codex sessions: small prompts, tokens not recorded |
| 2026-10-23 | 3C dev set (humanize #142, #206 × 3 strategies) | 6 tasks | 9.0344 | 15.7587 | harness debugging; found test-edit gate blocks PRs that change pinned behaviour |
| 2026-10-23 | 3C pilot humanize (10 eval PRs × 3 strategies) | 30 tasks | 22.2600 | 38.0187 | baseline 0.09, static 21.90, adaptive 0.27 |
| 2026-10-23 | 3C tenacity, Codex executor (baseline + adaptive) | 44 tasks | 0.00 (est, ChatGPT plan) | (unchanged) | baseline 454,805 in / 4,031,360 cached / 42,977 out; adaptive 494,834 / 4,204,544 / 45,899 tokens |
| 2026-10-23 | 3C tenacity re-runs: baseline (22) after limit invalidation | 22 tasks | 0.4300 | — | clean re-run; superseded rows kept in `superseded/` (their spend counted above) |
| 2026-10-23 | 3C tenacity re-run: static tasks 1–15 (stopped by session limit at task 16, resumed 2026-10-24) | 15 tasks | 43.7900 | — | limit-hit task discarded, nothing recorded |
| 2026-10-23 | 3B/3C Codex runs: reflector check (#13), humanize baseline + adaptive | 2 + 30 tasks | 0.00 (est, ChatGPT plan) | — | tokens in `results-*.csv` |
| 2026-10-24 | 3C tenacity static re-run, tasks 16–21 (resumed; stopped at the $65 cap before #741) | 6 tasks | 21.7200 | — | static total 65.51 |

**Pilot cap:** $25.00 — spent $6.72 (27%). **Total cap:** $150.00 — spent **$126.77** ($124.77 recorded in `results*.csv` across `eval/results/`, plus $2.00 estimated for the aborted run). Codex runs: $0 (ChatGPT plan; tokens recorded).
| 2026-10-26/27 | Horizon (sqlglot): A baseline 60, B adaptive 60, C adaptive+feedback 60, dev smoke 1 | 181 tasks | 58.2300 | — | separate $100 budget; see `results/2026-10-26-horizon/REPORT.md` |

## Round 2 (separate budget)

Phase 0 cap $30; dev $30; pilot $50 within main $350. Cumulative below is
round 2 only. Running costs are provisional and reconciled to raw CSVs.

| date | phase | arm / run | tasks | cost USD | cumulative round-2 USD | status |
|---|---|---|---|---|---|---|
| 2026-10-27 | 0 | A / r1-A-rep2 | 2/60 | 3.6267 | 3.6267 | stopped by $3 between-task cap (overshoot $0.6267); invalid environment; preserved, excluded from noise analysis |

| 2026-10-27 | 0 recovery step 1 | environment parity and isolated CLI pin | zero tokens | 0.0000 | 3.6267 | Claude 2.1.309 installed; restore venv PATH and runner Python 3.14.4 |
| 2026-10-27 | 0 recovery step 4 | audit 199 round-1 rollout sessions | zero tokens | 0.0000 | 3.6267 | notification endings A 2/60, B 3/65, C 0/74; original costs lower bounds; actual CLI versions differ from ENVIRONMENT.md |
| 2026-10-27 | 0 recovery step 3 | Claude accounting fix PR #31 | zero tokens | 0.0000 | 3.6267 | captured-fixture regressions, cumulative billing without duplication, raw gzip archives and per-model/per-call metadata; all local and CI checks pass at PR head 13a9fee; calibration used installed source 38bae79; actual 2.1.310 limit and four-result captures added |
| 2026-10-27 | 0 recovery step 2 | oracle preflight, original horizon | 60 tasks / 180 checks | 0.0000 | 3.6267 | all valid; no fixes or exclusions; absolute venv Python plus venv PATH |
| 2026-10-27 | 0 recovery step 5 | A / calibration-A1 | 1/1 | 0.0414 | 3.6681 | holdout pass; exact CLI estimate $0.04137888 (1.41× round-1 recorded cost); one zero-cost limit rejection and one auto-resume; no replicates |
| 2026-10-27 | 0 before A replicates | task-1 base suite timing | 2 suites, zero tokens | 0.0000 | 3.6681 | 43.003 s isolated / 42.442 s planned load (one sequential A); pipeline concurrency 4, executor timeout 900; below 160 s threshold |
| 2026-10-27 | 0 before A replicates | PR #31 durations and gzip export guards | zero live tokens | 0.0000 | 3.6681 | merged 89020d7 after green CI; fixture, demo, strict sim-sweep and plugin passed |
| 2026-10-28 | 0 interruption audit | A / r1-A-rep2 task 22 | no outcome | >= 0.00394290 estimated | >= 4.44244290 | one deduplicated billed response; second request unresolved; paid work held |
| 2026-10-28 | 0 owner-requested recovery | A2 unresolved request hold | no outcome | 0.1000 reservation | 4.54244290 encumbered | reservation only; caps unchanged; actual unknown usage unresolved |
| 2026-10-28 | 0 A replicate | A / r1-A-rep2 | 60/60 | 2.0841 | 5.7522 | completed |
| 2026-10-28 | 0 A replicate | A / r1-A-rep3 | 60/60 | 2.0681 | 7.8203 | completed |
| 2026-10-29 | 0 A replicate | A / r1-A-rep4 | 60/60 | 1.9010 | 9.7213 | completed |
| 2026-10-29 | 0 B replicate | B / r1-B-rep2 | 3/60 | 0.5358 | 11.1828 | stopped; owner review; max two runs |
| 2026-10-29 | 0 B replicate | B / r1-B-rep3 | 0/60 | 0.0000 | 11.1828 | stopped; owner review; max two runs |
| 2026-10-29 | 0 A5 reconciliation | A / task35 rounding only | no new task | 0.00003272 | 11.18287562 | 25/25 requests matched; cumulative CLI estimate reconciled; timeout failure retained; owner requested resume36 only |
| 2026-10-29 | 0 A replicate | A / r1-A-rep5 | 60/60 | 1.7010 | 11.9582 | completed; task35 timeout retained; billing reconciled |
| 2026-10-29 | 0 B recovery | B / r1-B-rep2 | 60/60 | 2.2667 (2.8025 total) | 14.2249 | sequential recovery after A5; archived scratch; carry repaired 2→3 tasks; recovery posted on #29; completed 38 pass, 0 timeouts |
| 2026-10-29 | 0 B replicate | B / r1-B-rep3 | 60/60 | 2.3232 | 16.5481 | fresh run, seed 3, after B2; completed 39 pass, 1 non-delivery, 0 timeouts |
| 2026-10-29 | 0 analysis | reanalysis + power | zero tokens | 0.0000 | 16.5481 | `reanalysis.py` and `power.py` run; outputs in `eval/results/2026-10-29-r2-noise/`; REPORT.md and POWER.md written; Phase 1 not started |
| 2026-10-30 | 0b task-12 causal test | 20 runs: c_skill 5, d_placebo 5, a_full 5, b_minus 5 (PR #7549, build e846812) | 2.6041 | 2.6041 (task-12 only; cumulative round-2 incl. Phase 0 about 19.15) | complete; holdout passes c 0/5, d 1/5, a 0/5, b 0/5; results in eval/results/2026-10-30-r2-task12 |
