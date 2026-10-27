"""Regression tests for evaluation launch guards; no agent calls."""

from types import SimpleNamespace

from eval.pr_replay import configure, limit_hit

from lithify.adapters import get_adapter
from lithify.config import load_config


def test_limit_notice_is_detected_without_an_outcome(tmp_path):
    (tmp_path / "lithify.log").write_text(
        "lithify run failed: probe base-1 stopped by an agent CLI limit: "
        "You've hit your session limit · resets 2:10pm (Africa/Johannesburg)"
    )
    assert limit_hit(tmp_path) == "agent CLI limit notice in lithify.log"


def test_session_budget_reaches_the_actual_adapter_command(tmp_path):
    (tmp_path / ".lithify").mkdir()
    args = SimpleNamespace(
        executor="claude@claude-haiku-5-5",
        max_k=2,
        adopt="all",
        strategy="baseline",
        no_skip=False,
        timeout=900,
        concurrency=4,
        roles="claude",
        session_cap_usd=1.5,
    )
    configure(tmp_path, args, "/venv/bin/python -m pytest -q")
    config = load_config(tmp_path)
    command = get_adapter(config.executor, config.adapter_args["claude"]).build_cmd("task", tmp_path)
    assert command[command.index("--max-budget-usd") + 1] == "1.5"
    assert "--dangerously-skip-permissions" in command
    assert config.test_cmd == "/venv/bin/python -m pytest -q"
