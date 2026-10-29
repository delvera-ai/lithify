# trajectory base-1

final message:
`FROM_ISO8601_TIMESTAMP` now transpiles to a timezone-aware conversion for every dialect, not just DuckDB. Snowflake gets `TO_TIMESTAMP_TZ`, and the rest get `CAST(... AS TIMESTAMPTZ)`, which each generator maps to its own type. The full suite passes (1122 tests) and ruff is clean.

```
trino → snowflake:  SELECT TO_TIMESTAMP_TZ('2022-07-01T07:00:00+00:00')
trino → duckdb:     SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
trino → bigquery:   SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP)
trino → tsql:       SELECT CAST('2022-07-01T07:00:00+00:00' AS DATETIMEOFFSET)
trino → presto:     SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')   (unchanged)
```

Changes:
- **`sqlglot/generator.py`**: the base generator now has `fromiso8601timestamp_sql`, which emits a cast to `TIMESTAMPTZ`. This moves the logic that was DuckDB-only up to the base class.
- **`sqlglot/generators/duckdb.py`**: removed the override, since the base method now does the same thing.
- **`sqlglot/generators/snowflake.py`**: overrides it to emit `TO_TIMESTAMP_TZ`, following your suggestion.
- **`sqlglot/generators/presto.py`**: a `rename_func` entry keeps Presto and Trino emitting `FROM_ISO8601_TIMESTAMP`. Without it, the existing Presto test fails because the base cast would leak into Presto output.
- **`tests/dialects/test_presto.py`**: added the Snowflake, Postgres and Spark expectations to the existing `validate_all` for this function. I did not weaken or change any existing expectation.

Dremio and SingleStore have no timezone-aware timestamp type, so sqlglot will warn that `TIMESTAMPTZ` is unsupported there, as it already does for other timezone casts. I did not commit; the changes are in the working tree.

