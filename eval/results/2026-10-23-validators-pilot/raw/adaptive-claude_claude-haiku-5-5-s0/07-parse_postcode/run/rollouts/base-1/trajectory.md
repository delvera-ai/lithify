# trajectory base-1

final message:
I added `parse_postcode(value)` in a new `app/addresses.py`. The full suite passes (189 tests, including the new ones), and the audit check reports no unrecorded rejections.

- **Behaviour:** the input is stripped, then must be five ASCII digits, optionally followed by a hyphen and four digits. The stripped string is returned. Non-strings, wrong lengths, non-digits and non-ASCII digits raise `ValidationError`.
- **Audit:** every rejection calls `record_rejection("postcode", value, reason)` first, with the original argument and the same text as the error message. This follows the repo's input-validation policy rather than the older `parse_name` and `parse_quantity` pattern.
- **Tests:** `tests/test_addresses.py` is new, following the `test_orders.py` / `test_users.py` style. It covers accepted forms and rejected inputs, and checks that each rejection adds one audit entry with the original value.
- **Direct calls:** I called the function on `"12345"`, `"  12345-6789 "`, `None`, `12345`, `"1234"`, `"12345-67890"` and Arabic-Indic digits. Each returned or raised as specified, and the audit list grew by one entry per rejection.

Choices I made that you may want to change: the field name is `"postcode"`, since the function name uses that term. The regex uses `[0-9]` rather than `\d` so that Unicode digits are rejected.

Nothing is committed.

## events
[tool_use Bash] {"command": "ls -la app tests && cat app/*.py && cat README.md && ls tests && cat tests/*.py | head -150", "description": "List app and tests, read sources and README"}
[tool_use Skill] {"skill": "input-validation"}
[tool_result] __init__.py  0B
audit.py  473B
errors.py  166B
orders.py  2.8K
users.py  3.8K
test_orders.py  2.7K
test_users.py  4.5K
"""Audit trail for rejected user input.

Policy: every rejected piece of user input must be recorded with
`record_rejection(field, value, reason)` before the error is raised, so that support can see
what users actually typed. Some older validators predate this policy and do not follow it yet.
"""

REJECTIONS: list[dict] = []


