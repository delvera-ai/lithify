# trajectory base-1

final message:
Both dialects now parse the two-argument `DATE_ADD` / `DATE_SUB` form. `date_add('2025-01-01', 1)` parses as a one-day add in Doris and StarRocks, and the full suite passes (1084 tests, including the new ones) with `ruff check` and `ruff format --check` clean.

Generation emits the `INTERVAL` form, not the two-argument form. Existing tests in `tests/dialects/test_dialect.py` require `DATE_ADD(x, 1)` to generate `DATE_ADD(x, INTERVAL 1 DAY)` for Doris and StarRocks, and I didn't want to edit those. So `date_add('2025-01-01', 1)` round-trips as `DATE_ADD('2025-01-01', INTERVAL 1 DAY)`, which is equivalent. If you want the two-argument text back out, that means changing those existing expectations, and I can do that if you want it.

Changes:
- **`sqlglot/dialects/dialect.py`**: new `build_date_delta_with_interval_or_days`. It uses the days form when the call has two arguments and the second isn't an `INTERVAL`, and otherwise falls through to the existing INTERVAL builder. MySQL is untouched.
- **`sqlglot/parsers/doris.py`** and **`sqlglot/parsers/starrocks.py`**: `DATE_ADD` and `DATE_SUB` use the new builder.
- **`tests/dialects/test_doris.py`** and **`tests/dialects/test_starrocks.py`**: a regression case for each dialect that parses the two-argument form for both functions.

I didn't commit anything.

