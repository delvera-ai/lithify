# 3A — Simulation robustness sweep

- **Date:** 2026-10-23. **Code:** `4202bc7` + this branch (adds `LITHIFY_MOCK_SEED`). **Cost:** $0 (simulated agent).
- **Command:** `python eval/sim_sweep.py --orders 10 --out eval/results/2026-10-23-sim-sweep`
- **Design:** the 14 `lithify demo` tasks in 10 orders (seed 0 = demo order, seeds 1–9 shuffled), noise `LITHIFY_MOCK_NOISE ∈ {0, 0.1, 0.2}`, 3 strategies; 90 runs. `max_k = 2`, `window = 6` (demo settings), `auto_adopt = true` (demo setting). Noise is the probability that the simulated executor overlooks one convention it knows; draws are keyed on `(seed, probe label, feature)`.
- **Raw data:** `runs.jsonl` (per-run k, first-pass and S sequences, and the order), `results.csv`, `summary.md`.

Cells are mean ± sd [min–max] over 10 orders. Tokens are simulated: compare ratios, not absolute values.


### noise = 0.0

| strategy | delivered | first_pass | executions | role_sessions | tokens |
|---|---|---|---|---|---|
| baseline | 0.00 ± 0.00 [0–0] | 0.00 ± 0.00 [0–0] | 14.00 ± 0.00 [14–14] | 0.00 ± 0.00 [0–0] | 185752.00 ± 0.00 [185752–185752] |
| static | 14.00 ± 0.00 [14–14] | 12.10 ± 0.32 [12–13] | 17.90 ± 0.32 [17–18] | 43.90 ± 0.32 [43–44] | 870904.90 ± 14008.34 [831093–876476] |
| adaptive | 14.00 ± 0.00 [14–14] | 12.10 ± 0.32 [12–13] | 22.30 ± 0.67 [21–23] | 11.80 ± 2.25 [7–14] | 652435.70 ± 44071.70 [561601–697057] |

Paired adaptive − static, delivered: 0.00 ± 0.00 [0–0]; tokens ratio: 0.75 ± 0.04 [0.675738–0.795295]; role-session ratio: 0.27 ± 0.05 [0.162791–0.318182] (n=10 orders)

### noise = 0.1

| strategy | delivered | first_pass | executions | role_sessions | tokens |
|---|---|---|---|---|---|
| baseline | 0.00 ± 0.00 [0–0] | 0.00 ± 0.00 [0–0] | 14.00 ± 0.00 [14–14] | 0.00 ± 0.00 [0–0] | 185752.00 ± 0.00 [185752–185752] |
| static | 13.90 ± 0.32 [13–14] | 11.10 ± 1.10 [9–13] | 18.80 ± 0.92 [17–20] | 44.80 ± 0.92 [43–46] | 911480.80 ± 41178.95 [831093–969274] |
| adaptive | 13.90 ± 0.32 [13–14] | 11.10 ± 1.10 [9–13] | 23.90 ± 1.45 [21–26] | 18.70 ± 6.78 [7–32] | 774988.10 ± 114996.45 [561601–984313] |

Paired adaptive − static, delivered: 0.00 ± 0.00 [0–0]; tokens ratio: 0.85 ± 0.10 [0.675738–1.01552]; role-session ratio: 0.42 ± 0.15 [0.162791–0.695652] (n=10 orders)

### noise = 0.2

| strategy | delivered | first_pass | executions | role_sessions | tokens |
|---|---|---|---|---|---|
| baseline | 0.00 ± 0.00 [0–0] | 0.00 ± 0.00 [0–0] | 14.00 ± 0.00 [14–14] | 0.00 ± 0.00 [0–0] | 185752.00 ± 0.00 [185752–185752] |
| static | 13.90 ± 0.32 [13–14] | 10.30 ± 0.82 [9–12] | 19.70 ± 0.82 [18–21] | 45.70 ± 0.82 [44–47] | 950529.30 ± 36826.75 [876131–1.00938e+06] |
| adaptive | 13.90 ± 0.32 [13–14] | 10.10 ± 1.10 [8–12] | 25.40 ± 1.71 [23–29] | 24.00 ± 6.27 [14–36] | 875731.50 ± 115197.21 [696621–1.10798e+06] |

Paired adaptive − static, delivered: 0.00 ± 0.00 [0–0]; tokens ratio: 0.92 ± 0.10 [0.795111–1.09769]; role-session ratio: 0.52 ± 0.13 [0.318182–0.765957] (n=10 orders)

adaptive < static on delivered: none

## Findings

1. **Adaptive never delivered less than static.** The paired delivered difference is 0 in all 30 (order × noise) cells. Both miss one task in 1/10 orders at noise 0.1 and 0.2. Baseline delivers 0/14 by construction: the starter harness has none of the fixture's conventions and baseline never learns.
2. **Seed 0 reproduces the README demo table exactly** (static 874,532 tokens / 44 role calls; adaptive 635,177 / 11).
3. **The cost advantage shrinks with executor noise.** Adaptive/static token ratio: 0.75 ± 0.04 at noise 0, 0.85 ± 0.10 at 0.1, 0.92 ± 0.10 at 0.2. Adaptive costs **more** than static in 3/30 cells (noise 0.1 seed 5: 1.02; noise 0.2 seed 1: 1.01; noise 0.2 seed 7: 1.10). Role-session savings hold up better (ratio ≤ 0.77 everywhere).
4. **Mechanism (from the k and first-pass sequences in `runs.jsonl`):**
   - *Long genesis.* Every adaptive run opens with 4–7 tasks at `k = max_k` (distribution over 30 runs: 13×4, 13×5, 3×6, 1×7). Early failures keep S below `explore_below = 0.4`, and confidence ramps over the first 5 tasks, so first-pass successes on tasks 3–4 still don't lift S above 0.4. A `k = 2` task with failing bases costs up to 8 executions and 8 role sessions; static's `k = 1` costs at most 4 + 5.
   - *Noise is outcome variance, not a harness defect.* After the harness has learned every convention, a noise-induced miss still counts as a first-pass failure. It pulls S out of cruise and triggers exploration that cannot help, e.g. noise 0.1 seed 5: `k = …0, 1, 1, 1, 1, 1` after a failure at task 10. This is the "outcome variance" failure class from the Harness² taxonomy.
5. **Implications for Phase 4 (to be tested on live data, not tuned here):** the default `max_k` (3 in config, 2 in the demo) and the genesis length dominate adaptive's cost. Candidates: a lower default `max_k`, and leaving cruise only after a failure that a harness change could plausibly fix. Any change to the thresholds must be tuned on the development set only (rule 6).

## Limits

The simulated executor is deterministic apart from the injected noise, and its proposers are scripted, so this sweep tests the schedule and plumbing, not model behaviour.
