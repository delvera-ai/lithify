"""Shared helpers for the live evaluation scripts (run_sequence.py, pr_replay.py).

Every live task goes through the real `lithify run` CLI in a scratch repository. After it
finishes, the holdout is re-run on the repository's working tree (the applied patch), so the
quality metric is the same whether or not the holdout was also used as a gate.
"""

from __future__ import annotations

import contextlib
import csv
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

HOME = str(Path.home())
EVAL_GIT = ["-c", "user.name=lithify-eval", "-c", "user.email=eval@localhost", "-c", "commit.gpgsign=false"]
SECRETISH = re.compile(r"(sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{30,}|AIza[0-9A-Za-z_-]{30,})")

COLUMNS = [
    "experiment",
    "strategy",
    "executor",
    "task_id",
    "task",
    "order_seed",
    "position",
    "k",
    "reason",
    "delivered",
    "applied",
    "first_pass",
    "holdout_pass",
    "selected",
    "executions",
    "role_sessions",
    "tokens_in",
    "tokens_cached",
    "tokens_out",
    "cost_usd",
    "wall_s",
    "always_on_tokens",
    "stability_after",
    "promoted",
    "proposed",
    "adopted",
    "adopt_policy",
    "lithify_commit",
]


def sh(cmd: list[str] | str, cwd: Path, check: bool = True, timeout: int | None = None, env=None) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, shell=isinstance(cmd, str), timeout=timeout, env=env)
    if check and proc.returncode != 0:
        raise RuntimeError(f"{cmd!r} failed in {cwd}: {proc.stderr[-2000:] or proc.stdout[-2000:]}")
    return proc


def git(cwd: Path, *args: str, check: bool = True) -> str:
    return sh(["git", *EVAL_GIT, *args], cwd, check=check).stdout


def lithify(cwd: Path, *args: str, timeout: int | None = None) -> subprocess.CompletedProcess:
    return sh([sys.executable, "-m", "lithify", *args], cwd, check=False, timeout=timeout)


def lithify_commit() -> str:
    here = Path(__file__).resolve().parent.parent
    sha = sh(["git", "rev-parse", "--short", "HEAD"], here, check=False).stdout.strip()
    dirty = sh(["git", "status", "--porcelain", "--", "src"], here, check=False).stdout.strip()
    return sha + ("+dirty" if dirty else "")


def redact(text: str, extra: dict[str, str] | None = None) -> str:
    for src, dst in (extra or {}).items():
        text = text.replace(src, dst)
    text = text.replace(HOME, "~")
    return SECRETISH.sub("<redacted>", text)


def copy_redacted(src: Path, dst: Path, extra: dict[str, str] | None = None) -> None:
    """Copy a run directory, redacting home paths, scratch paths and anything secret-shaped."""
    for p in src.rglob("*"):
        if p.is_symlink() or not p.is_file():
            continue
        out = dst / p.relative_to(src)
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            out.write_text(redact(p.read_text(encoding="utf-8"), extra), encoding="utf-8")
        except UnicodeDecodeError:
            shutil.copy2(p, out)


def run_task(
    repo: Path,
    task_file: Path,
    strategy: str,
    holdout: str | Callable[[Path, Path], int],
    timeout: int,
    evidence: Path,
    extra_redact: dict[str, str],
) -> dict[str, Any]:
    """Run one task through `lithify run` under a strategy; return the metrics for it.

    `holdout` is a shell command, or a callable(repo, log_path) -> exit code, run afterwards on
    the working tree with the applied patch."""
    args = ["run", "--task-file", str(task_file), "--json"]
    if strategy == "baseline":
        args += ["--k", "0", "--no-escalate"]
    elif strategy == "static":
        args += ["--k", "1"]
    t0 = time.time()
    proc = lithify(repo, *args, timeout=timeout)
    wall = round(time.time() - t0, 1)
    try:
        res = json.loads(proc.stdout[proc.stdout.find("{") :])
    except json.JSONDecodeError:
        res = {}
    tid = res.get("task_id") or _latest(repo)
    rdir = repo / ".lithify" / "runs" / tid if tid else None
    outcome = json.loads((rdir / "outcome.json").read_text()) if rdir and (rdir / "outcome.json").exists() else {}
    state = json.loads((repo / ".lithify" / "state.json").read_text())
    rec = state["history"][-1] if state["history"] and tid and state["history"][-1]["task_id"] == tid else {}
    hold_rc: int | None = None
    if callable(holdout):
        hold_rc = holdout(repo, evidence / "holdout_applied.txt")
    elif holdout:
        hold = sh(holdout, repo, check=False, timeout=600)
        hold_rc = hold.returncode
        (evidence / "holdout_applied.txt").write_text(
            f"exit {hold.returncode}\n{hold.stdout[-4000:]}{hold.stderr[-2000:]}", encoding="utf-8"
        )
    if rdir and rdir.exists():
        copy_redacted(rdir, evidence / "run", extra_redact)
    (evidence / "state.json").write_text(redact(json.dumps(state, indent=2), extra_redact), encoding="utf-8")
    (evidence / "lithify.log").write_text(redact(proc.stdout + "\n" + proc.stderr, extra_redact), encoding="utf-8")
    hl = evidence / "holdout_applied.txt"
    if hl.exists():
        hl.write_text(redact(hl.read_text(encoding="utf-8"), extra_redact), encoding="utf-8")
    usage = outcome.get("usage", {})
    proposal = outcome.get("proposal")
    proposed = ""
    if proposal:
        kf = Path(proposal) / "keys.json"
        proposed = " ".join(json.loads(kf.read_text())) if kf.exists() else "?"
    return {
        "task_id": tid or "",
        "k": outcome.get("k", rec.get("k", "")),
        "reason": outcome.get("reason", ""),
        "delivered": bool(res.get("delivered", rec.get("delivered", False))),
        "applied": bool(outcome.get("applied", False)),
        "first_pass": bool(outcome.get("first_pass", rec.get("first_pass", False))),
        "holdout_pass": (hold_rc == 0) if hold_rc is not None else "",
        "selected": outcome.get("selected", ""),
        "executions": int(usage.get("exec", rec.get("executions", 0))),
        "role_sessions": int(usage.get("roles", 0)),
        "tokens_in": int(usage.get("in", 0)),
        "tokens_cached": int(usage.get("cached", 0)),
        "tokens_out": int(usage.get("out", 0)),
        "cost_usd": round(float(usage.get("cost", 0.0)), 4),
        "wall_s": wall,
        "always_on_tokens": rec.get("always_on_tokens", ""),
        "stability_after": rec.get("stability_after", ""),
        "promoted": " ".join(outcome.get("promoted", [])),
        "proposed": proposed,
        "exit_code": proc.returncode,
    }


def _latest(repo: Path) -> str:
    rdir = repo / ".lithify" / "runs"
    runs = sorted(d.name for d in rdir.iterdir() if (d / "outcome.json").exists()) if rdir.is_dir() else []
    return runs[-1] if runs else ""


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        if new:
            w.writeheader()
        for r in rows:
            w.writerow(r)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def spent(results_root: Path) -> float:
    """Total live spend recorded in every results.csv under eval/results/."""
    total = 0.0
    for f in results_root.rglob("results*.csv"):
        with open(f, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                with contextlib.suppress(ValueError):
                    total += float(row.get("cost_usd") or 0)
    return total


def scrub_env() -> dict[str, str]:
    env = dict(os.environ)
    env.pop("LITHIFY_MOCK_NOISE", None)
    return env
