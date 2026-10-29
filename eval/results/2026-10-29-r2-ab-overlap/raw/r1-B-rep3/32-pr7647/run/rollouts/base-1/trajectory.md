# trajectory base-1

final message:
`canonicalize` no longer crashes on `DATEDIFF` arguments with no inferred type. The call from the report now returns `SELECT DATEDIFF(a, b) FROM t` unchanged. The full suite passes (1107 tests), and ruff lint and format checks are clean.

**Cause:** `_coerce_datediff_args` in `sqlglot/optimizer/canonicalize.py` read `e.type.this` without checking that `e.type` was set.

**Fix:** The check is now `if e.type and e.type.this not in ...`. An untyped argument is skipped, not cast to `DATETIME`, which matches the "leave it alone" behaviour you asked for. The other date helpers already return early on a missing type, so this brings `DATEDIFF` in line with them.

**Test:** I added an assertion to `test_canonicalize` in `tests/test_optimizer.py` that runs the exact call from the report and checks the output is unchanged. I did not add a fixture to `canonicalize.sql`, because that path runs the full qualify and annotate pipeline and the report's case is about a bare `canonicalize` call.

I haven't committed anything. The changes are in the working tree.

## events
[tool_use Bash] {"command": "cat sqlglot/optimizer/canonicalize.py && grep -n \"def _coerce_date\\|def _replace_date\\|def coerce_date\\|coerce_date\" -r sqlglot/optimizer/ | head -30", "description": "Read canonicalize module and find date-coercion helpers"}
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
…[8706 chars elided]…
ate(expression.this, expression.unit)
sqlglot/optimizer/canonicalize.py:115:        _coerce_date(node.left, node.right, promote_to_inferred_datetime_type)
sqlglot/optimizer/canonicalize.py:117:        _coerce_date(node.this, node.args["low"], promote_to_inferred_datetime_type)
sqlglot/optimizer/canonicalize.py:125:        _coerce_datediff_args(node)
sqlglot/optimizer/canonicalize.py:174:def _coerce_date(
sqlglot/optimizer/canonicalize.py:239:def _coerce_datediff_args(node: exp.DateDiff) -> None:
[assistant] The crash is in `_coerce_datediff_args`, which reads `e.type.this` without checking whether the type is set. The sibling helpers return early on a missing type. I'll reproduce it first, then make the matching change.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0, '.')\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.canonicalize import canonicalize\nprint(canonicalize(parse_one('SELECT DATEDIFF(a, b) FROM t')).sql())\n\" 2>&1 | tail -4", "description": "Reproduce the canonicalize crash"}
[tool_result]   File "~/.cache/lithify/work/repo-6e430de19896/20261029-191702-optimizer-canonicalize-crashes-w/base-1/sqlglot/optimizer/canonicalize.py", line 241, in _coerce_datediff_args
    if e.type.this not in exp.DataType.TEMPORAL_TYPES:
       ^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'this'
[assistant] Reproduced: `DATEDIFF` args with no inferred type hit `None.this`. The fix is to skip untyped args, the same way `_coerce_timeunit_arg` and `_coerce_date` do.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-191702-optimizer-canonicalize-crashes-w/base-1/sqlglot/optimizer/canonicalize.py", "old_string": "        if e.type.this not in exp.DataType.TEMPORAL_TYPES:", "new_string": "        if e.type and e.type.this not in exp.DataType.TEMPORAL_TYPES:"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-191702-optimizer-canonicalize-crashes-w/base-1/sqlglot/optimizer/canonicalize.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0, '.')\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.canonicalize import canonicalize\nprint(canonicalize(parse_one('SELECT DATEDIFF(a, b) FROM t')).sql())\n\" 2>&1 | tail -4", "description": "Apply null-type guard and re-run repro"}
[tool_result] SELECT DATEDIFF(a, b) FROM t
[assistant] The repro now passes. Next I'll add a regression test next to the existing canonicalize fixtures and run the project's test command.
[tool_use Bash] {"command": "grep -rn \"canonicalize\" tests/*.py | head; grep -n \"DATEDIFF\\|DATE_DIFF\" tests/fixtures/optimizer/canonicalize.sql | head", "description": "Locate canonicalize tests and DATEDIFF fixtures"}
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
[tool_use Bash] {"command": "sed -n 95,110p tests/fixtures/optimizer/canonicalize.sql; grep -n \"canonicalize\" tests/test_optimizer.py | sed -n 1,3p; grep -n \"def test_canonicalize\" -A12 tests/test_optimizer.py | head -30", "description": "View canonicalize fixture tail and test harness"}
[tool_result] SELECT DATE_TRUNC('SECOND', t.d) FROM temporal AS t;
SELECT DATE_TRUNC('SECOND', CAST("t"."d" AS DATETIME)) AS "_col_0" FROM "temporal" AS "t";

DATE_TRUNC('DAY', '2023-01-01');
DATE_TRUNC('DAY', CAST('2023-01-01' AS DATE));

DATEDIFF('2023-01-01', '2023-01-02', DAY);
DATEDIFF(CAST('2023-01-01' AS DATETIME), CAST('2023-01-02' AS DATETIME), DAY);

SELECT "t"."d" > '2023-01-01' AS "d" FROM "temporal" AS "t";
SELECT "t"."d" > CAST('2023-01-01' AS DATE) AS "d" FROM "temporal" AS "t";

