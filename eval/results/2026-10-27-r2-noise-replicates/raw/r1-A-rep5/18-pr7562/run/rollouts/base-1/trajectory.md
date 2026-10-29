# trajectory base-1

final message:
MySQL `ALTER TABLE ... MODIFY [COLUMN] col_name column_definition [FIRST | AFTER col]` now parses into its own `ModifyColumn` expression and round-trips. All four examples from your request come back unchanged. The full suite passes (1094 tests) and ruff is clean. I left the changes uncommitted.

What changed:

- **`sqlglot/expressions/ddl.py`**: new `ModifyColumn` expression, with `this` holding a `ColumnDef`.
- **`sqlglot/parsers/mysql.py`**: `MODIFY` now routes to a new `_parse_alter_table_modify`, which reads an optional `COLUMN`, a full column definition, and an optional position. Before, `MODIFY` went through the `ALTER COLUMN` parser and only the type was kept. Forms like `MODIFY COLUMN c INT COMMENT 'hi'` were turned into a table-option comment, and `FIRST`/`AFTER` fell back to a raw `Command`.
- **`sqlglot/parser.py`**: pulled the `FIRST`/`AFTER` parsing out of `_parse_add_column` into `_parse_column_position`, so `ADD` and `MODIFY` share it.
- **`sqlglot/generator.py`**: `modifycolumn_sql` emits `MODIFY COLUMN <column def>`. The base generator is used because the expression is only produced by the MySQL parser and MySQL-derived dialects inherit it.
- **`tests/dialects/test_mysql.py`**: added round-trip cases for the four forms, plus `MODIFY c INT NOT NULL AFTER d`, which normalizes to `MODIFY COLUMN c ...`.

The existing `ALTER COLUMN ... SET DATA TYPE` → `MODIFY COLUMN` mapping is unchanged, and its test still passes. Snowflake and ClickHouse `MODIFY` handling is untouched.

