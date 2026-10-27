"""Launch only the owner's one capped calibration, after all oracle checks pass."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume-after-limit", action="store_true")
    options = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    work = Path.home() / ".cache/lithify-dev/r2-noise-scratch"
    out = root / "eval/results/2026-10-27-r2-calibration"
    oracle = root / "eval/results/2026-10-27-r2-preflight/oracle.csv"
    with oracle.open() as f:
        checks = list(csv.DictReader(f))
    frozen = json.loads((root / "eval/round2/INPUT_MANIFEST.json").read_text())["tasks"]
    assert len(checks) == 60 and {int(r["pr"]) for r in checks} == {p["number"] for p in frozen}
    frozen_by_pr = {p["number"]: p for p in frozen}
    assert all(
        (r["base"], r["merge"]) == (frozen_by_pr[int(r["pr"])]["base"], frozen_by_pr[int(r["pr"])]["merge"]) for r in checks
    )
    assert all((r["holdout_base_rc"], r["holdout_merge_rc"], r["suite_merge_rc"]) == ("1", "0", "0") for r in checks)
    assert not list(out.glob("results*.csv")), "Calibration already recorded; no repeat authorized"
    scratch = work / "replay-r2-calibration-calibration-A1"
    if options.resume_after_limit:
        authorization = json.loads((out / "limit-resume-authorization.json").read_text())
        assert authorization["classification"] == "CLI session limit"
        assert authorization["recorded_cost"] == authorization["tokens"] == 0
        assert not authorization["task_completed"]
        assert json.loads((scratch / "progress.json").read_text())["next_pos"] == 1
        ledger = out / "AUTO_RESUMES.json"
        resumes = json.loads(ledger.read_text()) if ledger.exists() else []
        now = datetime.now(UTC)
        assert sum(r["utc_date"] == now.date().isoformat() for r in resumes) < 3
        resumes.append(
            {
                "utc_date": now.date().isoformat(),
                "timestamp": now.isoformat(),
                "reason": "CLI session limit, zero tokens and cost",
                "task": "sqlglot#7492",
            }
        )
        ledger.write_text(json.dumps(resumes, indent=2) + "\n")
    else:
        assert not scratch.exists(), "Calibration scratch exists; inspect, do not auto-resume"
    manifest = json.loads((out / "run-environment.json").read_text())
    env = dict(os.environ)
    env["DISABLE_AUTOUPDATER"] = "1"
    cli_bin = work / "claude-2.1.310/node_modules/.bin"
    node_bin = work / "runtime-node24/node_modules/.bin"
    env["PATH"] = os.pathsep.join([str(cli_bin), str(node_bin), str(work / "env-sqlglot/bin"), env["PATH"]])
    for binary, expected in (("claude", "2.1.310"), ("node", "v24.15.0"), ("npm", "11.12.1")):
        version = subprocess.run([binary, "--version"], env=env, capture_output=True, text=True, check=True).stdout.strip()
        assert version.split()[0] == expected, (binary, version)
    py = work / "env-calibration/bin/python"
    args = [
        str(py),
        str(root / "eval/pr_replay.py"),
        "sqlglot",
        "--strategy",
        "baseline",
        "--split",
        "eval",
        "--first",
        "1",
        "--executor",
        "claude@claude-haiku-5-5",
        "--roles",
        "claude",
        "--limit-usd",
        "2",
        "--total-cap",
        "30",
        "--budget-glob",
        "*-r2-*",
        "--session-cap-usd",
        "1.5",
        "--work",
        str(work),
        "--out",
        str(out),
        "--experiment",
        "r2-calibration",
        "--label",
        "calibration-A1",
        "--replicate",
        "calibration",
        "--seed-label",
        "101",
        "--arm",
        "A",
        "--product-commit",
        manifest["product_commit"],
    ]
    if options.resume_after_limit:
        args.append("--resume")
    print("All 60 oracle checks passed; starting the single capped calibration.", flush=True)
    os.chdir(root)
    os.execve(py, args, env)


if __name__ == "__main__":
    main()
