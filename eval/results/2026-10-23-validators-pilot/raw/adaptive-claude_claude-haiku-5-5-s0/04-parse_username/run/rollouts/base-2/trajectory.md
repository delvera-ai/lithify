# trajectory base-2

final message:
I added `parse_username(value)` to `app/users.py`. The full suite passes (93 tests) and the audit check reports no unrecorded rejections in the new function.

- **Behaviour:** it strips surrounding whitespace, then accepts only 3–20 characters matching `[a-z][a-z0-9_]{2,19}`. Anything else raises `ValidationError`, and non-strings are rejected with "username must be a string".
- **Audit:** every rejection calls `record_rejection("username", value, reason)` first, with the original argument and the same text as the error message. The project's input-validation rule requires this.
- **Tests:** I added accept and reject cases to `tests/test_users.py`, following the existing `parse_email`/`parse_phone` test pattern. The rejection tests also check the audit entry. I did not edit any existing tests.
- **Direct calls:** `'  ada_99  '` returns `'ada_99'`, `'ab_'` returns `'ab_'`, and `'Ada'`, `'a'`, a 21-character string and `1` each raise and are audited.

One of my own new test cases initially used `"  Ada  "`, which my check had wrongly treated as valid. Uppercase is rejected, so I changed that case to `"  ada  "`. The code was right, and the test case was my error.

