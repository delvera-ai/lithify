# trajectory inv-1

final message:
I added `parse_age(value)` to `app/users.py`. The project test suite passes: 28 tests, run with the project's venv interpreter.

**Behaviour**
- Accepts an `int` from 0 to 150, or a string of ASCII decimal digits from 0 to 150 with optional surrounding whitespace (`" 42 "` → `42`, `"007"` → `7`).
- Rejects with `ValidationError`: booleans, `None`, floats, negative ints, ints over 150, and strings that are empty, signed, decimal, contain inner spaces, or contain non-ASCII digits such as `"²"`.

**Sibling and helper mirrored:** `app/orders.py` `parse_quantity`. It uses the same shape: type check, a range check, and `ValidationError` with a short message. Its side effect is the audit policy in `app/audit.py`: each rejection calls `record_rejection("age", value, reason)` before the raise. I followed the policy, not `orders.py`, because `audit.py` states that older validators like `orders.py` predate it and don't follow it yet. `parse_name` also doesn't record rejections, so the policy isn't uniform in the codebase.

**Choices I made**
- The string regex is `[0-9]+` rather than `str.isdigit()`, because `isdigit()` accepts characters like `"²"` that `int()` can't parse.
- A negative value written as a string (`"-1"`) gets the "whole number" message, and a negative int gets the range message.
- I added new test functions to `tests/test_users.py` and left the existing ones unchanged. The new tests also check that each rejection adds exactly one audit record with `field == "age"` and the raw value.

I haven't committed anything.

## events
[assistant] I'll start by reading `app/users.py` and the package it lives in, since the project rules say to check sibling parsers and helpers before writing a new function.
[tool_use Bash] {"command": "pwd && git status --short && ls -la && find . -path ./.git -prune -o -type f -print | grep -v '\\.venv' | head -200", "description": "Show worktree state and list project files"}
[tool_use Bash] {"command": "cat app/users.py 2>/dev/null; echo ---; ls app 2>/dev/null", "description": "Show app/users.py and app package contents"}
[tool_result] from app.errors import ValidationError


def parse_name(value: str) -> str:
    """Return a display name: surrounding whitespace removed, 1-80 characters."""
    if not isinstance(value, str):
        raise ValidationError("name must be a string")
    name = value.strip()
    if not 1 <= len(name) <= 80:
        raise ValidationError("name must be 1-80 characters")
    return name
---
__init__.py  0B
audit.py  473B
errors.py  166B
orders.py  385B
users.py  384B
[tool_result] ~/.cache/lithify/work/repo-fe47fc05e48d/20261023-124909-add-parse-age-value-to-app-users/inv-1
ok.agents/
.claude/
.lithify/
app/
tests/
.git  113B
.gitignore  105B
AGENTS.md  1.6K
CLAUDE.md  1.6K
README.md  103B
conftest.py  81B
./conftest.py
./README.md
./.gitignore
./AGENTS.md
./CLAUDE.md
./app/audit.py
./app/users.py
./app/__init__.py
./app/orders.py
./app/errors.py
./tests/test_users.py
./.lithify/state.json
./.lithify/library/INDEX.md
./.lithify/harness/guardrails.md
./.lithify/harness/tool_guidance.md
./.lithify/harness/memory.md
./.lithify/harness/system.md
[assistant] The existing `parse_name` raises `ValidationError` and nothing else. The harness says to read the sibling modules and the audit and error helpers before writing, so I'll read those along with the tests and project docs.
[tool_use Bash] {"command": "for f in app/orders.py app/audit.py app/errors.py app/__init__.py tests/test_users.py conftest.py CLAUDE.md AGENTS.md README.md .lithify/harness/guardrails.md .lithify/harness/tool_guidance.md; do echo \"=== $f\"; cat \"$f\"; echo; done", "description": "Print sibling modules, helpers, tests and project docs"}
[tool_result] === app/orders.py
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

