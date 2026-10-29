# trajectory base-1

final message:
`PARSE_DATETIME` now transpiles to DuckDB as `STRPTIME`, with the format string translated, and the full suite passes (1120 tests).

```
["SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')"]
```

**Change**
- `sqlglot/generators/duckdb.py`: added `parsedatetime_sql`, which calls the existing `str_to_time_sql` helper. The DuckDB generator had no handler for `exp.ParseDatetime`, so it fell back to emitting `PARSE_DATETIME` verbatim. The method is auto-discovered by name, following the same pattern as the `PARSE_TIME` fix. Unlike `PARSE_TIME`, there is no `CAST`, because the expected output is a plain `STRPTIME`.
- `tests/dialects/test_duckdb.py`: added a BigQuery → DuckDB case next to the existing `PARSE_TIME` cases.

**Not fixed: the `SAFE.` variant.** `SAFE.PARSE_DATETIME(...)` now emits `SAFE.STRPTIME(...)`, which DuckDB doesn't accept. Before this change it emitted `SAFE.PARSE_DATETIME(...)`, which was also invalid. The correct DuckDB output would be `TRY_STRPTIME`, which the DuckDB generator already uses for `StrToTime` with `safe`. Fixing it means handling the `SafeFunc` wrapper for `ParseDatetime`, which is a slightly larger change. I left it out to keep this change to the case you reported. I can take it on as a follow-up if you want.

I did not commit anything.

## events
[tool_use Bash] {"command": "grep -rn -i \"parse_datetime\\|ParseDatetime\\|PARSE_DATETIME\\|StrToTime\\|STRPTIME\" sqlglot/dialects/bigquery.py sqlglot/dialects/duckdb.py sqlglot/expressions.py | head -50", "description": "Find PARSE_DATETIME and STRPTIME references"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "grep -rn -i \"parse_datetime\\|ParseDatetime\\|StrToTime\\|STRPTIME\" sqlglot/dialects/bigquery.py sqlglot/dialects/duckdb.py sqlglot/dialects/dialect.py sqlglot/expressions/*.py 2>/dev/null | head -50; ls sqlglot | head -80", "description": "Search for datetime parse mappings in dialects"}
[tool_result] sqlglot/dialects/dialect.py:1724:def timestrtotime_sql(
sqlglot/dialects/dialect.py:1726:    expression: exp.TimeStrToTime,
sqlglot/dialects/dialect.py:1796:    return self.func("STRPTIME", expression.this, self.format_time(expression))
sqlglot/expressions/core.py:2385:        from sqlglot.expressions.temporal import TimeStrToTime as _TimeStrToTime
sqlglot/expressions/core.py:2387:        return _TimeStrToTime(this=datetime_literal, zone=tz)
sqlglot/expressions/temporal.py:440:class ParseDatetime(Expression, Func):
sqlglot/expressions/temporal.py:452:class StrToTime(Expression, Func):
sqlglot/expressions/temporal.py:464:class TimeStrToTime(Expression, Func):
__init__.py
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
[tool_use Bash] {"command": "sed -n 430,465p sqlglot/expressions/temporal.py; grep -rn \"ParseDatetime\\|PARSE_DATETIME\" sqlglot/ tests/ | head -30; sed -n 1785,1800p sqlglot/dialects/dialect.py", "description": "Inspect ParseDatetime and related references"}
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
…[2616 chars elided]…
OM " if trim_type or remove_chars else ""
    collation = f" COLLATE {collation}" if collation else ""
    return f"TRIM({trim_type}{remove_chars}{from_part}{target}{collation})"


def str_to_time_sql(self: Generator, expression: exp.Expr) -> str:
    return self.func("STRPTIME", expression.this, self.format_time(expression))


def concat_to_dpipe_sql(self: Generator, expression: exp.Concat) -> str:
    return self.sql(reduce(lambda x, y: exp.DPipe(this=x, expression=y), expression.expressions))
[tool_use Bash] {"command": "sed -n 245,260p sqlglot/parsers/bigquery.py; grep -n \"StrToTime\\|str_to_time\\|ParseDatetime\\|TimeToStr\\|TRANSFORMS = {\" sqlglot/generators/duckdb.py; grep -n \"def format_time\" -A12 sqlglot/generator.py | head -30; grep -n \"def build_formatted_time\" -A30 sqlglot/dialects/dialect.py | head -50", "description": "Inspect BigQuery parser, DuckDB generator, format_time"}
[tool_result]             [seq_get(args, 1), seq_get(args, 0)], dialect
        ),
        "PARSE_TIME": lambda args, dialect: build_formatted_time(exp.ParseTime)(
            [seq_get(args, 1), seq_get(args, 0)], dialect
        ),
        "PARSE_TIMESTAMP": _build_parse_timestamp,
        "PARSE_DATETIME": lambda args, dialect: build_formatted_time(exp.ParseDatetime)(
            [seq_get(args, 1), seq_get(args, 0)], dialect
        ),
        "REGEXP_CONTAINS": exp.RegexpLike.from_arg_list,
        "REGEXP
