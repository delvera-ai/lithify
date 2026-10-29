# trajectory base-1

final message:
`FROM_ISO8601_TIMESTAMP` now transpiles to every non-Presto dialect. Your Snowflake example gives `SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)`. The full suite passes (1122 tests), and ruff lint and format checks are clean.

**What changed**
- **`sqlglot/generator.py`**: the base generator now handles `FromISO8601Timestamp` by emitting `CAST(... AS TIMESTAMPTZ)`. Each dialect maps `TIMESTAMPTZ` to its own type, so this covers the other dialects too.
- **`sqlglot/generators/duckdb.py`**: removed its override, which was identical to the new base method.
- **`sqlglot/generators/presto.py`**: added an explicit override that keeps `FROM_ISO8601_TIMESTAMP(...)`. Trino and Athena inherit it, so they still emit the native function.
- **`tests/dialects/test_presto.py`**: added Snowflake and Postgres expectations to the existing `FROM_ISO8601_TIMESTAMP` test.

**Choices you may want to revisit**
- **Snowflake uses `CAST(... AS TIMESTAMPTZ)` rather than `TO_TIMESTAMP_TZ(...)`.** Snowflake accepts `TIMESTAMPTZ` as an alias for `TIMESTAMP_TZ`, and the result is the same for a string input. I went with the cast because it reuses the existing type mapping and matches the DuckDB behaviour. Switching to `TO_TIMESTAMP_TZ` would mean adding a dedicated generator method.
- **MySQL and StarRocks emit `TIMESTAMP('...')`, which drops the UTC offset.** Neither has a timezone-aware timestamp type, so this is the closest equivalent sqlglot already produces for a `TIMESTAMPTZ` cast in those dialects. The same loss happens for `CAST(x AS TIMESTAMPTZ)` today. If you want that case to be stricter, it needs a separate decision.
- **SingleStore gets a `:>` cast and an unsupported-type warning**, which is the existing behaviour for `TIMESTAMPTZ` there.

I didn't add Snowflake to a live database, so the Snowflake output is verified against the generator and its type mapping, not against a running Snowflake instance.

## events
[tool_use Bash] {"command": "grep -rn -i \"iso8601_timestamp\\|FromISO8601\\|from_iso8601\" sqlglot/ tests/ | head -50", "description": "Search for FROM_ISO8601_TIMESTAMP references"}
[tool_result] sqlglot/expressions/temporal.py:436:class FromISO8601Timestamp(Expression, Func):
sqlglot/expressions/temporal.py:437:    _sql_names = ["FROM_ISO8601_TIMESTAMP"]
sqlglot/generators/duckdb.py:2679:    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:
tests/dialects/test_presto.py:37:            "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
tests/dialects/test_presto.py:40:                "presto": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
[tool_use Bash] {"command": "sed -n 425,450p sqlglot/expressions/temporal.py && echo ---- && sed -n 2665,2700p sqlglot/generators/duckdb.py && echo ---- && sed -n 25,50p tests/dialects/test_presto.py && echo ---- && grep -n \"TO_TIMESTAMP_TZ\\|TimestampTz\\|StrToTime\\|class UnixToTime\\|class TimeStrToTime\" sqlglot/expressions/*.py | head -30", "description": "Read relevant expression, generator, and test code"}
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