SELECT "t"."d"
…[734 chars elided]…
timize = partial(
1275-            optimizer.optimize,
1276-            rules=[
1277-                optimizer.qualify.qualify,
1278-                optimizer.qualify_columns.quote_identifiers,
1279-                annotate_types,
1280-                optimizer.canonicalize.canonicalize,
1281-            ],
1282-        )
1283-        self.check_file("canonicalize", optimize, schema=self.schema)
1284-
1285-        # In T-SQL and Redshift, SELECT a + b can produce a NULL, so we can't transpile it
[tool_use Bash] {"command": "sed -n 1283,1300p tests/test_optimizer.py", "description": "View test_canonicalize tail for insertion point"}
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
[assistant] I'll add a regression test to `test_canonicalize` that uses the exact call from the report, so it doesn't depend on the schema.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-191702-optimizer-canonicalize-crashes-w/base-1/tests/test_optimizer.py", "old_string": "            'SELECT CAST(\"t\".\"a\" AS TEXT) || CAST(\"t\".\"b\" AS TEXT) AS \"_col_0\" FROM \"t\" AS \"t\"',\n        )\n\n    def test_tpch(self):", "new_string": "            'SELECT CAST(\"t\".\"a\" AS TEXT) || CAST(\"t\".\"b\" AS TEXT) AS \"_col_0\" FROM \"t\" AS \"t\"',\n        )\n\n        # DATEDIFF arguments without an inferred type must be left untouched\n        self.assertEqual(\n            canonicalize(parse_one(\"SELECT DATEDIFF(a, b) FROM t\")).sql(),\n            \"SELECT DATEDIFF(a, b) FROM t\",\n        )\n\n    def test_tpch(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-191702-optimizer-canonicalize-crashes-w/base-1/tests/test_optimizer.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"^from sqlglot\\|^import\" tests/test_optimizer.py | head -20", "description": "Check imports in test_optimizer.py"}
[tool_result] 11 matches in 1 files:

tests/test_optimizer.py:1:import unittest
tests/test_optimizer.py:6:import duckdb
tests/test_optimizer.py:9:import sqlglot
tests/test_optimizer.py:10:from sqlglot import exp, optimizer, parse_one
tests/test_optimizer.py:11:from sqlglot.errors import ANSI_RESET, ANSI_UNDERLINE, OptimizeError, SchemaE...
tests/test_optimizer.py:12:from sqlglot.optimizer.annotate_types import annotate_types
tests/test_optimizer.py:13:from sqlglot.optimizer.canonicalize_internal_names import canonicalize_intern...
tests/test_optimizer.py:14:from sqlglot.optimizer.normalize import normalization_distance
tests/test_optimizer.py:15:from sqlglot.optimizer.qualify import qualify
tests/test_optimizer.py:16:from sqlglot.optimizer.scope import build_scope, traverse_scope, walk_in_scope
tests/test_optimizer.py:17:from sqlglot.schema import MappingSchema
[assistant] The test file doesn't import `canonicalize`, but the existing test already reaches it via `optimizer.canonicalize.canonicalize`, so I'll use that instead of adding an import.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-191702-optimizer-canonicalize-crashes-w/base-1/tests/test_optimizer.py", "old_string": "            canonicalize(parse_one(\"SELECT DATEDIFF(a, b) FROM t\")).sql(),", "new_string": "            optimizer.canonicalize.canonicalize(parse_one(\"SELECT DATEDIFF(a, b) FROM t\")).sql(),"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-191702-optimizer-canonicalize-crashes-w/base-1/tests/test_optimizer.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py 2>&1 | tail -15", "description": "Run optimizer tests with project interpreter"}
[tool_result] ....................... [ 29%]
............. [ 45%]
...........................................                                                                [100%]
79 passed, 3818 subtests passed in 12.84s
[assistant] The optimizer tests pass. Now the full suite, using the project's check command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; git status --short; git diff --stat", "description": "Run full test suite and show diff stats"}
[tool_result] .......................... [ 32%]
.......................................... [ 36%]
....................................................................................... [ 43%]
.................................................. [ 48%]
............. [ 49%]
.......... [ 50%]
....... [ 51%]
........................... [ 53%]
..................................................................................................................................................................... [ 68%]
.
…[158 chars elided]…
.............................. [ 84%]
........................................................................... [ 91%]
............................................................... [ 97%]
.............................                             [100%]
1107 passed, 18017 subtests passed in 47.25s
 M sqlglot/optimizer/canonicalize.py
 M tests/test_optimizer.pysqlglot/optimizer/canonicalize.py | 2 +-
 tests/test_optimizer.py           | 6 ++++++
 2 files changed, 7 insertions(+), 1 deletion(-)
[assistant] The full suite passes (1107 tests). My new test line is long, so I'll check it against the project's lint config.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/optimizer/canonicalize.py tests/test_optimizer.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/optimizer/canonicalize.py tests/test_optimizer.py) 2>&1 | tail -8", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
2 files already formatted
[assistant] `canonicalize` no longer crashes on `DATEDIFF` arguments with no inferred type. The call from the report now returns `SELECT DATEDIFF(a, b) FROM t` unchanged. The full suite passes (1107 tests), and ruff lint and format checks are clean.

**Cause:** `_coerce_datediff_args` in `sqlglot/optimizer/canonicalize.py` read `e.type.this` without checking that `e.type` was set.

**Fix:** The check is now `if e.type and e.type.this not in ...`. An untyped argument is skipped, not cast to `DATETIME`, which matches the "leave it alone" behaviour you asked for. The other date helpers already return early on a missing type, so this brings `DATEDIFF` in line with them.

**Test:** I added an assertion to `test_canonicalize` in `tests/test_optimizer.py` that runs the exact call from the report and checks the output is unchanged. I did not add a fixture to `canonicalize.sql`, because that path runs the full qualify and annotate pipeline and the report's case is about a bare `canonicalize` call.

I haven't committed anything. The changes are in the working tree.
