# trajectory base-1

final message:
`PARSE_DATETIME` now transpiles to DuckDB as `STRPTIME`. Your example produces `SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')`, and the full suite passes (1120 passed).

**The cause:** BigQuery parses `PARSE_DATETIME` into `exp.ParseDatetime`, but the DuckDB generator had no handler for that node, so it fell back to emitting the original function name with its arguments unchanged.

**The fix:**
- `sqlglot/generators/duckdb.py`: added `parsedatetime_sql`, which emits `STRPTIME(this, format)`. I modeled it on the existing `parsetime_sql` but left out the `CAST(... AS TIME)` wrapper, since your expected output has no cast.
- `tests/dialects/test_duckdb.py`: added a `validate_all` case that reads `PARSE_DATETIME('%Y-%m-%d %H:%M:%S', x)` from BigQuery and expects `STRPTIME(x, '%Y-%m-%d %H:%M:%S')` for DuckDB.

Nothing is committed. The changes are in the working tree.

## events
[tool_use Bash] {"command": "git status --short && grep -rn \"PARSE_DATETIME\\|ParseDatetime\\|PARSE_TIMESTAMP\\|ParseTimestamp\\|StrToTime\" sqlglot/dialects/bigquery.py sqlglot/dialects/duckdb.py sqlglot/expressions.py | head -50", "description": "Check repo state and find parse-related mappings"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "git status --short; git log --oneline -1; grep -rn \"PARSE_DATETIME\\|ParseDatetime\\|ParseTimestamp\\|PARSE_TIMESTAMP\" --include=*.py sqlglot tests | head -50", "description": "Find PARSE_DATETIME references in sources and tests"}
[tool_result] cbaa17499 lithify: probe base
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"PARSE_DATETIME\\|ParseDatetime\\|PARSE_TIMESTAMP\\|ParseTimestamp\" sqlglot tests | head -50", "description": "Find PARSE_DATETIME references in sources and tests"}
[tool_result] sqlglot/parsers/bigquery.py:250:        "PARSE_TIMESTAMP": _build_parse_timestamp,
sqlglot/parsers/bigquery.py:251:        "PARSE_DATETIME": lambda args, dialect: build_formatted_time(exp.ParseDatetime)(
sqlglot/parsers/clickhouse.py:290:        "PARSEDATETIME": _build_datetime_format(exp.ParseDatetime),
sqlglot/typing/bigquery.py:246:            exp.ParseDatetime,
sqlglot/expressions/temporal.py:440:class ParseDatetime(Expression, Func):
sqlglot/generators/clickhouse.py:380:        exp.ParseDat
…[3422 chars elided]…
, 'yyyy-MM-dd HH:mm:ss')))",
tests/fixtures/optimizer/annotate_functions.sql:1109:SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2024-01-15 10:30:00');
tests/fixtures/optimizer/annotate_functions.sql:1117:SAFE.PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', '2024-01-15 10:30:00');
tests/fixtures/optimizer/annotate_functions.sql:1121:PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', '2024-01-15 10:30:00');
tests/fixtures/optimizer/annotate_functions.sql:1449:PARSE_DATETIME('%a %b %e %I:%M:%S %Y', 'Thu Dec 25 07:30:00 2008');
[tool_use Bash] {"command": "sed -n 240,260p sqlglot/parsers/bigquery.py; grep -n \"_build_parse_timestamp\" -A12 sqlglot/parsers/bigquery.py | head -30; sed -n 430,450p sqlglot/expressions/temporal.py; grep -n \"StrToTime\\|ParseDatetime\\|TimeToStr\\|TsOrDsToDate\\|PARSE_TIMESTAMP\\|Timestamp\" sqlglot/generators/duckdb.py sqlglot/parsers/duckdb.py | head -40; sed -n 1900,1935p tests/dialects/test_duckdb.py", "description": "Inspect BigQuery parser, ParseDatetime def, DuckDB mappings"}
[tool_result]             this=seq_get(args, 0), form=seq_get(args, 1), is_casefold=True
        ),
        "OCTET_LENGTH": exp.ByteLength.from_arg_list,
        "TO_HEX": _build_to_hex,
        "PARSE_DATE": lambda args, dialect: build_formatted_time(exp.StrToDate)(
            [seq_get(args, 1), seq_get(args, 0)], dialect
        ),
        "PARSE_TIME": lambda args, dialect: build_formatted_time(exp.ParseTime)(
            [seq_get(args, 1), seq_get(args, 0)], dialect
        ),
        "PARSE_TIMESTAMP": 
