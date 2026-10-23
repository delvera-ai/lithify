# trajectory inv-2

final message:
I added `parse_age(value)` to `app/users.py`. It returns the age as an int for accepted input, and raises `ValidationError` for everything else. Every rejection is also recorded in the audit log first.

The project's pytest run passes: 6 passed, exit 0.

**Convention from the survey:** `app/audit.py` says every rejected input must go through `record_rejection(field, value, reason)` before the error is raised. `parse_name` doesn't follow this, but its docstring says it predates the policy. `parse_age` does, on every rejection branch.

**Behaviour:**
- **Accepted:** ints from 0 to 150, and strings of ASCII digits with surrounding whitespace removed (for example `" 42 "` → `42`, `"150"` → `150`).
- **Rejected:** bools, other types (including `None` and floats), non-digit strings (`"abc"`, `""`, `"-5"`, `"+5"`, `"1e2"`, `"²"`), and values outside 0–150.

I called the function directly on each case. All 4 accepted inputs returned the expected int. All 14 rejected inputs raised `ValidationError` and added one audit record with field `"age"` and the input value. The last check was that the test suite still passes.

I didn't add tests for `parse_age` to `tests/test_users.py`, to keep the change to the function alone. I can add them if you want them in the repo.

## events
[tool_use Skill] {"skill": "survey-conventions"}
[tool_result] Launching skill: survey-conventions
[user] Base directory for this skill: ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/inv-2/.claude/skills/survey-conventions

Both earlier attempts at this kind of task read only the target module, `app/errors.py`, and one
sibling. Their own tests passed, but they still missed a convention that applies to every rejected
input. Reading two files is not enough to know the conventions.

1. Inventory the package (one call):
   `<python from memory.md> .lithify/harness/skills/survey-conventions/scripts/survey.py . --pkg app`
   Exit 2 means the packag
…[468 chars elided]…
every path of the new code must do. That includes the error
   type, plus any logging, recording or other side effect on rejection. It applies to every
   rejection branch, not only the main one.
4. Implement it. Then check each rejection branch against that list.
5. Verify the behaviour itself, not just your tests. Call the function directly with a
   `python -c` one-liner for one accepted case and one case from each rejection category in
   the task. Confirm each result, and that each convention from step 3 actually happened. Then
   run the project's test command and read its summary line.

[tool_use Bash] {"command": "ls app tests 2>/dev/null; cat app/users.py 2>/dev/null; git log --oneline | head -3", "description": "List app and tests, show users.py"}
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
6baf5c5 lithify: probe base
4711c1b eval: configure parse_age
7c077ea lithify init
[tool_use Bash] {"command": "python .lithify/harness/skills/survey-conventions/scripts/survey.py . --pkg app; echo \"exit=$?\"", "description": "Run survey script on app package"}
[tool_result] ## app/__init__.py  (0 lines)
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
exit=0
[tool_use Bash] {"command": "cat AGENTS.md; echo ----; cat README.md; echo ----; cat app/audit.py; echo ----; cat app/orders.py; echo ----; cat app/errors.py; echo ----; cat tests/test_users.py", "description": "Read docs and related app modules"}
[tool_result] <!-- lithify:begin — managed by `lithify sync`; edit .lithify/harness/ instead -->
## Project harness (lithify)

### Role and procedure

You are a careful engineer working in this repository. Make the smallest change that fully
satisfies the task, following the patterns the surrounding code already uses. Before adding or
changing code in `app/`, load the `survey-conventions` skill. Read the relevant code before
editing it. Finish only after the project's checks pass and you have called the chang
…[2186 chars elided]…
r(Exception):
    """Base class for every error this service raises on purpose."""


class ValidationError(AppError):
    """User input was rejected."""
----
import pytest
from app.errors import ValidationError
from app.users import parse_name


def test_parse_name_strips():
    assert parse_name("  Ada Lovelace ") == "Ada Lovelace"


@pytest.mark.parametrize("bad", ["", "   ", "x" * 81, None, 42])
def test_parse_name_rejects(bad):
    with pytest.raises(ValidationError):
        parse_name(bad)
[assistant] Survey findings: the audit policy in `app/audit.py` requires every rejected input to call `record_rejection(field, value, reason)` before raising. Only `parse_name` ignores it, and the docstring says older validators predate the policy. So each rejection branch in `parse_age` must record and then raise `ValidationError`.

