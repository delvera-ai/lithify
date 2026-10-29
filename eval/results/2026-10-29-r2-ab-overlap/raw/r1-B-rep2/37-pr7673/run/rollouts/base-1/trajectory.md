# trajectory base-1

final message:
BigQuery `PARSE_TIME` now transpiles to DuckDB as `CAST(STRPTIME(...) AS TIME)`, the same pattern `PARSE_DATE` uses for `DATE`:

```python
sqlglot.transpile("SELECT PARSE_TIME('%H:%M', '14:30')", read="bigquery", write="duckdb")
# ["SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
```

I ran that output in DuckDB 1.5.6 and it returns `time(14, 30)`. A 12-hour example with `%I:%M:%S %p` also returns the right value.

The change is in two files:
- **`sqlglot/generators/duckdb.py`**: added `parsetime_sql`, next to `strtodate_sql`. It's auto-discovered from the `ParseTime` expression name, so no `TRANSFORMS` entry was needed.
- **`tests/dialects/test_bigquery.py`**: added a `validate_all` case beside the existing `PARSE_DATE` cases, asserting the DuckDB output.

The full suite passes: 1112 tests, 50 seconds. I haven't committed anything.

**Not fixed:** `SAFE.PARSE_TIME(...)` becomes `SAFE.CAST(STRPTIME(...) AS TIME)`, which DuckDB rejects. `SAFE.PARSE_DATE` already does this today, so it's a general `SafeFunc` generation issue rather than something specific to this change. Fixing it would mean changing how safe-wrapped functions are generated for DuckDB, which goes beyond this task.

