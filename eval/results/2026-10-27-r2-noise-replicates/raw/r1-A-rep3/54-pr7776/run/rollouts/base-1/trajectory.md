# trajectory base-1

final message:
`FROM_ISO8601_TIMESTAMP` now transpiles to Snowflake as `TO_TIMESTAMP_TZ(...)`, and other dialects get a timezone-aware `CAST(... AS TIMESTAMPTZ)`. The full suite passes (1122 tests), and ruff lint and format are clean. I haven't committed anything.

```python
sqlglot.parse_one("select from_iso8601_timestamp('2022-07-01T07:00:00+00:00')", "trino").sql("snowflake")
# "SELECT TO_TIMESTAMP_TZ('2022-07-01T07:00:00+00:00')"
```

What changed:
- **`sqlglot/generator.py`**: the base generator gets a `fromiso8601timestamp_sql` fallback that casts to `TIMESTAMPTZ`. Every dialect without its own handling picks this up, so Spark, BigQuery, Postgres and the rest now emit a real cast instead of the bare function. The cast is rendered through each dialect's own type mapping, so Spark and BigQuery give `TIMESTAMP`.
- **`sqlglot/generators/snowflake.py`**: a Snowflake override emits `TO_TIMESTAMP_TZ`, following the TO_TIMESTAMP-family convention you suggested.
- **`sqlglot/generators/presto.py`**: a Presto/Trino override keeps the native `FROM_ISO8601_TIMESTAMP`. Without it, the base fallback would have rewritten Presto and Trino output too.
- **`sqlglot/generators/duckdb.py`**: removed the DuckDB-only method. The base fallback produces the identical `CAST(... AS TIMESTAMPTZ)`.
- **`tests/dialects/test_presto.py`**: added a new `validate_all` block for the Snowflake, BigQuery, Spark, Postgres, DuckDB, Presto and Trino outputs. The existing test is unchanged.

One caveat: for the fallback dialects, the result depends on how each one maps `TIMESTAMPTZ`. Spark and Databricks map it to `TIMESTAMP`, which is session-zone aware, so the offset is preserved as an instant. I didn't check the semantics of each target beyond that.

## events
[tool_use Bash] {"command": "grep -rn -i \"iso8601\\|FromISO8601\" sqlglot/ tests/ | head -50", "description": "Search for ISO8601 references in source and tests"}
[tool_result] sqlglot/expressions/temporal.py:436:class FromISO8601Timestamp(Expression, Func):
sqlglot/expressions/temporal.py:437:    _sql_names = ["FROM_ISO8601_TIMESTAMP"]
sqlglot/generators/duckdb.py:2679:    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:
tests/dialects/test_presto.py:37:            "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
tests/dialects/test_presto.py:40:                "presto": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
[tool_use Bash] {"command": "sed -n 425,445p sqlglot/expressions/temporal.py && echo ---- && sed -n 2670,2700p sqlglot/generators/duckdb.py && echo ---- && sed -n 25,50p tests/dialects/test_presto.py && echo ---- && grep -rn \"TO_TIMESTAMP_TZ\\|TIMESTAMPTZ\\|TimeStrToTime\\|class StrToTime\" sqlglot/generators/snowflake.py | head -20", "description": "Inspect expression, DuckDB generator, and Presto tests"}
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
----
        from_clause = f" FROM {from_clause}" if from_clause else ""
        return f"{force}I
