# trajectory base-1

final message:
MySQL `ALTER TABLE ... MODIFY [COLUMN] <column definition> [FIRST | AFTER col]` now parses into its own node and round-trips. All four examples from your request pass, and the full test suite is green (1094 passed), along with ruff check and format.

**What changed**

- **`sqlglot/expressions/ddl.py`**: new `AlterModifyColumn(this=ColumnDef)` node, separate from `AlterColumn`.
- **`sqlglot/parsers/mysql.py`**: `MODIFY` now goes to `_parse_alter_table_modify`. It parses a full column definition and an optional position. If that fails, it falls back to the existing `ALTER [COLUMN]` parsing, so `MODIFY COLUMN c DROP DEFAULT`-style input is unchanged.
- **`sqlglot/parser.py`**: pulled the `FIRST | AFTER` parsing out of `_parse_add_column` into `_parse_column_position()`, which both `ADD` and `MODIFY` now use. `ADD` behaves as before.
- **`sqlglot/generators/mysql.py`**: `altermodifycolumn_sql` emits `MODIFY COLUMN <column def>`. Doris, StarRocks and SingleStore inherit it.
- **`tests/dialects/test_mysql.py`**: identity tests for the four examples, plus `AFTER d` and a `MODIFY c INT` → `MODIFY COLUMN c INT` normalization.

**Things to know**

- The existing test `ALTER COLUMN c SET DATA TYPE LONGTEXT` → `MODIFY COLUMN c LONGTEXT` still passes. I left that path unchanged and didn't edit that test.
- `validate_identity` also passes when a statement falls back to a raw `Command`, so I checked the AST directly. The four examples and `AFTER` all produce `AlterModifyColumn`.
- I haven't committed anything.

