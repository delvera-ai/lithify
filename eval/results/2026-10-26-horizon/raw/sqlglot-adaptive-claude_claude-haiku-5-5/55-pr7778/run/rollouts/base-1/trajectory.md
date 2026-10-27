# trajectory base-1

final message:
`FROM_ISO8601_DATE` now transpiles to `CAST(... AS DATE)` for non-Presto/Trino dialects, and still round-trips in Trino and Presto. The full suite passes (1122 tests), and ruff check and format are clean.

Changes, following the same pattern as the existing `FROM_ISO8601_TIMESTAMP` support:

- **`sqlglot/expressions/temporal.py`**: new `FromISO8601Date` node mapped to `FROM_ISO8601_DATE`.
- **`sqlglot/generator.py`**: base `fromiso8601date_sql` emits `CAST(x AS DATE)`, so every dialect that doesn't override it gets the cast.
- **`sqlglot/generators/presto.py`**: `FromISO8601Date` maps to `rename_func("FROM_ISO8601_DATE")`. Trino inherits this, so it keeps the native function.
- **`tests/dialects/test_presto.py`**: new `validate_all` case covering Trino, Presto, DuckDB, Snowflake, Spark, Databricks and BigQuery.

Output after the change:
```
trino      SELECT FROM_ISO8601_DATE('2020-05-11')
snowflake  SELECT CAST('2020-05-11' AS DATE)
duckdb     SELECT CAST('2020-05-11' AS DATE)
spark      SELECT CAST('2020-05-11' AS DATE)
bigquery   SELECT CAST('2020-05-11' AS DATE)
```

I haven't committed anything.

## events
[tool_use Skill] {"skill": "sqlglot-syntax-support"}
[tool_result] Launching skill: sqlglot-syntax-support
[user] Base directory for this skill: ~/.cache/lithify/work/repo-161bf5b46800/20261027-102406-trino-other-dialects-from-iso860/base-1/.claude/skills/sqlglot-syntax-support

# Adding or fixing syntax support in sqlglot

## Contract: a syntax change touches three places that must agree
1. **Node** — the `exp.<Node>` class in `sqlglot/expressions/*.py`. New information goes in
   `arg_types` (optional args `False`). Prefer reusing an existing wrapper node over adding a flag.
2. **Parser** — a `_parse_*` method in `sqlglot/parser.py` (base) or `sqlglot/parsers/<dialect>.py`.
   Build nodes w
…[2311 chars elided]…
r is dialect-controlled: `Dialect.ON_CONDITION_EMPTY_BEFORE_ERROR`
  (Oracle sets `False`); use `_parse_on_handling` / `_parse_on_condition`, not ad-hoc matching.

## When the quoted example already works
If the literal example in the task already parses and round-trips, the requested feature is not
"done": find the form of the same construct and clause that still fails (the "incomplete" notes
above are the known gaps) and implement it, with a `validate_identity` test next to the existing ones. A no-change
deliverable must be justified by evidence that every form of the named construct works.

[tool_use Bash] {"command": "grep -rn -i \"iso8601\" sqlglot/ | head -50", "description": "Search for ISO8601 handling in sqlglot source"}
[tool_result] sqlglot/generator.py:3994:    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:
sqlglot/expressions/temporal.py:436:class FromISO8601Timestamp(Expression, Func):
sqlglot/expressions/temporal.py:437:    _sql_names = ["FROM_ISO8601_TIMESTAMP"]
sqlglot/generators/presto.py:307:        exp.FromISO8601Timestamp: rename_func("FROM_ISO8601_TIMESTAMP"),
[assistant] The skill's guidance applies here: the parse/generate pieces for this function need to agree. The closest existing precedent is `FROM_ISO8601_TIMESTAMP`, so I'll read how it is wired up.
[tool_use Bash] {"command": "sed -n 425,450p sqlglot/expressions/temporal.py && echo ---GEN && sed -n 3985,4005p sqlglot/generator.py && echo ---PRESTO && sed -n 300,312p sqlglot/generators/presto.py && echo ---SNOW && git show 7db4d2515 --stat && git show 7db4d2515 -- sqlglot/ | head -120 && echo ---TESTS && grep -rn -i \"iso8601\" tests/ | head -30", "description": "Inspect existing ISO8601 implementation and tests"}
[tool_result]     pass


class DateToDi(Expression, Func):
    pass


class DiToDate(Expression, Func):
    pass


