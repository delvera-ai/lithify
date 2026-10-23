# trajectory base-1

final message:
I added `parse_quantity_range(value)` to `app/orders.py`. The full suite passes (121 tests, up from 94 with the 27 new cases), and the audit checker reports no unaudited raises in the new function.

- **Accepts** strings like `"2-5"`, `" 2 - 5 "` and `"007-010"`, returning `(low, high)` as ints. Both ends must be ASCII digits from 1 to 999, and `low <= high`.
- **Rejects** non-strings, anything without exactly one hyphen, signs, decimals, non-ASCII digits, out-of-range ends, and `low > high`. Each rejection raises `ValidationError` with a message that names the problem.
- **Audits** every rejection with `record_rejection` before the raise, following the pattern in `app/users.py`. The field is `"quantity range"`, the noun the messages use, and the value is the original argument.

I also created `tests/test_orders.py`, since none existed, with accept and reject cases modelled on `tests/test_users.py`. I didn't change any existing test or the existing `parse_quantity`. Nothing is committed.

## events
[tool_use Skill] {"skill": "input-validation"}
[tool_result] Launching skill: input-validation
[user] Base directory for this skill: ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131037-add-parse-quantity-range-value-t/base-1/.claude/skills/input-validation

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

[tool_use Bash] {"command": "ls -la app tests && wc -l app/*.py && cat README.md", "description": "List app and tests, show README"}
[tool_result] __init__.py  0B
audit.py  473B
errors.py  166B
orders.py  385B
users.py  3.8K
test_users.py  4.5K
0 __init__.py
12 audit.py
6 errors.py
12 orders.py
82 users.py
Σ 112
# accounts service

Input parsing for the accounts service. Run the tests with `python3 -m pytest -q`.
[tool_use Bash] {"command": "cat app/orders.py; echo ---; cat app/audit.py; echo ---; cat app/errors.py; echo ---; cat app/users.py; echo ---; cat tests/test_users.py; echo ---; ls -la .lithify/harness/skills/input-validation/scripts/ 2>&1; ls .claude/skills/input-validation 2>&1", "description": "Read app modules, tests, and skill scripts"}
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
---
"""Audit trail for rejected user input.

Policy: every rejected piece of user input must be recorded with
`reco
…[8659 chars elided]…
"ab١",  # Arabic-Indic digit one: decimal, but not ASCII
        "abc@",
    ],
)
def test_parse_username_rejects_and_audits(bad):
    before = len(REJECTIONS)
    with pytest.raises(ValidationError) as excinfo:
        parse_username(bad)
    assert len(REJECTIONS) == before + 1
    entry = REJECTIONS[-1]
    assert entry["field"] == "username"
    assert entry["value"] is bad
    assert entry["reason"] == str(excinfo.value)
---
check_audit.py  2.6K
scripts/
.lithify-managed  24B
SKILL.md  2.9K
[tool_use Bash] {"command": "ls -la python 2>&1; python -m pytest -q 2>&1 | tail -5; echo ---; sed -n 1,80p .lithify/harness/skills/input-validation/scripts/check_audit.py", "description": "Check venv and run baseline tests, read audit checker"}
[tool_result] python -> ~/.local/share/uv/python/cpython-3.14-macos-aarch64-none/bin/python3.14  84B
........................................................................ [ 76%]
......................                                                   [100%]
94 passed in 0.05s
---
"""List `raise ValidationError` statements not immediately preceded by `record_rejection(...)`.