## events
[tool_use Bash] {"command": "grep -rn \"FromISO8601\\|FROM_ISO8601\\|from_iso8601\" --include=*.py . | head -50", "description": "Search for FROM_ISO8601_TIMESTAMP references"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -n \"TO_TIMESTAMP\\|StrToTime\\|TimeStrToTime\\|class TimeToStr\" sqlglot/dialects/snowflake.py | head -40; grep -n \"ISO8601\\|iso8601\" sqlglot/dialects/duckdb.py sqlglot/dialects/presto.py sqlglot/dialects/trino.py sqlglot/expressions.py", "description": "Inspect Snowflake timestamp handling and ISO8601 refs"}
[tool_result ERROR] Exit code 2
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "git grep -n -i \"iso8601\" -- '*.py' | head -50; echo ---; git grep -n \"TO_TIMESTAMP\\|TimeStrToTime\" -- sqlglot/dialects/snowflake.py | head -40", "description": "Search code for ISO8601 and Snowflake timestamp handling"}
[tool_result] sqlglot/expressions/temporal.py:436:class FromISO8601Timestamp(Expression, Func):
sqlglot/expressions/temporal.py:437:    _sql_names = ["FROM_ISO8601_TIMESTAMP"]
sqlglot/generators/duckdb.py:2679:    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:
tests/dialects/test_presto.py:37:            "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
tests/dialects/test_presto.py:40:                "presto": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
---
[tool_use Bash] {"command": "sed -n 425,445p sqlglot/expressions/temporal.py; echo ---; sed -n 2670,2690p sqlglot/generators/duckdb.py; echo ---; sed -n 25,50p tests/dialects/test_presto.py; echo ---; ls sqlglot/dialects/ | head -80; echo ---; git grep -n \"TimeStrToTime\\|StrToTime\" -- sqlglot/generators/snowflake.py sqlglot/dialects/snowflake.py | head -30", "description": "Read FromISO8601Timestamp class, DuckDB generator, and tests"}
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
…[1786 chars elided]…
use.py
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
---
sqlglot/generators/snowflake.py:590:        exp.TimeStrToTime: timestrtotime_sql,
sqlglot/generators/snowflake.py:952:    def strtotime_sql(self, expression: exp.StrToTime):
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\ns=\\\"select from_iso8601_timestamp('2022-07-01T07:00:00+00:00')\\\"\nfor d in ['snowflake','postgres','bigquery','spark','databricks','hive','presto','trino','duckdb','mysql','tsql','oracle','redshift','clickhouse','doris','starrocks','athena','sqlite','te
…[373 chars elided]…
ke',write='duckdb'))\nprint(sqlglot.transpile(\\\"select cast(x as timestamptz)\\\",read='duckdb',write='bigquery'))\nprint(sqlglot.transpile(\\\"select cast(x as timestamptz)\\\",read='duckdb',write='spark'))\n\"; git grep -n \"TIMESTAMPTZ\\|TIMESTAMP_TZ\" -- sqlglot/generators/snowflake.py sqlglot/dialects/snowflake.py | head -20", "description": "Check current transpile output across dialects"}
[tool_result] snowflake SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
postgres SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
bigquery SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
spark SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
databricks SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
hive SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
presto SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
trino SELECT FROM_ISO8601_TIME
…[1017 chars elided]…
:00:00+00:00')
risingwave SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
singlestore SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
dremio SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
fabric SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
['SELECT CAST(x AS TIMESTAMPTZ)']
['SELECT TO_TIMESTAMP_TZ(x)']
['SELECT CAST(x AS TIMESTAMP)']
['SELECT CAST(x AS TIMESTAMP)']
sqlglot/dialects/snowflake.py:168:            "TIMESTAMP_TZ": TokenType.TIMESTAMPTZ,
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.dialects.dialect import Dialect\nfor d in sorted(Dialect.classes):\n    try:\n        print(d, sqlglot.transpile(\\\"SELECT CAST(x AS TIMESTAMPTZ)\\\",read='duckdb',write=d)[0], '|', sqlglot.transpile(\\\"SELECT TO_TIMESTAMP_TZ(x)\\\",read='sno
…[29 chars elided]…
ept Exception as e: print(d,'ERR',e)\nprint(sqlglot.parse_one(\\\"select to_timestamp_tz(x)\\\",read='snowflake').__repr__()[:300])\n\"; git grep -n \"TO_TIMESTAMP_TZ\\|TIMESTAMPTZ\" -- sqlglot/ | head -30; git grep -n \"def cast_sql\\|def fromiso\\|def timestamp_sql\" -- sqlglot/generator.py sqlglot/generators/ | head", "description": "Check TIMESTAMPTZ casts and TO_TIMESTAMP_TZ across dialects"}
[tool_result] Dremio does not support time-zone-aware TIMESTAMP
Data type TIMESTAMPTZ is not supported when targeting SingleStore
 SELECT CAST(x AS TIMESTAMPTZ) | SELECT TO_TIMESTAMP_TZ(x)
athena SELECT CAST(x AS TIMESTAMP WITH TIME ZONE) | SELECT TO_TIMESTAMP_TZ(x)
bigquery SELECT CAST(x AS TIMESTAMP) | SELECT TO_TIMESTAMP_TZ(x)
clickhouse SELECT CAST(x AS Nullable(DateTime)) | SELECT TO_TIMESTAMP_TZ(x)
databricks SELECT CAST(x AS TIMESTAMP) | SELECT TO_TIMESTAMP_TZ(x)
doris SELECT CAST(x AS DATETIME) | SELE
…[5462 chars elided]…
| None = None) -> str:
sqlglot/generators/mysql.py:689:    def cast_sql(self, expression: exp.Cast, safe_prefix: str | None = None) -> str:
sqlglot/generators/postgres.py:493:    def cast_sql(self, expression: exp.Cast, safe_prefix: str | None = None) -> str:
sqlglot/generators/redshift.py:328:    def cast_sql(self, expression: exp.Cast, safe_prefix: str | None = None) -> str:
sqlglot/generators/snowflake.py:749:    def cast_sql(self, expression: exp.Cast, safe_prefix: str | None = None) -> str:
[tool_use Bash] {"command": "git grep -n \"def [a-z]*timestamp[a-z_]*_sql\\|def [a-z]*date[a-z_]*_sql\" -- sqlglot/generator.py | head -30; echo ---; git grep -n \"def timestrtotime_sql\\|def strtotime_sql\\|def unixtotime_sql\" -- sqlglot/generators/snowflake.py; echo ---; git grep -n \"TO_TIMESTAMP_TZ\\|TO_TIMESTAMP\" -- tests/dialects/test_snowflake.py | head", "description": "Locate generator insertion points and Snowflake tests"}
[tool_result] sqlglot/generator.py:2647:    def update_sql(self, expression: exp.Update) -> str:
sqlglot/generator.py:4073:    def parsedatetime_sql(self, expression: exp.ParseDatetime) -> str:
sqlglot/generator.py:4081:    def currentdate_sql(self, expression: exp.CurrentDate) -> str:
sqlglot/generator.py:5087:    def tsordstotimestamp_sql(self, expression: exp.TsOrDsToTimestamp) -> str:
sqlglot/generator.py:5094:    def tsordstodatetime_sql(self, expression: exp.TsOrDsToDatetime) -> str:
sqlglot/generator.p
…[1275 chars elided]…
-15 12:30:00')",
tests/dialects/test_snowflake.py:641:        self.validate_identity("TRY_TO_TIMESTAMP('2024-01-15 12:30:00', 'AUTO')")
tests/dialects/test_snowflake.py:791:        self.validate_identity("TO_TIMESTAMP(col, fmt)")
tests/dialects/test_snowflake.py:882:            """SELECT TO_TIMESTAMP('2025-01-16T14:45:30.123+0500', 'yyyy-mm-DDThh24:mi:ss.ff9tzhtzm')"""
tests/dialects/test_snowflake.py:1242:            "SELECT TO_TIMESTAMP('2025-01-16 14:45:30.123', 'yyyy-mm-DD hh24:mi:ss.ff6')",
[tool_use Bash] {"command": "sed -n 4073,4082p sqlglot/generator.py; echo ---; sed -n 945,960p sqlglot/generators/snowflake.py; echo ---; sed -n 485,500p tests/dialects/test_snowflake.py", "description": "Read insertion context in generators and tests"}
[tool_result]     def parsedatetime_sql(self, expression: exp.ParseDatetime) -> str:
        return self.func(
            "PARSE_DATETIME",
            expression.this,
            expression.args.get("format"),
            expression.args.get("zone"),
        )

    def currentdate_sql(self, expression: exp.CurrentDate) -> str:
        zone = self.sql(expression, "this")
---
        copy_options = self.expressions(expression, key="copy_options", flat=True, sep=" ")
        copy_options = f" STAGE_COPY_OPTIO
…[1387 chars elided]…
ESTAMP(123.4)").selects[0].assert_is(exp.Anonymous)
        self.validate_identity("SELECT TO_TIMESTAMP(x) FROM t")
        self.validate_identity("SELECT TO_TIMESTAMP_NTZ(x) FROM t")
        self.validate_identity("SELECT TO_TIMESTAMP_LTZ(x) FROM t")
        self.validate_identity("SELECT TO_TIMESTAMP_TZ(x) FROM t")
        self.validate_identity("TO_DECIMAL(expr)", "TO_NUMBER(expr)")
        self.validate_identity("TO_DECIMAL(expr, fmt)", "TO_NUMBER(expr, fmt)")
        self.validate_identity(
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131303-trino-snowflake-and-other-dialec/base-1/sqlglot/generator.py", "old_string": "    def currentdate_sql(self, expression: exp.CurrentDate) -> str:\n        zone = self.sql(expression, \"this\")", "new_string": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))\n\n    def currentdate_sql(self, expression: exp.CurrentDate) -> str:\n        zone = self.sql(expression, \"this\")"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131303-trino-snowflake-and-other-dialec/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131303-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/duckdb.py", "old_string": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))\n\n    def strposition_sql", "new_string": "    def strposition_sql"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131303-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131303-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/snowflake.py", "old_string": "    def strtotime_sql(self, expression: exp.StrToTime):\n        # target_type", "new_string": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.func(\"TO_TIMESTAMP_TZ\", expression.this)\n\n    def strtotime_sql(self, expression: exp.StrToTime):\n        # target_type"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131303-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131303-trino-snowflake-and-other-dialec/base-1/tests/dialects/test_presto.py", "old_string": "                \"duckdb\": \"SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)\",\n                \"presto\": \"SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')\",", "new_string": "                \"du
…[1 chars elided]…
kdb\": \"SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)\",\n                \"presto\": \"SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')\",\n                \"snowflake\": \"SELECT TO_TIMESTAMP_TZ('2020-05-11T11:15:05')\",\n                \"postgres\": \"SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)\",\n                \"spark\": \"SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMP)\","}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131303-trino-snowflake-and-other-dialec/base-1/tests/dialects/test_presto.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ns=\\\"select from_iso8601_timestamp('2022-07-01T07:00:00+00:00')\\\"\nprint(sqlglot.transpile(s,read='trino',write='snowflake')[0])\nprint(sqlglot.transpile(s,read='trino',write='duckdb')[0])\nprint(sqlglot.transpile(s,read='trino',write='bigquery')[0])\nprint(sqlglot.transpile(s,read='trino',write='mysql')[0])\nprint(sqlglot.transpile(s,read='trino',write='tsql')[0])\n\"; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify example transpilations and run full test suite"}
[tool_result] SELECT TO_TIMESTAMP_TZ('2022-07-01T07:00:00+00:00')
SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP)
SELECT TIMESTAMP('2022-07-01T07:00:00+00:00')
SELECT CAST('2022-07-01T07:00:00+00:00' AS DATETIMEOFFSET)
............................................... [ 72%]
..................................................................................................................................................................................
…[503 chars elided]…
'2020-05-11T11:15:05' AS TIMESTAMP WITH TIME ZONE)" != "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')"
E   - SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMP WITH TIME ZONE)
E   + SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')
=========================== short test summary info ============================
SUBFAILED[SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05') -> presto] tests/dialects/test_presto.py::TestPresto::test_cast
1 failed, 1122 passed, 18181 subtests passed in 50.79s
[tool_use Bash] {"command": "git grep -n \"TRANSFORMS = {\" -A3 -- sqlglot/generators/presto.py | head; git grep -n \"rename_func\" -- sqlglot/generators/presto.py | head -5; git grep -n \"exp.FromISO8601Timestamp\\|FromISO8601\" -- sqlglot/dialects/trino.py sqlglot/generators/trino.py", "description": "Inspect Presto generator TRANSFORMS"}
[tool_result] fatal: unable to resolve revision: -A3
sqlglot/generators/presto.py:17:    rename_func,
sqlglot/generators/presto.py:123:    return rename_func("ARBITRARY")(self, expression)
sqlglot/generators/presto.py:130:        return rename_func("FROM_UNIXTIME")(self, expression)
sqlglot/generators/presto.py:260:        exp.AnyValue: rename_func("ARBITRARY"),
sqlglot/generators/presto.py:268:        exp.ArgMax: rename_func("MAX_BY"),
[tool_use Bash] {"command": "sed -n 255,300p sqlglot/generators/presto.py", "description": "Read Presto generator TRANSFORMS section"}
[tool_result]         exp.DType.TIMETZ: "TIME",
    }

    TRANSFORMS = {
        **generator.Generator.TRANSFORMS,
        exp.AnyValue: rename_func("ARBITRARY"),
        exp.ApproxQuantile: lambda self, e: self.func(
            "APPROX_PERCENTILE",
            e.this,
            e.args.get("weight"),
            e.args.get("quantile"),
            e.args.get("accuracy"),
        ),
        exp.ArgMax: rename_func("MAX_BY"),
        exp.ArgMin: rename_func("MIN_BY"),
        exp.Array: transforms.preproces
…[1346 chars elided]…
, e.this),
        exp.DateStrToDate: datestrtodate_sql,
        exp.DateToDi: lambda self, e: (
            f"CAST(DATE_FORMAT({self.sql(e, 'this')}, {type(self.dialect).DATEINT_FORMAT}) AS INT)"
        ),
        exp.DateSub: _date_delta_sql("DATE_ADD", negate_interval=True),
        exp.DayOfWeek: lambda self, e: f"(({self.func('DAY_OF_WEEK', e.this)} % 7) + 1)",
        exp.DayOfWeekIso: rename_func("DAY_OF_WEEK"),
        exp.Decode: lambda self, e: encode_decode_sql(self, e, "FROM_UTF8"),
