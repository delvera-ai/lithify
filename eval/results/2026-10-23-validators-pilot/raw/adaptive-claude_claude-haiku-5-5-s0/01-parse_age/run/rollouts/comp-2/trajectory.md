# trajectory comp-2

final message:
`parse_age` is in `app/users.py` and passes. The full suite is 30 passed, and the audit check reports no unrecorded rejections for `parse_age`.

**What changed**
- `app/users.py`: new `parse_age(value)` returns an int from 0 to 150. It accepts an int, or a string of ASCII digits with optional surrounding whitespace. Everything else raises `ValidationError`.
- Every rejection goes through a private `_reject(field, value, reason)` helper that calls `record_rejection("age", <original argument>, <message>)` before raising. This is the audit policy in `app/audit.py`. I did not copy the raise-only shape of `parse_name` and `parse_quantity`, and I did not retrofit them since the task didn't ask.
- `tests/test_users.py`: I added accept and reject tests and extended the existing import line. The existing tests are unchanged. The reject tests check both the `ValidationError` and that an audit entry with the original value was recorded.

**Choices I made**
- Digits must be ASCII. `str.isdigit()` alone would accept characters like `²` and Arabic-Indic digits, and `int()` would then parse some of them, so I check `isascii()` too.
- `bool` is rejected even though it is a subclass of `int`.
- Strings are stripped before the digit check, so `"   "` is rejected and `" 42\t"` is accepted.
- The audit `field` is `"age"`, matching the error message noun.

I have not committed anything.

## events
[assistant] I'll start by reading the target module, the audit and error helpers, and the project's survey script.
[tool_use Bash] {"command": "ls -la && git status --short && python3 .lithify/harness/scripts/survey.py 2>&1 | head -150", "description": "List repo, check status, and run project survey script"}
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/comp-2/app/users.py"}
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/comp-2/app/audit.py"}
[tool_result] .agents/
.claude/
.lithify/
app/
tests/
.git  114B
.gitignore  105B
AGENTS.md  1.9K
CLAUDE.md  1.9K
README.md  103B
conftest.py  81B
ok## app/__init__.py  (0 lines)
  imports: -
  defines: -

## app/audit.py  (12 lines)
  imports: -
  defines: record_rejection

## app/errors.py  (6 lines)
  imports: -
  defines: AppError, ValidationError

## app/orders.py  (12 lines)
  imports: app.errors: ValidationError
  defines: parse_quantity

## app/users.py  (11 lines)
  imports: app.errors: ValidationError
  defines: parse_name

## modules no other package module imports
  app.audit, app.orders, app.users
## public names never imported/referenced by another package module
  app.audit: record_rejection
  app.errors: AppError
  app.orders: parse_quantity
  app.users: parse_name
## docs
  AGENTS.md
  README.md
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
[tool_result] 1	from app.errors import ValidationError
2	
3	
4	def parse_name(value: str) -> str:
5	    """Return a display name: surrounding whitespace removed, 1-80 characters."""
6	    if not isinstance(value, str):
7	        raise ValidationError("name must be a string")
8	    name = value.strip()
9	    if not 1 <= len(name) <= 80:
10	        raise ValidationError("name must be 1-80 characters")
11	    return name
12	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/comp-2/app/errors.py"}
[tool_result] 1	class AppError(Exception):
2	    """Base class for every error this service raises on purpose."""
3	
4	
5	class ValidationError(AppError):
6	    """User input was rejected."""
7	
[assistant] The project requires the `input-validators` skill for any validator change, so I'll load it before writing code. I'm also reading the tests and orders module for conventions.
[tool_use Skill] {"skill": "input-validators"}
[tool_result] Launching skill: input-validators
[user] Base directory for this skill: ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/comp-2/.claude/skills/input-validators

# Input validators in this repository

## Modules that own the concerns
- `app/errors.py`: `ValidationError(AppError)` is the error a validator raises for bad input.
  Do not raise `ValueError`/`TypeError` or define a new exception class for input rejection.
- `app/audit.py`: `record_rejection(field: str, value: object, reason: str)` appends a dict
  `{"field", "value", "reason"}` to the module-level list `REJECTIONS`. Its 
…[1700 chars elided]…
ck the `ValidationError` AND that an audit record with the original value
   was added. `REJECTIONS` is module-global and persists across tests: compare against entries
   added during the call, or clear it in a fixture.
4. Check the invariant (use `--only` so the legacy validators don't show as noise):
   `python3 .lithify/harness/skills/input-validators/scripts/check_audit.py app/<module>.py --only <function>`
   It lists every `raise ValidationError` not immediately preceded by `record_rejection(...)`.
   If you raise through a helper like `_reject`, check the helper by reading it instead.

[tool_use Bash] {"command": "cat app/orders.py && echo ---- && ls tests && cat tests/*.py && echo ---- && cat AGENTS.md README.md conftest.py", "description": "Show orders module, tests, and project docs"}
[tool_result] from app.errors import ValidationError


def parse_quantity(value) -> int:
    """Return an order quantity between 1 and 999."""
    try:
        qty = int(value)
    except (TypeError, ValueError):
        raise ValidationError("quantity must be a whole number") from None
    if not 1 <= qty <= 999:
        raise ValidationError("quantity must be between 1 and 999")
    return qty
----
test_users.py  343B
import pytest
from app.errors import ValidationError
from app.users import parse_name


de
…[1902 chars elided]…
oad on demand)

