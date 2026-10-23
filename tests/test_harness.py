from pathlib import Path

from lithify.harness import BEGIN, END, always_on_text, diff, promote, render


def make_harness(h: Path, guard: str = "- rule one\n", skill: str | None = "api-conventions") -> Path:
    h.mkdir(parents=True, exist_ok=True)
    (h / "system.md").write_text("Be careful.\n")
    (h / "guardrails.md").write_text(guard)
    if skill:
        d = h / "skills" / skill
        d.mkdir(parents=True, exist_ok=True)
        (d / "SKILL.md").write_text(
            f"---\nname: {skill}\ndescription: Use when a task touches the api layer.\n---\n\n- call `validate_payload`\n"
        )
    return h


def test_always_on_lists_skills(tmp_path):
    h = make_harness(tmp_path / "h")
    text = always_on_text(h)
    assert "Guardrails" in text and "rule one" in text
    assert "`api-conventions`" in text


def test_render_preserves_user_content(tmp_path):
    root = tmp_path / "r"
    root.mkdir()
    (root / "CLAUDE.md").write_text("# My notes\n\nkeep me\n")
    h = make_harness(root / ".lithify" / "harness")
    render(root, h)
    render(root, h)  # idempotent
    text = (root / "CLAUDE.md").read_text()
    assert text.count(BEGIN) == 1 and text.count(END) == 1
    assert text.startswith("# My notes") and "keep me" in text
    assert (root / "AGENTS.md").exists()
    for t in (".claude/skills", ".agents/skills"):
        assert (root / t / "api-conventions" / "SKILL.md").exists()


def test_render_never_overwrites_user_skill_and_prunes_stale(tmp_path):
    root = tmp_path / "r"
    user = root / ".claude" / "skills" / "api-conventions"
    user.mkdir(parents=True)
    (user / "SKILL.md").write_text("user owned\n")
    h = make_harness(root / ".lithify" / "harness")
    render(root, h)
    assert (user / "SKILL.md").read_text() == "user owned\n"
    assert (root / ".agents" / "skills" / "api-conventions" / ".lithify-managed").exists()
    # remove the skill from the harness: managed copy is pruned, user copy stays
    import shutil

    shutil.rmtree(h / "skills")
    render(root, h)
    assert not (root / ".agents" / "skills" / "api-conventions").exists()
    assert (user / "SKILL.md").exists()


def test_subagents_render_for_claude(tmp_path):
    root = tmp_path / "r"
    h = make_harness(root / ".lithify" / "harness", skill=None)
    a = h / "subagents" / "scout"
    a.mkdir(parents=True)
    (a / "AGENT.md").write_text("---\nname: scout\ndescription: finds things\n---\nbody\n")
    render(root, h)
    out = (root / ".claude" / "agents" / "scout.md").read_text()
    assert out.startswith("---\nname: scout")


def test_diff_and_promote(tmp_path):
    a = make_harness(tmp_path / "a")
    b = make_harness(tmp_path / "b", guard="- rule one\n- rule two\n", skill="db-conventions")
    text, churn, keys = diff(a, b)
    assert "rule two" in text and churn > 0
    assert keys == {"guardrails.md", "skills/api-conventions", "skills/db-conventions"}
    out = promote(a, b, {"skills/db-conventions"}, tmp_path / "out")
    assert (out / "skills" / "db-conventions" / "SKILL.md").exists()
    assert (out / "skills" / "api-conventions" / "SKILL.md").exists()  # not promoted away
    assert "rule two" not in (out / "guardrails.md").read_text()
