# trajectory base-1

final message:
`FROM_ISO8601_TIMESTAMP` now transpiles for Snowflake and the other non-Presto dialects. The full suite passes (1122 tests), and I left the changes uncommitted.

Your example now gives:

- **Snowflake:** `SELECT TO_TIMESTAMP_TZ('2022-07-01T07:00:00+00:00')`
- **DuckDB / Postgres:** `CAST(... AS TIMESTAMPTZ)`, same as before
- **BigQuery / Spark:** `CAST(... AS TIMESTAMP)`, since those dialects have no separate tz-aware type in sqlglot's mapping
- **Trino / Presto:** unchanged, `FROM_ISO8601_TIMESTAMP(...)`

The changes:

- **`sqlglot/generator.py`:** the base generator now emits `CAST(x AS TIMESTAMPTZ)`. Every dialect inherits this, so the DuckDB-only override is gone; its output is identical.
- **`sqlglot/generators/presto.py`:** Presto and Trino keep the native function via `function_fallback_sql`, so they don't pick up the cast.
- **`sqlglot/generators/snowflake.py`:** emits `TO_TIMESTAMP_TZ`, the Snowflake function you pointed to.
- **`tests/dialects/test_presto.py`:** added a `validate_all` case covering the Trino input and the DuckDB, Snowflake, and Presto outputs.

The Snowflake and DuckDB outputs are checked by string comparison only; I did not run them against live databases.

## events
[tool_use Bash] {"command": "grep -rn -i \"iso8601\" sqlglot/ tests/ | head -50", "description": "Search for ISO8601 references in sqlglot and tests"}
[tool_result] sqlglot/expressions/temporal.py:436:class FromISO8601Timestamp(Expression, Func):
sqlglot/expressions/temporal.py:437:    _sql_names = ["FROM_ISO8601_TIMESTAMP"]
sqlglot/generators/duckdb.py:2679:    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:
tests/dialects/test_presto.py:37:            "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
tests/dialects/test_presto.py:40:                "presto": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
[tool_use Bash] {"command": "sed -n 425,445p sqlglot/expressions/temporal.py; echo ---; sed -n 2670,2690p sqlglot/generators/duckdb.py; echo ---; sed -n 30,50p tests/dialects/test_presto.py; echo ---; grep -rn \"TO_TIMESTAMP_TZ\\|TimeStrToTime\\|class StrToTime\\|class TimestampFromParts\" sqlglot/expressions/*.py | head; echo ---; grep -n \"TO_TIMESTAMP\\|def timestamp\\|TIMESTAMP_TZ\" sqlglot/generators/snowflake.py sqlglot/dialects/snowflake.py | head -40", "description": "Inspect the expression, DuckDB generator, test, and Snowflake timestamp code"}
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
…[2095 chars elided]…
            "TIMESTAMP_TZ": TokenType.TIMESTAMPTZ,
