# Power simulation (Phase 0)

Registered in `eval/round2/REANALYSIS_PLAN.md`. Code: `eval/round2/power.py`. Grid: `power_grid.csv`.
Summary: `power_summary.json`.

This is a model of the planned learning-loop comparison, not a prediction of the actual result.

## Model

- Baseline task probabilities p_t come from the five A runs, one per task (empirical pass fractions).
  Mean p = 0.607. Sensitivity variant: Jeffreys-smoothed (k+0.5)/6, mean p = 0.589.
- Improved arm: q = p + λ(1−p), with λ chosen so the uniform task-average effect equals the target
  (λ = δ / mean(1−p), with mean(1−p) = 0.393). λ ≤ 1 holds in every cell, so none is infeasible.
- Each experiment draws W positions uniformly from the 60 tasks, with replacement. The first w are
  warm-up. Warm-up positions use p in the improved arm, so the effect applies only to the primary n = W − w.
- Each seed draws independent Bernoulli outcomes conditional on task probability. Seeds are averaged within
  each position, then one-sided sign-flip is run on primary positions with 1,999 permutations at α = .05,
  using plus-one correction. No observed-effect threshold is used.
- 5,000 experiments per cell. Monte Carlo SE in parentheses in the grid (max 0.007).
- Shared permutation sign banks per primary length, seeded with 20261027. This is a valid approximate
  randomisation, but it correlates tests across cells.

## Findings

1. **Seeds dominate.** At effect 0.10 and 100 windows, warm-up 30: power is 0.59, 0.89, 0.97 for 1, 2, 3
   seeds (empirical).
2. **Warm-up costs power through primary n, most at small windows.** At effect 0.10 with 3 seeds, moving
   warm-up from 20 to 40 drops power by 0.04 at W=100 (0.985 to 0.943), 0.38 at W=60 (0.80 to 0.43), and
   0.002 at W=150 (1.000 to 0.998).
3. **Round-1 scale was far too small.** The round-1 design (60 positions, 1 seed) has power at 0.10 effect
   of 0.30 (warm-up 20) or 0.19 (warm-up 30), and at 0.05 effect of 0.09 or 0.04. This matches the original
   finding that round 1 was underpowered.
4. **Calibration.** Null rejection at nominal 5% is conservative: 0.04%–3.4% (empirical), 0.8%–4.2%
   (Jeffreys). The sign-flip test with plus-one correction is conservative at these sizes. Power is
   therefore if anything understated, and effects must be larger to reach significance.
5. **Jeffreys sensitivity lowers power.** Smoothing shrinks the baseline spread, so the target
   marginal effect requires more of the chance mass to move. At effect 0.05, window 150, warm-up 30, 3 seeds:
   0.84 (empirical), 0.59 (Jeffreys). At effect 0.10, window 100, warm-up 30, 3 seeds: 0.97 vs 0.86.

## Cost and time at fixed budget

Measured A baseline cost is $0.0324/task on average across the five A runs. Median wall is about 195 s
(serial). E cost is unknown until Phase 1 and is not priced as B. The table gives baseline-arm dollars and
task counts, and warm-up is counted in tasks for every seed.

| W | warm-up | primary n | seeds | paid warm-up tasks (all seeds) | baseline-arm tasks | baseline-arm USD | baseline-arm serial hours |
|---|---|---|---|---|---|---|---|
| 60 | 30 | 30 | 3 | 90 | 180 | 5.83 | 9.8 |
| 100 | 30 | 70 | 3 | 90 | 300 | 9.71 | 16.3 |
| 150 | 30 | 120 | 3 | 90 | 450 | 14.57 | 24.4 |
| 150 | 30 | 120 | 1 | 30 | 150 | 4.86 | 8.1 |

Full table in `power_summary.json`. Primary n is 20–130 across the grid.

## Empirical baseline, S seeds (power ± MCSE)

