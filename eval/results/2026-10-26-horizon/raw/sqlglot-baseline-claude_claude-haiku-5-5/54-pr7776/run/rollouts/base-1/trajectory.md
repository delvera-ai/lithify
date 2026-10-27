# trajectory base-1

final message:
`FROM_ISO8601_TIMESTAMP` now transpiles for every dialect, not just DuckDB. Your example gives `SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)` for Snowflake. The full suite passes (1122 tests) and ruff is clean. The changes are uncommitted.

**What changed**

- **`sqlglot/generator.py`**: the base generator now emits `CAST(x AS TIMESTAMPTZ)`. Each dialect renders that cast with its own timezone-aware type, so the output stays valid everywhere:
  - Snowflake and Postgres: `TIMESTAMPTZ`
  - BigQuery and Spark: `TIMESTAMP`
  - T-SQL: `DATETIMEOFFSET`
  - Oracle and Redshift: `TIMESTAMP WITH TIME ZONE`
- **`sqlglot/generators/duckdb.py`**: removed the DuckDB-only override, since the base method now produces the same output.
- **`sqlglot/generators/presto.py`**: added an override that keeps the function name for Presto and Trino. The existing `test_presto.py` expects `FROM_ISO8601_TIMESTAMP` to round-trip, and I didn't want to weaken that test.
- **`tests/dialects/test_presto.py`**: added Snowflake, Postgres, BigQuery and T-SQL expectations to the existing `validate_all` case.

**Decision for you:** I used `CAST(... AS TIMESTAMPTZ)` for Snowflake rather than `TO_TIMESTAMP_TZ`. For ISO 8601 strings with an offset, both preserve the offset, and the cast is the one form that works across dialects. If you want Snowflake to use `TO_TIMESTAMP_TZ` specifically, that's a small Snowflake-only override.

## events
[tool_use Bash] {"command": "git status --short | head && grep -rn -i \"iso8601\" sqlglot/ | head -50", "description": "Search for ISO8601 references in sqlglot source"}
[tool_result] sqlglot/expressions/temporal.py:436:class FromISO8601Timestamp(Expression, Func):
sqlglot/expressions/temporal.py:437:    _sql_names = ["FROM_ISO8601_TIMESTAMP"]
sqlglot/generators/duckdb.py:2679:    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:
[tool_use Bash] {"command": "sed -n 425,445p sqlglot/expressions/temporal.py && sed -n 2670,2695p sqlglot/generators/duckdb.py && grep -rn -i \"FROM_ISO8601\\|fromiso8601\" tests/ | head -20 && grep -rn \"TO_TIMESTAMP_TZ\\|def totimestamp\\|ToTimestamp\\b\" sqlglot/generators/snowflake.py sqlglot/expressions/*.py | head -20", "description": "Inspect existing FromISO8601Timestamp code and related tests"}
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
        from_clause = f" FROM {from_clause}" if from_clause else ""
        return f"{force}INSTAL
…[822 chars elided]…
        # Build expression: STRPOS(HEX(haystack), HEX(needle))
            hex_strpos = exp.StrPosition(
                this=exp.Hex(this=this),
                substr=exp.Hex(this=substr),
            )

