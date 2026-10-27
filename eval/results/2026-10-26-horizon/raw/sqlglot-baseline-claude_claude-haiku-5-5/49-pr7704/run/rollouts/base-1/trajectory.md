# trajectory base-1

final message:
BigQuery `PARSE_DATETIME` now transpiles to DuckDB `STRPTIME` with arguments in DuckDB's order. Your example produces exactly the expected output:

```
["SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')"]
```

The full suite passes (1120 tests, 18167 subtests), and ruff lint and format are clean.

**What changed**

- `sqlglot/generators/duckdb.py`: added a `parsedatetime_sql` method next to `parsetime_sql`. It delegates to the existing `str_to_time_sql` helper, which emits `STRPTIME(value, format)`. The parser already builds `exp.ParseDatetime` from BigQuery's `PARSE_DATETIME`, so only the DuckDB generator was missing a case.
- `tests/dialects/test_bigquery.py`: added a `validate_all` case that reads BigQuery's `PARSE_DATETIME` and writes it for DuckDB.

**Choices I made**

- I fixed it in the DuckDB generator rather than changing the BigQuery parser to build `StrToTime`. Mapping it to `StrToTime` would have made BigQuery-to-BigQuery output switch to `PARSE_TIMESTAMP`, which would be a regression.
- I didn't commit anything. Let me know if you want a commit, and with what message.

