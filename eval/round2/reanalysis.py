"""Phase-0 reanalysis, registered in eval/round2/REANALYSIS_PLAN.md.

Exploratory only: no causal learning attribution is made. Reads round-1 and round-2 results,
checks them against INPUT_MANIFEST.json, and writes CSV/JSON outputs to
eval/results/2026-10-29-r2-noise/.

    eval/round2/reanalysis.py   (repository interpreter with numpy)
"""

from __future__ import annotations

import csv
import itertools
import json
import statistics
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "eval/results"
OUT = RESULTS / "2026-10-29-r2-noise"
SEED = 20261027
BOOT = 20_000
SIGNFLIP_RANDOM = 200_000
EXACT_MAX = 20

R1_DIR = "2026-10-26-horizon"
R2_A = "2026-10-27-r2-noise-replicates"
R2_B = "2026-10-29-r2-ab-overlap"

RUNS = {
    "A1": (f"{R1_DIR}/results-sqlglot-baseline-claude_claude-haiku-5-5.csv", "round1"),
    "A2": (f"{R2_A}/results-r1-A-rep2.csv", "round2"),
    "A3": (f"{R2_A}/results-r1-A-rep3.csv", "round2"),
    "A4": (f"{R2_A}/results-r1-A-rep4.csv", "round2"),
    "A5": (f"{R2_A}/results-r1-A-rep5.csv", "round2"),
    "B1": (f"{R1_DIR}/results-sqlglot-adaptive-claude_claude-haiku-5-5.csv", "round1"),
    "B2": (f"{R2_B}/results-r1-B-rep2.csv", "round2"),
    "B3": (f"{R2_B}/results-r1-B-rep3.csv", "round2"),
    "C1": (f"{R1_DIR}/results-sqlglot-adaptive-feedback-claude_claude-haiku-5-5.csv", "round1"),
}
A_KEYS = ["A1", "A2", "A3", "A4", "A5"]
B_KEYS = ["B1", "B2", "B3"]
WINS_B = [3, 20, 30, 39]
WINS_C = [12, 14, 30, 39, 45]


def load_manifest() -> list[dict]:
    manifest = json.loads((ROOT / "eval/round2/INPUT_MANIFEST.json").read_text(encoding="utf-8"))
    tasks = sorted(manifest["tasks"], key=lambda t: t["position"])
    assert [t["position"] for t in tasks] == list(range(1, 61))
    return tasks


def load_run(path: Path, kind: str) -> dict[str, dict]:
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    by_task = {}
    for r in rows:
        assert r["task"] not in by_task, f"duplicate task in {path.name}: {r['task']}"
        by_task[r["task"]] = r
    assert len(by_task) == 60, f"{path.name} has {len(by_task)} tasks"
    return by_task


def run_vectors(tasks: list[dict]) -> dict[str, dict]:
    keys = [f"sqlglot#{t['number']}" for t in tasks]
    out = {}
    for run, (rel, kind) in RUNS.items():
        rows = load_run(RESULTS / rel, kind)
        assert set(rows) == set(keys), f"{run}: task keys differ from manifest"
        if kind == "round1":
            passed = [rows[k]["holdout_pass"] == "True" for k in keys]
        else:
            passed = [rows[k]["outcome"] == "pass" for k in keys]
        delivered = [rows[k]["delivered"] == "True" for k in keys]
        cost = [float(rows[k]["cost_usd"] or 0) for k in keys]
        wall = [float(rows[k]["wall_s"] or 0) for k in keys]
        outcome = [rows[k].get("outcome") or ("pass" if p else "failure") for k, p in zip(keys, passed, strict=True)]
        out[run] = {
            "passed": np.array(passed, dtype=bool),
            "delivered": np.array(delivered, dtype=bool),
            "cost": np.array(cost),
            "wall": np.array(wall),
            "outcome": outcome,
            "source": rel,
            "kind": kind,
        }
    return out


