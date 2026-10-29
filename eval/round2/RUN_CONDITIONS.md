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


## Owner-approved schedule change (2026-10-29)

The owner requested parallel evaluation runs, limited to two at a time.
Only A5 remained when this was approved. Preserve the four-A-before-B rule;
finish A5, then run B2 and B3 concurrently, with at most two replay runners.
Each B retains internal concurrency 4, max_k 2, original adaptive settings,
independent clone/state, unchanged task order/text, and the verified 89020d7
product build. Do not overlap B with A or add a third run.

Before either B starts, time two waves of eight simultaneous frozen task-1
base suites (four possible probe suites per B). Every suite must pass and
finish within 160 seconds. A failed/incomplete preflight blocks paid B work.
This is a machine-load guard, not proof that wall times are interchangeable
with the sequential round-1 observations. Disclose parallel scheduling in
all B comparisons; retain original wall times and host-sleep evidence.

Recheck affordability after all A runs finish using measured A/old-A cost
ratio and original B cost. Reserve both full $7 B caps plus $2 between-task
headroom inside the unchanged $30 cap. If both do not fit, stop and ask
about $35 or one B. Phase accounting retains the unresolved $0.10 hold.

The cumulative mean >$0.068/task and median wall >620 seconds stop rules
remain unchanged, from the first completed task. A shared stop flag prevents
either B from starting another task after a tripwire/budget stop; an active
task may finish to preserve its outcome and cost. CLI-limit-only resumes
remain limited to three/run/UTC day. Crashes and budget stops never auto-resume.
After B, report Phase 0 and stop before Phase 1.


### Later owner override: start B beside A5 now (2026-10-29)

The owner explicitly requested B to start in parallel immediately. This
supersedes four-A-before-B for the remaining A5 run. A2–A4 remain complete;
B2 may overlap A5 after the unchanged load and budget guards. Count A5 as
one of the maximum two total evaluation runners; B3 may use a free slot.
Reserve the unspent portion of A5's $3 cap in addition to both $7 B caps and
$2 between-task headroom. Estimate cost ratio using completed A2–A4 only
while A5 is partial, and disclose that provisional estimate.

Run the same two eight-suite load waves while A5 is live: its own possible
suite makes the measured load conservatively higher than eight. Record the
temporary preflight load in A5's timing deviation; retain all measured times.
If a B stop occurs during overlap, stop A's isolated launcher process group;
A's already-loaded runner predates shared-stop support. Any interrupted A
usage is a lower bound pending reconciliation; never silently restart it.
An A failure also blocks further B tasks. Models, tests, budgets, tripwires
and three CLI-limit-only resumes/run/UTC-day remain unchanged.


### Owner cost-tripwire decision and failed B/B load guard (2026-10-29)

The owner selected: “Apply $0.068 mean-cost tripwire only to A; keep B’s $7 cap.”
B keeps the $7 per-run cap, $30 phase cap, and median-wall >620s tripwire.
This explicitly supersedes the earlier global mean-cost wording for B only.
A settings remain unchanged. Eight-suite load failed: all eight suites timed
out at 160s. Preserve that evidence; do not launch two B runs on that result.
A separate five-suite guard tests A5 plus one B. If it passes, permit at most
one B at a time, with at most two total A/B runs. B3 then follows B2, retaining
this stricter load limit until fresh evidence/approval supports more load.
