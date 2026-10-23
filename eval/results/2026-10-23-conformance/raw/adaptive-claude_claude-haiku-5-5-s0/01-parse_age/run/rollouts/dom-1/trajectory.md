# trajectory dom-1

final message:
I added `parse_age(value)` to `app/users.py`, with tests in `tests/test_users.py`. The full suite passes (28 tests), and the audit check reports every `ValidationError` raise in `parse_age` as recorded.

**Behaviour**
- An `int` (not `bool`) is range-checked directly.
- A `str` is stripped of surrounding whitespace, then must match `[0-9]+` exactly. This rejects signs, decimals, and inner spaces, and it avoids `str.isdigit()`, which accepts non-ASCII digits.
- Everything else is rejected with `ValidationError`, including `bool`, floats, `None`, lists, and empty or whitespace-only strings.
- Ages outside 0–150 are rejected.

**Audit policy**
Every reject branch calls `record_rejection("age", value, reason)` before raising. The recorded value is the original input, captured before any stripping. Accepted inputs record nothing. I followed the input-validation skill rather than the legacy `parse_name` and `parse_quantity` reject paths, which skip the audit.

**Choices I made**
- Leading zeros such as `"007"` are accepted as 7, since the spec only asks for decimal digits.
- The reject reason is one shared message for all type and format failures, so the error text doesn't reveal which check failed.

## events
[tool_use Bash] {"command": "cat app/users.py; echo ---; cat app/audit.py; echo ---; ls app tests 2>/dev/null; echo ---; cat app/orders.py | head -80", "description": "Read users, audit, and orders modules"}
[tool_use Skill] {"skill": "input-validation"}
[tool_result] from app.errors import ValidationError


def parse_name(value: str) -> str:
    """Return a display name: surrounding whitespace removed, 1-80 characters."""
    if not isinstance(value, str):
        raise ValidationError("name must be a string")
    name = value.strip()
    if not 1 <= len(name) <= 80:
        raise ValidationError("name must be 1-80 characters")
    return name
