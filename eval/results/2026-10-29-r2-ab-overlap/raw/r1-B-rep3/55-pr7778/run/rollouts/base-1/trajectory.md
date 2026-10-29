# trajectory base-1

final message:
`FROM_ISO8601_DATE` now transpiles to a `CAST(... AS DATE)` for non-Presto/Trino dialects, and round-trips in Trino and Presto. The full suite passes (1122 tests, 18191 subtests), and ruff lint and format checks are clean on the changed files. I did not commit.

Your example now gives:

- trino / presto: `SELECT FROM_ISO8601_DATE('2020-05-11')`
- snowflake / duckdb / spark / bigquery: `SELECT CAST('2020-05-11' AS DATE)`

Changes, following the same pattern as the existing `FROM_ISO8601_TIMESTAMP` support:

- `sqlglot/expressions/temporal.py`: new `FromISO8601Date` expression mapped to `FROM_ISO8601_DATE`.
- `sqlglot/generator.py`: base `fromiso8601date_sql` emits a cast to `DATE`, so every dialect gets it by default.
- `sqlglot/generators/presto.py`: Presto/Trino keep the native function name.
- `tests/dialects/test_presto.py`: a `validate_all` case covering Presto, Trino, DuckDB, Snowflake, Spark, Databricks and BigQuery.

## events
[tool_use Bash] {"command": "grep -rn -i \"iso8601\" sqlglot/ | head -50 && git show 7db4d2515 --stat | head -20", "description": "Search ISO8601 handling in sqlglot source"}
[tool_result] sqlglot/generator.py:3994:    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:
sqlglot/expressions/temporal.py:436:class FromISO8601Timestamp(Expression, Func):
sqlglot/expressions/temporal.py:437:    _sql_names = ["FROM_ISO8601_TIMESTAMP"]
sqlglot/generators/presto.py:307:        exp.FromISO8601Timestamp: rename_func("FROM_ISO8601_TIMESTAMP"),
commit 7db4d2515435ba3d0651f2bd467fca1a747be265
Author: Baruch Oxman <baruch@honeydew.ai>
Date:   Mon Jun 22 12:54:22 202
…[162 chars elided]…
   timestamp with timezone. Move DuckDB's cast-to-TIMESTAMPTZ logic into
    the base Generator so it transpiles correctly for all dialects (e.g.
    Snowflake, Spark), and keep the native function for Presto/Trino.
    
    Co-authored-by: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

 sqlglot/generator.py          | 3 +++
 sqlglot/generators/duckdb.py  | 3 ---
 sqlglot/generators/presto.py  | 1 +
 tests/dialects/test_presto.py | 5 +++++
 4 files changed, 9 insertions(+), 3 deletions(-)
