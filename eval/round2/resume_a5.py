"""Explicit owner-requested A5 recovery only; never starts a B run."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eval.round2.run_a_replicates import reset_delay, resume_allowed, summarize, update_ledger
from evalkit import redact, require_redacted, spent

ROOT = Path(__file__).resolve().parents[2]


def save(path: Path, value: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(redact(json.dumps(value, indent=2)) + "\n")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    work, out = args.work.resolve(), args.out.resolve()
    evidence = out / "A5_RECOVERY"
    status_file = evidence / "SUPERVISOR.json"
    label = "r1-A-rep5"
    state = {"started_at": datetime.now(UTC).isoformat(), "supervisor_pid": os.getpid(), "status": "preparing"}
    with (work / "A5_RECOVERY.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if status_file.exists():
            raise RuntimeError("A5 recovery already has a supervisor record; inspect before any restart")

        def persist() -> None:
            save(status_file, state)
            save(out / "SUPERVISOR.json", state)

        try:
            recovery = json.loads((evidence / "RECOVERY.json").read_text())
            run = work / f"replay-r2-noise-verified-{label}"
            assert hashlib.sha256((run / "progress.json").read_bytes()).hexdigest() == recovery["adjusted_checkpoint_sha256"]
            audit = evidence / "RECONCILIATION.json"
            assert hashlib.sha256(audit.read_bytes()).hexdigest() == recovery["reconciliation_sha256"]
            assert json.loads((run / "progress.json").read_text())["next_pos"] == 36
            assert hashlib.sha256((out / f"results-{label}.csv").read_bytes()).hexdigest() == recovery["csv_prefix_sha256"]
            assert (
                hashlib.sha256((run / "carried/.lithify/state.json").read_bytes()).hexdigest() == recovery["carried_state_sha256"]
            )
            import lithify

            source = json.loads((out / "RUN_ENVIRONMENT.json").read_text())
            package = Path(lithify.__file__).parent
            assert sys.version.startswith("3.14.4")
            assert all(
                hashlib.sha256((package / name).read_bytes()).hexdigest() == sha for name, sha in source["source_hashes"].items()
            )
            manifest = json.loads((ROOT / "eval/round2/INPUT_MANIFEST.json").read_text())
            assert hashlib.sha256((ROOT / "eval/prs/sqlglot/prs.json").read_bytes()).hexdigest() == manifest["prs_sha256"]
            for task in manifest["tasks"]:
                assert (
                    hashlib.sha256((ROOT / f"eval/prs/sqlglot/tasks/{task['number']}.md").read_bytes()).hexdigest()
                    == task["task_sha256"]
                )
            summary = summarize(out, label)
            assert summary["tasks"] == 35 and summary["mean_cost_usd"] <= 0.068 and summary["median_wall_s"] <= 620
            assert summary["cost_usd"] < 3
            assert sum(spent(p) for p in (ROOT / "eval/results").glob("*-r2-*") if p.is_dir()) < 30
            env = {k: os.environ[k] for k in ("HOME", "USER", "TMPDIR") if k in os.environ}
            env["DISABLE_AUTOUPDATER"] = "1"
            env["PATH"] = os.pathsep.join(
                [
                    str(work / "claude-2.1.310/node_modules/.bin"),
                    str(work / "env-sqlglot/bin"),
                    str(work / "runtime-node24/node_modules/.bin"),
                    "/opt/homebrew/bin",
                    "/usr/local/bin",
                    "/usr/bin",
                    "/bin",
                ]
            )
            assert subprocess.run(["claude", "--version"], env=env, capture_output=True, text=True, check=True).stdout.startswith(
                "2.1.310 "
            )
            subprocess.Popen(
                ["/usr/bin/caffeinate", "-i", "-w", str(os.getpid())], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            command = [
                sys.executable,
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
                str(work),
                "--out",
                str(out),
                "--experiment",
                "r2-noise-verified",
                "--label",
                label,
                "--replicate",
                label,
                "--seed-label",
                "5",
                "--arm",
                "A",
                "--product-commit",
                source["product_commit"],
                "--reconciliation",
                str(audit),
                "--resume",
            ]
            resumes_path = out / f"{label}-AUTO_RESUMES.json"
            resumes = json.loads(resumes_path.read_text()) if resumes_path.exists() else []
            while True:
                with (out / f"{label}.log").open("a") as log:
                    child = subprocess.Popen(
                        command,
                        cwd=ROOT,
                        env=env,
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        start_new_session=True,
                    )
                    state.update(status="running", child_pid=child.pid)
                    persist()
                    update_ledger(summarize(out, label), "running; task35 usage reconciled; owner recovery")
                    assert child.stdout is not None
                    for line in child.stdout:
                        log.write(redact(line, {str(work): "<work>"}))
                        log.flush()
                        if "run total" in line:
                            update_ledger(summarize(out, label), "running; task35 timeout billing reconciled; owner recovery")
                    code = child.wait()
                with (out / "CHILD_EXITS.jsonl").open("a") as log:
                    log.write(
                        json.dumps(
                            {
                                "label": label,
                                "exit_code": code,
                                "owner_recovery": True,
                                "timestamp": datetime.now(UTC).isoformat(),
                            }
                        )
                        + "\n"
                    )
                if code != 75:
                    break
                now = datetime.now(UTC)
                if not resume_allowed(resumes, now):
                    break
                notice = max((out / "interruptions" / label).rglob("lithify.log"), key=lambda p: p.stat().st_mtime).read_text()
                delay = reset_delay(notice, now)
                resumes.append(
                    {
                        "utc_date": now.date().isoformat(),
                        "timestamp": now.isoformat(),
                        "delay_s": delay,
                        "reason": "CLI session limit during owner-requested A5 recovery",
                    }
                )
                resumes_path.write_text(json.dumps(resumes, indent=2) + "\n")
                with (out / "DEVIATIONS.md").open("a") as log:
                    log.write(f"A5 CLI-limit resume scheduled at {now.isoformat()}, wait {delay:.0f}s.\n")
                state["status"] = "running"
                state["waiting_for_cli_reset"] = True
                persist()
                while delay > 0:
                    step = min(60, delay)
                    time.sleep(step)
                    delay -= step
                state.pop("waiting_for_cli_reset", None)
            summary = summarize(out, label)
            state.update(status="completed" if code == 0 and summary["tasks"] == 60 else "stopped; owner review", exit_code=code)
            update_ledger(summary, state["status"] + "; task35 timeout retained; billing reconciled")
            states = [summarize(out, f"r1-A-rep{n}") for n in range(2, 6)]
            (out / "A_PROGRESS.json").write_text(json.dumps(states, indent=2) + "\n")
            report = "A5 owner-requested recovery: " + state["status"] + ".\n\n" + json.dumps(states, indent=2) + "\n"
            report += (
                "\nTask35 remains a timeout failure. Its 25 matched requests reconcile to cumulative $0.02313272; "
                "no repeated task or billing. B remains stopped. Phase-0 analysis/report still required before Phase1.\n"
            )
            (evidence / "SUMMARY.md").write_text(report)
            (out / "A_SUMMARY.md").write_text(report)
            require_redacted(out)
            subprocess.run(["gh", "issue", "comment", "29", "--body-file", str(evidence / "SUMMARY.md")], cwd=ROOT, check=True)
            return code
        except BaseException:
            state.update(status="stopped; owner review", error=traceback.format_exc(), exit_code=1)
            raise
        finally:
            state["finished_at"] = datetime.now(UTC).isoformat()
            persist()


if __name__ == "__main__":
    raise SystemExit(main())
