"""Project operations behind the CLI: init, sync, status, adopt, compact, report."""

from __future__ import annotations

import json
import re
import shutil
import time
from collections.abc import Sequence
from importlib import resources
from pathlib import Path
from typing import Any

from . import prompts, worktree
from .adapters import ADAPTERS, get_adapter, split_spec
from .config import LITHIFY_DIR, Config, config_path, load_config, render_config
from .harness import (
    always_on_text,
    copy_harness,
    diff,
    drop_component,
    estimate_tokens,
    harness_dir,
    harness_hash,
    promote,
    render,
)
from .library import ensure_library, library_dir
from .state import State, choose_k, load_state, phase_for, save_state, stability
from .validate import errors, validate

GITIGNORE_LINES = ["# lithify (probe evidence; large and machine-specific)", ".lithify/runs/"]
VENDOR = {"claude": "anthropic", "codex": "openai", "agy": "google", "mock": "mock"}


def detect_test_cmd(root: Path) -> str:
    if (root / "pyproject.toml").exists() or (root / "pytest.ini").exists() or (root / "tests").is_dir():
        if (root / "tests" / "check.py").exists() and not any((root / "tests").glob("test_*.py")):
            return "python3 tests/check.py"
        return "python3 -m pytest -q"
    if (root / "package.json").exists():
        try:
            pkg = json.loads((root / "package.json").read_text(encoding="utf-8"))
            if "test" in pkg.get("scripts", {}):
                return "npm test --silent"
        except json.JSONDecodeError:
            pass
    if (root / "Cargo.toml").exists():
        return "cargo test -q"
    if (root / "go.mod").exists():
        return "go test ./..."
    if (root / "Makefile").exists() and "test:" in (root / "Makefile").read_text(encoding="utf-8", errors="ignore"):
        return "make test"
    return ""


def installed_clis() -> list[str]:
    return [n for n in ("claude", "codex", "agy") if ADAPTERS[n]().available()]


def init_project(
    start: Path, executor: str | None = None, test_cmd: str | None = None, force: bool = False
) -> tuple[Path, list[str]]:
    root = worktree.repo_root(start)
    notes: list[str] = []
    ldir = root / LITHIFY_DIR
    ldir.mkdir(exist_ok=True)
    hdir = harness_dir(root)
    if hdir.exists() and not force:
        notes.append("harness already exists — left untouched (use --force to reset)")
    else:
        if hdir.exists():
            shutil.rmtree(hdir)
        src = resources.files("lithify").joinpath("templates/harness")
        hdir.mkdir(parents=True)
        for item in src.iterdir():
            if item.is_file():
                (hdir / item.name).write_text(item.read_text(encoding="utf-8"), encoding="utf-8")
    clis = installed_clis()
    cfg = load_config(root) if config_path(root).exists() and not force else Config()
    if executor:
        cfg.executor = executor
    elif not config_path(root).exists() or force:
        cfg.executor = clis[0] if clis else "claude"
    if test_cmd is not None:
        cfg.test_cmd = test_cmd
    elif not cfg.test_cmd:
        cfg.test_cmd = detect_test_cmd(root)
    if not cfg.roles:
        others = [c for c in clis if VENDOR[c] != VENDOR.get(split_spec(cfg.executor)[0])]
        cfg.roles = {"select": others[0]} if others else {}
    if not config_path(root).exists() or force or executor or test_cmd is not None:
        config_path(root).write_text(render_config(cfg), encoding="utf-8")
    mem = hdir / "memory.md"
    if cfg.test_cmd and "`" + cfg.test_cmd + "`" not in mem.read_text(encoding="utf-8"):
        mem.write_text(
            mem.read_text(encoding="utf-8").rstrip()
            + ("\n" if mem.read_text(encoding="utf-8").strip() else "")
            + f"- The project's checks run with `{cfg.test_cmd}`.\n",
            encoding="utf-8",
        )
    ensure_library(root)
    if not (ldir / "state.json").exists():
        save_state(root, State())
    gi = root / ".gitignore"
    cur = gi.read_text(encoding="utf-8") if gi.exists() else ""
    if ".lithify/runs/" not in cur:
        gi.write_text(cur.rstrip() + ("\n\n" if cur.strip() else "") + "\n".join(GITIGNORE_LINES) + "\n", encoding="utf-8")
    stats = render(root)
    if not cfg.test_cmd:
        notes.append(
            "no test command detected — set test_cmd in .lithify/config.toml; without gates lithify "
            "cannot verify deliverables and will never enter cruise (k=0)"
        )
    if not clis and cfg.executor != "mock":
        notes.append("none of claude / codex / agy found on PATH")
    notes.append(
        f"executor={cfg.executor} select={cfg.role_cli('select')} test_cmd={cfg.test_cmd or '(none)'} "
        f"always-on≈{stats['always_on_tokens']} tokens"
    )
    return root, notes