## events
[tool_use Bash] {"command": "grep -n -i \"date_add\\|date_sub\\|DateAdd\\|DateSub\\|_parse_date_delta\\|interval\" sqlglot/dialects/doris.py sqlglot/dialects/starrocks.py && grep -n \"def _build_date_delta\\|def _build_date_add\\|def build_date_delta\" -A30 sqlglot/dialects/dialect.py sqlglot/dialects/mysql.py | head -120", "description": "Find DATE_ADD handling in Doris/StarRocks dialects"}
[tool_result ERROR] Exit code 1
[tool_use Bash] {"command": "grep -n -i \"date_add\\|date_sub\\|DateAdd\\|DateSub\\|interval\" sqlglot/dialects/doris.py sqlglot/dialects/starrocks.py sqlglot/dialects/mysql.py; echo ---; grep -n \"def _build_date_delta\\|def build_date_delta\\|def date_add_interval_sql\\|def _date_add_sql\" -A25 sqlglot/dialects/dialect.py sqlglot/dialects/mysql.py | head -150", "description": "Search DATE_ADD references across dialects"}
[tool_result] sqlglot/dialects/mysql.py:51:    VALID_INTERVAL_UNITS = {
sqlglot/dialects/mysql.py:52:        *Dialect.VALID_INTERVAL_UNITS,
---
sqlglot/dialects/dialect.py:1577:def build_date_delta(
sqlglot/dialects/dialect.py-1578-    exp_class: Type[E],
sqlglot/dialects/dialect.py-1579-    unit_mapping: dict[str, str] | None = None,
sqlglot/dialects/dialect.py-1580-    default_unit: str | None = "DAY",
sqlglot/dialects/dialect.py-1581-    supports_timezone: bool = False,
sqlglot/dialects/dialect.py-1582-) -
…[4197 chars elided]…
1642-
sqlglot/dialects/dialect.py-1643-    return _timestamptrunc_sql
sqlglot/dialects/dialect.py-1644-
sqlglot/dialects/dialect.py-1645-
sqlglot/dialects/dialect.py-1646-def no_timestamp_sql(self: Generator, expression: exp.Timestamp) -> str:
sqlglot/dialects/dialect.py-1647-    zone = expression.args.get("zone")
sqlglot/dialects/dialect.py-1648-    if not zone:
sqlglot/dialects/dialect.py-1649-        from sqlglot.optimizer.annotate_types import annotate_types
sqlglot/dialects/dialect.py-1650-
[tool_use Bash] {"command": "cat sqlglot/dialects/doris.py; echo ----; cat sqlglot/dialects/starrocks.py; echo ----; grep -n \"DateAdd\\|DateSub\\|DATE_ADD\\|DATE_SUB\" sqlglot/dialects/mysql.py sqlglot/dialects/dialect.py sqlglot/dialects/tsql.py | head -30; echo ----; grep -n \"class DateAdd\\|class DateSub\\|class TsOrDsAdd\\|class DateDiff\" -A8 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null | head -60", "description": "Read Doris and StarRocks dialect files"}
[tool_result] from __future__ import annotations

from sqlglot.dialects.mysql import MySQL
from sqlglot.generators.doris import DorisGenerator
from sqlglot.parsers.doris import DorisParser


class Doris(MySQL):
    DATE_FORMAT = "'yyyy-MM-dd'"
    DATEINT_FORMAT = "'yyyyMMdd'"
    TIME_FORMAT = "'yyyy-MM-dd HH:mm:ss'"

    Parser = DorisParser

    Generator = DorisGenerator
----
from __future__ import annotations

from sqlglot.dialects.mysql import MySQL
from sqlglot.generators.starrocks import StarRocksGene
…[3001 chars elided]…
expression when transpiling it
sqlglot/expressions/temporal.py-147-    arg_types = {"this": True, "expression": True, "unit": False, "return_type": False}
sqlglot/expressions/temporal.py-148-
sqlglot/expressions/temporal.py-149-    @property
sqlglot/expressions/temporal.py-150-    def return_type(self) -> DataType:
sqlglot/expressions/temporal.py-151-        return DataType.build(self.args.get("return_type") or DType.DATE)
sqlglot/expressions/temporal.py-152-
sqlglot/expressions/temporal.py-153-
[tool_use Bash] {"command": "ls sqlglot/parsers sqlglot/generators | head -100; echo ----; cat sqlglot/parsers/doris.py; echo ----; cat sqlglot/parsers/starrocks.py; echo ----; cat sqlglot/generators/doris.py; echo ----; cat sqlglot/generators/starrocks.py; echo ----; grep -n \"DATE_ADD\\|DATE_SUB\\|DateAdd\\|DateSub\\|build_date_delta_with_interval\" sqlglot/parsers/*.py sqlglot/generators/*.py sqlglot/dialects/*.py | head -60", "description": "Inspect parser and generator modules for Doris/StarRocks"}
[tool_result] <persisted-output>
Output too large (40KB). Full output saved to: ~/.claude/projects/-Users-user--cache-lithify-work-repo-3abf279ffb90-20261029-134140-doris-and-starrocks-dialects-bot-base-1/d51e9a4b-b4d8-4b6a-b379-e1af520fd584/tool-results/be5stvfjh.txt

Preview (first 2KB):
__init__.py  0B
athena.py  5.8K
bigquery.py  24.3K
clickhouse.py  26.6K
databricks.py  3.8K
doris.py  14.3K
dremio.py  3.3K
drill.py  4.2K
druid.py  892B
duckdb.py  172.4K
dune.py  323B
exasol.py  28.0K
fabr
…[1270 chars elided]…
 0), seq_get(args, 1)

    def _is_unit_like(e: exp.Expr | None) -> bool:
        if not (isinstance(e, exp.Literal) and e.is_string):
            return False
        text = e.this
        return not any(ch.isdigit() for ch in text)

    # Determine which argument is the unit
    unit, this = (a0, a1) if _is_unit_like(a0) else (a1, a0)

    return exp.TimestampTrunc(this=this, unit=unit)


