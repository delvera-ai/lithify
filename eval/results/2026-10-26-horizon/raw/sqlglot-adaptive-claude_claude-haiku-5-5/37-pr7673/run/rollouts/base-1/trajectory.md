# trajectory base-1

final message:
BigQuery `PARSE_TIME` now transpiles to DuckDB as a `TIME`:

```python
sqlglot.transpile("SELECT PARSE_TIME('%H:%M', '14:30')", read="bigquery", write="duckdb")
# ["SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
```

The change is a `parsetime_sql` method in `sqlglot/generators/duckdb.py`. It builds a `StrToTime` and casts it to `TIME`, the same pattern `tsordstotime_sql` already uses. I also added a regression case to `tests/dialects/test_duckdb.py`, next to the existing `PARSE_DATE` case.

Checks:
- The full test suite passes: 1112 tests, 18134 subtests.
- Ruff lint and format pass on both changed files.
- I ran the generated SQL in DuckDB 1.5.6. `STRPTIME('14:30', '%H:%M')` cast to `TIME` returns `14:30:00`, and the `%I:%M:%S %p` form also parses.

I did not commit anything.

## events
[tool_use Bash] {"command": "grep -rn \"PARSE_DATE\\|ParseDate\\|PARSE_TIME\\|ParseTime\\|StrToTime\\|StrToDate\" sqlglot/ | grep -v \"\\.pyc\" | head -60", "description": "Find PARSE_DATE/PARSE_TIME related code"}
[tool_result] sqlglot/generator.py:3960:    def strtotime_sql(self, expression: exp.StrToTime) -> str:
sqlglot/generator.py:4949:                    exp.StrToTime(this=this, format=expression.args["format"]),
sqlglot/generator.py:4980:                    exp.StrToTime(this=this, format=expression.args["format"], safe=safe),
sqlglot/generator.py:5108:                transformed = exp.StrToDate(this=value, format=fmt)
sqlglot/generator.py:5110:                transformed = exp.StrToTime(this=value, format=fmt)

…[4482 chars elided]…
essions/temporal.py:420:class DateStrToDate(Expression, Func):
sqlglot/expressions/temporal.py:440:class ParseDatetime(Expression, Func):
sqlglot/expressions/temporal.py:444:class ParseTime(Expression, Func):
sqlglot/expressions/temporal.py:448:class StrToDate(Expression, Func):
sqlglot/expressions/temporal.py:452:class StrToTime(Expression, Func):
sqlglot/expressions/temporal.py:460:class TimeStrToDate(Expression, Func):
sqlglot/expressions/temporal.py:464:class TimeStrToTime(Expression, Func):
[tool_use Bash] {"command": "sed -n 215,240p sqlglot/parsers/bigquery.py && grep -n \"ParseTime\\|ParseDate\\|class ParseDatetime\" -A4 sqlglot/expressions/temporal.py | head -30 && grep -rn \"ParseTime\\|PARSE_TIME\\|PARSE_DATE\" sqlglot/generators/ sqlglot/dialects/ tests/ | head -40", "description": "Inspect BigQuery parser and related generator code"}
[tool_result]         "JSON_VALUE_ARRAY": _build_extract_json_with_default_path(exp.JSONValueArray),
        "LENGTH": lambda args: exp.Length(this=seq_get(args, 0), binary=True),
        "MD5": exp.MD5Digest.from_arg_list,
        "SHA1": exp.SHA1Digest.from_arg_list,
        "NORMALIZE_AND_CASEFOLD": lambda args: exp.Normalize(
            this=seq_get(args, 0), form=seq_get(args, 1), is_casefold=True
        ),
        "OCTET_LENGTH": exp.ByteLength.from_arg_list,
        "TO_HEX": _build_to_hex,
        "
…[5280 chars elided]…

