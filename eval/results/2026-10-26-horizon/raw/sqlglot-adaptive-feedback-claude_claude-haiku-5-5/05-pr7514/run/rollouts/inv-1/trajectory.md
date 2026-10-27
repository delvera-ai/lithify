# trajectory inv-1

final message:
Doris and StarRocks now parse and generate the two-argument `DATE_ADD` / `DATE_SUB` form. The report's exact call parses and round-trips as `SELECT DATE_ADD('2025-01-01', 1) FROM a`.

Full suite, run after my last edit: `VERDICT: PASS` (1086 passed). Ruff check and format are clean on the touched files. I haven't committed.

**What changed**

- **Parsing** (`sqlglot/dialects/dialect.py`, `parsers/doris.py`, `parsers/starrocks.py`): a new builder, `build_date_delta_with_interval_or_days`, handles a non-interval second argument as days. It produces `exp.TsOrDsAdd(unit=DAY)`, the same node Hive uses. `DATE_SUB` negates the day count. The INTERVAL form still goes through the existing builder, so it is unchanged.
- **Generation** (`generators/mysql.py`, `doris.py`, `starrocks.py`): a shared `ts_or_ds_add_sql` emits `DATE_ADD(x, n)` for DAY or unitless nodes. Other units fall back to the INTERVAL form. Doris already had a `TsOrDsAdd` transform, but it ignored the unit, so an HOUR argument from another dialect silently came out as `DATE_ADD(x, 1)`. That is fixed as a side effect. StarRocks gets the same transform.
- **Tests**: a `test_date_add_sub_days` in each of `test_doris.py` and `test_starrocks.py` covers the AST node, identity round-trips, DATE_SUB, the duckdb output, and the INTERVAL HOUR fallback. No existing tests were changed.

**Choices to check**

- `DATE_SUB(x, n)` comes back out as `DATE_ADD(x, -n)`, not `DATE_SUB`. The meaning is the same, and it matches Hive. If you need the literal `DATE_SUB` spelling back, that needs a separate node, and I didn't add one.
- The two-arg form is only generated for DAY (or unitless) nodes. Other units keep the INTERVAL form, which both engines accept.

## events
[tool_use Bash] {"command": "git status --short | head && grep -rn -i \"date_add\\|DateAdd\\|DateSub\\|date_sub\" sqlglot/dialects/doris.py sqlglot/dialects/starrocks.py sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py 2>/dev/null; ls sqlglot/parsers | head -50", "description": "Check repo state and find date_add references"}
[tool_result] sqlglot/generators/doris.py:75:        exp.TsOrDsAdd: lambda self, e: self.func("DATE_ADD", e.this, e.expression),
sqlglot/generators/doris.py:184:        "date_add",
sqlglot/generators/doris.py:188:        "date_sub",
sqlglot/generators/doris.py:189:        "dateadd",
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
[tool_use Bash] {"command": "cat sqlglot/parsers/doris.py; echo ----; cat sqlglot/parsers/starrocks.py; echo ----; cat sqlglot/generators/starrocks.py | head -80; echo ----; sed -n 60,90p sqlglot/generators/doris.py; echo; grep -n \"DATE_ADD\\|DATE_SUB\\|DateAdd\\|TsOrDsAdd\\|DateSub\" sqlglot/generators/doris.py sqlglot/generators/starrocks.py sqlglot/parsers/mysql.py sqlglot/dialects/doris.py sqlglot/dialects/starrocks.py", "description": "Read Doris and StarRocks parser/generator files"}
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
    
