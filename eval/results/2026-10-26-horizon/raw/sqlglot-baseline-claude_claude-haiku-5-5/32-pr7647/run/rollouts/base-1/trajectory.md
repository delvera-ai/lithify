# trajectory base-1

final message:
`canonicalize` no longer crashes on a `DATEDIFF` argument with no inferred type. Those arguments are left alone, as the other date-coercion helpers do.

**Cause:** `_coerce_datediff_args` in `sqlglot/optimizer/canonicalize.py` read `e.type.this` without checking that `e.type` was set.

**Fix:** one line, guarding on the type before reading it:

```python
if e.type and e.type.this not in exp.DataType.TEMPORAL_TYPES:
```

**Test:** I added `test_canonicalize_datediff_unknown_type` to `tests/test_optimizer.py`. It canonicalizes `SELECT DATEDIFF(a, b) FROM t` and expects the SQL back unchanged. It fails without the fix and passes with it. I put it there rather than in the `canonicalize.sql` fixture because that fixture runs with a schema, and an untyped column can't be produced through it.

**Results:**
- Full suite (`tests/`, using the project's pytest command): 1108 passed.
- `ruff check` and `ruff format --check` pass on both changed files.

The changes are uncommitted in the worktree. I didn't commit, since you didn't ask for one. If you want one, I'll commit with the Co-Authored-By line from the session instructions.

## events
[tool_use Bash] {"command": "grep -n \"def \\|DATEDIFF\\|DateDiff\\|\\.type\" sqlglot/optimizer/canonicalize.py | head -80", "description": "Inspect canonicalize.py structure"}
[tool_result] 12:def canonicalize(expression: exp.Expr, dialect: DialectType = None) -> exp.Expr:
24:    def _canonicalize(expression: exp.Expr) -> exp.Expr:
61:        # coerce_type (COERCIBLE_DATE_OPS + Between, Extract, DateAdd, DateSub, DateTrunc, DateDiff)
68:        exp.DateDiff,
83:def add_text_to_concat(node: exp.Expr) -> exp.Expr:
84:    if isinstance(node, exp.Add) and node.type and node.type.this in exp.DataType.TEXT_TYPES:
94:def replace_date_funcs(node: exp.Expr, dialect: DialectType) -> exp.Expr
…[923 chars elided]…
) -> exp.Expr:
219:    if not arg.type:
222:    if arg.type.this in exp.DataType.TEXT_TYPES:
233:    elif arg.type.this == exp.DType.DATE and not is_date_unit(unit):
239:def _coerce_datediff_args(node: exp.DateDiff) -> None:
241:        if e.type.this not in exp.DataType.TEMPORAL_TYPES:
245:def _replace_cast(node: exp.Expr, to: exp.DATA_TYPE) -> None:
253:def _replace_int_predicate(expression: exp.Expr) -> None:
257:    elif expression.type and expression.type.this in exp.DataType.INTEGER_TYPES:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-151854-optimizer-canonicalize-crashes-w/base-1/sqlglot/optimizer/canonicalize.py"}
[tool_result] 1	from __future__ import annotations
2	
3	import itertools
4	import typing as t
5	
6	from sqlglot import exp
7	from sqlglot.dialects.dialect import Dialect, DialectType
8	from sqlglot.helper import is_date_unit, is_iso_date, is_iso_datetime
9	from sqlglot.optimizer.annotate_types import TypeAnnotator
10	
11	
12	def canonicalize(expression: exp.Expr, dialect: DialectType = None) -> exp.Expr:
13	    """Converts a sql expression into a standard form.
14	
15	    This method relies on annotate_types 
…[8464 chars elided]…
1	# presto has a boolean type whereas tsql doesn't (people use bits)
252	# with y as (select true as x) select x = 0 FROM y -- illegal presto query
253	def _replace_int_predicate(expression: exp.Expr) -> None:
254	    if isinstance(expression, exp.Coalesce):
255	        for child in expression.iter_expressions():
256	            _replace_int_predicate(child)
257	    elif expression.type and expression.type.this in exp.DataType.INTEGER_TYPES:
258	        expression.replace(expression.neq(0))
259	
[assistant] The crash is in `_coerce_datediff_args` (line 241): `e.type.this` runs even when `e.type` is `None`. I'll reproduce it first, then find the existing canonicalize tests.
[tool_use Bash] {"command": "python -c \"\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.canonicalize import canonicalize\nprint(canonicalize(parse_one('SELECT DATEDIFF(a, b) FROM t')).sql())\n\" 2>&1 | tail -3; grep -rn \"canonicalize\" tests/ | head -20", "description": "Reproduce crash and find canonicalize tests"}
[tool_result]     if e.type.this not in exp.DataType.TEMPORAL_TYPES:
       ^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'this'
tests/test_optimizer.py:13:from sqlglot.optimizer.canonicalize_internal_names import canonicalize_internal_names
tests/test_optimizer.py:32:def qualify_then_canonicalize(expression, **qualify_kwargs):
tests/test_optimizer.py:33:    return canonicalize_internal_names(qualify(expression, **qualify_kwargs))
tests/test_optimizer.py:176:                canonicalize_table
…[952 chars elided]…
imizer.py:1065:        canon_rename = qualify_then_canonicalize(
tests/test_optimizer.py:1073:        canon_alias_a = qualify_then_canonicalize(
tests/test_optimizer.py:1077:        canon_alias_b = qualify_then_canonicalize(
tests/test_optimizer.py:1084:        # handles and must be canonicalized — otherwise structurally identical queries
tests/test_optimizer.py:1086:        canon_unref_a = qualify_then_canonicalize(
tests/test_optimizer.py:1090:        canon_unref_b = qualify_then_canonicalize(
[assistant] Reproduced. Now the fix: skip arguments whose type is unknown, matching `_coerce_timeunit_arg`'s `if not arg.type: return arg`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-151854-optimizer-canonicalize-crashes-w/base-1/sqlglot/optimizer/canonicalize.py", "old_string": "        if e.type.this not in exp.DataType.TEMPORAL_TYPES:", "new_string": "        if e.type and e.type.this not in exp.DataType.TEMPORAL_TYPES:"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-151854-optimizer-canonicalize-crashes-w/base-1/sqlglot/optimizer/canonicalize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "grep -rln \"canonicalize import\\|optimizer.canonicalize\\b\" tests/ ; ls tests | grep -i canon; grep -n \"canonicalize\" tests/*.py | grep -v internal | head", "description": "Apply fix and locate existing canonicalize test file"}
[tool_result] tests/test_optimizer.py
tests/test_optimizer.py:32:def qualify_then_canonicalize(expression, **qualify_kwargs):
tests/test_optimizer.py:176:                canonicalize_table_aliases = meta.get("canonicalize_table_aliases")
tests/test_optimizer.py:189:                if canonicalize_table_aliases is not None:
tests/test_optimizer.py:190:                    func_kwargs["canonicalize_table_aliases"] = string_to_bool(
tests/test_optimizer.py:191:                        canonicalize_table_aliases
tests/test_optimizer.py:321:        optimizer.qualify_tables.qualify_tables(expression, canonicalize_table_aliases=True)
tests/test_optimizer.py:1043:            qualify_then_canonicalize,
tests/test_optimizer.py:1053:        canon_a = qualify_then_canonicalize(
tests/test_optimizer.py:1057:        canon_diff_table = qualify_then_canonicalize(
tests/test_optimizer.py:1065:        canon_rename = qualify_then_canonicalize(
[tool_use Bash] {"command": "grep -rn \"canonicalize(\" tests/ | head; ls tests/fixtures/optimizer | grep -i canon", "description": "Find existing canonicalize() test usages"}
[tool_result] tests/test_optimizer.py:32:def qualify_then_canonicalize(expression, **qualify_kwargs):
tests/test_optimizer.py:1053:        canon_a = qualify_then_canonicalize(
tests/test_optimizer.py:1057:        canon_diff_table = qualify_then_canonicalize(
tests/test_optimizer.py:1065:        canon_rename = qualify_then_canonicalize(
tests/test_optimizer.py:1073:        canon_alias_a = qualify_then_canonicalize(
tests/test_optimizer.py:1077:        canon_alias_b = qualify_then_canonicalize(
tests/test_optimizer.py:1086:        canon_unref_a = qualify_then_canonicalize(
tests/test_optimizer.py:1090:        canon_unref_b = qualify_then_canonicalize(
tests/test_optimizer.py:1096:        canon_exists_a = qualify_then_canonicalize(
tests/test_optimizer.py:1100:        canon_exists_b = qualify_then_canonicalize(
canonicalize.sql
canonicalize_internal_names.sql
[assistant] There's a fixture file `tests/fixtures/optimizer/canonicalize.sql`. I'll check its format and how it's run.
[tool_use Bash] {"command": "head -30 tests/fixtures/optimizer/canonicalize.sql; grep -n \"canonicalize.sql\\|\\\"canonicalize\\\"\" tests/*.py; grep -n -i \"datediff\" tests/fixtures/optimizer/canonicalize.sql", "description": "Inspect canonicalize fixture format"}
[tool_result] SELECT w.d + w.e AS c FROM w AS w;
SELECT CONCAT("w"."d", "w"."e") AS "c" FROM "w" AS "w";

SELECT CAST(w.d AS DATE) > w.e AS a FROM w AS w;
SELECT CAST("w"."d" AS DATE) > CAST("w"."e" AS DATE) AS "a" FROM "w" AS "w";

SELECT CAST(1 AS VARCHAR) AS a FROM w AS w;
SELECT CAST(1 AS VARCHAR) AS "a" FROM "w" AS "w";

SELECT CAST(1 + 3.2 AS DOUBLE) AS a FROM w AS w;
SELECT 1 + 3.2 AS "a" FROM "w" AS "w";

SELECT '1' + 1 AS "col";
SELECT '1' + 1 AS "col";

SELECT '1' + '1' AS "col";
SELECT CONCAT('1', 
…[157 chars elided]…
-01' AS DATE) IS NULL AS "a";
SELECT CAST('2022-01-01' AS DATE) IS NULL AS "a";

--------------------------------------
-- Ensure boolean predicates
--------------------------------------
SELECT a FROM x WHERE b;
SELECT "x"."a" AS "a" FROM "x" AS "x" WHERE "x"."b" <> 0;

tests/test_optimizer.py:1283:        self.check_file("canonicalize", optimize, schema=self.schema)
101:DATEDIFF('2023-01-01', '2023-01-02', DAY);
102:DATEDIFF(CAST('2023-01-01' AS DATETIME), CAST('2023-01-02' AS DATETIME), DAY);
[tool_use Bash] {"command": "sed -n 1270,1285p tests/test_optimizer.py; grep -n \"self.schema = \\|\\\"w\\\": {\\|\\\"x\\\": {\" tests/test_optimizer.py | head; grep -n \"def optimize\" -A12 tests/test_optimizer.py | head -30", "description": "Inspect canonicalize test harness and schema"}
[tool_result]         self.assertEqual(len(set(outer_table_aliases)), 3, outer_table_aliases)
        self.assertEqual(len(canon_triple_scope.selected_sources), 3)

    def test_canonicalize(self):
        optimize = partial(
            optimizer.optimize,
            rules=[
                optimizer.qualify.qualify,
                optimizer.qualify_columns.quote_identifiers,
                annotate_types,
                optimizer.canonicalize.canonicalize,
            ],
        )
        self.check_fil
…[207 chars elided]…
"w": {
232:            "x": {"a": "INT", "b": "INT"},
402:                schema={"db": {"x": {"z": "int"}, "y": {"a": "int"}}},
411:                schema={"db": {"x": {"z": "int"}, "y": {"a": "int"}}},
700:                expression, schema={"x": {"a": "int", "b": "int", "c": "str"}}
744:        schema = MappingSchema(self.schema, {"x": {"a"}, "y": {"b"}, "z": {"b"}})
1111:            schema={"x": {"a": "INT"}},
1120:            parse_one("SELECT a AS alpha FROM x"), schema={"x": {"a": "INT"}}
[assistant] The fixture harness runs with `self.schema`. I'll check which columns that schema defines, so I can pick a column with no type.
[tool_use Bash] {"command": "sed -n 123,145p tests/test_optimizer.py; sed -n 95,105p tests/fixtures/optimizer/canonicalize.sql", "description": "Read test schema and nearby DATEDIFF fixtures"}
[tool_result]         self.schema = {
            "x": {
                "a": "INT",
                "b": "INT",
            },
            "y": {
                "b": "INT",
                "c": "INT",
            },
            "z": {
                "b": "INT",
                "c": "INT",
            },
            "w": {
                "d": "TEXT",
                "e": "TEXT",
            },
            "temporal": {
                "d": "DATE",
                "t": "DATETIME",
            },
           
…[53 chars elided]…
 b_1 VARCHAR>",
SELECT DATE_TRUNC('SECOND', t.d) FROM temporal AS t;
SELECT DATE_TRUNC('SECOND', CAST("t"."d" AS DATETIME)) AS "_col_0" FROM "temporal" AS "t";

DATE_TRUNC('DAY', '2023-01-01');
DATE_TRUNC('DAY', CAST('2023-01-01' AS DATE));

DATEDIFF('2023-01-01', '2023-01-02', DAY);
DATEDIFF(CAST('2023-01-01' AS DATETIME), CAST('2023-01-02' AS DATETIME), DAY);

SELECT "t"."d" > '2023-01-01' AS "d" FROM "temporal" AS "t";
SELECT "t"."d" > CAST('2023-01-01' AS DATE) AS "d" FROM "temporal" AS "t";
[assistant] The fixture schema has no untyped columns, so I'll try a bare `DATEDIFF(a, b)` with no FROM clause. That gives untyped arguments without relying on the schema.
[tool_use Bash] {"command": "python -c \"\nfrom sqlglot import parse_one, optimizer\nfrom sqlglot.optimizer.canonicalize import canonicalize\nfrom sqlglot.optimizer.annotate_types import annotate_types\nfrom sqlglot.optimizer import qualify\nfor s in ['SELECT DATEDIFF(a, b) FROM t', 'SELECT DATEDIFF(a, b)']:\n    print(canonicalize(parse_one(s)).sql())\nprint(optimizer.optimize(parse_one('SELECT DATEDIFF(a, b)'), rules=[qualify.qualify, optimizer.qualify_columns.quote_identifiers, annotate_types, optimizer.canonicalize.canonicalize]).sql())\n\" 2>&1 | tail -5", "description": "Verify fix on repro and candidate fixture SQL"}
[tool_result]   File "~/.cache/lithify/work/repo-b63a38b63828/20261026-151854-optimizer-canonicalize-crashes-w/base-1/sqlglot/optimizer/qualify_columns.py", line 139, in validate_qualify_columns
    raise OptimizeError(error_msg)
sqlglot.errors.OptimizeError: Column 'a' could not be resolved. Line: 1, Col: 17
SELECT DATEDIFF(a, b) FROM t
SELECT DATEDIFF(a, b)
[assistant] The repro passes now: canonicalize returns `SELECT DATEDIFF(a, b) FROM t` unchanged. The fixture harness can't reach this case because it resolves columns against the schema, so I'll add a focused unit test next to `test_canonicalize` instead.
[tool_use Bash] {"command": "sed -n 1,30p tests/test_optimizer.py | grep -n \"import\"; sed -n 1284,1300p tests/test_optimizer.py", "description": "Check test imports and context after test_canonicalize"}
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
13:from sqlglot.optimizer.canonicalize_internal_names import canonicali
…[527 chars elided]…
b AS TEXT) FROM t", dialect="tsql")
        self.assertEqual(
            ast.sql("postgres"),
            'SELECT CAST("t"."a" AS TEXT) || CAST("t"."b" AS TEXT) AS "_col_0" FROM "t" AS "t"',
        )

    def test_tpch(self):
        self.check_file("tpc-h/tpc-h", optimizer.optimize, schema=TPCH_SCHEMA, pretty=True)

    def test_tpcds(self):
        self.check_file("tpc-ds/tpc-ds", optimizer.optimize, schema=TPCDS_SCHEMA, pretty=True)

    def test_file_schema(self):
        self.assertEqual(
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-151854-optimizer-canonicalize-crashes-w/base-1/tests/test_optimizer.py", "old_string": "            'SELECT CAST(\"t\".\"a\" AS TEXT) || CAST(\"t\".\"b\" AS TEXT) AS \"_col_0\" FROM \"t\" AS \"t\"',\n        )\n\n    def test_tpch(self):", "new_string": "            'SELECT CAST(\"t\".\"a\" AS TEXT) || CAST(\"t\".\"b\" AS TEXT) AS \"_col_0\" FROM \"t\" AS \"t\"',\n        )\n\n    def test_canonicalize_datediff_unknown_type(self):\n        self.assertEqual(\n            optimizer.canonicalize.canonicalize(parse_one(\"SELECT DATEDIFF(a, b) FROM t\")).sql(),\n            \"SELECT DATEDIFF(a, b) FROM t\",\n        )\n\n    def test_tpch(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-151854-optimizer-canonicalize-crashes-w/base-1/tests/test_optimizer.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k \"canonicalize\" 2>&1 | tail -15", "description": "Run canonicalize-related optimizer tests"}
[tool_result] ... [100%]
3 passed, 77 deselected, 100 subtests passed in 1.65s
[assistant] Targeted tests pass. Now I'll confirm the new test fails without the fix, then run the full suite the project harness specifies.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; git stash list >/dev/null; sed -i.bak 's/if e.type and e.type.this/if e.type.this/' sqlglot/optimizer/canonicalize.py && $PY -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k datediff_unknown 2>&1 | tail -2; mv sqlglot/optimizer/canonicalize.py.bak sqlglot/optimizer/canonicalize.py; git diff --stat; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Confirm test fails pre-fix, restore fix, run full suite"}
[tool_result] FAILED tests/test_optimizer.py::TestOptimizer::test_canonicalize_datediff_unknown_type
1 failed, 79 deselected in 0.22s
 sqlglot/optimizer/canonicalize.py | 2 +-
 tests/test_optimizer.py           | 6 ++++++
 2 files changed, 7 insertions(+), 1 deletion(-)
............................................... [ 72%]
........................................................................................................... [ 82%]
...................................................................................................... [ 91%]
.............................................................................................                            [100%]
1108 passed, 18017 subtests passed in 54.09s
[assistant] The test fails before the fix and the full suite passes (1108 passed). I'll run the project's linter and formatter on the two changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff check sqlglot/optimizer/canonicalize.py tests/test_optimizer.py 2>&1 | tail -2; $PY -m ruff format --check sqlglot/optimizer/canonicalize.py tests/test_optimizer.py 2>&1 | tail -2; git diff", "description": "Lint, format-check, and show final diff"}
[tool_result] All checks passed!
2 files already formatted
diff --git a/sqlglot/optimizer/canonicalize.py b/sqlglot/optimizer/canonicalize.py
index afb58085c..da220fd65 100644
--- a/sqlglot/optimizer/canonicalize.py
+++ b/sqlglot/optimizer/canonicalize.py
@@ -238,7 +238,7 @@ def _coerce_timeunit_arg(arg: exp.Expr, unit: exp.Expr | None) -> exp.Expr:
 
 def _coerce_datediff_args(node: exp.DateDiff) -> None:
     for e in (node.this, node.expression):
-        if e.type.this not in exp.DataType.TEMPORAL_TYPES:

…[371 chars elided]…
his,SELECT :expressions,1,:exp
             'SELECT CAST("t"."a" AS TEXT) || CAST("t"."b" AS TEXT) AS "_col_0" FROM "t" AS "t"',
         )
 
+    def test_canonicalize_datediff_unknown_type(self):
+        self.assertEqual(
+            optimizer.canonicalize.canonicalize(parse_one("SELECT DATEDIFF(a, b) FROM t")).sql(),
+            "SELECT DATEDIFF(a, b) FROM t",
+        )
+
     def test_tpch(self):
         self.check_file("tpc-h/tpc-h", optimizer.optimize, schema=TPCH_SCHEMA, pretty=True)
[assistant] `canonicalize` no longer crashes on a `DATEDIFF` argument with no inferred type. Those arguments are left alone, as the other date-coercion helpers do.

**Cause:** `_coerce_datediff_args` in `sqlglot/optimizer/canonicalize.py` read `e.type.this` without checking that `e.type` was set.

**Fix:** one line, guarding on the type before reading it:

```python
if e.type and e.type.this not in exp.DataType.TEMPORAL_TYPES:
```

**Test:** I added `test_canonicalize_datediff_unknown_type` to `tests/test_optimizer.py`. It canonicalizes `SELECT DATEDIFF(a, b) FROM t` and expects the SQL back unchanged. It fails without the fix and passes with it. I put it there rather than in the `canonicalize.sql` fixture because that fixture runs with a schema, and an untyped column can't be produced through it.

**Results:**
- Full suite (`tests/`, using the project's pytest command): 1108 passed.
- `ruff check` and `ruff format --check` pass on both changed files.

The changes are uncommitted in the worktree. I didn't commit, since you didn't ask for one. If you want one, I'll commit with the Co-Authored-By line from the session instructions.