tests/dialects/test_duckdb.py:1915:                "bigquery": "PARSE_TIMESTAMP('%-m/%e/%y %-I:%M %p', x)",
tests/dialects/test_hive.py:487:                "presto": "TO_UNIXTIME(COALESCE(TRY(DATE_PARSE(CAST(x AS VARCHAR), '%Y-%m-%d %T')), PARSE_DATETIME(DATE_FORMAT(x, '%Y-%m-%d %T'), 'yyyy-MM-dd HH:mm:ss')))",
tests/fixtures/optimizer/annotate_functions.sql:1081:SAFE.PARSE_DATE('%Y-%m-%d', '2024-01-15');
tests/fixtures/optimizer/annotate_functions.sql:1085:PARSE_DATE('%Y-%m-%d', '2024-01-15');
[tool_use Bash] {"command": "grep -n \"StrToDate\\|StrToTime\\|strtodate\\|strtotime\\|ParseTime\\|DType.TIME\\b\" sqlglot/generators/duckdb.py sqlglot/generator.py sqlglot/dialects/dialect.py | head -40; grep -n \"PARSE_DATE\\|StrToDate\" -B3 -A8 tests/dialects/test_duckdb.py | head -80", "description": "Find DuckDB generator handling for StrToDate/StrToTime"}
[tool_result] sqlglot/generators/duckdb.py:20:    datestrtodate_sql,
sqlglot/generators/duckdb.py:37:    timestrtotime_sql,
sqlglot/generators/duckdb.py:316:    this = exp.cast(expression.this, exp.DType.TIME)
sqlglot/generators/duckdb.py:317:    expr = exp.cast(expression.expression, exp.DType.TIME)
sqlglot/generators/duckdb.py:663:    if expression.is_type(exp.DType.TIME, exp.DType.TIMETZ, exp.DType.TIMESTAMPTZ):
sqlglot/generators/duckdb.py:1575:        exp.DateStrToDate: datestrtodate_sql,
sqlglot/generat
…[2097 chars elided]…
TIME('05/06/2020', '%m/%d/%Y') AS DATE) AS DATE)",
1825:            read={"bigquery": "SELECT DATE(PARSE_DATE('%m/%d/%Y', '05/06/2020'))"},
1826-        )
1827-        self.validate_all(
1828-            "SELECT CAST('2020-01-01' AS DATE) + INTERVAL '-1' DAY",
1829-            read={"mysql": "SELECT DATE '2020-01-01' + INTERVAL -1 DAY"},
1830-        )
1831-        self.validate_all(
1832-            "SELECT INTERVAL '1 quarter'",
1833-            write={"duckdb": "SELECT INTERVAL '1' QUARTER"},
[tool_use Bash] {"command": "sed -n 2615,2665p sqlglot/generators/duckdb.py; sed -n 3955,3975p sqlglot/generator.py; sed -n 4935,4960p sqlglot/generator.py; grep -n \"ParseTime\\|ParseDatetime\" sqlglot/generators/*.py sqlglot/dialects/*.py", "description": "Read DuckDB strtotime/strtodate generation code"}
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
…[3326 chars elided]…
exp.cast(this, exp.DType.TIME))

    def tsordstotimestamp_sql(self, expression: exp.TsOrDsToTimestamp) -> str:
        this = expression.this
sqlglot/generators/bigquery.py:357:        exp.ParseTime: lambda self, e: self.func("PARSE_TIME", self.format_time(e), e.this),
sqlglot/generators/bigquery.py:358:        exp.ParseDatetime: lambda self, e: self.func("PARSE_DATETIME", self.format_time(e), e.this),
sqlglot/generators/clickhouse.py:380:        exp.ParseDatetime: rename_func("parseDateTime"),
[tool_use Bash] {"command": "ls <work>/env-sqlglot/bin/python 2>&1; python3 -c \"\nimport sqlglot\nfor s in ['SELECT PARSE_TIME(\\'%H:%M\\', \\'14:30\\')', 'SELECT PARSE_TIME(\\'%I:%M:%S %p\\', x)']:\n    e = sqlglot.parse_one(s, read='bigquery'); print(repr(e.find(sqlglot.exp.ParseTime).args))\n    print(e.sql('duckdb'))\n\"", "description": "Check Python env and current PARSE_TIME output"}
[tool_result] <work>/env-sqlglot/bin/python
{'this': Literal(this='14:30', is_string=True), 'format': Literal(this='%H:%M', is_string=True)}
SELECT PARSE_TIME('14:30', '%H:%M')
{'this': Column(
  this=Identifier(this=x, quoted=False)), 'format': Literal(this='%I:%M:%S %p', is_string=True)}
