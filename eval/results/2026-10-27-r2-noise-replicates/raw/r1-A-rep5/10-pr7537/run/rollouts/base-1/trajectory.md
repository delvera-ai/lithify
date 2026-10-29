# trajectory base-1

final message:
`SHOW TABLES IN test` now parses and generates `SHOW TABLES FROM test`. The full suite passes (1089 tests) and ruff lint and format are clean.

**Cause:** in `sqlglot/parsers/mysql.py`, `_parse_show_mysql` consumed `IN` up front as the binlog `log` argument for every SHOW statement. The database branch only recognised `FROM`, so `IN test` was left unparsed.

**Fix:**
- `IN <string>` is now parsed as `log` only for `BINLOG EVENTS` and `RELAYLOG EVENTS`.
- For every other SHOW, `IN` is accepted wherever `FROM` introduces the database, so `SHOW FULL TABLES IN db LIKE '...'` and `SHOW TABLES IN db WHERE ...` work too.
- I added a `test_show_tables` case in `tests/dialects/test_mysql.py` covering `SHOW TABLES IN` and `SHOW FULL TABLES IN ... LIKE`.

I compared parse output for 14 SHOW statements before and after the change. Only the `IN`-database forms changed. The binlog forms, including `SHOW BINLOG EVENTS IN 'logfile' FROM 1 LIMIT 2, 3`, are unchanged.

**Not changed:**
- `SHOW COLUMNS IN t` still fails to parse. It's the same class of bug, but for the table position rather than the database, and you didn't ask for it.
- `SHOW GRANTS FOR 'u'@'h'` also fails, and it was already failing before my change.

I haven't committed anything.

