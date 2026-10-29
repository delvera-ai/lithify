# A5 continuation authorized by owner — 2026-10-29

Resume only A5 at36 after task35 usage reconciliation; B remains stopped.
Retain all35 existing outcomes, including timeout35 as a failure. The CSV
prefix is byte-identical; hash recorded in RECOVERY.json. Original checkpoint,
carry state, supervisor status, tripwire and summary are preserved, with a
full local scratch archive hash. Carry is advanced from task34 to the current
recorded task35 state so resuming at36 does not lose completed history.

All25 local requests have25 matched distinct responses; requestRef IDs and
message IDs agree with captured stream. The stream ends with a result event.
Deduplicated tokens match final cumulative modelUsage exactly. Five result
snapshots are cumulative: take the maximum per session, never their sum.
Exact CLI list-cost estimate is $0.02313272, versus recorded $0.0231.
Charge only $0.00003272 rounding difference separately and in checkpoint.
This reconciles recorded CLI usage, not a provider invoice.

Pass explicit --reconciliation with the audited row's SHA-256. The runner
validates it before any checkout reset or paid execution and uses a copy to
resolve that historical lower-bound flag for its stop decision. Original
CSV/outcome stay unchanged. Unknown new timeouts still stop. Reconciliation
must not mask a changed row, missing task, or mismatched cost. Regression
tests cover those cases and preservation of the failure outcome.

Use pinned Python3.14.4, Claude2.1.310, byte-verified89020d7, frozen60 inputs,
baseline k0/no escalation, timeout900, internal concurrency4, $3/run,
$30/phase, round-only budget glob, mean>$0.068 and median>620s stops. Detached
supervisor records status and exit codes, keeps host awake, and starts no B.
Only CLI-limit exit75 may auto-resume, maximum3/run/UTCday; record each.
No automatic crash/budget/tripwire resume. Stop/report after A5; Phase0 still
needs its complete analysis/report before Phase1.

Validation: full ruff, format, mypy and pytest passed; source/evidence checks
and gzip-aware leak scan precede commit. Product and frozen input hashes are
rechecked immediately before launch. No product code or prompt changed.
