# trajectory inv-2

final message:
Both Doris and StarRocks now parse and generate the two-argument `DATE_ADD` / `DATE_SUB` form. The full suite passes after my last edit: `SUMMARY: 1086 passed, 17855 subtests passed in 121.05s`, `EXIT: 0`.

**What changed**
- `sqlglot/dialects/dialect.py`: new `build_date_delta_with_days_or_interval`. An INTERVAL second argument keeps the existing `DateAdd`/`DateSub` path. Any other second argument becomes `exp.TsOrDsAdd(unit=DAY)`. `DATE_SUB` negates the days.
- `sqlglot/parsers/doris.py` and `sqlglot/parsers/starrocks.py`: `DATE_ADD` and `DATE_SUB` use that builder.
- `sqlglot/generators/starrocks.py`: `TsOrDsAdd` emits `DATE_ADD(x, n)` for DAY or unitless. Other units fall back to the INTERVAL form. Doris already emitted the two-arg form for `TsOrDsAdd`.
- Tests added to `tests/dialects/test_doris.py` and `tests/dialects/test_starrocks.py`. They assert the node class, the `DATE_SUB` rewrite, and cross-dialect output.

**Node types and result types**
- `DATE_ADD(x, 1)` parses to `exp.TsOrDsAdd`, the same node Hive and Spark use for this form. Its result type is DATE, the same as the Hive and Spark source.
- `DATE_ADD(x, INTERVAL 1 DAY)` still parses to `exp.DateAdd`, so existing behaviour is unchanged.
- Cross-dialect output for `DATE_ADD(x, 1)`: DuckDB `CAST(x AS DATE) + INTERVAL 1 DAY`, Hive and Spark `DATE_ADD(x, 1)`, MySQL `DATE_ADD(x, INTERVAL 1 DAY)`.

**Things you should know**
- **`DATE_SUB` does not round-trip.** `DATE_SUB(x, 1)` is parsed as `TsOrDsAdd` with `-1` and emitted as `DATE_ADD(x, -1)`. The arithmetic is identical, but the text changes. Keeping `DATE_SUB` verbatim would need a new flag on the node, which I did not add. This follows the Hive precedent.
- **Behaviour change for StarRocks output.** Other dialects' day-unit `TsOrDsAdd` (for example Hive `DATE_ADD(x, 1)`) now transpile to two-arg `DATE_ADD(x, 1)` in StarRocks. They previously produced `DATE_ADD(x, INTERVAL 1 DAY)`. Both are valid for the same date arithmetic, and the suite passes.
- **Pre-existing Doris bug, not fixed.** Doris's `TsOrDsAdd` transform ignores the unit. `dateadd(month, 1, x)` from Redshift becomes `DATE_ADD(x, 1)` in Doris, which adds one day. The StarRocks transform guards against this; Doris would need the same guard. I left it alone to keep the change scoped.

Nothing is committed. The changes are in the working tree.

## events
[tool_use Skill] {"skill": "sqlglot-dialect-functions"}
[tool_result] Launching skill: sqlglot-dialect-functions
[user] Base directory for this skill: ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-2/.claude/skills/sqlglot-dialect-functions

# Dialect functions and parse fixes in sqlglot