def record_rejection(field: str, value: object, reas
…[10117 chars elided]…
sername


def test_parse_name_strips():
    assert parse_name("  Ada Lovelace ") == "Ada Lovelace"


@pytest.mark.parametrize("bad", ["", "   ", "x" * 81, None, 42])
def test_parse_name_rejects(bad):
    with pytest.raises(ValidationError):
        parse_name(bad)


@pytest.mark.parametrize(
    "good, expected",
    [(0, 0), (42, 42), (150, 150), ("0", 0), ("150", 150), (" 42 ", 42), ("\t7\n", 7), ("0007", 7)],
)
def test_parse_age_accepts(good, expected):
    assert parse_age(good) == expected
[tool_result] Launching skill: input-validation
[user] Base directory for this skill: ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131152-create-app-addresses-py-with-par/base-1/.claude/skills/input-validation

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

[assistant] The skill's contract applies here: a new validator needs `record_rejection` before every raise, plus a test file. I'll check the audit-check script and the project's Python before writing anything.
[tool_use Bash] {"command": "ls -la .lithify/harness/skills/input-validation/scripts/ 2>&1; ls python 2>&1; git status --short; git log --oneline -1", "description": "Check audit script, venv python, and git state"}
[tool_result] check_audit.py  2.6K
python -> ~/.local/share/uv/python/cpython-3.14-macos-aarch64-none/bin/python3.14  84B
ok790a862 lithify: probe base
[assistant] Both exist and the tree is clean. Next I'll write the validator, following the `users.py` shape with `record_rejection` before every raise.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131152-create-app-addresses-py-with-par/base-1/app/addresses.py", "content": "import re\n\nfrom app.audit import record_rejection\nfrom app.errors import ValidationError\n\nPOSTCODE_PATTERN = re.compile(r\"[0-9]{5}(?:-[0-9]{4})?\")\n\n\ndef parse_postcode(value) -> str:\n    \"\"\"Return a US ZIP code: surrounding whitesp
…[192 chars elided]…
)\n        raise ValidationError(\"postcode must be a string\")\n    postcode = value.strip()\n    if not POSTCODE_PATTERN.fullmatch(postcode):\n        record_rejection(\"postcode\", value, \"postcode must be 5 digits, optionally followed by a hyphen and 4 digits\")\n        raise ValidationError(\"postcode must be 5 digits, optionally followed by a hyphen and 4 digits\")\n    return postcode\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131152-create-app-addresses-py-with-par/base-1/app/addresses.py (file state is current in your context — no need to Read it back)
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131152-create-app-addresses-py-with-par/base-1/tests/test_addresses.py", "content": "import pytest\nfrom app.addresses import parse_postcode\nfrom app.audit import REJECTIONS\nfrom app.errors import ValidationError\n\n\n@pytest.mark.parametrize(\n    \"good, expected\",\n    [\n        (\"12345\", \"12345\"),\n        (\"
…[752 chars elided]…
cimal, but not ASCII\n    ],\n)\ndef test_parse_postcode_rejects_and_audits(bad):\n    before = len(REJECTIONS)\n    with pytest.raises(ValidationError) as excinfo:\n        parse_postcode(bad)\n    assert len(REJECTIONS) == before + 1\n    entry = REJECTIONS[-1]\n    assert entry[\"field\"] == \"postcode\"\n    assert entry[\"value\"] is bad\n    assert entry[\"reason\"] == str(excinfo.value)\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131152-create-app-addresses-py-with-par/base-1/tests/test_addresses.py (file state is current in your context — no need to Read it back)
[assistant] Next: the project's test suite, the audit check, and a direct call on each input kind.
[tool_use Bash] {"command": "python -m pytest -q 2>&1 | tail -15; echo \"--- audit check\"; python .lithify/harness/skills/input-validation/scripts/check_audit.py app/addresses.py --only parse_postcode 2>&1; echo \"exit=$?\"; echo \"--- direct calls\"; ~/Coding/delvera/foundationa
…[149 chars elided]…
for v in [\"12345\", \"  12345-6789 \", None, 12345, \"1234\", \"12345-67890\", \"\u0661\u0662\u0663\u0664\u0665\"]:\n    try:\n        print(repr(v), \"->\", repr(parse_postcode(v)))\n    except ValidationError as e:\n        print(repr(v), \"-> ValidationError:\", e)\nprint(\"REJECTIONS:\", len(REJECTIONS), REJECTIONS[-1])\n'", "description": "Run tests, audit check, and direct validator calls"}
[tool_result] ........................................................................ [ 38%]
........................................................................ [ 76%]
.............................................                            [100%]
189 passed in 0.08s
--- audit check
ok: every checked ValidationError raise is preceded by record_rejection(...)
exit=0
--- direct calls
'12345' -> '12345'
'  12345-6789 ' -> '12345-6789'
None -> ValidationError: postcode must be a string
12345 -> ValidationError: postcode must be a string
'1234' -> ValidationError: postcode must be 5 digits, optionally followed by a hyphen and 4 digits
'12345-67890' -> ValidationError: postcode must be 5 digits, optionally followed by a hyphen and 4 digits
'١٢٣٤٥' -> ValidationError: postcode must be 5 digits, optionally followed by a hyphen and 4 digits
REJECTIONS: 5 {'field': 'postcode', 'value': '١٢٣٤٥', 'reason': 'postcode must be 5 digits, optionally followed by a hyphen and 4 digits'}
[assistant] I added `parse_postcode(value)` in a new `app/addresses.py`. The full suite passes (189 tests, including the new ones), and the audit check reports no unrecorded rejections.

- **Behaviour:** the input is stripped, then must be five ASCII digits, optionally followed by a hyphen and four digits. The stripped string is returned. Non-strings, wrong lengths, non-digits and non-ASCII digits raise `ValidationError`.
- **Audit:** every rejection calls `record_rejection("postcode", value, reason)` first, with the original argument and the same text as the error message. This follows the repo's input-v
…[157 chars elided]…
y` / `test_users.py` style. It covers accepted forms and rejected inputs, and checks that each rejection adds one audit entry with the original value.
- **Direct calls:** I called the function on `"12345"`, `"  12345-6789 "`, `None`, `12345`, `"1234"`, `"12345-67890"` and Arabic-Indic digits. Each returned or raised as specified, and the audit list grew by one entry per rejection.

Choices I made that you may want to change: the field name is `"postcode"`, since the function name uses that term. The regex uses `[0-9]` rather than `\d` so that Unicode digits are rejected.

Nothing is committed.