…[14176 chars elided]…
ee1454a20254015b/fe/fe-core/src/main/antlr4/org/apache/doris/nereids/DorisLexer.g4#L93
    RESERVED_KEYWORDS = {
        "account_lock",
        "account_unlock",
        "add",
        "adddate",

sqlglot/parsers/mysql.py:114:        "DATE_ADD": build_date_delta_with_interval(exp.DateAdd),
sqlglot/parsers/mysql.py:119:        "DATE_SUB": build_date_delta_with_interval(exp.DateSub),
sqlglot/generators/doris.py:75:        exp.TsOrDsAdd: lambda self, e: self.func("DATE_ADD", e.this, e.expression),
[tool_use Bash] {"command": "sed -n 100,125p sqlglot/parsers/mysql.py; echo ----; grep -n \"def build_date_delta_with_interval\" -A25 sqlglot/dialects/dialect.py; echo ----; grep -n \"DateAdd\\|DateSub\\|_date_add\\|date_delta\" sqlglot/generators/mysql.py sqlglot/generators/base.py | head -30; echo ----; grep -n \"class DateAdd\\|class DateSub\\|class TsOrDsAdd\" -A12 sqlglot/expressions/*.py | head -60", "description": "Inspect MySQL date_add builders and generator handling"}
[tool_result]     }

    FUNCTIONS = {
        **parser.Parser.FUNCTIONS,
        "BIT_AND": exp.BitwiseAndAgg.from_arg_list,
        "BIT_OR": exp.BitwiseOrAgg.from_arg_list,
        "BIT_XOR": exp.BitwiseXorAgg.from_arg_list,
        "BIT_COUNT": exp.BitwiseCount.from_arg_list,
        "CONVERT_TZ": lambda args: exp.ConvertTimezone(
            source_tz=seq_get(args, 1), target_tz=seq_get(args, 2), timestamp=seq_get(args, 0)
        ),
        "CURDATE": exp.CurrentDate.from_arg_list,
        "CURTIME": ex
…[4497 chars elided]…
ons/temporal.py-150-    def return_type(self) -> DataType:
sqlglot/expressions/temporal.py-151-        return DataType.build(self.args.get("return_type") or DType.DATE)
sqlglot/expressions/temporal.py-152-
sqlglot/expressions/temporal.py-153-
sqlglot/expressions/temporal.py-154-class TsOrDsDiff(Expression, Func, TimeUnit):
sqlglot/expressions/temporal.py-155-    arg_types = {"this": True, "expression": True, "unit": False}
sqlglot/expressions/temporal.py-156-
sqlglot/expressions/temporal.py-157-
[tool_use Bash] {"command": "grep -n \"def build_date_delta(\" -A40 sqlglot/dialects/dialect.py | head -60; echo ----; grep -rn \"TsOrDsAdd\" sqlglot/ | grep -v \"^sqlglot/expressions\" | head -40; echo ----; grep -n \"TsOrDsAdd\" -B3 -A3 sqlglot/generators/mysql.py sqlglot/generators/spark.py sqlglot/generators/hive.py 2>/dev/null | head -40", "description": "Inspect build_date_delta and TsOrDsAdd usage"}
[tool_result] 1577:def build_date_delta(
1578-    exp_class: Type[E],
1579-    unit_mapping: dict[str, str] | None = None,
1580-    default_unit: str | None = "DAY",
1581-    supports_timezone: bool = False,
1582-) -> t.Callable[[BuilderArgs], E]:
1583-    def _builder(args: BuilderArgs) -> E:
1584-        unit_based = len(args) >= 3
1585-        has_timezone = len(args) == 4
1586-        this = args[2] if unit_based else seq_get(args, 0)
1587-        unit = None
1588-        if unit_based or default_unit:
15
…[6530 chars elided]…
)} USING utf32))",
sqlglot/generators/hive.py-72-
sqlglot/generators/hive.py-73-
sqlglot/generators/hive.py-74-def _add_date_sql(self: HiveGenerator, expression: DATE_ADD_OR_SUB) -> str:
sqlglot/generators/hive.py:75:    if isinstance(expression, exp.TsOrDsAdd) and not expression.unit:
sqlglot/generators/hive.py-76-        return self.func("DATE_ADD", expression.this, expression.expression)
sqlglot/generators/hive.py-77-
sqlglot/generators/hive.py-78-    unit = expression.text("unit").upper()
--
[tool_use Bash] {"command": "grep -rn -i \"date_add\\|date_sub\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_mysql.py | head -40; echo ----; sed -n 28,70p sqlglot/parsers/hive.py; echo ----; sed -n 70,90p sqlglot/generators/hive.py", "description": "Check existing date_add tests and Hive reference pattern"}
[tool_result] tests/dialects/test_mysql.py:353:        self.validate_identity("DATE_ADD(x, INTERVAL '1' YEAR)")
tests/dialects/test_mysql.py:876:            "WITH t AS (SELECT CAST('2020-01-10' AS DATE) AS col, 5 AS num_days) SELECT DATE_ADD(col, INTERVAL num_days DAY) FROM t",
tests/dialects/test_mysql.py:878:                "mysql": "WITH t AS (SELECT CAST('2020-01-10' AS DATE) AS col, 5 AS num_days) SELECT DATE_ADD(col, INTERVAL num_days DAY) FROM t",
tests/dialects/test_mysql.py:1004:            "SELECT D
…[2689 chars elided]…
ion.expression)

    unit = expression.text("unit").upper()
    func, multiplier = DATE_DELTA_INTERVAL.get(unit, ("DATE_ADD", 1))

    if isinstance(expression, exp.DateSub):
        multiplier *= -1

    increment = expression.expression
    if isinstance(increment, exp.Literal):
        value = increment.to_py() if increment.is_number else int(increment.name)
        increment = exp.Literal.number(value * multiplier)
    elif multiplier != 1:
        increment *= exp.Literal.number(multiplier)
