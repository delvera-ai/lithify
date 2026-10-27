"""Zero-token oracle checks for the frozen 60-task horizon; no task reselection."""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evalkit import redact
from repos import REPOS, prepare_checkout, run_holdout


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    a.work = a.work.resolve()
    a.out.mkdir(parents=True, exist_ok=True)
    py = str(a.work / "env-sqlglot/bin/python")
    os.environ["PATH"] = str(Path(py).parent) + os.pathsep + os.environ["PATH"]
    root = Path(__file__).resolve().parents[2]
    prs = [p for p in json.loads((root / "eval/prs/sqlglot/prs.json").read_text())["prs"] if p["split"] == "eval"][:60]
    chunks = [list(enumerate(prs, 1))[i :: a.workers] for i in range(a.workers)]

    def shard(index: int) -> list[dict]:
        clone = a.work / f"oracle-shard-{index}"
        if not clone.exists():
            subprocess.run(["git", "clone", "-q", str(a.work / "sqlglot.git"), str(clone)], check=True)
        rows = []
        for pos, pr in chunks[index]:
            result_file = a.out / f"{pos:02d}-pr{pr['number']}.json"
            if result_file.exists():
                rows.append(json.loads(result_file.read_text()))
                continue
            t0 = time.monotonic()
            hdir = a.work / "holdouts/sqlglot" / str(pr["number"])
            logs = a.work / "oracle-logs" / str(pr["number"])
            logs.mkdir(parents=True, exist_ok=True)
            prepare_checkout("sqlglot", clone, pr["base"])
            base = run_holdout("sqlglot", clone, hdir, py, logs / "holdout-base.txt")
            prepare_checkout("sqlglot", clone, pr["merge"])
            merge = run_holdout("sqlglot", clone, hdir, py, logs / "holdout-merge.txt")
            cmd = REPOS["sqlglot"]["test_cmd"].format(py=py)
            try:
                suite = subprocess.run(cmd, shell=True, cwd=clone, capture_output=True, text=True, timeout=900)
                suite_rc = suite.returncode
                suite_output = suite.stdout + suite.stderr
            except subprocess.TimeoutExpired:
                suite_rc, suite_output = 124, "suite timeout at 900s"
            (logs / "suite-merge.txt").write_text(suite_output)
            row = {
                "position": pos,
                "pr": pr["number"],
                "base": pr["base"],
                "merge": pr["merge"],
                "holdout_base_rc": base,
                "holdout_merge_rc": merge,
                "suite_merge_rc": suite_rc,
                "valid": base == 1 and merge == 0 and suite_rc == 0,
                "wall_s": round(time.monotonic() - t0, 1),
            }
            result_file.write_text(json.dumps(row, indent=2) + "\n")
            for name in ("holdout-base.txt", "holdout-merge.txt", "suite-merge.txt"):
                dest = a.out / "logs" / str(pr["number"]) / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(redact((logs / name).read_text(), {str(a.work): "<scratch>"}))
            rows.append(row)
            print(json.dumps(row), flush=True)
        return rows

    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
        rows = sorted((r for batch in pool.map(shard, range(a.workers)) for r in batch), key=lambda r: r["position"])
    with (a.out / "oracle.csv").open("w") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"COMPLETE: {sum(r['valid'] for r in rows)}/{len(rows)} valid; zero tokens", flush=True)


if __name__ == "__main__":
    main()
