"""Project configuration (.lithify/config.toml)."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

LITHIFY_DIR = ".lithify"
CONFIG_FILE = "config.toml"

ROLE_NAMES = ("propose_inv", "propose_dom", "compose", "select", "reflect", "compact")


@dataclass
class Schedule:
    explore_below: float = 0.4
    cruise_at: float = 0.8
    window: int = 10
    first_pass_weight: float = 0.7
    churn_scale_lines: int = 40


@dataclass
class Budget:
    always_on_tokens: int = 2500


@dataclass
class Config:
    executor: str = "claude"
    roles: dict[str, str] = field(default_factory=dict)
    test_cmd: str = ""
    lint_cmd: str = ""
    typecheck_cmd: str = ""
    holdout_cmd: str = ""
    max_k: int = 3
    mode: str = "parallel"
    auto_adopt: bool = False
    allow_test_edits: bool = False
    skip_when_base_passes: bool = True
    timeout_s: int = 1800
    concurrency: int = 4
    adapter_args: dict[str, list[str]] = field(default_factory=dict)
    schedule: Schedule = field(default_factory=Schedule)
    budget: Budget = field(default_factory=Budget)

    def role_cli(self, role: str) -> str:
        # Roles default to the executor's CLI at that CLI's default model, so a cheap
        # executor ("claude@<small-model>") does not silently make every editor cheap too.
        return self.roles.get(role) or self.executor.partition("@")[0]

    def gate_commands(self) -> list[tuple[str, str]]:
        cmds = [
            ("test", self.test_cmd),
            ("lint", self.lint_cmd),
            ("typecheck", self.typecheck_cmd),
            ("holdout", self.holdout_cmd),
        ]
        return [(n, c) for n, c in cmds if c.strip()]


def config_path(root: Path) -> Path:
    return root / LITHIFY_DIR / CONFIG_FILE


def load_config(root: Path) -> Config:
    path = config_path(root)
    if not path.exists():
        return Config()
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    main = data.get("lithify", {})
    cfg = Config()
    for key in (
        "executor",
        "test_cmd",
        "lint_cmd",
        "typecheck_cmd",
        "holdout_cmd",
        "max_k",
        "mode",
        "auto_adopt",
        "allow_test_edits",
        "skip_when_base_passes",
        "timeout_s",
        "concurrency",
    ):
        if key in main:
            setattr(cfg, key, main[key])
    cfg.roles = dict(data.get("roles", {}))
    cfg.adapter_args = {k: list(v) for k, v in data.get("adapter_args", {}).items()}
    for key, val in data.get("schedule", {}).items():
        if hasattr(cfg.schedule, key):
            setattr(cfg.schedule, key, val)
    for key, val in data.get("budget", {}).items():
        if hasattr(cfg.budget, key):
            setattr(cfg.budget, key, val)
    if cfg.mode not in ("parallel", "sequential"):
        raise ValueError(f"mode must be 'parallel' or 'sequential', got {cfg.mode!r}")
    if cfg.max_k < 1:
        raise ValueError("max_k must be >= 1")
    return cfg


def _q(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render_config(cfg: Config) -> str:
    roles = "\n".join(f"{r} = {_q(cfg.role_cli(r))}" for r in ROLE_NAMES)
    return f"""# lithify configuration — https://github.com/delvera-ai/lithify
[lithify]
# CLI that executes tasks during probes: claude | codex | agy | mock, optionally cli@model
# (e.g. "claude@claude-haiku-5-5" — a cheaper executor with a stronger editor is the paper's setup)
executor = {_q(cfg.executor)}
# Deterministic gates, run in every probe worktree before any LLM judge sees a candidate.
test_cmd = {_q(cfg.test_cmd)}
lint_cmd = {_q(cfg.lint_cmd)}
typecheck_cmd = {_q(cfg.typecheck_cmd)}
# Optional checks the agents never see (e.g. a script outside the repo). Strongest anti-gaming gate.
holdout_cmd = {_q(cfg.holdout_cmd)}
max_k = {cfg.max_k}
mode = {_q(cfg.mode)}           # parallel | sequential
# false: harness changes land in .lithify/proposals/ for `lithify adopt`.
# true: components the reflector marks `helped` are promoted automatically.
auto_adopt = {str(cfg.auto_adopt).lower()}
# false: a probe that edits tests which existed before it started fails its gate.
allow_test_edits = {str(cfg.allow_test_edits).lower()}
# With real gates, base rollouts that all pass leave nothing to contrast: deliver and skip proposals.
skip_when_base_passes = {str(cfg.skip_when_base_passes).lower()}
timeout_s = {cfg.timeout_s}
concurrency = {cfg.concurrency}

# Which CLI plays each improvement role. Using a different vendor for `select`
# reduces self-preference bias when judging the executor's work.
[roles]
{roles}

[schedule]
explore_below = {cfg.schedule.explore_below}   # S below this -> k = max_k (wide exploration)
cruise_at = {cfg.schedule.cruise_at}         # S at/above this -> k = 0 (execute + observe only)
window = {cfg.schedule.window}
first_pass_weight = {cfg.schedule.first_pass_weight}
churn_scale_lines = {cfg.schedule.churn_scale_lines}

[budget]
always_on_tokens = {cfg.budget.always_on_tokens}  # warn when always-on harness text exceeds this

# Extra CLI flags per adapter, e.g. claude = ["--model", "claude-sonnet-5-5"]
[adapter_args]
"""
