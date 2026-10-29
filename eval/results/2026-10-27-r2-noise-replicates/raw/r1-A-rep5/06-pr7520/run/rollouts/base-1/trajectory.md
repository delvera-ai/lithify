# trajectory base-1

final message:
`ALTER TABLE t AUTO_INCREMENT=3000000000` now parses into the same `AutoIncrementProperty` that `CREATE TABLE` uses, and round-trips unchanged. The full suite passes (1086 tests) and ruff format and check are clean.

The change is one entry in the MySQL parser's `ALTER_PARSERS` (`sqlglot/parsers/mysql.py`):

```python
"AUTO_INCREMENT": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),
```

I also added `self.validate_identity("ALTER TABLE t AUTO_INCREMENT=3000000000")` to `tests/dialects/test_mysql.py`, next to the existing `RENAME INDEX` case.

One gap I left alone: `ALTER TABLE t AUTO_INCREMENT=3, ALGORITHM=INPLACE` still falls back to a `Command`. The action slot takes a single item, and the trailing comma options aren't consumed after it. Supporting that would mean changing how ALTER actions are parsed, which is a wider change than this request.

I haven't committed anything.

## events
[tool_use Bash] {"command": "grep -rn -i \"autoincrement\\|auto_increment\" sqlglot/ --include=*.py | head -50", "description": "Find auto-increment references in sqlglot source"}
[tool_use Bash] {"command": "grep -n -i \"ALTER_TABLE\\|def _parse_alter\\|_parse_alter_table\" sqlglot/parser.py sqlglot/dialects/mysql.py | head -40", "description": "Locate ALTER TABLE parsing code"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_result] sqlglot/parser.py:1421:        "ADD": lambda self: self._parse_alter_table_add(),
sqlglot/parser.py:1423:        "ALTER": lambda self: self._parse_alter_table_alter(),
sqlglot/parser.py:1426:        "DROP": lambda self: self._parse_alter_table_drop(),
sqlglot/parser.py:1427:        "RENAME": lambda self: self._parse_alter_table_rename(),
sqlglot/parser.py:1428:        "SET": lambda self: self._parse_alter_table_set(),
sqlglot/parser.py:1796:    ALTER_TABLE_PARTITIONS: t.ClassVar = False
sqlglot/
…[601 chars elided]…
 exp.RenameColumn | None:
sqlglot/parser.py:8619:    def _parse_alter_table_set(self) -> exp.AlterSet:
sqlglot/parser.py:8655:    def _parse_alter_session(self) -> exp.AlterSession:
sqlglot/parser.py:8667:    def _parse_alter(self) -> exp.Alter | exp.Command:
sqlglot/parser.py:8686:            this = self._parse_table(schema=True, parse_partition=self.ALTER_TABLE_PARTITIONS)
sqlglot/parser.py:8698:            cascade = self.dialect.ALTER_TABLE_SUPPORTS_CASCADE and self._match_text_seq("CASCADE")
[tool_use Bash] {"command": "grep -rn -i \"auto_increment\\|autoincrement\" sqlglot/ | grep -v \"\\.pyc\" | head -40; echo ---; sed -n 8594,8720p sqlglot/parser.py", "description": "Search AUTO_INCREMENT usage and view ALTER parser"}
[tool_result] sqlglot/tokenizer_core.py:247:    AUTO_INCREMENT = auto()
sqlglot/parser.py:660:        TokenType.AUTO_INCREMENT,
sqlglot/parser.py:1217:        "AUTO_INCREMENT": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),
sqlglot/parser.py:1327:        "AUTOINCREMENT": lambda self: self._parse_auto_increment(),
sqlglot/parser.py:1328:        "AUTO_INCREMENT": lambda self: self._parse_auto_increment(),
sqlglot/parser.py:1362:        "IDENTITY": lambda self: self._parse_auto_incremen
…[8210 chars elided]…
ists,
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

        return self._parse_as_command(start)

    def _parse_analyze(self) -> exp.Analyze | exp.Command:
        start = self._prev
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor s in ['ALTER TABLE t AUTO_INCREMENT=3000000000', 'CREATE TABLE t (id INT) AUTO_INCREMENT=3']:\n    e = sqlglot.parse_one(s, read='mysql')\n    print(type(e).__name__, repr(e))\n    print(e.sql('mysql'))\n\"; sed -n 1405,1435p sqlglot/parser.py; sed -n 1210,1220p sqlglot/parser.py; sed -n 36,50p sqlglot/expressions/properties.py; grep -n \"ALTER\" sqlglot/dialects/mysql.py sqlglot/generators/mysql.py | head", "description": "Check current MySQL ALTER parse behavior and related code"}
[tool_result] 'ALTER TABLE t AUTO_INCREMENT=3000000000' contains unsupported syntax. Falling back to parsing as a 'Command'.
Command Command(this=ALTER, expression=TABLE t AUTO_INCREMENT=3000000000)
ALTER TABLE t AUTO_INCREMENT=3000000000
Create Create(
  this=Schema(
    this=Table(
      this=Identifier(this=t, quoted=False)),
    expressions=[
      ColumnDef(
        this=Identifier(this=id, quoted=False),
        kind=DataType(this=DType.INT, nested=False))]),
  kind=TABLE,
  replace=False,
  refresh=Fal
…[2513 chars elided]…
entProperty),
        "BACKUP": lambda self: self.expression(
            exp.BackupProperty(this=self._parse_var(any_token=True))
        ),
