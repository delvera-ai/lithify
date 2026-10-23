"""Phase 3B: run the validators fixture task sequence under one strategy, with real CLIs.

    python eval/run_sequence.py --strategy adaptive --executor claude@claude-haiku-5-5 \
        --out eval/results/2026-10-23-validators-pilot --limit-usd 10

The fixture repo is copied to a scratch directory, `git init`ed and `lithify init`ed. Each task
then runs through `lithify run` in order; the runner commits after each task so the next one
builds on it (the pipeline itself never commits). Holdout scripts stay under eval/fixtures/
and are never copied into the scratch repository.

Adoption policy (--adopt): `all` (default) keeps the product default `auto_adopt = false` and
runs `lithify adopt <task-id>` after every task, i.e. a maintainer who accepts every proposal
unreviewed; `auto` sets `auto_adopt = true` (only `helped` components promoted, see #13);
`none` never adopts. Other eval-only choices: every editor role runs on the executor's CLI at
its default model; the holdout is a gate unless --no-holdout-gate. Holdout pass of the applied
patch is always measured afterwards on the working tree.
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from evalkit import copy_redacted, git, lithify, lithify_commit, redact, run_task, sh, spent, write_rows

from lithify.config import load_config, render_config

EVAL = Path(__file__).resolve().parent
FIXTURE = EVAL / "fixtures" / "validators"
RESULTS = EVAL / "results"
TEST_CMD = f"{sys.executable} -m pytest -q"
TOTAL_CAP_USD = 150.0


def home_writes(marker: Path) -> list[str]:
    home = Path.home()
    cmd = (
        f"find {home} -xdev \\( -path {home}/Library -o -path {home}/.Trash -o -name node_modules -o -name .git \\) "
        f"-prune -o -type f -newer {marker} -print"
    )
    out = sh(cmd, Path("/"), check=False, timeout=900).stdout
    return sorted(ln.replace(str(home), "~") for ln in out.splitlines() if ln.strip())


def classify_home_writes(paths: list[str]) -> dict[str, int]:
    """Summarise ~-relative paths without naming unrelated projects (the raw list stays local)."""
    buckets = {
        "~/.cache/lithify (probe worktrees, expected)": "~/.cache/lithify",
        "~/.claude (agent CLI session state, expected)": "~/.claude",
        "~/.codex (agent CLI session state, expected)": "~/.codex",
        "this repository's eval/ (runner output, expected)": "~/Coding/delvera/foundational/lithify/eval",
    }
    out = dict.fromkeys(buckets, 0)
    out["other (unattributed; reviewed by hand)"] = 0
    for path in paths:
        key = next((k for k, pre in buckets.items() if path.startswith(pre)), "other (unattributed; reviewed by hand)")
        out[key] += 1
    return out


def configure(repo: Path, a: argparse.Namespace, holdout_cmd: str) -> None:
    cfg = load_config(repo)
    cfg.executor = a.executor
    cfg.test_cmd = TEST_CMD
    cfg.holdout_cmd = holdout_cmd if a.holdout_gate else ""
    cfg.max_k = a.max_k
    cfg.auto_adopt = a.adopt == "auto"
    cfg.skip_when_base_passes = a.strategy != "static"
    cfg.timeout_s = a.timeout
    cfg.concurrency = a.concurrency
    role = a.roles or a.executor.partition("@")[0]
    cfg.roles = dict.fromkeys(("propose_inv", "propose_dom", "compose", "select", "reflect", "compact"), role)
    (repo / ".lithify" / "config.toml").write_text(render_config(cfg), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strategy", choices=["baseline", "static", "adaptive"], required=True)
    ap.add_argument("--executor", default="claude@claude-haiku-5-5")
    ap.add_argument("--roles", help="CLI (or cli@model) for every editor role; default: the executor's CLI")
    ap.add_argument("--max-k", type=int, default=2)
    ap.add_argument("--tasks", default="all", help="comma-separated task ids, or 'all'")
    ap.add_argument("--order-seed", type=int, default=0, help="0 = file order")
    ap.add_argument("--adopt", choices=["all", "auto", "none"], default="all")
    ap.add_argument("--no-holdout-gate", dest="holdout_gate", action="store_false")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--limit-usd", type=float, required=True, help="stop before a task once this run has spent this much")
    ap.add_argument("--out", required=True)
    ap.add_argument("--experiment", default="validators")
    ap.add_argument("--keep", action="store_true", help="keep the scratch repository")
    ap.add_argument("--home-audit", action="store_true", help="list files modified under ~ during the run (slow)")
    a = ap.parse_args(argv)

    tasks = json.loads((FIXTURE / "tasks.json").read_text())
    if a.tasks != "all":
        want = a.tasks.split(",")
        tasks = [t for t in tasks if t["id"] in want]
    if a.order_seed:
        random.Random(a.order_seed).shuffle(tasks)
    out = Path(a.out).resolve()
    label = f"{a.strategy}-{a.executor.replace('@', '_')}-s{a.order_seed}"
    ev_root = out / "raw" / label
    ev_root.mkdir(parents=True, exist_ok=True)

    scratch = Path(tempfile.mkdtemp(prefix="lithify-eval-"))
    repo = scratch / "repo"
    shutil.copytree(FIXTURE / "repo", repo)
    git(repo, "init", "-q", "-b", "main")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "fixture")
    r = lithify(repo, "init", "--executor", a.executor, "--test-cmd", TEST_CMD)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        return 1
    configure(repo, a, "")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "lithify init")
    redactions = {str(scratch): "<scratch>", str(EVAL): "<eval>", sys.executable: "python"}

    marker = scratch / "marker"
    marker.write_text("")
    time.sleep(1)
    commit = lithify_commit()
    run_cost = 0.0
    audit: list[dict] = []
    for pos, t in enumerate(tasks, 1):
        total = spent(RESULTS)
        if run_cost >= a.limit_usd or total >= TOTAL_CAP_USD:
            print(f"budget stop before {t['id']}: run ${run_cost:.2f} / limit ${a.limit_usd:.2f}; all results ${total:.2f}")
            break
        holdout = f"{sys.executable} {FIXTURE / 'holdout' / (t['id'] + '.py')}"
        configure(repo, a, holdout)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "--allow-empty", "-m", f"eval: configure {t['id']}")
        ev = ev_root / f"{pos:02d}-{t['id']}"
        ev.mkdir(parents=True, exist_ok=True)
        task_file = ev / "task.md"
        task_file.write_text(t["task"] + "\n", encoding="utf-8")
        head_before = git(repo, "rev-parse", "HEAD").strip()
        branches_before = git(repo, "branch", "--list").strip()
        print(f"[{label}] {pos}/{len(tasks)} {t['id']} …", flush=True)
        m = run_task(repo, task_file, a.strategy, holdout, a.timeout * 6, ev, redactions)
        m["adopted"] = ""
        if a.adopt == "all" and m["proposed"]:
            r = lithify(repo, "adopt", m["task_id"])
            (ev / "adopt.txt").write_text(r.stdout + r.stderr, encoding="utf-8")
            m["adopted"] = m["proposed"] if r.stdout.startswith("adopted") else ""
        # Safety invariants: the pipeline never commits, branches, or leaves worktrees behind.
        inv = {
            "task": t["id"],
            "head_unchanged": git(repo, "rev-parse", "HEAD").strip() == head_before,
            "branches_unchanged": git(repo, "branch", "--list").strip() == branches_before,
            "worktrees": git(repo, "worktree", "list").strip().count("\n") + 1,
            "test_edits_flagged": sorted({ln.split(":")[0] for ln in _grep(ev / "run", "edited pre-existing tests")}),
        }
        audit.append(inv)
        row = {
            "experiment": a.experiment,
            "strategy": a.strategy,
            "executor": a.executor,
            "task": t["id"],
            "order_seed": a.order_seed,
            "position": pos,
            "lithify_commit": commit,
            **m,
        }
        write_rows(out / "results.csv", [row])
        run_cost += float(m["cost_usd"])
        print(
            f"   k={m['k']} delivered={m['delivered']} first_pass={m['first_pass']} holdout={m['holdout_pass']} "
            f"exec={m['executions']} roles={m['role_sessions']} ${m['cost_usd']:.2f} ({m['wall_s']}s) "
            f"promoted=[{m['promoted']}] adopted=[{m['adopted']}] run total ${run_cost:.2f}",
            flush=True,
        )
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "--allow-empty", "-m", f"eval: task {pos} {t['id']}")

    summary = {
        "label": label,
        "scratch_kept": a.keep,
        "lithify_commit": commit,
        "run_cost_usd": round(run_cost, 4),
        "invariants": audit,
        "commits_by_others": [
            ln for ln in git(repo, "log", "--format=%an|%s").splitlines() if not ln.startswith("lithify-eval|")
        ],
    }
    if a.home_audit:
        writes = home_writes(marker)
        raw = scratch.parent / f"{scratch.name}-home-writes.txt"
        raw.write_text("\n".join(writes) + "\n", encoding="utf-8")
        summary["home_writes"] = classify_home_writes(writes)
        summary["home_writes_raw"] = "kept locally, not committed (names unrelated projects)"
        print(f"home-write list (local only): {raw}")
    (ev_root / "audit.json").write_text(redact(json.dumps(summary, indent=2), redactions), encoding="utf-8")
    copy_redacted(repo / ".lithify" / "harness", ev_root / "final-harness", redactions)
    if (repo / ".lithify" / "library").is_dir():
        copy_redacted(repo / ".lithify" / "library", ev_root / "library", redactions)
    print(f"done: {label} ${run_cost:.2f}; evidence in {ev_root}")
    if a.keep:
        print(f"scratch repository kept at {repo}")
    else:
        shutil.rmtree(scratch, ignore_errors=True)
    return 0


def _grep(root: Path, needle: str) -> list[str]:
    hits = []
    for p in root.rglob("gates.md") if root.is_dir() else []:
        if needle in p.read_text(encoding="utf-8", errors="ignore"):
            hits.append(f"{p.parent.name}:{needle}")
    return hits


if __name__ == "__main__":
    sys.exit(main())
