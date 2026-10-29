# trajectory base-1

final message:
Doris and StarRocks now both parse and generate the two-argument `DATE_ADD` / `DATE_SUB` form. The example from the report parses without error, and the full test suite passes (1084 tests), along with ruff check and format.

**What changed**
- **Parsing** (`sqlglot/dialects/dialect.py`, `parsers/doris.py`, `parsers/starrocks.py`): a new shared builder, `build_date_delta_with_interval_or_days`, takes the two-argument form as a day count and builds a `TsOrDsAdd` with unit `DAY`. The `INTERVAL` form still goes through the existing builder, so `DATE_ADD(x, INTERVAL 1 DAY)` parses exactly as before.
- **Generation** (`generators/starrocks.py`): StarRocks now emits `DATE_ADD(x, n)` for day-unit `TsOrDsAdd`. Doris already did this.

**Choices you may want to review**
- **`DATE_SUB(x, n)` becomes `TsOrDsAdd` with `-n`**, so it round-trips as `DATE_ADD(x, -1)`. The two forms are equivalent, but the output uses `DATE_ADD`. Keeping `DATE_SUB` would need a new node or a flag, since the parsed form is otherwise indistinguishable from `DATE_SUB(x, INTERVAL n DAY)`.
- **StarRocks only uses the two-argument form for day units.** Other units fall back to the MySQL `INTERVAL` output. I used a `TRANSFORMS` entry rather than an auto-discovered `tsordsadd_sql` method, because the inherited MySQL `TRANSFORMS` entry takes precedence over auto-discovered methods.
- **Doris's generator is unchanged.** It still ignores the unit, so a non-day `TsOrDsAdd` is emitted as a day count. That predates this change, and I left it alone to keep the change scoped.

**Tests added** in `tests/dialects/test_doris.py` and `test_starrocks.py`: identity and cross-dialect round trips for the two-argument form, the `DATE_SUB` negation, and a check that the `INTERVAL` forms are unchanged.

Nothing is committed. The changes are in the working tree.

