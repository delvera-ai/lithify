# trajectory base-1

final message:
`FROM_ISO8601_DATE` now transpiles to a `CAST(... AS DATE)` for the other dialects, and still round-trips in Presto and Trino. The full test suite passes (1122 passed) and ruff is clean. I left the changes uncommitted.

Your example now gives:

```
snowflake  SELECT CAST('2020-05-11' AS DATE)
duckdb     SELECT CAST('2020-05-11' AS DATE)
spark      SELECT CAST('2020-05-11' AS DATE)
bigquery   SELECT CAST('2020-05-11' AS DATE)
presto     SELECT FROM_ISO8601_DATE('2020-05-11')
trino      SELECT FROM_ISO8601_DATE('2020-05-11')
```

I followed the same pattern as the recent `FROM_ISO8601_TIMESTAMP` fix (7db4d2515):

- **`sqlglot/expressions/temporal.py`**: new `FromISO8601Date` expression, so the parser no longer treats it as an unknown function.
- **`sqlglot/generator.py`**: base-generator `fromiso8601date_sql` that emits a cast to `DATE`, which is what the other dialects get.
- **`sqlglot/generators/presto.py`**: keeps `FROM_ISO8601_DATE` as-is for Presto and Trino.
- **`tests/dialects/test_presto.py`**: a `validate_all` case covering Presto/Trino round-trip and the cast output for DuckDB, Snowflake, Spark and BigQuery.

## events
[tool_use Bash] {"command": "grep -rn -i \"iso8601\\|ISO8601\" sqlglot/ | head -50; git log --oneline -3; ls", "description": "Search ISO8601 references in sqlglot source"}
[tool_result] sqlglot/generator.py:3994:    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:
sqlglot/expressions/temporal.py:436:class FromISO8601Timestamp(Expression, Func):
sqlglot/expressions/temporal.py:437:    _sql_names = ["FROM_ISO8601_TIMESTAMP"]
sqlglot/generators/presto.py:307:        exp.FromISO8601Timestamp: rename_func("FROM_ISO8601_TIMESTAMP"),
45fb92346 lithify: probe base
53d3f3221 eval setup at 7db4d2515435
7db4d2515 fix(snowflake): transpile FROM_ISO8601_TIMESTAMP to cast [CLAUDE] (#7776)
AGENTS.md
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
[tool_use Bash] {"command": "git show 7db4d2515 --stat && git show 7db4d2515 -- sqlglot/ | head -150; sed -n 425,450p sqlglot/expressions/temporal.py; sed -n 3985,4005p sqlglot/generator.py; grep -n \"FromISO8601\\|from_iso8601\" -ri sqlglot/ tests/ | head -30", "description": "Inspect prior FROM_ISO8601_TIMESTAMP commit and related code"}
[tool_result] commit 7db4d2515435ba3d0651f2bd467fca1a747be265
Author: Baruch Oxman <baruch@honeydew.ai>
Date:   Mon Jun 22 12:54:22 2026 +0300

    fix(snowflake): transpile FROM_ISO8601_TIMESTAMP to cast [CLAUDE] (#7776)
    
    FROM_ISO8601_TIMESTAMP is a Presto/Trino function that returns a
    timestamp with timezone. Move DuckDB's cast-to-TIMESTAMPTZ logic into
    the base Generator so it transpiles correctly for all dialects (e.g.
    Snowflake, Spark), and keep the native function for Presto/Trino.
 
…[4351 chars elided]…
ions/temporal.py:437:    _sql_names = ["FROM_ISO8601_TIMESTAMP"]
sqlglot/generators/presto.py:307:        exp.FromISO8601Timestamp: rename_func("FROM_ISO8601_TIMESTAMP"),
tests/dialects/test_presto.py:37:            "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
tests/dialects/test_presto.py:40:                "presto": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
tests/dialects/test_presto.py:41:                "trino": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
[assistant] The FROM_ISO8601_TIMESTAMP fix (7db4d2515) is the pattern to follow. I'll mirror it for `FROM_ISO8601_DATE`: a dedicated expression class, a generic cast-to-DATE generator, and a Presto/Trino passthrough.
[tool_use Bash] {"command": "sed -n 30,50p tests/dialects/test_presto.py && grep -n \"class DiToDate\" -B2 -A2 sqlglot/expressions/temporal.py && grep -n \"DiToDate\\|DATE\\b\" sqlglot/generator.py | head", "description": "View existing Presto test and expression neighbors"}
[tool_result]             },
            write={
                "presto": "CAST(x AS BOOLEAN)",
                "tsql": "CAST(x AS BIT)",
            },
        )
        self.validate_all(
            "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
            write={
                "duckdb": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)",
                "presto": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
                "trino": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:
…[868 chars elided]…
ATE" statement
607:    # Whether FROM is supported in UPDATE statements or if joins must be generated instead, e.g:
608:    # Supported (Postgres, Doris etc): UPDATE t1 SET t1.a = t2.b FROM t2
609:    # Unsupported (MySQL, SingleStore): UPDATE t1 JOIN t2 ON TRUE SET t1.a = t2.b
2617:        Returns (join_sql, from_sql) for UPDATE statements.
2618:        - join_sql: placed after UPDATE table, before SET
2626:        # MySQL requires qualified column names in multi-table UPDATE to avoid ambiguity
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-194202-trino-other-dialects-from-iso860/base-1/sqlglot/expressions/temporal.py", "old_string": "class FromISO8601Timestamp(Expression, Func):\n    _sql_names = [\"FROM_ISO8601_TIMESTAMP\"]\n", "new_string": "class FromISO8601Date(Expression, Func):\n    _sql_names = [\"FROM_ISO8601_DATE\"]\n\n\nclass FromISO8601Timestamp(Expression, Func):\n    _sql_names = [\"FROM_ISO8601_TIMESTAMP\"]\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-194202-trino-other-dialects-from-iso860/base-1/sqlglot/expressions/temporal.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-194202-trino-other-dialects-from-iso860/base-1/sqlglot/generator.py", "old_string": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))\n", "new_string": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))\n\n    def fromiso8601date_sql(self, expression: exp.FromISO8601Date) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.DATE))\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-194202-trino-other-dialects-from-iso860/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-194202-trino-other-dialects-from-iso860/base-1/sqlglot/generators/presto.py", "old_string": "        exp.FromISO8601Timestamp: rename_func(\"FROM_ISO8601_TIMESTAMP\"),", "new_string": "        exp.FromISO8601Date: rename_func(\"FROM_ISO8601_DATE\"),\n        exp.FromISO8601Timestamp: rename_func(\"FROM_ISO8601_TIMESTAMP\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-194202-trino-other-dialects-from-iso860/base-1/sqlglot/generators/presto.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-194202-trino-other-dialects-from-iso860/base-1/tests/dialects/test_presto.py", "old_string": "        self.validate_all(\n            \"CAST(x AS INTERVAL YEAR TO MONTH)\",", "new_string": "        self.validate_all(\n            \"SELECT FROM_ISO8601_DATE('2020-05-11')\",\n            write={\n     
…[123 chars elided]…
-05-11')\",\n                \"trino\": \"SELECT FROM_ISO8601_DATE('2020-05-11')\",\n                \"snowflake\": \"SELECT CAST('2020-05-11' AS DATE)\",\n                \"spark\": \"SELECT CAST('2020-05-11' AS DATE)\",\n                \"bigquery\": \"SELECT CAST('2020-05-11' AS DATE)\",\n            },\n        )\n        self.validate_all(\n            \"CAST(x AS INTERVAL YEAR TO MONTH)\","}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-194202-trino-other-dialects-from-iso860/base-1/tests/dialects/test_presto.py has been updated successfully.
[assistant] Now I'll check the reproduction from the report and run the test suite with the project's configured interpreter.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls -la $PY 2>&1; PYTHONPATH=. $PY -c \"\nimport sqlglot\np = sqlglot.parse_one(\\\"SELECT FROM_ISO8601_DATE('2020-05-11')\\\", 'trino')\nfor d in ['snowflake','duckdb','spark','bigquery','presto','trino']:\n    print(d, p.sql(d))\n\"; PYTHONPATH=. $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_presto.py tests/dialects/test_trino.py 2>&1 | tail -5", "description": "Verify transpilation and run Presto/Trino tests"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 26 08:58 <work>/env-sqlglot/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
snowflake SELECT CAST('2020-05-11' AS DATE)
duckdb SELECT CAST('2020-05-11' AS DATE)
spark SELECT CAST('2020-05-11' AS DATE)
bigquery SELECT CAST('2020-05-11' AS DATE)
presto SELECT FROM_ISO8601_DATE('2020-05-11')
trino SELECT FROM_ISO8601_DATE('2020-05-11')
...........................                          [100%]
27 passed, 524 subtests passed in 0.19s
[assistant] Targeted tests pass and the outputs match the request. Now the full suite, with the project's configured check command.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; git status --short", "description": "Run full test suite and show changed files"}
[tool_result] ............................................ [ 81%]
............... [ 82%]
.................................................................. [ 88%]
.......... [ 89%]
.................................................................. [ 95%]
............................................ [ 99%]
...........                                                         [100%]
1122 passed, 18190 subtests passed in 58.89s
 M sqlglot/expressions/temporal.py
 M sqlglot/generator.py
 M sqlglot/generators/presto.py
 M tests/dialects/test_presto.py
