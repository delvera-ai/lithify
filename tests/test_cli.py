"""In-process CLI tests via lithify.cli.main (subprocess tests in test_integration.py add no coverage)."""

import io
import json
import re

import pytest

from lithify import cli
from lithify.demo import build_fixture, task_prompt

from .conftest import git


def run(capsys, monkeypatch, cwd, *argv, stdin=""):
    monkeypatch.chdir(cwd)
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin))
    rc = cli.main(list(argv))
    out = capsys.readouterr()
    return rc, out.out, out.err


@pytest.fixture
def fx(tmp_path, capsys, monkeypatch):
    repo = build_fixture(tmp_path / "fx", [("create_user", "api"), ("update_user", "api")])
    rc, out, _ = run(capsys, monkeypatch, repo, "init", "--executor", "mock", "--test-cmd", "python3 tests/check.py")
    assert rc == 0 and "lithify initialised" in out
    cfgp = repo / ".lithify" / "config.toml"
    cfgp.write_text(re.sub(r"(?m)^max_k = \d+", "max_k = 1", cfgp.read_text()))  # independent of the default
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    return repo


def test_status_validate_sync_doctor(fx, capsys, monkeypatch):
    rc, out, _ = run(capsys, monkeypatch, fx, "status")
    assert rc == 0 and "phase=genesis" in out and "next k=1" in out
    rc, out, _ = run(capsys, monkeypatch, fx, "status", "--json")
    assert json.loads(out)["initialized"]
    rc, out, _ = run(capsys, monkeypatch, fx, "validate")
    assert rc == 0 and "0 error(s)" in out
    rc, out, _ = run(capsys, monkeypatch, fx, "validate", str(fx / ".lithify" / "harness"))
    assert rc == 0
    rc, out, _ = run(capsys, monkeypatch, fx, "sync")
    assert rc == 0 and "rendered harness" in out
    rc, out, _ = run(capsys, monkeypatch, fx, "doctor")
    assert rc == 0 and "initialised=True" in out


def test_validate_reports_errors(fx, capsys, monkeypatch):
    (fx / ".lithify" / "harness" / "memory.md").write_text("token sk-abcdefghijklmnopqrstuvwxyz123456\n")
    rc, out, _ = run(capsys, monkeypatch, fx, "validate")
    assert rc == 1 and "credential" in out


def test_run_dry_run_json_logs_report_adopt(fx, capsys, monkeypatch):
    rc, out, _ = run(capsys, monkeypatch, fx, "run", "--dry-run", task_prompt("create_user", "api"))
    assert rc == 0 and "would run k=1" in out
    rc, out, _ = run(capsys, monkeypatch, fx, "run", "--json", "--quiet", task_prompt("create_user", "api"))
    res = json.loads(out)
    assert rc == 0 and res["delivered"] and res["applied"] and res["proposal"]
    rc, out, _ = run(capsys, monkeypatch, fx, "logs")
    assert rc == 0 and "finished" in out
    rc, out, _ = run(capsys, monkeypatch, fx, "report")
    assert rc == 0 and res["task_id"][:20] in out
    rc, out, _ = run(capsys, monkeypatch, fx, "adopt", "--list")
    assert rc == 0 and res["task_id"] in out
    rc, out, _ = run(capsys, monkeypatch, fx, "status")
    assert "pending proposals" in out
    rc, out, _ = run(capsys, monkeypatch, fx, "adopt", res["task_id"])
    assert rc == 0 and out.startswith("adopted")
    rc, out, _ = run(capsys, monkeypatch, fx, "adopt", "--list")
    assert "no pending proposals" in out


def test_run_needs_a_task_and_reports_git_errors(tmp_path, fx, capsys, monkeypatch):
    rc, _, err = run(capsys, monkeypatch, fx, "run")
    assert rc == 2 and "give a task" in err
    rc, _, err = run(capsys, monkeypatch, tmp_path, "logs")
    assert rc == 2 and "not inside a git repository" in err


def test_hook_session_start_reads_cwd_from_stdin(fx, tmp_path, capsys, monkeypatch):
    rc, out, _ = run(capsys, monkeypatch, tmp_path, "hook", "session-start", stdin=json.dumps({"cwd": str(fx)}))
    assert rc == 0
    ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert ctx.startswith("lithify: harness stability")
    rc, out, _ = run(capsys, monkeypatch, tmp_path, "hook", "session-start", stdin="not json")
    assert rc == 0 and out == ""


def test_demo_single_strategy(capsys, monkeypatch, tmp_path):
    rc, out, _ = run(capsys, monkeypatch, tmp_path, "demo", "--tasks", "2", "--strategies", "baseline")
    assert rc == 0 and "baseline" in out


def test_role_debug_helper(fx, capsys, monkeypatch):
    rc, out, _ = run(capsys, monkeypatch, fx, "role", "mock", "do", "nothing")
    assert rc == 0 and json.loads(out)["ok"] and "nothing to do" in json.loads(out)["text"]