- `input-validators` — Load when adding or changing any function in app/ that parses, validates or rejects user input (parse_* functions, anything that raises ValidationError), or when writing tests for such a function.

### Helper scripts

- `.lithify/harness/scripts/survey.py`
<!-- lithify:end -->
# accounts service

Input parsing for the accounts service. Run the tests with `python3 -m pytest -q`.
# Root conftest: puts the repository root on sys.path so tests can `import app`.
[assistant] The skill confirms the rule: every `ValidationError` path in a new validator must call `record_rejection` first, with the original argument as `value`. I'll add `parse_age` with a small private helper that records and then raises, so each rejection path shares one implementation.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/comp-2/app/users.py", "old_string": "from app.errors import ValidationError\n\n\ndef parse_name(value: str) -> str:\n    \"\"\"Return a display name: surrounding whitespace removed, 1-80 characters.\"\"\"\n    if not isinstance(value, str):\n        raise Valid
…[1080 chars elided]…
\", value, \"age must be a whole number\")\n    if isinstance(value, int):\n        age = value\n    else:\n        text = value.strip()\n        if not (text.isascii() and text.isdigit()):\n            _reject(\"age\", value, \"age must be a whole number\")\n        age = int(text)\n    if not 0 <= age <= 150:\n        _reject(\"age\", value, \"age must be between 0 and 150\")\n    return age\n"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/comp-2/app/users.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Next, the tests. I'm extending the existing import line and appending new tests without touching the existing ones. The reject tests check that an audit record with the original value was added during the call.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/comp-2/tests/test_users.py", "old_string": "import pytest\nfrom app.errors import ValidationError\nfrom app.users import parse_name\n", "new_string": "import pytest\nfrom app.audit import REJECTIONS\nfrom app.errors import ValidationError\nfrom app.users import parse_age, parse_name\n"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/comp-2/tests/test_users.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/comp-2/tests/test_users.py", "old_string": "@pytest.mark.parametrize(\"bad\", [\"\", \"   \", \"x\" * 81, None, 42])\ndef test_parse_name_rejects(bad):\n    with pytest.raises(ValidationError):\n        parse_name(bad)\n", "new_string": "@pytest.mark.parametriz
…[487 chars elided]…
], \"\", \"   \", \"-1\", \"+5\", \"12a\", \"1 2\", \"151\", \"\u0664\u0662\", \"4.5\"],\n)\ndef test_parse_age_rejects_and_records(bad):\n    before = len(REJECTIONS)\n    with pytest.raises(ValidationError):\n        parse_age(bad)\n    new = REJECTIONS[before:]\n    assert len(new) == 1\n    assert new[0][\"field\"] == \"age\"\n    assert new[0][\"value\"] is bad or new[0][\"value\"] == bad\n"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/comp-2/tests/test_users.py has been updated successfully.
[assistant] I'll tighten that last assertion, since `is bad or ==` is redundant. Then I'll run the test suite with the project's interpreter and the audit checker.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/comp-2/tests/test_users.py", "old_string": "    assert new[0][\"value\"] is bad or new[0][\"value\"] == bad", "new_string": "    assert new[0][\"value\"] == bad"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/comp-2/tests/test_users.py has been updated successfully.
[tool_use Bash] {"command": "ls python 2>&1; PY=python; [ -x \"$PY\" ] || PY=python3; echo \"using $PY\"; $PY -m pytest -q 2>&1 | tail -30; echo \"--- audit check\"; python3 .lithify/harness/skills/input-validators/scripts/check_audit.py app/users.py --only parse_age; echo \"exit=$?\"", "description": "Run pytest and audit invariant check"}
[tool_result] python -> ~/.local/share/uv/python/cpython-3.14-macos-aarch64-none/bin/python3.14  84B
using python
..............................                                           [100%]
30 passed in 0.01s
--- audit check
ok: every checked ValidationError raise is preceded by record_rejection(...)
exit=0
[assistant] `parse_age` is in `app/users.py` and passes. The full suite is 30 passed, and the audit check reports no unrecorded rejections for `parse_age`.

**What changed**
- `app/users.py`: new `parse_age(value)` returns an int from 0 to 150. It accepts an int, or a string of ASCII digits with optional surrounding whitespace. Everything else raises `ValidationError`.
- Every rejection goes through a private `_reject(field, value, reason)` helper that calls `record_rejection("age", <original argument>, <message>)` before raising. This is the audit policy in `app/audit.py`. I did not copy the raise-only s
…[188 chars elided]…
line. The existing tests are unchanged. The reject tests check both the `ValidationError` and that an audit entry with the original value was recorded.

**Choices I made**
- Digits must be ASCII. `str.isdigit()` alone would accept characters like `²` and Arabic-Indic digits, and `int()` would then parse some of them, so I check `isascii()` too.
- `bool` is rejected even though it is a subclass of `int`.
- Strings are stripped before the digit check, so `"   "` is rejected and `" 42\t"` is accepted.
- The audit `field` is `"age"`, matching the error message noun.

I have not committed anything.
