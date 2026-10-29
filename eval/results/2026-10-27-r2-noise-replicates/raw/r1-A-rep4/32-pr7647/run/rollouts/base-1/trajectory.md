# trajectory base-1

final message:
`canonicalize` no longer crashes on a `DATEDIFF` argument with no inferred type. The full test suite passes (1107 passed).

The cause was `_coerce_datediff_args` in `sqlglot/optimizer/canonicalize.py`, which read `e.type.this` without checking that the type was set. I added a `e.type and` guard, matching what `_coerce_timeunit_arg` already does. An argument with unknown type is now left alone.

```python
canonicalize(parse_one("SELECT DATEDIFF(a, b) FROM t")).sql()
# 'SELECT DATEDIFF(a, b) FROM t'
```

I didn't add a regression test for this case. The repo's guidelines ask for tests on non-trivial changes, and this is a one-line guard, so say if you want a test added to `tests/test_optimizer.py`.

Nothing has been committed.

## events
[tool_use Bash] {"command": "grep -n \"datediff\\|DateDiff\\|_coerce_date\\|def _coerce\\|def coerce_date\\|def _replace_date\" -i sqlglot/optimizer/canonicalize.py && sed -n 1,200p sqlglot/optimizer/canonicalize.py", "description": "Locate DATEDIFF handling in canonicalize"}
[tool_result] 61:        # coerce_type (COERCIBLE_DATE_OPS + Between, Extract, DateAdd, DateSub, DateTrunc, DateDiff)
68:        exp.DateDiff,
115:        _coerce_date(node.left, node.right, promote_to_inferred_datetime_type)
117:        _coerce_date(node.this, node.args["low"], promote_to_inferred_datetime_type)
124:    elif isinstance(node, exp.DateDiff):
125:        _coerce_datediff_args(node)
174:def _coerce_date(
218:def _coerce_timeunit_arg(arg: exp.Expr, unit: exp.Expr | None) -> exp.Expr:
239:def _coe
…[5856 chars elided]…
exp.DataType.TEMPORAL_TYPES
            or not b.type
            or b.type.this not in exp.DataType.TEXT_TYPES
        ):
            continue

        if promote_to_inferred_datetime_type:
            if b.is_string:
                date_text = b.name
                if is_iso_date(date_text):
                    b_type = exp.DType.DATE
                elif is_iso_datetime(date_text):
                    b_type = exp.DType.DATETIME
                else:
                    b_type = a_type.this
[tool_use Bash] {"command": "sed -n 200,280p sqlglot/optimizer/canonicalize.py; <work>/env-sqlglot/bin/python -c \"\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.canonicalize import canonicalize\ncanonicalize(parse_one('SELECT DATEDIFF(a, b) FROM t'))\nprint('ok')\" 2>&1 | tail -5", "description": "Read datediff helper and reproduce crash"}
[tool_result]                     b_type = a_type.this
            else:
                # If b is not a datetime string, we conservatively promote it to a DATETIME,
                # in order to ensure there are no surprising truncations due to downcasting
                b_type = exp.DType.DATETIME

            target_type = (
                b_type if b_type in TypeAnnotator.COERCES_TO.get(a_type.this, {}) else a_type
            )
        else:
            target_type = a_type

        if target_type != a
…[1618 chars elided]…
_int_predicate(child)
    elif expression.type and expression.type.this in exp.DataType.INTEGER_TYPES:
        expression.replace(expression.neq(0))
    _coerce_datediff_args(node)
  File "~/.cache/lithify/work/repo-d5521a213087/20261028-182456-optimizer-canonicalize-crashes-w/base-1/sqlglot/optimizer/canonicalize.py", line 241, in _coerce_datediff_args
    if e.type.this not in exp.DataType.TEMPORAL_TYPES:
       ^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'this'
[assistant] The crash is in `_coerce_datediff_args`, which reads `e.type.this` without checking whether the type is set. `_coerce_timeunit_arg` already returns early on a missing type, so I'll follow that pattern.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-182456-optimizer-canonicalize-crashes-w/base-1/sqlglot/optimizer/canonicalize.py", "old_string": "        if e.type.this not in exp.DataType.TEMPORAL_TYPES:", "new_string": "        if e.type and e.type.this not in exp.DataType.TEMPORAL_TYPES:"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-182456-optimizer-canonicalize-crashes-w/base-1/sqlglot/optimizer/canonicalize.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.canonicalize import canonicalize\nprint(canonicalize(parse_one('SELECT DATEDIFF(a, b) FROM t')).sql())\nprint(canonicalize(parse_one(\\\"SELECT DATEDIFF(CAST('2020-01-01' AS DATE), a) FROM t\\\")).sql())\" 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py tests/test_expressions.py 2>&1 | tail -5", "description": "Verify fix and run optimizer tests"}
[tool_result] SELECT DATEDIFF(a, b) FROM t
SELECT DATEDIFF(CAST('2020-01-01' AS DATE), a) FROM t
....................... [ 15%]
............. [ 24%]
............................................................................... [ 77%]
.................................                                        [100%]
148 passed, 3845 subtests passed in 14.02s
[assistant] The crash is fixed and the optimizer tests pass. I'll run the full project suite, since that's the check the repo specifies.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4; git diff --stat", "description": "Run full test suite and show diff stat"}
[tool_result] ........................................................................... [ 91%]
............................................................... [ 97%]
.............................                             [100%]
1107 passed, 18017 subtests passed in 49.89s
 sqlglot/optimizer/canonicalize.py | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
[assistant] `canonicalize` no longer crashes on a `DATEDIFF` argument with no inferred type. The full test suite passes (1107 passed).

The cause was `_coerce_datediff_args` in `sqlglot/optimizer/canonicalize.py`, which read `e.type.this` without checking that the type was set. I added a `e.type and` guard, matching what `_coerce_timeunit_arg` already does. An argument with unknown type is now left alone.

```python
canonicalize(parse_one("SELECT DATEDIFF(a, b) FROM t")).sql()
# 'SELECT DATEDIFF(a, b) FROM t'
```

I didn't add a regression test for this case. The repo's guidelines ask for tests on non-trivial changes, and this is a one-line guard, so say if you want a test added to `tests/test_optimizer.py`.

Nothing has been committed.
