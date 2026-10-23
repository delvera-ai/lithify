# trajectory base-1

final message:
`parse_username(value)` is added to `app/users.py`, with tests in `tests/test_users.py`. The full suite passes (94 tests) and the audit checker reports every `ValidationError` raise is preceded by `record_rejection`.

**Behaviour**
- Non-string input raises `ValidationError("username must be a string")`.
- Otherwise it strips surrounding whitespace and fullmatches `[a-z][a-z0-9_]{2,19}`. Anything else raises `ValidationError` with a message describing the rule.
- Every rejection is recorded with `record_rejection("username", value, reason)` before the raise. `value` is the original argument, not the stripped one.
- I read the spec as lowercase ASCII only, so `"Ada"` is rejected rather than lowercased. The regex uses an explicit `[a-z]` range, not `\w` or `\d`, so non-ASCII letters and digits are rejected too.

**Choices I made**
- The pattern is a module-level compiled regex, `USERNAME_PATTERN`, placed next to the imports.
- The new function is appended after `parse_phone`.
- I did not change `parse_name`, `parse_quantity` or the existing tests.

**Test notes**
- My first draft had `"  Ada  "` as an accept case. That was wrong against the lowercase-only rule, and the test failed. I changed it to `"  ada  "` and added `"Ada"` to the reject cases.
- The accept cases cover whitespace stripping, the 3-character and 20-character boundaries, underscores and digits. The reject cases cover length, a leading digit or underscore, hyphens, spaces, non-ASCII letters and digits, and non-string types. Each reject case checks that the audit entry's `field`, `value` and `reason` are correct.

I did not commit anything.

## events
[tool_use Bash] {"command": "ls -la app tests && cat README.md && cat app/users.py app/audit.py app/errors.py", "description": "List app and tests, show README and core modules"}
[tool_use Skill] {"skill": "input-validation"}
[tool_result] __init__.py  0B
audit.py  473B
errors.py  166B
orders.py  385B
users.py  3.1K
test_users.py  3.4K
# accounts service

Input parsing for the accounts service. Run the tests with `python3 -m pytest -q`.
from app.audit import record_rejection
from app.errors import ValidationError


def parse_name(value: str) -> str:
    """Return a display name: surrounding whitespace removed, 1-80 characters."""
    if not isinstance(value, str):
        raise ValidationError("name must be a string")
    name = v
…[2964 chars elided]…
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
[tool_result] Launching skill: input-validation
[user] Base directory for this skill: ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130952-add-parse-username-value-to-app/base-1/.claude/skills/input-validation

# Input validators in this repository

## Modules that own the concerns
- `app/errors.py`: `ValidationError(AppError)` is the error a validator raises for bad input.
  Do not raise `ValueError`/`TypeError` or define new exception classes for input rejection.
- `app/audit.py`: `record_rejection(field: str, value: object, reason: str)` appends a dict
  (`field`, `value`, `reason`) to the module-level list `REJECTIONS`. Its doc
…[1676 chars elided]…
t line; add accept/reject
   cases. Rejection tests also check that `app.audit.REJECTIONS` gained an entry whose `value` is
   the original input. `REJECTIONS` is module-global and persists across tests, so compare
   entries added by the call (or clear it in a fixture), not the total length.
3. Check the invariant (AST-based; flags any `raise ValidationError` not directly preceded by
   `record_rejection(...)`; `--only` keeps the legacy validators out of the output):
   `<python from memory.md> .lithify/harness/skills/input-validation/scripts/check_audit.py app/<module>.py --only <function>`

[tool_use Bash] {"command": "cat tests/test_users.py; echo ---; cat app/orders.py; echo ---; ls -la .lithify/harness/skills/input-validation/scripts/ 2>&1; ls python 2>&1", "description": "Show existing tests, orders module, and checker script paths"}
[tool_result] import pytest
from app.audit import REJECTIONS
from app.errors import ValidationError
from app.users import parse_age, parse_email, parse_name, parse_phone


