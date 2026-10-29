# trajectory base-1

final message:
MySQL `ALTER TABLE t AUTO_INCREMENT=...` now parses as the same `AutoIncrementProperty` that `CREATE TABLE` uses, and round-trips. The full suite passes (1086 tests) and ruff is clean on the changed files.

**Change:** I added one entry to `MySQLParser.ALTER_PARSERS` in `sqlglot/parsers/mysql.py`:

```python
"AUTO_INCREMENT": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),
```

Before this, the statement fell back to a raw `Command`. Now `ALTER TABLE t AUTO_INCREMENT=3000000000` produces an `Alter` whose action is an `AutoIncrementProperty`, and it generates back as `ALTER TABLE t AUTO_INCREMENT=3000000000`. The space-separated form `AUTO_INCREMENT 5` normalizes to `AUTO_INCREMENT=5`, as it does in `CREATE TABLE`.

**Tests:** I added two cases to the existing ALTER section of `tests/dialects/test_mysql.py`: the round-trip for `AUTO_INCREMENT=3000000000` and the normalization for `AUTO_INCREMENT 5`.

**Not covered:** A comma-joined option after the counter, such as `ALTER TABLE t AUTO_INCREMENT=1, ALGORITHM=INPLACE`, still falls back to `Command`. `ALTER TABLE t MODIFY COLUMN c INT, ALGORITHM=INPLACE` already behaves the same way, so this is a pre-existing limit of the comma-option handling, and I left it alone.

I haven't committed. The changes are in the working tree only.