## events
[tool_use Bash] {"command": "grep -rn \"PARSE_DATE\\|ParseDate\\|PARSE_TIME\\|ParseTime\\|StrToTime\\|StrToDate\" sqlglot/dialects/bigquery.py sqlglot/dialects/duckdb.py sqlglot/expressions.py sqlglot/expressions/*.py 2>/dev/null | head -50; ls sqlglot | head -80", "description": "Find PARSE_DATE/PARSE_TIME handling across dialects"}
[tool_result] sqlglot/expressions/core.py:2361:        from sqlglot.expressions.temporal import TimeStrToTime as _TimeStrToTime
sqlglot/expressions/core.py:2363:        return _TimeStrToTime(this=datetime_literal, zone=tz)
sqlglot/expressions/core.py:2366:        from sqlglot.expressions.temporal import DateStrToDate as _DateStrToDate
sqlglot/expressions/core.py:2368:        return _DateStrToDate(this=date_literal)
sqlglot/expressions/temporal.py:420:class DateStrToDate(Expression, Func):
sqlglot/expressions/
…[338 chars elided]…
nc):
sqlglot/expressions/temporal.py:464:class TimeStrToTime(Expression, Func):
dialects/
executor/
expressions/
generators/
optimizer/
parsers/
typing/
__init__.py  5.7K
__main__.py  2.1K
_typing.py  1.8K
_version.py  91B
diff.py  16.3K
errors.py  4.7K
generator.py  250.5K
helper.py  11.7K
jsonpath.py  7.9K
lineage.py  20.3K
parser.py  370.9K
planner.py  14.5K
py.typed  0B
schema.py  27.8K
serde.py  3.1K
time.py  18.0K
tokenizer_core.py  34.5K
tokens.py  22.8K
transforms.py  41.9K
trie.py  2.2K
[tool_use Bash] {"command": "grep -rn \"ParseDate\\|ParseTime\\|PARSE_DATE\\|PARSE_TIME\\|ParseDatetime\" sqlglot/ tests/ | grep -v \"\\.pyc\" | head -60; sed -n 436,450p sqlglot/expressions/temporal.py", "description": "Search PARSE_DATE/PARSE_TIME references in sqlglot and tests"}
[tool_result] sqlglot/parsers/clickhouse.py:290:        "PARSEDATETIME": _build_datetime_format(exp.ParseDatetime),
sqlglot/parsers/bigquery.py:224:        "PARSE_DATE": lambda args, dialect: build_formatted_time(exp.StrToDate)(
sqlglot/parsers/bigquery.py:227:        "PARSE_TIME": lambda args, dialect: build_formatted_time(exp.ParseTime)(
sqlglot/parsers/bigquery.py:230:        "PARSE_TIMESTAMP": _build_parse_timestamp,
sqlglot/parsers/bigquery.py:231:        "PARSE_DATETIME": lambda args, dialect: build_for
…[5676 chars elided]…
%Y', 'Thu Dec 25 07:30:00 2008');
tests/fixtures/optimizer/annotate_functions.sql:1437:PARSE_TIME("%I:%M:%S", "07:30:00");
class FromISO8601Timestamp(Expression, Func):
    _sql_names = ["FROM_ISO8601_TIMESTAMP"]


class ParseDatetime(Expression, Func):
    arg_types = {"this": True, "format": False, "zone": False}


class ParseTime(Expression, Func):
    arg_types = {"this": True, "format": True}


class StrToDate(Expression, Func):
    arg_types = {"this": True, "format": False, "safe": False}
[tool_use Bash] {"command": "sed -n 222,232p sqlglot/parsers/bigquery.py; grep -n \"StrToDate\\|StrToTime\\|def strtodate\\|def strtotime\\|_str_to_\\|STRPTIME\" sqlglot/generators/duckdb.py sqlglot/dialects/duckdb.py sqlglot/parsers/duckdb.py | head -30", "description": "Inspect BigQuery parser and DuckDB str-to-time handling"}
[tool_result]         "OCTET_LENGTH": exp.ByteLength.from_arg_list,
        "TO_HEX": _build_to_hex,
        "PARSE_DATE": lambda args, dialect: build_formatted_time(exp.StrToDate)(
            [seq_get(args, 1), seq_get(args, 0)], dialect
        ),
        "PARSE_TIME": lambda args, dialect: build_formatted_time(exp.ParseTime)(
            [seq_get(args, 1), seq_get(args, 0)], dialect
        ),
        "PARSE_TIMESTAMP": _build_parse_timestamp,
        "PARSE_DATETIME": lambda args, dialect: build_formatte
…[653 chars elided]…
oTime) -> str:
sqlglot/generators/duckdb.py:2631:exp.cast(self.func("TRY_STRPTIME", expression.this, formatted_time), cast_type)
sqlglot/generators/duckdb.py:2644:def strtodate_sql(self, expression: exp.StrToDate) -> str:
sqlglot/generators/duckdb.py:2646:function_name = "STRPTIME" if not expression.args.get("safe") else "TRY_STRPT...
sqlglot/generators/duckdb.py:2662:func_name = "TRY_STRPTIME" if safe else "STRPTIME"
sqlglot/parsers/duckdb.py:179:"STRPTIME": build_formatted_time(exp.StrToTime),
[tool_use Bash] {"command": "sed -n 2615,2670p sqlglot/generators/duckdb.py; sed -n 1570,1580p sqlglot/generators/duckdb.py; sed -n 1640,1670p sqlglot/generators/duckdb.py", "description": "Read DuckDB str-to-time/date generator code"}
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
…[3293 chars elided]…

        exp.TimestampSub: _date_delta_to_binary_interval_op(),
        exp.TimeStrToDate: lambda self, e: self.sql(exp.cast(e.this, exp.DType.DATE)),
        exp.TimeStrToTime: timestrtotime_sql,
        exp.TimeStrToUnix: lambda self, e: self.func(
            "EPOCH", exp.cast(e.this, exp.DType.TIMESTAMP)
        ),
        exp.TimeToStr: lambda self, e: self.func("STRFTIME", e.this, self.format_time(e)),
        exp.ToBoolean: _to_boolean_sql,
        exp.ToVariant: lambda self, e: self.sql(
[tool_use Bash] {"command": "sed -n 1720,1740p tests/dialects/test_bigquery.py; sed -n 1908,1918p tests/dialects/test_bigquery.py; sed -n 1820,1830p tests/dialects/test_duckdb.py; ls .lithify/harness/scripts/ && <work>/env-sqlglot/bin/python -c \"import duckdb; print(duckdb.__version__)\"", "description": "Inspect existing PARSE_DATE tests and check duckdb availability"}
[tool_result]                 "duckdb": "SELECT GENERATE_SERIES(CAST('2016-10-05 00:00:00' AS TIMESTAMP), CAST('2016-10-07 00:00:00' AS TIMESTAMP), INTERVAL '1' DAY)",
                "bigquery": "SELECT GENERATE_TIMESTAMP_ARRAY('2016-10-05 00:00:00', '2016-10-07 00:00:00', INTERVAL '1' DAY)",
            },
        )
        self.validate_all(
            "SELECT PARSE_DATE('%A %b %e %Y', 'Thursday Dec 25 2008')",
            write={
                "bigquery": "SELECT PARSE_DATE('%A %b %e %Y', 'Thursday Dec
…[1141 chars elided]…
query": "SELECT DATE('2024-01-15 23:30:00', 'Europe/Berlin')",
            },
        )
        self.validate_all(
            "SELECT CAST(CAST(STRPTIME('05/06/2020', '%m/%d/%Y') AS DATE) AS DATE)",
            read={"bigquery": "SELECT DATE(PARSE_DATE('%m/%d/%Y', '05/06/2020'))"},
        )
        self.validate_all(
            "SELECT CAST('2020-01-01' AS DATE) + INTERVAL '-1' DAY",
            read={"mysql": "SELECT DATE '2020-01-01' + INTERVAL -1 DAY"},
        )