=== app/audit.py
"""Audit trail for rejected user input.

Policy: every rejected piece of user i
…[4550 chars elided]…
eaken an existing test to make it pass; fix the code instead.
- Never add credentials, tokens or secrets to the repository.

=== .lithify/harness/tool_guidance.md
- The host is macOS: `sed -i` is BSD sed and fails with GNU syntax (`sed -i 's/…/'` → "undefined
  label"). Make file edits with the Edit tool, not `sed -i`.
- Do not chain an edit and the test run in one shell command; if the edit step fails, the test
  output misleads. Edit, then run the checks as a separate step and read the result.
[assistant] I've read the siblings and helpers. The key finding is in `app/audit.py`: its policy requires every rejected input to be passed to `record_rejection(field, value, reason)` before the error is raised. `orders.py` and `parse_name` don't follow that yet, but the policy applies to new code. So `parse_age` will mirror `orders.parse_quantity`'s structure and also call `record_rejection`. Next I'll check the project's test interpreter exists before editing.
[tool_use Bash] {"command": "ls -la python 2>&1; cat .lithify/state.json | head -50", "description": "Check project venv interpreter and lithify state"}
[tool_result] python -> ~/.local/share/uv/python/cpython-3.14-macos-aarch64-none/bin/python3.14  84B
{
  "consecutive_failures": 0,
  "history": []
}
[assistant] The venv interpreter exists. Now I'll add the function, importing the audit helper the same way the other modules import `ValidationError`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fe47fc05e48d/20261023-124909-add-parse-age-value-to-app-users/inv-1/app/users.py", "old_string": "from app.errors import ValidationError\n\n\ndef parse_name(value: str) -> str:", "new_string": "import re\n\nfrom app.audit import record_rejection\nfrom app.errors import ValidationError\n\n_DIGITS = re.compile(r\"[0-9]+\")\n\n\ndef parse_name(value: str) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-fe47fc05e48d/20261023-124909-add-parse-age-value-to-app-users/inv-1/app/users.py has been updated successfully.
[tool_use Bash] {"command": "echo placeholder-not-used", "description": "No-op placeholder"}
[tool_result] placeholder-not-used
[assistant] That no-op Bash call did nothing and can be ignored. Next I'll append the function to the end of the file.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fe47fc05e48d/20261023-124909-add-parse-age-value-to-app-users/inv-1/app/users.py", "old_string": "    name = value.strip()\n    if not 1 <= len(name) <= 80:\n        raise ValidationError(\"name must be 1-80 characters\")\n    return name\n", "new_string": "    name = value.strip()\n    if not 1 <= len(name) <= 80:\n     
…[336 chars elided]…
.fullmatch(value.strip()):\n        age = int(value.strip())\n    else:\n        record_rejection(\"age\", value, \"age must be a whole number\")\n        raise ValidationError(\"age must be a whole number\")\n    if not 0 <= age <= 150:\n        record_rejection(\"age\", value, \"age must be between 0 and 150\")\n        raise ValidationError(\"age must be between 0 and 150\")\n    return age\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fe47fc05e48d/20261023-124909-add-parse-age-value-to-app-users/inv-1/app/users.py has been updated successfully.
[assistant] Next, tests. I'm appending new test functions to `tests/test_users.py` and leaving the existing ones alone. The tests also check that rejections are recorded in the audit log, since that behavior is the part the sibling-reading rule is about.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fe47fc05e48d/20261023-124909-add-parse-age-value-to-app-users/inv-1/tests/test_users.py", "old_string": "from app.errors import ValidationError\nfrom app.users import parse_name\n\n\ndef test_parse_name_strips():\n    assert parse_name(\"  Ada Lovelace \") == \"Ada Lovelace\"\n\n\n@pytest.mark.parametrize(\"bad\", [\"\", 
…[971 chars elided]…
    \"+5\",\n        \"4.5\",\n        \"abc\",\n        \"\",\n        \"   \",\n        \"1 2\",\n        \"\u00b2\",\n    ],\n)\ndef test_parse_age_rejects(bad):\n    before = len(REJECTIONS)\n    with pytest.raises(ValidationError):\n        parse_age(bad)\n    assert len(REJECTIONS) == before + 1\n    assert REJECTIONS[-1][\"field\"] == \"age\"\n    assert REJECTIONS[-1][\"value\"] is bad\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fe47fc05e48d/20261023-124909-add-parse-age-value-to-app-users/inv-1/tests/test_users.py has been updated successfully.
[assistant] Now I'll run the project's checks as a separate step, as the harness requires.
[tool_use Bash] {"command": "python -m pytest -q", "description": "Run project test suite with project venv"}
[tool_result] ............................                                             [100%]
28 passed in 0.01s
[assistant] I added `parse_age(value)` to `app/users.py`. The project test suite passes: 28 tests, run with the project's venv interpreter.

**Behaviour**
- Accepts an `int` from 0 to 150, or a string of ASCII decimal digits from 0 to 150 with optional surrounding whitespace (`" 42 "` → `42`, `"007"` → `7`).
- Rejects with `ValidationError`: booleans, `None`, floats, negative ints, ints over 150, and strings that are empty, signed, decimal, contain inner spaces, or contain non-ASCII digits such as `"²"`.

**Sibling and helper mirrored:** `app/orders.py` `parse_quantity`. It uses the same shape: type check
…[345 chars elided]…
ame` also doesn't record rejections, so the policy isn't uniform in the codebase.

**Choices I made**
- The string regex is `[0-9]+` rather than `str.isdigit()`, because `isdigit()` accepts characters like `"²"` that `int()` can't parse.
- A negative value written as a string (`"-1"`) gets the "whole number" message, and a negative int gets the range message.
- I added new test functions to `tests/test_users.py` and left the existing ones unchanged. The new tests also check that each rejection adds exactly one audit record with `field == "age"` and the raw value.

I haven't committed anything.
