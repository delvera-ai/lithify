from lithify.validate import errors, validate

from .test_harness import make_harness


def msgs(issues):
    return " | ".join(str(i) for i in issues)


def test_clean_harness(tmp_path):
    assert errors(validate(make_harness(tmp_path / "h"))) == []


def test_skill_needs_trigger_and_matching_name(tmp_path):
    h = make_harness(tmp_path / "h", skill=None)
    d = h / "skills" / "thing"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text("---\nname: other\ndescription: short\n---\n")
    out = msgs(errors(validate(h)))
    assert "must equal directory name" in out and "trigger" in out


def test_named_script_must_ship(tmp_path):
    h = make_harness(tmp_path / "h", skill=None)
    d = h / "skills" / "verify"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(
        "---\nname: verify\ndescription: Use before finishing any change to verify it.\n---\n"
        "Run `python3 .lithify/harness/skills/verify/scripts/check.py`.\n"
    )
    assert "does not ship" in msgs(errors(validate(h)))
    (d / "scripts").mkdir()
    (d / "scripts" / "check.py").write_text("print('ok')\n")
    assert errors(validate(h)) == []


def test_script_must_compile(tmp_path):
    h = make_harness(tmp_path / "h")
    (h / "scripts").mkdir()
    (h / "scripts" / "bad.py").write_text("def broken(:\n")
    assert "does not compile" in msgs(errors(validate(h)))


def test_secrets_rejected(tmp_path):
    h = make_harness(tmp_path / "h")
    (h / "memory.md").write_text("key: sk-abcdefghijklmnopqrstuvwxyz123456\n")
    assert "credential" in msgs(errors(validate(h)))


def test_budget_warning(tmp_path):
    h = make_harness(tmp_path / "h", guard="- " + "x" * 4000 + "\n")
    issues = validate(h, budget_tokens=200)
    assert errors(issues) == []
    assert "exceeds budget" in msgs(issues)
