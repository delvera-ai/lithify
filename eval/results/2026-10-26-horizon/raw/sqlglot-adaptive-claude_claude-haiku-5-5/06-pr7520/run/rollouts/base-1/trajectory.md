# trajectory base-1

final message:
`ALTER TABLE t AUTO_INCREMENT=3000000000` now parses as an `AutoIncrementProperty` action and round-trips unchanged. The full suite passes (1086 passed) and ruff format and lint are clean.

The change is two edits:

- **`sqlglot/parsers/mysql.py`**: added `"AUTO_INCREMENT"` to the MySQL `ALTER_PARSERS`. It uses the same `_parse_property_assignment(exp.AutoIncrementProperty)` call as the CREATE TABLE property, so the two share one node type. I put it in the MySQL parser rather than the base parser so other dialects don't start accepting it. SingleStore inherits it through `MySQLParser.ALTER_PARSERS`.
- **`tests/dialects/test_mysql.py`**: added `validate_identity("ALTER TABLE t AUTO_INCREMENT=3000000000")` beside the other ALTER identity checks.

Before the change, the statement fell back to a generic `Command`. I haven't committed anything. Say if you want a commit, and I'll add the model attribution the repo asks for.

## events
[tool_use Bash] {"command": "grep -rn -i \"autoincrement\\|auto_increment\" sqlglot/ | head -60", "description": "Find AUTO_INCREMENT handling in sqlglot source"}
[tool_result] sqlglot/parser.py:660:        TokenType.AUTO_INCREMENT,
sqlglot/parser.py:1217:        "AUTO_INCREMENT": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),
sqlglot/parser.py:1327:        "AUTOINCREMENT": lambda self: self._parse_auto_increment(),
sqlglot/parser.py:1328:        "AUTO_INCREMENT": lambda self: self._parse_auto_increment(),
sqlglot/parser.py:1362:        "IDENTITY": lambda self: self._parse_auto_increment(),
sqlglot/parser.py:7081:    def _parse_auto_increment(
…[2583 chars elided]…
lot/generators/materialize.py:20:        exp.AutoIncrementColumnConstraint: lambda self, e: "",
sqlglot/generators/snowflake.py:653:        TokenType.AUTO_INCREMENT: "AUTOINCREMENT",
sqlglot/generators/snowflake.py:902:        return f"AUTOINCREMENT{start}{increment}{order_clause}"
sqlglot/generators/duckdb.py:4050:    def autoincrementcolumnconstraint_sql(self, _) -> str:
sqlglot/generators/duckdb.py:4051:        self.unsupported("The AUTOINCREMENT column constraint is not supported by DuckDB")
[tool_use Bash] {"command": "sed -n 1200,1230p sqlglot/parser.py && echo ---- && grep -n \"AlterTable\\|_parse_alter_table_set\\|def _parse_alter\\b\" sqlglot/parser.py | head -40 && echo ---- && grep -n \"class AlterTable\\|class AutoIncrementProperty\" -A6 sqlglot/expressions/*.py && echo ---- && grep -n -i \"alter\" sqlglot/dialects/mysql.py | head -40", "description": "Inspect parser property and ALTER TABLE code"}
[tool_result]         "LIMIT": lambda self, query: self._parse_pipe_syntax_limit(query),
        "ORDER BY": lambda self, query: query.order_by(
            self._parse_order(), append=False, copy=False
        ),
        "PIVOT": lambda self, query: self._parse_pipe_syntax_pivot(query),
        "SELECT": lambda self, query: self._parse_pipe_syntax_select(query),
        "TABLESAMPLE": lambda self, query: self._parse_pipe_syntax_tablesample(query),
        "UNPIVOT": lambda self, query: self._parse_pipe_synta
…[1427 chars elided]…
ble_set(self) -> exp.AlterSet:
8667:    def _parse_alter(self) -> exp.Alter | exp.Command:
----
sqlglot/expressions/properties.py:40:class AutoIncrementProperty(Property):
sqlglot/expressions/properties.py-41-    arg_types = {"this": True}
sqlglot/expressions/properties.py-42-
sqlglot/expressions/properties.py-43-
sqlglot/expressions/properties.py-44-class AutoRefreshProperty(Property):
sqlglot/expressions/properties.py-45-    arg_types = {"this": True}
sqlglot/expressions/properties.py-46-
----
[tool_use Bash] {"command": "sed -n 8600,8760p sqlglot/parser.py && echo ---- && sed -n 1415,1440p sqlglot/parser.py && echo ---- && grep -n \"ALTER_PARSERS\\|ALTER_TABLE_ADD_REQUIRED\\|def _parse_alter_table_alter\\|def _parse_property_assignment\" sqlglot/parser.py sqlglot/dialects/mysql.py", "description": "Read ALTER parsing code and ALTER_PARSERS"}
[tool_result]         self._retreat(index)
        return self._parse_csv(self._parse_drop_column)

    def _parse_alter_table_rename(self) -> exp.AlterRename | exp.RenameColumn | None:
        if self._match(TokenType.COLUMN) or not self.ALTER_RENAME_REQUIRES_COLUMN:
            exists = self._parse_exists()
            old_column = self._parse_column()
            to = self._match_text_seq("TO")
            new_column = self._parse_column()

            if old_column is None or not to or new_column is None:
…[8118 chars elided]…
ass: type[E], **kwargs: t.Any) -> E:
sqlglot/parser.py:8524:            not self.dialect.ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN
sqlglot/parser.py:8537:    def _parse_alter_table_alter(self) -> exp.Expr | None:
sqlglot/parser.py:8538:        if self._match_texts(self.ALTER_ALTER_PARSERS):
sqlglot/parser.py:8539:            return self.ALTER_ALTER_PARSERS[self._prev.text.upper()](self)
sqlglot/parser.py:8693:        parser = self.ALTER_PARSERS.get(self._prev.text.upper()) if self._prev else None
[tool_use Bash] {"command": "grep -n \"def altertable_sql\\|def alter_sql\" -A40 sqlglot/generator.py | head -90; echo ----; grep -n \"def property_sql\" -A25 sqlglot/generator.py | head -40; echo ----; grep -rn \"AUTO_INCREMENT\" tests/ | head -20; echo ----; grep -n \"def _parse_property_assignment\" -A10 sqlglot/parser.py", "description": "Read generator ALTER and property SQL code"}
[tool_result] 3975:    def alter_sql(self, expression: exp.Alter) -> str:
3976-        actions = expression.args["actions"]
3977-
3978-        if not self.dialect.ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN and isinstance(
3979-            actions[0], exp.ColumnDef
3980-        ):
3981-            actions_sql = self.expressions(expression, key="actions", flat=True)
3982-            actions_sql = f"ADD {actions_sql}"
3983-        else:
3984-            actions_list = []
3985-            for action in actions:
398
…[5347 chars elided]…
:    def _parse_property_assignment(self, exp_class: type[E], **kwargs: t.Any) -> E:
2791-        self._match(TokenType.EQ)
2792-        self._match(TokenType.ALIAS)
2793-
2794-        return self.expression(exp_class(this=self._parse_unquoted_field(), **kwargs))
2795-
2796-    def _parse_properties(self, before: bool | None = None) -> exp.Properties | None:
2797-        properties = []
2798-        while True:
2799-            if before:
2800-                prop = self._parse_property_before()
[tool_use Bash] {"command": "grep -n \"class Parser\\|PROPERTY_PARSERS\\|_PARSERS\\|ALTER\" sqlglot/dialects/mysql.py | head -30; echo ----; sed -n 170,200p tests/dialects/test_mysql.py; echo ----; grep -n \"ALTER TABLE\" tests/dialects/test_mysql.py | head -30; echo; source <work>/env-sqlglot/bin/python -c \"import sqlglot,sys;print(sqlglot.__file__, sys.version)\" 2>&1 | tail -2", "description": "Inspect MySQL parser and existing ALTER tests"}
[tool_result] ----
            },
        )
        self.validate_all(
            "CREATE TABLE t (id INT UNSIGNED)",
            write={
                "duckdb": "CREATE TABLE t (id UINTEGER)",
                "mysql": "CREATE TABLE t (id INT UNSIGNED)",
            },
        )
        self.validate_all(
            "CREATE TABLE z (a INT) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARACTER SET=utf8 COLLATE=utf8_bin COMMENT='x'",
            write={
                "duckdb": "CREATE TABLE z (a INT)",
       
…[2036 chars elided]…
ate_identity("ALTER TABLE t RENAME INDEX a TO b")
201:            "ALTER TABLE t RENAME KEY a TO b",
202:            "ALTER TABLE t RENAME INDEX a TO b",
241:        self.validate_identity("ALTER TABLE test_table ALTER COLUMN test_column SET DEFAULT 1")
1695:        expr = self.parse_one("ALTER TABLE t ADD COLUMN c INT INVISIBLE")

<work>/env-sqlglot/bin/python:2: unmatched '
[tool_use Bash] {"command": "ls sqlglot/dialects | head -50; ls sqlglot/parsers 2>/dev/null | head; grep -rln \"class MySQL\" sqlglot/ ; grep -rn \"ALTER_PARSERS\" sqlglot/ | grep -v \"^sqlglot/parser.py\" | head", "description": "Locate MySQL dialect parser module"}
[tool_result] __init__.py
athena.py
bigquery.py
clickhouse.py
databricks.py
dialect.py
doris.py
dremio.py
drill.py
druid.py
duckdb.py
dune.py
exasol.py
fabric.py
hive.py
materialize.py
mysql.py
oracle.py
postgres.py
presto.py
prql.py
redshift.py
risingwave.py
singlestore.py
snowflake.py
solr.py
spark.py
spark2.py
sqlite.py
starrocks.py
tableau.py
teradata.py
trino.py
tsql.py
__init__.py
athena.py
base.py
bigquery.py
clickhouse.py
databricks.py
doris.py
dremio.py
drill.py
druid.py
sqlglot/parsers/mysql.py
sqlg
…[170 chars elided]…
PARSERS,
sqlglot/parsers/hive.py:126:    ALTER_PARSERS = {
sqlglot/parsers/hive.py:127:        **parser.Parser.ALTER_PARSERS,
sqlglot/parsers/clickhouse.py:443:    ALTER_PARSERS = {
sqlglot/parsers/clickhouse.py:444:        **parser.Parser.ALTER_PARSERS,
sqlglot/parsers/snowflake.py:736:    ALTER_PARSERS = {
sqlglot/parsers/snowflake.py:737:        **parser.Parser.ALTER_PARSERS,
sqlglot/parsers/mysql.py:253:    ALTER_PARSERS = {
sqlglot/parsers/mysql.py:254:        **parser.Parser.ALTER_PARSERS,
[tool_use Bash] {"command": "sed -n 245,275p sqlglot/parsers/mysql.py; echo ----; grep -n \"^from\\|^import\" sqlglot/parsers/mysql.py; echo ----; sed -n 230,245p sqlglot/parsers/singlestore.py; echo; grep -n \"AUTO_INCREMENT\\|AutoIncrement\" sqlglot/parsers/mysql.py sqlglot/parsers/singlestore.py sqlglot/generators/mysql.py", "description": "View MySQL ALTER_PARSERS block and imports"}
[tool_result]         "FULLTEXT": lambda self: self._parse_index_constraint(kind="FULLTEXT"),
        "INDEX": lambda self: self._parse_index_constraint(),
        "KEY": lambda self: self._parse_index_constraint(),
        "SPATIAL": lambda self: self._parse_index_constraint(kind="SPATIAL"),
        "ZEROFILL": lambda self: self.expression(exp.ZeroFillColumnConstraint()),
        "INVISIBLE": lambda self: self.expression(exp.InvisibleColumnConstraint()),
    }

    ALTER_PARSERS = {
        **parser.Parser.A
…[989 chars elided]…
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
[assistant] Adding the MySQL-only ALTER parser entry. First, confirming current behavior with the project interpreter:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nprint(repr(sqlglot.parse_one('ALTER TABLE t AUTO_INCREMENT=3000000000', read='mysql')))\n\" 2>&1 | tail -3", "description": "Check current parse of ALTER TABLE AUTO_INCREMENT"}
[tool_result] 'ALTER TABLE t AUTO_INCREMENT=3000000000' contains unsupported syntax. Falling back to parsing as a 'Command'.
Command(this=ALTER, expression=TABLE t AUTO_INCREMENT=3000000000)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-155937-mysql-dialect-mysql-allows-setti/base-1/sqlglot/parsers/mysql.py", "old_string": "        \"MODIFY\": lambda self: self._parse_alter_table_alter(),\n    }", "new_string": "        \"AUTO_INCREMENT\": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),\n        \"MODIFY\": lambda self: self._parse_alter_table_alter(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-155937-mysql-dialect-mysql-allows-setti/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[assistant] Now a test next to the existing MySQL ALTER identity tests:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-155937-mysql-dialect-mysql-allows-setti/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"ALTER TABLE t RENAME INDEX a TO b\")\n", "new_string": "        self.validate_identity(\"ALTER TABLE t RENAME INDEX a TO b\")\n        self.validate_identity(\"ALTER TABLE t AUTO_INCREMENT=3000000000\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-155937-mysql-dialect-mysql-allows-setti/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one('ALTER TABLE t AUTO_INCREMENT=3000000000', read='mysql')\nprint(type(e).__name__, repr(e.args['actions'][0]))\nprint(e.sql('mysql'))\nprint(sqlglot.parse_one('ALTER TABLE t AUTO_INCREMENT = 5', read='mysql').sql('mysql'))\nprint(sqlglot.parse_one('ALTER TABLE t AUTO_INCREMENT=5', read='singlestore').sql('mysql'))\n\" 2>&1 | tail -6; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py tests/dialects/test_singlestore.py 2>&1 | tail -5", "description": "Verify parse, round-trip, and run MySQL tests"}
[tool_result] Alter AutoIncrementProperty(
  this=Literal(this=3000000000, is_string=False))
ALTER TABLE t AUTO_INCREMENT=3000000000
ALTER TABLE t AUTO_INCREMENT=5
ALTER TABLE t AUTO_INCREMENT=5
.............................. [ 40%]
.............................................                    [100%]
75 passed, 698 subtests passed in 0.35s
[assistant] Parsing, round-trip, and the MySQL/SingleStore tests pass. Now the full suite and the linter, since the edited line is long:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; RUFF=$(dirname $PY)/ruff; ls $RUFF 2>/dev/null && $RUFF format --check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py && $RUFF check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py; git -C . status --short", "description": "Run full test suite, ruff format and lint"}
[tool_result] ............................... [ 93%]
....................................................................       [100%]
1086 passed, 17844 subtests passed in 64.58s (0:01:04)
<work>/env-sqlglot/bin/ruff
2 files already formatted
All checks passed!
 M sqlglot/parsers/mysql.py
 M tests/dialects/test_mysql.py
[assistant] `ALTER TABLE t AUTO_INCREMENT=3000000000` now parses as an `AutoIncrementProperty` action and round-trips unchanged. The full suite passes (1086 passed) and ruff format and lint are clean.

The change is two edits:

- **`sqlglot/parsers/mysql.py`**: added `"AUTO_INCREMENT"` to the MySQL `ALTER_PARSERS`. It uses the same `_parse_property_assignment(exp.AutoIncrementProperty)` call as the CREATE TABLE property, so the two share one node type. I put it in the MySQL parser rather than the base parser so other dialects don't start accepting it. SingleStore inherits it through `MySQLParser.ALTER_PARSERS`.
- **`tests/dialects/test_mysql.py`**: added `validate_identity("ALTER TABLE t AUTO_INCREMENT=3000000000")` beside the other ALTER identity checks.

Before the change, the statement fell back to a generic `Command`. I haven't committed anything. Say if you want a commit, and I'll add the model attribution the repo asks for.
