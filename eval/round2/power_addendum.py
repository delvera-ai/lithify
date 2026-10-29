"""Power addendum for the Phase 2 preregistration: between-seed effect variation and a concentrated effect.

Extends eval/round2/power.py, which assumes one common effect for every learning seed. Here:

- uniform: each (experiment, seed) draws its own marginal effect delta_s ~ N(delta, TAU). The seed-level
  spread is TAU. Each seed's per-task probability is p + lambda_s (1 - p), as in power.py.
- concentrated: each (experiment, seed) flips a random subset of K never-passing A tasks (A pass fraction 0)
  to pass probability FLIP_Q. K = round(delta * 60 / FLIP_Q), so the expected marginal effect is delta.
  Which tasks flip differs by seed.

Decision rules, all on the same primary positions (after warm-up), sign-flip at ALPHA with PERMS permutations:

- pooled: the power.py test on the seed-averaged per-position difference.
- pooled_all_seeds_positive: pooled rejects and every seed's own primary mean difference is > 0.
- every_seed_rejects: each seed's own sign-flip test rejects at ALPHA, unadjusted.

Null cells (delta 0) report the rejection rate, which is the calibration check.

    eval/round2/power_addendum.py   (repository interpreter with numpy)
"""

from __future__ import annotations

import csv

import numpy as np
from power import ALPHA, EXPERIMENTS, PERMS, WARMUPS, WINDOWS, sign_bank
from reanalysis import A_KEYS, OUT, SEED, load_manifest, run_vectors

EFFECTS = [0.0, 0.05, 0.10, 0.15]
SEEDS = [1, 2, 3, 4]
SCENARIOS = ["uniform", "concentrated"]
TAU = 0.05
FLIP_Q = 0.9
N_TASKS = 60


def simulate(scenario, p, delta, W, w, S, rng, bank):
    e = EXPERIMENTS
    t = rng.integers(0, N_TASKS, size=(e, W))
    pt = p[t]
    base = rng.random((e, S, W)) < pt[:, None, :]
    if scenario == "uniform":
        mean_one_minus_p = float(np.mean(1 - p))
        ds = rng.normal(delta, TAU, size=(e, S))
        lam = ds / mean_one_minus_p
        q = np.clip(pt[:, None, :] + lam[:, :, None] * (1 - pt[:, None, :]), 0, 1)
    else:
        never = np.flatnonzero(p == 0)
        k = int(round(delta * N_TASKS / FLIP_Q))
        flip = np.zeros((e, S, N_TASKS), dtype=bool)
        if k > 0:
            pick = np.argsort(rng.random((e, S, len(never))), axis=2)[:, :, :k]
            rows = np.arange(e)[:, None, None]
            seeds = np.arange(S)[None, :, None]
            flip[rows, seeds, never[pick]] = True
        flipped = np.take_along_axis(flip, np.broadcast_to(t[:, None, :], (e, S, W)), axis=2)
        q = np.where(flipped, FLIP_Q, pt[:, None, :])
    q[:, :, :w] = pt[:, None, :w]
    imp = rng.random((e, S, W)) < q
    diff = imp.astype(float) - base

    pooled = diff.mean(axis=1)[:, w:]
    obs = pooled.sum(axis=1)
    count = np.sum(pooled @ bank.T >= obs[:, None] - 1e-12, axis=1)
    pooled_rej = (1 + count) / (PERMS + 1) <= ALPHA

    seed_means = diff[:, :, w:].mean(axis=2)
    all_positive = np.all(seed_means > 0, axis=1)

    every_rej = np.ones(e, dtype=bool)
    for s in range(S):
        ds_ = diff[:, s, w:]
        o = ds_.sum(axis=1)
        c = np.sum(ds_ @ bank.T >= o[:, None] - 1e-12, axis=1)
        every_rej &= (1 + c) / (PERMS + 1) <= ALPHA
    return {
        "pooled": float(pooled_rej.mean()),
        "pooled_all_seeds_positive": float((pooled_rej & all_positive).mean()),
        "every_seed_rejects": float(every_rej.mean()),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tasks = load_manifest()
    runs = run_vectors(tasks)
    A = np.stack([runs[key]["passed"] for key in A_KEYS], axis=1)
    p = A.mean(axis=1)
    banks = {}
    rows = []
    cell_id = 0
    for scenario in SCENARIOS:
        for W in WINDOWS:
            for w in WARMUPS:
                n = W - w
                if n not in banks:
                    banks[n] = sign_bank(n)
                for S in SEEDS:
                    for delta in EFFECTS:
                        cell_id += 1
                        rng = np.random.default_rng([SEED, 1000 + cell_id])
                        res = simulate(scenario, p, delta, W, w, S, rng, banks[n])
                        for rule, value in res.items():
                            rows.append(
                                {
                                    "scenario": scenario,
                                    "effect": delta,
                                    "window_total": W,
                                    "warmup": w,
                                    "primary_n": n,
                                    "seeds": S,
                                    "rule": rule,
                                    "power": round(value, 4),
                                    "kind": "null calibration" if delta == 0 else "power",
                                }
                            )
    path = OUT / "power_addendum_grid.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print("wrote", path)


if __name__ == "__main__":
    main()
