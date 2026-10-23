# trajectory base-1

final message:
`parse_discount(value)` is in `app/orders.py`, with tests in `tests/test_orders.py`. The full suite passes (165 tests), and the audit checker reports every rejection path records before raising.

**What it does**
- Accepts an int, a float, or a string of ASCII digits with an optional fraction and an optional single trailing `%`. It returns a float from 0 to 100 inclusive.
- Rejects booleans, other types, NaN, infinity, out-of-range values and huge ints. Each rejection calls `record_rejection("discount", value, reason)` with the original argument before raising `ValidationError`.

**Choices I made where the spec was open**
- **Surrounding whitespace is stripped**, so `" 7% "` is accepted. The other parsers in this repo do the same.
- **The string format is strict.** `"1e2"`, `"1_0"`, `"nan"`, `"inf"`, `".5"`, `"5."`, `"12 %"` and non-ASCII digits are all rejected. `float()` would accept several of these, so I used a regex. If you want `".5"` or `"5."` accepted, that's a one-line regex change.
- NaN is rejected by the range check, so its audit reason is "must be between 0 and 100", not a separate message.

**Verification**
- I called the function directly on sample inputs. Valid ones returned floats (`"12.5%"` → `12.5`, `" 7% "` → `7.0`). Invalid ones raised with the expected messages.
- The tests check that each rejection adds one audit entry whose `value` is the original object.

Nothing is committed.

## events
[assistant] I'll start by reading the project layout and the modules the CLAUDE.md says to check.
[tool_use Bash] {"command": "git status --short && ls -la && ls app tests && cat README.md", "description": "Show repo layout, app/tests listing, and README"}
[tool_use Skill] {"skill": "input-validation"}
[tool_result] ok.agents/
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
orders.py  1.7K
users.py  3.8K
test_orders.py  1.2K
test_users.py  4.5K
# accounts service

Input parsing for the accounts service. Run the tests with `python3 -m pytest -q`.
[tool_result] Launching skill: input-validation
[user] Base directory for this skill: ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131112-add-parse-discount-value-to-app/base-1/.claude/skills/input-validation

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

[assistant] The skill's rules are clear: record every rejection with `record_rejection` before raising, and check the original input value. Next I'll read the modules and tests it touches.
[tool_use Bash] {"command": "for f in app/orders.py app/errors.py app/audit.py app/users.py tests/test_orders.py tests/test_users.py conftest.py AGENTS.md CLAUDE.md; do echo \"=== $f\"; cat -n \"$f\"; done; echo; ls -la .lithify .lithify/harness/skills/input-validation/scripts 2>&1; git log --oneline | head -3", "description": "Print app modules, tests, and project docs"}
[tool_result] === app/orders.py
 1 │ from app.audit import record_rejection
 2 │ from app.errors import ValidationError
 3 │ 
 4 │ 
 5 │ def parse_quantity(value) -> int:
 6 │     """Return an order quantity between 1 and 999."""
 7 │     try:
 8 │         qty = int(value)
 9 │     except (TypeError, ValueError):
10 │         raise ValidationError("quantity must be a whole number") from None
11 │     if not 1 <= qty <= 999:
12 │         raise ValidationError("quantity must be between 1 and 999")
13 │     retu
…[18161 chars elided]…
t failures) may
29 │   only reflect an earlier failed step.
30 │ 
31 │ ### Skills (load on demand)
32 │ 
33 │ - `input-validation` — Load when adding or changing any function in app/ that parses or validates user input (parse_* functions, anything that raises ValidationError), or when writing tests for one.
34 │ <!-- lithify:end -->

harness/
library/
state.json  1.9K
check_audit.py  2.6K
7ca49a8 lithify: probe base
b6c0167 eval: configure parse_discount
edad13e eval: task 5 parse_quantity_range
[assistant] I've read the modules and the test conventions. Plan:

- Add `parse_discount` to `app/orders.py`, inlining `record_rejection` before each raise, matching `parse_quantity_range`.
- Accept numbers and strings, with a strict ASCII regex for strings. That rejects `1e2`, `1_0`, `nan` and `inf`, which `float()` would otherwise accept.
- Add tests to `tests/test_orders.py` in the existing style.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131112-add-parse-discount-value-to-app/base-1/app/orders.py", "old_string": "from app.audit import record_rejection\nfrom app.errors import ValidationError\n\n\ndef parse_quantity(value) -> int:", "new_string": "import re\n\nfrom app.audit import record_rejection\nfrom app.errors import ValidationError\n\nDISCOUNT_PATTERN = re.compile(r\"[0-9]+(?:\\.[0-9]+)?%?\")\n\n\ndef parse_quantity(value) -> int:"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131112-add-parse-discount-value-to-app/base-1/app/orders.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131112-add-parse-discount-value-to-app/base-1/app/orders.py", "old_string": "        record_rejection(\"quantity range\", value, \"quantity range low end must not exceed high end\")\n        raise ValidationError(\"quantity range low end must not exceed high end\")\n    return low, high\n", "new_stri
…[934 chars elided]…
ic string\")\n        raise ValidationError(\"discount must be a number or a numeric string\")\n    # NaN fails this comparison too, so it is rejected here with the range check\n    if not 0 <= discount <= 100:\n        record_rejection(\"discount\", value, \"discount must be between 0 and 100\")\n        raise ValidationError(\"discount must be between 0 and 100\")\n    return float(discount)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131112-add-parse-discount-value-to-app/base-1/app/orders.py has been updated successfully.
[assistant] Next, the tests. I'll add the import and accept/reject cases, using the same audit assertions as the other parser tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131112-add-parse-discount-value-to-app/base-1/tests/test_orders.py", "old_string": "from app.orders import parse_quantity_range\n", "new_string": "from app.orders import parse_discount, parse_quantity_range\n"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131112-add-parse-discount-value-to-app/base-1/tests/test_orders.py has been updated successfully.
[tool_use Bash] {"command": "cat >> tests/test_orders.py <<'EOF'\n\n\n@pytest.mark.parametrize(\n    \"good, expected\",\n    [\n        (0, 0.0),\n        (100, 100.0),\n        (12, 12.0),\n        (12.5, 12.5),\n        (99.99, 99.99),\n        (\"0\", 0.0),\n        (\"100\", 100.0),\n        (\"12.5\", 12.5),\n        (\"12.5%\", 12.5),\n        (\"100%\", 100.0),\n        (\"0.0%\", 0.0),\n        (\" 7 \",
…[1036 chars elided]…
parse_discount(bad)\n    assert len(REJECTIONS) == before + 1\n    entry = REJECTIONS[-1]\n    assert entry[\"field\"] == \"discount\"\n    assert entry[\"value\"] is bad\n    assert entry[\"reason\"] == str(excinfo.value)\nEOF\npython -m pytest -q 2>&1 | tail -30", "description": "Append discount tests and run the project's test suite"}
[tool_result] ........................................................................ [ 43%]
........................................................................ [ 87%]
.....................                                                    [100%]
165 passed in 0.06s
[assistant] The suite passes (165 tests). The file-change notice shows the same content I appended, so nothing outside my edits changed. Next I'll confirm the diff, run the audit checker the skill names, and call the function directly on each input kind.
[tool_use Bash] {"command": "git diff --stat && head -5 tests/test_orders.py && python .lithify/harness/skills/input-validation/scripts/check_audit.py app/orders.py --only parse_discount; echo \"exit=$?\"; python -I -c '\nimport sys; sys.path.insert(0, \".\")\nfrom app.orders import parse_disc
…[130 chars elided]…
 \", \"1e2\", \"nan\", True, None, \"\", 101, float(\"nan\"), 10**400, \"12 %\"]:\n    try:\n        print(repr(v), \"->\", repr(parse_discount(v)))\n    except ValidationError as e:\n        print(repr(v), \"-> ValidationError:\", e)\nprint(\"audit entries:\", len(REJECTIONS), \"last:\", REJECTIONS[-1])\n'", "description": "Check diff, run audit checker, and call parse_discount on sample inputs"}
[tool_result] app/orders.py        | 24 +++++++++++++++++
 tests/test_orders.py | 73 +++++++++++++++++++++++++++++++++++++++++++++++++++-
 2 files changed, 96 insertions(+), 1 deletion(-)
import pytest
from app.audit import REJECTIONS
from app.errors import ValidationError
from app.orders import parse_discount, parse_quantity_range
[123 more lines]ok: every checked ValidationError raise is preceded by record_rejection(...)
exit=0
0 -> 0.0
99.5 -> 99.5
100 -> 100.0
'12.5' -> 12.5
'12.5%' -> 12.5
' 7% ' -> 7.0

…[583 chars elided]…
000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000 -> ValidationError: discount must be between 0 and 100
'12 %' -> ValidationError: discount must look like 12.5 or 12.5%
audit entries: 9 last: {'field': 'discount', 'value': '12 %', 'reason': 'discount must look like 12.5 or 12.5%'}
[assistant] `parse_discount(value)` is in `app/orders.py`, with tests in `tests/test_orders.py`. The full suite passes (165 tests), and the audit checker reports every rejection path records before raising.

**What it does**
- Accepts an int, a float, or a string of ASCII digits with an optional fraction and an optional single trailing `%`. It returns a float from 0 to 100 inclusive.
- Rejects booleans, other types, NaN, infinity, out-of-range values and huge ints. Each rejection calls `record_rejection("discount", value, reason)` with the original argument before raising `ValidationError`.

**Choices I m
…[224 chars elided]…
"`, `"12 %"` and non-ASCII digits are all rejected. `float()` would accept several of these, so I used a regex. If you want `".5"` or `"5."` accepted, that's a one-line regex change.
- NaN is rejected by the range check, so its audit reason is "must be between 0 and 100", not a separate message.

**Verification**
- I called the function directly on sample inputs. Valid ones returned floats (`"12.5%"` → `12.5`, `" 7% "` → `7.0`). Invalid ones raised with the expected messages.
- The tests check that each rejection adds one audit entry whose `value` is the original object.

Nothing is committed.
