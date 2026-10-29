# Phase 0 report: round-2 noise replicates

Status: all registered Phase 0 paid runs are finished. Phase 0 analysis is complete. Phase 1 has not
started. This is exploratory analysis of an 8-to-10-run noise study. It makes no causal
learning claim.

Analysis code: `eval/round2/reanalysis.py` and `eval/round2/power.py`. Plan:
`eval/round2/REANALYSIS_PLAN.md` (commit 106458b). Outputs: `per_task.csv`, `pairs.csv`,
`runs.csv`, `reanalysis.json`, `power_grid.csv`, `power_summary.json`, `POWER.md`.

## 1. Spend and caps

Round-2 recorded spend, summed over all `*-r2-*` results CSVs: **$16.548**, under the $30 phase cap.

| item | USD | counted |
|---|---|---|
| A2 invalid environment run (stopped at 2/60) | 3.6267 | yes; excluded from analysis |
| Calibration A1 | 0.0414 | yes; excluded |
| A2 unresolved-request reservation | 0.1000 | yes; encumbered, not observed |
| A2 interruption audit | 0.0039 | yes |
| A5 task-35 rounding adjustment | 0.00003 | yes |
| A2 (r1-A-rep2) | 1.9802 | analysed |
| A3 (r1-A-rep3) | 2.0681 | analysed |
| A4 (r1-A-rep4) | 1.9010 | analysed |
| A5 (r1-A-rep5) | 1.7010 | analysed |
| B2 (r1-B-rep2) | 2.8025 | analysed |
| B3 (r1-B-rep3) | 2.3232 | analysed |

Per-run caps were respected: all A runs under $3, all B runs under $7. The mean-cost tripwire
applied to A only (owner decision). It was never hit: A5 mean was $0.0284/task and the
per-run cap was never reached. Median wall was under 620 s for every run.

## 2. Runs analysed

| run | product build | pass /60 | non-delivered | timeouts | cost USD | median wall s |
|---|---|---|---|---|---|---|
| A1 (round 1, baseline) | f964993 | 35 | 2 | 0 | 2.06 | 206 |
| A2 | 89020d7 | 37 | 1 | 0 | 1.98 | 192 |
| A3 | 89020d7 | 35 | 1 | 0 | 2.07 | 183 |
| A4 | 89020d7 | 38 | 0 | 0 | 1.90 | 211 |
| A5 | 89020d7 | 37 | 2 | 1 (task 35, reconciled) | 1.70 | 183 |
| B1 (round 1, adaptive) | f964993 | 38 | 0 | 0 | 5.21 | 279 |
| B2 | 89020d7 | 38 | 0 | 0 | 2.80 | 194 |
| B3 | 89020d7 | 39 | 1 | 0 | 2.32 | 184 |
| C1 (round 1, feedback, single replicate) | f964993 | 40 | 0 | 0 | 50.93 | 258 |

Round-1 costs are as recorded in the round-1 CSVs and were not re-audited in this pass.

Task 35 (sqlglot#7655) is counted as a failure. Its recorded CLI usage was reconciled
($0.02313272 list-cost estimate, $0.00003272 rounding). Task 35 was not rerun.

## 3. Registered results (exploratory)

**Baseline (five A runs).** 30 tasks always pass, 18 never pass, 12 sometimes pass.

**Noise floor.** Mean pairwise disagreement over all 10 A pairs and 60 tasks: **9.3%**, 95% task-cluster
bootstrap CI **4.7%–14.3%** (20,000 draws, seed 20261027). Pairwise discordant tasks ranged from 3 to 8
(`pairs.csv`). A1 and A2 disagree on 6 tasks. The plan's stop condition for determinism (identical raw
output) is therefore not met, and noise is treated as real.

**Wins at fixed positions, with baseline pass fraction.**

| arm | position | task | A1 | variant | A pass fraction | class |
|---|---|---|---|---|---|---|
| B1 win | 3 | sqlglot#7502 | fail | pass | 0.8 | sometimes |
| B1 win | 20 | sqlglot#7578 | fail | pass | 0.2 | sometimes |
| B1 win | 30 | sqlglot#7640 | fail | pass | 0.4 | sometimes |
| B1 win | 39 | sqlglot#7680 | fail | pass | 0.2 | sometimes |
| C1 win | 12 | sqlglot#7549 | fail | pass | **0.0** | never |
| C1 win | 14 | sqlglot#7550 | fail | pass | 0.8 | sometimes |
| C1 win | 30 | sqlglot#7640 | fail | pass | 0.4 | sometimes |
| C1 win | 39 | sqlglot#7680 | fail | pass | 0.2 | sometimes |
| C1 win | 45 | sqlglot#7729 | fail | pass | 0.4 | sometimes |

Eight of nine wins are on tasks that pass sometimes in A. This is consistent with run-to-run noise, not
proof of it. The C1 win at position 12 is on a task A never passed in five runs, so baseline noise does
not explain it. A single C replicate cannot show whether that win is reproducible.

