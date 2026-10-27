# trajectory base-1

final message:
`PARSE_DATETIME` now transpiles to DuckDB as `STRPTIME`, and the example produces the expected output:

```
SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')
```

**The change**

- `sqlglot/generators/duckdb.py`: added a `parsedatetime_sql` method that delegates to the existing `str_to_time_sql` helper. It's auto-discovered by name, so no `TRANSFORMS` entry is needed. The helper also handles the format-string translation, so `%a %b %e` and similar come out as DuckDB strftime tokens.
- `tests/dialects/test_bigquery.py`: added a `validate_all` case with the BigQuery → DuckDB expectation from your report.

**Verification**

- Full suite: 1120 passed, 18168 subtests passed.
- `ruff check` and `ruff format --check` pass on both files.

**Choices I made**

- `ParseDatetime`'s optional `zone` argument is ignored in the DuckDB output. BigQuery's `PARSE_DATETIME` never sets it, so this doesn't affect BigQuery input. If a zone ever reaches this path, it would be dropped silently. I didn't add a guard because it seemed out of scope; say if you want one.
- The output is plain `STRPTIME`, not cast to `TIMESTAMP`, to match your expected string exactly.

## events
[tool_use Bash] {"command": "grep -rn -i \"parse_datetime\\|ParseDatetime\\|PARSE_DATETIME\\|StrToTime\\|strptime\" sqlglot/dialects/bigquery.py sqlglot/dialects/duckdb.py sqlglot/parsers/bigquery.py sqlglot/generators/bigquery.py sqlglot/generators/duckdb.py sqlglot/parsers/duckdb.py sqlglot/expressions/*.py 2>/dev/null | head -60; ls sqlglot/parsers | head -50", "description": "Search for datetime parsing handling in BigQuery and DuckDB"}
[tool_result] sqlglot/parsers/bigquery.py:95:def _build_parse_timestamp(args: list, dialect: Dialect) -> exp.StrToTime:
sqlglot/parsers/bigquery.py:96:    this = build_formatted_time(exp.StrToTime)([seq_get(args, 1), seq_get(args, 0)], dialect)
sqlglot/parsers/bigquery.py:251:        "PARSE_DATETIME": lambda args, dialect: build_formatted_time(exp.ParseDatetime)(
sqlglot/parsers/duckdb.py:180:        "STRPTIME": build_formatted_time(exp.StrToTime),
sqlglot/generators/duckdb.py:37:    timestrtotime_sql,
sqlglo
…[2472 chars elided]…
poral import TimeStrToTime as _TimeStrToTime
sqlglot/expressions/core.py:2387:        return _TimeStrToTime(this=datetime_literal, zone=tz)
__init__.py
athena.py
base.py
bigquery.py
clickhouse.py
databricks.py
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
[tool_use Bash] {"command": "sed -n 430,465p sqlglot/expressions/temporal.py; sed -n 245,260p sqlglot/parsers/bigquery.py; grep -rn \"ParseDatetime\" sqlglot/ tests/ | grep -v \"\\.pyc\" | head -30; sed -n 2620,2690p sqlglot/generators/duckdb.py", "description": "Inspect ParseDatetime definition, parser, and DuckDB strtotime"}
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


class StrToTime(Expression, Func):
    arg_types = {"this": True, "format":
…[4070 chars elided]…
TRY_STRPTIME" if safe else "STRPTIME"
            strptime = exp.Anonymous(this=func_name, expressions=[this, time_format])
            return self.sql(cast_expr(this=strptime, to=time_type))

        if isinstance(this, exp.TsOrDsToTime) or this.is_type(exp.DType.TIME):
            return self.sql(this)

        return self.sql(cast_expr(this=this, to=time_type))

    def currentdate_sql(self, expression: exp.CurrentDate) -> str:
        if not expression.this:
            return "CURRENT_DATE"
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfrom sqlglot.dialects.dialect import str_to_time_sql\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\\\", read='bigquery', write='duckdb'))\nprint(repr(sqlglot.pa
…[68 chars elided]…
'bigquery').selects[0]))\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\\\", read='bigquery', write='bigquery'))\n\" ; grep -n \"def str_to_time_sql\" -A12 sqlglot/dialects/dialect.py; grep -n \"ParseDatetime\\|StrToTime\" sqlglot/generators/duckdb.py sqlglot/parsers/duckdb.py", "description": "Reproduce current transpile output and inspect helpers"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
1795:def str_to_time_sql(self: Generator, expression: exp.Expr) -> str:
1796-    return self.func("STRPTIME", expression.this, self.format_time(expression))
1797-
1798-
1799-def concat_to_dpipe_sql(self: Generator, expression: exp.Concat) -> str:
1800-    return self.sql(reduce(lambda x, y: exp.DPipe(this=x, expression=y), expression.expressions))
1801-
1802-
1803-def concat_w
…[25 chars elided]…
rator, expression: exp.ConcatWs) -> str:
1804-    delim, *rest_args = expression.expressions
1805-    return self.sql(
1806-        reduce(
1807-            lambda x, y: exp.DPipe(this=x, expression=exp.DPipe(this=delim, expression=y)),
sqlglot/parsers/duckdb.py:180:        "STRPTIME": build_formatted_time(exp.StrToTime),
sqlglot/generators/duckdb.py:1664:        exp.TimeStrToTime: timestrtotime_sql,
sqlglot/generators/duckdb.py:2627:    def strtotime_sql(self, expression: exp.StrToTime) -> str:
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\\\", read='bigquery', write='bigquery'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATETIME('%Y-%m-%d', x)\\\", read='bigquery', write='duckdb'))\n\"; grep -n \"ParseDatetime\\|parse_datetime\\|PARSE_DATETIME\" -i tests/dialects/*.py | head", "description": "Reproduce current transpile output with repo sources"}
[tool_result] ["SELECT PARSE_DATETIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')"]
["SELECT PARSE_DATETIME('%F %T', '2023-01-15 14:30:00')"]
["SELECT PARSE_DATETIME(x, '%Y-%m-%d')"]
tests/dialects/test_clickhouse.py:690:        self.validate_identity("SELECT parseDateTime('2021-01-04+23:00:00', '%Y-%m-%d+%H:%i:%s')")
tests/dialects/test_clickhouse.py:692:            "SELECT parseDateTime('2021-01-04+23:00:00', '%Y-%m-%d+%H:%i:%s', 'Asia/Istanbul')"
tests/dialects/test_bigquery.py:120:            "SAFE.PARSE_
…[325 chars elided]…
DATETIME('%a %b %e %I:%M:%S %Y', 'Thu Dec 25 07:30:00 2008')"
tests/dialects/test_dialect.py:801:                "presto": "TO_UNIXTIME(COALESCE(TRY(DATE_PARSE(CAST('2020-01-01' AS VARCHAR), '%Y-%m-%d')), PARSE_DATETIME(DATE_FORMAT(CAST('2020-01-01' AS TIMESTAMP), '%Y-%m-%d'), 'yyyy-MM-dd')))",
tests/dialects/test_hive.py:487:                "presto": "TO_UNIXTIME(COALESCE(TRY(DATE_PARSE(CAST(x AS VARCHAR), '%Y-%m-%d %T')), PARSE_DATETIME(DATE_FORMAT(x, '%Y-%m-%d %T'), 'yyyy-MM-dd HH:mm:ss')))",
[tool_use Bash] {"command": "sed -n 30,45p sqlglot/generators/duckdb.py; sed -n 1968,1990p tests/dialects/test_bigquery.py; grep -n \"str_to_time_sql\" sqlglot/generators/duckdb.py | head -3", "description": "Check duckdb generator imports and bigquery test pattern"}
[tool_result]     no_make_interval_sql,
    no_time_sql,
    no_timestamp_sql,
    rename_func,
    remove_from_array_using_filter,
    strposition_sql,
    str_to_time_sql,
    timestrtotime_sql,
    unit_to_str,
)
from sqlglot.generator import unsupported_args
from sqlglot.helper import is_date_unit, seq_get
from builtins import type as Type

