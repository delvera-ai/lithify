# trajectory base-1

final message:
MySQL `ALTER TABLE ... CHANGE [COLUMN] old new definition [FIRST | AFTER col]` now parses and round-trips. The full suite passes (1106 tests), and ruff lint and format are clean.

Changes:

- **`sqlglot/expressions/ddl.py`**: new `ChangeColumn` expression, which mirrors `ModifyColumn` and adds an `old_name` argument. `this` is the new column definition.
- **`sqlglot/parsers/mysql.py`**: `CHANGE` is registered in `ALTER_PARSERS`, and `_parse_alter_table_change` parses the optional `COLUMN` keyword, the old name, then the column definition (which handles `FIRST`/`AFTER` the same way `MODIFY` does).
- **`sqlglot/generator.py`**: `changecolumn_sql` plus a `SUPPORTS_CHANGE_COLUMN` flag, defaulting to `False`. Other dialects emit an "unsupported" warning, the same as `MODIFY COLUMN` does.
- **`sqlglot/generators/mysql.py`**: sets `SUPPORTS_CHANGE_COLUMN = True`.
- **`tests/dialects/test_mysql.py`**: round-trip cases for `CHANGE COLUMN` with defaults, comments, `FIRST`, and `AFTER`, plus a case showing the `COLUMN` keyword is normalized in when omitted.

Two choices you may want to revisit:

- I added a separate `ChangeColumn` class rather than an optional `old_name` on `ModifyColumn`, so `MODIFY` output is unchanged. The generator's unsupported-dialect handling follows the `MODIFY` pattern.
- Transpiling `CHANGE COLUMN` to a non-MySQL dialect keeps the MySQL syntax and warns, rather than rewriting it to a standard form. Other dialects have no column-redefinition equivalent for this, so I didn't invent one.

I didn't commit anything.

## events
[tool_use Bash] {"command": "grep -rn \"MODIFY\" sqlglot/dialects/mysql.py sqlglot/parser.py sqlglot/generator.py sqlglot/dialects/dialect.py | head -40; grep -rn \"CHANGE\" sqlglot/dialects/mysql.py | head", "description": "Find MODIFY and CHANGE handling in parser/generator"}
[tool_result] sqlglot/generator.py:470:    # Whether ALTER TABLE ... MODIFY COLUMN column-redefinition syntax is supported
sqlglot/generator.py:471:    SUPPORTS_MODIFY_COLUMN = False
sqlglot/generator.py:4010:        if not self.SUPPORTS_MODIFY_COLUMN:
sqlglot/generator.py:4011:            self.unsupported("MODIFY COLUMN is not supported in this dialect")
sqlglot/generator.py:4012:        return f"MODIFY COLUMN {self.sql(expression, 'this')}"
sqlglot/generator.py:6009:        return f"MODIFY {props}"
[tool_use Bash] {"command": "sed -n 4000,4020p sqlglot/generator.py; grep -rn \"SUPPORTS_MODIFY_COLUMN\\|ModifyColumn\\|AlterColumn\\|RenameColumn\" sqlglot/ | head -30; grep -rn \"MODIFY\" sqlglot/parser.py sqlglot/dialects/*.py | head; grep -rn \"MODIFY COLUMN\\|CHANGE COLUMN\\|CHANGE \" tests/dialects/test_mysql.py | head", "description": "Inspect modify-column generator and existing tests"}
[tool_result]         if not drop and not allow_null:
            self.unsupported("Unsupported ALTER COLUMN syntax")

        if allow_null is not None:
            keyword = "DROP" if drop else "SET"
            return f"ALTER COLUMN {this} {keyword} NOT NULL"

        return f"ALTER COLUMN {this} DROP DEFAULT"

    def modifycolumn_sql(self, expression: exp.ModifyColumn) -> str:
        if not self.SUPPORTS_MODIFY_COLUMN:
            self.unsupported("MODIFY COLUMN is not supported in this dialect")
      
