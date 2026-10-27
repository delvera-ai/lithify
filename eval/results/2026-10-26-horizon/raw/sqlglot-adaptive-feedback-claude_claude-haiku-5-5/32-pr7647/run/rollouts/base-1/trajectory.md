# trajectory base-1

final message:
`canonicalize` no longer crashes on a `DATEDIFF` argument with no inferred type. `SELECT DATEDIFF(a, b) FROM t` now comes back unchanged.

The full suite passed after my last edit: `SUMMARY: 1107 passed, 18017 subtests passed in 56.60s`, `EXIT: 0`. Ruff lint and format checks are clean on both changed files.

**The change**

- `sqlglot/optimizer/canonicalize.py`: in `_coerce_datediff_args`, the loop now checks `if e.type and ...` before reading `e.type.this`. This matches how `_coerce_date` and `_coerce_timeunit_arg` already skip untyped arguments.
- Typed arguments are coerced exactly as before. For example, `DATEDIFF(CAST(a AS DATE), b)` still turns `b` into `CAST(b AS DATETIME)`.
- `tests/test_optimizer.py`: a regression assertion added at the end of `test_canonicalize` that checks the untyped `DATEDIFF(a, b)` case is left alone. I did not add it to the `canonicalize.sql` fixture because that fixture runs with a schema, which makes an untyped argument hard to produce.