# Regex to detect time zones in timestamps of the form [+|-]TT[:tt]
# The pattern matches timezone offsets that appear after the time portion
        self.validate_all
…[815 chars elided]…
)
        self.validate_identity("ARPOX_TOP_SUM(col, 1.5, 2)")
        self.validate_identity("SAFE_CONVERT_BYTES_TO_STRING(b'\xc2')")
        self.validate_identity("FROM_HEX('foo')")
        self.validate_identity("TO_CODE_POINTS('foo')")
        self.validate_identity("CODE_POINTS_TO_BYTES([65, 98])")
        self.validate_identity("PARSE_BIGNUMERIC('1.2')")
        self.validate_identity("PARSE_NUMERIC('1.2')")
36:    str_to_time_sql,
2642:        base_sql = str_to_time_sql(self, expression)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-100607-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py", "old_string": "    def tsordstotime_sql(self, expression: exp.TsOrDsToTime) -> str:", "new_string": "    def parsedatetime_sql(self, expression: exp.ParseDatetime) -> str:\n        return str_to_time_sql(self, expression)\n\n    def tsordstotime_sql(self, expression: exp.TsOrDsToTime) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-100607-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-100607-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_bigquery.py", "old_string": "        self.validate_identity(\n            \"SELECT PARSE_DATETIME('%a %b %e %I:%M:%S %Y', 'Thu Dec 25 07:30:00 2008')\"\n        )", "new_string": "        self.validate_identity(\n            \"SELECT 
…[25 chars elided]…
%I:%M:%S %Y', 'Thu Dec 25 07:30:00 2008')\"\n        )\n        self.validate_all(\n            \"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\",\n            write={\n                \"bigquery\": \"SELECT PARSE_DATETIME('%F %T', '2023-01-15 14:30:00')\",\n                \"duckdb\": \"SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')\",\n            },\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-100607-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATETIME('%Y-
…[5 chars elided]…
', x)\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATETIME('%a %b %e %I:%M:%S %Y', x)\\\", read='bigquery', write='duckdb'))\n\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py tests/dialects/test_clickhouse.py 2>&1 | tail -15", "description": "Verify transpile output and run BigQuery/DuckDB tests"}
[tool_result] ["SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')"]
["SELECT STRPTIME(x, '%Y-%m-%d')"]
["SELECT STRPTIME(x, '%a %b %-d %I:%M:%S %Y')"]
.................. [ 13%]
...................................................................................................................                   [100%]
133 passed, 1937 subtests passed in 0.66s
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; git status --short", "description": "Run full test suite and show changed files"}
[tool_result] .................................................................................................................... [ 94%]
................. [ 95%]
................. [ 97%]
................................         [100%]
1120 passed, 18168 subtests passed in 51.48s
 M sqlglot/generators/duckdb.py
 M tests/dialects/test_bigquery.py
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/generators/duckdb.py tests/dialects/test_bigquery.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generators/duckdb.py tests/dialects/test_bigquery.py) 2>&1 | tail -5", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
2 files already formatted
[assistant] `PARSE_DATETIME` now transpiles to DuckDB as `STRPTIME`, and the example produces the expected output:

```
SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')
```

**The change**

- `sqlglot/generators/duckdb.py`: added a `parsedatetime_sql` method that delegates to the existing `str_to_time_sql` helper. It's auto-discovered by name, so no `TRANSFORMS` entry is needed. The helper also handles the format-string translation, so `%a %b %e` and similar come out as DuckDB strftime tokens.
- `tests/dialects/test_bigquery.py`: added a `validate_all` case with the BigQuery → DuckDB expectation from your report.

**Verification**

- Full suite: 1120 passed, 18168 subtests passed.
- `ruff check` and `ruff format --check` pass on both files.

**Choices I made**

- `ParseDatetime`'s optional `zone` argument is ignored in the DuckDB output. BigQuery's `PARSE_DATETIME` never sets it, so this doesn't affect BigQuery input. If a zone ever reaches this path, it would be dropped silently. I didn't add a guard because it seemed out of scope; say if you want one.
- The output is plain `STRPTIME`, not cast to `TIMESTAMP`, to match your expected string exactly.
