# trajectory base-1

final message:
BigQuery `PARSE_TIME` now transpiles to DuckDB as `CAST(STRPTIME(...) AS TIME)`, the same approach `PARSE_DATE` uses:

```python
sqlglot.transpile("SELECT PARSE_TIME('%H:%M', '14:30')", read="bigquery", write="duckdb")
# ["SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
```

The fix is a `parsetime_sql` method on the DuckDB generator (`sqlglot/generators/duckdb.py`). I added a read-from-BigQuery test next to the `PARSE_DATE` case in `tests/dialects/test_duckdb.py`.

Verification:
- The full suite passes: 1112 tests, 18134 subtests.
- Ruff lint and format checks pass on both files.
- I ran the generated SQL in DuckDB 1.5.6 and it returns proper `TIME` values.

The changes are uncommitted in the worktree. I haven't committed or opened a PR since you didn't ask for one.

## events
[tool_use Bash] {"command": "grep -rn \"PARSE_DATE\\|ParseDate\\|PARSE_TIME\\|ParseTime\\|TimeStrToTime\\|StrToTime\" sqlglot/dialects/bigquery.py sqlglot/dialects/duckdb.py sqlglot/expressions.py | head -50", "description": "Find PARSE_DATE and PARSE_TIME references"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "ls sqlglot | head -50; grep -rn \"PARSE_DATE\\|PARSE_TIME\\|ParseDate\\|ParseTime\" sqlglot/ tests/ | head -60", "description": "Locate PARSE_DATE and PARSE_TIME references"}
[tool_result] __init__.py
__main__.py
_typing.py
_version.py
dialects
diff.py
errors.py
executor
expressions
generator.py
generators
helper.py
jsonpath.py
lineage.py
optimizer
parser.py
parsers
planner.py
py.typed
schema.py
serde.py
time.py
tokenizer_core.py
tokens.py
transforms.py
trie.py
typing
sqlglot/parsers/clickhouse.py:290:        "PARSEDATETIME": _build_datetime_format(exp.ParseDatetime),
sqlglot/parsers/bigquery.py:224:        "PARSE_DATE": lambda args, dialect: build_formatted_time(exp.StrToDate)(
s
…[5582 chars elided]…
nctions.sql:1093:SAFE.PARSE_TIME('%H:%M:%S', '10:30:00');
tests/fixtures/optimizer/annotate_functions.sql:1097:SAFE.PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', '2024-01-15 10:30:00');
tests/fixtures/optimizer/annotate_functions.sql:1101:PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', '2024-01-15 10:30:00');
tests/fixtures/optimizer/annotate_functions.sql:1429:PARSE_DATETIME('%a %b %e %I:%M:%S %Y', 'Thu Dec 25 07:30:00 2008');
tests/fixtures/optimizer/annotate_functions.sql:1437:PARSE_TIME("%I:%M:%S", "07:30:00");
[tool_use Bash] {"command": "grep -n \"StrToDate\\|StrToTime\\|ParseTime\\|ParseDatetime\\|TimeToStr\\|TsOrDsToTime\\|DATE_PARSE\\|def strtotime\\|StrToTime\" sqlglot/generators/duckdb.py sqlglot/parsers/duckdb.py; sed -n 435,450p sqlglot/expressions/temporal.py; grep -n \"class StrToTime\\|class StrToDate\" -A8 sqlglot/expressions/temporal.py; sed -n 1820,1830p tests/dialects/test_duckdb.py; grep -n \"PARSE_TIME\\|STRPTIME\" tests/dialects/test_duckdb.py | head", "description": "Inspect DuckDB generator and temporal expressions"}
[tool_result] sqlglot/parsers/duckdb.py:175:        "STRFTIME": build_formatted_time(exp.TimeToStr),
sqlglot/parsers/duckdb.py:179:        "STRPTIME": build_formatted_time(exp.StrToTime),
sqlglot/generators/duckdb.py:1575:        exp.DateStrToDate: datestrtodate_sql,
sqlglot/generators/duckdb.py:1663:        exp.TimeStrToDate: lambda self, e: self.sql(exp.cast(e.this, exp.DType.DATE)),
sqlglot/generators/duckdb.py:1664:        exp.TimeStrToTime: timestrtotime_sql,
sqlglot/generators/duckdb.py:1668:        exp
…[1837 chars elided]…
23456789+07:00', '%Y-%m-%dT%H:%M:%S.%n%z')"
1824:            "SELECT CAST(CAST(STRPTIME('05/06/2020', '%m/%d/%Y') AS DATE) AS DATE)",
1894:            "STRPTIME(x, '%y-%-m')",
1896:                "bigquery": "PARSE_TIMESTAMP('%y-%-m', x)",
1897:                "duckdb": "STRPTIME(x, '%y-%-m')",
1913:            "STRPTIME(x, '%-m/%-d/%y %-I:%M %p')",
1915:                "bigquery": "PARSE_TIMESTAMP('%-m/%e/%y %-I:%M %p', x)",
1916:                "duckdb": "STRPTIME(x, '%-m/%-d/%y %-I:%M %p')",
[tool_use Bash] {"command": "sed -n 2615,2660p sqlglot/generators/duckdb.py; sed -n 1655,1670p sqlglot/generators/duckdb.py; sed -n 220,235p sqlglot/parsers/bigquery.py; grep -n \"ParseTime\\|StrToTime\" sqlglot/generators/bigquery.py sqlglot/parsers/*.py | head -20", "description": "Read DuckDB strtotime generator and BigQuery parser"}
[tool_result]             return self.func("SUBSTRING", expression.this, start, length)

        return self.function_fallback_sql(expression)

    def strtotime_sql(self, expression: exp.StrToTime) -> str:
        # Check if target_type requires TIMESTAMPTZ (for LTZ/TZ variants)
        target_type = expression.args.get("target_type")
        needs_tz = target_type and target_type.this in (
            exp.DType.TIMESTAMPLTZ,
            exp.DType.TIMESTAMPTZ,
        )

        if expression.args.get("safe"
…[4440 chars elided]…
7:        "TO_TIMESTAMP": build_formatted_time(exp.StrToTime),
sqlglot/parsers/snowflake.py:105:                    # use StrToTime, not UnixToTime.
sqlglot/parsers/snowflake.py:110:                    # Format string provided (e.g., 'YYYY-MM-DD'), use StrToTime
sqlglot/parsers/snowflake.py:111:                    strtotime_expr = build_formatted_time(exp.StrToTime)(args, dialect)
sqlglot/parsers/oracle.py:16:def _build_to_timestamp(args: list, dialect: Dialect) -> exp.StrToTime | exp.Anonymous:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-131150-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py", "old_string": "    def tsordstotime_sql(self, expression: exp.TsOrDsToTime) -> str:", "new_string": "    def parsetime_sql(self, expression: exp.ParseTime) -> str:\n        formatted_time = self.format_time(expression)\n        return self.sql(\n            exp.cast(\n                self.func(\"STRPTIME\", expression.this, formatted_time),\n                exp.DataType(this=exp.DType.TIME),\n            )\n        )\n\n    def tsordstotime_sql(self, expression: exp.TsOrDsToTime) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-131150-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[assistant] Now I'll check the output and look for the test file's existing `PARSE_DATE` case to model the new test on.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT PARSE_TIME('%H:%M', '14:30')\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_TIME('%H:%M', '14:30')\\\", read='bigquery', write='bigquery'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_TIME('%H:%M:%S', x)\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT CAST(PARSE_TIME('%H:%M', '14:30') AS STRING)\\\", read='bigquery', write='duckdb'))\n\"; <work>/env-sqlglot/bin/python -c \"import duckdb; print(duckdb.__version__)\"; sed -n 1880,1900p tests/dialects/test_duckdb.py", "description": "Check transpiled PARSE_TIME output and duckdb availability"}
[tool_result] ["SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
["SELECT PARSE_TIME('%H:%M', '14:30')"]
["SELECT CAST(STRPTIME(x, '%H:%M:%S') AS TIME)"]
["SELECT CAST(CAST(STRPTIME('14:30', '%H:%M') AS TIME) AS TEXT)"]
1.5.6
                "": "SHA(x)",
            },
        )

        self.validate_all(
            "STRFTIME(x, '%Y-%m-%d %H:%M:%S')",
            write={
                "bigquery": "FORMAT_DATE('%F %T', x)",
                "duckdb": "STRFTIME(x, '%Y-%m-%d %H:%M:%S')",
                "pr
…[15 chars elided]…
RMAT(x, '%Y-%m-%d %T')",
                "hive": "DATE_FORMAT(x, 'yyyy-MM-dd HH:mm:ss')",
            },
        )
        self.validate_all(
            "STRPTIME(x, '%y-%-m')",
            write={
                "bigquery": "PARSE_TIMESTAMP('%y-%-m', x)",
                "duckdb": "STRPTIME(x, '%y-%-m')",
                "presto": "DATE_PARSE(x, '%y-%c')",
                "hive": "CAST(FROM_UNIXTIME(UNIX_TIMESTAMP(x, 'yy-M')) AS TIMESTAMP)",
                "spark": "TO_TIMESTAMP(x, 'yy-M')",
[assistant] The output is right. Next I'll confirm DuckDB 1.5.6 actually accepts the generated SQL, then add a test next to the existing `PARSE_DATE` case.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport duckdb\nprint(duckdb.sql(\\\"SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME), CAST(STRPTIME('07:30:05', '%H:%M:%S') AS TIME)\\\").fetchall())\n\"", "description": "Verify generated DuckDB SQL runs"}
[tool_result] [(datetime.time(14, 30), datetime.time(7, 30, 5))]
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-131150-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_all(\n            \"SELECT CAST(CAST(STRPTIME('05/06/2020', '%m/%d/%Y') AS DATE) AS DATE)\",\n            read={\"bigquery\": \"SELECT DATE(PARSE_DATE('%m/%d/%Y', '05/06/2020'))\"},\n  
…[212 chars elided]…
5/06/2020'))\"},\n        )\n        self.validate_all(\n            \"SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)\",\n            read={\"bigquery\": \"SELECT PARSE_TIME('%H:%M', '14:30')\"},\n            write={\n                \"bigquery\": \"SELECT PARSE_TIME('%H:%M', '14:30')\",\n                \"duckdb\": \"SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)\",\n            },\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-131150-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] I put a wrong `write` entry in that test: the DuckDB SQL won't round-trip back to `PARSE_TIME`. I'll drop it and keep only the `read` case.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-131150-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_duckdb.py", "old_string": "            \"SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)\",\n            read={\"bigquery\": \"SELECT PARSE_TIME('%H:%M', '14:30')\"},\n            write={\n                \"bigquery\": \"SELECT PARSE_TIME('%H:%M', '14:30')\",\n                \"duckdb\": \"SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)\",\n            },\n        )", "new_string": "            \"SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)\",\n            read={\"bigquery\": \"SELECT PARSE_TIME('%H:%M', '14:30')\"},\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-131150-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] Now the full test suite, using the project's check command from the harness instructions.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full project test suite"}
[tool_result] ........................... [  8%]
............. [  9%]
........................................................................................................................................ [ 21%]
............................................................................................................................................................ [ 35%]
........................................ [ 39%]
..................... [ 41%]
................... [ 42%]
................................
…[254 chars elided]…
............................... [ 69%]
...................................................... [ 74%]
.................................................................................................................................................................. [ 88%]
...............................................................................................................................                                                   [100%]
1112 passed, 18134 subtests passed in 53.64s
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff check sqlglot/generators/duckdb.py tests/dialects/test_duckdb.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generators/duckdb.py tests/dialects/test_duckdb.py 2>&1 | tail -3; git diff --stat", "description": "Lint, format-check, and show diff stat"}
[tool_result] All checks passed!
2 files already formatted
 sqlglot/generators/duckdb.py  | 9 +++++++++
 tests/dialects/test_duckdb.py | 4 ++++
 2 files changed, 13 insertions(+)
[assistant] BigQuery `PARSE_TIME` now transpiles to DuckDB as `CAST(STRPTIME(...) AS TIME)`, the same approach `PARSE_DATE` uses:

```python
sqlglot.transpile("SELECT PARSE_TIME('%H:%M', '14:30')", read="bigquery", write="duckdb")
# ["SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
```

The fix is a `parsetime_sql` method on the DuckDB generator (`sqlglot/generators/duckdb.py`). I added a read-from-BigQuery test next to the `PARSE_DATE` case in `tests/dialects/test_duckdb.py`.

Verification:
- The full suite passes: 1112 tests, 18134 subtests.
- Ruff lint and format checks pass on both files.
- I ran the generated SQL in DuckDB 1.5.6 and it returns proper `TIME` values.

The changes are uncommitted in the worktree. I haven't committed or opened a PR since you didn't ask for one.