def sync(start: Path) -> dict[str, int]:
    root = worktree.repo_root(start)
    return render(root)


def proposals(root: Path) -> list[Path]:
    pdir = root / LITHIFY_DIR / "proposals"
    return sorted((d for d in pdir.iterdir() if (d / "harness").is_dir()), reverse=True) if pdir.is_dir() else []


def status(start: Path) -> dict[str, Any]:
    root = worktree.repo_root(start)
    cfg = load_config(root)
    st = load_state(root)
    s = stability(st.history, cfg.schedule)
    k, reason = choose_k(st, cfg.schedule, cfg.max_k)
    hdir = harness_dir(root)
    issues = validate(hdir, cfg.budget.always_on_tokens) if hdir.is_dir() else []
    tokens = estimate_tokens(always_on_text(hdir)) if hdir.is_dir() else 0
    lib = library_dir(root)
    return {
        "root": str(root),
        "initialized": hdir.is_dir(),
        "stability": s,
        "phase": phase_for(s, cfg.schedule),
        "next_k": k,
        "reason": reason,
        "tasks": len(st.history),
        "consecutive_failures": st.consecutive_failures,
        "pending_proposals": [p.name for p in proposals(root)],
        "always_on_tokens": tokens,
        "budget": cfg.budget.always_on_tokens,
        "validation": [str(i) for i in issues],
        "library_entries": len([d for d in lib.iterdir() if d.is_dir()]) if lib.is_dir() else 0,
        "executor": cfg.executor,
        "test_cmd": cfg.test_cmd,
    }


def adopt(start: Path, pid: str | None, only: list[str] | None = None, reject: bool = False) -> str:
    root = worktree.repo_root(start)
    plist = proposals(root)
    if not plist:
        return "no pending proposals"
    target = next((p for p in plist if p.name == pid), None) if pid else plist[0]
    if target is None:
        return f"no proposal {pid!r}; pending: {', '.join(p.name for p in plist)}"
    if reject:
        shutil.rmtree(target)
        return f"rejected {target.name}"
    keys = set(json.loads((target / "keys.json").read_text())) if (target / "keys.json").exists() else set()
    live = harness_dir(root)
    if only:
        unknown = set(only) - keys
        if unknown:
            return f"{', '.join(sorted(unknown))} not in proposal; components: {', '.join(sorted(keys))}"
        keys = set(only)
    tmp = root / LITHIFY_DIR / "runs" / f"adopt-{int(time.time())}"
    promote(live, target / "harness", keys, tmp)
    errs = errors(validate(tmp))
    if errs:
        shutil.rmtree(tmp, ignore_errors=True)
        return "adoption would produce an invalid harness:\n" + "\n".join(map(str, errs))
    _, churn, _ = diff(live, tmp)
    copy_harness(tmp, live)
    shutil.rmtree(tmp, ignore_errors=True)
    stats = render(root)
    remaining = set(json.loads((target / "keys.json").read_text())) - keys if only else set()
    if remaining:
        (target / "keys.json").write_text(json.dumps(sorted(remaining)))
    else:
        shutil.rmtree(target)
    return f"adopted {', '.join(sorted(keys))} from {target.name} ({churn} lines); always-on≈{stats['always_on_tokens']} tokens"


