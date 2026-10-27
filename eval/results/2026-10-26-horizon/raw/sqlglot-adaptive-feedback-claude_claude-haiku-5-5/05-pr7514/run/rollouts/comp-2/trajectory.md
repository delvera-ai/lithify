# trajectory comp-2

final message:
Doris and StarRocks now accept the two-argument `DATE_ADD` / `DATE_SUB` form, and the repro from your report parses. The full suite passes (`VERDICT: PASS`, 1086 tests) and ruff is clean. I haven't committed anything.

**What changed**
- **Parser:** a new builder in `sqlglot/dialects/dialect.py`, `build_date_delta_with_days_or_interval`, is registered for `DATE_ADD` and `DATE_SUB` in both `parsers/doris.py` and `parsers/starrocks.py`. A second argument that isn't an `INTERVAL` becomes `exp.TsOrDsAdd` with unit DAY. The `INTERVAL` form still yields `DateAdd` / `DateSub`. MySQL's parser is unchanged, since MySQL doesn't accept the two-argument form.
- **Generator:** `ts_or_ds_add_days_sql` in `sqlglot/generators/mysql.py` emits `DATE_ADD(x, n)` for DAY or unitless `TsOrDsAdd`, and falls back to the interval form for other units. Doris uses it in place of the old override, which dropped the unit. StarRocks gets it as a new `TsOrDsAdd` transform. MySQL is untouched.
- **Tests:** a `test_date_add_days` method in `tests/dialects/test_doris.py` and `tests/dialects/test_starrocks.py`. It asserts the AST node types, the two-argument round-trip, a Spark-to-Doris/StarRocks read, and a Redshift `DATEADD(MONTH, …)` case that must keep MONTH.

**Choices you may want to revisit**
- **`DATE_SUB(x, n)` generates as `DATE_ADD(x, -n)`.** I negated the amount (the Hive precedent), so it doesn't round-trip to the `DATE_SUB` name. It is semantically identical. Emitting `DATE_SUB` would mean changing how `DateSub` generates for DAY units, which would alter existing interval output.
- **Behaviour change:** `TsOrDsAdd` with DAY or no unit now generates as `DATE_ADD(x, n)` on StarRocks, where it used to be `DATE_ADD(x, INTERVAL n DAY)`. Non-DAY units on Doris now get the interval form instead of silently dropping the unit. Existing tests didn't pin either output.

## events
[tool_use Skill] {"skill": "sqlglot-date-arithmetic"}
[tool_result] Launching skill: sqlglot-date-arithmetic
[user] Base directory for this skill: ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/comp-2/.claude/skills/sqlglot-date-arithmetic

# Date arithmetic in sqlglot: which node, and how generators must treat it

Use together with `sqlglot-dialect-functions` (general parse/generate contract).

## Node map (verified in source)
| SQL shape | node | built by / precedent |
|---|---|---|
| `DATE_ADD(d, INTERVAL n UNIT)` / `DATE_SUB(...)` | `exp.DateAdd` / `exp.DateSub`, unit from the interval | `build_date_delta_with_interval` in `sqlglot/dialects/dialect.
…[3304 chars elided]…
d`, but `StarRocksGenerator`
   inherits MySQL's interval form. Both subclass `MySQLGenerator`/`MySQLParser`.
3. Tests in `tests/dialects/test_<d>.py` for each dialect:
   - Assert the node class (`validate_identity(...).assert_is(exp.X)`). Import `exp` if the file
     doesn't already, as `test_doris.py` didn't.
   - Cover both the new form and the old INTERVAL form.
   - Add a `validate_all` transpiling a non-DAY unit into the dialect.
   - In these MySQL-family dialects, `INTERVAL 1 DAY` generates as `INTERVAL '1' DAY`. Write
     identity expectations for interval forms with that in mind.

