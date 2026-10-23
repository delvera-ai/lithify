# trajectory base-1

final message:
`parse_phone(value)` is added to `app/users.py`, and the full test suite passes (72 tests).

- **Behaviour:** removes spaces, hyphens and parentheses, keeps an optional leading `+`, and requires 7–15 ASCII digits after that. For example, `"+1 (555) 010-9999"` returns `"+15550109999"`.
- **Rejections:** non-strings, letters, other punctuation, a `+` anywhere but the start, and digit counts outside 7–15 all raise `ValidationError`.
- **Audit:** I followed the project's audit policy rather than the `parse_name` pattern. Every rejection calls `record_rejection("phone", value, reason)` with the original input first. The audit checker reports no unrecorded raises in `parse_phone`.
- **Tests:** I added accept and reject cases to `tests/test_users.py`, and the rejection tests check the audit entry. I did not change any existing tests.

I called the function directly on valid, non-string, letter-containing and out-of-range inputs, and the outputs matched the rules above.

I chose a single error message for all format and length failures, and kept spaces as the only whitespace being stripped, as the spec said. Tabs are rejected rather than stripped. Say if you want tabs stripped too.

## events
[assistant] I'll read the project files and the validation skill first, since the project rules require an audit call for every rejection.
[tool_use Bash] {"command": "ls -la && ls app tests && cat README.md", "description": "List repo layout and read README"}
[tool_use Skill] {"skill": "input-validation"}
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130909-add-parse-phone-value-to-app-use/base-1/app/users.py"}
[tool_result] .agents/
.claude/
.lithify/
app/
tests/
.git  114B
.gitignore  105B
AGENTS.md  2.0K
CLAUDE.md  2.0K
README.md  103B
conftest.py  81B
__init__.py  0B
audit.py  473B
errors.py  166B
orders.py  385B
users.py  2.3K
test_users.py  2.4K
# accounts service

Input parsing for the accounts service. Run the tests with `python3 -m pytest -q`.
[tool_result] Launching skill: input-validation
[user] Base directory for this skill: ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130909-add-parse-phone-value-to-app-use/base-1/.claude/skills/input-validation

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
…[1553 chars elided]…
 domain = email.split("@")
47	    if not local:
48	        record_rejection("email", value, "email must have a part before the @")
49	        raise ValidationError("email must have a part before the @")
50	    if "." not in domain or domain.startswith(".") or domain.endswith("."):
51	        record_rejection("email", value, "email domain must contain a dot not at its start or end")
52	        raise ValidationError("email domain must contain a dot not at its start or end")
53	    return email
54	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130909-add-parse-phone-value-to-app-use/base-1/app/audit.py"}
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130909-add-parse-phone-value-to-app-use/base-1/app/errors.py"}
[tool_result] 1	class AppError(Exception):
2	    """Base class for every error this service raises on purpose."""
3	
4	
5	class ValidationError(AppError):
6	    """User input was rejected."""
7	
[assistant] The skill confirms the rule: every `raise ValidationError` needs a `record_rejection` call first, with the original value. Next I'll read the existing tests and the sibling `orders.py` before writing anything.
[tool_use Bash] {"command": "cat tests/test_users.py && echo ---ORDERS--- && cat app/orders.py && echo ---CONFTEST--- && cat conftest.py && echo ---AGENTS--- && cat AGENTS.md && echo ---CLAUDE--- && cat CLAUDE.md | head -5 && ls .lithify .lithify/harness/skills/input-validation/scripts 2>&1; git log --oneline -3", "description": "Read tests, orders module, and config files"}
[tool_result] import pytest
from app.audit import REJECTIONS
from app.errors import ValidationError
from app.users import parse_age, parse_email, parse_name


def test_parse_name_strips():
    assert parse_name("  Ada Lovelace ") == "Ada Lovelace"


@pytest.mark.parametrize("bad", ["", "   ", "x" * 81, None, 42])
def test_parse_name_rejects(bad):
    with pytest.raises(ValidationError):
        parse_name(bad)