class ApplicationProperty(Property):
    arg_types = {}


class AutoIncrementProperty(Property):
    arg_types = {"this": True}


class AutoRefreshProperty(Property):
    arg_types = {"this": True}


class BackupProperty(Property):
    arg_types = {"this": True}

sqlglot/generators/mysql.py:708:        """To avoid TO keyword in ALTER ... RENAME statements.
[tool_use Bash] {"command": "grep -n \"class Parser\\|PROPERTY_PARSERS\\|_PARSERS\\|class Generator\" sqlglot/dialects/mysql.py | head -30; grep -n \"def alter_sql\\|def _parse_property_assignment\" -A12 sqlglot/generator.py sqlglot/parser.py | head -60", "description": "Inspect MySQL parser class and alter generation"}
[tool_result] sqlglot/generator.py:3975:    def alter_sql(self, expression: exp.Alter) -> str:
sqlglot/generator.py-3976-        actions = expression.args["actions"]
sqlglot/generator.py-3977-
sqlglot/generator.py-3978-        if not self.dialect.ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN and isinstance(
sqlglot/generator.py-3979-            actions[0], exp.ColumnDef
sqlglot/generator.py-3980-        ):
sqlglot/generator.py-3981-            actions_sql = self.expressions(expression, key="actions", flat=True)
sq
…[721 chars elided]…
this=self._parse_unquoted_field(), **kwargs))
sqlglot/parser.py-2795-
sqlglot/parser.py-2796-    def _parse_properties(self, before: bool | None = None) -> exp.Properties | None:
sqlglot/parser.py-2797-        properties = []
sqlglot/parser.py-2798-        while True:
sqlglot/parser.py-2799-            if before:
sqlglot/parser.py-2800-                prop = self._parse_property_before()
sqlglot/parser.py-2801-            else:
sqlglot/parser.py-2802-                prop = self._parse_property()
[tool_use Bash] {"command": "ls sqlglot/dialects | head -50; ls sqlglot/parsers 2>/dev/null; ls sqlglot/generators | head -60; grep -rn \"ALTER_PARSERS\" sqlglot --include=*.py | head; sed -n 3988,4000p sqlglot/generator.py", "description": "Locate MySQL parser/generator files and ALTER_PARSERS overrides"}
[tool_result] __init__.py
__pycache__
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
__pycache__
athena.py
base.py
bigquery.py
clickhouse.py
databricks.py
doris.py
dremio.py
drill.py
druid.py
duckd
…[615 chars elided]…
eval):1: no matches found: --include=*.py
                else:
                    action_sql = self.sql(action)
                    if isinstance(action, exp.Query):
                        action_sql = f"AS {action_sql}"

                actions_list.append(action_sql)

            actions_sql = self.format_args(*actions_list).lstrip("\n")

        iceberg = (
            "ICEBERG "
            if expression.args.get("iceberg") and self.SUPPORTS_DROP_ALTER_ICEBERG_PROPERTY
            else ""
[tool_use Bash] {"command": "ls sqlglot/parsers 2>&1 | head -3; grep -n \"class Parser\" -A40 sqlglot/dialects/mysql.py | head -60; grep -rn \"ALTER_PARSERS\" sqlglot | grep -v pycache", "description": "View MySQL Parser class header and ALTER_PARSERS references"}
[tool_result] __init__.py
__pycache__
athena.py
sqlglot/parser.py:1420:    ALTER_PARSERS: t.ClassVar = {
sqlglot/parser.py:1434:    ALTER_ALTER_PARSERS: t.ClassVar = {
sqlglot/parser.py:8538:        if self._match_texts(self.ALTER_ALTER_PARSERS):
sqlglot/parser.py:8539:            return self.ALTER_ALTER_PARSERS[self._prev.text.upper()](self)
sqlglot/parser.py:8693:        parser = self.ALTER_PARSERS.get(self._prev.text.upper()) if self._prev else None
sqlglot/parsers/clickhouse.py:443:    ALTER_PARSERS = {
s
…[194 chars elided]…
ERS,
sqlglot/parsers/mysql.py:253:    ALTER_PARSERS = {
sqlglot/parsers/mysql.py:254:        **parser.Parser.ALTER_PARSERS,
sqlglot/parsers/mysql.py:258:    ALTER_ALTER_PARSERS = {
sqlglot/parsers/mysql.py:259:        **parser.Parser.ALTER_ALTER_PARSERS,
sqlglot/parsers/singlestore.py:236:    ALTER_PARSERS = {
sqlglot/parsers/singlestore.py:237:        **MySQLParser.ALTER_PARSERS,
sqlglot/parsers/hive.py:126:    ALTER_PARSERS = {
sqlglot/parsers/hive.py:127:        **parser.Parser.ALTER_PARSERS,
[tool_use Bash] {"command": "sed -n 240,275p sqlglot/parsers/mysql.py; grep -n \"ALTER\\|RENAME INDEX\" tests/dialects/test_mysql.py | head -20", "description": "View MySQL parser ALTER config and related tests"}
[tool_result]     SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
    SET_TRIE = new_trie(key.split(" ") for key in SET_PARSERS)

    CONSTRAINT_PARSERS = {
        **parser.Parser.CONSTRAINT_PARSERS,
        "FULLTEXT": lambda self: self._parse_index_constraint(kind="FULLTEXT"),
        "INDEX": lambda self: self._parse_index_constraint(),
        "KEY": lambda self: self._parse_index_constraint(),
        "SPATIAL": lambda self: self._parse_index_constraint(kind="SPATIAL"),
        "ZEROFILL": 
…[1885 chars elided]…
       "ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT",
195:        self.validate_identity("ALTER TABLE t ALTER INDEX i INVISIBLE")
196:        self.validate_identity("ALTER TABLE t ALTER INDEX i VISIBLE")
197:        self.validate_identity("ALTER TABLE t ALTER COLUMN c SET INVISIBLE")
198:        self.validate_identity("ALTER TABLE t ALTER COLUMN c SET VISIBLE")
199:        self.validate_identity("ALTER TABLE t RENAME INDEX a TO b")
201:            "ALTER TABLE t RENAME KEY a TO b",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-091757-mysql-dialect-mysql-allows-setti/base-1/sqlglot/parsers/mysql.py", "old_string": "        \"MODIFY\": lambda self: self._parse_alter_table_alter(),\n    }", "new_string": "        \"AUTO_INCREMENT\": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),\n        \"MODIFY\": lambda self: self._parse_alter_table_alter(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-091757-mysql-dialect-mysql-allows-setti/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t AUTO_INCREMENT=3000000000', 'ALTER TABLE t AUTO_INCREMENT 3000000000', 'ALTER TABLE t AUTO_INCREMENT=3, ALGORITHM=INPLACE']:\n    e = sqlglot.parse_one(s, read='mysql')\n    print(type(e).__name__, e.args.get('actions'))\n    print(e.sql('mysql'))\n    print(e.sql('mysql') == s)\nprint(sqlglot.transpile('ALTER TABLE t AUTO_INCREMENT=3', read='mysql', write='mysql'))\n\"; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -3", "description": "Verify ALTER AUTO_INCREMENT parse and round-trip, run MySQL tests"}
[tool_result] 'ALTER TABLE t AUTO_INCREMENT=3, ALGORITHM=INPLACE' contains unsupported syntax. Falling back to parsing as a 'Command'.
Alter [AutoIncrementProperty(
  this=Literal(this=3000000000, is_string=False))]
ALTER TABLE t AUTO_INCREMENT=3000000000
True
Alter [AutoIncrementProperty(
  this=Literal(this=3000000000, is_string=False))]
ALTER TABLE t AUTO_INCREMENT=3000000000
False
Command None
ALTER TABLE t AUTO_INCREMENT=3, ALGORITHM=INPLACE
True
['ALTER TABLE t AUTO_INCREMENT=3']
.............................. [ 61%]
...................                                               [100%]
49 passed, 481 subtests passed in 0.25s
[tool_use Bash] {"command": "sed -n 194,202p tests/dialects/test_mysql.py", "description": "View test context for insertion point"}
[tool_result]         )
        self.validate_identity("ALTER TABLE t ALTER INDEX i INVISIBLE")
        self.validate_identity("ALTER TABLE t ALTER INDEX i VISIBLE")
        self.validate_identity("ALTER TABLE t ALTER COLUMN c SET INVISIBLE")
        self.validate_identity("ALTER TABLE t ALTER COLUMN c SET VISIBLE")
        self.validate_identity("ALTER TABLE t RENAME INDEX a TO b")
        self.validate_identity(
            "ALTER TABLE t RENAME KEY a TO b",
            "ALTER TABLE t RENAME INDEX a TO b",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-091757-mysql-dialect-mysql-allows-setti/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"ALTER TABLE t RENAME INDEX a TO b\")\n        self.validate_identity(\n            \"ALTER TABLE t RENAME KEY a TO b\",", "new_string": "        self.validate_identity(\"ALTER TABLE t RENAME INDEX a TO b\")\n        self.validate_identity(\"ALTER TABLE t AUTO_INCREMENT=3000000000\")\n        self.validate_identity(\n            \"ALTER TABLE t RENAME KEY a TO b\","}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-091757-mysql-dialect-mysql-allows-setti/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py 2>&1 | tail -2; <work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py 2>&1 | tail -2", "description": "Run full test suite and ruff checks"}
[tool_result] ............................................... [ 73%]
.................................................................................................................................................................................................. [ 90%]
............................... [ 93%]
....................................................................       [100%]
1086 passed, 17844 subtests passed in 48.81s
2 files already formatted
All checks passed!
[assistant] `ALTER TABLE t AUTO_INCREMENT=3000000000` now parses into the same `AutoIncrementProperty` that `CREATE TABLE` uses, and round-trips unchanged. The full suite passes (1086 tests) and ruff format and check are clean.

The change is one entry in the MySQL parser's `ALTER_PARSERS` (`sqlglot/parsers/mysql.py`):

```python
"AUTO_INCREMENT": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),
```

I also added `self.validate_identity("ALTER TABLE t AUTO_INCREMENT=3000000000")` to `tests/dialects/test_mysql.py`, next to the existing `RENAME INDEX` case.

One gap I left alone: `ALTER TABLE t AUTO_INCREMENT=3, ALGORITHM=INPLACE` still falls back to a `Command`. The action slot takes a single item, and the trailing comma options aren't consumed after it. Supporting that would mean changing how ALTER actions are parsed, which is a wider change than this request.

I haven't committed anything.
