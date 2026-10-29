# trajectory base-1

final message:
`canonicalize` no longer crashes when a `DATEDIFF` argument has no inferred type. Arguments with unknown type are left alone.

**The fix** is one guard in `_coerce_datediff_args` (`sqlglot/optimizer/canonicalize.py:241`). The code read `e.type.this` without checking that `e.type` was set. It now reads `if e.type and e.type.this not in ...`, which matches how `_coerce_date` already skips untyped operands. Typed non-temporal arguments still get cast to `DATETIME`, as before.

**Verification:**
- Against the original code, `canonicalize(parse_one("SELECT DATEDIFF(a, b) FROM t"))` raises the exact `AttributeError: 'NoneType' object has no attribute 'this'` from the report. With the fix it returns `SELECT DATEDIFF(a, b) FROM t`.
- I added `test_canonicalize_datediff_untyped_args` to `tests/test_optimizer.py`. It passes.
- Full suite: 1108 passed, 18017 subtests passed.
- `ruff check` and `ruff format --check` pass on both changed files.

**Not fixed, but worth a look:** `parse_one("SELECT DATEDIFF(a, b) FROM t", read="snowflake")` and `read="duckdb"` raise `ParseError: Required keyword: 'this' missing for DateDiff`. That happens inside the parser, before `canonicalize` runs, so this change doesn't touch it. The two-argument form only parses in the default dialect, which is why the report's example works there.

I didn't commit anything.

