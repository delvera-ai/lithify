# trajectory base-1

final message:
`PARSE_TIME` now transpiles to DuckDB as a `TIME` cast around `STRPTIME`, the same way `PARSE_DATE` does:

```python
sqlglot.transpile("SELECT PARSE_TIME('%H:%M', '14:30')", read="bigquery", write="duckdb")
# ["SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
```

The change is a new `parsetime_sql` method in `sqlglot/generators/duckdb.py`, placed next to `strtodate_sql`. I also added a `validate_all` case for it in `tests/dialects/test_duckdb.py`, beside the `PARSE_DATE` case. The full suite passes (1112 tests) and ruff check and format are clean on both files.

I did not commit anything. The `safe` flag is not handled, because `ParseTime` has no `safe` argument.

## events
[tool_use Bash] {"command": "grep -rn \"PARSE_DATE\\|ParseDate\\|PARSE_TIME\\|ParseTime\\|StrToDate\\|StrToTime\" sqlglot/dialects/bigquery.py sqlglot/dialects/duckdb.py sqlglot/expressions.py | head -50", "description": "Find PARSE_DATE/PARSE_TIME references"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "ls sqlglot | head -50 && grep -rn \"PARSE_DATE\\|ParseDate\\|PARSE_TIME\\|ParseTime\\|ParseDatetime\\|PARSE_DATETIME\" sqlglot/ | head -60", "description": "Locate PARSE_DATE/PARSE_TIME handling"}
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
…[631 chars elided]…
ParseDatetime: rename_func("parseDateTime"),
sqlglot/generators/bigquery.py:357:        exp.ParseTime: lambda self, e: self.func("PARSE_TIME", self.format_time(e), e.this),
sqlglot/generators/bigquery.py:358:        exp.ParseDatetime: lambda self, e: self.func("PARSE_DATETIME", self.format_time(e), e.this),
sqlglot/generators/presto.py:511:        # timezone involved, we wrap it in a `TRY` call and use `PARSE_DATETIME` as a fallback,
sqlglot/generators/presto.py:522:            "PARSE_DATETIME",
[tool_use Bash] {"command": "sed -n 430,450p sqlglot/expressions/temporal.py && grep -n \"StrToDate\\|StrToTime\\|ParseDatetime\\|TimeToStr\\|TsOrDsToDate\\|TimeStrToTime\" sqlglot/generators/duckdb.py sqlglot/parsers/duckdb.py sqlglot/dialects/duckdb.py sqlglot/parsers/bigquery.py && sed -n 215,235p sqlglot/parsers/bigquery.py && grep -n \"class StrToDate\\|class StrToTime\\|class ParseTime\" -A4 sqlglot/expressions/temporal.py", "description": "Inspect expression classes and DuckDB generator mappings"}
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

sqlglot/parsers/duckdb.py:175:        "STRFTIME": build_formatted_time(exp.T
…[2792 chars elided]…
RegexpLike.from_arg_list,
        "REGEXP_EXTRACT": _build_regexp_extract(exp.RegexpExtract),
444:class ParseTime(Expression, Func):
445-    arg_types = {"this": True, "format": True}
446-
447-
448:class StrToDate(Expression, Func):
449-    arg_types = {"this": True, "format": False, "safe": False}
450-
451-
452:class StrToTime(Expression, Func):
453-    arg_types = {"this": True, "format": True, "zone": False, "safe": False, "target_type": False}
454-
455-
456-class StrToUnix(Expression, Func):
[tool_use Bash] {"command": "sed -n 2600,2665p sqlglot/generators/duckdb.py && sed -n 1560,1580p sqlglot/generators/duckdb.py && sed -n 1655,1675p sqlglot/generators/duckdb.py && grep -n \"ParseTime\\|ParseDatetime\" sqlglot/generators/duckdb.py; grep -n \"ParseTime\" -r tests | head", "description": "Read DuckDB StrToDate/StrToTime generators"}
[tool_result]                 ),
            )

        return strposition_sql(self, expression)

    def substring_sql(self, expression: exp.Substring) -> str:
        if expression.args.get("zero_start"):
            start = expression.args.get("start")
            length = expression.args.get("length")

            if start := expression.args.get("start"):
                start = exp.If(this=start.eq(0), true=exp.Literal.number(1), false=start)
            if length := expression.args.get("length"):
      
