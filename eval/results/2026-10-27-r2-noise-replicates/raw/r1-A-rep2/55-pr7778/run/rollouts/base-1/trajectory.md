# trajectory base-1

final message:
`FROM_ISO8601_DATE` now transpiles to a cast to `DATE` for non-Presto/Trino dialects, and stays as `FROM_ISO8601_DATE(...)` for Presto and Trino. The full suite passes (1122 tests) and ruff is clean. I haven't committed.

Your example now produces:

```
trino      SELECT FROM_ISO8601_DATE('2020-05-11')
snowflake  SELECT CAST('2020-05-11' AS DATE)
duckdb     SELECT CAST('2020-05-11' AS DATE)
spark      SELECT CAST('2020-05-11' AS DATE)
bigquery   SELECT CAST('2020-05-11' AS DATE)
```

I followed the same pattern as the recent `FROM_ISO8601_TIMESTAMP` fix:

- **`sqlglot/expressions/temporal.py`**: new `FromISO8601Date` expression mapped to `FROM_ISO8601_DATE`.
- **`sqlglot/generator.py`**: base `fromiso8601date_sql` emits `CAST(... AS DATE)`, so every dialect gets the cast by default.
- **`sqlglot/generators/presto.py`**: keeps the native function name for Presto and Trino.
- **`tests/dialects/test_presto.py`**: a `validate_all` case covering the Presto/Trino round-trip and the cast output for the other dialects.

## events
[tool_use Bash] {"command": "grep -rn \"ISO8601\\|iso8601\" sqlglot/ tests/ | grep -v \"\\.pyc\" | head -50; git show 7db4d2515 --stat | head -20", "description": "Search ISO8601 handling across sqlglot and show last commit"}
[tool_result] sqlglot/generator.py:3994:    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:
sqlglot/expressions/temporal.py:436:class FromISO8601Timestamp(Expression, Func):
sqlglot/expressions/temporal.py:437:    _sql_names = ["FROM_ISO8601_TIMESTAMP"]
sqlglot/generators/presto.py:307:        exp.FromISO8601Timestamp: rename_func("FROM_ISO8601_TIMESTAMP"),
tests/dialects/test_presto.py:37:            "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
tests/dialects/test_
…[492 chars elided]…
   timestamp with timezone. Move DuckDB's cast-to-TIMESTAMPTZ logic into
    the base Generator so it transpiles correctly for all dialects (e.g.
    Snowflake, Spark), and keep the native function for Presto/Trino.
    
    Co-authored-by: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

 sqlglot/generator.py          | 3 +++
 sqlglot/generators/duckdb.py  | 3 ---
 sqlglot/generators/presto.py  | 1 +
 tests/dialects/test_presto.py | 5 +++++
 4 files changed, 9 insertions(+), 3 deletions(-)
[tool_use Bash] {"command": "sed -n 3990,4000p sqlglot/generator.py; sed -n 425,445p sqlglot/expressions/temporal.py; grep -rn \"FromISO8601\\|ISO8601_DATE\\|class Date(\" sqlglot/expressions/*.py | head; grep -n \"ISO8601\\|iso8601\" sqlglot/dialects/*.py sqlglot/generators/*.py | head; sed -n 30,50p tests/dialects/test_presto.py; grep -n \"ISO8601\" tests/dialects/test_trino.py", "description": "Inspect relevant generator, expression, and test code"}
[tool_result]         this = self.sql(expression, "this")
        zone = self.sql(expression, "zone")
        return f"{this} AT TIME ZONE {zone} AT TIME ZONE 'UTC'"

    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:
        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))

    def add_sql(self, expression: exp.Add) -> str:
        return self.binary(expression, "+")

    def and_sql(self, expression: exp.And, stack: list[str | exp.Expr] | None = None) -> st