[tool_use Bash] {"command": "grep -n \"DATE_SUB\\|_build_date_add\" sqlglot/parsers/hive.py; grep -n \"^def date_add_sql\" -A3 sqlglot/generators/mysql.py sqlglot/dialects/dialect.py; sed -n 1,12p sqlglot/generators/doris.py; grep -n \"^from\\|^import\" sqlglot/generators/starrocks.py; ls tests/dialects | grep -i \"doris\\|starrocks\"; ls .lithify/harness/scripts/", "description": "Locate date_add_sql and Hive DATE_SUB mapping"}
[tool_result] 32:def _build_date_add(args: list) -> exp.TsOrDsAdd:
73:        "DATE_SUB": _build_date_add,
sqlglot/generators/mysql.py:74:def date_add_sql(
sqlglot/generators/mysql.py-75-    kind: str,
sqlglot/generators/mysql.py-76-) -> t.Callable[[generator.Generator, exp.Expr], str]:
sqlglot/generators/mysql.py-77-    def func(self: generator.Generator, expression: exp.Expr) -> str:
from __future__ import annotations

from sqlglot import exp
from sqlglot.dialects.dialect import (
    approx_count_distinct_sql,
    property_sql,
    rename_func,
    time_format,
    unit_to_str,
)
from sqlglot.generators.mysql import MySQLGenerator

