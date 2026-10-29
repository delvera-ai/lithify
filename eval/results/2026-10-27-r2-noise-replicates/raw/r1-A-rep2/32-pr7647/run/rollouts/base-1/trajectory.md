# trajectory base-1

final message:
`canonicalize` no longer crashes on a `DATEDIFF` argument with no inferred type. The argument is left alone, the same way `_coerce_date` and `_coerce_timeunit_arg` treat untyped arguments.

**The fix** is one line in `sqlglot/optimizer/canonicalize.py`, in `_coerce_datediff_args`: the type check is now `if e.type and e.type.this not in ...`. Untyped arguments fall through without being cast.

**Verification**
- Your repro now returns `SELECT DATEDIFF(a, b) FROM t`.
- I added `test_canonicalize_untyped_datediff` to `tests/test_optimizer.py`. It fails without the fix and passes with it.
- The full suite passes: 1108 passed, 18017 subtests. Ruff is clean on both changed files.

**Choices I made**
- **Test placement:** I put the regression test in `tests/test_optimizer.py` as a direct call to `canonicalize`. I first tried a fixture line in `tests/fixtures/optimizer/canonicalize.sql`, but it didn't reproduce the crash. Unqualified columns get an `UNKNOWN` type, not `None`, so they take the existing cast branch. I reverted that fixture edit.
- **Scope:** Arguments with `UNKNOWN` type still get cast to `DATETIME`, as before. I only changed the `None` case, since that's the one that crashed.

Nothing is committed. The changes are in the working tree.

