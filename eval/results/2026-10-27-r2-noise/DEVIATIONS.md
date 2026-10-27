# Phase 0 interruption: r1-A-rep2

Run stopped at the run budget check before task 3. Completed two tasks, cost
$3.6267. The $3 run cap is checked between tasks, so the second task caused
$0.6267 overshoot. The owner's $30 phase cap was not exceeded. No automatic
budget resume is authorized or scheduled.

Both recorded tasks (#7492 and #7487) failed the deterministic gate because
`tests/dialects/test_dialect.py::TestDialect::test_lazy_load` invokes bare
`python`, absent from the launch PATH. Each gate reported 1 failed, 1080
passed. These are environment-invalid outcomes, not measured agent failures.
Preserve all raw data and CSV rows, exclude this run from noise estimation,
and retain the entire spend in the ledger. This invalidation is a deviation
from the preregistered run plan; no replacement run has started.

Evidence: raw/r1-A-rep2/{01-pr7492,02-pr7487}/run/rollouts/base-1/gates.md;
results-r1-A-rep2.csv; scratch progress.json has next_pos=3. Neither delivered.

Executor session logs identify claude-haiku-5-5 for both tasks, matching the
requested model label. Costs were $2.1994 and $1.4273 versus round-1 baseline
$0.0294 and $0.0153 for these tasks. Cause of the cost difference is not yet
established. Model labels alone cannot prove an identical backend build.
No additional paid calls should be scheduled until environment preflight
and affordability are resolved. Phase 0 remains incomplete.
