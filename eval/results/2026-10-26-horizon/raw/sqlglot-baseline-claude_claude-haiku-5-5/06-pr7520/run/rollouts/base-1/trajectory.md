# trajectory base-1

final message:
`ALTER TABLE t AUTO_INCREMENT=3000000000` now parses as an `Alter` whose action is the same `AutoIncrementProperty` that `CREATE TABLE` uses, and it round-trips. The full suite passes (1086 tests) and ruff is clean.

**The change**
- `sqlglot/parsers/mysql.py`: added `"AUTO_INCREMENT"` to the MySQL `ALTER_PARSERS`, using `_parse_property_assignment(exp.AutoIncrementProperty)`. This is the same helper the `CREATE TABLE` property already uses, so the `=` is optional, as in `ALTER TABLE t AUTO_INCREMENT 5`.
- `tests/dialects/test_mysql.py`: added a `validate_identity` round-trip for `ALTER TABLE t AUTO_INCREMENT=3000000000` next to the other MySQL ALTER identities.

I scoped it to the MySQL parser rather than the base parser, since the request was MySQL-specific.

**Known gap:** `ALTER TABLE t AUTO_INCREMENT=1, ALGORITHM=INPLACE` still falls back to a `Command`. The ALTER option list starts at the current token, so the leading comma after a single action isn't consumed. Fixing that means touching the shared ALTER option handling, which felt beyond this change, so I left it. Say if you want it included.

Changes are uncommitted, since you didn't ask for a commit.

## events
[tool_use Bash] {"command": "rg -n -i \"autoincrement|auto_increment\" sqlglot/ | head -50; echo ---; rg -n \"def _parse_alter_table|ALTER_PARSERS|def _parse_alter\\b|AlterTable|def alter_sql|def altertable\" sqlglot/parser.py sqlglot/generator.py sqlglot/dialects/mysql.py sqlglot/expressions.py | head -40", "description": "Search auto-increment and ALTER TABLE code"}
[tool_result] sqlglot/tokens.py:238:        "AUTOINCREMENT": TokenType.AUTO_INCREMENT,
sqlglot/tokens.py:239:        "AUTO_INCREMENT": TokenType.AUTO_INCREMENT,
sqlglot/tokenizer_core.py:247:    AUTO_INCREMENT = auto()
sqlglot/parser.py:660:        TokenType.AUTO_INCREMENT,
sqlglot/parser.py:1217:        "AUTO_INCREMENT": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),
sqlglot/parser.py:1327:        "AUTOINCREMENT": lambda self: self._parse_auto_increment(),
sqlglot/parser.py:1328:   
…[3649 chars elided]…
ALTER_PARSERS[self._prev.text.upper()](self)
sqlglot/parser.py:8594:    def _parse_alter_table_drop(self) -> list[exp.Expr]:
sqlglot/parser.py:8604:    def _parse_alter_table_rename(self) -> exp.AlterRename | exp.RenameColumn | None:
sqlglot/parser.py:8619:    def _parse_alter_table_set(self) -> exp.AlterSet:
sqlglot/parser.py:8667:    def _parse_alter(self) -> exp.Alter | exp.Command:
sqlglot/parser.py:8693:        parser = self.ALTER_PARSERS.get(self._prev.text.upper()) if self._prev else None
[tool_use Bash] {"command": "sed -n 8660,8760p sqlglot/parser.py; echo ----; sed -n 3975,4010p sqlglot/generator.py; echo ----; rg -n \"AUTO_INCREMENT|AutoIncrement\" tests/dialects/test_mysql.py | head; rg -n \"ALTER_PARSERS: t.ClassVar\" -A 14 sqlglot/parser.py; rg -n \"_parse_alter_table_set|AlterSet\" -n sqlglot/parser.py | head", "description": "Read ALTER parsing and generation code"}
[tool_result]         self._match_text_seq("UNSET")
        expressions = self._parse_csv(
            lambda: self.expression(exp.SetItem(this=self._parse_id_var(any_token=True)))
        )
        return self.expression(exp.AlterSession(expressions=expressions, unset=True))

    def _parse_alter(self) -> exp.Alter | exp.Command:
        start = self._prev

        iceberg = self._match_text_seq("ICEBERG")

        alter_token = self._match_set(self.ALTERABLES) and self._prev
        if not alter_token:
    