class DorisParser(MySQLParser):
    FUNCTIONS = {
        **MySQLParser.FUNCTIONS,
...
</persisted-output>
[tool_use Bash] {"command": "cat sqlglot/parsers/doris.py; echo ----SR; cat sqlglot/parsers/starrocks.py; echo ----; grep -n \"DATE_ADD\\|DATE_SUB\\|DateAdd\\|DateSub\\|build_date_delta_with_interval\" sqlglot/parsers/*.py sqlglot/generators/*.py sqlglot/dialects/*.py | head -60", "description": "Read Doris and StarRocks parser modules"}
[tool_result] from __future__ import annotations


from sqlglot import exp
from sqlglot.helper import seq_get
from sqlglot.parsers.mysql import MySQLParser
from sqlglot.tokens import TokenType


# Accept both DATE_TRUNC(datetime, unit) and DATE_TRUNC(unit, datetime)
def _build_date_trunc(args: list[exp.Expr]) -> exp.Expr:
    a0, a1 = seq_get(args, 0), seq_get(args, 1)

    def _is_unit_like(e: exp.Expr | None) -> bool:
        if not (isinstance(e, exp.Literal) and e.is_string):
            return False
    
…[14405 chars elided]…
tampAdd, exp.DateSub]
sqlglot/generators/presto.py:102:return self.func("DATE_ADD", unit, expression.expression, expression.this)
sqlglot/generators/presto.py:147:) -> t.Callable[[PrestoGenerator, DATE_ADD_OR_SUB], str]:
sqlglot/generators/presto.py:148:def _delta_sql(self: PrestoGenerator, expression: DATE_ADD_OR_SUB) -> str:
sqlglot/generators/presto.py:295:exp.DateAdd: _date_delta_sql("DATE_ADD"),
sqlglot/generators/presto.py:301:exp.DateSub: _date_delta_sql("DATE_ADD", negate_interval=True),
[tool_use Bash] {"command": "cat sqlglot/generators/doris.py; echo ----SR; cat sqlglot/generators/starrocks.py; echo ----MYSQLPARSER; grep -n \"DATE_ADD\\|DATE_SUB\\|DATE_ADD\\|DateAdd\\|DateSub\\|build_date_delta\\|ADDDATE\\|SUBDATE\\|DAYS\" sqlglot/parsers/mysql.py sqlglot/parsers/base.py sqlglot/parser.py 2>/dev/null | head -40; echo ----MYSQLGEN; grep -n \"DateAdd\\|DateSub\\|date_add_sql\\|def date_add\" sqlglot/generators/mysql.py sqlglot/dialects/dialect.py | head", "description": "Read generators and MySQL DATE_ADD handling"}
[tool_result] from __future__ import annotations

from sqlglot import exp
from sqlglot.dialects.dialect import (
    approx_count_distinct_sql,
    property_sql,
    rename_func,
    time_format,
    unit_to_str,
)
from sqlglot.generators.mysql import MySQLGenerator