Before editing, the plan is:
- **Error type:** `ValidationError` on every rejection.
- **Side effect:** `record_rejection("age", value, reason)` before each raise.
- **Accepted:** non-bool ints in 0–150, and whitespace-trimmed strings made only of ASCII digits whose value is in 0–150.
- **Rejected:** bools, other types, non-digit strings (including `-5`, `+5`, and empty), and out-of-range values.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/inv-2/app/users.py"}
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/inv-2/app/users.py", "old_string": "from app.errors import ValidationError\n\n\ndef parse_name(value: str) -> str:", "new_string": "import re\n\nfrom app.audit import record_rejection\nfrom app.errors import ValidationError\n\n_DIGITS = re.compile(r\"[0-9]+\")\
…[452 chars elided]…
_rejection(\"age\", value, \"not a string of decimal digits\")\n            raise ValidationError(\"age must be a whole number\")\n        age = int(text)\n    else:\n        age = value\n    if not 0 <= age <= 150:\n        record_rejection(\"age\", value, \"outside 0-150\")\n        raise ValidationError(\"age must be between 0 and 150\")\n    return age\n\n\ndef parse_name(value: str) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/inv-2/app/users.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Now I'll call the function directly for one accepted case and one case from each rejection category, and check the audit record each time.
[tool_use Bash] {"command": "python -c '\nfrom app import audit\nfrom app.users import parse_age\nfrom app.errors import ValidationError\nok = [(\" 42 \", 42), (0, 0), (\"150\", 150), (150, 150)]\nbad = [True, None, 3.5, \"abc\", \"\", \"  \", \"-5\", \"+5\", \"1e2\", \"\u00b2\", -1, 151, \"151\", \"1000\"]\nfor v, want in ok:\n    got = parse_age(v); a
…[400 chars elided]…
= v and rec[\"field\"] == \"age\"\n        print(\"rej \", repr(v), \"->\", e, \"| recorded:\", rec[\"reason\"])\nprint(\"rejections recorded:\", len(audit.REJECTIONS) - n0, \"of\", len(bad))\n'\necho \"---\"\npython -m pytest -q; echo \"exit=$?\"", "description": "Call parse_age directly on accepted and rejected inputs, then run tests"}
[tool_result] ok   ' 42 ' -> 42
ok   0 -> 0
ok   '150' -> 150
ok   150 -> 150
rej  True -> age must be a whole number | recorded: not an int or a string
rej  None -> age must be a whole number | recorded: not an int or a string
rej  3.5 -> age must be a whole number | recorded: not an int or a string
rej  'abc' -> age must be a whole number | recorded: not a string of decimal digits
rej  '' -> age must be a whole number | recorded: not a string of decimal digits
rej  '  ' -> age must be a whole number | recor
…[282 chars elided]…
its
rej  '²' -> age must be a whole number | recorded: not a string of decimal digits
rej  -1 -> age must be between 0 and 150 | recorded: outside 0-150
rej  151 -> age must be between 0 and 150 | recorded: outside 0-150
rej  '151' -> age must be between 0 and 150 | recorded: outside 0-150
rej  '1000' -> age must be between 0 and 150 | recorded: outside 0-150
rejections recorded: 14 of 14
---
......                                                                   [100%]
6 passed in 0.01s
exit=0
[assistant] I added `parse_age(value)` to `app/users.py`. It returns the age as an int for accepted input, and raises `ValidationError` for everything else. Every rejection is also recorded in the audit log first.

The project's pytest run passes: 6 passed, exit 0.

**Convention from the survey:** `app/audit.py` says every rejected input must go through `record_rejection(field, value, reason)` before the error is raised. `parse_name` doesn't follow this, but its docstring says it predates the policy. `parse_age` does, on every rejection branch.

**Behaviour:**
- **Accepted:** ints from 0 to 150, and strin
…[73 chars elided]…
 "` → `42`, `"150"` → `150`).
- **Rejected:** bools, other types (including `None` and floats), non-digit strings (`"abc"`, `""`, `"-5"`, `"+5"`, `"1e2"`, `"²"`), and values outside 0–150.

I called the function directly on each case. All 4 accepted inputs returned the expected int. All 14 rejected inputs raised `ValidationError` and added one audit record with field `"age"` and the input value. The last check was that the test suite still passes.

I didn't add tests for `parse_age` to `tests/test_users.py`, to keep the change to the function alone. I can add them if you want them in the repo.