…[7604 chars elided]…
),
1438-        "COMPOUND": lambda self: self._parse_alter_sortkey(compound=True),
1439-    }
1440-
1441-    SCHEMA_UNNAMED_CONSTRAINTS: t.ClassVar = {
1442-        "CHECK",
1443-        "EXCLUDE",
1444-        "FOREIGN KEY",
1445-        "LIKE",
1446-        "PERIOD",
1447-        "PRIMARY KEY",
1448-        "UNIQUE",
1428:        "SET": lambda self: self._parse_alter_table_set(),
8619:    def _parse_alter_table_set(self) -> exp.AlterSet:
8620:        alter_set = self.expression(exp.AlterSet())
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t AUTO_INCREMENT=3000000000','ALTER TABLE t AUTO_INCREMENT 5']:\n    e=sqlglot.parse_one(s,read='mysql'); print(type(e).__name__, repr(e)[:300]); print(e.sql('mysql'))\n\"; rg -n \"def _parse_property_assignment\" -A 12 sqlglot/parser.py; rg -n \"def property_sql\" -A 12 sqlglot/generator.py | head -30", "description": "Check current parse of ALTER AUTO_INCREMENT"}
[tool_result] 'ALTER TABLE t AUTO_INCREMENT=3000000000' contains unsupported syntax. Falling back to parsing as a 'Command'.
'ALTER TABLE t AUTO_INCREMENT 5' contains unsupported syntax. Falling back to parsing as a 'Command'.
Command Command(this=ALTER, expression=TABLE t AUTO_INCREMENT=3000000000)
ALTER TABLE t AUTO_INCREMENT=3000000000
Command Command(this=ALTER, expression=TABLE t AUTO_INCREMENT 5)
ALTER TABLE t AUTO_INCREMENT 5
2790:    def _parse_property_assignment(self, exp_class: type[E], **kwargs: t
…[665 chars elided]…
80-            return f"{self.property_name(expression)}={self.sql(expression, 'value')}"
1981-
1982-        property_name = exp.Properties.PROPERTY_TO_NAME.get(property_cls)
1983-        if not property_name:
1984-            self.unsupported(f"Unsupported property {expression.key}")
1985-
1986-        return f"{property_name}={self.sql(expression, 'this')}"
1987-
1988-    def uuidproperty_sql(self, expression: exp.UuidProperty) -> str:
1989-        return f"UUID {self.sql(expression, 'this')}"
[tool_use Bash] {"command": "rg -n \"class Parser|ALTER|_PARSERS|PROPERTY_PARSERS\" sqlglot/dialects/mysql.py | head -40; rg -n \"ALTER TABLE .* (ADD|RENAME|MODIFY)\" tests/dialects/test_mysql.py | head -5", "description": "Inspect MySQL parser class structure"}
[tool_result] 32:        self.validate_identity("ALTER TABLE t ADD COLUMN c INT INVISIBLE")
33:        self.validate_identity("ALTER TABLE t1 ADD COLUMN x INT, ALGORITHM=INPLACE, LOCK=EXCLUSIVE")
34:        self.validate_identity("ALTER TABLE t ADD INDEX `i` (`c`)")
35:        self.validate_identity("ALTER TABLE t ADD UNIQUE `i` (`c`)")
36:        self.validate_identity("ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT")
[tool_use Bash] {"command": "ls sqlglot/dialects/ | grep -i mysql; rg -n \"class Parser|ALTER_PARSERS|PROPERTY_PARSERS\" sqlglot/parsers/mysql.py sqlglot/dialects/mysql.py 2>/dev/null | head; rg -ln \"class MySQL\" sqlglot | head; sed -n 25,40p tests/dialects/test_mysql.py", "description": "Locate MySQL parser module and test layout"}
[tool_result] mysql.py
sqlglot/parsers/mysql.py:225:    PROPERTY_PARSERS = {
sqlglot/parsers/mysql.py:226:        **parser.Parser.PROPERTY_PARSERS,
sqlglot/parsers/mysql.py:253:    ALTER_PARSERS = {
sqlglot/parsers/mysql.py:254:        **parser.Parser.ALTER_PARSERS,
sqlglot/parsers/mysql.py:258:    ALTER_ALTER_PARSERS = {
sqlglot/parsers/mysql.py:259:        **parser.Parser.ALTER_ALTER_PARSERS,
sqlglot/generators/mysql.py
sqlglot/dialects/mysql.py
sqlglot/parsers/mysql.py
        self.validate_identity("DELET
…[707 chars elided]…
validate_identity("ALTER TABLE t ADD INDEX `i` (`c`)")
        self.validate_identity("ALTER TABLE t ADD UNIQUE `i` (`c`)")
        self.validate_identity("ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT")
        self.validate_identity("ALTER VIEW v AS SELECT a, b, c, d FROM foo")
        self.validate_identity("ALTER VIEW v AS SELECT * FROM foo WHERE c > 100")
        self.validate_identity(
            "ALTER ALGORITHM = MERGE VIEW v AS SELECT * FROM foo", check_command_warning=True
[tool_use Bash] {"command": "sed -n 220,275p sqlglot/parsers/mysql.py", "description": "Read MySQL parser property and ALTER maps"}
[tool_result]         "SESSION VARIABLES": _show_parser("VARIABLES"),
        "VARIABLES": _show_parser("VARIABLES"),
        "WARNINGS": _show_parser("WARNINGS"),
    }

    PROPERTY_PARSERS = {
        **parser.Parser.PROPERTY_PARSERS,
        "LOCK": lambda self: self._parse_property_assignment(exp.LockProperty),
        "PARTITION BY": lambda self: self._parse_partition_property(),
    }

    SET_PARSERS = {
        **parser.Parser.SET_PARSERS,
        "PERSIST": lambda self: self._parse_set_item_assignme
…[1147 chars elided]…
      **parser.Parser.ALTER_ALTER_PARSERS,
        "INDEX": lambda self: self._parse_alter_table_alter_index(),
    }

    SCHEMA_UNNAMED_CONSTRAINTS = {
        *parser.Parser.SCHEMA_UNNAMED_CONSTRAINTS,
        "FULLTEXT",
        "INDEX",
        "KEY",
        "SPATIAL",
    }

    PROFILE_TYPES: parser.OPTIONS_TYPE = {
        **dict.fromkeys(("ALL", "CPU", "IPC", "MEMORY", "SOURCE", "SWAPS"), tuple()),
        "BLOCK": ("IO",),
        "CONTEXT": ("SWITCHES",),
        "PAGE": ("FAULTS",),
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-134041-mysql-dialect-mysql-allows-setti/base-1/sqlglot/parsers/mysql.py", "old_string": "        \"MODIFY\": lambda self: self._parse_alter_table_alter(),\n    }", "new_string": "        \"AUTO_INCREMENT\": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),\n        \"MODIFY\": lambda self: self._parse_alter_table_alter(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-134041-mysql-dialect-mysql-allows-setti/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[assistant] Now a test in the MySQL dialect file, next to the other ALTER identities.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-134041-mysql-dialect-mysql-allows-setti/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT\")\n", "new_string": "        self.validate_identity(\"ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT\")\n        self.validate_identity(\"ALTER TABLE t AUTO_INCREMENT=3000000000\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-134041-mysql-dialect-mysql-allows-setti/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t AUTO_INCREMENT=3000000000','ALTER TABLE t AUTO_INCREMENT 5', 'ALTER TABLE t AUTO_INCREMENT=1, ALGORITHM=INPLACE']:\n    e=sqlglot.parse_one(s,read='mysql'); print(type(e).__name__, repr(e.args.get('actions'))); print(e.sql('mysql'))\n\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -15", "description": "Verify parse output and run MySQL tests"}
[tool_result] 'ALTER TABLE t AUTO_INCREMENT=1, ALGORITHM=INPLACE' contains unsupported syntax. Falling back to parsing as a 'Command'.
Alter [AutoIncrementProperty(
  this=Literal(this=3000000000, is_string=False))]
ALTER TABLE t AUTO_INCREMENT=3000000000
Alter [AutoIncrementProperty(
  this=Literal(this=5, is_string=False))]
ALTER TABLE t AUTO_INCREMENT=5
Command None
ALTER TABLE t AUTO_INCREMENT=1, ALGORITHM=INPLACE
.............................. [ 61%]
...................                                               [100%]
49 passed, 481 subtests passed in 0.31s
[assistant] The change works for the single-action form. The combined form `AUTO_INCREMENT=1, ALGORITHM=INPLACE` still falls back to a Command; I'll note that below. Now the full suite and style checks.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; $PY -m ruff check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py 2>&1 | tail -3; $PY -m ruff format --check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py 2>&1 | tail -3; git status --short", "description": "Run full test suite and ruff checks"}
[tool_result] ............................................... [ 73%]
.................................................................................................................................................................................................. [ 90%]
............................... [ 93%]
....................................................................       [100%]
1086 passed, 17844 subtests passed in 56.02s
All checks passed!
2 files already formatted
 M sqlglot/parsers/mysql.py
 M tests/dialects/test_mysql.py
[assistant] `ALTER TABLE t AUTO_INCREMENT=3000000000` now parses as an `Alter` whose action is the same `AutoIncrementProperty` that `CREATE TABLE` uses, and it round-trips. The full suite passes (1086 tests) and ruff is clean.

**The change**
- `sqlglot/parsers/mysql.py`: added `"AUTO_INCREMENT"` to the MySQL `ALTER_PARSERS`, using `_parse_property_assignment(exp.AutoIncrementProperty)`. This is the same helper the `CREATE TABLE` property already uses, so the `=` is optional, as in `ALTER TABLE t AUTO_INCREMENT 5`.
- `tests/dialects/test_mysql.py`: added a `validate_identity` round-trip for `ALTER TABLE t AUTO_INCREMENT=3000000000` next to the other MySQL ALTER identities.

I scoped it to the MySQL parser rather than the base parser, since the request was MySQL-specific.

**Known gap:** `ALTER TABLE t AUTO_INCREMENT=1, ALGORITHM=INPLACE` still falls back to a `Command`. The ALTER option list starts at the current token, so the leading comma after a single action isn't consumed. Fixing that means touching the shared ALTER option handling, which felt beyond this change, so I left it. Say if you want it included.

Changes are uncommitted, since you didn't ask for a commit.
