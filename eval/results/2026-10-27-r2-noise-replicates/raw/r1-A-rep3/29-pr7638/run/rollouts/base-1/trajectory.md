# trajectory base-1

final message:
MySQL `ALTER TABLE ... CHANGE [COLUMN] old new definition [FIRST | AFTER col]` now parses and round-trips. The full suite passes (1106 tests), and ruff check and format are clean. I haven't committed.

The change reuses the existing `MODIFY COLUMN` path:

- **`sqlglot/expressions/ddl.py`**: `ModifyColumn` gets an optional `old_column` arg. Without it the node is still `MODIFY`, so existing behaviour is unchanged.
- **`sqlglot/parsers/mysql.py`**: `CHANGE` is registered in `ALTER_PARSERS`. The new `_parse_alter_table_change` reads the optional `COLUMN` keyword, the old name, and the new name, then parses the column definition with the same helper `MODIFY` uses. So `FIRST`/`AFTER` and constraints come along.
- **`sqlglot/generator.py`**: `modifycolumn_sql` emits `CHANGE COLUMN old <def>` when `old_column` is set, and `MODIFY COLUMN <def>` otherwise.
- **`tests/dialects/test_mysql.py`**: identity tests for `CHANGE COLUMN` with constraints, `FIRST`, and `AFTER`, plus `CHANGE a b INT NOT NULL` normalising to `CHANGE COLUMN a b INT NOT NULL`.

Choices to check:
- The output always includes `COLUMN` (`CHANGE COLUMN`), matching how `MODIFY` always emits `MODIFY COLUMN`.
- For non-MySQL targets, the unsupported-feature warning still says "MODIFY COLUMN", since the warning text is shared. For example, transpiling `CHANGE` to Postgres warns about MODIFY. Say if you want a separate message for the rename case.

## events
[tool_use Bash] {"command": "grep -rn -i \"modify\" sqlglot/dialects/mysql.py sqlglot/parser.py sqlglot/generator.py sqlglot/dialects/dialect.py | head -50; grep -rn -i \"MODIFY\" tests/dialects/test_mysql.py | head -20", "description": "Find MODIFY COLUMN handling in MySQL code"}
[tool_result] sqlglot/generator.py:470:    # Whether ALTER TABLE ... MODIFY COLUMN column-redefinition syntax is supported
sqlglot/generator.py:471:    SUPPORTS_MODIFY_COLUMN = False
sqlglot/generator.py:4009:    def modifycolumn_sql(self, expression: exp.ModifyColumn) -> str:
sqlglot/generator.py:4010:        if not self.SUPPORTS_MODIFY_COLUMN:
sqlglot/generator.py:4011:            self.unsupported("MODIFY COLUMN is not supported in this dialect")
sqlglot/generator.py:4012:        return f"MODIFY COLUMN {sel
…[1017 chars elided]…
ts/dialects/test_mysql.py:47:        self.validate_identity("ALTER TABLE t MODIFY COLUMN c INT AFTER d")
tests/dialects/test_mysql.py:48:        self.validate_identity("ALTER TABLE t MODIFY COLUMN c INT NOT NULL AFTER d")
tests/dialects/test_mysql.py:50:            "ALTER TABLE t MODIFY c INT NOT NULL",
tests/dialects/test_mysql.py:51:            "ALTER TABLE t MODIFY COLUMN c INT NOT NULL",
tests/dialects/test_mysql.py:179:            "ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT",
[tool_use Bash] {"command": "grep -rn \"ModifyColumn\\|ModifyColumn\\|RenameColumn\\|ColumnDef\\b\" sqlglot/parser.py sqlglot/dialects/mysql.py sqlglot/expressions.py sqlglot/generator.py | head -40; grep -n \"class ModifyColumn\" -A 8 sqlglot/expressions.py; grep -n \"class RenameColumn\" -A 6 sqlglot/expressions.py; grep -n \"MODIFY\" sqlglot/parser.py sqlglot/dialects/mysql.py sqlglot/tokens.py", "description": "Locate ModifyColumn and related parser code"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:1153:    def columndef_sql(self, expression: exp.ColumnDef, sep: str = " ") -> str:
sqlglot/generator.py:3666:    def jsoncolumndef_sql(self, expression: exp.JSONColumnDef) -> str:
sqlglot/generator.py:3698:    def openjsoncolumndef_sql(self, expression: exp.OpenJSONColumnDef) -> str:
sqlglot/generator.py:4009:    def modifycolumn_sql(self, expression: exp.ModifyColumn) -> str:
sqlglot/generator.py:4045:    de
…[1189 chars elided]…
72:    def _parse_add_column(self) -> exp.ColumnDef | None:
sqlglot/parser.py:8602:            if isinstance(column_def, exp.ColumnDef):
sqlglot/parser.py:8699:    def _parse_alter_table_rename(self) -> exp.AlterRename | exp.RenameColumn | None:
sqlglot/parser.py:8711:            return self.expression(exp.RenameColumn(this=old_column, to=new_column, exists=exists))
ugrep: warning: sqlglot/expressions.py: No such file or directory
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "sed -n 4000,4070p sqlglot/generator.py; sed -n 8540,8720p sqlglot/parser.py; grep -rn \"class ModifyColumn\" -A 8 sqlglot/expressions/ ; grep -rn \"ModifyColumn\\|ALTER_TABLE_INCLUDE\\|SUPPORTS_MODIFY_COLUMN\\|_parse_alter_table_alter\\|_parse_alter_table_rename\" sqlglot/ | grep -v \"\\.pyc\"", "description": "Read ALTER TABLE parsing and generation code"}
[tool_result]         if not drop and not allow_null:
            self.unsupported("Unsupported ALTER COLUMN syntax")

        if allow_null is not None:
            keyword = "DROP" if drop else "SET"
            return f"ALTER COLUMN {this} {keyword} NOT NULL"

        return f"ALTER COLUMN {this} DROP DEFAULT"

    def modifycolumn_sql(self, expression: exp.ModifyColumn) -> str:
        if not self.SUPPORTS_MODIFY_COLUMN:
            self.unsupported("MODIFY COLUMN is not supported in this dialect")
      
