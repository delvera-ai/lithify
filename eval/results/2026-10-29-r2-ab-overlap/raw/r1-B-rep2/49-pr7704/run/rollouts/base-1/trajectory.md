# trajectory base-1

final message:
`PARSE_DATETIME` now transpiles to DuckDB as `STRPTIME`, with the arguments in DuckDB's order:

```
SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')
→ SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')
```

**The change**
- `sqlglot/generators/duckdb.py`: added `parsedatetime_sql`, next to the existing `parsetime_sql` that handles BigQuery's `PARSE_TIME` the same way. It emits `STRPTIME(this, format)` using the usual `format_time` mapping. The parser and the BigQuery round-trip are untouched.
- `tests/dialects/test_bigquery.py`: added a `validate_all` case covering the BigQuery and DuckDB outputs. BigQuery normalizes the format to `%F %T` on its own side, so that is the expected BigQuery string.

**Verification**
- Probe output is correct for the issue's query, for the existing `%a %b %e …` format, and for a column argument (`STRPTIME(x, '%Y-%m-%d')`).
- `tests/dialects/test_bigquery.py` and `test_duckdb.py`: 102 passed.
- Full suite: 1120 passed.
- `ruff check` and `ruff format --check` are clean on both files.

**Not done**
- I did not commit. The working tree has the two modified files only.
- The BigQuery `zone` argument of `PARSE_DATETIME` is still not carried over to DuckDB. The builder never sets it, so this is outside the reported case.

## events
[tool_use Bash] {"command": "grep -rn -i \"parse_datetime\\|ParseDatetime\\|PARSE_TIMESTAMP\\|ParseTimestamp\\|StrToDate\\|StrptimeSql\\|StrToTime\" sqlglot/ | head -60", "description": "Locate PARSE_DATETIME handling in sqlglot"}
[tool_result] sqlglot/parsers/clickhouse.py:49:    strtodate = exp.StrToDate.from_arg_list(args)
sqlglot/parsers/clickhouse.py:50:    return exp.cast(strtodate, exp.DType.DATETIME.into_expr())
sqlglot/parsers/clickhouse.py:290:        "PARSEDATETIME": _build_datetime_format(exp.ParseDatetime),
sqlglot/parsers/singlestore.py:27:        "TO_TIMESTAMP": build_formatted_time(exp.StrToTime),
sqlglot/parsers/singlestore.py:29:        "STR_TO_DATE": build_formatted_time(exp.StrToDate, "mysql"),
sqlglot/parsers/spark
…[4462 chars elided]…
sqlglot/expressions/temporal.py:448:class StrToDate(Expression, Func):
sqlglot/expressions/temporal.py:452:class StrToTime(Expression, Func):
sqlglot/expressions/temporal.py:460:class TimeStrToDate(Expression, Func):
sqlglot/expressions/temporal.py:464:class TimeStrToTime(Expression, Func):
sqlglot/expressions/core.py:2385:        from sqlglot.expressions.temporal import TimeStrToTime as _TimeStrToTime
sqlglot/expressions/core.py:2387:        return _TimeStrToTime(this=datetime_literal, zone=tz)
[tool_use Bash] {"command": "sed -n 436,450p sqlglot/expressions/temporal.py && echo ---- && sed -n 240,260p sqlglot/parsers/bigquery.py && echo ---- && sed -n 40,100p sqlglot/parsers/bigquery.py && echo ---- && grep -n \"ParseDatetime\\|parsedatetime\" -i sqlglot/generator.py sqlglot/dialects/*.py sqlglot/parsers/*.py sqlglot/typing/*.py tests/dialects/*.py | head -40", "description": "Read ParseDatetime definition and BigQuery builders"}
[tool_result] class FromISO8601Timestamp(Expression, Func):
    _sql_names = ["FROM_ISO8601_TIMESTAMP"]


class ParseDatetime(Expression, Func):
    arg_types = {"this": True, "format": False, "zone": False}


class ParseTime(Expression, Func):
    arg_types = {"this": True, "format": True}


class StrToDate(Expression, Func):
    arg_types = {"this": True, "format": False, "safe": False}

----
            this=seq_get(args, 0), form=seq_get(args, 1), is_casefold=True
        ),
        "OCTET_LENGTH": exp.By
…[3037 chars elided]…
    "PARSEDATETIME": _build_datetime_format(exp.ParseDatetime),