## events
[tool_use Bash] {"command": "grep -n \"DateDiff\\|_coerce_date\\|def _coerce\\|def coerce\" sqlglot/optimizer/canonicalize.py && sed -n 1,200p sqlglot/optimizer/canonicalize.py", "description": "Locate date handling in canonicalize.py"}
[tool_result] 61:        # coerce_type (COERCIBLE_DATE_OPS + Between, Extract, DateAdd, DateSub, DateTrunc, DateDiff)
68:        exp.DateDiff,
113:def coerce_type(node: exp.Expr, promote_to_inferred_datetime_type: bool) -> exp.Expr:
115:        _coerce_date(node.left, node.right, promote_to_inferred_datetime_type)
117:        _coerce_date(node.this, node.args["low"], promote_to_inferred_datetime_type)
124:    elif isinstance(node, exp.DateDiff):
125:        _coerce_datediff_args(node)
174:def _coerce_date(
21
…[5946 chars elided]…
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
[tool_use Bash] {"command": "sed -n 200,280p sqlglot/optimizer/canonicalize.py; <work>/env-sqlglot/bin/python -c \"\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.canonicalize import canonicalize\ncanonicalize(parse_one('SELECT DATEDIFF(a, b) FROM t'))\" 2>&1 | tail -5", "description": "Read remaining helpers and reproduce the crash"}
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
  File "~/.cache/lithify/work/repo-fdb04f649b80/20261028-092158-optimizer-canonicalize-crashes-w/base-1/sqlglot/optimizer/canonicalize.py", line 241, in _coerce_datediff_args
    if e.type.this not in exp.DataType.TEMPORAL_TYPES:
       ^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'this'
[assistant] The crash is in `_coerce_datediff_args`, which reads `e.type.this` without checking whether the type is set. The other helpers (`_coerce_timeunit_arg`, `_coerce_date`) return early on a missing type, so I'll match that.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-092158-optimizer-canonicalize-crashes-w/base-1/sqlglot/optimizer/canonicalize.py", "old_string": "        if e.type.this not in exp.DataType.TEMPORAL_TYPES:", "new_string": "        if e.type and e.type.this not in exp.DataType.TEMPORAL_TYPES:"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-092158-optimizer-canonicalize-crashes-w/base-1/sqlglot/optimizer/canonicalize.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.canonicalize import canonicalize\nprint(canonicalize(parse_one('SELECT DATEDIFF(a, b) FROM t')).sql())\nprint(canonicalize(parse_one(\\\"SELECT DATEDIFF(CAST(a AS DATE), '2020-01-01') FROM t\\\")).sql())\" 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Apply fix, check repro output, and run the test suite"}
[tool_result] SELECT DATEDIFF(a, b) FROM t
SELECT DATEDIFF(CAST(a AS DATE), '2020-01-01') FROM t
...................................................................................................................................... [ 84%]
........................................................................... [ 91%]
............................................................... [ 97%]
.............................                             [100%]
1107 passed, 18017 subtests passed in 51.73s
[assistant] The repro now runs and the suite passes. I'll add a regression test next to the existing canonicalize tests.
[tool_use Bash] {"command": "grep -rn \"datediff\\|DATEDIFF\" tests/test_optimizer.py tests/fixtures/optimizer/canonicalize.sql | head -20; grep -n \"canonicalize\" tests/test_optimizer.py | head", "description": "Find existing canonicalize tests for DATEDIFF"}
[tool_result] tests/fixtures/optimizer/canonicalize.sql:101:DATEDIFF('2023-01-01', '2023-01-02', DAY);
tests/fixtures/optimizer/canonicalize.sql:102:DATEDIFF(CAST('2023-01-01' AS DATETIME), CAST('2023-01-02' AS DATETIME), DAY);
tests/test_optimizer.py:1664:                "SELECT DATEDIFF('2023-01-01', '2023-01-02', DAY) FROM x AS x",
13:from sqlglot.optimizer.canonicalize_internal_names import canonicalize_internal_names
32:def qualify_then_canonicalize(expression, **qualify_kwargs):
33:    return canonicali
…[44 chars elided]…
ify_kwargs))
176:                canonicalize_table_aliases = meta.get("canonicalize_table_aliases")
189:                if canonicalize_table_aliases is not None:
190:                    func_kwargs["canonicalize_table_aliases"] = string_to_bool(
191:                        canonicalize_table_aliases
321:        optimizer.qualify_tables.qualify_tables(expression, canonicalize_table_aliases=True)
1034:    def test_canonicalize_internal_names(self):
1042:            "canonicalize_internal_names",
[tool_use Bash] {"command": "sed -n 95,110p tests/fixtures/optimizer/canonicalize.sql; grep -n \"canonicalize.sql\" tests/test_optimizer.py", "description": "View canonicalize fixture tail and its test wiring"}
[tool_result] SELECT DATE_TRUNC('SECOND', t.d) FROM temporal AS t;
SELECT DATE_TRUNC('SECOND', CAST("t"."d" AS DATETIME)) AS "_col_0" FROM "temporal" AS "t";

DATE_TRUNC('DAY', '2023-01-01');
DATE_TRUNC('DAY', CAST('2023-01-01' AS DATE));

DATEDIFF('2023-01-01', '2023-01-02', DAY);
DATEDIFF(CAST('2023-01-01' AS DATETIME), CAST('2023-01-02' AS DATETIME), DAY);

SELECT "t"."d" > '2023-01-01' AS "d" FROM "temporal" AS "t";
SELECT "t"."d" > CAST('2023-01-01' AS DATE) AS "d" FROM "temporal" AS "t";

SELECT "t"."d" > CAST('2023-01-01' AS DATETIME) AS "d" FROM "temporal" AS "t";
SELECT "t"."d" > CAST('2023-01-01' AS DATETIME) AS "d" FROM "temporal" AS "t";

SELECT "t"."t" > '2023-01-01 00:00:01' AS "t" FROM "temporal" AS "t";
[tool_use Bash] {"command": "grep -n '\"canonicalize\"' -A3 tests/test_optimizer.py | head -20", "description": "Find canonicalize fixture test wiring"}
[tool_result] 1283:        self.check_file("canonicalize", optimize, schema=self.schema)
1284-
1285-        # In T-SQL and Redshift, SELECT a + b can produce a NULL, so we can't transpile it
1286-        # into a CONCAT in Postgres, because that coalesces NULL values with empty strings
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-092158-optimizer-canonicalize-crashes-w/base-1/tests/fixtures/optimizer/canonicalize.sql", "old_string": "DATEDIFF(CAST('2023-01-01' AS DATETIME), CAST('2023-01-02' AS DATETIME), DAY);\n", "new_string": "DATEDIFF(CAST('2023-01-01' AS DATETIME), CAST('2023-01-02' AS DATETIME), DAY);\n\nDATEDIFF(untyped_a, untyped_b, DAY);\nDATEDIFF(untyped_a, untyped_b, DAY);\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-092158-optimizer-canonicalize-crashes-w/base-1/tests/fixtures/optimizer/canonicalize.sql has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k canonicalize 2>&1 | tail -30", "description": "Run canonicalize optimizer tests"}
[tool_result]                         canonicalize_table_aliases
                    )
    
                future = pool.submit(parse_and_optimize, func, sql, dialect, **func_kwargs)
                results[future] = (
                    sql,
                    title,
                    expected,
                    dialect,
                    execute if meta.get("execute") is None else False,
                )
    
        for future in as_completed(results):
            sql, title, expected, dialect, e
