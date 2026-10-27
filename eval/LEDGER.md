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
