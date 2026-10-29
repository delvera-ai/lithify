# trajectory base-1

final message:
MySQL's `ALTER TABLE ... CHANGE [COLUMN] old new_def [FIRST | AFTER col]` now parses and round-trips. The full test suite passes (1106 passed), and ruff lint and format are clean.

`CHANGE` is represented the same way as `MODIFY`, with one extra argument. `exp.ModifyColumn` gets an optional `old_name`, and the `ColumnDef` holds the new name and full redefinition. `MODIFY` output is unchanged.

Changes:
- **`sqlglot/expressions/ddl.py`**: `ModifyColumn` takes an optional `old_name` argument.
- **`sqlglot/parsers/mysql.py`**: `CHANGE` is registered in `ALTER_PARSERS`. The column-definition parsing that `MODIFY` used is factored into a helper that `CHANGE` also calls, with the old name passed through.
- **`sqlglot/generators/mysql.py`**: `modifycolumn_sql` emits `CHANGE COLUMN old new_def` when `old_name` is set, and falls back to the existing `MODIFY COLUMN` output otherwise.
- **`tests/dialects/test_mysql.py`**: identity tests for `CHANGE COLUMN` with `NOT NULL`, `DEFAULT ... FIRST`, and `COMMENT ... AFTER`, plus a case showing `CHANGE a b` normalizes to `CHANGE COLUMN a b`, matching the existing `MODIFY c` → `MODIFY COLUMN c` normalization.

Decisions you may want to revisit:
- **Output always includes `COLUMN`**, so `CHANGE a b` comes back as `CHANGE COLUMN a b`. This follows the `MODIFY` precedent.
- **SingleStore is unaffected.** It defines its own `CHANGE` parser as a `RenameColumn`, which overrides the MySQL entry. Doris and StarRocks inherit the MySQL parser and so now also accept `CHANGE`, which is consistent with their MySQL compatibility.
- **Other dialects get a lossy result.** Transpiling `CHANGE` to a dialect without column-redefinition support (e.g. Postgres) emits `MODIFY COLUMN b INT` with an "unsupported" warning, which drops the rename. This is the same path `MODIFY` already takes. Fixing it would mean changing the base generator's handling of `old_name`; I left that alone to keep the change to MySQL.

## events
[tool_use Bash] {"command": "rtk grep -rn \"MODIFY\\|CHANGE\" sqlglot/dialects/mysql.py sqlglot/parser.py sqlglot/generator.py | head -50; rtk grep -rn \"MODIFY COLUMN\\|CHANGE COLUMN\\|AlterColumn\" tests/dialects/test_mysql.py | head", "description": "Find MODIFY/CHANGE handling in parser and generator"}
[tool_result] sqlglot/parser.py:4916:        if not self._match_text_seq("CHANGES", "(", "INFORMATION", "=>"):
sqlglot/generator.py:470:    # Whether ALTER TABLE ... MODIFY COLUMN column-redefinition syntax is supported
sqlglot/generator.py:471:    SUPPORTS_MODIFY_COLUMN = False
sqlglot/generator.py:4010:        if not self.SUPPORTS_MODIFY_COLUMN:
sqlglot/generator.py:4011:            self.unsupported("MODIFY COLUMN is not supported in this dialect")
sqlglot/generator.py:4012:        return f"MODIFY COLUMN {s
…[799 chars elided]…
       self.validate_identity("ALTER TABLE t MODIFY COLUMN c INT COMMENT 'hi'")
