# trajectory base-1

final message:
The MySQL dialect now parses and round-trips `ALTER TABLE ... CHANGE [COLUMN] old new_def [FIRST | AFTER col]`. The full test suite passes (1106 passed), and ruff check and format are clean.

Previously these statements fell back to a raw `Command`. Now they parse into the same `ModifyColumn` node that `MODIFY COLUMN` uses, with one extra arg:

- **`sqlglot/expressions/ddl.py`**: `ModifyColumn` gets `arg_types = {"this": True, "old_name": False}`. `this` is the new column definition, `old_name` is the original name.
- **`sqlglot/parsers/mysql.py`**: `CHANGE` is registered in `ALTER_PARSERS`, handled by a new `_parse_alter_table_change`. It reads the optional `COLUMN` keyword, the old name, then the column definition, which already covers `FIRST`/`AFTER`.
- **`sqlglot/generators/mysql.py`**: a `modifycolumn_sql` override emits `CHANGE COLUMN old new_def` when `old_name` is set and otherwise defers to the base `MODIFY COLUMN` output.
- **`tests/dialects/test_mysql.py`**: identity tests for `CHANGE COLUMN` with `NOT NULL`, `AFTER`, and `FIRST`, plus a `CHANGE` (no `COLUMN`) → `CHANGE COLUMN` normalization case.

Choices you may want to redirect:
- I named the extra arg `old_name`.
- `CHANGE` always generates with the `COLUMN` keyword, matching how `MODIFY` always generates `MODIFY COLUMN`.
- Other dialects still output `MODIFY COLUMN` if a `ModifyColumn` carries `old_name`, which drops the rename. Only MySQL can produce that node today, so I left it alone.

I haven't committed anything.