…[11622 chars elided]…
parse_alter_table_rename()
sqlglot/parsers/mysql.py:329:        return self.expression(exp.ModifyColumn(this=column_def))
sqlglot/parsers/mysql.py:551:    def _parse_alter_table_alter_index(self) -> exp.AlterIndex:
sqlglot/expressions/ddl.py:248:class ModifyColumn(Expression):
sqlglot/generators/tsql.py:130:    ALTER_TABLE_INCLUDE_COLUMN_KEYWORD = False
sqlglot/generators/oracle.py:33:    ALTER_TABLE_INCLUDE_COLUMN_KEYWORD = False
sqlglot/generators/mysql.py:114:    SUPPORTS_MODIFY_COLUMN = True
[tool_use Bash] {"command": "sed -n 250,340p sqlglot/parsers/mysql.py; grep -n \"ALTER_PARSERS\" -A 12 sqlglot/parsers/mysql.py | head -30", "description": "Read MySQL parser ALTER handling"}
[tool_result]         "INVISIBLE": lambda self: self.expression(exp.InvisibleColumnConstraint()),
    }

    ALTER_PARSERS = {
        **parser.Parser.ALTER_PARSERS,
        "MODIFY": lambda self: self._parse_alter_table_modify(),
        "AUTO_INCREMENT": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),
    }

    ALTER_ALTER_PARSERS = {
        **parser.Parser.ALTER_ALTER_PARSERS,
        "INDEX": lambda self: self._parse_alter_table_alter_index(),
    }

    SCHEMA_UNNAMED_CONSTRAIN
…[2438 chars elided]…
 lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),
257-    }
258-
259:    ALTER_ALTER_PARSERS = {
260:        **parser.Parser.ALTER_ALTER_PARSERS,
261-        "INDEX": lambda self: self._parse_alter_table_alter_index(),
262-    }
263-
264-    SCHEMA_UNNAMED_CONSTRAINTS = {
265-        *parser.Parser.SCHEMA_UNNAMED_CONSTRAINTS,
266-        "FULLTEXT",
267-        "INDEX",
268-        "KEY",
269-        "SPATIAL",
270-    }
271-
272-    PROFILE_TYPES: parser.OPTIONS_TYPE = {
[tool_use Bash] {"command": "sed -n 240,252p sqlglot/expressions/ddl.py; grep -n \"ALTER_PARSERS = \" -A 14 sqlglot/parser.py | head -24; grep -n \"def _parse_alter(\" -A 40 sqlglot/parser.py | head -60; sed -n 36,56p tests/dialects/test_mysql.py", "description": "Inspect ModifyColumn, ALTER dispatch, and MySQL tests"}
[tool_result]         "drop": False,
        "comment": False,
        "allow_null": False,
        "visible": False,
        "rename_to": False,
    }


