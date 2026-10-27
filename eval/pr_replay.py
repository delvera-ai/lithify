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
import csv
import json
import os
import re
import shutil
import statistics
import sys
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
    if a.session_cap_usd is not None:
        cfg.adapter_args["claude"] = ["--dangerously-skip-permissions", "--max-budget-usd", str(a.session_cap_usd)]
    role = a.roles or a.executor.partition("@")[0]
    cfg.roles = dict.fromkeys(("propose_inv", "propose_dom", "compose", "select", "reflect", "compact"), role)
    # render_config emits an empty adapter_args table; preserve explicit run caps here.
    rendered = render_config(cfg)
    rendered += "\n".join(f"{json.dumps(cli)} = {json.dumps(args)}" for cli, args in cfg.adapter_args.items()) + "\n"
    (clone / ".lithify" / "config.toml").write_text(rendered, encoding="utf-8")
    if load_config(clone).adapter_args != cfg.adapter_args:
        raise RuntimeError("adapter argument configuration did not round-trip; refusing uncapped execution")


# Signatures of a subscription or rate limit cutting sessions short: the CLI returns the notice as
# its whole answer, or the session fails with an empty error. Such a task measures nothing.
LIMIT_TEXT = re.compile(r"(session|usage|rate) limit|hit your limit|limit reached|resets \d", re.I)
LIMIT_LOG = re.compile(r"discarded \(\)|\[executor: \]")


def limit_hit(ev: Path) -> str:
    log = ev / "lithify.log"
    if log.exists():
        text = log.read_text(encoding="utf-8", errors="ignore")
        if LIMIT_TEXT.search(text):
            return "agent CLI limit notice in lithify.log"
        if LIMIT_LOG.search(text):
            return "session failed with an empty error (lithify.log)"
    for t in (ev / "run").rglob("trajectory.md") if (ev / "run").is_dir() else []:
        head = t.read_text(encoding="utf-8", errors="ignore")[:4000]
        if LIMIT_TEXT.search(head):
            return f"limit notice in {t.parent.name}/trajectory.md"
    return ""


def tripwire_reasons(rows: list[dict], run_cost: float, max_mean_cost: float | None, max_median_wall: float | None) -> list[str]:
    if not rows:
        return []
    reasons = []
    mean_cost = run_cost / len(rows)
    median_wall = statistics.median(float(row["wall_s"]) for row in rows)
    if max_mean_cost is not None and mean_cost > max_mean_cost:
        reasons.append(f"mean cost/task ${mean_cost:.6f} exceeds ${max_mean_cost:.6f}")
    if max_median_wall is not None and median_wall > max_median_wall:
        reasons.append(f"median wall {median_wall:.3f}s exceeds {max_median_wall:.3f}s")
    if any(str(row.get("cost_lower_bound", "")).lower() == "true" for row in rows):
        reasons.append("timeout cost is a lower bound; reconcile before further paid work")
    return reasons