## events
[tool_use Bash] {"command": "grep -rn \"PARSE_DATETIME\\|ParseDatetime\\|STRPTIME\\|StrToTime\" sqlglot/dialects/bigquery.py sqlglot/dialects/duckdb.py sqlglot/expressions.py | head -50", "description": "Locate PARSE_DATETIME and STRPTIME handling"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "ls && grep -rn \"PARSE_DATETIME\\|ParseDatetime\\|StrToTime\" sqlglot/dialects/bigquery.py sqlglot/dialects/duckdb.py sqlglot/expressions.py 2>/dev/null | head -50; grep -rn \"PARSE_DATETIME\\|ParseDatetime\" --include=*.py . | grep -v \"^./tests\" | head", "description": "List repo root and grep for PARSE_DATETIME"}
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
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"PARSE_DATETIME\\|ParseDatetime\" sqlglot tests | head -40; echo ---; grep -rn \"StrToTime\\|STRPTIME\" sqlglot/dialects/duckdb.py sqlglot/dialects/bigquery.py | head -30", "description": "Search for PARSE_DATETIME and StrToTime usages"}
[tool_result] sqlglot/parsers/clickhouse.py:290:        "PARSEDATETIME": _build_datetime_format(exp.ParseDatetime),
sqlglot/parsers/bigquery.py:251:        "PARSE_DATETIME": lambda args, dialect: build_formatted_time(exp.ParseDatetime)(
sqlglot/typing/bigquery.py:246:            exp.ParseDatetime,
sqlglot/expressions/temporal.py:440:class ParseDatetime(Expression, Func):
sqlglot/generators/clickhouse.py:380:        exp.ParseDatetime: rename_func("parseDateTime"),
sqlglot/generators/bigquery.py:358:        exp
…[1082 chars elided]…
01-01' AS TIMESTAMP), '%Y-%m-%d'), 'yyyy-MM-dd')))",
tests/dialects/test_hive.py:487:                "presto": "TO_UNIXTIME(COALESCE(TRY(DATE_PARSE(CAST(x AS VARCHAR), '%Y-%m-%d %T')), PARSE_DATETIME(DATE_FORMAT(x, '%Y-%m-%d %T'), 'yyyy-MM-dd HH:mm:ss')))",
tests/fixtures/optimizer/annotate_functions.sql:1109:SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2024-01-15 10:30:00');
tests/fixtures/optimizer/annotate_functions.sql:1449:PARSE_DATETIME('%a %b %e %I:%M:%S %Y', 'Thu Dec 25 07:30:00 2008');
---
[tool_use Bash] {"command": "sed -n 430,460p sqlglot/expressions/temporal.py; echo ---BQ-parser; sed -n 240,260p sqlglot/parsers/bigquery.py; echo ---; grep -rn \"ParseDatetime\\|StrToTime\" sqlglot/generators/duckdb.py sqlglot/parsers/duckdb.py sqlglot/dialects/duckdb.py sqlglot/generators/bigquery.py sqlglot/parsers/bigquery.py 2>/dev/null; grep -n \"class StrToTime\" -A12 sqlglot/expressions/temporal.py; grep -n \"def build_formatted_time\" -A25 sqlglot/dialects/dialect.py", "description": "Inspect expression, parser, and formatted-time helpers"}
[tool_result] class DiToDate(Expression, Func):
    pass


class FromISO8601Timestamp(Expression, Func):
    _sql_names = ["FROM_ISO8601_TIMESTAMP"]


class ParseDatetime(Expression, Func):
    arg_types = {"this": True, "format": False, "zone": False}


class ParseTime(Expression, Func):
    arg_types = {"this": True, "format": True}


class StrToDate(Expression, Func):
    arg_types = {"this": True, "format": False, "safe": False}


class StrToTime(Expression, Func):
    arg_types = {"this": True, "format":
…[3269 chars elided]…
f _builder(args: BuilderArgs, dialect: Dialect) -> E:
1562-        target_dialect = (
1563-            t.cast(Dialect, Dialect[dialect_override])
1564-            if isinstance(dialect_override, str)
1565-            else dialect
1566-        )
1567-
1568-        fmt = seq_get(args, 1)
1569-        if not fmt:
1570-            fmt = target_dialect.TIME_FORMAT if default is True else default or None
1571-
1572-        return exp_class(this=seq_get(args, 0), format=target_dialect.format_time(fmt))
[tool_use Bash] {"command": "sed -n 2620,2650p sqlglot/generators/duckdb.py; echo ---; sed -n 1655,1670p sqlglot/generators/duckdb.py; echo; grep -n \"ParseDatetime\\|PARSE_DATETIME\" -B2 -A8 sqlglot/typing/bigquery.py | head -30; grep -rn \"PARSE_DATETIME\\|ParseDatetime\" tests/dialects/test_duckdb.py | head", "description": "Inspect DuckDB strtotime generator and typing"}
[tool_result]             if length := expression.args.get("length"):
                length = exp.If(this=length < 0, true=exp.Literal.number(0), false=length)

            return self.func("SUBSTRING", expression.this, start, length)

        return self.function_fallback_sql(expression)

    def strtotime_sql(self, expression: exp.StrToTime) -> str:
        # Check if target_type requires TIMESTAMPTZ (for LTZ/TZ variants)
        target_type = expression.args.get("target_type")
        needs_tz = target_ty
…[1359 chars elided]…
eToStr: lambda self, e: self.func("STRFTIME", e.this, self.format_time(e)),
        exp.ToBoolean: _to_boolean_sql,
        exp.ToVariant: lambda self, e: self.sql(

244-        expr_type: {"returns": exp.DType.DATETIME}
245-        for expr_type in {
246:            exp.ParseDatetime,
247-            exp.TimestampFromParts,
248-        }
249-    },
250-    **{
251-        expr_type: {"returns": exp.DType.DOUBLE}
252-        for expr_type in {
253-            exp.Atan2,
254-            exp.Corr,
[tool_use Bash] {"command": "grep -n \"def str_to_time_sql\" -A8 sqlglot/dialects/dialect.py; grep -n \"str_to_time_sql\\|^from\\|^import\" sqlglot/generators/duckdb.py | head -40; grep -n \"    def .*_sql(self, expression: exp.Parse\\|def parse.*_sql\" sqlglot/generators/duckdb.py", "description": "Check str_to_time_sql helper and imports"}
[tool_result] 1795:def str_to_time_sql(self: Generator, expression: exp.Expr) -> str:
1796-    return self.func("STRPTIME", expression.this, self.format_time(expression))
1797-
1798-
1799-def concat_to_dpipe_sql(self: Generator, expression: exp.Concat) -> str:
1800-    return self.sql(reduce(lambda x, y: exp.DPipe(this=x, expression=y), expression.expressions))
1801-
1802-
1803-def concat_ws_to_dpipe_sql(self: Generator, expression: exp.ConcatWs) -> str:
1:from __future__ import annotations
3:from decimal imp
…[154 chars elided]…
lect import (
36:    str_to_time_sql,
40:from sqlglot.generator import unsupported_args
41:from sqlglot.helper import is_date_unit, seq_get
42:from builtins import type as Type
2642:        base_sql = str_to_time_sql(self, expression)
2322:    def parseurl_sql(self, expression: exp.ParseUrl) -> str:
2326:    def parseip_sql(self, expression: exp.ParseIp) -> str:
2662:    def parsetime_sql(self, expression: exp.ParseTime) -> str:
2709:    def parsejson_sql(self, expression: exp.ParseJSON) -> str:
[tool_use Bash] {"command": "sed -n 2660,2672p sqlglot/generators/duckdb.py", "description": "View existing parsetime_sql for pattern"}
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
[assistant] Existing `parsetime_sql` shows the pattern. I'll reproduce the bug first, then add a DuckDB `parsedatetime_sql` alongside it.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\\\", read='bigquery', write='bigquery'))\n\"", "description": "Reproduce the transpile bug"}
[tool_result] ["SELECT PARSE_DATETIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')"]
["SELECT PARSE_DATETIME('%F %T', '2023-01-15 14:30:00')"]
[assistant] Reproduced: DuckDB gets the verbatim `PARSE_DATETIME` call with arguments in BigQuery order. Adding the DuckDB generator method:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-183154-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py", "old_string": "    def tsordstotime_sql(self, expression: exp.TsOrDsToTime) -> str:", "new_string": "    def parsedatetime_sql(self, expression: exp.ParseDatetime) -> str:\n        return str_to_time_sql(self, expression)\n\n    def tsordstotime_sql(self, expression: exp.TsOrDsToTime) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-183154-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\\\", read='bigquery', write='bigquery'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATETIME('%Y-%m-%d', x)\\\", read='bigquery', write='duckdb'))\n\"", "description": "Verify the fix on the reproduction cases"}
[tool_result] ["SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')"]
["SELECT PARSE_DATETIME('%F %T', '2023-01-15 14:30:00')"]
["SELECT STRPTIME(x, '%Y-%m-%d')"]
[assistant] The output now matches the expected result. Next I'll add a regression test next to the existing BigQuery `PARSE_DATETIME` test.
[tool_use Bash] {"command": "sed -n 1970,1990p tests/dialects/test_bigquery.py", "description": "View existing PARSE_DATETIME test context"}
[tool_result]             write={
                "bigquery": "SELECT CAST(col AS STRUCT<fld1 STRUCT<fld2 INT64>>).fld1.fld2",
                "snowflake": "SELECT CAST(col AS OBJECT(fld1 OBJECT(fld2 INT))):fld1.fld2",
            },
        )
        self.validate_identity(
            "SELECT PARSE_DATETIME('%a %b %e %I:%M:%S %Y', 'Thu Dec 25 07:30:00 2008')"
        )
        self.validate_identity("FORMAT_TIME('%R', CAST('15:30:00' AS TIME))")
        self.validate_identity("PARSE_TIME('%I:%M:%S', '07:30:
…[156 chars elided]…
S_TO_STRING([65, 255])")
        self.validate_identity("APPROX_TOP_COUNT(col, 2)")
        self.validate_identity("ARPOX_TOP_SUM(col, 1.5, 2)")
        self.validate_identity("SAFE_CONVERT_BYTES_TO_STRING(b'\xc2')")
        self.validate_identity("FROM_HEX('foo')")
        self.validate_identity("TO_CODE_POINTS('foo')")
        self.validate_identity("CODE_POINTS_TO_BYTES([65, 98])")
        self.validate_identity("PARSE_BIGNUMERIC('1.2')")
        self.validate_identity("PARSE_NUMERIC('1.2')")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-183154-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_bigquery.py", "old_string": "        self.validate_identity(\n            \"SELECT PARSE_DATETIME('%a %b %e %I:%M:%S %Y', 'Thu Dec 25 07:30:00 2008')\"\n        )\n        self.validate_identity(\"FORMAT_TIME('%R', CAST('15:30:00' AS 
…[607 chars elided]…
15 14:30:00', '%Y-%m-%d %H:%M:%S')\",\n            read={\n                \"bigquery\": \"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\",\n            },\n            write={\n                \"duckdb\": \"SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')\",\n            },\n        )\n        self.validate_identity(\"FORMAT_TIME('%R', CAST('15:30:00' AS TIME))\")"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-183154-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[assistant] The first block I added is a DuckDB-to-DuckDB round trip that doesn't test this fix, so I'll remove it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-183154-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_bigquery.py", "old_string": "        self.validate_all(\n            \"SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')\",\n            read={\n                \"duckdb\": \"SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')\",\n            },\n            write={\n                \"duckdb\": \"SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')\",\n            },\n        )\n        self.validate_all(", "new_string": "        self.validate_all("}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-183154-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[assistant] Now the project's test command, as specified in the repo's harness notes:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/ 2>&1 | tail -30", "description": "Run full pytest suite", "timeout": 900000}
[tool_result] .................................. [  3%]
...................................................................... [  9%]
............................................. [ 13%]
.................................................................... [ 19%]
..................... [ 21%]
.................................................................................. [ 28%]
........................................................................................... [ 36%]
.................................
…[1077 chars elided]…
 %T', '2023-01-15 14:30:00')" != "SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')"
E   - SELECT PARSE_DATETIME('%F %T', '2023-01-15 14:30:00')
E   + SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')
=========================== short test summary info ============================
SUBFAILED[bigquery -> SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')] tests/dialects/test_bigquery.py::TestBigQuery::test_bigquery
1 failed, 1120 passed, 18167 subtests passed in 51.80s
[assistant] The failure is in how I wrote the test, not the fix. `validate_all`'s `read` argument compares against the BigQuery-side output, so the input should go through `write`. I'll restructure it that way.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-183154-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_bigquery.py", "old_string": "        self.validate_all(\n            \"SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')\",\n            read={\n                \"bigquery\": \"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '202
…[51 chars elided]…
write={\n                \"duckdb\": \"SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')\",\n            },\n        )", "new_string": "        self.validate_all(\n            \"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\",\n            write={\n                \"duckdb\": \"SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')\",\n            },\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-183154-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/ 2>&1 | tail -4; <work>/env-sqlglot/bin/python -m ruff check sq
…[9 chars elided]…
erators/duckdb.py tests/dialects/test_bigquery.py 2>&1 | tail -2; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generators/duckdb.py tests/dialects/test_bigquery.py 2>&1 | tail -2", "description": "Rerun full test suite and lint/format checks", "timeout": 900000}
[tool_result] .................................. [ 94%]
................. [ 95%]
................................................          [100%]
1120 passed, 18167 subtests passed in 67.12s (0:01:07)
All checks passed!
2 files already formatted
[assistant] BigQuery `PARSE_DATETIME` now transpiles to DuckDB `STRPTIME` with arguments in DuckDB's order. Your example produces exactly the expected output:

```
["SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')"]
```

The full suite passes (1120 tests, 18167 subtests), and ruff lint and format are clean.

**What changed**

- `sqlglot/generators/duckdb.py`: added a `parsedatetime_sql` method next to `parsetime_sql`. It delegates to the existing `str_to_time_sql` helper, which emits `STRPTIME(value, format)`. The parser already builds `exp.ParseDatetime` from BigQuery's `PARSE_DATETIME`, so only the DuckDB generator was missing a case.
- `tests/dialects/test_bigquery.py`: added a `validate_all` case that reads BigQuery's `PARSE_DATETIME` and writes it for DuckDB.

**Choices I made**

- I fixed it in the DuckDB generator rather than changing the BigQuery parser to build `StrToTime`. Mapping it to `StrToTime` would have made BigQuery-to-BigQuery output switch to `PARSE_TIMESTAMP`, which would be a regression.
- I didn't commit anything. Let me know if you want a commit, and with what message.
