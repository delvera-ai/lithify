# trajectory base-1

final message:
MySQL `ALTER TABLE ... MODIFY [COLUMN] col definition [FIRST | AFTER col]` now parses into its own node and round-trips. The full test suite passes (1094 tests), and ruff check and format are clean.

All four forms from your request round-trip exactly. `MODIFY COLUMN c INT COMMENT 'hi'` previously came out wrong: the COMMENT was moved into table options. The FIRST and COMMENT forms used to fall back to a raw `Command`. Without the `COLUMN` keyword, `MODIFY c INT NOT NULL` is normalized to `MODIFY COLUMN c INT NOT NULL`.

What changed:
- **`sqlglot/expressions/ddl.py`**: new `AlterModifyColumn` expression wrapping a `ColumnDef`, so it is not mistaken for an `ADD`.
- **`sqlglot/parsers/mysql.py`**: `MODIFY` now routes to a new `_parse_alter_table_modify_column`, which parses an optional `COLUMN`, a full column definition, and an optional position.
- **`sqlglot/parser.py`**: the FIRST/AFTER parsing from `ADD COLUMN` moved into `_parse_column_position()`, which both paths now share.
- **`sqlglot/generators/mysql.py`**: `altermodifycolumn_sql` emits `MODIFY COLUMN <column def>`.
- **`tests/dialects/test_mysql.py`**: added round-trip identities for the four forms, plus `AFTER` and the no-`COLUMN` form. I did not touch any existing test.

Existing `ALTER COLUMN ... SET DATA TYPE` and `ALTER COLUMN ... SET DEFAULT` still parse as before. Because `SingleStore` inherits the MySQL `ALTER` parsers, it picks up the same `MODIFY` change, and the test suite still passes.

One limitation: a trailing option after a MODIFY, such as `ALTER TABLE t MODIFY COLUMN c INT, ALGORITHM=INPLACE`, still falls back to `Command`. It round-trips verbatim, but the structure isn't parsed. `ADD` only handles this by accident, so I left it alone rather than widen the change.

