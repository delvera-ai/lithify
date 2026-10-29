# trajectory base-1

final message:
`FROM_ISO8601_DATE` now transpiles from Trino to Snowflake, DuckDB, Spark, and BigQuery as a cast to `DATE`, and round-trips unchanged in Presto/Trino. The full suite passes (1122 tests), and I confirmed your example output.

I followed the same pattern as the recent `FROM_ISO8601_TIMESTAMP` fix:

- **`sqlglot/expressions/temporal.py`**: added `FromISO8601Date` with `_sql_names = ["FROM_ISO8601_DATE"]`, so the parser recognises it instead of treating it as an unknown function.
- **`sqlglot/generator.py`**: added `fromiso8601date_sql`, which emits `CAST(x AS DATE)`. This is the default for every dialect that doesn't override it.
- **`sqlglot/generators/presto.py`**: added a `rename_func` entry so Presto and Trino keep `FROM_ISO8601_DATE(...)`.
- **`tests/dialects/test_presto.py`**: added a `validate_all` case covering Presto, Trino, DuckDB, Snowflake, Spark, Databricks, and BigQuery.

I haven't committed anything.

## events
[tool_use Bash] {"command": "grep -rn -i \"iso8601\" sqlglot/dialects/presto.py sqlglot/dialects/trino.py sqlglot/dialects/snowflake.py sqlglot/dialects/duckdb.py sqlglot/dialects/spark*.py sqlglot/dialects/bigquery.py sqlglot/expressions.py | head -50; git log --oneline -1 -- sqlglot/dialects/snowflake.py", "description": "Find ISO8601 handling across dialects"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
2e7f8b7e6 feat(snowflake)!: add UNDROP support for all Snowflake Time Travel object types (#7735)
[tool_use Bash] {"command": "ls; grep -rn -i \"iso8601\" sqlglot/ | head -50; git show 7db4d2515 --stat | head -20", "description": "Search for ISO8601 handling in sqlglot source"}
[tool_result] AGENTS.md
CHANGELOG.md
CLAUDE.md
CONTRIBUTING.md
LICENSE
MANIFEST.in
Makefile
README.md
benchmarks
pdoc
posts
pyproject.toml
setup.cfg
setup.py
sqlglot
sqlglot-integration-tests
sqlglot.png
sqlglotc
tests
sqlglot/generator.py:3994:    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:
sqlglot/expressions/temporal.py:436:class FromISO8601Timestamp(Expression, Func):
sqlglot/expressions/temporal.py:437:    _sql_names = ["FROM_ISO8601_TIMESTAMP"]
sqlglot/generators/pre
…[367 chars elided]…
   timestamp with timezone. Move DuckDB's cast-to-TIMESTAMPTZ logic into
    the base Generator so it transpiles correctly for all dialects (e.g.
    Snowflake, Spark), and keep the native function for Presto/Trino.
    
    Co-authored-by: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

 sqlglot/generator.py          | 3 +++
 sqlglot/generators/duckdb.py  | 3 ---
 sqlglot/generators/presto.py  | 1 +
 tests/dialects/test_presto.py | 5 +++++
 4 files changed, 9 insertions(+), 3 deletions(-)
[tool_use Bash] {"command": "git show 7db4d2515 -- sqlglot tests | head -120; sed -n 425,445p sqlglot/expressions/temporal.py; sed -n 3988,4002p sqlglot/generator.py; grep -n \"FromISO8601\\|ISO8601\" sqlglot/generators/presto.py sqlglot/parser.py sqlglot/dialects/*.py sqlglot/expressions/*.py", "description": "Inspect precedent commit and related code"}
[tool_result] commit 7db4d2515435ba3d0651f2bd467fca1a747be265
Author: Baruch Oxman <baruch@honeydew.ai>
Date:   Mon Jun 22 12:54:22 2026 +0300

    fix(snowflake): transpile FROM_ISO8601_TIMESTAMP to cast [CLAUDE] (#7776)
    
    FROM_ISO8601_TIMESTAMP is a Presto/Trino function that returns a
    timestamp with timezone. Move DuckDB's cast-to-TIMESTAMPTZ logic into
    the base Generator so it transpiles correctly for all dialects (e.g.
    Snowflake, Spark), and keep the native function for Presto/Trino.
 
…[3612 chars elided]…
lf, expression: exp.Add) -> str:
        return self.binary(expression, "+")

    def and_sql(self, expression: exp.And, stack: list[str | exp.Expr] | None = None) -> str:
        return self.connector_sql(expression, "AND", stack)

sqlglot/generators/presto.py:307:        exp.FromISO8601Timestamp: rename_func("FROM_ISO8601_TIMESTAMP"),
sqlglot/expressions/temporal.py:436:class FromISO8601Timestamp(Expression, Func):
sqlglot/expressions/temporal.py:437:    _sql_names = ["FROM_ISO8601_TIMESTAMP"]
[assistant] Following the pattern from the recent `FROM_ISO8601_TIMESTAMP` commit: add an expression class, a base-generator cast to `DATE`, and a Presto/Trino passthrough.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-142239-trino-other-dialects-from-iso860/base-1/sqlglot/expressions/temporal.py", "old_string": "class FromISO8601Timestamp(Expression, Func):", "new_string": "class FromISO8601Date(Expression, Func):\n    _sql_names = [\"FROM_ISO8601_DATE\"]\n\n\nclass FromISO8601Timestamp(Expression, Func):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-142239-trino-other-dialects-from-iso860/base-1/sqlglot/expressions/temporal.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-142239-trino-other-dialects-from-iso860/base-1/sqlglot/generator.py", "old_string": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:", "new_string": "    def fromiso8601date_sql(self, expression: exp.FromISO8601Date) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.DATE))\n\n    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-142239-trino-other-dialects-from-iso860/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-142239-trino-other-dialects-from-iso860/base-1/sqlglot/generators/presto.py", "offset": 300, "limit": 12}
[tool_result] 300	        exp.Decode: lambda self, e: encode_decode_sql(self, e, "FROM_UTF8"),
301	        exp.DiToDate: lambda self, e: (
302	            f"CAST(DATE_PARSE(CAST({self.sql(e, 'this')} AS VARCHAR), {type(self.dialect).DATEINT_FORMAT}) AS DATE)"
303	        ),
304	        exp.Encode: lambda self, e: encode_decode_sql(self, e, "TO_UTF8"),
305	        exp.FileFormatProperty: lambda self, e: f"format={self.sql(exp.Literal.string(e.name))}",
306	        exp.First: _first_last_sql,
307	        exp.FromISO8601Timestamp: rename_func("FROM_ISO8601_TIMESTAMP"),
308	        exp.FromTimeZone: lambda self, e: (
309	            f"WITH_TIMEZONE({self.sql(e, 'this')}, {self.sql(e, 'zone')}) AT TIME ZONE 'UTC'"
310	        ),
311	        exp.GenerateSeries: sequence_sql,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-142239-trino-other-dialects-from-iso860/base-1/sqlglot/generators/presto.py", "old_string": "        exp.FromISO8601Timestamp: rename_func(\"FROM_ISO8601_TIMESTAMP\"),", "new_string": "        exp.FromISO8601Date: rename_func(\"FROM_ISO8601_DATE\"),\n        exp.FromISO8601Timestamp: rename_func(\"FROM_ISO8601_TIMESTAMP\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-142239-trino-other-dialects-from-iso860/base-1/sqlglot/generators/presto.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"FROM_ISO8601_TIMESTAMP\" -B3 -A8 tests/dialects/test_presto.py | head -30", "description": "Locate existing ISO8601 timestamp tests in Presto"}
[tool_result] 34-            },
35-        )
36-        self.validate_all(
37:            "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
38-            write={
39-                "duckdb": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)",
40:                "presto": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
41:                "trino": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
42-                "snowflake": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)",
43-                "spark": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMP)",
44-                "databricks": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMP)",
45-                "bigquery": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMP)",
46-            },
47-        )
48-        self.validate_all(
49-            "CAST(x AS INTERVAL YEAR TO MONTH)",
[assistant] Now I'll add a test alongside the existing timestamp test, then run the check command from the project harness.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-142239-trino-other-dialects-from-iso860/base-1/tests/dialects/test_presto.py", "old_string": "        self.validate_all(\n            \"SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')\",", "new_string": "        self.validate_all(\n            \"SELECT FROM_ISO8601_DATE('2020-05-11')\",\n       
…[233 chars elided]…
          \"snowflake\": \"SELECT CAST('2020-05-11' AS DATE)\",\n                \"spark\": \"SELECT CAST('2020-05-11' AS DATE)\",\n                \"databricks\": \"SELECT CAST('2020-05-11' AS DATE)\",\n                \"bigquery\": \"SELECT CAST('2020-05-11' AS DATE)\",\n            },\n        )\n        self.validate_all(\n            \"SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')\","}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-142239-trino-other-dialects-from-iso860/base-1/tests/dialects/test_presto.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_presto.py tests/dialects/test_trino.py tests/dialects/test_snowflake.py 2>&1 | tail -15; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\np = sqlglot.parse_one(\\\"SELECT FROM_ISO8601_DATE('2020-05-11')\\\", 'trino')\nfor d in ['snowflake','duckdb','spark','bigquery','trino']: print(d, p.sql(d))\n\"", "description": "Run dialect tests and verify the reported example"}
