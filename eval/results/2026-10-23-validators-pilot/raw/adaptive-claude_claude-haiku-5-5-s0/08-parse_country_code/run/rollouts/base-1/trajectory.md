# trajectory base-1

final message:
I added `parse_country_code(value)` to `app/addresses.py`. The full suite passes (208 tests), and the audit checker reports no unrecorded rejections for the new function.

**Behaviour**
- Surrounding whitespace is stripped, then the value must match exactly two ASCII letters. The result is uppercased, so `"gb"` and `" us "` give `"GB"` and `"US"`.
- Non-strings raise `ValidationError("country code must be a string")`.
- Anything else raises `ValidationError("country code must be exactly two ASCII letters")`. That covers `"GBR"`, `"G1"`, `"G B"`, `"ÄB"` and fullwidth `"ＧＢ"`.
- Every rejection calls `record_rejection` first, with the original argument as `value`, and the error message as `reason`.

**Choices I made**
- The audit field is `"country code"` (with a space), matching the noun in the error message as the input-validation guidance says. The other validators use single words, so rename it to `"country_code"` if you prefer that style.
- The regex is `[A-Za-z]{2}`, not `\d`-style or `str.isalpha()`, so non-ASCII letters are rejected by construction.

**Tests**
- `tests/test_addresses.py` gained accept cases (case folding, whitespace) and reject cases that also check the audit entry, following the postcode tests. The existing tests are unchanged.

**Direct calls** (run against the real function): `'gb'` → `'GB'`, `' us '` → `'US'`, `'Gb'` → `'GB'`. `None`, `42`, `'GBR'`, `'ÄB'` and `'G1'` raised `ValidationError`, and each left one audit entry.

I did not commit anything.

## events
[assistant] I'll start by reading the validation skill, the existing modules, and the README, since the project instructions require them.
[tool_use Skill] {"skill": "input-validation"}
[tool_result] Launching skill: input-validation
[user] Base directory for this skill: ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131215-add-parse-country-code-value-to/base-1/.claude/skills/input-validation

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