1:from __future__ import annotations
4:from sqlglot import exp, transforms
5:from sqlglot.dialects.dialect import (
13:from sqlglot.generators.mysql import MySQLGenerator
test_doris.py
test_starrocks.py
run_tests.py
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nprint(repr(sqlglot.parse_one(\\\"DATE_SUB(x, 1)\\\", read='hive')))\nprint(sqlglot.transpile(\\\"DATE_SUB(x, 1)\\\", read='hive', write='hive'))\nprint(sqlglot.transpile(\\\"DATE_SUB(x, 1)\\\", read='hive', write='doris'))\nprint(sqlglot.transpile(\\\"DATE_ADD(x, 1)\\\", read='hive', write='starrocks'))\n\" 2>&1 | tail -20", "description": "Probe Hive DATE_SUB AST and current outputs"}
[tool_result] TsOrDsAdd(
  this=Column(
    this=Identifier(this=x, quoted=False)),
  expression=Mul(
    this=Literal(this=1, is_string=False),
    expression=Neg(
      this=Literal(this=1, is_string=False))),
  unit=Var(this=DAY))
['DATE_ADD(x, 1 * -1)']
['DATE_ADD(x, 1 * -1)']
['DATE_ADD(x, INTERVAL 1 DAY)']
[tool_use Bash] {"command": "grep -n \"TRANSFORMS\\|_sql\\\"\\|getattr(self\" sqlglot/generator.py | head -30; grep -n \"def date_add_sql\" -B2 -A20 sqlglot/generators/mysql.py | head -30", "description": "Check generator dispatch order for TRANSFORMS vs methods"}
[tool_result] 13:from sqlglot.jsonpath import ALL_JSON_PATH_PARTS, JSON_PATH_PART_TRANSFORMS
64:AFTER_HAVING_MODIFIER_TRANSFORMS: dict[str, t.Any] = {
80:    dispatch: dict[type[exp.Expr], t.Callable[..., str]] = dict(cls.TRANSFORMS)
83:        if not attr_name.endswith("_sql") or attr_name.startswith("_"):
134:    TRANSFORMS: t.ClassVar[dict[type[exp.Expr], t.Callable[..., str]]] = {
135:        **JSON_PATH_PART_TRANSFORMS,
632:    AFTER_HAVING_MODIFIER_TRANSFORMS: t.ClassVar = {
636:        **AFTER_HAVING_M
…[569 chars elided]…
s=expression.expression, unit=unit_to_var(expression)),
82-        )
83-
84-    return func
85-
86-
87-def _ts_or_ds_to_date_sql(self: MySQLGenerator, expression: exp.TsOrDsToDate) -> str:
88-    time_format = expression.args.get("format")
89-    return _str_to_date_sql(self, expression) if time_format else self.func("DATE", expression.this)
90-
91-
92-def _remove_ts_or_ds_to_date(
93-    to_sql: t.Callable[[MySQLGenerator, exp.Expr], str] | None = None,
94-    args: tuple[str, ...] = ("this",),
[tool_use Bash] {"command": "sed -n 76,100p sqlglot/generator.py; sed -n 3505,3516p sqlglot/generator.py", "description": "Read generator dispatch construction"}
[tool_result] def _build_dispatch(
    cls: type[Generator],
) -> dict[type[exp.Expr], t.Callable[..., str]]:
    dispatch: dict[type[exp.Expr], t.Callable[..., str]] = dict(cls.TRANSFORMS)

    for attr_name in dir(cls):
        if not attr_name.endswith("_sql") or attr_name.startswith("_"):
            continue

        expr_key = attr_name[:-4]
        expr_cls = exp.EXPR_CLASSES.get(expr_key)

        if expr_cls and expr_cls not in dispatch:
            dispatch[expr_cls] = getattr(cls, attr_name)

    r
…[120 chars elided]…
   Args:
        pretty: Whether to format the produced SQL string.

        return path

    def json_path_part(self, expression: int | str | exp.JSONPathPart) -> str:
        if isinstance(expression, exp.JSONPathPart):
            transform = self.TRANSFORMS.get(expression.__class__)
            if not callable(transform):
                self.unsupported(f"Unsupported JSONPathPart type {expression.__class__.__name__}")
                return ""

            return transform(self, expression)
[assistant] Doris already maps `TsOrDsAdd` to the two-argument `DATE_ADD` on output, and StarRocks inherits MySQL's INTERVAL form. The parser side is the gap: MySQL's `build_date_delta_with_interval` rejects a non-interval second argument. Plan:

- **Parse:** a shared builder in `dialect.py` returns `TsOrDsAdd(this, days, unit=DAY)` for the two-arg form, with the day count negated for `DATE_SUB` (same approach Hive uses). The INTERVAL form still goes through the existing builder.
- **Generate:** a unit-aware `TsOrDsAdd` transform in `mysql.py` emits `DATE_ADD(x, n)` for DAY or unitless, and falls back to INTERVAL otherwise. Doris and StarRocks both use it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-1/sqlglot/dialects/dialect.py", "old_string": "        return expression_class(this=args[0], expression=interval.this, unit=unit_to_str(interval))\n\n    return _builder\n\n", "new_string": "        return expression_class(this=args[0], expression=interval.
…[268 chars elided]…
h_interval(expression_class)\n\n    def _builder(args: BuilderArgs) -> E | exp.TsOrDsAdd | None:\n        if len(args) == 2 and not isinstance(args[1], exp.Interval):\n            days = exp.Neg(this=args[1]) if negate else args[1]\n            return exp.TsOrDsAdd(this=args[0], expression=days, unit=exp.Literal.string(\"DAY\"))\n\n        return interval_builder(args)\n\n    return _builder\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-1/sqlglot/dialects/dialect.py has been updated successfully.
[assistant] Now the parsers.
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\np='sqlglot/parsers/doris.py'\ns=open(p).read()\ns=s.replace('''from sqlglot import exp\nfrom sqlglot.helper import seq_get\n''','''from sqlglot import exp\nfrom sqlglot.dialects.dialect import build_date_delta_with_interval_or_days\nfrom sqlglot.helper import seq_get\n''',1)\ns=s.replace('''        \"COLLECT_SET\": exp.ArrayUniqueAgg.from_arg_list,\n     
…[759 chars elided]…
 FUNCTIONS = {\n        **MySQLParser.FUNCTIONS,\n        \"DATE_ADD\": build_date_delta_with_interval_or_days(exp.DateAdd),\n        \"DATE_SUB\": build_date_delta_with_interval_or_days(exp.DateSub, negate=True),\n        \"DATE_TRUNC\": build_timestamp_trunc,''',1)\nopen(p,'w').write(s)\nEOF\ngit diff --stat", "description": "Wire two-argument DATE_ADD/DATE_SUB into Doris and StarRocks parsers"}
[tool_result]  sqlglot/dialects/dialect.py  | 16 ++++++++++++++++
 sqlglot/parsers/doris.py     |  3 +++
 sqlglot/parsers/starrocks.py |  4 +++-
 3 files changed, 22 insertions(+), 1 deletion(-)
[assistant] Now the generators: a unit-aware helper in `mysql.py`, used by both Doris and StarRocks.
[tool_use Bash] {"command": "python3 - <<'EOF'\np='sqlglot/generators/mysql.py'\ns=open(p).read()\nold='''    return func\n\n\ndef _ts_or_ds_to_date_sql('''\nnew='''    return func\n\n\ndef ts_or_ds_add_sql(self: MySQLGenerator, expression: exp.TsOrDsAdd) -> str:\n    # Doris/StarRocks accept DATE_ADD(date, days) without INTERVAL for day arithmetic\n    if expression.text(\"unit\").upper() in (\"\", \"DAY\"):\n  
…[803 chars elided]…
.mysql import MySQLGenerator, ts_or_ds_add_sql\n''',1)\nold='''        exp.TimestampTrunc:'''\nprint(s.count(old))\nopen(p,'w').write(s)\nEOF\ngrep -n \"TRANSFORMS = {\" -A3 sqlglot/generators/starrocks.py; grep -n \"exp.TimeStrToDate\\|exp.TsOrDsToDate\\|exp.TimestampTrunc\\|exp.Trim\" sqlglot/generators/starrocks.py", "description": "Add shared TsOrDsAdd generator and wire into Doris/StarRocks"}
[tool_result] 1
88:    TRANSFORMS = {
89-        **{k: v for k, v in MySQLGenerator.TRANSFORMS.items() if k is not exp.DateTrunc},
90-        exp.Array: inline_array_sql,
91-        exp.ArrayAgg: rename_func("ARRAY_AGG"),
107:        exp.TimestampTrunc: lambda self, e: self.func("DATE_TRUNC", unit_to_str(e), e.this),
108:        exp.TimeStrToDate: rename_func("TO_DATE"),
[tool_use Bash] {"command": "sed -n 104,118p sqlglot/generators/starrocks.py", "description": "View StarRocks TRANSFORMS tail"}
[tool_result]         exp.SqlSecurityProperty: lambda self, e: f"SECURITY {self.sql(e.this)}",
        exp.StDistance: st_distance_sphere,
        exp.StrToUnix: lambda self, e: self.func("UNIX_TIMESTAMP", e.this, self.format_time(e)),
        exp.TimestampTrunc: lambda self, e: self.func("DATE_TRUNC", unit_to_str(e), e.this),
        exp.TimeStrToDate: rename_func("TO_DATE"),
        exp.UnixToStr: lambda self, e: self.func("FROM_UNIXTIME", e.this, self.format_time(e)),
        exp.UnixToTime: rename_func("FROM_UNIXTIME"),
    }

    # https://docs.starrocks.io/docs/sql-reference/sql-statements/keywords/#reserved-keywords
    RESERVED_KEYWORDS = {
        "add",
        "all",
        "alter",
        "analyze",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-1/sqlglot/generators/starrocks.py", "old_string": "        exp.TimeStrToDate: rename_func(\"TO_DATE\"),\n        exp.UnixToStr:", "new_string": "        exp.TimeStrToDate: rename_func(\"TO_DATE\"),\n        exp.TsOrDsAdd: ts_or_ds_add_sql,\n        exp.UnixToStr:"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-1/sqlglot/generators/starrocks.py has been updated successfully.
[assistant] Now let me check the AST and the round-trips, including the exact call from the report.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor d in ['doris','starrocks']:\n    print('==', d)\n    e = sqlglot.parse_one(\\\"select date_add('2025-01-01', 1) from a\\\", read=d, error_level=sqlglot.ErrorLevel.IMMEDIATE)\n
…[177 chars elided]…
lect date_add(x, INTERVAL 1 DAY)\\\", \\\"select date_sub(x, INTERVAL 2 MONTH)\\\", \\\"select date_add(x, INTERVAL 1 HOUR)\\\"]:\n        print(sqlglot.transpile(s, read=d, write=d)[0], ' | duckdb:', sqlglot.transpile(s, read=d, write='duckdb')[0], ' | hive:', sqlglot.transpile(s, read=d, write='hive')[0])\n\" 2>&1 | tail -40", "description": "Verify AST and round-trip outputs for both dialects"}
[tool_result] == doris
TsOrDsAdd(
  this=Literal(this='2025-01-01', is_string=True),
  expression=Literal(this=1, is_string=False),
  unit=Var(this=DAY))
SELECT DATE_ADD('2025-01-01', 1)  | duckdb: SELECT CAST('2025-01-01' AS DATE) + INTERVAL 1 DAY  | hive: SELECT DATE_ADD('2025-01-01', 1)
SELECT DATE_ADD('2025-01-01', -1)  | duckdb: SELECT CAST('2025-01-01' AS DATE) + INTERVAL (-1) DAY  | hive: SELECT DATE_ADD('2025-01-01', -1)
SELECT DATE_ADD(x, -n)  | duckdb: SELECT CAST(x AS DATE) + INTERVAL (-n) DAY  | h
…[719 chars elided]…
 INTERVAL (-1) DAY  | hive: SELECT DATE_ADD('2025-01-01', -1)
SELECT DATE_ADD(x, -n)  | duckdb: SELECT CAST(x AS DATE) + INTERVAL (-n) DAY  | hive: SELECT DATE_ADD(x, -n)
SELECT DATE_ADD(x, INTERVAL '1' DAY)  | duckdb: SELECT x + INTERVAL '1' DAY  | hive: SELECT DATE_ADD(x, 1)
SELECT DATE_SUB(x, INTERVAL '2' MONTH)  | duckdb: SELECT x - INTERVAL '2' MONTH  | hive: SELECT ADD_MONTHS(x, -2)
SELECT DATE_ADD(x, INTERVAL '1' HOUR)  | duckdb: SELECT x + INTERVAL '1' HOUR  | hive: SELECT DATE_ADD(x, 1)
[assistant] Both dialects now parse and emit the two-arg form, and the INTERVAL forms are unchanged. One behaviour to note: `DATE_SUB(x, n)` comes back out as `DATE_ADD(x, -n)` (same semantics, same approach Hive takes). Next, the non-DAY unit case, then tests. Let me look at the existing test files' style.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nfrom sqlglot import exp\nimport sqlglot\nfor d in ['doris','starrocks']:\n    print(sqlglot.transpile(exp.TsOrDsAdd(this=exp.column('x'), expression=exp.Literal.number(1), unit=exp.var('HOUR')).sql() and 'select 1', read
…[31 chars elided]…
d(this=exp.column('x'), expression=exp.Literal.number(1), unit=exp.var('HOUR')).sql(d))\n    print(exp.TsOrDsAdd(this=exp.column('x'), expression=exp.Literal.number(1)).sql(d))\n\"; sed -n 1,25p tests/dialects/test_doris.py; grep -n \"def test_\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py | tail -4", "description": "Check non-DAY and unitless TsOrDsAdd output, view test layout"}
[tool_result] SELECT 1
DATE_ADD(x, INTERVAL 1 HOUR)
DATE_ADD(x, 1)
SELECT 1
DATE_ADD(x, INTERVAL 1 HOUR)
DATE_ADD(x, 1)
from tests.dialects.test_dialect import Validator


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
  
…[130 chars elided]…
 argMax(a, b), argMin(c, d)",
            },
        )
        self.validate_all(
            "SELECT ARRAY_SUM(x -> x * x, ARRAY(2, 3))",
            read={
                "clickhouse": "SELECT arraySum(x -> x*x, [2, 3])",
            },
tests/dialects/test_starrocks.py:157:    def test_unnest(self):
tests/dialects/test_starrocks.py:215:    def test_analyze(self):
tests/dialects/test_starrocks.py:236:    def test_between(self):
tests/dialects/test_starrocks.py:254:    def test_partition(self):
[assistant] Non-DAY units now correctly fall back to INTERVAL (before, Doris would have silently emitted `DATE_ADD(x, 1)` for an HOUR). Now I'll add tests to both dialect test files, after checking the end of each class.
[tool_use Bash] {"command": "tail -5 tests/dialects/test_doris.py; echo ----; sed -n 1,12p tests/dialects/test_starrocks.py; echo ----; tail -8 tests/dialects/test_starrocks.py", "description": "View ends of Doris and StarRocks test files"}
[tool_result]         # Combined BUILD and REFRESH
        self.validate_identity(
            "CREATE MATERIALIZED VIEW mv BUILD DEFERRED REFRESH AUTO ON SCHEDULE EVERY 10 MINUTE AS SELECT 1"
        )
----
from sqlglot import exp
from sqlglot.errors import UnsupportedError
from tests.dialects.test_dialect import Validator


class TestStarrocks(Validator):
    dialect = "starrocks"

    def test_starrocks(self):
        self.assertEqual(self.validate_identity("arr[1]").expressions[0], exp.Literal.number(0))

…[144 chars elided]…
   self.validate_identity(
            "CREATE TABLE test_table (col1 BIGINT) PARTITION BY RANGE (col1) (START ('1') END ('10') EVERY (1), START ('10') END ('100') EVERY (10))"
        )
        self.validate_identity(
            "CREATE TABLE test_table (col1 DATE) PARTITION BY RANGE (col1) (START ('2019-01-01') END ('2021-01-01') EVERY (INTERVAL 1 YEAR), START ('2021-01-01') END ('2021-05-01') EVERY (INTERVAL 1 MONTH), START ('2021-05-01') END ('2021-05-04') EVERY (INTERVAL 1 DAY))"
        )
[tool_use Bash] {"command": "cat >> tests/dialects/test_doris.py <<'EOF'\n\n    def test_date_add_sub_days(self):\n        expr = self.validate_identity(\"SELECT DATE_ADD('2025-01-01', 1)\").selects[0]\n        self.assertIsInstance(expr, exp.TsOrDsAdd)\n        self.assertEqual(expr.text(\"unit\"), \"DAY\")\n\n        self.validate_identity(\"SELECT DATE_ADD(x, -n)\")\n        self.validate_identity(\"SELECT DAT
…[1859 chars elided]…
vate/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/f0ecd001-19e9-4b3c-8461-34bf1f0fcf2a/scratchpad/hwork/env-sqlglot/bin/python; $PY .lithify/harness/scripts/run_tests.py -q -p no:cacheprovider --color=no tests/dialects/test_doris.py tests/dialects/test_starrocks.py 2>&1 | tail -30", "description": "Add Doris/StarRocks tests and run their dialect test files", "timeout": 600000}
[tool_result] from sqlglot import exp
from tests.dialects.test_dialect import Validator

cmd: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no -rfE -q -p no:cacheprovider --color=no tests/dialects/test_doris.py tests/dialects/test_starrocks.py
log: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/pytest-inv-1-1793031336.log
elapsed: 1s, exit: 1
FAILED tests/dialects/test_doris.py::TestDoris::test_date_add_sub_days - Asse...
FAILED tests/dialects/test_starrocks.py::TestStarrocks::test_date_add_sub_days
========================= 2 failed, 20 passed in 0.35s =========================
VERDICT: FAIL
[This command modified 2 files you've previously read: tests/dialects/test_doris.py, tests/dialects/test_starrocks.py. Call Read before editing.]
[assistant] Two new tests fail. Let me look at the assertion before touching anything.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_doris.py::TestDoris::test_date_add_sub_days tests/dialects/test_starrocks.py::TestStarrocks::test_date_add_sub_days 2>&1 | grep -E \"Error|assert|^E \" | head -20", "description": "Show assertion details for the two failing tests"}
[tool_result]         self.assertIsInstance(expr, exp.TsOrDsAdd)
        self.assertEqual(expr.text("unit"), "DAY")
    self.assertEqual(
E   AssertionError: 'SELECT DATE_ADD(x, INTERVAL 1 DAY)' != "SELECT DATE_ADD(x, INTERVAL '1' DAY)"
E   - SELECT DATE_ADD(x, INTERVAL 1 DAY)
E   + SELECT DATE_ADD(x, INTERVAL '1' DAY)
E   ?                             + +
        self.assertIsInstance(expr, exp.TsOrDsAdd)
        self.assertEqual(expr.text("unit"), "DAY")
    self.assertEqual(
E   AssertionError: 'SELECT DATE_ADD(x, INTERVAL 1 DAY)' != "SELECT DATE_ADD(x, INTERVAL '1' DAY)"
E   - SELECT DATE_ADD(x, INTERVAL 1 DAY)
E   + SELECT DATE_ADD(x, INTERVAL '1' DAY)
E   ?                             + +
[assistant] The code is fine; my test expectation was wrong. The existing INTERVAL output quotes the number (`INTERVAL '1' DAY`), as the MySQL tests already show. I'll correct my new test lines (not any existing test).
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-1/tests/dialects/test_doris.py", "offset": 170}
[tool_result] 170	        # DELETE with multiple table references
171	        self.validate_all(
172	            "DELETE FROM orders o WHERE o.customer_id IN (SELECT c.id FROM customers AS c WHERE c.status_code = 'inactive')",
173	            read={
174	                "postgres": "DELETE FROM orders AS o WHERE o.customer_id IN (SELECT c.id FROM customers AS c WHERE c.status_code = 'inactive')",
175	            },
176	            write={
177	                "doris": "DELETE FROM orders o WHERE o.customer_id I
…[5232 chars elided]…
,
269	            },
270	        )
271	        self.validate_all(
272	            "SELECT DATE_ADD('2025-01-01', 1)",
273	            write={
274	                "doris": "SELECT DATE_ADD('2025-01-01', 1)",
275	                "duckdb": "SELECT CAST('2025-01-01' AS DATE) + INTERVAL 1 DAY",
276	            },
277	        )
278	        self.validate_all(
279	            "SELECT DATE_ADD(x, INTERVAL 1 HOUR)",
280	            write={"doris": "SELECT DATE_ADD(x, INTERVAL 1 HOUR)"},
281	        )
282	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-1/tests/dialects/test_starrocks.py", "offset": 265}
[tool_result] 265	
266	        # Expr-based partitioning
267	        self.validate_identity(
268	            "CREATE TABLE test_table (col2 DATE) PARTITION BY DATE_TRUNC('DAY', col2)"
269	        )
270	        self.validate_identity(
271	            "CREATE TABLE test_table (col2 BIGINT) PARTITION BY FROM_UNIXTIME(col2, '%Y%m%d')"
272	        )
273	        self.validate_identity(
274	            "CREATE TABLE test_table (col1 STRING, col2 BIGINT) PARTITION BY FROM_UNIXTIME(col2, '%Y%m%d'), col1"
275	        )
…[2521 chars elided]…
D(x, INTERVAL 1 DAY)")
316	        self.validate_all(
317	            "SELECT DATE_SUB('2025-01-01', 1)",
318	            write={
319	                "starrocks": "SELECT DATE_ADD('2025-01-01', -1)",
320	                "duckdb": "SELECT CAST('2025-01-01' AS DATE) + INTERVAL (-1) DAY",
321	            },
322	        )
323	        self.validate_all(
324	            "SELECT DATE_ADD(x, INTERVAL 1 HOUR)",
325	            write={"starrocks": "SELECT DATE_ADD(x, INTERVAL 1 HOUR)"},
326	        )
327	
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-1/tests/dialects/test_doris.py", "old_string": "        self.validate_identity(\"SELECT DATE_ADD(x, INTERVAL 1 DAY)\")", "new_string": "        self.validate_identity(\"SELECT DATE_ADD(x, INTERVAL '1' DAY)\")"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-1/tests/dialects/test_doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-1/tests/dialects/test_doris.py", "old_string": "            \"SELECT DATE_ADD(x, INTERVAL 1 HOUR)\",\n            write={\"doris\": \"SELECT DATE_ADD(x, INTERVAL 1 HOUR)\"},", "new_string": "            \"SELECT DATE_ADD(x, INTERVAL '1' HOUR)\",\n            write={\"doris\": \"SELECT DATE_ADD(x, INTERVAL '1' HOUR)\"},"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-1/tests/dialects/test_doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-1/tests/dialects/test_starrocks.py", "old_string": "        self.validate_identity(\"SELECT DATE_ADD(x, INTERVAL 1 DAY)\")", "new_string": "        self.validate_identity(\"SELECT DATE_ADD(x, INTERVAL '1' DAY)\")"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-1/tests/dialects/test_starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-1/tests/dialects/test_starrocks.py", "old_string": "            \"SELECT DATE_ADD(x, INTERVAL 1 HOUR)\",\n            write={\"starrocks\": \"SELECT DATE_ADD(x, INTERVAL 1 HOUR)\"},", "new_string": "            \"SELECT DATE_ADD(x, INTERVAL '1' HOUR)\",\n            write={\"starrocks\": \"SELECT DATE_ADD(x, INTERVAL '1' HOUR)\"},"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-1/tests/dialects/test_starrocks.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/scripts/run_tests.py -q -p no:cacheprovider --color=no tests/dialects/test_doris.py tests/dialects/test_starrocks.py 2>&1 | tail -15", "description": "Rerun Doris and StarRocks dialect test files", "timeout": 600000}
[tool_result] cmd: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no -rfE -q -p no:cacheprovider --color=no tests/dialects/test_doris.py tests/dialects/test_starrocks.py
log: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/pytest-inv-1-1793031350.log
elapsed: 0s, exit: 0
============================== 22 passed in 0.17s ==============================
VERDICT: PASS
[assistant] Dialect files pass. Now the full suite, run once after my last edit as the project requires.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/scripts/run_tests.py -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run full test suite after final edits", "timeout": 600000}
[tool_result] cmd: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no -rfE -q -p no:cacheprovider --color=no
log: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/pytest-inv-1-1793031354.log
elapsed: 125s, exit: 0
======================= 1086 passed in 124.54s (0:02:04) =======================
VERDICT: PASS
[assistant] Full suite passes. Last, the exact call from the report plus a lint check on the touched files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nprint(sqlglot.parse('select date_add(\\'2025-01-01\\', 1) from a', dialect='doris', error_level=sqlglot.ErrorLevel.IMMEDIATE)[0].sql('doris'))\nprint(sqlglot.parse('select date_add(\\'2025-01-01\\', 1) fr
…[331 chars elided]…
t_starrocks.py 2>&1 | tail -3; $PY -m ruff format --check sqlglot/dialects/dialect.py sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py sqlglot/generators/mysql.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py tests/dialects/test_doris.py tests/dialects/test_starrocks.py 2>&1 | tail -3; git status --short", "description": "Run issue repro, ruff lint and format check, git status"}
[tool_result] SELECT DATE_ADD('2025-01-01', 1) FROM a
SELECT DATE_ADD('2025-01-01', 1) FROM a
All checks passed!
8 files already formatted
 M sqlglot/dialects/dialect.py
 M sqlglot/generators/doris.py
 M sqlglot/generators/mysql.py
 M sqlglot/generators/starrocks.py
 M sqlglot/parsers/doris.py
 M sqlglot/parsers/starrocks.py
 M tests/dialects/test_doris.py
 M tests/dialects/test_starrocks.py
[assistant] Doris and StarRocks now parse and generate the two-argument `DATE_ADD` / `DATE_SUB` form. The report's exact call parses and round-trips as `SELECT DATE_ADD('2025-01-01', 1) FROM a`.

Full suite, run after my last edit: `VERDICT: PASS` (1086 passed). Ruff check and format are clean on the touched files. I haven't committed.

**What changed**

- **Parsing** (`sqlglot/dialects/dialect.py`, `parsers/doris.py`, `parsers/starrocks.py`): a new builder, `build_date_delta_with_interval_or_days`, handles a non-interval second argument as days. It produces `exp.TsOrDsAdd(unit=DAY)`, the same node Hive u
…[521 chars elided]…
rm.
- **Tests**: a `test_date_add_sub_days` in each of `test_doris.py` and `test_starrocks.py` covers the AST node, identity round-trips, DATE_SUB, the duckdb output, and the INTERVAL HOUR fallback. No existing tests were changed.

**Choices to check**

- `DATE_SUB(x, n)` comes back out as `DATE_ADD(x, -n)`, not `DATE_SUB`. The meaning is the same, and it matches Hive. If you need the literal `DATE_SUB` spelling back, that needs a separate node, and I didn't add one.
- The two-arg form is only generated for DAY (or unitless) nodes. Other units keep the INTERVAL form, which both engines accept.
