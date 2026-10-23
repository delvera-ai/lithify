"""Phase 3A: simulation robustness sweep (credential-free; safe for CI).

Runs the `lithify demo` task sequence under baseline / static / adaptive across shuffled task
orders and mock noise levels, and reports mean and spread per strategy. The billing area is
new in every order, so each shuffle moves the point where the harness meets an unseen
convention.

    python eval/sim_sweep.py                              # 10 orders x noise {0, 0.1, 0.2}
    python eval/sim_sweep.py --orders 2 --noise 0,0.2     # quick (CI)
    python eval/sim_sweep.py --out eval/results/<date>-sim-sweep
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import statistics
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path

from lithify.demo import TASKS, run_strategy

STRATEGIES = ("baseline", "static", "adaptive")
METRICS = ("delivered", "first_pass", "executions", "role_sessions", "tokens")


def order_for(seed: int) -> list[tuple[str, str]]:
    tasks = list(TASKS)
    if seed:  # seed 0 is the canonical demo order
        random.Random(seed).shuffle(tasks)
    return tasks


def one(job: tuple[int, float, str, int]) -> dict:
    seed, noise, strategy, max_k = job
    os.environ["LITHIFY_MOCK_NOISE"] = str(noise)
    os.environ["LITHIFY_MOCK_SEED"] = f"s{seed}:"
    with tempfile.TemporaryDirectory(prefix="lithify-sweep-") as td:
        os.environ["LITHIFY_WORK_DIR"] = str(Path(td) / "_work")
        tasks = order_for(seed)
        t0 = time.time()
        r = run_strategy(strategy, Path(td), tasks, max_k, quiet=True)
    row = asdict(r)
    row.update(seed=seed, noise=noise, strategy=strategy, max_k=max_k, n_tasks=len(tasks), wall_s=round(time.time() - t0, 1))
    row["order"] = [t for t, _ in tasks]
    return row


def spread(xs: list[float]) -> str:
    if not xs:
        return "-"
    sd = statistics.stdev(xs) if len(xs) > 1 else 0.0
    return f"{statistics.mean(xs):.2f} ± {sd:.2f} [{min(xs):g}–{max(xs):g}]"


def summarise(rows: list[dict]) -> tuple[str, list[str]]:
    lines = []
    anomalies = []
    for noise in sorted({r["noise"] for r in rows}):
        lines.append(f"\n### noise = {noise}\n")
        lines.append("| strategy | " + " | ".join(METRICS) + " |")
        lines.append("|---|" + "---|" * len(METRICS))
        for s in STRATEGIES:
            sel = [r for r in rows if r["noise"] == noise and r["strategy"] == s]
            if sel:
                lines.append(f"| {s} | " + " | ".join(spread([r[m] for r in sel]) for m in METRICS) + " |")
        by_seed: dict[int, dict[str, dict]] = {}
        for r in rows:
            if r["noise"] == noise:
                by_seed.setdefault(r["seed"], {})[r["strategy"]] = r
        for seed, d in sorted(by_seed.items()):
            if "static" in d and "adaptive" in d and d["adaptive"]["delivered"] < d["static"]["delivered"]:
                anomalies.append(
                    f"noise={noise} seed={seed}: adaptive delivered {d['adaptive']['delivered']} < static "
                    f"{d['static']['delivered']} (adaptive k={d['adaptive']['ks']}, first={d['adaptive']['first']})"
                )
        pairs = [(d["adaptive"], d["static"]) for d in by_seed.values() if "static" in d and "adaptive" in d]
        if pairs:
            dd = [a["delivered"] - b["delivered"] for a, b in pairs]
            tr = [a["tokens"] / b["tokens"] for a, b in pairs if b["tokens"]]
            rr = [a["role_sessions"] / b["role_sessions"] for a, b in pairs if b["role_sessions"]]
            lines.append(
                f"\nPaired adaptive − static, delivered: {spread(dd)}; tokens ratio: {spread(tr)}; "
                f"role-session ratio: {spread(rr)} (n={len(pairs)} orders)"
            )
    return "\n".join(lines), anomalies


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--orders", type=int, default=10, help="number of task orders (seed 0 = demo order)")
    ap.add_argument("--noise", default="0,0.1,0.2")
    ap.add_argument("--max-k", type=int, default=2)
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--out", help="write runs.jsonl, results.csv and summary.md here")
    ap.add_argument("--strict", action="store_true", help="exit 1 if adaptive ever delivers less than static")
    a = ap.parse_args(argv)
    noises = [float(x) for x in a.noise.split(",")]
    jobs = [(seed, n, s, a.max_k) for n in noises for seed in range(a.orders) for s in STRATEGIES]
    with ProcessPoolExecutor(max_workers=a.jobs) as ex:
        rows = list(ex.map(one, jobs))
    table, anomalies = summarise(rows)
    print(table)
    print("\nadaptive < static on delivered:", "none" if not anomalies else "")
    for x in anomalies:
        print("  " + x)
    if a.out:
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        with open(out / "runs.jsonl", "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        cols = ["noise", "seed", "strategy", "max_k", "n_tasks", *METRICS, "always_on", "final_s", "wall_s", "ks"]
        with open(out / "results.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(cols)
            for r in sorted(rows, key=lambda r: (r["noise"], r["seed"], STRATEGIES.index(r["strategy"]))):
                w.writerow([" ".join(map(str, r[c])) if c == "ks" else r[c] for c in cols])
        found = "none" if not anomalies else "\n- " + "\n- ".join(anomalies)
        (out / "summary.md").write_text(f"{table}\n\nadaptive < static on delivered: {found}\n", encoding="utf-8")
    return 1 if (a.strict and anomalies) else 0


if __name__ == "__main__":
    sys.exit(main())