---
"""Audit trail for rejected user input.

Policy: every rejected piece of user input must be recorded with
`recor
…[351 chars elided]…
 reason})
---
__init__.py  0B
audit.py  473B
errors.py  166B
orders.py  385B
users.py  384B
test_users.py  344B
---
from app.errors import ValidationError


def parse_quantity(value) -> int:
    """Return an order quantity between 1 and 999."""
    try:
        qty = int(value)
    except (TypeError, ValueError):
        raise ValidationError("quantity must be a whole number") from None
    if not 1 <= qty <= 999:
        raise ValidationError("quantity must be between 1 and 999")
    return qty
[tool_result] Launching skill: input-validation
[user] Base directory for this skill: ~/.cache/lithify/work/repo-fe47fc05e48d/20261023-124909-add-parse-age-value-to-app-users/dom-1/.claude/skills/input-validation

# Input validation in this repository

## INVARIANT: every rejection is audited before it is raised
- Source of truth: the docstring of `app/audit.py`. Every rejected piece of user input must be
  recorded with `record_rejection(field, value, reason)` **before** the `ValidationError` is
  raised. `record_rejection` appends `{"field", "value", "reason"}` to `app.audit.REJECTIONS`.
- Errors: raise `ValidationError` from `app/e
…[1409 chars elided]…
  rejection appended a record with the right field and the raw value. `REJECTIONS` is a
   module-level list shared across tests, so compare length before/after or clear it first
   (e.g. `REJECTIONS.clear()`), and assert accepted inputs add no record.

## Check
Run `python3 .lithify/harness/skills/input-validation/scripts/check_audit.py app --func <name>`
to list `raise ValidationError` statements in the named function(s) that are not directly
preceded by a `record_rejection(...)` call. Without `--func` it reports every function, so the
legacy validators above will show up; that is expected.

[tool_use Bash] {"command": "cat app/errors.py; echo ---; cat tests/test_users.py; echo ---; ls -a; ls .lithify/harness/skills/input-validation/scripts 2>&1", "description": "Read errors module, existing tests, and check script location"}
[tool_result] class AppError(Exception):
    """Base class for every error this service raises on purpose."""


class ValidationError(AppError):
    """User input was rejected."""
---
import pytest

from app.errors import ValidationError
from app.users import parse_name


def test_parse_name_strips():
    assert parse_name("  Ada Lovelace ") == "Ada Lovelace"


@pytest.mark.parametrize("bad", ["", "   ", "x" * 81, None, 42])
def test_parse_name_rejects(bad):
    with pytest.raises(ValidationError):
        parse_name(bad)
---
.agents/
.claude/
.lithify/
app/
tests/
.git  113B
.gitignore  105B
AGENTS.md  1.2K
CLAUDE.md  1.2K
README.md  103B
conftest.py  81B
check_audit.py  2.4K
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fe47fc05e48d/20261023-124909-add-parse-age-value-to-app-users/dom-1/app/users.py", "old_string": "from app.errors import ValidationError\n\n\ndef parse_name", "new_string": "import re\n\nfrom app.audit import record_rejection\nfrom app.errors import ValidationError\n\n_DIGITS = re.compile(r\"[0-9]+\")\n\n\ndef parse_age(v
…[392 chars elided]…
trip()):\n        age = int(value.strip())\n    else:\n        record_rejection(\"age\", value, \"age must be a whole number\")\n        raise ValidationError(\"age must be a whole number\")\n    if not 0 <= age <= 150:\n        record_rejection(\"age\", value, \"age must be between 0 and 150\")\n        raise ValidationError(\"age must be between 0 and 150\")\n    return age\n\n\ndef parse_name"}
[tool_result] The file ~/.cache/lithify/work/repo-fe47fc05e48d/20261023-124909-add-parse-age-value-to-app-users/dom-1/app/users.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fe47fc05e48d/20261023-124909-add-parse-age-value-to-app-users/dom-1/tests/test_users.py", "old_string": "import pytest\n\nfrom app.errors import ValidationError\nfrom app.users import parse_name\n\n\ndef test_parse_name_strips():\n    assert parse_name(\"  Ada Lovelace \") == \"Ada Lovelace\"\n\n\n@pytest.mark.parametrize
…[929 chars elided]…
 [-1, 151, \"-1\", \"151\", \"abc\", \"\", \"   \", \"1.5\", \"+5\", \"1 2\", None, 3.0, True, False, [\"1\"]],\n)\ndef test_parse_age_rejects(bad):\n    REJECTIONS.clear()\n    with pytest.raises(ValidationError):\n        parse_age(bad)\n    assert len(REJECTIONS) == 1\n    assert REJECTIONS[0][\"field\"] == \"age\"\n    assert REJECTIONS[0][\"value\"] is bad or REJECTIONS[0][\"value\"] == bad"}
[tool_result] The file ~/.cache/lithify/work/repo-fe47fc05e48d/20261023-124909-add-parse-age-value-to-app-users/dom-1/tests/test_users.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fe47fc05e48d/20261023-124909-add-parse-age-value-to-app-users/dom-1/tests/test_users.py", "old_string": "    assert REJECTIONS[0][\"value\"] is bad or REJECTIONS[0][\"value\"] == bad", "new_string": "    assert REJECTIONS[0][\"value\"] == bad"}
[tool_result] The file ~/.cache/lithify/work/repo-fe47fc05e48d/20261023-124909-add-parse-age-value-to-app-users/dom-1/tests/test_users.py has been updated successfully.
[tool_use Bash] {"command": "python -m pytest -q 2>&1 | tail -15; echo ---; python3 .lithify/harness/skills/input-validation/scripts/check_audit.py app --func parse_age", "description": "Run test suite and audit check for parse_age"}
[tool_result] ............................                                             [100%]
28 passed in 0.01s
---
ok: every selected ValidationError raise is audited
[assistant] I added `parse_age(value)` to `app/users.py`, with tests in `tests/test_users.py`. The full suite passes (28 tests), and the audit check reports every `ValidationError` raise in `parse_age` as recorded.

**Behaviour**
- An `int` (not `bool`) is range-checked directly.
- A `str` is stripped of surrounding whitespace, then must match `[0-9]+` exactly. This rejects signs, decimals, and inner spaces, and it avoids `str.isdigit()`, which accepts non-ASCII digits.
- Everything else is rejected with `ValidationError`, including `bool`, floats, `None`, lists, and empty or whitespace-only strings.
- Ag
…[12 chars elided]…
–150 are rejected.

**Audit policy**
Every reject branch calls `record_rejection("age", value, reason)` before raising. The recorded value is the original input, captured before any stripping. Accepted inputs record nothing. I followed the input-validation skill rather than the legacy `parse_name` and `parse_quantity` reject paths, which skip the audit.

**Choices I made**
- Leading zeros such as `"007"` are accepted as 7, since the spec only asks for decimal digits.
- The reject reason is one shared message for all type and format failures, so the error text doesn't reveal which check failed.
