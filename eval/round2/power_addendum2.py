"""Power addendum 2 for the Phase 2 preregistration.

Extends eval/round2/power_addendum.py with three things the owner asked for:

(i)  The conjunction rule AP: the pooled sign-flip p < .05 AND every learning seed's own primary mean
     difference is positive. Null rate and power are reported for AP directly.
(ii) Designs with 4, 5 or 6 learning seeds on W = 60, 70, 80 tasks. Baseline seeds are fixed at 3.
     Each learning seed's difference is taken against the mean of the 3 baseline seeds at the same position.
(iii) An internal pilot. The first 3 learning seeds, on warm-up positions only, estimate tau as the SD across
     seeds of the per-seed warm-up mean difference. A pre-registered rule then picks S in {4, 5, 6}:
     S = 4 if tau_hat <= 0.04, S = 5 if tau_hat <= 0.07, else S = 6. The thresholds are a candidate for the
     preregistration, not estimated. Power and null rates are reported for the realised S.

Modelling choice that differs from power_addendum.py: the learning effect also applies during warm-up. A
pilot on warm-up tasks would otherwise see only noise. The earlier grid assumed no warm-up effect. This
addendum reports both the uniform and concentrated scenarios with the effect present in warm-up.

The baseline mean is taken over 3 seeds per position, so the baseline noise is shared across learning seeds.
Only the pooled sign-flip test and the seed-sign rule are computed here. Per-seed sign-flip tests are not
needed for the claim rule, and they are in power_addendum.py.

    eval/round2/power_addendum2.py   (run with numpy; see the commit message for the command)
"""

from __future__ import annotations

import csv

import numpy as np
from power import ALPHA, EXPERIMENTS, PERMS, sign_bank
from reanalysis import A_KEYS, OUT, SEED, load_manifest, run_vectors

N_TASKS = 60
BASE_SEEDS = 3
MAX_SEEDS = 6
PILOT_SEEDS = 3
DESIGN_SEEDS = [4, 5, 6]
WINDOWS = [60, 70, 80]
WARMUPS = [20, 30]
EFFECTS = [0.0, 0.10]
TAUS = [0.0, 0.03, 0.05, 0.08]
FLIP_Q = 0.9


def draw(p, scenario, delta, tau, W, rng):
    e = EXPERIMENTS
    t = rng.integers(0, N_TASKS, size=(e, W))
    pt = p[t]
    base = rng.random((e, BASE_SEEDS, W)) < pt[:, None, :]
    if scenario == "uniform":
        lam = rng.normal(delta, tau, size=(e, MAX_SEEDS)) / float(np.mean(1 - p))
        q = np.clip(pt[:, None, :] + lam[:, :, None] * (1 - pt[:, None, :]), 0, 1)
    else:
        never = np.flatnonzero(p == 0)
        k = int(round(delta * N_TASKS / FLIP_Q))
        flip = np.zeros((e, MAX_SEEDS, N_TASKS), dtype=bool)
        if k > 0:
            pick = np.argsort(rng.random((e, MAX_SEEDS, len(never))), axis=2)[:, :, :k]
            rows = np.arange(e)[:, None, None]
            seeds = np.arange(MAX_SEEDS)[None, :, None]
            flip[rows, seeds, never[pick]] = True
        flipped = np.take_along_axis(flip, np.broadcast_to(t[:, None, :], (e, MAX_SEEDS, W)), axis=2)
        q = np.where(flipped, FLIP_Q, pt[:, None, :])
    imp = rng.random((e, MAX_SEEDS, W)) < q
    base_mean = base.mean(axis=1)
    return imp.astype(float) - base_mean[:, None, :], imp


