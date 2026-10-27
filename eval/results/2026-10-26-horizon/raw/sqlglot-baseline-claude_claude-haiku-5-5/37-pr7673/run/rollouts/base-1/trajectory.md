# trajectory base-1

final message:
BigQuery `PARSE_TIME` now transpiles to DuckDB as `CAST(STRPTIME(...) AS TIME)`, the same pattern `PARSE_DATE` uses:

```python
sqlglot.transpile("SELECT PARSE_TIME('%H:%M', '14:30')", read="bigquery", write="duckdb")
# ["SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
```

The full suite passes (1112 passed) and ruff check and format are clean. I didn't commit.

Changes:
- **`sqlglot/generators/duckdb.py`**: added `parsetime_sql` next to `strtodate_sql`. It is auto-discovered by name, so no `TRANSFORMS` entry is needed.
- **`tests/dialects/test_duckdb.py`**: added a `validate_all` case beside the existing `PARSE_DATE` one.

One thing I left alone: `SAFE.PARSE_TIME(...)` comes out as `SAFE.CAST(STRPTIME(...) AS TIME)`, which DuckDB won't accept. `SAFE.PARSE_DATE` already produces the same `SAFE.CAST(...)` shape on the untouched code, so this is a pre-existing `SAFE.` prefix problem, not something specific to `PARSE_TIME`. Fixing it would mean changing how `SAFE.`-prefixed functions are generated for DuckDB, which goes beyond this task.

