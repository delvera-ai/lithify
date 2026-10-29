# trajectory base-1

final message:
MySQL `ALTER TABLE ... CHANGE [COLUMN] old new definition [FIRST | AFTER col]` now parses and round-trips. The full suite passes (1106 tests), and ruff lint and format checks are clean.

- **Parser** (`sqlglot/parsers/mysql.py`): `CHANGE` is registered in `ALTER_PARSERS`. The new `_parse_alter_table_change` reads the optional `COLUMN` keyword, the old name, then the new column definition via `_parse_column_def`, which already handles `FIRST`/`AFTER`.
- **Expression** (`sqlglot/expressions/ddl.py`): `ModifyColumn` gains an optional `old_name` arg. `CHANGE` produces the same `ModifyColumn` node as `MODIFY COLUMN`, plus `old_name`.
- **Generator** (`sqlglot/generator.py`): when `old_name` is set, output is `CHANGE COLUMN old new definition`. Without it, output is unchanged `MODIFY COLUMN`.
- **Tests** (`tests/dialects/test_mysql.py`): identity cases with `COLUMN`, `FIRST`, `AFTER`, and constraints, plus `CHANGE a b ...` normalizing to `CHANGE COLUMN a b ...`, mirroring the existing `MODIFY` tests.

Choices to review:
- Output always includes `COLUMN` (`CHANGE a b` becomes `CHANGE COLUMN a b`), matching how `MODIFY c` already becomes `MODIFY COLUMN c`.
- SingleStore has its own `CHANGE` override (a rename-only form). It still takes precedence there, so its behavior is unchanged.
- Known wart: the non-MySQL unsupported-dialect warning still says "MODIFY COLUMN is not supported", even when the statement is a `CHANGE`. I left the existing message text alone; say if you want it made generic.

I haven't committed anything.