def compact(start: Path, cli: str | None = None) -> str:
    """Run the janitor role on a copy of the harness; result becomes a proposal."""
    root = worktree.repo_root(start)
    cfg = load_config(root)
    live = harness_dir(root)
    tokens = estimate_tokens(always_on_text(live))
    ts = time.strftime("%Y%m%d-%H%M%S")
    work = worktree.work_base(root) / f"compact-{ts}"
    ctx = work / "ctx"
    (ctx / "context").mkdir(parents=True)
    copy_harness(live, ctx / "context" / "harness")
    lib = library_dir(root)
    if lib.is_dir():
        shutil.copytree(lib, ctx / "context" / "library", ignore=shutil.ignore_patterns("harness"))
    (ctx / "context" / "budget.md").write_text(
        f"always-on estimate: {tokens} tokens\nbudget: {cfg.budget.always_on_tokens} tokens\n", encoding="utf-8"
    )
    (ctx / "MISSION.md").write_text(prompts.render("compact"), encoding="utf-8")
    role_cli = cli or cfg.role_cli("compact")
    res = get_adapter(role_cli, cfg.adapter_args.get(split_spec(role_cli)[0])).run(
        "Read MISSION.md in the current directory and carry it out exactly. Work only inside the current directory.",
        ctx,
        cfg.timeout_s,
        role="compact",
    )
    try:
        if not res.ok:
            return f"compact session failed: {res.error[:300]}"
        new_h = ctx / "context" / "harness"
        errs = errors(validate(new_h))
        if errs:
            return "compacted harness failed validation; discarded:\n" + "\n".join(map(str, errs))
        hdiff, churn, changed = diff(live, new_h)
        if not changed:
            return f"nothing to compact (always-on≈{tokens} tokens)"
        after = estimate_tokens(always_on_text(new_h))
        pdir = root / LITHIFY_DIR / "proposals" / f"{ts}-compact"
        copy_harness(new_h, pdir / "harness")
        (pdir / "harness.diff").write_text(hdiff, encoding="utf-8")
        (pdir / "keys.json").write_text(json.dumps(sorted(changed)))
        (pdir / "PROPOSAL.md").write_text(
            f"# Compaction proposal\n\nalways-on: {tokens} → {after} tokens; {churn} lines changed.\n\n"
            f"Review `harness.diff`, then `lithify adopt {pdir.name}`.\n",
            encoding="utf-8",
        )
        return f"compaction proposal {pdir.name}: always-on {tokens} → {after} tokens ({churn} lines)"
    finally:
        shutil.rmtree(work, ignore_errors=True)


def spark(values: Sequence[float], lo: float = 0.0, hi: float = 1.0) -> str:
    bars = "▁▂▃▄▅▆▇█"
    if not values:
        return ""
    span = (hi - lo) or 1.0
    return "".join(bars[min(7, max(0, int((v - lo) / span * 7.999)))] for v in values)


def report(start: Path) -> str:
    root = worktree.repo_root(start)
    st = load_state(root)
    recs = st.records()
    if not recs:
        return "no tasks recorded yet"
    lines = [
        f"{'task':42} {'k':>2} {'1st':>4} {'ok':>3} {'exec':>4} {'tok_in':>9} {'tok_out':>8} {'cost$':>7} {'aot':>5} {'S':>5}"
    ]
    for r in recs:
        lines.append(
            f"{r.task_id[:42]:42} {r.k:>2} {'✓' if r.first_pass else '·':>4} {'✓' if r.delivered else '✗':>3} "
            f"{r.executions:>4} {r.tokens_in:>9} {r.tokens_out:>8} {r.cost_usd:>7.2f} "
            f"{r.always_on_tokens:>5} {r.stability_after:>5.2f}"
        )
    s_vals = [r.stability_after for r in recs]
    toks = [r.tokens_in + r.tokens_out for r in recs]
    lines.append("")
    lines.append(f"S       {spark(s_vals)}  ({s_vals[0]:.2f} → {s_vals[-1]:.2f})")
    lines.append(f"tokens  {spark(toks, 0, max(toks) or 1)}  (max {max(toks)}, last {toks[-1]})")
    lines.append(f"k       {' '.join(str(r.k) for r in recs)}")
    return "\n".join(lines)


def prepare_ablation(root: Path, task_id: str, component: str) -> tuple[str, Path, str]:
    """Copy a past task's frozen start harness without one component (`rule:<id>` or `skill:<name>`).

    Returns the task text, the ablated harness directory and the new task id. The live harness is not read.
    """
    run = root / LITHIFY_DIR / "runs" / task_id
    if not (run / "outcome.json").exists():
        raise ValueError(f"no run {task_id!r} under {run.parent}")
    start = run / "harness-start"
    if not start.is_dir():
        raise ValueError(f"{task_id} predates harness snapshots and cannot be replayed")
    data = json.loads((run / "outcome.json").read_text(encoding="utf-8"))
    if harness_hash(start) != data.get("start_harness_sha256"):
        raise ValueError(f"the snapshot of {task_id} does not match its recorded hash")
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", component).strip("-")
    new_id = f"{task_id}-without-{slug}"
    dst = root / LITHIFY_DIR / "runs" / new_id / "start-harness"
    if dst.parent.exists():
        raise ValueError(f"{new_id} already exists; remove {dst.parent} to replay it again")
    dst.parent.mkdir(parents=True)
    copy_harness(start, dst)
    drop_component(dst, component)
    return data["task"], dst, new_id