## events
[tool_use Bash] {"command": "cat sqlglot/optimizer/canonicalize.py && grep -n \"def _coerce_date\\|def coerce_date\\|_coerce_date\" -r sqlglot | head -30 && ls .lithify/harness 2>/dev/null; cat .lithify/harness/memory.md 2>/dev/null | head -30", "description": "Read canonicalize module and find date coercion helpers"}
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
…[9455 chars elided]…
on -m pytest -q -p no:cacheprovider --color=no`.
- Layout: expression classes live in `sqlglot/expressions/*.py` (there is no `expressions.py`). A dialect's parser is `sqlglot/parsers/<d>.py` and its generator is `sqlglot/generators/<d>.py`; `sqlglot/dialects/<d>.py` only wires them together.
- The full suite (~1100 tests) takes 60–80 s alone; `tests/test_executor.py::TestExecutor::test_execute_tpcds`
  is slowest and looks hung under CPU contention. Run the dialect's own test file first (<1 s).
[assistant] The crash is in `_coerce_datediff_args`, which reads `e.type.this` without checking for a missing type. The other helpers in this file check `if not type` first. I'll reproduce it before editing.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.canonicalize import canonicalize\nprint(canonicalize(parse_one('SELECT DATEDIFF(a, b) FROM t')).sql())\n\" 2>&1 | tail -5", "description": "Reproduce the canonicalize DATEDIFF crash"}
[tool_result]     _coerce_datediff_args(node)
  File "~/.cache/lithify/work/repo-55c905b0df68/20261027-091521-optimizer-canonicalize-crashes-w/base-1/sqlglot/optimizer/canonicalize.py", line 241, in _coerce_datediff_args
    if e.type.this not in exp.DataType.TEMPORAL_TYPES:
       ^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'this'
[assistant] Reproduced. I'll make the helper skip arguments with no inferred type, the same way `_coerce_date` and `_coerce_timeunit_arg` do.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-091521-optimizer-canonicalize-crashes-w/base-1/sqlglot/optimizer/canonicalize.py", "old_string": "    for e in (node.this, node.expression):\n        if e.type.this not in exp.DataType.TEMPORAL_TYPES:", "new_string": "    for e in (node.this, node.expression):\n        if e.type and e.type.this not in exp.DataType.TEMPORAL_TYPES:"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-091521-optimizer-canonicalize-crashes-w/base-1/sqlglot/optimizer/canonicalize.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.canonicalize import canonicalize\nfrom sqlglot.optimizer.annotate_types import annotate_types\nfor q in ['SELECT DATEDIFF(a, b) FROM t', 'SELECT DATEDIFF
…[43 chars elided]…
IFF(a, CAST(b AS DATE)) FROM t']:\n    print(canonicalize(parse_one(q)).sql())\nprint(canonicalize(annotate_types(parse_one('SELECT DATEDIFF(CAST(a AS DATE), b) FROM t'))).sql())\n\" 2>&1 | tail -8; grep -n \"DATEDIFF\\|DateDiff\" tests/test_optimizer.py tests/fixtures/optimizer/canonicalize.sql 2>/dev/null | head -20", "description": "Verify fix and look for existing canonicalize datediff tests"}
[tool_result] SELECT DATEDIFF(a, b) FROM t
SELECT DATEDIFF(CAST(a AS DATE), b) FROM t
SELECT DATEDIFF(a, CAST(b AS DATE)) FROM t
SELECT DATEDIFF(CAST(a AS DATE), CAST(b AS DATETIME)) FROM t
tests/fixtures/optimizer/canonicalize.sql:101:DATEDIFF('2023-01-01', '2023-01-02', DAY);
tests/fixtures/optimizer/canonicalize.sql:102:DATEDIFF(CAST('2023-01-01' AS DATETIME), CAST('2023-01-02' AS DATETIME), DAY);
tests/test_optimizer.py:1664:                "SELECT DATEDIFF('2023-01-01', '2023-01-02', DAY) FROM x AS x",
[assistant] The crash is gone, and typed arguments still get coerced as before. Next I'll add a regression test, so I'll check how the canonicalize fixtures are structured.
[tool_use Bash] {"command": "sed -n 95,110p tests/fixtures/optimizer/canonicalize.sql; grep -n \"canonicalize\" tests/test_optimizer.py | head; sed -n 1655,1675p tests/test_optimizer.py", "description": "Inspect canonicalize fixtures and test harness"}
[tool_result] SELECT DATE_TRUNC('SECOND', t.d) FROM temporal AS t;
SELECT DATE_TRUNC('SECOND', CAST("t"."d" AS DATETIME)) AS "_col_0" FROM "temporal" AS "t";

DATE_TRUNC('DAY', '2023-01-01');
DATE_TRUNC('DAY', CAST('2023-01-01' AS DATE));

DATEDIFF('2023-01-01', '2023-01-02', DAY);
DATEDIFF(CAST('2023-01-01' AS DATETIME), CAST('2023-01-02' AS DATETIME), DAY);

SELECT "t"."d" > '2023-01-01' AS "d" FROM "temporal" AS "t";
SELECT "t"."d" > CAST('2023-01-01' AS DATE) AS "d" FROM "temporal" AS "t";

SELECT "t"."d"
…[1291 chars elided]…
) FROM x AS x",
                exp.DataType.Type.INT,
            ),
        ]:
            with self.subTest(sql):
                expression = annotate_types(parse_one(sql), schema=schema)
                self.assertEqual(expected_type, expression.expressions[0].type.this)
                self.assertEqual(sql, expression.sql())

    def test_lateral_annotation(self):
        expression = optimizer.optimize(
            parse_one("SELECT c FROM (select 1 a) as x LATERAL VIEW EXPLODE (a) AS c")
[tool_use Bash] {"command": "grep -rn \"canonicalize.sql\\|def test_canonicalize\" tests/*.py | head; grep -n -A12 \"def test_canonicalize(self\" tests/test_optimizer.py", "description": "Find where canonicalize fixture is tested"}
[tool_result] tests/test_optimizer.py:1034:    def test_canonicalize_internal_names(self):
tests/test_optimizer.py:1273:    def test_canonicalize(self):
1273:    def test_canonicalize(self):
1274-        optimize = partial(
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
[assistant] The fixture runs through `qualify` and `annotate_types` with a schema, so an untyped argument is awkward to build there. I'll add a small direct test next to `test_canonicalize`. First I'll find where that method ends.
[tool_use Bash] {"command": "sed -n 1284,1310p tests/test_optimizer.py", "description": "Read end of test_canonicalize to place new test"}
[tool_result]         # In T-SQL and Redshift, SELECT a + b can produce a NULL, so we can't transpile it
        # into a CONCAT in Postgres, because that coalesces NULL values with empty strings
        ast = optimize("SELECT CAST(a AS TEXT) + CAST(b AS TEXT) FROM t", dialect="tsql")
        self.assertEqual(
            ast.sql("postgres"),
            'SELECT CAST("t"."a" AS TEXT) || CAST("t"."b" AS TEXT) AS "_col_0" FROM "t" AS "t"',
        )

    def test_tpch(self):
        self.check_file("tpc-h/tpc-h
…[153 chars elided]…
CDS_SCHEMA, pretty=True)

    def test_file_schema(self):
        self.assertEqual(
            optimizer.optimize(
                "SELECT * FROM foo",
                on_qualify=lambda table: table.replace(exp.to_table("bar")),
            ).sql(),
            'SELECT * FROM "bar"',
        )

    def test_scope(self):
        ast = parse_one("SELECT IF(a IN UNNEST(b), 1, 0) AS c FROM t", dialect="bigquery")
        self.assertEqual(build_scope(ast).columns, [exp.column("a"), exp.column("b")])
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-091521-optimizer-canonicalize-crashes-w/base-1/tests/test_optimizer.py", "old_string": "            'SELECT CAST(\"t\".\"a\" AS TEXT) || CAST(\"t\".\"b\" AS TEXT) AS \"_col_0\" FROM \"t\" AS \"t\"',\n        )\n\n    def test_tpch(self):", "new_string": "            'SELECT CAST(\"t\".\"a\" AS TEXT) || CAST(\"t\".\"b\" AS TEXT) AS \"_col_0\" FROM \"t\" AS \"t\"',\n        )\n\n        # DATEDIFF arguments without an inferred type are left alone\n        self.assertEqual(\n            canonicalize(parse_one(\"SELECT DATEDIFF(a, b) FROM t\")).sql(),\n            \"SELECT DATEDIFF(a, b) FROM t\",\n        )\n\n    def test_tpch(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-091521-optimizer-canonicalize-crashes-w/base-1/tests/test_optimizer.py has been updated successfully.
[assistant] The test file doesn't import `canonicalize` directly, so I'll call it through the module reference the surrounding test already uses.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-091521-optimizer-canonicalize-crashes-w/base-1/tests/test_optimizer.py", "old_string": "            canonicalize(parse_one(\"SELECT DATEDIFF(a, b) FROM t\")).sql(),", "new_string": "            optimizer.canonicalize.canonicalize(parse_one(\"SELECT DATEDIFF(a, b) FROM t\")).sql(),"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-091521-optimizer-canonicalize-crashes-w/base-1/tests/test_optimizer.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k \"canonicalize\" 2>&1 | tail -5; git stash list >/dev/null; $PY .lithify/harness/scripts/run_suite.py tests/test_optimizer.py 2>&1 | tail -8", "description": "Run canonicalize tests and optimizer test file", "timeout": 600000}
[tool_result] .. [100%]
2 passed, 77 deselected, 100 subtests passed in 1.30s
WARNING: 2 other pytest process(es) running; expect slower runs:
  18165       00:14 <work>/env-sqlglot/b
  34207 03-13:44:40 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no tests/test_optimizer.py
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-fd61dae823.log
ELAPSED: 15s
SUMMARY: 79 passed, 3818 subtests passed in 14.51s
EXIT: 0
[assistant] The optimizer file passes. The harness requires a full-suite run after the last edit, so I'll run that now.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py 2>&1 | tail -15", "description": "Run full test suite in foreground", "timeout": 600000}
[tool_result] WARNING: 2 other pytest process(es) running; expect slower runs:
  18165       00:32 <work>/env-sqlglot/b
  34207 03-13:44:58 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-fd61dae823.log
ELAPSED: 57s
SUMMARY: 1107 passed, 18017 subtests passed in 56.60s
EXIT: 0
[assistant] The full suite passes. I'll finish with a lint and format check on the two changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff check sqlglot/optimizer/canonicalize.py tests/test_optimizer.py 2>&1 | tail -3; $PY -m ruff format --check sqlglot/optimizer/canonicalize.py tests/test_optimizer.py 2>&1 | tail -3; git diff --stat", "description": "Lint, format-check, and show diff stat"}
[tool_result] All checks passed!
2 files already formatted
 sqlglot/optimizer/canonicalize.py | 2 +-
 tests/test_optimizer.py           | 6 ++++++
 2 files changed, 7 insertions(+), 1 deletion(-)
[assistant] `canonicalize` no longer crashes on a `DATEDIFF` argument with no inferred type. `SELECT DATEDIFF(a, b) FROM t` now comes back unchanged.

The full suite passed after my last edit: `SUMMARY: 1107 passed, 18017 subtests passed in 56.60s`, `EXIT: 0`. Ruff lint and format checks are clean on both changed files.

**The change**

- `sqlglot/optimizer/canonicalize.py`: in `_coerce_datediff_args`, the loop now checks `if e.type and ...` before reading `e.type.this`. This matches how `_coerce_date` and `_coerce_timeunit_arg` already skip untyped arguments.
- Typed arguments are coerced exactly as before. For example, `DATEDIFF(CAST(a AS DATE), b)` still turns `b` into `CAST(b AS DATETIME)`.
- `tests/test_optimizer.py`: a regression assertion added at the end of `test_canonicalize` that checks the untyped `DATEDIFF(a, b)` case is left alone. I did not add it to the `canonicalize.sql` fixture because that fixture runs with a schema, which makes an untyped argument hard to produce.
