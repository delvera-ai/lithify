# trajectory base-1

final message:
MySQL `MODIFY [COLUMN] col <definition> [FIRST | AFTER col]` now parses into its own node and round-trips. All four examples from your request pass as identity tests, and the full suite passes (1094 tests), with ruff clean.

What changed:

- **Parser** (`sqlglot/parsers/mysql.py`): `MODIFY` gets a dedicated `_parse_alter_table_modify`. It parses a full column definition plus an optional `FIRST`/`AFTER` position. If no column definition follows, it falls back to the old alter-column path, so `ALTER COLUMN ... SET DATA TYPE` still round-trips to `MODIFY COLUMN c LONGTEXT` as before.
- **Expression** (`sqlglot/expressions/ddl.py`): new `ModifyColumn(this=ColumnDef)` node, so MySQL's whole-column redefinition is no longer represented as an `AlterColumn`.
- **MySQL generator** (`sqlglot/generators/mysql.py`): `modifycolumn_sql` emits `MODIFY COLUMN <column def>`.
- **Base generator** (`sqlglot/generator.py`): for non-MySQL output, `ModifyColumn` degrades to `ALTER COLUMN c SET DATA TYPE <type>`. If the definition has constraints or a position, it raises an unsupported warning, since those can't be expressed that way. Without this fallback, transpiling to other dialects would raise `Unsupported expression type ModifyColumn`.
- **Tests** (`tests/dialects/test_mysql.py`): identity tests for the four examples plus `AFTER d`.

Choices to confirm:
- The `MODIFY` keyword without `COLUMN` also parses and comes back with `COLUMN` added, which matches MySQL's own normalization.
- I added a new expression class rather than reusing `AlterColumn`, because no existing node carries a full column definition with constraints and position.

I haven't committed anything.

