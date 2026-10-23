# trajectory comp-1

final message:
`parse_age(value)` is added to `app/users.py`. The project's test suite passes (30 tests) and the audit checker reports every `ValidationError` raise in `parse_age` is audited.

**Behavior**
- Accepts ints and strings of ASCII decimal digits, with surrounding whitespace stripped. Valid ages are 0–150 inclusive.
- Rejects `bool` (including `True`/`False`), floats, `None`, and other types.
- Rejects non-digit strings, signed strings like `"-1"` and `"+5"`, decimals, exponents, empty or whitespace-only strings, and anything out of range.
- Every rejection calls `record_rejection("age", <original value>, reason)` before raising `ValidationError`. Accepted inputs record nothing.

**Choices I made**
- I used `str.isascii()` together with `isdigit()`, because `isdigit()` alone accepts non-ASCII digits such as Arabic-Indic `"٤٢"`.
- I inlined each `record_rejection` call directly before its `raise` instead of using a helper. That keeps the checker's per-raise check meaningful.
- Strings like `"007"` are accepted and return `7`.

**Tests** (added to `tests/test_users.py`; existing tests untouched)
- An accept test covering boundaries, string and int forms, and whitespace, asserting no audit record is written.
- A reject test covering the cases above, asserting exactly one audit record with field `"age"` and the raw value.

I didn't touch the legacy `parse_name` and `parse_quantity` reject paths, which don't audit.

## events
[assistant] I'll load the project's `input-validation` skill first, since this adds a parser, then read the relevant modules.
[tool_use Skill] {"skill": "input-validation"}
[tool_result] Launching skill: input-validation
[user] Base directory for this skill: ~/.cache/lithify/work/repo-fe47fc05e48d/20261023-124909-add-parse-age-value-to-app-users/comp-1/.claude/skills/input-validation

# Input validation in this repository

## INVARIANT: every rejection is audited before it is raised
- Source of truth: the docstring of `app/audit.py`. Every rejected piece of user input must be
  recorded with `record_rejection(field, value, reason)` **before** the `ValidationError` is
  raised. `record_rejection` appends `{"field", "value", "reason"}` to `app.audit.REJECTIONS`.