class FromISO8601Timestamp(Expression, Func):
    _sql_names = ["FROM_ISO8601_TIMESTAMP"]


class ParseDatetime(Expression, Func):
    arg_types = {"this": True, "format": False, "zone": False, "default_year": False}


class ParseTime(Expression, Func):
    arg_types = {"this": True, "format": True}


class StrToDate(Expression, Func):
    arg_types = {"this": True, "format": False, "safe": False
…[4769 chars elided]…
ESTAMP"),
         exp.FromTimeZone: lambda self, e: (
             f"WITH_TIMEZONE({self.sql(e, 'this')}, {self.sql(e, 'zone')}) AT TIME ZONE 'UTC'"
         ),
---TESTS
tests/dialects/test_presto.py:37:            "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
tests/dialects/test_presto.py:40:                "presto": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
tests/dialects/test_presto.py:41:                "trino": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
[assistant] The `FROM_ISO8601_TIMESTAMP` commit is the exact pattern to copy. Before editing, I'll confirm there's no existing `FROM_ISO8601_DATE` node and check how Trino inherits from Presto.
[tool_use Bash] {"command": "grep -rn \"ISO8601_DATE\\|FromISO8601Date\" sqlglot tests | head; echo ---; grep -n \"class\\|import\" sqlglot/generators/trino.py | head -20; grep -n \"class.*Generator\\|import\" sqlglot/dialects/trino.py | head; echo ---; sed -n 30,50p tests/dialects/test_presto.py; echo ---; grep -n \"DATE(\\|\\\"date\\\"\\|DType.DATE\\b\" sqlglot/generator.py | head -5; cat -A /dev/null; grep -n \"def cast\" sqlglot/expressions/*.py | head -3", "description": "Check for existing ISO8601 date node and Trino inheritance"}
[tool_result] ---
1:from __future__ import annotations
3:from sqlglot import exp, transforms
4:from sqlglot.dialects.dialect import (
11:from sqlglot.generators.presto import PrestoGenerator, amend_exploded_column_table
14:class TrinoGenerator(PrestoGenerator):
1:from __future__ import annotations
3:from sqlglot.dialects.presto import Presto
4:from sqlglot.generators.trino import TrinoGenerator
5:from sqlglot.parsers.trino import TrinoParser
6:from sqlglot.tokens import TokenType
---
            },
          
…[882 chars elided]…
L YEAR TO MONTH)",
            write={
---
4086:        return f"CURRENT_DATE({zone})" if zone else "CURRENT_DATE"
5112:                    exp.DType.DATE,
5116:        if isinstance(this, exp.TsOrDsToDate) or this.is_type(exp.DType.DATE):
5120:            return self.sql(exp.TryCast(this=this, to=exp.DataType(this=exp.DType.DATE)))
5122:        return self.sql(exp.cast(this, exp.DType.DATE))
cat: illegal option -- A
usage: cat [-belnstuv] [file ...]
sqlglot/expressions/builders.py:457:def cast(
[assistant] No existing node, and Trino inherits Presto's transforms. The change is three small edits mirroring the timestamp commit: a node, a base-generator cast, and a Presto/Trino passthrough.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-102406-trino-other-dialects-from-iso860/base-1/sqlglot/expressions/temporal.py", "old_string": "class FromISO8601Timestamp(Expression, Func):\n    _sql_names = [\"FROM_ISO8601_TIMESTAMP\"]\n", "new_string": "class FromISO8601Date(Expression, Func):\n    _sql_names = [\"FROM_ISO8601_DATE\"]\n\n\nclass FromISO8601Timestamp(Expression, Func):\n    _sql_names = [\"FROM_ISO8601_TIMESTAMP\"]\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-102406-trino-other-dialects-from-iso860/base-1/sqlglot/expressions/temporal.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-102406-trino-other-dialects-from-iso860/base-1/sqlglot/generator.py", "old_string": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))\n", "new_string": "    def fromiso8601date_sql(self, expression: exp.FromISO8601Date) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.DATE))\n\n    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-102406-trino-other-dialects-from-iso860/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-102406-trino-other-dialects-from-iso860/base-1/sqlglot/generators/presto.py", "old_string": "        exp.FromISO8601Timestamp: rename_func(\"FROM_ISO8601_TIMESTAMP\"),", "new_string": "        exp.FromISO8601Date: rename_func(\"FROM_ISO8601_DATE\"),\n        exp.FromISO8601Timestamp: rename_func(\"FROM_ISO8601_TIMESTAMP\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-102406-trino-other-dialects-from-iso860/base-1/sqlglot/generators/presto.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-102406-trino-other-dialects-from-iso860/base-1/tests/dialects/test_presto.py", "old_string": "        self.validate_all(\n            \"CAST(x AS INTERVAL YEAR TO MONTH)\",", "new_string": "        self.validate_all(\n            \"SELECT FROM_ISO8601_DATE('2020-05-11')\",\n            write={\n     
…[195 chars elided]…
-05-11')\",\n                \"snowflake\": \"SELECT CAST('2020-05-11' AS DATE)\",\n                \"spark\": \"SELECT CAST('2020-05-11' AS DATE)\",\n                \"databricks\": \"SELECT CAST('2020-05-11' AS DATE)\",\n                \"bigquery\": \"SELECT CAST('2020-05-11' AS DATE)\",\n            },\n        )\n        self.validate_all(\n            \"CAST(x AS INTERVAL YEAR TO MONTH)\","}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-102406-trino-other-dialects-from-iso860/base-1/tests/dialects/test_presto.py has been updated successfully.
[assistant] Edits are in. Now I'll run the reproduction from the report and the dialect tests, using the project's Python per the harness notes.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; [ -x $PY ] || PY=python3; $PY -c \"\nimport sqlglot\np = sqlglot.parse_one(\\\"SELECT FROM_ISO8601_DATE('2020-05-11')\\\", 'trino')\nfor d in ['trino','presto','snowflake','duckdb','spark','bigquery']:\n    print(d, p.sql(d))\n\" && $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_presto.py tests/dialects/test_trino.py tests/dialects/test_snowflake.py tests/dialects/test_duckdb.py 2>&1 | tail -15", "description": "Run repro script and dialect tests"}
[tool_result] trino SELECT FROM_ISO8601_DATE('2020-05-11')
presto SELECT FROM_ISO8601_DATE('2020-05-11')
snowflake SELECT CAST('2020-05-11' AS DATE)
duckdb SELECT CAST('2020-05-11' AS DATE)
spark SELECT CAST('2020-05-11' AS DATE)
bigquery SELECT CAST('2020-05-11' AS DATE)
.................................. [ 20%]
........................... [ 36%]
............................... [ 55%]
...........................................................................                  [100%]
167 passed, 2696 subtests passed in 0.78s
[assistant] Repro now behaves as requested and the focused tests pass. Next I'll run the full suite to catch regressions.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; [ -x $PY ] || PY=python3; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; ruff check sqlglot tests/dialects/test_presto.py 2>&1 | tail -2; ruff format --check sqlglot tests/dialects/test_presto.py 2>&1 | tail -2", "description": "Run full test suite and lint checks"}
[tool_result] ............... [ 82%]
.................................................................. [ 88%]
.......... [ 89%]
..........................................................................................................................                                                        [100%]
1122 passed, 18191 subtests passed in 52.41s
All checks passed!
177 files already formatted
[assistant] `FROM_ISO8601_DATE` now transpiles to `CAST(... AS DATE)` for non-Presto/Trino dialects, and still round-trips in Trino and Presto. The full suite passes (1122 tests), and ruff check and format are clean.

Changes, following the same pattern as the existing `FROM_ISO8601_TIMESTAMP` support:

- **`sqlglot/expressions/temporal.py`**: new `FromISO8601Date` node mapped to `FROM_ISO8601_DATE`.
- **`sqlglot/generator.py`**: base `fromiso8601date_sql` emits `CAST(x AS DATE)`, so every dialect that doesn't override it gets the cast.
- **`sqlglot/generators/presto.py`**: `FromISO8601Date` maps to `rename_func("FROM_ISO8601_DATE")`. Trino inherits this, so it keeps the native function.
- **`tests/dialects/test_presto.py`**: new `validate_all` case covering Trino, Presto, DuckDB, Snowflake, Spark, Databricks and BigQuery.

Output after the change:
```
trino      SELECT FROM_ISO8601_DATE('2020-05-11')
snowflake  SELECT CAST('2020-05-11' AS DATE)
duckdb     SELECT CAST('2020-05-11' AS DATE)
spark      SELECT CAST('2020-05-11' AS DATE)
bigquery   SELECT CAST('2020-05-11' AS DATE)
```

I haven't committed anything.
