# Phase 0 reanalysis plan

Registered before generating or inspecting round-2 replicate outcomes. Round-1
outcomes and the owner-provided external review are already known.

## Frozen inputs and execution

Use the first 60 eval PRs in eval/prs/sqlglot/prs.json, in merge order,
and the existing task texts without edits. Record SHA-256 hashes in an input manifest.
Use a non-editable installation of f964993; 3b828e2 is the same product source
and differs only in eval/pr_replay.py. Preserve all round-1 files.
Executor: claude@claude-haiku-5-5; editor roles: claude. Independent clones
and state for r1-A-rep2 through rep5 and r1-B-rep2 through rep3.
Replicate 1 is the corresponding round-1 run. A uses k=0 and no escalation;
B uses round-1 adaptive defaults, max_k=2, adopt all, no feedback.
Seed labels 2..5 and 2..3 identify independent stochastic CLI sessions, not
controlled model RNG seeds (the executor exposes none); order seed remains 0.

Run A2 first. If every task has identical raw executor output and patch to A1,
stop and report deterministic output rather than fitting a stochastic noise model.
Identical pass/fail vectors alone do not establish determinism.

Phase cap $30. Each A run cap $3; each B run cap $7; aggregate round-2 cap
$30 with budget glob *-r2-*. Caps are checked between tasks; reserve task-cost
headroom and stop scheduling near the phase cap. No automatic crash or budget
resumes. CLI limit resumes may occur at most three times per run per UTC day;
each must be logged, with no completed task repeated. Expected duration 1–2 days.

## Estimands and analysis (exploratory)

For each task, baseline probability is its pass fraction over five A replicates.
Report always-pass (5/5), always-fail (0/5), and sometimes-pass task shares.
Noise floor is mean pairwise A disagreement: average over all 10 replicate
pairs and all tasks. Its 95% percentile bootstrap interval resamples tasks as
clusters, preserving all replicate outcomes; 20,000 draws, RNG seed 20261027.
Also report every pair and replicate separately, including non-deliveries.

Show the five C wins at positions 12,14,30,39,45 and four B wins at 3,20,30,39,
with baseline pass fractions. A sometimes-pass task makes that win consistent
with noise; this is not proof that the win was caused by noise.

Compare fixed round-1 C and mean B (three replicates) separately to mean A,
using per-task differences. Also show round-1 B vs mean A separately.
Report all 60 and the original primary 31–60 windows, with no multiplicity-
adjusted confirmatory claim. One-sided sign-flip test of the mean difference:
exact enumeration for <=20 nonzero differences; otherwise 200,000 random
sign vectors with plus-one p correction. Paired task bootstrap percentile
95% CI, 20,000 draws. Seed 20261027. Report no causal learning attribution.

## Power simulation

Grid: effects .05/.10/.15; total windows 60/100/150; 1/2/3 seeds per arm;
warm-up 20/30/40, with primary n = total minus warm-up. Simulate 5,000
experiments per cell, reporting Monte Carlo standard error. Sample baseline
latent task probabilities from the empirical five-run pass fractions. For the
improved arm use q=p+lambda*(1-p), with lambda chosen to attain the target
marginal effect (flag impossible cells). Independent Bernoulli draws conditional
on task difficulty, average seeds within each task, then one-sided sign-flip
at alpha .05 with 1,999 permutations and plus-one correction. This is a model,
not an identified prediction; report sensitivity using Jeffreys-smoothed
probabilities (successes+.5)/6 to expose uncertainty at 0/5 and 5/5.
Report estimated null rejection rates as calibration and retain all cells.

At fixed cost, show primary sample count and power as warm-up varies, using
measured A/B dollars and wall time, including paid warm-up for every seed.
E cost is unknown until Phase 1; do not price it as B or select a main window
now. Phase 2 must redo affordability with measured E cost and ask the owner
before selecting a task window. No observed-effect threshold in power tests.

## Interpretation and reporting

Round 1 is inconclusive: the original H1 was underpowered and its observed
10-point threshold capped power near 50% at a true 10-point effect. Shared A
noise correlates B/C comparisons. Two A failures were non-deliveries. Missing
harness snapshots prevent ruling out always-on effects. Exact-string failures
must not be assumed unlearnable: convention and domain semantics differ from
unguessable wording. Adoption that merely fixes the feedback task is circular.

Outputs: input manifest; per-task and per-pair CSVs; POWER.md;
eval/results/<date>-r2-noise/REPORT.md; ledger entries for each run.
List missing data, caps, interruptions and deviations; never silently pool
product builds. Stop and report after Phase 0, before product changes.