## events
[tool_use Bash] {"command": "grep -n \"DATE_ADD\\|DateAdd\\|DATE_SUB\\|DateSub\\|DATE_ADD_SUB\\|date_add\\|DATEDIFF\" sqlglot/dialects/doris.py sqlglot/dialects/starrocks.py sqlglot/dialects/mysql.py | head -60; ls <work>/env-sqlglot/bin/python"}
[tool_result] <work>/env-sqlglot/bin/python
[tool_use Bash] {"command": "cat sqlglot/dialects/doris.py | head -150; echo ----; cat sqlglot/dialects/starrocks.py | head -150; echo ----; grep -n \"DATE_ADD\\|DateAdd\\|_parse_date_delta\\|build_date_delta\\|DATE_SUB\" sqlglot/dialects/mysql.py sqlglot/dialects/dialect.py | head -40"}
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
…[643 chars elided]…
exp.DateAdd,
sqlglot/dialects/dialect.py:58:DATETIME_ADD = (exp.DateAdd, exp.TimeAdd, exp.DatetimeAdd, exp.TsOrDsAdd, exp.TimestampAdd)
sqlglot/dialects/dialect.py:1577:def build_date_delta(
sqlglot/dialects/dialect.py:1599:def build_date_delta_with_interval(
sqlglot/dialects/dialect.py:1934:def date_delta_sql(name: str, cast: bool = False) -> t.Callable[[Generator, DATE_ADD_OR_DIFF], str]:
sqlglot/dialects/dialect.py:1935:    def _delta_sql(self: Generator, expression: DATE_ADD_OR_DIFF) -> str:
[tool_use Bash] {"command": "cat sqlglot/parsers/doris.py; echo ----; cat sqlglot/parsers/starrocks.py; echo ----; cat sqlglot/generators/doris.py; echo -----; cat sqlglot/generators/starrocks.py; echo ----; grep -n \"DATE_ADD\\|DATE_SUB\\|DateAdd\\|DateSub\\|build_date_delta\\|DATE_ADD_SUB\" sqlglot/parsers/mysql.py sqlglot/generators/mysql.py"}
[tool_result] <persisted-output>
Output too large (35.2KB). Full output saved to: ~/.claude/projects/-Users-user--cache-lithify-work-repo-e2b5bc4f1eee-20261029-091426-doris-and-starrocks-dialects-bot-base-1/ca4bd548-1afd-4178-9a4d-68e955f8cd60/tool-results/bp2lif8fc.txt

Preview (first 2KB):
from __future__ import annotations


from sqlglot import exp
from sqlglot.helper import seq_get
from sqlglot.parsers.mysql import MySQLParser
from sqlglot.tokens import TokenType


# Accept both DATE_TRUNC
…[1304 chars elided]…
       "UNIQUE": lambda self: self._parse_composite_key_property(exp.UniqueKeyProperty),
        # Plain KEY without UNIQUE/DUPLICATE/AGGREGATE prefixes should be treated as UniqueKeyProperty with unique=False
        "KEY": lambda self: self._parse_composite_key_property(exp.UniqueKeyProperty),
        "BUILD": lambda self: self._parse_build_property(),
        "REFRESH": lambda self: self._parse_refresh_property(),
    }

    def _parse_partition_property(
        self,
...
</persisted-output>
[tool_use Bash] {"command": "grep -rn \"DATE_ADD\\|DATE_SUB\\|DateAdd\\|DateSub\\|build_date_delta\\|DATE_ADD_SUB\\|ADDDATE\\|SUBDATE\" sqlglot/parsers/mysql.py sqlglot/generators/mysql.py sqlglot/parsers/doris.py sqlglot/generators/doris.py sqlglot/parsers/starrocks.py sqlglot/generators/starrocks.py sqlglot/parser.py sqlglot/dialects/mysql.py | head -40; grep -rn \"date_add\\|DATE_ADD\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_mysql.py | head -30"}
[tool_result] sqlglot/generators/mysql.py:8:    build_date_delta,
sqlglot/generators/mysql.py:9:    build_date_delta_with_interval,
sqlglot/generators/mysql.py:151:        exp.DateAdd: _remove_ts_or_ds_to_date(date_add_sql("ADD")),
sqlglot/generators/mysql.py:153:        exp.DateSub: _remove_ts_or_ds_to_date(date_add_sql("SUB")),
sqlglot/generators/mysql.py:740:        timestamp_diff = build_date_delta(exp.TimestampDiff)([unit, start_ts, expression.this])
sqlglot/generators/mysql.py:742:        dateadd = buil
…[1238 chars elided]…
AL (2 * 2) MONTH) FROM foo",
tests/dialects/test_mysql.py:1460:                        f"DATE_ADD('0000-01-01 00:00:00', INTERVAL (TIMESTAMPDIFF({unit}, '0000-01-01 00:00:00', {cast})) {unit})",
tests/dialects/test_mysql.py:1465:                            "mysql": f"DATE_ADD('0000-01-01 00:00:00', INTERVAL (TIMESTAMPDIFF({unit}, '0000-01-01 00:00:00', {cast})) {unit})",
tests/dialects/test_mysql.py:1618:                self.validate_identity(f"DATE_ADD(base_date, INTERVAL day_interval {unit})")
[tool_use Bash] {"command": "sed -n 1570,1625p sqlglot/dialects/dialect.py; echo ----; sed -n 1930,1960p sqlglot/dialects/dialect.py; echo ----; sed -n 105,125p sqlglot/parsers/mysql.py; echo ----; grep -n \"def date_add_sql\" -A25 sqlglot/dialects/dialect.py; echo ----; grep -n \"^def \\|^    def \\|TsOrDsAdd\" sqlglot/generators/doris.py | head -5; sed -n 60,90p sqlglot/generators/doris.py"}
[tool_result]         """
        time_format = self.format_time(expression)
        return time_format if time_format != Dialect.get_or_raise(dialect).TIME_FORMAT else None

    return _time_format


def build_date_delta(
    exp_class: Type[E],
    unit_mapping: dict[str, str] | None = None,
    default_unit: str | None = "DAY",
    supports_timezone: bool = False,
) -> t.Callable[[BuilderArgs], E]:
    def _builder(args: BuilderArgs) -> E:
        unit_based = len(args) >= 3
        has_timezone = len(args
…[5203 chars elided]…
elf.func("DATE_TRUNC", e.this, unit_to_str(e)),
        exp.UnixToStr: lambda self, e: self.func(
            "FROM_UNIXTIME", e.this, time_format("doris")(self, e)
        ),
        exp.UnixToTime: rename_func("FROM_UNIXTIME"),
    }

    # https://github.com/apache/doris/blob/e4f41dbf1ec03f5937fdeba2ee1454a20254015b/fe/fe-core/src/main/antlr4/org/apache/doris/nereids/DorisLexer.g4#L93
    RESERVED_KEYWORDS = {
        "account_lock",
        "account_unlock",
        "add",
        "adddate",
[tool_use Bash] {"command": "cat sqlglot/generators/starrocks.py | head -60; echo ----; grep -n \"class TsOrDsAdd\" -A12 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null; grep -n \"class DateSub\\|class DateAdd\" -A6 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null; echo ----; grep -n \"TsOrDsAdd\\|DateSub\" sqlglot/parsers/*.py sqlglot/generators/mysql.py sqlglot/generators/starrocks.py | head; echo ---; grep -n \"starrocks\\|doris\" tests/dialects/test_*.py | grep -i \"date_add\\|date_sub\\|DATE_\" | head"}
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

…[4870 chars elided]…
ris": "DATE_FORMAT(x, '%Y-%m-%d')",
tests/dialects/test_dialect.py:1067:                "starrocks": "DATE_ADD(x, INTERVAL 1 DAY)",
tests/dialects/test_dialect.py:1069:                "doris": "DATE_ADD(x, INTERVAL 1 DAY)",
tests/dialects/test_dialect.py:1083:                "starrocks": "DATE_ADD(x, INTERVAL 1 DAY)",
tests/dialects/test_dialect.py:1084:                "doris": "DATE_ADD(x, INTERVAL 1 DAY)",
tests/dialects/test_dialect.py:1102:                "starrocks": "DATE_TRUNC('DAY', x)",
[tool_use Bash] {"command": "sed -n 28,45p sqlglot/parsers/hive.py; sed -n 60,70p sqlglot/parsers/hive.py; grep -n \"TsOrDsAdd\" sqlglot/generators/hive.py sqlglot/generators/spark*.py sqlglot/generators/mysql.py sqlglot/generators/starrocks.py sqlglot/generators/doris.py | head; grep -n \"Neg\\b\" sqlglot/parsers/*.py | head -3; sed -n 1,30p sqlglot/parsers/starrocks.py"}
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
        **parser.Parser.FUNCTIONS,
        "BASE64": exp.ToBase64.from_
…[1968 chars elided]…
 2), unit=seq_get(args, 0)
        ),
        "ARRAY_FLATTEN": exp.Flatten.from_arg_list,
        "REGEXP": exp.RegexpLike.from_arg_list,
    }

    PROPERTY_PARSERS = {
        **MySQLParser.PROPERTY_PARSERS,
        "PROPERTIES": lambda self: self._parse_wrapped_properties(),
        "UNIQUE": lambda self: self._parse_composite_key_property(exp.UniqueKeyProperty),
        "ROLLUP": lambda self: self._parse_rollup_property(),
        "REFRESH": lambda self: self._parse_refresh_property(),
    }
[tool_use Bash] {"command": "grep -n \"BuilderArgs\\|^from\\|^import\" sqlglot/dialects/dialect.py | head -30; sed -n 1,12p sqlglot/parsers/doris.py | grep -n import; grep -n \"def date_add_sql\" -A20 sqlglot/dialects/dialect.py | head -30; grep -n \"_sql\\b.*getattr\\|TRANSFORMS\" sqlglot/generator.py | head"}
[tool_result] 1:from __future__ import annotations
3:import importlib
4:import logging
5:import typing as t
6:import sys
7:from collections.abc import Iterable, MutableSequence
8:from enum import Enum, auto
9:from functools import reduce
10:from builtins import type as Type
12:from sqlglot import exp
13:from sqlglot.dialects import DIALECT_MODULE_NAMES
14:from sqlglot.errors import ParseError
15:from sqlglot.generator import Generator, unsupported_args
16:from sqlglot.expressions import apply_index_offset
17:
…[1171 chars elided]…
dict[str, t.Any] = {
80:    dispatch: dict[type[exp.Expr], t.Callable[..., str]] = dict(cls.TRANSFORMS)
134:    TRANSFORMS: t.ClassVar[dict[type[exp.Expr], t.Callable[..., str]]] = {
135:        **JSON_PATH_PART_TRANSFORMS,
632:    AFTER_HAVING_MODIFIER_TRANSFORMS: t.ClassVar = {
636:        **AFTER_HAVING_MODIFIER_TRANSFORMS,
3024:            *[gen(self, expression) for gen in self.AFTER_HAVING_MODIFIER_TRANSFORMS.values()],
3510:            transform = self.TRANSFORMS.get(expression.__class__)
[assistant] Now I'll add a shared builder in `dialect.py` and wire it into both parsers.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-091426-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py", "old_string": "        return expression_class(this=args[0], expression=interval.this, unit=unit_to_str(interval))\n\n    return _builder\n\n", "new_string": "        return expression_class(this=args[0], expression=interval
…[269 chars elided]…
h_interval(expression_class)\n\n    def _builder(args: BuilderArgs) -> E | exp.TsOrDsAdd | None:\n        if len(args) == 2 and not isinstance(args[1], exp.Interval):\n            days = exp.Neg(this=args[1]) if negate else args[1]\n            return exp.TsOrDsAdd(this=args[0], expression=days, unit=exp.Literal.string(\"DAY\"))\n\n        return interval_builder(args)\n\n    return _builder\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-091426-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py has been updated successfully.
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\np='sqlglot/parsers/doris.py'\ns=open(p).read()\ns=s.replace(\"\"\"from sqlglot import exp\nfrom sqlglot.helper import seq_get\n\"\"\",\"\"\"from sqlglot import exp\nfrom sqlglot.dialects.dialect import build_date_delta_with_interval_or_days\nfrom sqlglot.helper import seq_get\n\"\"\",1)\ns=s.replace(\"\"\"        \"COLLECT_SET\": exp.ArrayUniqueAgg.from_a
…[682 chars elided]…
ld_timestamp_trunc,\n\"\"\",\"\"\"        **MySQLParser.FUNCTIONS,\n        \"DATE_ADD\": build_date_delta_with_interval_or_days(exp.DateAdd),\n        \"DATE_SUB\": build_date_delta_with_interval_or_days(exp.DateSub, negate=True),\n        \"DATE_TRUNC\": build_timestamp_trunc,\n\"\"\",1)\nopen(p,'w').write(s)\nEOF\ngit diff --stat; grep -n \"date_add_sql\" sqlglot/dialects/dialect.py | head -3"}
[tool_result]  sqlglot/dialects/dialect.py  | 16 ++++++++++++++++
 sqlglot/parsers/doris.py     |  3 +++
 sqlglot/parsers/starrocks.py |  4 +++-
 3 files changed, 22 insertions(+), 1 deletion(-)
[assistant] Parsing is wired up. Now let me check what the generators currently emit for this node before touching StarRocks' output.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor d in ['doris','starrocks']:\n    for q in ['select date_add(\\'2025-01-01\\', 1) from a','select date_sub(\\'2025-01-01\\', 1) from a','select date_add(x, interval 1 day) from a','select date_sub(x, interval 2 month) from a']:\n        e=sqlglot.parse_one(q,read=d)\n        print(d, '|', repr(e.selects[0])[:0], '|', e.sql(d), '|', e.sql('duckdb'), '|', e.sql('mysql'))\n\""}
[tool_result] doris |  | SELECT DATE_ADD('2025-01-01', 1) FROM a | SELECT CAST('2025-01-01' AS DATE) + INTERVAL 1 DAY FROM a | SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY) FROM a
doris |  | SELECT DATE_ADD('2025-01-01', -1) FROM a | SELECT CAST('2025-01-01' AS DATE) + INTERVAL (-1) DAY FROM a | SELECT DATE_ADD('2025-01-01', INTERVAL -1 DAY) FROM a
doris |  | SELECT DATE_ADD(x, INTERVAL '1' DAY) FROM a | SELECT x + INTERVAL '1' DAY FROM a | SELECT DATE_ADD(x, INTERVAL '1' DAY) FROM a
doris |  | SELECT DATE_SU
…[279 chars elided]…
INTERVAL 1 DAY) FROM a
starrocks |  | SELECT DATE_ADD('2025-01-01', INTERVAL -1 DAY) FROM a | SELECT CAST('2025-01-01' AS DATE) + INTERVAL (-1) DAY FROM a | SELECT DATE_ADD('2025-01-01', INTERVAL -1 DAY) FROM a
starrocks |  | SELECT DATE_ADD(x, INTERVAL '1' DAY) FROM a | SELECT x + INTERVAL '1' DAY FROM a | SELECT DATE_ADD(x, INTERVAL '1' DAY) FROM a
starrocks |  | SELECT DATE_SUB(x, INTERVAL '2' MONTH) FROM a | SELECT x - INTERVAL '2' MONTH FROM a | SELECT DATE_SUB(x, INTERVAL '2' MONTH) FROM a
[assistant] Doris already emits the two-argument form. StarRocks still emits the `INTERVAL` form, so I'll add a generator method there. It only uses the two-argument form for day units and falls back to the existing MySQL output for other units.
[tool_use Bash] {"command": "grep -n \"    def \\|    TRANSFORMS\\|^class\\|^from\" sqlglot/generators/starrocks.py | head -30; grep -n \"date_add_sql\" sqlglot/generators/mysql.py | head -3; sed -n 1,25p sqlglot/generators/mysql.py | grep -n \"date_add_sql\\|dialect import\" "}
[tool_result] 1:from __future__ import annotations
4:from sqlglot import exp, transforms
5:from sqlglot.dialects.dialect import (
13:from sqlglot.generators.mysql import MySQLGenerator
54:class StarRocksGenerator(MySQLGenerator):
88:    TRANSFORMS = {
268:    def create_sql(self, expression: exp.Create) -> str:
289:    def partitionedbyproperty_sql(self, expression: exp.PartitionedByProperty) -> str:
305:    def cluster_sql(self, expression: exp.Cluster) -> str:
310:    def refreshtriggerproperty_sql(self, expression: exp.RefreshTriggerProperty) -> str:
74:def date_add_sql(
151:        exp.DateAdd: _remove_ts_or_ds_to_date(date_add_sql("ADD")),
153:        exp.DateSub: _remove_ts_or_ds_to_date(date_add_sql("SUB")),
6:from sqlglot.dialects.dialect import (
[tool_use Bash] {"command": "sed -n 5,13p sqlglot/generators/starrocks.py; sed -n 305,312p sqlglot/generators/starrocks.py"}
[tool_result] from sqlglot.dialects.dialect import (
    approx_count_distinct_sql,
    arrow_json_extract_sql,
    rename_func,
    unit_to_str,
    inline_array_sql,
    property_sql,
)
from sqlglot.generators.mysql import MySQLGenerator
    def cluster_sql(self, expression: exp.Cluster) -> str:
        """Generate StarRocks ORDER BY clause for clustering."""
        expressions = self.expressions(expression, flat=True)
        return f"ORDER BY ({expressions})" if expressions else ""

    def refreshtriggerproperty_sql(self, expression: exp.RefreshTriggerProperty) -> str:
        """Generate StarRocks REFRESH clause for materialized views.
        There is a little difference of the syntax between StarRocks and Doris.
[tool_use Bash] {"command": "python3 - <<'EOF'\np='sqlglot/generators/starrocks.py'\ns=open(p).read()\ns=s.replace(\"\"\"    arrow_json_extract_sql,\n    rename_func,\n\"\"\",\"\"\"    arrow_json_extract_sql,\n    date_add_sql,\n    rename_func,\n\"\"\",1)\ns=s.replace(\"\"\"    def cluster_sql(self, expression: exp.Cluster) -> str:\"\"\",\"\"\"    def tsordsadd_sql(self, expression: exp.TsOrDsAdd) -> str:\n     
…[896 chars elided]…
nspile(\\\"select date_add(x, 1)\\\", read='hive', write='starrocks'))\nprint(sqlglot.transpile(\\\"select date_sub(x, 1)\\\", read='doris', write='starrocks'))\nprint(sqlglot.transpile(\\\"select date_add(x, interval 1 month)\\\", read='hive', write='starrocks'))\nprint(sqlglot.parse(\\\"select date_add('2025-01-01', 1) from a\\\", dialect='doris', error_level=sqlglot.ErrorLevel.IMMEDIATE))\n\""}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 6, in <module>
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-091426-doris-and-starrocks-dialects-bot/base-1/sqlglot/__init__.py", line 171, in parse_one
    dialect = Dialect.get_or_raise(read or dialect)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-091426-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py", l
…[2207 chars elided]…
 AS DATE) + INTERVAL (-1) DAY FROM a | SELECT DATE_ADD('2025-01-01', INTERVAL -1 DAY) FROM a
doris | SELECT DATE_ADD(x, INTERVAL '1' DAY) FROM a | SELECT x + INTERVAL '1' DAY FROM a | SELECT DATE_ADD(x, INTERVAL '1' DAY) FROM a
doris | SELECT DATE_SUB(x, INTERVAL '2' MONTH) FROM a | SELECT x - INTERVAL '2' MONTH FROM a | SELECT DATE_SUB(x, INTERVAL '2' MONTH) FROM a
doris | SELECT DATE_ADD(x, n) FROM a | SELECT CAST(x AS DATE) + INTERVAL (n) DAY FROM a | SELECT DATE_ADD(x, INTERVAL n DAY) FROM a
[assistant] `date_add_sql` lives in `generators/mysql.py`, not `dialect.py`. Fixing the import:
[tool_use Bash] {"command": "python3 - <<'EOF'\np='sqlglot/generators/starrocks.py'\ns=open(p).read()\ns=s.replace(\"    date_add_sql,\\n\",\"\",1)\ns=s.replace(\"from sqlglot.generators.mysql import MySQLGenerator\",\"from sqlglot.generators.mysql import MySQLGenerator, date_add_sql\",1)\nopen(p,'w').write(s)\nEOF\n<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nf
…[395 chars elided]…
nspile(\\\"select date_add(x, 1)\\\", read='hive', write='starrocks'))\nprint(sqlglot.transpile(\\\"select date_sub(x, 1)\\\", read='doris', write='starrocks'))\nprint(sqlglot.transpile(\\\"select date_add(x, interval 1 month)\\\", read='hive', write='starrocks'))\nprint(sqlglot.parse(\\\"select date_add('2025-01-01', 1) from a\\\", dialect='doris', error_level=sqlglot.ErrorLevel.IMMEDIATE))\n\""}
[tool_result] doris | SELECT DATE_ADD('2025-01-01', 1) FROM a | SELECT CAST('2025-01-01' AS DATE) + INTERVAL 1 DAY FROM a | SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY) FROM a
doris | SELECT DATE_ADD('2025-01-01', -1) FROM a | SELECT CAST('2025-01-01' AS DATE) + INTERVAL (-1) DAY FROM a | SELECT DATE_ADD('2025-01-01', INTERVAL -1 DAY) FROM a
doris | SELECT DATE_ADD(x, INTERVAL '1' DAY) FROM a | SELECT x + INTERVAL '1' DAY FROM a | SELECT DATE_ADD(x, INTERVAL '1' DAY) FROM a
doris | SELECT DATE_SUB(x, INTERVA
…[925 chars elided]…
AL n DAY) FROM a | SELECT CAST(x AS DATE) + INTERVAL (n) DAY FROM a | SELECT DATE_ADD(x, INTERVAL n DAY) FROM a
['SELECT DATE_ADD(x, INTERVAL 1 DAY)']
['SELECT DATE_ADD(x, INTERVAL -1 DAY)']
["SELECT DATE_ADD(x, INTERVAL (INTERVAL '1' MONTH) DAY)"]
[Select(
  expressions=[
    TsOrDsAdd(
      this=Literal(this='2025-01-01', is_string=True),
      expression=Literal(this=1, is_string=False),
      unit=Var(this=DAY))],
  from_=From(
    this=Table(
      this=Identifier(this=a, quoted=False))))]
[assistant] The StarRocks output still uses the `INTERVAL` form, so the new method isn't being dispatched. Checking how generator dispatch resolves names:
[tool_use Bash] {"command": "sed -n 76,100p sqlglot/generator.py"}
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
[assistant] Inherited `TRANSFORMS` entries from MySQL take precedence over auto-discovered `*_sql` methods, so the method I added is never reached. I'll replace it with a `TRANSFORMS` entry in the StarRocks generator, keeping the day-only guard.
[tool_use Bash] {"command": "python3 - <<'EOF'\np='sqlglot/generators/starrocks.py'\ns=open(p).read()\ns=s.replace(\"\"\"    def tsordsadd_sql(self, expression: exp.TsOrDsAdd) -> str:\n        if expression.text(\"unit\").upper() == \"DAY\":\n            return self.func(\"DATE_ADD\", expression.this, expression.expression)\n        return date_add_sql(\"ADD\")(self, expression)\n\n\"\"\",\"\",1)\nopen(p,'w').write(s)\nEOF\ngrep -n \"TRANSFORMS = {\" -A4 sqlglot/generators/starrocks.py; grep -n \"exp.TimeToUnix\\|exp.TimestampTrunc\\|exp.Trim\\|exp.TsOrDsToDate\\|exp.Unix\" sqlglot/generators/starrocks.py"}
[tool_result] 88:    TRANSFORMS = {
89-        **{k: v for k, v in MySQLGenerator.TRANSFORMS.items() if k is not exp.DateTrunc},
90-        exp.Array: inline_array_sql,
91-        exp.ArrayAgg: rename_func("ARRAY_AGG"),
92-        exp.ArrayFilter: rename_func("ARRAY_FILTER"),
107:        exp.TimestampTrunc: lambda self, e: self.func("DATE_TRUNC", unit_to_str(e), e.this),
109:        exp.UnixToStr: lambda self, e: self.func("FROM_UNIXTIME", e.this, self.format_time(e)),
110:        exp.UnixToTime: rename_func("FROM_UNIXTIME"),
[tool_use Bash] {"command": "sed -n 104,112p sqlglot/generators/starrocks.py"}
[tool_result]         exp.SqlSecurityProperty: lambda self, e: f"SECURITY {self.sql(e.this)}",
        exp.StDistance: st_distance_sphere,
        exp.StrToUnix: lambda self, e: self.func("UNIX_TIMESTAMP", e.this, self.format_time(e)),
        exp.TimestampTrunc: lambda self, e: self.func("DATE_TRUNC", unit_to_str(e), e.this),
        exp.TimeStrToDate: rename_func("TO_DATE"),
        exp.UnixToStr: lambda self, e: self.func("FROM_UNIXTIME", e.this, self.format_time(e)),
        exp.UnixToTime: rename_func("FROM_UNIXTIME"),
    }
[tool_use Bash] {"command": "python3 - <<'EOF'\np='sqlglot/generators/starrocks.py'\ns=open(p).read()\ns=s.replace(\"\"\"        exp.TimeStrToDate: rename_func(\"TO_DATE\"),\n        exp.UnixToStr\"\"\",\"\"\"        exp.TimeStrToDate: rename_func(\"TO_DATE\"),\n        exp.TsOrDsAdd: lambda self, e: (\n            self.func(\"DATE_ADD\", e.this, e.expression)\n            if e.text(\"unit\").upper() == \"DAY\"\n
…[855 chars elided]…
rocks'))\nprint(sqlglot.transpile(\\\"select date_add(x, 1)\\\", read='starrocks', write='doris'))\nprint(sqlglot.parse('select date_add(\\'2025-01-01\\', 1) from a', dialect='doris', error_level=sqlglot.ErrorLevel.IMMEDIATE)[0].sql('doris'))\nprint(sqlglot.parse('select date_add(\\'2025-01-01\\', 1) from a', dialect='starrocks', error_level=sqlglot.ErrorLevel.IMMEDIATE)[0].sql('starrocks'))\n\""}
[tool_result] doris | SELECT DATE_ADD('2025-01-01', 1) FROM a | SELECT CAST('2025-01-01' AS DATE) + INTERVAL 1 DAY FROM a | SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY) FROM a
doris | SELECT DATE_ADD('2025-01-01', -1) FROM a | SELECT CAST('2025-01-01' AS DATE) + INTERVAL (-1) DAY FROM a | SELECT DATE_ADD('2025-01-01', INTERVAL -1 DAY) FROM a
doris | SELECT DATE_ADD(x, INTERVAL '1' DAY) FROM a | SELECT x + INTERVAL '1' DAY FROM a | SELECT DATE_ADD(x, INTERVAL '1' DAY) FROM a
doris | SELECT DATE_SUB(x, INTERVA
…[681 chars elided]…
ATE_ADD(x, INTERVAL '1' DAY) FROM a
starrocks | SELECT DATE_SUB(x, INTERVAL '2' MONTH) FROM a | SELECT x - INTERVAL '2' MONTH FROM a | SELECT DATE_SUB(x, INTERVAL '2' MONTH) FROM a
starrocks | SELECT DATE_ADD(x, n) FROM a | SELECT CAST(x AS DATE) + INTERVAL (n) DAY FROM a | SELECT DATE_ADD(x, INTERVAL n DAY) FROM a
['SELECT DATE_ADD(x, 1)']
['SELECT DATE_ADD(x, 1)']
['SELECT DATE_ADD(x, 1)']
['SELECT DATE_ADD(x, 1)']
SELECT DATE_ADD('2025-01-01', 1) FROM a
SELECT DATE_ADD('2025-01-01', 1) FROM a
[assistant] Both dialects now parse and emit the two-argument form, and the `INTERVAL` forms are unchanged. Next I'll add tests to the dialect test files and run the project's test command.
[tool_use Bash] {"command": "ls tests/dialects | grep -i \"doris\\|starrocks\"; grep -n \"def test_\\|validate_all\" tests/dialects/test_doris.py | head -8; grep -n \"def test_\\|validate_all\" tests/dialects/test_starrocks.py | head -8"}
[tool_result] test_doris.py
test_starrocks.py
7:    def test_doris(self):
8:        self.validate_all(
15:        self.validate_all(
21:        self.validate_all(
31:        self.validate_all(
41:        self.validate_all(
51:        self.validate_all(
59:        self.validate_all(
9:    def test_starrocks(self):
20:        self.validate_all(
30:    def test_ddl(self):
77:        self.validate_all(
125:    def test_identity(self):
136:    def test_time(self):
145:    def test_regex(self):
146:        self.validate_all(
[tool_use Bash] {"command": "sed -n 1,30p tests/dialects/test_doris.py; echo ----; sed -n 1,30p tests/dialects/test_starrocks.py"}
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
             
…[1063 chars elided]…
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
[tool_use Bash] {"command": "python3 - <<'EOF'\np='tests/dialects/test_doris.py'\ns=open(p).read()\ns=s.replace(\"\"\"    def test_doris(self):\n\"\"\",\"\"\"    def test_doris(self):\n        self.validate_identity(\"SELECT DATE_ADD('2025-01-01', 1)\")\n        self.validate_all(\n            \"SELECT DATE_SUB('2025-01-01', 1)\",\n            write={\n                \"doris\": \"SELECT DATE_ADD('2025-01-01', -1
…[902 chars elided]…
 self.validate_all(\n            \"SELECT DATE_ADD(x, INTERVAL 1 MONTH)\",\n            write={\"starrocks\": \"SELECT DATE_ADD(x, INTERVAL 1 MONTH)\"},\n        )\n\"\"\",1)\nopen(p,'w').write(s)\nEOF\n<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_doris.py tests/dialects/test_starrocks.py 2>&1 | tail -30"}
[tool_result] ....................     [100%]
=================================== FAILURES ===================================
_ TestDoris.test_doris [SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY) -> doris] _
tests/dialects/test_dialect.py:101: in validate_all
    self.assertEqual(
E   AssertionError: "SELECT DATE_ADD('2025-01-01', INTERVAL '1' DAY)" != "SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY)"
E   - SELECT DATE_ADD('2025-01-01', INTERVAL '1' DAY)
E   ?                                        - -
E   + S
…[306 chars elided]…

E   - SELECT DATE_ADD(x, INTERVAL '1' MONTH)
E   ?                             - -
E   + SELECT DATE_ADD(x, INTERVAL 1 MONTH)
=========================== short test summary info ============================
SUBFAILED[SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY) -> doris] tests/dialects/test_doris.py::TestDoris::test_doris
SUBFAILED[SELECT DATE_ADD(x, INTERVAL 1 MONTH) -> starrocks] tests/dialects/test_starrocks.py::TestStarrocks::test_starrocks
2 failed, 20 passed, 118 subtests passed in 0.20s
[assistant] Both failures are mistakes in my new test expectations, not the code: the interval literal is generated as `'1'`. Correcting those two expected strings:
[tool_use Bash] {"command": "sed -i \"s/write={\\\"doris\\\": \\\"SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY)\\\"}/write={\\\"doris\\\": \\\"SELECT DATE_ADD('2025-01-01', INTERVAL '1' DAY)\\\"}/\" tests/dialects/test_doris.py && sed -i 's/write={\"starrocks\": \"SELECT DATE_ADD(x, INTERVAL 1 MONTH)\"}/write={\"starrocks\": \"SELECT DATE_ADD(x, INTERVAL '\"'\"'1'\"'\"' MONTH)\"}/' tests/dialects/test_starrocks.py && grep -n \"INTERVAL '1'\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15"}
[tool_result ERROR] Exit code 1
sed: 2: "tests/dialects/test_dor ...": undefined label 'ests/dialects/test_doris.py'
[assistant] The `sed -i` call failed because BSD sed on macOS needs an explicit backup-suffix argument. I'll make the edits with Python instead.
[tool_use Bash] {"command": "python3 - <<'EOF'\nfor p,a,b in [\n ('tests/dialects/test_doris.py',\"write={\\\"doris\\\": \\\"SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY)\\\"}\",\"write={\\\"doris\\\": \\\"SELECT DATE_ADD('2025-01-01', INTERVAL '1' DAY)\\\"}\"),\n ('tests/dialects/test_starrocks.py','write={\"starrocks\": \"SELECT DATE_ADD(x, INTERVAL 1 MONTH)\"}','write={\"starrocks\": \"SELECT DATE_ADD(x, INTERVAL \\'1\\' MONTH)\"}'),\n]:\n    s=open(p).read(); assert s.count(a)==1, p; open(p,'w').write(s.replace(a,b))\nEOF\n<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15"}
[tool_result] ............. [ 23%]
..................................................................................................................................... [ 35%]
............................................................................................................................................ [ 48%]
.............................................. [ 52%]
.................................. [ 55%]
............................................... [ 60%]
............... [ 61%]
.... [ 62%]
....
…[1 chars elided]…
.............................................................. [ 68%]
............................................... [ 72%]
........................................................... [ 78%]
....................................................................................................................................... [ 90%]
............................... [ 93%]
........................................................................   [100%]
1084 passed, 17850 subtests passed in 52.62s
[assistant] The full suite passes (1084 tests). Last step: lint the changed files and review the final diff.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/dialects/dialect.py sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py sqlglot/generators/starrocks.py tests/dialects/test_doris.py tests/dialects/test_starrocks.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot tests/dialects/test_doris.py tests/dialects/test_starrocks.py) 2>&1 | tail -8; git status --short; git diff sqlglot/"}
[tool_result] All checks passed!
175 files already formatted
 M sqlglot/dialects/dialect.py
 M sqlglot/generators/starrocks.py
 M sqlglot/parsers/doris.py
 M sqlglot/parsers/starrocks.py
 M tests/dialects/test_doris.py
 M tests/dialects/test_starrocks.py
diff --git a/sqlglot/dialects/dialect.py b/sqlglot/dialects/dialect.py
index bbb4515c5..f9c2e10b3 100644
--- a/sqlglot/dialects/dialect.py
+++ b/sqlglot/dialects/dialect.py
@@ -1613,6 +1613,22 @@ def build_date_delta_with_interval(
     return _builder
 
 
+d
…[3320 chars elided]…
10,6 +10,8 @@ from sqlglot.parsers.mysql import MySQLParser
 class StarRocksParser(MySQLParser):
     FUNCTIONS = {
         **MySQLParser.FUNCTIONS,
+        "DATE_ADD": build_date_delta_with_interval_or_days(exp.DateAdd),
+        "DATE_SUB": build_date_delta_with_interval_or_days(exp.DateSub, negate=True),
         "DATE_TRUNC": build_timestamp_trunc,
         "DATEDIFF": lambda args: exp.DateDiff(
             this=seq_get(args, 0), expression=seq_get(args, 1), unit=exp.Literal.string("DAY")
[assistant] Doris and StarRocks now both parse and generate the two-argument `DATE_ADD` / `DATE_SUB` form. The example from the report parses without error, and the full test suite passes (1084 tests), along with ruff check and format.

**What changed**
- **Parsing** (`sqlglot/dialects/dialect.py`, `parsers/doris.py`, `parsers/starrocks.py`): a new shared builder, `build_date_delta_with_interval_or_days`, takes the two-argument form as a day count and builds a `TsOrDsAdd` with unit `DAY`. The `INTERVAL` form still goes through the existing builder, so `DATE_ADD(x, INTERVAL 1 DAY)` parses exactly as before
…[632 chars elided]…
-discovered `tsordsadd_sql` method, because the inherited MySQL `TRANSFORMS` entry takes precedence over auto-discovered methods.
- **Doris's generator is unchanged.** It still ignores the unit, so a non-day `TsOrDsAdd` is emitted as a day count. That predates this change, and I left it alone to keep the change scoped.

**Tests added** in `tests/dialects/test_doris.py` and `test_starrocks.py`: identity and cross-dialect round trips for the two-argument form, the `DATE_SUB` negation, and a check that the `INTERVAL` forms are unchanged.

Nothing is committed. The changes are in the working tree.