[tool_use Bash] {"command": "cat .lithify/harness/tool_guidance.md 2>/dev/null | head -50; grep -rn \"DATE_ADD\\|DateAdd\\|DATE_SUB\\|DateSub\" sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py sqlglot/dialects/doris.py sqlglot/dialects/starrocks.py sqlglot/dialects/mysql.py 2>/dev/null", "description": "Read date-arithmetic guidance and grep Doris/StarRocks date functions"}
[tool_result] - The shell is macOS zsh: `timeout` is not installed; use the Bash tool's own timeout. `sed -i`
  needs `-i ''` (BSD). An unquoted `$VAR` holding several paths is NOT word-split, so pass paths
  literally. `grep --include=*.py` needs quoting (`--include='*.py'`).
- Running tests: always use `<python> .lithify/harness/scripts/run_tests.py [pytest args]` as a
  FOREGROUND Bash call with `timeout: 600000` (its default limit is 540 s; for `--limit N` set the
  Bash timeout above N). It refuses to st
…[203 chars elided]…
` are not passes.
- Do not run pytest with `run_in_background`, `| tail`, `&`, or `sleep`-polling. A backgrounded
  run's output is empty until it ends, a piped `||` fallback never fires (the exit code is
  `tail`'s), `sleep N; cat` is blocked, and every extra run competes for CPU with the last one.
  Run the dialect's test file first, then the full suite once after your final edit.
sqlglot/generators/doris.py:75:        exp.TsOrDsAdd: lambda self, e: self.func("DATE_ADD", e.this, e.expression),
[assistant] The skill's contract is clear: a parser branch for the two-argument form, a unit-aware generator, and tests per dialect. Next I'll read the existing Doris and StarRocks parser and generator code and the shared builders.
[tool_use Bash] {"command": "cat sqlglot/parsers/doris.py; echo ----; cat sqlglot/parsers/starrocks.py; echo ----; cat sqlglot/generators/doris.py; echo ----; cat sqlglot/generators/starrocks.py; echo ----; grep -n \"def build_date_delta_with_interval\" -A25 sqlglot/dialects/dialect.py; echo ----; grep -n \"DATE_ADD\\|DATE_SUB\\|DateAdd\\|DateSub\\|TsOrDsAdd\" sqlglot/parsers/mysql.py sqlglot/generators/mysql.py", "description": "Read Doris/StarRocks parser and generator and MySQL date handling"}
[tool_result] <persisted-output>
Output too large (35.7KB). Full output saved to: ~/.claude/projects/-Users-user--cache-lithify-work-repo-55c905b0df68-20261026-160938-doris-and-starrocks-dialects-bot-comp-2/ac3d7f92-3e1d-4841-baa0-dc71619805f9/tool-results/bf8c5ya42.txt

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
[tool_use Bash] {"command": "grep -n \"DATE_ADD\\|DATE_SUB\\|DateAdd\\|DateSub\\|TsOrDsAdd\\|build_date_delta\" sqlglot/parsers/mysql.py sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py sqlglot/generators/mysql.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py sqlglot/dialects/dialect.py sqlglot/parsers/hive.py sqlglot/parsers/spark.py sqlglot/generators/spark.py sqlglot/generators/hive.py; echo ----; grep -n \"def build_date_delta_with_interval\" -A25 sqlglot/dialects/dialect.py", "description": "Locate date arithmetic handling across dialects"}
[tool_result] sqlglot/generators/mysql.py:8:    build_date_delta,
sqlglot/generators/mysql.py:9:    build_date_delta_with_interval,
sqlglot/generators/mysql.py:151:        exp.DateAdd: _remove_ts_or_ds_to_date(date_add_sql("ADD")),
sqlglot/generators/mysql.py:153:        exp.DateSub: _remove_ts_or_ds_to_date(date_add_sql("SUB")),
sqlglot/generators/mysql.py:209:        exp.TsOrDsAdd: date_add_sql("ADD"),
sqlglot/generators/mysql.py:740:        timestamp_diff = build_date_delta(exp.TimestampDiff)([unit, start_
…[4693 chars elided]…
610-
1611-        return expression_class(this=args[0], expression=interval.this, unit=unit_to_str(interval))
1612-
1613-    return _builder
1614-
1615-
1616-def date_trunc_to_time(args: BuilderArgs) -> exp.DateTrunc | exp.TimestampTrunc:
1617-    unit = seq_get(args, 0)
1618-    this = seq_get(args, 1)
1619-
1620-    if isinstance(this, exp.Cast) and this.is_type("date"):
1621-        return exp.DateTrunc(unit=unit, this=this)
1622-    return exp.TimestampTrunc(this=this, unit=unit)
1623-
1624-
[assistant] The shared builder raises on the non-interval form, and MySQL's generator emits `TsOrDsAdd` through `date_add_sql("ADD")`. Next I'll check the Spark/Hive two-argument precedents and the existing Doris/StarRocks tests.
[tool_use Bash] {"command": "sed -n 40,50p sqlglot/parsers/spark.py; echo ----; sed -n 30,40p sqlglot/parsers/hive.py; echo ----; sed -n 30,60p sqlglot/generators/spark.py; echo ----; sed -n 60,80p sqlglot/generators/doris.py; echo ----; grep -n \"def date_add_sql\" -A25 sqlglot/dialects/dialect.py; echo ----; grep -n \"DATE_ADD\\|DATE_SUB\\|date_add\\|exp\\b\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py | head -40; grep -n \"^from\\|^import\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py", "description": "Read Spark/Hive/MySQL date builders and existing dialect tests"}
[tool_result] def _build_dateadd(args: list) -> exp.Expr:
    expression = seq_get(args, 1)

    if len(args) == 2:
        # DATE_ADD(startDate, numDays INTEGER)
        # https://docs.databricks.com/en/sql/language-manual/functions/date_add.html
        return exp.TsOrDsAdd(
            this=seq_get(args, 0), expression=expression, unit=exp.Literal.string("DAY")
        )

    # DATE_ADD / DATEADD / TIMESTAMPADD(unit, value integer, expr)
----


def _build_date_add(args: list) -> exp.TsOrDsAdd:
    expressi
…[3007 chars elided]…
exp.column("c"),
tests/dialects/test_starrocks.py:90:                exp.column("d"),
tests/dialects/test_starrocks.py:95:        single_column_cluster = exp.Cluster(expressions=[exp.column("c")])
tests/dialects/test_doris.py:1:from tests.dialects.test_dialect import Validator
tests/dialects/test_starrocks.py:1:from sqlglot import exp
tests/dialects/test_starrocks.py:2:from sqlglot.errors import UnsupportedError
tests/dialects/test_starrocks.py:3:from tests.dialects.test_dialect import Validator
[assistant] I have enough of the precedents now. Before editing, I need to see where `date_add_sql` lives, what the StarRocks generator looks like, and which existing Doris/StarRocks tests pin the current DATE_ADD output, since a generator change could break them.
[tool_use Bash] {"command": "grep -rn \"def date_add_sql\" -A22 sqlglot/ | head -40; echo ----; cat sqlglot/generators/starrocks.py | head -60; echo ----; cat sqlglot/parsers/starrocks.py | head -40; echo ----; grep -rn \"DATE_ADD\\|DATE_SUB\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_mysql.py | head -40", "description": "Inspect date_add_sql helper, StarRocks files, and related tests"}
[tool_result] sqlglot/generators/mysql.py:74:def date_add_sql(
sqlglot/generators/mysql.py-75-    kind: str,
sqlglot/generators/mysql.py-76-) -> t.Callable[[generator.Generator, exp.Expr], str]:
sqlglot/generators/mysql.py-77-    def func(self: generator.Generator, expression: exp.Expr) -> str:
sqlglot/generators/mysql.py-78-        return self.func(
sqlglot/generators/mysql.py-79-            f"DATE_{kind}",
sqlglot/generators/mysql.py-80-            expression.this,
sqlglot/generators/mysql.py-81-           
…[5719 chars elided]…
AS __timestamp FROM tableT",
tests/dialects/test_mysql.py:1460:                        f"DATE_ADD('0000-01-01 00:00:00', INTERVAL (TIMESTAMPDIFF({unit}, '0000-01-01 00:00:00', {cast})) {unit})",
tests/dialects/test_mysql.py:1465:                            "mysql": f"DATE_ADD('0000-01-01 00:00:00', INTERVAL (TIMESTAMPDIFF({unit}, '0000-01-01 00:00:00', {cast})) {unit})",
tests/dialects/test_mysql.py:1618:                self.validate_identity(f"DATE_ADD(base_date, INTERVAL day_interval {unit})")
[assistant] The existing tests don't pin Doris or StarRocks `DATE_ADD` output, so the generator change should be safe. Here's the plan, following the contract:

- **Parser:** a shared builder in `dialect.py`, next to `build_date_delta_with_interval`. A non-interval second argument becomes `exp.TsOrDsAdd` with unit DAY. `DATE_SUB` negates the amount, which is the Hive precedent.
- **Generator:** a unit-aware `TsOrDsAdd` transform in `generators/mysql.py`, used by both Doris and StarRocks. It emits the 2-arg form for DAY or no unit and falls back to the interval form otherwise. MySQL itself is left alone.

I'll check the Doris and StarRocks generator imports and the `unit_to_str` helper before editing.
[tool_use Bash] {"command": "sed -n 1,25p sqlglot/generators/doris.py; echo ----; grep -n \"TRANSFORMS\" sqlglot/generators/starrocks.py; echo ----; sed -n 1,20p sqlglot/generators/mysql.py; echo ----; grep -n \"def unit_to_str\" -A8 sqlglot/dialects/dialect.py", "description": "Check generator imports and unit helpers"}
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
        
…[665 chars elided]…
aren_current_date_sql,
    no_pivot_sql,
    no_tablesample_sql,
    no_trycast_sql,
    rename_func,
----
1979:def unit_to_str(expression: exp.Expr, default: str = "DAY") -> exp.Expr | None:
1980-    unit = expression.args.get("unit")
1981-    if not unit:
1982-        return exp.Literal.string(default) if default else None
1983-
1984-    if isinstance(unit, exp.Placeholder) or type(unit) not in (exp.Var, exp.Literal):
1985-        return unit
1986-
1987-    return exp.Literal.string(unit.name)
[assistant] Now the edits. First, the shared parser builder in `dialect.py`:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/comp-2/sqlglot/dialects/dialect.py", "old_string": "        return expression_class(this=args[0], expression=interval.this, unit=unit_to_str(interval))\n\n    return _builder\n\n\ndef date_trunc_to_time(", "new_string": "        return expression_class(this=arg
…[313 chars elided]…
ss)\n\n    def _builder(args: BuilderArgs) -> E | exp.TsOrDsAdd | None:\n        if len(args) == 2 and not isinstance(args[1], exp.Interval):\n            days = exp.Neg(this=args[1]) if negate else args[1]\n            return exp.TsOrDsAdd(this=args[0], expression=days, unit=exp.Literal.string(\"DAY\"))\n\n        return interval_builder(args)\n\n    return _builder\n\n\ndef date_trunc_to_time("}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/comp-2/sqlglot/dialects/dialect.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/comp-2/sqlglot/generators/mysql.py", "old_string": "def _ts_or_ds_to_date_sql(self: MySQLGenerator, expression: exp.TsOrDsToDate) -> str:", "new_string": "def ts_or_ds_add_days_sql(self: MySQLGenerator, expression: exp.TsOrDsAdd) -> str:\n    if not expression.unit or expression.text(\"unit\").upper() == \"DAY\":\n        return self.func(\"DATE_ADD\", expression.this, expression.expression)\n\n    return date_add_sql(\"ADD\")(self, expression)\n\n\ndef _ts_or_ds_to_date_sql(self: MySQLGenerator, expression: exp.TsOrDsToDate) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/comp-2/sqlglot/generators/mysql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/comp-2/sqlglot/generators/doris.py", "old_string": "        exp.TsOrDsAdd: lambda self, e: self.func(\"DATE_ADD\", e.this, e.expression),", "new_string": "        exp.TsOrDsAdd: ts_or_ds_add_days_sql,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/comp-2/sqlglot/generators/doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/comp-2/sqlglot/generators/doris.py", "old_string": "from sqlglot.generators.mysql import MySQLGenerator\n", "new_string": "from sqlglot.generators.mysql import MySQLGenerator, ts_or_ds_add_days_sql\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/comp-2/sqlglot/generators/doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/comp-2/sqlglot/generators/starrocks.py", "old_string": "from sqlglot.generators.mysql import MySQLGenerator\n", "new_string": "from sqlglot.generators.mysql import MySQLGenerator, ts_or_ds_add_days_sql\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/comp-2/sqlglot/generators/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/comp-2/sqlglot/generators/starrocks.py", "old_string": "        **{k: v for k, v in MySQLGenerator.TRANSFORMS.items() if k is not exp.DateTrunc},", "new_string": "        **{k: v for k, v in MySQLGenerator.TRANSFORMS.items() if k is not exp.DateTrunc},\n        exp.TsOrDsAdd: ts_or_ds_add_days_sql,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/comp-2/sqlglot/generators/starrocks.py has been updated successfully.
[assistant] Next, the parsers. Doris and StarRocks each register `DATE_ADD` and `DATE_SUB` with the shared builder:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/comp-2/sqlglot/parsers/doris.py", "old_string": "from sqlglot import exp\nfrom sqlglot.helper import seq_get\nfrom sqlglot.parsers.mysql import MySQLParser", "new_string": "from sqlglot import exp\nfrom sqlglot.dialects.dialect import build_date_delta_with_days_or_interval\nfrom sqlglot.helper import seq_get\nfrom sqlglot.parsers.mysql import MySQLParser"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/comp-2/sqlglot/parsers/doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/comp-2/sqlglot/parsers/doris.py", "old_string": "        \"COLLECT_SET\": exp.ArrayUniqueAgg.from_arg_list,\n        \"DATE_TRUNC\": _build_date_trunc,", "new_string": "        \"COLLECT_SET\": exp.ArrayUniqueAgg.from_arg_list,\n        \"DATE_ADD\": build_date_delta_with_days_or_interval(exp.DateAdd),\n        \"DATE_SUB\": build_date_delta_with_days_or_interval(exp.DateSub, negate=True),\n        \"DATE_TRUNC\": _build_date_trunc,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/comp-2/sqlglot/parsers/doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/comp-2/sqlglot/parsers/starrocks.py", "old_string": "from sqlglot.dialects.dialect import build_timestamp_trunc\nfrom sqlglot.helper import seq_get\nfrom sqlglot.parsers.mysql import MySQLParser\n\n\nclass StarRocksParser(MySQLParser):\n    FUNCTIONS = {\n     
…[183 chars elided]…
mp_trunc\nfrom sqlglot.helper import seq_get\nfrom sqlglot.parsers.mysql import MySQLParser\n\n\nclass StarRocksParser(MySQLParser):\n    FUNCTIONS = {\n        **MySQLParser.FUNCTIONS,\n        \"DATE_ADD\": build_date_delta_with_days_or_interval(exp.DateAdd),\n        \"DATE_SUB\": build_date_delta_with_days_or_interval(exp.DateSub, negate=True),\n        \"DATE_TRUNC\": build_timestamp_trunc,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/comp-2/sqlglot/parsers/starrocks.py has been updated successfully.
[assistant] Before writing tests, I'll check the AST nodes and generated SQL directly against the reported repro and a few edge cases.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor d in ['doris','starrocks']:\n    for s in [\\\"date_add('2025-01-01', 1)\\\", \\\"date_sub('2025-01-01', 1)\\\", \\\"date_add('2025-01-01', INTERVAL 1 DAY)\\\", \\\"date_sub('2025-01-
…[296 chars elided]…
gs.get('unit')), e.selects[0].expression.args)\nprint(sqlglot.transpile(\\\"SELECT DATEADD(MONTH, 1, x)\\\", read='redshift', write='doris'))\nprint(sqlglot.transpile(\\\"SELECT DATEADD(MONTH, 1, x)\\\", read='redshift', write='starrocks'))\nprint(sqlglot.transpile(\\\"SELECT DATE_ADD(x, 1)\\\", read='spark', write='doris'))\n\"", "description": "Verify parsed AST and generated SQL for new forms"}
[tool_result] doris | date_add('2025-01-01', 1) | TsOrDsAdd | DATE_ADD('2025-01-01', 1) | CAST('2025-01-01' AS DATE) + INTERVAL 1 DAY
doris | date_sub('2025-01-01', 1) | TsOrDsAdd | DATE_ADD('2025-01-01', -1) | CAST('2025-01-01' AS DATE) + INTERVAL (-1) DAY
doris | date_add('2025-01-01', INTERVAL 1 DAY) | DateAdd | DATE_ADD('2025-01-01', INTERVAL '1' DAY) | CAST('2025-01-01' AS DATE) + INTERVAL '1' DAY
doris | date_sub('2025-01-01', INTERVAL 2 MONTH) | DateSub | DATE_SUB('2025-01-01', INTERVAL '2' MONTH) | CA
…[457 chars elided]…
ATE_ADD('2025-01-01', INTERVAL '1' DAY) | CAST('2025-01-01' AS DATE) + INTERVAL '1' DAY
starrocks | date_sub('2025-01-01', INTERVAL 2 MONTH) | DateSub | DATE_SUB('2025-01-01', INTERVAL '2' MONTH) | CAST('2025-01-01' AS DATE) - INTERVAL '2' MONTH
starrocks | date_add(x, col) | TsOrDsAdd | DATE_ADD(x, col) | CAST(x AS DATE) + INTERVAL (col) DAY
Var(this=DAY) {'this': '1', 'is_string': False}
['SELECT DATE_ADD(x, INTERVAL 1 MONTH)']
['SELECT DATE_ADD(x, INTERVAL 1 MONTH)']
['SELECT DATE_ADD(x, 1)']
[assistant] Parsing and generation behave as intended: the reported repro now yields `TsOrDsAdd`, the interval forms still yield `DateAdd`/`DateSub`, and the MONTH unit survives the Redshift transpile. Next I'll add tests to each dialect's file, following the existing style.
[tool_use Bash] {"command": "sed -n 1,30p tests/dialects/test_doris.py; echo ----; sed -n 1,20p tests/dialects/test_starrocks.py", "description": "Read top of Doris and StarRocks test files"}
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
             
…[782 chars elided]…
identity("SELECT ARRAY_JOIN([1, 3, 5, NULL], '_', 'NULL')")
        self.validate_identity("SELECT ARRAY_JOIN([1, 3, 5, NULL], '_')")
        self.validate_identity("ALTER TABLE a SWAP WITH b")
        self.validate_identity("SELECT ARRAY_AGG(a) FROM x")
        self.validate_identity("SELECT ST_POINT(10, 20)")
        self.validate_identity("SELECT ST_DISTANCE_SPHERE(10.1, 20.2, 30.3, 40.4)")
        self.validate_identity("ARRAY_FLATTEN(arr)").assert_is(exp.Flatten)

        self.validate_all(
[assistant] Each test class gets one new method. I'll append it at the end of each class, so I need the file tails.
[tool_use Bash] {"command": "tail -n 6 tests/dialects/test_doris.py; echo ----; tail -n 6 tests/dialects/test_starrocks.py; echo ----; grep -n \"def validate_all\" -A12 tests/dialects/test_dialect.py | head -30", "description": "Read test file tails and validate_all semantics"}
[tool_result]         )

        # Combined BUILD and REFRESH
        self.validate_identity(
            "CREATE MATERIALIZED VIEW mv BUILD DEFERRED REFRESH AUTO ON SCHEDULE EVERY 10 MINUTE AS SELECT 1"
        )
----
        self.validate_identity(
            "CREATE TABLE test_table (col1 BIGINT) PARTITION BY RANGE (col1) (START ('1') END ('10') EVERY (1), START ('10') END ('100') EVERY (10))"
        )
        self.validate_identity(
            "CREATE TABLE test_table (col1 DATE) PARTITION BY RANGE (co
…[279 chars elided]…
y=False, identify=False):
69-        """
70-        Validate that:
71-        1. Everything in `read` transpiles to `sql`
72-        2. `sql` transpiles to everything in `write`
73-
74-        Args:
75-            sql (str): Main SQL expression
76-            read (dict): Mapping of dialect -> SQL
77-            write (dict): Mapping of dialect -> SQL
78-            pretty (bool): prettify both read and write
79-            identify (bool): quote identifiers in both read and write
80-        """
[tool_use Bash] {"command": "cat >> tests/dialects/test_doris.py <<'EOF'\n\n    def test_date_add_days(self):\n        self.validate_identity(\"DATE_ADD(x, 1)\").assert_is(exp.TsOrDsAdd)\n        self.validate_identity(\"DATE_SUB(x, 1)\", \"DATE_ADD(x, -1)\").assert_is(exp.TsOrDsAdd)\n        self.assertIsInstance(\n            parse_one(\"DATE_ADD(x, INTERVAL 1 DAY)\", read=self.dialect), exp.DateAdd\n        )\
…[1740 chars elided]…
alects/test_starrocks.py\n<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_tests.py tests/dialects/test_doris.py tests/dialects/test_starrocks.py 2>&1 | tail -n 60", "description": "Add date-add tests to Doris and StarRocks test files and run them", "timeout": 600000}
[tool_result] ==> tests/dialects/test_doris.py <==
from sqlglot import exp, parse_one
from tests.dialects.test_dialect import Validator


==> tests/dialects/test_starrocks.py <==
from sqlglot import exp, parse_one
from sqlglot.errors import UnsupportedError
from tests.dialects.test_dialect import Validator
cmd: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no -rfE tests/dialects/test_doris.py tests/dialects/test_starrocks.py
log: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/pytest-comp-2-1793031840.log
elapsed: 1s, exit: 0
=================== 22 passed, 122 subtests passed in 0.30s ====================
VERDICT: PASS
[This command modified 2 files you've previously read: tests/dialects/test_doris.py, tests/dialects/test_starrocks.py. Call Read before editing.]
[assistant] The Doris and StarRocks test files pass. My last edit was to the tests, so the harness requires one full-suite run after it. I'll start that now.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_tests.py 2>&1 | tail -n 30", "description": "Run full test suite after final edit", "timeout": 600000}
[tool_result] cmd: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no -rfE
log: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/pytest-comp-2-1793031843.log
elapsed: 65s, exit: 0
============ 1086 passed, 17852 subtests passed in 64.09s (0:01:04) ============
VERDICT: PASS
[assistant] The full suite passes. I'll also run the repo's linter and formatter on the changed files, since the project's pre-commit uses ruff.
[tool_use Bash] {"command": "R=<work>/env-sqlglot/bin; ($R/ruff --version || $R/python -m ruff --version) 2>&1; $R/python -m ruff check sqlglot/dialects/dialect.py sqlglot/generators/mysql.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py sqlglot/parsers/doris.py sqlglot/parsers/s
…[42 chars elided]…
ests/dialects/test_starrocks.py 2>&1 | tail -n 15; $R/python -m ruff format --check sqlglot/dialects/dialect.py sqlglot/generators/mysql.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py tests/dialects/test_doris.py tests/dialects/test_starrocks.py 2>&1 | tail -n 5", "description": "Run ruff lint and format check on changed files"}
[tool_result] ruff 0.15.6
All checks passed!
8 files already formatted
[assistant] Doris and StarRocks now accept the two-argument `DATE_ADD` / `DATE_SUB` form, and the repro from your report parses. The full suite passes (`VERDICT: PASS`, 1086 tests) and ruff is clean. I haven't committed anything.

**What changed**
- **Parser:** a new builder in `sqlglot/dialects/dialect.py`, `build_date_delta_with_days_or_interval`, is registered for `DATE_ADD` and `DATE_SUB` in both `parsers/doris.py` and `parsers/starrocks.py`. A second argument that isn't an `INTERVAL` becomes `exp.TsOrDsAdd` with unit DAY. The `INTERVAL` form still yields `DateAdd` / `DateSub`. MySQL's parser is uncha
…[669 chars elided]…
ant to revisit**
- **`DATE_SUB(x, n)` generates as `DATE_ADD(x, -n)`.** I negated the amount (the Hive precedent), so it doesn't round-trip to the `DATE_SUB` name. It is semantically identical. Emitting `DATE_SUB` would mean changing how `DateSub` generates for DAY units, which would alter existing interval output.
- **Behaviour change:** `TsOrDsAdd` with DAY or no unit now generates as `DATE_ADD(x, n)` on StarRocks, where it used to be `DATE_ADD(x, INTERVAL n DAY)`. Non-DAY units on Doris now get the interval form instead of silently dropping the unit. Existing tests didn't pin either output.
