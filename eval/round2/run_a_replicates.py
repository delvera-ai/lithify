"""Run only A2..A5 sequentially with owner tripwires and capped CLI-limit resumes."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evalkit import redact, require_redacted, spent

ROOT = Path(__file__).resolve().parents[2]


def summarize(out: Path, label: str) -> dict:
    path = out / f"results-{label}.csv"
    rows = list(csv.DictReader(path.open())) if path.exists() else []
    costs = sum(float(r["cost_usd"]) for r in rows)
    interruption_dir = out / "interruptions" / label
    if interruption_dir.exists():
        costs += spent(interruption_dir)
    return {
        "label": label,
        "tasks": len(rows),
        "passes": sum(r["holdout_pass"] == "True" for r in rows),
        "timeouts": sum(r.get("outcome") == "timeout" for r in rows),
        "cost_usd": round(costs, 4),
        "mean_cost_usd": costs / len(rows) if rows else None,
        "median_wall_s": statistics.median(float(r["wall_s"]) for r in rows) if rows else None,
        **{
            f"median_{key}": statistics.median([float(r[key]) for r in rows if r.get(key) not in (None, "")])
            if any(r.get(key) not in (None, "") for r in rows)
            else None
            for key in ("active_s", "api_s", "idle_s")
        },
    }


def resume_allowed(resumes: list[dict], now: datetime) -> bool:
    return sum(r["utc_date"] == now.date().isoformat() for r in resumes) < 3


def reset_delay(text: str, now: datetime) -> float:
    match = re.search(r"resets\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)\s*\(([^)]+)\)", text, re.I)
    if not match:
        raise RuntimeError("CLI limit reset time missing; refusing to guess a paid retry")
    hour = int(match[1]) % 12 + (12 if match[3].lower() == "pm" else 0)
    local = now.astimezone(ZoneInfo(match[4]))
    reset = local.replace(hour=hour, minute=int(match[2] or 0), second=0, microsecond=0)
    if reset < local - timedelta(hours=12):
        reset += timedelta(days=1)
    return max(60.0, (reset - local).total_seconds() + 60)


def update_ledger(summary: dict, status: str) -> None:
    total = sum(spent(p) for p in (ROOT / "eval/results").glob("*-r2-*") if p.is_dir())
    path = ROOT / "eval/LEDGER.md"
    lines = path.read_text().splitlines()
    marker = f"| 0 A replicate | A / {summary['label']} |"
    lines = [line for line in lines if marker not in line]
    lines.append(
        f"| {datetime.now(UTC).date()} | 0 A replicate | A / {summary['label']} | "
        f"{summary['tasks']}/60 | {summary['cost_usd']:.4f} | {total:.4f} | {status} |"
    )
    path.write_text("\n".join(lines) + "\n")


def post_summary(out: Path, states: list[dict], final_status: str) -> None:
    text = "Phase-0 A replicate summary: " + final_status + ".\n\n"
    for state in states:
        text += (
            f"{state['label']}: {state['tasks']}/60 tasks, {state['passes']} passes, "
            f"{state['timeouts']} timeouts, ${state['cost_usd']:.4f}, "
            f"mean/task {state['mean_cost_usd']}, median wall {state['median_wall_s']}.\n"
        )
    if len(states) < 4 or any(s["tasks"] != 60 for s in states):
        text += "\nPartial data: no noise floor is estimated.\n"
    text += "\nExplicit timeout 900 / concurrency 4; A arms sequential. Tripwires: $0.068 mean/task, 620s median wall. "
    text += "B has not started. Full report and raw redacted evidence: " + str(out.relative_to(ROOT))
    if (out / "RECOVERY.json").exists():
        text += "\nCost totals include the separately recorded $0.10 unresolved-request budget reservation, not observed spend.\n"
    report = out / "A_SUMMARY.md"
    report.write_text(text + "\n")
    require_redacted(out)
    subprocess.run(["gh", "issue", "comment", "29", "--body-file", str(report)], cwd=ROOT, check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--python", type=Path, required=True)
    ap.add_argument("--product-commit", required=True)
    ap.add_argument("--resume-a2", action="store_true", help="explicit owner-reviewed A2 recovery only")
    a = ap.parse_args()
    a.out = a.out.resolve()
    a.work = a.work.resolve()
    a.out.mkdir(parents=True, exist_ok=True)
    condition = json.loads((ROOT / "eval/results/2026-10-27-r2-suite-timing/timings.json").read_text())
    assert len(condition) == 2 and all(r["returncode"] == 0 and r["wall_s"] <= 160 for r in condition)
    manifest = json.loads((ROOT / "eval/round2/INPUT_MANIFEST.json").read_text())
    import hashlib

    assert hashlib.sha256((ROOT / "eval/prs/sqlglot/prs.json").read_bytes()).hexdigest() == manifest["prs_sha256"]
    for item in manifest["tasks"]:
        path = ROOT / f"eval/prs/sqlglot/tasks/{item['number']}.md"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["task_sha256"]
    env = {k: os.environ[k] for k in ("HOME", "USER", "TMPDIR") if k in os.environ}
    env["DISABLE_AUTOUPDATER"] = "1"
    env["PATH"] = os.pathsep.join(
        [
            str(a.work / "claude-2.1.310/node_modules/.bin"),
            str(a.work / "env-sqlglot/bin"),
            str(a.work / "runtime-node24/node_modules/.bin"),
            "/opt/homebrew/bin",
            "/usr/local/bin",
            "/usr/bin",
            "/bin",
        ]
    )
    version = subprocess.run(["claude", "--version"], env=env, capture_output=True, text=True, check=True).stdout
    assert version.startswith("2.1.310 ")
    states = []
    for replicate in range(2, 6):
        label = f"r1-A-rep{replicate}"
        run_dir = a.work / f"replay-r2-noise-verified-{label}"
        recover = a.resume_a2 and replicate == 2
        if recover:
            recovery = json.loads((a.out / "RECOVERY.json").read_text())
            checkpoint = run_dir / "progress.json"
            assert hashlib.sha256(checkpoint.read_bytes()).hexdigest() == recovery["adjusted_progress_sha256"]
            progress = json.loads(checkpoint.read_text())
            rows = list(csv.DictReader((a.out / f"results-{label}.csv").open()))
            assert progress["next_pos"] == recovery["resume_position"] == 22
            assert len(rows) == len(progress["audit"]) == 21
            assert [int(row["position"]) for row in rows] == list(range(1, 22))
            assert abs(progress["run_cost"] - recovery["adjusted_run_cost_usd"]) < 1e-9
            assert progress["run_cost"] < 3 and progress["run_cost"] / len(rows) <= 0.068
            assert statistics.median(float(row["wall_s"]) for row in rows) <= 620
        elif run_dir.exists():
            raise RuntimeError(f"existing run {label}: inspect progress; never restart silently")
        total = sum(spent(p) for p in (ROOT / "eval/results").glob("*-r2-*") if p.is_dir())
        if 30 - total < 3.5:
            post_summary(a.out, states, "budget headroom insufficient; no automatic budget resume")
            return 80
        command = [
            str(a.python),
            str(ROOT / "eval/pr_replay.py"),
            "sqlglot",
            "--strategy",
            "baseline",
            "--split",
            "eval",
            "--first",
            "60",
            "--executor",
            "claude@claude-haiku-5-5",
            "--roles",
            "claude",
            "--timeout",
            "900",
            "--concurrency",
            "4",
            "--limit-usd",
            "3",
            "--total-cap",
            "30",
            "--budget-glob",
            "*-r2-*",
            "--max-mean-cost",
            "0.068",
            "--max-median-wall",
            "620",
            "--work",
            str(a.work),
            "--out",
            str(a.out),
            "--experiment",
            "r2-noise-verified",
            "--label",
            label,
            "--replicate",
            label,
            "--seed-label",
            str(replicate),
            "--arm",
            "A",
            "--product-commit",
            a.product_commit,
        ]
        if recover:
            command.append("--resume")
        resumes_path = a.out / f"{label}-AUTO_RESUMES.json"
        resumes = json.loads(resumes_path.read_text()) if resumes_path.exists() else []
        log_path = a.out / f"{label}.log"
        while True:
            update_ledger(summarize(a.out, label), "running; explicit $3/$30 caps and owner tripwires")
            with log_path.open("a") as log:
                child = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                assert child.stdout is not None
                for line in child.stdout:
                    line = redact(line, {str(a.work): "<work>"})
                    log.write(line)
                    log.flush()
                    print(line, end="", flush=True)
                    if "run total" in line:
                        update_ledger(summarize(a.out, label), "running; explicit $3/$30 caps and owner tripwires")
                code = child.wait()
            with (a.out / "CHILD_EXITS.jsonl").open("a") as exits:
                exits.write(json.dumps({"label": label, "exit_code": code, "timestamp": datetime.now(UTC).isoformat()}) + "\n")
            summary = summarize(a.out, label)
            if code != 75:
                break
            now = datetime.now(UTC)
            if not resume_allowed(resumes, now):
                break
            evidence = a.out / "interruptions" / label
            latest_notice = max(evidence.rglob("lithify.log"), key=lambda p: p.stat().st_mtime)
            notices = latest_notice.read_text()
            delay = reset_delay(notices, now)
            resumes.append(
                {
                    "utc_date": now.date().isoformat(),
                    "timestamp": now.isoformat(),
                    "delay_s": delay,
                    "reason": "CLI session limit",
                    "label": label,
                }
            )
            (a.out / f"{label}-AUTO_RESUMES.json").write_text(json.dumps(resumes, indent=2) + "\n")
            with (a.out / "DEVIATIONS.md").open("a") as deviations:
                deviations.write(
                    f"{label}: auto-resume {len(resumes)} at {now.isoformat()} after CLI limit; wait {delay:.0f}s.\n"
                )
            while delay > 0:
                print(f"{label}: waiting for CLI reset ({delay:.0f}s remaining)", flush=True)
                step = min(60, delay)
                time.sleep(step)
                delay -= step
            if "--resume" not in command:
                command.append("--resume")
        states.append(summary)
        status = "completed" if code == 0 and summary["tasks"] == 60 else f"stopped exit {code}; owner review"
        update_ledger(summary, status)
        (a.out / "A_PROGRESS.json").write_text(json.dumps(states, indent=2) + "\n")
        if code or summary["tasks"] != 60:
            post_summary(a.out, states, status)
            return code or 81
        # Identical outcomes alone are not determinism: compare actual executor output/patch.
        if replicate == 2:
            original = ROOT / "eval/results/2026-10-26-horizon/raw/sqlglot-baseline-claude_claude-haiku-5-5"
            same = True
            for task in sorted((a.out / "raw" / label).glob("[0-9]*")):
                previous = original / task.name / "run/rollouts/base-1"
                current = task / "run/rollouts/base-1"
                for name in ("trajectory.md", "deliverable.patch"):
                    before = (previous / name).read_text()
                    after = (current / name).read_text()
                    if name == "trajectory.md":
                        before = before.split("final message:\n", 1)[1].split("\n## events", 1)[0]
                        after = after.split("final message:\n", 1)[1].split("\n## events", 1)[0]
                    same = same and before == after
            if same:
                post_summary(a.out, states, "deterministic raw output; stop per reanalysis plan")
                return 82
    post_summary(a.out, states, "all four A replicates complete; assess B against remaining $30 cap")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
