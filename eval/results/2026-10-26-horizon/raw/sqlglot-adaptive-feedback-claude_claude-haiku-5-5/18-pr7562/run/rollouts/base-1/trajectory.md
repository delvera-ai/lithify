# trajectory base-1

final message:
`MODIFY COLUMN` in the MySQL dialect now parses into a real column definition, and all four examples round-trip. The full suite passed after my last edit: `SUMMARY: 1094 passed, 17872 subtests passed in 48.96s`, `EXIT: 0`. The changes are uncommitted in the worktree.

**What changed**

- **Parser** (`sqlglot/parsers/mysql.py`): `MODIFY` now goes to a new `_parse_alter_table_modify`. It takes an optional `COLUMN`, parses a full column definition (type, constraints, `COMMENT`), and then an optional `FIRST` or `AFTER col`. If it can't find a column definition, it falls back to a raw `Command`, as before.
- **New node** (`sqlglot/expressions/ddl.py`): `AlterModifyColumn(this=ColumnDef)`. I used a separate node rather than `ADD`-style actions, because the base `alter_sql` would otherwise emit `ADD`.
- **Shared helper** (`sqlglot/parser.py`): the FIRST/AFTER parsing moved out of `_parse_add_column` into `_parse_column_position()`, so ADD and MODIFY share it. ADD behaviour is unchanged.
- **MySQL generator** (`sqlglot/generators/mysql.py`): `altermodifycolumn_sql` emits `MODIFY COLUMN <column def>`, position included.
- **Base generator** (`sqlglot/generator.py`): other dialects get the old lossy output. Transpiling to Postgres gives `ALTER TABLE t ALTER COLUMN c SET DATA TYPE INT` and emits an "unsupported" warning. Without this, transpiling raised `ValueError`, which would have been a regression.
- **Tests** (`tests/dialects/test_mysql.py`): identity tests for the four examples, plus an assertion that the parsed action is `exp.AlterModifyColumn`.

**Left as-is**

- The existing `ALTER COLUMN ... SET DATA TYPE` → `MODIFY COLUMN` transpile path still uses `AlterColumn`, and its existing test still passes.
- `MODIFY COLUMN a INT, ADD COLUMN b INT` (several actions in one statement) still falls back to a raw `Command`. I did not check the pre-change output for that statement.
- I did not run mypy; only ruff check and format, which pass.