[tool_use Bash] {"command": "sed -n 3985,4005p sqlglot/generator.py && echo ---- && sed -n 425,445p sqlglot/expressions/temporal.py && echo ---- && sed -n 295,315p sqlglot/generators/presto.py && echo ---- && git show 7db4d2515 -- tests/dialects/test_presto.py sqlglot/generators/duckdb.py && grep -rn \"FromISO8601\\|ISO8601\" sqlglot/ tests/ | grep -v \"^sqlglot/generator.py:3994\"", "description": "Inspect ISO8601 code and recent commit diff"}
[tool_result]         this = self.sql(expression, "this")
        zone = self.sql(expression, "zone")
        return f"{this} AT TIME ZONE {zone}"

    def fromtimezone_sql(self, expression: exp.FromTimeZone) -> str:
        this = self.sql(expression, "this")
        zone = self.sql(expression, "zone")
        return f"{this} AT TIME ZONE {zone} AT TIME ZONE 'UTC'"

    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:
        return self.sql(exp.cast(expression.this, exp.DType
…[3353 chars elided]…
ions/temporal.py:437:    _sql_names = ["FROM_ISO8601_TIMESTAMP"]
sqlglot/generators/presto.py:307:        exp.FromISO8601Timestamp: rename_func("FROM_ISO8601_TIMESTAMP"),
tests/dialects/test_presto.py:37:            "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
tests/dialects/test_presto.py:40:                "presto": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
tests/dialects/test_presto.py:41:                "trino": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-203233-trino-other-dialects-from-iso860/base-1/sqlglot/expressions/temporal.py", "old_string": "class FromISO8601Timestamp(Expression, Func):\n    _sql_names = [\"FROM_ISO8601_TIMESTAMP\"]\n", "new_string": "class FromISO8601Date(Expression, Func):\n    _sql_names = [\"FROM_ISO8601_DATE\"]\n\n\nclass FromISO8601Timestamp(Expression, Func):\n    _sql_names = [\"FROM_ISO8601_TIMESTAMP\"]\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-203233-trino-other-dialects-from-iso860/base-1/sqlglot/expressions/temporal.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-203233-trino-other-dialects-from-iso860/base-1/tests/dialects/test_presto.py", "offset": 30, "limit": 25}
[tool_result] 30	            },
31	            write={
32	                "presto": "CAST(x AS BOOLEAN)",
33	                "tsql": "CAST(x AS BIT)",
34	            },
35	        )
36	        self.validate_all(
37	            "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
38	            write={
39	                "duckdb": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)",
40	                "presto": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
41	                "trino": "SELECT FROM_
…[171 chars elided]…
020-05-11T11:15:05' AS TIMESTAMP)",
44	                "databricks": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMP)",
45	                "bigquery": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMP)",
46	            },
47	        )
48	        self.validate_all(
49	            "CAST(x AS INTERVAL YEAR TO MONTH)",
50	            write={
51	                "oracle": "CAST(x AS INTERVAL YEAR TO MONTH)",
52	                "presto": "CAST(x AS INTERVAL YEAR TO MONTH)",
53	            },
54	        )
[assistant] Now the generator method (auto-discovered by name, per the repo's convention), the Presto/Trino mapping, and a test.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-203233-trino-other-dialects-from-iso860/base-1/sqlglot/generator.py", "old_string": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:", "new_string": "    def fromiso8601date_sql(self, expression: exp.FromISO8601Date) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.DATE))\n\n    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-203233-trino-other-dialects-from-iso860/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-203233-trino-other-dialects-from-iso860/base-1/sqlglot/generators/presto.py", "old_string": "        exp.FromISO8601Timestamp: rename_func(\"FROM_ISO8601_TIMESTAMP\"),", "new_string": "        exp.FromISO8601Date: rename_func(\"FROM_ISO8601_DATE\"),\n        exp.FromISO8601Timestamp: rename_func(\"FROM_ISO8601_TIMESTAMP\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-203233-trino-other-dialects-from-iso860/base-1/sqlglot/generators/presto.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-203233-trino-other-dialects-from-iso860/base-1/tests/dialects/test_presto.py", "old_string": "        self.validate_all(\n            \"CAST(x AS INTERVAL YEAR TO MONTH)\",", "new_string": "        self.validate_all(\n            \"SELECT FROM_ISO8601_DATE('2020-05-11')\",\n            write={\n     
…[195 chars elided]…
-05-11')\",\n                \"snowflake\": \"SELECT CAST('2020-05-11' AS DATE)\",\n                \"spark\": \"SELECT CAST('2020-05-11' AS DATE)\",\n                \"databricks\": \"SELECT CAST('2020-05-11' AS DATE)\",\n                \"bigquery\": \"SELECT CAST('2020-05-11' AS DATE)\",\n            },\n        )\n        self.validate_all(\n            \"CAST(x AS INTERVAL YEAR TO MONTH)\","}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-203233-trino-other-dialects-from-iso860/base-1/tests/dialects/test_presto.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\np = sqlglot.parse_one(\\\"SELECT FROM_ISO8601_DATE('2020-05-11')\\\", 'trino')\nfor d in ['trino','presto','snowflake','duckdb','spark','bigquery']:\n    print(d, p.sql(d))\n\" && $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Check example output and run full test suite"}
[tool_result] trino SELECT FROM_ISO8601_DATE('2020-05-11')
presto SELECT FROM_ISO8601_DATE('2020-05-11')
snowflake SELECT CAST('2020-05-11' AS DATE)
duckdb SELECT CAST('2020-05-11' AS DATE)
spark SELECT CAST('2020-05-11' AS DATE)
bigquery SELECT CAST('2020-05-11' AS DATE)
.................................................................... [ 19%]
..................... [ 21%]
.............. [ 22%]
................................................................. [ 28%]
.........................................
…[443 chars elided]…
............................. [ 71%]
........................................................... [ 77%]
............................................ [ 81%]
............... [ 82%]
.................................................................. [ 88%]
.......... [ 89%]
..........................................................................................................................                                                        [100%]
1122 passed, 18191 subtests passed in 46.61s
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff check sqlglot/expressions/temporal.py sqlglot/generator.py sqlglot/generators/presto.py tests/dialects/test_presto.py && $PY -m ruff format --check sqlglot/expressions/temporal.py sqlglot/generator.py sqlglot/generators/presto.py tests/dialects/test_presto.py) 2>&1 | tail -5; git status --short", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
4 files already formatted
 M sqlglot/expressions/temporal.py
 M sqlglot/generator.py
 M sqlglot/generators/presto.py
 M tests/dialects/test_presto.py
[assistant] `FROM_ISO8601_DATE` now transpiles to a `CAST(... AS DATE)` for non-Presto/Trino dialects, and round-trips in Trino and Presto. The full suite passes (1122 tests, 18191 subtests), and ruff lint and format checks are clean on the changed files. I did not commit.

Your example now gives:

- trino / presto: `SELECT FROM_ISO8601_DATE('2020-05-11')`
- snowflake / duckdb / spark / bigquery: `SELECT CAST('2020-05-11' AS DATE)`

Changes, following the same pattern as the existing `FROM_ISO8601_TIMESTAMP` support:

- `sqlglot/expressions/temporal.py`: new `FromISO8601Date` expression mapped to `FROM_ISO8601_DATE`.
- `sqlglot/generator.py`: base `fromiso8601date_sql` emits a cast to `DATE`, so every dialect gets it by default.
- `sqlglot/generators/presto.py`: Presto/Trino keep the native function name.
- `tests/dialects/test_presto.py`: a `validate_all` case covering Presto, Trino, DuckDB, Snowflake, Spark, Databricks and BigQuery.
