# trajectory inv-1

final message:
`parse_age` is in `app/users.py`, and it matches every clause of the task. The project suite passes: 28 tests, the 6 original plus the new ones.

**What it does**
- Accepts an int, or a string of decimal digits with optional surrounding whitespace, and returns an int.
- Valid ages are 0 to 150 inclusive.
- Rejects with `ValidationError`: other types (including `None` and floats), booleans, empty or whitespace-only strings, non-digit strings (`"-1"`, `"+5"`, `"4a"`, `"1 2"`), and ages outside 0 to 150.

**Repo convention followed**
- `app/audit.py` says every rejected input must go through `record_rejection(field, value, reason)` before the raise. `parse_name` doesn't do this, but its docstring marks the older validators as the exception. The new function records on every rejection path, with `field="age"`.

**Verification**
- I ran the function directly against each accepted and rejected kind and read the output. Accepted: `0`, `150`, `"42"`, `" 42\n"`, `"007"`, `42`. Rejected with the expected messages: `True`, `None`, `4.5`, `""`, `"-1"`, `"+5"`, `"4a"`, `"151"`, `151`, `-1`. Each rejection added one audit entry.

**Changes**
- `app/users.py`: the new function, plus `re` and `audit` imports.
- `tests/test_users.py`: new parametrized tests for accepted and rejected inputs, including the audit-record check. The only edit to existing lines is the import line, which now also imports `parse_age`. No existing test was changed.

I haven't committed anything. The working tree has the two modified files.

## events
[assistant] I'll start by surveying the repo, reading the target module, and checking the existing error conventions.
[tool_use Bash] {"command": "git status --short && ls -la && find app tests -type f -name '*.py' | sort && cat README.md 2>/dev/null | head -80", "description": "Inspect repo layout, files, and README"}
[tool_use Bash] {"command": "ls .lithify/harness/scripts/ && python .lithify/harness/scripts/survey.py app 2>&1 | head -150", "description": "Run the project survey script on app package"}
[tool_result] ok.agents/
.claude/
.lithify/
app/
tests/
.git  113B
.gitignore  105B
AGENTS.md  2.0K
CLAUDE.md  2.0K
README.md  103B
conftest.py  81B
app/__init__.py
app/audit.py
app/errors.py
app/orders.py
app/users.py
tests/test_users.py
# accounts service

Input parsing for the accounts service. Run the tests with `python3 -m pytest -q`.
[tool_result] survey.py  2.6K
app/__init__.py
app/audit.py
  def record_rejection(field, value, reason)
app/errors.py
  class AppError: Base class for every error this service raises on purpose.
  class ValidationError: User input was rejected.
app/orders.py
  imports: app.errors.ValidationError
  def parse_quantity(value): Return an order quantity between 1 and 999.