[assistant] The full suite passes. The repo's CLAUDE.md also asks for `make check`, so I'll run the style checks on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff --version && $PY -m ruff check sqlglot/expressions/temporal.py sqlglot/generator.py sqlglot/generators/presto.py tests/dialects/test_presto.py && $PY -m ruff format --check sqlglot/expressions/temporal.py sqlglot/generator.py sqlglot/generators/presto.py tests/dialects/test_presto.py) 2>&1 | tail -6", "description": "Run ruff lint and format checks on changed files"}
[tool_result] ruff 0.15.6
All checks passed!
4 files already formatted
[assistant] `FROM_ISO8601_DATE` now transpiles to a `CAST(... AS DATE)` for the other dialects, and still round-trips in Presto and Trino. The full test suite passes (1122 passed) and ruff is clean. I left the changes uncommitted.

Your example now gives:

```
snowflake  SELECT CAST('2020-05-11' AS DATE)
duckdb     SELECT CAST('2020-05-11' AS DATE)
spark      SELECT CAST('2020-05-11' AS DATE)
bigquery   SELECT CAST('2020-05-11' AS DATE)
presto     SELECT FROM_ISO8601_DATE('2020-05-11')
trino      SELECT FROM_ISO8601_DATE('2020-05-11')
```

I followed the same pattern as the recent `FROM_ISO8601_TIMESTAMP` fix (7db4d2515):

- **`sqlglot/expressions/temporal.py`**: new `FromISO8601Date` expression, so the parser no longer treats it as an unknown function.
- **`sqlglot/generator.py`**: base-generator `fromiso8601date_sql` that emits a cast to `DATE`, which is what the other dialects get.
- **`sqlglot/generators/presto.py`**: keeps `FROM_ISO8601_DATE` as-is for Presto and Trino.
- **`tests/dialects/test_presto.py`**: a `validate_all` case covering Presto/Trino round-trip and the cast output for DuckDB, Snowflake, Spark and BigQuery.
