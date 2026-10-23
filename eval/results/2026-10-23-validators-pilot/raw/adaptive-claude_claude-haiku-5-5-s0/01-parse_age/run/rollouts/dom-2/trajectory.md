# trajectory dom-2

final message:
I added `parse_age(value)` to `app/users.py`. The full suite passes (28 tests).

**Behaviour**
- Accepts an `int` from 0 to 150, or a string of ASCII decimal digits with optional surrounding whitespace, and returns an `int`.
- Rejects with `ValidationError` for: non-int/non-str types, booleans, non-digit strings (including signs, decimals, inner spaces and empty or whitespace-only strings), and ages outside 0–150.

**Project policy**
- Following the `input-validation` skill, every rejection goes through a small `_reject` helper that calls `record_rejection("age", <original argument>, <message>)` before raising. This is the only place `ValidationError` is raised in `parse_age`.
- I did not touch `parse_name` or `parse_quantity`, which still raise without auditing. The skill says not to retrofit them unless asked.

**Choices I made**
- Digits are matched with `[0-9]+`, not `str.isdigit()` or `isdecimal()`, so Unicode digits such as superscripts are rejected.
- Booleans are rejected explicitly, since `bool` is a subclass of `int`.
- Reject messages are `"age must be a whole number"` and `"age must be between 0 and 150"`. The second is worded to match the existing `parse_quantity` message style.

**Tests** (`tests/test_users.py`)
- Accept cases cover the bounds, a plain int, whitespace-padded strings and a leading-zero string.
- Reject cases are parametrized over all the bad inputs above. Each one checks that the audit log gained exactly one `age` entry whose `value` is the original object. A fixture clears `REJECTIONS` before and after each test.

## events
[tool_use Skill] {"skill": "input-validation"}
[tool_result] Launching skill: input-validation
[user] Base directory for this skill: ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/dom-2/.claude/skills/input-validation

# Input validators in this repository

## Modules that own the concerns
- `app/errors.py`: `ValidationError(AppError)` is the only error a validator raises for bad input.
  Do not raise `ValueError`/`TypeError` or define new exception classes.
- `app/audit.py`: `record_rejection(field: str, value: object, reason: str)` appends to the
  module-level list `REJECTIONS`. Its docstring is the policy: every rejected piece of user 
…[1467 chars elided]…
 validator touches
1. The domain module in `app/` — validator calls `record_rejection` then raises `ValidationError`
   on every rejecting branch.
2. `tests/test_<module>.py` — import the validator into the existing import line; add
   accept/reject cases. For rejections, also assert that `app.audit.REJECTIONS` gained an entry
   whose `value` is the original input (clear the list first, it is module-global state).

Check before finishing: in the changed function, count `raise ValidationError` sites and confirm
each one is reached only after a `record_rejection` call with the raw input value.

[tool_use Bash] {"command": "ls -R app tests 2>/dev/null | head -50 && cat app/users.py app/errors.py app/audit.py", "description": "List project files and read core modules"}
[tool_result] __init__.py  0B
audit.py  473B
errors.py  166B
orders.py  385B
users.py  384B
test_users.py  343B
from app.errors import ValidationError


def parse_name(value: str) -> str:
    """Return a display name: surrounding whitespace removed, 1-80 characters."""
    if not isinstance(value, str):
        raise ValidationError("name must be a string")
    name = value.strip()
    if not 1 <= len(name) <= 80:
        raise ValidationError("name must be 1-80 characters")
    return name