def signflip(d: np.ndarray, label: str) -> dict:
    """One-sided sign-flip test of the mean (or sum) of paired differences d, with a paired task bootstrap."""
    obs = float(d.sum())
    nz = d[d != 0]
    rng = np.random.default_rng(SEED)
    if len(nz) <= EXACT_MAX:
        signs = np.array(list(itertools.product((-1.0, 1.0), repeat=len(nz))))
        sums = signs @ nz
        p = float(np.mean(sums >= obs - 1e-12))
        method = f"exact 2^{len(nz)}"
    else:
        count = 0
        chunk = 20_000
        for _ in range(0, SIGNFLIP_RANDOM, chunk):
            signs = rng.choice((-1.0, 1.0), size=(chunk, len(nz)))
            count += int(np.sum(signs @ nz >= obs - 1e-12))
        p = (count + 1) / (SIGNFLIP_RANDOM + 1)
        method = f"random {SIGNFLIP_RANDOM} with plus-one correction"
    idx = rng.integers(0, len(d), size=(BOOT, len(d)))
    means = d[idx].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return {
        "label": label,
        "n_tasks": len(d),
        "n_nonzero": len(nz),
        "mean_difference": float(d.mean()),
        "ci95_task_bootstrap": [float(lo), float(hi)],
        "one_sided_p": p,
        "method": method,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tasks = load_manifest()
    runs = run_vectors(tasks)
    keys = list(RUNS)
    P = np.stack([runs[k]["passed"] for k in keys], axis=1).astype(float)  # 60 x 9
    idx = {k: i for i, k in enumerate(keys)}
    A = np.stack([runs[k]["passed"] for k in A_KEYS], axis=1)
    pfrac = A.mean(axis=1)
    always = int(np.sum(pfrac == 1))
    never = int(np.sum(pfrac == 0))
    sometimes = 60 - always - never

    # Per-task table.
    with (OUT / "per_task.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["position", "task", "pr", *keys, "A_pass_fraction", "A_class"])
        for i, t in enumerate(tasks):
            cls = "always" if pfrac[i] == 1 else "never" if pfrac[i] == 0 else "sometimes"
            w.writerow(
                [
                    t["position"],
                    f"sqlglot#{t['number']}",
                    t["number"],
                    *[int(P[i, j]) for j in range(len(keys))],
                    f"{pfrac[i]:.4f}",
                    cls,
                ]
            )

    # Pairwise A discordance, including non-deliveries separately.
    pairs = list(itertools.combinations(A_KEYS, 2))
    D = np.zeros((60, len(pairs)), dtype=bool)
    pair_rows = []
    for c, (a, b) in enumerate(pairs):
        dis = runs[a]["passed"] != runs[b]["passed"]
        D[:, c] = dis
        pair_rows.append(
            {
                "pair": f"{a}-{b}",
                "discordant_tasks": int(dis.sum()),
                "fraction": float(dis.mean()),
                "both_pass": int(np.sum(runs[a]["passed"] & runs[b]["passed"])),
                "both_fail": int(np.sum(~runs[a]["passed"] & ~runs[b]["passed"])),
                "a_only_pass": int(np.sum(runs[a]["passed"] & ~runs[b]["passed"])),
                "b_only_pass": int(np.sum(~runs[a]["passed"] & runs[b]["passed"])),
            }
        )
    with (OUT / "pairs.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(pair_rows[0]))
        w.writeheader()
        w.writerows(pair_rows)
    noise_mean = float(D.mean())
    rng = np.random.default_rng(SEED)
    boot_idx = rng.integers(0, 60, size=(BOOT, 60))
    boot_stat = D[boot_idx].mean(axis=(1, 2))
    noise_ci = [float(x) for x in np.percentile(boot_stat, [2.5, 97.5])]

    # Per-run delivery and cost summary.
    run_rows = []
    for k in keys:
        r = runs[k]
        run_rows.append(
            {
                "run": k,
                "source": r["source"],
                "pass": int(r["passed"].sum()),
                "delivered": int(r["delivered"].sum()),
                "non_delivered": int((~r["delivered"]).sum()),
                "timeouts": sum(o == "timeout" for o in r["outcome"]),
                "cost_usd": round(float(r["cost"].sum()), 4),
                "mean_cost_usd": round(float(r["cost"].mean()), 5),
                "median_wall_s": round(float(statistics.median(r["wall"])), 2),
            }
        )
    with (OUT / "runs.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(run_rows[0]))
        w.writeheader()
        w.writerows(run_rows)

    # Registered wins with baseline pass fractions.
    wins = {
        "B_wins": [
            {
                "position": p,
                "task": f"sqlglot#{tasks[p - 1]['number']}",
                "A1": bool(runs["A1"]["passed"][p - 1]),
                "B1": bool(runs["B1"]["passed"][p - 1]),
                "A_pass_fraction": float(pfrac[p - 1]),
                "A_class": "always" if pfrac[p - 1] == 1 else "never" if pfrac[p - 1] == 0 else "sometimes",
            }
            for p in WINS_B
        ],
        "C_wins": [
            {
                "position": p,
                "task": f"sqlglot#{tasks[p - 1]['number']}",
                "A1": bool(runs["A1"]["passed"][p - 1]),
                "C1": bool(runs["C1"]["passed"][p - 1]),
                "A_pass_fraction": float(pfrac[p - 1]),
                "A_class": "always" if pfrac[p - 1] == 1 else "never" if pfrac[p - 1] == 0 else "sometimes",
            }
            for p in WINS_C
        ],
    }

    # Comparisons to mean A, all 60 and primary 31-60.
    mean_b = P[:, [idx[k] for k in B_KEYS]].mean(axis=1)
    c1 = P[:, idx["C1"]]
    b1 = P[:, idx["B1"]]
    comparisons = {}
    for window, sl in (("all60", slice(0, 60)), ("primary31_60", slice(30, 60))):
        for label, arr in (("C1_minus_meanA", c1), ("meanB_minus_meanA", mean_b), ("B1_minus_meanA", b1)):
            d = (arr - pfrac)[sl]
            comparisons[f"{label}|{window}"] = signflip(d, f"{label} {window}")

    # Build-sensitivity: A2-A5 and B2-B3 share product 89020d7; A1, B1 and C1 are round-1 f964993 runs.
    r2_a = np.stack([runs[k]["passed"] for k in ["A2", "A3", "A4", "A5"]], axis=1).mean(axis=1)
    r2_b = P[:, [idx["B2"], idx["B3"]]].mean(axis=1)
    for window, sl in (("all60", slice(0, 60)), ("primary31_60", slice(30, 60))):
        comparisons[f"meanB23_minus_meanA2to5|{window}|round2_build_only"] = signflip(
            (r2_b - r2_a)[sl], f"meanB23_minus_meanA2to5 {window}"
        )

    # Determinism check registered in the plan: identical raw output is required to stop.
    a1_a2_discord = int(np.sum(runs["A1"]["passed"] != runs["A2"]["passed"]))
    result = {
        "seed": SEED,
        "bootstrap_draws": BOOT,
        "signflip_random": SIGNFLIP_RANDOM,
        "a_pass_fraction": {
            "always_pass": always,
            "never_pass": never,
            "sometimes_pass": sometimes,
        },
        "noise_floor_mean_pairwise_disagreement": noise_mean,
        "noise_floor_ci95": noise_ci,
        "a1_a2_discordant_tasks": a1_a2_discord,
        "wins": wins,
        "comparisons": comparisons,
        "round2_outcome_matches_passed": all(
            (runs[k]["outcome"][i] == "pass") == bool(runs[k]["passed"][i]) for k in keys for i in range(60)
        ),
    }
    (OUT / "reanalysis.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in result if k not in ("wins", "comparisons")}, indent=2))
    for name, c in comparisons.items():
        print(name, {k: c[k] for k in ("mean_difference", "ci95_task_bootstrap", "one_sided_p", "method", "n_nonzero")})


if __name__ == "__main__":
    main()
