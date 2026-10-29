# trajectory base-1

final message:
`ALTER TABLE t AUTO_INCREMENT=3000000000` now parses in the MySQL dialect as the same `AutoIncrementProperty` that `CREATE TABLE` uses, and round-trips back to MySQL unchanged.

The change is one line in `sqlglot/parsers/mysql.py`: `AUTO_INCREMENT` is added to the MySQL `ALTER_PARSERS`, using the same `_parse_property_assignment(exp.AutoIncrementProperty)` the CREATE TABLE path uses. No generator change was needed, since the existing property rendering already emits `AUTO_INCREMENT=<n>`. I also added two identity tests to `tests/dialects/test_mysql.py`: the `=` form, and the space-separated `AUTO_INCREMENT 5` form, which normalizes to `=5`.

Results: the full suite passes (1086 passed), and `ruff check` and `ruff format --check` are clean on both files. I didn't commit anything.

One gap I left alone: an AUTO_INCREMENT action combined with another action in one statement, e.g. `ALTER TABLE t AUTO_INCREMENT=1, ADD COLUMN c INT`, still falls back to a `Command`. Comma-separated `ADD` actions alone work fine, so this is specific to property-style actions being followed by a comma. Fixing it means changing how trailing ALTER options are parsed, which seemed out of scope for this request. Say if you want it handled.

## events
[tool_use Bash] {"command": "grep -rn -i \"autoincrement\\|auto_increment\" sqlglot/ tests/dialects/test_mysql.py | head -60", "description": "Find auto-increment references in sqlglot and tests"}
[tool_result] sqlglot/tokens.py:238:        "AUTOINCREMENT": TokenType.AUTO_INCREMENT,
sqlglot/tokens.py:239:        "AUTO_INCREMENT": TokenType.AUTO_INCREMENT,
sqlglot/tokenizer_core.py:247:    AUTO_INCREMENT = auto()
sqlglot/parser.py:660:        TokenType.AUTO_INCREMENT,
sqlglot/parser.py:1217:        "AUTO_INCREMENT": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),
sqlglot/parser.py:1327:        "AUTOINCREMENT": lambda self: self._parse_auto_increment(),
sqlglot/parser.py:1328:   
…[4798 chars elided]…
         "CREATE TABLE z (a INT DEFAULT NULL, PRIMARY KEY (a)) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARACTER SET=utf8 COLLATE=utf8_bin COMMENT='x'"
tests/dialects/test_mysql.py:1134:              `id` int(11) NOT NULL AUTO_INCREMENT,
tests/dialects/test_mysql.py:1139:            ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARACTER SET=utf8 COLLATE=utf8_bin COMMENT='客户账户表'
tests/dialects/test_mysql.py:1143:  `id` INT(11) NOT NULL AUTO_INCREMENT,
tests/dialects/test_mysql.py:1150:AUTO_INCREMENT=1
[tool_use Bash] {"command": "sed -n 1195,1230p sqlglot/parser.py && echo ---ALTER--- && grep -n \"_parse_alter_table\\|ALTER_PARSERS\\|def _parse_alter_table_add\\|_parse_alter_table_alter\\|\\\"RENAME\\\"\" sqlglot/parser.py | head -30 && echo ---MYSQL--- && grep -n -i \"alter\" sqlglot/dialects/mysql.py sqlglot/parsers/mysql.py sqlglot/generators/mysql.py 2>/dev/null | head -40", "description": "Inspect table property parsing and ALTER TABLE code"}
[tool_result]         "AS": lambda self, query: self._build_pipe_cte(
            query, [exp.Star()], self._parse_table_alias()
        ),
        "DISTINCT": lambda self, query: self._advance() or query.distinct(copy=False),
        "EXTEND": lambda self, query: self._parse_pipe_syntax_extend(query),
        "LIMIT": lambda self, query: self._parse_pipe_syntax_limit(query),
        "ORDER BY": lambda self, query: query.order_by(
            self._parse_order(), append=False, copy=False
        ),
        "P
