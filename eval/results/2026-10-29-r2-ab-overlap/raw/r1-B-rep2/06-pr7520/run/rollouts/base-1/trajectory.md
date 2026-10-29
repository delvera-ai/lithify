# trajectory base-1

final message:
`ALTER TABLE t AUTO_INCREMENT=3000000000` now parses as an `Alter` action and round-trips unchanged. Before this change it fell back to a raw `Command`.

The change is one line in `sqlglot/parsers/mysql.py`: an `AUTO_INCREMENT` entry in the MySQL `ALTER_PARSERS` that calls `_parse_property_assignment(exp.AutoIncrementProperty)`. That's the same node `CREATE TABLE` produces, so the action prints as `AUTO_INCREMENT=<value>`. I added it to the MySQL parser rather than the base parser, so other dialects are unaffected.

I added one round-trip assertion to the existing ALTER block in `tests/dialects/test_mysql.py`.

Verification:
- Full suite: 1086 passed, 17844 subtests passed.
- `ruff format --check` and `ruff check` pass on both files.

The changes are uncommitted in the worktree. I haven't committed or opened a PR since you didn't ask for one.

## events
[tool_use Bash] {"command": "grep -rn -i \"autoincrement\\|auto_increment\" sqlglot/ tests/dialects/test_mysql.py | head -60; echo ---; grep -n \"def _parse_alter_table_alter\\|def _parse_alter\\b\\|ALTER_PARSERS\\|def _parse_alter_table_\" sqlglot/parser.py sqlglot/dialects/mysql.py | head -30", "description": "Find AUTO_INCREMENT and ALTER parsing code"}
[tool_result] sqlglot/tokens.py:238:        "AUTOINCREMENT": TokenType.AUTO_INCREMENT,
sqlglot/tokens.py:239:        "AUTO_INCREMENT": TokenType.AUTO_INCREMENT,
sqlglot/tokenizer_core.py:247:    AUTO_INCREMENT = auto()
sqlglot/parser.py:660:        TokenType.AUTO_INCREMENT,
sqlglot/parser.py:1217:        "AUTO_INCREMENT": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),
sqlglot/parser.py:1327:        "AUTOINCREMENT": lambda self: self._parse_auto_increment(),
sqlglot/parser.py:1328:   
…[5679 chars elided]…
y:8539:return self.ALTER_ALTER_PARSERS[self._prev.text.upper()](self)
sqlglot/parser.py:8594:def _parse_alter_table_drop(self) -> list[exp.Expr]:
sqlglot/parser.py:8604:def _parse_alter_table_rename(self) -> exp.AlterRename | exp.RenameColumn | N...
sqlglot/parser.py:8619:def _parse_alter_table_set(self) -> exp.AlterSet:
sqlglot/parser.py:8667:def _parse_alter(self) -> exp.Alter | exp.Command:
sqlglot/parser.py:8693:parser = self.ALTER_PARSERS.get(self._prev.text.upper()) if self._prev else None
[tool_use Bash] {"command": "sed -n 1415,1450p sqlglot/parser.py; echo ---; sed -n 8660,8720p sqlglot/parser.py; echo ---; sed -n 1205,1225p sqlglot/parser.py; echo ---; sed -n 35,50p sqlglot/expressions/properties.py; echo ---; grep -n \"_parse_property_assignment\" sqlglot/parser.py | head -3; echo ---; grep -n \"ALTER\\|alter\" sqlglot/dialects/mysql.py | head; echo ---; grep -n \"def alter_sql\\|def altertable\\|AlterTable\\|def _parse_alter_table_alter\" sqlglot/generator.py | head", "description": "Inspect ALTER parser and property handling"}
[tool_result]             # Trino ref: https://docs.aws.amazon.com/athena/latest/ug/create-table-as.html#ctas-table-properties
            this, expression = expression, this

        return self.expression(klass(this=this, expression=expression))

    ALTER_PARSERS: t.ClassVar = {
        "ADD": lambda self: self._parse_alter_table_add(),
        "AS": lambda self: self._parse_select(),
        "ALTER": lambda self: self._parse_alter_table_alter(),
        "CLUSTER BY": lambda self: self._parse_cluster(wrapp
…[4519 chars elided]…
BY": lambda self: self._parse_cluster(),
---

class ApplicationProperty(Property):
    arg_types = {}


class AutoIncrementProperty(Property):
    arg_types = {"this": True}


class AutoRefreshProperty(Property):
    arg_types = {"this": True}


class BackupProperty(Property):
    arg_types = {"this": True}

---
15 matches in 15 files:

1215:0:lambda self: self._parse_property_assignment(exp.AlgorithmProperty),
---
0 matches for 'ALTER\|alter'
---
1 matches in 1 files:

3975:0:exp.Alter) -> str:
[tool_use Bash] {"command": "grep -n \"def _parse_property_assignment\" -A8 sqlglot/parser.py; echo ---; sed -n 3970,4010p sqlglot/generator.py; echo ---; grep -n \"def property_sql\" -A12 sqlglot/generator.py; echo ---; grep -n \"ALTER_PARSERS\\|ALTER_ALTER\" sqlglot/dialects/*.py sqlglot/parsers/*.py 2>/dev/null | head; echo ---; grep -n \"ALTER TABLE\" tests/dialects/test_mysql.py | head -30", "description": "Inspect property assignment, alter generator, mysql alter tests"}
[tool_result] 2790:    def _parse_property_assignment(self, exp_class: type[E], **kwargs: t.Any) -> E:
2791-        self._match(TokenType.EQ)
2792-        self._match(TokenType.ALIAS)
2793-
2794-        return self.expression(exp_class(this=self._parse_unquoted_field(), **kwargs))
2795-
2796-    def _parse_properties(self, before: bool | None = None) -> exp.Properties | None:
2797-        properties = []
2798-        while True:
---
        if self.ALTER_SET_WRAPPED:
            exprs = f"({exprs})"

        
…[3982 chars elided]…
identity("ALTER TABLE t ALTER COLUMN c SET VISIBLE")
tests/dialects/test_mysql.py:199:self.validate_identity("ALTER TABLE t RENAME INDEX a TO b")
tests/dialects/test_mysql.py:201:"ALTER TABLE t RENAME KEY a TO b",
tests/dialects/test_mysql.py:202:"ALTER TABLE t RENAME INDEX a TO b",
tests/dialects/test_mysql.py:241:self.validate_identity("ALTER TABLE test_table ALTER COLUMN test_column SET DEFA...
tests/dialects/test_mysql.py:1695:expr = self.parse_one("ALTER TABLE t ADD COLUMN c INT INVISIBLE")
[tool_use Bash] {"command": "sed -n 240,275p sqlglot/parsers/mysql.py; echo ---; sed -n 1,30p sqlglot/parsers/mysql.py | grep -n import; echo ---; sed -n 190,210p tests/dialects/test_mysql.py; echo ---; grep -n \"ALGORITHM\\|LOCK=\" tests/dialects/test_mysql.py | head; echo; ls <work>/env-sqlglot/bin/python && git log --oneline -1 -- sqlglot/parsers/mysql.py", "description": "View MySQL ALTER parsers and related tests"}
[tool_result]     SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
    SET_TRIE = new_trie(key.split(" ") for key in SET_PARSERS)

    CONSTRAINT_PARSERS = {
        **parser.Parser.CONSTRAINT_PARSERS,
        "FULLTEXT": lambda self: self._parse_index_constraint(kind="FULLTEXT"),
        "INDEX": lambda self: self._parse_index_constraint(),
        "KEY": lambda self: self._parse_index_constraint(),
        "SPATIAL": lambda self: self._parse_index_constraint(kind="SPATIAL"),
        "ZEROFILL": 
…[2189 chars elided]…
VALUE))"
---
2 matches in 1 files:

tests/dialects/test_mysql.py:33:self.validate_identity("ALTER TABLE t1 ADD COLUMN x INT, ALGORITHM=INPLACE, L...
tests/dialects/test_mysql.py:40:"ALTER ALGORITHM = MERGE VIEW v AS SELECT * FROM foo", check_command_warning=...

<work>/env-sqlglot/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12  84B
cb91d9142 Feat(mysql): support `ALTER TABLE ... RENAME INDEX`. (#7511)
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t AUTO_INCREMENT=3000000000','ALTER TABLE t AUTO_INCREMENT 5']:\n    e=sqlglot.parse_one(s,read='mysql'); print(type(e).__name__, repr(e.sql('mysql')), e.args.get('actions'))\n\" 2>&1 | tail -5", "description": "Check current parse of ALTER AUTO_INCREMENT"}
[tool_result] 'ALTER TABLE t AUTO_INCREMENT=3000000000' contains unsupported syntax. Falling back to parsing as a 'Command'.
'ALTER TABLE t AUTO_INCREMENT 5' contains unsupported syntax. Falling back to parsing as a 'Command'.
Command 'ALTER TABLE t AUTO_INCREMENT=3000000000' None
Command 'ALTER TABLE t AUTO_INCREMENT 5' None
[assistant] Confirmed: it currently falls back to a `Command`. I'll add an `AUTO_INCREMENT` entry to the MySQL `ALTER_PARSERS`, reusing the same `AutoIncrementProperty` that `CREATE TABLE` uses.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-134557-mysql-dialect-mysql-allows-setti/base-1/sqlglot/parsers/mysql.py", "old_string": "        \"MODIFY\": lambda self: self._parse_alter_table_alter(),\n    }", "new_string": "        \"AUTO_INCREMENT\": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),\n        \"MODIFY\": lambda self: self._parse_alter_table_alter(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-134557-mysql-dialect-mysql-allows-setti/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[assistant] Now a test in the existing ALTER block of the MySQL tests, next to the `RENAME INDEX` cases:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-134557-mysql-dialect-mysql-allows-setti/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"ALTER TABLE t RENAME INDEX a TO b\")\n        self.validate_identity(\n            \"ALTER TABLE t RENAME KEY a TO b\",", "new_string": "        self.validate_identity(\"ALTER TABLE t RENAME INDEX a TO b\")\n        self.validate_identity(\"ALTER TABLE t AUTO_INCREMENT=3000000000\")\n        self.validate_identity(\n            \"ALTER TABLE t RENAME KEY a TO b\","}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-134557-mysql-dialect-mysql-allows-setti/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\ne=sqlglot.parse_one('ALTER TABLE t AUTO_INCREMENT=3000000000',read='mysql')\nprint(type(e).__name__, e.args['actions'], e.sql('mysql'), e.sql('mysql')==  'ALTER TABLE t AUTO_INCREMENT=3000000000')\nprint(sqlglot.transpile('ALTER TABLE t AUTO_INCREMENT=5', read='mysql', write='duckdb'))\n\" 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py tests/test_transpile.py tests/test_parser.py 2>&1 | tail -5", "description": "Verify AST and run MySQL and parser test suites"}
[tool_result] Alter [AutoIncrementProperty(
  this=Literal(this=3000000000, is_string=False))] ALTER TABLE t AUTO_INCREMENT=3000000000 True
['ALTER TABLE t AUTO_INCREMENT=5']
.............................. [ 21%]
.................................................................................... [ 80%]
...........................              [100%]
141 passed, 1574 subtests passed in 9.91s
[assistant] Targeted tests pass. Running the full suite with the project's checker, plus ruff on the changed files:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py 2>&1 | tail -2; <work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py 2>&1 | tail -2; git diff --stat", "description": "Run full test suite and lint checks"}
[tool_result] .................................................................................................................................................................................................. [ 90%]
............................... [ 93%]
....................................................................       [100%]
1086 passed, 17844 subtests passed in 49.66s
2 files already formatted
All checks passed!
sqlglot/parsers/mysql.py     | 1 +
 tests/dialects/test_mysql.py | 1 +
 2 files changed, 2 insertions(+)
[assistant] `ALTER TABLE t AUTO_INCREMENT=3000000000` now parses as an `Alter` action and round-trips unchanged. Before this change it fell back to a raw `Command`.

The change is one line in `sqlglot/parsers/mysql.py`: an `AUTO_INCREMENT` entry in the MySQL `ALTER_PARSERS` that calls `_parse_property_assignment(exp.AutoIncrementProperty)`. That's the same node `CREATE TABLE` produces, so the action prints as `AUTO_INCREMENT=<value>`. I added it to the MySQL parser rather than the base parser, so other dialects are unaffected.

I added one round-trip assertion to the existing ALTER block in `tests/dialects/test_mysql.py`.

Verification:
- Full suite: 1086 passed, 17844 subtests passed.
- `ruff format --check` and `ruff check` pass on both files.

The changes are uncommitted in the worktree. I haven't committed or opened a PR since you didn't ask for one.
