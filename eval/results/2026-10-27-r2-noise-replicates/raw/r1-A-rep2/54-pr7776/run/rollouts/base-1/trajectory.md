# trajectory base-1

final message:
`FROM_ISO8601_TIMESTAMP` now transpiles for every dialect, not just DuckDB. Your Snowflake example now gives:

```
SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
```

The full suite passes (1122 tests), and ruff check and format are clean.

I used a `CAST` to `TIMESTAMPTZ` rather than `TO_TIMESTAMP_TZ`. The cast preserves the offset the same way, and the generator already maps `TIMESTAMPTZ` to each dialect's native type. The results for other dialects are:

- **Snowflake / Postgres / DuckDB:** `CAST(... AS TIMESTAMPTZ)`
- **BigQuery / Spark:** `CAST(... AS TIMESTAMP)`, since they have no tz-aware timestamp type. Their timestamps are UTC-normalized, so the offset is still applied. I haven't verified this against a live engine.

Changes:

- **`sqlglot/generator.py`:** the base generator now has the `CAST(... AS TIMESTAMPTZ)` rewrite. This is the DuckDB logic moved up a level.
- **`sqlglot/generators/duckdb.py`:** removed the now-redundant override. DuckDB output is unchanged.
- **`sqlglot/generators/presto.py`:** added an override that keeps the function form. Without it, Presto and Trino would have started emitting the `CAST` as well, which breaks their round-trip.
- **`tests/dialects/test_presto.py`:** added Snowflake and BigQuery expectations to the existing `FROM_ISO8601_TIMESTAMP` test.

Nothing was run against a live Snowflake or BigQuery instance, so the semantics are verified by reasoning and the generated SQL, not by executing the queries.