…[3630 chars elided]…
ql.py:259:        **parser.Parser.ALTER_ALTER_PARSERS,
sqlglot/parsers/mysql.py:260:        "INDEX": lambda self: self._parse_alter_table_alter_index(),
sqlglot/parsers/mysql.py:304:    def _parse_alter_table_rename(self):
sqlglot/parsers/mysql.py:310:        return super()._parse_alter_table_rename()
sqlglot/parsers/mysql.py:512:    def _parse_alter_table_alter_index(self) -> exp.AlterIndex:
sqlglot/parsers/mysql.py:522:        return self.expression(exp.AlterIndex(this=index, visible=visible))
[tool_use Bash] {"command": "sed -n 1415,1440p sqlglot/parser.py && echo ---ALTERTBL--- && sed -n 8680,8730p sqlglot/parser.py && echo ---ALTERSET--- && sed -n 8619,8640p sqlglot/parser.py && echo ---MYSQLPARSER--- && sed -n 240,265p sqlglot/parsers/mysql.py && echo ---ALTERCLASS--- && grep -n \"class AlterTable\\|class AlterSet\" -A12 sqlglot/expressions/*.py | head -60 && echo ---PROPS--- && sed -n 1,80p sqlglot/generators/mysql.py | grep -n \"PROPERTIES\\|Location\" ; grep -n \"def alter_sql\\|def alterset_sql\\|def _parse_property_assignment\" -A3 sqlglot/generator.py sqlglot/parser.py | head -30", "description": "Inspect ALTER parsing, AlterSet, and property helpers"}
[tool_result]             # Trino ref: https://docs.aws.amazon.com/athena/latest/ug/create-table-as.html#ctas-table-properties
            this, expression = expression, this

        return self.expression(klass(this=this, expression=expression))

    ALTER_PARSERS: t.ClassVar = {
        "ADD": lambda self: self._parse_alter_table_add(),
        "AS": lambda self: self._parse_select(),
        "ALTER": lambda self: self._parse_alter_table_alter(),
        "CLUSTER BY": lambda self: self._parse_cluster(wrapp
…[6197 chars elided]…
er_sql(self, expression: exp.Alter) -> str:
sqlglot/generator.py-3976-        actions = expression.args["actions"]
sqlglot/generator.py-3977-
sqlglot/generator.py-3978-        if not self.dialect.ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN and isinstance(
sqlglot/parser.py:2790:    def _parse_property_assignment(self, exp_class: type[E], **kwargs: t.Any) -> E:
sqlglot/parser.py-2791-        self._match(TokenType.EQ)
sqlglot/parser.py-2792-        self._match(TokenType.ALIAS)
sqlglot/parser.py-2793-
[tool_use Bash] {"command": "sed -n 3975,4010p sqlglot/generator.py && echo ---PROP--- && sed -n 36,50p sqlglot/expressions/properties.py && echo ---PARSEASSIGN--- && sed -n 2790,2800p sqlglot/parser.py && echo ---MYSQLGEN--- && grep -n \"def property_sql\\|def _property_sql\\|def propertyassignment\\|PROPERTY\" sqlglot/generator.py | head; git log --oneline -3 -- tests/dialects/test_mysql.py | cat", "description": "Read alter_sql generator and property SQL helpers"}
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
…[2158 chars elided]…
TY_TO_NAME.get(property_cls)
1997:            if self.LIKE_PROPERTY_INSIDE_SCHEMA and not isinstance(expression.parent, exp.Schema):
3999:            if expression.args.get("iceberg") and self.SUPPORTS_DROP_ALTER_ICEBERG_PROPERTY
4420:        property_name = exp.Properties.PROPERTY_TO_NAME.get(expression.__class__)
cb91d9142 Feat(mysql): support `ALTER TABLE ... RENAME INDEX`. (#7511)
c1f929fa6 chore: Fix PR 7510 (#7513)
6678ee028 feat(mysql): Add `INVISIBLE` column constraint for MySQL. (#7510)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-164356-mysql-dialect-mysql-allows-setti/base-1/sqlglot/parsers/mysql.py", "old_string": "        \"MODIFY\": lambda self: self._parse_alter_table_alter(),\n    }", "new_string": "        \"MODIFY\": lambda self: self._parse_alter_table_alter(),\n        \"AUTO_INCREMENT\": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-164356-mysql-dialect-mysql-allows-setti/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t AUTO_INCREMENT=3000000000', 'ALTER TABLE t AUTO_INCREMENT 5', 'ALTER TABLE t AUTO_INCREMENT=1, ADD COLUMN c INT']:\n    e = sqlglot.parse_one(s, read='mysql')\n    print(type(e).__name__, repr(e.args.get('actions')[0].__class__.__name__ if e.args.get('actions') else None), e.sql('mysql'))\nprint(repr(sqlglot.parse_one('ALTER TABLE t AUTO_INCREMENT=3000000000', read='mysql')))\nprint(sqlglot.transpile('ALTER TABLE t AUTO_INCREMENT=3000000000', read='mysql', write='postgres'))\n\"", "description": "Check ALTER TABLE AUTO_INCREMENT parsing and round-trip"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t AUTO_INCREMENT=3000000000', 'ALTER TABLE t AUTO_INCREMENT 5', 'ALTER TABLE t AUTO_INCREMENT=1, ADD COLUMN c INT']:\n    e = sqlglot.parse_one(s, read='mysql')\n    print(type(e).__name__, e.sql('mysql'))\nprint(repr(sqlglot.parse_one('ALTER TABLE t AUTO_INCREMENT=3000000000', read='mysql')))\nprint(sqlglot.transpile('ALTER TABLE t AUTO_INCREMENT=3000000000', read='mysql', write='postgres'))\n\"", "description": "Check ALTER TABLE AUTO_INCREMENT parsing and round-trip"}
[tool_result] 'ALTER TABLE t AUTO_INCREMENT=1, ADD COLUMN c INT' contains unsupported syntax. Falling back to parsing as a 'Command'.
Alter ALTER TABLE t AUTO_INCREMENT=3000000000
Alter ALTER TABLE t AUTO_INCREMENT=5
Command ALTER TABLE t AUTO_INCREMENT=1, ADD COLUMN c INT
Alter(
  this=Table(
    this=Identifier(this=t, quoted=False)),
  kind=TABLE,
  exists=False,
  actions=[
    AutoIncrementProperty(
      this=Literal(this=3000000000, is_string=False))],
  only=False,
  not_valid=False,
  check=False,
  cascade=False,
  iceberg=False)
['ALTER TABLE t AUTO_INCREMENT=3000000000']
[assistant] The single-action forms parse and round-trip. The comma-combined form falls back to `Command`; I'll check whether that's a pre-existing limitation for other ALTER actions too.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(type(sqlglot.parse_one('ALTER TABLE t ADD COLUMN a INT, ADD COLUMN b INT', read='mysql')).__name__)\n\" ; grep -n \"ALTER TABLE\" tests/dialects/test_mysql.py | tail -15", "description": "Check pre-existing comma-separated ALTER behavior and test locations"}
[tool_result] Alter
35:        self.validate_identity("ALTER TABLE t ADD UNIQUE `i` (`c`)")
36:        self.validate_identity("ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT")
133:            "ALTER TABLE t ADD KEY `i` (`c`)",
134:            "ALTER TABLE t ADD INDEX `i` (`c`)",
149:            "ALTER TABLE test_table ALTER COLUMN test_column SET DATA TYPE LONGTEXT",
150:            "ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT",
195:        self.validate_identity("ALTER TABLE t ALTER 
…[108 chars elided]…
lf.validate_identity("ALTER TABLE t ALTER COLUMN c SET INVISIBLE")
198:        self.validate_identity("ALTER TABLE t ALTER COLUMN c SET VISIBLE")
199:        self.validate_identity("ALTER TABLE t RENAME INDEX a TO b")
201:            "ALTER TABLE t RENAME KEY a TO b",
202:            "ALTER TABLE t RENAME INDEX a TO b",
241:        self.validate_identity("ALTER TABLE test_table ALTER COLUMN test_column SET DEFAULT 1")
1695:        expr = self.parse_one("ALTER TABLE t ADD COLUMN c INT INVISIBLE")
[assistant] Comma-combined ALTER actions already work for `ADD`, but not after a property-style action (the trailing `options` csv consumes the comma). That's a separate, pre-existing shape of the parser, so I'll leave it alone and note it. Now the tests:
[tool_use Bash] {"command": "sed -n 194,206p tests/dialects/test_mysql.py", "description": "View test block near RENAME INDEX tests"}
[tool_result]         )
        self.validate_identity("ALTER TABLE t ALTER INDEX i INVISIBLE")
        self.validate_identity("ALTER TABLE t ALTER INDEX i VISIBLE")
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
[tool_use Edit] {"replace_all": false, "file_path": "<work>/../../../../../..~/.cache/lithify/work/repo-d5521a213087/20261028-164356-mysql-dialect-mysql-allows-setti/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\n            \"ALTER TABLE t RENAME KEY a TO b\",\n            \"ALTER TABLE t RENAME INDEX a TO b\",\n        )\n", "new_string": "        self.validate_identity(\n            \"ALTER TABLE t RENAME KEY a TO b\",\n            \"ALTER TABLE t RENAME INDEX a TO b\",\n        )\n        self.validate_identity(\"ALTER TABLE t AUTO_INCREMENT=3000000000\")\n        self.validate_identity(\"ALTER TABLE t AUTO_INCREMENT 5\", \"ALTER TABLE t AUTO_INCREMENT=5\")\n"}
[tool_result] The file <work>/../../../../../..~/.cache/lithify/work/repo-d5521a213087/20261028-164356-mysql-dialect-mysql-allows-setti/base-1/tests/dialects/test_mysql.py has been updated successfully.
[assistant] The edit tool resolved that path to the intended file, but I'll confirm with git and run the tests.
[tool_use Bash] {"command": "git status --short && git diff --stat && PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -5", "description": "Confirm changed files and run MySQL dialect tests"}
[tool_result]  M sqlglot/parsers/mysql.py
 M tests/dialects/test_mysql.py
 sqlglot/parsers/mysql.py     | 1 +
 tests/dialects/test_mysql.py | 2 ++
 2 files changed, 3 insertions(+)
.............................. [ 61%]
...................                                               [100%]
49 passed, 481 subtests passed in 0.25s
[assistant] Now the project's full check command, plus a formatter/lint pass on the two changed files.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; (ruff check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py && ruff format --check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py) 2>&1 | tail -4", "description": "Run full test suite and lint/format checks"}
[tool_result] .................................................................................................... [ 53%]
.......................................... [ 56%]
................................................................................................................................ [ 68%]
............................................... [ 73%]
.................................................................................................................................................................................................. [ 90%]
............................... [ 93%]
....................................................................       [100%]
1086 passed, 17844 subtests passed in 48.94s
All checks passed!
2 files already formatted
[assistant] `ALTER TABLE t AUTO_INCREMENT=3000000000` now parses in the MySQL dialect as the same `AutoIncrementProperty` that `CREATE TABLE` uses, and round-trips back to MySQL unchanged.

The change is one line in `sqlglot/parsers/mysql.py`: `AUTO_INCREMENT` is added to the MySQL `ALTER_PARSERS`, using the same `_parse_property_assignment(exp.AutoIncrementProperty)` the CREATE TABLE path uses. No generator change was needed, since the existing property rendering already emits `AUTO_INCREMENT=<n>`. I also added two identity tests to `tests/dialects/test_mysql.py`: the `=` form, and the space-separated `A
…[30 chars elided]…
ormalizes to `=5`.

Results: the full suite passes (1086 passed), and `ruff check` and `ruff format --check` are clean on both files. I didn't commit anything.

One gap I left alone: an AUTO_INCREMENT action combined with another action in one statement, e.g. `ALTER TABLE t AUTO_INCREMENT=1, ADD COLUMN c INT`, still falls back to a `Command`. Comma-separated `ADD` actions alone work fine, so this is specific to property-style actions being followed by a comma. Fixing it means changing how trailing ALTER options are parsed, which seemed out of scope for this request. Say if you want it handled.