def reset_to(repo_name: str, clone: Path, base: str, keep: Path | None, save: bool = True) -> None:
    """Check out `base`, restore the carried lithify state, render it and commit the setup.

    With save=False the state already in `keep` is restored as is (resuming an interrupted task)."""
    if keep is not None and save:
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
    ap.add_argument(
        "--feedback",
        action="store_true",
        help="after a delivered task fails its holdout, run `lithify feedback` with that output",
    )
    ap.add_argument("--no-skip", action="store_true", help="ablation: skip_when_base_passes = false for adaptive")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--limit-usd", type=float, required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--experiment", default="pr-replay")
    ap.add_argument("--label", default="")
    ap.add_argument("--total-cap", type=float, default=TOTAL_CAP_USD, help="cap on spend across --budget-glob result dirs")
    ap.add_argument("--budget-glob", default="*", help="eval/results/ directories counted toward --total-cap")
    ap.add_argument("--session-cap-usd", type=float, help="Claude per-session budget, in addition to runner caps")
    ap.add_argument("--product-commit", help="verified installed product commit (separate from tooling checkout)")
    ap.add_argument("--replicate", default="")
    ap.add_argument("--seed-label", type=int, default=0, help="session label, not an executor RNG seed")
    ap.add_argument("--arm", default="")
    ap.add_argument("--max-mean-cost", type=float, help="stop after a task if cumulative mean cost exceeds this")
    ap.add_argument("--max-median-wall", type=float, help="stop after a task if median wall_s exceeds this")
    ap.add_argument("--resume", action="store_true", help="continue an interrupted run from its progress.json")
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

    arm = a.strategy + ("-noskip" if a.no_skip else "") + ("-feedback" if a.feedback else "")
    label = a.label or f"{a.repo}-{arm}-{a.executor.replace('@', '_')}"
    ev_root = out / "raw" / label
    ev_root.mkdir(parents=True, exist_ok=True)
    run_dir = work / f"replay-{a.experiment}-{label}"
    clone = run_dir / "repo"
    progress_file = run_dir / "progress.json"
    progress = {"next_pos": 1, "run_cost": 0.0, "audit": []}
    if a.resume:
        if not progress_file.exists():
            print(f"nothing to resume in {run_dir}", file=sys.stderr)
            return 1
        progress = json.loads(progress_file.read_text())
    else:
        shutil.rmtree(run_dir, ignore_errors=True)
        run_dir.mkdir(parents=True)
        git(work, "clone", "-q", str(work / f"{a.repo}.git"), str(clone))
    py = setup_env(a.repo, clone, work)
    test_cmd = spec["test_cmd"].format(py=py)
    redactions = {str(run_dir): "<run>", str(work): "<work>", str(EVAL): "<eval>"}

    commit = a.product_commit or lithify_commit()
    keep = run_dir / "carried"
    run_cost = float(progress["run_cost"])
    audit: list[dict] = list(progress["audit"])
    start = int(progress["next_pos"])
    csv_path = out / f"results-{label}.csv"
    completed = list(csv.DictReader(csv_path.open())) if a.resume and csv_path.exists() else []
    stop_reason: list[str] = []
    exit_code = 0

    def save_progress(next_pos: int) -> None:
        progress_file.write_text(json.dumps({"next_pos": next_pos, "run_cost": run_cost, "audit": audit}), encoding="utf-8")

    for pos, pr in enumerate(prs, 1):
        if pos < start:
            continue
        # The experiment-wide cap counts only this experiment's result directories.
        total = sum(spent(d) for d in RESULTS.glob(a.budget_glob) if d.is_dir())
        if run_cost >= a.limit_usd or total >= a.total_cap:
            print(f"budget stop before #{pr['number']}: run ${run_cost:.2f}/{a.limit_usd:.2f}; all results ${total:.2f}")
            stop_reason = ["budget cap"]
            exit_code = 80
            break
        reset_to(a.repo, clone, pr["base"], keep if pos > 1 else None, save=not (a.resume and pos == start))
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
        hit = limit_hit(ev)
        if hit:
            interrupted = out / "interruptions" / label / f"{pos:02d}-{time.time_ns()}"
            copy_redacted(ev, interrupted, redactions)
            write_rows(interrupted / "results-interrupted.csv", [{**m, "replicate": label, "outcome": "cli-limit"}])
            run_cost += float(m["cost_usd"])
            shutil.rmtree(ev, ignore_errors=True)
            save_progress(pos)
            print(f"LIMIT HIT at {pos}/{len(prs)} #{pr['number']}: {hit}; nothing recorded. Re-run with --resume.", flush=True)
            return 75
        (ev / "applied.diff").write_text(redact(git(clone, "diff", "HEAD"), redactions), encoding="utf-8")
        m["adopted"] = ""
        if a.adopt == "all" and m["proposed"]:
            r = lithify(clone, "adopt", m["task_id"])
            (ev / "adopt.txt").write_text(redact(r.stdout + r.stderr, redactions), encoding="utf-8")
            m["adopted"] = m["proposed"] if r.stdout.startswith("adopted") else ""
        m["feedback"] = ""
        if a.feedback and m["delivered"] and m["holdout_pass"] is False and m["task_id"]:
            # Post-delivery feedback: the task is already scored; its hidden-test failure now
            # reaches lithify the way a CI failure or review would, before the clone moves on.
            fb = lithify(
                clone, "feedback", m["task_id"], "--log", str(ev / "holdout_applied.txt"), "--json", timeout=a.timeout * 4
            )
            (ev / "feedback.txt").write_text(redact(fb.stdout + fb.stderr, redactions), encoding="utf-8")
            if LIMIT_TEXT.search(fb.stdout + fb.stderr):
                save_progress(pos)
                print(f"LIMIT HIT during feedback at {pos}/{len(prs)}; task kept unrecorded. Re-run with --resume.", flush=True)
                return 75
            try:
                res = json.loads(fb.stdout[fb.stdout.find("{") :])
            except json.JSONDecodeError:
                res = {}
            u = res.get("usage") or {}
            m["cost_usd"] = round(float(m["cost_usd"]) + float(u.get("cost", 0.0)), 4)
            m["role_sessions"] = int(m["role_sessions"]) + int(u.get("roles", 0))
            for col, key in (("tokens_in", "in"), ("tokens_cached", "cached"), ("tokens_out", "out")):
                m[col] = int(m[col]) + int(u.get(key, 0))
            m["feedback"] = " ".join(res.get("components") or []) or ("none" if res else "error")
            if a.adopt == "all" and res.get("proposal"):
                r = lithify(clone, "adopt", f"{m['task_id']}-feedback")
                (ev / "adopt-feedback.txt").write_text(redact(r.stdout + r.stderr, redactions), encoding="utf-8")
                if r.stdout.startswith("adopted"):
                    m["adopted"] = (m["adopted"] + " " + m["feedback"]).strip()
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
            "strategy": a.strategy + ("-noskip" if a.no_skip else "") + ("-feedback" if a.feedback else ""),
            "adopt_policy": a.adopt,
            "executor": a.executor,
            "task": f"{a.repo}#{pr['number']}",
            "order_seed": 0,
            "seed": a.seed_label,
            "replicate": a.replicate,
            "arm": a.arm or arm,
            "tooling_commit": lithify_commit(),
            "position": pos,
            "lithify_commit": commit,
            **m,
        }
        write_rows(csv_path, [row])
        completed.append(row)
        run_cost += float(m["cost_usd"])
        print(
            f"   k={m['k']} delivered={m['delivered']} first_pass={m['first_pass']} holdout={m['holdout_pass']} "
            f"exec={m['executions']} roles={m['role_sessions']} ${m['cost_usd']:.2f} ({time.time() - t0:.0f}s) "
            f"adopted=[{m['adopted']}] run total ${run_cost:.2f}",
            flush=True,
        )
        save_progress(pos + 1)
        stop_reason = tripwire_reasons(completed, run_cost, a.max_mean_cost, a.max_median_wall)
        if stop_reason:
            (ev_root / "tripwire.json").write_text(json.dumps({"reasons": stop_reason, "position": pos}, indent=2))
            print("TRIPWIRE STOP: " + "; ".join(stop_reason), flush=True)
            exit_code = 76
            break

    summary = {
        "label": label,
        "lithify_commit": commit,
        "run_cost_usd": round(run_cost, 4),
        "stop_reason": stop_reason,
        "completed_tasks": len(completed),
        "invariants": audit,
    }
    (ev_root / "audit.json").write_text(redact(json.dumps(summary, indent=2), redactions), encoding="utf-8")
    copy_redacted(clone / ".lithify" / "harness", ev_root / "final-harness", redactions)
    if (clone / ".lithify" / "library").is_dir():
        copy_redacted(clone / ".lithify" / "library", ev_root / "library", redactions)
    print(f"done: {label} ${run_cost:.2f}; scratch {run_dir}")
    return exit_code


if __name__ == "__main__":
    os.environ.pop("VIRTUAL_ENV", None)
    sys.exit(main())
