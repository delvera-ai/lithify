# trajectory base-1

final message:
MySQL `ALTER TABLE ... MODIFY [COLUMN] col <definition> [FIRST | AFTER col]` now parses into its own node and round-trips. The full suite passes (1094 tests) and ruff is clean. I haven't committed anything.

All four statements from your request round-trip unchanged, and `MODIFY c INT AFTER d` (no `COLUMN`) normalizes to `MODIFY COLUMN c INT AFTER d`.

**What changed:**
- **`sqlglot/expressions/ddl.py`**: new `exp.AlterModifyColumn(this=ColumnDef)`. It is separate from `AlterColumn`, so the different semantics stay visible in the AST. The position lives on the `ColumnDef`, as it already does for `ADD ... FIRST/AFTER`.
- **`sqlglot/parsers/mysql.py`**: `MODIFY` now calls a new `_parse_alter_table_modify`. It parses a full column definition and an optional `FIRST`/`AFTER`. If no column definition follows, it falls back to the old `ALTER`-style parse.
- **`sqlglot/generator.py`**: `altermodifycolumn_sql` emits `MODIFY COLUMN ...`. I put it in the base generator, next to `altermodifysqlsecurity_sql`. A MySQL-only generator made transpiling to other dialects crash with `Unsupported expression type`.
- **`tests/dialects/test_mysql.py`**: added round-trip tests for the four statements in your request, plus `AFTER`. I did not change any existing test.

**Things to know:**
- Transpiling to other dialects now emits `MODIFY COLUMN ...` verbatim, which is not valid in most of them. This matches how `MODIFY SQL SECURITY` is already handled, but it does not produce correct SQL for those targets. If you want a warning or a different translation there, say so.
- The existing `ALTER COLUMN c SET DATA TYPE` path still produces `MODIFY COLUMN c <type>` through `AlterColumn`, and its existing test still passes.

## events
[tool_use Bash] {"command": "grep -n \"MODIFY\\|ALTER_COLUMN\\|AlterColumn\\|_parse_alter_table_alter\\|_parse_alter_table_add\" sqlglot/dialects/mysql.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -80", "description": "Find alter-table related code paths"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:3903:    def altercolumn_sql(self, expression: exp.AlterColumn) -> str:
sqlglot/generator.py:5929:        return f"MODIFY {props}"
sqlglot/parser.py:1435:        "ADD": lambda self: self._parse_alter_table_add(),
sqlglot/parser.py:1437:        "ALTER": lambda self: self._parse_alter_table_alter(),
sqlglot/parser.py:8537:    def _parse_alter_table_add(self) -> list[exp.Expr]:
sqlglot/parser.py:8576:    def _par
…[376 chars elided]…
string()))
sqlglot/parser.py:8592:            return self.expression(exp.AlterColumn(this=column, drop=True, allow_null=True))
sqlglot/parser.py:8594:            return self.expression(exp.AlterColumn(this=column, allow_null=False))
sqlglot/parser.py:8597:            return self.expression(exp.AlterColumn(this=column, visible="VISIBLE"))
sqlglot/parser.py:8599:            return self.expression(exp.AlterColumn(this=column, visible="INVISIBLE"))
sqlglot/parser.py:8604:            exp.AlterColumn(
[tool_use Bash] {"command": "sed -n 1420,1450p sqlglot/parser.py && echo ---- && sed -n 8530,8625p sqlglot/parser.py && echo ---- && sed -n 3895,3935p sqlglot/generator.py && echo ---- && grep -n \"class AlterColumn\" -A 25 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null; grep -rn \"class AlterColumn\" sqlglot/", "description": "Read parser alter-table and generator code"}
[tool_result]         this, expression = seq_get(args, 0), seq_get(args, 1)

        if isinstance(this, exp.Literal):
            # Check for Iceberg partition transforms (bucket / truncate) and ensure their arguments are in the right order
            #  - For Hive, it's `bucket(<num buckets>, <col name>)` or `truncate(<num_chars>, <col_name>)`
            #  - For Trino, it's reversed - `bucket(<col name>, <num buckets>)` or `truncate(<col_name>, <num_chars>)`
            # Both variants are canonicalized 
…[8126 chars elided]…
 True}
