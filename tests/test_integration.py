"""End-to-end runs with the simulated agent: real git worktrees, gates, rendering and state."""

import json
import subprocess
import sys

from lithify import ops
from lithify.config import Config, render_config
from lithify.demo import build_fixture, run_demo, task_prompt
from lithify.harness import harness_dir
from lithify.pipeline import Pipeline
from lithify.state import load_state

from .conftest import git


def setup_fixture(tmp_path, auto_adopt=True, max_k=2):
    repo = build_fixture(tmp_path / "fx", [("create_user", "api"), ("list_orders", "db"), ("update_user", "api")])
    ops.init_project(repo, executor="mock", test_cmd="python3 tests/check.py")
    cfg = Config(executor="mock", test_cmd="python3 tests/check.py", max_k=max_k, auto_adopt=auto_adopt)
    (repo / ".lithify" / "config.toml").write_text(render_config(cfg))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init lithify")
    return repo, cfg


def test_genesis_task_improves_and_promotes(tmp_path):
    repo, cfg = setup_fixture(tmp_path)
    out = Pipeline(repo, cfg, log=lambda m: None, seed=1).run_task(task_prompt("create_user", "api"))
    assert out.delivered and out.applied and not out.first_pass and out.k == 2
    assert (repo / "features" / "create_user.py").exists()
    assert "AppError" in (harness_dir(repo) / "guardrails.md").read_text()
    assert (repo / ".claude" / "skills" / "api-conventions" / "SKILL.md").exists()
    assert (repo / ".agents" / "skills" / "api-conventions" / "SKILL.md").exists()
    assert "skills/api-conventions" in out.promoted
    entries = [d for d in (repo / ".lithify" / "library").iterdir() if d.is_dir()]
    assert len(entries) == 1 and "helped" in (entries[0] / "EXPERIENCE.md").read_text()
    # probe worktrees cleaned up; nothing leaked into the repo's worktree list
    assert git(repo, "worktree", "list").count("\n") == 1


def test_proposal_flow_without_auto_adopt(tmp_path):
    repo, cfg = setup_fixture(tmp_path, auto_adopt=False)
    out = Pipeline(repo, cfg, log=lambda m: None, seed=1).run_task(task_prompt("create_user", "api"))
    assert out.delivered and out.proposal is not None and out.promoted == []
    assert "AppError" not in (harness_dir(repo) / "guardrails.md").read_text()
    msg = ops.adopt(repo, out.proposal.name)
    assert msg.startswith("adopted")
    assert "AppError" in (harness_dir(repo) / "guardrails.md").read_text()
    assert "AppError" in (repo / "CLAUDE.md").read_text()
    assert ops.proposals(repo) == []


def test_cruise_executes_once(tmp_path):
    repo, cfg = setup_fixture(tmp_path)
    Pipeline(repo, cfg, log=lambda m: None, seed=1).run_task(task_prompt("create_user", "api"))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "t1")
    out = Pipeline(repo, cfg, log=lambda m: None, seed=2).run_task(task_prompt("update_user", "api"), k_override=0)
    assert out.first_pass and out.executions == 1 and out.role_sessions == 0


def test_dry_run_has_no_side_effects(tmp_path):
    repo, cfg = setup_fixture(tmp_path)
    out = Pipeline(repo, cfg, log=lambda m: None).run_task("anything", dry_run=True)
    assert "would run k=2" in out.message
    assert load_state(repo).history == []


def test_demo_adaptive_beats_static_on_role_calls():
    res = {r.name: r for r in run_demo(n_tasks=14, max_k=2, log=lambda m: None)}
    assert res["baseline"].delivered == 0
    assert res["adaptive"].delivered == res["static"].delivered == 14
    assert res["adaptive"].role_sessions < res["static"].role_sessions / 2
    assert res["adaptive"].tokens < res["static"].tokens
    assert 0 in res["adaptive"].ks and res["adaptive"].ks[0] == 2


