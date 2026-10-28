# trajectory base-1

final message:
Doris and StarRocks now parse and generate the two-argument `DATE_ADD(date, days)` form, and your repro works. The full suite passes (1086 tests) and ruff is clean.

**What changed**
- **Parsing:** `DATE_ADD` and `DATE_SUB` in both dialects use a new builder in `sqlglot/dialects/dialect.py`. When the second argument is an `INTERVAL`, it behaves as before. Otherwise it builds `exp.TsOrDsAdd` with unit `DAY`, the same representation Hive uses.
- **`DATE_SUB` two-arg:** it becomes `TsOrDsAdd` with the days negated, so `date_sub(x, n + 1)` produces `DATE_ADD(x, -(n + 1))`. The parentheses matter; without them `-n + 1` would be wrong.
- **Generating:** a shared `ts_or_ds_add_days_sql` helper is used by both generators. It emits `DATE_ADD(x, n)` for day offsets and falls back to the `INTERVAL` form for other units.

**Behaviour changes to be aware of**
- Doris previously emitted the two-argument form for every `TsOrDsAdd`, which was wrong for non-day units. For example, Snowflake `DATEADD(month, 1, x)` became `DATE_ADD(x, 1)`. It now emits `DATE_ADD(x, INTERVAL 1 MONTH)`.
- A two-argument `DATE_SUB` comes out as `DATE_ADD(x, -n)` rather than `DATE_SUB`, which is equivalent in both dialects.
- StarRocks gained the two-argument output for day offsets. Before, it inherited MySQL's `INTERVAL` form.

**Tests:** I added `test_date_add_sub_days` to `tests/dialects/test_doris.py` and `tests/dialects/test_starrocks.py`. They cover round-trips, `DATE_SUB` with a compound argument, reading from Hive, and writing to MySQL.

I haven't committed anything.

## events
[tool_use Bash] {"command": "grep -n -i \"date_add\\|dateadd\\|DATE_SUB\\|DateAdd\\|DateSub\" sqlglot/dialects/doris.py sqlglot/dialects/starrocks.py sqlglot/dialects/mysql.py && grep -n \"def _build_date_delta\\|def build_date_delta\" -A 30 sqlglot/dialects/dialect.py | head -60", "description": "Find DATE_ADD handling in Doris/StarRocks/MySQL"}
[tool_result ERROR] Exit code 1
[tool_use Bash] {"command": "ls sqlglot/dialects | grep -i \"doris\\|starrocks\"; grep -rn -i \"date_add\\|DateAdd\\b\" sqlglot/dialects/doris.py sqlglot/dialects/starrocks.py sqlglot/dialects/mysql.py; grep -n \"def build_date_delta\\|def date_add_interval_sql\\|def _build_date_delta\" -A 25 sqlglot/dialects/dialect.py | head -80", "description": "Search DATE_ADD handling in dialect files"}
[tool_result] doris.py
starrocks.py
1577:def build_date_delta(
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
1588-        if unit_bas
…[2017 chars elided]…
pression: exp.TimestampTrunc) -> str:
1638-        args = [unit_to_str(expression), expression.this]
1639-        if zone:
1640-            args.append(expression.args.get("zone"))
1641-        return self.func(func, *args)
1642-
1643-    return _timestamptrunc_sql
1644-
1645-
1646-def no_timestamp_sql(self: Generator, expression: exp.Timestamp) -> str:
1647-    zone = expression.args.get("zone")
1648-    if not zone:
1649-        from sqlglot.optimizer.annotate_types import annotate_types
1650-
[tool_use Bash] {"command": "cat sqlglot/dialects/doris.py; echo ======; cat sqlglot/dialects/starrocks.py", "description": "Show Doris and StarRocks dialect sources"}
[tool_result ERROR] Exit code 1
from __future__ import annotations

from sqlglot.dialects.mysql import MySQL
from sqlglot.generators.doris import DorisGenerator
from sqlglot.parsers.doris import DorisParser


class Doris(MySQL):
    DATE_FORMAT = "'yyyy-MM-dd'"
    DATEINT_FORMAT = "'yyyyMMdd'"
    TIME_FORMAT = "'yyyy-MM-dd HH:mm:ss'"

    Parser = DorisParser

    Generator = DorisGenerator
(eval):1: ===== not found
[tool_use Bash] {"command": "cat sqlglot/parsers/doris.py; echo ======GEN; cat sqlglot/generators/doris.py; echo ======SR; cat sqlglot/dialects/starrocks.py; ls sqlglot/parsers | grep -i star; ls sqlglot/generators | grep -i star", "description": "Show Doris parser and generator sources"}
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
    
