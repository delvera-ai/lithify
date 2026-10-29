# trajectory base-1

final message:
MySQL `ALTER TABLE t AUTO_INCREMENT=3000000000` now parses as an `AutoIncrementProperty` action and round-trips. The full suite passes (1086 tests) and ruff is clean. I left the changes uncommitted.

The change is in `sqlglot/parsers/mysql.py`. MySQL already had its own `ALTER_PARSERS` table there, so I added the `AUTO_INCREMENT` entry to that table. It reuses the same `_parse_property_assignment(exp.AutoIncrementProperty)` call that the `CREATE TABLE` path uses. Otherwise the statement fell back to `exp.Command`.

I added round-trip tests to `tests/dialects/test_mysql.py`, next to the existing ALTER TABLE tests. They cover `AUTO_INCREMENT=3000000000` alone and combined with `ALGORITHM=INPLACE`.

Transpiling this statement to Postgres gives `ALTER TABLE t AUTO_INCREMENT=3000000000`, which Postgres does not accept. That is out of scope for this MySQL-only change. It is the same generic property output that the existing `CREATE TABLE` path produces.

## events
[tool_use Bash] {"command": "grep -rn -i \"auto_increment\\|AutoIncrementProperty\" sqlglot/ | head -50 && grep -n \"def _parse_alter_table_alter\\|def _parse_alter\\b\\|ALTER_PARSERS\\|def _parse_alter_table_set\\|AlterTable\" sqlglot/parser.py sqlglot/dialects/mysql.py | head -40", "description": "Search for auto-increment and ALTER parsing code"}
[tool_result] sqlglot/tokens.py:238:        "AUTOINCREMENT": TokenType.AUTO_INCREMENT,
sqlglot/tokens.py:239:        "AUTO_INCREMENT": TokenType.AUTO_INCREMENT,
sqlglot/tokenizer_core.py:247:    AUTO_INCREMENT = auto()
sqlglot/generator.py:653:        exp.AutoIncrementProperty: exp.Properties.Location.POST_SCHEMA,
sqlglot/generator.py:1174:        return self.token_sql(TokenType.AUTO_INCREMENT)
sqlglot/parser.py:660:        TokenType.AUTO_INCREMENT,
sqlglot/parser.py:1217:        "AUTO_INCREMENT": lambda self
…[1964 chars elided]…
  def _parse_alter_table_alter(self) -> exp.Expr | None:
