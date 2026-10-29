# trajectory base-1

final message:
BigQuery `PARSE_TIME` now transpiles to DuckDB as `CAST(STRPTIME(...) AS TIME)`, the same pattern `PARSE_DATE` uses:

```python
sqlglot.transpile("SELECT PARSE_TIME('%H:%M', '14:30')", read="bigquery", write="duckdb")
# ["SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
```

The change is a new `parsetime_sql` method in `sqlglot/generators/duckdb.py`, placed next to `strtodate_sql`. I also added a `validate_all` case to `tests/dialects/test_bigquery.py` covering the round trip and the DuckDB output.

The full suite passes (1112 tests), and ruff check and format are clean on both files. The changes are uncommitted in the working tree. I haven't committed because you didn't ask for a commit.

## events
[tool_use Bash] {"command": "grep -rn \"PARSE_DATE\\|ParseDate\\|ParseTime\\|PARSE_TIME\" sqlglot/ | head -50", "description": "Find PARSE_DATE and PARSE_TIME references"}
[tool_result] sqlglot/parsers/clickhouse.py:290:        "PARSEDATETIME": _build_datetime_format(exp.ParseDatetime),
sqlglot/parsers/bigquery.py:224:        "PARSE_DATE": lambda args, dialect: build_formatted_time(exp.StrToDate)(
sqlglot/parsers/bigquery.py:227:        "PARSE_TIME": lambda args, dialect: build_formatted_time(exp.ParseTime)(
sqlglot/parsers/bigquery.py:230:        "PARSE_TIMESTAMP": _build_parse_timestamp,
sqlglot/parsers/bigquery.py:231:        "PARSE_DATETIME": lambda args, dialect: build_for
…[347 chars elided]…
ParseDatetime: rename_func("parseDateTime"),
sqlglot/generators/bigquery.py:357:        exp.ParseTime: lambda self, e: self.func("PARSE_TIME", self.format_time(e), e.this),
sqlglot/generators/bigquery.py:358:        exp.ParseDatetime: lambda self, e: self.func("PARSE_DATETIME", self.format_time(e), e.this),
sqlglot/generators/presto.py:511:        # timezone involved, we wrap it in a `TRY` call and use `PARSE_DATETIME` as a fallback,
sqlglot/generators/presto.py:522:            "PARSE_DATETIME",
[tool_use Bash] {"command": "grep -n \"StrToDate\\|StrToTime\\|TsOrDsToDate\\|TimeToStr\\|def _str_to\\|ParseTime\" sqlglot/generators/duckdb.py sqlglot/dialects/duckdb.py sqlglot/parsers/duckdb.py; sed -n 435,450p sqlglot/expressions/temporal.py; grep -n \"class StrToDate\\|class StrToTime\" -A4 sqlglot/expressions/temporal.py; ls <work>/env-sqlglot/bin/python", "description": "Inspect duckdb str-to-date handling and env python"}
[tool_result] 8 matches in 2 files:

sqlglot/generators/duckdb.py:1575:exp.DateStrToDate: datestrtodate_sql,
sqlglot/generators/duckdb.py:1663:exp.TimeStrToDate: lambda self, e: self.sql(exp.cast(e.this, exp.DType.DATE)),
sqlglot/generators/duckdb.py:1664:exp.TimeStrToTime: timestrtotime_sql,
sqlglot/generators/duckdb.py:1668:exp.TimeToStr: lambda self, e: self.func("STRFTIME", e.this, self.format_time...
sqlglot/generators/duckdb.py:2619:def strtotime_sql(self, expression: exp.StrToTime) -> str:
sqlglot/gene
…[592 chars elided]…
t": False, "safe": False}

448:class StrToDate(Expression, Func):
449-    arg_types = {"this": True, "format": False, "safe": False}
450-
451-
452:class StrToTime(Expression, Func):
453-    arg_types = {"this": True, "format": True, "zone": False, "safe": False, "target_type": False}
454-
455-
456-class StrToUnix(Expression, Func):
<work>/env-sqlglot/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12  84B
[tool_use Bash] {"command": "sed -n 2615,2665p sqlglot/generators/duckdb.py; grep -n \"PARSE_DATE\\|PARSE_TIME\" -B2 -A6 tests/dialects/test_bigquery.py | head -80", "description": "Read duckdb str-to-time/date generators and bigquery tests"}
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
…[5188 chars elided]…
115-            "SELECT CAST(TIMESTAMP '2008-12-25 00:00:00+00:00' AS STRING FORMAT 'YYYY-MM-DD HH24:MI:SS TZH:TZM') AS date_time_to_string",
1116-            write={
1117-                "bigquery": "SELECT CAST(CAST('2008-12-25 00:00:00+00:00' AS TIMESTAMP) AS STRING FORMAT 'YYYY-MM-DD HH24:MI:SS TZH:TZM') AS date_time_to_string",
1118-            },
--
1156-            "cast(x as date format 'MM/DD/YYYY')",
1157-            write={
1158:                "bigquery": "PARSE_DATE('%m/%d/%Y', x)",
[assistant] The BigQuery `PARSE_DATE` path goes through `exp.StrToDate`, whose DuckDB generator emits `CAST(STRPTIME(...) AS DATE)`. `PARSE_TIME` parses to `exp.ParseTime`, which DuckDB has no generator for, so it falls back to a raw function name. I'll add a DuckDB `parsetime_sql` mirroring `strtodate_sql`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-193203-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py", "old_string": "    def tsordstotime_sql(self, expression: exp.TsOrDsToTime) -> str:", "new_string": "    def parsetime_sql(self, expression: exp.ParseTime) -> str:\n        return self.sql(\n            exp.cast(\n                self.func(\"STRPTIME\", expression.this, self.format_time(expression)),\n                exp.DataType(this=exp.DType.TIME),\n            )\n        )\n\n    def tsordstotime_sql(self, expression: exp.TsOrDsToTime) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-193203-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT PARSE_TIME('%H:%M', '14:30')\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_TIME('%H:%M:%S', t) FROM x\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATE('%Y-%m-%d', d)\\\", read='bigquery', write='duckdb'))\n\"", "description": "Check PARSE_TIME transpilation output"}
[tool_result] ["SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
["SELECT CAST(STRPTIME(t, '%H:%M:%S') AS TIME) FROM x"]
["SELECT CAST(STRPTIME(d, '%Y-%m-%d') AS DATE)"]
[assistant] The output is correct. Now I'll add a regression test next to the existing BigQuery→DuckDB cases, then run the suite.
[tool_use Bash] {"command": "sed -n 1150,1165p tests/dialects/test_bigquery.py", "description": "View PARSE_DATE test block for placement"}
[tool_result]             write={
                "bigquery": "SELECT CAST(STRUCT(1) AS STRUCT<INT64>)",
                "snowflake": "SELECT CAST(OBJECT_CONSTRUCT('_0', 1) AS OBJECT)",
            },
        )
        self.validate_all(
            "cast(x as date format 'MM/DD/YYYY')",
            write={
                "bigquery": "PARSE_DATE('%m/%d/%Y', x)",
            },
        )
        self.validate_all(
            "cast(x as time format 'YYYY.MM.DD HH:MI:SSTZH')",
            write={
                "bigquery": "PARSE_TIMESTAMP('%Y.%m.%d %I:%M:%S%z', x)",
            },
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-193203-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_bigquery.py", "old_string": "        self.validate_all(\n            \"PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%E6S%z', x)\",\n            write={\n                \"bigquery\": \"PARSE_TIMESTAMP('%FT%H:%M:%E6S%z', x)\",\n                \"du
…[464 chars elided]…
           },\n        )\n        self.validate_all(\n            \"PARSE_TIME('%H:%M', '14:30')\",\n            write={\n                \"bigquery\": \"PARSE_TIME('%H:%M', '14:30')\",\n                \"duckdb\": \"CAST(STRPTIME('14:30', '%H:%M') AS TIME)\",\n            },\n        )\n        self.validate_all(\n            \"SELECT results FROM Coordinates, Coordinates.position AS results\","}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-193203-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run project test suite", "timeout": 900000}
[tool_result] ........................... [ 37%]
.................................. [ 41%]
.......... [ 41%]
......................................... [ 45%]
......................................... [ 49%]
..................................... [ 52%]
.............................. [ 55%]
................... [ 57%]
..... [ 57%]
................... [ 59%]
........................ [ 61%]
............................................................................................................................................ [ 73%]
.................................................................................................................................. [ 85%]
................................................................................................................................................................                                                  [100%]
1112 passed, 18135 subtests passed in 46.31s
[assistant] All 1112 tests pass. I'll run the linter on the two changed files, then commit.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/generators/duckdb.py tests/dialects/test_bigquery.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generators/duckdb.py tests/dialects/test_bigquery.py) 2>&1 | tail -5; git status --short", "description": "Lint changed files and show git status"}
[tool_result] All checks passed!
2 files already formatted
 M sqlglot/generators/duckdb.py
 M tests/dialects/test_bigquery.py
[assistant] BigQuery `PARSE_TIME` now transpiles to DuckDB as `CAST(STRPTIME(...) AS TIME)`, the same pattern `PARSE_DATE` uses:

```python
sqlglot.transpile("SELECT PARSE_TIME('%H:%M', '14:30')", read="bigquery", write="duckdb")
# ["SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
```

The change is a new `parsetime_sql` method in `sqlglot/generators/duckdb.py`, placed next to `strtodate_sql`. I also added a `validate_all` case to `tests/dialects/test_bigquery.py` covering the round trip and the DuckDB output.

The full suite passes (1112 tests), and ruff check and format are clean on both files. The changes are uncommitted in the working tree. I haven't committed because you didn't ask for a commit.