…[3904 chars elided]…
       self.validate_identity("ALTER TABLE t MODIFY COLUMN c INT COMMENT 'hi'")
tests/dialects/test_mysql.py:46:        self.validate_identity("ALTER TABLE t MODIFY COLUMN c INT FIRST")
tests/dialects/test_mysql.py:47:        self.validate_identity("ALTER TABLE t MODIFY COLUMN c INT AFTER d")
tests/dialects/test_mysql.py:48:        self.validate_identity("ALTER TABLE t MODIFY COLUMN c INT NOT NULL AFTER d")
tests/dialects/test_mysql.py:51:            "ALTER TABLE t MODIFY COLUMN c INT NOT NULL",
[tool_use Bash] {"command": "sed -n 300,335p sqlglot/parsers/mysql.py; sed -n 225,300p sqlglot/expressions/ddl.py; grep -n \"MODIFY\\|ModifyColumn\\|_parse_alter_table_alter\\|_parse_modify\" sqlglot/parsers/mysql.py sqlglot/parser.py | head -20; sed -n 36,60p tests/dialects/test_mysql.py", "description": "Read MySQL modify-column parser and expression defs"}
[tool_result]     LOG_DEFAULTS_TO_LN = True
    STRING_ALIASES = True
    VALUES_FOLLOWED_BY_PAREN = False
    SUPPORTS_PARTITION_SELECTION = True

    def _parse_alter_table_rename(self):
        if self._match_texts(("INDEX", "KEY")):
            old = self._parse_field(any_token=True)
            self._match_text_seq("TO")
            new = self._parse_field(any_token=True)
            return self.expression(exp.RenameIndex(this=old, to=new))
        return super()._parse_alter_table_rename()

    def _par
…[3967 chars elided]…
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
[tool_use Bash] {"command": "grep -n \"FIRST\\|\\\"AFTER\\\"\\|first\\b\" sqlglot/parsers/mysql.py sqlglot/parser.py | head; grep -rn \"ModifyColumn\\|modifycolumn\" sqlglot/ tests/ | grep -v \"^sqlglot/expressions/ddl.py\"; grep -n \"SUPPORTS_MODIFY_COLUMN\" -r sqlglot/ ; cat .lithify/harness/scripts/probe_parse.py | head -30", "description": "Locate FIRST/AFTER handling and ModifyColumn usages"}
[tool_result] 33 matches in 1 files:

sqlglot/parser.py:81:if not dialect.LOG_BASE_FIRST:
sqlglot/parser.py:700:TokenType.FIRST,
sqlglot/parser.py:837:TokenType.FIRST,
sqlglot/parser.py:1589:"AFTER": tuple(),
sqlglot/parser.py:1769:# Whether the TRIM function expects the characters to trim as its first argument
sqlglot/parser.py:1770:TRIM_PATTERN_FIRST: t.ClassVar = False
sqlglot/parser.py:1827:# Whether JSON_EXTRACT requires a JSON expression as the first argument, e.g ...
sqlglot/parser.py:2048:of them, sto
…[978 chars elided]…
hows both

Exits 0 if every statement is OK, 1 if any statement is ERR or UNSTABLE, and 2
if stdin holds no statements.

Usage (use the interpreter named in memory.md):
  <python> -I .lithify/harness/scripts/probe_parse.py --read oracle < variants.sql