…[3751 chars elided]…
nd = self._match_texts(("MANUAL", "COMMIT", "SCHEDULE")) and self._prev.text.upper()
        every = self._match_text_seq("EVERY") and self._parse_number()
        unit = self._parse_var(any_token=True) if every else None
        starts = self._match_text_seq("STARTS") and self._parse_string()

        return self.expression(
            exp.RefreshTriggerProperty(
                method=method, kind=kind, every=every, unit=unit, starts=starts
            )
        )
(eval):1: =====GEN not found
[tool_use Bash] {"command": "cat sqlglot/generators/doris.py; echo ---SR---; cat sqlglot/dialects/starrocks.py; echo ---SRP---; cat sqlglot/parsers/starrocks.py 2>/dev/null; echo ---SRG---; cat sqlglot/generators/starrocks.py 2>/dev/null; echo ---; grep -rn \"DATE_ADD\\|DATE_SUB\\|DateAdd\\|DateSub\\|build_date_delta_with_interval\" sqlglot/parsers/mysql.py sqlglot/generators/mysql.py sqlglot/parsers/doris.py sqlglot/generators/doris.py sqlglot/dialects/mysql.py", "description": "Show Doris/StarRocks generator and MySQL date handling"}
[tool_result] <persisted-output>
Output too large (30.9KB). Full output saved to: ~/.claude/projects/-Users-user--cache-lithify-work-repo-fdb04f649b80-20261027-160011-doris-and-starrocks-dialects-bot-base-1/150531f5-870f-484b-8ddc-f24b0aa5077b/tool-results/bxcnfslb2.txt

Preview (first 2KB):
from __future__ import annotations

from sqlglot import exp
from sqlglot.dialects.dialect import (
    approx_count_distinct_sql,
    property_sql,
    rename_func,
    time_format,
    unit_to_str,
)
from
…[1315 chars elided]…
  exp.ArgMin: rename_func("MIN_BY"),
        exp.ArrayAgg: rename_func("COLLECT_LIST"),
        exp.ArrayToString: rename_func("ARRAY_JOIN"),
        exp.ArrayUniqueAgg: rename_func("COLLECT_SET"),
        exp.CurrentDate: lambda self, _: self.func("CURRENT_DATE"),
        exp.CurrentTimestamp: lambda self, _: self.func("NOW"),
        exp.DateTrunc: lambda self, e: self.func("DATE_TRUNC", e.this, unit_to_str(e)),
        exp.EuclideanDistance: rename_func("L2_DISTANCE"),