sqlglot/generators/snowflake.py:603:        exp.UnixToTime: lambda self, e: self.func("TO_TIMESTAMP", e.this, e.args.get("scale")),
sqlglot/generators/snowflake.py:741:    def timestampfromparts_sql(self, expression: exp.TimestampFromParts) -> str:
sqlglot/generators/snowflake.py:964:        func_name = TIMESTAMP_TYPES.get(type_enum, "TO_TIMESTAMP")
sqlglot/generators/snowflake.py:972:    def timestampsub_sql(self, expression: exp.TimestampSub):
[tool_use Bash] {"command": "sed -n 955,972p sqlglot/generators/snowflake.py; echo ---; grep -n \"TO_TIMESTAMP_TZ\\|TIMESTAMP_TZ\" sqlglot/generators/snowflake.py sqlglot/dialects/snowflake.py tests/dialects/test_snowflake.py | head -20; echo ---; grep -n \"class Generator\\|def function_fallback_sql\\|def timestampfromparts_sql\\|class Trino\\|class Presto\" sqlglot/generator.py sqlglot/generators/presto.py sqlglot/generators/trino.py sqlglot/dialects/trino.py sqlglot/dialects/presto.py 2>/dev/null; echo ---; ls <work>/env-sqlglot/bin/python && <work>/env-sqlglot/bin/python -c \"import sqlglot;print(sqlglot.__version__)\"", "description": "Inspect Snowflake timestamp generation, Presto/Trino generators, and test env"}
[tool_result]         # Get the type enum from DataType instance or from type annotation
        if isinstance(target_type, exp.DataType):
            type_enum = target_type.this
        elif expression.type:
            type_enum = expression.type.this
        else:
            type_enum = exp.DType.TIMESTAMP

        func_name = TIMESTAMP_TYPES.get(type_enum, "TO_TIMESTAMP")

        return self.func(
            f"{'TRY_' if expression.args.get('safe') else ''}{func_name}",
            expression.this,
  
…[1259 chars elided]…
28:59.999999+00:00'))""",
---
sqlglot/dialects/trino.py:9:class Trino(Presto):
sqlglot/generators/trino.py:14:class TrinoGenerator(PrestoGenerator):
sqlglot/generators/presto.py:210:class PrestoGenerator(generator.Generator):
sqlglot/generator.py:96:class Generator:
sqlglot/generator.py:4568:    def function_fallback_sql(self, expression: exp.Func) -> str:
sqlglot/dialects/presto.py:17:class Presto(Dialect):
---
<work>/env-sqlglot/bin/python
0.0.0+eval
[tool_use Bash] {"command": "grep -n \"    def f[a-z]*_sql\" sqlglot/generator.py | head -30; echo ---; grep -n \"    def f[a-z]*_sql\" sqlglot/generators/presto.py sqlglot/generators/snowflake.py | head; echo ---; grep -n \"def fromiso\\|fromiso\" sqlglot/generators/*.py", "description": "List nearby generator method definitions"}
[tool_result] 1888:    def fetch_sql(self, expression: exp.Fetch) -> str:
1905:    def filter_sql(self, expression: exp.Filter) -> str:
2105:    def fallbackproperty_sql(self, expression: exp.FallbackProperty) -> str:
2119:    def freespaceproperty_sql(self, expression: exp.FreespaceProperty) -> str:
2718:    def from_sql(self, expression: exp.From) -> str:
3262:    def forclause_sql(self, expression: exp.ForClause) -> str:
3693:    def foreignkey_sql(self, expression: exp.ForeignKey) -> str:
3767:    def for
…[459 chars elided]…
s/clickhouse.py:90:        # The first step to removing is parsing the string with `datetime.datetime.fromisoformat`.
sqlglot/generators/clickhouse.py:92:        # In python <3.11, `fromisoformat()` can only parse timestamps of millisecond (3 digit)
sqlglot/generators/clickhouse.py:121:            datetime.datetime.fromisoformat(ts_string).replace(tzinfo=None).isoformat(sep=" ")
sqlglot/generators/duckdb.py:2679:    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:
[tool_use Bash] {"command": "sed -n 3985,3995p sqlglot/generator.py; echo ---; sed -n 205,240p sqlglot/generators/presto.py", "description": "View insertion points in generator files"}
[tool_result]         this = self.sql(expression, "this")
        zone = self.sql(expression, "zone")
        return f"{this} AT TIME ZONE {zone}"

    def fromtimezone_sql(self, expression: exp.FromTimeZone) -> str:
        this = self.sql(expression, "this")
        zone = self.sql(expression, "zone")
        return f"{this} AT TIME ZONE {zone} AT TIME ZONE 'UTC'"

    def add_sql(self, expression: exp.Add) -> str:
        return self.binary(expression, "+")
---
                    column.parent.replace(exp
…[622 chars elided]…
MULTI_ARG_DISTINCT = False
    SUPPORTS_TO_NUMBER = False
    HEX_FUNC = "TO_HEX"
    PARSE_JSON_NAME: str | None = "JSON_PARSE"
    PAD_FILL_PATTERN_IS_REQUIRED = True
    EXCEPT_INTERSECT_SUPPORT_ALL_CLAUSE = False
    SUPPORTS_MEDIAN = False
    ARRAY_SIZE_NAME = "CARDINALITY"

    PROPERTIES_LOCATION = {
        **generator.Generator.PROPERTIES_LOCATION,
        exp.LocationProperty: exp.Properties.Location.UNSUPPORTED,
        exp.VolatileProperty: exp.Properties.Location.UNSUPPORTED,
    }
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-083235-trino-snowflake-and-other-dialec/base-1/sqlglot/generator.py", "old_string": "        return f\"{this} AT TIME ZONE {zone} AT TIME ZONE 'UTC'\"\n\n    def add_sql(self, expression: exp.Add) -> str:", "new_string": "        return f\"{this} AT TIME ZONE {zone} AT TIME ZONE 'UTC'\"\n\n    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))\n\n    def add_sql(self, expression: exp.Add) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-083235-trino-snowflake-and-other-dialec/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-083235-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/duckdb.py", "old_string": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))\n\n    def strposition_sql", "new_string": "    def strposition_sql"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-083235-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[assistant] Now Presto keeps the function (it's native there), and Snowflake gets its `TO_TIMESTAMP_TZ` equivalent. I'll find a method spot in the Presto generator first.
[tool_use Bash] {"command": "grep -n \"    def \" sqlglot/generators/presto.py | head -8; grep -n \"    def \" sqlglot/generators/snowflake.py | sed -n 1,12p", "description": "Find method positions in Presto and Snowflake generators"}
[tool_result] 148:    def _delta_sql(self: PrestoGenerator, expression: DATE_ADD_OR_SUB) -> str:
452:    def extract_sql(self, expression: exp.Extract) -> str:
477:    def jsonformat_sql(self, expression: exp.JSONFormat) -> str:
491:    def md5_sql(self, expression: exp.MD5) -> str:
504:    def strtounix_sql(self, expression: exp.StrToUnix) -> str:
525:    def bracket_sql(self, expression: exp.Bracket) -> str:
530:    def struct_sql(self, expression: exp.Struct) -> str:
560:    def interval_sql(self, expressi
…[350 chars elided]…
values_sql(self, expression: exp.Values, values_as_table: bool = True) -> str:
687:    def datatype_sql(self, expression: exp.DataType) -> str:
718:    def tonumber_sql(self, expression: exp.ToNumber) -> str:
741:    def timestampfromparts_sql(self, expression: exp.TimestampFromParts) -> str:
749:    def cast_sql(self, expression: exp.Cast, safe_prefix: str | None = None) -> str:
757:    def trycast_sql(self, expression: exp.TryCast) -> str:
773:    def log_sql(self, expression: exp.Log) -> str:
[tool_use Bash] {"command": "sed -n 490,492p sqlglot/generators/presto.py; sed -n 738,749p sqlglot/generators/snowflake.py", "description": "View insertion context in Presto and Snowflake"}
[tool_result]     def md5_sql(self, expression: exp.MD5) -> str:
        this = expression.this
            scale,
        )

    def timestampfromparts_sql(self, expression: exp.TimestampFromParts) -> str:
        milli = expression.args.get("milli")
        if milli is not None:
            milli_to_nano = milli.pop() * exp.Literal.number(1000000)
            expression.set("nano", milli_to_nano)

        return rename_func("TIMESTAMP_FROM_PARTS")(self, expression)

    def cast_sql(self, expression: exp.Cast, safe_prefix: str | None = None) -> str:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-083235-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/presto.py", "old_string": "    def md5_sql(self, expression: exp.MD5) -> str:\n        this = expression.this", "new_string": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.function_fallback_sql(expression)\n\n    def md5_sql(self, expression: exp.MD5) -> str:\n        this = expression.this"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-083235-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/presto.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-083235-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/snowflake.py", "old_string": "        return rename_func(\"TIMESTAMP_FROM_PARTS\")(self, expression)\n\n    def cast_sql(", "new_string": "        return rename_func(\"TIMESTAMP_FROM_PARTS\")(self, expression)\n\n    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.func(\"TO_TIMESTAMP_TZ\", expression.this)\n\n    def cast_sql("}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-083235-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[assistant] Now I'll add a test to the Presto dialect file (where the existing case lives) and run a quick check across dialects.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-083235-trino-snowflake-and-other-dialec/base-1/tests/dialects/test_presto.py", "old_string": "                \"presto\": \"SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')\",\n            },\n        )\n        self.validate_all(\n            \"CAST(x AS INTERVAL YEAR TO MONTH)\",", "new_string"
