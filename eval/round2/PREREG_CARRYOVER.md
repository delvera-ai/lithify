# Phase 2 preregistration: carry-over log

Every decision here must be **adopted** by the Phase 2 preregistration, or **explicitly overridden** with a reason
written next to it. Each entry gives the rule, the rationale, and the source (commit, file or #29 comment).

Entries are appended in the same commit as any later decision on #29 that affects the design.

## Entries

### 1. Rate reading of a 0/5 baseline

- **Rule:** a task with 0/5 baseline passes is treated as "rate ≤ ~0.3", never as "never-pass".
- **Rationale:** task 12 passed 1/28 across all non-round-1-C runs (A 0/5, B 0/3, task-12 arms 1/20). Under a
  per-run rate of 0.3, a 0/5 result is about a 17% chance (0.7^5 ≈ 0.17), so 0/5 does not establish zero.
- **Source:** `eval/results/2026-10-30-r2-task12/REPORT.md` (commit 97fac9c).
- **Status:** adopted.

### 2. Replicate single-task wins before interpreting them

- **Rule:** any single-task win is replicated before it is interpreted.
- **Rationale:** round-1 C's only task-12 win did not reproduce: 0/5 on the full harness, and the one task-12
  pass in the arms was a placebo run. A single win can be luck.
- **Source:** `eval/results/2026-10-30-r2-task12/REPORT.md` (commit 97fac9c); #29 comment of 2026-10-30T08:21:58Z.
- **Status:** adopted.

### 3. The pooled task-level test is not a learning claim under seed spread

- **Rule:** the pooled task-level sign-flip test is **not** sufficient on its own for a learning claim. The claim
  rule must be seed-aware.
- **Rationale:** under uniform seed spread the pooled test's null rate is inflated to 0.15–0.22 at W = 100,
  S = 2–4, against a nominal 0.05.
- **Source:** `eval/results/2026-10-29-r2-noise/POWER.md`, Addendum 1; #29 comment of 2026-10-29T20:31:23Z.
- **Status:** adopted.

### 4. Seed-level exact sign-flip needs at least 5 seeds

- **Rule:** a seed-level exact sign-flip test cannot reach α = .05 with ≤ 4 seeds. The design needs S ≥ 5 if that
  test is used.
- **Rationale:** the smallest one-sided p across S seed means is 1/2^S, which is 0.0625 at S = 4. S = 5 gives
  0.031.
- **Source:** `eval/results/2026-10-29-r2-noise/POWER.md`, Addendum 1, item 2 (line ~157).
- **Status:** adopted. Open question: whether the claim uses this test at all (see entry 5).

### 5. Conjunction claim rule: evaluate before adopting

- **Rule (candidate):** a learning claim requires "pooled p < .05 AND every learning seed positive" (the AP rule).
- **Rationale:** the Addendum 2 numbers are preliminary. The null is 0.01–0.03 without seed spread and 0.06–0.11
  with τ = 0.05. Power at δ = 0.10, W = 80, warm-up 30, S = 4 is 0.79 (τ = 0.05). The null is still inflated under
  spread, though less than the pooled test.
- **Still to evaluate before the preregistration:** the null rate and power of this rule, at the window and seed
  counts Phase 2 will use.
- **Source:** `eval/results/2026-10-29-r2-noise/POWER.md`, Addendum 2; #29 comment of 2026-10-30T05:13:31Z.
- **Status:** **open**.

### 6. Learning seed counts and windows

- **Rule (candidate):** 4–6 learning seeds on W = 60–80, with 3 baseline seeds.
- **Rationale:** AP clears 0.70 power at τ = 0.05 only at W = 80 with S = 4–6. Under τ = 0.08 it stays below 0.70 at
  every window and seed count tested. Budget: S = 4 × W = 80 is about $320–640 against the $350 main budget.
- **Still to evaluate:** the choice of seed count and window, given entry 5.
- **Source:** `eval/results/2026-10-29-r2-noise/POWER.md`, Addendum 2 (ii), (iii); #29 comment of 2026-10-30T05:13:31Z.
- **Status:** **open**.

### 7. Internal pilot picks S by a fixed rule

- **Rule (candidate):** an internal pilot estimates τ on warm-up tasks and picks S by a rule fixed in advance.
- **Rationale:** the tested adaptive rule (3 seeds, bias-corrected τ̂) did not adapt: mean chosen S was 4.1–5.0.
  Adaptive S gave no power advantage and inflated the null (P null 0.19 at τ = 0.05, W = 80, warm-up 30).
  Current recommendation is fixed S = 4 at W = 80.
- **Source:** `eval/results/2026-10-29-r2-noise/POWER.md`, Addendum 2 (iii) and line ~239; #29 comment of
  2026-10-30T05:13:31Z.
- **Status:** **open**. The fixed-S recommendation is not yet adopted, and the pilot-rule question is open.

### 8. Pin the build, CLI and interpreter; report by build

- **Rule:** pin Claude Code 2.1.310; executor `claude@claude-haiku-5-5`, roles `claude`; the non-editable runner
  uses project venv Python 3.14.4; gates and holdouts use the absolute repo-venv Python with that venv's bin first
  on PATH. Lithify build `89020d7` is the instrumented build for Phase 0 replicates. Results are reported **by
  build**, never pooled silently. Arm A rows labelled `f964993`, B and C rows `f964993` and `3b828e2`, are the same
  source for `eval/pr_replay.py` only. The task-12 arms ran lithify `e8468122` (PR #32, which adds
  `--harness-dir`), so they are a separate build from Phase 0's `89020d7` and must be reported as such.
- **Rationale:** round 1 ran `f964993`. Phase 0 replicates ran `89020d7`. The 2.1.309 pin was stale; A actually ran
  2.1.310, and B/C ran 2.1.310–2.1.311. The Phase 0 A2 run is invalid and excluded.
- **Source:** `eval/round2/ENVIRONMENT_PARITY.md` (session evidence correction and calibration runtime decision);
  `eval/round2/RUN_CONDITIONS.md` (implementation/build record); `eval/results/2026-10-29-r2-noise/REPORT.md`.
- **Status:** adopted.

### 9. Run conditions and timeouts

- **Rule:** executor `--timeout 900`, internal `--concurrency 4`, as in round 1. Single suite active for A runs.
  Executor, gate and outer-runner timeouts are **distinct outcomes**, retained with their billed cost, and scored as
  failures. A gate or holdout timeout has its own recorded outcome. Tripwires: cumulative mean cost/task above
  $0.068 (A only; B uses $7 per-run cap) or median `wall_s` above 620 s stops the phase. CLI-limit-only auto-resume,
  at most 3 per run per UTC day, every resume logged. Crashes and budget stops never auto-resume.
- **Rationale:** round 1 had timeouts that were not separated from failures, and tripwires that the owner set on
  cost and wall time. Concurrency is part of the timing evidence.
- **Source:** `eval/round2/RUN_CONDITIONS.md` (owner-approved Phase 0 run conditions, parallel schedule change,
  and the 2026-10-29 cost-tripwire decision).
- **Status:** adopted for Phase 0. Phase 2 must restate it, since the parallel-B rules were owner overrides.

### 10. Spec-test validity and whether spec tests may rank deliverables

- **Status:** **pending**. Filled in when the Phase 1 item 2 offline check reports (AUC and precision/recall on the
  12 "sometimes" horizon tasks, $8 DEV cap). Until then, spec tests may not be used to rank deliverables in any
  preregistered claim.
- **Source:** `lithify-round2-prompt.md`, Phase 1 item 2.
