"""Owner-approved two-run B supervisor, gated on all A runs and load timing."""

from __future__ import annotations

import argparse
import csv
import fcntl
import hashlib
import json
import os
import signal
import statistics
import subprocess
import sys
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eval.round2.run_a_replicates import reset_delay, resume_allowed, summarize
from evalkit import redact, require_redacted, spent
from repos import prepare_checkout

ROOT = Path(__file__).resolve().parents[2]


def write_json(path: Path, value: dict | list) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(redact(json.dumps(value, indent=2)) + "\n")
    temporary.replace(path)


def phase_spend() -> float:
    return sum(spent(p) for p in (ROOT / "eval/results").glob("*-r2-*") if p.is_dir())


def update_ledger(states: list[dict], status: str) -> None:
    path = ROOT / "eval/LEDGER.md"
    lines = path.read_text().splitlines()
    for state in states:
        marker = f"| 0 B replicate | B / {state['label']} |"
        lines = [line for line in lines if marker not in line]
        lines.append(
            f"| {datetime.now(UTC).date()} | 0 B replicate | B / {state['label']} | "
            f"{state['tasks']}/60 | {state['cost_usd']:.4f} | {phase_spend():.4f} | {status}; max two runs |"
        )
    path.write_text("\n".join(lines) + "\n")


def budget_fits(total: float) -> bool:
    # Reserve both entire $7 caps plus $2 between-task overshoot headroom.
    return 30 - total >= 16


def timing_passes(rows: list[dict]) -> bool:
    return len(rows) == 16 and all(row["returncode"] == 0 and row["wall_s"] <= 160 for row in rows)


