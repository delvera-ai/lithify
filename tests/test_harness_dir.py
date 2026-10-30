"""A task can start from a supplied harness directory: validated, frozen, hashed in outcome.json."""

import json
import shutil

import pytest

from lithify import ops
from lithify.config import Config, render_config
from lithify.demo import build_fixture, task_prompt
from lithify.harness import harness_dir, harness_hash
from lithify.pipeline import Pipeline

from .conftest import git


def setup_fixture(tmp_path):
    repo = build_fixture(tmp_path / "fx", [("create_user", "api"), ("list_orders", "db")])
    ops.init_project(repo, executor="mock", test_cmd="python3 tests/check.py")
    cfg = Config(executor="mock", test_cmd="python3 tests/check.py", max_k=2, auto_adopt=True)
    (repo / ".lithify" / "config.toml").write_text(render_config(cfg))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init lithify")
    return repo, cfg


def alt_harness(repo, tmp_path, marker):
    alt = tmp_path / "alt-harness"
    shutil.copytree(harness_dir(repo), alt)
    with (alt / "guardrails.md").open("a", encoding="utf-8") as fh:
        fh.write(f"\n{marker}\n")
    return alt


def test_hash_follows_content_and_skips_pycache(tmp_path):
    d = tmp_path / "h"
    (d / "skills" / "x").mkdir(parents=True)
    (d / "skills" / "x" / "SKILL.md").write_text("one\n", encoding="utf-8")
    first = harness_hash(d)
    assert first == harness_hash(d)
    (d / "skills" / "x" / "__pycache__").mkdir()
    (d / "skills" / "x" / "__pycache__" / "junk.pyc").write_bytes(b"x")
    assert harness_hash(d) == first
    (d / "skills" / "x" / "SKILL.md").write_text("two\n", encoding="utf-8")
    assert harness_hash(d) != first


def test_run_starts_from_supplied_harness_and_records_its_hash(tmp_path):
    repo, cfg = setup_fixture(tmp_path)
    alt = alt_harness(repo, tmp_path, "ALT-MARKER-7")
    live_before = harness_hash(harness_dir(repo))
    # --no-escalate, as in the round-2 arms: a k=0 failure does not promote anything into the live harness
    out = Pipeline(repo, cfg, log=lambda m: None, seed=1, escalate=False).run_task(
        task_prompt("create_user", "api"), k_override=0, start_harness=alt
    )
    run = json.loads((repo / ".lithify" / "runs" / out.task_id / "outcome.json").read_text(encoding="utf-8"))
    assert run["start_harness_sha256"] == harness_hash(alt)
    assert run["start_harness_sha256"] != live_before
    assert harness_hash(harness_dir(repo)) == live_before
    assert "ALT-MARKER-7" not in (harness_dir(repo) / "guardrails.md").read_text(encoding="utf-8")


def test_default_run_records_live_harness_hash(tmp_path):
    repo, cfg = setup_fixture(tmp_path)
    live_before = harness_hash(harness_dir(repo))
    out = Pipeline(repo, cfg, log=lambda m: None, seed=1, escalate=False).run_task(
        task_prompt("create_user", "api"), k_override=0
    )
    run = json.loads((repo / ".lithify" / "runs" / out.task_id / "outcome.json").read_text(encoding="utf-8"))
    assert run["start_harness_sha256"] == live_before


def test_missing_supplied_harness_is_refused(tmp_path):
    repo, cfg = setup_fixture(tmp_path)
    with pytest.raises(RuntimeError, match="no harness found at"):
        Pipeline(repo, cfg, log=lambda m: None, seed=1).run_task(
            task_prompt("create_user", "api"), k_override=0, start_harness=tmp_path / "absent"
        )


def test_invalid_supplied_harness_is_refused(tmp_path):
    repo, cfg = setup_fixture(tmp_path)
    bad = alt_harness(repo, tmp_path, "x")
    (bad / "scripts").mkdir()
    (bad / "scripts" / "broken.py").write_text("def (:\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="fails validation"):
        Pipeline(repo, cfg, log=lambda m: None, seed=1).run_task(
            task_prompt("create_user", "api"), k_override=0, start_harness=bad
        )