…[390 chars elided]…
a" AS DATETIME), CAST("untyped_b" AS DATETIME), DAY)'
E               - DATEDIFF(untyped_a, untyped_b, DAY)
E               + DATEDIFF(CAST("untyped_a" AS DATETIME), CAST("untyped_b" AS DATETIME), DAY)

tests/test_optimizer.py:209: AssertionError
=========================== short test summary info ============================
SUBFAILED[32, DATEDIFF(untyped_a, untyped_b, DAY)] tests/test_optimizer.py::TestOptimizer::test_canonicalize
1 failed, 2 passed, 77 deselected, 100 subtests passed in 1.31s
[assistant] The fixture path doesn't reproduce the bug: unqualified columns get `UNKNOWN` type rather than `None`, so they take the existing cast branch. The crash only happens when the type is `None`, so the regression test should call `canonicalize` directly. I'll revert the fixture edit and add a direct test.
[tool_use Bash] {"command": "git checkout -- tests/fixtures/optimizer/canonicalize.sql && grep -n \"^from\\|^import\\|    def test_canonicalize\" tests/test_optimizer.py | head -40; grep -rln \"optimizer.canonicalize import\" tests/ ", "description": "Revert fixture edit and find test imports"}
[tool_result] 1:import unittest
2:from concurrent.futures import ProcessPoolExecutor, as_completed
3:from functools import partial
4:from unittest.mock import patch
6:import duckdb
7:from pandas.testing import assert_frame_equal
9:import sqlglot
10:from sqlglot import exp, optimizer, parse_one
11:from sqlglot.errors import ANSI_RESET, ANSI_UNDERLINE, OptimizeError, SchemaError
12:from sqlglot.optimizer.annotate_types import annotate_types
13:from sqlglot.optimizer.canonicalize_internal_names import canonicalize_internal_names
14:from sqlglot.optimizer.normalize import normalization_distance
15:from sqlglot.optimizer.qualify import qualify
16:from sqlglot.optimizer.scope import build_scope, traverse_scope, walk_in_scope
17:from sqlglot.schema import MappingSchema
18:from tests.helpers import (
1034:    def test_canonicalize_internal_names(self):
1273:    def test_canonicalize(self):
[tool_use Bash] {"command": "git status --short && git diff --stat && grep -c untyped tests/fixtures/optimizer/canonicalize.sql", "description": "Check working tree status after fixture revert"}
[tool_result]  M sqlglot/optimizer/canonicalize.py
 sqlglot/optimizer/canonicalize.py | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
0
[assistant] The fixture is back to its original state and only the source fix remains. Next I'll find where `test_canonicalize` ends so the new test can go right after it.
[tool_use Bash] {"command": "awk 'NR>1273 && /^    def /{print NR\": \"$0; exit}' tests/test_optimizer.py", "description": "Find end of test_canonicalize method"}
[tool_result] 1293:     def test_tpch(self):
[tool_use Bash] {"command": "sed -n 1286,1293p tests/test_optimizer.py", "description": "View lines just before test_tpch"}
[tool_result]         # into a CONCAT in Postgres, because that coalesces NULL values with empty strings
        ast = optimize("SELECT CAST(a AS TEXT) + CAST(b AS TEXT) FROM t", dialect="tsql")
        self.assertEqual(
            ast.sql("postgres"),
            'SELECT CAST("t"."a" AS TEXT) || CAST("t"."b" AS TEXT) AS "_col_0" FROM "t" AS "t"',
        )

    def test_tpch(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-092158-optimizer-canonicalize-crashes-w/base-1/tests/test_optimizer.py", "old_string": "            'SELECT CAST(\"t\".\"a\" AS TEXT) || CAST(\"t\".\"b\" AS TEXT) AS \"_col_0\" FROM \"t\" AS \"t\"',\n        )\n\n    def test_tpch(self):", "new_string": "            'SELECT CAST(\"t\".\"a\" AS TEXT) || CAST(\"t\".\"b\" AS TEXT) AS \"_col_0\" FROM \"t\" AS \"t\"',\n        )\n\n    def test_canonicalize_untyped_datediff(self):\n        expression = parse_one(\"SELECT DATEDIFF(a, b) FROM t\")\n        self.assertEqual(canonicalize(expression).sql(), \"SELECT DATEDIFF(a, b) FROM t\")\n\n    def test_tpch(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-092158-optimizer-canonicalize-crashes-w/base-1/tests/test_optimizer.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-092158-optimizer-canonicalize-crashes-w/base-1/tests/test_optimizer.py", "old_string": "from sqlglot.optimizer.annotate_types import annotate_types\n", "new_string": "from sqlglot.optimizer.annotate_types import annotate_types\nfrom sqlglot.optimizer.canonicalize import canonicalize\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-092158-optimizer-canonicalize-crashes-w/base-1/tests/test_optimizer.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k untyped_datediff 2>&1 | tail -2; git stash list >/dev/null; git diff --quiet sqlglot/optimizer/canonicalize.py; sed -i 's/if e.type and e.type.this/if e.type.this/' sqlglot/optimizer/canonicalize.py && $PY -m pytest -q -p no:cacheprov
…[180 chars elided]…
onicalize.py && git diff sqlglot/optimizer/canonicalize.py | grep \"^[+-] \" ; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1; <work>/env-sqlglot/bin/python -m ruff check sqlglot/optimizer/canonicalize.py tests/test_optimizer.py 2>&1 | tail -1", "description": "Verify regression test fails without fix, passes with it, and run full suite"}
[tool_result] .                                                                        [100%]
1 passed, 79 deselected in 0.19s
sed: 1: "sqlglot/optimizer/canon ...": unterminated substitute pattern
sed: 1: "sqlglot/optimizer/canon ...": unterminated substitute pattern
1108 passed, 18017 subtests passed in 49.91s
All checks passed!
[assistant] The `sed` probes errored, so I haven't yet confirmed the test fails without the fix. I'll check the fix is still in place and test against the original line via Python.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; git diff sqlglot/optimizer/canonicalize.py; cp sqlglot/optimizer/canonicalize.py /tmp/canon_fixed.py && $PY -c \"\nimport pathlib\np=pathlib.Path('sqlglot/optimizer/canonicalize.py')\np.write_text(p.read_text().replace('if e.type and e.type.this not in','if e.type.this not in'))\" && $PY -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k untyped_datediff 2>&1 | tail -1; cp /tmp/canon_fixed.py sqlglot/optimizer/canonicalize.py && git diff --stat && rm /tmp/canon_fixed.py", "description": "Confirm fix present and test fails without it"}
[tool_result] diff --git a/sqlglot/optimizer/canonicalize.py b/sqlglot/optimizer/canonicalize.py
index afb58085c..da220fd65 100644
--- a/sqlglot/optimizer/canonicalize.py
+++ b/sqlglot/optimizer/canonicalize.py
@@ -238,7 +238,7 @@ def _coerce_timeunit_arg(arg: exp.Expr, unit: exp.Expr | None) -> exp.Expr:
 
 def _coerce_datediff_args(node: exp.DateDiff) -> None:
     for e in (node.this, node.expression):
