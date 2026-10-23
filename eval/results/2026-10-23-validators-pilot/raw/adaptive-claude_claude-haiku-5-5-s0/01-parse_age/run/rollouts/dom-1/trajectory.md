# trajectory dom-1

final message:
`parse_age` is added to `app/users.py`, and the full suite passes (28 tests). The audit checker also passes for `parse_age`.

**What it does**
- Accepts an `int`, or a `str` of ASCII decimal digits with optional surrounding whitespace. Returns the value as an `int`.
- Valid range is 0 to 150 inclusive.
- Rejects with `ValidationError`: non-int/non-str types, `bool`, non-digit strings (including `+5`, `1.5`, `1 2`, empty), negatives, and values over 150.
- Each rejection calls `record_rejection("age", value, msg)` first, with the raw caller value, as the project's audit invariant requires.

**Choices I made**
- Two messages: a type error ("age must be an integer or a string of digits") and a range/format error ("age must be a whole number from 0 to 150").
- I used `re.fullmatch(r"[0-9]+")` rather than `str.isdigit()`, because `isdigit()` accepts Unicode digits like superscripts.
- I did not touch `parse_name` or `parse_quantity`. They still skip the audit call, as the task only asked for the new function.

**Tests**
Added to `tests/test_users.py` without changing the existing `parse_name` tests. They cover valid inputs (including whitespace and leading zeros), and rejections that check both the `ValidationError` and that exactly one audit record was added for the rejected value.

## events
[tool_use Skill] {"skill": "input-validators"}
[tool_result] Launching skill: input-validators
[user] Base directory for this skill: ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/dom-1/.claude/skills/input-validators

# Input validators in this service

The `app/` package is input parsing for the accounts service. Each `parse_<field>(value)` takes a
raw value, returns the normalised value, and rejects bad input.

## Invariants (verify against the source before relying on them)

- ERROR TYPE: rejected input raises `ValidationError` from `app/errors.py`, which subclasses
  `AppError`, the base class for every error the service raises on pur
…[1539 chars elided]…
rt from `app.<module>`. A rejection test
   should check both the `ValidationError` and that an audit record exists for the
   rejected value. `app.audit.REJECTIONS` is a module-level list that persists across tests,
   so check entries added during the call, not the list's total length.
4. Check the invariant:
   `python3 .lithify/harness/skills/input-validators/scripts/check_audit.py app/<module>.py --only <function>`
   It lists every `raise ValidationError` that is not immediately preceded by a
   `record_rejection(...)` call. Use `--only` so the legacy validators do not show up as noise.

