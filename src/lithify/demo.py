"""`lithify demo`: a credential-free, deterministic end-to-end run.

Builds a small fixture repository with hidden project conventions enforced by a real check
script, then runs the same task sequence under three strategies with the simulated agent:

  baseline   plain agent: one execution per task, no harness improvement
  static     a vanilla Harness² step (k=1, always propose) on every task
  adaptive   lithify: dynamic k, gate-first selection, evidence-gated promotion

Tokens are simulated, so compare shapes and ratios, not absolute numbers.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .config import Config, Schedule, render_config
from .harness import harness_dir
from .ops import init_project, spark
from .pipeline import Pipeline
from .state import load_state

CHECK_PY = '''"""Project conventions. Each features/<name>.py must declare the helpers it uses."""
import pathlib
import re
import sys

GLOBAL = {
    "AppError": "errors must be raised as AppError from app/errors.py, never a bare Exception",
    "get_logger": "log through get_logger from app/log.py, never print",
}
AREA = {
    "api": {"validate_payload": "API handlers must call validate_payload from app/api.py before reading input"},
    "db": {"use_session": "database access must go through use_session from app/db.py"},
    "reports": {"stream_csv": "report exports must stream rows with stream_csv from app/reports.py"},
    "billing": {
        "idempotency_key": "billing operations must pass an idempotency_key from app/billing.py",
        "money_decimal": "billing amounts must use money_decimal from app/billing.py, never float",
    },
}
FEATURES = {FEATURES}

failed = False
for f in sorted(pathlib.Path("features").glob("*.py")):
    name = f.stem
    m = re.search(r"^# uses: (.*)$", f.read_text(), re.M)
    uses = {u.strip() for u in (m.group(1).split(",") if m else []) if u.strip()}
    required = dict(GLOBAL)
    required.update(AREA.get(FEATURES.get(name, ""), {}))
    for tok, why in required.items():
        if tok not in uses:
            print(f"FAIL {name}: missing `{tok}` — {why}")
            failed = True
print("FAILED" if failed else "OK")
sys.exit(1 if failed else 0)
'''

# A new area ("billing", two conventions) arrives after the harness has stabilised, so the
# demo shows an anomaly re-heating k and the harness recovering.
TASKS: list[tuple[str, str]] = [
    ("create_user", "api"),
    ("list_orders", "db"),
    ("update_user", "api"),
    ("export_sales", "reports"),
    ("delete_order", "db"),
    ("search_users", "api"),
    ("archive_orders", "db"),
    ("monthly_report", "reports"),
    ("charge_card", "billing"),
    ("ban_user", "api"),
    ("refund_order", "db"),
    ("issue_invoice", "billing"),
    ("daily_digest", "reports"),
    ("rename_user", "api"),
]

APP_FILES = {
    "app/__init__.py": "",
    "app/errors.py": "class AppError(Exception):\n    pass\n",
    "app/log.py": "import logging\n\n\ndef get_logger(name):\n    return logging.getLogger(name)\n",
    "app/api.py": "def validate_payload(payload):\n    return dict(payload)\n",
    "app/db.py": "from contextlib import contextmanager\n\n\n@contextmanager\ndef use_session():\n    yield object()\n",
    "app/reports.py": "def stream_csv(rows):\n    yield from rows\n",
    "app/billing.py": "from decimal import Decimal\n\n\ndef money_decimal(x):\n    return Decimal(str(x))\n\n\n"
    "def idempotency_key(*parts):\n    return ':'.join(map(str, parts))\n",
    "README.md": "# fixture service\n\nSmall service used by `lithify demo`.\n",
}


def task_prompt(name: str, area: str) -> str:
    return f"Add feature `{name}` [area: {area}]: create features/{name}.py implementing it."


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=demo", "-c", "user.email=demo@localhost", "-c", "commit.gpgsign=false", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


def build_fixture(dest: Path, tasks: list[tuple[str, str]]) -> Path:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for rel, body in APP_FILES.items():
        p = dest / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    (dest / "tests").mkdir()
    (dest / "tests" / "check.py").write_text(CHECK_PY.replace("{FEATURES}", repr(dict(tasks))), encoding="utf-8")
    (dest / "features").mkdir()
    (dest / "features" / ".gitkeep").write_text("", encoding="utf-8")
    _git(dest, "init", "-q", "-b", "main")
    _git(dest, "add", "-A")
    _git(dest, "commit", "-q", "-m", "fixture")
    return dest


@dataclass
class StrategyResult:
    name: str
    delivered: int
    first_pass: int
    executions: int
    role_sessions: int
    tokens: int
    always_on: int
    final_s: float
    ks: list[int]
    s_curve: list[float]
    first: list[bool]


def run_strategy(name: str, base: Path, tasks: list[tuple[str, str]], max_k: int, quiet: bool, log=print) -> StrategyResult:
    repo = build_fixture(base / name, tasks)
    init_project(repo, executor="mock", test_cmd="python3 tests/check.py")
    cfg = Config(
        executor="mock",
        test_cmd="python3 tests/check.py",
        max_k=max_k,
        auto_adopt=True,
        concurrency=4,
        schedule=Schedule(window=6),
    )
    cfg.roles = {}
    if name == "static":
        cfg.skip_when_base_passes = False
    (repo / ".lithify" / "config.toml").write_text(render_config(cfg), encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "lithify init")
    execs = roles = toks = 0
    for i, (feat, area) in enumerate(tasks, 1):
        sink = (lambda _m: None) if quiet else log
        pipe = Pipeline(repo, cfg, log=sink, seed=i, escalate=(name != "baseline"))
        k_override = {"baseline": 0, "static": 1}.get(name)
        out = pipe.run_task(task_prompt(feat, area), k_override=k_override)
        execs += out.executions
        roles += out.role_sessions
        toks += int(pipe.usage["in"] + pipe.usage["out"])
        # commit the applied work (and any promoted harness) so the next task builds on it
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "--allow-empty", "-m", f"task {i}: {feat}")
        if not quiet:
            log("")
    st = load_state(repo)
    recs = st.records()
    from .harness import always_on_text, estimate_tokens

    return StrategyResult(
        name=name,
        delivered=sum(r.delivered for r in recs),
        first_pass=sum(r.first_pass for r in recs),
        executions=execs,
        role_sessions=roles,
        tokens=toks,
        always_on=estimate_tokens(always_on_text(harness_dir(repo))),
        final_s=recs[-1].stability_after if recs else 0.0,
        ks=[r.k for r in recs],
        s_curve=[r.stability_after for r in recs],
        first=[r.first_pass for r in recs],
    )


def run_demo(
    n_tasks: int = 14,
    max_k: int = 2,
    verbose: bool = False,
    keep: Path | None = None,
    strategies: tuple[str, ...] = ("baseline", "static", "adaptive"),
    log=print,
) -> list[StrategyResult]:
    tasks = TASKS[: max(1, min(n_tasks, len(TASKS)))]
    tmp = Path(keep) if keep else Path(tempfile.mkdtemp(prefix="lithify-demo-"))
    results = []
    try:
        for name in strategies:
            log(f"── strategy: {name} " + "─" * 40)
            r = run_strategy(name, tmp, tasks, max_k, quiet=not verbose, log=log)
            results.append(r)
            log(f"   first-pass  {''.join('✓' if f else '·' for f in r.first)}")
            log(f"   k per task  {' '.join(map(str, r.ks))}")
            log(f"   S curve     {spark(r.s_curve)}  → {r.final_s:.2f}")
        log("")
        log(
            f"{'strategy':10} {'delivered':>9} {'1st-pass':>8} {'executions':>10} {'role-calls':>10} "
            f"{'sim-tokens':>11} {'always-on':>9} {'final S':>7}"
        )
        n = len(tasks)
        for r in results:
            log(
                f"{r.name:10} {r.delivered:>6}/{n:<2} {r.first_pass:>5}/{n:<2} {r.executions:>10} "
                f"{r.role_sessions:>10} {r.tokens:>11,} {r.always_on:>9} {r.final_s:>7.2f}"
            )
        log("\n(simulated agent: compare shapes and ratios, not absolute token counts)")
        if keep:
            log(f"fixture repositories kept in {tmp}")
        return results
    finally:
        if not keep:
            shutil.rmtree(tmp, ignore_errors=True)
