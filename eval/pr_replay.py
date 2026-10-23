"""Phase 3C: replay merged PRs as tasks under one strategy (docs/benchmarking.md, Level 2).

    <tools-python> eval/pr_replay.py humanize --strategy adaptive --split eval --first 10 \
        --work <scratch>/pr-work --out eval/results/<date>-pr-replay-pilot --limit-usd 25

Run it with a Python that has lithify installed non-editably in a scratch venv, so no path in
the agents' environment leads back to this repository (eval/prs holds the task texts and the
runner; holdouts live only in the scratch work directory).

For each PR, in merge order: the clone is reset to the PR's base and the strategy's own
`.lithify/` (harness, state, library) is restored on top, committed as the eval setup; the
redacted task text (eval/prs/<repo>/tasks/<n>.md) runs through `lithify run`; then the PR's
own test files are copied in, run against the applied patch, and removed (post-hoc holdout:
no strategy ever sees it). Gates: the repository's existing test suite only.

Strategies: baseline = `--k 0 --no-escalate`; static = `--k 1` with skip_when_base_passes =
false; adaptive = the schedule decides (max_k). Adoption: `--adopt all` (default), i.e.
auto_adopt = false and every proposal is adopted after the task (see #13).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from evalkit import copy_redacted, git, lithify, lithify_commit, redact, run_task, spent, write_rows
from repos import REPOS, run_holdout, setup_env, write_version_stub

from lithify.config import load_config, render_config

EVAL = Path(__file__).resolve().parent
RESULTS = EVAL / "results"
TOTAL_CAP_USD = 150.0
CARRIED = (".lithify",)  # the strategy's state that persists across tasks


def configure(clone: Path, a: argparse.Namespace, test_cmd: str) -> None:
    cfg = load_config(clone)
    cfg.executor = a.executor
    cfg.test_cmd = test_cmd
    cfg.lint_cmd = cfg.typecheck_cmd = cfg.holdout_cmd = ""
    cfg.max_k = a.max_k
    cfg.auto_adopt = a.adopt == "auto"
    cfg.skip_when_base_passes = a.strategy != "static" and not a.no_skip
    cfg.timeout_s = a.timeout
    cfg.concurrency = a.concurrency
    role = a.roles or a.executor.partition("@")[0]
    cfg.roles = dict.fromkeys(("propose_inv", "propose_dom", "compose", "select", "reflect", "compact"), role)
    (clone / ".lithify" / "config.toml").write_text(render_config(cfg), encoding="utf-8")


def reset_to(repo_name: str, clone: Path, base: str, keep: Path | None) -> None:
    """Check out `base`, restore the carried lithify state, render it and commit the setup."""
    if keep is not None:
        shutil.rmtree(keep, ignore_errors=True)
        for name in CARRIED:
            if (clone / name).exists():
                shutil.copytree(clone / name, keep / name, ignore=shutil.ignore_patterns("runs"))
    git(clone, "checkout", "-q", "-f", "-B", "eval", base)
    git(clone, "clean", "-qfdx")
    if keep is not None:
        for name in CARRIED:
            if (keep / name).exists():
                shutil.copytree(keep / name, clone / name, dirs_exist_ok=True)
    vf = write_version_stub(repo_name, clone)
    gi = clone / ".gitignore"
    cur = gi.read_text(encoding="utf-8") if gi.exists() else ""
    if ".lithify/runs/" not in cur:
        gi.write_text(cur.rstrip() + "\n.lithify/runs/\n", encoding="utf-8")
    if (clone / ".lithify").exists():
        lithify(clone, "sync")
    git(clone, "add", "-A")
    if vf:
        git(clone, "add", "-f", vf)
    git(clone, "commit", "-q", "--allow-empty", "-m", f"eval setup at {base[:12]}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo", choices=sorted(REPOS))
    ap.add_argument("--strategy", choices=["baseline", "static", "adaptive"], required=True)
    ap.add_argument("--split", choices=["dev", "eval"], required=True)
    ap.add_argument("--first", type=int, help="only the first N PRs of the split, in merge order")
    ap.add_argument("--only", help="comma-separated PR numbers (dev debugging)")
    ap.add_argument("--executor", default="claude@claude-haiku-5-5")
    ap.add_argument("--roles")
    ap.add_argument("--max-k", type=int, default=2)
    ap.add_argument("--adopt", choices=["all", "auto", "none"], default="all")
    ap.add_argument("--no-skip", action="store_true", help="ablation: skip_when_base_passes = false for adaptive")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--limit-usd", type=float, required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--experiment", default="pr-replay")
    ap.add_argument("--label", default="")
    a = ap.parse_args(argv)

    spec = REPOS[a.repo]
    work = Path(a.work).resolve()
    out = Path(a.out).resolve()
    prs = [p for p in json.loads((EVAL / "prs" / a.repo / "prs.json").read_text())["prs"] if p["split"] == a.split]
    if a.only:
        want = {int(x) for x in a.only.split(",")}
        prs = [p for p in prs if p["number"] in want]
    if a.first:
        prs = prs[: a.first]
    tasks_dir = EVAL / "prs" / a.repo / "tasks"
    missing = [p["number"] for p in prs if not (tasks_dir / f"{p['number']}.md").exists()]
    if missing:
        print(f"missing task texts: {missing}", file=sys.stderr)
        return 1

    label = a.label or f"{a.repo}-{a.strategy}-{a.executor.replace('@', '_')}"
    ev_root = out / "raw" / label
    ev_root.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix=f"replay-{a.strategy}-", dir=work))
    clone = run_dir / "repo"
    git(work, "clone", "-q", str(work / f"{a.repo}.git"), str(clone))
    py = setup_env(a.repo, clone, work)
    test_cmd = spec["test_cmd"].format(py=py)
    redactions = {str(run_dir): "<run>", str(work): "<work>", str(EVAL): "<eval>"}

    commit = lithify_commit()
    keep = run_dir / "carried"
    run_cost = 0.0
    audit: list[dict] = []
    for pos, pr in enumerate(prs, 1):
        total = spent(RESULTS)
        if run_cost >= a.limit_usd or total >= TOTAL_CAP_USD:
            print(f"budget stop before #{pr['number']}: run ${run_cost:.2f}/{a.limit_usd:.2f}; all results ${total:.2f}")
            break
        reset_to(a.repo, clone, pr["base"], keep if pos > 1 else None)
        if pos == 1:
            r = lithify(clone, "init", "--executor", a.executor, "--test-cmd", test_cmd)
            if r.returncode != 0:
                print(r.stderr, file=sys.stderr)
                return 1
            configure(clone, a, test_cmd)
            git(clone, "add", "-A")
            git(clone, "commit", "-q", "-m", "lithify init")
        ev = ev_root / f"{pos:02d}-pr{pr['number']}"
        ev.mkdir(parents=True, exist_ok=True)
        task_file = ev / "task.md"
        shutil.copy2(tasks_dir / f"{pr['number']}.md", task_file)
        hdir = work / "holdouts" / a.repo / str(pr["number"])

        def holdout(repo: Path, log: Path, hdir: Path = hdir) -> int:
            return run_holdout(a.repo, repo, hdir, py, log)

        head_before = git(clone, "rev-parse", "HEAD").strip()
        branches_before = git(clone, "branch", "--list").strip()
        print(f"[{label}] {pos}/{len(prs)} #{pr['number']} {pr['title'][:60]} …", flush=True)
        t0 = time.time()
        m = run_task(clone, task_file, a.strategy, holdout, a.timeout * 6, ev, redactions)
        (ev / "applied.diff").write_text(redact(git(clone, "diff", "HEAD"), redactions), encoding="utf-8")
        m["adopted"] = ""
        if a.adopt == "all" and m["proposed"]:
            r = lithify(clone, "adopt", m["task_id"])
            (ev / "adopt.txt").write_text(redact(r.stdout + r.stderr, redactions), encoding="utf-8")
            m["adopted"] = m["proposed"] if r.stdout.startswith("adopted") else ""
        audit.append(
            {
                "pr": pr["number"],
                "head_unchanged": git(clone, "rev-parse", "HEAD").strip() == head_before,
                "branches_unchanged": git(clone, "branch", "--list").strip() == branches_before,
                "worktrees": git(clone, "worktree", "list").strip().count("\n") + 1,
                "test_edits_flagged": sorted(
                    p.parent.name for p in (ev / "run").rglob("gates.md") if "edited pre-existing tests" in p.read_text()
                ),
            }
        )
        row = {
            "experiment": a.experiment,
            "strategy": a.strategy + ("-noskip" if a.no_skip else ""),
            "adopt_policy": a.adopt,
            "executor": a.executor,
            "task": f"{a.repo}#{pr['number']}",
            "order_seed": 0,
            "position": pos,
            "lithify_commit": commit,
            **m,
        }
        write_rows(out / f"results-{label}.csv", [row])
        run_cost += float(m["cost_usd"])
        print(
            f"   k={m['k']} delivered={m['delivered']} first_pass={m['first_pass']} holdout={m['holdout_pass']} "
            f"exec={m['executions']} roles={m['role_sessions']} ${m['cost_usd']:.2f} ({time.time() - t0:.0f}s) "
            f"adopted=[{m['adopted']}] run total ${run_cost:.2f}",
            flush=True,
        )

    summary = {
        "label": label,
        "lithify_commit": commit,
        "run_cost_usd": round(run_cost, 4),
        "invariants": audit,
    }
    (ev_root / "audit.json").write_text(redact(json.dumps(summary, indent=2), redactions), encoding="utf-8")
    copy_redacted(clone / ".lithify" / "harness", ev_root / "final-harness", redactions)
    if (clone / ".lithify" / "library").is_dir():
        copy_redacted(clone / ".lithify" / "library", ev_root / "library", redactions)
    print(f"done: {label} ${run_cost:.2f}; scratch {run_dir}")
    return 0


if __name__ == "__main__":
    os.environ.pop("VIRTUAL_ENV", None)
    sys.exit(main())