…[1699 chars elided]…
5-11T11:15:05' AS TIMESTAMPTZ)",
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
----
sqlglot/generators/snowflake.py:590:        exp.TimeStrToTime: timestrtotime_sql,
[tool_use Bash] {"command": "grep -rn \"TO_TIMESTAMP_TZ\\|TIMESTAMPTZ\" sqlglot/ | grep -v \"^sqlglot/dialects/tsql\\|bigquery\" | head -40; echo ----; grep -n \"def timestrtotime_sql\" -A12 sqlglot/generators/snowflake.py; echo ----; grep -n \"class Presto\\|class Trino\" -A3 sqlglot/dialects/*.py | head; echo ----; git log --oneline -3 -- sqlglot/generators/duckdb.py | head -3", "description": "Find timestamptz handling across generators"}
[tool_result] sqlglot/tokenizer_core.py:166:    TIMESTAMPTZ = auto()
sqlglot/generator.py:384:    # Whether TIMETZ / TIMESTAMPTZ will be generated using the "WITH TIME ZONE" syntax
sqlglot/generator.py:1758:            exp.DType.TIMESTAMPTZ,
sqlglot/generator.py:5775:        start_ts = exp.cast(exp.Literal.string("1970-01-01 00:00:00+00"), to=exp.DType.TIMESTAMPTZ)
sqlglot/tokens.py:494:        "TIMESTAMPTZ": TokenType.TIMESTAMPTZ,
sqlglot/parser.py:517:        TokenType.TIMESTAMPTZ,
sqlglot/parser.py:867:   
…[3291 chars elided]…
SQL.TIME_FORMAT
sqlglot/dialects/trino.py:9:class Trino(Presto):
sqlglot/dialects/trino.py-10-    SUPPORTS_USER_DEFINED_TYPES = False
sqlglot/dialects/trino.py-11-    LOG_BASE_FIRST = True
sqlglot/dialects/trino.py-12-    CONCAT_WS_COALESCE = True
----
12eba761a feat(duckdb): Add transpilation support for Snowflake STARTS WITH ... CONNECT BY (#7709)
6f4a99035 chore(parser): PARSE_DATETIME uses year as default (#7743)
a28815065 feat(duckdb): Add transpilation support for TRY_CAST INTERVAL (#7731)
[tool_use Bash] {"command": "sed -n 60,90p sqlglot/parsers/snowflake.py; echo ----; grep -n \"CAST_TO_FUNC\\|TO_TIMESTAMP\" sqlglot/generators/snowflake.py | head; echo ----; grep -rn \"FromISO8601\\|from_iso8601\" tests/ sqlglot/ | grep -v \"^tests/dialects/test_presto\" ; echo ----; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor d in ['snowflake','duckdb','spark','bigquery','postgres','presto','databricks']:\n    print(d, sqlglot.parse_one(\\\"select CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)\\\", 'duckdb').sql(d))\n\"", "description": "Check Snowflake cast mappings and experiment with cast output"}
[tool_result]     )


def _build_date_from_parts(args: list) -> exp.DateFromParts:
    return exp.DateFromParts(
        year=seq_get(args, 0),
        month=seq_get(args, 1),
        day=seq_get(args, 2),
        allow_overflow=True,
    )


# Timestamp types used in _build_datetime
TIMESTAMP_TYPES = {
    exp.DType.TIMESTAMP: "TO_TIMESTAMP",
    exp.DType.TIMESTAMPLTZ: "TO_TIMESTAMP_LTZ",
    exp.DType.TIMESTAMPNTZ: "TO_TIMESTAMP_NTZ",
    exp.DType.TIMESTAMPTZ: "TO_TIMESTAMP_TZ",
}


def _build_datetime(na
…[826 chars elided]…
on: exp.FromISO8601Timestamp) -> str:
----
snowflake SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
duckdb SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
spark SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP)
bigquery SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP)
postgres SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
presto SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP WITH TIME ZONE)
databricks SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP)
[tool_use Bash] {"command": "sed -n 945,985p sqlglot/generators/snowflake.py; grep -n \"TIMESTAMP_TYPES\\|_build_datetime(\" sqlglot/parsers/snowflake.py | head -3; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.parse_one(\\\"select CAST(x AS TIMESTAMPTZ)\\\", 'duckdb').sql('snowflake'))\nprint(sqlglot.parse_one(\\\"select TO_TIMESTAMP_TZ('2022-07-01T07:00:00+00:00')\\\", 'snowflake').sql('duckdb'))\nprint(sqlglot.parse_one(\\\"select TO_TIMESTAMP_TZ(x)\\\", 'snowflake').sql('snowflake'))\n\"", "description": "Inspect Snowflake cast-to-function logic"}
[tool_result]         copy_options = self.expressions(expression, key="copy_options", flat=True, sep=" ")
        copy_options = f" STAGE_COPY_OPTIONS = ({copy_options})" if copy_options else ""
        tag = self.expressions(expression, key="tag", flat=True)
        tag = f" TAG {tag}" if tag else ""

        return f"SET{exprs}{file_format}{copy_options}{tag}"

    def strtotime_sql(self, expression: exp.StrToTime):
        # target_type is stored as a DataType instance
        target_type = expression.args
…[828 chars elided]…
    )
        )

    def jsonextract_sql(self, expression: exp.JSONExtract):
        this = expression.this

        # JSON strings are valid coming from other dialects such as BQ so
        # for these cases we PARSE_JSON preemptively