sqlglot/parser.py:8538:        if self._match_texts(self.ALTER_ALTER_PARSERS):
sqlglot/parser.py:8539:            return self.ALTER_ALTER_PARSERS[self._prev.text.upper()](self)
sqlglot/parser.py:8619:    def _parse_alter_table_set(self) -> exp.AlterSet:
sqlglot/parser.py:8667:    def _parse_alter(self) -> exp.Alter | exp.Command:
sqlglot/parser.py:8693:        parser = self.ALTER_PARSERS.get(self._prev.text.upper()) if self._prev else None
[tool_use Bash] {"command": "sed -n 1415,1450p sqlglot/parser.py && sed -n 8530,8560p sqlglot/parser.py && sed -n 8660,8730p sqlglot/parser.py && sed -n 7075,7100p sqlglot/parser.py && sed -n 35,50p sqlglot/expressions/properties.py && grep -n \"AUTO_INCREMENT\\|AutoIncrement\" tests/dialects/test_mysql.py | head; grep -n \"ALTER_PARSERS\\|_parse_alter_table_set\\|ALTER_TABLE\" sqlglot/dialects/mysql.py | head", "description": "Inspect ALTER parsing code and tests"}
[tool_result]             # Trino ref: https://docs.aws.amazon.com/athena/latest/ug/create-table-as.html#ctas-table-properties
            this, expression = expression, this

        return self.expression(klass(this=this, expression=expression))

    ALTER_PARSERS: t.ClassVar = {
        "ADD": lambda self: self._parse_alter_table_add(),
        "AS": lambda self: self._parse_select(),
        "ALTER": lambda self: self._parse_alter_table_alter(),
        "CLUSTER BY": lambda self: self._parse_cluster(wrapp
…[7331 chars elided]…
              "mysql": "CREATE TABLE x (id INT NOT NULL AUTO_INCREMENT, PRIMARY KEY (id))",
1122:            "CREATE TABLE z (a INT) ENGINE=InnoDB AUTO_INCREMENT=1 CHARACTER SET=utf8 COLLATE=utf8_bin COMMENT='x'"
1125:            "CREATE TABLE z (a INT) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARACTER SET=utf8 COLLATE=utf8_bin COMMENT='x'"
1128:            "CREATE TABLE z (a INT DEFAULT NULL, PRIMARY KEY (a)) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARACTER SET=utf8 COLLATE=utf8_bin COMMENT='x'"
[tool_use Bash] {"command": "grep -n \"class Parser\\|class Generator\\|PROPERTY_PARSERS\\|ALTER\\|_parse_property_assignment\" sqlglot/dialects/mysql.py | head -30; grep -n \"def _parse_property_assignment\" -A12 sqlglot/parser.py; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t AUTO_INCREMENT=3000000000','ALTER TABLE t AUTO_INCREMENT 3']:\n    try:\n        e=sqlglot.parse_one(s,read='mysql'); print(type(e).__name__, repr(e.args.get('actions')), e.sql('mysql'))\n    except Exception as ex: print('ERR',ex)\n\"", "description": "Inspect MySQL parser and current ALTER behavior"}
[tool_result] 2790:    def _parse_property_assignment(self, exp_class: type[E], **kwargs: t.Any) -> E:
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
2801-            else:
2802-                prop = self._parse_property()
'ALTER TABLE t AUTO_INCREMENT=3000000000' contains unsupported syntax. Falling back to parsing as a 'Command'.
'ALTER TABLE t AUTO_INCREMENT 3' contains unsupported syntax. Falling back to parsing as a 'Command'.
Command None ALTER TABLE t AUTO_INCREMENT=3000000000
Command None ALTER TABLE t AUTO_INCREMENT 3
[tool_use Bash] {"command": "ls sqlglot/dialects/ | head -50; ls sqlglot/parsers sqlglot/generators 2>/dev/null | head -80; grep -rln \"class MySQL\" sqlglot/", "description": "Locate MySQL dialect implementation files"}
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
sqlglot/generators:
__init__.py
__pycache__
athena.py
bigquery.py
clickhouse.py
databricks.py
doris.py
dremio.py
drill.py
dr
…[230 chars elided]…
y
teradata.py
trino.py
tsql.py

sqlglot/parsers:
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
sqlglot/parsers/mysql.py
sqlglot/dialects/mysql.py
sqlglot/generators/mysql.py
[tool_use Bash] {"command": "cat sqlglot/parsers/mysql.py | head -150; grep -n \"ALTER\\|alter\" sqlglot/generators/mysql.py sqlglot/generators/base.py | head -30", "description": "Read MySQL parser and check generator ALTER handling"}
[tool_result] from __future__ import annotations

import typing as t

from sqlglot import exp, parser
from sqlglot.trie import new_trie
from sqlglot.dialects.dialect import (
    Dialect,
    build_date_delta,
    build_date_delta_with_interval,
    build_formatted_time,
    isnull_to_is_null,
)
from sqlglot.helper import seq_get
from sqlglot.tokens import TokenType


# All specifiers for time parts (as opposed to date parts)
# https://dev.mysql.com/doc/refman/8.0/en/date-and-time-functions.html#function_date
…[4951 chars elided]…
s=exp.TsOrDsToDate(this=seq_get(args, 0))),
ugrep: warning: sqlglot/generators/base.py: No such file or directory
328:        "alter",
707:    def alterrename_sql(self, expression: exp.AlterRename, include_to: bool = True) -> str:
708:        """To avoid TO keyword in ALTER ... RENAME statements.
711:        return super().alterrename_sql(expression, include_to=False)
713:    def altercolumn_sql(self, expression: exp.AlterColumn) -> str:
716:            return super().altercolumn_sql(expression)
[tool_use Bash] {"command": "grep -n \"class MySQLParser\" -A3 sqlglot/parsers/mysql.py | head -3 && grep -n \"^    FUNCTIONS = {\" sqlglot/parsers/mysql.py && grep -n \"def alter_sql\" -A25 sqlglot/generators/base.py | head -40 && grep -n \"AutoIncrement\\|def _parse_unquoted_field\" -A3 sqlglot/parser.py | head -20", "description": "Check ALTER generation and parser hooks"}
[tool_result] 54:class MySQLParser(parser.Parser):
55-    NO_PAREN_FUNCTIONS = {
56-        **parser.Parser.NO_PAREN_FUNCTIONS,
102:    FUNCTIONS = {
ugrep: warning: sqlglot/generators/base.py: No such file or directory
1217:        "AUTO_INCREMENT": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),
1218-        "BACKUP": lambda self: self.expression(
1219-            exp.BackupProperty(this=self._parse_var(any_token=True))
1220-        ),
--
2783:    def _parse_unquoted_field(self) -> 
…[57 chars elided]…

2785-        if isinstance(field, exp.Identifier) and not field.quoted:
2786-            field = exp.var(field)
--
7083:    ) -> exp.GeneratedAsIdentityColumnConstraint | exp.AutoIncrementColumnConstraint:
7084-        start = None
7085-        increment = None
7086-        order = None
--
7106:        return exp.AutoIncrementColumnConstraint()
7107-
7108-    def _parse_check_constraint(self) -> exp.CheckColumnConstraint | None:
7109-        if not self._match(TokenType.L_PAREN, advance=False):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111905-mysql-dialect-mysql-allows-setti/base-1/sqlglot/parsers/mysql.py", "old_string": "    FUNCTIONS = {\n        **parser.Parser.FUNCTIONS,\n        \"BIT_AND\": exp.BitwiseAndAgg.from_arg_list,", "new_string": "    ALTER_PARSERS = {\n        **parser.Parser.ALTER_PARSERS,\n        \"AUTO_INCREMENT\": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),\n    }\n\n    FUNCTIONS = {\n        **parser.Parser.FUNCTIONS,\n        \"BIT_AND\": exp.BitwiseAndAgg.from_arg_list,"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-111905-mysql-dialect-mysql-allows-setti/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t AUTO_INCREMENT=3000000000','ALTER TABLE t AUTO_INCREMENT 3', 'ALTER TABLE t AUTO_INCREMENT = 5']:\n    e=sqlglot.parse_one(s,read='mysql'); print(type(e).__name__, repr(e.args.get('actions')), e.sql('mysql'))\ne=sqlglot.parse_one('ALTER TABLE t AUTO_INCREMENT=3000000000',read='mysql'); print(repr(e.sql('mysql')), e.sql('mysql', pretty=False))\nprint(sqlglot.transpile('ALTER TABLE t AUTO_INCREMENT=3000000000',read='mysql',write='postgres'))\n\"", "description": "Test MySQL ALTER TABLE AUTO_INCREMENT parsing"}
[tool_result] 'ALTER TABLE t AUTO_INCREMENT=3000000000' contains unsupported syntax. Falling back to parsing as a 'Command'.
'ALTER TABLE t AUTO_INCREMENT 3' contains unsupported syntax. Falling back to parsing as a 'Command'.
'ALTER TABLE t AUTO_INCREMENT = 5' contains unsupported syntax. Falling back to parsing as a 'Command'.
'ALTER TABLE t AUTO_INCREMENT=3000000000' contains unsupported syntax. Falling back to parsing as a 'Command'.
'ALTER TABLE t AUTO_INCREMENT=3000000000' contains unsupported syntax. Falling back to parsing as a 'Command'.
Command None ALTER TABLE t AUTO_INCREMENT=3000000000
Command None ALTER TABLE t AUTO_INCREMENT 3
Command None ALTER TABLE t AUTO_INCREMENT = 5
'ALTER TABLE t AUTO_INCREMENT=3000000000' ALTER TABLE t AUTO_INCREMENT=3000000000
['ALTER TABLE t AUTO_INCREMENT=3000000000']
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nfrom sqlglot.dialects.mysql import MySQL\nfrom sqlglot import tokens\nprint('AUTO_INCREMENT' in MySQL.Parser.ALTER_PARSERS, MySQL.Parser.ALTER_PARSERS.keys())\nfrom sqlglot.parsers.mysql import MySQLParser\nprint(MySQLParser.ALTER_PARSERS.keys())\nprint([ (t.token_type, t.text) for t in MySQL().tokenize('ALTER TABLE t AUTO_INCREMENT=3')])\n\" ; grep -n \"_parse_alter\\b\\|ALTER_PARSERS\\|def _parse_alter_table_set\" -n sqlglot/parser*.py sqlglot/parsers/base.py | head", "description": "Debug why MySQL ALTER parser override is not used"}
[tool_result] False dict_keys(['ADD', 'AS', 'ALTER', 'CLUSTER BY', 'DELETE', 'DROP', 'RENAME', 'SET', 'SWAP', 'MODIFY'])
dict_keys(['ADD', 'AS', 'ALTER', 'CLUSTER BY', 'DELETE', 'DROP', 'RENAME', 'SET', 'SWAP', 'MODIFY'])
[(<TokenType.ALTER: 217>, 'ALTER'), (<TokenType.TABLE: 82>, 'TABLE'), (<TokenType.VAR: 87>, 't'), (<TokenType.AUTO_INCREMENT: 226>, 'AUTO_INCREMENT'), (<TokenType.EQ: 28>, '='), (<TokenType.NUMBER: 76>, '3')]
sqlglot/parser.py:1067:        TokenType.ALTER: lambda self: self._parse_alter(),
s
…[62 chars elided]…
t/parser.py:1434:    ALTER_ALTER_PARSERS: t.ClassVar = {
sqlglot/parser.py:8538:        if self._match_texts(self.ALTER_ALTER_PARSERS):
sqlglot/parser.py:8539:            return self.ALTER_ALTER_PARSERS[self._prev.text.upper()](self)
sqlglot/parser.py:8619:    def _parse_alter_table_set(self) -> exp.AlterSet:
sqlglot/parser.py:8667:    def _parse_alter(self) -> exp.Alter | exp.Command:
sqlglot/parser.py:8693:        parser = self.ALTER_PARSERS.get(self._prev.text.upper()) if self._prev else None
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot; print(sqlglot.__file__)\nfrom sqlglot.dialects.mysql import MySQL; print(MySQL.Parser.__module__, MySQL.Parser.__mro__)\n\"; grep -n \"ALTER_PARSERS\" -A3 sqlglot/parsers/base.py | head; ls sqlglot/parsers/__pycache__ | head -3", "description": "Check which sqlglot package is being imported"}
[tool_result] ~/.cache/lithify/work/repo-90e86f132b84/20261028-111905-mysql-dialect-mysql-allows-setti/base-1/sqlglot/__init__.py
sqlglot.parsers.mysql (<class 'sqlglot.parsers.mysql.MySQLParser'>, <class 'sqlglot.parser.Parser'>, <class 'object'>)
__init__.cpython-312.pyc
base.cpython-312.pyc
mysql.cpython-312.pyc
[tool_use Bash] {"command": "grep -n \"ALTER_PARSERS\\|MODIFY\" sqlglot/parsers/mysql.py sqlglot/parser.py sqlglot/dialects/mysql.py", "description": "Find all ALTER_PARSERS definitions for MySQL"}
[tool_result] sqlglot/parser.py:1420:    ALTER_PARSERS: t.ClassVar = {
sqlglot/parser.py:1434:    ALTER_ALTER_PARSERS: t.ClassVar = {
sqlglot/parser.py:8538:        if self._match_texts(self.ALTER_ALTER_PARSERS):
sqlglot/parser.py:8539:            return self.ALTER_ALTER_PARSERS[self._prev.text.upper()](self)
sqlglot/parser.py:8693:        parser = self.ALTER_PARSERS.get(self._prev.text.upper()) if self._prev else None
sqlglot/parsers/mysql.py:102:    ALTER_PARSERS = {
sqlglot/parsers/mysql.py:103:        **parser.Parser.ALTER_PARSERS,
sqlglot/parsers/mysql.py:258:    ALTER_PARSERS = {
sqlglot/parsers/mysql.py:259:        **parser.Parser.ALTER_PARSERS,
sqlglot/parsers/mysql.py:260:        "MODIFY": lambda self: self._parse_alter_table_alter(),
sqlglot/parsers/mysql.py:263:    ALTER_ALTER_PARSERS = {
sqlglot/parsers/mysql.py:264:        **parser.Parser.ALTER_ALTER_PARSERS,
[assistant] There's already a MySQL `ALTER_PARSERS` at line 258 that overrides the one I added. I'll move the entry there.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111905-mysql-dialect-mysql-allows-setti/base-1/sqlglot/parsers/mysql.py", "old_string": "    ALTER_PARSERS = {\n        **parser.Parser.ALTER_PARSERS,\n        \"AUTO_INCREMENT\": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),\n    }\n\n    FUNCTIONS = {", "new_string": "    FUNCTIONS = {"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-111905-mysql-dialect-mysql-allows-setti/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Bash] {"command": "sed -n 255,265p sqlglot/parsers/mysql.py", "description": "View existing MySQL ALTER_PARSERS block"}
[tool_result]         "MODIFY": lambda self: self._parse_alter_table_alter(),
    }

    ALTER_ALTER_PARSERS = {
        **parser.Parser.ALTER_ALTER_PARSERS,
        "INDEX": lambda self: self._parse_alter_table_alter_index(),
    }

    SCHEMA_UNNAMED_CONSTRAINTS = {
        *parser.Parser.SCHEMA_UNNAMED_CONSTRAINTS,
        "FULLTEXT",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111905-mysql-dialect-mysql-allows-setti/base-1/sqlglot/parsers/mysql.py", "old_string": "        \"MODIFY\": lambda self: self._parse_alter_table_alter(),\n    }", "new_string": "        \"AUTO_INCREMENT\": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),\n        \"MODIFY\": lambda self: self._parse_alter_table_alter(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-111905-mysql-dialect-mysql-allows-setti/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t AUTO_INCREMENT=3000000000','ALTER TABLE t AUTO_INCREMENT 3', 'ALTER TABLE t AUTO_INCREMENT = 5', 'ALTER TABLE db.t AUTO_INCREMENT=1 ALGORITHM=INPLACE']:\n    e=sqlglot.parse_one(s,read='mysql'); print(type(e).__name__, repr(e.args.get('actions')), e.sql('mysql'))\nprint(sqlglot.transpile('ALTER TABLE t AUTO_INCREMENT=3000000000',read='mysql',write='mysql'))\nprint(sqlglot.transpile('ALTER TABLE t AUTO_INCREMENT=3000000000',read='mysql',write='postgres'))\n\" 2>&1", "description": "Verify MySQL ALTER TABLE AUTO_INCREMENT parse and output"}
[tool_result] Alter [AutoIncrementProperty(
  this=Literal(this=3000000000, is_string=False))] ALTER TABLE t AUTO_INCREMENT=3000000000
Alter [AutoIncrementProperty(
  this=Literal(this=3, is_string=False))] ALTER TABLE t AUTO_INCREMENT=3
Alter [AutoIncrementProperty(
  this=Literal(this=5, is_string=False))] ALTER TABLE t AUTO_INCREMENT=5
Alter [AutoIncrementProperty(
  this=Literal(this=1, is_string=False))] ALTER TABLE db.t AUTO_INCREMENT=1, ALGORITHM=INPLACE
['ALTER TABLE t AUTO_INCREMENT=3000000000']
['ALTER TABLE t AUTO_INCREMENT=3000000000']
[assistant] Parsing and round-tripping work. Now I'll add a test next to the existing MySQL ALTER TABLE tests.
[tool_use Bash] {"command": "grep -n \"ALTER TABLE\" tests/dialects/test_mysql.py | head -30", "description": "Find existing ALTER TABLE tests in MySQL test file"}
[tool_result] 32:        self.validate_identity("ALTER TABLE t ADD COLUMN c INT INVISIBLE")
33:        self.validate_identity("ALTER TABLE t1 ADD COLUMN x INT, ALGORITHM=INPLACE, LOCK=EXCLUSIVE")
34:        self.validate_identity("ALTER TABLE t ADD INDEX `i` (`c`)")
35:        self.validate_identity("ALTER TABLE t ADD UNIQUE `i` (`c`)")
36:        self.validate_identity("ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT")
133:            "ALTER TABLE t ADD KEY `i` (`c`)",
134:            "ALTER TABLE 
…[355 chars elided]…
lf.validate_identity("ALTER TABLE t ALTER COLUMN c SET INVISIBLE")
198:        self.validate_identity("ALTER TABLE t ALTER COLUMN c SET VISIBLE")
199:        self.validate_identity("ALTER TABLE t RENAME INDEX a TO b")
201:            "ALTER TABLE t RENAME KEY a TO b",
202:            "ALTER TABLE t RENAME INDEX a TO b",
241:        self.validate_identity("ALTER TABLE test_table ALTER COLUMN test_column SET DEFAULT 1")
1695:        expr = self.parse_one("ALTER TABLE t ADD COLUMN c INT INVISIBLE")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111905-mysql-dialect-mysql-allows-setti/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"ALTER TABLE t RENAME INDEX a TO b\")\n", "new_string": "        self.validate_identity(\"ALTER TABLE t RENAME INDEX a TO b\")\n        self.validate_identity(\"ALTER TABLE t AUTO_INCREMENT=3000000000\")\n        self.validate_identity(\n            \"ALTER TABLE t AUTO_INCREMENT=1, ALGORITHM=INPLACE\",\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-111905-mysql-dialect-mysql-allows-setti/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111905-mysql-dialect-mysql-allows-setti/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\n            \"ALTER TABLE t AUTO_INCREMENT=1, ALGORITHM=INPLACE\",\n        )\n", "new_string": "        self.validate_identity(\"ALTER TABLE t AUTO_INCREMENT=1, ALGORITHM=INPLACE\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-111905-mysql-dialect-mysql-allows-setti/base-1/tests/dialects/test_mysql.py has been updated successfully.
[assistant] Now the project's test command, plus lint on the two changed files.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; (<work>/env-sqlglot/bin/ruff check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py) 2>&1 | tail -5", "description": "Run full pytest suite and lint changed files"}
[tool_result] ................................................................................. [  7%]
............................................. [ 11%]
...................................................... [ 16%]
........ [ 17%]
................................. [ 20%]
...............................................................................................................................................................................................................................................
…[285 chars elided]…
......................... [ 68%]
............................................... [ 73%]
.................................................................................................................................................................................................. [ 90%]
............................... [ 93%]
....................................................................       [100%]
1086 passed, 17844 subtests passed in 52.43s
All checks passed!
2 files already formatted
[assistant] MySQL `ALTER TABLE t AUTO_INCREMENT=3000000000` now parses as an `AutoIncrementProperty` action and round-trips. The full suite passes (1086 tests) and ruff is clean. I left the changes uncommitted.

The change is in `sqlglot/parsers/mysql.py`. MySQL already had its own `ALTER_PARSERS` table there, so I added the `AUTO_INCREMENT` entry to that table. It reuses the same `_parse_property_assignment(exp.AutoIncrementProperty)` call that the `CREATE TABLE` path uses. Otherwise the statement fell back to `exp.Command`.

I added round-trip tests to `tests/dialects/test_mysql.py`, next to the existing ALTER TABLE tests. They cover `AUTO_INCREMENT=3000000000` alone and combined with `ALGORITHM=INPLACE`.

Transpiling this statement to Postgres gives `ALTER TABLE t AUTO_INCREMENT=3000000000`, which Postgres does not accept. That is out of scope for this MySQL-only change. It is the same generic property output that the existing `CREATE TABLE` path produces.
