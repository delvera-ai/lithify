# trajectory comp-1

final message:
Doris and StarRocks now parse and generate the two-argument `DATE_ADD` / `DATE_SUB` form. The full suite passes after my last edit: `VERDICT: PASS` (1086 passed).

**What changed**
- **Parsing:** `DATE_ADD(d, n)` builds `exp.TsOrDsAdd` with unit `DAY`. `DATE_SUB(d, n)` builds the same node with `n` negated, since there is no `TsOrDsSub`. The INTERVAL form still builds `DateAdd` / `DateSub`. A shared builder, `build_date_delta_with_days`, lives in `sqlglot/dialects/dialect.py` and is wired into both parsers.
- **Generating:** a shared helper, `ts_or_ds_add_days_sql` in `sqlglot/generators/mysql.py`, emits `DATE_ADD(d, n)` only when the unit is DAY or absent. Otherwise it falls back to the INTERVAL spelling. Doris and StarRocks both use it.
- **Bug fixed along the way:** Doris's old `TsOrDsAdd` entry ignored the unit. Redshift `DATEADD(MONTH, 1, x)` came out as `DATE_ADD(x, 1)`, which is one day. It now emits `DATE_ADD(x, INTERVAL 1 MONTH)`.

**Tests:** I added `test_date_add_days` to `tests/dialects/test_doris.py` and `tests/dialects/test_starrocks.py`. They assert node classes, the 2-arg and negated forms, the unchanged INTERVAL form, and the Redshift MONTH transpile. I did not edit any existing test.

**Choices to review**
- `DATE_SUB(d, n)` round-trips as `DATE_ADD(d, -n)`, not as `DATE_SUB`. That is semantically equal, but the spelling changes.
- The day-count node leaves `return_type` at its default, like the Hive precedent. I did not set it.
- StarRocks generation also changed: any day-unit `TsOrDsAdd` (for example from Hive) now emits the 2-arg form instead of the INTERVAL form. The existing suite still passes with that change.

## events
[tool_use Skill] {"skill": "sqlglot-date-arithmetic"}
[tool_result] Launching skill: sqlglot-date-arithmetic
[user] Base directory for this skill: ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/comp-1/.claude/skills/sqlglot-date-arithmetic

# Date arithmetic in sqlglot: which node, and transforms that keep the unit

Use together with `sqlglot-dialect-functions` (canonical-node and parser/generator contract).

## Node map (verified in source)
| SQL shape | node | built by / precedent |
|---|---|---|
| `DATE_ADD(d, INTERVAL n UNIT)` / `DATE_SUB(...)` (MySQL family) | `exp.DateAdd` / `exp.DateSub` | `build_date_delta_with_interval` in `sqlglot/dialects/dia
…[2504 chars elided]…
 e.this, e.expression)` that turned a MONTH into
  days. Don't copy an unguarded lambda into another dialect.

## Done means, read from actual output
- The new form parses into the node above in every dialect the task names, and the INTERVAL
  form still parses into `DateAdd` / `DateSub`.
- Transpiling Redshift `SELECT DATEADD(MONTH, 1, x), ADD_MONTHS(x, 2)` into each dialect whose
  generator you touched still contains `MONTH`; compare against the output before your edit.
- The tests assert the node class, cover the new and old forms, and include a non-DAY unit
  transpiled into the dialect.