def test_cli_init_status_hook(repo):
    env_py = [sys.executable, "-m", "lithify"]
    r = subprocess.run([*env_py, "init", "--executor", "mock", "--test-cmd", "true"], cwd=repo, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    st = json.loads(subprocess.run([*env_py, "status", "--json"], cwd=repo, capture_output=True, text=True).stdout)
    assert st["initialized"] and st["next_k"] == 3 and st["phase"] == "genesis"
    hook = subprocess.run([*env_py, "hook", "session-start"], cwd=repo, input="{}", capture_output=True, text=True)
    payload = json.loads(hook.stdout)
    assert "lithify" in payload["hookSpecificOutput"]["additionalContext"]
    assert ".lithify/runs/" in (repo / ".gitignore").read_text()
    v = subprocess.run([*env_py, "validate"], cwd=repo, capture_output=True, text=True)
    assert v.returncode == 0


def test_hook_is_silent_outside_a_repo(tmp_path):
    r = subprocess.run(
        [sys.executable, "-m", "lithify", "hook", "session-start"], cwd=tmp_path, input="{}", capture_output=True, text=True
    )
    assert r.returncode == 0 and r.stdout == ""


def test_test_edit_detection_allows_appends_but_flags_rewrites(repo):
    from lithify import worktree as wtm

    (repo / "tests").mkdir()
    (repo / "tests" / "test_a.py").write_text("from m import a\n\n\ndef test_a():\n    assert a() == 1\n")
    (repo / "m.pyc").write_text("junk")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "tests")
    wt = wtm.create(repo, "t")
    wtm.seal_base(wt)
    f = wt / "tests" / "test_a.py"
    f.write_text("from m import a, b\n\n\ndef test_a():\n    assert a() == 1\n\n\ndef test_b():\n    assert b()\n")
    (wt / "m.pyc").write_text("changed junk")
    patch = wtm.deliverable(wt)
    assert "m.pyc" not in patch
    assert wtm.weakened_tests(wt, ["tests/test_a.py"]) == []
    f.write_text("from m import a, b\n\n\ndef test_a():\n    assert a() in (1, 2)\n")
    wtm.deliverable(wt)
    assert wtm.weakened_tests(wt, ["tests/test_a.py"])
    wtm.remove(repo, wt)


def test_deliverable_keeps_source_files_under_agent_dirs(repo):
    """Only rendered subpaths are excluded: a repo whose real sources live under .agents/ or
    .claude-plugin/ (lithify itself) must not have those edits silently dropped."""
    from lithify import worktree as wtm
    from lithify.harness import render

    ops.init_project(repo, executor="mock", test_cmd="true")
    for rel in (".agents/plugins/marketplace.json", ".claude-plugin/plugin.json", ".claude/settings.json"):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text('{"v": 1}\n')
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "plugin sources")
    (repo / ".agents/plugins/marketplace.json").write_text('{"v": 2}\n')  # uncommitted, must reach the probe
    wt = wtm.create(repo, "t", wtm.dirty_patch(repo))
    assert (wt / ".agents/plugins/marketplace.json").read_text() == '{"v": 2}\n'
    render(wt, harness_dir(wt))
    wtm.seal_base(wt)
    (wt / ".agents/plugins/marketplace.json").write_text('{"v": 3}\n')
    (wt / ".claude-plugin/plugin.json").write_text('{"v": 3}\n')
    (wt / ".claude/settings.json").write_text('{"v": 3}\n')
    (wt / ".agents/skills/x").mkdir(parents=True)
    (wt / ".agents/skills/x/SKILL.md").write_text("rendered\n")
    (wt / ".claude/skills/x").mkdir(parents=True)
    (wt / ".claude/skills/x/SKILL.md").write_text("rendered\n")
    (wt / ".claude/agents").mkdir(parents=True)
    (wt / ".claude/agents/a.md").write_text("rendered\n")
    (wt / "CLAUDE.md").write_text("changed\n")
    (wt / ".lithify/harness/memory.md").write_text("changed\n")
    paths = {p for _, p in wtm.changed_files(wt)} if wtm.deliverable(wt) else set()
    assert paths == {".agents/plugins/marketplace.json", ".claude-plugin/plugin.json", ".claude/settings.json"}
    wtm.remove(repo, wt)


def test_holdout_command_never_reaches_agents(tmp_path):
    """holdout_cmd must stay invisible: no config in probe worktrees, no path in gate reports."""
    from lithify.config import load_config

    repo, _ = setup_fixture(tmp_path)
    secret = tmp_path / "hidden" / "holdout_check.py"
    secret.parent.mkdir()
    secret.write_text("import sys\nprint('holdout ran')\nsys.exit(0)\n")
    cfgp = repo / ".lithify" / "config.toml"
    cfgp.write_text(cfgp.read_text().replace('holdout_cmd = ""', f'holdout_cmd = "python3 {secret}"'))
    git(repo, "commit", "-qam", "holdout")
    cfg = load_config(repo)
    pipe = Pipeline(repo, cfg, log=lambda m: None, seed=1, keep_worktrees=True)
    out = pipe.run_task(task_prompt("create_user", "api"))
    assert out.delivered
    evidence = list((repo / ".lithify" / "runs" / out.task_id).rglob("*.md"))
    gates = [p for p in evidence if p.name == "gates.md"]
    assert gates and all("holdout=pass" in p.read_text() or "holdout=FAIL" in p.read_text() for p in gates)
    assert not any(str(secret) in p.read_text() for p in evidence)
    assert pipe._wts and not any((wt / ".lithify" / "config.toml").exists() for wt in pipe._wts)
    for wt in pipe._wts:
        from lithify import worktree as wtm

        wtm.remove(repo, wt)