sqlglot/typing/bigquery.py:246:            exp.ParseDatetime,
tests/dialects/test_bigquery.py:122:        ).assert_is(exp.SafeFunc).this.assert_is(exp.ParseDatetime)
tests/dialects/test_clickhouse.py:690:        self.validate_identity("SELECT parseDateTime('2021-01-04+23:00:00', '%Y-%m-%d+%H:%i:%s')")
tests/dialects/test_clickhouse.py:692:            "SELECT parseDateTime('2021-01-04+23:00:00', '%Y-%m-%d+%H:%i:%s', 'Asia/Istanbul')"
[tool_use Bash] {"command": "sed -n 4050,4075p sqlglot/generator.py && echo ---- && grep -n \"STRPTIME\\|StrToTime\\|strtotime\\|def .*_sql\" sqlglot/generators/duckdb.py | head -80 && echo ---- && grep -n \"ParseDatetime\\|StrToTime\" -A3 sqlglot/generators/bigquery.py | head -40; echo ----; sed -n 240,250p sqlglot/typing/bigquery.py; ls .lithify/harness/scripts/", "description": "Inspect generator handling for StrToTime in DuckDB"}
[tool_result]         action = f" {action}" if action else ""
        default = self.sql(expression, "default")
        default = f" DEFAULT {default} ON CONVERSION ERROR" if default else ""
        return f"{safe_prefix or ''}CAST({self.sql(expression, 'this')} AS{to_sql}{default}{format_sql}{action})"

    # Base implementation that excludes safe, zone, and target_type metadata args
    def strtotime_sql(self, expression: exp.StrToTime) -> str:
        return self.func("STR_TO_TIME", expression.this, expres
…[4411 chars elided]…
       exp.TimeFromParts: rename_func("TIME"),
--
389:        exp.TimeStrToTime: timestrtotime_sql,
390-        exp.Transaction: lambda *_: "BEGIN TRANSACTION",
391-        exp.TsOrDsAdd: _ts_or_ds_add_sql,
392-        exp.TsOrDsDiff: _ts_or_ds_diff_sql,
----
            exp.LaxBool,
        }
    },
    **{
        expr_type: {"returns": exp.DType.DATETIME}
        for expr_type in {
            exp.ParseDatetime,
            exp.TimestampFromParts,
        }
    },
    **{
probe_parse.py  2.2K
[tool_use Bash] {"command": "sed -n 2625,2665p sqlglot/generators/duckdb.py; echo ----; grep -n \"ParseTime\\|ParseDatetime\" -B2 -A8 sqlglot/generators/duckdb.py | head -40; echo ----; cat .lithify/harness/scripts/probe_parse.py | head -30; echo; printf \"%s\\n\" \"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\" | <work>/env-sqlglot/bin/python -I .lithify/harness/scripts/probe_parse.py 2>&1 | head -20", "description": "Inspect DuckDB StrToTime generator and probe current output"}
[tool_result]         return self.function_fallback_sql(expression)

    def strtotime_sql(self, expression: exp.StrToTime) -> str:
        # Check if target_type requires TIMESTAMPTZ (for LTZ/TZ variants)
        target_type = expression.args.get("target_type")
        needs_tz = target_type and target_type.this in (
            exp.DType.TIMESTAMPLTZ,
            exp.DType.TIMESTAMPTZ,
        )

        if expression.args.get("safe"):
            formatted_time = self.format_time(expression)
            ca
…[2268 chars elided]…


import sqlglot


def probe(sql, read, write):
    try:
        out = sqlglot.transpile(sql, read=read, write=write)[0]
    except Exception as e:
        return "ERR", f"{type(e).__name__}: {str(e).splitlines()[0]}"


Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164025-bigquery-duckdb-bigquery-s-parse/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "printf \"%s\\n\" \"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\" \"SELECT PARSE_DATETIME('%Y-%m-%d', x) FROM t\" | PYTHONPATH=. <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py --read bigquery --write duckdb; PYTHONPATH=. <work>/env-sqlglot/bin/python -c \
…[61 chars elided]…
ne(\\\"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\\\", read='bigquery')\nprint(repr(e.selects[0]))\nprint(sqlglot.parse_one(\\\"SELECT PARSE_TIMESTAMP('%Y-%m-%d', x)\\\", read='bigquery').sql('duckdb'))\n\"; grep -n \"PARSE_DATETIME\\|ParseDatetime\" -B3 -A3 tests/dialects/test_bigquery.py | head -40", "description": "Probe current BigQuery to DuckDB output and inspect AST"}
[tool_result] OK        SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')
          SELECT PARSE_DATETIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')
OK        SELECT PARSE_DATETIME('%Y-%m-%d', x) FROM t
          SELECT PARSE_DATETIME(x, '%Y-%m-%d') FROM t
ParseDatetime(
  this=Literal(this='2023-01-15 14:30:00', is_string=True),
  format=Literal(this='%Y-%m-%d %H:%M:%S', is_string=True))
SELECT STRPTIME(x, '%Y-%m-%d')
117-            "SAFE.PARSE_DATE('%F', '2024-01-15')",
118-        ).asser
…[342 chars elided]…
ity(
124-            "SAFE.PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', '2024-01-15 10:30:00')",
125-            "SAFE.PARSE_TIMESTAMP('%F %T', '2024-01-15 10:30:00')",
--
1973-            },
1974-        )
1975-        self.validate_identity(
1976:            "SELECT PARSE_DATETIME('%a %b %e %I:%M:%S %Y', 'Thu Dec 25 07:30:00 2008')"
1977-        )
1978-        self.validate_identity("FORMAT_TIME('%R', CAST('15:30:00' AS TIME))")
1979-        self.validate_identity("PARSE_TIME('%I:%M:%S', '07:30:00')")
[tool_use Bash] {"command": "sed -n 1955,1980p tests/dialects/test_bigquery.py; echo ----; grep -n \"def parsetime_sql\" -B2 sqlglot/generators/duckdb.py; grep -n \"    def .*_sql\" sqlglot/generators/duckdb.py | awk -F: '$1>2600 && $1<2700'", "description": "View nearby BigQuery test and DuckDB method layout"}
[tool_result]             read={
                "duckdb": 'SELECT * FROM t1, UNNEST("t1"."t2"."t3"."t4") "t3" ("col")',
            },
            write={
                "bigquery": "SELECT * FROM t1 CROSS JOIN UNNEST(`t1`.`t2`.`t3`.`t4`) AS `col`",
                "redshift": 'SELECT * FROM t1 CROSS JOIN "t1"."t2"."t3"."t4" AS "col"',
            },
        )

        self.validate_identity("ARRAY_FIRST(['a', 'b'])")
        self.validate_identity("ARRAY_LAST(['a', 'b'])")
        self.validate_identity("J
…[499 chars elided]…
self.validate_identity("FORMAT_TIME('%R', CAST('15:30:00' AS TIME))")
        self.validate_identity("PARSE_TIME('%I:%M:%S', '07:30:00')")
        self.validate_identity("BYTE_LENGTH('foo')")
----
2660-        )
2661-
2662:    def parsetime_sql(self, expression: exp.ParseTime) -> str:
2613:0:exp.Substring) -> str:
2627:0:exp.StrToTime) -> str:
2652:0:exp.StrToDate) -> str:
2662:0:exp.ParseTime) -> str:
2671:0:exp.TsOrDsToTime) -> str:
2688:0:exp.CurrentDate) -> str:
2698:0:exp.CheckJson) -> str:
[assistant] I'll add a DuckDB generator method next to the existing `parsetime_sql`, which already maps BigQuery's sibling `PARSE_TIME` to `STRPTIME`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164025-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py", "old_string": "                exp.DataType(this=exp.DType.TIME),\n            )\n        )\n\n", "new_string": "                exp.DataType(this=exp.DType.TIME),\n            )\n        )\n\n    def parsedatetime_sql(self, expression: exp.ParseDatetime) -> str:\n        return self.func(\"STRPTIME\", expression.this, self.format_time(expression))\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-164025-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[assistant] Now a regression test in the BigQuery test file, next to the existing `PARSE_DATETIME` identity test.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164025-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_bigquery.py", "old_string": "        self.validate_identity(\n            \"SELECT PARSE_DATETIME('%a %b %e %I:%M:%S %Y', 'Thu Dec 25 07:30:00 2008')\"\n        )\n", "new_string": "        self.validate_identity(\n            \"SELEC
…[41 chars elided]…
'Thu Dec 25 07:30:00 2008')\"\n        )\n        self.validate_all(\n            \"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\",\n            write={\n                \"bigquery\": \"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\",\n                \"duckdb\": \"SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')\",\n            },\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-164025-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; printf \"%s\\n\" \"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\" \"SELECT PARSE_DATETIME('%a %b %e %I:%M:%S %Y', 'Thu Dec 25 07:30:00 2008')\" \"SELECT PARSE_DATETIME('%Y-%m-%d', x) FROM t\" | PYTHONPATH=. $PY .lithify/harness/scripts/probe_parse.py --read bigquery --write duckdb; echo; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py 2>&1 | tail -15", "description": "Probe the fix and run BigQuery and DuckDB dialect tests"}
[tool_result] OK        SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')
          SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')
