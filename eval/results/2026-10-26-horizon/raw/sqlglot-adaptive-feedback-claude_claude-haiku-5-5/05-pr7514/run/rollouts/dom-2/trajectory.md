# trajectory dom-2

final message:
Doris and StarRocks now parse and generate the two-argument `DATE_ADD` / `DATE_SUB` form. The full suite passes (1086 tests), and ruff is clean. I haven't committed anything.

**What changed**
- **Parser:** a new shared builder, `build_date_delta_with_interval_or_days` in `sqlglot/dialects/dialect.py`, is wired into the Doris and StarRocks parsers for `DATE_ADD` and `DATE_SUB`. A second argument that isn't an `INTERVAL` becomes `exp.TsOrDsAdd` with unit `DAY`. The INTERVAL form still produces `DateAdd`/`DateSub`.
- **`DATE_SUB` days form:** the days are negated (`DATE_SUB(x, 1)` becomes `TsOrDsAdd` with `-1`), so it generates as `DATE_ADD(x, -1)`. That text doesn't round-trip exactly, but it's the same as Hive's handling.
- **Generator:** `date_add_days_sql` in `sqlglot/generators/mysql.py` is used for `TsOrDsAdd` in Doris and StarRocks. A DAY or missing unit emits `DATE_ADD(d, n)`. Any other unit falls back to the INTERVAL form.
- **Tests:** `test_date_add_days` in `tests/dialects/test_doris.py` and `tests/dialects/test_starrocks.py` checks the node class and the output for both forms, and a Redshift `DATEADD(MONTH, 1, x)` case.

**Bug fixed along the way:** Doris's old `TsOrDsAdd` transform ignored the unit, so `DATEADD(MONTH, 1, x)` from Redshift came out as `DATE_ADD(x, 1)`. It now keeps the MONTH unit.

**Things to check before merging**
- **StarRocks output changes:** any `TsOrDsAdd` with a DAY unit that transpiles into StarRocks now emits the two-argument form. Previously it emitted `DATE_ADD(x, INTERVAL n DAY)`. For example, Spark `DATE_ADD(x, 1)` → StarRocks now gives `DATE_ADD(x, 1)`. The full suite passes, but this is a visible output change.
- **StarRocks 2-argument support:** I took this from your description and did not check StarRocks's docs.
- **MySQL is unchanged:** it still rejects the two-argument form, as before.

## events
[tool_use Skill] {"skill": "sqlglot-date-arithmetic"}
[tool_result] Launching skill: sqlglot-date-arithmetic
[user] Base directory for this skill: ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-2/.claude/skills/sqlglot-date-arithmetic

# Date arithmetic in sqlglot: which node, and how generators must treat it

Use together with `sqlglot-dialect-functions` (general parse/generate contract).

## Node map (verified in source)
| SQL shape | node | built by / precedent |
|---|---|---|
| `DATE_ADD(d, INTERVAL n UNIT)` / `DATE_SUB(...)` | `exp.DateAdd` / `exp.DateSub`, unit from the interval | `build_date_delta_with_interval` in `sqlglot/dialects/dialect.p
…[3303 chars elided]…
d`, but `StarRocksGenerator`
   inherits MySQL's interval form. Both subclass `MySQLGenerator`/`MySQLParser`.
3. Tests in `tests/dialects/test_<d>.py` for each dialect:
   - Assert the node class (`validate_identity(...).assert_is(exp.X)`). Import `exp` if the file
     doesn't already, as `test_doris.py` didn't.
   - Cover both the new form and the old INTERVAL form.
   - Add a `validate_all` transpiling a non-DAY unit into the dialect.
   - In these MySQL-family dialects, `INTERVAL 1 DAY` generates as `INTERVAL '1' DAY`. Write
     identity expectations for interval forms with that in mind.

