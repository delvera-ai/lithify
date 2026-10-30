"""Attribution: per-task harness snapshots, rollout reads, always-on rule ids and `lithify ablate`.

`tests/fixtures/claude_2.1.310_read_skill.jsonl` is a real 2.1.310 stream (a round-2 task-12 run). Only its
Read/Skill calls, their results (truncated) and the final result event are kept; local paths are scrubbed.
"""

import json
from pathlib import Path

import pytest

from lithify import ops
from lithify.adapters.claude import ClaudeAdapter
from lithify.config import Config, render_config
from lithify.demo import build_fixture, task_prompt
from lithify.harness import always_on_rules, classify_read, drop_component, harness_dir, harness_hash
from lithify.pipeline import Pipeline
from lithify.state import load_state

from .conftest import git

FIX = Path(__file__).parent / "fixtures"


def setup_fixture(tmp_path):
    repo = build_fixture(tmp_path / "fx", [("create_user", "api"), ("list_orders", "db")])
    ops.init_project(repo, executor="mock", test_cmd="python3 tests/check.py")
    cfg = Config(executor="mock", test_cmd="python3 tests/check.py", max_k=2, auto_adopt=True)
    (repo / ".lithify" / "config.toml").write_text(render_config(cfg))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init lithify")
    return repo, cfg


def test_rule_ids_are_stable_per_bullet_text(tmp_path):
    hdir = tmp_path / "h"
    hdir.mkdir()
    (hdir / "guardrails.md").write_text("# Guardrails\n\n- never skip tests\n- keep diffs small\n", encoding="utf-8")
    before = always_on_rules(hdir)
    assert sorted(before.values()) == ["- keep diffs small", "- never skip tests"]
    (hdir / "guardrails.md").write_text("# Guardrails\n\n- never skip tests\n- keep diffs tiny\n", encoding="utf-8")
    after = always_on_rules(hdir)
    kept = [k for k in before if before[k] == "- never skip tests"]
    assert kept and all(k in after for k in kept)
    assert "- keep diffs small" not in after.values()


def test_drop_component_removes_one_rule_or_skill(tmp_path):
    hdir = tmp_path / "h"
    (hdir / "skills" / "x").mkdir(parents=True)
    (hdir / "skills" / "x" / "SKILL.md").write_text("---\nname: x\n---\nbody\n", encoding="utf-8")
    (hdir / "guardrails.md").write_text("- keep\n- drop me\n", encoding="utf-8")
    rule = next(k for k, v in always_on_rules(hdir).items() if v == "- drop me")
    assert drop_component(hdir, f"rule:{rule}").startswith("rule ")
    assert (hdir / "guardrails.md").read_text(encoding="utf-8") == "- keep\n"
    assert drop_component(hdir, "skill:x") == "skill x"
    assert not (hdir / "skills" / "x").exists()
    with pytest.raises(ValueError):
        drop_component(hdir, "rule:missing#00000000")
    with pytest.raises(ValueError):
        drop_component(hdir, "bogus")


def test_classify_read_names_skills_instructions_and_files(tmp_path):
    wt = tmp_path / "wt"
    assert classify_read(str(wt / ".claude/skills/sqlglot-rewrites/SKILL.md"), wt) == "skill:sqlglot-rewrites"
    assert classify_read(str(wt / ".agents/skills/s/scripts/run.py"), wt) == "skill:s"
    assert classify_read(str(wt / "CLAUDE.md"), wt) == "instructions:CLAUDE.md"
    assert classify_read(str(wt / ".lithify/library/a.md"), wt) == "lithify:.lithify/library/a.md"
    assert classify_read(str(wt / "sqlglot/optimizer.py"), wt) == "file:sqlglot/optimizer.py"
    assert classify_read("skill:sqlglot-rewrites", wt) == "skill:sqlglot-rewrites"


def test_claude_stream_records_reads_and_skill_calls():
    stream = (FIX / "claude_2.1.310_read_skill.jsonl").read_text(encoding="utf-8")
    reads = ClaudeAdapter().parse(stream, "", 0).meta["reads"]
    assert reads.count("skill:sqlglot-optimizer-rewrites") == 1
    assert sum(not r.startswith("skill:") for r in reads) == 10  # the 10 Read calls in the captured stream


def test_run_records_snapshots_hashes_and_reads(tmp_path):
    repo, cfg = setup_fixture(tmp_path)
    out = Pipeline(repo, cfg, log=lambda m: None, seed=1, escalate=False).run_task(
        task_prompt("create_user", "api"), k_override=0
    )
    run = repo / ".lithify" / "runs" / out.task_id
    data = json.loads((run / "outcome.json").read_text(encoding="utf-8"))
    assert data["harness_after_sha256"] == harness_hash(harness_dir(repo))
    assert harness_hash(run / "harness-after") == data["harness_after_sha256"]
    assert harness_hash(run / "harness-start") == data["start_harness_sha256"]
    assert data["always_on_rules"] == sorted(always_on_rules(run / "harness-start"))
    assert data["always_on_rules"]
    assert all("reads" in p for p in data["probes"].values())
    assert load_state(repo).history[-1]["harness_after_sha256"] == data["harness_after_sha256"]


def test_ablate_replays_from_the_frozen_start_without_one_rule(tmp_path):
    repo, cfg = setup_fixture(tmp_path)
    out = Pipeline(repo, cfg, log=lambda m: None, seed=1, escalate=False).run_task(
        task_prompt("create_user", "api"), k_override=0
    )
    base = repo / ".lithify" / "runs" / out.task_id
    data = json.loads((base / "outcome.json").read_text(encoding="utf-8"))
    rule = data["always_on_rules"][0]
    text = always_on_rules(base / "harness-start")[rule]

    task, start, new_id = ops.prepare_ablation(repo, out.task_id, f"rule:{rule}")
    assert task == data["task"]
    assert new_id == f"{out.task_id}-without-rule-{rule.replace('#', '-')}"
    assert text not in [v for v in always_on_rules(start).values()]
    assert harness_hash(harness_dir(repo)) == data["harness_after_sha256"]  # live harness untouched

    replay = Pipeline(repo, cfg, log=lambda m: None, seed=1, escalate=False).run_task(
        task, k_override=0, task_id=new_id, start_harness=start
    )
    assert replay.task_id == new_id
    assert (repo / ".lithify" / "runs" / new_id / "outcome.json").exists()
    with pytest.raises(ValueError, match="already exists"):
        ops.prepare_ablation(repo, out.task_id, f"rule:{rule}")
    with pytest.raises(ValueError, match="no run"):
        ops.prepare_ablation(repo, "no-such-task", f"rule:{rule}")
