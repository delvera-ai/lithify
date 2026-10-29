# B2 recovery — 2026-10-29 (sequential, after A5)

## Why B2 stopped

`r1-B-rep2` stopped at task 3 with exit 78 at the shared phase guard
(`PHASE_STOP.json`, 09:23:32Z), which was triggered by the failed A/B
run. It did not hit its own cost or wall limit. Its prior records
(`SUPERVISOR.json`, `CHILD_EXITS.jsonl`, `PHASE_STOP.json`,
`COST_TRIPWIRE_DECISION.json`, `AFFORDABILITY.json`, `DEVIATIONS.md`) are
preserved unchanged as historical evidence. This record does not replace
them.

## Preconditions verified before launch

- A5 finished: `A5_RECOVERY/SUPERVISOR.json` status `completed`, exit 0,
  finished 11:37:16Z. CSV: 60 rows, 37 pass, 22 failure, 1 timeout
  (task 35, reconciled per `RECONCILIATION.json`, original row unchanged).
  Cost $1.701, mean $0.0284/task, median wall 183.2 s. No new timeouts.
- No B process was running. The overlap was not repeated.
- Python: runner `env-r2-replicates` 3.14.4; repo `env-sqlglot` 3.12.13.
  Claude CLI 2.1.310.
- Installed `lithify` package: 33 of 33 source hashes match
  `RUN_ENVIRONMENT.json` for product commit `89020d7`.
- `eval/prs/sqlglot/prs.json` matches `INPUT_MANIFEST.json`
  `prs_sha256`. All 60 task files match their `task_sha256`.
- Spend (round-2 CSVs, per-row sum, all `*-r2-*` directories): $11.958176.
  This includes the invalid A2 environment run, calibration, the $0.10
  A2 reservation, A2–A5, and B2's $0.5358.
- Affordability, worst case: $11.958 + B2 remaining cap $6.4642 + B3
  full cap $7.00 + $2.00 between-task headroom = $27.42, within the $30
  phase cap. Both B runs fit with no increase, so no $35 request is
  needed.

## Scratch archive and carry repair

B2 scratch archived before any change to the run directory:

- `<work>/archive-b2-before-task4-20261029T104902Z/`
  (full copy of `replay-r2-noise-verified-r1-B-rep2/`, the CSV, and
  `MANIFEST.sha256`).
- The stale carry, which held 2 history entries, was moved into that
  archive as `carried-stale-before-task4/`.

Carry repaired: `carried/.lithify` rebuilt from the clone `repo/.lithify`
(excluding `runs`). Both `state.json` files hold 3 history entries and are
byte-identical (`cmp`). With this, `pr_replay --resume` at position 4
restores task 3's state and does not lose it.

Resume state: `progress.json` next_pos 4, run_cost $0.5357999999999999,
3 audit entries, 3 CSV rows. The CSV is appended, not rewritten.

## Recovery command

Mirrors `run_b_parallel.py` with these deliberate changes:

- `--max-mean-cost` is omitted. The owner's decision limits the mean-cost
  tripwire to A.
- `--phase-stop-file` points to a fresh path,
  `eval/results/2026-10-29-r2-ab-overlap/B2_RECOVERY_PHASE_STOP.json`,
  which does not exist yet. The old `PHASE_STOP.json` would otherwise
  make the run exit 78 immediately. The old file is kept as evidence.

```
pr_replay.py sqlglot --strategy adaptive --split eval --first 60 --max-k 2
  --adopt all --executor claude@claude-haiku-5-5 --roles claude
  --timeout 900 --concurrency 4 --limit-usd 7 --total-cap 30
  --budget-glob "*-r2-*" --max-median-wall 620
  --phase-stop-file <B2_RECOVERY_PHASE_STOP.json>
  --work <r2-noise-scratch> --out <2026-10-29-r2-ab-overlap>
  --experiment r2-noise-verified --label r1-B-rep2 --replicate r1-B-rep2
  --seed-label 2 --arm B --product-commit 89020d7516ca4dd288909281747f053453a8a216
  --resume
```

Run under `caffeinate -i -w <pid>`, recorded in
`B2_RECOVERY_SUPERVISOR.json`. A new supervisor record is created; the old
one is not overwritten.

## Stop rules

- Median wall > 620 s stops B2.
- Budget stop at $7 per run or $30 per phase stops B2.
- A new timeout with unresolved usage stops B2 for reconciliation.
- Crashes, budget stops, and tripwires are not auto-resumed. Each requires
  a new report.
- B has no mean-cost tripwire, per the owner decision.

## Deviations

1. B2 continues in a separate recovery run because the original runner
   refuses existing clones. The recovery supervisor is separate from the
   original.
2. The carry was repaired by archive-and-rebuild, not by editing the
   original state in place.
3. Phase-stop file path changed to a fresh file (see above).
4. Launched after A5 finished, not overlapping it. The earlier
   overlap-era load tests remain recorded and unchanged.