[tool_use Bash] {"command": "ls -la app tests && wc -l app/*.py README.md && git status --short && git log --oneline -3", "description": "List app and test files and git state"}
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131215-add-parse-country-code-value-to/base-1/README.md"}
[tool_result] 1	# accounts service
2	
3	Input parsing for the accounts service. Run the tests with `python3 -m pytest -q`.
4	
[tool_result] __init__.py  0B
addresses.py  797B
audit.py  473B
errors.py  166B
orders.py  2.8K
users.py  3.8K
test_addresses.py  1.2K
test_orders.py  2.7K
test_users.py  4.5K
0 app/__init__.py
18 app/addresses.py
12 app/audit.py
6 app/errors.py
60 app/orders.py
82 app/users.py
3 README.md
Σ 181
ok1a04248 lithify: probe base
7e314a9 eval: configure parse_country_code
6479d83 eval: task 7 parse_postcode
[assistant] The skill requires `record_rejection` before every `ValidationError` raise. Next I'll read the domain module, audit and error modules, and the existing tests.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131215-add-parse-country-code-value-to/base-1/app/addresses.py"}
[tool_result] 1	import re
2	
3	from app.audit import record_rejection
4	from app.errors import ValidationError
5	
6	POSTCODE_PATTERN = re.compile(r"[0-9]{5}(?:-[0-9]{4})?")
7	
8	
9	def parse_postcode(value) -> str:
10	    """Return a US ZIP code: surrounding whitespace removed, five digits optionally followed by a hyphen and four digits."""
11	    if not isinstance(value, str):
12	        record_rejection("postcode", value, "postcode must be a string")
13	        raise ValidationError("postcode must be a string")
14	    postcode = value.strip()
15	    if not POSTCODE_PATTERN.fullmatch(postcode):
16	        record_rejection("postcode", value, "postcode must be 5 digits, optionally followed by a hyphen and 4 digits")
17	        raise ValidationError("postcode must be 5 digits, optionally followed by a hyphen and 4 digits")
18	    return postcode
19	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131215-add-parse-country-code-value-to/base-1/app/audit.py"}
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131215-add-parse-country-code-value-to/base-1/app/errors.py"}
[tool_result] 1	class AppError(Exception):
2	    """Base class for every error this service raises on purpose."""
3	
4	
5	class ValidationError(AppError):
6	    """User input was rejected."""
7	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131215-add-parse-country-code-value-to/base-1/app/users.py"}
[tool_result] 1	import re
2	
3	from app.audit import record_rejection
4	from app.errors import ValidationError
5	
6	USERNAME_PATTERN = re.compile(r"[a-z][a-z0-9_]{2,19}")
7	
8	
9	def parse_name(value: str) -> str:
10	    """Return a display name: surrounding whitespace removed, 1-80 characters."""
11	    if not isinstance(value, str):
12	        raise ValidationError("name must be a string")
13	    name = value.strip()
14	    if not 1 <= len(name) <= 80:
15	        raise ValidationError("name must be 1-80 cha
…[3140 chars elided]…
   record_rejection("username", value, "username must be a string")
77	        raise ValidationError("username must be a string")
78	    username = value.strip()
79	    if not USERNAME_PATTERN.fullmatch(username):
80	        record_rejection("username", value, "username must be 3-20 lowercase letters, digits or underscores, starting with a letter")
81	        raise ValidationError("username must be 3-20 lowercase letters, digits or underscores, starting with a letter")
82	    return username
83	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131215-add-parse-country-code-value-to/base-1/tests/test_addresses.py"}
[tool_result] 1	import pytest
2	from app.addresses import parse_postcode
3	from app.audit import REJECTIONS
4	from app.errors import ValidationError
5	
6	
7	@pytest.mark.parametrize(
8	    "good, expected",
9	    [
10	        ("12345", "12345"),
11	        ("12345-6789", "12345-6789"),
12	        (" 12345 ", "12345"),
13	        ("\t12345-6789\n", "12345-6789"),
14	        ("00501", "00501"),
15	    ],
16	)
17	def test_parse_postcode_accepts(good, expected):
18	    assert parse_postcode(good) == expected
19	

…[395 chars elided]…
	        "+12345",
41	        "12345+",
42	        "١٢٣٤٥",  # Arabic-Indic digits: decimal, but not ASCII
43	    ],
44	)
45	def test_parse_postcode_rejects_and_audits(bad):
46	    before = len(REJECTIONS)
47	    with pytest.raises(ValidationError) as excinfo:
48	        parse_postcode(bad)
49	    assert len(REJECTIONS) == before + 1
50	    entry = REJECTIONS[-1]
51	    assert entry["field"] == "postcode"
52	    assert entry["value"] is bad
53	    assert entry["reason"] == str(excinfo.value)
54	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131215-add-parse-country-code-value-to/base-1/tests/test_users.py"}
[tool_result] 1	import pytest
2	from app.audit import REJECTIONS
3	from app.errors import ValidationError
4	from app.users import parse_age, parse_email, parse_name, parse_phone, parse_username
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
1
…[4317 chars elided]…
etter
181	        "ab١",  # Arabic-Indic digit one: decimal, but not ASCII
182	        "abc@",
183	    ],
184	)
185	def test_parse_username_rejects_and_audits(bad):
186	    before = len(REJECTIONS)
187	    with pytest.raises(ValidationError) as excinfo:
188	        parse_username(bad)
189	    assert len(REJECTIONS) == before + 1
190	    entry = REJECTIONS[-1]
191	    assert entry["field"] == "username"
192	    assert entry["value"] is bad
193	    assert entry["reason"] == str(excinfo.value)
194	
[tool_use Bash] {"command": "ls -la .lithify/harness/skills/input-validation/scripts/ 2>&1; ls python 2>&1", "description": "Check audit check script and project venv python exist"}
[tool_result] check_audit.py  2.6K
python -> ~/.local/share/uv/python/cpython-3.14-macos-aarch64-none/bin/python3.14  84B
[assistant] I have the picture now. `addresses.py` currently holds only `parse_postcode`, which is the pattern to follow with audit calls before each raise. I'll add the pattern constant and the new function, then the tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131215-add-parse-country-code-value-to/base-1/app/addresses.py", "old_string": "POSTCODE_PATTERN = re.compile(r\"[0-9]{5}(?:-[0-9]{4})?\")\n", "new_string": "POSTCODE_PATTERN = re.compile(r\"[0-9]{5}(?:-[0-9]{4})?\")\nCOUNTRY_CODE_PATTERN = re.compile(r\"[A-Za-z]{2}\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131215-add-parse-country-code-value-to/base-1/app/addresses.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131215-add-parse-country-code-value-to/base-1/app/addresses.py", "old_string": "        record_rejection(\"postcode\", value, \"postcode must be 5 digits, optionally followed by a hyphen and 4 digits\")\n        raise ValidationError(\"postcode must be 5 digits, optionally followed by a hyphen and 4 
…[545 chars elided]…
, value, \"country code must be a string\")\n        raise ValidationError(\"country code must be a string\")\n    code = value.strip()\n    if not COUNTRY_CODE_PATTERN.fullmatch(code):\n        record_rejection(\"country code\", value, \"country code must be exactly two ASCII letters\")\n        raise ValidationError(\"country code must be exactly two ASCII letters\")\n    return code.upper()\n"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131215-add-parse-country-code-value-to/base-1/app/addresses.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Now the tests: I'm adding the function to the existing import line and adding accept and reject-and-audit cases in the same style as the postcode tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131215-add-parse-country-code-value-to/base-1/tests/test_addresses.py", "old_string": "from app.addresses import parse_postcode\n", "new_string": "from app.addresses import parse_country_code, parse_postcode\n"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131215-add-parse-country-code-value-to/base-1/tests/test_addresses.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131215-add-parse-country-code-value-to/base-1/tests/test_addresses.py", "old_string": "def test_parse_postcode_rejects_and_audits(bad):\n    before = len(REJECTIONS)\n    with pytest.raises(ValidationError) as excinfo:\n        parse_postcode(bad)\n    assert len(REJECTIONS) == before + 1\n    entry 
…[1224 chars elided]…
ot ASCII\n    ],\n)\ndef test_parse_country_code_rejects_and_audits(bad):\n    before = len(REJECTIONS)\n    with pytest.raises(ValidationError) as excinfo:\n        parse_country_code(bad)\n    assert len(REJECTIONS) == before + 1\n    entry = REJECTIONS[-1]\n    assert entry[\"field\"] == \"country code\"\n    assert entry[\"value\"] is bad\n    assert entry[\"reason\"] == str(excinfo.value)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131215-add-parse-country-code-value-to/base-1/tests/test_addresses.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Next I'll run the project's test command, the audit-invariant checker, and a direct call on each input kind the task names.
[tool_use Bash] {"command": "PY=python; $PY -m pytest -q 2>&1 | tail -15; echo \"--- audit check\"; $PY .lithify/harness/skills/input-validation/scripts/check_audit.py app/addresses.py --only parse_country_code 2>&1; echo \"exit=$?\"; echo \"--- direct calls\"; $PY -c '\nfrom app.addresses import parse_country_code as p\nfrom app.audit import REJECTIONS\nfor v in [\"gb\",\" us \",\"Gb\", None, 42, \"GBR\", \"\u00c4B\", \"G1\"]:\n    try:\n        print(repr(v), \"->\", repr(p(v)))\n    except Exception as e:\n        print(repr(v), \"-> raised\", type(e).__name__, e)\nprint(\"audit entries:\", len(REJECTIONS))\nfor r in REJECTIONS: print(r)\n'", "description": "Run tests, audit checker, and direct function calls"}
[tool_result] ........................................................................ [ 34%]
........................................................................ [ 69%]
................................................................         [100%]
208 passed in 0.06s
--- audit check
ok: every checked ValidationError raise is preceded by record_rejection(...)
exit=0
--- direct calls
'gb' -> 'GB'
' us ' -> 'US'
'Gb' -> 'GB'
None -> raised ValidationError country code must be a string
42 -> raised Validati
…[259 chars elided]…
ASCII letters
audit entries: 5
{'field': 'country code', 'value': None, 'reason': 'country code must be a string'}
{'field': 'country code', 'value': 42, 'reason': 'country code must be a string'}
{'field': 'country code', 'value': 'GBR', 'reason': 'country code must be exactly two ASCII letters'}
{'field': 'country code', 'value': 'ÄB', 'reason': 'country code must be exactly two ASCII letters'}
{'field': 'country code', 'value': 'G1', 'reason': 'country code must be exactly two ASCII letters'}
[assistant] I added `parse_country_code(value)` to `app/addresses.py`. The full suite passes (208 tests), and the audit checker reports no unrecorded rejections for the new function.

**Behaviour**
- Surrounding whitespace is stripped, then the value must match exactly two ASCII letters. The result is uppercased, so `"gb"` and `" us "` give `"GB"` and `"US"`.
- Non-strings raise `ValidationError("country code must be a string")`.
- Anything else raises `ValidationError("country code must be exactly two ASCII letters")`. That covers `"GBR"`, `"G1"`, `"G B"`, `"ÄB"` and fullwidth `"ＧＢ"`.
- Every rejection c
…[300 chars elided]…
ename it to `"country_code"` if you prefer that style.
- The regex is `[A-Za-z]{2}`, not `\d`-style or `str.isalpha()`, so non-ASCII letters are rejected by construction.

**Tests**
- `tests/test_addresses.py` gained accept cases (case folding, whitespace) and reject cases that also check the audit entry, following the postcode tests. The existing tests are unchanged.

**Direct calls** (run against the real function): `'gb'` → `'GB'`, `' us '` → `'US'`, `'Gb'` → `'GB'`. `None`, `42`, `'GBR'`, `'ÄB'` and `'G1'` raised `ValidationError`, and each left one audit entry.

I did not commit anything.
