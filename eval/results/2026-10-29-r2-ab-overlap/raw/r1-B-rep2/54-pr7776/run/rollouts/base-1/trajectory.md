# trajectory base-1

final message:
`FROM_ISO8601_TIMESTAMP` now transpiles to a timezone-aware cast for every non-Presto/Trino dialect. The full suite passes (1122 passed), and ruff check and format are clean.

```python
sqlglot.parse_one("select from_iso8601_timestamp('2022-07-01T07:00:00+00:00')", "trino").sql("snowflake")
# SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
```

**What changed**
- `sqlglot/generator.py`: the base generator now has `fromiso8601timestamp_sql`, which emits `CAST(x AS TIMESTAMPTZ)`. I moved this from DuckDB, which already did the same thing, so every dialect inherits it.
- `sqlglot/generators/duckdb.py`: removed the override that is now in the base. DuckDB output is unchanged.
- `sqlglot/generators/presto.py`: added an override that keeps the `FROM_ISO8601_TIMESTAMP(...)` function form. Presto and Trino have this function natively, so their output stays the same.
- `tests/dialects/test_presto.py`: added a `validate_all` case covering DuckDB, Postgres, Snowflake and Trino round-trips.

**Choices to check**
- For Snowflake I used the generic `CAST(... AS TIMESTAMPTZ)` instead of `TO_TIMESTAMP_TZ`. It is valid Snowflake, it is the same conversion, and it keeps one code path. If you want `TO_TIMESTAMP_TZ` specifically, it is a small Snowflake-only override.
- Some dialects lose the offset. BigQuery, Spark, Hive and Databricks map the result to `TIMESTAMP`, which is an instant and so keeps the same moment in time. MySQL emits `TIMESTAMP('...')`, and ClickHouse emits `Nullable(DateTime)`, which drops the timezone. I did not special-case these.

## events
[tool_use Bash] {"command": "grep -rn -i \"FROM_ISO8601\\|FromISO8601\" sqlglot/ tests/ | head -50; echo ---; ls .lithify/harness/scripts/ 2>/dev/null", "description": "Search for FROM_ISO8601 references in code and tests"}
[tool_result] sqlglot/expressions/temporal.py:436:class FromISO8601Timestamp(Expression, Func):
sqlglot/expressions/temporal.py:437:    _sql_names = ["FROM_ISO8601_TIMESTAMP"]
sqlglot/generators/duckdb.py:2679:    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:
tests/dialects/test_presto.py:37:            "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
tests/dialects/test_presto.py:40:                "presto": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
---
probe_parse.py  2.2K
[tool_use Bash] {"command": "sed -n 425,445p sqlglot/expressions/temporal.py; echo ---; sed -n 2670,2690p sqlglot/generators/duckdb.py; echo ---; sed -n 30,50p tests/dialects/test_presto.py; echo ---; grep -rn \"ISO8601\\|iso8601\" sqlglot/ | grep -v \"^sqlglot/expressions/temporal.py:43[6-7]\" | head -30", "description": "Read the relevant expression, DuckDB generator, and tests"}
[tool_result]     pass


class DateToDi(Expression, Func):
    pass


class DiToDate(Expression, Func):
    pass


class FromISO8601Timestamp(Expression, Func):
    _sql_names = ["FROM_ISO8601_TIMESTAMP"]


class ParseDatetime(Expression, Func):
    arg_types = {"this": True, "format": False, "zone": False, "default_year": False}


class ParseTime(Expression, Func):
    arg_types = {"this": True, "format": True}
---
        from_clause = f" FROM {from_clause}" if from_clause else ""
        return f"{force}IN