…[1104 chars elided]…
ino": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
                "snowflake": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)",
                "spark": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMP)",
                "databricks": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMP)",
                "bigquery": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMP)",
            },
        )
        self.validate_all(
            "CAST(x AS INTERVAL YEAR TO MONTH)",
            write={
[assistant] The existing `FROM_ISO8601_TIMESTAMP` handling is the pattern to follow. I'll add a matching `FromISO8601Date` expression, a base generator cast to `DATE`, and keep the native name for Presto/Trino.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-103942-trino-other-dialects-from-iso860/base-1/sqlglot/expressions/temporal.py", "old_string": "class FromISO8601Timestamp(Expression, Func):\n    _sql_names = [\"FROM_ISO8601_TIMESTAMP\"]\n", "new_string": "class FromISO8601Timestamp(Expression, Func):\n    _sql_names = [\"FROM_ISO8601_TIMESTAMP\"]\n\n\nclass FromISO8601Date(Expression, Func):\n    _sql_names = [\"FROM_ISO8601_DATE\"]\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-103942-trino-other-dialects-from-iso860/base-1/sqlglot/expressions/temporal.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-103942-trino-other-dialects-from-iso860/base-1/sqlglot/generator.py", "old_string": "        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))\n\n    def add_sql", "new_string": "        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))\n\n    def fromiso8601date_sql(self, expression: exp.FromISO8601Date) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.DATE))\n\n    def add_sql"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-103942-trino-other-dialects-from-iso860/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-103942-trino-other-dialects-from-iso860/base-1/sqlglot/generators/presto.py", "old_string": "        exp.FromISO8601Timestamp: rename_func(\"FROM_ISO8601_TIMESTAMP\"),", "new_string": "        exp.FromISO8601Timestamp: rename_func(\"FROM_ISO8601_TIMESTAMP\"),\n        exp.FromISO8601Date: rename_func(\"FROM_ISO8601_DATE\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-103942-trino-other-dialects-from-iso860/base-1/sqlglot/generators/presto.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-103942-trino-other-dialects-from-iso860/base-1/tests/dialects/test_presto.py", "offset": 34, "limit": 12}
[tool_result] 34	            },
35	        )
36	        self.validate_all(
37	            "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
38	            write={
39	                "duckdb": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)",
40	                "presto": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
41	                "trino": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
42	                "snowflake": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)",
43	                "spark": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMP)",
44	                "databricks": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMP)",
45	                "bigquery": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMP)",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-103942-trino-other-dialects-from-iso860/base-1/tests/dialects/test_presto.py", "old_string": "                \"bigquery\": \"SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMP)\",\n            },\n        )\n        self.validate_all(\n            \"CAST(x AS INTERVAL YEAR TO MONTH)\",", "new_string": "
…[417 chars elided]…
-05-11')\",\n                \"snowflake\": \"SELECT CAST('2020-05-11' AS DATE)\",\n                \"spark\": \"SELECT CAST('2020-05-11' AS DATE)\",\n                \"databricks\": \"SELECT CAST('2020-05-11' AS DATE)\",\n                \"bigquery\": \"SELECT CAST('2020-05-11' AS DATE)\",\n            },\n        )\n        self.validate_all(\n            \"CAST(x AS INTERVAL YEAR TO MONTH)\","}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-103942-trino-other-dialects-from-iso860/base-1/tests/dialects/test_presto.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_presto.py tests/dialects/test_trino.py 2>&1 | tail -15; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\np = sqlglot.parse_one(\\\"SELECT FROM_ISO8601_DATE('2020-05-11')\\\", 'trino')\nprint(type(p.selects[0]).__name__)\nfor d in ['trino','snowflake','duckdb','spark','bigquery']: print(d, p.sql(d))\"", "description": "Run Presto/Trino tests and verify transpilation output"}
[tool_result] ...........................                         [100%]
27 passed, 525 subtests passed in 0.35s
FromISO8601Date
trino SELECT FROM_ISO8601_DATE('2020-05-11')
snowflake SELECT CAST('2020-05-11' AS DATE)
duckdb SELECT CAST('2020-05-11' AS DATE)
spark SELECT CAST('2020-05-11' AS DATE)
bigquery SELECT CAST('2020-05-11' AS DATE)
[assistant] Targeted tests pass and the output matches the request. Now the project's full check suite.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full project test suite"}
[tool_result] .................................................................... [ 19%]
..................... [ 21%]
.............. [ 22%]
................................................................. [ 28%]
................................................................................ [ 35%]
...................................................... [ 40%]
......................................................................................................................................................
…[184 chars elided]…
............................. [ 71%]
........................................................... [ 77%]
............................................ [ 81%]
............... [ 82%]
.................................................................. [ 88%]
.......... [ 89%]
..........................................................................................................................                                                        [100%]
1122 passed, 18191 subtests passed in 49.79s
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/expressions/temporal.py sqlglot/generator.py sqlglot/generators/presto.py tests/dialects/test_presto.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot tests/dialects/test_presto.py) 2>&1 | tail -5; git status --short", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
177 files already formatted
 M sqlglot/expressions/temporal.py
 M sqlglot/generator.py
 M sqlglot/generators/presto.py
 M tests/dialects/test_presto.py
[assistant] `FROM_ISO8601_DATE` now transpiles to a cast to `DATE` for non-Presto/Trino dialects, and stays as `FROM_ISO8601_DATE(...)` for Presto and Trino. The full suite passes (1122 tests) and ruff is clean. I haven't committed.

Your example now produces:

```
trino      SELECT FROM_ISO8601_DATE('2020-05-11')
snowflake  SELECT CAST('2020-05-11' AS DATE)
duckdb     SELECT CAST('2020-05-11' AS DATE)
spark      SELECT CAST('2020-05-11' AS DATE)
bigquery   SELECT CAST('2020-05-11' AS DATE)
```

I followed the same pattern as the recent `FROM_ISO8601_TIMESTAMP` fix:

- **`sqlglot/expressions/temporal.py`**: new `FromISO8601Date` expression mapped to `FROM_ISO8601_DATE`.
- **`sqlglot/generator.py`**: base `fromiso8601date_sql` emits `CAST(... AS DATE)`, so every dialect gets the cast by default.
- **`sqlglot/generators/presto.py`**: keeps the native function name for Presto and Trino.
- **`tests/dialects/test_presto.py`**: a `validate_all` case covering the Presto/Trino round-trip and the cast output for the other dialects.
