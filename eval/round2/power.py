"""Power simulation registered in eval/round2/REANALYSIS_PLAN.md.

A model, not an identified prediction. Baseline task probabilities come from the five A runs
(empirical pass fractions, plus a Jeffreys-smoothed sensitivity variant). The improved arm uses
q = p + lambda * (1 - p), with lambda chosen so the uniform task-average effect equals the target.
Each experiment draws W task positions, averages seeds within each position, and runs a one-sided
sign-flip test on primary positions (after warm-up) with 1,999 permutations at alpha .05. Rejection
rates at effect 0 are reported as null calibration. No observed-effect threshold is used.

    eval/round2/power.py   (repository interpreter with numpy)
"""

from __future__ import annotations

import csv
import json
import statistics

import numpy as np
from reanalysis import A_KEYS, OUT, SEED, load_manifest, run_vectors

EFFECTS = [0.0, 0.05, 0.10, 0.15]
WINDOWS = [60, 100, 150]
SEEDS = [1, 2, 3]
WARMUPS = [20, 30, 40]
EXPERIMENTS = 5000
PERMS = 1999
ALPHA = 0.05


def lam_for(p: np.ndarray, delta: float) -> tuple[float, bool]:
    if delta == 0:
        return 0.0, True
    lam = delta / float(np.mean(1 - p))
    return lam, lam <= 1


def sign_bank(n: int) -> np.ndarray:
    rng = np.random.default_rng(SEED)
    return rng.choice((-1.0, 1.0), size=(PERMS, n))


def one_cell(p: np.ndarray, delta: float, W: int, w: int, S: int, rng: np.random.Generator, bank: np.ndarray):
    lam, feasible = lam_for(p, delta)
    if not feasible:
        return None
    q = p + lam * (1 - p)
    t = rng.integers(0, len(p), size=(EXPERIMENTS, W))
    pt = p[t]
    qt = q[t]
    pimp = np.concatenate([pt[:, :w], qt[:, w:]], axis=1)
    base = rng.random((EXPERIMENTS, S, W)) < pt[:, None, :]
    imp = rng.random((EXPERIMENTS, S, W)) < pimp[:, None, :]
    d = imp.mean(axis=1)[:, w:] - base.mean(axis=1)[:, w:]
    obs = d.sum(axis=1)
    perm = d @ bank.T
    count = np.sum(perm >= obs[:, None] - 1e-12, axis=1)
    pval = (1 + count) / (PERMS + 1)
    rej = pval <= ALPHA
    power = float(rej.mean())
    mcse = float(np.sqrt(power * (1 - power) / EXPERIMENTS))
    return {"power": power, "mcse": mcse, "lambda": lam, "feasible": True}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tasks = load_manifest()
    runs = run_vectors(tasks)
    A = np.stack([runs[k]["passed"] for k in A_KEYS], axis=1)
    p_emp = A.mean(axis=1)
    k_pass = A.sum(axis=1)
    p_jeff = (k_pass + 0.5) / 6
    variants = {"empirical": p_emp, "jeffreys": p_jeff}
    banks = {}
    rows = []
    cell_id = 0
    for variant, p in variants.items():
        for W in WINDOWS:
            for w in WARMUPS:
                n = W - w
                if n not in banks:
                    banks[n] = sign_bank(n)
                for S in SEEDS:
                    for delta in EFFECTS:
                        cell_id += 1
                        rng = np.random.default_rng([SEED, cell_id])
                        res = one_cell(p, delta, W, w, S, rng, banks[n])
                        row = {
                            "variant": variant,
                            "effect": delta,
                            "window_total": W,
                            "warmup": w,
                            "primary_n": n,
                            "seeds": S,
                            "power": None if res is None else round(res["power"], 4),
                            "mcse": None if res is None else round(res["mcse"], 4),
                            "lambda": None if res is None else round(res["lambda"], 4),
                            "feasible": res is not None,
                            "kind": "null calibration" if delta == 0 else "power",
                        }
                        rows.append(row)

    with (OUT / "power_grid.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    cost_a = [float(runs[k]["cost"].mean()) for k in A_KEYS]
    wall_a = [float(statistics.median(runs[k]["wall"])) for k in A_KEYS]
    cost_table = []
    for W in WINDOWS:
        for w in WARMUPS:
            for S in SEEDS:
                cost_table.append(
                    {
                        "window_total": W,
                        "warmup": w,
                        "primary_n": W - w,
                        "seeds": S,
                        "paid_warmup_tasks_all_seeds": S * w,
                        "baseline_arm_tasks": S * W,
                        "baseline_arm_usd_at_measured_A_mean": round(S * W * statistics.mean(cost_a), 2),
                        "baseline_arm_median_wall_hours_serial": round(S * W * statistics.mean(wall_a) / 3600, 2),
                    }
                )
    summary = {
        "seed": SEED,
        "experiments_per_cell": EXPERIMENTS,
        "permutations": PERMS,
        "alpha": ALPHA,
        "empirical_pass_fraction_mean": round(float(p_emp.mean()), 4),
        "jeffreys_pass_fraction_mean": round(float(p_jeff.mean()), 4),
        "mean_one_minus_p_empirical": round(float(np.mean(1 - p_emp)), 4),
        "measured_A_mean_cost_usd_per_task": round(statistics.mean(cost_a), 5),
        "measured_A_median_wall_s": round(statistics.mean(wall_a), 2),
        "E_cost": "unknown until Phase 1; not priced as B",
        "cost_table": cost_table,
    }
    (OUT / "power_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(
        "empirical mean p",
        summary["empirical_pass_fraction_mean"],
        "| jeffreys mean p",
        summary["jeffreys_pass_fraction_mean"],
        "| mean(1-p) empirical",
        summary["mean_one_minus_p_empirical"],
    )
    for r in rows:
        if r["variant"] == "empirical" and r["seeds"] == 3:
            print(r["effect"], r["window_total"], r["warmup"], r["primary_n"], r["power"], r["mcse"], r["lambda"])


if __name__ == "__main__":
    main()