class StrToDate(Expression, Func):
    arg_types = {"this": True, "format": False, "safe": False
…[2529 chars elided]…
import TimeStrToTime as _TimeStrToTime
sqlglot/expressions/core.py:2397:return _TimeStrToTime(this=datetime_literal, zone=tz)
sqlglot/expressions/temporal.py:400:class TimestampTzFromParts(Expression, Func):
sqlglot/expressions/temporal.py:452:class StrToTime(Expression, Func):
sqlglot/expressions/temporal.py:464:class TimeStrToTime(Expression, Func):
sqlglot/expressions/temporal.py:528:class UnixToTime(Expression, Func):
sqlglot/expressions/temporal.py:551:class UnixToTimeStr(Expression, Func):
[tool_use Bash] {"command": "ls; PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sqlglot\nfrom sqlglot import exp\nsql=\\\"select from_iso8601_timestamp('2022-07-01T07:00:00+00:00')\\\"\nfor d in ['snowflake','bigquery','spark','mysql','postgres','tsql','oracle','clickhouse','redshift','hive','databricks','doris','starrocks','teradata','sqlite','drill','druid','p
…[156 chars elided]…
ad='trino',write=d)[0])\n    except Exception as e: print(d,'ERR',e)\nprint(sqlglot.transpile(\\\"select cast('2022-07-01T07:00:00+00:00' as timestamptz)\\\",read='duckdb',write='snowflake'))\n\" ; grep -rn \"class Generator\\|class Trino\\|class Presto\\|class Athena\" sqlglot/dialects/{trino,presto,athena}.py | head", "description": "Check current output across dialects and generator hierarchy"}
[tool_result] .agents/
.claude/
.github/
.lithify/
benchmarks/
pdoc/
posts/
sqlglot/
sqlglot-integration-tests/
sqlglotc/
tests/
.gitignore  1.9K
.gitmodules  135B
.gitpod.yml  217B
.pre-commit-config.yaml  1.7K
AGENTS.md  18.1K
CHANGELOG.md  1.8M
CLAUDE.md -> AGENTS.md  9B
CONTRIBUTING.md  3.8K
LICENSE  1.0K
MANIFEST.in  70B
Makefile  4.4K
README.md  22.6K
pyproject.toml  1.3K
setup.cfg  241B
setup.py  1.2K
sqlglot.png  7.2K
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
sqlglot/dialects/trino.py:9:class Trino(Presto):
sqlglot/dialects/presto.py:17:class Presto(Dialect):
sqlglot/dialects/athena.py:13:class Athena(Dialect):
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nsql=\\\"select from_iso8601_timestamp('2022-07-01T07:00:00+00:00')\\\"\nfor d in ['snowflake','bigquery','spark','mysql','postgres','tsql','oracle','clickhouse','redshift','hive','databricks','doris','teradata','sqlite','drill','presto','trino','athena','duckdb','exasol','materiali
…[133 chars elided]…
 e: print(d,'ERR',e)\nprint(sqlglot.transpile(\\\"select cast('2022-07-01T07:00:00+00:00' as timestamptz)\\\",read='duckdb',write='snowflake'))\nprint(sqlglot.transpile(\\\"select cast('2022-07-01T07:00:00+00:00' as timestamptz)\\\",read='duckdb',write='mysql'))\n\"; grep -n \"TIMESTAMPTZ\\|TIMESTAMP_TZ\" sqlglot/dialects/snowflake.py | head", "description": "Check current output across dialects"}
[tool_result] snowflake -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
bigquery -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
spark -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
mysql -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
postgres -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
tsql -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
oracle -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
clickhouse -> 
…[832 chars elided]…
CT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
materialize -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
risingwave -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
prql -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
tableau -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
["SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)"]
["SELECT TIMESTAMP('2022-07-01T07:00:00+00:00')"]
1 matches in 1 files:

168:0:TokenType.TIMESTAMPTZ,
[tool_use Bash] {"command": "grep -n \"class Generator\\|_sql(self\\|= function_fallback\\|self.func(\\\"\" sqlglot/dialects/presto.py sqlglot/dialects/trino.py sqlglot/dialects/athena.py | head -60; echo ----; grep -n \"def function_fallback_sql\\|def timestamptz\\|def fromiso\" sqlglot/generator.py sqlglot/generators/*.py | head; echo ---; grep -n \"TIMESTAMPTZ\" sqlglot/generators/snowflake.py sqlglot/generator.py | head", "description": "Inspect Presto/Trino/Athena generators and base helpers"}
[tool_result] rg: regex parse error:
    (?:class Generator|_sql(self|= function_fallback|self.func(")
                           ^
error: unclosed group
0 matches for 'class Generator\|_sql(self\|= function_fallback\|self.func("'
----
3 matches in 2 files:

sqlglot/generator.py:4568:def function_fallback_sql(self, expression: exp.Func) -> str:
sqlglot/generators/duckdb.py:2679:def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:
sqlglot/generators/duckdb.py:3078:def timestamptzfromparts_sql(self, expression: exp.TimestampTzFromParts) -> str:
---
3 matches in 1 files:

sqlglot/generator.py:384:# Whether TIMETZ / TIMESTAMPTZ will be generated using the "WITH TIME ZONE" synt...
sqlglot/generator.py:1758:exp.DType.TIMESTAMPTZ,
sqlglot/generator.py:5775:...exp.cast(exp.Literal.string("1970-01-01 00:00:00+00"), to=exp.DType.TIMESTAMPTZ)
[tool_use Bash] {"command": "grep -n -E \"class Generator|_sql\\(self|function_fallback\" sqlglot/dialects/presto.py sqlglot/dialects/trino.py sqlglot/dialects/athena.py | head -60; echo ----; sed -n 380,390p sqlglot/generator.py; sed -n 1750,1765p sqlglot/generator.py; echo ----; grep -n -E \"TIMESTAMPTZ|TIMESTAMP_TZ\" sqlglot/dialects/snowflake.py sqlglot/generators/snowflake.py | head", "description": "Inspect Presto/Trino/Athena generators and base helpers"}
[tool_result] ----

    # Whether to generate an unquoted value for EXTRACT's date part argument
    EXTRACT_ALLOWS_QUOTES = True

    # Whether TIMETZ / TIMESTAMPTZ will be generated using the "WITH TIME ZONE" syntax
    TZ_TO_WITH_TIME_ZONE = False

    # Whether the NVL2 function is supported
    NVL2_SUPPORTED = True

    # https://cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax
            elif type_value == exp.DType.INTERVAL:
                nested = f" {interior}"
            else:
                nested = f"({interior})"

        type_sql = f"{type_sql}{nested}{values}"
        if self.TZ_TO_WITH_TIME_ZONE and type_value in (
            exp.DType.TIMETZ,
            exp.DType.TIMESTAMPTZ,
        ):
            type_sql = f"{type_sql} WITH TIME ZONE"

        collate = self.sql(expression, "collate")
        if collate:
            type_sql = f"{type_sql} COLLATE {collate}"

----
sqlglot/dialects/snowflake.py:168:            "TIMESTAMP_TZ": TokenType.TIMESTAMPTZ,
[tool_use Bash] {"command": "ls sqlglot/generators/ | head -80; grep -n -E \"class |_sql\\(self\" sqlglot/generators/presto.py | head -20; grep -n -E \"class Generator\" sqlglot/generators/trino.py sqlglot/generators/athena.py; grep -n -E \"class Athena|class Generator|class Trino\" -A3 sqlglot/dialects/athena.py | head -20; sed -n 4560,4580p sqlglot/generator.py", "description": "List generators and inspect Presto generator"}
[tool_result] __init__.py  0B
athena.py  5.8K
bigquery.py  24.6K
clickhouse.py  26.8K
databricks.py  4.1K
doris.py  14.3K
dremio.py  3.3K
drill.py  4.2K
druid.py  892B
duckdb.py  183.2K
dune.py  323B
exasol.py  29.4K
fabric.py  6.5K
hive.py  21.0K
materialize.py  2.0K
mysql.py  26.7K
oracle.py  6.7K
postgres.py  21.6K
presto.py  25.0K
prql.py  192B
python.py  3.9K
redshift.py  11.7K
risingwave.py  1.1K
singlestore.py  42.3K
snowflake.py  46.8K
solr.py  192B
spark.py  7.8K
spark2.py  9.6K
sqlite.py  12.7K
star
…[2031 chars elided]…
TO {to_clause})"

        return self.function_fallback_sql(expression)

    def function_fallback_sql(self, expression: exp.Func) -> str:
        args = []

        for key in expression.arg_types:
            arg_value = expression.args.get(key)

            if isinstance(arg_value, list):
                for value in arg_value:
                    args.append(value)
            elif arg_value is not None:
                args.append(arg_value)

        if self.dialect.PRESERVE_ORIGINAL_NAMES:
[tool_use Bash] {"command": "grep -n -E \"^    def f|^    def e\" sqlglot/generator.py | head -30; grep -n -E \"class .*Generator\" sqlglot/generators/trino.py sqlglot/generators/athena.py; grep -n -E \"PrestoGenerator|TrinoGenerator\" sqlglot/generators/trino.py sqlglot/generators/athena.py sqlglot/dialects/athena.py | head -5", "description": "Find method placement and Trino/Athena generator bases"}
[tool_result] 1888:    def fetch_sql(self, expression: exp.Fetch) -> str:
1905:    def filter_sql(self, expression: exp.Filter) -> str:
2105:    def fallbackproperty_sql(self, expression: exp.FallbackProperty) -> str:
2119:    def freespaceproperty_sql(self, expression: exp.FreespaceProperty) -> str:
2718:    def from_sql(self, expression: exp.From) -> str:
2972:    def escape_str(
3262:    def forclause_sql(self, expression: exp.ForClause) -> str:
3567:    def exists_sql(self, expression: exp.Exists) -> str:
…[1396 chars elided]…
nerator):
sqlglot/generators/athena.py:125:class AthenaGenerator(generator.Generator):
sqlglot/generators/trino.py:11:from sqlglot.generators.presto import PrestoGenerator, amend_exploded_column_table
sqlglot/generators/trino.py:14:class TrinoGenerator(PrestoGenerator):
sqlglot/generators/trino.py:17:        **PrestoGenerator.PROPERTIES_LOCATION,
sqlglot/generators/trino.py:22:        **PrestoGenerator.TRANSFORMS,
sqlglot/generators/athena.py:7:from sqlglot.generators.trino import TrinoGenerator
[tool_use Bash] {"command": "sed -n 3986,3994p sqlglot/generator.py; echo ----; sed -n 205,215p sqlglot/generators/presto.py; grep -n -E \"    def [a-z_]+_sql\" sqlglot/generators/presto.py | head -3; sed -n 452,455p sqlglot/generators/presto.py", "description": "View insertion points in generator and presto"}
[tool_result]         zone = self.sql(expression, "zone")
        return f"{this} AT TIME ZONE {zone}"

    def fromtimezone_sql(self, expression: exp.FromTimeZone) -> str:
        this = self.sql(expression, "this")
        zone = self.sql(expression, "zone")
        return f"{this} AT TIME ZONE {zone} AT TIME ZONE 'UTC'"

    def add_sql(self, expression: exp.Add) -> str:
----
                    column.parent.replace(exp.column(column.parent.expression, table=new_table))

    return expression


class Pres
…[46 chars elided]…
INDS: tuple[str, ...] = ()
    SUPPORTS_DECODE_CASE = False

    AFTER_HAVING_MODIFIER_TRANSFORMS = generator.AFTER_HAVING_MODIFIER_TRANSFORMS

148:    def _delta_sql(self: PrestoGenerator, expression: DATE_ADD_OR_SUB) -> str:
452:    def extract_sql(self, expression: exp.Extract) -> str:
477:    def jsonformat_sql(self, expression: exp.JSONFormat) -> str:
    def extract_sql(self, expression: exp.Extract) -> str:
        date_part = expression.name

        if not date_part.startswith("EPOCH"):
[assistant] Now the edits: a generic fallback in the base generator, a native passthrough for Presto/Trino, and removing the now-duplicate DuckDB override.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-202950-trino-snowflake-and-other-dialec/base-1/sqlglot/generator.py", "old_string": "        return f\"{this} AT TIME ZONE {zone} AT TIME ZONE 'UTC'\"\n\n    def add_sql(self, expression: exp.Add) -> str:", "new_string": "        return f\"{this} AT TIME ZONE {zone} AT TIME ZONE 'UTC'\"\n\n    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))\n\n    def add_sql(self, expression: exp.Add) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-202950-trino-snowflake-and-other-dialec/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-202950-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/duckdb.py", "old_string": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))\n\n    def strposition_sql", "new_string": "    def strposition_sql"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-202950-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-202950-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/presto.py", "old_string": "    def extract_sql(self, expression: exp.Extract) -> str:\n        date_part = expression.name", "new_string": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.func(\"FROM_ISO8601_TIMESTAMP\", expression.this)\n\n    def extract_sql(self, expression: exp.Extract) -> str:\n        date_part = expression.name"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-202950-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/presto.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nsql=\\\"select from_iso8601_timestamp('2022-07-01T07:00:00+00:00')\\\"\nfor d in ['snowflake','bigquery','spark','mysql','postgres','tsql','oracle','clickhouse','redshift','hive','databricks','doris','teradata','sqlite','drill','presto','trino','athena','duckdb','exasol','materialize','risingwave','starrocks','singlestore','fabric','dremio']:\n    try: print(d, '->', sqlglot.transpile(sql,read='trino',write=d)[0])\n    except Exception as e: print(d,'ERR',e)\nprint(sqlglot.transpile(sql,read='trino',write='snowflake')[0])\nprint(sqlglot.transpile(sql,read='presto',write='snowflake')[0])\n\"", "description": "Re-check transpilation output across dialects"}
[tool_result] Data type TIMESTAMPTZ is not supported when targeting SingleStore
Dremio does not support time-zone-aware TIMESTAMP
snowflake -> SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
bigquery -> SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP)
spark -> SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP)
mysql -> SELECT TIMESTAMP('2022-07-01T07:00:00+00:00')
postgres -> SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
tsql -> SELECT CAST('2022-07-01T07:00:00+00:00' AS DATETIMEOFFS
…[986 chars elided]…
lize -> SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
risingwave -> SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
starrocks -> SELECT TIMESTAMP('2022-07-01T07:00:00+00:00')
singlestore -> SELECT '2022-07-01T07:00:00+00:00' :> TIMESTAMP
fabric -> SELECT CAST('2022-07-01T07:00:00+00:00' AS DATETIME2(6))
dremio -> SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
[assistant] Output now looks right across dialects. Next I'll extend the existing test for the new targets and run the suite.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-202950-trino-snowflake-and-other-dialec/base-1/tests/dialects/test_presto.py", "old_string": "                \"duckdb\": \"SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)\",\n                \"presto\": \"SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')\",\n            },", "new_string": "                \"duckdb\": \"SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)\",\n                \"presto\": \"SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')\",\n                \"snowflake\": \"SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)\",\n                \"postgres\": \"SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)\",\n            },"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-202950-trino-snowflake-and-other-dialec/base-1/tests/dialects/test_presto.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_presto.py tests/dialects/test_duckdb.py tests/dialects/test_trino.py tests/dialects/test_athena.py tests/dialects/test_snowflake.py 2>&1 | tail -15; echo ====; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run targeted dialect tests and full test suite"}
[tool_result ERROR] Exit code 1
................................................................................................ [ 54%]
..................................... [ 76%]
.......... [ 81%]
................................                [100%]
175 passed, 2690 subtests passed in 0.70s
(eval):1: === not found
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full project test suite"}
[tool_result] ................................................................. [ 28%]
................................................................................ [ 35%]
...................................................... [ 40%]
............................................................. [ 45%]
....................... [ 47%]
................................................................................................................... [ 57%]
............................................ [ 61%]
..
…[91 chars elided]…
............................................. [ 72%]
.................................................................................................................................................................................................. [ 90%]
............................... [ 92%]
............................................................. [ 98%]
....................                                                                  [100%]
1122 passed, 18181 subtests passed in 46.58s
[assistant] Full suite passes (1122 tests). Checking lint and formatting on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff check sqlglot/generator.py sqlglot/generators/presto.py sqlglot/generators/duckdb.py tests/dialects/test_presto.py 2>&1 | tail -3; $PY -m ruff format --check sqlglot/generator.py sqlglot/generators/presto.py sqlglot/generators/duckdb.py tests/dialects/test_presto.py 2>&1 | tail -3; git status --short; git diff --stat", "description": "Lint, format-check, and show changed files"}
[tool_result] All checks passed!
4 files already formatted
 M sqlglot/generator.py
 M sqlglot/generators/duckdb.py
 M sqlglot/generators/presto.py
 M tests/dialects/test_presto.pysqlglot/generator.py          | 3 +++
 sqlglot/generators/duckdb.py  | 3 ---
 sqlglot/generators/presto.py  | 3 +++
 tests/dialects/test_presto.py | 2 ++
 4 files changed, 8 insertions(+), 3 deletions(-)
[assistant] `FROM_ISO8601_TIMESTAMP` now transpiles to every non-Presto dialect. Your Snowflake example gives `SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)`. The full suite passes (1122 tests), and ruff lint and format checks are clean.

**What changed**
- **`sqlglot/generator.py`**: the base generator now handles `FromISO8601Timestamp` by emitting `CAST(... AS TIMESTAMPTZ)`. Each dialect maps `TIMESTAMPTZ` to its own type, so this covers the other dialects too.
- **`sqlglot/generators/duckdb.py`**: removed its override, which was identical to the new base method.
- **`sqlglot/generators/presto
…[727 chars elided]…
.')`, which drops the UTC offset.** Neither has a timezone-aware timestamp type, so this is the closest equivalent sqlglot already produces for a `TIMESTAMPTZ` cast in those dialects. The same loss happens for `CAST(x AS TIMESTAMPTZ)` today. If you want that case to be stricter, it needs a separate decision.
- **SingleStore gets a `:>` cast and an unsupported-type warning**, which is the existing behaviour for `TIMESTAMPTZ` there.

I didn't add Snowflake to a live database, so the Snowflake output is verified against the generator and its type mapping, not against a running Snowflake instance.