…[222 chars elided]…
            write={\n                \"duckdb\": \"SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)\",\n                \"snowflake\": \"SELECT TO_TIMESTAMP_TZ('2022-07-01T07:00:00+00:00')\",\n                \"presto\": \"SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')\",\n            },\n        )\n        self.validate_all(\n            \"CAST(x AS INTERVAL YEAR TO MONTH)\","}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-083235-trino-snowflake-and-other-dialec/base-1/tests/dialects/test_presto.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor d in ['snowflake','duckdb','bigquery','spark','postgres','trino','presto']:\n    print(d, '->', sqlglot.transpile(\\\"select from_iso8601_timestamp('2022-07-01T07:00:00+00:00')\\\", read='trino', write=d)[0])\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/ 2>&1 | tail -15", "description": "Check transpilation output across dialects and run dialect tests"}
[tool_result] snowflake -> SELECT TO_TIMESTAMP_TZ('2022-07-01T07:00:00+00:00')
duckdb -> SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
bigquery -> SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP)
spark -> SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP)
postgres -> SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
trino -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
presto -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
.................................. 
…[391 chars elided]…
........................... [ 53%]
...................................................... [ 61%]
................................................ [ 67%]
.................................................................................................................................................................. [ 89%]
..................................... [ 94%]
......................................                                             [100%]
736 passed, 11100 subtests passed in 2.53s
[assistant] Dialect tests pass. Running the full suite as the project harness specifies.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; git status --short", "description": "Run full test suite and show changed files"}
[tool_result] .................................................................................................................................................................................................. [ 89%]
............................... [ 92%]
............................................................. [ 98%]
.....................                                                                 [100%]
1122 passed, 18182 subtests passed in 51.45s
 M sqlglot/generator.py
 M sqlglot/generators/duckdb.py
 M sqlglot/generators/presto.py
 M sqlglot/generators/snowflake.py
 M tests/dialects/test_presto.py