## events
[tool_use Bash] {"command": "grep -n \"DATEDIFF\\|DateDiff\\|def _coerce_date\\|def coerce_date\\|_coerce_date\\|\\.type\" sqlglot/optimizer/canonicalize.py | head -50; echo ---; grep -n \"def _coerce_date\\|def coerce_date\" -A25 sqlglot/optimizer/canonicalize.py", "description": "Locate date coercion code in canonicalize"}
[tool_result] 61:        # coerce_type (COERCIBLE_DATE_OPS + Between, Extract, DateAdd, DateSub, DateTrunc, DateDiff)
68:        exp.DateDiff,
84:    if isinstance(node, exp.Add) and node.type and node.type.this in exp.DataType.TEXT_TYPES:
104:        if not node.type:
108:        return exp.cast(node.this, to=node.type or exp.DType.TIMESTAMP)
115:        _coerce_date(node.left, node.right, promote_to_inferred_datetime_type)
117:        _coerce_date(node.this, node.args["low"], promote_to_inferred_datetime_ty
…[2276 chars elided]…
se
251-# presto has a boolean type whereas tsql doesn't (people use bits)
252-# with y as (select true as x) select x = 0 FROM y -- illegal presto query
253-def _replace_int_predicate(expression: exp.Expr) -> None:
254-    if isinstance(expression, exp.Coalesce):
255-        for child in expression.iter_expressions():
256-            _replace_int_predicate(child)
257-    elif expression.type and expression.type.this in exp.DataType.INTEGER_TYPES:
258-        expression.replace(expression.neq(0))
[assistant] The crash is at line 241: `e.type` is `None` for an untyped argument, and `.this` is read without a guard. The sibling helpers (`_coerce_date`, line 187) skip untyped operands, so I'll match that.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-125522-optimizer-canonicalize-crashes-w/base-1/sqlglot/optimizer/canonicalize.py", "old_string": "        if e.type.this not in exp.DataType.TEMPORAL_TYPES:", "new_string": "        if e.type and e.type.this not in exp.DataType.TEMPORAL_TYPES:"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-125522-optimizer-canonicalize-crashes-w/base-1/sqlglot/optimizer/canonicalize.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.canonicalize import canonicalize\nprint(canonicalize(parse_one('SELECT DATEDIFF(a, b) FROM t')).sql())\nprint(canonicalize(parse_one('SELECT DATEDIFF(a, b) FROM t', read='snowflake')).sql())\n\"", "description": "Reproduce the reported canonicalize call after fix"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 5, in <module>
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-125522-optimizer-canonicalize-crashes-w/base-1/sqlglot/__init__.py", line 160, in parse_one
    result = dialect.parse(sql, **opts)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-125522-optimizer-canonicalize-crashes-w/base-1/sqlglot/dialects/dialect.py", line 1119, in parse
    r
…[7151 chars elided]…
zer-canonicalize-crashes-w/base-1/sqlglot/parser.py", line 2003, in validate_expression
    self.raise_error(error_message)
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-125522-optimizer-canonicalize-crashes-w/base-1/sqlglot/parser.py", line 1992, in raise_error
    raise error
sqlglot.errors.ParseError: Required keyword: 'this' missing for <class 'sqlglot.expressions.temporal.DateDiff'>. Line 1, Col: 21.
  SELECT DATEDIFF(a, b[4m)[0m FROM t
SELECT DATEDIFF(a, b) FROM t
[assistant] The fixed path now succeeds for the Snowflake parse. The default-dialect `DATEDIFF(a, b)` fails earlier, inside `parse_one`, so it never reaches `canonicalize`. That's a parser issue, separate from this bug. Next I'll confirm the original code actually crashed on the untyped path, then run the test suite.
[tool_use Bash] {"command": "git show HEAD:sqlglot/optimizer/canonicalize.py > /tmp/canon_orig.py && <work>/env-sqlglot/bin/python -c \"\nimport importlib.util\nfrom sqlglot import parse_one, exp\nspec = importlib.util.spec_from_file_location('canon_orig', '/tmp/canon_orig.py')\nm = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\ne = parse_one('SELECT
…[69 chars elided]…
e); print('no crash')\nexcept Exception as ex: print('orig:', type(ex).__name__, ex)\n\" 2>&1 | tail -3; grep -rn \"canonicalize\" tests/*.py | head -5; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py tests/test_transpile.py 2>&1 | tail -5", "description": "Confirm original crash and run optimizer tests"}
[tool_result]     raise error
sqlglot.errors.ParseError: Required keyword: 'this' missing for <class 'sqlglot.expressions.temporal.DateDiff'>. Line 1, Col: 21.
  SELECT DATEDIFF(a, b[4m)[0m FROM t
tests/test_optimizer.py:13:from sqlglot.optimizer.canonicalize_internal_names import canonicalize_internal_names
tests/test_optimizer.py:32:def qualify_then_canonicalize(expression, **qualify_kwargs):
tests/test_optimizer.py:33:    return canonicalize_internal_names(qualify(expression, **qualify_kwargs))
tests/test_optimizer.py:176:                canonicalize_table_aliases = meta.get("canonicalize_table_aliases")
tests/test_optimizer.py:189:                if canonicalize_table_aliases is not None:
....................... [ 21%]
............. [ 33%]
.......................................................................                      [100%]
107 passed, 4840 subtests passed in 16.52s
[assistant] The parse error is ambiguous: it could come from the default-dialect line or the Snowflake line. I'll run each case separately to see which one fails.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; for d in \"\" snowflake duckdb; do echo \"== dialect '$d'\"; $PY -c \"\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.canonicalize import canonicalize\ne = parse_one('SELECT DATEDIFF(a, b) FROM t', read='$d' or None)\nprint(e.sql())\nprint(canonicalize(e).sql())\n\" 2>&1 | tail -2; done", "description": "Test DATEDIFF canonicalize across dialects separately"}
[tool_result] == dialect ''
SELECT DATEDIFF(a, b) FROM t
SELECT DATEDIFF(a, b) FROM t
== dialect 'snowflake'
sqlglot.errors.ParseError: Required keyword: 'this' missing for <class 'sqlglot.expressions.temporal.DateDiff'>. Line 1, Col: 21.
  SELECT DATEDIFF(a, b[4m)[0m FROM t
== dialect 'duckdb'
sqlglot.errors.ParseError: Required keyword: 'this' missing for <class 'sqlglot.expressions.temporal.DateDiff'>. Line 1, Col: 21.
  SELECT DATEDIFF(a, b[4m)[0m FROM t
[assistant] The default dialect works after the fix. The Snowflake and DuckDB parse failures are a separate parser issue, not part of this bug. Next I'll confirm the original code crashed on the default-dialect input, then look for an existing canonicalize test to extend.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport importlib.util\nfrom sqlglot import parse_one\nspec = importlib.util.spec_from_file_location('canon_orig', '/tmp/canon_orig.py')\nm = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\ntry: m.canonicalize(parse_one('SELECT DATEDIFF(a, b) FROM t')); print('no crash')\nexcept Exception as ex: print('orig:', type(ex).__name__, ex)\n\"; grep -rln \"optimizer.canonicalize import\\|optimizer import canonicalize\" tests/ ; grep -rn \"DATEDIFF\\|DateDiff\" tests/test_optimizer.py | head -5", "description": "Confirm original crash and locate canonicalize tests"}
[tool_result] orig: AttributeError 'NoneType' object has no attribute 'this'
tests/test_optimizer.py:1664:                "SELECT DATEDIFF('2023-01-01', '2023-01-02', DAY) FROM x AS x",
[assistant] The original code reproduces the exact `AttributeError` from the report, and the fix clears it. Next I'll add a regression test. I'll check where canonicalize is tested first.
[tool_use Bash] {"command": "ls tests | grep -i canon; grep -rln \"canonicalize(\" tests/ | head; grep -n \"def test_\" tests/test_optimizer.py | head -3", "description": "Find canonicalize test files"}
[tool_result] tests/test_optimizer.py
228:    def test_optimize(self, logger):
247:    def test_isolate_table_selects(self):
254:    def test_qualify_tables(self):
[tool_use Bash] {"command": "grep -n \"canonicalize\" tests/test_optimizer.py | head; grep -rn \"^from\\|^import\" tests/test_optimizer.py | head -30; grep -n \"def test_\" tests/test_optimizer.py | tail -3; tail -5 tests/test_optimizer.py", "description": "Inspect canonicalize imports and test structure"}
[tool_result] 13:from sqlglot.optimizer.canonicalize_internal_names import canonicalize_internal_names
32:def qualify_then_canonicalize(expression, **qualify_kwargs):
33:    return canonicalize_internal_names(qualify(expression, **qualify_kwargs))
176:                canonicalize_table_aliases = meta.get("canonicalize_table_aliases")
189:                if canonicalize_table_aliases is not None:
190:                    func_kwargs["canonicalize_table_aliases"] = string_to_bool(
191:                        can
…[1367 chars elided]…
:from tests.helpers import (
2642:    def test_null_coerce_annotation(self):
2654:    def test_correlated_subqueries_annotation(self):
2714:    def test_order_by_alias_annotation(self):
        # Regression: self-referential alias (BigQuery pseudocolumn pattern)
        sql = "SELECT _col AS _col FROM t"
        schema_ext = {"t": {"_col": "INT"}}
        query = optimizer.qualify.qualify(parse_one(sql), schema=schema_ext)
        optimizer.annotate_types.annotate_types(query, schema=schema_ext)
[assistant] I'll add a regression test at the end of the optimizer test class, next to the other recent regression tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-125522-optimizer-canonicalize-crashes-w/base-1/tests/test_optimizer.py", "old_string": "        query = optimizer.qualify.qualify(parse_one(sql), schema=schema_ext)\n        optimizer.annotate_types.annotate_types(query, schema=schema_ext)", "new_string": "        query = optimizer.qualify.qualify(parse_one(sql), schema=schema_ext)\n        optimizer.annotate_types.annotate_types(query, schema=schema_ext)\n\n    def test_canonicalize_datediff_untyped_args(self):\n        from sqlglot.optimizer.canonicalize import canonicalize\n\n        self.assertEqual(\n            canonicalize(parse_one(\"SELECT DATEDIFF(a, b) FROM t\")).sql(),\n            \"SELECT DATEDIFF(a, b) FROM t\",\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-125522-optimizer-canonicalize-crashes-w/base-1/tests/test_optimizer.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k datediff_untyped 2>&1 | tail -2; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4", "description": "Run new regression test and full test suite"}
[tool_result] .                                                                        [100%]
1 passed, 79 deselected in 0.27s
........................................................................................................... [ 82%]
...................................................................................................... [ 91%]
.............................................................................................                            [100%]
1108 passed, 18017 subtests passed in 53.60s
[assistant] The full suite passes. I'll run the linter on the two changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff check sqlglot/optimizer/canonicalize.py tests/test_optimizer.py && $PY -m ruff format --check sqlglot/optimizer/canonicalize.py tests/test_optimizer.py) 2>&1 | tail -3; git status --short; rm -f /tmp/canon_orig.py", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
2 files already formatted
 M sqlglot/optimizer/canonicalize.py
 M tests/test_optimizer.py
[assistant] `canonicalize` no longer crashes when a `DATEDIFF` argument has no inferred type. Arguments with unknown type are left alone.

**The fix** is one guard in `_coerce_datediff_args` (`sqlglot/optimizer/canonicalize.py:241`). The code read `e.type.this` without checking that `e.type` was set. It now reads `if e.type and e.type.this not in ...`, which matches how `_coerce_date` already skips untyped operands. Typed non-temporal arguments still get cast to `DATETIME`, as before.

**Verification:**
- Against the original code, `canonicalize(parse_one("SELECT DATEDIFF(a, b) FROM t"))` raises the exact
…[153 chars elided]…
onicalize_datediff_untyped_args` to `tests/test_optimizer.py`. It passes.
- Full suite: 1108 passed, 18017 subtests passed.
- `ruff check` and `ruff format --check` pass on both changed files.

**Not fixed, but worth a look:** `parse_one("SELECT DATEDIFF(a, b) FROM t", read="snowflake")` and `read="duckdb"` raise `ParseError: Required keyword: 'this' missing for DateDiff`. That happens inside the parser, before `canonicalize` runs, so this change doesn't touch it. The two-argument form only parses in the default dialect, which is why the report's example works there.

I didn't commit anything.
