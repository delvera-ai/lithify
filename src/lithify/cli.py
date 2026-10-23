"""Command-line interface. Standard library only, so it runs anywhere Python 3.11+ does."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, ops, worktree
from .adapters import ADAPTERS, get_adapter
from .config import load_config
from .harness import harness_dir
from .pipeline import Pipeline
from .validate import errors, validate


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def cmd_init(a: argparse.Namespace) -> int:
    root, notes = ops.init_project(Path.cwd(), executor=a.executor, test_cmd=a.test_cmd, force=a.force)
    print(f"lithify initialised in {root}")
    for n in notes:
        print(f"  • {n}")
    print(
        "\nnext: review .lithify/config.toml, commit .lithify/ CLAUDE.md AGENTS.md, then:\n"
        '  lithify run "<task>"      (or /lithify-run inside Claude Code, Codex or agy)'
    )
    return 0


def cmd_sync(a: argparse.Namespace) -> int:
    stats = ops.sync(Path.cwd())
    print(
        f"rendered harness: always-on≈{stats['always_on_tokens']} tokens, "
        f"{stats['skills']} skill(s), {stats['subagents']} subagent(s)"
    )
    return 0


def cmd_validate(a: argparse.Namespace) -> int:
    if a.path:
        hdir = Path(a.path)
        budget = None
    else:
        root = worktree.repo_root(Path.cwd())
        hdir = harness_dir(root)
        budget = load_config(root).budget.always_on_tokens
    issues = validate(hdir, budget)
    for i in issues:
        print(i)
    errs = errors(issues)
    print(f"{len(errs)} error(s), {len(issues) - len(errs)} warning(s)")
    return 1 if errs else 0


def cmd_status(a: argparse.Namespace) -> int:
    s = ops.status(Path.cwd())
    if a.json:
        print(json.dumps(s, indent=2))
        return 0
    if not s["initialized"]:
        print("lithify is not initialised here — run `lithify init`")
        return 1
    print(f"stability S={s['stability']:.2f}  phase={s['phase']}  next k={s['next_k']} ({s['reason']})")
    print(
        f"tasks={s['tasks']}  library entries={s['library_entries']}  "
        f"always-on≈{s['always_on_tokens']}/{s['budget']} tokens  executor={s['executor']}"
    )
    if s["pending_proposals"]:
        print(f"pending proposals: {', '.join(s['pending_proposals'])}  (lithify adopt --list)")
    for v in s["validation"]:
        print(f"  {v}")
    return 0


def cmd_run(a: argparse.Namespace) -> int:
    root = worktree.repo_root(Path.cwd())
    cfg = load_config(root)
    if a.executor:
        cfg.executor = a.executor
    if a.max_k:
        cfg.max_k = a.max_k
    task = " ".join(a.task).strip()
    if a.task_file:
        task = Path(a.task_file).read_text(encoding="utf-8").strip()
    if not task:
        _err('give a task: lithify run "add rate limiting to the API"')
        return 2
    if a.detach and not a.dry_run:
        return _detach(root, task, a)
    log = (lambda _m: None) if a.quiet else (lambda m: print(m, flush=True))
    pipe = Pipeline(root, cfg, log=log, keep_worktrees=a.keep, escalate=not a.no_escalate)
    try:
        out = pipe.run_task(task, k_override=a.k, mode=a.mode, dry_run=a.dry_run, task_id=a.task_id)
    except Exception as e:
        _err(f"lithify run failed: {e}")
        return 1
    if a.dry_run:
        print(out.message)
        return 0
    if a.json:
        print(
            json.dumps(
                {
                    "task_id": out.task_id,
                    "k": out.k,
                    "delivered": out.delivered,
                    "applied": out.applied,
                    "first_pass": out.first_pass,
                    "selected": out.selected,
                    "promoted": out.promoted,
                    "proposal": str(out.proposal) if out.proposal else None,
                    "stability": out.record.stability_after if out.record else None,
                    "executions": out.executions,
                    "role_sessions": out.role_sessions,
                },
                indent=2,
            )
        )
    return 0 if out.delivered and out.applied else 3


def _detach(root: Path, task: str, a: argparse.Namespace) -> int:
    """Run in a background process so agent shells with command timeouts can poll it."""
    import subprocess

    from .pipeline import new_task_id

    tid = new_task_id(task)
    rdir = root / ".lithify" / "runs" / tid
    rdir.mkdir(parents=True, exist_ok=True)
    (rdir / "task.md").write_text(task + "\n", encoding="utf-8")
    argv = [sys.executable, "-m", "lithify", "run", "--task-file", str(rdir / "task.md"), "--task-id", tid]
    for flag, val in (("--k", a.k), ("--max-k", a.max_k), ("--mode", a.mode), ("--executor", a.executor)):
        if val is not None:
            argv += [flag, str(val)]
    if a.keep:
        argv.append("--keep")
    if a.no_escalate:
        argv.append("--no-escalate")
    with open(rdir / "run.log", "w", encoding="utf-8") as logf:
        proc = subprocess.Popen(
            argv, cwd=root, stdout=logf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True
        )
    (rdir / "pid").write_text(str(proc.pid), encoding="utf-8")
    print(json.dumps({"task_id": tid, "pid": proc.pid, "log": str(rdir / "run.log"), "poll": f"lithify logs {tid}"}))
    return 0


def _latest_run(root: Path) -> Path | None:
    rdir = root / ".lithify" / "runs"
    runs = (
        sorted((d for d in rdir.iterdir() if (d / "run.log").exists() or (d / "outcome.json").exists()), key=lambda d: d.name)
        if rdir.is_dir()
        else []
    )
    return runs[-1] if runs else None


def cmd_logs(a: argparse.Namespace) -> int:
    import os

    root = worktree.repo_root(Path.cwd())
    rdir = (root / ".lithify" / "runs" / a.id) if a.id else _latest_run(root)
    if rdir is None or not rdir.exists():
        print("no runs found")
        return 1
    log = rdir / "run.log"
    lines = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
    print("\n".join(lines[-a.tail :]))
    done = (rdir / "outcome.json").exists()
    running = False
    if (rdir / "pid").exists() and not done:
        try:
            os.kill(int((rdir / "pid").read_text()), 0)
            running = True
        except (OSError, ValueError):
            running = False
    state = "finished" if done else "running" if running else "stopped (no outcome — check the log)"
    print(f"\n[{rdir.name}: {state}]")
    if done:
        o = json.loads((rdir / "outcome.json").read_text(encoding="utf-8"))
        print(
            json.dumps(
                {k: o.get(k) for k in ("selected", "applied", "first_pass", "promoted", "proposal", "stability_after", "why")},
                indent=2,
            )
        )
    return 0


def cmd_adopt(a: argparse.Namespace) -> int:
    root = worktree.repo_root(Path.cwd())
    if a.list:
        plist = ops.proposals(root)
        if not plist:
            print("no pending proposals")
        for p in plist:
            head = (p / "PROPOSAL.md").read_text(encoding="utf-8").splitlines()
            comp = next((ln for ln in head if ln.startswith("Components") or ln.startswith("always-on")), "")
            print(f"{p.name}\n   {comp}\n   diff: {p.relative_to(root)}/harness.diff")
        return 0
    print(ops.adopt(Path.cwd(), a.id, only=a.only, reject=a.reject))
    return 0


def cmd_compact(a: argparse.Namespace) -> int:
    print(ops.compact(Path.cwd(), cli=a.cli))
    return 0


def cmd_report(a: argparse.Namespace) -> int:
    print(ops.report(Path.cwd()))
    return 0


def cmd_demo(a: argparse.Namespace) -> int:
    from .demo import run_demo

    strategies = tuple(a.strategies.split(",")) if a.strategies else ("baseline", "static", "adaptive")
    run_demo(n_tasks=a.tasks, max_k=a.max_k, verbose=a.verbose, keep=Path(a.keep) if a.keep else None, strategies=strategies)
    return 0


def cmd_doctor(a: argparse.Namespace) -> int:
    print(f"lithify {__version__}  python {sys.version.split()[0]}")
    for name in ("claude", "codex", "agy"):
        ad = ADAPTERS[name]()
        print(f"  {name:7} {'✓ ' + ad.version() if ad.available() else '✗ not on PATH'}")
    try:
        s = ops.status(Path.cwd())
        print(f"  repo    {s['root']}  initialised={s['initialized']}  test_cmd={s['test_cmd'] or '(none)'}")
        print(f"  work    {worktree.work_base(Path(s['root']))}")
    except worktree.GitError as e:
        print(f"  repo    {e}")
    return 0


def cmd_hook(a: argparse.Namespace) -> int:
    """Hooks must never break the host CLI: every failure is silent and exits 0."""
    try:
        import os

        raw = sys.stdin.read() if not sys.stdin.isatty() else ""
        if a.event != "session-start":
            return 0
        cwd = Path.cwd()
        try:  # Claude Code and Codex pass the session cwd on stdin
            payload = json.loads(raw) if raw.strip() else {}
            if isinstance(payload, dict) and payload.get("cwd") and os.path.isdir(payload["cwd"]):
                cwd = Path(payload["cwd"])
        except json.JSONDecodeError:
            pass
        s = ops.status(cwd)
        if not s["initialized"]:
            return 0
        msg = f"lithify: harness stability S={s['stability']:.2f} ({s['phase']}); the next `lithify run` uses k={s['next_k']}."
        if s["pending_proposals"]:
            msg += (
                f" {len(s['pending_proposals'])} harness proposal(s) await review — mention this to the user "
                "and suggest `lithify adopt --list`."
            )
        if s["always_on_tokens"] > s["budget"]:
            msg += " The always-on harness is over budget; suggest `lithify compact`."
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": msg}}))
    except Exception:
        return 0
    return 0


def cmd_role(a: argparse.Namespace) -> int:
    """Debug helper: run one adapter with a prompt in the current directory."""
    res = get_adapter(a.cli).run(" ".join(a.prompt), Path.cwd(), role=a.role)
    print(
        json.dumps(
            {
                "ok": res.ok,
                "text": res.text[-2000:],
                "error": res.error,
                "tokens_in": res.tokens_in,
                "tokens_out": res.tokens_out,
                "cost_usd": res.cost_usd,
            },
            indent=2,
        )
    )
    return 0 if res.ok else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="lithify", description="Self-hardening agent harnesses (Harness²-style) for Claude Code, Codex and Antigravity."
    )
    p.add_argument("--version", action="version", version=f"lithify {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)
    clis = sorted(ADAPTERS)

    s = sub.add_parser("init", help="create .lithify/ and render the harness into CLAUDE.md/AGENTS.md/skills")
    s.add_argument("--executor", help="cli or cli@model: " + " | ".join(clis))
    s.add_argument("--test-cmd")
    s.add_argument("--force", action="store_true", help="reset the harness and config to defaults")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("sync", help="re-render .lithify/harness into each CLI's native paths")
    s.set_defaults(fn=cmd_sync)

    s = sub.add_parser("validate", help="zero-token structural check of a harness")
    s.add_argument("path", nargs="?")
    s.set_defaults(fn=cmd_validate)

    s = sub.add_parser("status", help="stability, phase, next k, pending proposals")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("run", help="run a task through Propose→Probe→Compose with dynamic k")
    s.add_argument("task", nargs="*")
    s.add_argument("--task-file")
    s.add_argument("--k", type=int, help="override the schedule (0 = cruise)")
    s.add_argument("--max-k", type=int)
    s.add_argument("--mode", choices=["parallel", "sequential"])
    s.add_argument("--executor", help="cli or cli@model, e.g. claude@claude-haiku-5-5")
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--keep", action="store_true", help="keep probe worktrees for inspection")
    s.add_argument("--json", action="store_true")
    s.add_argument("--quiet", action="store_true")
    s.add_argument("--detach", action="store_true", help="run in the background; poll with `lithify logs`")
    s.add_argument("--no-escalate", action="store_true", help="k=0 failures stay failures (baseline arm for evals)")
    s.add_argument("--task-id", help=argparse.SUPPRESS)
    s.set_defaults(fn=cmd_run)

    s = sub.add_parser("logs", help="show the log and outcome of the latest (or given) run")
    s.add_argument("id", nargs="?")
    s.add_argument("--tail", type=int, default=40)
    s.set_defaults(fn=cmd_logs)

    s = sub.add_parser("adopt", help="review and adopt harness proposals")
    s.add_argument("id", nargs="?")
    s.add_argument("--list", action="store_true")
    s.add_argument("--only", nargs="+", metavar="COMPONENT")
    s.add_argument("--reject", action="store_true")
    s.set_defaults(fn=cmd_adopt)

    s = sub.add_parser("compact", help="janitor pass: shrink the always-on harness into a proposal")
    s.add_argument("--cli", choices=clis)
    s.set_defaults(fn=cmd_compact)

    s = sub.add_parser("report", help="per-task metrics and the stability curve")
    s.set_defaults(fn=cmd_report)

    s = sub.add_parser("demo", help="credential-free simulated comparison: baseline vs static vs adaptive")
    s.add_argument("--tasks", type=int, default=14)
    s.add_argument("--max-k", type=int, default=2)
    s.add_argument("--strategies", help="comma list of baseline,static,adaptive")
    s.add_argument("--verbose", action="store_true")
    s.add_argument("--keep", metavar="DIR", help="keep fixture repos in DIR")
    s.set_defaults(fn=cmd_demo)

    s = sub.add_parser("doctor", help="check installed CLIs and repository setup")
    s.set_defaults(fn=cmd_doctor)

    s = sub.add_parser("hook", help="lifecycle hook entry point (used by the plugins)")
    s.add_argument("event", choices=["session-start"])
    s.set_defaults(fn=cmd_hook)

    s = sub.add_parser("role", help=argparse.SUPPRESS)
    s.add_argument("cli", choices=clis)
    s.add_argument("--role", default="execute")
    s.add_argument("prompt", nargs="+")
    s.set_defaults(fn=cmd_role)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.fn(args) or 0)
    except worktree.GitError as e:
        _err(str(e))
        return 2
    except KeyboardInterrupt:
        return 130