-        if e.type.this not in exp.DataType.TEMPORAL_TYPES:
+        if e.type and e.type.this not in exp.DataType.TEMPORAL_TYPES:
             e.replace(exp.cast(e.copy(), to=exp.DType.DATETIME))
 
 
1 failed, 79 deselected in 0.20s
 sqlglot/optimizer/canonicalize.py | 2 +-
 tests/test_optimizer.py           | 5 +++++
 2 files changed, 6 insertions(+), 1 deletion(-)
[assistant] `canonicalize` no longer crashes on a `DATEDIFF` argument with no inferred type. The argument is left alone, the same way `_coerce_date` and `_coerce_timeunit_arg` treat untyped arguments.

**The fix** is one line in `sqlglot/optimizer/canonicalize.py`, in `_coerce_datediff_args`: the type check is now `if e.type and e.type.this not in ...`. Untyped arguments fall through without being cast.

**Verification**
- Your repro now returns `SELECT DATEDIFF(a, b) FROM t`.
- I added `test_canonicalize_untyped_datediff` to `tests/test_optimizer.py`. It fails without the fix and passes with it.
- The fu
…[62 chars elided]…
 both changed files.

**Choices I made**
- **Test placement:** I put the regression test in `tests/test_optimizer.py` as a direct call to `canonicalize`. I first tried a fixture line in `tests/fixtures/optimizer/canonicalize.sql`, but it didn't reproduce the crash. Unqualified columns get an `UNKNOWN` type, not `None`, so they take the existing cast branch. I reverted that fixture edit.
- **Scope:** Arguments with `UNKNOWN` type still get cast to `DATETIME`, as before. I only changed the `None` case, since that's the one that crashed.

Nothing is committed. The changes are in the working tree.