def _lag_lead_sql(self, expression: exp.Lag | exp.Lead) -> str:
    return self.func(
        "LAG" if isinstance(expression, exp.Lag) else "LEAD",
        expression.this,
        expression.args.get("offset") or exp.Literal.number(1),
        
…[24548 chars elided]…
lot/dialects/dialect.py:39:exp.DateSub,
sqlglot/dialects/dialect.py:43:DATE_ADD_OR_SUB = t.Union[exp.DateAdd, exp.TsOrDsAdd, exp.DateSub]
sqlglot/dialects/dialect.py:48:exp.DateAdd,
sqlglot/dialects/dialect.py:49:exp.DateSub,
sqlglot/dialects/dialect.py:58:DATETIME_ADD = (exp.DateAdd, exp.TimeAdd, exp.DatetimeAdd, exp.TsOrDsAdd, exp...
sqlglot/dialects/dialect.py:1625:def date_add_interval_sql(data_type: str, kind: str) -> t.Callable[[Generator...
sqlglot/generators/mysql.py:74:def date_add_sql(
[tool_use Bash] {"command": "sed -n 60,100p sqlglot/generators/mysql.py; sed -n 145,160p sqlglot/generators/mysql.py; echo ----; sed -n 105,125p sqlglot/parsers/mysql.py; echo ----; sed -n 1570,1600p sqlglot/dialects/dialect.py | head -5; echo; grep -n \"def unit_to_var\\|def unit_to_str\" -A12 sqlglot/dialects/dialect.py | head -40; echo ----; grep -rn \"DATE_ADD\\|date_add\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_mysql.py | head -30", "description": "Review MySQL date_add generator and existing tests"}
[tool_result] def _unix_to_time_sql(self: MySQLGenerator, expression: exp.UnixToTime) -> str:
    scale = expression.args.get("scale")
    timestamp = expression.this

    if scale in (None, exp.UnixToTime.SECONDS):
        return self.func("FROM_UNIXTIME", timestamp, self.format_time(expression))

    return self.func(
        "FROM_UNIXTIME",
        exp.Div(this=timestamp, expression=exp.func("POW", 10, scale)),
        self.format_time(expression),
    )


def date_add_sql(
    kind: str,
) -> t.Callable[
…[5006 chars elided]…
AL (2 * 2) MONTH) FROM foo",
tests/dialects/test_mysql.py:1460:                        f"DATE_ADD('0000-01-01 00:00:00', INTERVAL (TIMESTAMPDIFF({unit}, '0000-01-01 00:00:00', {cast})) {unit})",
tests/dialects/test_mysql.py:1465:                            "mysql": f"DATE_ADD('0000-01-01 00:00:00', INTERVAL (TIMESTAMPDIFF({unit}, '0000-01-01 00:00:00', {cast})) {unit})",
tests/dialects/test_mysql.py:1618:                self.validate_identity(f"DATE_ADD(base_date, INTERVAL day_interval {unit})")
[tool_use Bash] {"command": "ls tests/dialects | grep -i \"doris\\|starrocks\"; grep -rn -i \"date_add\\|date_sub\\|days_add\\|INTERVAL\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py | head -40; echo ----; grep -rln \"\\\"doris\\\"\\|\\\"starrocks\\\"\\|doris\\|starrocks\" tests | head -20", "description": "Check existing Doris/StarRocks tests for DATE_ADD"}
[tool_result] test_doris.py  11.5K
test_starrocks.py  15.3K
tests/dialects/test_doris.py:143:            "CREATE TABLE test_table (c1 INT, c2 DATE) PARTITION BY RANGE (`c2`) (FROM ('2000-11-14') TO ('2021-11-14') INTERVAL 2 YEAR)"
tests/dialects/test_starrocks.py:46:            "UNIQUE KEY (col1, col2) PARTITION BY RANGE (col1) (START ('2024-01-01') END ('2024-01-31') EVERY (INTERVAL 1 DAY)) DISTRIBUTED BY HASH (col1)",
tests/dialects/test_starrocks.py:111:            "REFRESH IMMEDIATE START ('2025-01-01 00:
…[924 chars elided]…
ts/dialects/test_snowflake.py
tests/dialects/test_bigquery.py
tests/dialects/test_spark.py
tests/dialects/test_presto.py
tests/dialects/test_redshift.py
tests/dialects/test_oracle.py
tests/dialects/test_duckdb.py
tests/dialects/test_dialect.py
tests/dialects/test_starrocks.py
tests/dialects/test_mysql.py
tests/dialects/test_teradata.py
tests/dialects/test_hive.py
tests/dialects/test_clickhouse.py
tests/dialects/test_postgres.py
tests/test_transpile.py
tests/fixtures/optimizer/qualify_columns.sql
[tool_use Bash] {"command": "grep -rn \"doris\\|starrocks\" tests/dialects/*.py tests/test_transpile.py | grep -i \"date_add\\|date_sub\\|interval\\|DATE_\" | head -20; echo ---; grep -rn \"\\\"doris\\\"\\|\\\"starrocks\\\"\" tests/dialects/test_dialect.py | head; echo ---; sed -n 1,30p tests/dialects/test_starrocks.py", "description": "Find cross-dialect DATE_ADD expectations for Doris/StarRocks"}
[tool_result] tests/dialects/test_bigquery.py:1523:                "starrocks": "DATE_DIFF('DAY', CAST('2010-07-07' AS DATE), CAST('2008-12-25' AS DATE))",
tests/dialects/test_bigquery.py:1537:                "starrocks": "DATE_DIFF('MINUTE', CAST('2010-07-07' AS DATE), CAST('2008-12-25' AS DATE))",
tests/dialects/test_clickhouse.py:1801:                    "doris": f"DATE_TRUNC(x, '{unit}')",
tests/dialects/test_clickhouse.py:1814:                "doris": "DATE_TRUNC(x, 'WEEK')",
tests/dialects/test_dialect.
…[2805 chars elided]…
tity("SELECT ST_POINT(10, 20)")
        self.validate_identity("SELECT ST_DISTANCE_SPHERE(10.1, 20.2, 30.3, 40.4)")
        self.validate_identity("ARRAY_FLATTEN(arr)").assert_is(exp.Flatten)

        self.validate_all(
            "SELECT * FROM t WHERE cond",
            read={
                "": "SELECT * FROM t WHERE cond IS TRUE",
                "starrocks": "SELECT * FROM t WHERE cond",
            },
        )

        self.validate_identity("CURRENT_VERSION()")

    def test_ddl(self):
[tool_use Bash] {"command": "sed -n 1055,1090p tests/dialects/test_dialect.py", "description": "View DATE_ADD cross-dialect test expectations"}
[tool_result]             write={
                "bigquery": "DATE_ADD(x, INTERVAL 1 DAY)",
                "drill": "DATE_ADD(x, INTERVAL 1 DAY)",
                "duckdb": "x + INTERVAL 1 DAY",
                "hive": "DATE_ADD(x, 1)",
                "materialize": "x + INTERVAL '1 DAY'",
                "mysql": "DATE_ADD(x, INTERVAL 1 DAY)",
                "postgres": "x + INTERVAL '1 DAY'",
                "presto": "DATE_ADD('DAY', 1, x)",
                "snowflake": "DATEADD(DAY, 1, x)",
          
…[508 chars elided]…
          "duckdb": "x + INTERVAL 1 DAY",
                "hive": "DATE_ADD(x, 1)",
                "mysql": "DATE_ADD(x, INTERVAL 1 DAY)",
                "presto": "DATE_ADD('DAY', 1, x)",
                "spark": "DATE_ADD(x, 1)",
                "starrocks": "DATE_ADD(x, INTERVAL 1 DAY)",
                "doris": "DATE_ADD(x, INTERVAL 1 DAY)",
                "dremio": "DATE_ADD(x, 1)",
            },
        )
        self.validate_all(
            "DATE_TRUNC('DAY', x)",
            read={
[assistant] The existing `test_dialect.py` cases pin Doris/StarRocks output for `DateAdd` with a DAY unit to the `INTERVAL` form, so generation has to stay as is. The fix is on the parse side. Let me reproduce first.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor d in ['doris','starrocks']:\n    try:\n        print(sqlglot.transpile(\\\"select date_add('2025-01-01', 1), date_sub('2025-01-01', 1)\\\", read=d, write=d, error_level=sqlglot.ErrorLevel.IMMEDIATE))\n    except Exception as e: print(d, type(e).__name__, e)\n\"", "description": "Reproduce the two-argument DATE_ADD parse error"}
[tool_result] doris ParseError INTERVAL expression expected but got '1'
starrocks ParseError INTERVAL expression expected but got '1'
[assistant] Reproduced in both dialects. I'll add a shared builder next to `build_date_delta_with_interval` that falls back to the days form when the second argument isn't an `INTERVAL`, and wire it into both parsers.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-134140-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py", "old_string": "        return expression_class(this=args[0], expression=interval.this, unit=unit_to_str(interval))\n\n    return _builder\n\n\ndef date_trunc_to_time(", "new_string": "        return expression_class(this=arg
…[298 chars elided]…
s a number of days\n    interval_builder = build_date_delta_with_interval(expression_class)\n    days_builder = build_date_delta(expression_class)\n\n    def _builder(args: BuilderArgs) -> E | None:\n        if len(args) == 2 and not isinstance(args[1], exp.Interval):\n            return days_builder(args)\n        return interval_builder(args)\n\n    return _builder\n\n\ndef date_trunc_to_time("}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-134140-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-134140-doris-and-starrocks-dialects-bot/base-1/sqlglot/parsers/doris.py", "old_string": "from sqlglot import exp\nfrom sqlglot.helper import seq_get\nfrom sqlglot.parsers.mysql import MySQLParser", "new_string": "from sqlglot import exp\nfrom sqlglot.dialects.dialect import build_date_delta_with_interval_or_days\nfrom sqlglot.helper import seq_get\nfrom sqlglot.parsers.mysql import MySQLParser"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-134140-doris-and-starrocks-dialects-bot/base-1/sqlglot/parsers/doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-134140-doris-and-starrocks-dialects-bot/base-1/sqlglot/parsers/starrocks.py", "old_string": "from sqlglot.dialects.dialect import build_timestamp_trunc\nfrom sqlglot.helper import seq_get\nfrom sqlglot.parsers.mysql import MySQLParser\n\n\nclass StarRocksParser(MySQLParser):\n    FUNCTIONS = {\n     
…[170 chars elided]…
build_timestamp_trunc\nfrom sqlglot.helper import seq_get\nfrom sqlglot.parsers.mysql import MySQLParser\n\n\nclass StarRocksParser(MySQLParser):\n    FUNCTIONS = {\n        **MySQLParser.FUNCTIONS,\n        \"DATE_ADD\": build_date_delta_with_interval_or_days(exp.DateAdd),\n        \"DATE_SUB\": build_date_delta_with_interval_or_days(exp.DateSub),\n        \"DATE_TRUNC\": build_timestamp_trunc,"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-134140-doris-and-starrocks-dialects-bot/base-1/sqlglot/parsers/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-134140-doris-and-starrocks-dialects-bot/base-1/sqlglot/parsers/doris.py", "old_string": "        **MySQLParser.FUNCTIONS,\n        \"COLLECT_SET\": exp.ArrayUniqueAgg.from_arg_list,\n        \"DATE_TRUNC\": _build_date_trunc,", "new_string": "        **MySQLParser.FUNCTIONS,\n        \"COLLECT_SET\": exp.ArrayUniqueAgg.from_arg_list,\n        \"DATE_ADD\": build_date_delta_with_interval_or_days(exp.DateAdd),\n        \"DATE_SUB\": build_date_delta_with_interval_or_days(exp.DateSub),\n        \"DATE_TRUNC\": _build_date_trunc,"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-134140-doris-and-starrocks-dialects-bot/base-1/sqlglot/parsers/doris.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor d in ['doris','starrocks']:\n    for s in [\\\"select date_add('2025-01-01', 1), date_sub('2025-01-01', 1) from a\\\", \\\"select date_add('2025-01-01', INTERVAL 1 DAY), date_sub(x, interval 2 month)\\\", \\\"select date_add(x, col)\\\"]:\n        print(d, '|', sqlglot.transpile(s, rea
…[71 chars elided]…
lot.transpile(\\\"select date_add('2025-01-01', 1)\\\", read='doris', write='mysql')[0])\nprint(sqlglot.transpile(\\\"select date_add('2025-01-01', 1)\\\", read='starrocks', write='duckdb')[0])\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify parse/generate and run full test suite"}
[tool_result] doris | SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY), DATE_SUB('2025-01-01', INTERVAL 1 DAY) FROM a
doris | SELECT DATE_ADD('2025-01-01', INTERVAL '1' DAY), DATE_SUB(x, INTERVAL '2' MONTH)
doris | SELECT DATE_ADD(x, INTERVAL col DAY)
starrocks | SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY), DATE_SUB('2025-01-01', INTERVAL 1 DAY) FROM a
starrocks | SELECT DATE_ADD('2025-01-01', INTERVAL '1' DAY), DATE_SUB(x, INTERVAL '2' MONTH)
starrocks | SELECT DATE_ADD(x, INTERVAL col DAY)
SELECT DATE_ADD('2
…[746 chars elided]…
....................... [ 65%]
............................... [ 68%]
............................................... [ 73%]
................................................................................................................................................................................................................................. [ 93%]
................. [ 95%]
................. [ 97%]
................................         [100%]
1084 passed, 17844 subtests passed in 48.23s
[assistant] Both dialects now parse and generate the two-argument form, and the full suite passes (1084 passed). Next I'll add regression tests to the Doris and StarRocks test files.
[tool_use Bash] {"command": "sed -n 1,25p tests/dialects/test_doris.py; echo ----; grep -n \"def test_\" tests/dialects/test_starrocks.py", "description": "Look at Doris test file structure"}
[tool_result] from tests.dialects.test_dialect import Validator


class TestDoris(Validator):
    dialect = "doris"

    def test_doris(self):
        self.validate_all(
            "SELECT TO_DATE('2020-02-02 00:00:00')",
            write={
                "doris": "SELECT TO_DATE('2020-02-02 00:00:00')",
                "oracle": "SELECT CAST('2020-02-02 00:00:00' AS DATE)",
            },
        )
        self.validate_all(
            "SELECT MAX_BY(a, b), MIN_BY(c, d)",
            read={
                "clickhouse": "SELECT argMax(a, b), argMin(c, d)",
            },
        )
        self.validate_all(
            "SELECT ARRAY_SUM(x -> x * x, ARRAY(2, 3))",
            read={
                "clickhouse": "SELECT arraySum(x -> x*x, [2, 3])",
            },
----
9 matches in 9 files:

125:0:
136:0:
145:0:
157:0:
215:0:
236:0:
254:0:
30:0:
9:0:
[tool_use Bash] {"command": "grep -n \"    def \" tests/dialects/test_doris.py | head; grep -n \"    def test_starrocks\" -A3 tests/dialects/test_starrocks.py", "description": "List test method definitions in Doris and StarRocks tests"}
[tool_result] 11 matches in 11 files:

102:0:
108:0:
116:0:
121:0:
126:0:
135:0:
154:0:
229:0:
9:    def test_starrocks(self):
10-        self.assertEqual(self.validate_identity("arr[1]").expressions[0], exp.Literal.number(0))
11-
12-        self.validate_identity("SELECT ARRAY_JOIN([1, 3, 5, NULL], '_', 'NULL')")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-134140-doris-and-starrocks-dialects-bot/base-1/tests/dialects/test_doris.py", "old_string": "    def test_doris(self):\n        self.validate_all(\n            \"SELECT TO_DATE('2020-02-02 00:00:00')\",", "new_string": "    def test_doris(self):\n        self.validate_all(\n            \"SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY), DATE_SUB('2025-01-01', INTERVAL 1 DAY)\",\n            read={\n                \"doris\": \"SELECT DATE_ADD('2025-01-01', 1), DATE_SUB('2025-01-01', 1)\",\n            },\n        )\n        self.validate_all(\n            \"SELECT TO_DATE('2020-02-02 00:00:00')\","}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-134140-doris-and-starrocks-dialects-bot/base-1/tests/dialects/test_doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-134140-doris-and-starrocks-dialects-bot/base-1/tests/dialects/test_starrocks.py", "old_string": "        self.validate_identity(\"CURRENT_VERSION()\")\n", "new_string": "        self.validate_identity(\"CURRENT_VERSION()\")\n\n        self.validate_all(\n            \"SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY), DATE_SUB('2025-01-01', INTERVAL 1 DAY)\",\n            read={\n                \"starrocks\": \"SELECT DATE_ADD('2025-01-01', 1), DATE_SUB('2025-01-01', 1)\",\n            },\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-134140-doris-and-starrocks-dialects-bot/base-1/tests/dialects/test_starrocks.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_doris.py tests/dialects/test_starrocks.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; (ruff check sqlglot/dialects/dialect.py sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py tests/dialects/test_doris.py tests/dialects/test_starrocks.py && ruff format --check sqlglot tests) 2>&1 | tail -5; git status --short", "description": "Run targeted and full tests, plus lint and format check"}
[tool_result] ....................         [100%]
20 passed, 116 subtests passed in 0.17s
....................................................................       [100%]
1084 passed, 17846 subtests passed in 62.00s (0:01:02)
All checks passed!
233 files already formatted
 M sqlglot/dialects/dialect.py
 M sqlglot/parsers/doris.py
 M sqlglot/parsers/starrocks.py
 M tests/dialects/test_doris.py
 M tests/dialects/test_starrocks.py
[assistant] Both dialects now parse the two-argument `DATE_ADD` / `DATE_SUB` form. `date_add('2025-01-01', 1)` parses as a one-day add in Doris and StarRocks, and the full suite passes (1084 tests, including the new ones) with `ruff check` and `ruff format --check` clean.

Generation emits the `INTERVAL` form, not the two-argument form. Existing tests in `tests/dialects/test_dialect.py` require `DATE_ADD(x, 1)` to generate `DATE_ADD(x, INTERVAL 1 DAY)` for Doris and StarRocks, and I didn't want to edit those. So `date_add('2025-01-01', 1)` round-trips as `DATE_ADD('2025-01-01', INTERVAL 1 DAY)`, which is 
…[120 chars elided]…
at if you want it.

Changes:
- **`sqlglot/dialects/dialect.py`**: new `build_date_delta_with_interval_or_days`. It uses the days form when the call has two arguments and the second isn't an `INTERVAL`, and otherwise falls through to the existing INTERVAL builder. MySQL is untouched.
- **`sqlglot/parsers/doris.py`** and **`sqlglot/parsers/starrocks.py`**: `DATE_ADD` and `DATE_SUB` use the new builder.
- **`tests/dialects/test_doris.py`** and **`tests/dialects/test_starrocks.py`**: a regression case for each dialect that parses the two-argument form for both functions.

I didn't commit anything.