app/users.py
  imports: app.errors.ValidationError
  def parse_name(value): Return a display name: surrounding whitespace removed, 1-80 characters.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/inv-1/app/users.py"}
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/inv-1/app/errors.py"}
[tool_result] 1	class AppError(Exception):
2	    """Base class for every error this service raises on purpose."""
3	
4	
5	class ValidationError(AppError):
6	    """User input was rejected."""
7	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/inv-1/app/audit.py"}
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/inv-1/app/orders.py"}
[tool_result] 1	from app.errors import ValidationError
2	
3	
4	def parse_quantity(value) -> int:
5	    """Return an order quantity between 1 and 999."""
6	    try:
7	        qty = int(value)
8	    except (TypeError, ValueError):
9	        raise ValidationError("quantity must be a whole number") from None
10	    if not 1 <= qty <= 999:
11	        raise ValidationError("quantity must be between 1 and 999")
12	    return qty
13	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/inv-1/tests/test_users.py"}
[tool_result] 1	import pytest
2	from app.errors import ValidationError
3	from app.users import parse_name
4	
5	
6	def test_parse_name_strips():
7	    assert parse_name("  Ada Lovelace ") == "Ada Lovelace"
8	
9	
10	@pytest.mark.parametrize("bad", ["", "   ", "x" * 81, None, 42])
11	def test_parse_name_rejects(bad):
12	    with pytest.raises(ValidationError):
13	        parse_name(bad)
14	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/inv-1/AGENTS.md"}
[tool_result] 1	<!-- lithify:begin — managed by `lithify sync`; edit .lithify/harness/ instead -->
2	## Project harness (lithify)
3	
4	### Role and procedure
5	
6	You are a careful engineer working in this repository. Make the smallest change that fully
7	satisfies the task, following the patterns the surrounding code already uses.
8	
9	Procedure:
10	1. Survey before editing. Run `.lithify/harness/scripts/survey.py app` with the project python
11	   (see memory) to map every module and its top-level helpers, 
…[1199 chars elided]…
p -rn PAT --include='*.py' app tests`); an unquoted
33	  glob aborts with "no matches found". Scope searches to `app tests`, not `.` (avoids `.venv`).
34	- BSD `sed -i` needs an explicit suffix (`sed -i '' ...`); prefer the Edit tool for in-place edits.
35	- In a chained command, read each step's output before trusting the last one: an earlier step
36	  can fail while the final command still runs.
37	
38	### Helper scripts
39	
40	- `.lithify/harness/scripts/survey.py`
41	<!-- lithify:end -->
42	
[assistant] The key convention is in `app/audit.py`: every rejected input must be passed to `record_rejection(field, value, reason)` before raising. `parse_name` skips this, but its docstring says that's a legacy gap, so the new code should follow the policy. Next I'll get a baseline test run.
[tool_use Bash] {"command": "python -m pytest -q 2>&1 | tail -15; cat conftest.py; git log --oneline -3 -- app/audit.py", "description": "Run baseline test suite and check audit history"}
[tool_result] ......                                                                   [100%]
6 passed in 0.01s
# Root conftest: puts the repository root on sys.path so tests can `import app`.
d2ee313 fixture
[assistant] Baseline is 6 passing. Now I'll add `parse_age` with the audit call on every rejection path.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/inv-1/app/users.py", "old_string": "from app.errors import ValidationError\n\n\ndef parse_name(value: str) -> str:", "new_string": "import re\n\nfrom app.audit import record_rejection\nfrom app.errors import ValidationError\n\n_DECIMAL_DIGITS = re.compile(r\"[0
…[504 chars elided]…
   age = value\n    else:\n        record_rejection(\"age\", value, \"age must be an int or a string\")\n        raise ValidationError(\"age must be an int or a string\")\n    if not 0 <= age <= 150:\n        record_rejection(\"age\", value, \"age must be between 0 and 150\")\n        raise ValidationError(\"age must be between 0 and 150\")\n    return age\n\n\ndef parse_name(value: str) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/inv-1/app/users.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Next, tests for the new function. I'm only adding to the test file and not touching the existing tests. I'll also check the audit log in the tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/inv-1/tests/test_users.py", "old_string": "from app.users import parse_name\n", "new_string": "from app import audit\nfrom app.users import parse_age, parse_name\n"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/inv-1/tests/test_users.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/inv-1/tests/test_users.py", "old_string": "@pytest.mark.parametrize(\"bad\", [\"\", \"   \", \"x\" * 81, None, 42])\ndef test_parse_name_rejects(bad):\n    with pytest.raises(ValidationError):\n        parse_name(bad)\n", "new_string": "@pytest.mark.parametrize
…[400 chars elided]…
st.mark.parametrize(\n    \"bad\",\n    [None, 4.5, True, False, [42], \"\", \"   \", \"-1\", \"+5\", \"4a\", \"1 2\", \"151\", 151, -1, 1000],\n)\ndef test_parse_age_rejects(bad):\n    before = len(audit.REJECTIONS)\n    with pytest.raises(ValidationError):\n        parse_age(bad)\n    assert audit.REJECTIONS[before][\"field\"] == \"age\"\n    assert audit.REJECTIONS[before][\"value\"] is bad\n"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130202-add-parse-age-value-to-app-users/inv-1/tests/test_users.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Now I'll run the project checks, then exercise the function directly against each clause and read the output.
[tool_use Bash] {"command": "python -m pytest -q 2>&1 | tail -15", "description": "Run project test suite"}
[tool_result] ............................                                             [100%]
28 passed in 0.01s
[tool_use Bash] {"command": "python -I -c '\nimport sys; sys.path.insert(0, \".\")\nfrom app import audit\nfrom app.errors import ValidationError\nfrom app.users import parse_age\nfor v in [0, 150, \"42\", \" 42\\n\", \"007\", 42, True, None, 4.5, \"\", \"-1\", \"+5\", \"4a\", \"151\", 151, -1]:\n    try:\n        print(\"ACCEPT\", repr(v), \"->\", repr(parse_age(v)))\n    except ValidationError as e:\n        print(\"REJECT\", repr(v), \"->\", type(e).__name__, str(e))\nprint(\"audit entries:\", len(audit.REJECTIONS))\nprint(\"last:\", audit.REJECTIONS[-1])\n' 2>&1; git diff --stat", "description": "Exercise parse_age on accepted and rejected inputs"}
[tool_result] ACCEPT 0 -> 0
ACCEPT 150 -> 150
ACCEPT '42' -> 42
ACCEPT ' 42\n' -> 42
ACCEPT '007' -> 7
ACCEPT 42 -> 42
REJECT True -> ValidationError age must be an int or a string
REJECT None -> ValidationError age must be an int or a string
REJECT 4.5 -> ValidationError age must be an int or a string
REJECT '' -> ValidationError age must be a whole number
REJECT '-1' -> ValidationError age must be a whole number
REJECT '+5' -> ValidationError age must be a whole number
REJECT '4a' -> ValidationError age must be a whole number
REJECT '151' -> ValidationError age must be between 0 and 150
REJECT 151 -> ValidationError age must be between 0 and 150
REJECT -1 -> ValidationError age must be between 0 and 150
audit entries: 10
last: {'field': 'age', 'value': -1, 'reason': 'age must be between 0 and 150'}
app/users.py        | 24 ++++++++++++++++++++++++
 tests/test_users.py | 23 ++++++++++++++++++++++-
 2 files changed, 46 insertions(+), 1 deletion(-)
[assistant] `parse_age` is in `app/users.py`, and it matches every clause of the task. The project suite passes: 28 tests, the 6 original plus the new ones.

**What it does**
- Accepts an int, or a string of decimal digits with optional surrounding whitespace, and returns an int.
- Valid ages are 0 to 150 inclusive.
- Rejects with `ValidationError`: other types (including `None` and floats), booleans, empty or whitespace-only strings, non-digit strings (`"-1"`, `"+5"`, `"4a"`, `"1 2"`), and ages outside 0 to 150.

**Repo convention followed**
- `app/audit.py` says every rejected input must go through `rec
…[322 chars elided]…
put. Accepted: `0`, `150`, `"42"`, `" 42\n"`, `"007"`, `42`. Rejected with the expected messages: `True`, `None`, `4.5`, `""`, `"-1"`, `"+5"`, `"4a"`, `"151"`, `151`, `-1`. Each rejection added one audit entry.

**Changes**
- `app/users.py`: the new function, plus `re` and `audit` imports.
- `tests/test_users.py`: new parametrized tests for accepted and rejected inputs, including the audit-record check. The only edit to existing lines is the import line, which now also imports `parse_age`. No existing test was changed.

I haven't committed anything. The working tree has the two modified files.
