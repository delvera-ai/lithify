# trajectory base-1

final message:
`PARSE_TIME` now transpiles to DuckDB as `CAST(STRPTIME(...) AS TIME)`, the same shape `PARSE_DATE` uses.

```python
sqlglot.transpile("SELECT PARSE_TIME('%H:%M', '14:30')", read="bigquery", write="duckdb")
# ["SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
```

- **Change:** added `parsetime_sql` to `sqlglot/generators/duckdb.py`, next to `strtodate_sql`. The method is auto-discovered by name, so no `TRANSFORMS` entry is needed. The BigQuery parser already builds `exp.ParseTime` for `PARSE_TIME`, so no parser change was needed.
- **Test:** added a `validate_all` in `tests/dialects/test_bigquery.py` that checks the BigQuery identity and the DuckDB output.
- **Verification:** the BigQuery and DuckDB test files pass. The full suite passed after the last edit (`SUMMARY: 1112 passed, 18135 subtests passed`, `EXIT: 0`). `ruff format` and `ruff check` are clean on both files.
- **Target validity:** `STRPTIME` returns a timestamp and casting it to `TIME` is valid in DuckDB. The `%H`, `%I`, `%M`, `%S` and `%p` specifiers are all supported by DuckDB's `strptime`.
- **Type:** `exp.ParseTime` is already annotated as `TIME` in the BigQuery typing, which matches the DuckDB output.

**Not fixed:** `SAFE.PARSE_TIME` and `SAFE.PARSE_DATE` still produce invalid DuckDB output. BigQuery's `SAFE.` prefix is parsed as a generic `SafeFunc` wrapper, and DuckDB gets `SAFE.STRPTIME(...)` or `SAFE.CAST(...)`. This predates my change and affects `PARSE_DATE` too, so I left it alone. Fixing it means changing how `SafeFunc` is handled, which is a separate change.

I did not commit anything.

