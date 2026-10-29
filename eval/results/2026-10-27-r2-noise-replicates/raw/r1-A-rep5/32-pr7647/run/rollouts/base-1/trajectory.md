# trajectory base-1

final message:
`canonicalize` no longer crashes on a `DATEDIFF` argument with no inferred type. The argument is left unchanged, and the full suite passes (1108 tests, 18017 subtests).

**Cause:** `_coerce_datediff_args` in `sqlglot/optimizer/canonicalize.py` read `e.type.this` without checking that `e.type` was set. The sibling helpers (`_coerce_date`, `_coerce_timeunit_arg`) return early in that case.

**Fix:** one line, `if e.type and e.type.this not in ...`, so untyped arguments are skipped.

**Test:** I added `test_canonicalize_datediff_untyped_args` to `tests/test_optimizer.py`. It runs `canonicalize(parse_one("SELECT DATEDIFF(a, b) FROM t"))` and expects the SQL back unchanged. I first tried a fixture case in `tests/fixtures/optimizer/canonicalize.sql`, but the fixture's schema types `a` and `b`, so it never reached the `None` path. I reverted that and used the direct unit test.

I did not commit anything. The CLAUDE.md asks for a model name in commit messages and PR titles, so when you commit, tell me whether you want that included.

## events
[tool_use Bash] {"command": "grep -n \"DateDiff\\|def _coerce_date\\|def coerce_date\\|def _replace_date\\|def _to_date\" -r sqlglot/optimizer/canonicalize.py sqlglot/optimizer/annotate_types.py sqlglot/optimizer/*.py | head -50", "description": "Locate DateDiff and date-coercion code in optimizer"}
[tool_result] sqlglot/optimizer/canonicalize.py:61:        # coerce_type (COERCIBLE_DATE_OPS + Between, Extract, DateAdd, DateSub, DateTrunc, DateDiff)
sqlglot/optimizer/canonicalize.py:68:        exp.DateDiff,
sqlglot/optimizer/canonicalize.py:124:    elif isinstance(node, exp.DateDiff):
sqlglot/optimizer/canonicalize.py:174:def _coerce_date(
sqlglot/optimizer/canonicalize.py:239:def _coerce_datediff_args(node: exp.DateDiff) -> None:
sqlglot/optimizer/annotate_types.py:87:def _coerce_date_literal(l: exp.Expr
…[291 chars elided]…
s.py:101:def _coerce_date(l: exp.Expr, unit: exp.Expr | None) -> exp.DType:
sqlglot/optimizer/canonicalize.py:61:        # coerce_type (COERCIBLE_DATE_OPS + Between, Extract, DateAdd, DateSub, DateTrunc, DateDiff)
sqlglot/optimizer/canonicalize.py:68:        exp.DateDiff,
sqlglot/optimizer/canonicalize.py:124:    elif isinstance(node, exp.DateDiff):
sqlglot/optimizer/canonicalize.py:174:def _coerce_date(
sqlglot/optimizer/canonicalize.py:239:def _coerce_datediff_args(node: exp.DateDiff) -> None:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105620-optimizer-canonicalize-crashes-w/base-1/sqlglot/optimizer/canonicalize.py"}
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
[assistant] The crash is in `_coerce_datediff_args`: it reads `e.type.this` without checking that `e.type` is set. The sibling helpers (`_coerce_timeunit_arg`, `_coerce_date`) return early when the type is missing. I'll reproduce first.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.canonicalize import canonicalize\nprint(canonicalize(parse_one('SELECT DATEDIFF(a, b) FROM t')).sql())\n\" 2>&1 | tail -5; grep -n \"DATEDIFF\\|DateDiff\" tests/test_optimizer.py | head; ls tests/fixtures/optimizer/ | grep -i canon", "description": "Reproduce the canonicalize DATEDIFF crash"}
[tool_result]     _coerce_datediff_args(node)
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105620-optimizer-canonicalize-crashes-w/base-1/sqlglot/optimizer/canonicalize.py", line 241, in _coerce_datediff_args
    if e.type.this not in exp.DataType.TEMPORAL_TYPES:
       ^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'this'
1664:                "SELECT DATEDIFF('2023-01-01', '2023-01-02', DAY) FROM x AS x",
canonicalize.sql
canonicalize_internal_names.sql
[assistant] Reproduced. Applying the fix: skip arguments with no inferred type, the same way `_coerce_date` does.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105620-optimizer-canonicalize-crashes-w/base-1/sqlglot/optimizer/canonicalize.py", "old_string": "        if e.type.this not in exp.DataType.TEMPORAL_TYPES:", "new_string": "        if e.type and e.type.this not in exp.DataType.TEMPORAL_TYPES:"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105620-optimizer-canonicalize-crashes-w/base-1/sqlglot/optimizer/canonicalize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "grep -n \"canonicalize\" tests/test_optimizer.py | head -5; grep -n -B2 -A3 \"DATE_DIFF\\|DATEDIFF\" tests/fixtures/optimizer/canonicalize.sql | head -40", "description": "Apply fix and find existing canonicalize tests"}
[tool_result] 13:from sqlglot.optimizer.canonicalize_internal_names import canonicalize_internal_names
32:def qualify_then_canonicalize(expression, **qualify_kwargs):
33:    return canonicalize_internal_names(qualify(expression, **qualify_kwargs))
176:                canonicalize_table_aliases = meta.get("canonicalize_table_aliases")
189:                if canonicalize_table_aliases is not None:
99-DATE_TRUNC('DAY', CAST('2023-01-01' AS DATE));
100-
101:DATEDIFF('2023-01-01', '2023-01-02', DAY);
102:DATEDIFF(CAST('2023-01-01' AS DATETIME), CAST('2023-01-02' AS DATETIME), DAY);
103-
104-SELECT "t"."d" > '2023-01-01' AS "d" FROM "temporal" AS "t";
105-SELECT "t"."d" > CAST('2023-01-01' AS DATE) AS "d" FROM "temporal" AS "t";
[assistant] I'll add a fixture case next to the existing DATEDIFF entry, then run the optimizer tests and the repro.
[tool_use Bash] {"command": "sed -n 96,104p tests/fixtures/optimizer/canonicalize.sql | cat -A | cut -c1-120", "description": "View fixture lines around DATEDIFF cases"}
[tool_result] cat: illegal option -- A
usage: cat [-belnstuv] [file ...]
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105620-optimizer-canonicalize-crashes-w/base-1/tests/fixtures/optimizer/canonicalize.sql", "offset": 96, "limit": 10}
[tool_result] 96	SELECT DATE_TRUNC('SECOND', CAST("t"."d" AS DATETIME)) AS "_col_0" FROM "temporal" AS "t";
97	
98	DATE_TRUNC('DAY', '2023-01-01');
99	DATE_TRUNC('DAY', CAST('2023-01-01' AS DATE));
100	
101	DATEDIFF('2023-01-01', '2023-01-02', DAY);
102	DATEDIFF(CAST('2023-01-01' AS DATETIME), CAST('2023-01-02' AS DATETIME), DAY);
103	
104	SELECT "t"."d" > '2023-01-01' AS "d" FROM "temporal" AS "t";
105	SELECT "t"."d" > CAST('2023-01-01' AS DATE) AS "d" FROM "temporal" AS "t";
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105620-optimizer-canonicalize-crashes-w/base-1/tests/fixtures/optimizer/canonicalize.sql", "old_string": "DATEDIFF(CAST('2023-01-01' AS DATETIME), CAST('2023-01-02' AS DATETIME), DAY);\n", "new_string": "DATEDIFF(CAST('2023-01-01' AS DATETIME), CAST('2023-01-02' AS DATETIME), DAY);\n\nDATEDIFF(a, b, DAY);\nDATEDIFF(a, b, DAY);\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105620-optimizer-canonicalize-crashes-w/base-1/tests/fixtures/optimizer/canonicalize.sql has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.canonicalize import canonicalize\nprint(canonicalize(parse_one('SELECT DATEDIFF(a, b) FROM t')).sql())\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py 2>&1 | tail -15", "description": "Verify repro fixed and run optimizer tests"}
[tool_result] SELECT DATEDIFF(a, b) FROM t
            with self.subTest(title):
                optimized = future.result()
                actual = optimized.sql(pretty=pretty, dialect=dialect)
>               self.assertEqual(
                    expected,
                    actual,
                )
E               AssertionError: 'DATEDIFF(a, b, DAY)' != 'DATEDIFF(CAST("a" AS DATETIME), CAST("b" AS DATETIME), DAY)'
E               - DATEDIFF(a, b, DAY)
E               + DATEDIFF(CAST("a" AS DATETIME), CAST("b" AS DATETIME), DAY)

tests/test_optimizer.py:209: AssertionError
=========================== short test summary info ============================
SUBFAILED[32, DATEDIFF(a, b, DAY)] tests/test_optimizer.py::TestOptimizer::test_canonicalize
1 failed, 79 passed, 3818 subtests passed in 15.37s
[assistant] The fixture case got a `CAST` added, so `a` and `b` have a non-None type under the fixture's schema. That means this case doesn't exercise the crash path. I'll check the schema the test uses before choosing where the regression test should go.
[tool_use Bash] {"command": "sed -n 180,200p tests/test_optimizer.py; grep -n \"def test_canonicalize\" -A6 tests/test_optimizer.py", "description": "Inspect canonicalize test harness and schema"}
[tool_result]                 if leave_tables_isolated is not None:
                    func_kwargs["leave_tables_isolated"] = string_to_bool(leave_tables_isolated)

                if validate_qualify_columns is not None:
                    func_kwargs["validate_qualify_columns"] = string_to_bool(
                        validate_qualify_columns
                    )
                if dialect:
                    func_kwargs["dialect"] = dialect
                if canonicalize_table_aliases is not None:
  
…[469 chars elided]…
  def test_canonicalize_internal_names(self):
1035-        schema = {
1036-            **self.schema,
1037-            "jtbl": {"j": "JSON"},
1038-            "pvt": {"c": "TEXT", "v": "INT"},
1039-        }
1040-
--
1273:    def test_canonicalize(self):
1274-        optimize = partial(
1275-            optimizer.optimize,
1276-            rules=[
1277-                optimizer.qualify.qualify,
1278-                optimizer.qualify_columns.quote_identifiers,
1279-                annotate_types,
[assistant] The fixture harness runs with the test schema, so `a` and `b` get typed there and the case never hits the `None` path. I'll revert the fixture line and add a direct unit test that calls `canonicalize` with no schema, which matches the reported repro.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105620-optimizer-canonicalize-crashes-w/base-1/tests/fixtures/optimizer/canonicalize.sql", "old_string": "DATEDIFF(CAST('2023-01-01' AS DATETIME), CAST('2023-01-02' AS DATETIME), DAY);\n\nDATEDIFF(a, b, DAY);\nDATEDIFF(a, b, DAY);\n", "new_string": "DATEDIFF(CAST('2023-01-01' AS DATETIME), CAST('2023-01-02' AS DATETIME), DAY);\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105620-optimizer-canonicalize-crashes-w/base-1/tests/fixtures/optimizer/canonicalize.sql has been updated successfully.
[tool_use Bash] {"command": "git status --short && grep -n \"^from\\|^import\" tests/test_optimizer.py && grep -n \"canonicalize\" tests/test_optimizer.py | head -3 && sed -n 1270,1273p tests/test_optimizer.py", "description": "Revert fixture edit and check test imports"}
[tool_result]  M sqlglot/optimizer/canonicalize.py
1:import unittest
2:from concurrent.futures import ProcessPoolExecutor, as_completed
3:from functools import partial
4:from unittest.mock import patch
6:import duckdb
7:from pandas.testing import assert_frame_equal
9:import sqlglot
10:from sqlglot import exp, optimizer, parse_one
11:from sqlglot.errors import ANSI_RESET, ANSI_UNDERLINE, OptimizeError, SchemaError
12:from sqlglot.optimizer.annotate_types import annotate_types
13:from sqlglot.optimizer.canonica
…[244 chars elided]…
n_scope
17:from sqlglot.schema import MappingSchema
18:from tests.helpers import (
13:from sqlglot.optimizer.canonicalize_internal_names import canonicalize_internal_names
32:def qualify_then_canonicalize(expression, **qualify_kwargs):
33:    return canonicalize_internal_names(qualify(expression, **qualify_kwargs))
        self.assertEqual(len(set(outer_table_aliases)), 3, outer_table_aliases)
        self.assertEqual(len(canon_triple_scope.selected_sources), 3)

    def test_canonicalize(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105620-optimizer-canonicalize-crashes-w/base-1/tests/test_optimizer.py", "old_string": "        self.assertEqual(len(canon_triple_scope.selected_sources), 3)\n\n    def test_canonicalize(self):", "new_string": "        self.assertEqual(len(canon_triple_scope.selected_sources), 3)\n\n    def test_canonicalize_datediff_untyped_args(self):\n        self.assertEqual(\n            canonicalize(parse_one(\"SELECT DATEDIFF(a, b) FROM t\")).sql(),\n            \"SELECT DATEDIFF(a, b) FROM t\",\n        )\n\n    def test_canonicalize(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105620-optimizer-canonicalize-crashes-w/base-1/tests/test_optimizer.py has been updated successfully.
[tool_use Bash] {"command": "sed -i 's/^from sqlglot.optimizer.annotate_types import annotate_types$/from sqlglot.optimizer.annotate_types import annotate_types\\nfrom sqlglot.optimizer.canonicalize import canonicalize/' tests/test_optimizer.py && sed -n 12,14p tests/test_optimizer.py && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py 2>&1 | tail -3 && git stash list | head -0; git diff --stat", "description": "Add canonicalize import and run optimizer tests"}
[tool_result] sed: 2: "tests/test_optimizer.py
": undefined label 'ests/test_optimizer.py'
 sqlglot/optimizer/canonicalize.py | 2 +-
 tests/test_optimizer.py           | 6 ++++++
 2 files changed, 7 insertions(+), 1 deletion(-)
[assistant] The `sed -i` call failed on macOS (it needs a backup suffix argument), so I'll add the import with Edit.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105620-optimizer-canonicalize-crashes-w/base-1/tests/test_optimizer.py", "old_string": "from sqlglot.optimizer.annotate_types import annotate_types\nfrom sqlglot.optimizer.canonicalize_internal_names import canonicalize_internal_names", "new_string": "from sqlglot.optimizer.annotate_types import annotate_types\nfrom sqlglot.optimizer.canonicalize import canonicalize\nfrom sqlglot.optimizer.canonicalize_internal_names import canonicalize_internal_names"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105620-optimizer-canonicalize-crashes-w/base-1/tests/test_optimizer.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py 2>&1 | tail -3; git stash --help >/dev/null 2>&1; git diff", "description": "Run optimizer tests and show diff"}
[tool_result] ............. [ 45%]
............................................                                                               [100%]
80 passed, 3818 subtests passed in 15.28s
diff --git a/sqlglot/optimizer/canonicalize.py b/sqlglot/optimizer/canonicalize.py
index afb58085c..da220fd65 100644
--- a/sqlglot/optimizer/canonicalize.py
+++ b/sqlglot/optimizer/canonicalize.py
@@ -238,7 +238,7 @@ def _coerce_timeunit_arg(arg: exp.Expr, unit: exp.Expr | None) -> exp.Expr:
 
 def _coerce_datediff_args(n
…[979 chars elided]…
 :this,SELECT :expressions,1,:exp
         self.assertEqual(len(set(outer_table_aliases)), 3, outer_table_aliases)
         self.assertEqual(len(canon_triple_scope.selected_sources), 3)
 
+    def test_canonicalize_datediff_untyped_args(self):
+        self.assertEqual(
+            canonicalize(parse_one("SELECT DATEDIFF(a, b) FROM t")).sql(),
+            "SELECT DATEDIFF(a, b) FROM t",
+        )
+
     def test_canonicalize(self):
         optimize = partial(
             optimizer.optimize,
[assistant] The optimizer tests pass. Next I'll run the full suite with the project's check command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4", "description": "Run full test suite"}
[tool_result] ........................................................................................................... [ 82%]
...................................................................................................... [ 91%]
.............................................................................................                            [100%]
1108 passed, 18017 subtests passed in 54.20s
[assistant] `canonicalize` no longer crashes on a `DATEDIFF` argument with no inferred type. The argument is left unchanged, and the full suite passes (1108 tests, 18017 subtests).

**Cause:** `_coerce_datediff_args` in `sqlglot/optimizer/canonicalize.py` read `e.type.this` without checking that `e.type` was set. The sibling helpers (`_coerce_date`, `_coerce_timeunit_arg`) return early in that case.

**Fix:** one line, `if e.type and e.type.this not in ...`, so untyped arguments are skipped.

**Test:** I added `test_canonicalize_datediff_untyped_args` to `tests/test_optimizer.py`. It runs `canonicalize(parse_one("SELECT DATEDIFF(a, b) FROM t"))` and expects the SQL back unchanged. I first tried a fixture case in `tests/fixtures/optimizer/canonicalize.sql`, but the fixture's schema types `a` and `b`, so it never reached the `None` path. I reverted that and used the direct unit test.

I did not commit anything. The CLAUDE.md asks for a model name in commit messages and PR titles, so when you commit, tell me whether you want that included.