def pilot_tau(diff, imp, w):
    """Method-of-moments tau estimate from the pilot seeds on warm-up positions.

    The across-seed variance of each pilot seed's warm-up mean is tau^2 plus sampling variance. The sampling
    variance is sum_i q(1-q) / w^2, estimated from the pilot seeds' pooled outcome rate. E[m(1-m)] = q(1-q)(1-1/n)
    for n = 3 Bernoulli draws, so the plug-in is scaled by n/(n-1) = 3/2.
    """
    seed_means = diff[:, :PILOT_SEEDS, :w].mean(axis=2)
    between = seed_means.var(axis=1, ddof=1)
    qbar = imp[:, :PILOT_SEEDS, :w].mean(axis=1)
    sampling = 1.5 * (qbar * (1 - qbar)).sum(axis=1) / (w * w)
    return np.sqrt(np.maximum(between - sampling, 0.0))


def pooled_reject(diff, S, w, bank):
    primary = diff[:, :S, w:]
    pooled = primary.mean(axis=1)
    obs = pooled.sum(axis=1)
    count = np.sum(pooled @ bank.T >= obs[:, None] - 1e-12, axis=1)
    rej = (1 + count) / (PERMS + 1) <= ALPHA
    all_positive = np.all(primary.mean(axis=2) > 0, axis=1)
    return rej, rej & all_positive


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tasks = load_manifest()
    runs = run_vectors(tasks)
    A = np.stack([runs[key]["passed"] for key in A_KEYS], axis=1)
    p = A.mean(axis=1)
    banks = {}
    rows = []
    cell = 0
    for scenario in ["uniform", "concentrated"]:
        taus = TAUS if scenario == "uniform" else [None]
        for tau in taus:
            for delta in EFFECTS:
                for W in WINDOWS:
                    for w in WARMUPS:
                        n = W - w
                        if n not in banks:
                            banks[n] = sign_bank(n)
                        cell += 1
                        rng = np.random.default_rng([SEED, 5000 + cell])
                        diff, imp = draw(p, scenario, delta, 0.0 if tau is None else tau, W, rng)
                        tau_hat = pilot_tau(diff, imp, w)
                        s_adapt = np.where(tau_hat <= 0.04, 4, np.where(tau_hat <= 0.07, 5, 6))
                        results = {}
                        for S in DESIGN_SEEDS:
                            results[S] = pooled_reject(diff, S, w, banks[n])
                        adapt_p = np.where(s_adapt == 4, results[4][0],
                                           np.where(s_adapt == 5, results[5][0], results[6][0]))
                        adapt_ap = np.where(s_adapt == 4, results[4][1],
                                            np.where(s_adapt == 5, results[5][1], results[6][1]))
                        designs = [(f"fixed {S}", results[S][0].mean(), results[S][1].mean(), S)
                                   for S in DESIGN_SEEDS]
                        if scenario == "uniform":
                            designs.append(("adaptive", adapt_p.mean(), adapt_ap.mean(),
                                            float(s_adapt.mean())))
                        for label, pw, ap, s_mean in designs:
                            rows.append({
                                "scenario": scenario,
                                "tau_true": "" if tau is None else tau,
                                "effect": delta,
                                "window_total": W,
                                "warmup": w,
                                "primary_n": n,
                                "design": label,
                                "mean_learning_seeds": round(float(s_mean), 3),
                                "baseline_seeds": BASE_SEEDS,
                                "power_P": round(float(pw), 4),
                                "power_AP": round(float(ap), 4),
                                "kind": "null calibration" if delta == 0 else "power",
                            })
                        if scenario == "uniform":
                            rows.append({
                                "scenario": scenario,
                                "tau_true": tau,
                                "effect": delta,
                                "window_total": W,
                                "warmup": w,
                                "primary_n": n,
                                "design": "pilot tau_hat: mean_learning_seeds=median, power_P=q10, power_AP=q90",
                                "mean_learning_seeds": round(float(np.median(tau_hat)), 4),
                                "baseline_seeds": BASE_SEEDS,
                                "power_P": round(float(np.quantile(tau_hat, 0.1)), 4),
                                "power_AP": round(float(np.quantile(tau_hat, 0.9)), 4),
                                "kind": "pilot",
                            })
    path = OUT / "power_addendum2_grid.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print("wrote", path)


if __name__ == "__main__":
    main()