## events
[tool_use Bash] {"command": "grep -rn \"PARSE_DATE\\|ParseDate\\|PARSE_TIME\\|ParseTime\\|TIME_FROM_PARTS\\|StrToTime\\b\" sqlglot/dialects/bigquery.py sqlglot/dialects/duckdb.py sqlglot/generators/duckdb.py sqlglot/parsers/bigquery.py sqlglot/generators/bigquery.py sqlglot/expressions/*.py | head -60; cat .lithify/harness/skills/sqlglot-dialect-functions/SKILL.md | head -80"}
[tool_result] sqlglot/parsers/bigquery.py:95:def _build_parse_timestamp(args: list, dialect: Dialect) -> exp.StrToTime:
sqlglot/parsers/bigquery.py:96:    this = build_formatted_time(exp.StrToTime)([seq_get(args, 1), seq_get(args, 0)], dialect)
sqlglot/parsers/bigquery.py:224:        "PARSE_DATE": lambda args, dialect: build_formatted_time(exp.StrToDate)(
sqlglot/parsers/bigquery.py:227:        "PARSE_TIME": lambda args, dialect: build_formatted_time(exp.ParseTime)(
sqlglot/parsers/bigquery.py:230:        "PA
…[7552 chars elided]…
date_add` in `sqlglot/parsers/hive.py`), which belongs to the Hive family.
- Keep the operation. A `*_SUB` call stays `exp.DateSub`. Do not rewrite it as an Add with a
  negated operand: that loses the function name on round-trip.
- Default units follow existing builders: `build_date_delta(..., default_unit=...)` in
  `sqlglot/dialects/dialect.py` fills the unit when it is absent. Extend or wrap the existing
  shared builder there (next to `build_date_delta_with_interval`) rather than creating a
[tool_use Bash] {"command": "sed -n 215,240p sqlglot/parsers/bigquery.py; sed -n 430,470p sqlglot/expressions/temporal.py; grep -n \"ParseTime\\|ParseDate\\|StrToDate\\|StrToTime\\|def strtotime_sql\\|def strtodate_sql\" -A12 sqlglot/generators/duckdb.py | sed -n 1,120p; grep -rn \"ParseTime\\|PARSE_TIME\" sqlglot/ tests/ | grep -v \"^sqlglot/expressions/temporal.py\" | head -30"}
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
…[7064 chars elided]…
kdb.py:1915:                "bigquery": "PARSE_TIMESTAMP('%-m/%e/%y %-I:%M %p', x)",
tests/fixtures/optimizer/annotate_functions.sql:1093:SAFE.PARSE_TIME('%H:%M:%S', '10:30:00');
tests/fixtures/optimizer/annotate_functions.sql:1097:SAFE.PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', '2024-01-15 10:30:00');
tests/fixtures/optimizer/annotate_functions.sql:1101:PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', '2024-01-15 10:30:00');
tests/fixtures/optimizer/annotate_functions.sql:1437:PARSE_TIME("%I:%M:%S", "07:30:00");
[tool_use Bash] {"command": "grep -rn \"PARSE_DATE\" tests/dialects/*.py | head; sed -n 1905,1925p tests/dialects/test_bigquery.py; grep -n \"def parsedate\\|ParseTime\\|StrToDate\" sqlglot/generators/duckdb.py sqlglot/typing/*.py | head; grep -n \"exp.DType.TIME\\b\\|DType.TIME:\" sqlglot/generators/duckdb.py | head -3"}
[tool_result] tests/dialects/test_dialect.py:801:                "presto": "TO_UNIXTIME(COALESCE(TRY(DATE_PARSE(CAST('2020-01-01' AS VARCHAR), '%Y-%m-%d')), PARSE_DATETIME(DATE_FORMAT(CAST('2020-01-01' AS TIMESTAMP), '%Y-%m-%d'), 'yyyy-MM-dd')))",
tests/dialects/test_bigquery.py:53:            "SAFE.PARSE_DATE('%Y-%m-%d', '2024-01-15')",
tests/dialects/test_bigquery.py:54:            "SAFE.PARSE_DATE('%F', '2024-01-15')",
tests/dialects/test_bigquery.py:57:            "SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S',
…[2055 chars elided]…
 strtodate_sql(self, expression: exp.StrToDate) -> str:
sqlglot/typing/__init__.py:78:            exp.DateStrToDate,
sqlglot/typing/__init__.py:81:            exp.StrToDate,
sqlglot/typing/__init__.py:82:            exp.TimeStrToDate,
sqlglot/typing/bigquery.py:283:            exp.ParseTime,
316:    this = exp.cast(expression.this, exp.DType.TIME)
317:    expr = exp.cast(expression.expression, exp.DType.TIME)
663:    if expression.is_type(exp.DType.TIME, exp.DType.TIMETZ, exp.DType.TIMESTAMPTZ):
[tool_use Bash] {"command": "sed -n 70,90p sqlglot/typing/__init__.py; sed -n 278,290p sqlglot/typing/bigquery.py; cat > /tmp/probe_pt.py <<'EOF'\nimport sqlglot\nfor sql in [\"SELECT PARSE_TIME('%H:%M', '14:30')\", \"SELECT PARSE_TIME('%I:%M:%S %p', col) FROM t\", \"SELECT SAFE.PARSE_TIME('%H:%M:%S', '10:30:00')\"]:\n    print(sqlglot.transpile(sql, read=\"bigquery\", write=\"duckdb\"))\nprint(repr(sqlglot.parse_one(\"SELECT PARSE_TIME('%H:%M', '14:30')\", read=\"bigquery\").selects[0]))\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_pt.py"}
[tool_result]         }
    },
    **{
        expr_type: {"returns": exp.DType.DATE}
        for expr_type in {
            exp.CurrentDate,
            exp.Date,
            exp.DateFromParts,
            exp.DateStrToDate,
            exp.DiToDate,
            exp.LastDay,
            exp.StrToDate,
            exp.TimeStrToDate,
            exp.TsOrDsToDate,
        }
    },
    **{
        expr_type: {"returns": exp.DType.DATETIME}
        for expr_type in {
            exp.CurrentDatetime,
            e
…[46 chars elided]…
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
["SELECT PARSE_TIME('14:30', '%H:%M')"]
["SELECT PARSE_TIME(col, '%I:%M:%S %p') FROM t"]
["SELECT SAFE.PARSE_TIME('10:30:00', '%H:%M:%S')"]
ParseTime(
  this=Literal(this='14:30', is_string=True),
  format=Literal(this='%H:%M', is_string=True))
[tool_use Bash] {"command": "grep -rn '\"SAFE\"\\|SAFE\\.' sqlglot/parsers/bigquery.py sqlglot/generators/bigquery.py sqlglot/generators/duckdb.py | head; cat > /tmp/probe_pd.py <<'EOF'\nimport sqlglot\nfor sql in [\"SELECT SAFE.PARSE_DATE('%Y-%m-%d', '2024-01-15')\", \"SELECT PARSE_DATE('%Y-%m-%d', '2024-01-15')\", \"SELECT SAFE.PARSE_TIMESTAMP('%Y', x)\"]:\n    print(sqlglot.transpile(sql, read=\"bigquery\", write=\"duckdb\"))\nprint(repr(sqlglot.parse_one(\"SELECT SAFE.PARSE_DATE('%Y-%m-%d', x)\", read=\"bigquery\").selects[0]))\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_pd.py"}
[tool_result] sqlglot/parsers/bigquery.py:723:            elif prefix == "SAFE":
["SELECT SAFE.CAST(STRPTIME('2024-01-15', '%Y-%m-%d') AS DATE)"]
["SELECT CAST(STRPTIME('2024-01-15', '%Y-%m-%d') AS DATE)"]
["SELECT SAFE.STRPTIME(x, '%Y')"]
SafeFunc(
  this=StrToDate(
    this=Column(
      this=Identifier(this=x, quoted=False)),
    format=Literal(this='%Y-%m-%d', is_string=True)))
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-100941-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py", "old_string": "    def tsordstotime_sql(self, expression: exp.TsOrDsToTime) -> str:", "new_string": "    def parsetime_sql(self, expression: exp.ParseTime) -> str:\n        formatted_time = self.format_time(expression)\n        return self.sql(\n            exp.cast(self.func(\"STRPTIME\", expression.this, formatted_time), exp.DType.TIME)\n        )\n\n    def tsordstotime_sql(self, expression: exp.TsOrDsToTime) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-100941-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Bash] {"command": "cat > /tmp/probe_pt2.py <<'EOF'\nimport sqlglot\nfrom sqlglot import exp\nfor sql in [\"SELECT PARSE_TIME('%H:%M', '14:30')\", \"SELECT PARSE_TIME('%I:%M:%S %p', col) FROM t\", \"SELECT PARSE_TIME('%H:%M:%S', x) AS t\"]:\n    print(sqlglot.transpile(sql, read=\"bigquery\", write=\"duckdb\"))\n    print(sqlglot.transpile(sql, read=\"bigquery\", write=\"bigquery\"))\n    print(sqlglot.t
…[640 chars elided]…
b\"))\nprint(sqlglot.parse_one(\"SELECT PARSE_TIME('%H:%M', '14:30')\", read=\"bigquery\").selects[0].type)\nprint(sqlglot.parse_one(\"SELECT PARSE_TIME('%H:%M', '14:30')\", read=\"bigquery\").selects[0].type)\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_pt2.py"}
[tool_result] ["SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
["SELECT PARSE_TIME('%H:%M', '14:30')"]
["SELECT PARSE_TIME('14:30', '%H:%M')"]
["SELECT CAST(STRPTIME(col, '%I:%M:%S %p') AS TIME) FROM t"]
["SELECT PARSE_TIME('%I:%M:%S %p', col) FROM t"]
["SELECT PARSE_TIME(col, '%I:%M:%S %p') FROM t"]
["SELECT CAST(STRPTIME(x, '%H:%M:%S') AS TIME) AS t"]
["SELECT PARSE_TIME('%T', x) AS t"]
["SELECT PARSE_TIME(x, '%H:%M:%S') AS t"]
ParseTime Literal
["SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
["SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
SELECT
  CAST(STRPTIME('14:30', '%H:%M') AS TIME)
SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)
None
None
[tool_use Bash] {"command": "grep -n 'PARSE_TIME(' tests/dialects/test_bigquery.py && sed -n 1150,1162p tests/dialects/test_bigquery.py"}
[tool_result] 1914:        self.validate_identity("PARSE_TIME('%I:%M:%S', '07:30:00')")
            write={
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-100941-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_bigquery.py", "old_string": "        self.validate_identity(\"PARSE_TIME('%I:%M:%S', '07:30:00')\")\n", "new_string": "        self.validate_identity(\"PARSE_TIME('%I:%M:%S', '07:30:00')\")\n        self.validate_all(\n            \"PARSE_TIME('%H:%M', '14:30')\",\n            write={\n                \"bigquery\": \"PARSE_TIME('%H:%M', '14:30')\",\n                \"duckdb\": \"CAST(STRPTIME('14:30', '%H:%M') AS TIME)\",\n            },\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-100941-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py 2>&1 | tail -5"}
[tool_result] ................... [ 18%]
.............................. [ 48%]
.....................................................                                        [100%]
102 passed, 1659 subtests passed in 0.57s
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] WARNING: 2 other pytest process(es) running; expect slower runs:
  34207 03-14:39:08 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
  72264       00:02 <work>/env-sqlglot/b
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-5eb2fd74e7.log
ELAPSED: 85s
SUMMARY: 1112 passed, 18135 subtests passed in 84.90s (0:01:24)
EXIT: 0
[tool_use Bash] {"command": "(ruff format --check sqlglot/generators/duckdb.py tests/dialects/test_bigquery.py; ruff check sqlglot/generators/duckdb.py tests/dialects/test_bigquery.py) 2>&1 | tail -3; git status --short"}
[tool_result] 2 files already formatted
All checks passed!
 M sqlglot/generators/duckdb.py
 M tests/dialects/test_bigquery.py
[assistant] `PARSE_TIME` now transpiles to DuckDB as `CAST(STRPTIME(...) AS TIME)`, the same shape `PARSE_DATE` uses.

```python
sqlglot.transpile("SELECT PARSE_TIME('%H:%M', '14:30')", read="bigquery", write="duckdb")
# ["SELECT CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
```

- **Change:** added `parsetime_sql` to `sqlglot/generators/duckdb.py`, next to `strtodate_sql`. The method is auto-discovered by name, so no `TRANSFORMS` entry is needed. The BigQuery parser already builds `exp.ParseTime` for `PARSE_TIME`, so no parser change was needed.
- **Test:** added a `validate_all` in `tests/dialects/test_big
…[391 chars elided]…
H`, `%I`, `%M`, `%S` and `%p` specifiers are all supported by DuckDB's `strptime`.
- **Type:** `exp.ParseTime` is already annotated as `TIME` in the BigQuery typing, which matches the DuckDB output.

**Not fixed:** `SAFE.PARSE_TIME` and `SAFE.PARSE_DATE` still produce invalid DuckDB output. BigQuery's `SAFE.` prefix is parsed as a generic `SafeFunc` wrapper, and DuckDB gets `SAFE.STRPTIME(...)` or `SAFE.CAST(...)`. This predates my change and affects `PARSE_DATE` too, so I left it alone. Fixing it means changing how `SafeFunc` is handled, which is a separate change.

I did not commit anything.
