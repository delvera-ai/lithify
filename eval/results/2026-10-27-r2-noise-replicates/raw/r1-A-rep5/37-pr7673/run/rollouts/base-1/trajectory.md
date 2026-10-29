# trajectory base-1

final message:
`PARSE_TIME` now transpiles to DuckDB as `CAST(STRPTIME(...) AS TIME)`, the same way `PARSE_DATE` becomes a `DATE` cast:

```python
sqlglot.transpile("SELECT PARSE_TIME('%H:%M', '14:30')", read="bigquery", write="duckdb")
# ["SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
```

The full suite passes: 1112 tests, 18134 subtests.

**Changes**
- `sqlglot/generators/duckdb.py`: added a `parsetime_sql` method next to `strtodate_sql`. It is auto-discovered by name, so no `TRANSFORMS` entry is needed. The BigQuery format string is converted to DuckDB's format through the usual `format_time` path, so format directives like `%I:%M:%S %p` also come out correctly.
- `tests/dialects/test_duckdb.py`: added a BigQuery→DuckDB case next to the existing `PARSE_DATE` case.

I did not run `make style`/ruff. I did not commit.

## events
[tool_use Bash] {"command": "rtk grep -rn \"PARSE_DATE\\|ParseDate\\|PARSE_TIME\\|ParseTime\\|TimeToStr\\|StrToTime\" sqlglot/dialects/bigquery.py sqlglot/dialects/duckdb.py sqlglot/expressions.py | head -60", "description": "Find PARSE_DATE/PARSE_TIME handling in dialects"}
[tool_result] (eval):1: command not found: rtk
[tool_use Bash] {"command": "grep -rn \"PARSE_DATE\\|ParseDate\\|PARSE_TIME\\|ParseTime\\|StrToTime\\|TsOrDsToTime\\|TimeStrToTime\" sqlglot/dialects/bigquery.py sqlglot/dialects/duckdb.py sqlglot/expressions.py | head -60", "description": "Find PARSE_DATE/PARSE_TIME handling in dialects"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "ls && grep -rn \"PARSE_DATE\\|ParseDate\\|PARSE_TIME\\|ParseTime\\|StrToTime\\|TsOrDsToTime\\|TimeStrToTime\" sqlglot/dialects/bigquery.py sqlglot/dialects/duckdb.py sqlglot/expressions/*.py | head -60", "description": "Find PARSE_DATE/PARSE_TIME handling in dialects"}
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
sqlglot/expressions/core.py:2361:        from sqlglot.expressions.temporal import TimeStrToTime as _TimeStrToTime
sqlglot/expressions/core.py:2363:        return _TimeStrToTime(this=datetime_literal, zone=tz)
sqlglot/expressions/core.py:2371:        from sqlglot.expressions.temporal import TsOr
…[51 chars elided]…
py:2373:        return _TsOrDsToTime(this=time_literal)
sqlglot/expressions/temporal.py:440:class ParseDatetime(Expression, Func):
sqlglot/expressions/temporal.py:444:class ParseTime(Expression, Func):
sqlglot/expressions/temporal.py:452:class StrToTime(Expression, Func):
sqlglot/expressions/temporal.py:464:class TimeStrToTime(Expression, Func):
sqlglot/expressions/temporal.py:500:class TsOrDsToTime(Expression, Func):
sqlglot/expressions/temporal.py:504:class TsOrDsToTimestamp(Expression, Func):
[tool_use Bash] {"command": "grep -rn \"ParseTime\\|ParseDate\\|PARSE_DATE\\|PARSE_TIME\\|ParseDatetime\\|ParseDatetime\" sqlglot/ tests/ | grep -v \"\\.pyc\" | head -60; sed -n 425,470p sqlglot/expressions/temporal.py", "description": "Search ParseTime/ParseDate usages across sqlglot and tests"}
[tool_result] sqlglot/parsers/clickhouse.py:290:        "PARSEDATETIME": _build_datetime_format(exp.ParseDatetime),
sqlglot/parsers/bigquery.py:224:        "PARSE_DATE": lambda args, dialect: build_formatted_time(exp.StrToDate)(
sqlglot/parsers/bigquery.py:227:        "PARSE_TIME": lambda args, dialect: build_formatted_time(exp.ParseTime)(
sqlglot/parsers/bigquery.py:230:        "PARSE_TIMESTAMP": _build_parse_timestamp,
sqlglot/parsers/bigquery.py:231:        "PARSE_DATETIME": lambda args, dialect: build_for
…[6186 chars elided]…
StrToDate(Expression, Func):
    arg_types = {"this": True, "format": False, "safe": False}


class StrToTime(Expression, Func):
    arg_types = {"this": True, "format": True, "zone": False, "safe": False, "target_type": False}


class StrToUnix(Expression, Func):
    arg_types = {"this": False, "format": False}


class TimeStrToDate(Expression, Func):
    pass


class TimeStrToTime(Expression, Func):
    arg_types = {"this": True, "zone": False}


class TimeStrToUnix(Expression, Func):
    pass
[tool_use Bash] {"command": "grep -n \"StrToDate\\|StrToTime\\|ParseTime\\|def strtodate\\|def strtotime\\|_str_to\\|STRPTIME\\|TIME_TYPE\\|DATE_TYPE\" sqlglot/generators/duckdb.py sqlglot/parsers/duckdb.py sqlglot/dialects/duckdb.py | head -40; sed -n 220,232p sqlglot/parsers/bigquery.py; sed -n 1820,1830p tests/dialects/test_duckdb.py; sed -n 275,290p sqlglot/typing/bigquery.py", "description": "Inspect duckdb generator and bigquery parser for date/time parsing"}
[tool_result] sqlglot/parsers/duckdb.py:179:        "STRPTIME": build_formatted_time(exp.StrToTime),
sqlglot/generators/duckdb.py:1575:        exp.DateStrToDate: datestrtodate_sql,
sqlglot/generators/duckdb.py:1586:            f"CAST(STRPTIME(CAST({self.sql(e, 'this')} AS TEXT), {self.dialect.DATEINT_FORMAT}) AS DATE)"
sqlglot/generators/duckdb.py:1649:            "EPOCH", self.func("STRPTIME", e.this, self.format_time(e))
sqlglot/generators/duckdb.py:1663:        exp.TimeStrToDate: lambda self, e: self.sql(e
…[1697 chars elided]…
2020-01-01' AS DATE) + INTERVAL '-1' DAY",
            read={"mysql": "SELECT DATE '2020-01-01' + INTERVAL -1 DAY"},
        )
            exp.JSONRemove,
            exp.JSONSet,
            exp.JSONStripNulls,
        }
    },
    **{
        expr_type: {"returns": exp.DType.TIME}
        for expr_type in {
            exp.ParseTime,
            exp.TimeFromParts,
            exp.TimeTrunc,
            exp.TsOrDsToTime,
        }
    },
    **{
        expr_type: {"returns": exp.DType.VARCHAR}
[tool_use Bash] {"command": "sed -n 2615,2680p sqlglot/generators/duckdb.py; grep -n \"StrToTime\\|StrToDate\" sqlglot/generators/bigquery.py sqlglot/generators/duckdb.py | head; grep -n \"ParseTime\\|ParseDatetime\" sqlglot/generators/*.py sqlglot/dialects/*.py", "description": "View duckdb strtotime/strtodate generators"}
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
…[2840 chars elided]…
        exp.TimeStrToTime: timestrtotime_sql,
sqlglot/generators/duckdb.py:2619:    def strtotime_sql(self, expression: exp.StrToTime) -> str:
sqlglot/generators/bigquery.py:357:        exp.ParseTime: lambda self, e: self.func("PARSE_TIME", self.format_time(e), e.this),
sqlglot/generators/bigquery.py:358:        exp.ParseDatetime: lambda self, e: self.func("PARSE_DATETIME", self.format_time(e), e.this),
sqlglot/generators/clickhouse.py:380:        exp.ParseDatetime: rename_func("parseDateTime"),
[assistant] The BigQuery parser already builds `exp.ParseTime`, and DuckDB's `strtodate_sql` is the model to follow. I'll add a `parsetime_sql` method to the DuckDB generator, auto-discovered by name, that mirrors it with a `TIME` cast.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-120745-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py", "old_string": "    def tsordstotime_sql(self, expression: exp.TsOrDsToTime) -> str:", "new_string": "    def parsetime_sql(self, expression: exp.ParseTime) -> str:\n        formatted_time = self.format_time(expression)\n        return self.sql(\n            exp.cast(\n                self.func(\"STRPTIME\", expression.this, formatted_time),\n                exp.DataType(this=exp.DType.TIME),\n            )\n        )\n\n    def tsordstotime_sql(self, expression: exp.TsOrDsToTime) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-120745-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[assistant] Next, a test next to the existing `PARSE_DATE` case in the DuckDB tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-120745-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_duckdb.py", "old_string": "            read={\"bigquery\": \"SELECT DATE(PARSE_DATE('%m/%d/%Y', '05/06/2020'))\"},\n        )\n", "new_string": "            read={\"bigquery\": \"SELECT DATE(PARSE_DATE('%m/%d/%Y', '05/06/2020'))\"},\n        )\n        self.validate_all(\n            \"SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)\",\n            read={\"bigquery\": \"SELECT PARSE_TIME('%H:%M', '14:30')\"},\n            write={\"duckdb\": \"SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)\"},\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-120745-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-120745-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_duckdb.py", "old_string": "            read={\"bigquery\": \"SELECT PARSE_TIME('%H:%M', '14:30')\"},\n            write={\"duckdb\": \"SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)\"},\n        )", "new_string": "            read={\"bigquery\": \"SELECT PARSE_TIME('%H:%M', '14:30')\"},\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-120745-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT PARSE_TIME('%H:%M', '14:30')\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_TIME('%I:%M:%S %p', x)\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATE('%m/%d/%Y', x)\\\", read='bigquery', write='duckdb'))\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py tests/dialects/test_bigquery.py tests/dialects/test_dialect.py 2>&1 | tail -15", "description": "Check transpile output and run dialect tests"}
[tool_result] ["SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
["SELECT CAST(STRPTIME(x, '%I:%M:%S %p') AS TIME)"]
["SELECT CAST(STRPTIME(x, '%m/%d/%Y') AS DATE)"]
........................ [ 12%]
.......................................................................................................................................... [ 81%]
...................................... [100%]
200 passed, 4483 subtests passed in 0.99s
[assistant] The transpile output is right and the dialect tests pass. Running the full suite now, as the project harness requires.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; git status --short", "description": "Run full test suite and show git status"}
[tool_result] ........................... [  8%]
............. [  9%]
........................................................................................................................................ [ 21%]
............................................................................................................................................................ [ 35%]
........................................ [ 39%]
..................... [ 41%]
................... [ 42%]
................................
…[319 chars elided]…
............................ [ 74%]
.................................................................................................................................................................. [ 88%]
...............................................................................................................................                                                   [100%]
1112 passed, 18134 subtests passed in 55.25s
 M sqlglot/generators/duckdb.py
 M tests/dialects/test_duckdb.py
[assistant] `PARSE_TIME` now transpiles to DuckDB as `CAST(STRPTIME(...) AS TIME)`, the same way `PARSE_DATE` becomes a `DATE` cast:

```python
sqlglot.transpile("SELECT PARSE_TIME('%H:%M', '14:30')", read="bigquery", write="duckdb")
# ["SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
```

The full suite passes: 1112 tests, 18134 subtests.

**Changes**
- `sqlglot/generators/duckdb.py`: added a `parsetime_sql` method next to `strtodate_sql`. It is auto-discovered by name, so no `TRANSFORMS` entry is needed. The BigQuery format string is converted to DuckDB's format through the usual `format_time` path, so format directives like `%I:%M:%S %p` also come out correctly.
- `tests/dialects/test_duckdb.py`: added a BigQuery→DuckDB case next to the existing `PARSE_DATE` case.

I did not run `make style`/ruff. I did not commit.