…[3633 chars elided]…
cast(e.this, exp.DType.TIMESTAMP)
        ),
        exp.TimeToStr: lambda self, e: self.func("STRFTIME", e.this, self.format_time(e)),
        exp.ToBoolean: _to_boolean_sql,
        exp.ToVariant: lambda self, e: self.sql(
            exp.cast(e.this, exp.DataType.from_str("VARIANT", dialect="duckdb"))
        ),
        exp.TimeToUnix: rename_func("EPOCH"),
        exp.TsOrDiToDi: lambda self, e: (
            f"CAST(SUBSTR(REPLACE(CAST({self.sql(e, 'this')} AS TEXT), '-', ''), 1, 8) AS INT)"
[assistant] The DuckDB generator already handles `StrToDate` via `STRPTIME` + cast. I'll add the matching `parsetime_sql` method right after `strtodate_sql`, then check it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-093751-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py", "old_string": "    def tsordstotime_sql(self, expression: exp.TsOrDsToTime) -> str:", "new_string": "    def parsetime_sql(self, expression: exp.ParseTime) -> str:\n        return self.sql(\n            exp.cast(\n                self.func(\"STRPTIME\", expression.this, self.format_time(expression)),\n                exp.DataType(this=exp.DType.TIME),\n            )\n        )\n\n    def tsordstotime_sql(self, expression: exp.TsOrDsToTime) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-093751-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT PARSE_TIME('%H:%M', '14:30')\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_TIME('%H:%M:%S', t) FROM x\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATE('%Y-%m-%d', d)\\\", read='bigquery', write='duckdb'))\n\"", "description": "Check PARSE_TIME transpilation to DuckDB"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sys; sys.path.insert(0, '.')\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT PARSE_TIME('%H:%M', '14:30')\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_TIME('%H:%M:%S', t) FROM x\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATE('%Y-%m-%d', d)\\\", read='bigquery', write='duckdb'))\n\"", "description": "Check PARSE_TIME transpilation to DuckDB"}
[tool_result] ["SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
["SELECT CAST(STRPTIME(t, '%H:%M:%S') AS TIME) FROM x"]
["SELECT CAST(STRPTIME(d, '%Y-%m-%d') AS DATE)"]
[assistant] The output matches the `PARSE_DATE` pattern. Next I'll find where the existing `PARSE_DATE` cross-dialect test lives so the new case sits beside it.
[tool_use Bash] {"command": "grep -rn \"PARSE_DATE\\|PARSE_TIME\" tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py | head -20", "description": "Find existing PARSE_DATE/PARSE_TIME tests"}
[tool_result] tests/dialects/test_duckdb.py:1825:            read={"bigquery": "SELECT DATE(PARSE_DATE('%m/%d/%Y', '05/06/2020'))"},
tests/dialects/test_duckdb.py:1896:                "bigquery": "PARSE_TIMESTAMP('%y-%-m', x)",
tests/dialects/test_duckdb.py:1915:                "bigquery": "PARSE_TIMESTAMP('%-m/%e/%y %-I:%M %p', x)",
tests/dialects/test_bigquery.py:53:            "SAFE.PARSE_DATE('%Y-%m-%d', '2024-01-15')",
tests/dialects/test_bigquery.py:54:            "SAFE.PARSE_DATE('%F', '2024-01-15')",

…[1141 chars elided]…
: "SELECT PARSE_TIMESTAMP('%Y%m%d', '20201225', 'America/New_York')"},
tests/dialects/test_bigquery.py:1112:            write={"bigquery": "SELECT PARSE_TIMESTAMP('%Y%m%d', '20201225')"},
tests/dialects/test_bigquery.py:1158:                "bigquery": "PARSE_DATE('%m/%d/%Y', x)",
tests/dialects/test_bigquery.py:1164:                "bigquery": "PARSE_TIMESTAMP('%Y.%m.%d %I:%M:%S%z', x)",
tests/dialects/test_bigquery.py:1725:            "SELECT PARSE_DATE('%A %b %e %Y', 'Thursday Dec 25 2008')",
[tool_use Bash] {"command": "sed -n 1815,1835p tests/dialects/test_duckdb.py", "description": "View surrounding DuckDB test context"}
[tool_result]             },
        )
        self.validate_all(
            "SELECT CAST(CAST('2024-01-15 23:30:00' AS TIMESTAMP) AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Berlin' AS DATE)",
            read={
                "bigquery": "SELECT DATE('2024-01-15 23:30:00', 'Europe/Berlin')",
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
        self.validate_all(
            "SELECT INTERVAL '1 quarter'",
            write={"duckdb": "SELECT INTERVAL '1' QUARTER"},
        )
        self.validate_all(
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-093751-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_duckdb.py", "old_string": "            read={\"bigquery\": \"SELECT DATE(PARSE_DATE('%m/%d/%Y', '05/06/2020'))\"},\n        )\n", "new_string": "            read={\"bigquery\": \"SELECT DATE(PARSE_DATE('%m/%d/%Y', '05/06/2020'))\"},\n        )\n        self.validate_all(\n            \"SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)\",\n            read={\"bigquery\": \"SELECT PARSE_TIME('%H:%M', '14:30')\"},\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-093751-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_duckdb.py has been updated successfully.
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
1112 passed, 18134 subtests passed in 49.91s
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/generators/duckdb.py tests/dialects/test_duckdb.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generators/duckdb.py tests/dialects/test_duckdb.py) 2>&1 | tail -5; git status --short", "description": "Lint changed files and show git status"}
[tool_result] All checks passed!
2 files already formatted
 M sqlglot/generators/duckdb.py
 M tests/dialects/test_duckdb.py
[assistant] `PARSE_TIME` now transpiles to DuckDB as a `TIME` cast around `STRPTIME`, the same way `PARSE_DATE` does:

```python
sqlglot.transpile("SELECT PARSE_TIME('%H:%M', '14:30')", read="bigquery", write="duckdb")
# ["SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
```

The change is a new `parsetime_sql` method in `sqlglot/generators/duckdb.py`, placed next to `strtodate_sql`. I also added a `validate_all` case for it in `tests/dialects/test_duckdb.py`, beside the `PARSE_DATE` case. The full suite passes (1112 tests) and ruff check and format are clean on both files.

I did not commit anything. The `safe` flag is not handled, because `ParseTime` has no `safe` argument.