...
</persisted-output>
[tool_use Bash] {"command": "grep -n \"DATE_ADD\\|DATE_SUB\\|DateAdd\\|DateSub\\|DATE_DIFF\\|date_add\\|date_sub\" sqlglot/generators/doris.py sqlglot/generators/mysql.py sqlglot/parsers/mysql.py sqlglot/parsers/doris.py sqlglot/dialects/starrocks.py sqlglot/parsers/starrocks.py sqlglot/generators/starrocks.py sqlglot/dialects/mysql.py 2>&1; ls sqlglot/parsers | head -80; ls tests/dialects | grep -i \"doris\\|starrocks\"", "description": "Grep date add/sub handling in MySQL-family files"}
[tool_result] sqlglot/generators/doris.py:75:        exp.TsOrDsAdd: lambda self, e: self.func("DATE_ADD", e.this, e.expression),
sqlglot/generators/doris.py:184:        "date_add",
sqlglot/generators/doris.py:188:        "date_sub",
sqlglot/generators/mysql.py:10:    date_add_interval_sql,
sqlglot/generators/mysql.py:74:def date_add_sql(
sqlglot/generators/mysql.py:151:        exp.DateAdd: _remove_ts_or_ds_to_date(date_add_sql("ADD")),
sqlglot/generators/mysql.py:153:        exp.DateSub: _remove_ts_or_ds_to_d
…[705 chars elided]…
s.py:96:        exp.DateDiff: lambda self, e: self.func("DATE_DIFF", unit_to_str(e), e.this, e.expression),
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
test_doris.py
test_starrocks.py
[tool_use Bash] {"command": "sed -n 60,100p sqlglot/generators/mysql.py; echo; sed -n 105,125p sqlglot/parsers/mysql.py; echo; cat sqlglot/parsers/starrocks.py; echo; sed -n 1,40p sqlglot/dialects/starrocks.py; grep -n \"DATE_ADD\\|DATE_SUB\\|date_add\\|date_sub\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_mysql.py | head -40", "description": "Inspect MySQL date_add generator and parser entries"}
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
…[9709 chars elided]…
AS __timestamp FROM tableT",
tests/dialects/test_mysql.py:1460:                        f"DATE_ADD('0000-01-01 00:00:00', INTERVAL (TIMESTAMPDIFF({unit}, '0000-01-01 00:00:00', {cast})) {unit})",
tests/dialects/test_mysql.py:1465:                            "mysql": f"DATE_ADD('0000-01-01 00:00:00', INTERVAL (TIMESTAMPDIFF({unit}, '0000-01-01 00:00:00', {cast})) {unit})",
tests/dialects/test_mysql.py:1618:                self.validate_identity(f"DATE_ADD(base_date, INTERVAL day_interval {unit})")
[tool_use Bash] {"command": "grep -rn \"class TsOrDsAdd\\|class DateAdd\\|class DateSub\\|class TsOrDsDiff\" -A 8 sqlglot/expressions/*.py | head -60; echo; grep -rn \"TsOrDsAdd\" sqlglot --include=*.py | head -40; echo; grep -rn -i \"date_sub\\|date_add\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_mysql.py | head; grep -n \"TsOrDsAdd\" tests/*.py tests/dialects/*.py | head", "description": "Inspect TsOrDsAdd/DateAdd expression classes and usage"}
[tool_result] sqlglot/expressions/temporal.py:80:class DateAdd(Expression, Func, IntervalOp):
sqlglot/expressions/temporal.py-81-    arg_types = {"this": True, "expression": True, "unit": False}
sqlglot/expressions/temporal.py-82-
sqlglot/expressions/temporal.py-83-
sqlglot/expressions/temporal.py-84-class DateBin(Expression, Func, IntervalOp):
sqlglot/expressions/temporal.py-85-    arg_types = {"this": True, "expression": True, "unit": False, "zone": False, "origin": False}
sqlglot/expressions/temporal.py-86
…[3093 chars elided]…
:00', INTERVAL (TIMESTAMPDIFF({unit}, '0000-01-01 00:00:00', {cast})) {unit})",
tests/dialects/test_mysql.py:1465:                            "mysql": f"DATE_ADD('0000-01-01 00:00:00', INTERVAL (TIMESTAMPDIFF({unit}, '0000-01-01 00:00:00', {cast})) {unit})",
tests/dialects/test_mysql.py:1618:                self.validate_identity(f"DATE_ADD(base_date, INTERVAL day_interval {unit})")
tests/test_expressions.py:752:        self.assertIsInstance(parse_one("TS_OR_DS_ADD(a, 1, 'day')"), exp.TsOrDsAdd)
[tool_use Bash] {"command": "grep -rn \"TsOrDsAdd\" sqlglot | head -40; echo; grep -rn \"TS_OR_DS_ADD\\|DATE_SUB\" sqlglot/parsers/*.py | head; echo; grep -n \"date_sub\\|date_add\\|DATE_ADD\" -i sqlglot/generators/starrocks.py tests/dialects/test_doris.py tests/dialects/test_starrocks.py | head -20", "description": "Locate TsOrDsAdd usages across sqlglot and tests"}
[tool_result] sqlglot/parsers/redshift.py:25:        if expr_type is exp.TsOrDsAdd:
sqlglot/parsers/redshift.py:36:        "ADD_MONTHS": lambda args: exp.TsOrDsAdd(
sqlglot/parsers/redshift.py:43:        "DATEADD": _build_date_delta(exp.TsOrDsAdd),
sqlglot/parsers/redshift.py:44:        "DATE_ADD": _build_date_delta(exp.TsOrDsAdd),
sqlglot/parsers/hive.py:32:def _build_date_add(args: list) -> exp.TsOrDsAdd:
sqlglot/parsers/hive.py:37:    return exp.TsOrDsAdd(
sqlglot/parsers/hive.py:64:        "DATE_ADD": lam
…[2658 chars elided]…
 default_unit=None),
sqlglot/parsers/duckdb.py:103:        **{k: v for k, v in parser.Parser.FUNCTIONS.items() if k not in ("DATE_SUB", "GLOB")},
sqlglot/parsers/bigquery.py:191:        "DATE_SUB": build_date_delta_with_interval(exp.DateSub),
sqlglot/parsers/hive.py:73:        "DATE_SUB": _build_date_add,
sqlglot/parsers/mysql.py:119:        "DATE_SUB": build_date_delta_with_interval(exp.DateSub),
sqlglot/parsers/dremio.py:105:        "DATE_SUB": build_date_delta_with_cast_interval(exp.DateSub),
[tool_use Bash] {"command": "sed -n 28,80p sqlglot/parsers/hive.py; echo ----; sed -n 70,80p sqlglot/generators/hive.py; echo ----; sed -n 1,60p tests/dialects/test_doris.py | head -80; grep -n \"TsOrDs\\|DATE_ADD\\|date_add\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py", "description": "Review Hive date_add parsing and related tests"}
[tool_result]     expr.set("safe", True)
    return expr


def _build_date_add(args: list) -> exp.TsOrDsAdd:
    expression = seq_get(args, 1)
    if expression:
        expression = expression * -1

    return exp.TsOrDsAdd(
        this=seq_get(args, 0), expression=expression, unit=exp.Literal.string("DAY")
    )


class HiveParser(parser.Parser):
    LOG_DEFAULTS_TO_LN = True
    STRICT_CAST = False
    VALUES_FOLLOWED_BY_PAREN = False
    JOINS_HAVE_EQUAL_PRECEDENCE = True
    ADD_JOIN_ON_TRUE = True
    
…[3349 chars elided]…
         "postgres": """SELECT JSON_EXTRACT_PATH(CAST('{"key": 1}' AS JSONB), 'key')""",
            },
        )
        self.validate_all(
            "SELECT GROUP_CONCAT('aa', ',')",
            read={
                "doris": "SELECT GROUP_CONCAT('aa', ',')",
                "mysql": "SELECT GROUP_CONCAT('aa' SEPARATOR ',')",
                "postgres": "SELECT STRING_AGG('aa', ',')",
            },
        )
        self.validate_all(
            "SELECT LAG(1, 1, NULL) OVER (ORDER BY 1)",
[tool_use Bash] {"command": "sed -n 1,30p sqlglot/generators/starrocks.py; echo ----; grep -n \"TRANSFORMS\\|^class\\|    def \" sqlglot/generators/starrocks.py | head -40; echo ----; grep -n \"import\" sqlglot/parsers/mysql.py | head -20; grep -n \"^class Neg\" -A3 sqlglot/expressions/*.py; grep -n \"def unit_to_var\\|def unit_to_str\" -A12 sqlglot/dialects/dialect.py | head -40", "description": "Inspect StarRocks generator and helper functions"}
[tool_result] from __future__ import annotations


from sqlglot import exp, transforms
from sqlglot.dialects.dialect import (
    approx_count_distinct_sql,
    arrow_json_extract_sql,
    rename_func,
    unit_to_str,
    inline_array_sql,
    property_sql,
)
from sqlglot.generators.mysql import MySQLGenerator


def _eliminate_between_in_delete(expression: exp.Expr) -> exp.Expr:
    """
    StarRocks doesn't support BETWEEN in DELETE statements, so we convert
    BETWEEN expressions to explicit comparisons.

…[1835 chars elided]…
t.name)
1988-
1989-
1990:def unit_to_var(expression: exp.Expr, default: str = "DAY") -> exp.Expr | None:
1991-    unit = expression.args.get("unit")
1992-
1993-    if isinstance(unit, (exp.Var, exp.Placeholder, exp.WeekStart, exp.Column)):
1994-        return unit
1995-
1996-    value = unit.name if unit else default
1997-    return exp.Var(this=value) if value else None
1998-
1999-
2000-@t.overload
2001-def map_date_part(part: exp.Expr, dialect: DialectType = Dialect) -> exp.Expr:
2002-    pass
[tool_use Bash] {"command": "grep -n \"_sql\\b\\|TRANSFORMS\" sqlglot/generator.py | head -40; grep -n \"def sql(\" -A40 sqlglot/generator.py | grep -n \"transform\\|getattr\\|_sql\" ", "description": "Check generator dispatch order for TRANSFORMS vs methods"}
[tool_result] 13:from sqlglot.jsonpath import ALL_JSON_PATH_PARTS, JSON_PATH_PART_TRANSFORMS
64:AFTER_HAVING_MODIFIER_TRANSFORMS: dict[str, t.Any] = {
80:    dispatch: dict[type[exp.Expr], t.Callable[..., str]] = dict(cls.TRANSFORMS)
83:        if not attr_name.endswith("_sql") or attr_name.startswith("_"):
134:    TRANSFORMS: t.ClassVar[dict[type[exp.Expr], t.Callable[..., str]]] = {
135:        **JSON_PATH_PART_TRANSFORMS,
192:        exp.Get: lambda self, e: self.get_put_sql(e),
206:        exp.JSONObject:
…[1930 chars elided]…
_: exp.AutoIncrementColumnConstraint) -> str:
1174:        return self.token_sql(TokenType.AUTO_INCREMENT)
24:1085-            sql = self.function_fallback_sql(expression)
26:1087-            sql = self.property_sql(expression)
32:1093-    def uncache_sql(self, expression: exp.Uncache) -> str:
34:1095-        exists_sql = " IF EXISTS" if expression.args.get("exists") else ""
35:1096-        return f"UNCACHE TABLE{exists_sql} {table}"
37:1098-    def cache_sql(self, expression: exp.Cache) -> str:
[tool_use Bash] {"command": "sed -n 76,100p sqlglot/generator.py", "description": "Read generator method discovery logic"}
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

    return dispatch


class Generator:
    """
    Generator converts a given syntax tree to the corresponding SQL string.

    Args:
        pretty: Whether to format the produced SQL string.
[assistant] Parsing and generation are both in play, and `TRANSFORMS` takes precedence over `*_sql` methods, so the MySQL `TsOrDsAdd` entry would shadow a method. I'll put the shared builder and generator helper in `dialect.py`, next to the existing `build_date_delta_with_interval` and `date_add_interval_sql`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-160011-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py", "old_string": "        return expression_class(this=args[0], expression=interval.this, unit=unit_to_str(interval))\n\n    return _builder\n\n\ndef date_trunc_to_time(", "new_string": "        return expression_class(this=arg
…[418 chars elided]…
ss)\n\n    def _builder(args: BuilderArgs) -> E | exp.TsOrDsAdd | None:\n        if len(args) == 2 and not isinstance(args[1], exp.Interval):\n            days = exp.Neg(this=args[1]) if negate else args[1]\n            return exp.TsOrDsAdd(this=args[0], expression=days, unit=exp.Literal.string(\"DAY\"))\n\n        return interval_builder(args)\n\n    return _builder\n\n\ndef date_trunc_to_time("}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-160011-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-160011-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py", "old_string": "        return f\"{data_type}_{kind}({this}, {self.sql(interval)})\"\n\n    return func\n", "new_string": "        return f\"{data_type}_{kind}({this}, {self.sql(interval)})\"\n\n    return func\n\n\ndef ts_or_ds_add_days_sql(self: Generator, expression: exp.TsOrDsAdd) -> str:\n    # Two-argument DATE_ADD(date, days) is only valid for day offsets, other units need INTERVAL\n    if expression.text(\"unit\").upper() in (\"\", \"DAY\"):\n        return self.func(\"DATE_ADD\", expression.this, expression.expression)\n\n    return date_add_interval_sql(\"DATE\", \"ADD\")(self, expression)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-160011-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py has been updated successfully.
[assistant] Now the parsers and generators. Checking the imports in `dialect.py` first.
[tool_use Bash] {"command": "grep -n \"^from sqlglot.generator\\|import Generator\\|Generator\\b\" sqlglot/dialects/dialect.py | head -8; grep -n \"date_add_interval_sql\" sqlglot/generators/mysql.py | head -2; sed -n 5,14p sqlglot/parsers/mysql.py", "description": "Check Generator import and mysql dialect helper imports"}
[tool_result] 15:from sqlglot.generator import Generator, unsupported_args
255:        base_generator = (getattr(base, "generator_class", Generator),)
267:            "Generator", klass.__dict__.get("generator_class", base_generator[0])
761:    generator_class = Generator
1147:    def generator(self, **opts: Unpack[GeneratorArgs]) -> Generator:
1161:def rename_func(name: str) -> t.Callable[[Generator, exp.Expr], str]:
1165:def bracket_to_element_at_sql(self: Generator, expression: exp.Bracket) -> str:
1179:def approx_count_distinct_sql(self: Generator, expression: exp.ApproxDistinct) -> str:
10:    date_add_interval_sql,
192:        exp.TimestampAdd: date_add_interval_sql("DATE", "ADD"),
from sqlglot import exp, parser
from sqlglot.trie import new_trie
from sqlglot.dialects.dialect import (
    Dialect,
    build_date_delta,
    build_date_delta_with_interval,
    build_formatted_time,
    isnull_to_is_null,
)
from sqlglot.helper import seq_get
[assistant] Now wiring the parsers and generators for both dialects.
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\ndef edit(path, old, new, count=1):\n    s = open(path).read()\n    assert s.count(old) == count, (path, s.count(old), old)\n    s = s.replace(old, new)\n    open(path, \"w\").write(s)\n\n# Doris parser\np = \"sqlglot/parsers/doris.py\"\nedit(p, \"from sqlglot.helper import seq_get\\n\",\n     \"from sqlglot.dialects.dialect import build_date_delta_with_da
…[1391 chars elided]…
ator\np = \"sqlglot/generators/starrocks.py\"\nedit(p, '''    rename_func,\n    unit_to_str,\n    inline_array_sql,\n    property_sql,\n)''', '''    rename_func,\n    ts_or_ds_add_days_sql,\n    unit_to_str,\n    inline_array_sql,\n    property_sql,\n)''')\nEOF\nsed -n 86,100p sqlglot/generators/starrocks.py", "description": "Wire DATE_ADD/DATE_SUB builders and generator into Doris and StarRocks"}
[tool_result]         exp.PartitionedByProperty: exp.Properties.Location.POST_SCHEMA,
    }

    TRANSFORMS = {
        **{k: v for k, v in MySQLGenerator.TRANSFORMS.items() if k is not exp.DateTrunc},
        exp.Array: inline_array_sql,
        exp.ArrayAgg: rename_func("ARRAY_AGG"),
        exp.ArrayFilter: rename_func("ARRAY_FILTER"),
        exp.ArrayToString: rename_func("ARRAY_JOIN"),
        exp.ApproxDistinct: approx_count_distinct_sql,
        exp.CurrentVersion: lambda *_: "CURRENT_VERSION()",
        exp.DateDiff: lambda self, e: self.func("DATE_DIFF", unit_to_str(e), e.this, e.expression),
        exp.Delete: transforms.preprocess([_eliminate_between_in_delete]),
        exp.Flatten: rename_func("ARRAY_FLATTEN"),
        exp.JSONExtractScalar: arrow_json_extract_sql,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-160011-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/starrocks.py", "old_string": "        exp.Flatten: rename_func(\"ARRAY_FLATTEN\"),\n        exp.JSONExtractScalar: arrow_json_extract_sql,", "new_string": "        exp.Flatten: rename_func(\"ARRAY_FLATTEN\"),\n        exp.JSONExtractScalar: arrow_json_extract_sql,\n        exp.TsOrDsAdd: ts_or_ds_add_days_sql,"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-160011-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[assistant] Now I'll check the reported repro and some edge cases with the project's Python.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python && $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor d in ['doris','starrocks']:\n    for q in [\\\"select date_add('2025-01-01', 1) from a\\\", \\\"select date_sub('2025-01-01', 1) from a\\\", \\\"select date_sub('2025-01-01', n + 1) from a\\\", \\\"select date_add(x, INTERVAL 1 DAY) from a\\\", \\\"se
…[184 chars elided]…
lot.parse_one(\\\"date_add(x, 1)\\\", read='doris')))\nprint(sqlglot.transpile(\\\"SELECT DATEADD(month, 1, x)\\\", read='snowflake', write='doris'))\nprint(sqlglot.transpile(\\\"SELECT DATE_ADD(x, 1)\\\", read='spark', write='starrocks'))\nprint(sqlglot.transpile(\\\"SELECT DATE_ADD(x, 1)\\\", read='spark', write='doris'))\n\"\n", "description": "Run repro and edge cases for Doris and StarRocks"}
[tool_result] doris | SELECT DATE_ADD('2025-01-01', 1) FROM a | SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY) FROM a | SELECT DATE_ADD('2025-01-01', 1) FROM a
doris | SELECT DATE_ADD('2025-01-01', -1) FROM a | SELECT DATE_ADD('2025-01-01', INTERVAL -1 DAY) FROM a | SELECT DATE_ADD('2025-01-01', -1) FROM a
doris | SELECT DATE_ADD('2025-01-01', -n + 1) FROM a | SELECT DATE_ADD('2025-01-01', INTERVAL -n + 1 DAY) FROM a | SELECT DATE_ADD('2025-01-01', -n + 1) FROM a
doris | SELECT DATE_ADD(x, INTERVAL '1' DAY) FR
…[687 chars elided]…
rocks | SELECT DATE_ADD(x, INTERVAL '1' DAY) FROM a | SELECT DATE_ADD(x, INTERVAL '1' DAY) FROM a | SELECT DATE_ADD(x, 1) FROM a
starrocks | SELECT DATE_SUB(x, INTERVAL '2' MONTH) FROM a | SELECT DATE_SUB(x, INTERVAL '2' MONTH) FROM a | SELECT ADD_MONTHS(x, -2) FROM a
TsOrDsAdd(
  this=Column(
    this=Identifier(this=x, quoted=False)),
  expression=Literal(this=1, is_string=False),
  unit=Var(this=DAY))
['SELECT DATE_ADD(x, INTERVAL 1 MONTH)']
['SELECT DATE_ADD(x, 1)']
['SELECT DATE_ADD(x, 1)']
[assistant] The repro now parses, but `date_sub(x, n + 1)` comes out as `DATE_ADD(x, -n + 1)`, which is wrong: `Neg` doesn't parenthesize a binary operand. I'll wrap binary operands before negating.
[tool_use Bash] {"command": "grep -n \"^def paren\" -A3 sqlglot/expressions/*.py | head; grep -n \"exp.paren(\" sqlglot/dialects/dialect.py | head -3", "description": "Check exp.paren helper signature"}
[tool_result] sqlglot/expressions/core.py:2923:def paren(expression: ExpOrStr, copy: bool = True) -> Paren:
sqlglot/expressions/core.py-2924-    """
sqlglot/expressions/core.py-2925-    Wrap an expression in parentheses.
sqlglot/expressions/core.py-2926-
1723:            start=exp.Length(this=expression.this) - exp.paren(expression.expression - 1),
2300:            end = exp.paren(exp.Sub(this=end, expression=step_value), copy=False)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-160011-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py", "old_string": "            days = exp.Neg(this=args[1]) if negate else args[1]\n            return", "new_string": "            days = args[1]\n            if negate:\n                days = exp.Neg(this=exp.paren(days) if isinstance(days, exp.Binary) else days)\n            return"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-160011-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py has been updated successfully.
[assistant] Re-checking the edge cases, then adding tests to the Doris and StarRocks test files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python && $PY -c \"\nimport sqlglot\nfor d in ['doris','starrocks']:\n    print(sqlglot.transpile(\\\"select date_sub('2025-01-01', n + 1) from a\\\", read=d, write=d))\n    print(sqlglot.transpile(\\\"select date_sub('2025-01-01', 1) from a\\\", read=d, write=d))\n    print(sqlglot.transpile(\\\"select date_add(x, 1)\\\", read=d, write='duckdb'))\n\"; grep -n \"def test_\\|validate_identity\\|validate_all\" tests/dialects/test_starrocks.py | head -10; tail -5 tests/dialects/test_starrocks.py; tail -5 tests/dialects/test_doris.py", "description": "Recheck edge cases and inspect test file layout"}
[tool_result] ["SELECT DATE_ADD('2025-01-01', -(n + 1)) FROM a"]
["SELECT DATE_ADD('2025-01-01', -1) FROM a"]
['SELECT CAST(x AS DATE) + INTERVAL 1 DAY']
["SELECT DATE_ADD('2025-01-01', -(n + 1)) FROM a"]
["SELECT DATE_ADD('2025-01-01', -1) FROM a"]
['SELECT CAST(x AS DATE) + INTERVAL 1 DAY']
9:    def test_starrocks(self):
10:        self.assertEqual(self.validate_identity("arr[1]").expressions[0], exp.Literal.number(0))
12:        self.validate_identity("SELECT ARRAY_JOIN([1, 3, 5, NULL], '_', 'NULL')")
13:
…[621 chars elided]…
     self.validate_identity(
            "CREATE TABLE test_table (col1 DATE) PARTITION BY RANGE (col1) (START ('2019-01-01') END ('2021-01-01') EVERY (INTERVAL 1 YEAR), START ('2021-01-01') END ('2021-05-01') EVERY (INTERVAL 1 MONTH), START ('2021-05-01') END ('2021-05-04') EVERY (INTERVAL 1 DAY))"
        )

        # Combined BUILD and REFRESH
        self.validate_identity(
            "CREATE MATERIALIZED VIEW mv BUILD DEFERRED REFRESH AUTO ON SCHEDULE EVERY 10 MINUTE AS SELECT 1"
        )
[assistant] Edge cases look right now. Adding regression tests to both dialect test files.
[tool_use Bash] {"command": "python3 - <<'EOF'\ntests = {\n\"tests/dialects/test_doris.py\": '''\n    def test_date_add_sub_days(self):\n        self.validate_identity(\"SELECT DATE_ADD('2025-01-01', 1)\")\n        self.validate_identity(\"SELECT DATE_ADD(x, INTERVAL 1 DAY)\")\n        self.validate_all(\n            \"SELECT DATE_ADD(x, -1)\",\n            read={\"doris\": \"SELECT DATE_SUB(x, 1)\"},\n        )\
…[1058 chars elided]…
(path, \"w\").write(s.rstrip(\"\\n\") + \"\\n\" + block)\nEOF\nPY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_mysql.py tests/dialects/test_hive.py 2>&1 | tail -30", "description": "Add Doris/StarRocks date_add tests and run dialect tests"}
[tool_result] >       self.validate_identity("SELECT DATE_ADD(x, INTERVAL 1 DAY)")

tests/dialects/test_doris.py:258: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/dialects/test_dialect.py:63: in validate_identity
    self.assertEqual(
E   AssertionError: 'SELECT DATE_ADD(x, INTERVAL 1 DAY)' != "SELECT DATE_ADD(x, INTERVAL '1' DAY)"
E   - SELECT DATE_ADD(x, INTERVAL 1 DAY)
E   + SELECT DATE_ADD(x, INTERVAL '1' DAY)
E   ?                             + +
_______________
…[540 chars elided]…
nError: 'SELECT DATE_ADD(x, INTERVAL 1 DAY)' != "SELECT DATE_ADD(x, INTERVAL '1' DAY)"
E   - SELECT DATE_ADD(x, INTERVAL 1 DAY)
E   + SELECT DATE_ADD(x, INTERVAL '1' DAY)
E   ?                             + +
=========================== short test summary info ============================
FAILED tests/dialects/test_doris.py::TestDoris::test_date_add_sub_days - Asse...
FAILED tests/dialects/test_starrocks.py::TestStarrocks::test_date_add_sub_days
2 failed, 83 passed, 1085 subtests passed in 0.37s
[assistant] Both failures are in my new test, not the code: this codebase emits `INTERVAL '1' DAY` with the quoted literal, so the identity string was wrong. Fixing the test expectation.
[tool_use Bash] {"command": "sed -i \"s/self.validate_identity(\\\"SELECT DATE_ADD(x, INTERVAL 1 DAY)\\\")/self.validate_identity(\\\"SELECT DATE_ADD(x, INTERVAL '1' DAY)\\\")/\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py && PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_mysql.py tests/dialects/test_hive.py 2>&1 | tail -3", "description": "Fix test expectation and rerun dialect tests"}
[tool_result] sed: 2: "tests/dialects/test_dor ...": undefined label 'ests/dialects/test_doris.py'
(eval):1: command not found: -m
[assistant] The shell quoting mangled that `sed`. Doing the replacement in Python instead.
[tool_use Bash] {"command": "python3 -c \"\nold = 'self.validate_identity(\\\"SELECT DATE_ADD(x, INTERVAL 1 DAY)\\\")'\nnew = 'self.validate_identity(\\\"SELECT DATE_ADD(x, INTERVAL \\'1\\' DAY)\\\")'\nfor p in ['tests/dialects/test_doris.py', 'tests/dialects/test_starrocks.py']:\n    s = open(p).read()\n    assert s.count(old) == 1, p\n    open(p, 'w').write(s.replace(old, new))\nprint('ok')\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_mysql.py tests/dialects/test_hive.py 2>&1 | tail -3", "description": "Fix test expectation via Python and rerun dialect tests"}
[tool_result] ok
.............................. [ 61%]
................................. [100%]
85 passed, 1093 subtests passed in 0.33s
[assistant] Targeted tests pass. Running the full suite with the project's check command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite"}
[tool_result] ....... [ 30%]
............................................................................................. [ 39%]
................................................................................................... [ 48%]
.............................................. [ 52%]
.................... [ 54%]
............................................. [ 58%]
................................ [ 61%]
..................................................................... [ 67%]
............................................................................................................ [ 77%]
.................................................................................... [ 85%]
................................................. [ 90%]
............................... [ 93%]
.......................................................................... [ 99%]
..                                                                       [100%]
1086 passed, 17852 subtests passed in 50.72s
[assistant] Full suite passes (1086). Running the linter and checking the diff.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot tests/dialects/test_doris.py tests/dialects/test_starrocks.py 2>&1; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/dialects/dialect.py sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py tests/dialects/test_doris.py tests/dialects/test_starrocks.py 2>&1) | tail -12; git status --short; git diff --stat", "description": "Run ruff lint/format check and show changed files"}
[tool_result] All checks passed!
7 files already formatted
 M sqlglot/dialects/dialect.py
 M sqlglot/generators/doris.py
 M sqlglot/generators/starrocks.py
 M sqlglot/parsers/doris.py
 M sqlglot/parsers/starrocks.py
 M tests/dialects/test_doris.py
 M tests/dialects/test_starrocks.py
 sqlglot/dialects/dialect.py      | 27 +++++++++++++++++++++++++++
 sqlglot/generators/doris.py      |  3 ++-
 sqlglot/generators/starrocks.py  |  2 ++
 sqlglot/parsers/doris.py         |  3 +++
 sqlglot/parsers/starrocks.py     |  4 +++-
 tests/dialects/test_doris.py     | 16 ++++++++++++++++
 tests/dialects/test_starrocks.py | 16 ++++++++++++++++
 7 files changed, 69 insertions(+), 2 deletions(-)
[assistant] Doris and StarRocks now parse and generate the two-argument `DATE_ADD(date, days)` form, and your repro works. The full suite passes (1086 tests) and ruff is clean.

**What changed**
- **Parsing:** `DATE_ADD` and `DATE_SUB` in both dialects use a new builder in `sqlglot/dialects/dialect.py`. When the second argument is an `INTERVAL`, it behaves as before. Otherwise it builds `exp.TsOrDsAdd` with unit `DAY`, the same representation Hive uses.
- **`DATE_SUB` two-arg:** it becomes `TsOrDsAdd` with the days negated, so `date_sub(x, n + 1)` produces `DATE_ADD(x, -(n + 1))`. The parentheses matter; 
…[361 chars elided]…
its. For example, Snowflake `DATEADD(month, 1, x)` became `DATE_ADD(x, 1)`. It now emits `DATE_ADD(x, INTERVAL 1 MONTH)`.
- A two-argument `DATE_SUB` comes out as `DATE_ADD(x, -n)` rather than `DATE_SUB`, which is equivalent in both dialects.
- StarRocks gained the two-argument output for day offsets. Before, it inherited MySQL's `INTERVAL` form.

**Tests:** I added `test_date_add_sub_days` to `tests/dialects/test_doris.py` and `tests/dialects/test_starrocks.py`. They cover round-trips, `DATE_SUB` with a compound argument, reading from Hive, and writing to MySQL.

I haven't committed anything.