## events
[tool_use Bash] {"command": "git status --short | head && cat .lithify/harness/memory.md 2>/dev/null | head -20; grep -rn \"MODIFY\" sqlglot/parsers/mysql.py sqlglot/parser.py sqlglot/generators/mysql.py sqlglot/generators/base.py sqlglot/dialects/mysql.py | head -40", "description": "Check repo state and grep MODIFY handling"}
[tool_result] - The project's checks run with `<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no`.
- Layout: expression classes live in `sqlglot/expressions/*.py` (there is no `expressions.py`). A dialect's parser is `sqlglot/parsers/<d>.py` and its generator is `sqlglot/generators/<d>.py`; `sqlglot/dialects/<d>.py` only wires them together.
- The full suite (~1085 
…[61 chars elided]…
  `tests/test_executor.py::TestExecutor::test_execute_tpcds`; with several pytest runs competing
  for CPU it sits there for minutes and looks hung, but it is only slow. Run the dialect's own
  test file first (well under a second), then the full suite once.
ugrep: warning: sqlglot/generators/base.py: No such file or directory
sqlglot/parsers/mysql.py:255:        "MODIFY": lambda self: self._parse_alter_table_alter(),
sqlglot/generators/mysql.py:719:        return f"MODIFY COLUMN {this} {dtype}"
[tool_use Bash] {"command": "sed -n 235,275p sqlglot/parsers/mysql.py; echo ----; grep -n \"_parse_alter_table_alter\\|def _parse_alter\\|AlterColumn\\|_parse_alter_table_add\\|ALTER_PARSERS\" sqlglot/parser.py sqlglot/parsers/*.py sqlglot/generators/*.py sqlglot/expressions/*.py | head -60", "description": "Inspect MySQL ALTER parser and related helpers"}
[tool_result]         "CHARACTER SET": lambda self: self._parse_set_item_charset("CHARACTER SET"),
        "CHARSET": lambda self: self._parse_set_item_charset("CHARACTER SET"),
        "NAMES": lambda self: self._parse_set_item_names(),
    }

    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
    SET_TRIE = new_trie(key.split(" ") for key in SET_PARSERS)

    CONSTRAINT_PARSERS = {
        **parser.Parser.CONSTRAINT_PARSERS,
        "FULLTEXT": lambda self: self._parse_index_constraint(kind="F
…[5420 chars elided]…
t(self) -> exp.AlterSet:
sqlglot/parsers/tsql.py:714:    def _parse_alter_table_alter(self) -> exp.Expr | None:
sqlglot/parsers/tsql.py:715:        expression = super()._parse_alter_table_alter()
sqlglot/generators/mysql.py:713:    def altercolumn_sql(self, expression: exp.AlterColumn) -> str:
sqlglot/generators/singlestore.py:1581:    def altercolumn_sql(self, expression: exp.AlterColumn) -> str:
sqlglot/generators/spark2.py:235:    def altercolumn_sql(self, expression: exp.AlterColumn) -> str:
[tool_use Bash] {"command": "sed -n 8537,8612p sqlglot/parser.py; echo ----; sed -n 8706,8760p sqlglot/parser.py; echo ----; sed -n 225,260p sqlglot/expressions/ddl.py; echo ----; sed -n 700,725p sqlglot/generators/mysql.py; echo ----; sed -n 820,850p sqlglot/parsers/clickhouse.py; echo; sed -n 225,245p sqlglot/parsers/hive.py; echo ----; grep -n \"ColumnDef\\b\\|class ColumnDef\" sqlglot/expressions/ddl.py | head; grep -n \"def _parse_column_def\\|def _parse_column_def\\|ColumnPosition\\|FIRST\\b\" sqlglot/parser.py | head -20", "description": "Read ALTER parsing, AlterColumn expression, and MySQL generator"}
[tool_result]     def _parse_alter_table_add(self) -> list[exp.Expr]:
        def _parse_add_alteration() -> exp.Expr | None:
            self._match_text_seq("ADD")
            if self._match_set(self.ADD_CONSTRAINT_TOKENS, advance=False):
                return self.expression(
                    exp.AddConstraint(expressions=self._parse_csv(self._parse_constraint))
                )

            column_def = self._parse_add_column()
            if isinstance(column_def, exp.ColumnDef):
                ret
…[9656 chars elided]…
se "FIRST"
7036:    def _parse_column_def(
8073:            invert_order = self._prev.token_type == TokenType.FROM or self.TRIM_PATTERN_FIRST
8169:        first: bool | None = True if self._match(TokenType.FIRST) else None
8217:        # This covers Oracle's FIRST/LAST syntax: aggregate KEEP (...) OVER (...)
8489:    def _parse_column_def_with_exists(self):
8513:        if self._match_texts(("FIRST", "AFTER")):
8516:                exp.ColumnPosition(this=self._parse_column(), position=position)
[tool_use Bash] {"command": "grep -rn \"MODIFY\" tests/ | grep -v -i \"clickhouse\\|snowflake\" | head -40; echo ----; sed -n 8489,8525p sqlglot/parser.py; echo ----; grep -n \"def columnposition_sql\\|def columndef_sql\\|ColumnPosition\" -A12 sqlglot/generators/base.py sqlglot/generators/mysql.py | head -60; echo; grep -n \"def _parse_column_def\" -A40 sqlglot/parser.py | sed -n 1,50p", "description": "Find MODIFY tests and column-def/position helpers"}
[tool_result] tests/test_transpile.py:941:            "ALTER TABLE table1 MODIFY COLUMN name1 SET TAG foo='bar'",
tests/dialects/test_singlestore.py:962:        self.validate_identity("ALTER TABLE t MODIFY COLUMN name TEXT COLLATE 'binary'")
tests/dialects/test_mysql.py:40:        self.validate_identity("ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT")
tests/dialects/test_mysql.py:167:            "ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT",
----
    def _parse_column_def_with_exists
…[3095 chars elided]…
   constraints.append(in_out_constraint)
7073-            kind = self._parse_types()
7074-        elif (
7075-            kind
7076-            and self._match(TokenType.ALIAS, advance=False)
--
8489:    def _parse_column_def_with_exists(self):
8490-        start = self._index
8491-        self._match(TokenType.COLUMN)
8492-
8493-        exists_column = self._parse_exists(not_=True)
8494-        expression = self._parse_field_def()
8495-
8496-        if not isinstance(expression, exp.ColumnDef):
[tool_use Bash] {"command": "grep -rn \"ColumnPosition\\|\\\"position\\\"\" sqlglot/generators/*.py sqlglot/expressions/*.py | head; echo ----; grep -rn \"AFTER\\|FIRST\" tests/dialects/test_mysql.py | head; echo ----; grep -n \"def columndef_sql\" -A25 sqlglot/generators/generator.py 2>/dev/null | head -40; ls sqlglot/generators | head -50", "description": "Locate ColumnPosition generation and MySQL FIRST/AFTER tests"}
[tool_result] sqlglot/generators/bigquery.py:348:            e.args.get("position"),
sqlglot/generators/mysql.py:689:        position = self._prefixed_sql("FROM", expression, "position")
sqlglot/generators/oracle.py:16:    position = expression.args.get("position")
sqlglot/generators/singlestore.py:210:        exp.RegexpExtractAll: unsupported_args("position", "occurrence", "group")(
sqlglot/generators/singlestore.py:223:                e.args.get("position"),
sqlglot/generators/singlestore.py:1056:        "p
…[1844 chars elided]…
OM table1",
tests/dialects/test_mysql.py:1700:            "SELECT FIRST_VALUE(col1) RESPECT NULLS OVER (ORDER BY col2) FROM table1",
----
__init__.py
athena.py
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
python.py
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
[tool_use Bash] {"command": "grep -rn \"columnposition\\|ColumnPosition\" sqlglot/*.py sqlglot/expressions/*.py | head; grep -rn \"def columnposition_sql\" -A8 sqlglot/ | head -20; grep -rn \"ADD COLUMN.*FIRST\\|ADD.*AFTER\" tests/dialects/*.py | head -5; grep -n \"def columndef_sql\" -A30 sqlglot/generator.py | grep -n \"position\" ", "description": "Find ColumnPosition generator and test usage"}
[tool_result] sqlglot/generator.py:1136:    def columnposition_sql(self, expression: exp.ColumnPosition) -> str:
sqlglot/parser.py:8516:                exp.ColumnPosition(this=self._parse_column(), position=position)
sqlglot/expressions/query.py:497:class ColumnPosition(Expression):
sqlglot/generator.py:1136:    def columnposition_sql(self, expression: exp.ColumnPosition) -> str:
sqlglot/generator.py-1137-        this = self.sql(expression, "this")
sqlglot/generator.py-1138-        this = f" {this}" if this e
…[111 chars elided]…
        return f"{position}{this}"
sqlglot/generator.py-1141-
sqlglot/generator.py-1142-    def columndef_sql(self, expression: exp.ColumnDef, sep: str = " ") -> str:
sqlglot/generator.py-1143-        column = self.sql(expression, "this")
sqlglot/generator.py-1144-        kind = self.sql(expression, "kind")
8:1149-        position = self.sql(expression, "position")
9:1150-        position = f" {position}" if position else ""
14:1155-        return f"{exists}{column}{kind}{constraints}{position}"
[tool_use Bash] {"command": "grep -n \"def alter_sql\" -A50 sqlglot/generator.py | head -80; grep -n \"def altercolumn_sql\" -A30 sqlglot/generator.py | head -40", "description": "Read base generator alter_sql and altercolumn_sql"}
[tool_result] 3983:    def alter_sql(self, expression: exp.Alter) -> str:
3984-        actions = expression.args["actions"]
3985-
3986-        if not self.dialect.ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN and isinstance(
3987-            actions[0], exp.ColumnDef
3988-        ):
3989-            actions_sql = self.expressions(expression, key="actions", flat=True)
3990-            actions_sql = f"ADD {actions_sql}"
3991-        else:
3992-            actions_list = []
3993-            for action in actions:
399
…[2823 chars elided]…
 comment:
3921-            return f"ALTER COLUMN {this} COMMENT {comment}"
3922-
3923-        visible = expression.args.get("visible")
3924-        if visible:
3925-            return f"ALTER COLUMN {this} SET {visible}"
3926-
3927-        allow_null = expression.args.get("allow_null")
3928-        drop = expression.args.get("drop")
3929-
3930-        if not drop and not allow_null:
3931-            self.unsupported("Unsupported ALTER COLUMN syntax")
3932-
3933-        if allow_null is not None:
[tool_use Bash] {"command": "grep -n \"def _parse_field_def\" -A12 sqlglot/parser.py; grep -n \"class ColumnDef\" -A14 sqlglot/expressions/ddl.py; grep -n \"^class.*Generator\" sqlglot/generators/singlestore.py sqlglot/generators/mysql.py sqlglot/generators/starrocks.py sqlglot/generators/doris.py; grep -n \"ALTER_TABLE_ADD\" sqlglot/dialects/*.py sqlglot/dialect.py | head; sed -n 160,172p tests/dialects/test_mysql.py; sed -n 36,42p tests/dialects/test_mysql.py", "description": "Check field def parser, ColumnDef args, generator inheritance"}
[tool_result] 7033:    def _parse_field_def(self) -> exp.Expr | None:
7034-        return self._parse_column_def(self._parse_field(any_token=True))
7035-
7036-    def _parse_column_def(
7037-        self, this: exp.Expr | None, computed_column: bool = True
7038-    ) -> exp.Expr | None:
7039-        # column defs are not really columns, they're identifiers
7040-        if isinstance(this, exp.Column):
7041-            this = this.this
7042-
7043-        if not computed_column:
7044-            self._match(Tok
…[1508 chars elided]…
BLE t ADD INDEX `i` (`c`)")
        self.validate_identity("ALTER TABLE t ADD UNIQUE `i` (`c`)")
        self.validate_identity("ALTER TABLE t DROP PRIMARY KEY")
        self.validate_identity("ALTER TABLE t DROP COLUMN c, DROP PRIMARY KEY, DROP INDEX `i`")
        self.validate_identity("ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT")
        self.validate_identity("ALTER TABLE t AUTO_INCREMENT=3000000000")
        self.validate_identity("ALTER VIEW v AS SELECT a, b, c, d FROM foo")
[assistant] Current behavior is clear: MySQL routes `MODIFY` through `_parse_alter_table_alter`, which produces an `AlterColumn` with a dtype, and that drops constraints and position. The plan is a new `AlterModifyColumn` node that wraps a full `ColumnDef`, with the FIRST/AFTER parsing pulled out of `_parse_add_column` so both paths share it. I'll make the edits now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-202305-mysql-dialect-alter-table-modify/base-1/sqlglot/parser.py", "old_string": "        # https://docs.databricks.com/delta/update-schema.html#explicitly-update-schema-to-add-columns\n        if self._match_texts((\"FIRST\", \"AFTER\")):\n            position = self._prev.text\n            column_p
…[359 chars elided]…
f._parse_column_position():\n            expression.set(\"position\", position)\n\n        return expression\n\n    def _parse_column_position(self) -> exp.ColumnPosition | None:\n        if not self._match_texts((\"FIRST\", \"AFTER\")):\n            return None\n\n        position = self._prev.text\n        return self.expression(exp.ColumnPosition(this=self._parse_column(), position=position))"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-202305-mysql-dialect-alter-table-modify/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-202305-mysql-dialect-alter-table-modify/base-1/sqlglot/expressions/ddl.py", "old_string": "class AlterIndex(Expression):", "new_string": "class AlterModifyColumn(Expression):\n    arg_types = {\"this\": True}\n\n\nclass AlterIndex(Expression):"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-202305-mysql-dialect-alter-table-modify/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-202305-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py", "old_string": "        \"MODIFY\": lambda self: self._parse_alter_table_alter(),", "new_string": "        \"MODIFY\": lambda self: self._parse_alter_table_modify(),"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-202305-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"def _parse_alter_table_alter_index\" -B3 -A12 sqlglot/parsers/mysql.py; grep -n \"^from\\|^import\" sqlglot/parsers/mysql.py; grep -n \"def columndef_sql\" sqlglot/generators/mysql.py", "description": "Locate MySQL alter index parser method and imports"}
[tool_result] 535-            parse_interval=parse_interval, fallback_to_identifier=fallback_to_identifier
536-        )
537-
538:    def _parse_alter_table_alter_index(self) -> exp.AlterIndex:
539-        index = self._parse_field(any_token=True)
540-
541-        if self._match_text_seq("VISIBLE"):
542-            visible = True
543-        elif self._match_text_seq("INVISIBLE"):
544-            visible = False
545-        else:
546-            visible = None
547-
548-        return self.expression(exp.AlterIndex(this=index, visible=visible))
549-
550-    def _parse_partition_property(
1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, parser
6:from sqlglot.trie import new_trie
7:from sqlglot.dialects.dialect import (
14:from sqlglot.helper import seq_get
15:from sqlglot.tokens import TokenType
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-202305-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py", "old_string": "    def _parse_alter_table_alter_index(self) -> exp.AlterIndex:", "new_string": "    def _parse_alter_table_modify(self) -> exp.Expr | None:\n        start = self._index\n        self._match(TokenType.COLUMN)\n\n
…[10 chars elided]…
lumn_def = self._parse_field_def()\n        if not isinstance(column_def, exp.ColumnDef):\n            self._retreat(start)\n            return None\n\n        if position := self._parse_column_position():\n            column_def.set(\"position\", position)\n\n        return self.expression(exp.AlterModifyColumn(this=column_def))\n\n    def _parse_alter_table_alter_index(self) -> exp.AlterIndex:"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-202305-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-202305-mysql-dialect-alter-table-modify/base-1/sqlglot/generators/mysql.py", "old_string": "        this = self.sql(expression, \"this\")\n        return f\"MODIFY COLUMN {this} {dtype}\"", "new_string": "        this = self.sql(expression, \"this\")\n        return f\"MODIFY COLUMN {this} {dtype}\"\n\n    def altermodifycolumn_sql(self, expression: exp.AlterModifyColumn) -> str:\n        return f\"MODIFY COLUMN {self.sql(expression, 'this')}\""}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-202305-mysql-dialect-alter-table-modify/base-1/sqlglot/generators/mysql.py has been updated successfully.
[assistant] Now I'll add tests and check the AST for each of the four examples, including the position and the existing `MODIFY COLUMN ... LONGTEXT` case.
[tool_use Bash] {"command": "grep -n \"def test_ddl\" tests/dialects/test_mysql.py | head -3 && grep -n 'ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT' tests/dialects/test_mysql.py && PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sys; sys.path.insert(0, '.')\nfrom sqlglot 
…[417 chars elided]…
  print(type(e).__name__, '|', e.sql('mysql'))\n    if isinstance(e, exp.Alter):\n        a = e.args['actions'][0]; print('  ', type(a).__name__, repr(a)[:0], a.this.sql() if hasattr(a,'this') else '', '| pos:', (a.this.args.get('position') and a.this.args['position'].sql()) if isinstance(a, exp.AlterModifyColumn) else '')\n\"", "description": "Check AST and round-trip for MODIFY COLUMN examples"}
[tool_result] 12:    def test_ddl(self):
40:        self.validate_identity("ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT")
167:            "ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT",
'ALTER TABLE t MODIFY COLUMN c INT FIRST, ADD COLUMN x INT' contains unsupported syntax. Falling back to parsing as a 'Command'.
'ALTER TABLE t MODIFY c' contains unsupported syntax. Falling back to parsing as a 'Command'.
Alter | ALTER TABLE t MODIFY COLUMN c INT NOT NULL DEFAULT 5
   AlterModifyCol
…[90 chars elided]…
) NOT NULL DEFAULT 'foo'
   AlterModifyColumn  c VARCHAR(50) NOT NULL DEFAULT 'foo' | pos: None
Alter | ALTER TABLE t MODIFY COLUMN c INT COMMENT 'hi'
   AlterModifyColumn  c INT COMMENT 'hi' | pos: None
Alter | ALTER TABLE t MODIFY COLUMN c INT FIRST
   AlterModifyColumn  c INT FIRST | pos: FIRST
Alter | ALTER TABLE t MODIFY COLUMN c INT AFTER d
   AlterModifyColumn  c INT AFTER d | pos: AFTER d
Command | ALTER TABLE t MODIFY COLUMN c INT FIRST, ADD COLUMN x INT
Command | ALTER TABLE t MODIFY c
[assistant] The AST is right for all four examples: `AlterModifyColumn` wraps a full `ColumnDef`, and the position lands on the column def. Now I'll add the tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-202305-mysql-dialect-alter-table-modify/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT\")\n        self.validate_identity(\"ALTER TABLE t AUTO_INCREMENT=3000000000\")", "new_string": "        self.validat
…[360 chars elided]…
elf.validate_identity(\"ALTER TABLE t MODIFY COLUMN c INT FIRST\")\n        self.validate_identity(\"ALTER TABLE t MODIFY COLUMN c INT AFTER d\")\n        self.assertIsInstance(\n            self.parse_one(\"ALTER TABLE t MODIFY COLUMN c INT AFTER d\").args[\"actions\"][0],\n            exp.AlterModifyColumn,\n        )\n        self.validate_identity(\"ALTER TABLE t AUTO_INCREMENT=3000000000\")"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-202305-mysql-dialect-alter-table-modify/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "sed -n 1,10p tests/dialects/test_mysql.py | grep import; PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py tests/dialects/test_singlestore.py tests/dialects/test_starrocks.py tests/dialects/test_doris.py tests/dialects/test_snowflake.py tests/dialects/test_hive.py tests/test_transpile.py 2>&1 | tail -30", "description": "Run MySQL-family and related dialect tests"}
[tool_result] import unittest
import sys
from sqlglot import UnsupportedError, expressions as exp
from sqlglot.dialects.mysql import MySQL
from tests.dialects.test_dialect import Validator
.............................. [ 12%]
............................................................................. [ 45%]
........................... [ 56%]
............................... [ 69%]
........................................................................                                               [100%]
237 passed, 3893 subtests passed in 0.94s
[assistant] The MySQL-family and related tests pass. Next I'll check what a non-MySQL target produces now, since `AlterModifyColumn` has no generator outside MySQL.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfor d in ['postgres','duckdb','hive']:\n    try: print(d, sqlglot.transpile('ALTER TABLE t MODIFY COLUMN c INT NOT NULL', read='mysql', write=d))\n    except Exception as ex: print(d, 'ERR', type(ex).__name__, ex)\nprint(sqlglot.transpile('ALTER TABLE t MODIFY COLUMN c INT NOT NULL', read='mysql', write='postgres', unsupported_level=sqlglot.ErrorLevel.RAISE) if False else '')\n\" 2>&1; git stash list | head -0; git show HEAD:sqlglot/parsers/mysql.py >/dev/null && echo ok", "description": "Check cross-dialect output for MODIFY COLUMN"}
[tool_result] postgres ERR ValueError Unsupported expression type AlterModifyColumn
duckdb ERR ValueError Unsupported expression type AlterModifyColumn
hive ERR ValueError Unsupported expression type AlterModifyColumn

head: illegal line count -- 0
ok
[assistant] Transpiling MySQL `MODIFY COLUMN` to another dialect now raises. Before this change it produced a lossy `ALTER COLUMN ... TYPE` through `AlterColumn`. I'll keep that fallback in the base generator and mark it unsupported so the loss is reported, not silent.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-202305-mysql-dialect-alter-table-modify/base-1/sqlglot/generator.py", "old_string": "    def alter_sql(self, expression: exp.Alter) -> str:", "new_string": "    def altermodifycolumn_sql(self, expression: exp.AlterModifyColumn) -> str:\n        column = expression.this\n        self.unsupported(\"MODIFY COLUMN only alters the column type in this dialect\")\n        return self.altercolumn_sql(\n            exp.AlterColumn(this=column.this, dtype=column.args.get(\"kind\"))\n        )\n\n    def alter_sql(self, expression: exp.Alter) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-202305-mysql-dialect-alter-table-modify/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfor d in ['postgres','duckdb','hive']:\n    print(d, sqlglot.transpile('ALTER TABLE t MODIFY COLUMN c INT NOT NULL', read='mysql', write=d))\n\" 2>&1; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py tests/dialects/test_singlestore.py tests/dialects/test_starrocks.py tests/dialects/test_doris.py tests/dialects/test_postgres.py tests/dialects/test_hive.py tests/test_transpile.py 2>&1 | tail -3", "description": "Verify cross-dialect fallback and rerun related tests"}
[tool_result] MODIFY COLUMN only alters the column type in this dialect
MODIFY COLUMN only alters the column type in this dialect
MODIFY COLUMN only alters the column type in this dialect
postgres ['ALTER TABLE t ALTER COLUMN c SET DATA TYPE INT']
duckdb ['ALTER TABLE t ALTER COLUMN c SET DATA TYPE INT']
hive ['ALTER TABLE t CHANGE COLUMN c c INT']
.............................. [ 17%]
.........................................................................................................................................            [100%]
167 passed, 2702 subtests passed in 0.55s
[assistant] Cross-dialect output is unchanged in shape: it's still the type change, now with an unsupported warning. Next is the full suite, as the project harness requires, plus lint on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/scripts/run_suite.py 2>&1 | tail -25", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; ls $PY/ 2>/dev/null | head -3; $PY/ruff check sqlglot/parser.py sqlglot/generator.py sqlglot/parsers/mysql.py sqlglot/generators/mysql.py sqlglot/expressions/ddl.py tests/dialects/test_mysql.py 2>&1 | tail -3; $PY/ruff format --check sqlglot/parser.py sqlglot/generator.py sqlglot/parsers/mysql.py sqlglot/generators/mysql.py sqlglot/expressions/ddl.py tests/dialects/test_mysql.py 2>&1 | tail -3", "description": "Lint and format-check changed files"}
[tool_result] WARNING: 1 other pytest process(es) running; expect slower runs:
  34207 03-00:53:27 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-40a149004e.log
ELAPSED: 49s
SUMMARY: 1094 passed, 17872 subtests passed in 48.96s
EXIT: 0
[tool_result] activate
activate.bat
activate.csh
All checks passed!
6 files already formatted
[tool_use Bash] {"command": "git diff --stat && git diff -- sqlglot/ | head -150", "description": "Review final diff of source changes"}
[tool_result]  sqlglot/expressions/ddl.py   |  4 ++++
 sqlglot/generator.py         |  7 +++++++
 sqlglot/generators/mysql.py  |  3 +++
 sqlglot/parser.py            | 15 +++++++++------
 sqlglot/parsers/mysql.py     | 16 +++++++++++++++-
 tests/dialects/test_mysql.py |  9 +++++++++
 6 files changed, 47 insertions(+), 7 deletions(-)
diff --git a/sqlglot/expressions/ddl.py b/sqlglot/expressions/ddl.py
index 79e8ac348..29e8222ec 100644
--- a/sqlglot/expressions/ddl.py
+++ b/sqlglot/expressions/ddl.py
@@ -245,6 
…[3497 chars elided]…

+        self._match(TokenType.COLUMN)
+
+        column_def = self._parse_field_def()
+        if not isinstance(column_def, exp.ColumnDef):
+            self._retreat(start)
+            return None
+
+        if position := self._parse_column_position():
+            column_def.set("position", position)
+
+        return self.expression(exp.AlterModifyColumn(this=column_def))
+
     def _parse_alter_table_alter_index(self) -> exp.AlterIndex:
         index = self._parse_field(any_token=True)
[assistant] `MODIFY COLUMN` in the MySQL dialect now parses into a real column definition, and all four examples round-trip. The full suite passed after my last edit: `SUMMARY: 1094 passed, 17872 subtests passed in 48.96s`, `EXIT: 0`. The changes are uncommitted in the worktree.

**What changed**

- **Parser** (`sqlglot/parsers/mysql.py`): `MODIFY` now goes to a new `_parse_alter_table_modify`. It takes an optional `COLUMN`, parses a full column definition (type, constraints, `COMMENT`), and then an optional `FIRST` or `AFTER col`. If it can't find a column definition, it falls back to a raw `Command`, as
…[761 chars elided]…
sed `ValueError`, which would have been a regression.
- **Tests** (`tests/dialects/test_mysql.py`): identity tests for the four examples, plus an assertion that the parsed action is `exp.AlterModifyColumn`.

**Left as-is**

- The existing `ALTER COLUMN ... SET DATA TYPE` → `MODIFY COLUMN` transpile path still uses `AlterColumn`, and its existing test still passes.
- `MODIFY COLUMN a INT, ADD COLUMN b INT` (several actions in one statement) still falls back to a raw `Command`. I did not check the pre-change output for that statement.
- I did not run mypy; only ruff check and format, which pass.