## events
[tool_use Bash] {"command": "grep -n \"MODIFY\\|ALTER_TABLE\\|AlterColumn\\|_parse_alter_table\" sqlglot/dialects/mysql.py sqlglot/parser.py sqlglot/generator.py sqlglot/dialects/dialect.py | head -60; grep -n \"class AlterColumn\\|class AlterTable\\|class ColumnDef\" -A12 sqlglot/expressions.py | head -80", "description": "Locate ALTER TABLE handling in sqlglot"}
[tool_result] sqlglot/generator.py:396:    ALTER_TABLE_INCLUDE_COLUMN_KEYWORD = True
sqlglot/generator.py:3903:    def altercolumn_sql(self, expression: exp.AlterColumn) -> str:
sqlglot/generator.py:3986:        if not self.dialect.ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN and isinstance(
sqlglot/generator.py:4021:            if expression.args.get("cascade") and self.dialect.ALTER_TABLE_SUPPORTS_CASCADE
sqlglot/generator.py:4038:        elif isinstance(expression, exp.ColumnDef) and self.ALTER_TABLE_INCLUDE_C
…[1879 chars elided]…
.Expr]:
sqlglot/parser.py:8643:    def _parse_alter_table_rename(self) -> exp.AlterRename | exp.RenameColumn | None:
sqlglot/parser.py:8658:    def _parse_alter_table_set(self) -> exp.AlterSet:
sqlglot/parser.py:8725:            this = self._parse_table(schema=True, parse_partition=self.ALTER_TABLE_PARTITIONS)
sqlglot/parser.py:8737:            cascade = self.dialect.ALTER_TABLE_SUPPORTS_CASCADE and self._match_text_seq("CASCADE")
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "sed -n 8530,8640p sqlglot/parser.py; sed -n 8715,8760p sqlglot/parser.py; sed -n 3900,3935p sqlglot/generator.py; sed -n 3975,4050p sqlglot/generator.py; grep -rn \"MODIFY\\|AlterColumn\\|\\\"FIRST\\\"\\|position\" sqlglot/dialects/mysql.py | head; grep -n \"class AlterColumn\" -A20 sqlglot/expressions/*.py | head -40", "description": "Read ALTER parsing and generation code"}
[tool_result]     # https://docs.aws.amazon.com/athena/latest/ug/alter-table-drop-partition.html
    def _parse_drop_partition(self, exists: bool | None = None) -> exp.DropPartition:
        return self.expression(
            exp.DropPartition(expressions=self._parse_csv(self._parse_partition), exists=exists)
        )

    def _parse_alter_table_add(self) -> list[exp.Expr]:
        def _parse_add_alteration() -> exp.Expr | None:
            self._match_text_seq("ADD")
            if self._match_set(self.ADD
…[11226 chars elided]…
y-243-        "visible": False,
sqlglot/expressions/ddl.py-244-        "rename_to": False,
sqlglot/expressions/ddl.py-245-    }
sqlglot/expressions/ddl.py-246-
sqlglot/expressions/ddl.py-247-
sqlglot/expressions/ddl.py-248-class AlterIndex(Expression):
sqlglot/expressions/ddl.py-249-    arg_types = {"this": True, "visible": True}
sqlglot/expressions/ddl.py-250-
sqlglot/expressions/ddl.py-251-
sqlglot/expressions/ddl.py-252-class AlterDistStyle(Expression):
sqlglot/expressions/ddl.py-253-    pass
[tool_use Bash] {"command": "grep -n \"ALTER_PARSERS\\|ALTER_ALTER_PARSERS\\|_parse_add_column\\|_parse_column_def_with_exists\\|\\\"FIRST\\\"\\|\\\"AFTER\\\"\\|ColumnPosition\\|ColumnDef(\" sqlglot/parser.py sqlglot/dialects/mysql.py sqlglot/generator.py | head -40; grep -n \"class ColumnDef\\|class ColumnPosition\" -A12 sqlglot/expressions/*.py; grep -rn \"MODIFY\" tests/dialects/test_mysql.py tests/dialects/test_dialect.py | head", "description": "Find ALTER parsers, column position handling, MODIFY tests"}
[tool_result] sqlglot/generator.py:1136:    def columnposition_sql(self, expression: exp.ColumnPosition) -> str:
sqlglot/generator.py:3014:            limit = exp.Fetch(direction="FIRST", count=exp.maybe_copy(limit.expression))
sqlglot/generator.py:3246:            first = "FIRST" if first else "LAST"
sqlglot/parser.py:1434:    ALTER_PARSERS: t.ClassVar = {
sqlglot/parser.py:1448:    ALTER_ALTER_PARSERS: t.ClassVar = {
sqlglot/parser.py:1588:        "AFTER": tuple(),
sqlglot/parser.py:2719:            "after"
…[2409 chars elided]…
False,
sqlglot/expressions/query.py-509-        "output": False,
sqlglot/expressions/query.py-510-    }
sqlglot/expressions/query.py-511-
sqlglot/expressions/query.py-512-    @property
sqlglot/expressions/query.py-513-    def constraints(self) -> list[ColumnConstraint]:
tests/dialects/test_mysql.py:40:        self.validate_identity("ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT")
tests/dialects/test_mysql.py:167:            "ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT",
[tool_use Bash] {"command": "sed -n 1430,1450p sqlglot/parser.py; sed -n 8489,8530p sqlglot/parser.py; sed -n 1130,1145p sqlglot/generator.py; sed -n 160,175p tests/dialects/test_mysql.py; sed -n 35,42p tests/dialects/test_mysql.py; grep -n \"ALTER_TABLE\\|class Parser\" sqlglot/dialects/mysql.py; grep -n \"def columndef_sql\" -A25 sqlglot/generator.py | grep -n position", "description": "Read column def helpers and existing MySQL tests"}
[tool_result]             this, expression = expression, this

        return self.expression(klass(this=this, expression=expression))

    ALTER_PARSERS: t.ClassVar = {
        "ADD": lambda self: self._parse_alter_table_add(),
        "AS": lambda self: self._parse_select(),
        "ALTER": lambda self: self._parse_alter_table_alter(),
        "CLUSTER BY": lambda self: self._parse_cluster(wrapped=True),
        "DELETE": lambda self: self.expression(exp.Delete(where=self._parse_where())),
        "DROP": 
…[3875 chars elided]…
("ALTER TABLE t DROP COLUMN c, DROP PRIMARY KEY, DROP INDEX `i`")
        self.validate_identity("ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT")
        self.validate_identity("ALTER TABLE t AUTO_INCREMENT=3000000000")
        self.validate_identity("ALTER VIEW v AS SELECT a, b, c, d FROM foo")
8:1149-        position = self.sql(expression, "position")
9:1150-        position = f" {position}" if position else ""
14:1155-        return f"{exists}{column}{kind}{constraints}{position}"
[tool_use Bash] {"command": "grep -n \"class \\|^    [A-Z_]* = \\|def _parse\\|_parse_column_def\\|ALTER\" sqlglot/dialects/mysql.py | head -80; grep -rn \"MODIFY\" sqlglot/ | grep -v \"^sqlglot/dialects/mysql\" | head; grep -n \"import\\|ddl\" sqlglot/expressions/__init__.py | head -20; wc -l sqlglot/dialects/mysql.py", "description": "Inspect MySQL dialect structure and MODIFY references"}
[tool_result] 14:class MySQL(Dialect):
15:    PROMOTE_TO_INFERRED_DATETIME_TYPE = True
18:    IDENTIFIERS_CAN_START_WITH_DIGIT = True
25:    NORMALIZATION_STRATEGY = NormalizationStrategy.CASE_SENSITIVE
27:    TIME_FORMAT = "'%Y-%m-%d %T'"
28:    DPIPE_IS_STRING_CONCAT = False
29:    SUPPORTS_USER_DEFINED_TYPES = False
30:    SAFE_DIVISION = True
31:    SAFE_TO_ELIMINATE_DOUBLE_NEGATION = False
32:    LEAST_GREATEST_IGNORES_NULLS = False
34:    EXPRESSION_METADATA = EXPRESSION_METADATA.copy()
37:    TIME_MAPP
…[1342 chars elided]…
glot.expressions.functions import *  # noqa: F401,F403
28:from sqlglot.expressions.builders import *  # noqa: F401,F403
30:# Explicitly import private helpers (not exported by star imports)
31:from sqlglot.expressions.core import (  # noqa: F401,E402
43:from sqlglot.expressions.query import _apply_cte_builder  # noqa: F401,E402
44:from sqlglot.expressions.dml import DML  # noqa: F401,E402
45:from sqlglot.expressions.array import _ExplodeOuter  # noqa: F401,E402
     158 sqlglot/dialects/mysql.py
[tool_use Bash] {"command": "sed -n 240,275p sqlglot/parsers/mysql.py; echo ----; sed -n 695,730p sqlglot/generators/mysql.py; echo ----; grep -n \"ALTER_PARSERS\\|^from\\|^import\" sqlglot/parsers/mysql.py | head -30; echo ----; grep -n \"_parse_alter_table_modify\" -A12 sqlglot/parsers/clickhouse.py | head -30", "description": "Read MySQL parser/generator ALTER handling"}
[tool_result]     SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
    SET_TRIE = new_trie(key.split(" ") for key in SET_PARSERS)

    CONSTRAINT_PARSERS = {
        **parser.Parser.CONSTRAINT_PARSERS,
        "FULLTEXT": lambda self: self._parse_index_constraint(kind="FULLTEXT"),
        "INDEX": lambda self: self._parse_index_constraint(),
        "KEY": lambda self: self._parse_index_constraint(),
        "SPATIAL": lambda self: self._parse_index_constraint(kind="SPATIAL"),
        "ZEROFILL": 
…[3721 chars elided]…
xpressions=properties.expressions))
833-        return None
834-
835-    def _parse_definer(self) -> exp.DefinerProperty | None:
836-        self._match(TokenType.EQ)
837-        if self._match(TokenType.CURRENT_USER):
838-            return exp.DefinerProperty(this=exp.Var(this=self._prev.text.upper()))
839-        return exp.DefinerProperty(this=self._parse_string())
840-
841-    def _parse_projection_def(self) -> exp.ProjectionDef | None:
842-        if not self._match_text_seq("PROJECTION"):
[tool_use Bash] {"command": "sed -n 228,247p sqlglot/expressions/ddl.py; grep -n \"def unsupported\" sqlglot/generator.py; grep -n \"altercolumn_sql\" sqlglot/generators/*.py | head; grep -rn \"MODIFY COLUMN\" tests/ | head", "description": "Inspect AlterColumn class and existing MODIFY test expectations"}
[tool_result] class CharacterSet(Expression):
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


30:def unsupported_args(
957:    def unsupported(self, message: str) -> None:
sqlglot/generators/hive.py:4
…[752 chars elided]…
'bar'",
tests/dialects/test_singlestore.py:962:        self.validate_identity("ALTER TABLE t MODIFY COLUMN name TEXT COLLATE 'binary'")
tests/dialects/test_snowflake.py:4399:                        "snowflake": f"ALTER TABLE a MODIFY COLUMN my_column {action} NOT NULL",
tests/dialects/test_mysql.py:40:        self.validate_identity("ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT")
tests/dialects/test_mysql.py:167:            "ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT",
[assistant] Existing MySQL `MODIFY` is routed to the alter-column path, so I'll give it its own parser branch and expression. Making the edits now.
[tool_use Bash] {"command": "grep -n \"_parse_alter_table_alter_index\" -B3 -A12 sqlglot/parsers/mysql.py | sed -n 1,30p; grep -n \"def _parse_alter_table_alter\\b\\|def _parse_alter_table_alter(\" sqlglot/parser.py", "description": "Locate MySQL alter-index parser for placement"}
[tool_result] 258-
259-    ALTER_ALTER_PARSERS = {
260-        **parser.Parser.ALTER_ALTER_PARSERS,
261:        "INDEX": lambda self: self._parse_alter_table_alter_index(),
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
273-        **dict.fromkeys(("ALL", "CPU", "IPC", "MEMORY", "SOURCE", "SWAPS"), tup
…[29 chars elided]…
se_interval=parse_interval, fallback_to_identifier=fallback_to_identifier
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
8576:    def _parse_alter_table_alter(self) -> exp.Expr | None:
[tool_use Bash] {"command": "sed -n 547,552p sqlglot/parsers/mysql.py", "description": "Read end of MySQL alter-index parser"}
[tool_result]         return self.expression(exp.AlterIndex(this=index, visible=visible))

    def _parse_partition_property(
        self,
    ) -> exp.Expr | None | list[exp.Expr]:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-194158-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py", "old_string": "        \"MODIFY\": lambda self: self._parse_alter_table_alter(),\n        \"AUTO_INCREMENT\"", "new_string": "        \"MODIFY\": lambda self: self._parse_alter_table_modify(),\n        \"AUTO_INCREMENT\""}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-194158-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-194158-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py", "old_string": "        return self.expression(exp.AlterIndex(this=index, visible=visible))\n\n    def _parse_partition_property(", "new_string": "        return self.expression(exp.AlterIndex(this=index, visible=visible))\n\n  
…[249 chars elided]…
eturn self._parse_alter_table_alter()\n\n        if self._match_texts((\"FIRST\", \"AFTER\")):\n            position = self._prev.text\n            column_def.set(\n                \"position\", self.expression(exp.ColumnPosition(this=self._parse_column(), position=position))\n            )\n\n        return self.expression(exp.ModifyColumn(this=column_def))\n\n    def _parse_partition_property("}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-194158-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-194158-mysql-dialect-alter-table-modify/base-1/sqlglot/expressions/ddl.py", "old_string": "        \"visible\": False,\n        \"rename_to\": False,\n    }\n\n\nclass AlterIndex(", "new_string": "        \"visible\": False,\n        \"rename_to\": False,\n    }\n\n\nclass ModifyColumn(Expression):\n    arg_types = {\"this\": True}\n\n\nclass AlterIndex("}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-194158-mysql-dialect-alter-table-modify/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-194158-mysql-dialect-alter-table-modify/base-1/sqlglot/generators/mysql.py", "old_string": "        this = self.sql(expression, \"this\")\n        return f\"MODIFY COLUMN {this} {dtype}\"\n", "new_string": "        this = self.sql(expression, \"this\")\n        return f\"MODIFY COLUMN {this} {dtype}\"\n\n    def modifycolumn_sql(self, expression: exp.ModifyColumn) -> str:\n        return f\"MODIFY COLUMN {self.sql(expression, 'this')}\"\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-194158-mysql-dialect-alter-table-modify/base-1/sqlglot/generators/mysql.py has been updated successfully.
[assistant] Now the tests: round-trip identities for the four examples in the MySQL test file, next to the existing `MODIFY` identity.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-194158-mysql-dialect-alter-table-modify/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT\")\n        self.validate_identity(\"ALTER TABLE t AUTO_INCREMENT=3000000000\")", "new_string": "        self.validat
…[184 chars elided]…
te_identity(\"ALTER TABLE t MODIFY COLUMN c VARCHAR(50) NOT NULL DEFAULT 'foo'\")\n        self.validate_identity(\"ALTER TABLE t MODIFY COLUMN c INT COMMENT 'hi'\")\n        self.validate_identity(\"ALTER TABLE t MODIFY COLUMN c INT FIRST\")\n        self.validate_identity(\"ALTER TABLE t MODIFY COLUMN c INT AFTER d\")\n        self.validate_identity(\"ALTER TABLE t AUTO_INCREMENT=3000000000\")"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-194158-mysql-dialect-alter-table-modify/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py tests/dialects/test_singlestore.py tests/dialects/test_doris.py tests/dialects/test_starrocks.py 2>&1 | tail -30; /private/tmp/claude-501/-Users-user-Coding-de
…[39 chars elided]…
9-4b3c-8461-34bf1f0fcf2a/scratchpad/hwork/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t MODIFY COLUMN c INT FIRST','ALTER TABLE t MODIFY COLUMN c INT NOT NULL DEFAULT 5']:\n    e=sqlglot.parse_one(s,read='mysql'); print(repr(e.args['actions'][0]))\n    for d in ['postgres','mysql']: print(d, e.sql(d))\n\"", "description": "Run MySQL-family tests and inspect parsed output"}
[tool_result ERROR] Exit code 1
.............................. [ 30%]
......................................................................                         [100%]
100 passed, 812 subtests passed in 0.79s
Traceback (most recent call last):
  File "<string>", line 5, in <module>
  File "~/.cache/lithify/work/repo-161bf5b46800/20261026-194158-mysql-dialect-alter-table-modify/base-1/sqlglot/expressions/core.py", line 1097, in sql
    return Dialect.get_or_raise(dialect).generate(self, copy=copy, *
…[1061 chars elided]…
^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-161bf5b46800/20261026-194158-mysql-dialect-alter-table-modify/base-1/sqlglot/generator.py", line 1089, in sql
    raise ValueError(f"Unsupported expression type {expression.__class__.__name__}")
ValueError: Unsupported expression type ModifyColumn
ModifyColumn(
  this=ColumnDef(
    this=Identifier(this=c, quoted=False),
    kind=DataType(this=DType.INT, nested=False),
    exists=False,
    position=ColumnPosition(position=FIRST)))
[assistant] MySQL round-trips pass (100 tests). Other dialects currently hit `Unsupported expression type ModifyColumn`, so I'll add a base-generator fallback that degrades to `ALTER COLUMN ... SET DATA TYPE` and flags anything it can't express.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-194158-mysql-dialect-alter-table-modify/base-1/sqlglot/generator.py", "old_string": "    def alterset_sql(self, expression: exp.AlterSet) -> str:", "new_string": "    def modifycolumn_sql(self, expression: exp.ModifyColumn) -> str:\n        column = expression.this\n        if column.args.get(\"constraints\") or column.args.get(\"position\"):\n            self.unsupported(\"MODIFY COLUMN with constraints or a position is not supported\")\n\n        return self.sql(exp.AlterColumn(this=column.this, dtype=column.args.get(\"kind\")))\n\n    def alterset_sql(self, expression: exp.AlterSet) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-194158-mysql-dialect-alter-table-modify/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t MODIFY COLUMN c INT FIRST','ALTER TABLE t MODIFY COLUMN c INT NOT NULL DEFAULT 5', 'ALTER TABLE t MODIFY COLUMN c INT AFTER d']:\n    e=sqlglot.parse_one(s,read='mysql')\n    for d in ['mysql','postgres']: print(d, '|', e.sql(d))\n\" 2>&1; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Check cross-dialect output and run full test suite"}
[tool_result] MODIFY COLUMN with constraints or a position is not supported
MODIFY COLUMN with constraints or a position is not supported
MODIFY COLUMN with constraints or a position is not supported
mysql | ALTER TABLE t MODIFY COLUMN c INT FIRST
postgres | ALTER TABLE t ALTER COLUMN c SET DATA TYPE INT
mysql | ALTER TABLE t MODIFY COLUMN c INT NOT NULL DEFAULT 5
postgres | ALTER TABLE t ALTER COLUMN c SET DATA TYPE INT
mysql | ALTER TABLE t MODIFY COLUMN c INT AFTER d
postgres | ALTER TABLE t ALTER COLUMN c
…[813 chars elided]…
....................................................... [ 71%]
............................................. [ 75%]
............................................. [ 79%]
............................... [ 82%]
............................................................................................................................................................................................                                           [100%]
1094 passed, 17872 subtests passed in 78.82s (0:01:18)
[assistant] Full suite passes (1094 tests). Running the linter on the changed files.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin; ($P/ruff --version || $P/python -m ruff --version) 2>&1; $P/ruff format sqlglot/parsers/mysql.py sqlglot/generators/mysql.py sqlglot/generator.py sqlglot/expressions/ddl.py tests/dialects/test_mysql.py 2>&1; $P/ruff check sqlglot tests/dialects/test_mysql.py 2>&1 | tail -3; git status --short; git diff --stat", "description": "Format and lint changed files, show diff stat"}
[tool_result] ruff 0.15.6
1 file reformatted, 4 files left unchanged
All checks passed!
 M sqlglot/expressions/ddl.py
 M sqlglot/generator.py
 M sqlglot/generators/mysql.py
 M sqlglot/parsers/mysql.py
 M tests/dialects/test_mysql.py
 sqlglot/expressions/ddl.py   |  4 ++++
 sqlglot/generator.py         |  7 +++++++
 sqlglot/generators/mysql.py  |  3 +++
 sqlglot/parsers/mysql.py     | 18 +++++++++++++++++-
 tests/dialects/test_mysql.py |  5 +++++
 5 files changed, 36 insertions(+), 1 deletion(-)
[This command modified 1 file you've previously read: sqlglot/parsers/mysql.py. Call Read before editing.]
[assistant] The formatter rewrapped a line in `parsers/mysql.py`. I'll confirm the final diff and re-run the MySQL tests.
[tool_use Bash] {"command": "git diff sqlglot/parsers/mysql.py; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects tests/test_transpile.py 2>&1 | tail -2", "description": "Review parser diff and re-run dialect tests"}
[tool_result] diff --git a/sqlglot/parsers/mysql.py b/sqlglot/parsers/mysql.py
index d4bf7e3c0..1f376557b 100644
--- a/sqlglot/parsers/mysql.py
+++ b/sqlglot/parsers/mysql.py
@@ -252,7 +252,7 @@ class MySQLParser(parser.Parser):
 
     ALTER_PARSERS = {
         **parser.Parser.ALTER_PARSERS,
-        "MODIFY": lambda self: self._parse_alter_table_alter(),
+        "MODIFY": lambda self: self._parse_alter_table_modify(),
         "AUTO_INCREMENT": lambda self: self._parse_property_assignment(exp.AutoIncrement
…[613 chars elided]…
 self.expression(exp.ColumnPosition(this=self._parse_column(), position=position)),
+            )
+
+        return self.expression(exp.ModifyColumn(this=column_def))
+
     def _parse_partition_property(
         self,
     ) -> exp.Expr | None | list[exp.Expr]:
....................................................................................................................................................                                      [100%]
755 passed, 12024 subtests passed in 2.53s
[assistant] MySQL `MODIFY [COLUMN] col <definition> [FIRST | AFTER col]` now parses into its own node and round-trips. All four examples from your request pass as identity tests, and the full suite passes (1094 tests), with ruff clean.

What changed:

- **Parser** (`sqlglot/parsers/mysql.py`): `MODIFY` gets a dedicated `_parse_alter_table_modify`. It parses a full column definition plus an optional `FIRST`/`AFTER` position. If no column definition follows, it falls back to the old alter-column path, so `ALTER COLUMN ... SET DATA TYPE` still round-trips to `MODIFY COLUMN c LONGTEXT` as before.
- **Expressi
…[475 chars elided]…
rted warning, since those can't be expressed that way. Without this fallback, transpiling to other dialects would raise `Unsupported expression type ModifyColumn`.
- **Tests** (`tests/dialects/test_mysql.py`): identity tests for the four examples plus `AFTER d`.

Choices to confirm:
- The `MODIFY` keyword without `COLUMN` also parses and comes back with `COLUMN` added, which matches MySQL's own normalization.
- I added a new expression class rather than reusing `AlterColumn`, because no existing node carries a full column definition with constraints and position.

I haven't committed anything.