**Mean differences per task, versus the mean of five A runs.** One-sided sign-flip test (exact enumeration;
no multiplicity adjustment). Paired task-bootstrap 95% CI, 20,000 draws.

| comparison | window | mean diff | 95% CI | one-sided p | nonzero tasks |
|---|---|---|---|---|---|
| C1 − mean A | all 60 | +0.060 | −0.000 to +0.123 | 0.040 | 13 |
| C1 − mean A | primary 31–60 | +0.087 | +0.020 to +0.167 | 0.016 | 6 |
| mean B (B1–B3) − mean A | all 60 | +0.032 | +0.003 to +0.062 | 0.023 | 14 |
| mean B (B1–B3) − mean A | primary 31–60 | +0.020 | −0.024 to +0.062 | 0.227 | 7 |
| B1 − mean A | all 60 | +0.027 | −0.030 to +0.083 | 0.216 | 12 |
| B1 − mean A | primary 31–60 | +0.020 | −0.040 to +0.093 | 0.375 | 6 |

**Build sensitivity.** Round-1 A1 and B1 and C1 used build f964993. A2–A5 and B2–B3 used 89020d7, which
adds instrumentation. Pooling these is a deviation from strict comparability. Restricting to the round-2
build only (B2–B3 vs A2–A5):

| comparison | window | mean diff | 95% CI | one-sided p |
|---|---|---|---|---|
| B2–B3 − A2–A5 | all 60 | +0.029 | −0.013 to +0.075 | 0.146 |
| B2–B3 − A2–A5 | primary 31–60 | +0.025 | −0.050 to +0.108 | 0.344 |

With one build, the all-60 B result is no longer significant. The earlier all-60 result depends on
including round-1 A1.

**Interpretation.**
- The round-1 totals (A1 35, B1 38, C1 40 of 60) are within the A noise band (A2–A5 35–38), so they do
  not show a learning benefit.
- The noise floor (about 9%) is larger than the B1/C1 totals suggest.
- The original H1 was underpowered. See `POWER.md`.
- None of this establishes that learning caused any difference. The B and C arms also differ in build,
  scheduling and session conditions, and only one C replicate exists.

## 4. Power

See `POWER.md` for the full grid. Summary:
- At 0.10 effect, 100 windows, warm-up 30, 3 seeds: power 0.97 (empirical baseline) and 0.86 (Jeffreys
  sensitivity).
- At 0.05 effect, 150 windows, warm-up 30, 3 seeds: power 0.84 (empirical) and 0.59 (Jeffreys).
- Null rejection rates across all 27 cells are 0.04%–3.4% (empirical) and 0.8%–4.2% (Jeffreys) at
  nominal 5%. The test is conservative at most sizes, which lowers power.
- Seeds matter: at 0.10 effect, 100 windows, warm-up 30, power is 0.59, 0.89 and 0.97 for 1, 2, 3 seeds.

Costs (measured A mean $0.0324/task; median wall about 195 s). E cost is unknown until Phase 1 and is not
priced as B. Per-cell cost tables are in `power_summary.json`.

## 5. Missing data, interruptions and deviations

- **A2 invalid environment run** ($3.63): stopped by the between-task cap after 2 tasks. Its environment
  was invalid. It is preserved, excluded from analysis, and still charged to Phase 0.
- **A2 interruption**: a crash on task 22 left an unresolved request. A $0.10 reservation is charged.
  Actual usage is unknown.
- **A3 interruption**: recorded as an interruption with zero cost and preserved under
  `interruptions/r1-A-rep3`.
- **A5 timeout**: task 35 ran to the 900 s limit with the CLI open. Its usage was reconciled
  (25/25 requests matched). It is scored as a failure and not rerun.
- **B2 stop and recovery**: stopped at task 3 by the shared phase guard, which fired when A5's stop
  record was written (not from B2's own limits).
  Resumed at task 4 after archiving scratch, repairing the carry from 2 to 3 tasks, and posting the
  recovery record on #29. B2 completed 60/60.
- **B3**: started fresh after B2, not overlapping. Completed 60/60.
- **Load tests**: 8-suite preflight failed (all 8 timed out at 160 s). A 5-suite A/B preflight passed while
  A5 was live. Both are preserved. The live preflight temporarily increased A5's load, and this is disclosed.
- **Mean-cost tripwire**: applied to A only, per the owner's decision. Not applied to B.
- **Product builds**: A2–A5 and B2–B3 used 89020d7 (instrumented). A1, B1 and C1 used f964993. Analyses
  are reported both pooled and by build.
- **Host sleep**: pmset evidence is recorded in `HOST_SLEEP_EVIDENCE.txt` for the A runs, including sleeps
  during A4. Not every idle gap is proven to be sleep. Active runs used `caffeinate -i -w`.
- **Schedule**: A runs ran sequentially. B2 and B3 ran sequentially, not in parallel, after the failed
  8-suite load test.

## 6. Stop

Phase 0 analysis and power are complete. Phase 1 (learning-loop product changes) has not started, and
no product code was changed in this phase. Phase 1 needs a fresh preregistration, pilot approval and
independent verification.
