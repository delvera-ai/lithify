# trajectory base-1

final message:
I added `parse_email(value)` to `app/users.py`. The full suite passes (51 tests), and the audit invariant check passes for the new function.

- **Behaviour:** it strips and lowercases the string, then rejects non-strings, inner whitespace, anything other than exactly one `@`, an empty local part, and a domain with no dot or a dot at its start or end. Each rejection calls `record_rejection("email", <original value>, <reason>)` before raising `ValidationError`, following the audit policy in `CLAUDE.md`.
- **Tests:** I added accept and reject cases to `tests/test_users.py`. The reject tests check that the audit entry's `value` is the original input and that its `reason` matches the error message.
- **Direct calls:** I called the function on sample inputs of each kind and read the output. Valid input returns the normalised address, and each invalid kind raises with the expected message.

Choices I made that you didn't specify:
- **Whitespace check:** it runs after stripping, so only whitespace inside the address is rejected. A value that is only whitespace is rejected by the `@` count instead.
- **Error messages:** I wrote them in the same style as `parse_age`.
- **Structure:** I wrote the `record_rejection` calls inline, as `parse_age` does, rather than adding a helper.

## events
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130825-add-parse-email-value-to-app-use/base-1/app/users.py"}
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130825-add-parse-email-value-to-app-use/base-1/app/audit.py"}
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130825-add-parse-email-value-to-app-use/base-1/app/errors.py"}
[tool_result] 1	class AppError(Exception):
2	    """Base class for every error this service raises on purpose."""
3	
4	
5	class ValidationError(AppError):
6	    """User input was rejected."""
7	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130825-add-parse-email-value-to-app-use/base-1/README.md"}
[tool_result] 1	# accounts service
2	
3	Input parsing for the accounts service. Run the tests with `python3 -m pytest -q`.
4	
[tool_use Skill] {"skill": "input-validation"}
[tool_result] Launching skill: input-validation
[user] Base directory for this skill: ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130825-add-parse-email-value-to-app-use/base-1/.claude/skills/input-validation

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