| effect | W | w | n | S=1 | S=2 | S=3 |
|---|---|---|---|---|---|---|
| 0.05 | 60 | 20 | 40 | 0.089±0.004 | 0.251±0.006 | 0.378±0.007 |
| 0.05 | 60 | 30 | 30 | 0.044±0.003 | 0.157±0.005 | 0.269±0.006 |
| 0.05 | 60 | 40 | 20 | 0.013±0.002 | 0.058±0.003 | 0.127±0.005 |
| 0.05 | 100 | 20 | 80 | 0.243±0.006 | 0.499±0.007 | 0.687±0.007 |
| 0.05 | 100 | 30 | 70 | 0.214±0.006 | 0.430±0.007 | 0.616±0.007 |
| 0.05 | 100 | 40 | 60 | 0.167±0.005 | 0.394±0.007 | 0.545±0.007 |
| 0.05 | 150 | 20 | 130 | 0.416±0.007 | 0.715±0.006 | 0.870±0.005 |
| 0.05 | 150 | 30 | 120 | 0.389±0.007 | 0.685±0.007 | 0.836±0.005 |
| 0.05 | 150 | 40 | 110 | 0.357±0.007 | 0.644±0.007 | 0.805±0.006 |
| 0.10 | 60 | 20 | 40 | 0.303±0.006 | 0.635±0.007 | 0.804±0.006 |
| 0.10 | 60 | 30 | 30 | 0.190±0.005 | 0.483±0.007 | 0.667±0.007 |
| 0.10 | 60 | 40 | 20 | 0.064±0.004 | 0.249±0.006 | 0.426±0.007 |
| 0.10 | 100 | 20 | 80 | 0.686±0.007 | 0.926±0.004 | 0.985±0.002 |
| 0.10 | 100 | 30 | 70 | 0.591±0.007 | 0.891±0.004 | 0.967±0.003 |
| 0.10 | 100 | 40 | 60 | 0.514±0.007 | 0.837±0.005 | 0.943±0.003 |
| 0.10 | 150 | 20 | 130 | 0.890±0.004 | 0.993±0.001 | 1.000±0.000 |
| 0.10 | 150 | 30 | 120 | 0.861±0.005 | 0.989±0.002 | 1.000±0.000 |
| 0.10 | 150 | 40 | 110 | 0.826±0.005 | 0.981±0.002 | 0.998±0.001 |
| 0.15 | 60 | 20 | 40 | 0.587±0.007 | 0.890±0.004 | 0.969±0.002 |
| 0.15 | 60 | 30 | 30 | 0.399±0.007 | 0.761±0.006 | 0.891±0.004 |
| 0.15 | 60 | 40 | 20 | 0.178±0.005 | 0.494±0.007 | 0.696±0.006 |
| 0.15 | 100 | 20 | 80 | 0.920±0.004 | 0.996±0.001 | 1.000±0.000 |
| 0.15 | 100 | 30 | 70 | 0.877±0.005 | 0.991±0.001 | 0.999±0.000 |
| 0.15 | 100 | 40 | 60 | 0.816±0.005 | 0.984±0.002 | 0.999±0.001 |
| 0.15 | 150 | 20 | 130 | 0.993±0.001 | 1.000±0.000 | 1.000±0.000 |
| 0.15 | 150 | 30 | 120 | 0.990±0.001 | 1.000±0.000 | 1.000±0.000 |
| 0.15 | 150 | 40 | 110 | 0.981±0.002 | 1.000±0.000 | 1.000±0.000 |
| 0 (null) | 60 | 20 | 40 | 0.005±0.001 | 0.010±0.001 | 0.015±0.002 |
| 0 (null) | 60 | 30 | 30 | 0.001±0.000 | 0.006±0.001 | 0.008±0.001 |
| 0 (null) | 60 | 40 | 20 | 0.000±0.000 | 0.002±0.001 | 0.002±0.001 |
| 0 (null) | 100 | 20 | 80 | 0.019±0.002 | 0.023±0.002 | 0.028±0.002 |
| 0 (null) | 100 | 30 | 70 | 0.012±0.002 | 0.024±0.002 | 0.027±0.002 |
| 0 (null) | 100 | 40 | 60 | 0.010±0.001 | 0.021±0.002 | 0.023±0.002 |
| 0 (null) | 150 | 20 | 130 | 0.021±0.002 | 0.032±0.003 | 0.033±0.003 |
| 0 (null) | 150 | 30 | 120 | 0.027±0.002 | 0.034±0.003 | 0.033±0.003 |
| 0 (null) | 150 | 40 | 110 | 0.022±0.002 | 0.030±0.002 | 0.031±0.003 |

Jeffreys sensitivity grid: `power_grid.csv`, variant `jeffreys`.

## Limits

- The model assumes independent Bernoulli outcomes given p_t. It does not model drift in executor
  behaviour, build changes, or schedule effects, which the round-2 data show exist.
- Task probabilities are fixed from five A runs. Their own uncertainty is only reflected through the
  Jeffreys variant.
- Targets are marginal over tasks. A learning effect that concentrates on particular tasks would behave
  differently.
- E cost is unknown. Window selection must wait for Phase 2 with measured E cost, owner approval, and a
  fresh affordability check.