OK        SELECT PARSE_DATETIME('%a %b %e %I:%M:%S %Y', 'Thu Dec 25 07:30:00 2008')
          SELECT STRPTIME('Thu Dec 25 07:30:00 2008', '%a %b %-d %I:%M:%S %Y')
OK        SELECT PARSE_DATETIME('%Y-%m-%d', x) FROM t
          SELECT STRPTIME(x, '%Y-%m-%d') FROM t

.................. [ 17%]
..............................................................
…[475 chars elided]…
')"
E   - SELECT PARSE_DATETIME('%F %T', '2023-01-15 14:30:00')
E   ?                         ^^ ^
E   + SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')
E   ?                         ^^ ^^^^^^^^^^^^^
=========================== short test summary info ============================
SUBFAILED[SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00') -> bigquery] tests/dialects/test_bigquery.py::TestBigQuery::test_bigquery
1 failed, 102 passed, 1661 subtests passed in 0.53s
[assistant] The BigQuery side of my test expectation was wrong: BigQuery's generator normalizes `%Y-%m-%d %H:%M:%S` to `%F %T`, as the existing test at line 121 shows. Correcting the expectation, not the code.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164025-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_bigquery.py", "old_string": "                \"bigquery\": \"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\",\n                \"duckdb\": \"SELECT STRPTIME", "new_string": "                \"bigquery\": \"SELECT PARSE_DATETIME('%F %T', '2023-01-15 14:30:00')\",\n                \"duckdb\": \"SELECT STRPTIME"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-164025-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Run BigQuery/DuckDB tests then full suite"}
[tool_result] .................. [ 17%]
....................................................................................                                     [100%]
102 passed, 1662 subtests passed in 0.43s
.................................................................................................................... [ 94%]
................. [ 95%]
................. [ 97%]
................................         [100%]
1120 passed, 18168 subtests passed in 45.63s
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff check sqlglot/generators/duckdb.py tests/dialects/test_bigquery.py && $PY -m ruff format --check sqlglot/generators/duckdb.py tests/dialects/test_bigquery.py) 2>&1 | tail -4; git status --short; git diff", "description": "Lint changed files and show the diff"}
[tool_result] All checks passed!
2 files already formatted
 M sqlglot/generators/duckdb.py
 M tests/dialects/test_bigquery.pysqlglot/generators/duckdb.py    | 3 +++
 tests/dialects/test_bigquery.py | 7 +++++++
 2 files changed, 10 insertions(+)

