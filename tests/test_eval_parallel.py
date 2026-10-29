"""Zero-token safety checks for the owner-approved two-run schedule."""

import json

from eval.round2.run_b_parallel import budget_fits, timing_passes


def test_parallel_launch_reserves_both_full_caps_and_headroom():
    assert budget_fits(14)
    assert not budget_fits(14.000001)
    assert budget_fits(12, remaining_a=2)
    assert not budget_fits(12.000001, remaining_a=2)


def test_preflight_requires_two_complete_waves_and_every_suite_to_pass():
    rows = [{"returncode": 0, "wall_s": 160}] * 16
    assert timing_passes(rows)
    assert not timing_passes(rows[:-1])
    assert not timing_passes([*rows[:-1], {"returncode": 0, "wall_s": 160.001}])
    assert not timing_passes([*rows[:-1], {"returncode": 1, "wall_s": 1}])


def test_shared_phase_stop_blocks_next_task_before_reset_or_model_call(tmp_path, monkeypatch):
    from eval import pr_replay

    evaluation = tmp_path / "eval"
    tasks = evaluation / "prs/sqlglot/tasks"
    tasks.mkdir(parents=True)
    (tasks / "1.md").write_text("frozen task")
    (tasks.parent / "prs.json").write_text(json.dumps({"prs": [{"number": 1, "split": "eval"}]}))
    stop = tmp_path / "stop.json"
    stop.write_text('{"reason": "other replicate tripped"}')
    monkeypatch.setattr(pr_replay, "EVAL", evaluation)
    monkeypatch.setattr(pr_replay, "RESULTS", evaluation / "results")
    monkeypatch.setattr(pr_replay, "setup_env", lambda *args: "/unused/python")
    monkeypatch.setattr(pr_replay, "lithify_commit", lambda: "test")

    def forbidden(*args, **kwargs):
        raise AssertionError("shared stop must prevent checkout reset and paid execution")

    monkeypatch.setattr(pr_replay, "reset_to", forbidden)
    monkeypatch.setattr(pr_replay, "run_task", forbidden)
    code = pr_replay.main(
        [
            "sqlglot",
            "--strategy",
            "baseline",
            "--split",
            "eval",
            "--limit-usd",
            "7",
            "--work",
            str(tmp_path / "work"),
            "--out",
            str(evaluation / "results/test"),
            "--phase-stop-file",
            str(stop),
        ]
    )
    assert code == 78
    assert not list((evaluation / "results/test").glob("results*.csv"))


def test_active_A_occupies_one_slot_until_successful_supervisor_exit(tmp_path, monkeypatch):
    import pytest
    from eval.round2 import run_b_parallel

    monkeypatch.setattr(run_b_parallel.os, "kill", lambda *args: None)
    path = tmp_path / "SUPERVISOR.json"
    path.write_text(json.dumps({"status": "running", "supervisor_pid": 1, "child_pid": 2}))
    assert run_b_parallel.running_a_slots(tmp_path) == 1
    path.write_text(json.dumps({"status": "completed", "exit_code": 0}))
    assert run_b_parallel.running_a_slots(tmp_path) == 0
    path.write_text(json.dumps({"status": "stopped; owner review", "exit_code": 76}))
    with pytest.raises(RuntimeError, match="stop the phase"):
        run_b_parallel.running_a_slots(tmp_path)


def test_five_suite_guard_does_not_authorize_eight_suite_B_pair():
    rows = [{"returncode": 0, "wall_s": 159}] * 10
    assert timing_passes(rows, suites=5)
    assert not timing_passes(rows)
