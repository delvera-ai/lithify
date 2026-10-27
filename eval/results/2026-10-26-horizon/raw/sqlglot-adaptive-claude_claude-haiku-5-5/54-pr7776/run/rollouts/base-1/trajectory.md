# trajectory base-1

final message:
`FROM_ISO8601_TIMESTAMP` now transpiles to each dialect's timezone-aware timestamp conversion. The full suite passes (1122 tests), and ruff check and format are clean.

```
trino → snowflake:  SELECT TO_TIMESTAMP_TZ('2022-07-01T07:00:00+00:00')
trino → duckdb:     SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
trino → postgres:   SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
trino → oracle:     SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP WITH TIME ZONE)
trino → tsql:       SELECT CAST('2022-07-01T07:00:00+00:00' AS DATETIMEOFFSET)
trino → bigquery:   SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP)
```

Changes:

- **`sqlglot/generator.py`**: the base generator now has `fromiso8601timestamp_sql`, which emits `CAST(x AS TIMESTAMPTZ)`. Every dialect inherits it, and each dialect's own type mapping decides the final type name.
- **`sqlglot/generators/duckdb.py`**: removed the override, since the base method now does the same thing.
- **`sqlglot/generators/presto.py`**: added an override that keeps `FROM_ISO8601_TIMESTAMP`, because Presto and Trino have that function natively. Trino inherits it.
- **`sqlglot/generators/snowflake.py`**: emits `TO_TIMESTAMP_TZ(x)`, as you suggested.
- **`tests/dialects/test_presto.py`**: added Snowflake and Postgres expectations to the existing `FROM_ISO8601_TIMESTAMP` case.

Choices you may want to revisit:

- I used the base-generator cast as the default instead of a per-dialect override for each target. That covers the long tail, but a dialect whose `TIMESTAMPTZ` maps to a plain `TIMESTAMP` (BigQuery, Spark, MySQL, Teradata) loses the offset. That matches how the rest of the codebase already maps those types, but it is a semantic loss for those targets.
- MySQL gets `TIMESTAMP('...')`. I did not check that against MySQL's documented behavior for offset-bearing strings.

I didn't commit anything.

## events
[tool_use Bash] {"command": "rg -n -i \"FromISO8601|from_iso8601\" sqlglot tests | head -50", "description": "Search for FROM_ISO8601 references"}
[tool_result] tests/dialects/test_presto.py:37:            "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
tests/dialects/test_presto.py:40:                "presto": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
sqlglot/generators/duckdb.py:2679:    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:
sqlglot/expressions/temporal.py:436:class FromISO8601Timestamp(Expression, Func):
sqlglot/expressions/temporal.py:437:    _sql_names = ["FROM_ISO8601_TIMESTAMP"]
[tool_use Bash] {"command": "sed -n 425,445p sqlglot/expressions/temporal.py && echo ---- && sed -n 2665,2700p sqlglot/generators/duckdb.py && echo ---- && rg -n \"TO_TIMESTAMP|ToTimestamp|TIMESTAMP_TZ|StrToTime|TimeStrToTime|AtTimeZone\" sqlglot/generators/snowflake.py | head -40 && echo ---- && sed -n 25,50p tests/dialects/test_presto.py", "description": "Inspect expression, DuckDB generator, Snowflake refs, tests"}
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

    def install_sql(self, expression: exp.Install) -> str:
        force = "FORCE " if expre
