"""Regression tests for evaluation launch guards; no agent calls."""

from types import SimpleNamespace

from eval.pr_replay import configure, limit_hit, tripwire_reasons

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


def test_tripwires_use_cumulative_mean_and_median_from_first_task():
    assert tripwire_reasons([{"wall_s": 621}], 0.02, 0.068, 620) == ["median wall 621.000s exceeds 620.000s"]
    assert tripwire_reasons([{"wall_s": 10}], 0.069, 0.068, 620) == ["mean cost/task $0.069000 exceeds $0.068000"]
    assert tripwire_reasons([{"wall_s": 10}, {"wall_s": 1000}, {"wall_s": 10}], 0.09, 0.068, 620) == []
    assert tripwire_reasons([{"wall_s": 620}], 0.068, 0.068, 620) == []


def test_timeout_outcomes_are_distinct(tmp_path):
    import json

    from eval.evalkit import timeout_kinds

    probe = tmp_path / "rollouts/base-1"
    probe.mkdir(parents=True)
    (probe / "run.json").write_text(json.dumps({"returncode": 124, "error": "timeout after 900s"}))
    (probe / "gates.md").write_text("TIMEOUT after 900s")
    assert timeout_kinds(tmp_path) == ["executor", "gate"]
    assert timeout_kinds(None, outer=True, hold_rc=124) == ["runner"]
    assert timeout_kinds(None, hold_rc=124) == ["holdout"]


def test_outer_timeout_keeps_partial_cost_and_does_not_reuse_old_outcome(tmp_path, monkeypatch):
    import json
    import subprocess

    from eval import evalkit

    repo = tmp_path / "repo"
    old = repo / ".lithify/runs/old"
    old.mkdir(parents=True)
    (old / "outcome.json").write_text(json.dumps({"usage": {"cost": 99}}))
    (repo / ".lithify/state.json").write_text(json.dumps({"history": []}))
    evidence = tmp_path / "evidence"
    evidence.mkdir()

    def interrupted(*args, **kwargs):
        sessions = repo / ".lithify/runs/new/sessions"
        sessions.mkdir(parents=True)
        (sessions / "001-execute.json").write_text(
            json.dumps(
                {
                    "results": [
                        {
                            "session_id": "new",
                            "total_cost_usd": 0.01,
                            "usage": {"input_tokens": 3},
                            "duration_ms": 10,
                            "duration_api_ms": 5,
                        }
                    ]
                }
            )
        )
        raise subprocess.TimeoutExpired("lithify", 5400)

    def forbidden_holdout(*args):
        raise AssertionError("an interrupted runner did not deliver a task")

    monkeypatch.setattr(evalkit, "lithify", interrupted)
    result = evalkit.run_task(repo, tmp_path / "task.md", "baseline", forbidden_holdout, 5400, evidence, {})
    assert result["task_id"] == "new" and result["outcome"] == "timeout"
    assert result["timeout_kind"] == "runner" and result["cost_lower_bound"]
    assert result["cost_usd"] == 0.01 and result["tokens_in"] == 3
    assert result["active_s"] == 0.01 and result["api_s"] == 0.005


def test_cli_resume_cap_and_timezone_reset_are_zero_token_checks():
    from datetime import UTC, datetime

    from eval.round2.run_a_replicates import reset_delay, resume_allowed

    now = datetime(2026, 10, 27, 12, 0, tzinfo=UTC)
    assert reset_delay("resets 2:10pm (Africa/Johannesburg)", now) == 660
    assert resume_allowed([{"utc_date": "2026-10-27"}] * 2, now)
    assert not resume_allowed([{"utc_date": "2026-10-27"}] * 3, now)


def test_replicate_ledger_keeps_prior_invalid_run_with_same_label(tmp_path, monkeypatch):
    from eval.round2 import run_a_replicates

    ledger = tmp_path / "eval/LEDGER.md"
    ledger.parent.mkdir()
    (tmp_path / "eval/results").mkdir()
    original = "| 2026-10-27 | 0 | A / r1-A-rep2 | 2/60 | 3.6267 | 3.6267 | invalid |\n"
    ledger.write_text(original)
    monkeypatch.setattr(run_a_replicates, "ROOT", tmp_path)
    summary = {"label": "r1-A-rep2", "tasks": 1, "cost_usd": 0.03}
    run_a_replicates.update_ledger(summary, "running")
    run_a_replicates.update_ledger(summary, "running")
    text = ledger.read_text()
    assert original in text
    assert text.count("| 0 A replicate | A / r1-A-rep2 |") == 1