[tool_use Bash] {"command": "grep -n \"exp.From\\|exp.Floor\\|exp.Get\" sqlglot/generators/presto.py | head", "description": "Find alphabetical insertion point in Presto TRANSFORMS"}
[tool_result] 307:        exp.FromTimeZone: lambda self, e: (
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131303-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/presto.py", "old_string": "        exp.FromTimeZone: lambda self, e: (", "new_string": "        exp.FromISO8601Timestamp: rename_func(\"FROM_ISO8601_TIMESTAMP\"),\n        exp.FromTimeZone: lambda self, e: ("}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131303-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/presto.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ns=\\\"select from_iso8601_timestamp('2022-07-01T07:00:00+00:00')\\\"\nprint(sqlglot.transpile(s,read='trino',write='snowflake')[0])\nprint(sqlglot.transpile(s,read='trino',write='trino')[0])\n\"; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4; git status --short", "description": "Re-verify example and run full test suite"}
[tool_result] SELECT TO_TIMESTAMP_TZ('2022-07-01T07:00:00+00:00')
SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
............................... [ 92%]
............................................................. [ 98%]
.....................                                                                 [100%]
1122 passed, 18182 subtests passed in 49.93s
 M sqlglot/generator.py
 M sqlglot/generators/duckdb.py
 M sqlglot/generators/presto.py
 M sqlglot/generators/snowflake.py
 M tests/dialects/test_presto.py
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/generator.py sqlglot/generators/duckdb.py sqlglot/generators/presto.py sqlglot/generators/snowflake.py tests/dialects/test_presto.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generator.py sqlglot/generators/duckdb.py sqlglot/generators/presto.py sqlglot/generators/snowflake.py tests/dialects/test_presto.py) 2>&1 | tail -5", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
5 files already formatted
[assistant] `FROM_ISO8601_TIMESTAMP` now transpiles to a timezone-aware conversion for every dialect, not just DuckDB. Snowflake gets `TO_TIMESTAMP_TZ`, and the rest get `CAST(... AS TIMESTAMPTZ)`, which each generator maps to its own type. The full suite passes (1122 tests) and ruff is clean.

```
trino → snowflake:  SELECT TO_TIMESTAMP_TZ('2022-07-01T07:00:00+00:00')
trino → duckdb:     SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
trino → bigquery:   SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP)
trino → tsql:       SELECT CAST('2022-07-01T07:00:00+00:00' AS DATETIMEOFFSET)
trino → pre
…[530 chars elided]…
`**: a `rename_func` entry keeps Presto and Trino emitting `FROM_ISO8601_TIMESTAMP`. Without it, the existing Presto test fails because the base cast would leak into Presto output.
- **`tests/dialects/test_presto.py`**: added the Snowflake, Postgres and Spark expectations to the existing `validate_all` for this function. I did not weaken or change any existing expectation.

Dremio and SingleStore have no timezone-aware timestamp type, so sqlglot will warn that `TIMESTAMPTZ` is unsupported there, as it already does for other timezone casts. I did not commit; the changes are in the working tree.
