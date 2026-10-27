# trajectory base-2

final message:
Doris and StarRocks now accept the two-argument `DATE_ADD` / `DATE_SUB` form. The full test suite passes: 1086 passed, 17854 subtests, 0 failures.

**Parsing:** `DATE_ADD(date, n)` builds `exp.TsOrDsAdd` with `unit=DAY` and `return_type=TIMESTAMP`. `DATE_SUB(date, n)` builds the same node with `Neg(n)`. The `INTERVAL` form still builds `DateAdd` / `DateSub`. A shared builder, `build_date_delta_with_interval_or_days` in `sqlglot/dialects/dialect.py`, is used by both parsers.

**Generation:**
- Doris already emitted `DATE_ADD(x, n)` for `TsOrDsAdd`.
- StarRocks now does too, via a new `TsOrDsAdd` transform.
- Both generators fall back to the `INTERVAL` form when the unit is not DAY.

**Results checked:**
- `DATE_ADD('2025-01-01', 1)` round-trips and transpiles to DuckDB as `CAST(... AS TIMESTAMP) + INTERVAL 1 DAY`, and to MySQL as `DATE_ADD(..., INTERVAL 1 DAY)`.
- Redshift `DATEADD(MONTH, 1, x)` now generates `DATE_ADD(x, INTERVAL '1' MONTH)` in Doris and StarRocks.

**Trade-offs:**
- `DATE_SUB(d, 1)` is emitted as `DATE_ADD(d, -1)`. It is equivalent but not textually identical.
- The unit guard in the Doris generator also fixes a pre-existing bug I found: a MONTH-unit `TsOrDsAdd` was emitted as `DATE_ADD(x, 1)` with the unit dropped.

**Tests:** `test_date_add_days` was added to `tests/dialects/test_doris.py` and `tests/dialects/test_starrocks.py`. It asserts node classes, round-trips, and the DuckDB, MySQL and Redshift-to-Doris/StarRocks targets. Ruff lint and format pass.

## events
[tool_use Bash] {"command": "git status --short | head && ls sqlglot/parsers | grep -iE 'doris|starrocks|mysql' ; ls sqlglot/generators | grep -iE 'doris|starrocks|mysql'; grep -n -iE 'date_add|DateAdd|DATE_SUB|DateSub' sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py sqlglot/parsers/mysql.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py sqlglot/generators/mysql.py sqlglot/dialects/doris.py sqlglot/dialects/starrocks.py sqlglot/dialects/mysql.py"}
[tool_result] doris.py
mysql.py
starrocks.py
doris.py
mysql.py
starrocks.py
sqlglot/parsers/mysql.py:114:        "DATE_ADD": build_date_delta_with_interval(exp.DateAdd),
sqlglot/parsers/mysql.py:119:        "DATE_SUB": build_date_delta_with_interval(exp.DateSub),
sqlglot/generators/doris.py:75:        exp.TsOrDsAdd: lambda self, e: self.func("DATE_ADD", e.this, e.expression),
sqlglot/generators/doris.py:184:        "date_add",
sqlglot/generators/doris.py:188:        "date_sub",
sqlglot/generators/doris.py:189
…[275 chars elided]…
Sub: _remove_ts_or_ds_to_date(date_add_sql("SUB")),
sqlglot/generators/mysql.py:192:        exp.TimestampAdd: date_add_interval_sql("DATE", "ADD"),
sqlglot/generators/mysql.py:196:        exp.TimestampSub: date_add_interval_sql("DATE", "SUB"),
sqlglot/generators/mysql.py:209:        exp.TsOrDsAdd: date_add_sql("ADD"),
sqlglot/generators/mysql.py:742:        dateadd = build_date_delta_with_interval(exp.DateAdd)([start_ts, interval])
sqlglot/generators/mysql.py:744:        return self.sql(dateadd)
[tool_use Bash] {"command": "cat sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py; cat sqlglot/dialects/doris.py sqlglot/dialects/starrocks.py; sed -n 1,140p sqlglot/generators/doris.py; sed -n 170,200p sqlglot/generators/doris.py; cat sqlglot/generators/starrocks.py | head -80; grep -n \"def build_date_delta_with_interval\" -A25 sqlglot/parsers/*.py sqlglot/*.py sqlglot/dialects/dialect.py | head -40"}
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
    
…[19920 chars elided]…
imestampTrunc:
sqlglot/dialects/dialect.py-1617-    unit = seq_get(args, 0)
sqlglot/dialects/dialect.py-1618-    this = seq_get(args, 1)
sqlglot/dialects/dialect.py-1619-
sqlglot/dialects/dialect.py-1620-    if isinstance(this, exp.Cast) and this.is_type("date"):
sqlglot/dialects/dialect.py-1621-        return exp.DateTrunc(unit=unit, this=this)
sqlglot/dialects/dialect.py-1622-    return exp.TimestampTrunc(this=this, unit=unit)
sqlglot/dialects/dialect.py-1623-
sqlglot/dialects/dialect.py-1624-
[tool_use Bash] {"command": "sed -n 70,95p sqlglot/generators/mysql.py; sed -n 105,125p sqlglot/parsers/mysql.py; grep -rn -i \"date_add\\|date_sub\\|TsOrDsAdd\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_mysql.py | head -40; grep -n \"class TsOrDsAdd\" -A12 sqlglot/expressions/*.py; grep -n \"TsOrDsAdd\" sqlglot/parsers/*.py sqlglot/dialects/*.py | head"}
[tool_result]         self.format_time(expression),
    )