sqlglot/expressions/ddl.py-250-
sqlglot/expressions/ddl.py-251-
sqlglot/expressions/ddl.py-252-class AlterDistStyle(Expression):
sqlglot/expressions/ddl.py-253-    pass
sqlglot/expressions/ddl.py-254-
sqlglot/expressions/ddl.py-255-
sqlglot/expressions/ddl.py-256-class AlterSortKey(Expression):
sqlglot/expressions/ddl.py-257-    arg_types = {"this": False, "expressions": False, "compound": False}
sqlglot/expressions/ddl.py-258-
sqlglot/expressions/ddl.py:233:class AlterColumn(Expression):
[tool_use Bash] {"command": "grep -n \"FIRST\\|AFTER\\|ColumnPosition\\|position\" sqlglot/parser.py sqlglot/generator.py sqlglot/dialects/mysql.py | head -40; echo ----; grep -n \"ALTER\" sqlglot/dialects/mysql.py | head; echo ----; grep -n \"class ColumnPosition\\|class ColumnDef\" -A 12 sqlglot/expressions/*.py | head -40; echo ----; grep -n \"MODIFY\" -B3 -A3 tests/dialects/test_mysql.py | head -60", "description": "Search FIRST/AFTER, ALTER parsers, and MODIFY tests"}
[tool_result] sqlglot/generator.py:64:AFTER_HAVING_MODIFIER_TRANSFORMS: dict[str, t.Any] = {
sqlglot/generator.py:298:    # Window functions that support NULLS FIRST/LAST
sqlglot/generator.py:302:    # FIRST(x IGNORE NULLS) OVER vs FIRST (x) IGNORE NULLS OVER
sqlglot/generator.py:306:    # FIRST(x IGNORE NULLS ORDER BY y) vs FIRST(x ORDER BY y IGNORE NULLS)
sqlglot/generator.py:632:    AFTER_HAVING_MODIFIER_TRANSFORMS: t.ClassVar = {
sqlglot/generator.py:636:        **AFTER_HAVING_MODIFIER_TRANSFORMS,
sqlglot
…[4515 chars elided]…
oo")
43-        self.validate_identity("ALTER VIEW v AS SELECT * FROM foo WHERE c > 100")
--
164-        )
165-        self.validate_identity(
166-            "ALTER TABLE test_table ALTER COLUMN test_column SET DATA TYPE LONGTEXT",
167:            "ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT",
168-        )
169-        self.validate_identity(
170-            "CREATE TABLE t (c DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP) DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC",
[tool_use Bash] {"command": "grep -rn \"MODIFY\" sqlglot/ | head -20; echo ----; sed -n 3935,3950p sqlglot/generator.py; echo ----; sed -n 1130,1160p sqlglot/generator.py; echo ----; sed -n 5915,5935p sqlglot/generator.py; echo ----; grep -n \"ALTER_TABLE_ADD\\|ALTER_SET_TYPE\" sqlglot/dialects/*.py sqlglot/dialects/dialect.py sqlglot/generator.py | head", "description": "Find MODIFY handling and related dialect flags"}
[tool_result] sqlglot/generator.py:5929:        return f"MODIFY {props}"
sqlglot/parsers/clickhouse.py:445:        "MODIFY": lambda self: self._parse_alter_table_modify(),
sqlglot/parsers/snowflake.py:742:        "MODIFY": lambda self: self._parse_alter_table_alter(),
sqlglot/parsers/mysql.py:255:        "MODIFY": lambda self: self._parse_alter_table_alter(),
sqlglot/generators/mysql.py:719:        return f"MODIFY COLUMN {this} {dtype}"
----
            return f"ALTER COLUMN {this} {keyword} NOT NULL"

      
…[2986 chars elided]…
  ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN = False
sqlglot/dialects/tsql.py:20:    ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN = False
sqlglot/generator.py:563:    ALTER_SET_TYPE = "SET DATA TYPE"
sqlglot/generator.py:3912:            alter_set_type = self.ALTER_SET_TYPE + " " if self.ALTER_SET_TYPE else ""
sqlglot/generator.py:3986:        if not self.dialect.ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN and isinstance(
sqlglot/dialects/dialect.py:699:    ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN = True
[tool_use Bash] {"command": "sed -n 240,275p sqlglot/parsers/mysql.py; echo ----; sed -n 690,730p sqlglot/generators/mysql.py; echo ----; grep -n \"_parse_alter_table_modify\" -A 25 sqlglot/parsers/clickhouse.py | head -50; echo ----; grep -n \"def _parse_column_def\\|def _parse_add_column\\|def _parse_column_position\\|ColumnPosition\" -A 12 sqlglot/parser.py | head -90", "description": "Read MySQL parser/generator alter code and column helpers"}
[tool_result]     SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
    SET_TRIE = new_trie(key.split(" ") for key in SET_PARSERS)

    CONSTRAINT_PARSERS = {
        **parser.Parser.CONSTRAINT_PARSERS,
        "FULLTEXT": lambda self: self._parse_index_constraint(kind="FULLTEXT"),
        "INDEX": lambda self: self._parse_index_constraint(),
        "KEY": lambda self: self._parse_index_constraint(),
        "SPATIAL": lambda self: self._parse_index_constraint(kind="SPATIAL"),
        "ZEROFILL": 
…[6465 chars elided]…
on)
8517-            )
8518-            expression.set("position", column_position)
8519-
8520-        return expression
8521-
8522-    def _parse_drop_column(self) -> exp.Drop | exp.Command | None:
8523-        drop = self._parse_drop() if self._match(TokenType.DROP) else None
8524-        if drop and not isinstance(drop, exp.Command):
8525-            drop.set("kind", drop.args.get("kind", "COLUMN"))
8526-        return drop
8527-
8528-    def _parse_alter_drop_action(self) -> exp.Expr | None:
[tool_use Bash] {"command": "sed -n 3975,4010p sqlglot/generator.py; echo ----; grep -n \"class AlterModifySqlSecurity\\|class AlterTable\\b\\|class AlterTable(\" -A 8 sqlglot/expressions/ddl.py; echo ----; sed -n 8489,8503p sqlglot/parser.py; echo ----; grep -n \"def _parse_field_def\" -A 12 sqlglot/parser.py; echo ----; grep -n \"AlterColumn\\|AlterModifySqlSecurity\\|\\\"AlterTable\\|exp.AlterTable\" sqlglot/*.py sqlglot/*/*.py | grep -v \"^sqlglot/expressions/ddl.py\" | head -30", "description": "Inspect alter_sql generator and expression defs"}
[tool_result]     def alterset_sql(self, expression: exp.AlterSet) -> str:
        exprs = self.expressions(expression, flat=True)
        if self.ALTER_SET_WRAPPED:
            exprs = f"({exprs})"

        return f"SET {exprs}"

    def alter_sql(self, expression: exp.Alter) -> str:
        actions = expression.args["actions"]

        if not self.dialect.ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN and isinstance(
            actions[0], exp.ColumnDef
        ):
            actions_sql = self.expressions(expre
…[3274 chars elided]…
lterColumn) -> str:
sqlglot/generators/spark2.py:235:    def altercolumn_sql(self, expression: exp.AlterColumn) -> str:
sqlglot/parsers/hive.py:236:            return self.expression(exp.AlterColumn(this=this, dtype=self._parse_types(schema=True)))
sqlglot/parsers/hive.py:249:            exp.AlterColumn(this=this, rename_to=column_new, dtype=dtype, comment=comment)
sqlglot/parsers/clickhouse.py:832:            return self.expression(exp.AlterModifySqlSecurity(expressions=properties.expressions))
[tool_use Bash] {"command": "sed -n 225,247p sqlglot/expressions/ddl.py; echo ----; grep -n \"columndef_sql\\|def add_column_sql\" -A6 sqlglot/generators/mysql.py | head -20; echo ----; sed -n 1,30p sqlglot/parsers/mysql.py | grep -n \"import\" ", "description": "Check ddl placement and mysql generator/parser imports"}
[tool_result] class UserDefinedFunction(Expression):
    arg_types = {"this": True, "expressions": False, "wrapped": False}


class CharacterSet(Expression):
    arg_types = {"this": True, "default": False}


class AlterColumn(Expression):
    arg_types = {
        "this": True,
        "dtype": False,
        "collate": False,
        "using": False,
        "default": False,
        "drop": False,
        "comment": False,
        "allow_null": False,
        "visible": False,
        "rename_to": False,
    }


----
----
1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, parser
6:from sqlglot.trie import new_trie
7:from sqlglot.dialects.dialect import (
14:from sqlglot.helper import seq_get
15:from sqlglot.tokens import TokenType
[assistant] Parser, generator and expression locations are clear. I'll add a dedicated expression for MySQL's `MODIFY COLUMN`, so it doesn't reuse `AlterColumn`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-120937-mysql-dialect-alter-table-modify/base-1/sqlglot/expressions/ddl.py", "old_string": "        \"visible\": False,\n        \"rename_to\": False,\n    }\n\n\nclass AlterIndex(Expression):", "new_string": "        \"visible\": False,\n        \"rename_to\": False,\n    }\n\n\nclass AlterModifyColumn(Expression):\n    arg_types = {\"this\": True}\n\n\nclass AlterIndex(Expression):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-120937-mysql-dialect-alter-table-modify/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[assistant] Next, the parser: route `MODIFY` to a column-definition parser for MySQL.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-120937-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py", "old_string": "        \"MODIFY\": lambda self: self._parse_alter_table_alter(),\n        \"AUTO_INCREMENT\"", "new_string": "        \"MODIFY\": lambda self: self._parse_alter_table_modify(),\n        \"AUTO_INCREMENT\""}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-120937-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"    def \" sqlglot/parsers/mysql.py | head -40; grep -n \"_parse_alter_table_alter_index\" -A8 sqlglot/parsers/mysql.py | tail -12", "description": "Locate parser method layout in MySQL parser"}
[tool_result] 48:    def _parse(self: MySQLParser) -> exp.Show:
305:    def _parse_alter_table_rename(self):
313:    def _parse_alter_drop_action(self) -> exp.Expr | None:
318:    def _parse_generated_as_identity(
339:    def _parse_primary_key_part(self) -> exp.Expr | None:
348:    def _parse_index_constraint(self, kind: str | None = None) -> exp.IndexColumnConstraint:
395:    def _parse_show_mysql(
481:    def _parse_oldstyle_limit(
496:    def _parse_set_item_charset(self, kind: str) -> exp.Expr:
500:    d
…[280 chars elided]…
 -> exp.Expr | None:
599:    def _parse_partition_list_value(self) -> exp.Partition:
607:    def _parse_primary_key(
268-        "KEY",
269-        "SPATIAL",
--
538:    def _parse_alter_table_alter_index(self) -> exp.AlterIndex:
539-        index = self._parse_field(any_token=True)
540-
541-        if self._match_text_seq("VISIBLE"):
542-            visible = True
543-        elif self._match_text_seq("INVISIBLE"):
544-            visible = False
545-        else:
546-            visible = None
[tool_use Bash] {"command": "sed -n 305,318p sqlglot/parsers/mysql.py", "description": "Read parser method near alter helpers"}
[tool_result]     def _parse_alter_table_rename(self):
        if self._match_texts(("INDEX", "KEY")):
            old = self._parse_field(any_token=True)
            self._match_text_seq("TO")
            new = self._parse_field(any_token=True)
            return self.expression(exp.RenameIndex(this=old, to=new))
        return super()._parse_alter_table_rename()

    def _parse_alter_drop_action(self) -> exp.Expr | None:
        if self._match_pair(TokenType.DROP, TokenType.PRIMARY_KEY):
            return self.expression(exp.DropPrimaryKey())
        return super()._parse_alter_drop_action()

    def _parse_generated_as_identity(
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-120937-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py", "old_string": "        return super()._parse_alter_drop_action()\n\n    def _parse_generated_as_identity(", "new_string": "        return super()._parse_alter_drop_action()\n\n    def _parse_alter_table_modify(self) -> exp.Expr
…[391 chars elided]…
f._match_texts((\"FIRST\", \"AFTER\")):\n            position = self._prev.text\n            column_position = self.expression(\n                exp.ColumnPosition(this=self._parse_column(), position=position)\n            )\n            column_def.set(\"position\", column_position)\n\n        return self.expression(exp.AlterModifyColumn(this=column_def))\n\n    def _parse_generated_as_identity("}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-120937-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[assistant] Now the MySQL generator, placed next to the existing `altercolumn_sql`:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-120937-mysql-dialect-alter-table-modify/base-1/sqlglot/generators/mysql.py", "old_string": "        this = self.sql(expression, \"this\")\n        return f\"MODIFY COLUMN {this} {dtype}\"\n", "new_string": "        this = self.sql(expression, \"this\")\n        return f\"MODIFY COLUMN {this} {dtype}\"\n\n    def altermodifycolumn_sql(self, expression: exp.AlterModifyColumn) -> str:\n        return f\"MODIFY COLUMN {self.sql(expression, 'this')}\"\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-120937-mysql-dialect-alter-table-modify/base-1/sqlglot/generators/mysql.py has been updated successfully.
[assistant] Now I'll check the round-trips from the request, plus the existing `MODIFY` tests.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in [\n 'ALTER TABLE t MODIFY COLUMN c INT NOT NULL DEFAULT 5',\n \\\"ALTER TABLE t MODIFY COLUMN c VARCHAR(50) NOT NULL DEFAULT 'foo'\\\",\n 'ALTER TABLE t MODIFY COLUMN c INT COMMENT \\'hi\\'',\n 'ALTER TABLE t MODIFY COLUMN c INT FIRST',\n 'ALTER TABLE t MODIFY c INT AFTER d',\n 'A
…[250 chars elided]…
DIFY COLUMN c INT AFTER d', read='mysql').args['actions'][0]))\nprint(sqlglot.transpile('ALTER TABLE t MODIFY COLUMN c INT FIRST', read='mysql', write='postgres'))\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -15", "description": "Verify round-trips and run MySQL dialect tests"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 16, in <module>
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-120937-mysql-dialect-alter-table-modify/base-1/sqlglot/__init__.py", line 211, in transpile
    write.generate(expression, copy=False, **opts) if expression else ""
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-120937-mysql-dialect-alter-table-modify/base-1/sqlglot/di
…[1276 chars elided]…
 NULL DEFAULT 'foo'
OK  ALTER TABLE t MODIFY COLUMN c INT COMMENT 'hi'
OK  ALTER TABLE t MODIFY COLUMN c INT FIRST
DIFF ALTER TABLE t MODIFY COLUMN c INT AFTER d
   expected ALTER TABLE t MODIFY c INT AFTER d
OK  ALTER TABLE t MODIFY COLUMN c LONGTEXT
AlterModifyColumn(
  this=ColumnDef(
    this=Identifier(this=c, quoted=False),
    kind=DataType(this=DType.INT, nested=False),
    position=ColumnPosition(
      this=Column(
        this=Identifier(this=d, quoted=False)),
      position=AFTER)))
[assistant] Round-trips pass. The `AFTER` case differs only because my test input omitted `COLUMN`, which is normalized, as intended. Transpiling to another dialect crashes, though, because the generator only exists in MySQL. I'll move the generator to the base class, next to `altermodifysqlsecurity_sql`, which follows the same pattern.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python - <<'EOF'\nimport pathlib\nmysql = pathlib.Path(\"sqlglot/generators/mysql.py\")\ns = mysql.read_text()\nblock = '\\n    def altermodifycolumn_sql(self, expression: exp.AlterModifyColumn) -> str:\\n        return f\"MODIFY COLUMN {self.sql(expression, \\'this\\')}\"\\n'\nassert s.count(block) == 1\nmysql.write_t
…[223 chars elided]…
ssions(expression, sep=\" \")\\n        return f\"MODIFY {props}\"\\n'\nassert g.count(anchor) == 1\ng = g.replace(anchor, anchor + '\\n    def altermodifycolumn_sql(self, expression: exp.AlterModifyColumn) -> str:\\n        return f\"MODIFY COLUMN {self.sql(expression, \\'this\\')}\"\\n')\ngen.write_text(g)\nEOF\ngit diff --stat", "description": "Move MODIFY COLUMN generator into base generator"}
[tool_result]  sqlglot/expressions/ddl.py |  4 ++++
 sqlglot/generator.py       |  3 +++
 sqlglot/parsers/mysql.py   | 20 +++++++++++++++++++-
 3 files changed, 26 insertions(+), 1 deletion(-)
[assistant] The `generators/mysql.py` notice is from my own script removing the override, so that file is back to its original state. Next I'll add tests and run the suite.
[tool_use Bash] {"command": "sed -n 36,42p tests/dialects/test_mysql.py", "description": "Read test anchor lines in MySQL tests"}
[tool_result]         self.validate_identity("ALTER TABLE t ADD INDEX `i` (`c`)")
        self.validate_identity("ALTER TABLE t ADD UNIQUE `i` (`c`)")
        self.validate_identity("ALTER TABLE t DROP PRIMARY KEY")
        self.validate_identity("ALTER TABLE t DROP COLUMN c, DROP PRIMARY KEY, DROP INDEX `i`")
        self.validate_identity("ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT")
        self.validate_identity("ALTER TABLE t AUTO_INCREMENT=3000000000")
        self.validate_identity("ALTER VIEW v AS SELECT a, b, c, d FROM foo")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-120937-mysql-dialect-alter-table-modify/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT\")\n        self.validate_identity(\"ALTER TABLE t AUTO_INCREMENT=3000000000\")", "new_string": "        self.validat
…[184 chars elided]…
te_identity(\"ALTER TABLE t MODIFY COLUMN c VARCHAR(50) NOT NULL DEFAULT 'foo'\")\n        self.validate_identity(\"ALTER TABLE t MODIFY COLUMN c INT COMMENT 'hi'\")\n        self.validate_identity(\"ALTER TABLE t MODIFY COLUMN c INT FIRST\")\n        self.validate_identity(\"ALTER TABLE t MODIFY COLUMN c INT AFTER d\")\n        self.validate_identity(\"ALTER TABLE t AUTO_INCREMENT=3000000000\")"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-120937-mysql-dialect-alter-table-modify/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nprint(sqlglot.transpile('ALTER TABLE t MODIFY COLUMN c INT FIRST', read='mysql', write='postgres'))\n\" ; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -5; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8", "description": "Run transpile check, MySQL tests, and full test suite"}
[tool_result] ['ALTER TABLE t MODIFY COLUMN c INT FIRST']
.............................. [ 60%]
....................                                              [100%]
50 passed, 481 subtests passed in 0.25s
................................... [ 46%]
...................................................................................................... [ 55%]
.................................................................................................................................................................................. [ 71%]
............................................. [ 75%]
............................................. [ 79%]
............................... [ 82%]
............................................................................................................................................................................................                                           [100%]
1094 passed, 17872 subtests passed in 49.79s
[assistant] All 1094 tests pass. Last, a lint and format check on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff --version >/dev/null 2>&1 && $PY -m ruff check sqlglot/parsers/mysql.py sqlglot/expressions/ddl.py sqlglot/generator.py tests/dialects/test_mysql.py && $PY -m ruff format --check sqlglot/parsers/mysql.py sqlglot/expressions/ddl.py sqlglot/generator.py tests/dialects/test_mysql.py) || echo \"ruff unavailable in env\"; git status --short", "description": "Run ruff check and format on changed files"}
[tool_result] All checks passed!
4 files already formatted
 M sqlglot/expressions/ddl.py
 M sqlglot/generator.py
 M sqlglot/parsers/mysql.py
 M tests/dialects/test_mysql.py
[assistant] MySQL `ALTER TABLE ... MODIFY [COLUMN] col <definition> [FIRST | AFTER col]` now parses into its own node and round-trips. The full suite passes (1094 tests) and ruff is clean. I haven't committed anything.

All four statements from your request round-trip unchanged, and `MODIFY c INT AFTER d` (no `COLUMN`) normalizes to `MODIFY COLUMN c INT AFTER d`.

**What changed:**
- **`sqlglot/expressions/ddl.py`**: new `exp.AlterModifyColumn(this=ColumnDef)`. It is separate from `AlterColumn`, so the different semantics stay visible in the AST. The position lives on the `ColumnDef`, as it already does f
…[520 chars elided]…
ts/dialects/test_mysql.py`**: added round-trip tests for the four statements in your request, plus `AFTER`. I did not change any existing test.

**Things to know:**
- Transpiling to other dialects now emits `MODIFY COLUMN ...` verbatim, which is not valid in most of them. This matches how `MODIFY SQL SECURITY` is already handled, but it does not produce correct SQL for those targets. If you want a warning or a different translation there, say so.
- The existing `ALTER COLUMN c SET DATA TYPE` path still produces `MODIFY COLUMN c <type>` through `AlterColumn`, and its existing test still passes.