tests/dialects/test_mysql.py:46:        self.validate_identity("ALTER TABLE t MODIFY COLUMN c INT FIRST")
tests/dialects/test_mysql.py:47:        self.validate_identity("ALTER TABLE t MODIFY COLUMN c INT AFTER d")
tests/dialects/test_mysql.py:48:        self.validate_identity("ALTER TABLE t MODIFY COLUMN c INT NOT NULL AFTER d")
tests/dialects/test_mysql.py:51:            "ALTER TABLE t MODIFY COLUMN c INT NOT NULL",
[tool_use Bash] {"command": "rtk grep -rn \"MODIFY\\|ModifyColumn\\|SUPPORTS_MODIFY\" sqlglot/ | grep -v \"^sqlglot/dialects/mysql.py:.*#\" | head -40; sed -n 30,70p tests/dialects/test_mysql.py; rtk grep -n \"ModifyColumn\\|class AlterColumn\\|class ColumnDef\" -A12 sqlglot/expressions.py | head -60", "description": "Locate MODIFY handling and related expressions"}
[tool_result] sqlglot/parsers/clickhouse.py:445:        "MODIFY": lambda self: self._parse_alter_table_modify(),
sqlglot/parsers/snowflake.py:743:        "MODIFY": lambda self: self._parse_alter_table_alter(),
sqlglot/parsers/mysql.py:255:        "MODIFY": lambda self: self._parse_alter_table_modify(),
sqlglot/parsers/mysql.py:329:        return self.expression(exp.ModifyColumn(this=column_def))
sqlglot/generator.py:470:    # Whether ALTER TABLE ... MODIFY COLUMN column-redefinition syntax is supported
sqlglo
…[2847 chars elided]…
        check_command_warning=True,
        )
        self.validate_identity(
            "CREATE SQL SECURITY INVOKER VIEW id_test (id, foo) AS SELECT 0, foo FROM test"
        )
        self.validate_identity(
            "CREATE SQL SECURITY DEFINER VIEW id_test (id, foo) AS SELECT 0, foo FROM test"
        )
        self.validate_identity(
            "ALTER SQL SECURITY = DEFINER VIEW v AS SELECT * FROM foo", check_command_warning=True
grep: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "sed -n 240,265p sqlglot/expressions/ddl.py; sed -n 300,340p sqlglot/parsers/mysql.py; sed -n 700,725p sqlglot/generators/mysql.py; rtk grep -n \"ModifyColumn\\|ALTER_TABLE\\|ColumnDef\" -B2 -A8 sqlglot/generators/mysql.py | head -5; rtk grep -n \"ModifyColumn\" -r sqlglot | head", "description": "Read MODIFY parser, generator and expression definitions"}
[tool_result]         "drop": False,
        "comment": False,
        "allow_null": False,
        "visible": False,
        "rename_to": False,
    }


class ModifyColumn(Expression):
    pass


class AlterIndex(Expression):
    arg_types = {"this": True, "visible": True}


class AlterDistStyle(Expression):
    pass


class AlterSortKey(Expression):
    arg_types = {"this": False, "expressions": False, "compound": False}


