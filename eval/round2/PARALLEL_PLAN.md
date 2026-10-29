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


## Superseding owner instruction: overlap B with A5 now

Start one B beside A5 as soon as preflight and affordability pass. Count the
active A supervisor as one occupied slot until successful exit, including
when it is waiting on a CLI limit. The second B can start only when the total
active A/B replay count stays at most two. Reserve A5's remaining full cap.
The earlier waiting B supervisor was explicitly cancelled with no B costs;
its state/evidence remains in 2026-10-29-r2-parallel-b. New overlap evidence
uses 2026-10-29-r2-overlap-b. A5 remains untouched unless a phase stop requires
termination; such an interruption requires usage reconciliation before any
further paid resume. Preflight adds synthetic CPU load to live A5; disclose it.


## Measured load and explicit cost scope (2026-10-29)

The eight-suite load guard failed (all eight timed out at 160 seconds). It is
preserved under 2026-10-29-r2-overlap-b and does not authorize simultaneous
B2/B3. A separate two-wave, five-suite load guard under 2026-10-29-r2-ab-load
can authorize A5 plus one B. Start the paid supervisor in
2026-10-29-r2-ab-overlap only after that check passes, with --overlap-a5,
--max-b-runs 1, --use-preflight and its explicit evidence directory. B3 follows
B2 under this load limit, even if A5 finishes sooner.

The owner selected “Apply $0.068 mean-cost tripwire only to A; keep B’s $7 cap.”
Use --mean-cost-a-only only with the recorded explicit decision. B retains
its $7 cap, $30 phase cap, 620-second median-wall tripwire, and original
internal concurrency4. No model, task, test or budget changes. Preflight
interference with A5 is a disclosed deviation; retain all original timings.