"""

import argparse
import sys

import sqlglot


def probe(sql, read, write):
    try:
        out = sqlglot.transpile(sql, read=read, write=write)[0]
    except Exception as e:
        return "ERR", f"{type(e).__name__}: {str(e).splitlines()[0]}"
[tool_use Bash] {"command": "sed -n 240,265p sqlglot/parsers/mysql.py; grep -n \"_parse_alter_table_modify\\|def _parse_column_def\" -A3 sqlglot/parser.py | head -20; grep -n \"_parse_column_def\" sqlglot/parser.py | head -3; <work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t MODIFY COLUMN c INT AFTER d','ALTER TABLE t CHANGE COLUMN a b INT NOT NULL AFTER d']:\n    print(repr(sqlglot.parse_one(s, read='mysql')))\n\" 2>&1 | tail -5", "description": "View MySQL ALTER parser table and probe current output"}
[tool_result]     SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
    SET_TRIE = new_trie(key.split(" ") for key in SET_PARSERS)

    CONSTRAINT_PARSERS = {
        **parser.Parser.CONSTRAINT_PARSERS,
        "FULLTEXT": lambda self: self._parse_index_constraint(kind="FULLTEXT"),
        "INDEX": lambda self: self._parse_index_constraint(),
        "KEY": lambda self: self._parse_index_constraint(),
        "SPATIAL": lambda self: self._parse_index_constraint(kind="SPATIAL"),
        "ZEROFILL": 
…[669 chars elided]…
, this: exp.Expr | None, computed_column: bool = True
7093-    ) -> exp.Expr | None:
7094-        # column defs are not really columns, they're identifiers
--
8557:    def _parse_column_def_with_exists(self):
8558-        start = self._index
8559-        self._match(TokenType.COLUMN)
8560-
8 matches in 3 files:

1048:0:lambda self: self._parse_column_def(self._parse_column()),
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -I -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t MODIFY COLUMN c INT AFTER d','ALTER TABLE t CHANGE COLUMN a b INT NOT NULL AFTER d','ALTER TABLE t CHANGE a b INT']:\n    try: print(repr(sqlglot.parse_one(s, read='mysql')))\n    except Exception as e: print('ERR', e)\n\" 2>&1 | tail -8; sed -n 8557,8575p sqlglot/parser.py; sed -n 7091,7100p sqlglot/parser.py", "description": "Probe current MODIFY/CHANGE parse behavior"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
    def _parse_column_def_with_exists(self):
        start = self._index
        self._match(TokenType.COLUMN)

        exists_column = self._parse_exists(not_=True)
        expression = self._parse_field_def()

        if not isinstance(expression, exp.ColumnDef):
            self._retreat(start)
            return None

        expression.set("exists", exists_column)

        return expression

    def _parse_add_column(self) -> exp.ColumnDef | None:
        if not self._prev.text.upper() == "ADD":
            return None

    def _parse_column_def(
        self, this: exp.Expr | None, computed_column: bool = True
    ) -> exp.Expr | None:
        # column defs are not really columns, they're identifiers
        if isinstance(this, exp.Column):
            this = this.this

        if not computed_column:
            self._match(TokenType.ALIAS)
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t MODIFY COLUMN c INT AFTER d','ALTER TABLE t CHANGE COLUMN a b INT NOT NULL AFTER d','ALTER TABLE t CHANGE a b INT']:\n    try: e=sqlglot.parse_one(s, read='mysql'); print(repr(e)); print(e.sql('mysql'))\n    except Exception as ex: print('ERR', ex)\n\" 2>&1 | tail -12", "description": "Probe current MODIFY/CHANGE parse behavior"}
[tool_result]             this=Identifier(this=d, quoted=False)),
          position=AFTER)))],
  only=False,
  not_valid=False,
  check=False,
  cascade=False,
  iceberg=False)
ALTER TABLE t MODIFY COLUMN c INT AFTER d
Command(this=ALTER, expression=TABLE t CHANGE COLUMN a b INT NOT NULL AFTER d)
ALTER TABLE t CHANGE COLUMN a b INT NOT NULL AFTER d
Command(this=ALTER, expression=TABLE t CHANGE a b INT)
ALTER TABLE t CHANGE a b INT
[tool_use Bash] {"command": "sed -n 466,474p sqlglot/generator.py; sed -n 110,116p sqlglot/generators/mysql.py; grep -n \"ALTER_PARSERS\" sqlglot/parser.py | head -3", "description": "View generator flag and MySQL generator flag context"}
[tool_result]     # Whether the CREATE TABLE LIKE statement is supported
    SUPPORTS_CREATE_TABLE_LIKE = True

    # Whether ALTER TABLE ... MODIFY COLUMN column-redefinition syntax is supported
    SUPPORTS_MODIFY_COLUMN = False

    # Whether the LikeProperty needs to be specified inside of the schema clause
    LIKE_PROPERTY_INSIDE_SCHEMA = False
    SELECT_KINDS: tuple[str, ...] = ()
    TRY_SUPPORTED = False
    SUPPORTS_UESCAPE = False
    SUPPORTS_DECODE_CASE = False
    SUPPORTS_MODIFY_COLUMN = True

    AFTER_HAVING_MODIFIER_TRANSFORMS = generator.AFTER_HAVING_MODIFIER_TRANSFORMS
5 matches in 4 files:

1435:0:t.ClassVar = {
[assistant] Now I'll make the edits: expression class, generator flag and method, and the MySQL parser.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-152946-mysql-dialect-support-change-col/base-1/sqlglot/expressions/ddl.py", "old_string": "class ModifyColumn(Expression):\n    pass\n", "new_string": "class ModifyColumn(Expression):\n    pass\n\n\nclass ChangeColumn(Expression):\n    arg_types = {\"this\": True, \"old_name\": True}\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-152946-mysql-dialect-support-change-col/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-152946-mysql-dialect-support-change-col/base-1/sqlglot/generator.py", "old_string": "    SUPPORTS_MODIFY_COLUMN = False\n\n", "new_string": "    SUPPORTS_MODIFY_COLUMN = False\n\n    # Whether ALTER TABLE ... CHANGE COLUMN old_name column-redefinition syntax is supported\n    SUPPORTS_CHANGE_COLUMN = False\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-152946-mysql-dialect-support-change-col/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-152946-mysql-dialect-support-change-col/base-1/sqlglot/generator.py", "old_string": "        return f\"MODIFY COLUMN {self.sql(expression, 'this')}\"\n", "new_string": "        return f\"MODIFY COLUMN {self.sql(expression, 'this')}\"\n\n    def changecolumn_sql(self, expression: exp.ChangeColumn) -> str:\n        if not self.SUPPORTS_CHANGE_COLUMN:\n            self.unsupported(\"CHANGE COLUMN is not supported in this dialect\")\n        return f\"CHANGE COLUMN {self.sql(expression, 'old_name')} {self.sql(expression, 'this')}\"\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-152946-mysql-dialect-support-change-col/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-152946-mysql-dialect-support-change-col/base-1/sqlglot/generators/mysql.py", "old_string": "    SUPPORTS_MODIFY_COLUMN = True\n", "new_string": "    SUPPORTS_MODIFY_COLUMN = True\n    SUPPORTS_CHANGE_COLUMN = True\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-152946-mysql-dialect-support-change-col/base-1/sqlglot/generators/mysql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-152946-mysql-dialect-support-change-col/base-1/sqlglot/parsers/mysql.py", "old_string": "        \"MODIFY\": lambda self: self._parse_alter_table_modify(),\n", "new_string": "        \"MODIFY\": lambda self: self._parse_alter_table_modify(),\n        \"CHANGE\": lambda self: self._parse_alter_table_change(),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-152946-mysql-dialect-support-change-col/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-152946-mysql-dialect-support-change-col/base-1/sqlglot/parsers/mysql.py", "old_string": "        return self.expression(exp.ModifyColumn(this=column_def))\n", "new_string": "        return self.expression(exp.ModifyColumn(this=column_def))\n\n    def _parse_alter_table_change(self) -> exp.Expr | None
…[85 chars elided]…
token=True)\n        if old_name is None:\n            return None\n\n        column = self._parse_field(any_token=True)\n        if column is None:\n            return None\n\n        column_def = self._parse_column_def(column)\n        if not isinstance(column_def, exp.ColumnDef):\n            return None\n\n        return self.expression(exp.ChangeColumn(this=column_def, old_name=old_name))\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-152946-mysql-dialect-support-change-col/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[assistant] Now I'll add tests next to the existing MODIFY ones and run the MySQL test file.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-152946-mysql-dialect-support-change-col/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"ALTER TABLE t AUTO_INCREMENT=3000000000\")\n", "new_string": "        self.validate_identity(\"ALTER TABLE t CHANGE COLUMN a b INT\")\n        self.validate_identity(\"ALTER T
…[131 chars elided]…
i'\")\n        self.validate_identity(\"ALTER TABLE t CHANGE COLUMN a b INT FIRST\")\n        self.validate_identity(\"ALTER TABLE t CHANGE COLUMN a b INT NOT NULL AFTER d\")\n        self.validate_identity(\n            \"ALTER TABLE t CHANGE a b INT\",\n            \"ALTER TABLE t CHANGE COLUMN a b INT\",\n        )\n        self.validate_identity(\"ALTER TABLE t AUTO_INCREMENT=3000000000\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-152946-mysql-dialect-support-change-col/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -30; $PY -c \"\nimport sqlglot\ne=sqlglot.parse_one('ALTER TABLE t CHANGE COLUMN a b INT AFTER d', read='mysql')\nprint(repr(e.find(sqlglot.exp.ChangeColumn)))\nprint(sqlglot.transpile('ALTER TABLE t CHANGE COLUMN a b INT', read='mysql', write='postgres'))\n\" 2>&1 | tail -4", "description": "Run MySQL dialect tests and sanity-check output"}
[tool_result] .............................. [ 60%]
....................                                              [100%]
50 passed, 481 subtests passed in 0.33s
        this=Identifier(this=d, quoted=False)),
      position=AFTER)),
  old_name=Identifier(this=a, quoted=False))
['ALTER TABLE t CHANGE COLUMN a b INT']
[assistant] MySQL tests pass. Running the full suite as the final gate.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; $PY -m ruff check sqlglot tests/dialects/test_mysql.py 2>&1 | tail -3; $PY -m ruff format --check sqlglot tests/dialects/test_mysql.py 2>&1 | tail -3", "description": "Run full test suite and ruff lint/format checks"}
[tool_result] ...................................................................................................................................................................................... [ 63%]
.......... [ 64%]
................................................................................................. [ 73%]
................................................................................................................................... [ 85%]
............................. [ 87%]
.............................................................................. [ 94%]
........................................................                                                [100%]
1106 passed, 17999 subtests passed in 56.40s
All checks passed!
176 files already formatted
[assistant] MySQL `ALTER TABLE ... CHANGE [COLUMN] old new definition [FIRST | AFTER col]` now parses and round-trips. The full suite passes (1106 tests), and ruff lint and format are clean.

Changes:

- **`sqlglot/expressions/ddl.py`**: new `ChangeColumn` expression, which mirrors `ModifyColumn` and adds an `old_name` argument. `this` is the new column definition.
- **`sqlglot/parsers/mysql.py`**: `CHANGE` is registered in `ALTER_PARSERS`, and `_parse_alter_table_change` parses the optional `COLUMN` keyword, the old name, then the column definition (which handles `FIRST`/`AFTER` the same way `MODIFY` doe
…[352 chars elided]…
aults, comments, `FIRST`, and `AFTER`, plus a case showing the `COLUMN` keyword is normalized in when omitted.

Two choices you may want to revisit:

- I added a separate `ChangeColumn` class rather than an optional `old_name` on `ModifyColumn`, so `MODIFY` output is unchanged. The generator's unsupported-dialect handling follows the `MODIFY` pattern.
- Transpiling `CHANGE COLUMN` to a non-MySQL dialect keeps the MySQL syntax and warns, rather than rewriting it to a standard form. Other dialects have no column-redefinition equivalent for this, so I didn't invent one.

I didn't commit anything.