## events
[tool_use Bash] {"command": "grep -rn \"AUTO_INCREMENT\\|AutoIncrementProperty\" sqlglot/ | head -50", "description": "Find AUTO_INCREMENT references in source"}
[tool_result] sqlglot/tokens.py:238:        "AUTOINCREMENT": TokenType.AUTO_INCREMENT,
sqlglot/tokens.py:239:        "AUTO_INCREMENT": TokenType.AUTO_INCREMENT,
sqlglot/tokenizer_core.py:247:    AUTO_INCREMENT = auto()
sqlglot/parser.py:660:        TokenType.AUTO_INCREMENT,
sqlglot/parser.py:1217:        "AUTO_INCREMENT": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),
sqlglot/parser.py:1328:        "AUTO_INCREMENT": lambda self: self._parse_auto_increment(),
sqlglot/generator.py:653:
…[92 chars elided]…
:1174:        return self.token_sql(TokenType.AUTO_INCREMENT)
sqlglot/expressions/properties.py:40:class AutoIncrementProperty(Property):
sqlglot/expressions/properties.py:587:        "AUTO_INCREMENT": AutoIncrementProperty,
sqlglot/generators/spark2.py:115:        exp.AutoIncrementProperty: exp.Properties.Location.UNSUPPORTED,
sqlglot/generators/sqlite.py:123:        TokenType.AUTO_INCREMENT: "AUTOINCREMENT",
sqlglot/generators/snowflake.py:653:        TokenType.AUTO_INCREMENT: "AUTOINCREMENT",
[tool_use Bash] {"command": "grep -n \"def _parse_alter_table_alter\\|def _parse_alter\\b\\|def _parse_alter(\\|ALTER_PARSERS\\|def _parse_alter_table_set\\|ALTER_PARSERS = \" sqlglot/parser.py sqlglot/dialects/mysql.py", "description": "Locate ALTER parser functions"}
[tool_result ERROR] Exit code 2
rg: regex parse error:
    (?:def _parse_alter_table_alter|def _parse_alter\b|def _parse_alter(|ALTER_PARSERS|def _parse_alter_table_set|ALTER_PARSERS = )
    ^
error: unclosed group
0 matches for 'def _parse_alter_table_alter\|def _parse_alter\b\|def _parse_alter(\|ALTER_PARSERS\|def _parse_alter_table_set\|ALTER_PARSERS = '
[tool_use Bash] {"command": "grep -n \"ALTER_PARSERS\\|def _parse_alter\\|def _parse_auto_increment\\|_parse_property_assignment(exp.AutoIncrement\" sqlglot/parser.py sqlglot/dialects/mysql.py sqlglot/dialects/dialect.py; sed -n 1205,1225p sqlglot/parser.py; sed -n 1320,1335p sqlglot/parser.py", "description": "Locate ALTER parsers and auto-increment parsing"}
[tool_result] rg: regex parse error:
    (?:ALTER_PARSERS|def _parse_alter|def _parse_auto_increment|_parse_property_assignment(exp.AutoIncrement)
    ^
error: unclosed group
0 matches for 'ALTER_PARSERS\|def _parse_alter\|def _parse_auto_increment\|_parse_property_assignment(exp.AutoIncrement'
        "SELECT": lambda self, query: self._parse_pipe_syntax_select(query),
        "TABLESAMPLE": lambda self, query: self._parse_pipe_syntax_tablesample(query),
        "UNPIVOT": lambda self, query: self._parse_pip
…[1473 chars elided]…
MENT": lambda self: self._parse_auto_increment(),
        "CASESPECIFIC": lambda self: self.expression(exp.CaseSpecificColumnConstraint(not_=False)),
        "CHARACTER SET": lambda self: self.expression(
            exp.CharacterSetColumnConstraint(this=self._parse_var_or_string())
        ),
        "CHECK": lambda self: self._parse_check_constraint(),
        "COLLATE": lambda self: self.expression(
            exp.CollateColumnConstraint(this=self._parse_identifier() or self._parse_column())
[tool_use Bash] {"command": "rg -n \"ALTER_PARSERS|def _parse_alter|_parse_alter_table_set|def _parse_property_assignment|AlterTable\\b\" sqlglot/parser.py sqlglot/dialects/mysql.py | head -40", "description": "Search ALTER parser definitions"}
[tool_result] 16 matches in 1 files:

sqlglot/parser.py:1420:ALTER_PARSERS: t.ClassVar = {
sqlglot/parser.py:1428:"SET": lambda self: self._parse_alter_table_set(),
sqlglot/parser.py:1434:ALTER_ALTER_PARSERS: t.ClassVar = {
sqlglot/parser.py:2790:def _parse_property_assignment(self, exp_class: type[E], **kwargs: t.Any) -> E:
sqlglot/parser.py:8498:def _parse_alter_table_add(self) -> list[exp.Expr]:
sqlglot/parser.py:8537:def _parse_alter_table_alter(self) -> exp.Expr | None:
sqlglot/parser.py:8538:if self._ma
…[311 chars elided]…
ot/parser.py:8594:def _parse_alter_table_drop(self) -> list[exp.Expr]:
sqlglot/parser.py:8604:def _parse_alter_table_rename(self) -> exp.AlterRename | exp.RenameColumn | N...
sqlglot/parser.py:8619:def _parse_alter_table_set(self) -> exp.AlterSet:
sqlglot/parser.py:8655:def _parse_alter_session(self) -> exp.AlterSession:
sqlglot/parser.py:8667:def _parse_alter(self) -> exp.Alter | exp.Command:
sqlglot/parser.py:8693:parser = self.ALTER_PARSERS.get(self._prev.text.upper()) if self._prev else None
[tool_use Bash] {"command": "sed -n 1418,1442p sqlglot/parser.py; echo ----; sed -n 8619,8720p sqlglot/parser.py; echo ----; sed -n 2790,2800p sqlglot/parser.py; echo ----; rg -n \"AlterSet|AlterTable|class Alter\" sqlglot/expressions/*.py | head; echo ----; rg -n \"AlterSet|_alter_table_set|AlterTable|alter_set\" sqlglot/generator.py sqlglot/generators/*.py sqlglot/dialects/mysql.py | head -20", "description": "Read ALTER parser and generator code"}
[tool_result]         return self.expression(klass(this=this, expression=expression))

    ALTER_PARSERS: t.ClassVar = {
        "ADD": lambda self: self._parse_alter_table_add(),
        "AS": lambda self: self._parse_select(),
        "ALTER": lambda self: self._parse_alter_table_alter(),
        "CLUSTER BY": lambda self: self._parse_cluster(wrapped=True),
        "DELETE": lambda self: self.expression(exp.Delete(where=self._parse_where())),
        "DROP": lambda self: self._parse_alter_table_drop(),
    
…[6486 chars elided]…
LUMN {this} {alter_set_type}{dtype}{collate}{using}"
sqlglot/generator.py:3968:def alterset_sql(self, expression: exp.AlterSet) -> str:
sqlglot/generators/hive.py:500:def alterset_sql(self, expression: exp.AlterSet) -> str:
sqlglot/generators/postgres.py:465:def alterset_sql(self, expression: exp.AlterSet) -> str:
sqlglot/generators/redshift.py:313:def alterset_sql(self, expression: exp.AlterSet) -> str:
sqlglot/generators/snowflake.py:933:def alterset_sql(self, expression: exp.AlterSet) -> str:
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -I -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t AUTO_INCREMENT=3000000000','ALTER TABLE t AUTO_INCREMENT 5','CREATE TABLE t (id INT) AUTO_INCREMENT=5']:\n    e=sqlglot.parse_one(s,read='mysql'); print(type(e).__name__, repr(e)[:300]); print(e.sql('mysql'))\n\"; rg -n \"ALTER_PARSERS|class Parser|class Generator|ALTER_TABLE|AUTO_INCREMENT|AutoIncrement\" sqlglot/dialects/mysql.py; rg -n -A12 \"def alterset_sql\" sqlglot/generator.py; rg -n -B2 -A3 \"ALTER_SET_WRAPPED|WRAP.*AlterSet|alter.*wrapped\" sqlglot/generator.py | head -30", "description": "Check current MySQL ALTER AUTO_INCREMENT behavior"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
0 matches for 'ALTER_PARSERS|class Parser|class Generator|ALTER_TABLE|AUTO_INCREMENT|AutoIncrement'
3968:    def alterset_sql(self, expression: exp.AlterSet) -> str:
3969-        exprs = self.expressions(expression, flat=True)
3970-        if self.ALTER_SET_WRAPPED:
3971-            exprs = f"({exprs})"
3972-
3973-        return f"SET {exprs}"
3974-
3975-    def alter_sql(self, expression: exp.Alter) -> str:
3976-        actions = expression.args["actions"]
3977-
3978-        if not self.dialect.ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN and isinstance(
3979-            actions[0], exp.ColumnDef
3980-        ):
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t AUTO_INCREMENT=3000000000','ALTER TABLE t AUTO_INCREMENT 5','CREATE TABLE t (id INT) AUTO_INCREMENT=5']:\n    e=sqlglot.parse_one(s,read='mysql'); print(type(e).__name__, repr(e)[:400]); print(e.sql('mysql'))\n\"; rg -n \"ALTER_PARSERS|class Parser|class Generator|AUTO_INCREMENT|AutoIncrement\" sqlglot/dialects/mysql.py; rg -n \"ALTER_SET_WRAPPED\" sqlglot/generators/mysql.py sqlglot/dialects/mysql.py sqlglot/generator.py", "description": "Check current MySQL ALTER AUTO_INCREMENT behavior"}
[tool_result] 'ALTER TABLE t AUTO_INCREMENT=3000000000' contains unsupported syntax. Falling back to parsing as a 'Command'.
'ALTER TABLE t AUTO_INCREMENT 5' contains unsupported syntax. Falling back to parsing as a 'Command'.
Command Command(this=ALTER, expression=TABLE t AUTO_INCREMENT=3000000000)
ALTER TABLE t AUTO_INCREMENT=3000000000
Command Command(this=ALTER, expression=TABLE t AUTO_INCREMENT 5)
ALTER TABLE t AUTO_INCREMENT 5
Create Create(
  this=Schema(
    this=Table(
      this=Identifier(this=t, q
…[86 chars elided]…
ted=False),
        kind=DataType(this=DType.INT, nested=False))]),
  kind=TABLE,
  replace=False,
  refresh=False,
  unique=False,
  exists=False,
  properties=Properties(
    expressions=[
      AutoIncrementProperty(
        this=Literal(thi
CREATE TABLE t (id INT) AUTO_INCREMENT=5
0 matches for 'ALTER_PARSERS|class Parser|class Generator|AUTO_INCREMENT|AutoIncrement'
2 matches in 1 files:

sqlglot/generator.py:549:ALTER_SET_WRAPPED = False
sqlglot/generator.py:3970:if self.ALTER_SET_WRAPPED:
[tool_use Bash] {"command": "rg -n \"class Parser|class Generator|_PARSERS|PROPERTY_PARSERS|class MySQL\" sqlglot/dialects/mysql.py; rg -n -A8 \"ALTER_PARSERS\" sqlglot/dialects/*.py | head -40; sed -n 3975,4000p sqlglot/generator.py; rg -n -B2 -A10 \"class AutoIncrementProperty\" sqlglot/expressions/properties.py", "description": "Inspect MySQL parser class and ALTER generation"}
[tool_result] 1 matches in 1 files:

14:0:
    def alter_sql(self, expression: exp.Alter) -> str:
        actions = expression.args["actions"]

        if not self.dialect.ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN and isinstance(
            actions[0], exp.ColumnDef
        ):
            actions_sql = self.expressions(expression, key="actions", flat=True)
            actions_sql = f"ADD {actions_sql}"
        else:
            actions_list = []
            for action in actions:
                if isinstance
…[305 chars elided]…
s_list.append(action_sql)

            actions_sql = self.format_args(*actions_list).lstrip("\n")

        iceberg = (
            "ICEBERG "
            if expression.args.get("iceberg") and self.SUPPORTS_DROP_ALTER_ICEBERG_PROPERTY
            else ""
38-
39-
40:class AutoIncrementProperty(Property):
41-    arg_types = {"this": True}
42-
43-
44-class AutoRefreshProperty(Property):
45-    arg_types = {"this": True}
46-
47-
48-class BackupProperty(Property):
49-    arg_types = {"this": True}
50-
[tool_use Bash] {"command": "cat sqlglot/dialects/mysql.py | head -30; rg -n \"class Parser|class Generator|class Tokenizer\" sqlglot/dialects/mysql.py; ls sqlglot/dialects | head -50; rg -ln \"class Parser\\(\" sqlglot/dialects/ | head; rg -n \"ALTER_PARSERS\" sqlglot/ | head", "description": "Inspect MySQL dialect file structure"}
[tool_result] from __future__ import annotations

from sqlglot import tokens
from sqlglot.dialects.dialect import (
    Dialect,
    NormalizationStrategy,
)
from sqlglot.generators.mysql import MySQLGenerator
from sqlglot.parsers.mysql import MySQLParser
from sqlglot.tokens import TokenType
from sqlglot.typing.mysql import EXPRESSION_METADATA


class MySQL(Dialect):
    PROMOTE_TO_INFERRED_DATETIME_TYPE = True

    # https://dev.mysql.com/doc/refman/8.0/en/identifiers.html
    IDENTIFIERS_CAN_START_WITH_DIGI
…[1251 chars elided]…
S: t.ClassVar = {
sqlglot/parser.py:1434:ALTER_ALTER_PARSERS: t.ClassVar = {
sqlglot/parser.py:8538:if self._match_texts(self.ALTER_ALTER_PARSERS):
sqlglot/parser.py:8539:return self.ALTER_ALTER_PARSERS[self._prev.text.upper()](self)
sqlglot/parser.py:8693:parser = self.ALTER_PARSERS.get(self._prev.text.upper()) if self._prev else None
sqlglot/parsers/clickhouse.py:443:ALTER_PARSERS = {
sqlglot/parsers/clickhouse.py:444:**parser.Parser.ALTER_PARSERS,
sqlglot/parsers/hive.py:126:ALTER_PARSERS = {
[tool_use Bash] {"command": "cat sqlglot/parsers/mysql.py | head -80; rg -n \"ALTER_PARSERS\" -A6 sqlglot/parsers/clickhouse.py sqlglot/parsers/hive.py", "description": "Read MySQL parser and sibling ALTER_PARSERS overrides"}
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
…[2290 chars elided]…
PARSERS = {
sqlglot/parsers/hive.py:127:        **parser.Parser.ALTER_PARSERS,
sqlglot/parsers/hive.py-128-        "CHANGE": lambda self: self._parse_alter_table_change(),
sqlglot/parsers/hive.py-129-    }
sqlglot/parsers/hive.py-130-
sqlglot/parsers/hive.py-131-    def _parse_transform(self) -> exp.Transform | exp.QueryTransform | None:
sqlglot/parsers/hive.py-132-        if not self._match(TokenType.L_PAREN, advance=False):
sqlglot/parsers/hive.py-133-            self._retreat(self._index - 1)
[tool_use Bash] {"command": "rg -n \"^    [A-Z_]+ = |^    def \" sqlglot/parsers/mysql.py | head -30; rg -n \"AUTO_INCREMENT\" tests/dialects/*.py | head", "description": "List MySQL parser class members and existing tests"}
[tool_result] 41 matches in 10 files:

304:0:
333:0:
342:0:str | None = None) -> exp.IndexColumnConstraint:
48:0:MySQLParser) -> exp.Show:
484:0:str) -> exp.Expr:
488:0:
512:0:
554:0:
573:0:
sqlglot/parsers/mysql.py:55:NO_PAREN_FUNCTIONS = {
sqlglot/parsers/mysql.py:61:ID_VAR_TOKENS = parser.Parser.ID_VAR_TOKENS - {TokenType.STRAIGHT_JOIN}
sqlglot/parsers/mysql.py:63:FUNC_TOKENS = {
sqlglot/parsers/mysql.py:72:CONJUNCTION = {
sqlglot/parsers/mysql.py:78:DISJUNCTION = {
sqlglot/parsers/mysql.py:83:TABLE_ALIAS_
…[1167 chars elided]…
 NOT NULL, c VARCHAR(1000)...
tests/dialects/test_mysql.py:142:...fo (a BIGINT(20) NOT NULL AUTO_INCREMENT, b BIGINT(20) NOT NULL, c VARCHAR(1000)...
tests/dialects/test_mysql.py:180:...E z (a INT) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARACTER SET=utf8 COLLATE=ut...
tests/dialects/test_mysql.py:183:...E z (a INT) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARACTER SET=utf8 COLLATE=ut...
tests/dialects/test_mysql.py:191:"mysql": "CREATE TABLE x (id INT NOT NULL AUTO_INCREMENT, PRIMARY KEY (id))",
[tool_use Bash] {"command": "sed -n 250,262p sqlglot/parsers/mysql.py; rg -n \"def test_ddl|ALTER TABLE\" tests/dialects/test_mysql.py | head -20", "description": "View MySQL ALTER_PARSERS and related tests"}
[tool_result]         "INVISIBLE": lambda self: self.expression(exp.InvisibleColumnConstraint()),
    }

    ALTER_PARSERS = {
        **parser.Parser.ALTER_PARSERS,
        "MODIFY": lambda self: self._parse_alter_table_alter(),
    }

    ALTER_ALTER_PARSERS = {
        **parser.Parser.ALTER_ALTER_PARSERS,
        "INDEX": lambda self: self._parse_alter_table_alter_index(),
    }

19 matches in 2 files:

12:0:
tests/dialects/test_mysql.py:32:self.validate_identity("ALTER TABLE t ADD COLUMN c INT INVISIBLE")
…[989 chars elided]…
_identity("ALTER TABLE t ALTER COLUMN c SET INVISIBLE")
tests/dialects/test_mysql.py:198:self.validate_identity("ALTER TABLE t ALTER COLUMN c SET VISIBLE")
tests/dialects/test_mysql.py:199:self.validate_identity("ALTER TABLE t RENAME INDEX a TO b")
tests/dialects/test_mysql.py:201:"ALTER TABLE t RENAME KEY a TO b",
tests/dialects/test_mysql.py:202:"ALTER TABLE t RENAME INDEX a TO b",
tests/dialects/test_mysql.py:241:self.validate_identity("ALTER TABLE test_table ALTER COLUMN test_column SET D...
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-173953-mysql-dialect-mysql-allows-setti/base-1/sqlglot/parsers/mysql.py", "old_string": "        \"MODIFY\": lambda self: self._parse_alter_table_alter(),\n    }", "new_string": "        \"AUTO_INCREMENT\": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),\n        \"MODIFY\": lambda self: self._parse_alter_table_alter(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-173953-mysql-dialect-mysql-allows-setti/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t AUTO_INCREMENT=3000000000','ALTER TABLE t AUTO_INCREMENT 5','ALTER TABLE \\`t\\` AUTO_INCREMENT=1, ALGORITHM=INPLACE','ALTER TABLE db.t AUTO_INCREMENT = 7']:\n    e=sqlglot.parse_one(s,read='mysql'); print(type(e).__name__, repr(e.args.get('actions'))[:200]); print(e.sql('mysql'))\n\"", "description": "Verify new MySQL ALTER AUTO_INCREMENT parsing"}
[tool_result] 'ALTER TABLE `t` AUTO_INCREMENT=1, ALGORITHM=INPLACE' contains unsupported syntax. Falling back to parsing as a 'Command'.
Alter [AutoIncrementProperty(
  this=Literal(this=3000000000, is_string=False))]
ALTER TABLE t AUTO_INCREMENT=3000000000
Alter [AutoIncrementProperty(
  this=Literal(this=5, is_string=False))]
ALTER TABLE t AUTO_INCREMENT=5
Command None
ALTER TABLE `t` AUTO_INCREMENT=1, ALGORITHM=INPLACE
Alter [AutoIncrementProperty(
  this=Literal(this=7, is_string=False))]
ALTER TABLE db.t AUTO_INCREMENT=7
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t ADD COLUMN c INT, ALGORITHM=INPLACE','ALTER TABLE t MODIFY COLUMN c INT, ALGORITHM=INPLACE','ALTER TABLE t AUTO_INCREMENT=1, ALGORITHM=INPLACE','ALTER TABLE t AUTO_INCREMENT=1, LOCK=NONE']:\n    e=sqlglot.parse_one(s,read='mysql'); print(type(e).__name__, e.sql('mysql'))\n\" 2>&1; git stash list | head -2 >/dev/null; $P -c \"\nimport sqlglot\nprint(sqlglot.parse_one('ALTER TABLE t ADD COLUMN c INT, ALGORITHM=INPLACE',read='mysql').sql('mysql'))\n\"", "description": "Check multi-option ALTER behavior"}
[tool_result] 'ALTER TABLE t MODIFY COLUMN c INT, ALGORITHM=INPLACE' contains unsupported syntax. Falling back to parsing as a 'Command'.
'ALTER TABLE t AUTO_INCREMENT=1, ALGORITHM=INPLACE' contains unsupported syntax. Falling back to parsing as a 'Command'.
'ALTER TABLE t AUTO_INCREMENT=1, LOCK=NONE' contains unsupported syntax. Falling back to parsing as a 'Command'.
Alter ALTER TABLE t ADD COLUMN c INT, ALGORITHM=INPLACE
Command ALTER TABLE t MODIFY COLUMN c INT, ALGORITHM=INPLACE
Command ALTER TABLE t AUTO_INCREMENT=1, ALGORITHM=INPLACE
Command ALTER TABLE t AUTO_INCREMENT=1, LOCK=NONE
ALTER TABLE t ADD COLUMN c INT, ALGORITHM=INPLACE
[tool_use Bash] {"command": "sed -n 28,40p tests/dialects/test_mysql.py; sed -n 192,206p tests/dialects/test_mysql.py", "description": "View MySQL ALTER test sections"}
[tool_result]         self.validate_identity("CREATE TABLE foo (a BIGINT, FULLTEXT INDEX (b))")
        self.validate_identity("CREATE TABLE foo (a BIGINT, SPATIAL INDEX (b))")
        self.validate_identity("CREATE TABLE foo (a INT UNSIGNED ZEROFILL)")
        self.validate_identity("CREATE TABLE foo (a INT INVISIBLE)")
        self.validate_identity("ALTER TABLE t ADD COLUMN c INT INVISIBLE")
        self.validate_identity("ALTER TABLE t1 ADD COLUMN x INT, ALGORITHM=INPLACE, LOCK=EXCLUSIVE")
        self.va
…[739 chars elided]…
 INDEX i VISIBLE")
        self.validate_identity("ALTER TABLE t ALTER COLUMN c SET INVISIBLE")
        self.validate_identity("ALTER TABLE t ALTER COLUMN c SET VISIBLE")
        self.validate_identity("ALTER TABLE t RENAME INDEX a TO b")
        self.validate_identity(
            "ALTER TABLE t RENAME KEY a TO b",
            "ALTER TABLE t RENAME INDEX a TO b",
        )
        self.validate_identity(
            "UPDATE foo JOIN bar ON TRUE SET foo.a = bar.a WHERE foo.id = bar.id"
        )
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-173953-mysql-dialect-mysql-allows-setti/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"ALTER TABLE t RENAME INDEX a TO b\")\n        self.validate_identity(\n            \"ALTER TABLE t RENAME KEY a TO b\",", "new_string": "        self.validate_identity(\"ALTER TABLE t AUTO_INCREMENT=3000000000\")\n        self.validate_identity(\n            \"ALTER TABLE t AUTO_INCREMENT 5\",\n            \"ALTER TABLE t AUTO_INCREMENT=5\",\n        )\n        self.validate_identity(\"ALTER TABLE t RENAME INDEX a TO b\")\n        self.validate_identity(\n            \"ALTER TABLE t RENAME KEY a TO b\","}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-173953-mysql-dialect-mysql-allows-setti/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite"}
[tool_result] ................................................................................. [  7%]
............................................. [ 11%]
...................................................... [ 16%]
........ [ 17%]
................................. [ 20%]
...............................................................................................................................................................................................................................................
…[240 chars elided]…
...................................................................... [ 68%]
............................................... [ 73%]
.................................................................................................................................................................................................. [ 90%]
............................... [ 93%]
....................................................................       [100%]
1086 passed, 17844 subtests passed in 46.87s
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; (rg -n \"^style\" -A4 Makefile); $P -m ruff check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py 2>&1 | tail -3; $P -m ruff format --check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py 2>&1 | tail -3; git status --short", "description": "Run ruff lint and format checks on changed files"}
[tool_result] 80:style:
81-	pre-commit run --all-files
82-	@if [ -f sqlglot-integration-tests/Makefile ]; then $(MAKE) -C sqlglot-integration-tests check-submodule; fi
83-
84-check: style test testc
All checks passed!
2 files already formatted
 M sqlglot/parsers/mysql.py
 M tests/dialects/test_mysql.py
[assistant] MySQL `ALTER TABLE t AUTO_INCREMENT=...` now parses as the same `AutoIncrementProperty` that `CREATE TABLE` uses, and round-trips. The full suite passes (1086 tests) and ruff is clean on the changed files.

**Change:** I added one entry to `MySQLParser.ALTER_PARSERS` in `sqlglot/parsers/mysql.py`:

```python
"AUTO_INCREMENT": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),
```

Before this, the statement fell back to a raw `Command`. Now `ALTER TABLE t AUTO_INCREMENT=3000000000` produces an `Alter` whose action is an `AutoIncrementProperty`, and it generates back as `A
…[119 chars elided]…
as it does in `CREATE TABLE`.

**Tests:** I added two cases to the existing ALTER section of `tests/dialects/test_mysql.py`: the round-trip for `AUTO_INCREMENT=3000000000` and the normalization for `AUTO_INCREMENT 5`.

**Not covered:** A comma-joined option after the counter, such as `ALTER TABLE t AUTO_INCREMENT=1, ALGORITHM=INPLACE`, still falls back to `Command`. `ALTER TABLE t MODIFY COLUMN c INT, ALGORITHM=INPLACE` already behaves the same way, so this is a pre-existing limit of the comma-option handling, and I left it alone.

I haven't committed. The changes are in the working tree only.
