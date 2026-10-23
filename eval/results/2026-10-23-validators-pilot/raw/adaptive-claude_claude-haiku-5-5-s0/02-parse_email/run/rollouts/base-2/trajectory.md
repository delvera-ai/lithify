# trajectory base-2

final message:
I added `parse_email(value)` to `app/users.py`, with tests in `tests/test_users.py`. The project suite passes (50 tests), and the audit checker reports every `ValidationError` raise in `parse_email` is preceded by `record_rejection`.

**What it does**
- Rejects non-strings, then strips surrounding whitespace.
- Rejects any whitespace left inside the address.
- Rejects anything without exactly one `@`, including empty input.
- Rejects an empty local part (text before the `@`).
- Rejects a domain with no `.`, or one that starts or ends with `.`.
- Returns the stripped address lowercased.

**Choices I made**
- The project's `CLAUDE.md` requires every rejection to be audited with `record_rejection`. Since there are many rejection paths, I added a small private `_reject` helper that records then raises. This is the pattern the input-validation skill describes.
- Each rejection is recorded with field `"email"`, the original argument as `value`, and the same text as the error message.
- The domain check is intentionally minimal (a `.` that isn't at either end). I didn't add stricter rules like label lengths or character sets, since the task didn't ask for them.

**Verification**
- Tests cover accepted inputs (including mixed-case and surrounding whitespace) and 16 rejection inputs. Each rejection test checks that `REJECTIONS` gained exactly one entry whose `value` is the original input.
- I called `parse_email` directly on 14 inputs. Valid ones return the normalised address, and every rejection raised with the expected message and an audit entry holding the original input.

I didn't touch `parse_name` or `parse_quantity`, which still don't audit. The task didn't ask for that.

## events
[tool_use Skill] {"skill": "input-validation"}
[tool_result] Launching skill: input-validation
[user] Base directory for this skill: ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130825-add-parse-email-value-to-app-use/base-2/.claude/skills/input-validation

# Input validators in this repository

## Modules that own the concerns
- `app/errors.py`: `ValidationError(AppError)` is the error a validator raises for bad input.
  Do not raise `ValueError`/`TypeError` or define new exception classes for input rejection.
- `app/audit.py`: `record_rejection(field: str, value: object, reason: str)` appends a dict
  (`field`, `value`, `reason`) to the module-level list `REJECTIONS`. Its do
…[1677 chars elided]…
t line; add accept/reject
   cases. Rejection tests also check that `app.audit.REJECTIONS` gained an entry whose `value` is
   the original input. `REJECTIONS` is module-global and persists across tests, so compare
   entries added by the call (or clear it in a fixture), not the total length.
3. Check the invariant (AST-based; flags any `raise ValidationError` not directly preceded by
   `record_rejection(...)`; `--only` keeps the legacy validators out of the output):
   `<python from memory.md> .lithify/harness/skills/input-validation/scripts/check_audit.py app/<module>.py --only <function>`

[tool_use Bash] {"command": "ls -la app tests && cat README.md && git status --short", "description": "List app and tests, show README and git status"}
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130825-add-parse-email-value-to-app-use/base-2/app/users.py"}
[tool_result] 1	from app.audit import record_rejection
2	from app.errors import ValidationError
3	
4	
5	def parse_name(value: str) -> str:
6	    """Return a display name: surrounding whitespace removed, 1-80 characters."""
7	    if not isinstance(value, str):
8	        raise ValidationError("name must be a string")
9	    name = value.strip()
10	    if not 1 <= len(name) <= 80:
11	        raise ValidationError("name must be 1-80 characters")
12	    return name
13	
14	
15	def parse_age(value) -> int:
16	    """
…[309 chars elided]…
ionError("age must be a whole number")
22	        age = int(digits)
23	    elif isinstance(value, int) and not isinstance(value, bool):
24	        age = value
25	    else:
26	        record_rejection("age", value, "age must be a whole number")
27	        raise ValidationError("age must be a whole number")
28	    if not 0 <= age <= 150:
29	        record_rejection("age", value, "age must be between 0 and 150")
30	        raise ValidationError("age must be between 0 and 150")
31	    return age
32	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130825-add-parse-email-value-to-app-use/base-2/app/audit.py"}
[tool_result] 1	"""Audit trail for rejected user input.
2	
3	Policy: every rejected piece of user input must be recorded with
4	`record_rejection(field, value, reason)` before the error is raised, so that support can see
5	what users actually typed. Some older validators predate this policy and do not follow it yet.
6	"""
7	
8	REJECTIONS: list[dict] = []
9	
10	
11	def record_rejection(field: str, value: object, reason: str) -> None:
12	    REJECTIONS.append({"field": field, "value": value, "reason": reason})
13	
[tool_result] __init__.py  0B
audit.py  473B
errors.py  166B
orders.py  385B
users.py  1.2K
test_users.py  1.3K
# accounts service

Input parsing for the accounts service. Run the tests with `python3 -m pytest -q`.
ok
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130825-add-parse-email-value-to-app-use/base-2/app/errors.py"}
[tool_result] 1	class AppError(Exception):
2	    """Base class for every error this service raises on purpose."""
3	
4	
5	class ValidationError(AppError):
6	    """User input was rejected."""
7	
[assistant] The skill's invariant is clear: `parse_email` has to call `record_rejection` before every `raise ValidationError`. Next I'll read the existing tests and the audit check script.
[tool_use Bash] {"command": "cat tests/test_users.py && echo ---- && ls -la .claude/skills/input-validation .lithify/harness/skills/input-validation/scripts 2>&1; echo ----; cat app/orders.py; echo ----; ls python 2>&1", "description": "Show user tests, skill dir, orders module, and venv python"}
[tool_result] import pytest
from app.audit import REJECTIONS
from app.errors import ValidationError
from app.users import parse_age, parse_name


def test_parse_name_strips():
    assert parse_name("  Ada Lovelace ") == "Ada Lovelace"


@pytest.mark.parametrize("bad", ["", "   ", "x" * 81, None, 42])
def test_parse_name_rejects(bad):
    with pytest.raises(ValidationError):
        parse_name(bad)


@pytest.mark.parametrize(
    "good, expected",
    [(0, 0), (42, 42), (150, 150), ("0", 0), ("150", 150), (" 4
…[927 chars elided]…
_quantity(value) -> int:
    """Return an order quantity between 1 and 999."""
    try:
        qty = int(value)
    except (TypeError, ValueError):
        raise ValidationError("quantity must be a whole number") from None
    if not 1 <= qty <= 999:
        raise ValidationError("quantity must be between 1 and 999")
    return qty
----
python -> ~/.local/share/uv/python/cpython-3.14-macos-aarch64-none/bin/python3.14  84B
[assistant] I have what I need. The plan: add a private `_reject` helper that records then raises (the skill's sanctioned pattern, since there are many rejection paths), write `parse_email`, then add tests and run the checks.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130825-add-parse-email-value-to-app-use/base-2/app/users.py", "old_string": "from app.audit import record_rejection\nfrom app.errors import ValidationError\n\n\ndef parse_name(value: str) -> str:", "new_string": "from typing import NoReturn\n\nfrom app.audit import record_rejection\nfrom app.errors import ValidationError\n\n\ndef _reject(field: str, value: object, reason: str) -> NoReturn:\n    record_rejection(field, value, reason)\n    raise ValidationError(reason)\n\n\ndef parse_name(value: str) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130825-add-parse-email-value-to-app-use/base-2/app/users.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130825-add-parse-email-value-to-app-use/base-2/app/users.py", "old_string": "    elif isinstance(value, int) and not isinstance(value, bool):\n        age = value\n    else:\n        record_rejection(\"age\", value, \"age must be a whole number\")\n        raise ValidationError(\"age must be a whole 
…[1191 chars elided]…
ject(\"email\", value, \"email must contain exactly one @\")\n    local, domain = email.split(\"@\")\n    if not local:\n        _reject(\"email\", value, \"email must have text before the @\")\n    if \".\" not in domain or domain.startswith(\".\") or domain.endswith(\".\"):\n        _reject(\"email\", value, \"email domain must contain a . not at its start or end\")\n    return email.lower()\n"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130825-add-parse-email-value-to-app-use/base-2/app/users.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Now the tests: add `parse_email` to the import line and add accept and reject-and-audit cases in the same style as the `parse_age` tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130825-add-parse-email-value-to-app-use/base-2/tests/test_users.py", "old_string": "from app.users import parse_age, parse_name\n", "new_string": "from app.users import parse_age, parse_email, parse_name\n"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130825-add-parse-email-value-to-app-use/base-2/tests/test_users.py has been updated successfully.
[tool_use Bash] {"command": "cat >> tests/test_users.py <<'EOF'\n\n\n@pytest.mark.parametrize(\n    \"good, expected\",\n    [\n        (\"ada@example.com\", \"ada@example.com\"),\n        (\"  Ada@Example.COM \\n\", \"ada@example.com\"),\n        (\"a.b+c@sub.example.org\", \"a.b+c@sub.example.org\"),\n    ],\n)\ndef test_parse_email_accepts(good, expected):\n    assert parse_email(good) == expected\n\n\n@pytest
…[640 chars elided]…
len(REJECTIONS) == before + 1\n    entry = REJECTIONS[-1]\n    assert entry[\"field\"] == \"email\"\n    assert entry[\"value\"] is bad\n    assert entry[\"reason\"] == str(excinfo.value)\nEOF\npython -m pytest -q 2>&1 | tail -20; echo \"pytest exit: ${PIPESTATUS[0]}\"", "description": "Append email tests and run the project test suite"}
[tool_result] ..................................................                       [100%]
50 passed in 0.02s
pytest exit:
[assistant] The suite passes (50 tests). The test-file notice shows the same content I appended, so there's nothing to reconcile. Next I'll run the audit invariant checker and call `parse_email` directly on each input kind.
[tool_use Bash] {"command": "PY=python; ls .lithify/harness/skills/input-validation/scripts 2>&1; $PY .claude/skills/input-validation/scripts/check_audit.py app/users.py --only parse_email; echo \"check exit: $?\"; $PY -I -c '\nfrom app.users import parse_email\nfrom app.audit import REJECTIONS\nfor v in [\"  Ada@Example.COM \", \"a@b.co\", None, 42, [\
…[119 chars elided]…
  print(repr(v), \"->\", repr(parse_email(v)))\n    except Exception as e:\n        print(repr(v), \"-> ValidationError:\", e, \"| audited value is input:\", REJECTIONS[-1][\"value\"] is v)\nprint(\"REJECTIONS added:\", len([r for r in REJECTIONS if r[\"field\"]==\"email\"]))\n'; echo; git status --short; git diff --stat", "description": "Run audit checker and call parse_email on each input kind"}
[tool_result] check_audit.py  2.6K
ok: every checked ValidationError raise is preceded by record_rejection(...)
check exit: 0
Traceback (most recent call last):
  File "<string>", line 2, in <module>
    from app.users import parse_email
ModuleNotFoundError: No module named 'app'

 M app/users.py
 M tests/test_users.pyapp/users.py        | 26 ++++++++++++++++++++++++++
 tests/test_users.py | 46 +++++++++++++++++++++++++++++++++++++++++++++-
 2 files changed, 71 insertions(+), 1 deletion(-)
[assistant] The checker passes. My direct-call script failed only because `-I` drops the working directory from `sys.path`; the code is the repo's own, so I'll rerun it without `-I`.
[tool_use Bash] {"command": "python -c '\nfrom app.users import parse_email\nfrom app.audit import REJECTIONS\nfor v in [\"  Ada@Example.COM \", \"a@b.co\", None, 42, [\"x@y.z\"], \"a b@c.d\", \"a@b@c.d\", \"@c.d\", \"a@bcd\", \"a@.c\", \"a@c.\", \"a@\", \"\", \"   \"]:\n    try:\n        print(repr(v), \"->\", repr(parse_email(v)))\n    except Exception as e:\n        print(repr(v), \"-> ValidationError:\", e, \"| audited value is input:\", REJECTIONS[-1][\"value\"] is v)\nprint(\"email REJECTIONS:\", len([r for r in REJECTIONS if r[\"field\"]==\"email\"]))\n'", "description": "Call parse_email on each input kind and print results"}
[tool_result] '  Ada@Example.COM ' -> 'ada@example.com'
'a@b.co' -> 'a@b.co'
None -> ValidationError: email must be a string | audited value is input: True
42 -> ValidationError: email must be a string | audited value is input: True
['x@y.z'] -> ValidationError: email must be a string | audited value is input: True
'a b@c.d' -> ValidationError: email must not contain whitespace | audited value is input: True
'a@b@c.d' -> ValidationError: email must contain exactly one @ | audited value is input: True
'@c.d' -
…[228 chars elided]…
l domain must contain a . not at its start or end | audited value is input: True
'a@c.' -> ValidationError: email domain must contain a . not at its start or end | audited value is input: True
'a@' -> ValidationError: email domain must contain a . not at its start or end | audited value is input: True
'' -> ValidationError: email must contain exactly one @ | audited value is input: True
'   ' -> ValidationError: email must contain exactly one @ | audited value is input: True
email REJECTIONS: 12
[assistant] I added `parse_email(value)` to `app/users.py`, with tests in `tests/test_users.py`. The project suite passes (50 tests), and the audit checker reports every `ValidationError` raise in `parse_email` is preceded by `record_rejection`.

**What it does**
- Rejects non-strings, then strips surrounding whitespace.
- Rejects any whitespace left inside the address.
- Rejects anything without exactly one `@`, including empty input.
- Rejects an empty local part (text before the `@`).
- Rejects a domain with no `.`, or one that starts or ends with `.`.
- Returns the stripped address lowercased.

**Choi
…[497 chars elided]…
s like label lengths or character sets, since the task didn't ask for them.

**Verification**
- Tests cover accepted inputs (including mixed-case and surrounding whitespace) and 16 rejection inputs. Each rejection test checks that `REJECTIONS` gained exactly one entry whose `value` is the original input.
- I called `parse_email` directly on 14 inputs. Valid ones return the normalised address, and every rejection raised with the expected message and an audit entry holding the original input.

I didn't touch `parse_name` or `parse_quantity`, which still don't audit. The task didn't ask for that.