## events
[tool_use Bash] {"command": "grep -rn \"PARSE_DATE\\|ParseDate\\|PARSE_TIME\\|ParseTime\\|TimeFromStr\\|StrToTime\\|StrToDate\" sqlglot/dialects/bigquery.py sqlglot/dialects/duckdb.py sqlglot/expressions.py | head -60; grep -rn \"PARSE_DATE\\|PARSE_TIME\" tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py | head -30", "description": "Find PARSE_DATE/PARSE_TIME handling"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
tests/dialects/test_duckdb.py:1825:            read={"bigquery": "SELECT DATE(PARSE_DATE('%m/%d/%Y', '05/06/2020'))"},
tests/dialects/test_duckdb.py:1896:                "bigquery": "PARSE_TIMESTAMP('%y-%-m', x)",
tests/dialects/test_duckdb.py:1915:                "bigquery": "PARSE_TIMESTAMP('%-m/%e/%y %-I:%M %p', x)",
tests/dialects/test_bigquery.py:53:            "SAFE.PARSE_DATE('%Y-%m-%d', '2024-01-15')",
tests/dialects/test_
…[1971 chars elided]…
       "bigquery": "SELECT PARSE_DATE('%Y%m%d', '20081225')",
tests/dialects/test_bigquery.py:1911:            "SELECT PARSE_DATETIME('%a %b %e %I:%M:%S %Y', 'Thu Dec 25 07:30:00 2008')"
tests/dialects/test_bigquery.py:1914:        self.validate_identity("PARSE_TIME('%I:%M:%S', '07:30:00')")
tests/dialects/test_bigquery.py:3063:            "SELECT PARSE_TIMESTAMP('%F %T', date)",
tests/dialects/test_bigquery.py:3084:          PARSE_TIMESTAMP('%c', 'Thu Dec 25 07:30:00 2008', 'UTC') AS parsed_ts,
[tool_use Bash] {"command": "ugrep -rn \"PARSE_DATE\\|ParseDate\\|ParseTime\\|PARSE_TIME\\|TimeToStr\\|StrToTime\" sqlglot/ | grep -v \"^sqlglot/.*\\.pyc\" | head -60", "description": "Search sqlglot source for parse date/time handling"}
[tool_result] (eval):1: command not found: ugrep
[tool_use Bash] {"command": "grep -rn \"PARSE_DATE\\|ParseDate\\|ParseTime\\|PARSE_TIME\\|StrToDate\\|StrToTime\\|TimeFromParts\\|TsOrDsToTime\\b\" sqlglot/ --include=*.py | head -80", "description": "Search sqlglot source for parse date/time handling"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"PARSE_DATE\\|ParseDate\\|ParseTime\\|PARSE_TIME\\|StrToDate\\|StrToTime\\|TsOrDsToTime\\b\" sqlglot/ | grep \"\\.py:\" | head -80", "description": "Search sqlglot source for parse date/time handling"}
[tool_result] sqlglot/parser.py:7746:                    (exp.StrToDate if to.this == exp.DType.DATE else exp.StrToTime)(
sqlglot/parser.py:7759:                if isinstance(fmt, exp.AtTimeZone) and isinstance(this, exp.StrToTime):
sqlglot/generator.py:3960:    def strtotime_sql(self, expression: exp.StrToTime) -> str:
sqlglot/generator.py:4942:    def tsordstotime_sql(self, expression: exp.TsOrDsToTime) -> str:
sqlglot/generator.py:4949:                    exp.StrToTime(this=this, format=expression.args["fo
…[6395 chars elided]…
on: exp.TimeStrToTime):
sqlglot/generators/clickhouse.py:308:        exp.DateStrToDate: rename_func("toDate"),
sqlglot/generators/clickhouse.py:347:        exp.TimeStrToTime: _timestrtotime_sql,
sqlglot/generators/clickhouse.py:380:        exp.ParseDatetime: rename_func("parseDateTime"),
sqlglot/generators/clickhouse.py:456:    def strtodate_sql(self, expression: exp.StrToDate) -> str:
sqlglot/generators/clickhouse.py:460:            # StrToDate returns DATEs in other dialects (eg. postgres), so
[tool_use Bash] {"command": "sed -n 436,470p sqlglot/expressions/temporal.py; echo ----; sed -n 218,235p sqlglot/parsers/bigquery.py; echo ----; grep -n \"StrToDate\\|StrToTime\\|ParseTime\\|ParseDatetime\\|strtodate\\|strtotime\\|def \\|Cast\" sqlglot/generators/duckdb.py | head -120; echo ----; grep -n \"ParseTime\\|PARSE_TIME\" -r sqlglot tests | head", "description": "Inspect temporal exprs, bigquery parser, duckdb generator"}
[tool_result] class FromISO8601Timestamp(Expression, Func):
    _sql_names = ["FROM_ISO8601_TIMESTAMP"]


class ParseDatetime(Expression, Func):
    arg_types = {"this": True, "format": False, "zone": False}


class ParseTime(Expression, Func):
    arg_types = {"this": True, "format": True}


class StrToDate(Expression, Func):
    arg_types = {"this": True, "format": False, "safe": False}


class StrToTime(Expression, Func):
    arg_types = {"this": True, "format": True, "zone": False, "safe": False, "target_
…[9986 chars elided]…
-%m-%Y %I:%M:%S', col) FROM t",
tests/dialects/test_snowflake.py:1900:                "bigquery": "SELECT PARSE_TIMESTAMP('%m/%d/%Y %H:%M:%S', '04/05/2013 01:02:03')",
tests/dialects/test_snowflake.py:1904:                "bigquery": "SELECT PARSE_TIMESTAMP('%m/%d/%Y %T', '04/05/2013 01:02:03')",
tests/dialects/test_duckdb.py:1896:                "bigquery": "PARSE_TIMESTAMP('%y-%-m', x)",
tests/dialects/test_duckdb.py:1915:                "bigquery": "PARSE_TIMESTAMP('%-m/%e/%y %-I:%M %p', x)",
[tool_use Bash] {"command": "sed -n 2615,2670p sqlglot/generators/duckdb.py; echo ----; grep -n \"PARSE_DATE\\|StrToDate\\|PARSE_TIMESTAMP\" tests/dialects/test_duckdb.py tests/dialects/test_bigquery.py | head -20; echo ----; sed -n 1815,1830p tests/dialects/test_duckdb.py; echo ---; sed -n 1905,1920p tests/dialects/test_bigquery.py; echo ---; sed -n 350,360p sqlglot/generators/bigquery.py", "description": "View duckdb strtotime/strtodate and tests"}
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
…[5525 chars elided]…
P_EXTRACT_ALL", e.this, e.expression),
        exp.RegexpReplace: regexp_replace_sql,
        exp.RegexpLike: rename_func("REGEXP_CONTAINS"),
        exp.ReturnsProperty: _returnsproperty_sql,
        exp.Rollback: lambda *_: "ROLLBACK TRANSACTION",
        exp.ParseTime: lambda self, e: self.func("PARSE_TIME", self.format_time(e), e.this),
        exp.ParseDatetime: lambda self, e: self.func("PARSE_DATETIME", self.format_time(e), e.this),
        exp.Select: transforms.preprocess(
            [
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls -la $PY 2>&1; $PY -I -c \"\nimport sqlglot\nprint(sqlglot.__file__)\nprint(sqlglot.transpile(\\\"SELECT PARSE_TIME('%H:%M', '14:30')\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATE('%m/%d/%Y', '05/06/2020')\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT SAFE.PARSE_TIME('%H:%M', '14:30')\\\", read='bigquery', write='duckdb'))\n\"", "description": "Check baseline transpile output with project Python"}
[tool_result ERROR] Exit code 1
lrwxr-xr-x@ 1 user  wheel  84 Oct 26 08:58 <work>/env-sqlglot/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\nprint(sqlglot.__file__)\nprint(sqlglot.transpile(\\\"SELECT PARSE_TIME('%H:%M', '14:30')\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATE('%m/%d/%Y', '05/06/2020')\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT SAFE.PARSE_TIME('%H:%M', '14:30')\\\", read='bigquery', write='duckdb'))\n\"", "description": "Check baseline transpile output with repo on path"}
[tool_result] ~/.cache/lithify/work/repo-b63a38b63828/20261026-153614-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/__init__.py
["SELECT PARSE_TIME('14:30', '%H:%M')"]
["SELECT CAST(STRPTIME('05/06/2020', '%m/%d/%Y') AS DATE)"]
["SELECT SAFE.PARSE_TIME('14:30', '%H:%M')"]
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-153614-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py", "old_string": "    def tsordstotime_sql(self, expression: exp.TsOrDsToTime) -> str:\n        this = expression.this", "new_string": "    def parsetime_sql(self, expression: exp.ParseTime) -> str:\n        return self.sql(\n            exp.cast(\n                self.func(\"STRPTIME\", expression.this, self.format_time(expression)),\n                exp.DataType(this=exp.DType.TIME),\n            )\n        )\n\n    def tsordstotime_sql(self, expression: exp.TsOrDsToTime) -> str:\n        this = expression.this"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-153614-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[assistant] Now I'll check the output and the round-trip, then add a test next to the existing `PARSE_DATE` case.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT PARSE_TIME('%H:%M', '14:30')\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_TIME('%I:%M:%S', '07:30:00')\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT SAFE.PARSE_TIME('%H:%M', '14:30')\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_TIME('%H:%M', '14:30')\\\", read='bigquery', write='bigquery'))\n\"", "description": "Verify new PARSE_TIME transpilation output"}
[tool_result] ["SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
["SELECT CAST(STRPTIME('07:30:00', '%I:%M:%S') AS TIME)"]
["SELECT SAFE.CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
["SELECT PARSE_TIME('%H:%M', '14:30')"]
[assistant] The plain case is right. The `SAFE.` prefix output looks wrong, so I'll check how `SAFE.PARSE_DATE` behaves for comparison.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT SAFE.PARSE_DATE('%m/%d/%Y', '05/06/2020')\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT SAFE.PARSE_TIMESTAMP('%m/%d/%Y', '05/06/2020')\\\", read='bigquery', write='duckdb'))\n\"; git -C . stash list >/dev/null; grep -n \"SafeFunc\\|safe\" sqlglot/generators/duckdb.py | head -20", "description": "Compare SAFE. handling for PARSE_DATE and PARSE_TIMESTAMP"}
[tool_result] ["SELECT SAFE.CAST(STRPTIME('05/06/2020', '%m/%d/%Y') AS DATE)"]
["SELECT SAFE.STRPTIME('05/06/2020', '%m/%d/%Y')"]
84:# cs/as/ps are Snowflake defaults; DuckDB already behaves the same way, so they are safe to drop.
245:    For TO_BOOLEAN (safe=False): NaN and INF values cause errors. We use DuckDB's native ERROR()
248:    For TRY_TO_BOOLEAN (safe=True): Use DuckDB's TRY_CAST for conversion, which returns NULL
252:    is_safe = expression.args.get("safe", False)
268:    if is_safe:
571:    Tran
…[543 chars elided]…
       func_name = "TRY_DECRYPT_RAW" if expression.args.get("safe") else "DECRYPT_RAW"
2424:        For TRY_TO_BINARY (safe=True), wrap with TRY():
2429:        is_safe = expression.args.get("safe")
2433:            func_name = "TRY_TO_BINARY" if is_safe else "TO_BINARY"
2447:            if is_safe:
2452:        return f"TRY({result})" if is_safe else result
2627:        if expression.args.get("safe"):
2646:        function_name = "STRPTIME" if not expression.args.get("safe") else "TRY_STRPTIME"
[assistant] `SAFE.PARSE_DATE` already produces `SAFE.CAST(...)` on the current code, so the `SAFE.` prefix issue is pre-existing and not specific to `PARSE_TIME`. I'll leave it alone and mirror `PARSE_DATE` exactly. Now the test:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-153614-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_duckdb.py", "old_string": "            read={\"bigquery\": \"SELECT DATE(PARSE_DATE('%m/%d/%Y', '05/06/2020'))\"},\n        )", "new_string": "            read={\"bigquery\": \"SELECT DATE(PARSE_DATE('%m/%d/%Y', '05/06/2020'))\"},\n        )\n        self.validate_all(\n            \"SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)\",\n            read={\"bigquery\": \"SELECT PARSE_TIME('%H:%M', '14:30')\"},\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-153614-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py tests/dialects/test_bigquery.py 2>&1 | tail -15", "description": "Run duckdb and bigquery dialect tests"}
[tool_result] ........................ [ 23%]
..............................................................................                                         [100%]
102 passed, 1658 subtests passed in 0.60s
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; $PY -m ruff check sqlglot/generators/duckdb.py tests/dialects/test_duckdb.py 2>&1 | tail -2; $PY -m ruff format --check sqlglot/generators/duckdb.py tests/dialects/test_duckdb.py 2>&1 | tail -2", "description": "Run full test suite and lint checks"}
[tool_result] ................................................................................................................................. [ 69%]
...................................................... [ 74%]
.................................................................................................................................................................. [ 88%]
...............................................................................................................................                                                   [100%]
1112 passed, 18134 subtests passed in 52.60s
All checks passed!
2 files already formatted
[assistant] BigQuery `PARSE_TIME` now transpiles to DuckDB as `CAST(STRPTIME(...) AS TIME)`, the same pattern `PARSE_DATE` uses:

```python
sqlglot.transpile("SELECT PARSE_TIME('%H:%M', '14:30')", read="bigquery", write="duckdb")
# ["SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
```

The full suite passes (1112 passed) and ruff check and format are clean. I didn't commit.

Changes:
- **`sqlglot/generators/duckdb.py`**: added `parsetime_sql` next to `strtodate_sql`. It is auto-discovered by name, so no `TRANSFORMS` entry is needed.
- **`tests/dialects/test_duckdb.py`**: added a `validate_all` case beside the existing `PARSE_DATE` one.

One thing I left alone: `SAFE.PARSE_TIME(...)` comes out as `SAFE.CAST(STRPTIME(...) AS TIME)`, which DuckDB won't accept. `SAFE.PARSE_DATE` already produces the same `SAFE.CAST(...)` shape on the untouched code, so this is a pre-existing `SAFE.` prefix problem, not something specific to `PARSE_TIME`. Fixing it would mean changing how `SAFE.`-prefixed functions are generated for DuckDB, which goes beyond this task.