## events
[tool_use Bash] {"command": "grep -n -i \"modify\\|ALTER_TABLE\\|AlterColumn\\|alter_column\" sqlglot/dialects/mysql.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -80", "description": "Find MODIFY and alter-related code"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:396:    ALTER_TABLE_INCLUDE_COLUMN_KEYWORD = True
sqlglot/generator.py:3903:    def altercolumn_sql(self, expression: exp.AlterColumn) -> str:
sqlglot/generator.py:3986:        if not self.dialect.ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN and isinstance(
sqlglot/generator.py:4021:            if expression.args.get("cascade") and self.dialect.ALTER_TABLE_SUPPORTS_CASCADE
sqlglot/generator.py:4038:        elif is
…[1837 chars elided]…
t/parser.py:8633:    def _parse_alter_table_drop(self) -> list[exp.Expr]:
sqlglot/parser.py:8643:    def _parse_alter_table_rename(self) -> exp.AlterRename | exp.RenameColumn | None:
sqlglot/parser.py:8658:    def _parse_alter_table_set(self) -> exp.AlterSet:
sqlglot/parser.py:8725:            this = self._parse_table(schema=True, parse_partition=self.ALTER_TABLE_PARTITIONS)
sqlglot/parser.py:8737:            cascade = self.dialect.ALTER_TABLE_SUPPORTS_CASCADE and self._match_text_seq("CASCADE")
[tool_use Bash] {"command": "sed -n 1425,1450p sqlglot/parser.py; echo ----; sed -n 8530,8660p sqlglot/parser.py; echo ----; sed -n 3900,3935p sqlglot/generator.py; echo ----; sed -n 3975,4060p sqlglot/generator.py; echo ----; grep -n \"class AlterColumn\\|class ColumnDef\\|class AlterTable\" -A22 sqlglot/expressions/*.py | head -120", "description": "Read alter table parser and generator code"}
[tool_result]             #  - For Trino, it's reversed - `bucket(<col name>, <num buckets>)` or `truncate(<col_name>, <num_chars>)`
            # Both variants are canonicalized in the latter i.e `bucket(<col name>, <num buckets>)`
            #
            # Hive ref: https://docs.aws.amazon.com/athena/latest/ug/querying-iceberg-creating-tables.html#querying-iceberg-partitioning
            # Trino ref: https://docs.aws.amazon.com/athena/latest/ug/create-table-as.html#ctas-table-properties
            this,
…[13666 chars elided]…
ts") or []
sqlglot/expressions/query.py-515-
sqlglot/expressions/query.py-516-    @property
sqlglot/expressions/query.py-517-    def kind(self) -> DataType | None:
sqlglot/expressions/query.py-518-        return self.args.get("kind")
sqlglot/expressions/query.py-519-
sqlglot/expressions/query.py-520-
sqlglot/expressions/query.py-521-class Changes(Expression):
sqlglot/expressions/query.py-522-    arg_types = {"information": True, "at_before": False, "end": False}
sqlglot/expressions/query.py-523-
[tool_use Bash] {"command": "grep -rn \"MODIFY\\|FIRST\\|AFTER\" sqlglot/dialects/mysql.py | head -30; echo ----; grep -n \"position\" sqlglot/parser.py sqlglot/generator.py | head -30; echo ----; grep -rn \"MODIFY\\|ALTER TABLE.*FIRST\\|AFTER\" tests/dialects/test_mysql.py | head -30; echo ----; grep -n \"ALTER_PARSERS\\|ALTER_TABLE_ADD_REQUIRED\" sqlglot/dialects/mysql.py sqlglot/dialects/dialect.py sqlglot/parser.py | head; echo; grep -n \"def _parse_column_def\\b\" -A60 sqlglot/parser.py | grep -n \"position\\|FIRST\\|AFTER\" ", "description": "Search MySQL dialect and parser for MODIFY/position"}
[tool_result] ----
sqlglot/parser.py:171:    return exp.Trim(this=this, expression=expression, position="LEADING" if is_left else "TRAILING")
sqlglot/parser.py:180:def build_locate_strposition(args: BuilderArgs) -> exp.StrPosition:
sqlglot/parser.py:184:        position=seq_get(args, 2),
sqlglot/parser.py:405:        "CHARINDEX": lambda args: build_locate_strposition(args),
sqlglot/parser.py:407:        "LOCATE": lambda args: build_locate_strposition(args),
sqlglot/parser.py:1509:        "POSITION": lambda se
…[2551 chars elided]…
qlglot/parser.py:1434:    ALTER_PARSERS: t.ClassVar = {
sqlglot/parser.py:1448:    ALTER_ALTER_PARSERS: t.ClassVar = {
sqlglot/parser.py:8563:            not self.dialect.ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN
sqlglot/parser.py:8577:        if self._match_texts(self.ALTER_ALTER_PARSERS):
sqlglot/parser.py:8578:            return self.ALTER_ALTER_PARSERS[self._prev.text.upper()](self)
sqlglot/parser.py:8732:        parser = self.ALTER_PARSERS.get(self._prev.text.upper()) if self._prev else None
[tool_use Bash] {"command": "sed -n 8495,8530p sqlglot/parser.py; echo ----; sed -n 1130,1160p sqlglot/generator.py; echo ----; sed -n 155,175p tests/dialects/test_mysql.py; sed -n 36,42p tests/dialects/test_mysql.py; echo ----; sed -n 8715,8760p sqlglot/parser.py; echo ---; grep -n \"class ColumnPosition\" -A3 sqlglot/expressions/*.py; grep -n \"ALTER_TABLE_ADD_REQUIRED\\|ALTER_TABLE\" sqlglot/dialects/mysql.py; grep -n \"class MySQL\" sqlglot/dialects/mysql.py", "description": "Read column position parsing and MySQL tests"}
[tool_result]         if not isinstance(expression, exp.ColumnDef):
            self._retreat(start)
            return None

        expression.set("exists", exists_column)

        return expression

    def _parse_add_column(self) -> exp.ColumnDef | None:
        if not self._prev.text.upper() == "ADD":
            return None

        expression = self._parse_column_def_with_exists()
        if not expression:
            return None

        # https://docs.databricks.com/delta/update-schema.html#explicit
…[5327 chars elided]…
       iceberg=iceberg,
                    )
                )

        return self._parse_as_command(start)

    def _parse_analyze(self) -> exp.Analyze | exp.Command:
        start = self._prev
        # https://duckdb.org/docs/sql/statements/analyze
---
sqlglot/expressions/query.py:497:class ColumnPosition(Expression):
sqlglot/expressions/query.py-498-    arg_types = {"this": False, "position": True}
sqlglot/expressions/query.py-499-
sqlglot/expressions/query.py-500-
14:class MySQL(Dialect):
[tool_use Bash] {"command": "grep -n \"MODIFY\\|ALTER_SET_TYPE\\|altercolumn\" sqlglot/dialects/mysql.py; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t MODIFY COLUMN c INT NOT NULL DEFAULT 5','ALTER TABLE t MODIFY COLUMN c VARCHAR(50) NOT NULL DEFAULT \\'foo\\'','ALTER TABLE t MODIFY COLUMN c INT COMMENT \\'hi\\'','ALTER TABLE t MODIFY COLUMN c INT FIRST','ALTER TABLE t MODIFY COLUMN c INT AFTER d']:\n    e=sqlglot.parse_one(s,read='mysql'); print(repr(e)[:300]); print(e.sql('mysql'))\n\"", "description": "Check current MySQL MODIFY parsing behavior"}
[tool_result] 'ALTER TABLE t MODIFY COLUMN c INT NOT NULL DEFAULT 5' contains unsupported syntax. Falling back to parsing as a 'Command'.
'ALTER TABLE t MODIFY COLUMN c VARCHAR(50) NOT NULL DEFAULT 'foo'' contains unsupported syntax. Falling back to parsing as a 'Command'.
'ALTER TABLE t MODIFY COLUMN c INT FIRST' contains unsupported syntax. Falling back to parsing as a 'Command'.
'ALTER TABLE t MODIFY COLUMN c INT AFTER d' contains unsupported syntax. Falling back to parsing as a 'Command'.
Command(this=ALT
…[336 chars elided]…

  kind=TABLE,
  exists=False,
  actions=[
    AlterColumn(
      this=Identifier(this=c, quoted=False),
      dtype=DataType(this=DType.INT, nested=False),
      collate=False,
      using=False)],
  only=False,
  options=[
    SchemaC
ALTER TABLE t MODIFY COLUMN c INT, COMMENT='hi'
Command(this=ALTER, expression=TABLE t MODIFY COLUMN c INT FIRST)
ALTER TABLE t MODIFY COLUMN c INT FIRST
Command(this=ALTER, expression=TABLE t MODIFY COLUMN c INT AFTER d)
ALTER TABLE t MODIFY COLUMN c INT AFTER d
[tool_use Bash] {"command": "grep -rn \"MODIFY\" sqlglot/ | grep -v \"^sqlglot/dialects/tsql\\|oracle\" | head -30; echo ----; grep -n \"class AlterModifySqlSecurity\" -A5 sqlglot/expressions/*.py; grep -n \"altermodifysqlsecurity\\|AlterModifySqlSecurity\" -B3 -A3 sqlglot/parser.py | head -30; echo ----; grep -n \"ALTER_PARSERS\" sqlglot/dialects/*.py | head; echo ----; grep -n \"def _parse_column_def\\b\" -A50 sqlglot/parser.py | head -80", "description": "Search for MODIFY usages and column def parsing"}
[tool_result] sqlglot/generator.py:5929:        return f"MODIFY {props}"
sqlglot/parsers/clickhouse.py:445:        "MODIFY": lambda self: self._parse_alter_table_modify(),
sqlglot/parsers/snowflake.py:742:        "MODIFY": lambda self: self._parse_alter_table_alter(),
sqlglot/parsers/mysql.py:255:        "MODIFY": lambda self: self._parse_alter_table_alter(),
sqlglot/generators/mysql.py:719:        return f"MODIFY COLUMN {this} {dtype}"
----
sqlglot/expressions/ddl.py:286:class AlterModifySqlSecurity(Expressi
…[2087 chars elided]…
f (
7075-            kind
7076-            and self._match(TokenType.ALIAS, advance=False)
7077-            and (
7078-                not self.WRAPPED_TRANSFORM_COLUMN_CONSTRAINT
7079-                or self._next.token_type == TokenType.L_PAREN
7080-            )
7081-        ):
7082-            self._advance()
7083-            constraints.append(
7084-                self.expression(
7085-                    exp.ColumnConstraint(
7086-                        kind=exp.ComputedColumnConstraint(
[tool_use Bash] {"command": "sed -n 240,275p sqlglot/parsers/mysql.py; echo ----; sed -n 700,725p sqlglot/generators/mysql.py; echo ----; sed -n 436,450p sqlglot/parsers/clickhouse.py; grep -n \"_parse_alter_table_modify\" -A25 sqlglot/parsers/clickhouse.py | sed -n 3,40p; echo ----; grep -n \"ALTER_TABLE_ADD\\|ALTER_SET_TYPE\" sqlglot/generators/mysql.py sqlglot/dialects/mysql.py sqlglot/generator.py | head; echo ---; ls tests/dialects | head -3; git log --oneline -1", "description": "Inspect MySQL parser/generator alter handling"}
[tool_result]     SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
    SET_TRIE = new_trie(key.split(" ") for key in SET_PARSERS)

    CONSTRAINT_PARSERS = {
        **parser.Parser.CONSTRAINT_PARSERS,
        "FULLTEXT": lambda self: self._parse_index_constraint(kind="FULLTEXT"),
        "INDEX": lambda self: self._parse_index_constraint(),
        "KEY": lambda self: self._parse_index_constraint(),
        "SPATIAL": lambda self: self._parse_index_constraint(kind="SPATIAL"),
        "ZEROFILL": 
…[4162 chars elided]…
())
840-
841-    def _parse_projection_def(self) -> exp.ProjectionDef | None:
842-        if not self._match_text_seq("PROJECTION"):
----
sqlglot/generator.py:563:    ALTER_SET_TYPE = "SET DATA TYPE"
sqlglot/generator.py:3912:            alter_set_type = self.ALTER_SET_TYPE + " " if self.ALTER_SET_TYPE else ""
sqlglot/generator.py:3986:        if not self.dialect.ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN and isinstance(
---
__init__.py
test_athena.py
test_bigquery.py
9ed34eee7 lithify: probe base
[tool_use Bash] {"command": "grep -n \"def _parse_column_def_with_exists\" -A12 sqlglot/parser.py; grep -n \"def _parse_field_def\" -A6 sqlglot/parser.py; grep -n \"altermodifysqlsecurity_sql\" -B2 -A3 sqlglot/generator.py; grep -n \"class AlterModifySqlSecurity\" -B2 -A3 sqlglot/expressions/ddl.py; grep -rn \"AlterModifySqlSecurity\" sqlglot/ | grep -v \"expressions/ddl.py\"", "description": "Inspect column-def helpers and modify-related generator"}
[tool_result] 8489:    def _parse_column_def_with_exists(self):
8490-        start = self._index
8491-        self._match(TokenType.COLUMN)
8492-
8493-        exists_column = self._parse_exists(not_=True)
8494-        expression = self._parse_field_def()
8495-
8496-        if not isinstance(expression, exp.ColumnDef):
8497-            self._retreat(start)
8498-            return None
8499-
8500-        expression.set("exists", exists_column)
8501-
7033:    def _parse_field_def(self) -> exp.Expr | None:
7034- 
…[364 chars elided]…
sion: exp.AlterModifySqlSecurity) -> str:
5928-        props = self.expressions(expression, sep=" ")
5929-        return f"MODIFY {props}"
5930-
284-
285-
286:class AlterModifySqlSecurity(Expression):
287-    arg_types = {"expressions": True}
288-
289-
sqlglot/generator.py:5927:    def altermodifysqlsecurity_sql(self, expression: exp.AlterModifySqlSecurity) -> str:
sqlglot/parsers/clickhouse.py:832:            return self.expression(exp.AlterModifySqlSecurity(expressions=properties.expressions))
[assistant] I have the picture: MySQL's `MODIFY` currently falls through to `AlterColumn` (and to a `Command` for the full-definition forms). I'll add a dedicated `ModifyColumn` expression, parse it from the MySQL `MODIFY` alter parser, and reuse the existing FIRST/AFTER parsing from `ADD`.
[tool_use Bash] {"command": "sed -n 1,30p sqlglot/parsers/mysql.py | grep -n \"import\"; grep -n \"^from\\|^import\" sqlglot/parsers/mysql.py | head; grep -n \"ColumnPosition\\|AlterColumn\" sqlglot/expressions/__init__.py | head -3", "description": "Check imports in MySQL parser and expression exports"}
[tool_result] 1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, parser
6:from sqlglot.trie import new_trie
7:from sqlglot.dialects.dialect import (
14:from sqlglot.helper import seq_get
15:from sqlglot.tokens import TokenType
1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, parser
6:from sqlglot.trie import new_trie
7:from sqlglot.dialects.dialect import (
14:from sqlglot.helper import seq_get
15:from sqlglot.tokens import TokenType
[assistant] Now the edits: expression, generator, base parser helper, and the MySQL parser.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-100530-mysql-dialect-alter-table-modify/base-1/sqlglot/expressions/ddl.py", "old_string": "        \"rename_to\": False,\n    }\n\n\nclass AlterIndex(Expression):", "new_string": "        \"rename_to\": False,\n    }\n\n\nclass ModifyColumn(Expression):\n    arg_types = {\"this\": True}\n\n\nclass AlterIndex(Expression):"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-100530-mysql-dialect-alter-table-modify/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-100530-mysql-dialect-alter-table-modify/base-1/sqlglot/generator.py", "old_string": "    def altermodifysqlsecurity_sql(self, expression: exp.AlterModifySqlSecurity) -> str:\n        props = self.expressions(expression, sep=\" \")\n        return f\"MODIFY {props}\"\n", "new_string": "    def altermodifysqlsecurity_sql(self, expression: exp.AlterModifySqlSecurity) -> str:\n        props = self.expressions(expression, sep=\" \")\n        return f\"MODIFY {props}\"\n\n    def modifycolumn_sql(self, expression: exp.ModifyColumn) -> str:\n        return f\"MODIFY COLUMN {self.sql(expression, 'this')}\"\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-100530-mysql-dialect-alter-table-modify/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-100530-mysql-dialect-alter-table-modify/base-1/sqlglot/parser.py", "old_string": "        expression = self._parse_column_def_with_exists()\n        if not expression:\n            return None\n\n        # https://docs.databricks.com/delta/update-schema.html#explicitly-update-schema-to-add-columns\n 
…[541 chars elided]…
expression\n\n    # https://docs.databricks.com/delta/update-schema.html#explicitly-update-schema-to-add-columns\n    def _parse_column_position(self) -> exp.ColumnPosition | None:\n        if self._match_texts((\"FIRST\", \"AFTER\")):\n            position = self._prev.text\n            return self.expression(exp.ColumnPosition(this=self._parse_column(), position=position))\n        return None"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-100530-mysql-dialect-alter-table-modify/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-100530-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py", "old_string": "        \"MODIFY\": lambda self: self._parse_alter_table_alter(),", "new_string": "        \"MODIFY\": lambda self: self._parse_alter_table_modify(),"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-100530-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"    def _parse_\" sqlglot/parsers/mysql.py | head -3", "description": "Locate first parser method in MySQL parser"}
[tool_result] 305:    def _parse_alter_table_rename(self):
313:    def _parse_alter_drop_action(self) -> exp.Expr | None:
318:    def _parse_generated_as_identity(
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-100530-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py", "offset": 303, "limit": 16}
[tool_result] 303	    SUPPORTS_PARTITION_SELECTION = True
304	
305	    def _parse_alter_table_rename(self):
306	        if self._match_texts(("INDEX", "KEY")):
307	            old = self._parse_field(any_token=True)
308	            self._match_text_seq("TO")
309	            new = self._parse_field(any_token=True)
310	            return self.expression(exp.RenameIndex(this=old, to=new))
311	        return super()._parse_alter_table_rename()
312	
313	    def _parse_alter_drop_action(self) -> exp.Expr | None:
314	        if self._match_pair(TokenType.DROP, TokenType.PRIMARY_KEY):
315	            return self.expression(exp.DropPrimaryKey())
316	        return super()._parse_alter_drop_action()
317	
318	    def _parse_generated_as_identity(
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-100530-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py", "old_string": "        return super()._parse_alter_drop_action()\n\n    def _parse_generated_as_identity(", "new_string": "        return super()._parse_alter_drop_action()\n\n    def _parse_alter_table_modify(self) -> exp.ModifyColumn | None:\n        self._match(TokenType.COLUMN)\n        column_def = self._parse_field_def()\n        if not isinstance(column_def, exp.ColumnDef):\n            return None\n\n        column_def.set(\"position\", self._parse_column_position())\n        return self.expression(exp.ModifyColumn(this=column_def))\n\n    def _parse_generated_as_identity("}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-100530-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[assistant] Now let me check the round-trips and the existing MySQL tests.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t MODIFY COLUMN c INT NOT NULL DEFAULT 5','ALTER TABLE t MODIFY COLUMN c VARCHAR(50) NOT NULL DEFAULT \\'foo\\'','ALTER TABLE t MODIFY COLUMN c INT COMMENT \\'hi\\'','ALTER TABLE t MODIFY COLUMN c INT FIRST','ALTER TABLE t MODIFY COLUMN c INT AFTER d','ALTER TABLE t 
…[73 chars elided]…
_column LONGTEXT']:\n    e=sqlglot.parse_one(s,read='mysql'); print(type(e.args['actions'][0]).__name__ if e.args.get('actions') else 'Command', '|', e.sql('mysql'))\n\" ; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -15", "description": "Verify MODIFY round-trips and run MySQL tests"}
[tool_result] ModifyColumn | ALTER TABLE t MODIFY COLUMN c INT NOT NULL DEFAULT 5
ModifyColumn | ALTER TABLE t MODIFY COLUMN c VARCHAR(50) NOT NULL DEFAULT 'foo'
ModifyColumn | ALTER TABLE t MODIFY COLUMN c INT COMMENT 'hi'
ModifyColumn | ALTER TABLE t MODIFY COLUMN c INT FIRST
ModifyColumn | ALTER TABLE t MODIFY COLUMN c INT AFTER d
ModifyColumn | ALTER TABLE t MODIFY COLUMN c INT NOT NULL AFTER d
ModifyColumn | ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT
.............................. [ 60%]
....................                                              [100%]
50 passed, 481 subtests passed in 0.27s
[assistant] All four examples round-trip and the existing MySQL tests pass. Next I'll add regression tests next to the existing `MODIFY` identity checks, then run the full suite.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-100530-mysql-dialect-alter-table-modify/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT\")\n        self.validate_identity(\"ALTER TABLE t AUTO_INCREMENT=3000000000\")", "new_string": "        self.validat
…[265 chars elided]…
\n        self.validate_identity(\"ALTER TABLE t MODIFY COLUMN c INT COMMENT 'hi'\")\n        self.validate_identity(\"ALTER TABLE t MODIFY COLUMN c INT FIRST\")\n        self.validate_identity(\"ALTER TABLE t MODIFY COLUMN c INT AFTER d\")\n        self.validate_identity(\"ALTER TABLE t MODIFY c INT NOT NULL AFTER d\")\n        self.validate_identity(\"ALTER TABLE t AUTO_INCREMENT=3000000000\")"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-100530-mysql-dialect-alter-table-modify/base-1/tests/dialects/test_mysql.py has been updated successfully.
[assistant] The last case drops the optional `COLUMN` keyword on output, so it needs an explicit expected string.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-100530-mysql-dialect-alter-table-modify/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"ALTER TABLE t MODIFY c INT NOT NULL AFTER d\")", "new_string": "        self.validate_identity(\n            \"ALTER TABLE t MODIFY c INT NOT NULL AFTER d\",\n            \"ALTER TABLE t MODIFY COLUMN c INT NOT NULL AFTER d\",\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-100530-mysql-dialect-alter-table-modify/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; git stash list | head -0; git status --short", "description": "Run full test suite and show changed files"}
[tool_result] ................................................................................. [  7%]
............................................................................................................................................ [ 20%]
............................................................ [ 25%]
...................................... [ 29%]
.............................................................................................. [ 37%]
...............................................
…[449 chars elided]…
...... [ 79%]
............................... [ 82%]
............................................................................................................................................................................................                                           [100%]
1094 passed, 17872 subtests passed in 54.77s
head: illegal line count -- 0
 M sqlglot/expressions/ddl.py
 M sqlglot/generator.py
 M sqlglot/parser.py
 M sqlglot/parsers/mysql.py
 M tests/dialects/test_mysql.py
[assistant] Full suite passes (1094). Now the linter and formatter on the changed files.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin; ($P/ruff --version && $P/ruff check sqlglot/expressions/ddl.py sqlglot/generator.py sqlglot/parser.py sqlglot/parsers/mysql.py tests/dialects/test_mysql.py && $P/ruff format --check sqlglot tests/dialects/test_mysql.py) 2>&1 | tail -12", "description": "Run ruff lint and format check"}
[tool_result] ruff 0.15.6
All checks passed!
175 files already formatted
[assistant] MySQL `ALTER TABLE ... MODIFY [COLUMN] col_name column_definition [FIRST | AFTER col]` now parses into its own `ModifyColumn` expression and round-trips. All four examples from your request come back unchanged. The full suite passes (1094 tests) and ruff is clean. I left the changes uncommitted.

What changed:

- **`sqlglot/expressions/ddl.py`**: new `ModifyColumn` expression, with `this` holding a `ColumnDef`.
- **`sqlglot/parsers/mysql.py`**: `MODIFY` now routes to a new `_parse_alter_table_modify`, which reads an optional `COLUMN`, a full column definition, and an optional position. Before,
…[309 chars elided]…
_parse_column_position`, so `ADD` and `MODIFY` share it.
- **`sqlglot/generator.py`**: `modifycolumn_sql` emits `MODIFY COLUMN <column def>`. The base generator is used because the expression is only produced by the MySQL parser and MySQL-derived dialects inherit it.
- **`tests/dialects/test_mysql.py`**: added round-trip cases for the four forms, plus `MODIFY c INT NOT NULL AFTER d`, which normalizes to `MODIFY COLUMN c ...`.

The existing `ALTER COLUMN ... SET DATA TYPE` → `MODIFY COLUMN` mapping is unchanged, and its test still passes. Snowflake and ClickHouse `MODIFY` handling is untouched.