tests/dialects/test_presto.py:37:            "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
tests/dialects/test_presto.py:40:                "presto": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
sqlglot/expressions/temporal.py:504:class TsOrDsToTimestamp(Expression, Func):
[tool_use Bash] {"command": "ls <work>/env-sqlglot/bin/python >/dev/null 2>&1 && echo ENV_OK; PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot impo
…[226 chars elided]…
.parse_one(\\\"select from_iso8601_timestamp('2022-07-01T07:00:00+00:00')\\\", 'trino').sql(d))\n    except Exception as e: print(d, 'ERR', e)\nprint(sqlglot.parse_one(\\\"select cast(x as timestamptz)\\\", 'postgres').sql('snowflake'))\nprint(sqlglot.parse_one(\\\"select cast(x as timestamptz)\\\", 'postgres').sql('bigquery'))\n\"", "description": "Check current transpile output across dialects"}
[tool_result] ENV_OK
snowflake -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
bigquery -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
postgres -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
duckdb -> SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
spark -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
databricks -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
presto -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
mys
…[246 chars elided]…
('2022-07-01T07:00:00+00:00')
hive -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
oracle -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
starrocks -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
doris -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
athena -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
trino -> SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')
SELECT CAST(x AS TIMESTAMPTZ)
SELECT CAST(x AS TIMESTAMP)
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; grep -n \"def [a-z]*_sql(self, expression: exp.[A-Za-z]*) -> str:\" sqlglot/generator.py | head -5; grep -n \"exp.cast(\" sqlglot/generator.py | head -5; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor d in ['snowflake','tsql','mysql','spark','clickhouse','oracle','redshift','hive']:\n    print(d, exp.cast(exp.column('x'), exp.DType.TIMESTAMPTZ).sql(d))\n\"", "description": "Check how TIMESTAMPTZ casts render per dialect"}
[tool_result] 1118:    def uncache_sql(self, expression: exp.Uncache) -> str:
1123:    def cache_sql(self, expression: exp.Cache) -> str:
1133:    def characterset_sql(self, expression: exp.CharacterSet) -> str:
1149:    def column_sql(self, expression: exp.Column) -> str:
1158:    def pseudocolumn_sql(self, expression: exp.Pseudocolumn) -> str:
204:        exp.Int64: lambda self, e: self.sql(exp.cast(e.this, exp.DType.BIGINT)),
1613:                    exp.cast(delimited_byte_string, exp.DType.BINARY, dialec
…[52 chars elided]…
limited_byte_string, exp.DType.VARCHAR, dialect=self.dialect)
3631:            args = [exp.cast(e, exp.DType.TEXT) for e in args]
4347:            return self.func("CONCAT", *(exp.cast(e, exp.DType.TEXT) for e in expression.flatten()))
snowflake CAST(x AS TIMESTAMPTZ)
tsql CAST(x AS DATETIMEOFFSET)
mysql TIMESTAMP(x)
spark CAST(x AS TIMESTAMP)
clickhouse CAST(x AS Nullable(DateTime))
oracle CAST(x AS TIMESTAMP WITH TIME ZONE)
redshift CAST(x AS TIMESTAMP WITH TIME ZONE)
hive CAST(x AS TIMESTAMP)
[tool_use Bash] {"command": "grep -n \"    def [a-z]*_sql(self, expression: exp.[A-Za-z]*) -> str:\" sqlglot/generator.py | awk -F: '$1>1100 && $1<1200'; sed -n 1155,1162p sqlglot/generator.py", "description": "View generator method layout near insertion point"}
[tool_result] 1118:    def uncache_sql(self, expression: exp.Uncache) -> str:
1123:    def cache_sql(self, expression: exp.Cache) -> str:
1133:    def characterset_sql(self, expression: exp.CharacterSet) -> str:
1149:    def column_sql(self, expression: exp.Column) -> str:
1158:    def pseudocolumn_sql(self, expression: exp.Pseudocolumn) -> str:
1161:    def columnposition_sql(self, expression: exp.ColumnPosition) -> str:
1182:    def columnconstraint_sql(self, expression: exp.ColumnConstraint) -> str:
1187:    def computedcolumnconstraint_sql(self, expression: exp.ComputedColumnConstraint) -> str:

        return f"{self.column_parts(expression)}{join_mark}"

    def pseudocolumn_sql(self, expression: exp.Pseudocolumn) -> str:
        return self.column_sql(expression)

    def columnposition_sql(self, expression: exp.ColumnPosition) -> str:
        this = self.sql(expression, "this")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-191218-trino-snowflake-and-other-dialec/base-1/sqlglot/generator.py", "old_string": "    def pseudocolumn_sql(self, expression: exp.Pseudocolumn) -> str:\n        return self.column_sql(expression)\n\n", "new_string": "    def pseudocolumn_sql(self, expression: exp.Pseudocolumn) -> str:\n        return self.column_sql(expression)\n\n    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-191218-trino-snowflake-and-other-dialec/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-191218-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/duckdb.py", "old_string": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))\n\n", "new_string": ""}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-191218-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[assistant] Now I'll check the transpile output across dialects and add a test to the Presto test file, which already covers this function.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor d in ['snowflake','bigquery','postgres','duckdb','spark','tsql','mysql','oracle','redshift','clickhouse','presto','trino']:\n    print(d, '->', sqlglot.parse_one(\\\"select from_iso8601_timestamp('2022-07-01T07:00:00+00:00')\\\", 'trino').sql(d))\n\"; sed -n 30,45p tests/dialects/test_presto.py", "description": "Verify new transpile output and view existing Presto test"}