[tool_result] .................................. [ 27%]
........................... [ 49%]
............................... [ 74%]
...............................                 [100%]
123 passed, 2093 subtests passed in 0.72s
snowflake SELECT CAST('2020-05-11' AS DATE)
duckdb SELECT CAST('2020-05-11' AS DATE)
spark SELECT CAST('2020-05-11' AS DATE)
bigquery SELECT CAST('2020-05-11' AS DATE)
trino SELECT FROM_ISO8601_DATE('2020-05-11')
[assistant] The targeted tests pass and the reported example now transpiles. Running the full suite to check for regressions.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; git status --short", "description": "Run full test suite and show changed files"}
[tool_result] ............... [ 82%]
.................................................................. [ 88%]
.......... [ 89%]
..........................................................................................................................                                                        [100%]
1122 passed, 18191 subtests passed in 49.60s
 M sqlglot/expressions/temporal.py
 M sqlglot/generator.py
 M sqlglot/generators/presto.py
 M tests/dialects/test_presto.py
[assistant] `FROM_ISO8601_DATE` now transpiles from Trino to Snowflake, DuckDB, Spark, and BigQuery as a cast to `DATE`, and round-trips unchanged in Presto/Trino. The full suite passes (1122 tests), and I confirmed your example output.

I followed the same pattern as the recent `FROM_ISO8601_TIMESTAMP` fix:

- **`sqlglot/expressions/temporal.py`**: added `FromISO8601Date` with `_sql_names = ["FROM_ISO8601_DATE"]`, so the parser recognises it instead of treating it as an unknown function.
- **`sqlglot/generator.py`**: added `fromiso8601date_sql`, which emits `CAST(x AS DATE)`. This is the default for every dialect that doesn't override it.
- **`sqlglot/generators/presto.py`**: added a `rename_func` entry so Presto and Trino keep `FROM_ISO8601_DATE(...)`.
- **`tests/dialects/test_presto.py`**: added a `validate_all` case covering Presto, Trino, DuckDB, Snowflake, Spark, Databricks, and BigQuery.

I haven't committed anything.