def date_add_sql(
    kind: str,
) -> t.Callable[[generator.Generator, exp.Expr], str]:
    def func(self: generator.Generator, expression: exp.Expr) -> str:
        return self.func(
            f"DATE_{kind}",
            expression.this,
            exp.Interval(this=expression.expression, unit=unit_to_var(expression)),
        )

    return func


def _ts_or_ds_to_date_sql(self: MySQLGenerator, expression: exp.TsOrDsToDate) -> str:
    time_forma
…[4262 chars elided]…
46:        return exp.TsOrDsAdd(
sqlglot/parsers/redshift.py:25:        if expr_type is exp.TsOrDsAdd:
sqlglot/parsers/redshift.py:36:        "ADD_MONTHS": lambda args: exp.TsOrDsAdd(
sqlglot/parsers/redshift.py:43:        "DATEADD": _build_date_delta(exp.TsOrDsAdd),
sqlglot/parsers/redshift.py:44:        "DATE_ADD": _build_date_delta(exp.TsOrDsAdd),
sqlglot/dialects/dialect.py:40:    exp.TsOrDsAdd,
sqlglot/dialects/dialect.py:43:DATE_ADD_OR_SUB = t.Union[exp.DateAdd, exp.TsOrDsAdd, exp.DateSub]
[tool_use Bash] {"command": "sed -n 28,70p sqlglot/parsers/hive.py; sed -n 40,55p sqlglot/parsers/spark.py; grep -rn -i \"date_add\\|date_sub\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py | head -20; ls tests/dialects | grep -i -E \"doris|starrocks\"; grep -rn \"DATE_ADD\\|date_add\" sqlglot/dialects/mysql.py sqlglot/parsers/mysql.py sqlglot/generators/mysql.py | head"}
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
    
…[1836 chars elided]…
ts_or_ds_to_date(date_add_sql("ADD")),
sqlglot/generators/mysql.py:153:        exp.DateSub: _remove_ts_or_ds_to_date(date_add_sql("SUB")),
sqlglot/generators/mysql.py:192:        exp.TimestampAdd: date_add_interval_sql("DATE", "ADD"),
sqlglot/generators/mysql.py:196:        exp.TimestampSub: date_add_interval_sql("DATE", "SUB"),
sqlglot/generators/mysql.py:209:        exp.TsOrDsAdd: date_add_sql("ADD"),
sqlglot/parsers/mysql.py:114:        "DATE_ADD": build_date_delta_with_interval(exp.DateAdd),
[tool_use Skill] {"skill": "sqlglot-dialect-functions"}
[tool_result] Launching skill: sqlglot-dialect-functions
[user] Base directory for this skill: ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/base-2/.claude/skills/sqlglot-dialect-functions

# Dialect functions and parse fixes in sqlglot

## The invariant: parse into the canonical expression, not a generic node
sqlglot is AST-first. If a function's meaning already has an expression class, the function must
parse into THAT class so it can transpile. The generic nodes `exp.Anonymous`, `exp.AnonymousAggFunc`,
`exp.ParameterizedAgg`, `exp.CombinedAggFunc` and `exp.CombinedParameterizedAgg` (all in
`sqlglot
…[6010 chars elided]…
late already in the file:
  - Parser: `FUNCTION_PARSERS["QUANTILE"] = lambda self: self._parse_quantile()`.
    `_parse_quantile` parses the first group, then `self._parse_func_params()`, which matches
    `)(` and parses the second group. With no second group it builds the non-parametric form.
  - Generator: `exp.Quantile: _quantile_sql` in `TRANSFORMS` emits
    `self.func("quantile", <param>) + f"({<arg>})"`.
  - `"quantile"` also stays in `AGG_FUNCTIONS`. The suffixed names (`quantileIf`, …) don't match
    the exact `FUNCTION_PARSERS` key, so they still parse through the combinator path.

[tool_use Bash] {"command": "ls .lithify 2>/dev/null; grep -n \"^def build_\\|^def .*delta\" sqlglot/dialects/dialect.py | head -60; grep -n \"_build_date_delta\\b\" -A15 sqlglot/parsers/redshift.py | head -30; grep -n \"^class\\|^def test\\|def test_\" tests/dialects/test_doris.py | head -30"}
[tool_result] harness
library
state.json
1537:def build_formatted_time(
1577:def build_date_delta(
1599:def build_date_delta_with_interval(
1840:def build_timestamp_trunc(args: BuilderArgs) -> exp.TimestampTrunc:
1844:def build_trunc(
1934:def date_delta_sql(name: str, cast: bool = False) -> t.Callable[[Generator, DATE_ADD_OR_DIFF], str]:
1949:def date_delta_to_binary_interval_op(
2066:def build_json_extract_path(
2224:def build_default_decimal_type(
2237:def build_timestamp_from_parts(args: BuilderArgs) -> e
…[1373 chars elided]…
currence=seq_get(args, 3),
54-            parameters=seq_get(args, 4),
55-        ),
4:class TestDoris(Validator):
7:    def test_doris(self):
91:    def test_identity(self):
102:    def test_time(self):
108:    def test_regex(self):
116:    def test_analyze(self):
121:    def test_key(self):
126:    def test_distributed(self):
135:    def test_partition(self):
154:    def test_table_alias_conversion(self):
229:    def test_rename_table(self):
239:    def test_materialized_view_properties(self):
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls -la $PY; $PY -c \"import sqlglot,sys;print(sqlglot.__file__)\"; for d in doris starrocks; do $PY -c \"\nimport sqlglot\nfor s in [\\\"select date_add('2025-01-01', 1) from a\\\", \\\"select date_sub('2025-01-01', 1) from a\\\", \\\"select date_add('2025-01-01', INTERVAL 1 DAY) from a\\\"]:\n  try:\n    e=sqlglot.parse_one(s, dialect='$d'); print(repr(e.selects[0])[:200]); print(e.sql('$d'))\n  except Exception as ex: print('ERR', ex)\n\"; done"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 26 08:58 <work>/env-sqlglot/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/base-2/sqlglot/__init__.py
ERR INTERVAL expression expected but got '1'
ERR INTERVAL expression expected but got '1'
DateAdd(
  this=Literal(this='2025-01-01', is_string=True),
  expression=Literal(this='1', is_string=True),
  unit=Var(this=DAY))
SELECT DATE_ADD('2025-01-01', INTERVAL '1' DAY) FROM a
ERR INTERVAL expression expected but got '1'
ERR INTERVAL expression expected but got '1'
DateAdd(
  this=Literal(this='2025-01-01', is_string=True),
  expression=Literal(this='1', is_string=True),
  unit=Var(this=DAY))
SELECT DATE_ADD('2025-01-01', INTERVAL '1' DAY) FROM a
[tool_use Bash] {"command": "grep -n \"TsOrDsAdd\\|DateSub\\|DateAdd\" sqlglot/generators/starrocks.py sqlglot/generators/doris.py; grep -n \"^class Neg\" sqlglot/expressions/*.py; sed -n 1595,1600p sqlglot/dialects/dialect.py; grep -n \"def unit_to_str\" -A12 sqlglot/dialects/dialect.py | head -20"}
[tool_result] sqlglot/generators/doris.py:75:        exp.TsOrDsAdd: lambda self, e: self.func("DATE_ADD", e.this, e.expression),
sqlglot/expressions/core.py:2215:class Neg(Unary):

    return _builder


def build_date_delta_with_interval(
    expression_class: Type[E],
1979:def unit_to_str(expression: exp.Expr, default: str = "DAY") -> exp.Expr | None:
1980-    unit = expression.args.get("unit")
1981-    if not unit:
1982-        return exp.Literal.string(default) if default else None
1983-
1984-    if isinstance(unit, exp.Placeholder) or type(unit) not in (exp.Var, exp.Literal):
1985-        return unit
1986-
1987-    return exp.Literal.string(unit.name)
1988-
1989-
1990-def unit_to_var(expression: exp.Expr, default: str = "DAY") -> exp.Expr | None:
1991-    unit = expression.args.get("unit")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/base-2/sqlglot/dialects/dialect.py", "old_string": "        return expression_class(this=args[0], expression=interval.this, unit=unit_to_str(interval))\n\n    return _builder\n\n", "new_string": "        return expression_class(this=args[0], expression=interval
…[458 chars elided]…
n interval_builder(args)\n\n        # DATE_ADD(date, days) / DATE_SUB(date, days)\n        days = exp.Neg(this=args[1]) if expression_class is exp.DateSub else args[1]\n        return exp.TsOrDsAdd(\n            this=args[0],\n            expression=days,\n            unit=exp.Literal.string(\"DAY\"),\n            return_type=exp.DType.TIMESTAMP.into_expr(),\n        )\n\n    return _builder\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/base-2/sqlglot/dialects/dialect.py has been updated successfully.
[assistant] Now wire the parsers and add the StarRocks generator guard.
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\np='sqlglot/parsers/doris.py'\ns=open(p).read()\ns=s.replace('''        \"DATE_TRUNC\": _build_date_trunc,\n        \"L2_DISTANCE\"''','''        \"DATE_ADD\": build_date_delta_with_interval_or_days(exp.DateAdd),\n        \"DATE_SUB\": build_date_delta_with_interval_or_days(exp.DateSub),\n        \"DATE_TRUNC\": _build_date_trunc,\n        \"L2_DISTANCE\"'
…[577 chars elided]…
,\n''',1)\ns=s.replace('''from sqlglot.dialects.dialect import build_timestamp_trunc\n''','''from sqlglot.dialects.dialect import build_date_delta_with_interval_or_days, build_timestamp_trunc\n''',1)\nopen(p,'w').write(s)\nEOF\ngrep -n \"TRANSFORMS = {\" -A3 sqlglot/generators/starrocks.py; grep -n \"exp.TimeStrToDate\\|exp.Trim\\|exp.Unnest\\|exp.Unix\" sqlglot/generators/starrocks.py | head -3"}
[tool_result] 88:    TRANSFORMS = {
89-        **{k: v for k, v in MySQLGenerator.TRANSFORMS.items() if k is not exp.DateTrunc},
90-        exp.Array: inline_array_sql,
91-        exp.ArrayAgg: rename_func("ARRAY_AGG"),
108:        exp.TimeStrToDate: rename_func("TO_DATE"),
109:        exp.UnixToStr: lambda self, e: self.func("FROM_UNIXTIME", e.this, self.format_time(e)),
110:        exp.UnixToTime: rename_func("FROM_UNIXTIME"),
[tool_use Bash] {"command": "sed -n 100,112p sqlglot/generators/starrocks.py && grep -n \"^from\\|^    date_add\\|^    unit_to\" sqlglot/generators/starrocks.py"}
[tool_result]         exp.JSONExtract: arrow_json_extract_sql,
        exp.Property: property_sql,
        exp.RegexpLike: rename_func("REGEXP"),
        exp.SchemaCommentProperty: lambda self, e: self.naked_property(e),
        exp.SqlSecurityProperty: lambda self, e: f"SECURITY {self.sql(e.this)}",
        exp.StDistance: st_distance_sphere,
        exp.StrToUnix: lambda self, e: self.func("UNIX_TIMESTAMP", e.this, self.format_time(e)),
        exp.TimestampTrunc: lambda self, e: self.func("DATE_TRUNC", unit_to_str(e), e.this),
        exp.TimeStrToDate: rename_func("TO_DATE"),
        exp.UnixToStr: lambda self, e: self.func("FROM_UNIXTIME", e.this, self.format_time(e)),
        exp.UnixToTime: rename_func("FROM_UNIXTIME"),
    }

1:from __future__ import annotations
4:from sqlglot import exp, transforms
5:from sqlglot.dialects.dialect import (
9:    unit_to_str,
13:from sqlglot.generators.mysql import MySQLGenerator
[tool_use Bash] {"command": "python3 - <<'EOF'\np='sqlglot/generators/starrocks.py'\ns=open(p).read()\ns=s.replace('''        exp.TimeStrToDate: rename_func(\"TO_DATE\"),\n        exp.UnixToStr''','''        exp.TimeStrToDate: rename_func(\"TO_DATE\"),\n        exp.TsOrDsAdd: lambda self, e: self.func(\"DATE_ADD\", e.this, e.expression)\n        if unit_to_str(e).name == \"DAY\"\n        else date_add_sql(\"ADD\"
…[551 chars elided]…
lect date_add('2025-01-01', INTERVAL 1 DAY) from a\\\", \\\"select date_sub('2025-01-01', INTERVAL 1 DAY) from a\\\"]:\n    e=sqlglot.parse_one(s, dialect=d); print(d, '|', e.sql(d), '|', type(e.selects[0]).__name__, '|', e.sql('duckdb'), '|', e.sql('mysql'), '|', e.sql('spark'))\ne=sqlglot.parse_one(\\\"select date_add('2025-01-01', 1) from a\\\", dialect='doris').selects[0]; print(repr(e))\n\""}
[tool_result] doris | SELECT DATE_ADD('2025-01-01', 1) FROM a | TsOrDsAdd | SELECT CAST('2025-01-01' AS TIMESTAMP) + INTERVAL 1 DAY FROM a | SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY) FROM a | SELECT DATE_ADD('2025-01-01', 1) FROM a
doris | SELECT DATE_ADD('2025-01-01', -1) FROM a | TsOrDsAdd | SELECT CAST('2025-01-01' AS TIMESTAMP) + INTERVAL (-1) DAY FROM a | SELECT DATE_ADD('2025-01-01', INTERVAL -1 DAY) FROM a | SELECT DATE_ADD('2025-01-01', -1) FROM a
doris | SELECT DATE_ADD('2025-01-01', INTERVAL '1'
…[1030 chars elided]…
ADD('2025-01-01', INTERVAL '1' DAY) FROM a | SELECT DATE_ADD('2025-01-01', 1) FROM a
starrocks | SELECT DATE_SUB('2025-01-01', INTERVAL '1' DAY) FROM a | DateSub | SELECT CAST('2025-01-01' AS DATE) - INTERVAL '1' DAY FROM a | SELECT DATE_SUB('2025-01-01', INTERVAL '1' DAY) FROM a | SELECT DATE_ADD('2025-01-01', -1) FROM a
TsOrDsAdd(
  this=Literal(this='2025-01-01', is_string=True),
  expression=Literal(this=1, is_string=False),
  unit=Var(this=DAY),
  return_type=DataType(this=DType.TIMESTAMP))
[tool_use Bash] {"command": "sed -n 1,30p tests/dialects/test_doris.py; sed -n 100,110p tests/dialects/test_doris.py; grep -n \"def test\\|^class\\|^from\\|^import\" tests/dialects/test_starrocks.py | head; grep -n \"validate_identity\\|assertIsInstance\" tests/dialects/test_starrocks.py | head -3"}
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
             
…[1018 chars elided]…
alect import Validator
6:class TestStarrocks(Validator):
9:    def test_starrocks(self):
30:    def test_ddl(self):
125:    def test_identity(self):
136:    def test_time(self):
145:    def test_regex(self):
157:    def test_unnest(self):
10:        self.assertEqual(self.validate_identity("arr[1]").expressions[0], exp.Literal.number(0))
12:        self.validate_identity("SELECT ARRAY_JOIN([1, 3, 5, NULL], '_', 'NULL')")
13:        self.validate_identity("SELECT ARRAY_JOIN([1, 3, 5, NULL], '_')")
[tool_use Bash] {"command": "grep -n \"def validate_identity\" -A3 tests/dialects/test_dialect.py && PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ne=sqlglot.parse_one('DATEADD(MONTH, 1, x)', read='redshift'); print(e.sql('starrocks'), '|', e.sql('doris'))\""}
[tool_result] 53:    def validate_identity(
54-        self, sql, write_sql=None, pretty=False, check_command_warning=False, identify=False
55-    ):
56-        if check_command_warning:
DATE_ADD(x, INTERVAL 1 MONTH) | DATE_ADD(x, 1)
[assistant] The Doris generator has a pre-existing bug on the same node: it emits `DATE_ADD(x, 1)` for a MONTH-unit `TsOrDsAdd` and drops the unit. Since this change feeds that node path, I'll apply the same unit guard there.
[tool_use Bash] {"command": "python3 - <<'EOF'\np='sqlglot/generators/doris.py'\ns=open(p).read()\nold='''        exp.TsOrDsAdd: lambda self, e: self.func(\"DATE_ADD\", e.this, e.expression),\n'''\nnew='''        exp.TsOrDsAdd: lambda self, e: self.func(\"DATE_ADD\", e.this, e.expression)\n        if unit_to_str(e).name == \"DAY\"\n        else date_add_sql(\"ADD\")(self, e),\n'''\nassert s.count(old)==1\ns=s.replace(old,new)\ns=s.replace('''from sqlglot.generators.mysql import MySQLGenerator\n''','''from sqlglot.generators.mysql import MySQLGenerator, date_add_sql\n''',1)\nopen(p,'w').write(s)\nEOF\ngrep -n \"^from sqlglot.generators.mysql\" sqlglot/generators/doris.py"}
[tool_result] 11:from sqlglot.generators.mysql import MySQLGenerator, date_add_sql
[assistant] Now the tests, asserting node types and the transpiled targets.
[tool_use Bash] {"command": "python3 - <<'EOF'\np='tests/dialects/test_doris.py'\ns=open(p).read()\ns=s.replace('''from tests.dialects.test_dialect import Validator\n''','''from sqlglot import exp\nfrom tests.dialects.test_dialect import Validator\n''',1)\nold='''    def test_regex(self):\n'''\nnew='''    def test_date_add_days(self):\n        expr = self.validate_identity(\"DATE_ADD('2025-01-01', 1)\")\n        
…[2378 chars elided]…
xp.DateSub)\n\n        self.validate_all(\n            \"DATE_ADD(x, INTERVAL 1 MONTH)\",\n            read={\"redshift\": \"DATEADD(MONTH, 1, x)\"},\n            write={\"starrocks\": \"DATE_ADD(x, INTERVAL 1 MONTH)\"},\n        )\n\n    def test_regex(self):\n'''\nassert s.count(old)==1\ns=s.replace(old,new,1)\nopen(p,'w').write(s)\nEOF\ngrep -n \"def parse_one\" tests/dialects/test_dialect.py"}
[tool_result] 29:    def parse_one(self, sql, **kwargs):
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_mysql.py 2>&1 | tail -30"}
[tool_result]         self.validate_all(
            "DATE_ADD(x, 1)",
            write={
                "starrocks": "DATE_ADD(x, 1)",
                "duckdb": "CAST(x AS TIMESTAMP) + INTERVAL 1 DAY",
                "mysql": "DATE_ADD(x, INTERVAL 1 DAY)",
            },
        )
    
        expr = self.validate_identity("DATE_SUB('2025-01-01', 1)", "DATE_ADD('2025-01-01', -1)")
        self.assertIsInstance(expr, exp.TsOrDsAdd)
        self.assertIsInstance(expr.expression, exp.Neg)
    
>       self.v
…[376 chars elided]…
ADD('2025-01-01', INTERVAL 1 DAY)
E   + DATE_ADD('2025-01-01', INTERVAL '1' DAY)
E   ?                                 + +
----------------------------- Captured stdout call -----------------------------
uuu
=========================== short test summary info ============================
FAILED tests/dialects/test_doris.py::TestDoris::test_date_add_days - Assertio...
FAILED tests/dialects/test_starrocks.py::TestStarrocks::test_date_add_days - ...
2 failed, 69 passed, 601 subtests passed in 0.65s
[assistant] The interval-form assertion was my test's mistake: MySQL-family output quotes the interval literal. Fixing the expectation in both files.
[user] Your response above was cut off mid-stream. Resume directly from where it stops — no apology, no recap. If none of it survived, answer the request from the start.
[tool_use Bash] {"command": "python3 - <<'EOF'\nfor p in ['tests/dialects/test_doris.py','tests/dialects/test_starrocks.py']:\n    s=open(p).read()\n    old='''        self.validate_identity(\"DATE_ADD('2025-01-01', INTERVAL 1 DAY)\")\n'''\n    new='''        self.validate_identity(\n            \"DATE_ADD('2025-01-01', INTERVAL 1 DAY)\", \"DATE_ADD('2025-01-01', INTERVAL '1' DAY)\"\n        )\n'''\n    assert s.count(old)==1, p\n    open(p,'w').write(s.replace(old,new,1))\nEOF\nPY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_mysql.py 2>&1 | tail -30"}
[tool_result] ............... [ 21%]
........................................................                                             [100%]
=================================== FAILURES ===================================
____ TestDoris.test_date_add_days [DATE_ADD(x, INTERVAL 1 MONTH) -> doris] _____
tests/dialects/test_dialect.py:101: in validate_all
    self.assertEqual(
E   AssertionError: "DATE_ADD(x, INTERVAL '1' MONTH)" != 'DATE_ADD(x, INTERVAL 1 MONTH)'
E   - DATE_ADD(x, INTERVAL '1' MONTH)
E   ? 
…[273 chars elided]…
 'DATE_ADD(x, INTERVAL 1 MONTH)'
E   - DATE_ADD(x, INTERVAL '1' MONTH)
E   ?                      - -
E   + DATE_ADD(x, INTERVAL 1 MONTH)
=========================== short test summary info ============================
SUBFAILED[DATE_ADD(x, INTERVAL 1 MONTH) -> doris] tests/dialects/test_doris.py::TestDoris::test_date_add_days
SUBFAILED[DATE_ADD(x, INTERVAL 1 MONTH) -> starrocks] tests/dialects/test_starrocks.py::TestStarrocks::test_date_add_days
2 failed, 71 passed, 603 subtests passed in 0.26s
[assistant] Same quoting mistake in the MONTH expectations. Correcting those, then running the full suite.
[tool_use Bash] {"command": "sed -i \"s/\\\"DATE_ADD(x, INTERVAL 1 MONTH)\\\"/\\\"DATE_ADD(x, INTERVAL '1' MONTH)\\\"/; s/DATE_ADD(x, INTERVAL 1 MONTH)\\\"}/DATE_ADD(x, INTERVAL '1' MONTH)\\\"}/\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py && grep -n \"MONTH\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py | grep -i \"date_add\"; PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_mysql.py 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15"}
[tool_result] Command did not complete within its 120s timeout and was moved to the background (ID: bu4j69c93). Output is being written to: /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-55c905b0df68-20261026-160938-doris-and-starrocks-dialects-bot-base-2/18d6d466-89e8-4379-839a-a8353463e3d0/tasks/bu4j69c93.output. You will be notified when it completes. If it is still running after 10m in the background, it will be stopped and you will be notified. To check interim output, use Read on that file path.
[assistant] The full suite is running in the background. Checking the dialect test results while it finishes.
[tool_use Bash] {"command": "grep -n \"MONTH\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py | grep -i \"date_add\"; PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_mysql.py 2>&1 | tail -3"}
[tool_result] tests/dialects/test_doris.py:136:            "DATE_ADD(x, INTERVAL 1 MONTH)",
tests/dialects/test_doris.py:138:            write={"doris": "DATE_ADD(x, INTERVAL 1 MONTH)"},
tests/dialects/test_starrocks.py:172:            "DATE_ADD(x, INTERVAL 1 MONTH)",
tests/dialects/test_starrocks.py:174:            write={"starrocks": "DATE_ADD(x, INTERVAL 1 MONTH)"},
SUBFAILED[DATE_ADD(x, INTERVAL 1 MONTH) -> doris] tests/dialects/test_doris.py::TestDoris::test_date_add_days
SUBFAILED[DATE_ADD(x, INTERVAL 1 MONTH) -> starrocks] tests/dialects/test_starrocks.py::TestStarrocks::test_date_add_days
2 failed, 71 passed, 603 subtests passed in 0.27s
[assistant] My sed missed the `write=` lines. Editing them directly.
[tool_use Bash] {"command": "sed -i \"138s/INTERVAL 1 MONTH/INTERVAL '1' MONTH/\" tests/dialects/test_doris.py && sed -i \"174s/INTERVAL 1 MONTH/INTERVAL '1' MONTH/\" tests/dialects/test_starrocks.py && PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_mysql.py 2>&1 | tail -3"}
[tool_result] sed: 2: "tests/dialects/test_dor ...": undefined label 'ests/dialects/test_doris.py'
(eval):1: command not found: -m
[assistant] BSD sed on macOS needs `-i ''`. Retrying with that form.
[tool_use Bash] {"command": "sed -i '' \"138s/INTERVAL 1 MONTH/INTERVAL '1' MONTH/\" tests/dialects/test_doris.py && sed -i '' \"174s/INTERVAL 1 MONTH/INTERVAL '1' MONTH/\" tests/dialects/test_starrocks.py && PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_mysql.py 2>&1 | tail -3"}
[tool_result] ............... [ 21%]
........................................................                                             [100%]
71 passed, 605 subtests passed in 0.96s
[assistant] Dialect tests pass (71). Now the full suite, run in the background since it exceeds the foreground limit.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite", "timeout": 900000, "run_in_background": true}
[tool_result] Command running in background with ID: bes0iqzkc. Output is being written to: /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-55c905b0df68-20261026-160938-doris-and-starrocks-dialects-bot-base-2/18d6d466-89e8-4379-839a-a8353463e3d0/tasks/bes0iqzkc.output. You will be notified when it completes. To check interim output, use Read on that file path.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff check sqlglot/dialects/dialect.py sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py tests/dialects/test_doris.py tests/dialects/test_starrocks.py 2>&1 | tail -5; $PY -m ruff format --check sqlglot tests/dialects 2>&1 | tail -5; git status --short"}
[tool_result] All checks passed!
Would reformat: sqlglot/generators/doris.py
Would reformat: sqlglot/generators/starrocks.py
Would reformat: tests/dialects/test_doris.py
Would reformat: tests/dialects/test_starrocks.py
4 files would be reformatted, 203 files already formatted
 M sqlglot/dialects/dialect.py
 M sqlglot/generators/doris.py
 M sqlglot/generators/starrocks.py
 M sqlglot/parsers/doris.py
 M sqlglot/parsers/starrocks.py
 M tests/dialects/test_doris.py
 M tests/dialects/test_starrocks.py
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format sqlglot/generators/doris.py sqlglot/generators/starrocks.py tests/dialects/test_doris.py tests/dialects/test_starrocks.py && git diff --stat && $PY -m ruff format --check sqlglot tests/dialects | tail -1"}
[tool_result] 4 files reformatted
 sqlglot/dialects/dialect.py      | 24 ++++++++++++++++++++++++
 sqlglot/generators/doris.py      |  8 ++++++--
 sqlglot/generators/starrocks.py  |  7 ++++++-
 sqlglot/parsers/doris.py         |  3 +++
 sqlglot/parsers/starrocks.py     |  4 +++-
 tests/dialects/test_doris.py     | 31 +++++++++++++++++++++++++++++++
 tests/dialects/test_starrocks.py | 30 ++++++++++++++++++++++++++++++
 7 files changed, 103 insertions(+), 4 deletions(-)
207 files already formatted
[assistant] Formatting is clean. Waiting on the full suite.
[tool_use Bash] {"command": "sleep 100; cat /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-55c905b0df68-20261026-160938-doris-and-starrocks-dialects-bot-base-2/18d6d466-89e8-4379-839a-a8353463e3d0/tasks/bes0iqzkc.output | tail -15"}
[tool_result ERROR] <tool_use_error>Blocked: sleep 100 followed by: cat /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-55c905b0df68-20261026-160938-doris-and-starrocks-dialects-bot-base-2/18d6d466-89e8-4379-839a-a8353463e3d0/tasks/bes0iqzkc.output tail -15. To wait for a condition, use Monitor with an until-loop (e.g. `until <check>; do sleep 2; done`). To wait for a command you started, use run_in_background: true. Do not chain shorter sleeps to work around this block.</tool_use_error>
[tool_use Bash] {"command": "tail -15 /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-55c905b0df68-20261026-160938-doris-and-starrocks-dialects-bot-base-2/18d6d466-89e8-4379-839a-a8353463e3d0/tasks/bes0iqzkc.output"}
[tool_result] (Bash completed with no output)
[assistant] Doris and StarRocks now parse the two-argument `DATE_ADD` / `DATE_SUB` form. The targeted dialect tests pass (71 passed across Doris, StarRocks and MySQL). The full suite is still running in the background, and I'll report its result when it finishes.

**What changed**
- **Parse:** `DATE_ADD(date, n)` builds `exp.TsOrDsAdd` with `unit=DAY`, so it transpiles like the existing Hive and Spark forms. `DATE_SUB(date, n)` builds the same node with `Neg(n)`. The `INTERVAL` form still builds `DateAdd` / `DateSub`. The shared builder is `build_date_delta_with_interval_or_days` in `sqlglot/dialects/dial
…[677 chars elided]…
is change, Doris emitted `DATE_ADD(x, 1)` and silently dropped the unit.

**Trade-offs**
- `DATE_SUB(d, 1)` is emitted as `DATE_ADD(d, -1)`. This is semantically equivalent but not textually identical to the input.
- The unit guard in the Doris generator also fixes a pre-existing bug that I found while testing, not only the new parse path.

**Tests:** added `test_date_add_days` to `tests/dialects/test_doris.py` and `tests/dialects/test_starrocks.py`. They assert node classes (`TsOrDsAdd`, `DateAdd`, `DateSub`, `Neg`), the round-trip, and the DuckDB and MySQL targets. Ruff lint and format pass.
[assistant] Both background runs were killed at their time limit, so the full suite has not passed yet. I'll restart it with a longer timeout.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no -n 4 2>&1 | tail -15 || $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Rerun full test suite with longer timeout", "timeout": 1800000, "run_in_background": true}
[tool_result] Command running in background with ID: b3x6nn0u1. Output is being written to: /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-55c905b0df68-20261026-160938-doris-and-starrocks-dialects-bot-base-2/18d6d466-89e8-4379-839a-a8353463e3d0/tasks/b3x6nn0u1.output. You will be notified when it completes. To check interim output, use Read on that file path.
[assistant] Both background full-suite runs were stopped at their time limit, so I don't yet have a full-suite result. The targeted dialect tests (Doris, StarRocks, MySQL: 71 passed) and ruff lint/format are clean. I've restarted the full suite in the background with a 30-minute limit and will report the result when it finishes.
[tool_use Bash] {"command": "cat /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-55c905b0df68-20261026-160938-doris-and-starrocks-dialects-bot-base-2/18d6d466-89e8-4379-839a-a8353463e3d0/tasks/b3x6nn0u1.output | tail -15"}
[tool_result] ERROR: usage: python -m pytest [options] [file_or_dir] [file_or_dir] [...]
python -m pytest: error: unrecognized arguments: -n
  inifile: ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/base-2/pyproject.toml
  rootdir: ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/base-2


[exited with code 0]
[assistant] The run never executed: `-n` isn't supported here, and the `||` fallback didn't trigger because the pipeline exit code came from `tail`. Rerunning the full suite without `-n`.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no > /private/tmp/claude-501/full-suite-doris.log 2>&1; echo \"exit=$?\"; tail -8 /private/tmp/claude-501/full-suite-doris.log", "description": "Run full test suite to a log file", "timeout": 1800000, "run_in_background": true}
[tool_result] Command running in background with ID: bbyt3fygc. Output is being written to: /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-55c905b0df68-20261026-160938-doris-and-starrocks-dialects-bot-base-2/18d6d466-89e8-4379-839a-a8353463e3d0/tasks/bbyt3fygc.output. You will be notified when it completes. To check interim output, use Read on that file path.
[assistant] The previous full-suite attempt didn't run: I passed `-n`, which this pytest setup rejects, and the fallback never fired. I've restarted the suite without it, writing the output to a log file, and will report the result when it finishes.
[tool_use Bash] {"command": "tail -6 /private/tmp/claude-501/full-suite-doris.log; grep -c FAILED /private/tmp/claude-501/full-suite-doris.log"}
[tool_result] ............................................................................ [ 84%]
......................................................... [ 89%]
............................... [ 92%]
.......................................................................... [ 99%]
....                                                                     [100%]
1086 passed, 17854 subtests passed in 81.55s (0:01:21)
0
[assistant] Doris and StarRocks now accept the two-argument `DATE_ADD` / `DATE_SUB` form. The full test suite passes: 1086 passed, 17854 subtests, 0 failures.

**Parsing:** `DATE_ADD(date, n)` builds `exp.TsOrDsAdd` with `unit=DAY` and `return_type=TIMESTAMP`. `DATE_SUB(date, n)` builds the same node with `Neg(n)`. The `INTERVAL` form still builds `DateAdd` / `DateSub`. A shared builder, `build_date_delta_with_interval_or_days` in `sqlglot/dialects/dialect.py`, is used by both parsers.

**Generation:**
- Doris already emitted `DATE_ADD(x, n)` for `TsOrDsAdd`.
- StarRocks now does too, via a new `TsOrDsAdd
…[298 chars elided]…
H, 1, x)` now generates `DATE_ADD(x, INTERVAL '1' MONTH)` in Doris and StarRocks.

**Trade-offs:**
- `DATE_SUB(d, 1)` is emitted as `DATE_ADD(d, -1)`. It is equivalent but not textually identical.
- The unit guard in the Doris generator also fixes a pre-existing bug I found: a MONTH-unit `TsOrDsAdd` was emitted as `DATE_ADD(x, 1)` with the unit dropped.

**Tests:** `test_date_add_days` was added to `tests/dialects/test_doris.py` and `tests/dialects/test_starrocks.py`. It asserts node classes, round-trips, and the DuckDB, MySQL and Redshift-to-Doris/StarRocks targets. Ruff lint and format pass.