[tool_use Bash] {"command": "git status --short && ls sqlglot/parsers/ | grep -iE 'doris|starrocks|mysql' ; ls sqlglot/generators | grep -iE 'doris|starrocks|mysql'; grep -rn \"DateAdd\\|DateSub\\|DATE_ADD\\|DATE_SUB\" sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py sqlglot/parsers/mysql.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py sqlglot/generators/mysql.py sqlglot/dialects/doris.py sqlglot/dialects/starrocks.py sqlglot/dialects/mysql.py", "description": "Check git status, list dialect files, grep date funcs"}
[tool_result] doris.py
mysql.py
starrocks.py
doris.py
mysql.py
starrocks.py
sqlglot/generators/mysql.py:151:        exp.DateAdd: _remove_ts_or_ds_to_date(date_add_sql("ADD")),
sqlglot/generators/mysql.py:153:        exp.DateSub: _remove_ts_or_ds_to_date(date_add_sql("SUB")),
sqlglot/generators/mysql.py:742:        dateadd = build_date_delta_with_interval(exp.DateAdd)([start_ts, interval])
sqlglot/generators/doris.py:75:        exp.TsOrDsAdd: lambda self, e: self.func("DATE_ADD", e.this, e.expression),
sqlglot/parsers/mysql.py:114:        "DATE_ADD": build_date_delta_with_interval(exp.DateAdd),
sqlglot/parsers/mysql.py:119:        "DATE_SUB": build_date_delta_with_interval(exp.DateSub),
[tool_use Bash] {"command": "grep -n \"def build_date_delta_with_interval\" -A 25 sqlglot/dialects/dialect.py; echo ---; grep -n \"DATE_ADD\\|DATE_SUB\\|DateAdd\\|DateSub\\|TsOrDsAdd\\|class \\|import\" sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py; echo ---; sed -n 60,90p sqlglot/generators/doris.py; echo ---; grep -n \"TsOrDsAdd\\|DATE_ADD\\|DATE_SUB\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py", "description": "Read date builder, Doris/StarRocks parser and generator code"}
[tool_result] 1599:def build_date_delta_with_interval(
1600-    expression_class: Type[E],
1601-) -> t.Callable[[BuilderArgs], E | None]:
1602-    def _builder(args: BuilderArgs) -> E | None:
1603-        if len(args) < 2:
1604-            return None
1605-
1606-        interval = args[1]
1607-
1608-        if not isinstance(interval, exp.Interval):
1609-            raise ParseError(f"INTERVAL expression expected but got '{interval}'")
1610-
1611-        return expression_class(this=args[0], expression=interv
…[3225 chars elided]…
func("DATE_TRUNC", e.this, unit_to_str(e)),
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
---
[tool_use Bash] {"command": "sed -n 1,80p sqlglot/parsers/doris.py; echo ---; sed -n 1,60p sqlglot/parsers/starrocks.py; echo ---; sed -n 100,125p sqlglot/parsers/mysql.py; echo ---; sed -n 140,160p sqlglot/generators/mysql.py; echo ---; grep -n \"def date_add_sql\" -A 25 sqlglot/generators/mysql.py sqlglot/dialects/dialect.py; echo ---; grep -n \"_dateadd_sql\\|_add_date_sql\" -A 14 sqlglot/generators/spark.py sqlglot/generators/hive.py | head -60; echo ---; grep -n \"_build_date_add\\b\" -A 20 sqlglot/parsers/hive.py | head -40", "description": "Read parsers, MySQL builders and precedent transforms"}
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
    
…[14582 chars elided]…
alar(
83-            this=seq_get(args, 0), expression=dialect.to_json_path(seq_get(args, 1))
84-        ),
85-        "LAST": build_with_ignore_nulls(exp.Last),
86-        "LAST_VALUE": build_with_ignore_nulls(exp.LastValue),
87-        "MAP": parser.build_var_map,
88-        "MONTH": lambda args: exp.Month(this=exp.TsOrDsToDate.from_arg_list(args)),
89-        "REGEXP_EXTRACT": build_regexp_extract(exp.RegexpExtract),
90-        "REGEXP_EXTRACT_ALL": build_regexp_extract(exp.RegexpExtractAll),
[tool_use Bash] {"command": "grep -n \"TsOrDsAdd\\|DATE_ADD\\|DATE_SUB\\|date_add\\|date_sub\" sqlglot/generators/starrocks.py sqlglot/generators/mysql.py; echo ---; grep -n \"_sql\\b\\|TRANSFORMS\" sqlglot/generator.py | grep -n \"getattr\\|TRANSFORMS\\|_sql_name\\|def sql\" | head; echo ---; grep -rn -i \"date_add\\|date_sub\\|TsOrDsAdd\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_mysql.py | head -40; echo ---; grep -n \"__neg__\" sqlglot/expressions/*.py | head -3; cat .lithify/harness/scripts/run_tests.py | head -5 >/dev/null; ls .lithify/harness", "description": "Check generator dispatch, StarRocks generator, and existing tests"}
[tool_result] sqlglot/generators/mysql.py:10:    date_add_interval_sql,
sqlglot/generators/mysql.py:74:def date_add_sql(
sqlglot/generators/mysql.py:151:        exp.DateAdd: _remove_ts_or_ds_to_date(date_add_sql("ADD")),
sqlglot/generators/mysql.py:153:        exp.DateSub: _remove_ts_or_ds_to_date(date_add_sql("SUB")),
sqlglot/generators/mysql.py:192:        exp.TimestampAdd: date_add_interval_sql("DATE", "ADD"),
sqlglot/generators/mysql.py:196:        exp.TimestampSub: date_add_interval_sql("DATE", "SUB"),
s
…[1961 chars elided]…
tests/dialects/test_mysql.py:1465:                            "mysql": f"DATE_ADD('0000-01-01 00:00:00', INTERVAL (TIMESTAMPDIFF({unit}, '0000-01-01 00:00:00', {cast})) {unit})",
tests/dialects/test_mysql.py:1618:                self.validate_identity(f"DATE_ADD(base_date, INTERVAL day_interval {unit})")
---
sqlglot/expressions/core.py:482:    def __neg__(self) -> Neg:
sqlglot/expressions/core.py:1537:    def __neg__(self) -> Neg:
guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
[tool_use Bash] {"command": "sed -n 3505,3525p sqlglot/generator.py; echo ---; sed -n 1,60p sqlglot/generators/doris.py; echo ---; grep -n \"TRANSFORMS\" sqlglot/generators/starrocks.py; sed -n 54,70p sqlglot/generators/starrocks.py; echo ---; sed -n 1,40p sqlglot/parsers/starrocks.py | grep -n DATE; cat tests/dialects/test_doris.py | head -30", "description": "Inspect generator dispatch and Doris/StarRocks class headers"}
[tool_result]         return path

    def json_path_part(self, expression: int | str | exp.JSONPathPart) -> str:
        if isinstance(expression, exp.JSONPathPart):
            transform = self.TRANSFORMS.get(expression.__class__)
            if not callable(transform):
                self.unsupported(f"Unsupported JSONPathPart type {expression.__class__.__name__}")
                return ""

            return transform(self, expression)

        if isinstance(expression, int):
            return str(expr
…[3640 chars elided]…
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
[assistant] Before editing, I'll capture the current behaviour for the Redshift baseline the skill asks for, and check the StarRocks TRANSFORMS block I'll need to touch.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor s in ['SELECT DATEADD(MONTH, 1, x), ADD_MONTHS(x, 2)']:\n    e = sqlglot.parse_one(s, read='redshift')\n    print([ (type(n).__name__, n.text('unit')) for n in e.find_all(exp.TsOrDsAdd)])\n    for d in ['doris','starrocks','mysql','hive']:\n        print(d, e.sql(d))\n\" ; sed -n 86,92p sqlglot/generators/starrocks.py; grep -n \"^from\\|^import\" sqlglot/generators/starrocks.py", "description": "Capture Redshift baseline transpilation before edits"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
    }

    TRANSFORMS = {
        **{k: v for k, v in MySQLGenerator.TRANSFORMS.items() if k is not exp.DateTrunc},
        exp.Array: inline_array_sql,
        exp.ArrayAgg: rename_func("ARRAY_AGG"),
        exp.ArrayFilter: rename_func("ARRAY_FILTER"),
1:from __future__ import annotations
4:from sqlglot import exp, transforms
5:from sqlglot.dialects.dialect import (
13:from sqlglot.generators.mysql import MySQLGenerator
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one('SELECT DATEADD(MONTH, 1, x), ADD_MONTHS(x, 2)', read='redshift')\nprint([ (type(n).__name__, n.text('unit')) for n in e.find_all(exp.TsOrDsAdd)])\nfor d in ['doris','starrocks','mysql','hive']:\n    print(d, e.sql(d))\nprint('doris day ->', sqlglot.transpile(\\\"SELECT DATE_ADD(x, 1)\\\", read='hive', write='doris'))\n\"", "description": "Capture Redshift baseline transpilation before edits"}
[tool_result] [('TsOrDsAdd', 'MONTH'), ('TsOrDsAdd', 'MONTH')]
doris SELECT DATE_ADD(x, 1), DATE_ADD(x, 2)
starrocks SELECT DATE_ADD(x, INTERVAL 1 MONTH), DATE_ADD(x, INTERVAL 2 MONTH)
mysql SELECT DATE_ADD(x, INTERVAL 1 MONTH), DATE_ADD(x, INTERVAL 2 MONTH)
hive SELECT ADD_MONTHS(x, 1), ADD_MONTHS(x, 2)
doris day -> ['SELECT DATE_ADD(x, 1)']
[assistant] The baseline confirms the bug the skill warns about: Doris turns Redshift `DATEADD(MONTH, 1, x)` into `DATE_ADD(x, 1)`, which is one day. I'll fix that as part of the change. Next, the shared parser builder in `dialect.py`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/comp-1/sqlglot/dialects/dialect.py", "old_string": "        return expression_class(this=args[0], expression=interval.this, unit=unit_to_str(interval))\n\n    return _builder\n\n\ndef date_trunc_to_time(", "new_string": "        return expression_class(this=arg
…[301 chars elided]…
n_class)\n\n    def _builder(args: BuilderArgs) -> E | exp.TsOrDsAdd | None:\n        if len(args) < 2 or isinstance(args[1], exp.Interval):\n            return interval_builder(args)\n\n        days = exp.Neg(this=args[1]) if negate_days else args[1]\n        return exp.TsOrDsAdd(this=args[0], expression=days, unit=exp.Literal.string(\"DAY\"))\n\n    return _builder\n\n\ndef date_trunc_to_time("}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/comp-1/sqlglot/dialects/dialect.py has been updated successfully.
[assistant] Now the generator side. I'll put one guarded helper next to `date_add_sql` in the MySQL generator, which both Doris and StarRocks already import from.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/comp-1/sqlglot/generators/mysql.py", "old_string": "    return func\n\n\ndef _ts_or_ds_to_date_sql(", "new_string": "    return func\n\n\ndef ts_or_ds_add_days_sql(self: MySQLGenerator, expression: exp.TsOrDsAdd) -> str:\n    if expression.text(\"unit\").upper() in (\"\", \"DAY\"):\n        return self.func(\"DATE_ADD\", expression.this, expression.expression)\n\n    return date_add_sql(\"ADD\")(self, expression)\n\n\ndef _ts_or_ds_to_date_sql("}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/comp-1/sqlglot/generators/mysql.py has been updated successfully.
[tool_use Bash] {"command": "sed -n 1,30p sqlglot/dialects/dialect.py | grep -n \"BuilderArgs\\|Type\\|import\" ; sed -n 1,20p sqlglot/parsers/starrocks.py >/dev/null; sed -n 4,14p sqlglot/generators/starrocks.py; sed -n 1,12p sqlglot/generators/mysql.py", "description": "Check imports needed in edited modules"}
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
…[411 chars elided]…
t (
    approx_count_distinct_sql,
    arrow_json_extract_sql,
    rename_func,
    unit_to_str,
    inline_array_sql,
    property_sql,
)
from sqlglot.generators.mysql import MySQLGenerator

from __future__ import annotations

import typing as t

from sqlglot import exp, generator, transforms
from sqlglot.dialects.dialect import (
    arrow_json_extract_sql,
    build_date_delta,
    build_date_delta_with_interval,
    date_add_interval_sql,
    datestrtodate_sql,
    length_or_char_length_sql,
[assistant] Imports are in place. Now the Doris and StarRocks parsers, generators, and dispatch wiring.
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\ndef edit(path, old, new, count=1):\n    s = open(path).read()\n    assert s.count(old) == count, (path, old, s.count(old))\n    open(path, \"w\").write(s.replace(old, new))\n\n# Doris parser\nedit(\"sqlglot/parsers/doris.py\",\n\"from sqlglot import exp\\nfrom sqlglot.helper import seq_get\\n\",\n\"from sqlglot import exp\\nfrom sqlglot.dialects.dialect i
…[2215 chars elided]…
elect date_sub(x, interval 2 month)']:\n        e = sqlglot.parse_one(s, read=d)\n        n = e.selects[0]\n        print(d, '|', type(n).__name__, '|', e.sql(d))\ne = sqlglot.parse_one('SELECT DATEADD(MONTH, 1, x), ADD_MONTHS(x, 2)', read='redshift')\nfor d in ['doris','starrocks','mysql','hive']: print(d, e.sql(d))\n\"", "description": "Wire parser and generator changes for Doris and StarRocks"}
[tool_result] ok
doris | TsOrDsAdd | SELECT DATE_ADD('2025-01-01', 1) FROM a
doris | TsOrDsAdd | SELECT DATE_ADD('2025-01-01', -1) FROM a
doris | DateAdd | SELECT DATE_ADD('2025-01-01', INTERVAL '1' DAY)
doris | DateSub | SELECT DATE_SUB(x, INTERVAL '2' MONTH)
starrocks | TsOrDsAdd | SELECT DATE_ADD('2025-01-01', 1) FROM a
starrocks | TsOrDsAdd | SELECT DATE_ADD('2025-01-01', -1) FROM a
starrocks | DateAdd | SELECT DATE_ADD('2025-01-01', INTERVAL '1' DAY)
starrocks | DateSub | SELECT DATE_SUB(x, INTERVAL '2' MONTH)
doris SELECT DATE_ADD(x, INTERVAL 1 MONTH), DATE_ADD(x, INTERVAL 2 MONTH)
starrocks SELECT DATE_ADD(x, INTERVAL 1 MONTH), DATE_ADD(x, INTERVAL 2 MONTH)
mysql SELECT DATE_ADD(x, INTERVAL 1 MONTH), DATE_ADD(x, INTERVAL 2 MONTH)
hive SELECT ADD_MONTHS(x, 1), ADD_MONTHS(x, 2)
[assistant] Parsing and generation now behave as intended, and the Redshift MONTH transpile keeps its unit in Doris and StarRocks. Next I'll look at the test conventions before adding tests.
[tool_use Bash] {"command": "grep -n \"assert_is\\|^from\\|^import\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py | head; grep -n \"def assert_is\" -A6 tests/dialects/test_dialect.py; tail -5 tests/dialects/test_doris.py; tail -5 tests/dialects/test_starrocks.py", "description": "Check test helpers and file endings"}
[tool_result] tests/dialects/test_doris.py:1:from tests.dialects.test_dialect import Validator
tests/dialects/test_starrocks.py:1:from sqlglot import exp
tests/dialects/test_starrocks.py:2:from sqlglot.errors import UnsupportedError
tests/dialects/test_starrocks.py:3:from tests.dialects.test_dialect import Validator
tests/dialects/test_starrocks.py:18:        self.validate_identity("ARRAY_FLATTEN(arr)").assert_is(exp.Flatten)

        # Combined BUILD and REFRESH
        self.validate_identity(
            "C
…[79 chars elided]…
UTE AS SELECT 1"
        )
            "CREATE TABLE test_table (col1 BIGINT) PARTITION BY RANGE (col1) (START ('1') END ('10') EVERY (1), START ('10') END ('100') EVERY (10))"
        )
        self.validate_identity(
            "CREATE TABLE test_table (col1 DATE) PARTITION BY RANGE (col1) (START ('2019-01-01') END ('2021-01-01') EVERY (INTERVAL 1 YEAR), START ('2021-01-01') END ('2021-05-01') EVERY (INTERVAL 1 MONTH), START ('2021-05-01') END ('2021-05-04') EVERY (INTERVAL 1 DAY))"
        )
[assistant] The test helpers return the parsed expression, so I can assert node classes directly. I'll add one test method per dialect covering: the new 2-arg form (node class and output), the negated `DATE_SUB` form, the INTERVAL form unchanged, and a non-DAY unit transpiled from Redshift.
[tool_use Bash] {"command": "cat >> tests/dialects/test_doris.py <<'EOF'\n\n    def test_date_add_days(self):\n        from sqlglot import exp\n\n        self.validate_identity(\"SELECT DATE_ADD(x, 1)\").selects[0].assert_is(exp.TsOrDsAdd)\n        self.validate_identity(\"SELECT DATE_ADD(x, -1)\")\n        self.validate_identity(\n            \"SELECT DATE_ADD(x, INTERVAL 1 DAY)\", \"SELECT DATE_ADD(x, INTERVAL 
…[1097 chars elided]…
, 1, x)\"},\n        )\nEOF\nPY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/scripts/run_tests.py tests/dialects/test_doris.py tests/dialects/test_starrocks.py 2>&1 | tail -40", "description": "Append Doris/StarRocks tests and run their dialect files", "timeout": 600000}
[tool_result] cmd: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no -rfE tests/dialects/test_doris.py tests/dialects/test_starrocks.py
log: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/pytest-comp-1-1793031822.log
elapsed: 0s, exit: 0
=================== 22 passed, 118 subtests passed in 0.18s ====================
VERDICT: PASS
[assistant] Both dialect files pass (22 tests). Now the full suite, run once after my last edit as the harness requires.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/scripts/run_tests.py 2>&1 | tail -30", "description": "Run full test suite after final edits", "timeout": 600000}
[tool_result] cmd: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no -rfE
log: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/pytest-comp-1-1793031825.log
elapsed: 72s, exit: 0
============ 1086 passed, 17848 subtests passed in 71.20s (0:01:11) ============
VERDICT: PASS
[assistant] Full suite passes. One last check: formatting on the touched files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff --version && $PY -m ruff format --check sqlglot/dialects/dialect.py sqlglot/generators/mysql.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py tests/dialects/test_doris.py tests/dialects/test_starrocks.py; $PY -m ruff check sqlglot/dialects/dialect.py sqlglot/generators/mysql.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py; git status --short", "description": "Check formatting and lint on changed files"}
[tool_result] ruff 0.15.6
8 files already formatted
All checks passed!
 M sqlglot/dialects/dialect.py
 M sqlglot/generators/doris.py
 M sqlglot/generators/mysql.py
 M sqlglot/generators/starrocks.py
 M sqlglot/parsers/doris.py
 M sqlglot/parsers/starrocks.py
 M tests/dialects/test_doris.py
 M tests/dialects/test_starrocks.py
[assistant] Doris and StarRocks now parse and generate the two-argument `DATE_ADD` / `DATE_SUB` form. The full suite passes after my last edit: `VERDICT: PASS` (1086 passed).

**What changed**
- **Parsing:** `DATE_ADD(d, n)` builds `exp.TsOrDsAdd` with unit `DAY`. `DATE_SUB(d, n)` builds the same node with `n` negated, since there is no `TsOrDsSub`. The INTERVAL form still builds `DateAdd` / `DateSub`. A shared builder, `build_date_delta_with_days`, lives in `sqlglot/dialects/dialect.py` and is wired into both parsers.
- **Generating:** a shared helper, `ts_or_ds_add_days_sql` in `sqlglot/generators/mysql
…[461 chars elided]…
ks.py`. They assert node classes, the 2-arg and negated forms, the unchanged INTERVAL form, and the Redshift MONTH transpile. I did not edit any existing test.

**Choices to review**
- `DATE_SUB(d, n)` round-trips as `DATE_ADD(d, -n)`, not as `DATE_SUB`. That is semantically equal, but the spelling changes.
- The day-count node leaves `return_type` at its default, like the Hive precedent. I did not set it.
- StarRocks generation also changed: any day-unit `TsOrDsAdd` (for example from Hive) now emits the 2-arg form instead of the INTERVAL form. The existing suite still passes with that change.