## The invariant: parse into the canonical expression, not a generic node
sqlglot is AST-first. If a function's meaning already has an expression class, the function must
parse into THAT class so it can transpile. The generic nodes `exp.Anonymous`, `exp.AnonymousAggFunc`,
`exp.ParameterizedAgg`, `exp.CombinedAggFunc` and `exp.CombinedParameterizedAgg` (all in
`sqlglot/
…[6077 chars elided]…
late already in the file:
  - Parser: `FUNCTION_PARSERS["QUANTILE"] = lambda self: self._parse_quantile()`.
    `_parse_quantile` parses the first group, then `self._parse_func_params()`, which matches
    `)(` and parses the second group. With no second group it builds the non-parametric form.
  - Generator: `exp.Quantile: _quantile_sql` in `TRANSFORMS` emits
    `self.func("quantile", <param>) + f"({<arg>})"`.
  - `"quantile"` also stays in `AGG_FUNCTIONS`. The suffixed names (`quantileIf`, …) don't match
    the exact `FUNCTION_PARSERS` key, so they still parse through the combinator path.

[tool_use Bash] {"command": "grep -rn \"DATE_ADD\\|DateAdd\\|DATE_SUB\\|DateSub\" sqlglot/dialects/doris.py sqlglot/dialects/starrocks.py sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py 2>&1; ls .lithify/harness 2>&1; cat .lithify/memory.md 2>/dev/null | head -30", "description": "Search Doris/StarRocks date_add handling"}
[tool_result] sqlglot/generators/doris.py:75:        exp.TsOrDsAdd: lambda self, e: self.func("DATE_ADD", e.this, e.expression),
guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
[assistant] The dialect-functions skill is loaded. Next I'll check the project's Python path and reproduce the failure.
[tool_use Bash] {"command": "cat .lithify/memory.md; echo ---; ls .lithify/harness/skills/sqlglot-dialect-functions/scripts/ 2>&1; echo ---; grep -rn \"DATE_ADD\\|DATE_SUB\\|DateAdd\\|DateSub\\|TsOrDsAdd\\|DATE_ADD\\|date_add\" sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py sqlglot/dialects/doris.py sqlglot/dialects/starrocks.py sqlglot/dialects/mysql.py sqlglot/parsers/mysql.py sqlglot/generators/mysql.py 2>&1", "description": "Read project memory and find date_add handling"}
[tool_result] cat: .lithify/memory.md: No such file or directory
---
ast_check.py
---
sqlglot/generators/doris.py:75:        exp.TsOrDsAdd: lambda self, e: self.func("DATE_ADD", e.this, e.expression),
sqlglot/generators/doris.py:184:        "date_add",
sqlglot/parsers/mysql.py:114:        "DATE_ADD": build_date_delta_with_interval(exp.DateAdd),
sqlglot/parsers/mysql.py:119:        "DATE_SUB": build_date_delta_with_interval(exp.DateSub),
sqlglot/generators/mysql.py:10:    date_add_interval_sql,
sqlglot/generat
…[117 chars elided]…
add_sql("ADD")),
sqlglot/generators/mysql.py:153:        exp.DateSub: _remove_ts_or_ds_to_date(date_add_sql("SUB")),
sqlglot/generators/mysql.py:192:        exp.TimestampAdd: date_add_interval_sql("DATE", "ADD"),
sqlglot/generators/mysql.py:196:        exp.TimestampSub: date_add_interval_sql("DATE", "SUB"),
sqlglot/generators/mysql.py:209:        exp.TsOrDsAdd: date_add_sql("ADD"),
sqlglot/generators/mysql.py:742:        dateadd = build_date_delta_with_interval(exp.DateAdd)([start_ts, interval])
[tool_use Bash] {"command": "ls -la .lithify/ 2>&1; cat .lithify/harness/memory.md 2>&1 | head -20; echo ---; sed -n 1,80p sqlglot/parsers/mysql.py | head -5; echo ---; grep -n \"def build_date_delta_with_interval\" -A 25 sqlglot/dialects/dialect.py; echo ---; sed -n 60,90p sqlglot/generators/doris.py; echo ---; sed -n 175,195p sqlglot/generators/doris.py; echo ---; cat sqlglot/dialects/starrocks.py | head -60; ls sqlglot/parsers/ | grep -i \"doris\\|starrocks\"; ls sqlglot/generators | grep -i \"doris\\|starrocks\"", "description": "Inspect lithify memory and date-delta builders"}
[tool_result] total 8
drwxr-xr-x@  5 user  staff   160 Oct 26 18:14 .
drwxr-xr-x@ 30 user  staff   960 Oct 26 18:14 ..
drwxr-xr-x@  8 user  staff   256 Oct 26 18:13 harness
drwxr-xr-x@  3 user  staff    96 Oct 26 18:14 library
-rw-r--r--@  1 user  staff  1734 Oct 26 18:14 state.json
- The project's checks run with `<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovid
…[3741 chars elided]…
ySQL
from sqlglot.generators.starrocks import StarRocksGenerator
from sqlglot.parsers.starrocks import StarRocksParser
from sqlglot.tokens import TokenType


class StarRocks(MySQL):
    STRICT_JSON_PATH_SYNTAX = False
    INDEX_OFFSET = 1

    class Tokenizer(MySQL.Tokenizer):
        KEYWORDS = {
            **MySQL.Tokenizer.KEYWORDS,
            "LARGEINT": TokenType.INT128,
        }

    Parser = StarRocksParser

    Generator = StarRocksGenerator
doris.py
starrocks.py
doris.py
starrocks.py
[assistant] The MySQL parser's `DATE_ADD` builder rejects a non-INTERVAL second argument, and Doris and StarRocks inherit it. Next I'll check the existing expression classes and dialect tests.
[tool_use Bash] {"command": "cat sqlglot/parsers/doris.py | head -80; echo ---SR; cat sqlglot/parsers/starrocks.py; echo ---GEN-SR; cat sqlglot/generators/starrocks.py; echo ---; grep -n \"class TsOrDsAdd\" -A 12 sqlglot/expressions/*.py; echo ---; grep -rn \"date_add\\|DATE_ADD\\|DATE_SUB\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_mysql.py | head -40", "description": "Read Doris/StarRocks parsers and related tests"}
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
    
…[19801 chars elided]…
AS __timestamp FROM tableT",
tests/dialects/test_mysql.py:1460:                        f"DATE_ADD('0000-01-01 00:00:00', INTERVAL (TIMESTAMPDIFF({unit}, '0000-01-01 00:00:00', {cast})) {unit})",
tests/dialects/test_mysql.py:1465:                            "mysql": f"DATE_ADD('0000-01-01 00:00:00', INTERVAL (TIMESTAMPDIFF({unit}, '0000-01-01 00:00:00', {cast})) {unit})",
tests/dialects/test_mysql.py:1618:                self.validate_identity(f"DATE_ADD(base_date, INTERVAL day_interval {unit})")
[assistant] Doris and StarRocks both inherit MySQL's `DATE_ADD`/`DATE_SUB` builders, which require an INTERVAL. Before choosing a canonical node, I'll check how Hive and Spark, which have the same days-form, parse it.
[tool_use Bash] {"command": "grep -rn \"\\\"DATE_ADD\\\"\\|\\\"DATE_SUB\\\"\\|\\\"DAYS_ADD\\\"\\|\\\"DATE_DIFF\\\"\\|TsOrDsAdd\" sqlglot/parsers/*.py sqlglot/dialects/dialect.py sqlglot/parser.py | head -40; echo ---; grep -rn \"TsOrDsAdd\" sqlglot/generators/*.py sqlglot/dialects/*.py | head -30", "description": "Find how Hive/Spark handle days-form DATE_ADD"}
[tool_result] sqlglot/parsers/bigquery.py:189:        "DATE_ADD": build_date_delta_with_interval(exp.DateAdd),
sqlglot/parsers/bigquery.py:190:        "DATE_DIFF": build_date_diff,
sqlglot/parsers/bigquery.py:191:        "DATE_SUB": build_date_delta_with_interval(exp.DateSub),
sqlglot/parsers/clickhouse.py:271:        "DATE_ADD": build_date_delta(exp.DateAdd, default_unit=None),
sqlglot/parsers/clickhouse.py:273:        "DATE_DIFF": build_date_delta(exp.DateDiff, default_unit=None, supports_timezone=True),
sq
…[4463 chars elided]…
t.Union[exp.DateAdd, exp.TsOrDsAdd, exp.DateSub]
sqlglot/dialects/dialect.py:56:    exp.TsOrDsAdd,
sqlglot/dialects/dialect.py:58:DATETIME_ADD = (exp.DateAdd, exp.TimeAdd, exp.DatetimeAdd, exp.TsOrDsAdd, exp.TimestampAdd)
sqlglot/dialects/dialect.py:1921:def ts_or_ds_add_cast(expression: exp.TsOrDsAdd) -> exp.TsOrDsAdd:
sqlglot/dialects/dialect.py:1936:        if cast and isinstance(expression, exp.TsOrDsAdd):
sqlglot/dialects/dialect.py:1959:            if isinstance(expression, exp.TsOrDsAdd):
[tool_use Bash] {"command": "sed -n 28,80p sqlglot/parsers/hive.py; echo ---; sed -n 40,60p sqlglot/parsers/spark.py; echo ---; sed -n 70,85p sqlglot/generators/hive.py; echo ---; grep -n \"def _add_date_sql\" -A 12 sqlglot/generators/hive.py; echo; grep -n \"DATE_SUB\\|DATE_ADD\\|date_sub\\|date_add\" tests/dialects/test_hive.py | head; echo ---; ls tests/dialects | grep -i \"doris\\|starrocks\"", "description": "Read Hive/Spark days-form date add builders"}
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
    
…[3621 chars elided]…
ESTAMP) AS DATE))",
450:                "spark": "DATE_ADD('2020-01-01', 1)",
455:            "DATE_SUB('2020-01-01', 1)",
458:                "bigquery": "DATE_ADD(CAST(CAST('2020-01-01' AS DATETIME) AS DATE), INTERVAL (1 * -1) DAY)",
460:                "hive": "DATE_ADD('2020-01-01', 1 * -1)",
461:                "presto": "DATE_ADD('DAY', 1 * -1, CAST(CAST('2020-01-01' AS TIMESTAMP) AS DATE))",
464:                "spark": "DATE_ADD('2020-01-01', 1 * -1)",
---
test_doris.py
test_starrocks.py
[assistant] Hive and Spark already parse the days-form to `exp.TsOrDsAdd` with `unit=DAY`, and Doris's generator already emits `TsOrDsAdd` as two-arg `DATE_ADD`. Next I'll reproduce with the project's Python and check the MySQL dict placement and existing Doris/StarRocks tests.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls -la $PY 2>&1; $PY -c \"import sqlglot,sys;print(sqlglot.__file__)\" 2>&1; echo ---; sed -n 100,125p sqlglot/parsers/mysql.py; echo ---; grep -n \"DATE_ADD\\|date_add\\|DATE_SUB\\|date_sub\\|TsOrDs\\|INTERVAL\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py | head -60", "description": "Check project python and existing Doris/StarRocks date tests"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 26 08:58 <work>/env-sqlglot/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-2/sqlglot/__init__.py
---
    }

    FUNCTIONS = {
        **parser.Parser.FUNCTIONS,
        "BIT_AND": exp
…[2174 chars elided]…
INTERVAL 5 MINUTE)",
tests/dialects/test_starrocks.py:306:            "CREATE TABLE test_table (col1 DATE) PARTITION BY RANGE (col1) (START ('2019-01-01') END ('2021-01-01') EVERY (INTERVAL 1 YEAR), START ('2021-01-01') END ('2021-05-01') EVERY (INTERVAL 1 MONTH), START ('2021-05-01') END ('2021-05-04') EVERY (INTERVAL 1 DAY))"
tests/dialects/test_doris.py:143:            "CREATE TABLE test_table (c1 INT, c2 DATE) PARTITION BY RANGE (`c2`) (FROM ('2000-11-14') TO ('2021-11-14') INTERVAL 2 YEAR)"
[assistant] The project Python resolves to this worktree's sqlglot. Next I'll reproduce the failure and look at the AST the script reports.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sqlglot\nfor d in ['doris','starrocks']:\n    for s in [\\\"select date_add('2025-01-01', 1) from a\\\", \\\"select date_sub('2025-01-01', 1) from a\\\", \\\"select date_add('2025-01-01', interval 1 day) from a
…[149 chars elided]…
>&1; echo ---; $PY .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py --read doris --write duckdb,mysql,starrocks --repr \"select date_add('2025-01-01', 1) from a\" 2>&1 | head -40; echo; $PY -c \"print(1)\"; $PY .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py --help 2>&1 | head -20", "description": "Reproduce the parse failure and inspect via ast_check"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
---
== select date_add('2025-01-01', 1) from a
  PARSE ERROR: INTERVAL expression expected but got '1'

1
usage: ast_check.py [-h] --read READ [--write WRITE] [--repr] sql [sql ...]

positional arguments:
  sql            one or more SQL strings

options:
  -h, --help     show this help message and exit
  --read READ    source dialect, e.g. clickhouse
  --write WRITE  comma-separated target dialects
  --repr         print full AST repr
[assistant] The `-I` flag dropped the worktree from the import path, so I'll rerun the checks without it.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor d in ['doris','starrocks']:\n    for s in [\\\"select date_add('2025-01-01', interval 1 day) from a\\\", \\\"select date_sub('2025-01-01', interval 1 day) from a\\\"]:\n        e = sqlglot.parse_one(s, read=d); print(d, type(e.selects[0]).__name__, e.sql(d))\nprint(sqlglot.transpile(\\\"select date_add(x, 1)\\\", read='hive', write='doris'))\nprint(sqlglot.transpile(\\\"select date_add(x, 1)\\\", read='hive', write='starrocks'))\n\" 2>&1; cat tests/dialects/test_doris.py | head -30", "description": "Check interval-form parses and TsOrDsAdd emission"}
[tool_result] doris DateAdd SELECT DATE_ADD('2025-01-01', INTERVAL '1' DAY) FROM a
doris DateSub SELECT DATE_SUB('2025-01-01', INTERVAL '1' DAY) FROM a
starrocks DateAdd SELECT DATE_ADD('2025-01-01', INTERVAL '1' DAY) FROM a
starrocks DateSub SELECT DATE_SUB('2025-01-01', INTERVAL '1' DAY) FROM a
['SELECT DATE_ADD(x, 1)']
['SELECT DATE_ADD(x, INTERVAL 1 DAY)']
from tests.dialects.test_dialect import Validator


class TestDoris(Validator):
    dialect = "doris"

    def test_doris(self):
        self.validate_
…[296 chars elided]…
, b), MIN_BY(c, d)",
            read={
                "clickhouse": "SELECT argMax(a, b), argMin(c, d)",
            },
        )
        self.validate_all(
            "SELECT ARRAY_SUM(x -> x * x, ARRAY(2, 3))",
            read={
                "clickhouse": "SELECT arraySum(x -> x*x, [2, 3])",
            },
            write={
                "clickhouse": "SELECT arraySum(x -> x * x, [2, 3])",
                "doris": "SELECT ARRAY_SUM(x -> x * x, ARRAY(2, 3))",
            },
        )