[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130825-add-parse-email-value-to-app-use/base-1/tests/test_users.py"}
[tool_result] 1	import pytest
2	from app.audit import REJECTIONS
3	from app.errors import ValidationError
4	from app.users import parse_age, parse_name
5	
6	
7	def test_parse_name_strips():
8	    assert parse_name("  Ada Lovelace ") == "Ada Lovelace"
9	
10	
11	@pytest.mark.parametrize("bad", ["", "   ", "x" * 81, None, 42])
12	def test_parse_name_rejects(bad):
13	    with pytest.raises(ValidationError):
14	        parse_name(bad)
15	
16	
17	@pytest.mark.parametrize(
18	    "good, expected",
19	    [(0, 0), (4
…[459 chars elided]…
1	        "+5",
42	        "151",
43	        "12 34",
44	        "٣",  # Arabic-Indic digit three: decimal, but not ASCII
45	    ],
46	)
47	def test_parse_age_rejects_and_audits(bad):
48	    before = len(REJECTIONS)
49	    with pytest.raises(ValidationError) as excinfo:
50	        parse_age(bad)
51	    assert len(REJECTIONS) == before + 1
52	    entry = REJECTIONS[-1]
53	    assert entry["field"] == "age"
54	    assert entry["value"] is bad
55	    assert entry["reason"] == str(excinfo.value)
56	
[tool_use Bash] {"command": "ls -la .lithify/harness/skills/input-validation/scripts/ 2>&1; ls .lithify 2>&1; git status --short", "description": "List validator scripts and repo status"}
[tool_result] check_audit.py  2.6K
harness/
library/
state.json  443B
ok
[assistant] Now I'll add the validator, recording each rejection before it raises.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130825-add-parse-email-value-to-app-use/base-1/app/users.py", "old_string": "        raise ValidationError(\"age must be between 0 and 150\")\n    return age\n", "new_string": "        raise ValidationError(\"age must be between 0 and 150\")\n    return age\n\n\ndef parse_email(value) -> str:\n    \"
…[806 chars elided]…
ave a part before the @\")\n        raise ValidationError(\"email must have a part before the @\")\n    if \".\" not in domain or domain.startswith(\".\") or domain.endswith(\".\"):\n        record_rejection(\"email\", value, \"email domain must contain a dot not at its start or end\")\n        raise ValidationError(\"email domain must contain a dot not at its start or end\")\n    return email\n"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130825-add-parse-email-value-to-app-use/base-1/app/users.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "ls .lithify/harness/skills/input-validation/ 2>&1; ls .lithify/harness/skills/input-validation/scripts; cat .lithify/harness/skills/input-validation/memory.md 2>&1 | head -20", "description": "Find the python interpreter note for the audit check"}
[tool_result] scripts/
SKILL.md  2.9K
check_audit.py  2.6K
cat: .lithify/harness/skills/input-validation/memory.md: No such file or directory (os error 2)
[assistant] Next, the tests. I'm adding `parse_email` to the import line and accept/reject cases that check the audit entry.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130825-add-parse-email-value-to-app-use/base-1/tests/test_users.py", "old_string": "from app.users import parse_age, parse_name\n", "new_string": "from app.users import parse_age, parse_email, parse_name\n"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-130825-add-parse-email-value-to-app-use/base-1/tests/test_users.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "cat >> tests/test_users.py << 'EOF'\n\n\n@pytest.mark.parametrize(\n    \"good, expected\",\n    [\n        (\"ada@example.com\", \"ada@example.com\"),\n        (\"  Ada@Example.COM  \", \"ada@example.com\"),\n        (\"a.b+c@sub.example.org\", \"a.b+c@sub.example.org\"),\n    ],\n)\ndef test_parse_email_accepts(good, expected):\n    assert parse_email(good) == expected\n\n\n@pytest.
…[618 chars elided]…
 excinfo:\n        parse_email(bad)\n    assert len(REJECTIONS) == before + 1\n    entry = REJECTIONS[-1]\n    assert entry[\"field\"] == \"email\"\n    assert entry[\"value\"] is bad\n    assert entry[\"reason\"] == str(excinfo.value)\nEOF\npython -m pytest -q 2>&1 | tail -30", "description": "Append email tests and run the test suite"}
[tool_result] ...................................................                      [100%]
51 passed in 0.02s
[assistant] Tests pass (51). Next I'll run the audit invariant checker and call the function directly on each input kind.
[tool_use Bash] {"command": "python .lithify/harness/skills/input-validation/scripts/check_audit.py app/users.py --only parse_email; echo \"exit=$?\"; python -I -c '\nfrom app.users import parse_email\nfrom app.audit import REJECTIONS\nfrom app.errors import ValidationError\ncases = [None, 42, \"  Ada@Example.COM \", \"a b@x.com\", \"a@b@c.com\", \"@x.com\", \"a@xcom\", \"a@.x.com\", \"a@x.\", \"ok@x.org\"]\nfor c in cases:\n    try:\n        print(repr(c), \"->\", repr(parse_email(c)))\n    except ValidationError as e:\n        print(repr(c), \"-> ValidationError:\", e)\nprint(REJECTIONS[-1])\n'", "description": "Run audit checker and direct calls on sample inputs"}
[tool_result ERROR] Exit code 1
ok: every checked ValidationError raise is preceded by record_rejection(...)
exit=0
Traceback (most recent call last):
  File "<string>", line 2, in <module>
    from app.users import parse_email
ModuleNotFoundError: No module named 'app'
[assistant] The audit check passes. The direct-call run failed only because `-I` drops the working directory from the import path, so I'll rerun it without that flag.
[tool_use Bash] {"command": "python -c '\nfrom app.users import parse_email\nfrom app.audit import REJECTIONS\nfrom app.errors import ValidationError\ncases = [None, 42, \"  Ada@Example.COM \", \"a b@x.com\", \"a@b@c.com\", \"@x.com\", \"a@xcom\", \"a@.x.com\", \"a@x.\", \"ok@x.org\"]\nfor c in cases:\n    try:\n        print(repr(c), \"->\", repr(parse_email(c)))\n    except ValidationError as e:\n        print(repr(c), \"-> ValidationError:\", e)\nprint(REJECTIONS[-1])\n'", "description": "Call parse_email directly on sample inputs"}
[tool_result] None -> ValidationError: email must be a string
42 -> ValidationError: email must be a string
'  Ada@Example.COM ' -> 'ada@example.com'
'a b@x.com' -> ValidationError: email must not contain whitespace
'a@b@c.com' -> ValidationError: email must contain exactly one @
'@x.com' -> ValidationError: email must have a part before the @
'a@xcom' -> ValidationError: email domain must contain a dot not at its start or end
'a@.x.com' -> ValidationError: email domain must contain a dot not at its start or end
'a@x.' -> ValidationError: email domain must contain a dot not at its start or end
'ok@x.org' -> 'ok@x.org'
{'field': 'email', 'value': 'a@x.', 'reason': 'email domain must contain a dot not at its start or end'}
[assistant] I added `parse_email(value)` to `app/users.py`. The full suite passes (51 tests), and the audit invariant check passes for the new function.

- **Behaviour:** it strips and lowercases the string, then rejects non-strings, inner whitespace, anything other than exactly one `@`, an empty local part, and a domain with no dot or a dot at its start or end. Each rejection calls `record_rejection("email", <original value>, <reason>)` before raising `ValidationError`, following the audit policy in `CLAUDE.md`.
- **Tests:** I added accept and reject cases to `tests/test_users.py`. The reject tests check
…[87 chars elided]…
 error message.
- **Direct calls:** I called the function on sample inputs of each kind and read the output. Valid input returns the normalised address, and each invalid kind raises with the expected message.

Choices I made that you didn't specify:
- **Whitespace check:** it runs after stripping, so only whitespace inside the address is rejected. A value that is only whitespace is rejected by the `@` count instead.
- **Error messages:** I wrote them in the same style as `parse_age`.
- **Structure:** I wrote the `record_rejection` calls inline, as `parse_age` does, rather than adding a helper.