--- Changes ---

sqlglot/generators/duckdb.py
  @@ -2668,6 +2668,9 @@ class DuckDBGenerator(generator.Generator):
  +    def parsedatetime_sql(self, expression: exp.ParseDatetime) -> str:
  +        return self.func("STRPTIME", expression.this, self.format_time(expres
…[307 chars elided]…
IME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')",
  +            write={
  +                "bigquery": "SELECT PARSE_DATETIME('%F %T', '2023-01-15 14:30:00')",
  +                "duckdb": "SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')",
  +            },
  +        )
           self.validate_identity("FORMAT_TIME('%R', CAST('15:30:00' AS TIME))")
           self.validate_identity("PARSE_TIME('%I:%M:%S', '07:30:00')")
           self.validate_identity("BYTE_LENGTH('foo')")
  +7 -0
[assistant] `PARSE_DATETIME` now transpiles to DuckDB as `STRPTIME`, with the arguments in DuckDB's order:

```
SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')
→ SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')
```

**The change**
- `sqlglot/generators/duckdb.py`: added `parsedatetime_sql`, next to the existing `parsetime_sql` that handles BigQuery's `PARSE_TIME` the same way. It emits `STRPTIME(this, format)` using the usual `format_time` mapping. The parser and the BigQuery round-trip are untouched.
- `tests/dialects/test_bigquery.py`: added a `validate_all` case covering th
…[90 chars elided]…
so that is the expected BigQuery string.

**Verification**
- Probe output is correct for the issue's query, for the existing `%a %b %e …` format, and for a column argument (`STRPTIME(x, '%Y-%m-%d')`).
- `tests/dialects/test_bigquery.py` and `test_duckdb.py`: 102 passed.
- Full suite: 1120 passed.
- `ruff check` and `ruff format --check` are clean on both files.

**Not done**
- I did not commit. The working tree has the two modified files only.
- The BigQuery `zone` argument of `PARSE_DATETIME` is still not carried over to DuckDB. The builder never sets it, so this is outside the reported case.
