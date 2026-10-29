# trajectory base-1

final message:
MySQL `ALTER TABLE ... MODIFY [COLUMN] col_name column_definition [FIRST | AFTER col]` now parses into a real column definition and round-trips. The full suite passes (1094 tests), and ruff check and format are clean.

Before the change, these statements fell back to `exp.Command` because the MySQL `MODIFY` hook reused the ALTER COLUMN parser, which has no way to take constraints, `COMMENT`, or a position. Now `MODIFY` gets its own parser.

Changes:
- **`sqlglot/expressions/ddl.py`**: new `ModifyColumn(this=ColumnDef)` expression. I kept it separate from `AlterColumn` because the semantics differ.
- **`sqlglot/parsers/mysql.py`**: `MODIFY` now dispatches to `_parse_alter_table_modify`. It takes the optional `COLUMN`, a full column definition, and an optional `FIRST`/`AFTER` position, which is stored on the `ColumnDef` the same way ADD does it.
- **`sqlglot/generators/mysql.py`**: `modifycolumn_sql` emits `MODIFY COLUMN <column def>`. The position and constraints come from the existing column-def generation.
- **`tests/dialects/test_mysql.py`**: added round-trip cases for all four examples from your request, plus `AFTER`, and a `MODIFY c INT NOT NULL` case that normalizes to `MODIFY COLUMN`. Existing assertions are untouched.

Decisions to check:
- `ALTER COLUMN c SET DATA TYPE` still generates `MODIFY COLUMN c <type>` in MySQL, so the existing transpile test is unaffected.
- The new `ModifyColumn` node has no generator outside MySQL. Transpiling it to another dialect will produce the generic fallback output, not valid SQL there. I didn't add handling for that because nothing in the request asked for it.
- `ALTER TABLE t MODIFY COLUMN c` with no type still falls back to `Command`, since a column definition needs a type in MySQL.