## events
[tool_use Bash] {"command": "rtk grep -n \"MODIFY\\|CHANGE\\|ModifyColumn\\|_parse_alter_table_alter\\|ALTER_PARSERS\" sqlglot/dialects/mysql.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -80", "description": "Find MODIFY/CHANGE handling across sqlglot sources"}
[tool_result] (eval):1: command not found: rtk
[tool_use Bash] {"command": "grep -n \"MODIFY\\|CHANGE\\|ModifyColumn\\|ALTER_PARSERS\" sqlglot/dialects/mysql.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -80", "description": "Find MODIFY/CHANGE handling across sqlglot sources"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:470:    # Whether ALTER TABLE ... MODIFY COLUMN column-redefinition syntax is supported
sqlglot/generator.py:471:    SUPPORTS_MODIFY_COLUMN = False
sqlglot/generator.py:4009:    def modifycolumn_sql(self, expression: exp.ModifyColumn) -> str:
sqlglot/generator.py:4010:        if not self.SUPPORTS_MODIFY_COLUMN:
sqlglot/generator.py:4011:            self.unsupported("MODIFY COLUMN is not supported in this diale
…[242 chars elided]…
ot/parser.py:1435:    ALTER_PARSERS: t.ClassVar = {
sqlglot/parser.py:1449:    ALTER_ALTER_PARSERS: t.ClassVar = {
sqlglot/parser.py:4916:        if not self._match_text_seq("CHANGES", "(", "INFORMATION", "=>"):
sqlglot/parser.py:8633:        if self._match_texts(self.ALTER_ALTER_PARSERS):
sqlglot/parser.py:8634:            return self.ALTER_ALTER_PARSERS[self._prev.text.upper()](self)
sqlglot/parser.py:8790:        parser = self.ALTER_PARSERS.get(self._prev.text.upper()) if self._prev else None
[tool_use Bash] {"command": "grep -rn \"ModifyColumn\\|MODIFY_COLUMN\\|\\\"MODIFY\\\"\\|\\\"CHANGE\\\"\" sqlglot/ | head -40; echo ---; sed -n 1425,1460p sqlglot/parser.py; echo ---; sed -n 8780,8830p sqlglot/parser.py", "description": "Locate ModifyColumn usage and ALTER parsing code"}
[tool_result] sqlglot/generator.py:471:    SUPPORTS_MODIFY_COLUMN = False
sqlglot/generator.py:4009:    def modifycolumn_sql(self, expression: exp.ModifyColumn) -> str:
sqlglot/generator.py:4010:        if not self.SUPPORTS_MODIFY_COLUMN:
sqlglot/parsers/singlestore.py:238:        "CHANGE": lambda self: self.expression(
sqlglot/parsers/clickhouse.py:445:        "MODIFY": lambda self: self._parse_alter_table_modify(),
sqlglot/parsers/hive.py:139:        "CHANGE": lambda self: self._parse_alter_table_change(),

…[3768 chars elided]…
ttps://duckdb.org/docs/sql/statements/analyze
        if not self._curr:
            return self.expression(exp.Analyze())

        options = []
        while self._match_texts(self.ANALYZE_STYLES):
            if self._prev.text.upper() == "BUFFER_USAGE_LIMIT":
                options.append(f"BUFFER_USAGE_LIMIT {self._parse_number()}")
            else:
                options.append(self._prev.text.upper())

        this: exp.Expr | None = None
        inner_expression: exp.Expr | None = None
[tool_use Bash] {"command": "sed -n 240,340p sqlglot/parsers/mysql.py; echo ---; sed -n 235,262p sqlglot/expressions/ddl.py; echo ---; sed -n 105,125p sqlglot/generators/mysql.py; echo ---; grep -n \"_parse_alter_table_change\" -A30 sqlglot/parsers/hive.py | head -60; echo ---; grep -n \"def _parse_alter_table_add\\|def _parse_alter_table_modify\\|def _parse_column_def\\|def _parse_add_column\\|def _parse_alter_table_alter\" -A3 sqlglot/parser.py sqlglot/parsers/*.py", "description": "Read MySQL MODIFY parser, ModifyColumn expr, and Hive CHANGE"}
[tool_result]     SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
    SET_TRIE = new_trie(key.split(" ") for key in SET_PARSERS)

    CONSTRAINT_PARSERS = {
        **parser.Parser.CONSTRAINT_PARSERS,
        "FULLTEXT": lambda self: self._parse_index_constraint(kind="FULLTEXT"),
        "INDEX": lambda self: self._parse_index_constraint(),
        "KEY": lambda self: self._parse_index_constraint(),
        "SPATIAL": lambda self: self._parse_index_constraint(kind="SPATIAL"),
        "ZEROFILL": 
…[8988 chars elided]…
1-        self, this: exp.Expr | None, computed_column: bool = True
sqlglot/parsers/tsql.py-602-    ) -> exp.Expr | None:
sqlglot/parsers/tsql.py-603-        this = super()._parse_column_def(this=this, computed_column=computed_column)
--
sqlglot/parsers/tsql.py:714:    def _parse_alter_table_alter(self) -> exp.Expr | None:
sqlglot/parsers/tsql.py-715-        expression = super()._parse_alter_table_alter()
sqlglot/parsers/tsql.py-716-
sqlglot/parsers/tsql.py-717-        if expression is not None:
[tool_use Bash] {"command": "grep -rn \"MODIFY\\|CHANGE COLUMN\\|ModifyColumn\\|FIRST\\b\\|AFTER\" tests/dialects/test_mysql.py | head -30; echo ---; grep -rn \"\\\"FIRST\\\"\\|\\\"AFTER\\\"\\|ColumnPosition\\|first_position\\|position\" sqlglot/parser.py sqlglot/parsers/mysql.py sqlglot/generators/mysql.py sqlglot/generator.py sqlglot/expressions/ddl.py | head -30; echo ---; git log --oneline -3 -- sqlglot/parsers/mysql.py; git status --short", "description": "Check existing MySQL MODIFY tests and FIRST/AFTER handling"}
[tool_result] tests/dialects/test_mysql.py:40:        self.validate_identity("ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT")
tests/dialects/test_mysql.py:41:        self.validate_identity("ALTER TABLE t MODIFY COLUMN c INT NOT NULL")
tests/dialects/test_mysql.py:42:        self.validate_identity("ALTER TABLE t MODIFY COLUMN c INT DEFAULT 5")
tests/dialects/test_mysql.py:43:        self.validate_identity("ALTER TABLE t MODIFY COLUMN c INT NOT NULL DEFAULT 5")
tests/dialects/test_mysql.py:44:      
…[5209 chars elided]…
position = self.expression(exp.ColumnPosition(this=self._parse_column(), position=pos))
sqlglot/parser.py:7165:            exp.ColumnDef(this=this, kind=kind, constraints=constraints, position=position)
sqlglot/parser.py:8079:    def _parse_position(self, haystack_first: bool = False) -> exp.StrPosition:
---
206e2f892 fix(mysql)!: full `MODIFY COLUMN` support. (#7562)
a88dfce09 fix(mysql): support SHOW TABLES IN <schema> parsing (#7537)
68861d9f3 feat(mysql)!: support `DROP PRIMARY KEY`. (#7530)
[tool_use Bash] {"command": "sed -n 36,56p tests/dialects/test_mysql.py; echo ---; sed -n 4005,4014p sqlglot/generator.py; echo ---; sed -n 230,245p sqlglot/parsers/singlestore.py", "description": "Read MySQL MODIFY tests and generator/parser references"}
[tool_result]         self.validate_identity("ALTER TABLE t ADD INDEX `i` (`c`)")
        self.validate_identity("ALTER TABLE t ADD UNIQUE `i` (`c`)")
        self.validate_identity("ALTER TABLE t DROP PRIMARY KEY")
        self.validate_identity("ALTER TABLE t DROP COLUMN c, DROP PRIMARY KEY, DROP INDEX `i`")
        self.validate_identity("ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT")
        self.validate_identity("ALTER TABLE t MODIFY COLUMN c INT NOT NULL")
        self.validate_identity("A
…[1522 chars elided]…
S FOR GROUP", target=True),
    }

    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)

    ALTER_PARSERS = {
        **MySQLParser.ALTER_PARSERS,
        "CHANGE": lambda self: self.expression(
            exp.RenameColumn(this=self._parse_column(), to=self._parse_column())
        ),
    }

    def _parse_vector_expressions(self, expressions: list[exp.Expr]) -> list[exp.Expr]:
        type_name = expressions[1].name.upper()
        if type_name in self.dialect.VECTOR_TYPE_ALIASES:
[assistant] Existing `MODIFY COLUMN` handling already covers the column definition and `FIRST`/`AFTER`, so I'll reuse `ModifyColumn` and add an optional original-name arg. Making the edits now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-104758-mysql-dialect-support-change-col/base-1/sqlglot/expressions/ddl.py", "old_string": "class ModifyColumn(Expression):\n    pass", "new_string": "class ModifyColumn(Expression):\n    arg_types = {\"this\": True, \"old_name\": False}"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-104758-mysql-dialect-support-change-col/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-104758-mysql-dialect-support-change-col/base-1/sqlglot/generator.py", "old_string": "        return f\"MODIFY COLUMN {self.sql(expression, 'this')}\"", "new_string": "        old_name = self.sql(expression, \"old_name\")\n        if old_name:\n            return f\"CHANGE COLUMN {old_name} {self.sql(expression, 'this')}\"\n        return f\"MODIFY COLUMN {self.sql(expression, 'this')}\""}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-104758-mysql-dialect-support-change-col/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-104758-mysql-dialect-support-change-col/base-1/sqlglot/parsers/mysql.py", "old_string": "        \"MODIFY\": lambda self: self._parse_alter_table_modify(),\n        \"AUTO_INCREMENT\"", "new_string": "        \"MODIFY\": lambda self: self._parse_alter_table_modify(),\n        \"CHANGE\": lambda self: self._parse_alter_table_change(),\n        \"AUTO_INCREMENT\""}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-104758-mysql-dialect-support-change-col/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-104758-mysql-dialect-support-change-col/base-1/sqlglot/parsers/mysql.py", "old_string": "        return self.expression(exp.ModifyColumn(this=column_def))\n\n", "new_string": "        return self.expression(exp.ModifyColumn(this=column_def))\n\n    def _parse_alter_table_change(self) -> exp.Expr | No
…[52 chars elided]…
  old_name = self._parse_field(any_token=True)\n        column = self._parse_field(any_token=True)\n        if old_name is None or column is None:\n            return None\n\n        column_def = self._parse_column_def(column)\n        if not isinstance(column_def, exp.ColumnDef):\n            return None\n\n        return self.expression(exp.ModifyColumn(this=column_def, old_name=old_name))\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-104758-mysql-dialect-support-change-col/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-104758-mysql-dialect-support-change-col/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"ALTER TABLE t AUTO_INCREMENT=3000000000\")", "new_string": "        self.validate_identity(\"ALTER TABLE t CHANGE COLUMN a b INT NOT NULL\")\n        self.validate_identity(\"
…[63 chars elided]…
        self.validate_identity(\"ALTER TABLE t CHANGE COLUMN a b INT FIRST\")\n        self.validate_identity(\"ALTER TABLE t CHANGE COLUMN a b INT AFTER d\")\n        self.validate_identity(\n            \"ALTER TABLE t CHANGE a b INT NOT NULL\",\n            \"ALTER TABLE t CHANGE COLUMN a b INT NOT NULL\",\n        )\n        self.validate_identity(\"ALTER TABLE t AUTO_INCREMENT=3000000000\")"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-104758-mysql-dialect-support-change-col/base-1/tests/dialects/test_mysql.py has been updated successfully.
[assistant] Now running the project's test command, which covers the whole suite.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run full project test suite", "timeout": 600000}
[tool_result] ................................................................ [  5%]
........................... [  8%]
............. [  9%]
........................................................................................................................................ [ 21%]
............................................................................................ [ 30%]
.......................... [ 32%]
.......................................... [ 36%]
............................................
…[317 chars elided]…
........................................................................... [ 73%]
................................................................................................................................... [ 85%]
............................. [ 87%]
.............................................................................. [ 94%]
........................................................                                                [100%]
1106 passed, 17999 subtests passed in 59.52s
[assistant] All 1106 tests pass. Next I'll check the AST shape and run the linter on the changed files.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ne = sqlglot.parse_one('ALTER TABLE t CHANGE a b INT AFTER d', read='mysql')\nprint(repr(e.args['actions'][0].args.get('old_name')))\nprint(e.sql('mysql'))\nprint(e.sql('postgres'))\n\"; <work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/mysql.py sqlglot/generator.py sqlglot/expressions/ddl.py tests/dialects/test_mysql.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot tests/dialects/test_mysql.py 2>&1 | tail -3", "description": "Check AST shape, cross-dialect output, and lint"}
[tool_result] MODIFY COLUMN is not supported in this dialect
Identifier(this=a, quoted=False)
ALTER TABLE t CHANGE COLUMN a b INT AFTER d
ALTER TABLE t CHANGE COLUMN a b INT AFTER d
All checks passed!
176 files already formatted
[assistant] MySQL `ALTER TABLE ... CHANGE [COLUMN] old new definition [FIRST | AFTER col]` now parses and round-trips. The full suite passes (1106 tests), and ruff lint and format checks are clean.

- **Parser** (`sqlglot/parsers/mysql.py`): `CHANGE` is registered in `ALTER_PARSERS`. The new `_parse_alter_table_change` reads the optional `COLUMN` keyword, the old name, then the new column definition via `_parse_column_def`, which already handles `FIRST`/`AFTER`.
- **Expression** (`sqlglot/expressions/ddl.py`): `ModifyColumn` gains an optional `old_name` arg. `CHANGE` produces the same `ModifyColumn` node 
…[339 chars elided]…
ing to `CHANGE COLUMN a b ...`, mirroring the existing `MODIFY` tests.

Choices to review:
- Output always includes `COLUMN` (`CHANGE a b` becomes `CHANGE COLUMN a b`), matching how `MODIFY c` already becomes `MODIFY COLUMN c`.
- SingleStore has its own `CHANGE` override (a rename-only form). It still takes precedence there, so its behavior is unchanged.
- Known wart: the non-MySQL unsupported-dialect warning still says "MODIFY COLUMN is not supported", even when the statement is a `CHANGE`. I left the existing message text alone; say if you want it made generic.

I haven't committed anything.