…[1784 chars elided]…
  target_dialect = (
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
1573-
1574-    return _builder
1575-
1576-
1577-def time_format(
[tool_use Bash] {"command": "sed -n 2620,2650p sqlglot/generators/duckdb.py; sed -n 1655,1672p sqlglot/generators/duckdb.py; sed -n 30,40p sqlglot/generators/duckdb.py; grep -n \"ParseTime\\|ParseDatetime\\|PARSE_\" sqlglot/generators/duckdb.py sqlglot/parsers/duckdb.py", "description": "Inspect DuckDB strtotime generation"}
[tool_result]             if length := expression.args.get("length"):
                length = exp.If(this=length < 0, true=exp.Literal.number(0), false=length)

            return self.func("SUBSTRING", expression.this, start, length)

        return self.function_fallback_sql(expression)

    def strtotime_sql(self, expression: exp.StrToTime) -> str:
        # Check if target_type requires TIMESTAMPTZ (for LTZ/TZ variants)
        target_type = expression.args.get("target_type")
        needs_tz = target_ty
…[1654 chars elided]…

    no_timestamp_sql,
    rename_func,
    remove_from_array_using_filter,
    strposition_sql,
    str_to_time_sql,
    timestrtotime_sql,
    unit_to_str,
)
from sqlglot.generator import unsupported_args
sqlglot/generators/duckdb.py:2323:        self.unsupported("PARSE_URL is not supported in DuckDB")
sqlglot/generators/duckdb.py:2327:        self.unsupported("PARSE_IP is not supported in DuckDB")
sqlglot/generators/duckdb.py:2662:    def parsetime_sql(self, expression: exp.ParseTime) -> str:
[tool_use Bash] {"command": "sed -n 2655,2680p sqlglot/generators/duckdb.py; grep -n \"ParseTime\" sqlglot/generators/bigquery.py sqlglot/parsers/bigquery.py; git log --oneline -3 -- sqlglot/generators/duckdb.py | cat", "description": "View DuckDB parsetime_sql implementation"}
[tool_result]         return self.sql(
            exp.cast(
                self.func(function_name, expression.this, formatted_time),
                exp.DataType(this=exp.DType.DATE),
            )
        )

    def parsetime_sql(self, expression: exp.ParseTime) -> str:
        formatted_time = self.format_time(expression)
        return self.sql(
            exp.cast(
                self.func("STRPTIME", expression.this, formatted_time),
                exp.DataType(this=exp.DType.TIME),
            )
 
…[509 chars elided]…
arsers/bigquery.py:247:        "PARSE_TIME": lambda args, dialect: build_formatted_time(exp.ParseTime)(
sqlglot/generators/bigquery.py:357:        exp.ParseTime: lambda self, e: self.func("PARSE_TIME", self.format_time(e), e.this),
6ae53c2e8 feat(duckdb): Add transpilation support for TRY_CAST date-format (#7707)
e23a9eece feat(duckdb): Add transpilation support for BOOLEAN and TEXT cases of TRY_CAST function (#7681)
a7e21a49f fix(duckdb): add transpilation support for bq func PARSE_TIME (#7673)
[tool_use Bash] {"command": "git show a7e21a49f --stat | cat && git show a7e21a49f -- tests | head -60; sed -n 1970,1985p tests/dialects/test_bigquery.py", "description": "Review prior PARSE_TIME fix for conventions"}
[tool_result] commit a7e21a49f6c83e2917b9e02fc39c9e4237f4850a
Author: William Goode <95141298+william-goode@users.noreply.github.com>
Date:   Mon May 25 11:08:41 2026 -0400

    fix(duckdb): add transpilation support for bq func PARSE_TIME (#7673)
    
    * fix: add ParseTime transpilation for BigQuery to DuckDB
    
    BigQuery's PARSE_TIME is parsed into exp.ParseTime but DuckDB's
    generator has no handler, so it falls through to function_fallback_sql
    and emits PARSE_TIME(...) verbatim, which DuckD
…[2675 chars elided]…
.validate_identity("FORMAT_TIME('%R', CAST('15:30:00' AS TIME))")
        self.validate_identity("PARSE_TIME('%I:%M:%S', '07:30:00')")
        self.validate_identity("BYTE_LENGTH('foo')")
        self.validate_identity("BYTE_LENGTH(b'foo')")
        self.validate_identity("CODE_POINTS_TO_STRING([65, 255])")
        self.validate_identity("APPROX_TOP_COUNT(col, 2)")
        self.validate_identity("ARPOX_TOP_SUM(col, 1.5, 2)")
        self.validate_identity("SAFE_CONVERT_BYTES_TO_STRING(b'\xc2')")
[assistant] The fix follows the same pattern as the `PARSE_TIME` handler already in the DuckDB generator. I'll add a `parsedatetime_sql` method that reuses the existing `str_to_time_sql` helper, which emits `STRPTIME` with the format translated.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-102308-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py", "old_string": "    def tsordstotime_sql(self, expression: exp.TsOrDsToTime) -> str:", "new_string": "    def parsedatetime_sql(self, expression: exp.ParseDatetime) -> str:\n        return str_to_time_sql(self, expression)\n\n    def tsordstotime_sql(self, expression: exp.TsOrDsToTime) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-102308-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[assistant] Next, I'll add a DuckDB test next to the existing `PARSE_TIME` cases, then check the output.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-102308-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_all(\n            \"SELECT CAST(STRPTIME('15:30:00.123456', '%H:%M:%S.%f') AS TIME)\",\n            read={\"bigquery\": \"SELECT PARSE_TIME('%H:%M:%E6S', '15:30:00.123456')\"},\n       
…[53 chars elided]…
       \"SELECT CAST(STRPTIME('15:30:00.123456', '%H:%M:%S.%f') AS TIME)\",\n            read={\"bigquery\": \"SELECT PARSE_TIME('%H:%M:%E6S', '15:30:00.123456')\"},\n        )\n        self.validate_all(\n            \"SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')\",\n            read={\"bigquery\": \"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\"},\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-102308-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT SAFE.PARSE_DATETIME('%F %T', '2024-01-15 10:30:00')\\\", read='bigquery', write='duckdb'))\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py tests/dialects/test_bigquery.py 2>&1 | tail -15", "description": "Verify transpile output and run DuckDB/BigQuery tests"}
[tool_result] ["SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')"]
["SELECT SAFE.STRPTIME('2024-01-15 10:30:00', '%Y-%m-%d %H:%M:%S')"]
........................ [ 23%]
..............................................................................                                      [100%]
102 passed, 1661 subtests passed in 0.58s
[assistant] The basic case now matches the expected output, and the DuckDB and BigQuery test files pass. The `SAFE.` variant still emits `SAFE.STRPTIME`, which DuckDB doesn't accept. Before I decide anything about it, I'll run the full suite the project harness specifies.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; git stash list | head -0; git status --short", "description": "Run full test suite and check git status"}
[tool_result] ........................................................... [ 91%]
.................................. [ 94%]
................. [ 95%]
................................................          [100%]
1120 passed, 18167 subtests passed in 50.46s
head: illegal line count -- 0
 M sqlglot/generators/duckdb.py
 M tests/dialects/test_duckdb.py
[assistant] `PARSE_DATETIME` now transpiles to DuckDB as `STRPTIME`, with the format string translated, and the full suite passes (1120 tests).

```
["SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')"]
```

**Change**
- `sqlglot/generators/duckdb.py`: added `parsedatetime_sql`, which calls the existing `str_to_time_sql` helper. The DuckDB generator had no handler for `exp.ParseDatetime`, so it fell back to emitting `PARSE_DATETIME` verbatim. The method is auto-discovered by name, following the same pattern as the `PARSE_TIME` fix. Unlike `PARSE_TIME`, there is no `CAST`, because the expected ou
…[98 chars elided]…
 to the existing `PARSE_TIME` cases.

**Not fixed: the `SAFE.` variant.** `SAFE.PARSE_DATETIME(...)` now emits `SAFE.STRPTIME(...)`, which DuckDB doesn't accept. Before this change it emitted `SAFE.PARSE_DATETIME(...)`, which was also invalid. The correct DuckDB output would be `TRY_STRPTIME`, which the DuckDB generator already uses for `StrToTime` with `safe`. Fixing it means handling the `SafeFunc` wrapper for `ParseDatetime`, which is a slightly larger change. I left it out to keep this change to the case you reported. I can take it on as a follow-up if you want.

I did not commit anything.