[tool_result] snowflake -> SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
bigquery -> SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP)
postgres -> SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
duckdb -> SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
spark -> SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMP)
tsql -> SELECT CAST('2022-07-01T07:00:00+00:00' AS DATETIMEOFFSET)
mysql -> SELECT TIMESTAMP('2022-07-01T07:00:00+00:00')
oracle -> SELECT CAST('2022-07-01T07:00:00+00:
…[394 chars elided]…
     "presto": "CAST(x AS BOOLEAN)",
                "tsql": "CAST(x AS BIT)",
            },
        )
        self.validate_all(
            "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
            write={
                "duckdb": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)",
                "presto": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
            },
        )
        self.validate_all(
            "CAST(x AS INTERVAL YEAR TO MONTH)",
            write={
[assistant] The existing Presto test expects `FROM_ISO8601_TIMESTAMP` to round-trip, so Presto/Trino must keep emitting the function. I'll add an override there and check whether Trino inherits from Presto.
[tool_use Bash] {"command": "grep -n \"^class\\|class Generator\" sqlglot/dialects/trino.py sqlglot/dialects/presto.py sqlglot/generators/presto.py sqlglot/generators/trino.py 2>/dev/null; grep -n \"def [a-z]*_sql\" sqlglot/generators/presto.py | head -5; grep -n \"function_fallback_sql\" sqlglot/generators/presto.py | head -3", "description": "Locate Presto and Trino generator classes"}
[tool_result] sqlglot/dialects/trino.py:9:class Trino(Presto):
sqlglot/dialects/presto.py:17:class Presto(Dialect):
sqlglot/generators/presto.py:210:class PrestoGenerator(generator.Generator):
sqlglot/generators/trino.py:14:class TrinoGenerator(PrestoGenerator):
452:    def extract_sql(self, expression: exp.Extract) -> str:
477:    def jsonformat_sql(self, expression: exp.JSONFormat) -> str:
504:    def strtounix_sql(self, expression: exp.StrToUnix) -> str:
525:    def bracket_sql(self, expression: exp.Bracket) -> str:
530:    def struct_sql(self, expression: exp.Struct) -> str:
121:        return self.function_fallback_sql(expression)
489:        return self.function_fallback_sql(expression)
[tool_use Bash] {"command": "sed -n 500,530p sqlglot/generators/presto.py", "description": "View Presto generator methods near insertion point"}
[tool_result]             this = exp.Encode(this=this, charset=exp.Literal.string("utf-8"))

        return self.func("LOWER", self.func("TO_HEX", self.func("MD5", self.sql(this))))

    def strtounix_sql(self, expression: exp.StrToUnix) -> str:
        # Since `TO_UNIXTIME` requires a `TIMESTAMP`, we need to parse the argument into one.
        # To do this, we first try to `DATE_PARSE` it, but since this can fail when there's a
        # timezone involved, we wrap it in a `TRY` call and use `PARSE_DATETIME`
…[668 chars elided]…
lf.format_time(expression, Hive.INVERSE_TIME_MAPPING, Hive.INVERSE_TIME_TRIE),
        )
        coalesced = self.func("COALESCE", self.func("TRY", parse_without_tz), parse_with_tz)
        return self.func("TO_UNIXTIME", coalesced)

    def bracket_sql(self, expression: exp.Bracket) -> str:
        if expression.args.get("safe"):
            return bracket_to_element_at_sql(self, expression)
        return super().bracket_sql(expression)

    def struct_sql(self, expression: exp.Struct) -> str:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-191218-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/presto.py", "old_string": "        return self.func(\"TO_UNIXTIME\", coalesced)\n\n    def bracket_sql(self, expression: exp.Bracket) -> str:", "new_string": "        return self.func(\"TO_UNIXTIME\", coalesced)\n\n    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.function_fallback_sql(expression)\n\n    def bracket_sql(self, expression: exp.Bracket) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-191218-trino-snowflake-and-other-dialec/base-1/sqlglot/generators/presto.py has been updated successfully.
[assistant] Next I'll add cross-dialect tests to the Presto test file, then run the Presto and DuckDB suites plus the full test run.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-191218-trino-snowflake-and-other-dialec/base-1/tests/dialects/test_presto.py", "old_string": "                \"duckdb\": \"SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)\",\n                \"presto\": \"SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')\",\n            },\n        )", "new_str
…[147 chars elided]…
AMP('2020-05-11T11:15:05')\",\n                \"snowflake\": \"SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)\",\n                \"postgres\": \"SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)\",\n                \"bigquery\": \"SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMP)\",\n                \"tsql\": \"SELECT CAST('2020-05-11T11:15:05' AS DATETIMEOFFSET)\",\n            },\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-191218-trino-snowflake-and-other-dialec/base-1/tests/dialects/test_presto.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_presto.py tests/dialects/test_trino.py tests/dialects/test_duckdb.py 2>&1 | tail -15; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run dialect tests and full test suite"}
[tool_result] .......................................................................                                  [100%]
71 passed, 1120 subtests passed in 0.33s
.............. [ 22%]
................................................................. [ 28%]
................................................................................ [ 35%]
...................................................... [ 40%]
......................... [ 42%]
................................... [ 45%]
..........................
…[256 chars elided]…
............................................. [ 72%]
.................................................................................................................................................................................................. [ 89%]
............................... [ 92%]
............................................................. [ 98%]
......................                                                                [100%]
1122 passed, 18183 subtests passed in 56.20s
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nprint(sqlglot.parse_one(\\\"select from_iso8601_timestamp('2022-07-01T07:00:00+00:00')\\\", 'trino').sql('snowflake'))\"; ($PY -m ruff check sqlglot/generator.py sqlglot/generators/presto.py sqlglot/generators/duckdb.py tests/dialects/test_presto.py && $PY -m ruff format --check sqlglot tests) 2>&1 | tail -3; git status --short", "description": "Confirm reported example and run lint on changed files"}
[tool_result] SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)
All checks passed!
236 files already formatted
 M sqlglot/generator.py
 M sqlglot/generators/duckdb.py
 M sqlglot/generators/presto.py
 M tests/dialects/test_presto.py