- Errors: raise `ValidationError` from `app/
…[1410 chars elided]…
  rejection appended a record with the right field and the raw value. `REJECTIONS` is a
   module-level list shared across tests, so compare length before/after or clear it first
   (e.g. `REJECTIONS.clear()`), and assert accepted inputs add no record.

## Check
Run `python3 .lithify/harness/skills/input-validation/scripts/check_audit.py app --func <name>`
to list `raise ValidationError` statements in the named function(s) that are not directly
preceded by a `record_rejection(...)` call. Without `--func` it reports every function, so the
legacy validators above will show up; that is expected.

[tool_use Bash] {"command": "ls app tests 2>/dev/null; git status --short; echo ---; cat app/users.py; echo ---; cat app/audit.py", "description": "List app and tests, show status, read users.py and audit.py"}
[tool_result] __init__.py  0B
audit.py  473B
errors.py  166B
orders.py  385B
users.py  384B
test_users.py  344B
ok---
from app.errors import ValidationError


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
`record_rejection(field, value, reason)` before the error is raised, so that support can see
what users actually typed. Some older validators predate this policy and do not follow it yet.
"""

REJECTIONS: list[dict] = []


def record_rejection(field: str, value: object, reason: str) -> None:
    REJECTIONS.append({"field": field, "value": value, "reason": reason})
[assistant] The skill confirms the pattern: call `record_rejection(field, raw_value, reason)` before each `raise ValidationError`, and add tests that check the audit record. Next I'll read the existing tests, errors, and the check script.
[tool_use Bash] {"command": "cat app/errors.py; echo ---; cat tests/test_users.py; echo ---; ls .lithify/harness/skills/input-validation/scripts/ 2>&1; echo ---; cat app/orders.py", "description": "Read errors, existing user tests, check script location, and orders.py"}
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
check_audit.py  2.4K
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
[assistant] I have what I need. Plan:

- `parse_age` in `app/users.py`: reject `bool` and non-int/str types, require ASCII digits for strings (so `isdigit()` doesn't accept Unicode digits such as Arabic-Indic), strip surrounding whitespace, then check 0–150.
- Every reject branch calls `record_rejection("age", <raw value>, reason)` before raising. I'm inlining the calls rather than using a helper so each `raise` sits directly after its record, which keeps the audit checker meaningful.
- Add tests to `tests/test_users.py` without changing the existing ones.

I'll make the edits now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fe47fc05e48d/20261023-124909-add-parse-age-value-to-app-users/comp-1/app/users.py", "old_string": "from app.errors import ValidationError\n", "new_string": "from app.audit import record_rejection\nfrom app.errors import ValidationError\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fe47fc05e48d/20261023-124909-add-parse-age-value-to-app-users/comp-1/app/users.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fe47fc05e48d/20261023-124909-add-parse-age-value-to-app-users/comp-1/app/users.py", "old_string": "    if not 1 <= len(name) <= 80:\n        raise ValidationError(\"name must be 1-80 characters\")\n    return name\n", "new_string": "    if not 1 <= len(name) <= 80:\n        raise ValidationError(\"name must be 1-80 charac
…[530 chars elided]…
     if not (text.isascii() and text.isdigit()):\n            record_rejection(\"age\", value, not_whole)\n            raise ValidationError(not_whole)\n        age = int(text)\n    else:\n        age = value\n    if not 0 <= age <= 150:\n        record_rejection(\"age\", value, \"age must be between 0 and 150\")\n        raise ValidationError(\"age must be between 0 and 150\")\n    return age\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fe47fc05e48d/20261023-124909-add-parse-age-value-to-app-users/comp-1/app/users.py has been updated successfully.
[assistant] Next, the tests. I'm appending new ones and leaving the existing `parse_name` tests unchanged.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fe47fc05e48d/20261023-124909-add-parse-age-value-to-app-users/comp-1/tests/test_users.py", "old_string": "import pytest\n\nfrom app.errors import ValidationError\nfrom app.users import parse_name\n", "new_string": "import pytest\n\nfrom app.audit import REJECTIONS\nfrom app.errors import ValidationError\nfrom app.users import parse_age, parse_name\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fe47fc05e48d/20261023-124909-add-parse-age-value-to-app-users/comp-1/tests/test_users.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fe47fc05e48d/20261023-124909-add-parse-age-value-to-app-users/comp-1/tests/test_users.py", "old_string": "@pytest.mark.parametrize(\"bad\", [\"\", \"   \", \"x\" * 81, None, 42])\ndef test_parse_name_rejects(bad):\n    with pytest.raises(ValidationError):\n        parse_name(bad)\n", "new_string": "@pytest.mark.parametriz
…[800 chars elided]…
  4.5,\n        None,\n        True,\n        False,\n    ],\n)\ndef test_parse_age_rejects_and_audits(bad):\n    REJECTIONS.clear()\n    with pytest.raises(ValidationError):\n        parse_age(bad)\n    assert len(REJECTIONS) == 1\n    assert REJECTIONS[0][\"field\"] == \"age\"\n    assert REJECTIONS[0][\"value\"] is bad or REJECTIONS[0][\"value\"] == bad\n    assert REJECTIONS[0][\"reason\"]\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fe47fc05e48d/20261023-124909-add-parse-age-value-to-app-users/comp-1/tests/test_users.py has been updated successfully.
[assistant] The `is bad or ==` assertion is looser than it should be. Since the same object is passed in and recorded, an identity check is exact, so I'll tighten it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fe47fc05e48d/20261023-124909-add-parse-age-value-to-app-users/comp-1/tests/test_users.py", "old_string": "    assert REJECTIONS[0][\"value\"] is bad or REJECTIONS[0][\"value\"] == bad\n", "new_string": "    assert REJECTIONS[0][\"value\"] is bad\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fe47fc05e48d/20261023-124909-add-parse-age-value-to-app-users/comp-1/tests/test_users.py has been updated successfully.
[assistant] Now I'll run the project checks as a separate step, plus the audit checker the skill describes.
[tool_use Bash] {"command": "python -m pytest -q 2>&1 | tail -30", "description": "Run project test suite with project venv"}
[tool_use Bash] {"command": "python3 .lithify/harness/skills/input-validation/scripts/check_audit.py app --func parse_age; echo \"exit=$?\"", "description": "Run audit checker on parse_age"}
[tool_result] ..............................                                           [100%]
30 passed in 0.01s
[tool_result] ok: every selected ValidationError raise is audited
exit=0
[assistant] `parse_age(value)` is added to `app/users.py`. The project's test suite passes (30 tests) and the audit checker reports every `ValidationError` raise in `parse_age` is audited.

**Behavior**
- Accepts ints and strings of ASCII decimal digits, with surrounding whitespace stripped. Valid ages are 0–150 inclusive.
- Rejects `bool` (including `True`/`False`), floats, `None`, and other types.
- Rejects non-digit strings, signed strings like `"-1"` and `"+5"`, decimals, exponents, empty or whitespace-only strings, and anything out of range.
- Every rejection calls `record_rejection("age", <original 
…[228 chars elided]…
"٤٢"`.
- I inlined each `record_rejection` call directly before its `raise` instead of using a helper. That keeps the checker's per-raise check meaningful.
- Strings like `"007"` are accepted and return `7`.

**Tests** (added to `tests/test_users.py`; existing tests untouched)
- An accept test covering boundaries, string and int forms, and whitespace, asserting no audit record is written.
- A reject test covering the cases above, asserting exactly one audit record with field `"age"` and the raw value.

I didn't touch the legacy `parse_name` and `parse_quantity` reject paths, which don't audit.