[assistant] The failure reproduces: Doris and StarRocks both reject the days-form `DATE_ADD`, and `DATE_SUB` has the same gap. Before editing I'll read the MySQL `date_add_sql` helper that the StarRocks fallback will call, and the tail of the two test files.
[tool_use Bash] {"command": "sed -n 74,95p sqlglot/generators/mysql.py; echo ---; grep -n \"^class\\|^from\\|^import\" sqlglot/generators/doris.py sqlglot/dialects/dialect.py | head -30; echo ---; grep -n \"def build_date_delta_with_interval\" -B3 sqlglot/dialects/dialect.py; echo ---; tail -20 tests/dialects/test_starrocks.py; echo ---; tail -12 tests/dialects/test_doris.py", "description": "Read MySQL date_add_sql and test file endings"}
[tool_result] def date_add_sql(
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
    time_format = expression.args.get("format")
    return _
…[3926 chars elided]…
VIEW mv REFRESH COMPLETE ON MANUAL AS SELECT 1")
        self.validate_identity("CREATE MATERIALIZED VIEW mv REFRESH AUTO ON COMMIT AS SELECT 1")
        self.validate_identity(
            "CREATE MATERIALIZED VIEW mv REFRESH AUTO ON SCHEDULE EVERY 5 MINUTE STARTS '2025-01-01 00:00:00' AS SELECT 1"
        )

        # Combined BUILD and REFRESH
        self.validate_identity(
            "CREATE MATERIALIZED VIEW mv BUILD DEFERRED REFRESH AUTO ON SCHEDULE EVERY 10 MINUTE AS SELECT 1"
        )
[assistant] I have what I need. The plan:

- **Parse:** in `dialect.py`, add a builder next to `build_date_delta_with_interval`. A second argument that is not an INTERVAL becomes `exp.TsOrDsAdd` with `unit=DAY`, the same node Hive and Spark use. `DATE_SUB` negates the days.
- **Wire:** Doris and StarRocks parsers use the builder for `DATE_ADD`/`DATE_SUB`.
- **Generate:** the StarRocks generator emits two-arg `DATE_ADD` for day units. It falls back to the INTERVAL form for other units, so nothing that currently transpiles correctly changes. Doris already emits two-arg for `TsOrDsAdd`.

Starting with the shared builder:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-2/sqlglot/dialects/dialect.py", "old_string": "        return expression_class(this=args[0], expression=interval.this, unit=unit_to_str(interval))\n\n    return _builder\n\n\ndef date_trunc_to_time(", "new_string": "        return expression_class(this=args
…[299 chars elided]…
val(expression_class)\n\n    def _builder(args: BuilderArgs) -> E | exp.TsOrDsAdd | None:\n        if len(args) < 2 or isinstance(args[1], exp.Interval):\n            return interval_builder(args)\n\n        days = -args[1] if negate_days else args[1]\n        return exp.TsOrDsAdd(this=args[0], expression=days, unit=exp.Literal.string(\"DAY\"))\n\n    return _builder\n\n\ndef date_trunc_to_time("}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-2/sqlglot/dialects/dialect.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"from sqlglot.dialects.dialect import\" -A 3 sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py sqlglot/parsers/mysql.py | head; grep -n \"build_date_delta_with_interval\" sqlglot/parsers/mysql.py | head -3; sed -n 1,30p sqlglot/generators/doris.py | grep -n \"import\\|    \" | head -20", "description": "Check existing dialect imports in parsers"}
[tool_result] sqlglot/parsers/starrocks.py:5:from sqlglot.dialects.dialect import build_timestamp_trunc
sqlglot/parsers/starrocks.py-6-from sqlglot.helper import seq_get
sqlglot/parsers/starrocks.py-7-from sqlglot.parsers.mysql import MySQLParser
sqlglot/parsers/starrocks.py-8-
sqlglot/parsers/mysql.py:7:from sqlglot.dialects.dialect import (
sqlglot/parsers/mysql.py-8-    Dialect,
sqlglot/parsers/mysql.py-9-    build_date_delta,
sqlglot/parsers/mysql.py-10-    build_date_delta_with_interval,
10:    build_dat
…[386 chars elided]…
glot.generators.mysql import MySQLGenerator
15:    return self.func(
16:        "LAG" if isinstance(expression, exp.Lag) else "LEAD",
17:        expression.this,
18:        expression.args.get("offset") or exp.Literal.number(1),
19:        expression.args.get("default") or exp.null(),
20:    )
24:    LAST_DAY_SUPPORTS_DATE_PART = False
25:    VARCHAR_REQUIRES_SIZE = False
26:    WITH_PROPERTIES_PREFIX = "PROPERTIES"
27:    RENAME_TABLE_WITH_DB = False
28:    UPDATE_STATEMENT_SUPPORTS_FROM = True
[assistant] Now I'll wire the builder into the Doris and StarRocks parsers.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-2/sqlglot/parsers/doris.py", "old_string": "from sqlglot import exp\nfrom sqlglot.helper import seq_get\nfrom sqlglot.parsers.mysql import MySQLParser", "new_string": "from sqlglot import exp\nfrom sqlglot.dialects.dialect import build_date_delta_with_days_or_interval\nfrom sqlglot.helper import seq_get\nfrom sqlglot.parsers.mysql import MySQLParser"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-2/sqlglot/parsers/doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-2/sqlglot/parsers/doris.py", "old_string": "        \"COLLECT_SET\": exp.ArrayUniqueAgg.from_arg_list,\n        \"DATE_TRUNC\": _build_date_trunc,", "new_string": "        \"COLLECT_SET\": exp.ArrayUniqueAgg.from_arg_list,\n        \"DATE_ADD\": build_date_delta_with_days_or_interval(exp.DateAdd),\n        \"DATE_SUB\": build_date_delta_with_days_or_interval(exp.DateSub, negate_days=True),\n        \"DATE_TRUNC\": _build_date_trunc,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-2/sqlglot/parsers/doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-2/sqlglot/parsers/starrocks.py", "old_string": "from sqlglot.dialects.dialect import build_timestamp_trunc\nfrom sqlglot.helper import seq_get\nfrom sqlglot.parsers.mysql import MySQLParser\n\n\nclass StarRocksParser(MySQLParser):\n    FUNCTIONS = {\n      
…[203 chars elided]…
\n)\nfrom sqlglot.helper import seq_get\nfrom sqlglot.parsers.mysql import MySQLParser\n\n\nclass StarRocksParser(MySQLParser):\n    FUNCTIONS = {\n        **MySQLParser.FUNCTIONS,\n        \"DATE_ADD\": build_date_delta_with_days_or_interval(exp.DateAdd),\n        \"DATE_SUB\": build_date_delta_with_days_or_interval(exp.DateSub, negate_days=True),\n        \"DATE_TRUNC\": build_timestamp_trunc,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-2/sqlglot/parsers/starrocks.py has been updated successfully.
[assistant] Next is the StarRocks generator. It needs a `TsOrDsAdd` transform, because MySQL's `TRANSFORMS` entry would otherwise win over an auto-discovered method.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-2/sqlglot/generators/starrocks.py", "old_string": "from sqlglot.generators.mysql import MySQLGenerator\n\n\ndef _eliminate_between_in_delete(", "new_string": "from sqlglot.generators.mysql import MySQLGenerator, date_add_sql\n\n\ndef _eliminate_between_in_delete("}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-2/sqlglot/generators/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-2/sqlglot/generators/starrocks.py", "old_string": "# https://docs.starrocks.io/docs/sql-reference/sql-functions/spatial-functions/st_distance_sphere/", "new_string": "def _ts_or_ds_add_sql(self: StarRocksGenerator, expression: exp.TsOrDsAdd) -> str:\n    if expression.text(\"unit\").upper() in (\"\", \"DAY\"):\n        return self.func(\"DATE_ADD\", expression.this, expression.expression)\n    return date_add_sql(\"ADD\")(self, expression)\n\n\n# https://docs.starrocks.io/docs/sql-reference/sql-functions/spatial-functions/st_distance_sphere/"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-2/sqlglot/generators/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-2/sqlglot/generators/starrocks.py", "old_string": "        exp.TimeStrToDate: rename_func(\"TO_DATE\"),\n        exp.UnixToStr: lambda self, e: self.func(\"FROM_UNIXTIME\", e.this, self.format_time(e)),", "new_string": "        exp.TimeStrToDate: rename_func(\"TO_DATE\"),\n        exp.TsOrDsAdd: _ts_or_ds_add_sql,\n        exp.UnixToStr: lambda self, e: self.func(\"FROM_UNIXTIME\", e.this, self.format_time(e)),"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-2/sqlglot/generators/starrocks.py has been updated successfully.
[assistant] Now I'll check the AST node and the output for each form, both dialects and several targets.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor d in ['doris','starrocks']:\n    for s in [\\\"select date_add('2025-01-01', 1) from a\\\", \\\"select date_sub('2025-01-01', 1) from a\\\", \\\"select date_add('2025-01-01', 
…[191 chars elided]…
      print(d, '|', type(n).__name__, '|', e.sql(d))\nprint()\nfor s in ['select date_add(x, 1) from a', 'select date_sub(x, 1) from a']:\n  for d in ['doris','starrocks']:\n    e = sqlglot.parse_one(s, read=d)\n    print(d, s, {w: e.sql(w) for w in ['duckdb','hive','spark','mysql','postgres','snowflake','doris','starrocks']})\n\" 2>&1", "description": "Verify parsed node types and generated SQL"}
[tool_result] doris | TsOrDsAdd | SELECT DATE_ADD('2025-01-01', 1) FROM a
doris | TsOrDsAdd | SELECT DATE_ADD('2025-01-01', -1) FROM a
doris | DateAdd | SELECT DATE_ADD('2025-01-01', INTERVAL '1' DAY) FROM a
doris | DateSub | SELECT DATE_SUB(x, INTERVAL '2' MONTH) FROM a
doris | TsOrDsAdd | SELECT DATE_ADD(x, n) FROM a
starrocks | TsOrDsAdd | SELECT DATE_ADD('2025-01-01', 1) FROM a
starrocks | TsOrDsAdd | SELECT DATE_ADD('2025-01-01', -1) FROM a
starrocks | DateAdd | SELECT DATE_ADD('2025-01-01', INTERVAL '1'
…[1590 chars elided]…
 a'}
starrocks select date_sub(x, 1) from a {'duckdb': 'SELECT CAST(x AS DATE) + INTERVAL (-1) DAY FROM a', 'hive': 'SELECT DATE_ADD(x, -1) FROM a', 'spark': 'SELECT DATE_ADD(x, -1) FROM a', 'mysql': 'SELECT DATE_ADD(x, INTERVAL -1 DAY) FROM a', 'postgres': "SELECT CAST(CAST(x AS TIMESTAMP) AS DATE) + INTERVAL '-1 DAY' FROM a", 'snowflake': 'SELECT DATEADD(DAY, -1, CAST(CAST(x AS TIMESTAMP) AS DATE)) FROM a', 'doris': 'SELECT DATE_ADD(x, -1) FROM a', 'starrocks': 'SELECT DATE_ADD(x, -1) FROM a'}
[assistant] Each form parses to `TsOrDsAdd` or `DateAdd`/`DateSub` as intended, with no generic nodes. The cross-dialect outputs match the day arithmetic in Hive, Spark, and DuckDB. The `DATE_SUB` case now round-trips as `DATE_ADD(x, -1)`, which is the same arithmetic but not the same text.

I still need to verify the StarRocks unit guard with a non-day `TsOrDsAdd`, and check what the test helpers offer.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nprint(sqlglot.transpile('select dateadd(month, 1, x)', read='redshift', write='starrocks'))\nprint(sqlglot.transpile('select dateadd(month, 1, x)', read='redshift', write='doris'))\nprint(sqlglot.transpile('select dateadd(month, 1, x)', read='redshift', write='mysql'))\n\"; grep -n \"def parse_one\\|def validate_identity\\|def validate_all\" -A2 tests/dialects/test_dialect.py | head -20", "description": "Check unit guard and test helper signatures"}
[tool_result] ['SELECT DATE_ADD(x, INTERVAL 1 MONTH)']
['SELECT DATE_ADD(x, 1)']
['SELECT DATE_ADD(x, INTERVAL 1 MONTH)']
29:    def parse_one(self, sql, **kwargs):
30-        return parse_one(sql, read=self.dialect, **kwargs)
31-
--
53:    def validate_identity(
54-        self, sql, write_sql=None, pretty=False, check_command_warning=False, identify=False
55-    ):
--
68:    def validate_all(self, sql, read=None, write=None, pretty=False, identify=False):
69-        """
70-        Validate that:
[assistant] The StarRocks guard works: a MONTH `TsOrDsAdd` still emits the INTERVAL form. Doris has a pre-existing unit-blind `TsOrDsAdd` transform that emits `DATE_ADD(x, 1)` for MONTH, which I'm leaving alone and will flag. Next I'll add tests to both dialect test files, starting with the imports in each.
[tool_use Bash] {"command": "head -5 tests/dialects/test_starrocks.py; echo ---; grep -n \"    def test_\" tests/dialects/test_starrocks.py tests/dialects/test_doris.py", "description": "Check test file headers and method names"}
[tool_result] from sqlglot import exp
from sqlglot.errors import UnsupportedError
from tests.dialects.test_dialect import Validator


---
tests/dialects/test_starrocks.py:9:    def test_starrocks(self):
tests/dialects/test_starrocks.py:30:    def test_ddl(self):
tests/dialects/test_starrocks.py:125:    def test_identity(self):
tests/dialects/test_starrocks.py:136:    def test_time(self):
tests/dialects/test_starrocks.py:145:    def test_regex(self):
tests/dialects/test_starrocks.py:157:    def test_unnest(sel
…[405 chars elided]…
:108:    def test_regex(self):
tests/dialects/test_doris.py:116:    def test_analyze(self):
tests/dialects/test_doris.py:121:    def test_key(self):
tests/dialects/test_doris.py:126:    def test_distributed(self):
tests/dialects/test_doris.py:135:    def test_partition(self):
tests/dialects/test_doris.py:154:    def test_table_alias_conversion(self):
tests/dialects/test_doris.py:229:    def test_rename_table(self):
tests/dialects/test_doris.py:239:    def test_materialized_view_properties(self):
[assistant] I'll add one test method to each file. Each asserts the node class, then the `DATE_SUB` rewrite, then the cross-dialect targets. The StarRocks test also covers the non-day unit guard.
[tool_use Bash] {"command": "tail -c 200 tests/dialects/test_doris.py | od -c | tail -3; tail -c 50 tests/dialects/test_starrocks.py | od -c | tail -2; head -3 tests/dialects/test_doris.py", "description": "Check trailing newline state of test files"}
[tool_result] 0000260        A   S       S   E   L   E   C   T       1   "  \n        
0000300                            )  \n                                
0000310
0000060    )  \n                                                        
0000062
from tests.dialects.test_dialect import Validator
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-2/tests/dialects/test_doris.py", "old_string": "from tests.dialects.test_dialect import Validator\n", "new_string": "from sqlglot import exp\nfrom tests.dialects.test_dialect import Validator\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-2/tests/dialects/test_doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-2/tests/dialects/test_doris.py", "old_string": "        self.validate_identity(\n            \"CREATE MATERIALIZED VIEW mv BUILD DEFERRED REFRESH AUTO ON SCHEDULE EVERY 10 MINUTE AS SELECT 1\"\n        )", "new_string": "        self.validate_identity(\n   
…[470 chars elided]…
: \"SELECT DATE_SUB(x, 1)\"})\n        self.validate_all(\n            \"SELECT DATE_ADD(x, 1)\",\n            write={\n                \"doris\": \"SELECT DATE_ADD(x, 1)\",\n                \"duckdb\": \"SELECT CAST(x AS DATE) + INTERVAL 1 DAY\",\n                \"hive\": \"SELECT DATE_ADD(x, 1)\",\n                \"mysql\": \"SELECT DATE_ADD(x, INTERVAL 1 DAY)\",\n            },\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-2/tests/dialects/test_doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-2/tests/dialects/test_starrocks.py", "old_string": "        self.validate_identity(\n            \"CREATE TABLE test_table (col1 DATE) PARTITION BY RANGE (col1) (START ('2019-01-01') END ('2021-01-01') EVERY (INTERVAL 1 YEAR), START ('2021-01-01') END ('202
…[969 chars elided]…
ADD(x, 1)\",\n                \"duckdb\": \"SELECT CAST(x AS DATE) + INTERVAL 1 DAY\",\n                \"hive\": \"SELECT DATE_ADD(x, 1)\",\n                \"mysql\": \"SELECT DATE_ADD(x, INTERVAL 1 DAY)\",\n            },\n        )\n        self.validate_all(\n            \"SELECT DATE_ADD(x, INTERVAL 1 MONTH)\",\n            read={\"redshift\": \"SELECT DATEADD(month, 1, x)\"},\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/inv-2/tests/dialects/test_starrocks.py has been updated successfully.
[assistant] Now I'll run the two dialect test files, then lint and format-check the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_doris.py tests/dialects/test_starrocks.py 2>&1 | tail -30; echo \"EXIT: ${PIPESTATUS[0]}\"; $PY -m ruff check sqlglot/dialects/dialect.py sqlglot/parsers/doris.py 
…[31 chars elided]…
lglot/generators/starrocks.py tests/dialects/test_doris.py tests/dialects/test_starrocks.py 2>&1 | tail -5; $PY -m ruff format --check sqlglot/dialects/dialect.py sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py sqlglot/generators/starrocks.py tests/dialects/test_doris.py tests/dialects/test_starrocks.py 2>&1 | tail -5", "description": "Run Doris/StarRocks tests, ruff check and format check"}
[tool_result] ...................... [100%]
22 passed, 125 subtests passed in 0.26s
EXIT: 
All checks passed!
Would reformat: tests/dialects/test_doris.py
1 file would be reformatted, 5 files already formatted
[assistant] Both dialect test files pass (22 tests). Ruff reports that `test_doris.py` would be reformatted, so I'll check whether that comes from my lines.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format --diff tests/dialects/test_doris.py 2>&1 | head -30; git stash list >/dev/null; git show HEAD:tests/dialects/test_doris.py > /tmp/orig_test_doris.py && $PY -m ruff format --check /tmp/orig_test_doris.py 2>&1 | tail -1", "description": "Inspect the formatter diff for test_doris.py"}
[tool_result] --- tests/dialects/test_doris.py
+++ tests/dialects/test_doris.py
@@ -269,4 +269,3 @@
                 "mysql": "SELECT DATE_ADD(x, INTERVAL 1 DAY)",
             },
         )
-

1 file would be reformatted
1 file already formatted
[assistant] The only formatter complaint is a trailing blank line from my test insertion, and the original file was already formatted. I'll format that one file, then run the full suite once.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format tests/dialects/test_doris.py && $PY -m ruff format --check sqlglot/dialects/dialect.py sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py sqlglot/generators/starrocks.py tests/dialects/test_doris.py tests/dialects/test_starrocks.py && git diff --stat && ls .lithify/harness/scripts/", "description": "Format test file and list changed files"}
[tool_result] 1 file reformatted
6 files already formatted
 sqlglot/dialects/dialect.py      | 15 +++++++++++++++
 sqlglot/generators/starrocks.py  |  9 ++++++++-
 sqlglot/parsers/doris.py         |  3 +++
 sqlglot/parsers/starrocks.py     |  7 ++++++-
 tests/dialects/test_doris.py     | 17 +++++++++++++++++
 tests/dialects/test_starrocks.py | 20 ++++++++++++++++++++
 6 files changed, 69 insertions(+), 2 deletions(-)
run_suite.py
[This command modified 1 file you've previously read: tests/dialects/test_doris.py. Call Read before editing.]
[assistant] The formatter rewrite is the change I just made, so the file state is expected. Now the full suite, run once through the project harness script:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/scripts/run_suite.py 2>&1 | tail -40", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] WARNING: 6 other pytest process(es) running; expect slower runs:
  34207 02-22:44:47 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
  43740       00:51 <work>/env-sqlglot/b
  44102       00:35 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/f0ecd001-19e9-
…[413 chars elided]…
claude-501/-Users-user-Coding-delvera-foundational-lithify/f0ecd001-19e9-4b3c-8461-34bf1f0fcf2a/scratchpad/hwork/env-sqlglot/b
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-06f4059a61.log
ELAPSED: 122s
SUMMARY: 1086 passed, 17855 subtests passed in 121.05s (0:02:01)
EXIT: 0
[assistant] Both Doris and StarRocks now parse and generate the two-argument `DATE_ADD` / `DATE_SUB` form. The full suite passes after my last edit: `SUMMARY: 1086 passed, 17855 subtests passed in 121.05s`, `EXIT: 0`.

**What changed**
- `sqlglot/dialects/dialect.py`: new `build_date_delta_with_days_or_interval`. An INTERVAL second argument keeps the existing `DateAdd`/`DateSub` path. Any other second argument becomes `exp.TsOrDsAdd(unit=DAY)`. `DATE_SUB` negates the days.
- `sqlglot/parsers/doris.py` and `sqlglot/parsers/starrocks.py`: `DATE_ADD` and `DATE_SUB` use that builder.
- `sqlglot/generators/sta
…[1160 chars elided]…
s' day-unit `TsOrDsAdd` (for example Hive `DATE_ADD(x, 1)`) now transpile to two-arg `DATE_ADD(x, 1)` in StarRocks. They previously produced `DATE_ADD(x, INTERVAL 1 DAY)`. Both are valid for the same date arithmetic, and the suite passes.
- **Pre-existing Doris bug, not fixed.** Doris's `TsOrDsAdd` transform ignores the unit. `dateadd(month, 1, x)` from Redshift becomes `DATE_ADD(x, 1)` in Doris, which adds one day. The StarRocks transform guards against this; Doris would need the same guard. I left it alone to keep the change scoped.

Nothing is committed. The changes are in the working tree.