73:TIMESTAMP_TYPES = {
81:def _build_datetime(name: str, kind: exp.DType, safe: bool = False) -> t.Callable:
103:            if kind in TIMESTAMP_TYPES:
SELECT CAST(x AS TIMESTAMPTZ)
SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
SELECT TO_TIMESTAMP_TZ(x)
[tool_use Bash] {"command": "grep -n \"def function_fallback_sql\\|def fromiso\\|def from_\\|def fromunixtime\\|def func(\" sqlglot/generator.py | head; echo ----; grep -n \"_sql(self\" sqlglot/generators/presto.py | head -80; echo ----; grep -n \"class Generator\" -A3 sqlglot/generators/presto.py; grep -n \"def timestrtotime_sql\\|def strtotime_sql\\|def cast_sql\" sqlglot/generators/snowflake.py sqlglot/generator.py", "description": "Locate generator helpers and Presto generator methods"}
[tool_result] 2718:    def from_sql(self, expression: exp.From) -> str:
4568:    def function_fallback_sql(self, expression: exp.Func) -> str:
4587:    def func(
----
38:def _initcap_sql(self: PrestoGenerator, expression: exp.Initcap) -> str:
57:def _schema_sql(self: PrestoGenerator, expression: exp.Schema) -> str:
80:def _quantile_sql(self: PrestoGenerator, expression: exp.Quantile) -> str:
91:def _ts_or_ds_to_date_sql(self: PrestoGenerator, expression: exp.TsOrDsToDate) -> str:
95:        return self.sql(ex
…[1724 chars elided]…
ct) -> str:
639:    def groupconcat_sql(self, expression: exp.GroupConcat) -> str:
----
sqlglot/generator.py:4058:    def cast_sql(self, expression: exp.Cast, safe_prefix: str | None = None) -> str:
sqlglot/generator.py:4070:    def strtotime_sql(self, expression: exp.StrToTime) -> str:
sqlglot/generators/snowflake.py:749:    def cast_sql(self, expression: exp.Cast, safe_prefix: str | None = None) -> str:
sqlglot/generators/snowflake.py:952:    def strtotime_sql(self, expression: exp.StrToTime):
[tool_use Bash] {"command": "sed -n 4056,4072p sqlglot/generator.py; echo ----; sed -n 500,525p sqlglot/generators/presto.py; echo ----; sed -n 4566,4586p sqlglot/generator.py; echo; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.parse_one(\\\"select from_iso8601_timestamp('2022-07-01T07:00:00+00:00')\\\", 'trino').sql('presto'))\nprint(sqlglot.parse_one(\\\"select from_iso8601_timestamp('2022-07-01T07:00:00+00:00')\\\", 'trino').sql('duckdb'))\nprint(sqlglot.parse_one(\\\"select from_iso8601_timestamp('2022-07-01T07:00:00+00:00')\\\", 'trino').sql('athena'))\"", "description": "Read base cast and fallback helpers; baseline outputs"}
[tool_result]         return self.binary(expression, "^")

    def cast_sql(self, expression: exp.Cast, safe_prefix: str | None = None) -> str:
        format_sql = self.sql(expression, "format")
        format_sql = f" FORMAT {format_sql}" if format_sql else ""
        to_sql = self.sql(expression, "to")
        to_sql = f" {to_sql}" if to_sql else ""
        action = self.sql(expression, "action")
        action = f" {action}" if action else ""
        default = self.sql(expression, "default")
        defau
…[2210 chars elided]…
           args.append(value)
            elif arg_value is not None:
                args.append(arg_value)

        if self.dialect.PRESERVE_ORIGINAL_NAMES:
            name = expression.meta_get("name") or expression.sql_name()
        else:
            name = expression.sql_name()

        return self.func(name, *args)


SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ns=\\\"SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')\\\"\nfor d in ['snowflake','spark','bigquery','postgres','databricks','redshift','mysql','tsql','clickhouse']:\n    print(d, sqlglot.parse_one(s,'presto').sql(d))\nprint(sqlglot.parse_one(\\\"SELECT FROM_ISO8601_TIMESTAMP(x)\\\",'presto').sql('snowflake'))\n\"", "description": "Check candidate outputs across dialects"}
[tool_result] snowflake SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
spark SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
bigquery SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
postgres SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
databricks SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
redshift SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
mysql SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
tsql SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
clickhouse SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
SELECT FROM_ISO8601_TIMESTAMP(x)
[assistant] Baseline confirmed: every non-DuckDB dialect emits the bare function. Now the edits: a base-generator fallback (cast to `TIMESTAMPTZ`), a Presto override that keeps the native function, a Snowflake `TO_TIMESTAMP_TZ` override, and removing the now-redundant DuckDB method.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-141942-trino-snowflake-and-other-dialec/base-1/sqlglot/generator.py", "old_string": "    # Base implementation that excludes safe, zone, and target_type metadata args\n    def strtotime_sql(self, expression: exp.StrToTime) -> str:", "new_string": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))\n\n    # Base implementation that excludes safe, zone, and target_type metadata args\n    def strtotime_sql(self, expression: exp.StrToTime) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-141942-trino-snowflake-and-other-dialec/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-141942-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/duckdb.py", "old_string": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))\n\n", "new_string": ""}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-141942-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-141942-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/presto.py", "old_string": "    def strtounix_sql(self, expression: exp.StrToUnix) -> str:", "new_string": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.function_fallback_sql(expression)\n\n    def strtounix_sql(self, expression: exp.StrToUnix) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-141942-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/presto.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-141942-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/snowflake.py", "old_string": "    def strtotime_sql(self, expression: exp.StrToTime):", "new_string": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.func(\"TO_TIMESTAMP_TZ\", expression.this)\n\n    def strtotime_sql(self, expression: exp.StrToTime):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-141942-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[assistant] Now a new test in the Presto test file (added alongside the existing case, not modifying it), then a check of the outputs.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-141942-trino-snowflake-and-other-dialec/base-1/tests/dialects/test_presto.py", "old_string": "                \"presto\": \"SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')\",\n            },\n        )\n", "new_string": "                \"presto\": \"SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:
…[427 chars elided]…
MPTZ)\",\n                \"snowflake\": \"SELECT TO_TIMESTAMP_TZ('2022-07-01T07:00:00+00:00')\",\n                \"spark\": \"SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP)\",\n                \"presto\": \"SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')\",\n                \"trino\": \"SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')\",\n            },\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-141942-trino-snowflake-and-other-dialec/base-1/tests/dialects/test_presto.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ns=\\\"select from_iso8601_timestamp('2022-07-01T07:00:00+00:00')\\\"\nfor d in ['snowflake','duckdb','spark','presto','trino','athena']:\n    print(d, sqlglot.parse_one(s,'trino').sql(d))\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify outputs and run the full test suite"}
[tool_result] snowflake SELECT TO_TIMESTAMP_TZ('2022-07-01T07:00:00+00:00')
duckdb SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
spark SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP)
presto SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
trino SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
athena SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
................................................................................ [ 35%]
..............................
…[403 chars elided]…
..................... [ 72%]
....................................................................................................... [ 81%]
................................................................... [ 87%]
........................ [ 89%]
.................................................................. [ 95%]
.......................... [ 97%]
.................. [ 99%]
.......                                                             [100%]
1122 passed, 18186 subtests passed in 56.91s
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/generator.py sqlglot/generators/ tests/dialects/test_presto.py 2>&1; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generator.py sqlglot/generators/duckdb.py sqlglot/generators/presto.py sqlglot/generators/snowflake.py tests/dialects/test_presto.py 2>&1) | tail -5; git status --short", "description": "Run ruff lint and format checks on changed files"}
[tool_result] All checks passed!
5 files already formatted
 M sqlglot/generator.py
 M sqlglot/generators/duckdb.py
 M sqlglot/generators/presto.py
 M sqlglot/generators/snowflake.py
 M tests/dialects/test_presto.py