probe_parse.py  2.2K
1.5.6
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-155428-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py", "old_string": "    def tsordstotime_sql(self, expression: exp.TsOrDsToTime) -> str:", "new_string": "    def parsetime_sql(self, expression: exp.ParseTime) -> str:\n        formatted_time = self.format_time(expression)\n        return self.sql(\n            exp.cast(\n                self.func(\"STRPTIME\", expression.this, formatted_time),\n                exp.DataType(this=exp.DType.TIME),\n            )\n        )\n\n    def tsordstotime_sql(self, expression: exp.TsOrDsToTime) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-155428-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[assistant] Now a test next to the existing PARSE_DATE duckdb cases, then a check against the real DuckDB.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-155428-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_bigquery.py", "old_string": "        self.validate_identity(\"PARSE_TIME('%I:%M:%S', '07:30:00')\")\n        self.validate_identity(\"BYTE_LENGTH('foo')\")", "new_string": "        self.validate_identity(\"PARSE_TIME('%I:%M:%S', '07:30:00')\")\n        self.validate_all(\n            \"SELECT PARSE_TIME('%H:%M', '14:30')\",\n            write={\n                \"bigquery\": \"SELECT PARSE_TIME('%H:%M', '14:30')\",\n                \"duckdb\": \"SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)\",\n            },\n        )\n        self.validate_identity(\"BYTE_LENGTH('foo')\")"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-155428-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py 2>&1 | tail -5; $PY -c \"\nimport sqlglot, duckdb\ns = sqlglot.transpile(\\\"SELECT PARSE_TIME('%H:%M', '14:30'), PARSE_TIME('%I:%M:%S %p', '02:15:30 PM'), SAFE.PARSE_TIME('%H:%M', '14:30')\\\", read='bigquery', write='duckdb')[0]\nprint(s)\ncon = duckdb.connect()\nprint(con.sql(s).fetchall())\nprint(con.sql(\\\"SELECT typeof(CAST(STRPTIME('14:30', '%H:%M') AS TIME))\\\").fetchall())\n\"", "description": "Run BigQuery and DuckDB tests and verify output in DuckDB"}
[tool_result ERROR] Exit code 1
................... [ 18%]
.............................. [ 48%]
.....................................................                                        [100%]
102 passed, 1659 subtests passed in 0.70s
Traceback (most recent call last):
  File "<string>", line 6, in <module>
_duckdb.ParserException: Parser Error: syntax error at or near "AS"

LINE 1: ... '%I:%M:%S %p') AS TIME), SAFE.CAST(STRPTIME('14:30', '%H:%M') AS TIME)
                                                                          ^
SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME), CAST(STRPTIME('02:15:30 PM', '%I:%M:%S %p') AS TIME), SAFE.CAST(STRPTIME('14:30', '%H:%M') AS TIME)
[assistant] The two existing BigQuery/DuckDB suites pass. The `SAFE.PARSE_TIME` case leaks a `SAFE.CAST` prefix, so I'll check whether `SAFE.PARSE_DATE` already does the same thing before deciding whether it's mine to fix.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT SAFE.PARSE_DATE('%Y-%m-%d', '2024-01-15')\\\", read='bigquery', write='duckdb')[0])\nprint(sqlglot.transpile(\\\"SELECT SAFE.PARSE_TIME('%H:%M', '14:30')\\\", read='bigquery', write='duckdb')[0])\nprint(repr(sqlglot.parse_one(\\\"SELECT SAFE.PARSE_TIME('%H:%M', '14:30')\\\", read='bigquery').selects[0]))\n\"; grep -n \"SafeFunc\\|\\\"SAFE\\\"\" sqlglot/generators/duckdb.py sqlglot/generators/generator.py | head", "description": "Compare SAFE.PARSE_DATE vs SAFE.PARSE_TIME output in DuckDB"}
[tool_result] SELECT SAFE.CAST(STRPTIME('2024-01-15', '%Y-%m-%d') AS DATE)
SELECT SAFE.CAST(STRPTIME('14:30', '%H:%M') AS TIME)
SafeFunc(
  this=ParseTime(
    this=Literal(this='14:30', is_string=True),
    format=Literal(this='%H:%M', is_string=True)))
rg: sqlglot/generators/generator.py: No such file or directory (os error 2)
0 matches for 'SafeFunc\|"SAFE"'
[assistant] `SAFE.PARSE_DATE` already emits the same `SAFE.CAST` today, so that's a pre-existing `SafeFunc` generation issue rather than something specific to `PARSE_TIME`. I'll leave it alone and flag it. Next, confirm the plain output actually runs in DuckDB and run the full suite.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot, duckdb\ns = sqlglot.transpile(\\\"SELECT PARSE_TIME('%H:%M', '14:30'), PARSE_TIME('%I:%M:%S %p', '02:15:30 PM')\\\", read='bigquery', write='duckdb')[0]\nprint(s)\nprint(duckdb.connect().sql(s).fetchall())\n\"; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4", "description": "Verify DuckDB output runs and run full test suite"}
[tool_result] SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME), CAST(STRPTIME('02:15:30 PM', '%I:%M:%S %p') AS TIME)
[(datetime.time(14, 30), datetime.time(14, 15, 30))]
............................................................................................................................................ [ 73%]
.................................................................................................................................. [ 85%]
................................................................................................................................................................                                                  [100%]
1112 passed, 18135 subtests passed in 50.16s
[assistant] BigQuery `PARSE_TIME` now transpiles to DuckDB as `CAST(STRPTIME(...) AS TIME)`, the same pattern `PARSE_DATE` uses for `DATE`:

```python
sqlglot.transpile("SELECT PARSE_TIME('%H:%M', '14:30')", read="bigquery", write="duckdb")
# ["SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
```

I ran that output in DuckDB 1.5.6 and it returns `time(14, 30)`. A 12-hour example with `%I:%M:%S %p` also returns the right value.

The change is in two files:
- **`sqlglot/generators/duckdb.py`**: added `parsetime_sql`, next to `strtodate_sql`. It's auto-discovered from the `ParseTime` expression name, so no `TRANSFORMS` entry was needed.
- **`tests/dialects/test_bigquery.py`**: added a `validate_all` case beside the existing `PARSE_DATE` cases, asserting the DuckDB output.

The full suite passes: 1112 tests, 50 seconds. I haven't committed anything.

**Not fixed:** `SAFE.PARSE_TIME(...)` becomes `SAFE.CAST(STRPTIME(...) AS TIME)`, which DuckDB rejects. `SAFE.PARSE_DATE` already does this today, so it's a general `SafeFunc` generation issue rather than something specific to this change. Fixing it would mean changing how safe-wrapped functions are generated for DuckDB, which goes beyond this task.
