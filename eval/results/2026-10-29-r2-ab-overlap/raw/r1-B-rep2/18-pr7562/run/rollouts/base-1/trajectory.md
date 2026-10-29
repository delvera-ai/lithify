# trajectory base-1

final message:
`ALTER TABLE ... MODIFY [COLUMN] col column_definition [FIRST | AFTER col]` now parses into its own node and round-trips in the MySQL dialect. All four statements from your request come back exactly as written, and the full suite passes (1094 tests), along with ruff format and lint.

**What changed**
- `sqlglot/expressions/ddl.py`: new `ModifyColumn` expression holding a single `ColumnDef`.
- `sqlglot/parsers/mysql.py`: `MODIFY` now dispatches to a new `_parse_alter_table_modify`, which parses an optional `COLUMN`, a full column definition, and an optional `FIRST`/`AFTER col`. The position is stored on the `ColumnDef` the same way `ADD COLUMN ... FIRST/AFTER` already does.
- `sqlglot/generators/mysql.py`: `modifycolumn_sql` emits `MODIFY COLUMN <column definition>`.
- `tests/dialects/test_mysql.py`: identity tests for the four statements, plus `AFTER`, and a normalization check that `MODIFY c INT AFTER d` becomes `MODIFY COLUMN c INT AFTER d`.

**Choices I made**
- I left the existing `ALTER COLUMN ... SET DATA TYPE` → `MODIFY COLUMN ... LONGTEXT` path alone, because an existing test depends on it. It still produces `AlterColumn`.
- `MODIFY` in Oracle is untouched, since the change is only in the MySQL parser.
- A comma-separated list that mixes `MODIFY` with other actions still falls back to `Command`, as before. Supporting that would be a separate change.

I haven't committed anything. The working tree has the four files above modified.