## events
[tool_use Bash] {"command": "grep -n -i \"modify\\|ALTER_COLUMN\\|_parse_alter_table_alter\\|AlterColumn\" sqlglot/dialects/mysql.py sqlglot/parser.py sqlglot/generator.py sqlglot/dialects/dialect.py | head -80", "description": "Search for MODIFY and alter-column handling"}
[tool_result] sqlglot/parser.py:1437:        "ALTER": lambda self: self._parse_alter_table_alter(),
sqlglot/parser.py:8576:    def _parse_alter_table_alter(self) -> exp.Expr | None:
sqlglot/parser.py:8586:            return self.expression(exp.AlterColumn(this=column, drop=True))
sqlglot/parser.py:8588:            return self.expression(exp.AlterColumn(this=column, default=self._parse_disjunction()))
sqlglot/parser.py:8590:            return self.expression(exp.AlterColumn(this=column, comment=self._parse_str
…[264 chars elided]…
 return self.expression(exp.AlterColumn(this=column, visible="VISIBLE"))
sqlglot/parser.py:8599:            return self.expression(exp.AlterColumn(this=column, visible="INVISIBLE"))
sqlglot/parser.py:8604:            exp.AlterColumn(
sqlglot/generator.py:3903:    def altercolumn_sql(self, expression: exp.AlterColumn) -> str:
sqlglot/generator.py:5927:    def altermodifysqlsecurity_sql(self, expression: exp.AlterModifySqlSecurity) -> str:
sqlglot/generator.py:5929:        return f"MODIFY {props}"
[tool_use Bash] {"command": "sed -n 8570,8620p sqlglot/parser.py && sed -n 3895,3935p sqlglot/generator.py && grep -n \"class AlterColumn\" -A 25 sqlglot/expressions/*.py | head -40; grep -n \"ALTER\\|_parse_alter\" sqlglot/dialects/mysql.py | head", "description": "Read alter-column parsing and generation code"}
[tool_result]                 if schema
                else self._parse_csv(self._parse_column_def_with_exists)
            )

        return self._parse_csv(_parse_add_alteration)

    def _parse_alter_table_alter(self) -> exp.Expr | None:
        if self._match_texts(self.ALTER_ALTER_PARSERS):
            return self.ALTER_ALTER_PARSERS[self._prev.text.upper()](self)

        # Many dialects support the ALTER [COLUMN] syntax, so if there is no
        # keyword after ALTER we default to parsing this statem
…[4384 chars elided]…
 {"this": True, "visible": True}
sqlglot/expressions/ddl.py-250-
sqlglot/expressions/ddl.py-251-
sqlglot/expressions/ddl.py-252-class AlterDistStyle(Expression):
sqlglot/expressions/ddl.py-253-    pass
sqlglot/expressions/ddl.py-254-
sqlglot/expressions/ddl.py-255-
sqlglot/expressions/ddl.py-256-class AlterSortKey(Expression):
sqlglot/expressions/ddl.py-257-    arg_types = {"this": False, "expressions": False, "compound": False}
sqlglot/expressions/ddl.py-258-
0 matches for 'ALTER\|_parse_alter'
[tool_use Bash] {"command": "grep -n \"ALTER_PARSERS\\|ALTER_ALTER_PARSERS\\|ColumnPosition\\|FIRST\\|AFTER\\|def _parse_alter\\b\\|def _parse_alter_table_add\\|def _parse_alter(\" sqlglot/parser.py sqlglot/dialects/mysql.py sqlglot/generator.py sqlglot/expressions/*.py | head -60; grep -n \"class ColumnDef\" -A 12 sqlglot/expressions/*.py | head -30", "description": "Locate ALTER parser hooks and column position support"}
[tool_result] rg: regex parse error:
    (?:ALTER_PARSERS|ALTER_ALTER_PARSERS|ColumnPosition|FIRST|AFTER|def _parse_alter\b|def _parse_alter_table_add|def _parse_alter()
    ^
error: unclosed group
0 matches for 'ALTER_PARSERS\|ALTER_ALTER_PARSERS\|ColumnPosition\|FIRST\|AFTER\|def _parse_alter\b\|def _parse_alter_table_add\|def _parse_alter('
sqlglot/expressions/query.py:501:class ColumnDef(Expression):
sqlglot/expressions/query.py-502-    arg_types = {
sqlglot/expressions/query.py-503-        "this": True,

…[59 chars elided]…
glot/expressions/query.py-505-        "constraints": False,
sqlglot/expressions/query.py-506-        "exists": False,
sqlglot/expressions/query.py-507-        "position": False,
sqlglot/expressions/query.py-508-        "default": False,
sqlglot/expressions/query.py-509-        "output": False,
sqlglot/expressions/query.py-510-    }
sqlglot/expressions/query.py-511-
sqlglot/expressions/query.py-512-    @property
sqlglot/expressions/query.py-513-    def constraints(self) -> list[ColumnConstraint]:
[tool_use Bash] {"command": "grep -n -E \"ALTER_PARSERS|ALTER_ALTER_PARSERS|ColumnPosition|\\\"FIRST\\\"|\\\"AFTER\\\"|def _parse_alter|_parse_alter_table_add|position\" sqlglot/parser.py sqlglot/dialects/mysql.py sqlglot/generator.py sqlglot/expressions/*.py | head -80", "description": "Locate ALTER parser hooks and column position support"}
[tool_result] sqlglot/parser.py:171:    return exp.Trim(this=this, expression=expression, position="LEADING" if is_left else "TRAILING")
sqlglot/parser.py:180:def build_locate_strposition(args: BuilderArgs) -> exp.StrPosition:
sqlglot/parser.py:184:        position=seq_get(args, 2),
sqlglot/parser.py:405:        "CHARINDEX": lambda args: build_locate_strposition(args),
sqlglot/parser.py:407:        "LOCATE": lambda args: build_locate_strposition(args),
sqlglot/parser.py:1434:    ALTER_PARSERS: t.ClassVar = {

…[5681 chars elided]…

sqlglot/expressions/core.py:1329:        Update this expression with positions from a token or other expression.
sqlglot/expressions/ddl.py:212:        "position": False,
sqlglot/expressions/ddl.py:308:        "position": False,
sqlglot/expressions/query.py:497:class ColumnPosition(Expression):
sqlglot/expressions/query.py:498:    arg_types = {"this": False, "position": True}
sqlglot/expressions/query.py:507:        "position": False,
sqlglot/expressions/string.py:197:        "position": False,
[tool_use Bash] {"command": "sed -n 1434,1460p sqlglot/parser.py && sed -n 8500,8540p sqlglot/parser.py && sed -n 8706,8745p sqlglot/parser.py && sed -n 1130,1160p sqlglot/generator.py && grep -n \"ALTER\\|Alter\" sqlglot/dialects/mysql.py | head; grep -rn \"MODIFY\" tests/dialects/test_mysql.py | head", "description": "Read ALTER dispatch, add-column, and MySQL tests"}
[tool_result]     ALTER_PARSERS: t.ClassVar = {
        "ADD": lambda self: self._parse_alter_table_add(),
        "AS": lambda self: self._parse_select(),
        "ALTER": lambda self: self._parse_alter_table_alter(),
        "CLUSTER BY": lambda self: self._parse_cluster(wrapped=True),
        "DELETE": lambda self: self.expression(exp.Delete(where=self._parse_where())),
        "DROP": lambda self: self._parse_alter_table_drop(),
        "RENAME": lambda self: self._parse_alter_table_rename(),
        "SET
…[5060 chars elided]…
def columnconstraint_sql(self, expression: exp.ColumnConstraint) -> str:
        this = self.sql(expression, "this")
        kind_sql = self.sql(expression, "kind").strip()
        return f"CONSTRAINT {this} {kind_sql}" if this else kind_sql
0 matches for 'ALTER\|Alter'
tests/dialects/test_mysql.py:40:        self.validate_identity("ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT")
tests/dialects/test_mysql.py:167:            "ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT",
[tool_use Bash] {"command": "sed -n 36,42p tests/dialects/test_mysql.py; sed -n 160,170p tests/dialects/test_mysql.py; <work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t MODIFY COLUMN c INT NOT NULL DEFAULT 5','ALTER TABLE t MODIFY COLUMN c VARCHAR(50) NOT NULL DEFAULT \\'foo\\'','ALTER TABLE t MODIFY COLUMN c INT COMMENT \\'hi\\'','ALTER TABLE t MODIFY COLUMN c INT FIRST','ALTER TABLE t MODIFY c INT AFTER d','ALTER TABLE t MODIFY COLUMN test_column LONGTEXT']:\n    e=sqlglot.parse_one(s,read='mysql'); print(repr(e)[:300]); print(e.sql('mysql'))\n\"", "description": "Check existing MODIFY tests and current parse output"}
[tool_result ERROR] Exit code 1
        self.validate_identity("ALTER TABLE t ADD INDEX `i` (`c`)")
        self.validate_identity("ALTER TABLE t ADD UNIQUE `i` (`c`)")
        self.validate_identity("ALTER TABLE t DROP PRIMARY KEY")
        self.validate_identity("ALTER TABLE t DROP COLUMN c, DROP PRIMARY KEY, DROP INDEX `i`")
        self.validate_identity("ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT")
        self.validate_identity("ALTER TABLE t AUTO_INCREMENT=3000000000")
        self.validate_id
…[266 chars elided]…
        )
        self.validate_identity(
            "ALTER TABLE test_table ALTER COLUMN test_column SET DATA TYPE LONGTEXT",
            "ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT",
        )
        self.validate_identity(
            "CREATE TABLE t (c DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP) DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC",
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "grep -n \"ALTER_SET_TYPE\\|def altercolumn_sql\\|MODIFY\" sqlglot/dialects/*.py | head -20; PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -I -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t MODIFY COLUMN c INT NOT NULL DEFAULT 5','ALTER TABLE t MODIFY COLUMN c VARCHAR(50) NOT NULL DEFAULT \\'foo\\'','ALTER TABLE t MODIFY COLUMN c INT COMMENT \\'hi\\'','ALTER TABLE t MODIFY COLUMN c INT FIRST','ALTER TABLE t MODIFY c INT AFTER d','ALTER TABLE t MODIFY COLUMN test_column LONGTEXT']:\n    e=sqlglot.parse_one(s,read='mysql'); print(repr(e)[:400]); print(e.sql('mysql'))\n\"", "description": "Inspect MODIFY generation and current parse output"}
[tool_result ERROR] Exit code 1
0 matches for 'ALTER_SET_TYPE\|def altercolumn_sql\|MODIFY'
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "grep -rn \"MODIFY\\|ALTER_SET_TYPE\" sqlglot/ | grep -v \"altermodify\" | head -20; PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t MODIFY COLUMN c INT NOT NULL DEFAULT 5','ALTER TABLE t MODIFY COLUMN c VARCHAR(50) NOT NULL DEFAULT \\'foo\\'','ALTER TABLE t MODIFY COLUMN c INT COMMENT \\'hi\\'','ALTER TABLE t MODIFY COLUMN c INT FIRST','ALTER TABLE t MODIFY c INT AFTER d','ALTER TABLE t MODIFY COLUMN test_column LONGTEXT']:\n    e=sqlglot.parse_one(s,read='mysql'); print(repr(e)[:400]); print(e.sql('mysql'))\n\"", "description": "Inspect MODIFY generation and current parse output"}
[tool_result] sqlglot/parsers/clickhouse.py:445:        "MODIFY": lambda self: self._parse_alter_table_modify(),
sqlglot/parsers/snowflake.py:742:        "MODIFY": lambda self: self._parse_alter_table_alter(),
sqlglot/parsers/mysql.py:255:        "MODIFY": lambda self: self._parse_alter_table_alter(),
sqlglot/generator.py:563:    ALTER_SET_TYPE = "SET DATA TYPE"
sqlglot/generator.py:3912:            alter_set_type = self.ALTER_SET_TYPE + " " if self.ALTER_SET_TYPE else ""
sqlglot/generator.py:5929:        ret
…[1658 chars elided]…
and(this=ALTER, expression=TABLE t MODIFY c INT AFTER d)
ALTER TABLE t MODIFY c INT AFTER d
Alter(
  this=Table(
    this=Identifier(this=t, quoted=False)),
  kind=TABLE,
  exists=False,
  actions=[
    AlterColumn(
      this=Identifier(this=test_column, quoted=False),
      dtype=DataType(this=DType.LONGTEXT, nested=False),
      collate=False,
      using=False)],
  only=False,
  not_valid=False,
  check=False,
  cascade=False,
  iceberg=False)
ALTER TABLE t MODIFY COLUMN test_column LONGTEXT
[tool_use Bash] {"command": "sed -n 240,275p sqlglot/parsers/mysql.py; sed -n 695,725p sqlglot/generators/mysql.py; grep -n \"def _parse_column_def\\b\\|def _parse_column_def(\" -A 3 sqlglot/parser.py | head; grep -n \"ALTER_TABLE_ADD_REQUIRED\\|ALTER_TABLE_ADD\\|CHANGE\" sqlglot/parsers/mysql.py sqlglot/generators/mysql.py | head", "description": "Read MySQL parser and generator alter-related code"}
[tool_result]     SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
    SET_TRIE = new_trie(key.split(" ") for key in SET_PARSERS)

    CONSTRAINT_PARSERS = {
        **parser.Parser.CONSTRAINT_PARSERS,
        "FULLTEXT": lambda self: self._parse_index_constraint(kind="FULLTEXT"),
        "INDEX": lambda self: self._parse_index_constraint(),
        "KEY": lambda self: self._parse_index_constraint(),
        "SPATIAL": lambda self: self._parse_index_constraint(kind="SPATIAL"),
        "ZEROFILL": 
…[2202 chars elided]…
ef _prefixed_sql(self, prefix: str, expression: exp.Expr, arg: str) -> str:
        sql = self.sql(expression, arg)
        return f" {prefix} {sql}" if sql else ""

    def _oldstyle_limit_sql(self, expression: exp.Show) -> str:
7036:    def _parse_column_def(
7037-        self, this: exp.Expr | None, computed_column: bool = True
7038-    ) -> exp.Expr | None:
7039-        # column defs are not really columns, they're identifiers
0 matches for 'ALTER_TABLE_ADD_REQUIRED\|ALTER_TABLE_ADD\|CHANGE'
[tool_use Bash] {"command": "grep -n \"def alter_sql\" -A 40 sqlglot/generator.py | head -60; grep -n \"def _parse_column_def_with_exists\" -A 12 sqlglot/parser.py; sed -n 225,235p sqlglot/expressions/ddl.py; grep -n \"ModifyColumn\\|class .*Modify\" sqlglot/expressions/*.py", "description": "Read alter_sql generator and column-def parsing helpers"}
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
…[1760 chars elided]…
nDef):
8497-            self._retreat(start)
8498-            return None
8499-
8500-        expression.set("exists", exists_column)
8501-
class UserDefinedFunction(Expression):
    arg_types = {"this": True, "expressions": False, "wrapped": False}


class CharacterSet(Expression):
    arg_types = {"this": True, "default": False}


class AlterColumn(Expression):
    arg_types = {
        "this": True,
1 matches in 1 files:

sqlglot/expressions/ddl.py:286:class AlterModifySqlSecurity(Expression):
[tool_use Bash] {"command": "grep -n \"def _parse_field_def\" -A 6 sqlglot/parser.py; grep -n \"def _parse_column_def(\" -A 30 sqlglot/parser.py | head -45; sed -n 280,292p sqlglot/expressions/ddl.py; sed -n 1,30p sqlglot/parsers/mysql.py | grep -n \"import\"", "description": "Read field and column definition parser helpers"}
[tool_result] 7033:    def _parse_field_def(self) -> exp.Expr | None:
7034-        return self._parse_column_def(self._parse_field(any_token=True))
7035-
7036-    def _parse_column_def(
7037-        self, this: exp.Expr | None, computed_column: bool = True
7038-    ) -> exp.Expr | None:
7039-        # column defs are not really columns, they're identifiers
7036:    def _parse_column_def(
7037-        self, this: exp.Expr | None, computed_column: bool = True
7038-    ) -> exp.Expr | None:
7039-        # column
…[1277 chars elided]…
tch_set({TokenType.IN, TokenType.OUT}, advance=False):


class RenameIndex(Expression):
    arg_types = {"this": True, "to": True}


class AlterModifySqlSecurity(Expression):
    arg_types = {"expressions": True}


class SwapTable(Expression):
    pass

1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, parser
6:from sqlglot.trie import new_trie
7:from sqlglot.dialects.dialect import (
14:from sqlglot.helper import seq_get
15:from sqlglot.tokens import TokenType
[tool_use Bash] {"command": "grep -n \"    def _parse_\\|^class \" sqlglot/parsers/mysql.py | head -30; grep -n \"ModifySqlSecurity\\|class AlterColumn\" sqlglot/expressions/__init__.py | head -3", "description": "Find method layout in MySQL parser"}
[tool_result] 17 matches in 12 files:

305:0:
313:0:
339:0:
348:0:str | None = None) -> exp.IndexColumnConstraint:
496:0:str) -> exp.Expr:
500:0:
514:0:
538:0:
54:0:
580:0:
599:0:
sqlglot/parsers/mysql.py:318:def _parse_generated_as_identity(
sqlglot/parsers/mysql.py:395:def _parse_show_mysql(
sqlglot/parsers/mysql.py:481:def _parse_oldstyle_limit(
sqlglot/parsers/mysql.py:523:def _parse_type(
sqlglot/parsers/mysql.py:550:def _parse_partition_property(
sqlglot/parsers/mysql.py:607:def _parse_primary_key(
0 matches for 'ModifySqlSecurity\|class AlterColumn'
[tool_use Bash] {"command": "sed -n 548,560p sqlglot/parsers/mysql.py; grep -n \"_parse_partition_property\\|_parse_primary_key\" sqlglot/parsers/mysql.py; grep -n \"exp.AlterColumn\\|AlterColumn\" sqlglot/expressions/__init__.py sqlglot/expressions/ddl.py | head -3", "description": "Check MySQL parser module-level helper style"}
[tool_result]         return self.expression(exp.AlterIndex(this=index, visible=visible))

    def _parse_partition_property(
        self,
    ) -> exp.Expr | None | list[exp.Expr]:
        partition_cls: type[exp.Expr] | None = None
        value_parser = None

        if self._match_text_seq("RANGE"):
            partition_cls = exp.PartitionByRangeProperty
            value_parser = self._parse_partition_range_value
        elif self._match_text_seq("LIST"):
            partition_cls = exp.PartitionByListProperty
5 matches in 3 files:

228:0:lambda self: self._parse_partition_property(),
339:0:
sqlglot/parsers/mysql.py:550:def _parse_partition_property(
sqlglot/parsers/mysql.py:607:def _parse_primary_key(
sqlglot/parsers/mysql.py:613:return super()._parse_primary_key(
1 matches in 1 files:

sqlglot/expressions/ddl.py:233:class AlterColumn(Expression):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-182203-mysql-dialect-alter-table-modify/base-1/sqlglot/expressions/ddl.py", "old_string": "class AlterIndex(Expression):\n    arg_types = {\"this\": True, \"visible\": True}", "new_string": "class ModifyColumn(Expression):\n    arg_types = {\"this\": True}\n\n\nclass AlterIndex(Expression):\n    arg_types = {\"this\": True, \"visible\": True}"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-182203-mysql-dialect-alter-table-modify/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-182203-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py", "old_string": "        \"MODIFY\": lambda self: self._parse_alter_table_alter(),", "new_string": "        \"MODIFY\": lambda self: self._parse_alter_table_modify(),"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-182203-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-182203-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py", "old_string": "    def _parse_partition_property(\n        self,\n    ) -> exp.Expr | None | list[exp.Expr]:", "new_string": "    def _parse_alter_table_modify(self) -> exp.ModifyColumn | None:\n        self._match(TokenType.CO
…[184 chars elided]…
          position = self._prev.text\n            column_position = self.expression(\n                exp.ColumnPosition(this=self._parse_column(), position=position)\n            )\n            column.set(\"position\", column_position)\n\n        return self.expression(exp.ModifyColumn(this=column))\n\n    def _parse_partition_property(\n        self,\n    ) -> exp.Expr | None | list[exp.Expr]:"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-182203-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-182203-mysql-dialect-alter-table-modify/base-1/sqlglot/generators/mysql.py", "old_string": "    def altercolumn_sql(self, expression: exp.AlterColumn) -> str:\n        dtype = self.sql(expression, \"dtype\")\n        if not dtype:\n            return super().altercolumn_sql(expression)\n\n        thi
…[135 chars elided]…
ression: exp.AlterColumn) -> str:\n        dtype = self.sql(expression, \"dtype\")\n        if not dtype:\n            return super().altercolumn_sql(expression)\n\n        this = self.sql(expression, \"this\")\n        return f\"MODIFY COLUMN {this} {dtype}\"\n\n    def modifycolumn_sql(self, expression: exp.ModifyColumn) -> str:\n        return f\"MODIFY COLUMN {self.sql(expression, 'this')}\""}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-182203-mysql-dialect-alter-table-modify/base-1/sqlglot/generators/mysql.py has been updated successfully.
[assistant] Now the tests: I'll add new round-trip cases next to the existing MODIFY identity test, leaving the existing assertions untouched.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-182203-mysql-dialect-alter-table-modify/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT\")\n", "new_string": "        self.validate_identity(\"ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT\")\n
…[155 chars elided]…
RCHAR(50) NOT NULL DEFAULT 'foo'\")\n        self.validate_identity(\"ALTER TABLE t MODIFY COLUMN c INT COMMENT 'hi'\")\n        self.validate_identity(\"ALTER TABLE t MODIFY COLUMN c INT FIRST\")\n        self.validate_identity(\"ALTER TABLE t MODIFY COLUMN c INT AFTER d\")\n        self.validate_identity(\"ALTER TABLE t MODIFY c INT NOT NULL\", \"ALTER TABLE t MODIFY COLUMN c INT NOT NULL\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-182203-mysql-dialect-alter-table-modify/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t MODIFY COLUMN c INT NOT NULL DEFAULT 5','ALTER TABLE t MODIFY COLUMN c INT COMMENT \\'hi\\'','ALTER TABLE t MODIFY COLUMN c INT FIRST','ALTER TABLE t MODIFY c INT AFTER d','ALTER TABLE t MODIFY COLUMN c', 'ALTER TABLE t ALTER COLUMN c SET DATA TYPE LONGTEXT']:\n    e=sqlglot.parse_one(s,read='mysql'); print(type(e.args['actions'][0]).__name__ if hasattr(e,'args') and e.args.get('actions') else type(e).__name__); print(e.sql('mysql'))\n\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -15", "description": "Verify parsing output and run MySQL dialect tests"}
[tool_result] 'ALTER TABLE t MODIFY COLUMN c' contains unsupported syntax. Falling back to parsing as a 'Command'.
ModifyColumn
ALTER TABLE t MODIFY COLUMN c INT NOT NULL DEFAULT 5
ModifyColumn
ALTER TABLE t MODIFY COLUMN c INT COMMENT 'hi'
ModifyColumn
ALTER TABLE t MODIFY COLUMN c INT FIRST
ModifyColumn
ALTER TABLE t MODIFY COLUMN c INT AFTER d
Command
ALTER TABLE t MODIFY COLUMN c
AlterColumn
ALTER TABLE t MODIFY COLUMN c LONGTEXT
.............................. [ 60%]
....................                                              [100%]
50 passed, 481 subtests passed in 0.27s
[assistant] MySQL tests pass. Running the full suite the project uses, plus lint on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; (command -v ruff >/dev/null && ruff check sqlglot/parsers/mysql.py sqlglot/generators/mysql.py sqlglot/expressions/ddl.py tests/dialects/test_mysql.py && ruff format --check sqlglot tests/dialects/test_mysql.py) 2>&1 | tail -8", "description": "Run full test suite and ruff checks"}
[tool_result] ................................... [ 46%]
...................................................................................................... [ 55%]
.................................................................................................................................................................................. [ 71%]
............................................. [ 75%]
............................................. [ 79%]
............................... [ 82%]
............................................................................................................................................................................................                                           [100%]
1094 passed, 17872 subtests passed in 47.49s
Ruff: No issues found
Ruff format: 1 files need formatting
═══════════════════════════════════════
1. test_mysql.py

[hint] Run `ruff format` to format these files
[tool_use Bash] {"command": "ruff format tests/dialects/test_mysql.py && git diff --stat && git diff tests/dialects/test_mysql.py | head -30", "description": "Format test file and show diff stats"}
[tool_result] 1 file reformatted
sqlglot/expressions/ddl.py   |  4 ++++
 sqlglot/generators/mysql.py  |  3 +++
 sqlglot/parsers/mysql.py     | 17 ++++++++++++++++-
 tests/dialects/test_mysql.py |  8 ++++++++
 4 files changed, 31 insertions(+), 1 deletion(-)
tests/dialects/test_mysql.py | 8 ++++++++
 1 file changed, 8 insertions(+)

--- Changes ---

tests/dialects/test_mysql.py
  @@ -38,6 +38,14 @@ class TestMySQL(Validator):
  +        self.validate_identity("ALTER TABLE t MODIFY COLUMN c INT NOT NULL DEFAULT
…[354 chars elided]…
    self.validate_identity(
  +            "ALTER TABLE t MODIFY c INT NOT NULL", "ALTER TABLE t MODIFY COLUMN c INT NOT NULL"
  +        )
           self.validate_identity("ALTER TABLE t AUTO_INCREMENT=3000000000")
           self.validate_identity("ALTER VIEW v AS SELECT a, b, c, d FROM foo")
           self.validate_identity("ALTER VIEW v AS SELECT * FROM foo WHERE c > 100")
  +8 -0
[This command modified 1 file you've previously read: tests/dialects/test_mysql.py. Call Read before editing.]
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; ruff format --check sqlglot tests/dialects/test_mysql.py | tail -1; ruff check sqlglot tests/dialects/test_mysql.py | tail -1", "description": "Re-run full suite and format check after formatting"}
[tool_result] ............................................................................................................................................................................................                                           [100%]
1094 passed, 17872 subtests passed in 48.03s
175 files already formatted
Ruff: No issues found
[assistant] MySQL `ALTER TABLE ... MODIFY [COLUMN] col_name column_definition [FIRST | AFTER col]` now parses into a real column definition and round-trips. The full suite passes (1094 tests), and ruff check and format are clean.

Before the change, these statements fell back to `exp.Command` because the MySQL `MODIFY` hook reused the ALTER COLUMN parser, which has no way to take constraints, `COMMENT`, or a position. Now `MODIFY` gets its own parser.

Changes:
- **`sqlglot/expressions/ddl.py`**: new `ModifyColumn(this=ColumnDef)` expression. I kept it separate from `AlterColumn` because the semantics dif
…[557 chars elided]…
T NOT NULL` case that normalizes to `MODIFY COLUMN`. Existing assertions are untouched.

Decisions to check:
- `ALTER COLUMN c SET DATA TYPE` still generates `MODIFY COLUMN c <type>` in MySQL, so the existing transpile test is unaffected.
- The new `ModifyColumn` node has no generator outside MySQL. Transpiling it to another dialect will produce the generic fallback output, not valid SQL there. I didn't add handling for that because nothing in the request asked for it.
- `ALTER TABLE t MODIFY COLUMN c` with no type still falls back to `Command`, since a column definition needs a type in MySQL.