…[1240 chars elided]…
             "presto": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
            },
        )
        self.validate_all(
            "CAST(x AS INTERVAL YEAR TO MONTH)",
            write={
                "oracle": "CAST(x AS INTERVAL YEAR TO MONTH)",
                "presto": "CAST(x AS INTERVAL YEAR TO MONTH)",
            },
        )
        self.validate_all(
---
sqlglot/generators/duckdb.py:2679:    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; cat .lithify/harness/scripts/probe_parse.py | head -30; echo ---; $P -c \"\nimport sqlglot\nfrom sqlglot import exp\ne=sqlglot.parse_one(\\\"select from_iso8601_timestamp('2022-07-01T07:00:00+00:00')\\\", 'trino')\nprint(repr(e.selects[0]))\n\" ; grep -n \"def cast_sql\\|def fromiso\\|TIMESTAMPTZ\" sqlglot/generator.py | head; grep -rln \"TIMESTAMPTZ\" sqlglot/generators/ | head -40", "description": "Confirm Trino parse tree and locate timestamptz handling"}
[tool_result] """Probe SQL statements for parse and round-trip failures with sqlglot.

Reads one SQL statement per line from stdin. Blank lines and lines starting with
`--` are skipped. Each statement is transpiled from --read to --write (--write
defaults to --read), then the output is transpiled again to check it is stable.

Prints, per statement:
  OK       output is stable; the next line is the output
  ERR      the error class and first line of the message; the statement failed
  UNSTABLE the output chang
…[1077 chars elided]…
t/generators/bigquery.py
sqlglot/generators/__pycache__/hive.cpython-312.pyc
sqlglot/generators/__pycache__/mysql.cpython-312.pyc
sqlglot/generators/__pycache__/presto.cpython-312.pyc
sqlglot/generators/doris.py
sqlglot/generators/hive.py
sqlglot/generators/tsql.py
sqlglot/generators/drill.py
sqlglot/generators/presto.py
sqlglot/generators/oracle.py
sqlglot/generators/exasol.py
sqlglot/generators/duckdb.py
sqlglot/generators/starrocks.py
sqlglot/generators/teradata.py
sqlglot/generators/mysql.py
[tool_use Bash] {"command": "grep -n \"^class \\|^from\\|^import\" sqlglot/generators/presto.py sqlglot/generators/trino.py | head; grep -n \"    def .*_sql(self, expression: exp.F\\|    def fromtimestamp\\|    def from_\\|    def formatdate\\|    def cast_sql\" sqlglot/generator.py | head -20; grep -n \"def function_fallback_sql\" sqlglot/generator.py", "description": "Inspect Presto/Trino generator classes and base method placement"}
[tool_result] 14 matches in 2 files:

sqlglot/generators/presto.py:1:from __future__ import annotations
sqlglot/generators/presto.py:3:import typing as t
sqlglot/generators/presto.py:5:from sqlglot import exp, generator, transforms
sqlglot/generators/presto.py:6:from sqlglot.dialects.dialect import (
sqlglot/generators/presto.py:30:from sqlglot.dialects.hive import Hive
sqlglot/generators/presto.py:31:from sqlglot.generator import unsupported_args
sqlglot/generators/presto.py:32:from sqlglot.optimizer.scope import find_all_in_scope
sqlglot/generators/presto.py:33:from sqlglot.transforms import unqualify_columns
rg: regex parse error:
    (?:    def .*_sql(self, expression: exp.F|    def fromtimestamp|    def from_|    def formatdate|    def cast_sql)
    ^
error: unclosed group
0 matches for '    def .*_sql(self, expression: exp.F\|    def fromtimestamp\|    def from_\|    def formatdate\|    def cast_sql'
1 matches in 1 files:

4568:0:exp.Func) -> str:
[tool_use Bash] {"command": "grep -n \"^class \\|    def .*_sql\" sqlglot/generators/presto.py | head -20; echo ---; grep -n \"^class \\|    def .*_sql\" sqlglot/generator.py | sed -n '1,400p' | grep -n \"fromt\\|from\\|formatdate\\|cast\\|dateadd\\|format\" | head -30; echo ---; grep -n \"class Trino\" -A3 sqlglot/dialects/trino.py; grep -n \"class Generator\" -A2 sqlglot/dialects/trino.py", "description": "List Presto generator methods and generic generator method names"}
[tool_result ERROR] Exit code 1
14 matches in 14 files:

148:0:PrestoGenerator, expression: DATE_ADD_OR_SUB) -> str:
210:0:
452:0:exp.Extract) -> str:
477:0:exp.JSONFormat) -> str:
491:0:exp.MD5) -> str:
504:0:exp.StrToUnix) -> str:
525:0:exp.Bracket) -> str:
530:0:exp.Struct) -> str:
560:0:exp.Interval) -> str:
565:0:exp.Transaction) -> str:
578:0:exp.Create) -> str:
589:0:exp.Delete) -> str:
611:0:exp.JSONExtract) -> str:
639:0:exp.GroupConcat) -> str:
---
---
9:class Trino(Presto):
10-    SUPPORTS_USER_DEFINED_TYPES = False
11-    LOG_BASE_FIRST = True
12-    CONCAT_WS_COALESCE = True
[tool_use Bash] {"command": "rtk proxy grep -n \"^class \\|    def .*_sql\" sqlglot/generators/presto.py | head -30; echo ---; rtk proxy grep -n \"    def cast_sql\\|    def function_fallback_sql\\|    def timestamptz\" sqlglot/generator.py", "description": "List Presto generator methods and base generator anchors"}
[tool_result] 148:    def _delta_sql(self: PrestoGenerator, expression: DATE_ADD_OR_SUB) -> str:
210:class PrestoGenerator(generator.Generator):
452:    def extract_sql(self, expression: exp.Extract) -> str:
477:    def jsonformat_sql(self, expression: exp.JSONFormat) -> str:
491:    def md5_sql(self, expression: exp.MD5) -> str:
504:    def strtounix_sql(self, expression: exp.StrToUnix) -> str:
525:    def bracket_sql(self, expression: exp.Bracket) -> str:
530:    def struct_sql(self, expression: exp.Struct)
…[73 chars elided]…

565:    def transaction_sql(self, expression: exp.Transaction) -> str:
578:    def create_sql(self, expression: exp.Create) -> str:
589:    def delete_sql(self, expression: exp.Delete) -> str:
611:    def jsonextract_sql(self, expression: exp.JSONExtract) -> str:
639:    def groupconcat_sql(self, expression: exp.GroupConcat) -> str:
---
4058:    def cast_sql(self, expression: exp.Cast, safe_prefix: str | None = None) -> str:
4568:    def function_fallback_sql(self, expression: exp.Func) -> str:
[tool_use Bash] {"command": "sed -n 4054,4058p sqlglot/generator.py; echo ---; sed -n 450,478p sqlglot/generators/presto.py", "description": "View insertion points in base generator and Presto generator"}
[tool_result]     def bitwisexor_sql(self, expression: exp.BitwiseXor) -> str:
        return self.binary(expression, "^")

    def cast_sql(self, expression: exp.Cast, safe_prefix: str | None = None) -> str:
---
    }

    def extract_sql(self, expression: exp.Extract) -> str:
        date_part = expression.name

        if not date_part.startswith("EPOCH"):
            return super().extract_sql(expression)

        if date_part == "EPOCH_MILLISECOND":
            scale = 10**3
        elif date_part == "EP
…[43 chars elided]…

        elif date_part == "EPOCH_NANOSECOND":
            scale = 10**9
        else:
            scale = None

        value = expression.expression

        ts = exp.cast(value, to=exp.DType.TIMESTAMP.into_expr())
        to_unix: exp.Expr = exp.TimeToUnix(this=ts)

        if scale:
            to_unix = exp.Mul(this=to_unix, expression=exp.Literal.number(scale))

        return self.sql(to_unix)

    def jsonformat_sql(self, expression: exp.JSONFormat) -> str:
        this = expression.this
[assistant] Trino/Presto has a native `FROM_ISO8601_TIMESTAMP`, so its generator must keep the function form. Everything else should fall back to a timezone-aware cast, which is what DuckDB already does. I'll move that logic into the base generator and keep Presto's output unchanged.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-165447-trino-snowflake-and-other-dialec/base-1/sqlglot/generator.py", "old_string": "    def cast_sql(self, expression: exp.Cast, safe_prefix: str | None = None) -> str:", "new_string": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))\n\n    def cast_sql(self, expression: exp.Cast, safe_prefix: str | None = None) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-165447-trino-snowflake-and-other-dialec/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-165447-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/duckdb.py", "old_string": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))\n\n    def strposition_sql", "new_string": "    def strposition_sql"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-165447-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-165447-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/presto.py", "old_string": "    def jsonformat_sql(self, expression: exp.JSONFormat) -> str:", "new_string": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.function_fallback_sql(expression)\n\n    def jsonformat_sql(self, expression: exp.JSONFormat) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-165447-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/presto.py has been updated successfully.
[assistant] Now I'll check the output across dialects and confirm the Presto/DuckDB behavior is unchanged.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nsql=\\\"select from_iso8601_timestamp('2022-07-01T07:00:00+00:00')\\\"\nfor d in ['snowflake','bigquery','spark','postgres','mysql','tsql','oracle','redshift','databricks','hive','clickhouse','trino','presto','duckdb']:\n    try: print(d, '=>', sqlglot.transpile(sql, read='trino', write=d)[0])\n    except Exception as e: print(d, 'ERR', e)\n\"", "description": "Transpile the Trino example across many dialects"}
[tool_result] snowflake => SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
bigquery => SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP)
spark => SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP)
postgres => SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
mysql => SELECT TIMESTAMP('2022-07-01T07:00:00+00:00')
tsql => SELECT CAST('2022-07-01T07:00:00+00:00' AS DATETIMEOFFSET)
oracle => SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP WITH TIME ZONE)
redshift => SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP WITH TIME ZONE)
databricks => SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP)
hive => SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP)
clickhouse => SELECT CAST('2022-07-01T07:00:00+00:00' AS Nullable(DateTime))
trino => SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
presto => SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
duckdb => SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
[assistant] Output looks right. Snowflake gets `CAST(... AS TIMESTAMPTZ)`, a valid Snowflake type, and Trino/Presto/DuckDB are unchanged. Next I'll add a regression test for the cross-dialect case and run the suite.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-165447-trino-snowflake-and-other-dialec/base-1/tests/dialects/test_presto.py", "old_string": "                \"presto\": \"SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')\",\n            },\n        )\n", "new_string": "                \"presto\": \"SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:
…[161 chars elided]…
={\n                \"duckdb\": \"SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)\",\n                \"postgres\": \"SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)\",\n                \"snowflake\": \"SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)\",\n                \"trino\": \"SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')\",\n            },\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-165447-trino-snowflake-and-other-dialec/base-1/tests/dialects/test_presto.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_presto.py tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py 2>&1 | tail -15; echo ==== FULL; timeout 600000 $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run dialect tests then the full pytest suite", "timeout": 600000}
[tool_result ERROR] Exit code 1
................................................................................................................................................. [ 90%]
...............                                      [100%]
160 passed, 2683 subtests passed in 0.69s
(eval):1: === not found
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run the full test suite", "timeout": 600000}
[tool_result] .................................. [  3%]
...................................................................... [  9%]
............................................. [ 13%]
.................................................................... [ 19%]
..................... [ 21%]
.............. [ 22%]
................................................................. [ 28%]
................................................................................ [ 35%]
.......................................
…[381 chars elided]…
............................................. [ 72%]
.................................................................................................................................................................................................. [ 89%]
............................... [ 92%]
............................................................. [ 98%]
......................                                                                [100%]
1122 passed, 18183 subtests passed in 45.88s
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/ruff check sqlglot/generator.py sqlglot/generators/presto.py sqlglot/generators/duckdb.py tests/dialects/test_presto.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/generator.py sqlglot/generators/presto.py sqlglot/generators/duckdb.py tests/dialects/test_presto.py) 2>&1 | tail -5; git status --short", "description": "Lint and format-check changed files; show git status"}
[tool_result] All checks passed!
4 files already formatted
 M sqlglot/generator.py
 M sqlglot/generators/duckdb.py
 M sqlglot/generators/presto.py
 M tests/dialects/test_presto.py
[assistant] `FROM_ISO8601_TIMESTAMP` now transpiles to a timezone-aware cast for every non-Presto/Trino dialect. The full suite passes (1122 passed), and ruff check and format are clean.

```python
sqlglot.parse_one("select from_iso8601_timestamp('2022-07-01T07:00:00+00:00')", "trino").sql("snowflake")
# SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
```

**What changed**
- `sqlglot/generator.py`: the base generator now has `fromiso8601timestamp_sql`, which emits `CAST(x AS TIMESTAMPTZ)`. I moved this from DuckDB, which already did the same thing, so every dialect inherits it.
- `sqlglot/generato
…[366 chars elided]…
s, Snowflake and Trino round-trips.

**Choices to check**
- For Snowflake I used the generic `CAST(... AS TIMESTAMPTZ)` instead of `TO_TIMESTAMP_TZ`. It is valid Snowflake, it is the same conversion, and it keeps one code path. If you want `TO_TIMESTAMP_TZ` specifically, it is a small Snowflake-only override.
- Some dialects lose the offset. BigQuery, Spark, Hive and Databricks map the result to `TIMESTAMP`, which is an instant and so keeps the same moment in time. MySQL emits `TIMESTAMP('...')`, and ClickHouse emits `Nullable(DateTime)`, which drops the timezone. I did not special-case these.