## events
[tool_use Bash] {"command": "grep -n \"MODIFY\\|ALTER_COLUMN\\|AlterColumn\\|_parse_alter_table_alter\\|_parse_alter_table_add\" sqlglot/dialects/mysql.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -80", "description": "Find MODIFY/alter-column handling in source"}
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
[tool_use Bash] {"command": "sed -n 8530,8630p sqlglot/parser.py && echo ---- && sed -n 3895,3935p sqlglot/generator.py && echo ---- && grep -n \"class AlterColumn\" -A 20 sqlglot/expressions/*.py | head -40; grep -rn \"class AlterColumn\" sqlglot | head", "description": "Read ALTER TABLE parsing and generation code"}
[tool_result]     # https://docs.aws.amazon.com/athena/latest/ug/alter-table-drop-partition.html
    def _parse_drop_partition(self, exists: bool | None = None) -> exp.DropPartition:
        return self.expression(
            exp.DropPartition(expressions=self._parse_csv(self._parse_partition), exists=exists)
        )

    def _parse_alter_table_add(self) -> list[exp.Expr]:
        def _parse_add_alteration() -> exp.Expr | None:
            self._match_text_seq("ADD")
            if self._match_set(self.ADD
…[6221 chars elided]…
-        "rename_to": False,
sqlglot/expressions/ddl.py-245-    }
sqlglot/expressions/ddl.py-246-
sqlglot/expressions/ddl.py-247-
sqlglot/expressions/ddl.py-248-class AlterIndex(Expression):
sqlglot/expressions/ddl.py-249-    arg_types = {"this": True, "visible": True}
sqlglot/expressions/ddl.py-250-
sqlglot/expressions/ddl.py-251-
sqlglot/expressions/ddl.py-252-class AlterDistStyle(Expression):
sqlglot/expressions/ddl.py-253-    pass
sqlglot/expressions/ddl.py:233:class AlterColumn(Expression):
[tool_use Bash] {"command": "grep -n \"ALTER\\|MODIFY\\|ColumnDef\\|_parse_alter\\|AFTER\\|FIRST\" sqlglot/dialects/mysql.py | head -60; echo ----; grep -n \"def _parse_alter_table_add\" -B2 -A40 sqlglot/parser.py | head -5; grep -n \"AFTER\\|\\\"FIRST\\\"\" sqlglot/parser.py sqlglot/generator.py | head -30", "description": "Inspect MySQL dialect and related position handling"}
[tool_result] ----
8535-        )
8536-
8537:    def _parse_alter_table_add(self) -> list[exp.Expr]:
8538-        def _parse_add_alteration() -> exp.Expr | None:
8539-            self._match_text_seq("ADD")
sqlglot/parser.py:1588:        "AFTER": tuple(),
sqlglot/parser.py:2719:            "after": self._match_text_seq("AFTER"),
sqlglot/parser.py:3910:        self._match_text_seq("FIRST", "BY")
sqlglot/parser.py:4220:        if self._match_text_seq("AFTER", "MATCH", "SKIP"):
sqlglot/parser.py:4221:           
…[444 chars elided]…
R_TRANSFORMS: t.ClassVar = {
sqlglot/generator.py:636:        **AFTER_HAVING_MODIFIER_TRANSFORMS,
sqlglot/generator.py:2020:        after = "AFTER " if expression.args.get("after") else ""
sqlglot/generator.py:3014:            limit = exp.Fetch(direction="FIRST", count=exp.maybe_copy(limit.expression))
sqlglot/generator.py:3026:            *[gen(self, expression) for gen in self.AFTER_HAVING_MODIFIER_TRANSFORMS.values()],
sqlglot/generator.py:3246:            first = "FIRST" if first else "LAST"
[tool_use Bash] {"command": "sed -n 8495,8530p sqlglot/parser.py; echo ----; grep -n \"ALTER_TABLE_ADD_REQUIRED\\|_parse_column_def_with_exists\\|def _parse_add_column\" sqlglot/parser.py sqlglot/dialects/mysql.py | head; echo ----; grep -n \"def alter_sql\\|def altertable_sql\\|def _parse_alter_table_alter\\|ALTER_TABLE_ADD\" -A3 sqlglot/generator.py | head -60; echo ----; sed -n 1425,1445p sqlglot/parser.py; ec
…[28 chars elided]…
thify-dev/r2-noise-scratch/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t MODIFY COLUMN c INT NOT NULL DEFAULT 5','ALTER TABLE t MODIFY COLUMN c INT FIRST','ALTER TABLE t MODIFY COLUMN c INT COMMENT \\'hi\\'']:\n    e=sqlglot.parse_one(s,read='mysql'); print(repr(e)); print(e.sql('mysql'))\n\"", "description": "Inspect add-column position parsing and current MODIFY output"}
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
…[3270 chars elided]…
 COLUMN c INT FIRST
Alter(
  this=Table(
    this=Identifier(this=t, quoted=False)),
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
    SchemaCommentProperty(
      this=Literal(this='hi', is_string=True))],
  not_valid=False,
  check=False,
  cascade=False,
  iceberg=False)
ALTER TABLE t MODIFY COLUMN c INT, COMMENT='hi'
[tool_use Bash] {"command": "sed -n 3983,4010p sqlglot/generator.py; echo ----; grep -n \"def columnposition_sql\\|def columndef_sql\" -A22 sqlglot/generator.py; echo ----; grep -n \"class ColumnPosition\\|class ColumnDef\" -A6 sqlglot/expressions/*.py; echo ----; grep -n \"ALTER\\|class Parser\" sqlglot/dialects/mysql.py | head -30; echo ----; grep -n \"def _parse_alter\\b\" -A30 sqlglot/parser.py | head -50; echo ----; grep -n \"ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN\" -r sqlglot | head", "description": "Read alter/column position generation and MySQL parser config"}
[tool_result]     def alter_sql(self, expression: exp.Alter) -> str:
        actions = expression.args["actions"]

        if not self.dialect.ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN and isinstance(
            actions[0], exp.ColumnDef
        ):
            actions_sql = self.expressions(expression, key="actions", flat=True)
            actions_sql = f"ADD {actions_sql}"
        else:
            actions_list = []
            for action in actions:
                if isinstance(action, (exp.ColumnDef, exp.
…[4210 chars elided]…
t self.dialect.ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN
sqlglot/generator.py:3986:        if not self.dialect.ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN and isinstance(
sqlglot/dialects/dialect.py:699:    ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN = True
sqlglot/dialects/tsql.py:20:    ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN = False
sqlglot/dialects/snowflake.py:27:    ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN = False
sqlglot/dialects/oracle.py:21:    ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN = False
[tool_use Bash] {"command": "grep -rn \"Modify\\|MODIFY\" sqlglot/ | head -20; echo ----; grep -n \"class Parser\\|class Generator\\|class Tokenizer\\|ALTER_PARSERS\\|_parse_column_def\\|TRANSFORMS = {\" sqlglot/dialects/mysql.py; echo ----; grep -n \"def add_column_sql\" -A8 sqlglot/generator.py; echo ----; grep -n \"ALTER_PARSERS\" -r sqlglot | head; echo ----; grep -n \"\\\"MODIFY\\\"\\|'MODIFY'\" -r tests | head; echo ----; grep -n \"ALTER\" tests/dialects/test_mysql.py | head -30", "description": "Check naming, parser hooks, and existing MySQL ALTER tests"}
[tool_result] sqlglot/generator.py:5927:    def altermodifysqlsecurity_sql(self, expression: exp.AlterModifySqlSecurity) -> str:
sqlglot/generator.py:5929:        return f"MODIFY {props}"
sqlglot/parsers/snowflake.py:742:        "MODIFY": lambda self: self._parse_alter_table_alter(),
sqlglot/parsers/clickhouse.py:445:        "MODIFY": lambda self: self._parse_alter_table_modify(),
sqlglot/parsers/clickhouse.py:832:            return self.expression(exp.AlterModifySqlSecurity(expressions=properties.expressions
…[3054 chars elided]…
validate_identity("ALTER TABLE t ALTER COLUMN c SET VISIBLE")
216:        self.validate_identity("ALTER TABLE t RENAME INDEX a TO b")
218:            "ALTER TABLE t RENAME KEY a TO b",
219:            "ALTER TABLE t RENAME INDEX a TO b",
258:        self.validate_identity("ALTER TABLE test_table ALTER COLUMN test_column SET DEFAULT 1")
1744:        expr = self.parse_one("ALTER TABLE t ADD COLUMN c INT INVISIBLE")
1748:        prop = self.parse_one("ALTER TABLE t AUTO_INCREMENT=3000000000").find(
[tool_use Bash] {"command": "sed -n 245,262p sqlglot/parsers/mysql.py; echo ----; sed -n 700,725p sqlglot/generators/mysql.py; echo ----; sed -n 155,175p tests/dialects/test_mysql.py; echo ----; sed -n 1,30p sqlglot/parsers/clickhouse.py | head -5; grep -n \"def _parse_alter_table_modify\" -A25 sqlglot/parsers/clickhouse.py; echo ----; grep -n \"class AlterColumn\\|AlterColumn\" sqlglot/parsers/*.py sqlglot/generators/*.py | head -20; echo ----; git log --oneline -3 -- sqlglot/generators/mysql.py", "description": "Inspect existing MySQL MODIFY handling and tests"}
[tool_result]         "FULLTEXT": lambda self: self._parse_index_constraint(kind="FULLTEXT"),
        "INDEX": lambda self: self._parse_index_constraint(),
        "KEY": lambda self: self._parse_index_constraint(),
        "SPATIAL": lambda self: self._parse_index_constraint(kind="SPATIAL"),
        "ZEROFILL": lambda self: self.expression(exp.ZeroFillColumnConstraint()),
        "INVISIBLE": lambda self: self.expression(exp.InvisibleColumnConstraint()),
    }

    ALTER_PARSERS = {
        **parser.Parser.A
…[4538 chars elided]…
:476:    def altercolumn_sql(self, expression: exp.AlterColumn) -> str:
sqlglot/generators/singlestore.py:1581:    def altercolumn_sql(self, expression: exp.AlterColumn) -> str:
sqlglot/generators/spark2.py:235:    def altercolumn_sql(self, expression: exp.AlterColumn) -> str:
----
08b51e81e Refactor: use ruff UP rule to modernize coding style (#7459)
3582aa542 refactor(generators): Cleanup and fully compile all generators (#7389)
1b14a7971 refactor(mysql)!: Extract and compile generator (#7381)
[tool_use Bash] {"command": "grep -n \"def _parse_column_def\\b\" -A12 sqlglot/parser.py | head -30; echo ----; grep -n \"    def _parse_\\|^class\\|^    class\" sqlglot/parsers/mysql.py | head -60; echo ----; grep -rn \"MODIFY\" tests/ | grep -v \"ALTER TABLE t MODIFY\\b\" | head -30; echo ----; grep -n \"^class\\|MySQL\" sqlglot/dialects/doris.py sqlglot/dialects/starrocks.py sqlglot/dialects/singlestore.py | head", "description": "Inspect column-def helper and MySQL parser layout, test references"}
[tool_result] 7036:    def _parse_column_def(
7037-        self, this: exp.Expr | None, computed_column: bool = True
7038-    ) -> exp.Expr | None:
7039-        # column defs are not really columns, they're identifiers
7040-        if isinstance(this, exp.Column):
7041-            this = this.this
7042-
7043-        if not computed_column:
7044-            self._match(TokenType.ALIAS)
7045-
7046-        kind = self._parse_types(schema=True)
7047-
7048-        if self._match_text_seq("FOR", "ORDINALITY"):
----
…[2085 chars elided]…
dialects/starrocks.py:15:            **MySQL.Tokenizer.KEYWORDS,
sqlglot/dialects/doris.py:3:from sqlglot.dialects.mysql import MySQL
sqlglot/dialects/doris.py:8:class Doris(MySQL):
sqlglot/dialects/singlestore.py:2:from sqlglot.dialects.mysql import MySQL
sqlglot/dialects/singlestore.py:7:class SingleStore(MySQL):
sqlglot/dialects/singlestore.py:10:    MYSQL_INVERSE_TIME_MAPPING = MySQL.INVERSE_TIME_MAPPING
sqlglot/dialects/singlestore.py:11:    MYSQL_INVERSE_TIME_TRIE = MySQL.INVERSE_TIME_TRIE
[tool_use Bash] {"command": "sed -n 280,292p sqlglot/expressions/ddl.py; echo ----; sed -n 300,318p sqlglot/parsers/mysql.py; echo ----; sed -n 1,30p sqlglot/parsers/mysql.py | grep -n import", "description": "View ddl expression and MySQL parser helper placement"}
[tool_result] class RenameIndex(Expression):
    arg_types = {"this": True, "to": True}


class AlterModifySqlSecurity(Expression):
    arg_types = {"expressions": True}


class SwapTable(Expression):
    pass

----
    LOG_DEFAULTS_TO_LN = True
    STRING_ALIASES = True
    VALUES_FOLLOWED_BY_PAREN = False
    SUPPORTS_PARTITION_SELECTION = True

    def _parse_alter_table_rename(self):
        if self._match_texts(("INDEX", "KEY")):
            old = self._parse_field(any_token=True)
            self._match
…[214 chars elided]…
p_action(self) -> exp.Expr | None:
        if self._match_pair(TokenType.DROP, TokenType.PRIMARY_KEY):
            return self.expression(exp.DropPrimaryKey())
        return super()._parse_alter_drop_action()

    def _parse_generated_as_identity(
----
1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, parser
6:from sqlglot.trie import new_trie
7:from sqlglot.dialects.dialect import (
14:from sqlglot.helper import seq_get
15:from sqlglot.tokens import TokenType
[assistant] Current behavior: `MODIFY` is routed to the ALTER COLUMN parser, so `MODIFY COLUMN c INT COMMENT 'hi'` is mis-parsed (the COMMENT lands in table options) and the other three forms fall back to `Command`. I'll add a dedicated expression, a MySQL parser entry, and a MySQL generator, and share the FIRST/AFTER parsing with ADD.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-173448-mysql-dialect-alter-table-modify/base-1/sqlglot/expressions/ddl.py", "old_string": "class AlterModifySqlSecurity(Expression):\n    arg_types = {\"expressions\": True}\n", "new_string": "class AlterModifySqlSecurity(Expression):\n    arg_types = {\"expressions\": True}\n\n\nclass AlterModifyColumn(Expression):\n    arg_types = {\"this\": True}\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-173448-mysql-dialect-alter-table-modify/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-173448-mysql-dialect-alter-table-modify/base-1/sqlglot/parser.py", "old_string": "        expression = self._parse_column_def_with_exists()\n        if not expression:\n            return None\n\n        # https://docs.databricks.com/delta/update-schema.html#explicitly-update-schema-to-add-columns\n 
…[599 chars elided]…
rse_column_position():\n            expression.set(\"position\", column_position)\n\n        return expression\n\n    def _parse_column_position(self) -> exp.ColumnPosition | None:\n        if self._match_texts((\"FIRST\", \"AFTER\")):\n            position = self._prev.text\n            return self.expression(exp.ColumnPosition(this=self._parse_column(), position=position))\n        return None"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-173448-mysql-dialect-alter-table-modify/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-173448-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py", "old_string": "        \"MODIFY\": lambda self: self._parse_alter_table_alter(),", "new_string": "        \"MODIFY\": lambda self: self._parse_alter_table_modify_column(),"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-173448-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-173448-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py", "old_string": "    def _parse_alter_drop_action(self) -> exp.Expr | None:\n        if self._match_pair(TokenType.DROP, TokenType.PRIMARY_KEY):", "new_string": "    def _parse_alter_table_modify_column(self) -> exp.AlterModifyCo
…[50 chars elided]…
    column_def = self._parse_column_def(self._parse_field(any_token=True))\n        if column_position := self._parse_column_position():\n            column_def.set(\"position\", column_position)\n        return self.expression(exp.AlterModifyColumn(this=column_def))\n\n    def _parse_alter_drop_action(self) -> exp.Expr | None:\n        if self._match_pair(TokenType.DROP, TokenType.PRIMARY_KEY):"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-173448-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-173448-mysql-dialect-alter-table-modify/base-1/sqlglot/generators/mysql.py", "old_string": "    def altercolumn_sql(self, expression: exp.AlterColumn) -> str:\n        dtype = self.sql(expression, \"dtype\")", "new_string": "    def altermodifycolumn_sql(self, expression: exp.AlterModifyColumn) -> str:\n        return f\"MODIFY COLUMN {self.sql(expression, 'this')}\"\n\n    def altercolumn_sql(self, expression: exp.AlterColumn) -> str:\n        dtype = self.sql(expression, \"dtype\")"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-173448-mysql-dialect-alter-table-modify/base-1/sqlglot/generators/mysql.py has been updated successfully.
[assistant] Now I'll check the round-trips from the request, plus a few edge cases.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ncases=['ALTER TABLE t MODIFY COLUMN c INT NOT NULL DEFAULT 5',\n\\\"ALTER TABLE t MODIFY COLUMN c VARCHAR(50) NOT NULL DEFAULT 'foo'\\\",\n\\\"ALTER TABLE t MODIFY COLUMN c INT COMMENT 'hi'\\\",\n'ALTER TABLE t MODIFY COLUMN c INT FIRST',\n'ALTER TABLE t MODIFY COLUMN c INT AFTER d',\n'ALT
…[134 chars elided]…
T, ADD COLUMN e INT',\n'ALTER TABLE t ADD COLUMN c INT FIRST',\n'ALTER TABLE t ADD COLUMN c INT AFTER d',\n]\nfor s in cases:\n    e=sqlglot.parse_one(s,read='mysql')\n    out=e.sql('mysql')\n    print(type(e.args['actions'][0]).__name__ if e.args.get('actions') else type(e).__name__, '|', out, '| OK' if out==s else '| DIFF')\n\"", "description": "Round-trip MODIFY COLUMN examples and edge cases"}
[tool_result] 'ALTER TABLE t MODIFY COLUMN c INT NOT NULL, ALGORITHM=INPLACE' contains unsupported syntax. Falling back to parsing as a 'Command'.
'ALTER TABLE t MODIFY c INT FIRST, ADD COLUMN e INT' contains unsupported syntax. Falling back to parsing as a 'Command'.
AlterModifyColumn | ALTER TABLE t MODIFY COLUMN c INT NOT NULL DEFAULT 5 | OK
AlterModifyColumn | ALTER TABLE t MODIFY COLUMN c VARCHAR(50) NOT NULL DEFAULT 'foo' | OK
AlterModifyColumn | ALTER TABLE t MODIFY COLUMN c INT COMMENT 'hi' | OK
AlterModifyColumn | ALTER TABLE t MODIFY COLUMN c INT FIRST | OK
AlterModifyColumn | ALTER TABLE t MODIFY COLUMN c INT AFTER d | OK
AlterModifyColumn | ALTER TABLE t MODIFY COLUMN c INT NOT NULL | DIFF
Command | ALTER TABLE t MODIFY COLUMN c INT NOT NULL, ALGORITHM=INPLACE | OK
Command | ALTER TABLE t MODIFY c INT FIRST, ADD COLUMN e INT | OK
ColumnDef | ALTER TABLE t ADD COLUMN c INT FIRST | OK
ColumnDef | ALTER TABLE t ADD COLUMN c INT AFTER d | OK
[assistant] The four spec examples round-trip. The `DIFF` line is only the optional `COLUMN` keyword being normalized, which is expected. Two comma-separated cases fell back to `Command`, so I'll check whether `ADD` handles the same trailing options.
[tool_use Bash] {"command": "sed -n 8745,8775p sqlglot/parser.py; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t1 ADD COLUMN x INT, ALGORITHM=INPLACE','ALTER TABLE t1 ADD COLUMN x INT NOT NULL, ALGORITHM=INPLACE','ALTER TABLE t1 MODIFY COLUMN x INT, ALGORITHM=INPLACE']:\n    e=sqlglot.parse_one(s,read='mysql'); print(type(e).__name__, e.sql('mysql'))\n\"", "description": "Compare ADD vs MODIFY with trailing ALGORITHM option"}
[tool_result]                         kind=alter_token.text.upper(),
                        exists=exists,
                        actions=actions,
                        only=only,
                        options=options,
                        cluster=cluster,
                        not_valid=not_valid,
                        check=check,
                        cascade=cascade,
                        iceberg=iceberg,
                    )
                )

        return self._parse_as_command(start
…[411 chars elided]…
MIT {self._parse_number()}")
            else:
                options.append(self._prev.text.upper())

        this: exp.Expr | None = None
        inner_expression: exp.Expr | None = None

'ALTER TABLE t1 MODIFY COLUMN x INT, ALGORITHM=INPLACE' contains unsupported syntax. Falling back to parsing as a 'Command'.
Alter ALTER TABLE t1 ADD COLUMN x INT, ALGORITHM=INPLACE
Alter ALTER TABLE t1 ADD COLUMN x INT NOT NULL, ALGORITHM=INPLACE
Command ALTER TABLE t1 MODIFY COLUMN x INT, ALGORITHM=INPLACE
[tool_use Bash] {"command": "sed -n 8736,8746p sqlglot/parser.py; grep -n \"def _parse_csv\" -A30 sqlglot/parser.py | head -40", "description": "Read alter option parsing and csv helper"}
[tool_result]             actions = ensure_list(parser(self))
            not_valid = self._match_text_seq("NOT", "VALID")
            options = self._parse_csv(self._parse_property)
            cascade = self.dialect.ALTER_TABLE_SUPPORTS_CASCADE and self._match_text_seq("CASCADE")

            if not self._curr and actions:
                return self.expression(
                    exp.Alter(
                        this=this,
                        kind=alter_token.text.upper(),
                        ex
…[827 chars elided]…
400-        parse_method: t.Callable[[], T | None],
8401-        sep: TokenType = TokenType.COMMA,
8402-        optional: bool = False,
8403-    ) -> list[T]:
8404-        return self._parse_wrapped(
8405-            lambda: self._parse_csv(parse_method, sep=sep), optional=optional
8406-        )
8407-
8408-    def _parse_wrapped(self, parse_method: t.Callable[[], T], optional: bool = False) -> T:
8409-        wrapped = self._match(TokenType.L_PAREN)
8410-        if not wrapped and not optional:
[assistant] The `ADD` path only accepts a trailing `, ALGORITHM=...` by accident: its column-list parser consumes the comma. The `MODIFY` form can't reach that code. These inputs still round-trip verbatim through `Command`, so I'll leave that case as a documented limitation rather than widen the change. Next I'll add tests next to the existing MySQL ALTER identities and run the suite.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-173448-mysql-dialect-alter-table-modify/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT\")\n", "new_string": "        self.validate_identity(\"ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT\")\n
…[193 chars elided]…
       self.validate_identity(\"ALTER TABLE t MODIFY COLUMN c INT COMMENT 'hi'\")\n        self.validate_identity(\"ALTER TABLE t MODIFY COLUMN c INT FIRST\")\n        self.validate_identity(\"ALTER TABLE t MODIFY COLUMN c INT AFTER d\")\n        self.validate_identity(\n            \"ALTER TABLE t MODIFY c INT NOT NULL\",\n            \"ALTER TABLE t MODIFY COLUMN c INT NOT NULL\",\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-173448-mysql-dialect-alter-table-modify/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run full project test suite"}
[tool_result] ................................................................................. [  7%]
............................................................................................................................................ [ 20%]
............................................................ [ 25%]
...................................... [ 29%]
.............................................................................................. [ 37%]
...............................................
…[284 chars elided]…
................................................................. [ 71%]
............................................. [ 75%]
............................................. [ 79%]
............................... [ 82%]
............................................................................................................................................................................................                                           [100%]
1094 passed, 17872 subtests passed in 50.60s
[assistant] The full suite passes (1094 tests). I'll also run the linter and formatter on the changed files.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/parser.py sqlglot/parsers/mysql.py sqlglot/generators/mysql.py sqlglot/expressions/ddl.py tests/dialects/test_mysql.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parser.py sqlglot/parsers/mysql.py sqlglot/generators/mysql.py sqlglot/expressions/ddl.py tests/dialects/test_mysql.py) 2>&1 | tail -8; git -C . diff --stat", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
5 files already formatted
 sqlglot/expressions/ddl.py   |  4 ++++
 sqlglot/generators/mysql.py  |  3 +++
 sqlglot/parser.py            | 12 +++++++-----
 sqlglot/parsers/mysql.py     |  9 ++++++++-
 tests/dialects/test_mysql.py |  9 +++++++++
 5 files changed, 31 insertions(+), 6 deletions(-)
[assistant] MySQL `ALTER TABLE ... MODIFY [COLUMN] col definition [FIRST | AFTER col]` now parses into its own node and round-trips. The full test suite passes (1094 tests), and ruff check and format are clean.

All four forms from your request round-trip exactly. `MODIFY COLUMN c INT COMMENT 'hi'` previously came out wrong: the COMMENT was moved into table options. The FIRST and COMMENT forms used to fall back to a raw `Command`. Without the `COLUMN` keyword, `MODIFY c INT NOT NULL` is normalized to `MODIFY COLUMN c INT NOT NULL`.

What changed:
- **`sqlglot/expressions/ddl.py`**: new `AlterModifyColumn`
…[569 chars elided]…
 forms, plus `AFTER` and the no-`COLUMN` form. I did not touch any existing test.

Existing `ALTER COLUMN ... SET DATA TYPE` and `ALTER COLUMN ... SET DEFAULT` still parse as before. Because `SingleStore` inherits the MySQL `ALTER` parsers, it picks up the same `MODIFY` change, and the test suite still passes.

One limitation: a trailing option after a MODIFY, such as `ALTER TABLE t MODIFY COLUMN c INT, ALGORITHM=INPLACE`, still falls back to `Command`. It round-trips verbatim, but the structure isn't parsed. `ADD` only handles this by accident, so I left it alone rather than widen the change.