## events
[tool_use Bash] {"command": "ls -la app tests; cat README.md; cat app/users.py app/audit.py app/errors.py; cat app/orders.py | head -80", "description": "List app and tests, read README and core modules"}
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
…[3349 chars elided]…
very error this service raises on purpose."""


class ValidationError(AppError):
    """User input was rejected."""
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
[user] Base directory for this skill: ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130952-add-parse-username-value-to-app/base-2/.claude/skills/input-validation

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

[tool_use Bash] {"command": "cat tests/test_users.py; ls -la .lithify/harness/skills/input-validation/scripts/ 2>&1; git status --short", "description": "Read existing user tests and check audit script exists"}
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
…[2550 chars elided]…
        "555.0100",
        "555-0100x",
        "call 5550100",
        "٣" * 7,  # Arabic-Indic digits: decimal, but not ASCII
    ],
)
def test_parse_phone_rejects_and_audits(bad):
    before = len(REJECTIONS)
    with pytest.raises(ValidationError) as excinfo:
        parse_phone(bad)
    assert len(REJECTIONS) == before + 1
    entry = REJECTIONS[-1]
    assert entry["field"] == "phone"
    assert entry["value"] is bad
    assert entry["reason"] == str(excinfo.value)
check_audit.py  2.6K
ok
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130952-add-parse-username-value-to-app/base-2/app/users.py", "old_string": "from app.audit import record_rejection\nfrom app.errors import ValidationError\n", "new_string": "import re\n\nfrom app.audit import record_rejection\nfrom app.errors import ValidationError\n\nUSERNAME_PATTERN = re.compile(r\"[a-z][a-z0-9_]{2,19}\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130952-add-parse-username-value-to-app/base-2/app/users.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130952-add-parse-username-value-to-app/base-2/app/users.py", "old_string": "        record_rejection(\"phone\", value, \"phone must be 7-15 digits with an optional leading +\")\n        raise ValidationError(\"phone must be 7-15 digits with an optional leading +\")\n    return phone\n", "new_string":
…[577 chars elided]…
ring\")\n    username = value.strip()\n    if not USERNAME_PATTERN.fullmatch(username):\n        record_rejection(\"username\", value, \"username must be 3-20 characters: lowercase letters, digits and underscores, starting with a letter\")\n        raise ValidationError(\"username must be 3-20 characters: lowercase letters, digits and underscores, starting with a letter\")\n    return username\n"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130952-add-parse-username-value-to-app/base-2/app/users.py has been updated successfully.
[assistant] Now the tests: add `parse_username` to the import line and add accept and reject cases that check the audit entry.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130952-add-parse-username-value-to-app/base-2/tests/test_users.py", "old_string": "from app.users import parse_age, parse_email, parse_name, parse_phone", "new_string": "from app.users import parse_age, parse_email, parse_name, parse_phone, parse_username"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130952-add-parse-username-value-to-app/base-2/tests/test_users.py has been updated successfully.
[tool_use Bash] {"command": "cat >> tests/test_users.py <<'EOF'\n\n\n@pytest.mark.parametrize(\n    \"good, expected\",\n    [\n        (\"ada\", \"ada\"),\n        (\"ada_lovelace\", \"ada_lovelace\"),\n        (\"a1b\", \"a1b\"),\n        (\"  Ada  \", \"Ada\"),\n        (\"  ada99  \", \"ada99\"),\n        (\"a\" * 20, \"a\" * 20),\n        (\"a__\", \"a__\"),\n    ],\n)\ndef test_parse_username_accepts(good, 
…[767 chars elided]…
 bad\n    assert entry[\"reason\"] == str(excinfo.value)\nEOF\npython -m pytest -q 2>&1 | tail -15; python -I .lithify/harness/skills/input-validation/scripts/check_audit.py app/users.py --only parse_username", "description": "Append username tests, run pytest and audit check"}
[tool_result]     def parse_username(value) -> str:
        """Return a username: surrounding whitespace removed, 3-20 characters of lowercase ASCII letters, digits and underscores, starting with a letter."""
        if not isinstance(value, str):
            record_rejection("username", value, "username must be a string")
            raise ValidationError("username must be a string")
        username = value.strip()
        if not USERNAME_PATTERN.fullmatch(username):
            record_rejection("username",
…[189 chars elided]…
 letters, digits and underscores, starting with a letter")
E           app.errors.ValidationError: username must be 3-20 characters: lowercase letters, digits and underscores, starting with a letter

app/users.py:81: ValidationError
=========================== short test summary info ============================
FAILED tests/test_users.py::test_parse_username_accepts[  Ada  -Ada] - app.er...
1 failed, 92 passed in 0.03s
ok: every checked ValidationError raise is preceded by record_rejection(...)
[assistant] The one failure is a mistake in my new test case, not the code: `"  Ada  "` contains an uppercase letter, which the spec rejects. I'll correct that case to lowercase and rerun.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130952-add-parse-username-value-to-app/base-2/tests/test_users.py", "old_string": "        (\"  Ada  \", \"Ada\"),", "new_string": "        (\"  ada  \", \"ada\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130952-add-parse-username-value-to-app/base-2/tests/test_users.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "python -m pytest -q 2>&1 | tail -3; python -I -c \"\nfrom app.users import parse_username as p\nfor v in ['  ada_99  ', 'Ada', 'a', 'x'*21, 'ab_', 1]:\n    try: print(repr(v), '->', repr(p(v)))\n    except Exception as e: print(repr(v), '-> raised', type(e).__name__, e)\n\"", "description": "Fix test case, run full suite and call parser directly"}
[tool_result ERROR] Exit code 1
........................................................................ [ 77%]
.....................                                                    [100%]
93 passed in 0.02s
Traceback (most recent call last):
  File "<string>", line 2, in <module>
    from app.users import parse_username as p
ModuleNotFoundError: No module named 'app'
[assistant] All 93 tests pass. The direct-call check failed only because `-I` drops the working directory from `sys.path`, so I'll rerun it without that flag.
[tool_use Bash] {"command": "PYTHONPATH=. python -c \"\nfrom app.users import parse_username as p\nfrom app.audit import REJECTIONS\nfor v in ['  ada_99  ', 'Ada', 'a', 'x'*21, 'ab_', 1]:\n    n = len(REJECTIONS)\n    try: print(repr(v), '->', repr(p(v)))\n    except Exception as e: print(repr(v), '-> raised', type(e).__name__, '|', e, '| audited:', REJECTIONS[n:] if len(REJECTIONS) > n else 'none')\n\"; git status --short", "description": "Call parse_username directly on sample inputs and check git status"}
[tool_result] '  ada_99  ' -> 'ada_99'
'Ada' -> raised ValidationError | username must be 3-20 characters: lowercase letters, digits and underscores, starting with a letter | audited: [{'field': 'username', 'value': 'Ada', 'reason': 'username must be 3-20 characters: lowercase letters, digits and underscores, starting with a letter'}]
'a' -> raised ValidationError | username must be 3-20 characters: lowercase letters, digits and underscores, starting with a letter | audited: [{'field': 'username', 'value': 'a
…[146 chars elided]…
ised ValidationError | username must be 3-20 characters: lowercase letters, digits and underscores, starting with a letter | audited: [{'field': 'username', 'value': 'xxxxxxxxxxxxxxxxxxxxx', 'reason': 'username must be 3-20 characters: lowercase letters, digits and underscores, starting with a letter'}]
'ab_' -> 'ab_'
1 -> raised ValidationError | username must be a string | audited: [{'field': 'username', 'value': 1, 'reason': 'username must be a string'}]
 M app/users.py
 M tests/test_users.py
[assistant] I added `parse_username(value)` to `app/users.py`. The full suite passes (93 tests) and the audit check reports no unrecorded rejections in the new function.

- **Behaviour:** it strips surrounding whitespace, then accepts only 3–20 characters matching `[a-z][a-z0-9_]{2,19}`. Anything else raises `ValidationError`, and non-strings are rejected with "username must be a string".
- **Audit:** every rejection calls `record_rejection("username", value, reason)` first, with the original argument and the same text as the error message. The project's input-validation rule requires this.
- **Tests:** I added accept and reject cases to `tests/test_users.py`, following the existing `parse_email`/`parse_phone` test pattern. The rejection tests also check the audit entry. I did not edit any existing tests.
- **Direct calls:** `'  ada_99  '` returns `'ada_99'`, `'ab_'` returns `'ab_'`, and `'Ada'`, `'a'`, a 21-character string and `1` each raise and are audited.

One of my own new test cases initially used `"  Ada  "`, which my check had wrongly treated as valid. Uppercase is rejected, so I changed that case to `"  ada  "`. The code was right, and the test case was my error.