## events
[tool_use Bash] {"command": "grep -n -i \"modify\" sqlglot/dialects/mysql.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -50; grep -n -i \"change\\|modify\" tests/dialects/test_mysql.py | head -30", "description": "Find MODIFY/CHANGE handling in MySQL and base code"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:470:    # Whether ALTER TABLE ... MODIFY COLUMN column-redefinition syntax is supported
sqlglot/generator.py:471:    SUPPORTS_MODIFY_COLUMN = False
sqlglot/generator.py:4009:    def modifycolumn_sql(self, expression: exp.ModifyColumn) -> str:
sqlglot/generator.py:4010:        if not self.SUPPORTS_MODIFY_COLUMN:
sqlglot/generator.py:4011:            self.unsupported("MODIFY COLUMN is not supported in this diale
…[955 chars elided]…

48:        self.validate_identity("ALTER TABLE t MODIFY COLUMN c INT NOT NULL AFTER d")
50:            "ALTER TABLE t MODIFY c INT NOT NULL",
51:            "ALTER TABLE t MODIFY COLUMN c INT NOT NULL",
179:            "ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT",
1689:            "CREATE TRIGGER audit_update AFTER UPDATE ON accounts FOR EACH ROW BEGIN INSERT INTO audit_log (user_id, old_balance, new_balance, changed_at) VALUES (OLD.user_id, OLD.balance, NEW.balance, NOW()) END",
[tool_use Bash] {"command": "grep -rn -i \"ModifyColumn\\|MODIFY\" sqlglot/ --include=*.py | grep -v \"AlterModify\" | head -40; echo ---; grep -n \"class ModifyColumn\" -A6 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null; echo ---; grep -n \"ModifyColumn\\|MODIFY\" -B3 -A25 sqlglot/dialects/mysql.py | head -120", "description": "Locate ModifyColumn across sqlglot sources"}
[tool_result] (eval):1: no matches found: --include=*.py
---
sqlglot/expressions/ddl.py:248:class ModifyColumn(Expression):
sqlglot/expressions/ddl.py-249-    pass
sqlglot/expressions/ddl.py-250-
sqlglot/expressions/ddl.py-251-
sqlglot/expressions/ddl.py-252-class AlterIndex(Expression):
sqlglot/expressions/ddl.py-253-    arg_types = {"this": True, "visible": True}
sqlglot/expressions/ddl.py-254-
---
[tool_use Bash] {"command": "grep -rn \"ModifyColumn\\|MODIFY\" sqlglot/ | grep -v AlterModify; echo ---; grep -n \"MODIFY\\|ModifyColumn\" -B3 -A3 sqlglot/parser.py sqlglot/dialects/mysql.py | head -80", "description": "Search for ModifyColumn and MODIFY usage in sqlglot"}
[tool_result] sqlglot/generator.py:470:    # Whether ALTER TABLE ... MODIFY COLUMN column-redefinition syntax is supported
sqlglot/generator.py:471:    SUPPORTS_MODIFY_COLUMN = False
sqlglot/generator.py:4009:    def modifycolumn_sql(self, expression: exp.ModifyColumn) -> str:
sqlglot/generator.py:4010:        if not self.SUPPORTS_MODIFY_COLUMN:
sqlglot/generator.py:4011:            self.unsupported("MODIFY COLUMN is not supported in this dialect")
sqlglot/generator.py:4012:        return f"MODIFY COLUMN {sel
…[183 chars elided]…
),
sqlglot/parsers/snowflake.py:743:        "MODIFY": lambda self: self._parse_alter_table_alter(),
sqlglot/parsers/mysql.py:255:        "MODIFY": lambda self: self._parse_alter_table_modify(),
sqlglot/parsers/mysql.py:329:        return self.expression(exp.ModifyColumn(this=column_def))
sqlglot/expressions/ddl.py:248:class ModifyColumn(Expression):
sqlglot/generators/mysql.py:114:    SUPPORTS_MODIFY_COLUMN = True
sqlglot/generators/mysql.py:720:        return f"MODIFY COLUMN {this} {dtype}"
---
[tool_use Bash] {"command": "sed -n 240,265p sqlglot/parsers/mysql.py; echo ...; sed -n 300,340p sqlglot/parsers/mysql.py; echo ---GEN; sed -n 700,725p sqlglot/generators/mysql.py; echo ---; grep -n \"CHANGE\" sqlglot/parsers/mysql.py sqlglot/generators/mysql.py sqlglot/parser.py sqlglot/tokens.py | head; grep -n \"change\" tests/dialects/test_mysql.py | head", "description": "Inspect MySQL ALTER TABLE modify parsing and generation"}
[tool_result]     SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
    SET_TRIE = new_trie(key.split(" ") for key in SET_PARSERS)

    CONSTRAINT_PARSERS = {
        **parser.Parser.CONSTRAINT_PARSERS,
        "FULLTEXT": lambda self: self._parse_index_constraint(kind="FULLTEXT"),
        "INDEX": lambda self: self._parse_index_constraint(),
        "KEY": lambda self: self._parse_index_constraint(),
        "SPATIAL": lambda self: self._parse_index_constraint(kind="SPATIAL"),
        "ZEROFILL": 
…[3241 chars elided]…
dtype}"

    def _prefixed_sql(self, prefix: str, expression: exp.Expr, arg: str) -> str:
        sql = self.sql(expression, arg)
        return f" {prefix} {sql}" if sql else ""

---
sqlglot/parser.py:4916:        if not self._match_text_seq("CHANGES", "(", "INFORMATION", "=>"):
1689:            "CREATE TRIGGER audit_update AFTER UPDATE ON accounts FOR EACH ROW BEGIN INSERT INTO audit_log (user_id, old_balance, new_balance, changed_at) VALUES (OLD.user_id, OLD.balance, NEW.balance, NOW()) END",
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -I -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t CHANGE c d INT NOT NULL AFTER x','ALTER TABLE t CHANGE COLUMN c d INT','ALTER TABLE t MODIFY COLUMN c INT FIRST']:\n    try:\n        e=sqlglot.parse_one(s,read='mysql'); print(repr(e)[:600]); print(e.sql('mysql'))\n    except Exception as ex: print('ERR',ex)\n\"; grep -n \"class ColumnDef\\b\" -A12 sqlglot/expressions/*.py | head -30; grep -n \"ModifyColumn\\|modify\" sqlglot/parser.py | head", "description": "Check current parsing of CHANGE and MODIFY statements"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
sqlglot/expressions/query.py:502:class ColumnDef(Expression):
sqlglot/expressions/query.py-503-    arg_types = {
sqlglot/expressions/query.py-504-        "this": True,
sqlglot/expressions/query.py-505-        "kind": False,
sqlglot/expressions/query.py-506-        "constraints": False,
sqlglot/expressions/query.py-507-        "exists": False,
sqlglot/expressions/query.py-508-        "position": False,
sqlglot/expressions/query.py-509-        "default": False,
sqlglot/expressions/query.py-510-        "output": False,
sqlglot/expressions/query.py-511-    }
sqlglot/expressions/query.py-512-
sqlglot/expressions/query.py-513-    @property
sqlglot/expressions/query.py-514-    def constraints(self) -> list[ColumnConstraint]:
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=. $P -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t CHANGE c d INT NOT NULL AFTER x','ALTER TABLE t CHANGE COLUMN c d INT','ALTER TABLE t MODIFY COLUMN c INT FIRST']:\n    try:\n        e=sqlglot.parse_one(s,read='mysql'); print(repr(e)[:700]); print(e.sql('mysql'))\n    except Exception as ex: print('ERR',ex)\n\"", "description": "Check current parsing of CHANGE and MODIFY statements"}
[tool_result] 'ALTER TABLE t CHANGE c d INT NOT NULL AFTER x' contains unsupported syntax. Falling back to parsing as a 'Command'.
'ALTER TABLE t CHANGE COLUMN c d INT' contains unsupported syntax. Falling back to parsing as a 'Command'.
Command(this=ALTER, expression=TABLE t CHANGE c d INT NOT NULL AFTER x)
ALTER TABLE t CHANGE c d INT NOT NULL AFTER x
Command(this=ALTER, expression=TABLE t CHANGE COLUMN c d INT)
ALTER TABLE t CHANGE COLUMN c d INT
Alter(
  this=Table(
    this=Identifier(this=t, quoted=False)),
  kind=TABLE,
  exists=False,
  actions=[
    ModifyColumn(
      this=ColumnDef(
        this=Identifier(this=c, quoted=False),
        kind=DataType(this=DType.INT, nested=False),
        position=ColumnPosition(position=FIRST)))],
  only=False,
  not_valid=False,
  check=False,
  cascade=False,
  iceberg=False)
ALTER TABLE t MODIFY COLUMN c INT FIRST
[tool_use Bash] {"command": "grep -n \"_match_texts(self.ALTER_PARSERS\\|ALTER_PARSERS\\b\" sqlglot/parser.py | head -5; sed -n 240,252p sqlglot/expressions/ddl.py; grep -n \"class RenameColumn\\|class AlterRename\" -A3 sqlglot/expressions/ddl.py; grep -n \"def _parse_column_def\" -A3 sqlglot/parser.py | head; grep -n \"Parser.*ALTER\\|_parse_alter_table_modify\\|MODIFY\" tests/dialects/test_mysql.py | head -3; sed -n 40,60p tests/dialects/test_mysql.py", "description": "Check ALTER parser dispatch and test conventions"}
[tool_result] 1435:    ALTER_PARSERS: t.ClassVar = {
1449:    ALTER_ALTER_PARSERS: t.ClassVar = {
8633:        if self._match_texts(self.ALTER_ALTER_PARSERS):
8634:            return self.ALTER_ALTER_PARSERS[self._prev.text.upper()](self)
8790:        parser = self.ALTER_PARSERS.get(self._prev.text.upper()) if self._prev else None
        "drop": False,
        "comment": False,
        "allow_null": False,
        "visible": False,
        "rename_to": False,
    }


class ModifyColumn(Expression):
    pass

…[1675 chars elided]…
NOT NULL",
        )
        self.validate_identity("ALTER TABLE t AUTO_INCREMENT=3000000000")
        self.validate_identity("ALTER VIEW v AS SELECT a, b, c, d FROM foo")
        self.validate_identity("ALTER VIEW v AS SELECT * FROM foo WHERE c > 100")
        self.validate_identity(
            "ALTER ALGORITHM = MERGE VIEW v AS SELECT * FROM foo", check_command_warning=True
        )
        self.validate_identity(
            "ALTER DEFINER = 'admin'@'localhost' VIEW v AS SELECT * FROM foo",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-091250-mysql-dialect-support-change-col/base-1/sqlglot/expressions/ddl.py", "old_string": "class ModifyColumn(Expression):\n    pass", "new_string": "class ModifyColumn(Expression):\n    arg_types = {\"this\": True, \"old_name\": False}"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-091250-mysql-dialect-support-change-col/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-091250-mysql-dialect-support-change-col/base-1/sqlglot/parsers/mysql.py", "old_string": "        \"MODIFY\": lambda self: self._parse_alter_table_modify(),\n        \"AUTO_INCREMENT\"", "new_string": "        \"MODIFY\": lambda self: self._parse_alter_table_modify(),\n        \"CHANGE\": lambda self: self._parse_alter_table_change(),\n        \"AUTO_INCREMENT\""}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-091250-mysql-dialect-support-change-col/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-091250-mysql-dialect-support-change-col/base-1/sqlglot/parsers/mysql.py", "old_string": "        return self.expression(exp.ModifyColumn(this=column_def))\n\n    def _parse_generated_as_identity(", "new_string": "        return self.expression(exp.ModifyColumn(this=column_def))\n\n    def _parse_alte
…[126 chars elided]…
ken=True)\n        column = self._parse_field(any_token=True)\n        if old_name is None or column is None:\n            return None\n\n        column_def = self._parse_column_def(column)\n        if not isinstance(column_def, exp.ColumnDef):\n            return None\n\n        return self.expression(exp.ModifyColumn(this=column_def, old_name=old_name))\n\n    def _parse_generated_as_identity("}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-091250-mysql-dialect-support-change-col/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-091250-mysql-dialect-support-change-col/base-1/sqlglot/generators/mysql.py", "old_string": "    def altercolumn_sql(self, expression: exp.AlterColumn) -> str:\n        dtype = self.sql(expression, \"dtype\")", "new_string": "    def modifycolumn_sql(self, expression: exp.ModifyColumn) -> str:\n        old_name = expression.args.get(\"old_name\")\n        if not old_name:\n            return super().modifycolumn_sql(expression)\n\n        return f\"CHANGE COLUMN {self.sql(old_name)} {self.sql(expression, 'this')}\"\n\n    def altercolumn_sql(self, expression: exp.AlterColumn) -> str:\n        dtype = self.sql(expression, \"dtype\")"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-091250-mysql-dialect-support-change-col/base-1/sqlglot/generators/mysql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-091250-mysql-dialect-support-change-col/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"ALTER TABLE t AUTO_INCREMENT=3000000000\")", "new_string": "        self.validate_identity(\"ALTER TABLE t CHANGE COLUMN c d INT NOT NULL\")\n        self.validate_identity(\"ALTER TABLE t CHANGE COLUMN c d INT NOT NULL AFTER e\")\n        self.validate_identity(\"ALTER TABLE t CHANGE COLUMN c d INT FIRST\")\n        self.validate_identity(\n            \"ALTER TABLE t CHANGE c d INT NOT NULL\",\n            \"ALTER TABLE t CHANGE COLUMN c d INT NOT NULL\",\n        )\n        self.validate_identity(\"ALTER TABLE t AUTO_INCREMENT=3000000000\")"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-091250-mysql-dialect-support-change-col/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=. $P -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t CHANGE c d INT NOT NULL AFTER x','ALTER TABLE t CHANGE COLUMN c d INT','ALTER TABLE t CHANGE c d INT FIRST']:\n    e=sqlglot.parse_one(s,read='mysql'); print(e.sql('mysql'), '|', type(e.args['actions'][0]).__name__, e.args['actions'][0].args.get('old_name'))\n\"; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify CHANGE round trips and run full test suite"}
[tool_result] ALTER TABLE t CHANGE COLUMN c d INT NOT NULL AFTER x | ModifyColumn c
ALTER TABLE t CHANGE COLUMN c d INT | ModifyColumn c
ALTER TABLE t CHANGE COLUMN c d INT FIRST | ModifyColumn c
........................... [  8%]
............. [  9%]
........................................................................................................................................ [ 21%]
............................................................................................ [ 30%]
..................
…[427 chars elided]…
........................................................................... [ 73%]
................................................................................................................................... [ 85%]
............................. [ 87%]
.............................................................................. [ 94%]
........................................................                                                [100%]
1106 passed, 17999 subtests passed in 51.49s
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin; ($P/ruff check sqlglot/parsers/mysql.py sqlglot/generators/mysql.py sqlglot/expressions/ddl.py tests/dialects/test_mysql.py && $P/ruff format --check sqlglot/parsers/mysql.py sqlglot/generators/mysql.py sqlglot/expressions/ddl.py tests/dialects/test_mysql.py) 2>&1 | tail -5; git status --short", "description": "Lint and format-check the changed files"}
[tool_result] All checks passed!
4 files already formatted
 M sqlglot/expressions/ddl.py
 M sqlglot/generators/mysql.py
 M sqlglot/parsers/mysql.py
 M tests/dialects/test_mysql.py
[assistant] The MySQL dialect now parses and round-trips `ALTER TABLE ... CHANGE [COLUMN] old new_def [FIRST | AFTER col]`. The full test suite passes (1106 passed), and ruff check and format are clean.

Previously these statements fell back to a raw `Command`. Now they parse into the same `ModifyColumn` node that `MODIFY COLUMN` uses, with one extra arg:

- **`sqlglot/expressions/ddl.py`**: `ModifyColumn` gets `arg_types = {"this": True, "old_name": False}`. `this` is the new column definition, `old_name` is the original name.
- **`sqlglot/parsers/mysql.py`**: `CHANGE` is registered in `ALTER_PARSERS`, h
…[308 chars elided]…
s to the base `MODIFY COLUMN` output.
- **`tests/dialects/test_mysql.py`**: identity tests for `CHANGE COLUMN` with `NOT NULL`, `AFTER`, and `FIRST`, plus a `CHANGE` (no `COLUMN`) → `CHANGE COLUMN` normalization case.

Choices you may want to redirect:
- I named the extra arg `old_name`.
- `CHANGE` always generates with the `COLUMN` keyword, matching how `MODIFY` always generates `MODIFY COLUMN`.
- Other dialects still output `MODIFY COLUMN` if a `ModifyColumn` carries `old_name`, which drops the rename. Only MySQL can produce that node today, so I left it alone.

I haven't committed anything.