class ModifyColumn(Expression):
    pass


class AlterIndex(Expression):
8764:    def _parse_alter(self) -> exp.Alter | exp.Command:
8765-        start = self._prev
8766-
8767-        iceberg = self._match_text_seq("ICEBERG")
8768-
8769-        alter_token = self._match_set(self.ALTERABLES) and self._prev
8770-        if not alter_token:
8771-            ret
…[2504 chars elided]…
        self.validate_identity("ALTER TABLE t MODIFY COLUMN c INT NOT NULL AFTER d")
        self.validate_identity(
            "ALTER TABLE t MODIFY c INT NOT NULL",
            "ALTER TABLE t MODIFY COLUMN c INT NOT NULL",
        )
        self.validate_identity("ALTER TABLE t AUTO_INCREMENT=3000000000")
        self.validate_identity("ALTER VIEW v AS SELECT a, b, c, d FROM foo")
        self.validate_identity("ALTER VIEW v AS SELECT * FROM foo WHERE c > 100")
        self.validate_identity(
[assistant] The MySQL parser already handles `MODIFY` through `ModifyColumn(this=ColumnDef)`. I'll add an optional `old_column` arg for `CHANGE` and reuse the same redefinition path.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-124344-mysql-dialect-support-change-col/base-1/sqlglot/expressions/ddl.py", "old_string": "class ModifyColumn(Expression):\n    pass", "new_string": "class ModifyColumn(Expression):\n    arg_types = {\"this\": True, \"old_column\": False}"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-124344-mysql-dialect-support-change-col/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-124344-mysql-dialect-support-change-col/base-1/sqlglot/parsers/mysql.py", "old_string": "        \"MODIFY\": lambda self: self._parse_alter_table_modify(),\n        \"AUTO_INCREMENT\"", "new_string": "        \"MODIFY\": lambda self: self._parse_alter_table_modify(),\n        \"CHANGE\": lambda self: self._parse_alter_table_change(),\n        \"AUTO_INCREMENT\""}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-124344-mysql-dialect-support-change-col/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-124344-mysql-dialect-support-change-col/base-1/sqlglot/parsers/mysql.py", "old_string": "        return self.expression(exp.ModifyColumn(this=column_def))\n\n", "new_string": "        return self.expression(exp.ModifyColumn(this=column_def))\n\n    def _parse_alter_table_change(self) -> exp.Expr | No
…[72 chars elided]…
_parse_field(any_token=True)\n        new_column = self._parse_field(any_token=True)\n        if old_column is None or new_column is None:\n            return None\n\n        column_def = self._parse_column_def(new_column)\n        if not isinstance(column_def, exp.ColumnDef):\n            return None\n\n        return self.expression(exp.ModifyColumn(this=column_def, old_column=old_column))\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-124344-mysql-dialect-support-change-col/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-124344-mysql-dialect-support-change-col/base-1/sqlglot/generator.py", "old_string": "        return f\"MODIFY COLUMN {self.sql(expression, 'this')}\"", "new_string": "        old_column = self.sql(expression, \"old_column\")\n        if old_column:\n            return f\"CHANGE COLUMN {old_column} {self.sql(expression, 'this')}\"\n        return f\"MODIFY COLUMN {self.sql(expression, 'this')}\""}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-124344-mysql-dialect-support-change-col/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-124344-mysql-dialect-support-change-col/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"ALTER TABLE t AUTO_INCREMENT=3000000000\")", "new_string": "        self.validate_identity(\"ALTER TABLE t CHANGE COLUMN a b INT\")\n        self.validate_identity(\"ALTER TAB
…[97 chars elided]…
CHANGE COLUMN a b INT FIRST\")\n        self.validate_identity(\"ALTER TABLE t CHANGE COLUMN a b INT AFTER d\")\n        self.validate_all(\n            \"ALTER TABLE t CHANGE a b INT NOT NULL\",\n            write={\n                \"mysql\": \"ALTER TABLE t CHANGE COLUMN a b INT NOT NULL\",\n            },\n        )\n        self.validate_identity(\"ALTER TABLE t AUTO_INCREMENT=3000000000\")"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-124344-mysql-dialect-support-change-col/base-1/tests/dialects/test_mysql.py has been updated successfully.
[assistant] The `validate_all` call I wrote is clumsier than the existing `MODIFY` pattern, so I'll switch it to the `validate_identity(src, expected)` form used there, then run the tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-124344-mysql-dialect-support-change-col/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_all(\n            \"ALTER TABLE t CHANGE a b INT NOT NULL\",\n            write={\n                \"mysql\": \"ALTER TABLE t CHANGE COLUMN a b INT NOT NULL\",\n            },\n        )", "new_string": "        self.validate_identity(\n            \"ALTER TABLE t CHANGE a b INT NOT NULL\",\n            \"ALTER TABLE t CHANGE COLUMN a b INT NOT NULL\",\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-124344-mysql-dialect-support-change-col/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -15; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t CHANGE COLUMN a b INT', 'ALTER TABLE t CHANGE a b VARCHAR(10) NOT NULL DEFAULT \\'x\\' AFTER c']:\n    e = sqlglot.parse_one(s, read='mysql'); print(type(e.args['actions'][0]).__name__, repr(e.args['actions'][0].args.get('old_column')) [:60]); print(e.sql('mysql'))\nprint(sqlglot.transpile('ALTER TABLE t CHANGE a b INT', read='mysql', write='postgres'))\n\"", "description": "Run MySQL tests and spot-check CHANGE parsing"}
[tool_result] .............................. [ 60%]
....................                                              [100%]
50 passed, 481 subtests passed in 0.38s
MODIFY COLUMN is not supported in this dialect
ModifyColumn Identifier(this=a, quoted=False)
ALTER TABLE t CHANGE COLUMN a b INT
ModifyColumn Identifier(this=a, quoted=False)
ALTER TABLE t CHANGE COLUMN a b VARCHAR(10) NOT NULL DEFAULT 'x' AFTER c
['ALTER TABLE t CHANGE COLUMN a b INT']
[assistant] MySQL tests pass. Now the full suite and lint.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; (<work>/env-sqlglot/bin/ruff check sqlglot/parsers/mysql.py sqlglot/generator.py sqlglot/expressions/ddl.py tests/dialects/test_mysql.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/parsers/mysql.py sqlglot/generator.py sqlglot/expressions/ddl.py tests/dialects/test_mysql.py) 2>&1 | tail -5", "description": "Run full test suite and ruff checks"}
[tool_result] ................................................................................................................................... [ 85%]
............................. [ 87%]
.............................................................................. [ 94%]
........................................................                                                [100%]
1106 passed, 17999 subtests passed in 57.21s
All checks passed!
4 files already formatted
[assistant] MySQL `ALTER TABLE ... CHANGE [COLUMN] old new definition [FIRST | AFTER col]` now parses and round-trips. The full suite passes (1106 tests), and ruff check and format are clean. I haven't committed.

The change reuses the existing `MODIFY COLUMN` path:

- **`sqlglot/expressions/ddl.py`**: `ModifyColumn` gets an optional `old_column` arg. Without it the node is still `MODIFY`, so existing behaviour is unchanged.
- **`sqlglot/parsers/mysql.py`**: `CHANGE` is registered in `ALTER_PARSERS`. The new `_parse_alter_table_change` reads the optional `COLUMN` keyword, the old name, and the new name, t
…[221 chars elided]…
, and `MODIFY COLUMN <def>` otherwise.
- **`tests/dialects/test_mysql.py`**: identity tests for `CHANGE COLUMN` with constraints, `FIRST`, and `AFTER`, plus `CHANGE a b INT NOT NULL` normalising to `CHANGE COLUMN a b INT NOT NULL`.

Choices to check:
- The output always includes `COLUMN` (`CHANGE COLUMN`), matching how `MODIFY` always emits `MODIFY COLUMN`.
- For non-MySQL targets, the unsupported-feature warning still says "MODIFY COLUMN", since the warning text is shared. For example, transpiling `CHANGE` to Postgres warns about MODIFY. Say if you want a separate message for the rename case.