## events
[tool_use Bash] {"command": "git status --short && grep -n -i \"MODIFY\\|ALTER_COLUMN\\|_parse_alter_table_alter\\|def _parse_alter\" sqlglot/dialects/mysql.py sqlglot/parser.py sqlglot/generator.py | head -80", "description": "Check status and find MODIFY/alter parsing code"}
[tool_result] oksqlglot/parser.py:1437:        "ALTER": lambda self: self._parse_alter_table_alter(),
sqlglot/parser.py:8528:    def _parse_alter_drop_action(self) -> exp.Expr | None:
sqlglot/parser.py:8537:    def _parse_alter_table_add(self) -> list[exp.Expr]:
sqlglot/parser.py:8576:    def _parse_alter_table_alter(self) -> exp.Expr | None:
sqlglot/parser.py:8612:    def _parse_alter_diststyle(self) -> exp.AlterDistStyle:
sqlglot/parser.py:8619:    def _parse_alter_sortkey(self, compound: bool | None = None
…[119 chars elided]…
y:8643:    def _parse_alter_table_rename(self) -> exp.AlterRename | exp.RenameColumn | None:
sqlglot/parser.py:8658:    def _parse_alter_table_set(self) -> exp.AlterSet:
sqlglot/parser.py:8694:    def _parse_alter_session(self) -> exp.AlterSession:
sqlglot/parser.py:8706:    def _parse_alter(self) -> exp.Alter | exp.Command:
sqlglot/generator.py:5927:    def altermodifysqlsecurity_sql(self, expression: exp.AlterModifySqlSecurity) -> str:
sqlglot/generator.py:5929:        return f"MODIFY {props}"
[tool_use Bash] {"command": "sed -n 8520,8720p sqlglot/parser.py && grep -n \"class AlterColumn\\|class AlterModify\\|class Alter(\" -A22 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null | head -120", "description": "Read ALTER parsing code and expression classes"}
[tool_result]         return expression

    def _parse_drop_column(self) -> exp.Drop | exp.Command | None:
        drop = self._parse_drop() if self._match(TokenType.DROP) else None
        if drop and not isinstance(drop, exp.Command):
            drop.set("kind", drop.args.get("kind", "COLUMN"))
        return drop

    def _parse_alter_drop_action(self) -> exp.Expr | None:
        return self._parse_drop_column()

    # https://docs.aws.amazon.com/athena/latest/ug/alter-table-drop-partition.html
    def _
…[11601 chars elided]…

sqlglot/expressions/ddl.py-391-
sqlglot/expressions/ddl.py-392-    @property
sqlglot/expressions/ddl.py-393-    def kind(self) -> str | None:
sqlglot/expressions/ddl.py-394-        kind = self.args.get("kind")
sqlglot/expressions/ddl.py-395-        return kind and kind.upper()
sqlglot/expressions/ddl.py-396-
sqlglot/expressions/ddl.py-397-    @property
sqlglot/expressions/ddl.py-398-    def actions(self) -> list[Expr]:
sqlglot/expressions/ddl.py-399-        return self.args.get("actions") or []
[assistant] Now the MySQL dialect's ALTER handling and how the current output looks for these inputs.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; grep -n \"ALTER\\|MODIFY\\|ADD_COLUMN\\|AlterColumn\" sqlglot/dialects/mysql.py | head -40; $PY -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t MODIFY COLUMN c INT NOT NULL DEFAULT 5','ALTER TABLE t MODIFY COLUMN c VARCHAR(50) NOT NULL DEFAULT \\'foo\\'','ALTER TABLE t MODIFY COLUMN c INT COMMENT \\'hi\\'','ALTER TABLE t MODIFY COLUMN c INT FIRST','ALTER TABLE t MODIFY c INT AFTER d']:\n    e=sqlglot.parse_one(s,read='mysql'); print(repr(e.args.get('actions'))[:400]); print(e.sql('mysql'))\n\"; grep -rn \"MODIFY\" tests/dialects/test_mysql.py | head", "description": "Inspect current MySQL MODIFY parse output"}
[tool_result] 0 matches for 'ALTER\|MODIFY\|ADD_COLUMN\|AlterColumn'
'ALTER TABLE t MODIFY COLUMN c INT NOT NULL DEFAULT 5' contains unsupported syntax. Falling back to parsing as a 'Command'.
'ALTER TABLE t MODIFY COLUMN c VARCHAR(50) NOT NULL DEFAULT 'foo'' contains unsupported syntax. Falling back to parsing as a 'Command'.
'ALTER TABLE t MODIFY COLUMN c INT FIRST' contains unsupported syntax. Falling back to parsing as a 'Command'.
'ALTER TABLE t MODIFY c INT AFTER d' contains unsupported syntax. Falling 
…[158 chars elided]…
'
[AlterColumn(
  this=Identifier(this=c, quoted=False),
  dtype=DataType(this=DType.INT, nested=False),
  collate=False,
  using=False)]
ALTER TABLE t MODIFY COLUMN c INT, COMMENT='hi'
None
ALTER TABLE t MODIFY COLUMN c INT FIRST
None
ALTER TABLE t MODIFY c INT AFTER d
tests/dialects/test_mysql.py:40:        self.validate_identity("ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT")
tests/dialects/test_mysql.py:167:            "ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT",
[assistant] The current parse is lossy: `MODIFY COLUMN c INT COMMENT 'hi'` loses the comment and turns into `INT, COMMENT='hi'`, and `FIRST`/`AFTER` fall back to a Command. Next I'll check how the existing ADD COLUMN handles position and how the MySQL parser hooks into ALTER.
[tool_use Bash] {"command": "grep -n \"ALTER_ALTER_PARSERS\\|ALTER_PARSERS\\|FIRST\\|\\\"AFTER\\\"\\|ALTER_TABLE_ADD_REQUIRED\" sqlglot/parser.py sqlglot/dialects/*.py | head -40; grep -n \"class Parser\" -A3 sqlglot/dialects/mysql.py | head; grep -n \"def _parse_column_def\\|def _parse_add_column\\|def _parse_column_def_with_exists\" -A25 sqlglot/parser.py | head -120", "description": "Locate ALTER parser hooks and column position handling"}
[tool_result] 37 matches in 10 files:

sqlglot/dialects/bigquery.py:27:LOG_BASE_FIRST = False
sqlglot/dialects/clickhouse.py:21:LOG_BASE_FIRST: bool | None = None
sqlglot/dialects/dialect.py:377:LOG_BASE_FIRST: bool | None = True
sqlglot/dialects/dialect.py:699:ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN = True
sqlglot/dialects/oracle.py:21:ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN = False
sqlglot/dialects/presto.py:24:LOG_BASE_FIRST: bool | None = None
sqlglot/dialects/snowflake.py:27:ALTER_TABLE_ADD_REQUIRED_FO
…[4299 chars elided]…
sion.set("position", column_position)
8519-
8520-        return expression
8521-
8522-    def _parse_drop_column(self) -> exp.Drop | exp.Command | None:
8523-        drop = self._parse_drop() if self._match(TokenType.DROP) else None
8524-        if drop and not isinstance(drop, exp.Command):
8525-            drop.set("kind", drop.args.get("kind", "COLUMN"))
8526-        return drop
8527-
8528-    def _parse_alter_drop_action(self) -> exp.Expr | None:
8529-        return self._parse_drop_column()
[tool_use Bash] {"command": "sed -n 1430,1460p sqlglot/parser.py; grep -n \"ColumnPosition\\|columnposition\\|\\\"position\\\"\" sqlglot/generator.py sqlglot/dialects/mysql.py sqlglot/dialects/dialect.py; grep -n \"def columndef_sql\\|def altercolumn_sql\" -A30 sqlglot/generator.py | head -90; grep -n \"class Parser\\|class Generator\\|ALTER\\|def \" sqlglot/dialects/mysql.py | head -80", "description": "Inspect ALTER parser table and ColumnDef/AlterColumn generators"}
[tool_result]             this, expression = expression, this

        return self.expression(klass(this=this, expression=expression))

    ALTER_PARSERS: t.ClassVar = {
        "ADD": lambda self: self._parse_alter_table_add(),
        "AS": lambda self: self._parse_select(),
        "ALTER": lambda self: self._parse_alter_table_alter(),
        "CLUSTER BY": lambda self: self._parse_cluster(wrapped=True),
        "DELETE": lambda self: self.expression(exp.Delete(where=self._parse_where())),
        "DROP": 
…[4093 chars elided]…
MENT {comment}"
3922-
3923-        visible = expression.args.get("visible")
3924-        if visible:
3925-            return f"ALTER COLUMN {this} SET {visible}"
3926-
3927-        allow_null = expression.args.get("allow_null")
3928-        drop = expression.args.get("drop")
3929-
3930-        if not drop and not allow_null:
3931-            self.unsupported("Unsupported ALTER COLUMN syntax")
3932-
3933-        if allow_null is not None:
0 matches for 'class Parser\|class Generator\|ALTER\|def '
[tool_use Bash] {"command": "sed -n 8720,8790p sqlglot/parser.py; grep -n \"def alter_sql\" -A45 sqlglot/generator.py; sed -n 1130,1141p sqlglot/generator.py; grep -n \"^class\\|ALTER\\|Parser\\|Generator\" sqlglot/dialects/mysql.py | head -60", "description": "Read _parse_alter dispatch and alter_sql generator"}
[tool_result]         if alter_token.token_type == TokenType.SESSION:
            this = None
            check = None
            cluster = None
        else:
            this = self._parse_table(schema=True, parse_partition=self.ALTER_TABLE_PARTITIONS)
            check = self._match_text_seq("WITH", "CHECK")
            cluster = self._parse_on_property() if self._match(TokenType.ON) else None

            if self._next:
                self._advance()

        parser = self.ALTER_PARSERS.get(self._prev.te
…[4898 chars elided]…
ession: exp.ColumnPosition) -> str:
        this = self.sql(expression, "this")
        this = f" {this}" if this else ""
        position = self.sql(expression, "position")
        return f"{position}{this}"

5 matches in 2 files:

14:0:
sqlglot/dialects/mysql.py:8:from sqlglot.generators.mysql import MySQLGenerator
sqlglot/dialects/mysql.py:9:from sqlglot.parsers.mysql import MySQLParser
sqlglot/dialects/mysql.py:156:Parser = MySQLParser
sqlglot/dialects/mysql.py:158:Generator = MySQLGenerator
[assistant] The MySQL parser and generator live in `sqlglot/parsers/mysql.py` and `sqlglot/generators/mysql.py`. Let me look at those, plus `add_column_sql`.
[tool_use Bash] {"command": "grep -n \"class \\|ALTER\\|_PARSERS\\|def \" sqlglot/parsers/mysql.py | head -80; echo ---; grep -n \"ALTER\\|def add_column_sql\\|def altercolumn\" -A6 sqlglot/generators/mysql.py | head -40; echo ---; grep -n \"def add_column_sql\" -A12 sqlglot/generator.py; grep -n \"class Alter\\|class ColumnDef\" -A3 sqlglot/expressions/ddl.py sqlglot/expressions/*.py | head -20", "description": "Inspect MySQL parser/generator ALTER hooks"}
[tool_result] 40 matches in 16 files:

23:0:str) -> bool:
305:0:
313:0:
339:0:
348:0:str | None = None) -> exp.IndexColumnConstraint:
36:0:list) -> exp.StrToDate | exp.StrToTime:
47:0:t.Any, **kwargs: t.Any) -> t.Callable[[MySQLParser], exp.Show]:
48:0:MySQLParser) -> exp.Show:
496:0:str) -> exp.Expr:
500:0:
514:0:
538:0:
54:0:
580:0:
599:0:
sqlglot/parsers/mysql.py:89:RANGE_PARSERS = {
sqlglot/parsers/mysql.py:90:**parser.Parser.RANGE_PARSERS,
sqlglot/parsers/mysql.py:154:FUNCTION_PARSERS = {
sqlglot/parsers
…[2926 chars elided]…
glot/expressions/ddl.py-253-    pass
sqlglot/expressions/ddl.py-254-
sqlglot/expressions/ddl.py-255-
sqlglot/expressions/ddl.py:256:class AlterSortKey(Expression):
sqlglot/expressions/ddl.py-257-    arg_types = {"this": False, "expressions": False, "compound": False}
sqlglot/expressions/ddl.py-258-
sqlglot/expressions/ddl.py-259-
sqlglot/expressions/ddl.py:260:class AlterSet(Expression):
sqlglot/expressions/ddl.py-261-    arg_types = {
sqlglot/expressions/ddl.py-262-        "expressions": False,
[assistant] The MySQL generator already emits `MODIFY COLUMN` for an `AlterColumn` with a dtype, which is why the current output looks plausible but drops everything after the type. My plan is a dedicated `ModifyColumn` expression wrapping a `ColumnDef`, so `FIRST`/`AFTER` reuses the existing `ColumnDef.position`. Let me check the remaining pieces before editing.
[tool_use Bash] {"command": "sed -n 250,265p sqlglot/parsers/mysql.py; grep -n \"def _parse_field_def\" -A8 sqlglot/parser.py; grep -n \"__all__\" sqlglot/expressions/ddl.py sqlglot/expressions/__init__.py | head; grep -n \"^from\\|^import\" sqlglot/parsers/mysql.py; grep -n \"^from\\|^import\\|^class\" sqlglot/generators/mysql.py | head; grep -n \"MODIFY\" -B3 -A3 tests/dialects/test_mysql.py tests/dialects/test_postgres.py tests/dialects/test_doris.py tests/dialects/test_starrocks.py 2>/dev/null | head -60", "description": "Check imports, field-def parser, and existing MODIFY tests"}
[tool_result]         "INVISIBLE": lambda self: self.expression(exp.InvisibleColumnConstraint()),
    }

    ALTER_PARSERS = {
        **parser.Parser.ALTER_PARSERS,
        "MODIFY": lambda self: self._parse_alter_table_alter(),
        "AUTO_INCREMENT": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),
    }

    ALTER_ALTER_PARSERS = {
        **parser.Parser.ALTER_ALTER_PARSERS,
        "INDEX": lambda self: self._parse_alter_table_alter_index(),
    }

    SCHEMA_UNNAMED_CONSTRAINT
…[2278 chars elided]…
sts/dialects/test_mysql.py-166-            "ALTER TABLE test_table ALTER COLUMN test_column SET DATA TYPE LONGTEXT",
tests/dialects/test_mysql.py:167:            "ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT",
tests/dialects/test_mysql.py-168-        )
tests/dialects/test_mysql.py-169-        self.validate_identity(
tests/dialects/test_mysql.py-170-            "CREATE TABLE t (c DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP) DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC",
[assistant] MySQL's `ALTER_PARSERS` already maps `MODIFY` to the generic alter-column parser, and there's an existing test (`SET DATA TYPE` → `MODIFY COLUMN ... LONGTEXT`) that depends on the `AlterColumn` generator path, so I'll leave that path alone. Making the edits now.
[tool_use Bash] {"command": "grep -rn \"ModifyColumn\\|class ModifyColumn\" sqlglot/ | head -3; sed -n 228,247p sqlglot/expressions/ddl.py", "description": "Check for name clashes and view AlterColumn definition"}
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-143700-mysql-dialect-alter-table-modify/base-1/sqlglot/expressions/ddl.py", "old_string": "        \"visible\": False,\n        \"rename_to\": False,\n    }\n\n\nclass AlterIndex(Expression):", "new_string": "        \"visible\": False,\n        \"rename_to\": False,\n    }\n\n\nclass ModifyColumn(Expression):\n    arg_types = {\"this\": True}\n\n\nclass AlterIndex(Expression):"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-143700-mysql-dialect-alter-table-modify/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-143700-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py", "old_string": "        \"MODIFY\": lambda self: self._parse_alter_table_alter(),", "new_string": "        \"MODIFY\": lambda self: self._parse_alter_table_modify(),"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-143700-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[assistant] Now the parser method. Let me check how `MySQLParser` is structured, since the file appears to be mostly module-level helpers.
[tool_use Bash] {"command": "grep -n \"MySQLParser\\|^class\" sqlglot/parsers/mysql.py | head; grep -n \"    def \" sqlglot/parsers/mysql.py | head -5; sed -n 1,30p sqlglot/parsers/mysql.py | tail -20", "description": "Locate MySQLParser class definition and its method style"}
[tool_result] 3 matches in 3 files:

47:0:t.Any, **kwargs: t.Any) -> t.Callable[[MySQLParser], exp.Show]:
48:0:MySQLParser) -> exp.Show:
54:0:
17 matches in 12 files:

305:0:
313:0:
339:0:
    build_formatted_time,
    isnull_to_is_null,
)
from sqlglot.helper import seq_get
from sqlglot.tokens import TokenType


# All specifiers for time parts (as opposed to date parts)
# https://dev.mysql.com/doc/refman/8.0/en/date-and-time-functions.html#function_date-format
TIME_SPECIFIERS = {"f", "H", "h", "I", "i", "k", "l", "p", "r", "S", "s", "T"}


def _has_time_specifier(date_format: str) -> bool:
    i = 0
    length = len(date_format)

    while i < length:
        if date_format[i] == "%":
            i += 1
            if i < length and date_format[i] in TIME_SPECIFIERS:
[tool_use Bash] {"command": "wc -l sqlglot/parsers/mysql.py && grep -n \"Parser\" sqlglot/parsers/mysql.py | head; sed -n 596,640p sqlglot/parsers/mysql.py", "description": "Find where MySQLParser class body lives"}
[tool_result] 615
22 matches in 4 files:

47:0:t.Any, **kwargs: t.Any) -> t.Callable[[MySQLParser], exp.Show]:
48:0:MySQLParser) -> exp.Show:
54:0:
sqlglot/parsers/mysql.py:56:**parser.Parser.NO_PAREN_FUNCTIONS,
sqlglot/parsers/mysql.py:61:ID_VAR_TOKENS = parser.Parser.ID_VAR_TOKENS - {TokenType.STRAIGHT_JOIN}
sqlglot/parsers/mysql.py:64:*parser.Parser.FUNC_TOKENS,
sqlglot/parsers/mysql.py:73:**parser.Parser.CONJUNCTION,
sqlglot/parsers/mysql.py:79:**parser.Parser.DISJUNCTION,
        part_range = self.expres