@pytest.mark.parametrize(
    "good, expected",
    [(0, 0), (42, 42), (150, 150), ("0", 0), ("150
…[4259 chars elided]…
 Load when adding or changing any function in app/ that parses or validates user input (parse_* functions, anything that raises ValidationError), or when writing tests for one.
<!-- lithify:end -->
---CLAUDE---
<!-- lithify:begin — managed by `lithify sync`; edit .lithify/harness/ instead -->
## Project harness (lithify)

### Role and procedure

harness/
library/
state.json  830B
check_audit.py  2.6K
6068eb9 lithify: probe base
08c2be0 eval: configure parse_phone
f9c1f2d eval: task 2 parse_email
[assistant] I have the full picture. `parse_phone` will follow the audited pattern from `parse_age` and `parse_email`, not the raise-only style of `parse_name`. I'll add it after `parse_email`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130909-add-parse-phone-value-to-app-use/base-1/app/users.py", "old_string": "        record_rejection(\"email\", value, \"email domain must contain a dot not at its start or end\")\n        raise ValidationError(\"email domain must contain a dot not at its start or end\")\n    return email\n", "new_s
…[588 chars elided]…
oin(ch for ch in value if ch not in \" -()\")\n    digits = phone[1:] if phone.startswith(\"+\") else phone\n    if not (digits.isascii() and digits.isdigit() and 7 <= len(digits) <= 15):\n        record_rejection(\"phone\", value, \"phone must be 7-15 digits with an optional leading +\")\n        raise ValidationError(\"phone must be 7-15 digits with an optional leading +\")\n    return phone\n"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130909-add-parse-phone-value-to-app-use/base-1/app/users.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Next, the tests: I'm adding `parse_phone` to the existing import line and adding accept and reject cases in the same style as the others.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130909-add-parse-phone-value-to-app-use/base-1/tests/test_users.py", "old_string": "from app.users import parse_age, parse_email, parse_name\n", "new_string": "from app.users import parse_age, parse_email, parse_name, parse_phone\n"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130909-add-parse-phone-value-to-app-use/base-1/tests/test_users.py has been updated successfully.
[tool_use Bash] {"command": "cat >> tests/test_users.py <<'EOF'\n\n\n@pytest.mark.parametrize(\n    \"good, expected\",\n    [\n        (\"5550100\", \"5550100\"),\n        (\"+1 (555) 010-9999\", \"+15550109999\"),\n        (\" 020 7946 0958 \", \"02079460958\"),\n        (\"555-0100\", \"5550100\"),\n        (\"+\" + \"1\" * 15, \"+\" + \"1\" * 15),\n        (\"1\" * 15, \"1\" * 15),\n    ],\n)\ndef test_parse_
…[941 chars elided]…
& python -m pytest -q 2>&1 | tail -15; echo \"pytest exit: ${PIPESTATUS[0]}\"; python -I .lithify/harness/skills/input-validation/scripts/check_audit.py app/users.py --only parse_phone; echo \"audit exit: $?\"", "description": "Append phone tests, run pytest and audit checker"}
[tool_result] python
........................................................................ [100%]
72 passed in 0.03s
pytest exit: 
ok: every checked ValidationError raise is preceded by record_rejection(...)
audit exit: 0
[assistant] All 72 tests pass and the audit checker is clean. The test file changed on disk mid-session (the Arabic-digit case is now a literal `"٣"` instead of the `\u0663` escape). It's the same test value, so I'm leaving it as is. Last, the project asks me to call the function directly on each input kind and read the output.
[tool_use Bash] {"command": "python -c '\nfrom app.users import parse_phone\nfrom app.audit import REJECTIONS\nfrom app.errors import ValidationError\ncases = [\"+1 (555) 010-9999\", \" 020 7946 0958 \", \"555-0100\", \"123456\", \"5550+100\", None, 5550100, \"call 5550100\", \"+\"]\nfor c in cases:\n    try:\n        print(repr(c), \"->\", repr(parse_phone(c)))\n    except ValidationError as e:\n        print(repr(c), \"-> ValidationError:\", e)\nprint(\"audit entries:\", len(REJECTIONS), REJECTIONS[-1])\n'", "description": "Call parse_phone directly on sample input kinds"}
[tool_result] '+1 (555) 010-9999' -> '+15550109999'
' 020 7946 0958 ' -> '02079460958'
'555-0100' -> '5550100'
'123456' -> ValidationError: phone must be 7-15 digits with an optional leading +
'5550+100' -> ValidationError: phone must be 7-15 digits with an optional leading +
None -> ValidationError: phone must be a string
5550100 -> ValidationError: phone must be a string
'call 5550100' -> ValidationError: phone must be 7-15 digits with an optional leading +
'+' -> ValidationError: phone must be 7-15 digits with an optional leading +
audit entries: 6 {'field': 'phone', 'value': '+', 'reason': 'phone must be 7-15 digits with an optional leading +'}
[assistant] `parse_phone(value)` is added to `app/users.py`, and the full test suite passes (72 tests).

- **Behaviour:** removes spaces, hyphens and parentheses, keeps an optional leading `+`, and requires 7–15 ASCII digits after that. For example, `"+1 (555) 010-9999"` returns `"+15550109999"`.
- **Rejections:** non-strings, letters, other punctuation, a `+` anywhere but the start, and digit counts outside 7–15 all raise `ValidationError`.
- **Audit:** I followed the project's audit policy rather than the `parse_name` pattern. Every rejection calls `record_rejection("phone", value, reason)` with the original input first. The audit checker reports no unrecorded raises in `parse_phone`.
- **Tests:** I added accept and reject cases to `tests/test_users.py`, and the rejection tests check the audit entry. I did not change any existing tests.

I called the function directly on valid, non-string, letter-containing and out-of-range inputs, and the outputs matched the rules above.

I chose a single error message for all format and length failures, and kept spaces as the only whitespace being stripped, as the spec said. Tabs are rejected rather than stripped. Say if you want tabs stripped too.