…[2221 chars elided]…
0-05-11T11:15:05')",
            write={
                "duckdb": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)",
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
[tool_use Bash] {"command": "rg -n \"TO_TIMESTAMP_TZ|TIMESTAMP_TZ|TIMESTAMPTZ\" sqlglot/ | head -40; echo ----; rg -n \"class Generator|TRANSFORMS = \\{|def cast_sql|def fromiso|_sql\\(self, expression\" sqlglot/generator.py | head -20; echo ----; rg -n \"class Generator|^from|^import\" sqlglot/generators/presto.py | head; echo ----; source /dev/null; ls <work>/env-sqlglot/bin/python 2>&1; python3 -c \"import sqlglot,sys;print(sqlglot.__file__)\" 2>&1", "description": "Find TIMESTAMPTZ handling and generator structure"}
[tool_result] sqlglot/generators/mysql.py:251:        exp.DType.TIMESTAMPTZ: "TIMESTAMP",
sqlglot/generators/mysql.py:271:        exp.DType.TIMESTAMPTZ: "TIMESTAMP",
sqlglot/generators/mysql.py:334:        exp.DType.TIMESTAMPTZ,
sqlglot/parser.py:517:        TokenType.TIMESTAMPTZ,
sqlglot/parser.py:867:        TokenType.TIMESTAMPTZ,
sqlglot/parser.py:934:        TokenType.TIMESTAMPTZ,
sqlglot/parser.py:6170:                    data_type = exp.DType.TIMESTAMPTZ.into_expr()
sqlglot/parser.py:6365:              
…[5000 chars elided]…
lect import (
30:from sqlglot.dialects.hive import Hive
31:from sqlglot.generator import unsupported_args
32:from sqlglot.optimizer.scope import find_all_in_scope
33:from sqlglot.transforms import unqualify_columns
----
<work>/env-sqlglot/bin/python
~/.cache/lithify/work/repo-161bf5b46800/20261027-102119-trino-snowflake-and-other-dialec/base-1/sqlglot/__init__.py
[tool_use Bash] {"command": "rg -n \"    def (f|g)[a-z_]*_sql\\(\" sqlglot/generator.py | head -30; echo ----; rg -n \"class Generator|class Trino|FROM_ISO|TRANSFORMS\" sqlglot/generators/trino.py | head; echo ----; rg -n \"    def [a-z]*_sql\\(\" sqlglot/generators/snowflake.py | head -5; echo ----; rg -n \"def function_fallback_sql\" sqlglot/generator.py", "description": "Locate insertion points in generators"}
[tool_result] 1209:    def generatedasidentitycolumnconstraint_sql(
1242:    def generatedasrowcolumnconstraint_sql(
1888:    def fetch_sql(self, expression: exp.Fetch) -> str:
1905:    def filter_sql(self, expression: exp.Filter) -> str:
2105:    def fallbackproperty_sql(self, expression: exp.FallbackProperty) -> str:
2119:    def freespaceproperty_sql(self, expression: exp.FreespaceProperty) -> str:
2718:    def from_sql(self, expression: exp.From) -> str:
2721:    def groupingsets_sql(self, expression: exp
…[1597 chars elided]…
r):
21:    TRANSFORMS = {
22:        **PrestoGenerator.TRANSFORMS,
----
620:    def sortarray_sql(self, expression: exp.SortArray) -> str:
627:    def nthvalue_sql(self, expression: exp.NthValue) -> str:
681:    def values_sql(self, expression: exp.Values, values_as_table: bool = True) -> str:
687:    def datatype_sql(self, expression: exp.DataType) -> str:
718:    def tonumber_sql(self, expression: exp.ToNumber) -> str:
----
4568:    def function_fallback_sql(self, expression: exp.Func) -> str:
[tool_use Bash] {"command": "sed -n 3985,3995p sqlglot/generator.py; echo ----; rg -n \"^class PrestoGenerator|    def [a-z]*_sql\\(\" sqlglot/generators/presto.py | head -5; echo ----; sed -n 716,722p sqlglot/generators/snowflake.py", "description": "View generator insertion context"}
[tool_result]         this = self.sql(expression, "this")
        zone = self.sql(expression, "zone")
        return f"{this} AT TIME ZONE {zone}"

    def fromtimezone_sql(self, expression: exp.FromTimeZone) -> str:
        this = self.sql(expression, "this")
        zone = self.sql(expression, "zone")
        return f"{this} AT TIME ZONE {zone} AT TIME ZONE 'UTC'"

    def add_sql(self, expression: exp.Add) -> str:
        return self.binary(expression, "+")
----
210:class PrestoGenerator(generator.Generato
…[69 chars elided]…
7:    def jsonformat_sql(self, expression: exp.JSONFormat) -> str:
504:    def strtounix_sql(self, expression: exp.StrToUnix) -> str:
525:    def bracket_sql(self, expression: exp.Bracket) -> str:
----
        return super().datatype_sql(expression)

    def tonumber_sql(self, expression: exp.ToNumber) -> str:
        precision = expression.args.get("precision")
        scale = expression.args.get("scale")

        default_precision = isinstance(precision, exp.Literal) and precision.name == "38"
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-102119-trino-snowflake-and-other-dialec/base-1/sqlglot/generator.py", "old_string": "    def fromtimezone_sql(self, expression: exp.FromTimeZone) -> str:\n        this = self.sql(expression, \"this\")\n        zone = self.sql(expression, \"zone\")\n        return f\"{this} AT TIME ZONE {zone} AT TIME
…[29 chars elided]…
": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))\n\n    def fromtimezone_sql(self, expression: exp.FromTimeZone) -> str:\n        this = self.sql(expression, \"this\")\n        zone = self.sql(expression, \"zone\")\n        return f\"{this} AT TIME ZONE {zone} AT TIME ZONE 'UTC'\"\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-102119-trino-snowflake-and-other-dialec/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now remove the DuckDB-only copy (it's identical to the new base method), and keep Presto/Trino emitting the native function.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-102119-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/duckdb.py", "old_string": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))\n\n    def strposition_sql", "new_string": "    def strposition_sql"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-102119-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Bash] {"command": "rg -n \"TRANSFORMS = \\{\" sqlglot/generators/presto.py && sed -n 210,216p sqlglot/generators/presto.py && sed -n 452,454p sqlglot/generators/presto.py && rg -n \"^class |    def [a-z]*_sql\\(\" sqlglot/generators/snowflake.py | sed -n 1,3p", "description": "Inspect Presto and Snowflake generator layout"}
[tool_result] 258:    TRANSFORMS = {
class PrestoGenerator(generator.Generator):
    SELECT_KINDS: tuple[str, ...] = ()
    SUPPORTS_DECODE_CASE = False

    AFTER_HAVING_MODIFIER_TRANSFORMS = generator.AFTER_HAVING_MODIFIER_TRANSFORMS

    INTERVAL_ALLOWS_PLURAL_FORM = False
    def extract_sql(self, expression: exp.Extract) -> str:
        date_part = expression.name

375:class SnowflakeGenerator(generator.Generator):
620:    def sortarray_sql(self, expression: exp.SortArray) -> str:
627:    def nthvalue_sql(self, expression: exp.NthValue) -> str:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-102119-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/presto.py", "old_string": "    def extract_sql(self, expression: exp.Extract) -> str:\n        date_part = expression.name", "new_string": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.function_fallback_sql(expression)\n\n    def extract_sql(self, expression: exp.Extract) -> str:\n        date_part = expression.name"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-102119-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/presto.py has been updated successfully.
[assistant] Now Snowflake gets the `TO_TIMESTAMP_TZ` form you suggested, since it's the native timezone-aware parser there.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-102119-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/snowflake.py", "old_string": "    def sortarray_sql(self, expression: exp.SortArray) -> str:", "new_string": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.func(\"TO_TIMESTAMP_TZ\", expression.this)\n\n    def sortarray_sql(self, expression: exp.SortArray) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-102119-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[assistant] Now let me check the behavior across dialects and add tests to the Presto test file, which already covers this function.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nq=\\\"select from_iso8601_timestamp('2022-07-01T07:00:00+00:00')\\\"\nfor d in ['snowflake','duckdb','bigquery','spark','postgres','oracle','tsql','trino','presto','mysql']:\n    print(d, '->', sqlglot.transpile(q, read='trino', write=d)[0])\n\"", "description": "Check transpiled output across dialects"}
[tool_result] snowflake -> SELECT TO_TIMESTAMP_TZ('2022-07-01T07:00:00+00:00')
duckdb -> SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
bigquery -> SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP)
spark -> SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP)
postgres -> SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
oracle -> SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP WITH TIME ZONE)
tsql -> SELECT CAST('2022-07-01T07:00:00+00:00' AS DATETIMEOFFSET)
trino -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
presto -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
mysql -> SELECT TIMESTAMP('2022-07-01T07:00:00+00:00')
[assistant] Output looks right for all targets. Adding Snowflake and the other common targets to the existing test:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-102119-trino-snowflake-and-other-dialec/base-1/tests/dialects/test_presto.py", "old_string": "            write={\n                \"duckdb\": \"SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)\",\n                \"presto\": \"SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')\",\n            },", "new_string": "            write={\n                \"duckdb\": \"SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)\",\n                \"presto\": \"SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')\",\n                \"snowflake\": \"SELECT TO_TIMESTAMP_TZ('2020-05-11T11:15:05')\",\n                \"postgres\": \"SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)\",\n            },"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-102119-trino-snowflake-and-other-dialec/base-1/tests/dialects/test_presto.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/ tests/test_transpile.py tests/test_generator.py 2>&1 | tail -15", "description": "Run dialect and generator test suites"}
[tool_result] ............................................. [ 19%]
.................................................................... [ 28%]
..................... [ 30%]
.............. [ 32%]
................................................................. [ 41%]
................................................................................ [ 51%]
...................................................... [ 58%]
............................................................. [ 66%]
....................... [ 69%]
................................................................................................................... [ 84%]
............................................ [ 90%]
.................. [ 92%]
....................................................... [ 99%]
...                                                                    [100%]
770 passed, 12123 subtests passed in 2.70s
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; $PY -m ruff check sqlglot tests/dialects/test_presto.py 2>&1 | tail -2; $PY -m ruff format --check sqlglot tests/dialects/test_presto.py 2>&1 | tail -2", "description": "Run full test suite and lint checks"}
[tool_result] ............................................................. [ 98%]
....................                                                                  [100%]
1122 passed, 18181 subtests passed in 55.90s
All checks passed!
177 files already formatted
[assistant] `FROM_ISO8601_TIMESTAMP` now transpiles to each dialect's timezone-aware timestamp conversion. The full suite passes (1122 tests), and ruff check and format are clean.

```
trino → snowflake:  SELECT TO_TIMESTAMP_TZ('2022-07-01T07:00:00+00:00')
trino → duckdb:     SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
trino → postgres:   SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
trino → oracle:     SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP WITH TIME ZONE)
trino → tsql:       SELECT CAST('2022-07-01T07:00:00+00:00' AS DATETIMEOFFSET)
trino → bigquery:   SELECT CAST('20
…[690 chars elided]…
stgres expectations to the existing `FROM_ISO8601_TIMESTAMP` case.

Choices you may want to revisit:

- I used the base-generator cast as the default instead of a per-dialect override for each target. That covers the long tail, but a dialect whose `TIMESTAMPTZ` maps to a plain `TIMESTAMP` (BigQuery, Spark, MySQL, Teradata) loses the offset. That matches how the rest of the codebase already maps those types, but it is a semantic loss for those targets.
- MySQL gets `TIMESTAMP('...')`. I did not check that against MySQL's documented behavior for offset-bearing strings.

I didn't commit anything.
