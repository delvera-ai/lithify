# trajectory base-1

final message:
`SHOW TABLES IN test` now parses in the MySQL dialect and generates as `SHOW TABLES FROM test`. The full suite passes (1089 tests), and ruff check and format are clean on the changed files.

The change is in `sqlglot/parsers/mysql.py` (`_parse_show_mysql`). `IN` was previously consumed only as a log-file argument for every SHOW statement, which is why `IN test` failed. Now:

- For `BINLOG EVENTS` and `RELAYLOG EVENTS`, `IN` still takes the log file string, so `SHOW BINLOG EVENTS IN 'logfile'` is unchanged.
- For all other SHOW forms, `IN` is accepted as a synonym for `FROM` and sets the database. `SHOW FULL TABLES IN test LIKE '%foo%'` works the same way.

I added assertions to `test_show_tables` in `tests/dialects/test_mysql.py` covering both the plain and `FULL` forms. I did not commit anything.

One behaviour change to be aware of: a non-binlog SHOW followed by `IN 'string'` used to parse into the `log` argument and now fails. That form isn't valid MySQL, so I left it.

## events
[tool_use Bash] {"command": "grep -n \"SHOW\" dialects/mysql.py | head -80 && grep -n \"def _parse_show_mysql\" -A60 dialects/mysql.py | head -120", "description": "Find SHOW parsing code in MySQL dialect"}
[tool_result] ugrep: warning: dialects/mysql.py: No such file or directory
ugrep: warning: dialects/mysql.py: No such file or directory
[tool_use Bash] {"command": "pwd && ls && git status --short | head && grep -rn \"_parse_show_mysql\\|def _parse_show\" sqlglot/dialects/mysql.py | head", "description": "Locate MySQL dialect SHOW parser"}
[tool_result] ~/.cache/lithify/work/repo-b63a38b63828/20261026-135052-mysql-mariadb-show-tables-in-sch/base-1
AGENTS.md
CHANGELOG.md
CLAUDE.md
CONTRIBUTING.md
LICENSE
MANIFEST.in
Makefile
README.md
benchmarks
pdoc
posts
pyproject.toml
setup.cfg
setup.py
sqlglot
sqlglot-integration-tests
sqlglot.png
sqlglotc
tests
[tool_use Bash] {"command": "grep -n \"SHOW\\|_parse_show\" sqlglot/dialects/mysql.py | head -60", "description": "Find SHOW references in MySQL dialect"}
[tool_result] 154:        COMMANDS = {*tokens.Tokenizer.COMMANDS, TokenType.REPLACE} - {TokenType.SHOW}
[tool_use Bash] {"command": "grep -n \"def _parse_show\\|SHOW_PARSERS\\|_parse_show_\" sqlglot/parser.py | head -40; grep -n \"def _parse_show\" -A50 sqlglot/dialects/mysql.py | head -150", "description": "Locate base and MySQL SHOW parser functions"}
[tool_result] 1543:    SHOW_PARSERS: t.ClassVar[dict[str, t.Callable]] = {}
1824:    SHOW_TRIE: t.ClassVar[dict] = new_trie(key.split(" ") for key in SHOW_PARSERS)
8987:    def _parse_show(self) -> exp.Expr | None:
8988:        parser = self._find_parser(self.SHOW_PARSERS, self.SHOW_TRIE)
[tool_use Bash] {"command": "grep -rn \"SHOW_PARSERS\\|_parse_show_mysql\" sqlglot/ | head -20; grep -n \"def _show_parser\\|def _parse_show\" -A40 sqlglot/dialects/mysql.py | head -200", "description": "Find SHOW parser definitions across sqlglot"}
[tool_result] sqlglot/parser.py:1543:    SHOW_PARSERS: t.ClassVar[dict[str, t.Callable]] = {}
sqlglot/parser.py:1824:    SHOW_TRIE: t.ClassVar[dict] = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parser.py:8988:        parser = self._find_parser(self.SHOW_PARSERS, self.SHOW_TRIE)
sqlglot/parsers/snowflake.py:805:    SHOW_PARSERS = {
sqlglot/parsers/snowflake.py:837:    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parsers/duckdb.py:97:    SHOW_PARSERS = {
sqlglot/parsers/duc
…[85 chars elided]…
arsers/singlestore.py:193:    SHOW_PARSERS = {
sqlglot/parsers/singlestore.py:194:        **MySQLParser.SHOW_PARSERS,
sqlglot/parsers/singlestore.py:234:    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parsers/mysql.py:49:        return self._parse_show_mysql(*args, **kwargs)
sqlglot/parsers/mysql.py:170:    SHOW_PARSERS = {
sqlglot/parsers/mysql.py:240:    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parsers/mysql.py:395:    def _parse_show_mysql(
[tool_use Bash] {"command": "sed -n 40,55p sqlglot/parsers/mysql.py && sed -n 395,470p sqlglot/parsers/mysql.py && grep -n \"BINLOG\\|TABLES\" sqlglot/parsers/mysql.py | head -30", "description": "Read MySQL SHOW parsing logic"}
[tool_result]     if mysql_date_format and _has_time_specifier(mysql_date_format.name):
        return exp.StrToTime(this=this, format=date_format)

    return exp.StrToDate(this=this, format=date_format)


def _show_parser(*args: t.Any, **kwargs: t.Any) -> t.Callable[[MySQLParser], exp.Show]:
    def _parse(self: MySQLParser) -> exp.Show:
        return self._parse_show_mysql(*args, **kwargs)

    return _parse


class MySQLParser(parser.Parser):
    NO_PAREN_FUNCTIONS = {
    def _parse_show_mysql(
        
…[2670 chars elided]…
,
                for_table=for_table,
                for_group=for_group,
                for_user=for_user,
                for_role=for_role,
                into_outfile=into_outfile,
                json=json,
173:        "BINLOG EVENTS": _show_parser("BINLOG EVENTS"),
198:        "OPEN TABLES": _show_parser("OPEN TABLES"),
216:        "FULL TABLES": _show_parser("TABLES", full=True),
217:        "TABLES": _show_parser("TABLES"),
413:        if this in ("BINLOG EVENTS", "RELAYLOG EVENTS"):
[tool_use Bash] {"command": "grep -rn \"SHOW.* IN \" tests/ | head -30; sed -n 165,240p sqlglot/parsers/mysql.py", "description": "Find existing SHOW ... IN usages in tests"}
[tool_result] tests/dialects/test_snowflake.py:5200:        ast = parse_one("SHOW DATABASES IN ACCOUNT", read="snowflake")
tests/dialects/test_snowflake.py:5206:        self.validate_identity("SHOW FILE FORMATS LIKE 'foo' IN DATABASE db1")
tests/dialects/test_snowflake.py:5207:        self.validate_identity("SHOW FILE FORMATS LIKE 'foo' IN SCHEMA db1.schema1")
tests/dialects/test_snowflake.py:5209:        ast = parse_one("SHOW FILE FORMATS IN ACCOUNT", read="snowflake")
tests/dialects/test_snowflake.py:5215: 
…[6127 chars elided]…
S = {
        **parser.Parser.SET_PARSERS,
        "PERSIST": lambda self: self._parse_set_item_assignment("PERSIST"),
        "PERSIST_ONLY": lambda self: self._parse_set_item_assignment("PERSIST_ONLY"),
        "CHARACTER SET": lambda self: self._parse_set_item_charset("CHARACTER SET"),
        "CHARSET": lambda self: self._parse_set_item_charset("CHARACTER SET"),
        "NAMES": lambda self: self._parse_set_item_names(),
    }

    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
[tool_use Bash] {"command": "grep -rn \"BINLOG\\|SHOW.*IN\\b\" tests/dialects/test_mysql.py | head -20; grep -n \"def show_sql\" -A30 sqlglot/generators/mysql.py | head -50", "description": "Check MySQL SHOW tests and generator"}
[tool_result] tests/dialects/test_mysql.py:1218:        for key in ["BINLOG", "RELAYLOG"]:
tests/dialects/test_mysql.py:1223:            show = self.validate_identity(f"SHOW {key} EVENTS IN 'log' FROM 1 LIMIT 2, 3")
tests/dialects/test_mysql.py:1605:        self.validate_identity("ANALYZE NO_WRITE_TO_BINLOG TABLE tbl")
656:    def show_sql(self, expression: exp.Show) -> str:
657-        this = f" {expression.name}"
658-        full = " FULL" if expression.args.get("full") else ""
659-        global_ = " GLOBA
…[758 chars elided]…
")
676-
677-        types = self.expressions(expression, key="types")
678-        types = f" {types}" if types else types
679-        query = self._prefixed_sql("FOR QUERY", expression, "query")
680-
681-        if expression.name == "PROFILE":
682-            offset = self._prefixed_sql("OFFSET", expression, "offset")
683-            limit = self._prefixed_sql("LIMIT", expression, "limit")
684-        else:
685-            offset = ""
686-            limit = self._oldstyle_limit_sql(expression)
[assistant] Only the binlog branch uses `IN` as a log-file argument, so I'll scope that to the binlog events and let the general branch accept `IN` as a database qualifier, alongside `FROM`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-135052-mysql-mariadb-show-tables-in-sch/base-1/sqlglot/parsers/mysql.py", "old_string": "        log = self._parse_string() if self._match_text_seq(\"IN\") else None\n\n        if this in (\"BINLOG EVENTS\", \"RELAYLOG EVENTS\"):\n            position = self._parse_number() if self._match_text_seq(\"
…[198 chars elided]…
OG EVENTS\", \"RELAYLOG EVENTS\"):\n            log = self._parse_string() if self._match_text_seq(\"IN\") else None\n            position = self._parse_number() if self._match_text_seq(\"FROM\") else None\n            db = None\n        else:\n            log = None\n            position = None\n            db = None\n\n            if self._match(TokenType.FROM) or self._match_text_seq(\"IN\"):"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-135052-mysql-mariadb-show-tables-in-sch/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[assistant] Now I'll add tests next to the existing SHOW tests, then run them.
[tool_use Bash] {"command": "grep -n \"SHOW TABLES\\|SHOW FULL TABLES\" tests/dialects/test_mysql.py | head; sed -n 1214,1230p tests/dialects/test_mysql.py", "description": "Find SHOW TABLES tests in MySQL test file"}
[tool_result] 1404:        show = self.validate_identity("SHOW TABLES")
1408:        show = self.validate_identity("SHOW FULL TABLES FROM db_name LIKE '%foo%'")
            self.assertIsInstance(show, exp.Show)
            self.assertEqual(show.name, write_key)

    def test_show_events(self):
        for key in ["BINLOG", "RELAYLOG"]:
            show = self.validate_identity(f"SHOW {key} EVENTS")
            self.assertIsInstance(show, exp.Show)
            self.assertEqual(show.name, f"{key} EVENTS")

            show = self.validate_identity(f"SHOW {key} EVENTS IN 'log' FROM 1 LIMIT 2, 3")
            self.assertEqual(show.text("log"), "log")
            self.assertEqual(show.text("position"), "1")
            self.assertEqual(show.text("limit"), "3")
            self.assertEqual(show.text("offset"), "2")

            show = self.validate_identity(f"SHOW {key} EVENTS LIMIT 1")
            self.assertEqual(show.text("limit"), "1")
[tool_use Bash] {"command": "sed -n 1400,1412p tests/dialects/test_mysql.py", "description": "Read existing SHOW TABLES test block"}
[tool_result]         show = self.validate_identity("SHOW REPLICA STATUS FOR CHANNEL channel_name")
        self.assertEqual(show.text("channel"), "channel_name")

    def test_show_tables(self):
        show = self.validate_identity("SHOW TABLES")
        self.assertIsInstance(show, exp.Show)
        self.assertEqual(show.name, "TABLES")

        show = self.validate_identity("SHOW FULL TABLES FROM db_name LIKE '%foo%'")
        self.assertTrue(show.args["full"])
        self.assertEqual(show.text("db"), "db_name")
        self.assertIsInstance(show.args["like"], exp.Literal)
        self.assertEqual(show.text("like"), "%foo%")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-135052-mysql-mariadb-show-tables-in-sch/base-1/tests/dialects/test_mysql.py", "old_string": "        show = self.validate_identity(\"SHOW FULL TABLES FROM db_name LIKE '%foo%'\")\n        self.assertTrue(show.args[\"full\"])\n        self.assertEqual(show.text(\"db\"), \"db_name\")\n        self.asse
…[424 chars elided]…
\"%foo%\")\n\n        show = self.validate_one(\"SHOW TABLES IN test\", write_sql=\"SHOW TABLES FROM test\")\n        self.assertEqual(show.text(\"db\"), \"test\")\n\n        show = self.validate_one(\"SHOW FULL TABLES IN test LIKE '%foo%'\", write_sql=\"SHOW FULL TABLES FROM test LIKE '%foo%'\")\n        self.assertTrue(show.args[\"full\"])\n        self.assertEqual(show.text(\"db\"), \"test\")"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-135052-mysql-mariadb-show-tables-in-sch/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"def validate_one\\|def validate_identity\" -A3 tests/dialects/test_dialect.py; P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfor s in ['SHOW TABLES IN test','SHOW FULL TABLES IN test LIKE \\'%foo%\\'', \\\"SHOW BINLOG EVENTS IN 'logfile'\\\"]:\n    print(sqlglot.transpile(s, read='mysql', write='mysql'))\n\"; $P -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py tests/dialects/test_snowflake.py 2>&1 | tail -15", "description": "Check helper signatures, run sample parses and dialect tests"}
[tool_result] 53:    def validate_identity(
54-        self, sql, write_sql=None, pretty=False, check_command_warning=False, identify=False
55-    ):
56-        if check_command_warning:
['SHOW TABLES FROM test']
["SHOW FULL TABLES FROM test LIKE '%foo%'"]
["SHOW BINLOG EVENTS IN 'logfile'"]
    
        show = self.validate_identity("SHOW FULL TABLES FROM db_name LIKE '%foo%'")
        self.assertTrue(show.args["full"])
        self.assertEqual(show.text("db"), "db_name")
        self.assertIsInstance(show.a
…[78 chars elided]…

    
>       show = self.validate_one("SHOW TABLES IN test", write_sql="SHOW TABLES FROM test")
               ^^^^^^^^^^^^^^^^^
E       AttributeError: 'TestMySQL' object has no attribute 'validate_one'. Did you mean: 'validate_all'?

tests/dialects/test_mysql.py:1414: AttributeError
=========================== short test summary info ============================
FAILED tests/dialects/test_mysql.py::TestMySQL::test_show_tables - AttributeE...
1 failed, 144 passed, 2046 subtests passed in 0.69s
[assistant] The helper is `validate_identity` with `write_sql`, not `validate_one`. Fixing the test to use it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-135052-mysql-mariadb-show-tables-in-sch/base-1/tests/dialects/test_mysql.py", "old_string": "        show = self.validate_one(\"SHOW TABLES IN test\", write_sql=\"SHOW TABLES FROM test\")\n        self.assertEqual(show.text(\"db\"), \"test\")\n\n        show = self.validate_one(\"SHOW FULL TABLES IN 
…[84 chars elided]…
 self.assertTrue(show.args[\"full\"])", "new_string": "        show = self.validate_identity(\"SHOW TABLES IN test\", \"SHOW TABLES FROM test\")\n        self.assertEqual(show.text(\"db\"), \"test\")\n\n        show = self.validate_identity(\n            \"SHOW FULL TABLES IN test LIKE '%foo%'\", \"SHOW FULL TABLES FROM test LIKE '%foo%'\"\n        )\n        self.assertTrue(show.args[\"full\"])"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-135052-mysql-mariadb-show-tables-in-sch/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; $P -m ruff check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py && $P -m ruff format --check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py", "description": "Run full test suite and lint changed files"}
[tool_result] .................................................................................................................... [ 83%]
.............................................................................. [ 90%]
............................... [ 93%]
.......................................................................... [100%]
1089 passed, 17847 subtests passed in 62.37s (0:01:02)
All checks passed!
2 files already formatted
[assistant] `SHOW TABLES IN test` now parses in the MySQL dialect and generates as `SHOW TABLES FROM test`. The full suite passes (1089 tests), and ruff check and format are clean on the changed files.

The change is in `sqlglot/parsers/mysql.py` (`_parse_show_mysql`). `IN` was previously consumed only as a log-file argument for every SHOW statement, which is why `IN test` failed. Now:

- For `BINLOG EVENTS` and `RELAYLOG EVENTS`, `IN` still takes the log file string, so `SHOW BINLOG EVENTS IN 'logfile'` is unchanged.
- For all other SHOW forms, `IN` is accepted as a synonym for `FROM` and sets the database. `SHOW FULL TABLES IN test LIKE '%foo%'` works the same way.

I added assertions to `test_show_tables` in `tests/dialects/test_mysql.py` covering both the plain and `FULL` forms. I did not commit anything.

One behaviour change to be aware of: a non-binlog SHOW followed by `IN 'string'` used to parse into the `log` argument and now fails. That form isn't valid MySQL, so I left it.