[assistant] `FROM_ISO8601_TIMESTAMP` now transpiles for every dialect, not just DuckDB. Your example gives `SELECT CAST('2022-07-01T07:00:00+00:00' AS TIMESTAMPTZ)` for Snowflake. The full suite passes (1122 tests) and ruff is clean. The changes are uncommitted.

**What changed**

- **`sqlglot/generator.py`**: the base generator now emits `CAST(x AS TIMESTAMPTZ)`. Each dialect renders that cast with its own timezone-aware type, so the output stays valid everywhere:
  - Snowflake and Postgres: `TIMESTAMPTZ`
  - BigQuery and Spark: `TIMESTAMP`
  - T-SQL: `DATETIMEOFFSET`
  - Oracle and Redshift: `TIMESTAMP 
…[221 chars elided]…
ame for Presto and Trino. The existing `test_presto.py` expects `FROM_ISO8601_TIMESTAMP` to round-trip, and I didn't want to weaken that test.
- **`tests/dialects/test_presto.py`**: added Snowflake, Postgres, BigQuery and T-SQL expectations to the existing `validate_all` case.

**Decision for you:** I used `CAST(... AS TIMESTAMPTZ)` for Snowflake rather than `TO_TIMESTAMP_TZ`. For ISO 8601 strings with an offset, both preserve the offset, and the cast is the one form that works across dialects. If you want Snowflake to use `TO_TIMESTAMP_TZ` specifically, that's a small Snowflake-only override.