Usage: check_audit.py FILE [FILE ...] [--only FUNC [FUNC ..
…[1985 chars elided]…
 ast.AsyncFunctionDef)):
                continue
            if args.only and node.name not in args.only:
                continue
            for line in _scan(node):
                print(f"{path}:{line}: {node.name}: ValidationError raised without a preceding record_rejection(...)")
                bad += 1
    if bad == 0:
        print("ok: every checked ValidationError raise is preceded by record_rejection(...)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
[assistant] Baseline is 94 passing. The validators in `app/users.py` record inline before each raise, so I'll match that and keep every raise directly checkable.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131037-add-parse-quantity-range-value-t/base-1/app/orders.py", "old_string": "from app.errors import ValidationError\n\n\ndef parse_quantity(value) -> int:", "new_string": "from app.audit import record_rejection\nfrom app.errors import ValidationError\n\n\ndef parse_quantity(value) -> int:"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131037-add-parse-quantity-range-value-t/base-1/app/orders.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131037-add-parse-quantity-range-value-t/base-1/app/orders.py", "old_string": "    if not 1 <= qty <= 999:\n        raise ValidationError(\"quantity must be between 1 and 999\")\n    return qty\n", "new_string": "    if not 1 <= qty <= 999:\n        raise ValidationError(\"quantity must be between 1 a
…[1039 chars elided]…
tion(\"quantity range\", value, \"quantity range ends must be between 1 and 999\")\n        raise ValidationError(\"quantity range ends must be between 1 and 999\")\n    if low > high:\n        record_rejection(\"quantity range\", value, \"quantity range low end must not exceed high end\")\n        raise ValidationError(\"quantity range low end must not exceed high end\")\n    return low, high\n"}
[tool_result] The file ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131037-add-parse-quantity-range-value-t/base-1/app/orders.py has been updated successfully.
[assistant] No `tests/test_orders.py` exists yet, so I'll create it in the same style as `tests/test_users.py`.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131037-add-parse-quantity-range-value-t/base-1/tests/test_orders.py", "content": "import pytest\nfrom app.audit import REJECTIONS\nfrom app.errors import ValidationError\nfrom app.orders import parse_quantity_range\n\n\n@pytest.mark.parametrize(\n    \"good, expected\",\n    [\n        (\"2-5\", (2, 5)),\n        (\" 2 - 
…[760 chars elided]…
II\n    ],\n)\ndef test_parse_quantity_range_rejects_and_audits(bad):\n    before = len(REJECTIONS)\n    with pytest.raises(ValidationError) as excinfo:\n        parse_quantity_range(bad)\n    assert len(REJECTIONS) == before + 1\n    entry = REJECTIONS[-1]\n    assert entry[\"field\"] == \"quantity range\"\n    assert entry[\"value\"] is bad\n    assert entry[\"reason\"] == str(excinfo.value)\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-bbb38b6f3614/20261023-131037-add-parse-quantity-range-value-t/base-1/tests/test_orders.py (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PY=python; $PY -m pytest -q 2>&1 | tail -3; echo ---; $PY .lithify/harness/skills/input-validation/scripts/check_audit.py app/orders.py --only parse_quantity_range; echo \"exit=$?\"; echo ---; $PY -c '\nfrom app.orders import parse_quantity_range as p\nfrom app.audit import REJECTIONS\nfor v in [\"2-5\",\" 3 - 9 \",\"999-999\",\"5-2\",\"2-1000\",\"2\",\"abc\",None,[\"2-5\"]]:\n    try: print(repr(v), \"->\", p(v))\n    except Exception as e: print(repr(v), \"-> ValidationError:\", e)\nprint(\"audit entries:\", len(REJECTIONS), REJECTIONS[-1])\n' 2>&1; echo ---; git status --short", "description": "Run tests, audit checker, and manual calls"}
[tool_result] ........................................................................ [ 59%]
.................................................                        [100%]
121 passed in 0.03s
---
ok: every checked ValidationError raise is preceded by record_rejection(...)
exit=0
---
'2-5' -> (2, 5)
' 3 - 9 ' -> (3, 9)
'999-999' -> (999, 999)
'5-2' -> ValidationError: quantity range low end must not exceed high end
'2-1000' -> ValidationError: quantity range ends must be between 1 and 999
'2' -> ValidationError: quantity range must look like 2-5
'abc' -> ValidationError: quantity range must look like 2-5
None -> ValidationError: quantity range must be a string
['2-5'] -> ValidationError: quantity range must be a string
audit entries: 6 {'field': 'quantity range', 'value': ['2-5'], 'reason': 'quantity range must be a string'}
---
 M app/orders.py
?? tests/test_orders.py
[assistant] I added `parse_quantity_range(value)` to `app/orders.py`. The full suite passes (121 tests, up from 94 with the 27 new cases), and the audit checker reports no unaudited raises in the new function.

- **Accepts** strings like `"2-5"`, `" 2 - 5 "` and `"007-010"`, returning `(low, high)` as ints. Both ends must be ASCII digits from 1 to 999, and `low <= high`.
- **Rejects** non-strings, anything without exactly one hyphen, signs, decimals, non-ASCII digits, out-of-range ends, and `low > high`. Each rejection raises `ValidationError` with a message that names the problem.
- **Audits** every rejection with `record_rejection` before the raise, following the pattern in `app/users.py`. The field is `"quantity range"`, the noun the messages use, and the value is the original argument.

I also created `tests/test_orders.py`, since none existed, with accept and reject cases modelled on `tests/test_users.py`. I didn't change any existing test or the existing `parse_quantity`. Nothing is committed.