## events
[tool_use Bash] {"command": "grep -n \"FROM\\|_parse_show_mysql\\|def _parse_show\\|SHOW_PARSERS\\|\\\"IN\\\"\" sqlglot/dialects/mysql.py | head -80", "description": "Find SHOW parsing code in mysql dialect"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "pwd; ls; git -C ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092914-mysql-mariadb-show-tables-in-sch/base-1 status --short | head; ls sqlglot/dialects | grep -i -E \"mysql|maria\"", "description": "Check working directory and dialect files"}
[tool_result] ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092914-mysql-mariadb-show-tables-in-sch/base-1
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
mysql.py
[tool_use Bash] {"command": "grep -n \"SHOW\\|_parse_show\\|\\\"IN\\\"\\|TokenType.IN\\b\" sqlglot/dialects/mysql.py | head -80", "description": "Search SHOW handling in mysql dialect"}
[tool_result] 154:        COMMANDS = {*tokens.Tokenizer.COMMANDS, TokenType.REPLACE} - {TokenType.SHOW}
[tool_use Bash] {"command": "grep -n \"def _parse_show\\|_parse_show_mysql\\|SHOW_PARSERS\\|\\\"TABLES\\\"\\|def _show_parser\" sqlglot/dialects/mysql.py sqlglot/parser.py | head -40", "description": "Locate SHOW parser functions"}
[tool_result] sqlglot/parser.py:1543:    SHOW_PARSERS: t.ClassVar[dict[str, t.Callable]] = {}
sqlglot/parser.py:1824:    SHOW_TRIE: t.ClassVar[dict] = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parser.py:8756:        elif self._match_text_seq("TABLES"):
sqlglot/parser.py:8987:    def _parse_show(self) -> exp.Expr | None:
sqlglot/parser.py:8988:        parser = self._find_parser(self.SHOW_PARSERS, self.SHOW_TRIE)
[tool_use Bash] {"command": "grep -n \"SHOW_PARSERS\\|def _parse_show_mysql\\|def _parse_show\\b\" -r sqlglot/ | head; sed -n 8980,9000p sqlglot/parser.py", "description": "Find SHOW parsers across sqlglot"}
[tool_result] sqlglot/parser.py:1543:    SHOW_PARSERS: t.ClassVar[dict[str, t.Callable]] = {}
sqlglot/parser.py:1824:    SHOW_TRIE: t.ClassVar[dict] = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parser.py:8987:    def _parse_show(self) -> exp.Expr | None:
sqlglot/parser.py:8988:        parser = self._find_parser(self.SHOW_PARSERS, self.SHOW_TRIE)
sqlglot/parsers/singlestore.py:193:    SHOW_PARSERS = {
sqlglot/parsers/singlestore.py:194:        **MySQLParser.SHOW_PARSERS,
sqlglot/parsers/singlesto
…[653 chars elided]…
ser:
            return parser(self)
        return self._parse_as_command(self._prev)

    def _parse_set_item_assignment(self, kind: str | None = None) -> exp.Expr | None:
        index = self._index

        if kind in ("GLOBAL", "SESSION") and self._match_text_seq("TRANSACTION"):
            return self._parse_set_transaction(global_=kind == "GLOBAL")

        left = self._parse_primary() or self._parse_column()
        assignment_delimiter = self._match_texts(self.SET_ASSIGNMENT_DELIMITERS)
[assistant] The parser code has moved into `sqlglot/parsers/`. Let me look at the MySQL one.
[tool_use Bash] {"command": "ls sqlglot/parsers | head -50; grep -n \"SHOW\" sqlglot/parsers/mysql.py", "description": "List parsers dir and MySQL SHOW references"}
[tool_result] __init__.py
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
167:        TokenType.SHOW: lambda self: self._parse_show(),
170:    SHOW_PARSERS = {
240:    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
[tool_use Bash] {"command": "sed -n 165,245p sqlglot/parsers/mysql.py; grep -n \"def _parse_show_mysql\" -A60 sqlglot/parsers/mysql.py | head -90", "description": "Read MySQL SHOW parser config and helper"}
[tool_result]     STATEMENT_PARSERS = {
        **parser.Parser.STATEMENT_PARSERS,
        TokenType.SHOW: lambda self: self._parse_show(),
    }

    SHOW_PARSERS = {
        "BINARY LOGS": _show_parser("BINARY LOGS"),
        "MASTER LOGS": _show_parser("BINARY LOGS"),
        "BINLOG EVENTS": _show_parser("BINLOG EVENTS"),
        "CHARACTER SET": _show_parser("CHARACTER SET"),
        "CHARSET": _show_parser("CHARACTER SET"),
        "COLLATION": _show_parser("COLLATION"),
        "FULL COLUMNS": _show_pa
…[5703 chars elided]…
= self._parse_string() if self._match_text_seq("FOR", "USER") else None
446-        for_role = self._parse_string() if self._match_text_seq("FOR", "ROLE") else None
447-        into_outfile = self._parse_string() if self._match_text_seq("INTO", "OUTFILE") else None
448-
449-        return self.expression(
450-            exp.Show(
451-                this=this,
452-                target=target_id,
453-                full=full,
454-                log=log,
455-                position=position,
[tool_use Bash] {"command": "grep -n \"def _show_parser\" -A25 sqlglot/parsers/mysql.py; grep -rn \"SHOW [A-Z ]* IN \\|SHOW.* IN '\" tests/ | head -30; grep -n \"def show_sql\" -A40 sqlglot/generators/mysql.py | head -70", "description": "Inspect show parser helper, tests, and generator"}
[tool_result] 47:def _show_parser(*args: t.Any, **kwargs: t.Any) -> t.Callable[[MySQLParser], exp.Show]:
48-    def _parse(self: MySQLParser) -> exp.Show:
49-        return self._parse_show_mysql(*args, **kwargs)
50-
51-    return _parse
52-
53-
54-class MySQLParser(parser.Parser):
55-    NO_PAREN_FUNCTIONS = {
56-        **parser.Parser.NO_PAREN_FUNCTIONS,
57-        TokenType.LOCALTIME: exp.Localtime,
58-        TokenType.LOCALTIMESTAMP: exp.Localtimestamp,
59-    }
60-
61-    ID_VAR_TOKENS = parser.Parser.
…[4883 chars elided]…
         offset = ""
686-            limit = self._oldstyle_limit_sql(expression)
687-
688-        log = self._prefixed_sql("IN", expression, "log")
689-        position = self._prefixed_sql("FROM", expression, "position")
690-
691-        channel = self._prefixed_sql("FOR CHANNEL", expression, "channel")
692-
693-        if expression.name == "ENGINE":
694-            mutex_or_status = " MUTEX" if expression.args.get("mutex") else " STATUS"
695-        else:
696-            mutex_or_status = ""
[tool_use Bash] {"command": "grep -n \"SHOW\" tests/dialects/test_mysql.py | grep -i \" in\\b\" ; grep -n \"BINLOG\\|RELAYLOG\" tests/dialects/test_mysql.py", "description": "Find MySQL SHOW tests involving IN and binlog"}
[tool_result] 1223:            show = self.validate_identity(f"SHOW {key} EVENTS IN 'log' FROM 1 LIMIT 2, 3")
1218:        for key in ["BINLOG", "RELAYLOG"]:
1605:        self.validate_identity("ANALYZE NO_WRITE_TO_BINLOG TABLE tbl")
[assistant] Before editing, I'll capture baseline behaviour for a set of SHOW statements so I can diff afterwards.
[tool_use Bash] {"command": "mkdir -p /tmp/show_probe && cat > /tmp/show_probe/probe.py <<'EOF'\nimport sqlglot\nstmts = [\n    \"SHOW TABLES IN test\",\n    \"SHOW TABLES FROM test\",\n    \"SHOW FULL TABLES IN test LIKE 'a%'\",\n    \"SHOW TABLES IN test WHERE 1=1\",\n    \"SHOW TABLES\",\n    \"SHOW COLUMNS FROM t FROM db\",\n    \"SHOW COLUMNS FROM t IN db\",\n    \"SHOW COLUMNS IN t\",\n    \"SHOW INDEX FROM
…[359 chars elided]…
 print(repr(s), \"=> ERROR\", type(e).__name__, str(e).splitlines()[0])\nEOF\ncd ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092914-mysql-mariadb-show-tables-in-sch/base-1 && PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -I /tmp/show_probe/probe.py | tee /tmp/show_probe/before.txt", "description": "Capture baseline SHOW parsing output"}
[tool_result] Traceback (most recent call last):
  File "/tmp/show_probe/probe.py", line 1, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "sed -i '1i import sys; sys.path.insert(0, \"~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092914-mysql-mariadb-show-tables-in-sch/base-1\")' /tmp/show_probe/probe.py && <work>/env-sqlglot/bin/python -I /tmp/show_probe/probe.py | tee /tmp/show_probe/before.txt", "description": "Capture baseline SHOW parsing output"}
[tool_result ERROR] Exit code 1
sed: 1: "/tmp/show_probe/probe.py
": unterminated substitute pattern
[tool_use Bash] {"command": "{ echo 'import sys; sys.path.insert(0, \"~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092914-mysql-mariadb-show-tables-in-sch/base-1\")'; cat /tmp/show_probe/probe.py; } > /tmp/show_probe/p2.py && mv /tmp/show_probe/p2.py /tmp/show_probe/probe.py && <work>/env-sqlglot/bin/python -I /tmp/show_probe/probe.py | tee /tmp/show_probe/before.txt", "description": "Capture baseline SHOW parsing output"}
[tool_result] 'SHOW TABLES IN test' => ERROR ParseError Invalid expression / Unexpected token. Line 1, Col: 19.
'SHOW TABLES FROM test' => SHOW TABLES FROM test
"SHOW FULL TABLES IN test LIKE 'a%'" => ERROR ParseError Invalid expression / Unexpected token. Line 1, Col: 24.
'SHOW TABLES IN test WHERE 1=1' => ERROR ParseError Invalid expression / Unexpected token. Line 1, Col: 19.
'SHOW TABLES' => SHOW TABLES
'SHOW COLUMNS FROM t FROM db' => SHOW COLUMNS FROM t FROM db
'SHOW COLUMNS FROM t IN db' => ERROR Parse
…[76 chars elided]…
IN t' => ERROR ParseError Invalid expression / Unexpected token. Line 1, Col: 17.
'SHOW INDEX FROM t' => SHOW INDEX FROM t
"SHOW BINLOG EVENTS IN 'logfile'" => SHOW BINLOG EVENTS IN 'logfile'
"SHOW BINLOG EVENTS IN 'logfile' FROM 1 LIMIT 2, 3" => SHOW BINLOG EVENTS IN 'logfile' FROM 1 LIMIT 2, 3
'SHOW RELAYLOG EVENTS' => SHOW RELAYLOG EVENTS
"SHOW DATABASES LIKE 'x%'" => SHOW DATABASES LIKE 'x%'
"SHOW GRANTS FOR 'u'@'h'" => ERROR ParseError Invalid expression / Unexpected token. Line 1, Col: 20.
[assistant] Baseline confirms the bug (`SHOW TABLES IN test`, plus `FULL` and `WHERE` variants). Now the fix: `IN` is currently consumed up front as the binlog `log` for every SHOW, so I'll scope that to the binlog forms and let `IN` act like `FROM` for the database in the other branch.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092914-mysql-mariadb-show-tables-in-sch/base-1/sqlglot/parsers/mysql.py", "old_string": "        log = self._parse_string() if self._match_text_seq(\"IN\") else None\n\n        if this in (\"BINLOG EVENTS\", \"RELAYLOG EVENTS\"):\n            position = self._parse_number() if self._match_text_seq(\"
…[284 chars elided]…
     log = self._parse_string() if self._match_text_seq(\"IN\") else None\n            position = self._parse_number() if self._match_text_seq(\"FROM\") else None\n            db = None\n        else:\n            log = None\n            position = None\n            db = None\n\n            if self._match(TokenType.FROM) or self._match_text_seq(\"IN\"):\n                db = self._parse_id_var()"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092914-mysql-mariadb-show-tables-in-sch/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I /tmp/show_probe/probe.py > /tmp/show_probe/after.txt; diff /tmp/show_probe/before.txt /tmp/show_probe/after.txt; echo ---; cat /tmp/show_probe/after.txt", "description": "Re-run SHOW probe and diff against baseline"}
[tool_result] 1c1
< 'SHOW TABLES IN test' => ERROR ParseError Invalid expression / Unexpected token. Line 1, Col: 19.
---
> 'SHOW TABLES IN test' => SHOW TABLES FROM test
3,4c3,4
< "SHOW FULL TABLES IN test LIKE 'a%'" => ERROR ParseError Invalid expression / Unexpected token. Line 1, Col: 24.
< 'SHOW TABLES IN test WHERE 1=1' => ERROR ParseError Invalid expression / Unexpected token. Line 1, Col: 19.
---
> "SHOW FULL TABLES IN test LIKE 'a%'" => SHOW FULL TABLES FROM test LIKE 'a%'
> 'SHOW TABLES IN test WHER
…[628 chars elided]…
IN t' => ERROR ParseError Invalid expression / Unexpected token. Line 1, Col: 17.
'SHOW INDEX FROM t' => SHOW INDEX FROM t
"SHOW BINLOG EVENTS IN 'logfile'" => SHOW BINLOG EVENTS IN 'logfile'
"SHOW BINLOG EVENTS IN 'logfile' FROM 1 LIMIT 2, 3" => SHOW BINLOG EVENTS IN 'logfile' FROM 1 LIMIT 2, 3
'SHOW RELAYLOG EVENTS' => SHOW RELAYLOG EVENTS
"SHOW DATABASES LIKE 'x%'" => SHOW DATABASES LIKE 'x%'
"SHOW GRANTS FOR 'u'@'h'" => ERROR ParseError Invalid expression / Unexpected token. Line 1, Col: 20.
[assistant] Only the intended cases changed; the binlog forms are byte-identical. Next, a regression test in the MySQL dialect tests.
[tool_use Bash] {"command": "grep -n \"SHOW TABLES\\|SHOW FULL\\|def test_show\\|def test_\" tests/dialects/test_mysql.py | grep -i -B1 -A1 \"show\" | head -30", "description": "Find existing SHOW tests in MySQL tests"}
[tool_result] 904:    def test_mysql(self):
1199:    def test_show_simple(self):
1217:    def test_show_events(self):
1233:    def test_show_like_or_where(self):
1267:    def test_show_columns(self):
1274:        show = self.validate_identity("SHOW FULL COLUMNS FROM tbl_name FROM db_name LIKE '%foo%'")
1282:    def test_show_name(self):
1299:    def test_show_grants(self):
1305:    def test_show_engine(self):
1317:    def test_show_errors(self):
1327:    def test_show_index(self):
1340:    def test_show_db_like_or_where_sql(self):
1364:    def test_show_processlist(self):
1370:        show = self.validate_identity("SHOW FULL PROCESSLIST")
1374:    def test_show_profile(self):
1391:    def test_show_replica_status(self):
1403:    def test_show_tables(self):
1404:        show = self.validate_identity("SHOW TABLES")
1408:        show = self.validate_identity("SHOW FULL TABLES FROM db_name LIKE '%foo%'")
1414:    def test_set_variable(self):
[tool_use Bash] {"command": "sed -n 1403,1414p tests/dialects/test_mysql.py", "description": "Read existing SHOW TABLES test"}
[tool_result]     def test_show_tables(self):
        show = self.validate_identity("SHOW TABLES")
        self.assertIsInstance(show, exp.Show)
        self.assertEqual(show.name, "TABLES")

        show = self.validate_identity("SHOW FULL TABLES FROM db_name LIKE '%foo%'")
        self.assertTrue(show.args["full"])
        self.assertEqual(show.text("db"), "db_name")
        self.assertIsInstance(show.args["like"], exp.Literal)
        self.assertEqual(show.text("like"), "%foo%")

    def test_set_variable(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092914-mysql-mariadb-show-tables-in-sch/base-1/tests/dialects/test_mysql.py", "old_string": "        self.assertIsInstance(show.args[\"like\"], exp.Literal)\n        self.assertEqual(show.text(\"like\"), \"%foo%\")\n\n    def test_set_variable(self):", "new_string": "        self.assertIsInstance(sho
…[198 chars elided]…
 FROM db_name\",\n        )\n        self.assertEqual(show.text(\"db\"), \"db_name\")\n\n        show = self.validate_identity(\n            \"SHOW FULL TABLES IN db_name LIKE '%foo%'\",\n            \"SHOW FULL TABLES FROM db_name LIKE '%foo%'\",\n        )\n        self.assertTrue(show.args[\"full\"])\n        self.assertEqual(show.text(\"db\"), \"db_name\")\n\n    def test_set_variable(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092914-mysql-mariadb-show-tables-in-sch/base-1/tests/dialects/test_mysql.py has been updated successfully.
[assistant] Now the project's check command, full suite, then the style check.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run project test suite", "timeout": 600000}
[tool_result] ......................................................................................................................................................................... [ 35%]
.......................................................................................................................................... [ 48%]
.............................................. [ 52%]
.................... [ 54%]
...................................................... [ 59%]
.......... [ 60%]
...............
…[25 chars elided]…
[ 63%]
.......... [ 64%]
..................................... [ 68%]
............................................... [ 72%]
.................................................................................................................... [ 83%]
.............................................................................. [ 90%]
............................... [ 93%]
.......................................................................... [100%]
1089 passed, 17847 subtests passed in 55.72s
[tool_use Bash] {"command": "grep -n \"^style\\|^check:\" -A3 Makefile | head; (<work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py) 2>&1 | tail -5; git diff --stat", "description": "Lint, format check, and show diff stat"}
[tool_result] 83:style:
84-	pre-commit run --all-files
85-	@if [ -f sqlglot-integration-tests/Makefile ]; then $(MAKE) -C sqlglot-integration-tests check-submodule; fi
86-
87:check: style test testc
88-
89-docs:
90-	python pdoc/cli.py -o docs
All checks passed!
2 files already formatted
 sqlglot/parsers/mysql.py     |  6 +++---
 tests/dialects/test_mysql.py | 13 +++++++++++++
 2 files changed, 16 insertions(+), 3 deletions(-)
[assistant] `SHOW TABLES IN test` now parses and generates `SHOW TABLES FROM test`. The full suite passes (1089 tests) and ruff lint and format are clean.

**Cause:** in `sqlglot/parsers/mysql.py`, `_parse_show_mysql` consumed `IN` up front as the binlog `log` argument for every SHOW statement. The database branch only recognised `FROM`, so `IN test` was left unparsed.

**Fix:**
- `IN <string>` is now parsed as `log` only for `BINLOG EVENTS` and `RELAYLOG EVENTS`.
- For every other SHOW, `IN` is accepted wherever `FROM` introduces the database, so `SHOW FULL TABLES IN db LIKE '...'` and `SHOW TABLES IN db
…[50 chars elided]…
s` case in `tests/dialects/test_mysql.py` covering `SHOW TABLES IN` and `SHOW FULL TABLES IN ... LIKE`.

I compared parse output for 14 SHOW statements before and after the change. Only the `IN`-database forms changed. The binlog forms, including `SHOW BINLOG EVENTS IN 'logfile' FROM 1 LIMIT 2, 3`, are unchanged.

**Not changed:**
- `SHOW COLUMNS IN t` still fails to parse. It's the same class of bug, but for the table position rather than the database, and you didn't ask for it.
- `SHOW GRANTS FOR 'u'@'h'` also fails, and it was already failing before my change.

I haven't committed anything.