class AppError(Exc
…[120 chars elided]…
User input was rejected."""
"""Audit trail for rejected user input.

Policy: every rejected piece of user input must be recorded with
`record_rejection(field, value, reason)` before the error is raised, so that support can see
what users actually typed. Some older validators predate this policy and do not follow it yet.
"""

REJECTIONS: list[dict] = []


def record_rejection(field: str, value: object, reason: str) -> None:
    REJECTIONS.append({"field": field, "value": value, "reason": reason})
[tool_use Bash] {"command": "cat tests/test_users.py && cat app/orders.py && git status --short", "description": "Read existing user tests and orders module"}
[tool_result] import pytest
from app.errors import ValidationError
from app.users import parse_name


def test_parse_name_strips():
    assert parse_name("  Ada Lovelace ") == "Ada Lovelace"


@pytest.mark.parametrize("bad", ["", "   ", "x" * 81, None, 42])
def test_parse_name_rejects(bad):
    with pytest.raises(ValidationError):
        parse_name(bad)
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
ok
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/dom-2/app/users.py", "old_string": "from app.errors import ValidationError\n\n\ndef parse_name(value: str) -> str:", "new_string": "import re\nfrom typing import NoReturn\n\nfrom app.audit import record_rejection\nfrom app.errors import ValidationError\n\n_DIGITS = re.compile(r\"[0-9]+\")\n\n\ndef _reject(field: str, value: object, reason: str) -> NoReturn:\n    record_rejection(field, value, reason)\n    raise ValidationError(reason)\n\n\ndef parse_name(value: str) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/dom-2/app/users.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/dom-2/app/users.py", "old_string": "    if not 1 <= len(name) <= 80:\n        raise ValidationError(\"name must be 1-80 characters\")\n    return name", "new_string": "    if not 1 <= len(name) <= 80:\n        raise ValidationError(\"name must be 1-80 character
…[231 chars elided]…
 _reject(\"age\", value, \"age must be a whole number\")\n    if isinstance(value, int):\n        age = value\n    else:\n        text = value.strip()\n        if not _DIGITS.fullmatch(text):\n            _reject(\"age\", value, \"age must be a whole number\")\n        age = int(text)\n    if not 0 <= age <= 150:\n        _reject(\"age\", value, \"age must be between 0 and 150\")\n    return age"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/dom-2/app/users.py has been updated successfully.
[assistant] Now the tests: accept cases, reject cases, and an audit check for each rejection.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/dom-2/tests/test_users.py", "old_string": "import pytest\nfrom app.errors import ValidationError\nfrom app.users import parse_name\n", "new_string": "import pytest\nfrom app import audit\nfrom app.errors import ValidationError\nfrom app.users import parse_age, parse_name\n"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/dom-2/tests/test_users.py has been updated successfully.
[tool_use Bash] {"command": "cat >> tests/test_users.py <<'EOF'\n\n\n@pytest.fixture\ndef clear_rejections():\n    audit.REJECTIONS.clear()\n    yield\n    audit.REJECTIONS.clear()\n\n\n@pytest.mark.parametrize(\n    \"good, expected\",\n    [(0, 0), (150, 150), (42, 42), (\"0\", 0), (\"150\", 150), (\"  37\\t\", 37), (\"007\", 7)],\n)\ndef test_parse_age_accepts(good, expected):\n    assert parse_age(good) == ex
…[189 chars elided]…
ejects(bad, clear_rejections):\n    with pytest.raises(ValidationError):\n        parse_age(bad)\n    assert len(audit.REJECTIONS) == 1\n    assert audit.REJECTIONS[0][\"field\"] == \"age\"\n    assert audit.REJECTIONS[0][\"value\"] is bad\nEOF\npython -m pytest -q 2>&1 | tail -20", "description": "Append parse_age tests and run pytest"}
[tool_result] ............................                                             [100%]
28 passed in 0.01s
[tool_use Bash] {"command": "git diff --stat && head -5 tests/test_users.py && python -m pytest -q 2>&1 | tail -2", "description": "Check diff stat, test file header, and rerun tests"}
[tool_result] app/users.py        | 27 +++++++++++++++++++++++++++
 tests/test_users.py | 30 +++++++++++++++++++++++++++++-
 2 files changed, 56 insertions(+), 1 deletion(-)
import pytest
from app import audit
from app.errors import ValidationError
from app.users import parse_age, parse_name
[37 more lines]............................                                             [100%]
28 passed in 0.01s
[assistant] I added `parse_age(value)` to `app/users.py`. The full suite passes (28 tests).

**Behaviour**
- Accepts an `int` from 0 to 150, or a string of ASCII decimal digits with optional surrounding whitespace, and returns an `int`.
- Rejects with `ValidationError` for: non-int/non-str types, booleans, non-digit strings (including signs, decimals, inner spaces and empty or whitespace-only strings), and ages outside 0–150.

**Project policy**
- Following the `input-validation` skill, every rejection goes through a small `_reject` helper that calls `record_rejection("age", <original argument>, <message>
…[369 chars elided]…
.
- Booleans are rejected explicitly, since `bool` is a subclass of `int`.
- Reject messages are `"age must be a whole number"` and `"age must be between 0 and 150"`. The second is worded to match the existing `parse_quantity` message style.

**Tests** (`tests/test_users.py`)
- Accept cases cover the bounds, a plain int, whitespace-padded strings and a leading-zero string.
- Reject cases are parametrized over all the bad inputs above. Each one checks that the audit log gained exactly one `age` entry whose `value` is the original object. A fixture clears `REJECTIONS` before and after each test.