[tool_use Bash] {"command": "git status --short && find . -path ./.git -prune -o -type f -print | grep -v '\\.venv' | head -50 && cat app/users.py app/audit.py app/errors.py 2>/dev/null", "description": "Inspect repo layout and app modules"}
[tool_result] ok./conftest.py
./README.md
./.gitignore
./AGENTS.md
./CLAUDE.md
./app/audit.py
./app/users.py
./app/__init__.py
./app/orders.py
./app/errors.py
./tests/test_users.py
./.lithify/state.json
./.lithify/library/INDEX.md
./.lithify/harness/guardrails.md
./.lithify/harness/tool_guidance.md
./.lithify/harness/memory.md
./.lithify/harness/system.md
./.agents/skills/input-validators/.lithify-managed
./.agents/skills/input-validators/SKILL.md
./.claude/skills/input-validators/.lithify-managed
./.claude/s
…[786 chars elided]…
reason)` before the error is raised, so that support can see
what users actually typed. Some older validators predate this policy and do not follow it yet.
"""

REJECTIONS: list[dict] = []


def record_rejection(field: str, value: object, reason: str) -> None:
    REJECTIONS.append({"field": field, "value": value, "reason": reason})
class AppError(Exception):
    """Base class for every error this service raises on purpose."""


class ValidationError(AppError):
    """User input was rejected."""
[tool_use Bash] {"command": "cat tests/test_users.py && cat conftest.py && cat CLAUDE.md AGENTS.md | head -80 && cat .lithify/harness/skills/input-validators/scripts/check_audit.py | head -60", "description": "Read existing tests, conftest, and audit check script"}
[tool_result] import pytest
from app.errors import ValidationError
from app.users import parse_name


def test_parse_name_strips():
    assert parse_name("  Ada Lovelace ") == "Ada Lovelace"


@pytest.mark.parametrize("bad", ["", "   ", "x" * 81, None, 42])
def test_parse_name_rejects(bad):
    with pytest.raises(ValidationError):
        parse_name(bad)
# Root conftest: puts the repository root on sys.path so tests can `import app`.
<!-- lithify:begin — managed by `lithify sync`; edit .lithify/harness/ inste
…[3874 chars elided]…
ate(block):
                if _is_validation_raise(stmt) and not (i > 0 and _is_record(block[i - 1])):
                    problems.append(stmt.lineno)
                if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    stack.append(stmt)
    return sorted(problems)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--only", nargs="+", default=None, help="function names to check")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/dom-1/app/users.py", "old_string": "from app.errors import ValidationError\n\n\ndef parse_name(value: str) -> str:", "new_string": "import re\n\nfrom app.audit import record_rejection\nfrom app.errors import ValidationError\n\n_DIGITS = re.compile(r\"[0-9]+\")\
…[503 chars elided]…
number from 0 to 150\"\n            record_rejection(\"age\", value, msg)\n            raise ValidationError(msg)\n        age = int(text)\n    else:\n        age = value\n    if not 0 <= age <= 150:\n        msg = \"age must be a whole number from 0 to 150\"\n        record_rejection(\"age\", value, msg)\n        raise ValidationError(msg)\n    return age\n\n\ndef parse_name(value: str) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/dom-1/app/users.py has been updated successfully.
[assistant] Now the tests. I'm adding them to the existing file without changing `parse_name`'s tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/dom-1/tests/test_users.py", "old_string": "import pytest\nfrom app.errors import ValidationError\nfrom app.users import parse_name\n", "new_string": "import pytest\nfrom app.audit import REJECTIONS\nfrom app.errors import ValidationError\nfrom app.users import 
…[333 chars elided]…
-1\", \"\", \"   \", \"12a\", \"1.5\", \"+5\", \"1 2\", None, 4.0, True, False, [\"3\"]],\n)\ndef test_parse_age_rejects_and_audits(bad):\n    before = len(REJECTIONS)\n    with pytest.raises(ValidationError):\n        parse_age(bad)\n    new = REJECTIONS[before:]\n    assert len(new) == 1\n    assert new[0][\"field\"] == \"age\"\n    assert new[0][\"value\"] is bad or new[0][\"value\"] == bad\n"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/dom-1/tests/test_users.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/dom-1/tests/test_users.py", "old_string": "    assert new[0][\"value\"] is bad or new[0][\"value\"] == bad", "new_string": "    assert new[0][\"value\"] == bad"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/dom-1/tests/test_users.py has been updated successfully.
[tool_use Bash] {"command": "python -m pytest -q 2>&1 | tail -20; python3 .lithify/harness/skills/input-validators/scripts/check_audit.py app/users.py --only parse_age; echo \"check exit $?\"", "description": "Run test suite and audit invariant checker"}
[tool_result] ............................                                             [100%]
28 passed in 0.01s
ok: every checked ValidationError raise is preceded by record_rejection(...)
check exit 0
[assistant] `parse_age` is added to `app/users.py`, and the full suite passes (28 tests). The audit checker also passes for `parse_age`.

**What it does**
- Accepts an `int`, or a `str` of ASCII decimal digits with optional surrounding whitespace. Returns the value as an `int`.
- Valid range is 0 to 150 inclusive.
- Rejects with `ValidationError`: non-int/non-str types, `bool`, non-digit strings (including `+5`, `1.5`, `1 2`, empty), negatives, and values over 150.
- Each rejection calls `record_rejection("age", value, msg)` first, with the raw caller value, as the project's audit invariant requires.

**C
…[98 chars elided]…
a range/format error ("age must be a whole number from 0 to 150").
- I used `re.fullmatch(r"[0-9]+")` rather than `str.isdigit()`, because `isdigit()` accepts Unicode digits like superscripts.
- I did not touch `parse_name` or `parse_quantity`. They still skip the audit call, as the task only asked for the new function.

**Tests**
Added to `tests/test_users.py` without changing the existing `parse_name` tests. They cover valid inputs (including whitespace and leading zeros), and rejections that check both the `ValidationError` and that exactly one audit record was added for the rejected value.