…[389 chars elided]…
_list = self.expression(exp.PartitionList(this=name, expressions=values))
        return self.expression(exp.Partition(expressions=[part_list]))

    def _parse_primary_key(
        self,
        wrapped_optional: bool = False,
        in_props: bool = False,
        named_primary_key: bool = False,
    ) -> exp.PrimaryKeyColumnConstraint | exp.PrimaryKey:
        return super()._parse_primary_key(
            wrapped_optional=wrapped_optional, in_props=in_props, named_primary_key=True
        )
[assistant] Methods sit at the end of the `MySQLParser` class body, so I'll append the new one after `_parse_primary_key`.
[tool_use Bash] {"command": "tail -c 200 sqlglot/parsers/mysql.py | od -c | tail -3", "description": "Check file ending for appending method"}
[tool_result] 0000260    m   a   r   y   _   k   e   y   =   T   r   u   e  \n        
0000300                            )  \n                                
0000310
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-143700-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py", "old_string": "        return super()._parse_primary_key(\n            wrapped_optional=wrapped_optional, in_props=in_props, named_primary_key=True\n        )", "new_string": "        return super()._parse_primary_key(\n       
…[282 chars elided]…
._parse_field_def()\n\n        if isinstance(column, exp.ColumnDef) and self._match_texts((\"FIRST\", \"AFTER\")):\n            position = self._prev.text.upper()\n            column.set(\n                \"position\",\n                self.expression(exp.ColumnPosition(this=self._parse_column(), position=position)),\n            )\n\n        return self.expression(exp.ModifyColumn(this=column))"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-143700-mysql-dialect-alter-table-modify/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-143700-mysql-dialect-alter-table-modify/base-1/sqlglot/generators/mysql.py", "old_string": "    def altercolumn_sql(self, expression: exp.AlterColumn) -> str:\n        dtype = self.sql(expression, \"dtype\")\n        if not dtype:\n            return super().altercolumn_sql(expression)\n\n        thi
…[135 chars elided]…
ression: exp.AlterColumn) -> str:\n        dtype = self.sql(expression, \"dtype\")\n        if not dtype:\n            return super().altercolumn_sql(expression)\n\n        this = self.sql(expression, \"this\")\n        return f\"MODIFY COLUMN {this} {dtype}\"\n\n    def modifycolumn_sql(self, expression: exp.ModifyColumn) -> str:\n        return f\"MODIFY COLUMN {self.sql(expression, 'this')}\""}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-143700-mysql-dialect-alter-table-modify/base-1/sqlglot/generators/mysql.py has been updated successfully.
[assistant] Now let me verify the four required round-trips plus a few adjacent cases (no `COLUMN` keyword, `AFTER`, multiple actions).
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ncases=['ALTER TABLE t MODIFY COLUMN c INT NOT NULL DEFAULT 5','ALTER TABLE t MODIFY COLUMN c VARCHAR(50) NOT NULL DEFAULT \\'foo\\'','ALTER TABLE t MODIFY COLUMN c INT COMMENT \\'hi\\'','ALTER TABLE t MODIFY COLUMN c INT FIRST','ALTER TABLE t MODIFY c INT AFTER d','ALTER TABLE t MODIFY \\`c\\` INT NOT NULL AFTER \\`d\\`','ALTER TABLE t MODIFY c INT FIRST, ADD COLUMN e INT']\nfor s in cases:\n    e=sqlglot.parse_one(s,read='mysql'); out=e.sql('mysql'); print('OK ' if out==s else 'DIFF', out, '|', type(e.args['actions'][0]).__name__)\n\"", "description": "Round-trip MODIFY COLUMN cases through MySQL dialect"}
[tool_result ERROR] Exit code 1
'ALTER TABLE t MODIFY c INT FIRST, ADD COLUMN e INT' contains unsupported syntax. Falling back to parsing as a 'Command'.
Traceback (most recent call last):
  File "<string>", line 5, in <module>
KeyError: 'actions'
OK  ALTER TABLE t MODIFY COLUMN c INT NOT NULL DEFAULT 5 | ModifyColumn
OK  ALTER TABLE t MODIFY COLUMN c VARCHAR(50) NOT NULL DEFAULT 'foo' | ModifyColumn
OK  ALTER TABLE t MODIFY COLUMN c INT COMMENT 'hi' | ModifyColumn
OK  ALTER TABLE t MODIFY COLUMN c INT FIRST | ModifyColumn
DIFF ALTER TABLE t MODIFY COLUMN c INT AFTER d | ModifyColumn
DIFF ALTER TABLE t MODIFY COLUMN `c` INT NOT NULL AFTER `d` | ModifyColumn
[assistant] The four required statements round-trip exactly. The two "DIFF" lines are intended: the input omitted the optional `COLUMN` keyword, which the generator normalizes. The multi-action case falls back to `Command`, which matches how the parser already handles multi-action MODIFY, so it isn't a regression from this change. Now I'll add tests next to the existing MODIFY identity test.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-143700-mysql-dialect-alter-table-modify/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT\")\n", "new_string": "        self.validate_identity(\"ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT\")\n
…[153 chars elided]…
VARCHAR(50) NOT NULL DEFAULT 'foo'\")\n        self.validate_identity(\"ALTER TABLE t MODIFY COLUMN c INT COMMENT 'hi'\")\n        self.validate_identity(\"ALTER TABLE t MODIFY COLUMN c INT FIRST\")\n        self.validate_identity(\"ALTER TABLE t MODIFY COLUMN c INT AFTER d\")\n        self.validate_identity(\"ALTER TABLE t MODIFY c INT AFTER d\", \"ALTER TABLE t MODIFY COLUMN c INT AFTER d\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-143700-mysql-dialect-alter-table-modify/base-1/tests/dialects/test_mysql.py has been updated successfully.
[assistant] Running the MySQL tests first, then the full suite using the project's check command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py tests/dialects/test_doris.py tests/dialects/test_starrocks.py 2>&1 | tail -15", "description": "Run MySQL-family dialect tests"}
[tool_result] .............................. [ 40%]
.......................................... [ 97%]
..                                                    [100%]
74 passed, 595 subtests passed in 0.37s
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite"}
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
1094 passed, 17872 subtests passed in 53.47s
[assistant] All 1094 tests pass. Now the style check, since one of my test lines is probably over the line-length limit.
[tool_use Bash] {"command": "R=<work>/env-sqlglot/bin; ($R/ruff --version || which ruff) 2>&1 | head -2; $R/ruff format --check sqlglot/expressions/ddl.py sqlglot/parsers/mysql.py sqlglot/generators/mysql.py tests/dialects/test_mysql.py 2>&1 | tail -5; $R/ruff check sqlglot/expressions/ddl.py sqlglot/parsers/mysql.py sqlglot/generators/mysql.py tests/dialects/test_mysql.py 2>&1 | tail -3", "description": "Run ruff format and lint checks on changed files"}
[tool_result] ruff 0.15.6
Would reformat: tests/dialects/test_mysql.py
1 file would be reformatted, 3 files already formatted
All checks passed!
[tool_use Bash] {"command": "R=<work>/env-sqlglot/bin; $R/ruff format tests/dialects/test_mysql.py && git diff --stat && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -1", "description": "Apply ruff format and rerun MySQL tests"}
[tool_result] 1 file reformatted
sqlglot/expressions/ddl.py   |  4 ++++
 sqlglot/generators/mysql.py  |  3 +++
 sqlglot/parsers/mysql.py     | 16 +++++++++++++++-
 tests/dialects/test_mysql.py |  8 ++++++++
 4 files changed, 30 insertions(+), 1 deletion(-)
50 passed, 481 subtests passed in 0.17s
[This command modified 1 file you've previously read: tests/dialects/test_mysql.py. Call Read before editing.]
[assistant] `ALTER TABLE ... MODIFY [COLUMN] col column_definition [FIRST | AFTER col]` now parses into its own node and round-trips in the MySQL dialect. All four statements from your request come back exactly as written, and the full suite passes (1094 tests), along with ruff format and lint.

**What changed**
- `sqlglot/expressions/ddl.py`: new `ModifyColumn` expression holding a single `ColumnDef`.
- `sqlglot/parsers/mysql.py`: `MODIFY` now dispatches to a new `_parse_alter_table_modify`, which parses an optional `COLUMN`, a full column definition, and an optional `FIRST`/`AFTER col`. The position is 
…[262 chars elided]…
`, and a normalization check that `MODIFY c INT AFTER d` becomes `MODIFY COLUMN c INT AFTER d`.

**Choices I made**
- I left the existing `ALTER COLUMN ... SET DATA TYPE` → `MODIFY COLUMN ... LONGTEXT` path alone, because an existing test depends on it. It still produces `AlterColumn`.
- `MODIFY` in Oracle is untouched, since the change is only in the MySQL parser.
- A comma-separated list that mixes `MODIFY` with other actions still falls back to `Command`, as before. Supporting that would be a separate change.

I haven't committed anything. The working tree has the four files above modified.