[assistant] `FROM_ISO8601_TIMESTAMP` now transpiles for Snowflake and the other non-Presto dialects. The full suite passes (1122 tests), and I left the changes uncommitted.

Your example now gives:

- **Snowflake:** `SELECT TO_TIMESTAMP_TZ('2022-07-01T07:00:00+00:00')`
- **DuckDB / Postgres:** `CAST(... AS TIMESTAMPTZ)`, same as before
- **BigQuery / Spark:** `CAST(... AS TIMESTAMP)`, since those dialects have no separate tz-aware type in sqlglot's mapping
- **Trino / Presto:** unchanged, `FROM_ISO8601_TIMESTAMP(...)`

The changes:

- **`sqlglot/generator.py`:** the base generator now emits `CAST(x AS TIM
…[3 chars elided]…
AMPTZ)`. Every dialect inherits this, so the DuckDB-only override is gone; its output is identical.
- **`sqlglot/generators/presto.py`:** Presto and Trino keep the native function via `function_fallback_sql`, so they don't pick up the cast.
- **`sqlglot/generators/snowflake.py`:** emits `TO_TIMESTAMP_TZ`, the Snowflake function you pointed to.
- **`tests/dialects/test_presto.py`:** added a `validate_all` case covering the Trino input and the DuckDB, Snowflake, and Presto outputs.

The Snowflake and DuckDB outputs are checked by string comparison only; I did not run them against live databases.
