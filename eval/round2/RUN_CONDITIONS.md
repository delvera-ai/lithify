# Owner-approved Phase-0 run conditions (2026-10-27)

This addendum records the owner's instructions after accepting calibration;
it does not change the frozen tasks, hypotheses, or statistical decisions.

- Merge PR #31 with per-result active/API duration and gzip leak validation.
- Pin CLI 2.1.310; executor claude@claude-haiku-5-5, roles claude.
- Explicit executor --timeout 900 and internal --concurrency 4 match the
  original horizon commands (which used f964993 defaults). A is k=0 with
  no escalation, so one suite/probe is active. Run A replicates sequentially.
- Benchmark the first task's base suite twice at this one-suite load before
  paid work. Block if either fails or exceeds 160 s (2x the 80 s upper end
  of the owner's round-1 60–80 s reference). Record every measurement.
- Run four A replicates before B, each with independent clone/state and
  replicate labels r1-A-rep2..5. The earlier environment-invalid A2 remains
  preserved and excluded; replacement data uses a separate result directory.
- After each completed task, stop the phase if the replicate's cumulative
  mean cost/task exceeds $0.068 or median wall_s exceeds 620 s. This applies
  from the first task, without an invented minimum sample size. Do not
  automatically resume a tripwire, budget stop or crash.
- Record executor, gate and outer-runner timeouts as distinct outcomes;
  retain their billed cost and score them as failures. CLI limits alone may
  auto-resume, maximum three per UTC day per run, with every resume logged.
- Every run passes --limit-usd, --total-cap 30, and --budget-glob '*-r2-*'.
  All previous round-2 spend ($3.6681) remains charged to the phase.
- B follows only within remaining cap. Estimate both B costs from round 1
  and completed A cost ratio, with headroom; if both will not fit, ask the
  owner whether to raise the cap to $35 or run only one B replicate. Do not
  decide or spend past $30 without the owner's answer.
- No raw session streams are committed: gzip is decompressed, redacted,
  recompressed, and scanned before export/archive. A failed leak scan blocks
  archiving, including .lithify/runs/*/sessions/*.gz.
- Post suite timing and A summary to tracking issue #29; stop/report if a
  tripwire fires. Phase 0 still ends with noise reanalysis/power and a report.


Implementation/build record: PR #31 merged at 89020d7 after all CI passed.
Replicates use a non-editable installation of that instrumented build, with
only package sources (no eval data) in its installation source directory.
This owner-requested instrumentation supersedes f964993 for the new rows;
record it explicitly rather than silently relabeling it as the old build.
All task/source hashes are checked before launch. A retains the registered
$3 per-run cap, in addition to the $30 phase cap and owner's mean/median
tripwires. An executor/outer timeout with only a lower-bound cost stops
further paid work for reconciliation; gate/holdout timeouts have their own
recorded outcome without pretending their billed CLI cost is unknown.
