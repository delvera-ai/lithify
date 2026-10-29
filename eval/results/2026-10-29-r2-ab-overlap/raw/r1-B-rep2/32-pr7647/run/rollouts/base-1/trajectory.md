# trajectory base-1

final message:
`canonicalize` no longer crashes on `DATEDIFF` arguments with no inferred type. The full suite passes (1107 tests).

**The fix:** in `sqlglot/optimizer/canonicalize.py`, `_coerce_datediff_args` read `e.type.this` without checking that `e.type` was set. It now checks `e.type and ...`, so an argument with no type is skipped. That matches how `_coerce_date` and `_coerce_timeunit_arg` already handle missing types.

**Test:** I added a case to `test_canonicalize` in `tests/test_optimizer.py` (plus the import it needs). It runs `canonicalize(parse_one("SELECT DATEDIFF(a, b) FROM t"))` and expects the SQL unchanged. I reproduced the `AttributeError` before the change.

**Behaviour to be aware of:** the fix only covers arguments whose type is `None`. Arguments typed as `UNKNOWN`, which is what the optimizer's annotation pass gives untyped columns, still get cast to `DATETIME`, as they did before. I left that alone because the issue only asked for the crash fix. If you want `UNKNOWN` skipped too, that is a separate behaviour change.

I did not commit anything.

## events
[tool_use Bash] {"command": "cat sqlglot/optimizer/canonicalize.py && grep -rn \"DateDiff\\|def _coerce_date\\|def coerce_date\" sqlglot/optimizer/*.py | head -40", "description": "Read canonicalize module and find date helpers"}
[tool_result] from __future__ import annotations

import itertools
import typing as t

from sqlglot import exp
from sqlglot.dialects.dialect import Dialect, DialectType
from sqlglot.helper import is_date_unit, is_iso_date, is_iso_datetime
from sqlglot.optimizer.annotate_types import TypeAnnotator