[assistant] `FROM_ISO8601_TIMESTAMP` now transpiles to Snowflake as `TO_TIMESTAMP_TZ(...)`, and other dialects get a timezone-aware `CAST(... AS TIMESTAMPTZ)`. The full suite passes (1122 tests), and ruff lint and format are clean. I haven't committed anything.

```python
sqlglot.parse_one("select from_iso8601_timestamp('2022-07-01T07:00:00+00:00')", "trino").sql("snowflake")
# "SELECT TO_TIMESTAMP_TZ('2022-07-01T07:00:00+00:00')"
```

What changed:
- **`sqlglot/generator.py`**: the base generator gets a `fromiso8601timestamp_sql` fallback that casts to `TIMESTAMPTZ`. Every dialect without its own handlin
…[533 chars elided]…
utput too.
- **`sqlglot/generators/duckdb.py`**: removed the DuckDB-only method. The base fallback produces the identical `CAST(... AS TIMESTAMPTZ)`.
- **`tests/dialects/test_presto.py`**: added a new `validate_all` block for the Snowflake, BigQuery, Spark, Postgres, DuckDB, Presto and Trino outputs. The existing test is unchanged.

One caveat: for the fallback dialects, the result depends on how each one maps `TIMESTAMPTZ`. Spark and Databricks map it to `TIMESTAMP`, which is session-zone aware, so the offset is preserved as an instant. I didn't check the semantics of each target beyond that.