def test_parse_name_strips():
    assert parse_name("  Ada Lovelace ") == "Ada Lovelace"


@pytest.mark.parametrize("bad", ["", "   ", "x" * 81, None, 42])
def test_parse_name_rejects(bad):
    with pytest.raises(ValidationError):
        parse_name(bad)


@pytest.mark.parametrize(
    "good, expected",
    [(0, 0), (42, 42), (150, 150), ("
…[3101 chars elided]…
int:
    """Return an order quantity between 1 and 999."""
    try:
        qty = int(value)
    except (TypeError, ValueError):
        raise ValidationError("quantity must be a whole number") from None
    if not 1 <= qty <= 999:
        raise ValidationError("quantity must be between 1 and 999")
    return qty
---
check_audit.py  2.6K
python -> ~/.local/share/uv/python/cpython-3.14-macos-aarch64-none/bin/python3.14  84B
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130952-add-parse-username-value-to-app/base-1/app/users.py", "old_string": "    if not (digits.isascii() and digits.isdigit() and 7 <= len(digits) <= 15):\n        record_rejection(\"phone\", value, \"phone must be 7-15 digits with an optional leading +\")\n        raise ValidationError(\"phone must 
…[711 chars elided]…
or(\"username must be a string\")\n    username = value.strip()\n    if not USERNAME_PATTERN.fullmatch(username):\n        record_rejection(\"username\", value, \"username must be 3-20 lowercase letters, digits or underscores, starting with a letter\")\n        raise ValidationError(\"username must be 3-20 lowercase letters, digits or underscores, starting with a letter\")\n    return username\n"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130952-add-parse-username-value-to-app/base-1/app/users.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130952-add-parse-username-value-to-app/base-1/app/users.py", "old_string": "from app.audit import record_rejection\nfrom app.errors import ValidationError\n", "new_string": "import re\n\nfrom app.audit import record_rejection\nfrom app.errors import ValidationError\n\nUSERNAME_PATTERN = re.compile(r\"[a-z][a-z0-9_]{2,19}\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130952-add-parse-username-value-to-app/base-1/app/users.py has been updated successfully.
[assistant] Now the tests: add the import and accept/reject cases, leaving the existing tests untouched.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130952-add-parse-username-value-to-app/base-1/tests/test_users.py", "old_string": "from app.users import parse_age, parse_email, parse_name, parse_phone", "new_string": "from app.users import parse_age, parse_email, parse_name, parse_phone, parse_username"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130952-add-parse-username-value-to-app/base-1/tests/test_users.py has been updated successfully.
[tool_use Bash] {"command": "cat >> tests/test_users.py <<'EOF'\n\n\n@pytest.mark.parametrize(\n    \"good, expected\",\n    [\n        (\"abc\", \"abc\"),\n        (\"ada_lovelace\", \"ada_lovelace\"),\n        (\"  Ada  \", \"Ada\"),\n        (\"\\tuser42\\n\", \"user42\"),\n        (\"a\" * 20, \"a\" * 20),\n        (\"a\" + \"9\" * 19, \"a\" + \"9\" * 19),\n    ],\n)\ndef test_parse_username_accepts(good, exp
…[823 chars elided]…
xcinfo.value)\nEOF\npython -m pytest -q 2>&1 | tail -15; echo \"---checker\"; python .lithify/harness/skills/input-validation/scripts/check_audit.py app/users.py --only parse_username 2>&1; echo \"exit $?\"", "description": "Run test suite and audit checker for parse_username"}
[tool_result]     def parse_username(value) -> str:
        """Return a username: surrounding whitespace removed, 3-20 characters of lowercase ASCII letters, digits and underscores, starting with a letter."""
        if not isinstance(value, str):
            record_rejection("username", value, "username must be a string")
            raise ValidationError("username must be a string")
        username = value.strip()
        if not USERNAME_PATTERN.fullmatch(username):
            record_rejection("username",
…[168 chars elided]…
ters, digits or underscores, starting with a letter")
E           app.errors.ValidationError: username must be 3-20 lowercase letters, digits or underscores, starting with a letter

app/users.py:81: ValidationError
=========================== short test summary info ============================
FAILED tests/test_users.py::test_parse_username_accepts[  Ada  -Ada] - app.er...
1 failed, 92 passed in 0.03s
---checker
ok: every checked ValidationError raise is preceded by record_rejection(...)
exit 0
[assistant] The one failure is a mistake in my test, not the code. I wrote `"  Ada  "` as an accept case, but the spec allows only lowercase letters, so `Ada` is correctly rejected. I'll fix the case to `"  ada  "` and add an uppercase reject case.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130952-add-parse-username-value-to-app/base-1/tests/test_users.py", "old_string": "        (\"  Ada  \", \"Ada\"),", "new_string": "        (\"  ada  \", \"ada\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130952-add-parse-username-value-to-app/base-1/tests/test_users.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130952-add-parse-username-value-to-app/base-1/tests/test_users.py", "old_string": "        \"ab c\",\n        \"abc\\n\\nx\",", "new_string": "        \"ab c\",\n        \"Ada\",  # uppercase is not allowed\n        \"abc\\n\\nx\","}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130952-add-parse-username-value-to-app/base-1/tests/test_users.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "python -m pytest -q 2>&1 | tail -3; echo \"---checker\"; python .lithify/harness/skills/input-validation/scripts/check_audit.py app/users.py --only parse_username 2>&1; echo \"exit $?\"; echo \"---direct calls\"; ~/Coding/delvera/foundational/lithify/.
…[39 chars elided]…
port parse_username\nfrom app.errors import ValidationError\nfor v in [\"  ada_99 \", \"Ada\", \"ab\", \"1abc\", \"abc_def_ghi_jkl_mno_pq\", None]:\n    try:\n        print(repr(v), \"->\", repr(parse_username(v)))\n    except ValidationError as e:\n        print(repr(v), \"-> ValidationError:\", e)\n'; git status --short", "description": "Rerun tests, audit checker, direct calls, and git status"}
[tool_result] ........................................................................ [ 76%]
......................                                                   [100%]
94 passed in 0.02s
---checker
ok: every checked ValidationError raise is preceded by record_rejection(...)
exit 0
---direct calls
'  ada_99 ' -> 'ada_99'
'Ada' -> ValidationError: username must be 3-20 lowercase letters, digits or underscores, starting with a letter
'ab' -> ValidationError: username must be 3-20 lowercase letters, digits or underscores, starting with a letter
'1abc' -> ValidationError: username must be 3-20 lowercase letters, digits or underscores, starting with a letter
'abc_def_ghi_jkl_mno_pq' -> ValidationError: username must be 3-20 lowercase letters, digits or underscores, starting with a letter
None -> ValidationError: username must be a string
 M app/users.py
 M tests/test_users.py
[assistant] `parse_username(value)` is added to `app/users.py`, with tests in `tests/test_users.py`. The full suite passes (94 tests) and the audit checker reports every `ValidationError` raise is preceded by `record_rejection`.

**Behaviour**
- Non-string input raises `ValidationError("username must be a string")`.
- Otherwise it strips surrounding whitespace and fullmatches `[a-z][a-z0-9_]{2,19}`. Anything else raises `ValidationError` with a message describing the rule.
- Every rejection is recorded with `record_rejection("username", value, reason)` before the raise. `value` is the original argument, n
…[430 chars elided]…
uantity` or the existing tests.

**Test notes**
- My first draft had `"  Ada  "` as an accept case. That was wrong against the lowercase-only rule, and the test failed. I changed it to `"  ada  "` and added `"Ada"` to the reject cases.
- The accept cases cover whitespace stripping, the 3-character and 20-character boundaries, underscores and digits. The reject cases cover length, a leading digit or underscore, hyphens, spaces, non-ASCII letters and digits, and non-string types. Each reject case checks that the audit entry's `field`, `value` and `reason` are correct.

I did not commit anything.