def load_preflight(work: Path, out: Path, env: dict, base: str) -> None:
    py = work / "env-sqlglot/bin/python"
    clones = []
    for i in range(8):
        clone = work / "parallel-b-preflight" / str(i)
        if clone.exists():
            raise RuntimeError("existing preflight checkout; inspect rather than reset it")
        clone.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "-q", str(work / "sqlglot.git"), str(clone)], check=True)
        prepare_checkout("sqlglot", clone, base)
        clones.append(clone)
    rows = []
    for wave in range(2):
        children = []
        for i, clone in enumerate(clones):
            stream = (work / f"B-preflight-{wave}-{i}.log").open("w")
            start = time.monotonic()
            child = subprocess.Popen(
                [str(py), "-m", "pytest", "-q", "-p", "no:cacheprovider", "--color=no"],
                cwd=clone,
                env=env,
                stdout=stream,
                stderr=stream,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
            children.append((i, child, stream, start))
        pending = list(children)
        while pending:
            for item in pending[:]:
                i, child, stream, start = item
                elapsed = time.monotonic() - start
                code = child.poll()
                if code is None and elapsed <= 160:
                    continue
                if code is None:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
                    code = 124
                stream.close()
                row = {
                    "wave": wave,
                    "suite": i,
                    "replicate_concurrency": 2,
                    "suite_concurrency": 8,
                    "base": base,
                    "returncode": code,
                    "wall_s": round(elapsed, 3),
                }
                rows.append(row)
                (out / f"preflight-{wave}-{i}.log").write_text(redact((work / f"B-preflight-{wave}-{i}.log").read_text()))
                write_json(out / "PREFLIGHT.json", rows)
                pending.remove(item)
            time.sleep(0.1)
        if any(row["returncode"] or row["wall_s"] > 160 for row in rows):
            raise RuntimeError("concurrent-load timing failed; no B launch authorized under failed preflight")
    if not timing_passes(rows):
        raise RuntimeError("incomplete timing evidence")


def verify_inputs(work: Path, a_out: Path) -> dict:
    import lithify

    manifest = json.loads((ROOT / "eval/round2/INPUT_MANIFEST.json").read_text())
    for task in manifest["tasks"]:
        assert (
            hashlib.sha256((ROOT / f"eval/prs/sqlglot/tasks/{task['number']}.md").read_bytes()).hexdigest() == task["task_sha256"]
        )
    assert hashlib.sha256((ROOT / "eval/prs/sqlglot/prs.json").read_bytes()).hexdigest() == manifest["prs_sha256"]
    source = json.loads((a_out / "RUN_ENVIRONMENT.json").read_text())
    package = Path(lithify.__file__).parent
    assert sys.version.startswith("3.14.4")
    assert all(hashlib.sha256((package / name).read_bytes()).hexdigest() == sha for name, sha in source["source_hashes"].items())
    old = list(csv.DictReader(next((ROOT / "eval/results/2026-10-26-horizon").glob("results-*baseline*.csv")).open()))
    old_b = list(csv.DictReader(next((ROOT / "eval/results/2026-10-26-horizon").glob("results-*adaptive-claude*.csv")).open()))
    totals = []
    for number in range(2, 6):
        rows = list(csv.DictReader((a_out / f"results-r1-A-rep{number}.csv").open()))
        assert [int(row["position"]) for row in rows] == list(range(1, 61))
        totals.append(sum(float(row["cost_usd"]) for row in rows))
        state = summarize(a_out, f"r1-A-rep{number}")
        assert state["mean_cost_usd"] <= 0.068 and state["median_wall_s"] <= 620
        assert not any(row.get("cost_lower_bound", "").lower() == "true" for row in rows)
    ratio = statistics.mean(totals) / sum(float(row["cost_usd"]) for row in old)
    estimate = max(1, ratio) * sum(float(row["cost_usd"]) for row in old_b)
    assert source["product_commit"] == "89020d7516ca4dd288909281747f053453a8a216"
    return {
        "a_cost_ratio": ratio,
        "estimated_each_b_usd": estimate,
        "reserved_b_caps_usd": 14,
        "overshoot_headroom_usd": 2,
        "phase_used_reserved_usd": phase_spend(),
        "both_fit": budget_fits(phase_spend()),
        "product_commit": source["product_commit"],
    }


def run(args: argparse.Namespace, status: dict) -> int:
    out, work, a_out = args.out.resolve(), args.work.resolve(), args.a_out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    stop = out / "PHASE_STOP.json"
    if (out / "SUPERVISOR.json").exists():
        raise RuntimeError("B supervisor record already exists; inspect, never restart silently")

    def save() -> None:
        write_json(out / "SUPERVISOR.json", status)

    def halt(reason: str) -> None:
        if not stop.exists():
            write_json(stop, {"timestamp": datetime.now(UTC).isoformat(), "reason": reason})
        status.update(status="stopping after current tasks; owner review", reason=reason)
        save()

    status.update(status="waiting for all four A replicates", pid=os.getpid())
    save()
    subprocess.Popen(["/usr/bin/caffeinate", "-i", "-w", str(os.getpid())], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    while True:
        a_state = json.loads((a_out / "SUPERVISOR.json").read_text())
        if a_state["status"] == "completed" and a_state.get("exit_code") == 0:
            break
        if a_state["status"] != "running":
            raise RuntimeError("A supervisor stopped without success; B remains unstarted")
        os.kill(int(a_state["supervisor_pid"]), 0)
        time.sleep(30)
    affordability = verify_inputs(work, a_out)
    write_json(out / "AFFORDABILITY.json", affordability)
    if not affordability["both_fit"]:
        raise RuntimeError("both B runs do not fit with full-cap headroom; ask owner about $35 cap or one B")
    env = {key: os.environ[key] for key in ("HOME", "USER", "TMPDIR") if key in os.environ}
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
    status["status"] = "zero-token eight-suite preflight"
    save()
    base = json.loads((ROOT / "eval/round2/INPUT_MANIFEST.json").read_text())["tasks"][0]["base"]
    load_preflight(work, out, env, base)
    if not budget_fits(phase_spend()):
        raise RuntimeError("budget changed during preflight; no paid launch")
    provenance = json.loads((a_out / "RUN_ENVIRONMENT.json").read_text())
    provenance.update(
        replicate_concurrency=2,
        arm="B",
        max_k=2,
        run_cap_usd=7,
        schedule_change="owner requested at most two concurrent runs on 2026-10-29",
    )
    write_json(out / "RUN_ENVIRONMENT.json", provenance)
    labels = ["r1-B-rep2", "r1-B-rep3"]
    entries = {}
    for seed, label in zip((2, 3), labels, strict=True):
        assert not (work / f"replay-r2-noise-verified-{label}").exists()
        assert not (out / f"results-{label}.csv").exists()
        entries[label] = {"seed": seed, "resumes": [], "ready_at": 0, "done": False}
    children = {}

    def interrupt(signum: int, _frame: object) -> None:
        halt(f"supervisor received signal {signum}; do not start more tasks")

    signal.signal(signal.SIGTERM, interrupt)
    signal.signal(signal.SIGINT, interrupt)
    try:
        while not all(entry["done"] for entry in entries.values()):
            for label, entry in entries.items():
                if label in children or entry["done"]:
                    continue
                if stop.exists():
                    entry["done"] = True
                    continue
                if time.time() < entry["ready_at"]:
                    continue
                command = [
                    sys.executable,
                    str(ROOT / "eval/pr_replay.py"),
                    "sqlglot",
                    "--strategy",
                    "adaptive",
                    "--split",
                    "eval",
                    "--first",
                    "60",
                    "--max-k",
                    "2",
                    "--adopt",
                    "all",
                    "--executor",
                    "claude@claude-haiku-5-5",
                    "--roles",
                    "claude",
                    "--timeout",
                    "900",
                    "--concurrency",
                    "4",
                    "--limit-usd",
                    "7",
                    "--total-cap",
                    "30",
                    "--budget-glob",
                    "*-r2-*",
                    "--max-mean-cost",
                    "0.068",
                    "--max-median-wall",
                    "620",
                    "--phase-stop-file",
                    str(stop),
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
                    str(entry["seed"]),
                    "--arm",
                    "B",
                    "--product-commit",
                    affordability["product_commit"],
                ]
                if entry["resumes"]:
                    command.append("--resume")
                stream = (work / f"{label}.console.log").open("a")
                child = subprocess.Popen(
                    command, cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=stream, stderr=stream, start_new_session=True
                )
                children[label] = (child, stream)
            assert len(children) <= 2
            for label, (child, stream) in list(children.items()):
                (out / f"{label}.log").write_text(redact((work / f"{label}.console.log").read_text()))
                code = child.poll()
                if code is None:
                    continue
                stream.close()
                del children[label]
                entry = entries[label]
                with (out / "CHILD_EXITS.jsonl").open("a") as exits:
                    exits.write(
                        json.dumps({"label": label, "exit_code": code, "timestamp": datetime.now(UTC).isoformat()}) + "\n"
                    )
                if code == 75 and not stop.exists():
                    now = datetime.now(UTC)
                    if not resume_allowed(entry["resumes"], now):
                        halt(f"{label}: CLI-limit daily resume allowance exhausted")
                        entry["done"] = True
                        continue
                    notice = max(
                        (out / "interruptions" / label).rglob("lithify.log"), key=lambda p: p.stat().st_mtime
                    ).read_text()
                    delay = reset_delay(notice, now)
                    entry["resumes"].append({"utc_date": now.date().isoformat(), "timestamp": now.isoformat(), "delay_s": delay})
                    entry["ready_at"] = time.time() + delay
                    write_json(out / f"{label}-AUTO_RESUMES.json", entry["resumes"])
                    with (out / "DEVIATIONS.md").open("a") as deviations:
                        deviations.write(
                            f"{label}: CLI-limit auto-resume {len(entry['resumes'])} scheduled at {now.isoformat()} "
                            f"after {delay:.0f}s.\n"
                        )
                else:
                    entry["done"] = True
                    if code != 0 or summarize(out, label)["tasks"] != 60:
                        halt(f"{label}: stopped exit {code}; owner review")
            states = [summarize(out, label) for label in labels]
            status.update(
                status="running two B replicates" if not stop.exists() else "stopping; owner review",
                active={label: child.pid for label, (child, _) in children.items()},
                runs=states,
            )
            save()
            write_json(out / "B_PROGRESS.json", states)
            update_ledger(states, status["status"])
            time.sleep(5)
    except BaseException:
        halt("B supervisor exception; owner review")
        # Each child observes the shared stop file before its next task.
        raise
    finally:
        for label, (child, stream) in children.items():
            code = child.wait()
            stream.close()
            (out / f"{label}.log").write_text(redact((work / f"{label}.console.log").read_text()))
            with (out / "CHILD_EXITS.jsonl").open("a") as exits:
                exits.write(json.dumps({"label": label, "exit_code": code, "drained_after_stop": True}) + "\n")
        if children:
            update_ledger([summarize(out, label) for label in labels], "stopped after supervisor exception")
    state = "stopped; owner review" if stop.exists() else "B2 and B3 complete; Phase-0 report required before Phase 1"
    status["status"] = state
    update_ledger(status.get("runs", []), state)
    report = "Phase-0 parallel B summary: " + state + ".\n\n" + json.dumps(status.get("runs", []), indent=2) + "\n"
    report += (
        "\nTwo runs maximum; pipeline concurrency 4 each. Budgets $7/run and $30/phase unchanged. "
        "Original mean/median tripwires retained.\n"
    )
    (out / "B_SUMMARY.md").write_text(report)
    require_redacted(out)
    subprocess.run(["gh", "issue", "comment", "29", "--body-file", str(out / "B_SUMMARY.md")], cwd=ROOT, check=True)
    return 78 if stop.exists() else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--a-out", type=Path, required=True)
    args = parser.parse_args()
    status = {"started_at": datetime.now(UTC).isoformat(), "max_concurrent_runs": 2}
    with (args.work / "B_PARALLEL.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (args.out / "SUPERVISOR.json").exists():
            raise RuntimeError("existing B supervisor record; inspect before recovery")
        try:
            code = run(args, status)
            status["exit_code"] = code
            return code
        except BaseException:
            status.update(status="stopped; owner review", error=traceback.format_exc(), exit_code=1)
            report = args.out / "B_STOP.md"
            args.out.mkdir(parents=True, exist_ok=True)
            report.write_text(redact("Parallel B supervisor stopped; owner review.\n\n" + traceback.format_exc()))
            require_redacted(args.out)
            subprocess.run(["gh", "issue", "comment", "29", "--body-file", str(report)], cwd=ROOT, check=False)
            raise
        finally:
            status["finished_at"] = datetime.now(UTC).isoformat()
            args.out.mkdir(parents=True, exist_ok=True)
            write_json(args.out / "SUPERVISOR.json", status)


if __name__ == "__main__":
    raise SystemExit(main())