SELECT PARSE_TIME(x, '%I:%M:%S %p')
[assistant] Current output confirmed. The `ParseTime` node already carries `this` and `format`, so I'll add a DuckDB generator method that mirrors `tsordstotime_sql`: a `StrToTime` cast to `TIME`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-055710-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py", "old_string": "    def strtodate_sql(self, expression: exp.StrToDate) -> str:\n        formatted_time = self.format_time(expression)\n        function_name = \"STRPTIME\" if not expression.args.get(\"safe\") else \"TRY_STRP
…[514 chars elided]…
.func(function_name, expression.this, formatted_time),\n                exp.DataType(this=exp.DType.DATE),\n            )\n        )\n\n    def parsetime_sql(self, expression: exp.ParseTime) -> str:\n        return self.sql(\n            exp.cast(\n                exp.StrToTime(this=expression.this, format=expression.args[\"format\"]),\n                exp.DType.TIME,\n            )\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-055710-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[assistant] Now a test next to the existing `PARSE_DATE` case in the DuckDB tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-055710-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_duckdb.py", "old_string": "            read={\"bigquery\": \"SELECT DATE(PARSE_DATE('%m/%d/%Y', '05/06/2020'))\"},\n        )\n", "new_string": "            read={\"bigquery\": \"SELECT DATE(PARSE_DATE('%m/%d/%Y', '05/06/2020'))\"},\n        )\n        self.validate_all(\n            \"SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)\",\n            read={\"bigquery\": \"SELECT PARSE_TIME('%H:%M', '14:30')\"},\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-055710-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT PARSE_TIME('%H:%M', '14:30')\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_TIME('%I:%M:%S %p', x)\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_TIME('%H:%M', '14:30')\\\", read='bigquery', write='bigquery'))\n\" && $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py tests/dialects/test_bigquery.py tests/dialects/test_dialect.py 2>&1 | tail -15", "description": "Verify transpile output and run dialect tests"}
[tool_result] ["SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
["SELECT CAST(STRPTIME(x, '%I:%M:%S %p') AS TIME)"]
["SELECT PARSE_TIME('%H:%M', '14:30')"]
........................ [ 12%]
.......................................................................................................................................... [ 81%]
...................................... [100%]
200 passed, 4483 subtests passed in 0.93s
[assistant] Transpile output is right and the dialect tests pass. Now the full suite, plus a check that DuckDB actually accepts the generated SQL, if DuckDB is installed.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; $PY -c \"import duckdb; print(duckdb.__version__); print(duckdb.sql(\\\"SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME) AS t, CAST(STRPTIME('02:05:09 PM', '%I:%M:%S %p') AS TIME) AS t2\\\").fetchall())\" 2>&1 | tail -3", "description": "Run full test suite and verify with DuckDB"}
[tool_result] ................................................................................................................................. [ 69%]
...................................................... [ 74%]
.................................................................................................................................................................. [ 88%]
...............................................................................................................................                                                   [100%]
1112 passed, 18134 subtests passed in 49.52s
1.5.6
[(datetime.time(14, 30), datetime.time(14, 5, 9))]
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff check sqlglot/generators/duckdb.py tests/dialects/test_duckdb.py && $PY -m ruff format --check sqlglot/generators/duckdb.py tests/dialects/test_duckdb.py) 2>&1 | tail -3; git diff --stat", "description": "Lint and format check changed files"}
[tool_result] All checks passed!
2 files already formatted
 sqlglot/generators/duckdb.py  | 8 ++++++++
 tests/dialects/test_duckdb.py | 4 ++++
 2 files changed, 12 insertions(+)
[assistant] BigQuery `PARSE_TIME` now transpiles to DuckDB as a `TIME`:

```python
sqlglot.transpile("SELECT PARSE_TIME('%H:%M', '14:30')", read="bigquery", write="duckdb")
# ["SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
```

The change is a `parsetime_sql` method in `sqlglot/generators/duckdb.py`. It builds a `StrToTime` and casts it to `TIME`, the same pattern `tsordstotime_sql` already uses. I also added a regression case to `tests/dialects/test_duckdb.py`, next to the existing `PARSE_DATE` case.

Checks:
- The full test suite passes: 1112 tests, 18134 subtests.
- Ruff lint and format pass on both changed files.
- I ran the generated SQL in DuckDB 1.5.6. `STRPTIME('14:30', '%H:%M')` cast to `TIME` returns `14:30:00`, and the `%I:%M:%S %p` form also parses.

I did not commit anything.