def canonicalize(expression: exp.Expr, dialect: DialectType = None) -> exp.Expr:
    """Converts a sql expression into a standard form.

    This method relies on annotate_types because many of the
    conversions 
…[8181 chars elided]…
s.py:101:def _coerce_date(l: exp.Expr, unit: exp.Expr | None) -> exp.DType:
sqlglot/optimizer/canonicalize.py:61:        # coerce_type (COERCIBLE_DATE_OPS + Between, Extract, DateAdd, DateSub, DateTrunc, DateDiff)
sqlglot/optimizer/canonicalize.py:68:        exp.DateDiff,
sqlglot/optimizer/canonicalize.py:124:    elif isinstance(node, exp.DateDiff):
sqlglot/optimizer/canonicalize.py:174:def _coerce_date(
sqlglot/optimizer/canonicalize.py:239:def _coerce_datediff_args(node: exp.DateDiff) -> None:
[assistant] The crash is in `_coerce_datediff_args`, which reads `e.type.this` without checking that `e.type` exists. Let me reproduce it first.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.canonicalize import canonicalize\nprint(canonicalize(parse_one('SELECT DATEDIFF(a, b) FROM t')).sql())\n\" 2>&1 | tail -5", "description": "Reproduce the canonicalize crash"}
[tool_result]     _coerce_datediff_args(node)
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-153802-optimizer-canonicalize-crashes-w/base-1/sqlglot/optimizer/canonicalize.py", line 241, in _coerce_datediff_args
    if e.type.this not in exp.DataType.TEMPORAL_TYPES:
       ^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'this'
[assistant] Reproduced. I'll apply the same guard the other helpers use: skip arguments whose type is unknown.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-153802-optimizer-canonicalize-crashes-w/base-1/sqlglot/optimizer/canonicalize.py", "old_string": "        if e.type.this not in exp.DataType.TEMPORAL_TYPES:", "new_string": "        if e.type and e.type.this not in exp.DataType.TEMPORAL_TYPES:"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-153802-optimizer-canonicalize-crashes-w/base-1/sqlglot/optimizer/canonicalize.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.canonicalize import canonicalize\nprint(canonicalize(parse_one('SELECT DATEDIFF(a, b) FROM t')).sql())\nprint(canonicalize(parse_one(\\\"SELECT DATEDIFF(CAST(a AS VARCHAR), '2020-01-01') FROM t\\\")).sql())\n\" 2>&1 | tail -5", "description": "Apply guard and re-run repro"}
[tool_result] SELECT DATEDIFF(a, b) FROM t
SELECT DATEDIFF(CAST(CAST(a AS VARCHAR) AS DATETIME), '2020-01-01') FROM t
[assistant] The crash is gone and typed arguments still get the existing coercion. Next I'll add a regression test next to the existing canonicalize tests.
[tool_use Bash] {"command": "grep -rn \"canonicalize\" tests/*.py | head; grep -n \"DATEDIFF\\|DateDiff\" tests/fixtures/optimizer/canonicalize.sql | head", "description": "Locate canonicalize tests and DATEDIFF fixtures"}
[tool_result] tests/test_optimizer.py:13:from sqlglot.optimizer.canonicalize_internal_names import canonicalize_internal_names
tests/test_optimizer.py:32:def qualify_then_canonicalize(expression, **qualify_kwargs):
tests/test_optimizer.py:33:    return canonicalize_internal_names(qualify(expression, **qualify_kwargs))
tests/test_optimizer.py:176:                canonicalize_table_aliases = meta.get("canonicalize_table_aliases")
tests/test_optimizer.py:189:                if canonicalize_table_aliases is not N
…[198 chars elided]…
test_optimizer.py:321:        optimizer.qualify_tables.qualify_tables(expression, canonicalize_table_aliases=True)
tests/test_optimizer.py:1034:    def test_canonicalize_internal_names(self):
tests/test_optimizer.py:1042:            "canonicalize_internal_names",
2 matches in 1 files:

tests/fixtures/optimizer/canonicalize.sql:101:DATEDIFF('2023-01-01', '2023-01-02', DAY);
tests/fixtures/optimizer/canonicalize.sql:102:DATEDIFF(CAST('2023-01-01' AS DATETIME), CAST('2023-01-02' AS DATETIME), DAY);
[tool_use Bash] {"command": "sed -n 95,110p tests/fixtures/optimizer/canonicalize.sql; echo ---; tail -c 300 tests/fixtures/optimizer/canonicalize.sql | od -c | tail -3", "description": "View DATEDIFF fixture region"}
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
---
0000420    '   Y   E   A   R   '   ,       C   A   S   T   (   "   x   "
0000440        A   S       D   A   T   E   )   )   ;  \n                
0000454
[assistant] I'll add a fixture case right after the existing DATEDIFF entry and run the optimizer tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-153802-optimizer-canonicalize-crashes-w/base-1/tests/fixtures/optimizer/canonicalize.sql", "old_string": "DATEDIFF(CAST('2023-01-01' AS DATETIME), CAST('2023-01-02' AS DATETIME), DAY);\n", "new_string": "DATEDIFF(CAST('2023-01-01' AS DATETIME), CAST('2023-01-02' AS DATETIME), DAY);\n\nDATEDIFF(a, b);\nDATEDIFF(a, b);\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-153802-optimizer-canonicalize-crashes-w/base-1/tests/fixtures/optimizer/canonicalize.sql has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k canonical 2>&1 | tail -15", "description": "Run canonicalize optimizer tests"}
[tool_result]             with self.subTest(title):
                optimized = future.result()
                actual = optimized.sql(pretty=pretty, dialect=dialect)
>               self.assertEqual(
                    expected,
                    actual,
                )
E               AssertionError: 'DATEDIFF(a, b)' != 'DATEDIFF(CAST("a" AS DATETIME), CAST("b" AS DATETIME))'
E               - DATEDIFF(a, b)
E               + DATEDIFF(CAST("a" AS DATETIME), CAST("b" AS DATETIME))

tests/test_optimizer.py:209: AssertionError
=========================== short test summary info ============================
SUBFAILED[32, DATEDIFF(a, b)] tests/test_optimizer.py::TestOptimizer::test_canonicalize
1 failed, 2 passed, 77 deselected, 100 subtests passed in 1.54s
[assistant] The fixture harness annotates types, so `a` and `b` come through as `UNKNOWN` rather than `None`. That is a different case, and the existing code deliberately casts those, so the fixture expectation was wrong. I'll revert the fixture and cover the untyped (`None`) path with a direct test instead.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-153802-optimizer-canonicalize-crashes-w/base-1/tests/fixtures/optimizer/canonicalize.sql", "old_string": "DATEDIFF(CAST('2023-01-01' AS DATETIME), CAST('2023-01-02' AS DATETIME), DAY);\n\nDATEDIFF(a, b);\nDATEDIFF(a, b);\n", "new_string": "DATEDIFF(CAST('2023-01-01' AS DATETIME), CAST('2023-01-02' AS DATETIME), DAY);\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-153802-optimizer-canonicalize-crashes-w/base-1/tests/fixtures/optimizer/canonicalize.sql has been updated successfully.
[tool_use Bash] {"command": "grep -n \"def test_canonicalize\" -A 12 tests/test_optimizer.py; grep -n \"^from\\|^import\" tests/test_optimizer.py", "description": "Inspect test_canonicalize and imports"}
[tool_result] 1034:    def test_canonicalize_internal_names(self):
1035-        schema = {
1036-            **self.schema,
1037-            "jtbl": {"j": "JSON"},
1038-            "pvt": {"c": "TEXT", "v": "INT"},
1039-        }
1040-
1041-        self.check_file(
1042-            "canonicalize_internal_names",
1043-            qualify_then_canonicalize,
1044-            schema=schema,
1045-            catalog="c",
1046-            db="db",
--
1273:    def test_canonicalize(self):
1274-        optimize = part
…[1179 chars elided]…

tests/test_optimizer.py:13:from sqlglot.optimizer.canonicalize_internal_names import canonicalize_intern...
tests/test_optimizer.py:14:from sqlglot.optimizer.normalize import normalization_distance
tests/test_optimizer.py:15:from sqlglot.optimizer.qualify import qualify
tests/test_optimizer.py:16:from sqlglot.optimizer.scope import build_scope, traverse_scope, walk_in_scope
tests/test_optimizer.py:17:from sqlglot.schema import MappingSchema
tests/test_optimizer.py:18:from tests.helpers import (
[tool_use Bash] {"command": "sed -n 1283,1300p tests/test_optimizer.py", "description": "View end of test_canonicalize"}
[tool_result]         self.check_file("canonicalize", optimize, schema=self.schema)

        # In T-SQL and Redshift, SELECT a + b can produce a NULL, so we can't transpile it
        # into a CONCAT in Postgres, because that coalesces NULL values with empty strings
        ast = optimize("SELECT CAST(a AS TEXT) + CAST(b AS TEXT) FROM t", dialect="tsql")
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-153802-optimizer-canonicalize-crashes-w/base-1/tests/test_optimizer.py", "old_string": "            'SELECT CAST(\"t\".\"a\" AS TEXT) || CAST(\"t\".\"b\" AS TEXT) AS \"_col_0\" FROM \"t\" AS \"t\"',\n        )\n\n    def test_tpch(self):", "new_string": "            'SELECT CAST(\"t\".\"a\" AS TEXT) || CAST(\"t\".\"b\" AS TEXT) AS \"_col_0\" FROM \"t\" AS \"t\"',\n        )\n\n        # DATEDIFF arguments without an inferred type are left untouched\n        self.assertEqual(\n            canonicalize(parse_one(\"SELECT DATEDIFF(a, b) FROM t\")).sql(),\n            \"SELECT DATEDIFF(a, b) FROM t\",\n        )\n\n    def test_tpch(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-153802-optimizer-canonicalize-crashes-w/base-1/tests/test_optimizer.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"^from sqlglot.optimizer.canonicalize \" tests/test_optimizer.py || sed -i 's/^from sqlglot.optimizer.annotate_types import annotate_types$/from sqlglot.optimizer.annotate_types import annotate_types\\nfrom sqlglot.optimizer.canonicalize import canonicalize/' tests/test_optimizer.py && sed -n 10,16p tests/test_optimizer.py", "description": "Add canonicalize import to test module"}
[tool_result ERROR] Exit code 1
0 matches for '^from sqlglot.optimizer.canonicalize '
sed: 2: "tests/test_optimizer.py
": undefined label 'ests/test_optimizer.py'
[assistant] The `grep ||` chain broke the sed call, so I'll add the import with Edit.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-153802-optimizer-canonicalize-crashes-w/base-1/tests/test_optimizer.py", "old_string": "from sqlglot.optimizer.annotate_types import annotate_types\n", "new_string": "from sqlglot.optimizer.annotate_types import annotate_types\nfrom sqlglot.optimizer.canonicalize import canonicalize\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-153802-optimizer-canonicalize-crashes-w/base-1/tests/test_optimizer.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k canonical 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k canonical 2>&1 | tail -3 && git stash list >/dev/null; git diff --stat", "description": "Run canonicalize tests and show diff stats"}
[tool_result] .. [100%]
2 passed, 77 deselected, 100 subtests passed in 1.14s
.. [100%]
2 passed, 77 deselected, 100 subtests passed in 1.12s
sqlglot/optimizer/canonicalize.py | 2 +-
 tests/test_optimizer.py           | 7 +++++++
 2 files changed, 8 insertions(+), 1 deletion(-)
[assistant] The targeted tests pass. Now the full suite as the final gate.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4", "description": "Run full test suite", "timeout": 400000}
[tool_result] ........................................................................... [ 91%]
............................................................... [ 97%]
.............................                             [100%]
1107 passed, 18017 subtests passed in 48.75s
[assistant] `canonicalize` no longer crashes on `DATEDIFF` arguments with no inferred type. The full suite passes (1107 tests).

**The fix:** in `sqlglot/optimizer/canonicalize.py`, `_coerce_datediff_args` read `e.type.this` without checking that `e.type` was set. It now checks `e.type and ...`, so an argument with no type is skipped. That matches how `_coerce_date` and `_coerce_timeunit_arg` already handle missing types.

**Test:** I added a case to `test_canonicalize` in `tests/test_optimizer.py` (plus the import it needs). It runs `canonicalize(parse_one("SELECT DATEDIFF(a, b) FROM t"))` and expects the SQL unchanged. I reproduced the `AttributeError` before the change.

**Behaviour to be aware of:** the fix only covers arguments whose type is `None`. Arguments typed as `UNKNOWN`, which is what the optimizer's annotation pass gives untyped columns, still get cast to `DATETIME`, as they did before. I left that alone because the issue only asked for the crash fix. If you want `UNKNOWN` skipped too, that is a separate behaviour change.

I did not commit anything.