## events
[tool_use Bash] {"command": "grep -n \"MODIFY\\|ALTER_COLUMN\\|AlterColumn\\|_parse_alter_table_alter\\|_parse_alter_table_add\" sqlglot/dialects/mysql.py sqlglot/parser.py sqlglot/generator.py sqlglot/dialects/dialect.py | head -80; grep -rn \"MODIFY\" tests/dialects/test_mysql.py | head", "description": "Find MODIFY and ALTER handling in parser/generator"}
[tool_result] sqlglot/generator.py:3903:    def altercolumn_sql(self, expression: exp.AlterColumn) -> str:
sqlglot/generator.py:5929:        return f"MODIFY {props}"
sqlglot/parser.py:1435:        "ADD": lambda self: self._parse_alter_table_add(),
sqlglot/parser.py:1437:        "ALTER": lambda self: self._parse_alter_table_alter(),
sqlglot/parser.py:8537:    def _parse_alter_table_add(self) -> list[exp.Expr]:
sqlglot/parser.py:8576:    def _parse_alter_table_alter(self) -> exp.Expr | None:
sqlglot/parser.py:8
…[540 chars elided]…
))
sqlglot/parser.py:8597:            return self.expression(exp.AlterColumn(this=column, visible="VISIBLE"))
sqlglot/parser.py:8599:            return self.expression(exp.AlterColumn(this=column, visible="INVISIBLE"))
sqlglot/parser.py:8604:            exp.AlterColumn(
tests/dialects/test_mysql.py:40:        self.validate_identity("ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT")
tests/dialects/test_mysql.py:167:            "ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT",
[tool_use Bash] {"command": "sed -n 8530,8620p sqlglot/parser.py; sed -n 3895,3940p sqlglot/generator.py; sed -n 150,185p tests/dialects/test_mysql.py; grep -n \"class AlterColumn\" -A 20 sqlglot/expressions.py; grep -n \"class ColumnDef\" -A 12 sqlglot/expressions.py", "description": "Read ALTER parsing, generator, and tests"}
[tool_result ERROR] Exit code 2

    # https://docs.aws.amazon.com/athena/latest/ug/alter-table-drop-partition.html
    def _parse_drop_partition(self, exists: bool | None = None) -> exp.DropPartition:
        return self.expression(
            exp.DropPartition(expressions=self._parse_csv(self._parse_partition), exists=exists)
        )

    def _parse_alter_table_add(self) -> list[exp.Expr]:
        def _parse_add_alteration() -> exp.Expr | None:
            self._match_text_seq("ADD")
            if self._match
…[6700 chars elided]…
a (a DESC))",
        )
        self.validate_identity(
            "CREATE TABLE `foo` (a VARCHAR(10), UNIQUE INDEX idx_a (a))",
            "CREATE TABLE `foo` (a VARCHAR(10), UNIQUE idx_a (a))",
        )

        self.validate_all(
            "insert into t(i) values (default)",
            write={
                "duckdb": "INSERT INTO t (i) VALUES (DEFAULT)",
ugrep: warning: sqlglot/expressions.py: No such file or directory
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "grep -rn \"MODIFY\\|ALTER_SET_TYPE\\|ALTER_ALTER_PARSERS\" sqlglot/ | head -30; grep -rn \"class AlterColumn\\|class ColumnDef\" -A 14 sqlglot/expressions/ | head -50; sed -n 120,140p tests/dialects/test_mysql.py; sed -n 30,45p tests/dialects/test_mysql.py", "description": "Locate MODIFY, AlterColumn, ColumnDef definitions"}
[tool_result] sqlglot/generator.py:563:    ALTER_SET_TYPE = "SET DATA TYPE"
sqlglot/generator.py:3912:            alter_set_type = self.ALTER_SET_TYPE + " " if self.ALTER_SET_TYPE else ""
sqlglot/generator.py:5929:        return f"MODIFY {props}"
sqlglot/parser.py:1448:    ALTER_ALTER_PARSERS: t.ClassVar = {
sqlglot/parser.py:8577:        if self._match_texts(self.ALTER_ALTER_PARSERS):
sqlglot/parser.py:8578:            return self.ALTER_ALTER_PARSERS[self._prev.text.upper()](self)
sqlglot/parsers/clickhouse.
…[3909 chars elided]…
DROP COLUMN c, DROP PRIMARY KEY, DROP INDEX `i`")
        self.validate_identity("ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT")
        self.validate_identity("ALTER TABLE t AUTO_INCREMENT=3000000000")
        self.validate_identity("ALTER VIEW v AS SELECT a, b, c, d FROM foo")
        self.validate_identity("ALTER VIEW v AS SELECT * FROM foo WHERE c > 100")
        self.validate_identity(
            "ALTER ALGORITHM = MERGE VIEW v AS SELECT * FROM foo", check_command_warning=True
[tool_use Bash] {"command": "sed -n 245,275p sqlglot/parsers/mysql.py; sed -n 700,730p sqlglot/generators/mysql.py; sed -n 5915,5935p sqlglot/generator.py; grep -n \"_parse_column_def\\b\\|def _parse_column_def\\|position\" sqlglot/parser.py | head -30; grep -n \"ColumnPosition\\|class.*Position\" -A6 sqlglot/expressions/*.py | head -30; grep -rn \"FIRST\\|AFTER\" sqlglot/generators/mysql.py sqlglot/generator.py sqlglot/parsers/mysql.py | head", "description": "Inspect MySQL parser/generator and column position handling"}
[tool_result]         "FULLTEXT": lambda self: self._parse_index_constraint(kind="FULLTEXT"),
        "INDEX": lambda self: self._parse_index_constraint(),
        "KEY": lambda self: self._parse_index_constraint(),
        "SPATIAL": lambda self: self._parse_index_constraint(kind="SPATIAL"),
        "ZEROFILL": lambda self: self.expression(exp.ZeroFillColumnConstraint()),
        "INVISIBLE": lambda self: self.expression(exp.InvisibleColumnConstraint()),
    }

    ALTER_PARSERS = {
        **parser.Parser.A
…[6920 chars elided]…
IRST(x IGNORE NULLS ORDER BY y) vs FIRST(x ORDER BY y IGNORE NULLS)
sqlglot/generator.py:632:    AFTER_HAVING_MODIFIER_TRANSFORMS: t.ClassVar = {
sqlglot/generator.py:636:        **AFTER_HAVING_MODIFIER_TRANSFORMS,
sqlglot/generator.py:2020:        after = "AFTER " if expression.args.get("after") else ""
sqlglot/generator.py:2904:            nulls_sort_change = " NULLS FIRST"
sqlglot/generator.py:2912:        # If the NULLS FIRST/LAST clause is unsupported, we add another sort key to simulate it
[tool_use Bash] {"command": "sed -n 8486,8525p sqlglot/parser.py; grep -n \"def altertable_sql\" -A 60 sqlglot/generator.py | head -90; grep -n \"def columnposition_sql\\|def columndef_sql\" -A 14 sqlglot/generator.py; grep -n \"class AlterTable\\b\" -A 12 sqlglot/expressions/ddl.py; grep -n \"ALTER_TABLE_ADD_REQUIRED\\|ALTER_TABLE_ADD\" sqlglot/parsers/mysql.py sqlglot/dialect.py sqlglot/dialects/dialect.py sqlglot/generators/mysql.py 2>/dev/null", "description": "Read ADD column position, ALTER TABLE generator, ColumnDef generator"}
[tool_result ERROR] Exit code 2

        return self.expression(exp.Refresh(this=this, kind=kind))

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

    def _parse_add_c
…[1568 chars elided]…
 if kind else ""
1148-        constraints = f" {constraints}" if constraints else ""
1149-        position = self.sql(expression, "position")
1150-        position = f" {position}" if position else ""
1151-
1152-        if expression.find(exp.ComputedColumnConstraint) and not self.COMPUTED_COLUMN_WITH_TYPE:
1153-            kind = ""
1154-
1155-        return f"{exists}{column}{kind}{constraints}{position}"
1156-
sqlglot/dialects/dialect.py:699:    ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN = True
[tool_use Bash] {"command": "grep -n \"def altertable_sql\" -A 45 sqlglot/generator.py; grep -n \"class AlterTable\\b\" -A 12 sqlglot/expressions/ddl.py; grep -n \"def _parse_alter\\b\" -A 30 sqlglot/parser.py | head -50; ls tests/dialects | grep mysql", "description": "Read ALTER TABLE generator and parser entry"}
[tool_result] 8706:    def _parse_alter(self) -> exp.Alter | exp.Command:
8707-        start = self._prev
8708-
8709-        iceberg = self._match_text_seq("ICEBERG")
8710-
8711-        alter_token = self._match_set(self.ALTERABLES) and self._prev
8712-        if not alter_token:
8713-            return self._parse_as_command(start)
8714-        if iceberg and alter_token.token_type != TokenType.TABLE:
8715-            return self._parse_as_command(start)
8716-
8717-        exists = self._parse_exists()
8718-
…[372 chars elided]…
", "CHECK")
8727-            cluster = self._parse_on_property() if self._match(TokenType.ON) else None
8728-
8729-            if self._next:
8730-                self._advance()
8731-
8732-        parser = self.ALTER_PARSERS.get(self._prev.text.upper()) if self._prev else None
8733-        if parser:
8734-            actions = ensure_list(parser(self))
8735-            not_valid = self._match_text_seq("NOT", "VALID")
8736-            options = self._parse_csv(self._parse_property)
test_mysql.py
[tool_use Bash] {"command": "grep -rn \"def altertable_sql\" sqlglot/; grep -rn \"class Alter\\b\" -A 12 sqlglot/expressions/; sed -n 8736,8760p sqlglot/parser.py", "description": "Locate altertable generator and Alter expression"}
[tool_result] sqlglot/expressions/ddl.py:377:class Alter(Expression):
sqlglot/expressions/ddl.py-378-    arg_types = {
sqlglot/expressions/ddl.py-379-        "this": False,
sqlglot/expressions/ddl.py-380-        "kind": True,
sqlglot/expressions/ddl.py-381-        "actions": True,
sqlglot/expressions/ddl.py-382-        "exists": False,
sqlglot/expressions/ddl.py-383-        "only": False,
sqlglot/expressions/ddl.py-384-        "options": False,
sqlglot/expressions/ddl.py-385-        "cluster": False,
sqlglot/
…[675 chars elided]…
              only=only,
                        options=options,
                        cluster=cluster,
                        not_valid=not_valid,
                        check=check,
                        cascade=cascade,
                        iceberg=iceberg,
                    )
                )

        return self._parse_as_command(start)

    def _parse_analyze(self) -> exp.Analyze | exp.Command:
        start = self._prev
        # https://duckdb.org/docs/sql/statements/analyze
[tool_use Bash] {"command": "grep -rn \"def alter_sql\" -A 50 sqlglot/generator.py | head -70; grep -rn \"ColumnDef\" sqlglot/generator.py | head -20", "description": "Read Alter generator logic"}
[tool_result] sqlglot/generator.py:3983:    def alter_sql(self, expression: exp.Alter) -> str:
sqlglot/generator.py-3984-        actions = expression.args["actions"]
sqlglot/generator.py-3985-
sqlglot/generator.py-3986-        if not self.dialect.ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN and isinstance(
sqlglot/generator.py-3987-            actions[0], exp.ColumnDef
sqlglot/generator.py-3988-        ):
sqlglot/generator.py-3989-            actions_sql = self.expressions(expression, key="actions", flat=True)
sq
…[3128 chars elided]…
str = " ") -> str:
sqlglot/generator.py:3597:    def jsoncolumndef_sql(self, expression: exp.JSONColumnDef) -> str:
sqlglot/generator.py:3628:    def openjsoncolumndef_sql(self, expression: exp.OpenJSONColumnDef) -> str:
sqlglot/generator.py:3987:            actions[0], exp.ColumnDef
sqlglot/generator.py:3994:                if isinstance(action, (exp.ColumnDef, exp.Schema)):
sqlglot/generator.py:4038:        elif isinstance(expression, exp.ColumnDef) and self.ALTER_TABLE_INCLUDE_COLUMN_KEYWORD:
[tool_use Bash] {"command": "grep -rn \"class AlterModifySqlSecurity\\|class AlterColumn\\|class AlterDistStyle\" -B2 -A6 sqlglot/expressions/; grep -rn \"MODIFY\" tests/ | grep -v \"^tests/fixtures/identity\" | head -30; grep -rn \"ALTER_PARSERS\\b\" sqlglot/parsers/*.py | head; grep -n \"def _parse_field_def\" -A 8 sqlglot/parser.py", "description": "Check expression placement, existing MODIFY tests, field def"}
[tool_result] sqlglot/expressions/ddl.py-231-
sqlglot/expressions/ddl.py-232-
sqlglot/expressions/ddl.py:233:class AlterColumn(Expression):
sqlglot/expressions/ddl.py-234-    arg_types = {
sqlglot/expressions/ddl.py-235-        "this": True,
sqlglot/expressions/ddl.py-236-        "dtype": False,
sqlglot/expressions/ddl.py-237-        "collate": False,
sqlglot/expressions/ddl.py-238-        "using": False,
sqlglot/expressions/ddl.py-239-        "default": False,
--
sqlglot/expressions/ddl.py-250-
sqlglot/expre
…[2451 chars elided]…
{
sqlglot/parsers/mysql.py:260:        **parser.Parser.ALTER_ALTER_PARSERS,
7033:    def _parse_field_def(self) -> exp.Expr | None:
7034-        return self._parse_column_def(self._parse_field(any_token=True))
7035-
7036-    def _parse_column_def(
7037-        self, this: exp.Expr | None, computed_column: bool = True
7038-    ) -> exp.Expr | None:
7039-        # column defs are not really columns, they're identifiers
7040-        if isinstance(this, exp.Column):
7041-            this = this.this
[assistant] Current state: MySQL's `MODIFY` is routed to the generic `ALTER [COLUMN]` parser, so `MODIFY COLUMN c INT NOT NULL` fails to round-trip. I'll add a dedicated node for MODIFY and keep the existing `ALTER COLUMN ... SET DATA TYPE` → `MODIFY COLUMN` behavior intact, since an existing test depends on it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-143222-mysql-dialect-alter-table-modify/base-1/sqlglot/expressions/ddl.py", "old_string": "class AlterDistStyle(Expression):\n    pass", "new_string": "class AlterModifyColumn(Expression):\n    arg_types = {\"this\": True}\n\n\nclass AlterDistStyle(Expression):\n    pass"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-143222-mysql-dialect-alter-table-modify/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-143222-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py", "offset": 1, "limit": 30}
[tool_result] 1	from __future__ import annotations
2	
3	import typing as t
4	
5	from sqlglot import exp, parser
6	from sqlglot.trie import new_trie
7	from sqlglot.dialects.dialect import (
8	    Dialect,
9	    build_date_delta,
10	    build_date_delta_with_interval,
11	    build_formatted_time,
12	    isnull_to_is_null,
13	)
14	from sqlglot.helper import seq_get
15	from sqlglot.tokens import TokenType
16	
17	
18	# All specifiers for time parts (as opposed to date parts)
19	# https://dev.mysql.com/doc/refman/8.0/en/date-and-time-functions.html#function_date-format
20	TIME_SPECIFIERS = {"f", "H", "h", "I", "i", "k", "l", "p", "r", "S", "s", "T"}
21	
22	
23	def _has_time_specifier(date_format: str) -> bool:
24	    i = 0
25	    length = len(date_format)
26	
27	    while i < length:
28	        if date_format[i] == "%":
29	            i += 1
30	            if i < length and date_format[i] in TIME_SPECIFIERS:
[tool_use Bash] {"command": "grep -n \"_parse_alter_table_alter_index\\|def _parse_\" sqlglot/parsers/mysql.py | head -30", "description": "Find parser method definitions in MySQL parser"}
[tool_result] 261:        "INDEX": lambda self: self._parse_alter_table_alter_index(),
305:    def _parse_alter_table_rename(self):
313:    def _parse_alter_drop_action(self) -> exp.Expr | None:
318:    def _parse_generated_as_identity(
339:    def _parse_primary_key_part(self) -> exp.Expr | None:
348:    def _parse_index_constraint(self, kind: str | None = None) -> exp.IndexColumnConstraint:
395:    def _parse_show_mysql(
481:    def _parse_oldstyle_limit(
496:    def _parse_set_item_charset(self, kind: str) -> exp.Expr:
500:    def _parse_charset_name(self) -> exp.Expr | None:
514:    def _parse_set_item_names(self) -> exp.Expr:
523:    def _parse_type(
538:    def _parse_alter_table_alter_index(self) -> exp.AlterIndex:
550:    def _parse_partition_property(
580:    def _parse_partition_range_value(self) -> exp.Expr | None:
599:    def _parse_partition_list_value(self) -> exp.Partition:
607:    def _parse_primary_key(
[tool_use Bash] {"command": "sed -n 536,550p sqlglot/parsers/mysql.py", "description": "Read ALTER INDEX parser method for placement"}
[tool_result]         )

    def _parse_alter_table_alter_index(self) -> exp.AlterIndex:
        index = self._parse_field(any_token=True)

        if self._match_text_seq("VISIBLE"):
            visible = True
        elif self._match_text_seq("INVISIBLE"):
            visible = False
        else:
            visible = None

        return self.expression(exp.AlterIndex(this=index, visible=visible))

    def _parse_partition_property(
[assistant] Now the parser: a shared column-position helper in the base parser, used by ADD and by the new MySQL MODIFY path.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-143222-mysql-dialect-alter-table-modify/base-1/sqlglot/parser.py", "old_string": "        expression = self._parse_column_def_with_exists()\n        if not expression:\n            return None\n\n        # https://docs.databricks.com/delta/update-schema.html#explicitly-update-schema-to-add-columns\n 
…[549 chars elided]…
dd-columns\n        expression.set(\"position\", self._parse_column_position())\n\n        return expression\n\n    def _parse_column_position(self) -> exp.ColumnPosition | None:\n        if not self._match_texts((\"FIRST\", \"AFTER\")):\n            return None\n\n        position = self._prev.text\n        return self.expression(exp.ColumnPosition(this=self._parse_column(), position=position))"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-143222-mysql-dialect-alter-table-modify/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-143222-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py", "old_string": "        \"MODIFY\": lambda self: self._parse_alter_table_alter(),", "new_string": "        \"MODIFY\": lambda self: self._parse_alter_table_modify(),"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-143222-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-143222-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py", "old_string": "    def _parse_alter_table_alter_index(self) -> exp.AlterIndex:", "new_string": "    def _parse_alter_table_modify(self) -> exp.Expr | None:\n        # MODIFY [COLUMN] redefines the whole column, unlike ALTER [COLUMN] which only changes an attribute\n        column_def = self._parse_column_def_with_exists()\n        if not column_def:\n            return self._parse_alter_table_alter()\n\n        column_def.set(\"position\", self._parse_column_position())\n        return self.expression(exp.AlterModifyColumn(this=column_def))\n\n    def _parse_alter_table_alter_index(self) -> exp.AlterIndex:"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-143222-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[assistant] Now the MySQL generator, placed next to `altercolumn_sql`, plus tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-143222-mysql-dialect-alter-table-modify/base-1/sqlglot/generators/mysql.py", "old_string": "        this = self.sql(expression, \"this\")\n        return f\"MODIFY COLUMN {this} {dtype}\"\n", "new_string": "        this = self.sql(expression, \"this\")\n        return f\"MODIFY COLUMN {this} {dtype}\"\n\n    def altermodifycolumn_sql(self, expression: exp.AlterModifyColumn) -> str:\n        return f\"MODIFY COLUMN {self.sql(expression, 'this')}\"\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-143222-mysql-dialect-alter-table-modify/base-1/sqlglot/generators/mysql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-143222-mysql-dialect-alter-table-modify/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT\")\n", "new_string": "        self.validate_identity(\"ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT\")\n
…[137 chars elided]…
MODIFY COLUMN c VARCHAR(50) NOT NULL DEFAULT 'foo'\")\n        self.validate_identity(\"ALTER TABLE t MODIFY COLUMN c INT COMMENT 'hi'\")\n        self.validate_identity(\"ALTER TABLE t MODIFY COLUMN c INT FIRST\")\n        self.validate_identity(\"ALTER TABLE t MODIFY COLUMN c INT AFTER d\")\n        self.validate_identity(\"ALTER TABLE t MODIFY c INT\", \"ALTER TABLE t MODIFY COLUMN c INT\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-143222-mysql-dialect-alter-table-modify/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py tests/dialects/test_singlestore.py tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/test_parser.py tests/test_transpile.py 2>&1 | tail -30", "description": "Run MySQL-family and parser tests"}
[tool_result] .............................. [ 15%]
............................................................................................................................................ [ 88%]
......................                                                                [100%]
192 passed, 1905 subtests passed in 11.29s
[assistant] Those pass, but `validate_identity` would also pass if the statement fell back to a raw `Command`. I'll confirm the AST node type directly, then run the full suite.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t MODIFY COLUMN c INT NOT NULL DEFAULT 5','ALTER TABLE t MODIFY COLUMN c INT FIRST','ALTER TABLE t MODIFY COLUMN c INT AFTER d','ALTER TABLE t MODIFY COLUMN c VARCHAR(50) NOT NULL DEFAULT \
…[259 chars elided]…
, e.sql('mysql'))\nprint(sqlglot.transpile('ALTER TABLE t MODIFY COLUMN c INT FIRST', read='mysql', write='mysql'))\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify AST node types and run full test suite"}
[tool_result] AlterModifyColumn | ALTER TABLE t MODIFY COLUMN c INT NOT NULL DEFAULT 5
AlterModifyColumn | ALTER TABLE t MODIFY COLUMN c INT FIRST
AlterModifyColumn | ALTER TABLE t MODIFY COLUMN c INT AFTER d
AlterModifyColumn | ALTER TABLE t MODIFY COLUMN c VARCHAR(50) NOT NULL DEFAULT 'foo'
AlterModifyColumn | ALTER TABLE t MODIFY COLUMN c INT COMMENT 'hi'
AlterColumn | ALTER TABLE t ALTER COLUMN c SET DEFAULT 1
AlterColumn | ALTER TABLE t MODIFY COLUMN c LONGTEXT
['ALTER TABLE t MODIFY COLUMN c INT FIRST']
…[785 chars elided]…
................................................................. [ 71%]
............................................. [ 75%]
............................................. [ 79%]
............................... [ 82%]
............................................................................................................................................................................................                                           [100%]
1094 passed, 17872 subtests passed in 55.94s
[assistant] Full suite passes (1094). Quick lint on the changed files:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; ($PY/ruff --version >/dev/null 2>&1 && $PY/ruff check sqlglot/parser.py sqlglot/parsers/mysql.py sqlglot/generators/mysql.py sqlglot/expressions/ddl.py tests/dialects/test_mysql.py && $PY/ruff format --check sqlglot tests/dialects/test_mysql.py) 2>&1 | tail -8; git status --short; git diff --stat", "description": "Lint changed files and show diff stat"}
[tool_result] All checks passed!
175 files already formatted
 M sqlglot/expressions/ddl.py
 M sqlglot/generators/mysql.py
 M sqlglot/parser.py
 M sqlglot/parsers/mysql.py
 M tests/dialects/test_mysql.py
 sqlglot/expressions/ddl.py   |  4 ++++
 sqlglot/generators/mysql.py  |  3 +++
 sqlglot/parser.py            | 14 ++++++++------
 sqlglot/parsers/mysql.py     | 11 ++++++++++-
 tests/dialects/test_mysql.py |  6 ++++++
 5 files changed, 31 insertions(+), 7 deletions(-)
[assistant] MySQL `ALTER TABLE ... MODIFY [COLUMN] <column definition> [FIRST | AFTER col]` now parses into its own node and round-trips. All four examples from your request pass, and the full test suite is green (1094 passed), along with ruff check and format.

**What changed**

- **`sqlglot/expressions/ddl.py`**: new `AlterModifyColumn(this=ColumnDef)` node, separate from `AlterColumn`.
- **`sqlglot/parsers/mysql.py`**: `MODIFY` now goes to `_parse_alter_table_modify`. It parses a full column definition and an optional position. If that fails, it falls back to the existing `ALTER [COLUMN]` parsing, so `
…[320 chars elided]…
UMN <column def>`. Doris, StarRocks and SingleStore inherit it.
- **`tests/dialects/test_mysql.py`**: identity tests for the four examples, plus `AFTER d` and a `MODIFY c INT` → `MODIFY COLUMN c INT` normalization.

**Things to know**

- The existing test `ALTER COLUMN c SET DATA TYPE LONGTEXT` → `MODIFY COLUMN c LONGTEXT` still passes. I left that path unchanged and didn't edit that test.
- `validate_identity` also passes when a statement falls back to a raw `Command`, so I checked the AST directly. The four examples and `AFTER` all produce `AlterModifyColumn`.
- I haven't committed anything.