[tool_use Bash] {"command": "grep -n -i \"date_add\\|dateadd\\|DateAdd\\|date_sub\\|DateSub\" sqlglot/parsers/doris.py sqlglot/generators/doris.py sqlglot/parsers/starrocks.py sqlglot/generators/starrocks.py sqlglot/dialects/doris.py sqlglot/dialects/starrocks.py sqlglot/dialects/mysql.py sqlglot/parsers/mysql.py sqlglot/generators/mysql.py", "description": "Load skill and grep Doris/StarRocks date functions"}
[tool_result] sqlglot/generators/doris.py:75:        exp.TsOrDsAdd: lambda self, e: self.func("DATE_ADD", e.this, e.expression),
sqlglot/generators/doris.py:184:        "date_add",
sqlglot/generators/doris.py:188:        "date_sub",
sqlglot/generators/doris.py:189:        "dateadd",
sqlglot/generators/mysql.py:10:    date_add_interval_sql,
sqlglot/generators/mysql.py:74:def date_add_sql(
sqlglot/generators/mysql.py:151:        exp.DateAdd: _remove_ts_or_ds_to_date(date_add_sql("ADD")),
sqlglot/generators/mysq
…[213 chars elided]…
exp.TimestampSub: date_add_interval_sql("DATE", "SUB"),
sqlglot/generators/mysql.py:209:        exp.TsOrDsAdd: date_add_sql("ADD"),
sqlglot/generators/mysql.py:742:        dateadd = build_date_delta_with_interval(exp.DateAdd)([start_ts, interval])
sqlglot/generators/mysql.py:744:        return self.sql(dateadd)
sqlglot/parsers/mysql.py:114:        "DATE_ADD": build_date_delta_with_interval(exp.DateAdd),
sqlglot/parsers/mysql.py:119:        "DATE_SUB": build_date_delta_with_interval(exp.DateSub),
[assistant] The skill's reference confirms the plan: a parser branch on arg count, a unit-aware `TsOrDsAdd` generator, and tests for both forms. Next I'll read the Doris and StarRocks parser and generator files and the shared builder.
[tool_use Bash] {"command": "ls sqlglot/parsers | grep -i \"doris\\|starrocks\\|mysql\"; ls sqlglot/generators | grep -i \"doris\\|starrocks\\|mysql\"; cat sqlglot/parsers/doris.py; cat sqlglot/parsers/starrocks.py; cat sqlglot/generators/starrocks.py; sed -n 1,260p sqlglot/generators/doris.py", "description": "Show Doris and StarRocks parser and generator sources"}
[tool_result] doris.py
mysql.py
starrocks.py
doris.py
mysql.py
starrocks.py
from __future__ import annotations


from sqlglot import exp
from sqlglot.helper import seq_get
from sqlglot.parsers.mysql import MySQLParser
from sqlglot.tokens import TokenType


# Accept both DATE_TRUNC(datetime, unit) and DATE_TRUNC(unit, datetime)
def _build_date_trunc(args: list[exp.Expr]) -> exp.Expr:
    a0, a1 = seq_get(args, 0), seq_get(args, 1)

    def _is_unit_like(e: exp.Expr | None) -> bool:
        if not (isinstance(e
…[26295 chars elided]…
    "errors",
        "events",
        "every",
        "except",
        "exclude",
        "execute",
        "exists",
        "expired",
        "explain",
        "export",
        "extended",
        "external",
        "extract",
        "failed_login_attempts",
        "false",
        "fast",
        "feature",
        "fields",
        "file",
        "filter",
        "first",
        "float",
        "follower",
        "following",
        "for",
        "foreign",
        "force",
[tool_use Bash] {"command": "grep -n \"def build_date_delta_with_interval\" -A 25 sqlglot/dialects/dialect.py; grep -n \"def build_date_delta\\b\" -A 30 sqlglot/dialects/dialect.py | head -50; grep -n \"DATE_ADD\\|_build_date_add\\|def _build_dateadd\" -A 12 sqlglot/parsers/hive.py | head -60; sed -n 60,80p sqlglot/generators/mysql.py; sed -n 100,125p sqlglot/parsers/mysql.py; sed -n 140,160p sqlglot/generators/mysql.py; sed -n 185,212p sqlglot/generators/mysql.py", "description": "Show shared date builders and MySQL date handling"}
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
…[7284 chars elided]…
meToStr: _remove_ts_or_ds_to_date(
            lambda self, e: self.func("DATE_FORMAT", e.this, self.format_time(e))
        ),
        exp.Trim: trim_sql,
        exp.Trunc: rename_func("TRUNCATE"),
        exp.TryCast: no_trycast_sql,
        exp.TsOrDsAdd: date_add_sql("ADD"),
        exp.TsOrDsDiff: lambda self, e: self.func("DATEDIFF", e.this, e.expression),
        exp.TsOrDsToDate: _ts_or_ds_to_date_sql,
        exp.Unicode: lambda self, e: f"ORD(CONVERT({self.sql(e.this)} USING utf32))",
[assistant] The parser and generator layout is clear. Before designing the change I need three things: the existing Doris and StarRocks tests that cover `DATE_ADD`/`TsOrDsAdd` (so I don't break them), how `unit_to_str` behaves, and the MySQL `date_add_sql` output.
[tool_use Bash] {"command": "grep -n -i \"date_add\\|date_sub\\|dateadd\\|TsOrDsAdd\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_mysql.py | head -80; sed -n 74,90p sqlglot/generators/mysql.py; grep -n \"def unit_to_str\" -A 12 sqlglot/dialects/dialect.py; grep -n \"^from\\|^import\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py; grep -rn \"TsOrDsAdd\\|_dateadd_sql\" -A 6 sqlglot/generators/spark.py | head -40", "description": "Find existing date-add tests and helper signatures"}
[tool_result] tests/dialects/test_mysql.py:353:        self.validate_identity("DATE_ADD(x, INTERVAL '1' YEAR)")
tests/dialects/test_mysql.py:876:            "WITH t AS (SELECT CAST('2020-01-10' AS DATE) AS col, 5 AS num_days) SELECT DATE_ADD(col, INTERVAL num_days DAY) FROM t",
tests/dialects/test_mysql.py:878:                "mysql": "WITH t AS (SELECT CAST('2020-01-10' AS DATE) AS col, 5 AS num_days) SELECT DATE_ADD(col, INTERVAL num_days DAY) FROM t",
tests/dialects/test_mysql.py:1004:            "SELECT D
…[3873 chars elided]…
pFromParts: rename_func("MAKE_TIMESTAMP"),
sqlglot/generators/spark.py-131-            exp.TimestampSub: date_delta_to_binary_interval_op(cast=False),
sqlglot/generators/spark.py-132-            exp.DatetimeDiff: timestampdiff_sql,
sqlglot/generators/spark.py-133-            exp.TimestampDiff: timestampdiff_sql,
sqlglot/generators/spark.py-134-            exp.TryCast: lambda self, e: (
sqlglot/generators/spark.py-135-                self.trycast_sql(e) if e.args.get("safe") else self.cast_sql(e)
[assistant] No existing Doris or StarRocks tests touch `DATE_ADD` on `TsOrDsAdd`, so the risk is limited to other dialects that transpile into StarRocks. Next I'll look at the test file structure and confirm the venv that the harness uses.
[tool_use Bash] {"command": "sed -n 1,30p tests/dialects/test_doris.py; echo ----; sed -n 1,25p tests/dialects/test_starrocks.py; echo ----; tail -5 tests/dialects/test_doris.py; echo ----; tail -5 tests/dialects/test_starrocks.py; echo ----; ls <work>/env-sqlglot/bin/python 2>&1; git status --short", "description": "Inspect test file headers and venv availability"}
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
             
…[1806 chars elided]…
'100') EVERY (10))"
        )
        self.validate_identity(
            "CREATE TABLE test_table (col1 DATE) PARTITION BY RANGE (col1) (START ('2019-01-01') END ('2021-01-01') EVERY (INTERVAL 1 YEAR), START ('2021-01-01') END ('2021-05-01') EVERY (INTERVAL 1 MONTH), START ('2021-05-01') END ('2021-05-04') EVERY (INTERVAL 1 DAY))"
        )
----
<work>/env-sqlglot/bin/python
[assistant] The venv exists. Before editing, I'll reproduce the reported parse error and check the current generator output for a non-DAY unit, since that determines whether the Doris `TsOrDsAdd` transform is already wrong.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ntry:\n    sqlglot.parse('select date_add(\\'2025-01-01\\', 1) from a', dialect='doris', error_level=sqlglot.ErrorLevel.IMMEDIATE)\nexcept Exception as e: print('ERR', e)\nprint(sqlglot.transpile(\\\"SELEC
…[16 chars elided]…
 1, x)\\\", read='redshift', write='doris'))\nprint(sqlglot.transpile(\\\"SELECT DATEADD(MONTH, 1, x)\\\", read='redshift', write='starrocks'))\nprint(sqlglot.transpile(\\\"SELECT DATE_ADD(x, INTERVAL 1 DAY)\\\", read='mysql', write='starrocks'))\nprint(sqlglot.transpile(\\\"SELECT x + 1\\\", read='spark', write='doris'))\n\"", "description": "Reproduce parse error and baseline transpile outputs"}