## events
[tool_use Bash] {"command": "rg -n -i \"from_iso8601|FromISO8601\" sqlglot tests | head -50", "description": "Search for FROM_ISO8601 references"}
[tool_result] sqlglot/generators/duckdb.py:2679:    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:
sqlglot/expressions/temporal.py:436:class FromISO8601Timestamp(Expression, Func):
sqlglot/expressions/temporal.py:437:    _sql_names = ["FROM_ISO8601_TIMESTAMP"]
tests/dialects/test_presto.py:37:            "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
tests/dialects/test_presto.py:40:                "presto": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
[tool_use Bash] {"command": "sed -n 425,445p sqlglot/expressions/temporal.py && echo ---- && sed -n 2670,2695p sqlglot/generators/duckdb.py && echo ---- && sed -n 25,50p tests/dialects/test_presto.py && echo ---- && rg -n \"TO_TIMESTAMP_TZ|TimestampTZ|ToTimestamp\\b|class StrToTime|class TimeStrToTime|class UnixToTime\\b\" sqlglot/expressions/*.py | head -30", "description": "Inspect expression, duckdb generator, and tests"}
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
…[1687 chars elided]…

            write={
                "oracle": "CAST(x AS INTERVAL YEAR TO MONTH)",
                "presto": "CAST(x AS INTERVAL YEAR TO MONTH)",
            },
        )
        self.validate_all(
----
sqlglot/expressions/temporal.py:452:class StrToTime(Expression, Func):
sqlglot/expressions/temporal.py:464:class TimeStrToTime(Expression, Func):
sqlglot/expressions/temporal.py:504:class TsOrDsToTimestamp(Expression, Func):
sqlglot/expressions/temporal.py:528:class UnixToTime(Expression, Func):
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor d in ['snowflake','bigquery','spark','postgres','databricks','redshift','mysql','hive','clickhouse','tsql','oracle','doris','starrocks','athena','sqlite']:\n    try:\n        print(d, sqlglot.transpile(\\\"select from_iso8601_timestamp('2022-07-01T07:00:00+00:00')\\\", read='trino', write=d))\n    except Exception as e: print(d, 'ERR', e)\nprint(sqlglot.transpile(\\\"select cast('2022-07-01T07:00:00+00:00' as timestamptz)\\\", read='postgres', write='snowflake'))\n\"; rg -n \"fromiso|def timestamptz|TIMESTAMPTZ\" sqlglot/generator.py | head", "description": "Check current transpilation output across dialects"}
[tool_result] snowflake ["SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')"]
bigquery ["SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')"]
spark ["SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')"]
postgres ["SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')"]
databricks ["SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')"]
redshift ["SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')"]
mysql ["SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')"]
…[358 chars elided]…
s ["SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')"]
athena ["SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')"]
sqlite ["SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')"]
["SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)"]
384:    # Whether TIMETZ / TIMESTAMPTZ will be generated using the "WITH TIME ZONE" syntax
1758:            exp.DType.TIMESTAMPTZ,
5775:        start_ts = exp.cast(exp.Literal.string("1970-01-01 00:00:00+00"), to=exp.DType.TIMESTAMPTZ)
[tool_use Bash] {"command": "rg -n \"    def (f|g|h)[a-z0-9_]*_sql\\(\" sqlglot/generator.py | head -30", "description": "Locate generator methods near f-prefixed names"}
[tool_result] 1209:    def generatedasidentitycolumnconstraint_sql(
1242:    def generatedasrowcolumnconstraint_sql(
1508:    def heredoc_sql(self, expression: exp.Heredoc) -> str:
1572:    def hexstring_sql(
1888:    def fetch_sql(self, expression: exp.Fetch) -> str:
1905:    def filter_sql(self, expression: exp.Filter) -> str:
1917:    def hint_sql(self, expression: exp.Hint) -> str:
1982:    def hex_sql(self, expression: exp.Hex) -> str:
2105:    def fallbackproperty_sql(self, expression: exp.FallbackPrope
…[971 chars elided]…
   def gte_sql(self, expression: exp.GTE) -> str:
4568:    def function_fallback_sql(self, expression: exp.Func) -> str:
4970:    def generateembedding_sql(self, expression: exp.GenerateEmbedding) -> str:
4974:    def generatetext_sql(self, expression: exp.GenerateText) -> str:
4977:    def generatetable_sql(self, expression: exp.GenerateTable) -> str:
4980:    def generatebool_sql(self, expression: exp.GenerateBool) -> str:
4983:    def generateint_sql(self, expression: exp.GenerateInt) -> str:
[tool_use Bash] {"command": "sed -n 3985,3995p sqlglot/generator.py", "description": "View context around fromtimezone_sql"}
[tool_result]         this = self.sql(expression, "this")
        zone = self.sql(expression, "zone")
        return f"{this} AT TIME ZONE {zone}"

    def fromtimezone_sql(self, expression: exp.FromTimeZone) -> str:
        this = self.sql(expression, "this")
        zone = self.sql(expression, "zone")
        return f"{this} AT TIME ZONE {zone} AT TIME ZONE 'UTC'"

    def add_sql(self, expression: exp.Add) -> str:
        return self.binary(expression, "+")
[tool_use Bash] {"command": "ls sqlglot/dialects | head -80; rg -n \"function_fallback_sql|class Generator\" sqlglot/generators/presto.py sqlglot/generators/trino.py | head; rg -n \"FromISO8601|from_iso8601\" sqlglot/dialects sqlglot/generators | head", "description": "Inspect Presto and Trino generator structure"}
[tool_result] __init__.py
__pycache__
athena.py
bigquery.py
clickhouse.py
databricks.py
dialect.py
doris.py
dremio.py
drill.py
druid.py
duckdb.py
dune.py
exasol.py
fabric.py
hive.py
materialize.py
mysql.py
oracle.py
postgres.py
presto.py
prql.py
redshift.py
risingwave.py
singlestore.py
snowflake.py
solr.py
spark.py
spark2.py
sqlite.py
starrocks.py
tableau.py
teradata.py
trino.py
tsql.py
sqlglot/generators/presto.py:121:        return self.function_fallback_sql(expression)
sqlglot/generators/presto.py:489:        return self.function_fallback_sql(expression)
sqlglot/generators/duckdb.py:2679:    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:
[tool_use Bash] {"command": "sed -n 110,125p sqlglot/generators/presto.py; echo ----; sed -n 480,492p sqlglot/generators/presto.py; echo ----; rg -n \"    def [a-z]+_sql\" sqlglot/generators/presto.py | sed -n 1,200p | awk -F: '$2 ~ /def (f|g|h|e)/' ; echo; rg -n \"^class |def \\w+_sql\" sqlglot/generators/presto.py | head -5", "description": "View Presto generator snippets and method listing"}
[tool_result] def _first_last_sql(self: PrestoGenerator, expression: exp.Func) -> str:
    """
    Trino doesn't support FIRST / LAST as functions, but they're valid in the context
    of MATCH_RECOGNIZE, so we need to preserve them in that case. In all other cases
    they're converted into an ARBITRARY call.

    Reference: https://trino.io/docs/current/sql/match-recognize.html#logical-navigation-functions
    """
    if isinstance(expression.find_ancestor(exp.MatchRecognize, exp.Select), exp.MatchRecognize
…[539 chars elided]…
= expression.this
----
452:    def extract_sql(self, expression: exp.Extract) -> str:
639:    def groupconcat_sql(self, expression: exp.GroupConcat) -> str:

38:def _initcap_sql(self: PrestoGenerator, expression: exp.Initcap) -> str:
57:def _schema_sql(self: PrestoGenerator, expression: exp.Schema) -> str:
80:def _quantile_sql(self: PrestoGenerator, expression: exp.Quantile) -> str:
85:def _str_to_time_sql(
91:def _ts_or_ds_to_date_sql(self: PrestoGenerator, expression: exp.TsOrDsToDate) -> str:
[assistant] The fix belongs in the base generator: every dialect should get the `CAST(x AS TIMESTAMPTZ)` rewrite that DuckDB already uses, and the generator maps `TIMESTAMPTZ` per dialect. Presto/Trino must keep the function form, so they get an explicit override.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-103717-trino-snowflake-and-other-dialec/base-1/sqlglot/generator.py", "old_string": "        return f\"{this} AT TIME ZONE {zone} AT TIME ZONE 'UTC'\"\n\n    def add_sql(self, expression: exp.Add) -> str:", "new_string": "        return f\"{this} AT TIME ZONE {zone} AT TIME ZONE 'UTC'\"\n\n    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))\n\n    def add_sql(self, expression: exp.Add) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-103717-trino-snowflake-and-other-dialec/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-103717-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/duckdb.py", "old_string": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))\n\n    def strposition_sql", "new_string": "    def strposition_sql"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-103717-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-103717-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/presto.py", "old_string": "        return self.function_fallback_sql(expression)\n\n    def md5_sql(self, expression: exp.MD5) -> str:", "new_string": "        return self.function_fallback_sql(expression)\n\n    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.function_fallback_sql(expression)\n\n    def md5_sql(self, expression: exp.MD5) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-103717-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/presto.py has been updated successfully.
[assistant] Now I'll add a cross-dialect test next to the existing DuckDB one, then check the output.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-103717-trino-snowflake-and-other-dialec/base-1/tests/dialects/test_presto.py", "old_string": "                \"duckdb\": \"SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)\",\n                \"presto\": \"SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')\",\n            },\n        )", "new_string": "                \"duckdb\": \"SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)\",\n                \"presto\": \"SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')\",\n                \"snowflake\": \"SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)\",\n                \"bigquery\": \"SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMP)\",\n            },\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-103717-trino-snowflake-and-other-dialec/base-1/tests/dialects/test_presto.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor d in ['snowflake','bigquery','spark','postgres','duckdb','presto','trino']:\n    print(d, sqlglot.transpile(\\\"select from_iso8601_timestamp('2022-07-01T07:00:00+00:00')\\\", read='trino', write=d))\n\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_presto.py tests/dialects/test_duckdb.py 2>&1 | tail -5", "description": "Verify transpile output and run presto/duckdb tests"}
[tool_result] snowflake ["SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)"]
bigquery ["SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP)"]
spark ["SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP)"]
postgres ["SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)"]
duckdb ["SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)"]
presto ["SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')"]
trino ["SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')"]
................................................................                                                [100%]
64 passed, 1113 subtests passed in 0.33s
[assistant] Output is correct across dialects and the Presto/DuckDB tests pass. Running the full project suite now.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8", "description": "Run full project test suite"}
[tool_result] .................. [ 63%]
......................................................... [ 68%]
............................................... [ 72%]
.................................................................................................................................................................................................. [ 90%]
............................... [ 92%]
............................................................. [ 98%]
....................                                                                  [100%]
1122 passed, 18181 subtests passed in 49.93s
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff check sqlglot tests/dialects/test_presto.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot tests/dialects/test_presto.py 2>&1 | tail -3; git status --short", "description": "Run lint and format checks, show changed files"}
[tool_result] All checks passed!
177 files already formatted
 M sqlglot/generator.py
 M sqlglot/generators/duckdb.py
 M sqlglot/generators/presto.py
 M tests/dialects/test_presto.py
[assistant] `FROM_ISO8601_TIMESTAMP` now transpiles for every dialect, not just DuckDB. Your Snowflake example now gives:

```
SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
```

The full suite passes (1122 tests), and ruff check and format are clean.

I used a `CAST` to `TIMESTAMPTZ` rather than `TO_TIMESTAMP_TZ`. The cast preserves the offset the same way, and the generator already maps `TIMESTAMPTZ` to each dialect's native type. The results for other dialects are:

- **Snowflake / Postgres / DuckDB:** `CAST(... AS TIMESTAMPTZ)`
- **BigQuery / Spark:** `CAST(... AS TIMESTAMP)`, since they have
…[279 chars elided]…
oved up a level.
- **`sqlglot/generators/duckdb.py`:** removed the now-redundant override. DuckDB output is unchanged.
- **`sqlglot/generators/presto.py`:** added an override that keeps the function form. Without it, Presto and Trino would have started emitting the `CAST` as well, which breaks their round-trip.
- **`tests/dialects/test_presto.py`:** added Snowflake and BigQuery expectations to the existing `FROM_ISO8601_TIMESTAMP` test.

Nothing was run against a live Snowflake or BigQuery instance, so the semantics are verified by reasoning and the generated SQL, not by executing the queries.
