# Two-run schedule — 2026-10-29

Owner authorization: “I think let's do the parallel runs but limit it to two at a time.”

A2–A4 are complete and A5 is running. Existing A supervisor remains untouched.
The new detached B supervisor waits for successful A supervisor exit and all
four complete A CSVs, verifies frozen input/product source hashes, checks
original tripwires, and writes an affordability calculation before paid work.

It then runs two zero-token waves of eight simultaneous suites on independent
clones at the frozen first base. Gate: all 16 suites pass within 160 seconds.
Failure stops and reports. No test edits, skipped tests or smaller suites.

If the load guard and affordability checks pass, start exactly B2 and B3,
using separate clones/state/session labels. Full flags preserve baseline task
window/order, adaptive max_k=2, adopt all, no feedback, executor
claude@claude-haiku-5-5, role claude, timeout900, internal concurrency4,
limit-usd7, total-cap30, round-only budget glob, mean .068 and median620.
Phase checks reserve both full caps plus $2 overshoot headroom. A shared stop
flag blocks new tasks after either B stops; running tasks finish and retain
usage. CLI limits alone can retry, three/run/UTC day, with explicit --resume.

No third evaluation runner is scheduled. The supervisor keeps the host awake
against idle sleep, persists status/exit records, and refuses an existing run
or supervisor state. Its output directory is a separate *-r2-* directory.
Local stdout is redacted before export, and the existing gzip-aware leak scan
still gates evidence. The parallel protocol deviation and host sleep remain
visible in the final analysis. B completion does not start Phase 1.