[tool_result] ERR INTERVAL expression expected but got '1'
['SELECT DATE_ADD(x, 1)']
['SELECT DATE_ADD(x, INTERVAL 1 MONTH)']
["SELECT DATE_ADD(x, INTERVAL '1' DAY)"]
['SELECT x + 1']
[assistant] Reproduced. The parse error is as reported, and there is a second bug: Doris currently turns `DATEADD(MONTH, 1, x)` into `DATE_ADD(x, 1)`, which silently drops the unit. Changing that generator is required for this feature anyway, so I'll fix both.

Plan:
- **Parser** (`dialect.py`): a shared builder that uses the two-argument days form when arg 2 isn't an `Interval`. `DATE_SUB` negates the days, which matches the Hive precedent. Wire it into Doris and StarRocks.
- **Generator** (`mysql.py`): a unit-aware helper. A DAY or missing unit emits `DATE_ADD(d, n)`, and any other unit falls back to the interval form. Use it for Doris and StarRocks.
- **Tests**: add cases to `test_doris.py` and `test_starrocks.py`, asserting the AST node as well as the output.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-2/sqlglot/dialects/dialect.py", "old_string": "        return expression_class(this=args[0], expression=interval.this, unit=unit_to_str(interval))\n\n    return _builder\n\n\ndef date_trunc_to_time(", "new_string": "        return expression_class(this=args
…[322 chars elided]…
\n    def _builder(args: BuilderArgs) -> E | exp.TsOrDsAdd | None:\n        if len(args) == 2 and not isinstance(args[1], exp.Interval):\n            days = exp.Neg(this=args[1]) if negate_days else args[1]\n            return exp.TsOrDsAdd(this=args[0], expression=days, unit=exp.Literal.string(\"DAY\"))\n\n        return interval_builder(args)\n\n    return _builder\n\n\ndef date_trunc_to_time("}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-2/sqlglot/dialects/dialect.py has been updated successfully.
[assistant] Next, the unit-aware generator helper in `mysql.py`, placed beside `date_add_sql`:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-2/sqlglot/generators/mysql.py", "old_string": "            exp.Interval(this=expression.expression, unit=unit_to_var(expression)),\n        )\n\n    return func\n\n\n", "new_string": "            exp.Interval(this=expression.expression, unit=unit_to_var(expression)),\n        )\n\n    return func\n\n\ndef date_add_days_sql(self: MySQLGenerator, expression: exp.TsOrDsAdd) -> str:\n    if not expression.unit or expression.text(\"unit\").upper() == \"DAY\":\n        return self.func(\"DATE_ADD\", expression.this, expression.expression)\n\n    return date_add_sql(\"ADD\")(self, expression)\n\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-2/sqlglot/generators/mysql.py has been updated successfully.
[assistant] Now I'll wire up the Doris and StarRocks parsers and generators.
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\ndef edit(path, old, new, count=1):\n    s = open(path).read()\n    assert s.count(old) == count, (path, s.count(old))\n    open(path, \"w\").write(s.replace(old, new))\n\n# Doris parser\nedit(\"sqlglot/parsers/doris.py\",\n\"from sqlglot.helper import seq_get\\n\",\n\"from sqlglot.dialects.dialect import build_date_delta_with_interval_or_days\\nfrom sqlgl
…[1569 chars elided]…
 MySQLGenerator, date_add_days_sql\\n\")\nedit(\"sqlglot/generators/starrocks.py\",\n\"        exp.TimeStrToDate: rename_func(\\\"TO_DATE\\\"),\\n        exp.UnixToStr:\",\n\"        exp.TimeStrToDate: rename_func(\\\"TO_DATE\\\"),\\n        exp.TsOrDsAdd: date_add_days_sql,\\n        exp.UnixToStr:\")\nprint(\"ok\")\nEOF\ngit diff --stat", "description": "Apply parser and generator wiring edits"}
[tool_result] ok
 sqlglot/dialects/dialect.py     | 15 +++++++++++++++
 sqlglot/generators/doris.py     |  4 ++--
 sqlglot/generators/mysql.py     |  7 +++++++
 sqlglot/generators/starrocks.py |  3 ++-
 sqlglot/parsers/doris.py        |  3 +++
 sqlglot/parsers/starrocks.py    |  4 +++-
 6 files changed, 32 insertions(+), 4 deletions(-)
[assistant] Wiring is in. Next I'll check the AST nodes and the generated SQL for both dialects, including the non-DAY unit and DATE_SUB cases.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor d in ['doris','starrocks']:\n    for s in [\\\"select date_add('2025-01-01', 1) from a\\\", \\\"select date_sub('2025-01-01', 1) from a\\\", \\\"select date_add('2025-01-01', 
…[462 chars elided]…
 DATEADD(MONTH, 1, x)\\\", read='redshift', write='starrocks'))\nprint(sqlglot.transpile(\\\"SELECT DATE_ADD(x, 1)\\\", read='spark', write='starrocks'))\nprint(sqlglot.transpile(\\\"SELECT DATE_SUB(x, 1)\\\", read='hive', write='doris'))\nprint(sqlglot.transpile(\\\"SELECT DATE_ADD(x, 1)\\\", read='mysql', write='doris'))\n\"", "description": "Check AST nodes and generated SQL for both dialects"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 14, in <module>
  File "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-2/sqlglot/__init__.py", line 212, in transpile
    for expression in parse(sql, read, error_level=error_level)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-2/sqlglot/
…[8189 chars elided]…
, 1) FROM a
starrocks TsOrDsAdd | SELECT DATE_ADD('2025-01-01', -1) FROM a
starrocks DateAdd | SELECT DATE_ADD('2025-01-01', INTERVAL '1' DAY) FROM a
starrocks DateSub | SELECT DATE_SUB(x, INTERVAL '2' MONTH) FROM a
TsOrDsAdd(
  this=Literal(this='2025-01-01', is_string=True),
  expression=Neg(
    this=Literal(this=1, is_string=False)),
  unit=Var(this=DAY))
['SELECT DATE_ADD(x, INTERVAL 1 MONTH)']
['SELECT DATE_ADD(x, INTERVAL 1 MONTH)']
['SELECT DATE_ADD(x, 1)']
['SELECT DATE_ADD(x, 1 * -1)']
[assistant] The core behavior works in both dialects:
- The 2-argument form parses to `TsOrDsAdd` and round-trips.
- The INTERVAL form still parses to `DateAdd`/`DateSub`.
- `DATEADD(MONTH, 1, x)` now keeps the MONTH unit in Doris.

The `ParseError` at the end is from my own check, not a regression: MySQL is not one of the target dialects and still requires `INTERVAL`, which is correct. Next I'll confirm the `validate_identity` signature before writing the tests.
[tool_use Bash] {"command": "grep -n \"def validate_identity\\|def validate_all\" -A 4 tests/dialects/test_dialect.py", "description": "Check Validator helper signatures"}
[tool_result] 53:    def validate_identity(
54-        self, sql, write_sql=None, pretty=False, check_command_warning=False, identify=False
55-    ):
56-        if check_command_warning:
57-            with self.assertLogs(parser_logger) as cm:
--
68:    def validate_all(self, sql, read=None, write=None, pretty=False, identify=False):
69-        """
70-        Validate that:
71-        1. Everything in `read` transpiles to `sql`
72-        2. `sql` transpiles to everything in `write`
[assistant] Now the tests. I'm adding one method per dialect that asserts the AST node, covers the two-argument and INTERVAL forms, and checks that a non-DAY unit keeps its unit. Doris needs an `exp` import added.
[tool_use Bash] {"command": "python3 - <<'EOF'\ndef edit(path, old, new):\n    s = open(path).read()\n    assert s.count(old) == 1, (path, s.count(old))\n    open(path, \"w\").write(s.replace(old, new))\n\nedit(\"tests/dialects/test_doris.py\",\n\"from tests.dialects.test_dialect import Validator\\n\",\n\"from sqlglot import exp\\nfrom tests.dialects.test_dialect import Validator\\n\")\n\ns = open(\"tests/dialect
…[1402 chars elided]…
st_starrocks.py\", \"w\").write(s)\nprint(\"ok\")\nEOF\nPY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_doris.py tests/dialects/test_starrocks.py 2>&1 | tail -40", "description": "Add Doris and StarRocks tests and run them"}
[tool_result] ok
......................       [100%]
22 passed, 116 subtests passed in 0.26s
[assistant] Both dialect test files pass. Now the full suite, since I changed the shared `dialect.py` and `mysql.py` modules and the StarRocks output for `TsOrDsAdd` affects other dialects' transpilation:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -40", "description": "Run full project test suite"}
[tool_result] Command did not complete within its 120s timeout and was moved to the background (ID: bu6tttvan). Output is being written to: /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-55c905b0df68-20261026-160938-doris-and-starrocks-dialects-bot-dom-2/696f4dfc-27fe-4a1d-8080-98f4a29de589/tasks/bu6tttvan.output. You will be notified when it completes. If it is still running after 10m in the background, it will be stopped and you will be notified. To check interim output, use Read on that file path.
[assistant] The full suite is still running in the background. Meanwhile I'll run the linter and formatter on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; FILES=\"sqlglot/dialects/dialect.py sqlglot/generators/mysql.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py tests/dialects/test_doris.py tests/dialects/test_starrocks.py\"; ($PY -m ruff check $FILES && $PY -m ruff format --check $FILES) 2>&1 | tail -20", "description": "Run ruff lint and format check on changed files"}
[tool_result] E902 No such file or directory (os error 2)
--> sqlglot/dialects/dialect.py sqlglot/generators/mysql.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py tests/dialects/test_doris.py tests/dialects/test_starrocks.py:1:1

Found 1 error.
[assistant] The linter failed only because zsh doesn't word-split the unquoted variable, so it saw one long filename. I'll pass the paths explicitly.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff check sqlglot/dialects/dialect.py sqlglot/generators/mysql.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py tests/dialects/test_doris.py tests/dialects/test_starrocks.py 2>&1 | tail -20; $PY -m ruff format --check sqlglot/dialects/dialect.py sqlglot/generators/mysql.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py tests/dialects/test_doris.py tests/dialects/test_starrocks.py 2>&1 | tail -20", "description": "Run ruff check and format check on changed files"}
[tool_result] All checks passed!
8 files already formatted
[tool_use Bash] {"command": "sleep 60; cat /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-55c905b0df68-20261026-160938-doris-and-starrocks-dialects-bot-dom-2/696f4dfc-27fe-4a1d-8080-98f4a29de589/tasks/bu6tttvan.output | tail -30", "description": "Check background full test run output"}
[tool_result ERROR] <tool_use_error>Blocked: sleep 60 followed by: cat /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-55c905b0df68-20261026-160938-doris-and-starrocks-dialects-bot-dom-2/696f4dfc-27fe-4a1d-8080-98f4a29de589/tasks/bu6tttvan.output tail -30. To wait for a condition, use Monitor with an until-loop (e.g. `until <check>; do sleep 2; done`). To wait for a command you started, use run_in_background: true. Do not chain shorter sleeps to work around this block.</tool_use_error>
[tool_use Read] {"file_path": "/private/tmp/claude-501/-Users-user--cache-lithify-work-repo-55c905b0df68-20261026-160938-doris-and-starrocks-dialects-bot-dom-2/696f4dfc-27fe-4a1d-8080-98f4a29de589/tasks/bu6tttvan.output"}
[tool_result] 1	................................................................................. [  7%]
2	............................................. [ 11%]
3	...................................................... [ 16%]
4	........ [ 17%]
5	................................ [ 20%]
6	....................................................................................................................................................................................................................................
…[358 chars elided]…
. [ 68%]
13	............................................... [ 72%]
14	........................................................... [ 78%]
15	....................................................................................................................................... [ 90%]
16	............................... [ 93%]
17	......................................................................     [100%]
18	1086 passed, 17846 subtests passed in 133.87s (0:02:13)
19	
20	[exited with code 0]
21	
[assistant] Doris and StarRocks now parse and generate the two-argument `DATE_ADD` / `DATE_SUB` form. The full suite passes (1086 tests), and ruff is clean. I haven't committed anything.

**What changed**
- **Parser:** a new shared builder, `build_date_delta_with_interval_or_days` in `sqlglot/dialects/dialect.py`, is wired into the Doris and StarRocks parsers for `DATE_ADD` and `DATE_SUB`. A second argument that isn't an `INTERVAL` becomes `exp.TsOrDsAdd` with unit `DAY`. The INTERVAL form still produces `DateAdd`/`DateSub`.
- **`DATE_SUB` days form:** the days are negated (`DATE_SUB(x, 1)` becomes `TsOrD
…[664 chars elided]…
shift came out as `DATE_ADD(x, 1)`. It now keeps the MONTH unit.

**Things to check before merging**
- **StarRocks output changes:** any `TsOrDsAdd` with a DAY unit that transpiles into StarRocks now emits the two-argument form. Previously it emitted `DATE_ADD(x, INTERVAL n DAY)`. For example, Spark `DATE_ADD(x, 1)` → StarRocks now gives `DATE_ADD(x, 1)`. The full suite passes, but this is a visible output change.
- **StarRocks 2-argument support:** I took this from your description and did not check StarRocks's docs.
- **MySQL is unchanged:** it still rejects the two-argument form, as before.