class AlterSet(Expression):
    arg_types = {
    LOG_DEFAULTS_TO_LN = True
    STRIN
…[2503 chars elided]…
self.sql(expression, "this")
        return f"MODIFY COLUMN {this} {dtype}"

    def _prefixed_sql(self, prefix: str, expression: exp.Expr, arg: str) -> str:
        sql = self.sql(expression, arg)
        return f" {prefix} {sql}" if sql else ""

sqlglot/parsers/mysql.py:329:        return self.expression(exp.ModifyColumn(this=column_def))
sqlglot/generator.py:4009:    def modifycolumn_sql(self, expression: exp.ModifyColumn) -> str:
sqlglot/expressions/ddl.py:248:class ModifyColumn(Expression):
[tool_use Bash] {"command": "sed -n 245,262p sqlglot/parsers/mysql.py; rtk grep -n \"def modifycolumn_sql\" -A4 sqlglot/generator.py; rtk grep -n \"ALTER_PARSERS\\b\" -A3 sqlglot/parser.py | head -20; rtk grep -rn '\"CHANGE\"' sqlglot | head; git log --oneline -3 -- sqlglot/parsers/mysql.py", "description": "Inspect ALTER parser dispatch and related code"}
[tool_result]         "FULLTEXT": lambda self: self._parse_index_constraint(kind="FULLTEXT"),
        "INDEX": lambda self: self._parse_index_constraint(),
        "KEY": lambda self: self._parse_index_constraint(),
        "SPATIAL": lambda self: self._parse_index_constraint(kind="SPATIAL"),
        "ZEROFILL": lambda self: self.expression(exp.ZeroFillColumnConstraint()),
        "INVISIBLE": lambda self: self.expression(exp.InvisibleColumnConstraint()),
    }

    ALTER_PARSERS = {
        **parser.Parser.A
…[1501 chars elided]…
    if parser:
8792-            actions = ensure_list(parser(self))
8793-            not_valid = self._match_text_seq("NOT", "VALID")
sqlglot/parsers/singlestore.py:238:        "CHANGE": lambda self: self.expression(
sqlglot/parsers/hive.py:139:        "CHANGE": lambda self: self._parse_alter_table_change(),
206e2f892 fix(mysql)!: full `MODIFY COLUMN` support. (#7562)
a88dfce09 fix(mysql): support SHOW TABLES IN <schema> parsing (#7537)
68861d9f3 feat(mysql)!: support `DROP PRIMARY KEY`. (#7530)
[tool_use Bash] {"command": "rtk grep -n \"def _parse_alter_table_change\" -A25 sqlglot/parsers/hive.py; rtk grep -n \"def _parse_column_def\" -A3 sqlglot/parser.py; git show 206e2f892 --stat; rtk grep -rn \"RenameColumn\\|class AlterColumn\\b\" -A3 sqlglot/expressions/ddl.py | head -20", "description": "Read Hive CHANGE parsing and MODIFY commit scope"}
[tool_result] 238:    def _parse_alter_table_change(self) -> exp.Expr | None:
239-        self._match(TokenType.COLUMN)
240-        this = self._parse_field(any_token=True)
241-
242-        if self.CHANGE_COLUMN_ALTER_SYNTAX and self._match_text_seq("TYPE"):
243-            return self.expression(exp.AlterColumn(this=this, dtype=self._parse_types(schema=True)))
244-
245-        column_new = self._parse_field(any_token=True)
246-        dtype = self._parse_types(schema=True)
247-
248-        comment = self._ma
…[2893 chars elided]…
++++++++
 6 files changed, 48 insertions(+), 15 deletions(-)
sqlglot/expressions/ddl.py:233:class AlterColumn(Expression):
sqlglot/expressions/ddl.py-234-    arg_types = {
sqlglot/expressions/ddl.py-235-        "this": True,
sqlglot/expressions/ddl.py-236-        "dtype": False,
--
sqlglot/expressions/ddl.py:278:class RenameColumn(Expression):
sqlglot/expressions/ddl.py-279-    arg_types = {"this": True, "to": True, "exists": False}
sqlglot/expressions/ddl.py-280-
sqlglot/expressions/ddl.py-281-
[tool_use Bash] {"command": "sed -n 230,245p sqlglot/parsers/singlestore.py; rtk grep -n \"^class\\|ALTER_PARSERS\" sqlglot/parsers/singlestore.py sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py sqlglot/dialects/singlestore.py 2>/dev/null | head; rtk grep -n \"class.*MySQL\\|mysql\" sqlglot/dialects/doris.py sqlglot/dialects/starrocks.py | head -5", "description": "Check subclasses that inherit MySQL parser dispatch"}
[tool_result]         "USERS FOR ROLE": _show_parser("USERS FOR ROLE", target=True),
        "USERS FOR GROUP": _show_parser("USERS FOR GROUP", target=True),
    }

    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)

    ALTER_PARSERS = {
        **MySQLParser.ALTER_PARSERS,
        "CHANGE": lambda self: self.expression(
            exp.RenameColumn(this=self._parse_column(), to=self._parse_column())
        ),
    }

    def _parse_vector_expressions(self, expressions: list[exp.Expr]) -> list[
…[229 chars elided]…
lass DorisParser(MySQLParser):
sqlglot/parsers/singlestore.py:23:class SingleStoreParser(MySQLParser):
sqlglot/parsers/singlestore.py:236:ALTER_PARSERS = {
sqlglot/parsers/singlestore.py:237:**MySQLParser.ALTER_PARSERS,
sqlglot/parsers/starrocks.py:11:class StarRocksParser(MySQLParser):
5 matches in 2 files:

sqlglot/dialects/doris.py:3:from sqlglot.dialects.mysql import MySQL
sqlglot/dialects/doris.py:8:class Doris(MySQL):
sqlglot/dialects/starrocks.py:3:from sqlglot.dialects.mysql import MySQL
[assistant] Picture so far: MySQL's `MODIFY` parses to `exp.ModifyColumn(this=ColumnDef)`, and the MySQL generator emits it via the base `modifycolumn_sql`. SingleStore overrides `CHANGE` itself, so adding it to MySQL's `ALTER_PARSERS` won't disturb it. I'll add an optional `old_name` arg to `ModifyColumn` and share the column-definition parsing between `MODIFY` and `CHANGE`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-190613-mysql-dialect-support-change-col/base-1/sqlglot/expressions/ddl.py", "old_string": "class ModifyColumn(Expression):\n    pass", "new_string": "class ModifyColumn(Expression):\n    arg_types = {\"this\": True, \"old_name\": False}"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-190613-mysql-dialect-support-change-col/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-190613-mysql-dialect-support-change-col/base-1/sqlglot/generators/mysql.py", "offset": 700, "limit": 25}
[tool_result] 700	        for_group = self._prefixed_sql("FOR GROUP", expression, "for_group")
701	        for_user = self._prefixed_sql("FOR USER", expression, "for_user")
702	        for_role = self._prefixed_sql("FOR ROLE", expression, "for_role")
703	        into_outfile = self._prefixed_sql("INTO OUTFILE", expression, "into_outfile")
704	        json = " JSON" if expression.args.get("json") else ""
705	
706	        return f"SHOW{full}{global_}{this}{json}{target}{for_table}{types}{db}{query}{log}{positio
…[455 chars elided]…
13	
714	    def altercolumn_sql(self, expression: exp.AlterColumn) -> str:
715	        dtype = self.sql(expression, "dtype")
716	        if not dtype:
717	            return super().altercolumn_sql(expression)
718	
719	        this = self.sql(expression, "this")
720	        return f"MODIFY COLUMN {this} {dtype}"
721	
722	    def _prefixed_sql(self, prefix: str, expression: exp.Expr, arg: str) -> str:
723	        sql = self.sql(expression, arg)
724	        return f" {prefix} {sql}" if sql else ""
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-190613-mysql-dialect-support-change-col/base-1/sqlglot/generators/mysql.py", "old_string": "        this = self.sql(expression, \"this\")\n        return f\"MODIFY COLUMN {this} {dtype}\"\n\n    def _prefixed_sql(", "new_string": "        this = self.sql(expression, \"this\")\n        return f\"MODIFY COLUMN {this} {dtype}\"\n\n    def modifycolumn_sql(self, expression: exp.ModifyColumn) -> str:\n        old_name = self.sql(expression, \"old_name\")\n        if not old_name:\n            return super().modifycolumn_sql(expression)\n\n        return f\"CHANGE COLUMN {old_name} {self.sql(expression, 'this')}\"\n\n    def _prefixed_sql("}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-190613-mysql-dialect-support-change-col/base-1/sqlglot/generators/mysql.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-190613-mysql-dialect-support-change-col/base-1/sqlglot/parsers/mysql.py", "offset": 252, "limit": 5}
[tool_result] 252	
253	    ALTER_PARSERS = {
254	        **parser.Parser.ALTER_PARSERS,
255	        "MODIFY": lambda self: self._parse_alter_table_modify(),
256	        "AUTO_INCREMENT": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-190613-mysql-dialect-support-change-col/base-1/sqlglot/parsers/mysql.py", "old_string": "        \"MODIFY\": lambda self: self._parse_alter_table_modify(),\n        \"AUTO_INCREMENT\"", "new_string": "        \"MODIFY\": lambda self: self._parse_alter_table_modify(),\n        \"CHANGE\": lambda self: self._parse_alter_table_change(),\n        \"AUTO_INCREMENT\""}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-190613-mysql-dialect-support-change-col/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-190613-mysql-dialect-support-change-col/base-1/sqlglot/parsers/mysql.py", "old_string": "    def _parse_alter_table_modify(self) -> exp.Expr | None:\n        self._match(TokenType.COLUMN)\n\n        column = self._parse_field(any_token=True)\n        if column is None:\n            return None\n\n   
…[596 chars elided]…
ify_column(self, old_name: exp.Expr | None = None) -> exp.Expr | None:\n        column = self._parse_field(any_token=True)\n        if column is None:\n            return None\n\n        column_def = self._parse_column_def(column)\n        if not isinstance(column_def, exp.ColumnDef):\n            return None\n\n        return self.expression(exp.ModifyColumn(this=column_def, old_name=old_name))"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-190613-mysql-dialect-support-change-col/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[assistant] Now the tests, next to the existing `MODIFY` identities.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-190613-mysql-dialect-support-change-col/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\n            \"ALTER TABLE t MODIFY c INT NOT NULL\",\n            \"ALTER TABLE t MODIFY COLUMN c INT NOT NULL\",\n        )", "new_string": "        self.validate_identity(\n
…[162 chars elided]…
ER TABLE t CHANGE COLUMN a b INT NOT NULL\")\n        self.validate_identity(\"ALTER TABLE t CHANGE COLUMN a b INT DEFAULT 5 FIRST\")\n        self.validate_identity(\"ALTER TABLE t CHANGE COLUMN a b VARCHAR(50) COMMENT 'hi' AFTER c\")\n        self.validate_identity(\n            \"ALTER TABLE t CHANGE a b INT NOT NULL\",\n            \"ALTER TABLE t CHANGE COLUMN a b INT NOT NULL\",\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-190613-mysql-dialect-support-change-col/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -30; $PY -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t CHANGE COLUMN a b INT', 'ALTER TABLE t CHANGE a b INT']:\n    e = sqlglot.parse_one(s, read='mysql'); print(repr(e.args['actions'][0].args.get('old_name')), e.sql('mysql'))\nprint(sqlglot.transpile('ALTER TABLE t CHANGE a b INT', read='mysql', write='postgres'))\n\"", "description": "Run MySQL dialect tests and spot-check CHANGE output"}
[tool_result] .............................. [ 60%]
....................                                              [100%]
50 passed, 481 subtests passed in 0.37s
MODIFY COLUMN is not supported in this dialect
Identifier(this=a, quoted=False) ALTER TABLE t CHANGE COLUMN a b INT
Identifier(this=a, quoted=False) ALTER TABLE t CHANGE COLUMN a b INT
['ALTER TABLE t MODIFY COLUMN b INT']
[assistant] MySQL tests pass. Now the full suite, since `ALTER_PARSERS` and `ModifyColumn` are shared with Doris, StarRocks, and the generic base.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; git status --short", "description": "Run full test suite and show changed files"}
[tool_result] ...................................................................................................................................................................................... [ 63%]
.......... [ 64%]
................................................................................................. [ 73%]
................................................................................................................................... [ 85%]
............................. [ 87%]
.............................................................................. [ 94%]
........................................................                                                [100%]
1106 passed, 17999 subtests passed in 47.51s
 M sqlglot/expressions/ddl.py
 M sqlglot/generators/mysql.py
 M sqlglot/parsers/mysql.py
 M tests/dialects/test_mysql.py
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/expressions/ddl.py sqlglot/generators/mysql.py sqlglot/parsers/mysql.py tests/dialects/test_mysql.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/expressions/ddl.py sqlglot/generators/mysql.py sqlglot/parsers/mysql.py tests/dialects/test_mysql.py) 2>&1 | tail -5", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
4 files already formatted
[assistant] MySQL's `ALTER TABLE ... CHANGE [COLUMN] old new_def [FIRST | AFTER col]` now parses and round-trips. The full test suite passes (1106 passed), and ruff lint and format are clean.

`CHANGE` is represented the same way as `MODIFY`, with one extra argument. `exp.ModifyColumn` gets an optional `old_name`, and the `ColumnDef` holds the new name and full redefinition. `MODIFY` output is unchanged.

Changes:
- **`sqlglot/expressions/ddl.py`**: `ModifyColumn` takes an optional `old_name` argument.
- **`sqlglot/parsers/mysql.py`**: `CHANGE` is registered in `ALTER_PARSERS`. The column-definition parsi
…[751 chars elided]…
.** It defines its own `CHANGE` parser as a `RenameColumn`, which overrides the MySQL entry. Doris and StarRocks inherit the MySQL parser and so now also accept `CHANGE`, which is consistent with their MySQL compatibility.
- **Other dialects get a lossy result.** Transpiling `CHANGE` to a dialect without column-redefinition support (e.g. Postgres) emits `MODIFY COLUMN b INT` with an "unsupported" warning, which drops the rename. This is the same path `MODIFY` already takes. Fixing it would mean changing the base generator's handling of `old_name`; I left that alone to keep the change to MySQL.