…[5119 chars elided]…
self.validate_all(
            "STRPTIME(x, '%-m/%-d/%y %-I:%M %p')",
            write={
                "bigquery": "PARSE_TIMESTAMP('%-m/%e/%y %-I:%M %p', x)",
                "duckdb": "STRPTIME(x, '%-m/%-d/%y %-I:%M %p')",
                "presto": "DATE_PARSE(x, '%c/%e/%y %l:%i %p')",
                "hive": "CAST(FROM_UNIXTIME(UNIX_TIMESTAMP(x, 'M/d/yy h:mm a')) AS TIMESTAMP)",
                "spark": "TO_TIMESTAMP(x, 'M/d/yy h:mm a')",
            },
        )
        self.validate_all(
[tool_use Bash] {"command": "sed -n 2620,2650p sqlglot/generators/duckdb.py; grep -n \"def parsetime\\|def strtotime\\|def parse\" sqlglot/generators/*.py | head; sed -n 1,30p sqlglot/generators/duckdb.py | grep -n import", "description": "Read DuckDB strtotime generator logic"}
[tool_result]             if length := expression.args.get("length"):
                length = exp.If(this=length < 0, true=exp.Literal.number(0), false=length)

            return self.func("SUBSTRING", expression.this, start, length)

        return self.function_fallback_sql(expression)

    def strtotime_sql(self, expression: exp.StrToTime) -> str:
        # Check if target_type requires TIMESTAMPTZ (for LTZ/TZ variants)
        target_type = expression.args.get("target_type")
        needs_tz = target_ty
…[1002 chars elided]…
generators/duckdb.py:2662:    def parsetime_sql(self, expression: exp.ParseTime) -> str:
sqlglot/generators/duckdb.py:2709:    def parsejson_sql(self, expression: exp.ParseJSON) -> str:
sqlglot/generators/snowflake.py:944:    def strtotime_sql(self, expression: exp.StrToTime):
1:from __future__ import annotations
3:from decimal import Decimal
4:from itertools import groupby
5:import re
6:import typing as t
8:from sqlglot import exp, generator, transforms
10:from sqlglot.dialects.dialect import (
[tool_use Bash] {"command": "sed -n 2660,2680p sqlglot/generators/duckdb.py; grep -n \"ParseTime\" sqlglot/generators/duckdb.py sqlglot/parsers/duckdb.py tests/dialects/test_duckdb.py | head", "description": "Read DuckDB parsetime generator as pattern"}
[tool_result]         )

    def parsetime_sql(self, expression: exp.ParseTime) -> str:
        formatted_time = self.format_time(expression)
        return self.sql(
            exp.cast(
                self.func("STRPTIME", expression.this, formatted_time),
                exp.DataType(this=exp.DType.TIME),
            )
        )

    def tsordstotime_sql(self, expression: exp.TsOrDsToTime) -> str:
        this = expression.this
        time_format = self.format_time(expression)
        safe = expression.args.get("safe")
        time_type = exp.DataType.from_str("TIME", dialect="duckdb")
        cast_expr = exp.TryCast if safe else exp.Cast

        if time_format:
            func_name = "TRY_STRPTIME" if safe else "STRPTIME"
            strptime = exp.Anonymous(this=func_name, expressions=[this, time_format])
sqlglot/generators/duckdb.py:2662:    def parsetime_sql(self, expression: exp.ParseTime) -> str:
[tool_use Bash] {"command": "sed -n 1965,1990p tests/dialects/test_bigquery.py", "description": "View existing PARSE_DATETIME test in BigQuery tests"}
[tool_result]         self.validate_identity("ARRAY_LAST(['a', 'b'])")
        self.validate_identity("JSON_TYPE(PARSE_JSON('1'))")

        self.validate_all(
            "SELECT CAST(col AS STRUCT<fld1 STRUCT<fld2 INT>>).fld1.fld2",
            write={
                "bigquery": "SELECT CAST(col AS STRUCT<fld1 STRUCT<fld2 INT64>>).fld1.fld2",
                "snowflake": "SELECT CAST(col AS OBJECT(fld1 OBJECT(fld2 INT))):fld1.fld2",
            },
        )
        self.validate_identity(
            "SELE
…[377 chars elided]…
S_TO_STRING([65, 255])")
        self.validate_identity("APPROX_TOP_COUNT(col, 2)")
        self.validate_identity("ARPOX_TOP_SUM(col, 1.5, 2)")
        self.validate_identity("SAFE_CONVERT_BYTES_TO_STRING(b'\xc2')")
        self.validate_identity("FROM_HEX('foo')")
        self.validate_identity("TO_CODE_POINTS('foo')")
        self.validate_identity("CODE_POINTS_TO_BYTES([65, 98])")
        self.validate_identity("PARSE_BIGNUMERIC('1.2')")
        self.validate_identity("PARSE_NUMERIC('1.2')")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-140148-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py", "old_string": "    def tsordstotime_sql(self, expression: exp.TsOrDsToTime) -> str:", "new_string": "    def parsedatetime_sql(self, expression: exp.ParseDatetime) -> str:\n        return self.func(\"STRPTIME\", expression.this, self.format_time(expression))\n\n    def tsordstotime_sql(self, expression: exp.TsOrDsToTime) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-140148-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-140148-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_all(\n            \"TO_TIMESTAMP(x)\",\n            write={\n                \"bigquery\": \"TIMESTAMP_SECONDS(x)\",", "new_string": "        self.validate_all(\n            \"STRPTIME(
…[69 chars elided]…
query\": \"PARSE_DATETIME('%Y-%m-%d %H:%M:%S', x)\",\n            },\n            write={\n                \"bigquery\": \"PARSE_DATETIME('%Y-%m-%d %H:%M:%S', x)\",\n                \"duckdb\": \"STRPTIME(x, '%Y-%m-%d %H:%M:%S')\",\n            },\n        )\n        self.validate_all(\n            \"TO_TIMESTAMP(x)\",\n            write={\n                \"bigquery\": \"TIMESTAMP_SECONDS(x)\","}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-140148-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-140148-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_all(\n            \"STRPTIME(x, '%Y-%m-%d %H:%M:%S')\",\n            read={\n                \"bigquery\": \"PARSE_DATETIME('%Y-%m-%d %H:%M:%S', x)\",\n            },\n            write={\n                \"bigquery\": \"PARSE_DATETIME('%Y-%m-%d %H:%M:%S', x)\",\n                \"duckdb\": \"STRPTIME(x, '%Y-%m-%d %H:%M:%S')\",\n            },\n        )", "new_string": "        self.validate_all(\n            \"STRPTIME(x, '%Y-%m-%d %H:%M:%S')\",\n            read={\n                \"bigquery\": \"PARSE_DATETIME('%Y-%m-%d %H:%M:%S', x)\",\n            },\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-140148-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] Now I'll verify the exact example from the report and run the test suite with the project's interpreter.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATETIME('%Y-%m-%d', x)\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATETIME('%a %b %e %I:%M:%S %Y', d)\\\", read='bigquery', write='duckdb'))\n\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py tests/dialects/test_bigquery.py tests/test_transpile.py tests/dialects/test_dialect.py 2>&1 | tail -15", "description": "Verify example output and run relevant dialect tests"}
[tool_result] ["SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')"]
["SELECT STRPTIME(x, '%Y-%m-%d')"]
["SELECT STRPTIME(d, '%a %b %-d %I:%M:%S %Y')"]
........................ [ 10%]
..................................................................................................... [ 54%]
....................... [ 64%]
....................................... [ 82%]
.........................................                    [100%]
228 passed, 5513 subtests passed in 1.25s
[assistant] The target output matches. Running the full project suite now, since the check command is the whole test run.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; git status --short", "description": "Run full project test suite and show changed files"}
[tool_result] ................................................................................................................................................... [ 64%]
......................................................................................................................................................................................................................... [ 83%]
....................... [ 85%]
........................................................... [ 91%]
.................................. [ 94%]
................. [ 95%]
................................................          [100%]
1120 passed, 18167 subtests passed in 50.26s
 M sqlglot/generators/duckdb.py
 M tests/dialects/test_duckdb.py
[assistant] `PARSE_DATETIME` now transpiles to DuckDB as `STRPTIME`. Your example produces `SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')`, and the full suite passes (1120 passed).

**The cause:** BigQuery parses `PARSE_DATETIME` into `exp.ParseDatetime`, but the DuckDB generator had no handler for that node, so it fell back to emitting the original function name with its arguments unchanged.

**The fix:**
- `sqlglot/generators/duckdb.py`: added `parsedatetime_sql`, which emits `STRPTIME(this, format)`. I modeled it on the existing `parsetime_sql` but left out the `CAST(... AS TIME)` wrapper, since your expected output has no cast.
- `tests/dialects/test_duckdb.py`: added a `validate_all` case that reads `PARSE_DATETIME('%Y-%m-%d %H:%M:%S', x)` from BigQuery and expects `STRPTIME(x, '%Y-%m-%d %H:%M:%S')` for DuckDB.

Nothing is committed. The changes are in the working tree.