def test_test_edit_only_failure_is_saved_for_review(repo, monkeypatch):
    """#15: a fix that must change an assertion an existing test pins is never applied, but the work is
    kept as needs-review.patch instead of being reported as plain "no rollout passed"."""
    from lithify.adapters.base import RunResult
    from lithify.adapters.mock import MockAdapter
    from lithify.config import Config

    (repo / "tests").mkdir()
    (repo / "tests" / "test_a.py").write_text("def test_a():\n    assert 1 + 1 == 2\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "tests")

    def rewrites_assertion(self, prompt, cwd, timeout_s=1800, role="execute"):
        (cwd / "tests" / "test_a.py").write_text("def test_a():\n    assert 1 + 1 >= 2\n")
        return RunResult(ok=True, text="done")

    monkeypatch.setattr(MockAdapter, "run", rewrites_assertion)
    for test_cmd, expect_review in (("true", True), ("false", False)):
        ops.init_project(repo, executor="mock", test_cmd=test_cmd, force=True)
        cfg = Config(executor="mock", test_cmd=test_cmd)
        out = Pipeline(repo, cfg, log=lambda m: None, escalate=False).run_task("change the pinned behaviour", k_override=0)
        assert not out.delivered and not out.applied
        assert (repo / "tests" / "test_a.py").read_text().endswith("== 2\n")  # nothing applied
        outcome = json.loads((repo / ".lithify" / "runs" / out.task_id / "outcome.json").read_text())
        assert bool(outcome["needs_review"]) is expect_review
        if expect_review:
            assert ">= 2" in (repo / ".lithify" / "runs" / out.task_id / "needs-review.patch").read_text()
            assert "saved for review" in out.message


def test_agent_limit_stops_the_task_cleanly(tmp_path, monkeypatch):
    """A usage/session-limit notice must stop the task: no further sessions, no state record, no worktrees."""
    import pytest

    from lithify.adapters.base import LimitReached, RunResult
    from lithify.adapters.mock import MockAdapter

    repo, cfg = setup_fixture(tmp_path)
    calls = []

    def limited(self, prompt, cwd, timeout_s=1800, role="execute"):
        calls.append(role)
        return RunResult(ok=False, error="You've hit your session limit · resets 6:40pm")

    monkeypatch.setattr(MockAdapter, "run", limited)
    pipe = Pipeline(repo, cfg, log=lambda m: None, seed=1)
    with pytest.raises(LimitReached):
        pipe.run_task(task_prompt("create_user", "api"))
    # parallel base probes may already be in flight; no role session may start after the refusal
    assert set(calls) == {"execute"} and len(calls) <= cfg.max_k
    assert load_state(repo).history == []
    assert git(repo, "worktree", "list").count("\n") == 1


def test_post_delivery_feedback_hardens_harness_and_reheats(tmp_path, capsys, monkeypatch):
    """`lithify feedback`: a task that passed its gates but failed a later check proposes a harness
    edit from that failure, stops counting as first-pass, and never alters the delivered work."""
    from lithify import cli
    from lithify.config import load_config
    from lithify.feedback import feedback
    from lithify.state import choose_k, stability

    repo = build_fixture(tmp_path / "fx", [("create_user", "api"), ("update_user", "api")])
    ops.init_project(repo, executor="mock", test_cmd="true")  # the gate checks nothing
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    cfg = load_config(repo)
    out = Pipeline(repo, cfg, log=lambda m: None, seed=1).run_task(task_prompt("create_user", "api"), k_override=0)
    assert out.delivered and out.first_pass
    s_before = stability(load_state(repo).history, cfg.schedule)

    ci = "FAIL create_user: missing `AppError` — errors must be raised as AppError from app/errors.py, never a bare Exception\n"
    res = feedback(repo, out.task_id, ci, log=lambda m: None)
    assert res["proposal"] and "guardrails.md" in res["components"] and res["marked"]
    st = load_state(repo)
    assert st.history[-1]["feedback_failed"] and not st.history[-1]["first_pass"]
    assert stability(st.history, cfg.schedule) < s_before or s_before == 0
    assert choose_k(st, cfg.schedule, cfg.max_k)[0] >= 1  # explores again
    assert "AppError" not in (harness_dir(repo) / "guardrails.md").read_text()  # proposal, not promoted
    assert git(repo, "worktree", "list").count("\n") == 1
    assert ops.adopt(repo, f"{out.task_id}-feedback").startswith("adopted")
    assert "AppError" in (harness_dir(repo) / "guardrails.md").read_text()

    monkeypatch.chdir(repo)
    log = tmp_path / "ci.txt"
    log.write_text(ci)
    assert cli.main(["feedback", "no-such-task", "--log", str(log)]) == 1
    assert "no outcome" in capsys.readouterr().err
