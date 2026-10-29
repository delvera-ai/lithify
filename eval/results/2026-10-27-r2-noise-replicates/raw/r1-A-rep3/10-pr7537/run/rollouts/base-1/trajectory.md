# trajectory base-1

final message:
`SHOW TABLES IN <schema>` now parses in the MySQL dialect and generates the `FROM` form. The full test suite passes (1089 passed) and ruff is clean.

**The cause:** the generic `IN` check at the top of `_parse_show_mysql` (`sqlglot/parsers/mysql.py`) consumed the `IN` keyword for every SHOW statement, intended only for `BINLOG EVENTS IN 'log'`. With no string after it, the schema name was left unparsed, so the parse failed.

**The fix**, in `sqlglot/parsers/mysql.py`:
- The `IN 'logfile'` check now runs only for `BINLOG EVENTS` and `RELAYLOG EVENTS`, where it belongs.
- The database branch accepts `FROM` or `IN`, so `SHOW TABLES IN x`, `SHOW FULL TABLES IN x LIKE ...`, and `SHOW COLUMNS FROM t IN db` all parse. MySQL documents the `IN` form of the database argument for `COLUMNS` as well.

**Tests:** I added two cases to `test_show_tables` in `tests/dialects/test_mysql.py`, checking that `SHOW TABLES IN test` and `SHOW FULL TABLES IN test LIKE '%foo%'` both generate the `FROM` form. The existing binlog tests cover the `IN 'logfile'` path and still pass.

## events
[tool_use Bash] {"command": "grep -n \"SHOW\\|_parse_show\\|def _parse_show_mysql\\|\\\"IN\\\"\\|\\\"FROM\\\"\" sqlglot/dialects/mysql.py | head -80", "description": "Find SHOW parsing code in mysql dialect"}
[tool_result] 154:        COMMANDS = {*tokens.Tokenizer.COMMANDS, TokenType.REPLACE} - {TokenType.SHOW}
[tool_use Bash] {"command": "grep -n \"_parse_show_mysql\\|def _parse_show\\|\\\"TABLES\\\"\\|SHOW_PARSERS\\|\\\"BINLOG\\\"\" sqlglot/dialects/mysql.py sqlglot/parser.py | head -40", "description": "Locate SHOW parser functions"}
[tool_result] sqlglot/parser.py:1543:    SHOW_PARSERS: t.ClassVar[dict[str, t.Callable]] = {}
sqlglot/parser.py:1824:    SHOW_TRIE: t.ClassVar[dict] = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parser.py:8756:        elif self._match_text_seq("TABLES"):
sqlglot/parser.py:8987:    def _parse_show(self) -> exp.Expr | None:
sqlglot/parser.py:8988:        parser = self._find_parser(self.SHOW_PARSERS, self.SHOW_TRIE)
[tool_use Bash] {"command": "grep -rn \"SHOW_PARSERS\\|_parse_show_mysql\\|def _parse_show\" sqlglot/ | head; grep -n \"SHOW\" sqlglot/dialects/mysql.py | head -30", "description": "Find SHOW_PARSERS definitions across sqlglot"}
[tool_result] sqlglot/parser.py:1543:    SHOW_PARSERS: t.ClassVar[dict[str, t.Callable]] = {}
sqlglot/parser.py:1824:    SHOW_TRIE: t.ClassVar[dict] = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parser.py:8987:    def _parse_show(self) -> exp.Expr | None:
sqlglot/parser.py:8988:        parser = self._find_parser(self.SHOW_PARSERS, self.SHOW_TRIE)
sqlglot/parsers/snowflake.py:805:    SHOW_PARSERS = {
sqlglot/parsers/snowflake.py:837:    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parsers/snowflake.py:1129:    def _parse_show_snowflake(
sqlglot/parsers/singlestore.py:193:    SHOW_PARSERS = {
sqlglot/parsers/singlestore.py:194:        **MySQLParser.SHOW_PARSERS,
sqlglot/parsers/singlestore.py:234:    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
154:        COMMANDS = {*tokens.Tokenizer.COMMANDS, TokenType.REPLACE} - {TokenType.SHOW}
[tool_use Bash] {"command": "grep -n \"SHOW\\|_parse_show\" sqlglot/parsers/mysql.py | head -60; sed -n 8980,9010p sqlglot/parser.py; sed -n 8740,8775p sqlglot/parser.py", "description": "Inspect MySQL SHOW parsers and base _parse_show"}
[tool_result] 49:        return self._parse_show_mysql(*args, **kwargs)
167:        TokenType.SHOW: lambda self: self._parse_show(),
170:    SHOW_PARSERS = {
240:    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
395:    def _parse_show_mysql(
            whens.append(
                self.expression(
                    exp.When(matched=matched, source=source, condition=condition, then=then)
                )
            )
        return self.expression(exp.Whens(expressions=whens))

    def _p
…[2164 chars elided]…
h_texts(self.ANALYZE_EXPRESSION_PARSERS):
            kind = None
            inner_expression = self.ANALYZE_EXPRESSION_PARSERS[self._prev.text.upper()](self)
        else:
            # Empty kind  https://prestodb.io/docs/current/sql/analyze.html
            kind = None
            this = self._parse_table_parts()

        partition = self._try_parse(self._parse_partition)
        if not partition and self._match_texts(self.PARTITION_KEYWORDS):
            return self._parse_as_command(start)
[tool_use Bash] {"command": "sed -n 170,240p sqlglot/parsers/mysql.py; sed -n 395,480p sqlglot/parsers/mysql.py", "description": "Read MySQL SHOW_PARSERS and _parse_show_mysql"}
[tool_result]     SHOW_PARSERS = {
        "BINARY LOGS": _show_parser("BINARY LOGS"),
        "MASTER LOGS": _show_parser("BINARY LOGS"),
        "BINLOG EVENTS": _show_parser("BINLOG EVENTS"),
        "CHARACTER SET": _show_parser("CHARACTER SET"),
        "CHARSET": _show_parser("CHARACTER SET"),
        "COLLATION": _show_parser("COLLATION"),
        "FULL COLUMNS": _show_parser("COLUMNS", target="FROM", full=True),
        "COLUMNS": _show_parser("COLUMNS", target="FROM"),
        "CREATE DATABASE": _sho
…[5822 chars elided]…
       limit=limit,
                mutex=mutex,
                for_table=for_table,
                for_group=for_group,
                for_user=for_user,
                for_role=for_role,
                into_outfile=into_outfile,
                json=json,
                global_=global_,
            )
        )

    def _parse_oldstyle_limit(
        self,
    ) -> tuple[exp.Expr | None, exp.Expr | None]:
        limit = None
        offset = None
        if self._match_text_seq("LIMIT"):
[tool_use Bash] {"command": "grep -rn \"SHOW .* IN \\|SHOW .*FROM\" tests/dialects/test_mysql.py | head -40; grep -n \"def show_sql\" -A40 sqlglot/generators/mysql.py | head -70", "description": "Check existing SHOW tests and MySQL show generator"}
[tool_result] tests/dialects/test_mysql.py:1223:            show = self.validate_identity(f"SHOW {key} EVENTS IN 'log' FROM 1 LIMIT 2, 3")
tests/dialects/test_mysql.py:1268:        show = self.validate_identity("SHOW COLUMNS FROM tbl_name")
tests/dialects/test_mysql.py:1274:        show = self.validate_identity("SHOW FULL COLUMNS FROM tbl_name FROM db_name LIKE '%foo%'")
tests/dialects/test_mysql.py:1328:        show = self.validate_identity("SHOW INDEX FROM foo")
tests/dialects/test_mysql.py:1333:        sho
…[1772 chars elided]…
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
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['SHOW TABLES IN test', 'SHOW FULL TABLES IN test LIKE \\'%foo%\\'', 'SHOW COLUMNS IN t IN db', \\\"SHOW BINLOG EVENTS IN 'logfile'\\\"]:\n    try: print(repr(sqlglot.parse_one(s, dialect='mysql').sql('mysql')))\n    except Exception as e: print('ERR', s, type(e).__name__)\n\"; sed -n 1215,1230p tests/dialects/test_mysql.py", "description": "Reproduce the SHOW TABLES IN parse failure"}
[tool_result] ERR SHOW TABLES IN test ParseError
ERR SHOW FULL TABLES IN test LIKE '%foo%' ParseError
ERR SHOW COLUMNS IN t IN db ParseError
"SHOW BINLOG EVENTS IN 'logfile'"
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
[assistant] Reproduced. The `IN` keyword is consumed by the generic `log` match before the `db` branch can see it, so I'll scope `log` to the binlog events shows and let `db` accept `IN`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-113002-mysql-mariadb-show-tables-in-sch/base-1/sqlglot/parsers/mysql.py", "old_string": "        log = self._parse_string() if self._match_text_seq(\"IN\") else None\n\n        if this in (\"BINLOG EVENTS\", \"RELAYLOG EVENTS\"):\n            position = self._parse_number() if self._match_text_seq(\"
…[186 chars elided]…
s in (\"BINLOG EVENTS\", \"RELAYLOG EVENTS\"):\n            log = self._parse_string() if self._match_text_seq(\"IN\") else None\n            position = self._parse_number() if self._match_text_seq(\"FROM\") else None\n            db = None\n        else:\n            log = None\n            position = None\n            db = None\n\n            if self._match_set((TokenType.FROM, TokenType.IN)):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-113002-mysql-mariadb-show-tables-in-sch/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[assistant] Now I'll add coverage next to the existing `SHOW ... FROM` tests.
[tool_use Bash] {"command": "sed -n 1400,1415p tests/dialects/test_mysql.py; sed -n 1326,1340p tests/dialects/test_mysql.py", "description": "View existing SHOW TABLES and INDEX tests"}
[tool_result]         show = self.validate_identity("SHOW REPLICA STATUS FOR CHANNEL channel_name")
        self.assertEqual(show.text("channel"), "channel_name")

    def test_show_tables(self):
        show = self.validate_identity("SHOW TABLES")
        self.assertIsInstance(show, exp.Show)
        self.assertEqual(show.name, "TABLES")

        show = self.validate_identity("SHOW FULL TABLES FROM db_name LIKE '%foo%'")
        self.assertTrue(show.args["full"])
        self.assertEqual(show.text("db"), "db
…[235 chars elided]…
f):
        show = self.validate_identity("SHOW INDEX FROM foo")
        self.assertIsInstance(show, exp.Show)
        self.assertEqual(show.name, "INDEX")
        self.assertEqual(show.text("target"), "foo")

        show = self.validate_identity("SHOW INDEX FROM foo FROM bar")
        self.assertEqual(show.text("db"), "bar")

        self.validate_all(
            "SHOW INDEX FROM bar.foo", write={"mysql": "SHOW INDEX FROM foo FROM bar"}
        )

    def test_show_db_like_or_where_sql(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-113002-mysql-mariadb-show-tables-in-sch/base-1/tests/dialects/test_mysql.py", "old_string": "        self.assertIsInstance(show.args[\"like\"], exp.Literal)\n        self.assertEqual(show.text(\"like\"), \"%foo%\")\n\n    def test_set_variable(self):", "new_string": "        self.assertIsInstance(sho
…[36 chars elided]…
    self.assertEqual(show.text(\"like\"), \"%foo%\")\n\n        self.validate_all(\n            \"SHOW TABLES IN test\",\n            write={\"mysql\": \"SHOW TABLES FROM test\"},\n        )\n        self.validate_all(\n            \"SHOW FULL TABLES IN test LIKE '%foo%'\",\n            write={\"mysql\": \"SHOW FULL TABLES FROM test LIKE '%foo%'\"},\n        )\n\n    def test_set_variable(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-113002-mysql-mariadb-show-tables-in-sch/base-1/tests/dialects/test_mysql.py has been updated successfully.
[assistant] Now I'll run the MySQL test file and the full suite, plus a check on the other `IN` forms.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['SHOW TABLES IN test', 'SHOW FULL TABLES IN test LIKE \\'%foo%\\'', 'SHOW COLUMNS FROM t IN db', 'SHOW COLUMNS FROM t FROM db', \\\"SHOW BINLOG EVENTS IN 'logfile'\\\", \\\"SHOW BINLOG EVENTS IN 'log' FROM 1 LIMIT 2, 3\\\"]:\n    try: print(repr(sqlglot.parse_one(s, dialect='mysql').sql('mysql')))\n    except Exception as e: print('ERR', s, type(e).__name__, e)\n\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -5; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Verify fix, run MySQL tests and full suite"}
[tool_result] 'SHOW TABLES FROM test'
"SHOW FULL TABLES FROM test LIKE '%foo%'"
'SHOW COLUMNS FROM t FROM db'
'SHOW COLUMNS FROM t FROM db'
"SHOW BINLOG EVENTS IN 'logfile'"
"SHOW BINLOG EVENTS IN 'log' FROM 1 LIMIT 2, 3"
.............................. [ 60%]
....................                                            [100%]
50 passed, 483 subtests passed in 0.27s
................................................. [ 90%]
............................... [ 93%]
.......................................................................... [ 99%]
..                                                                       [100%]
1089 passed, 17849 subtests passed in 52.83s
[assistant] All green. I'll run the linter on the two changed files too.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py && $PY -m ruff format --check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py) 2>&1 | tail -5; git diff --stat", "description": "Lint changed files and show diff stat"}
[tool_result] All checks passed!
2 files already formatted
 sqlglot/parsers/mysql.py     | 6 +++---
 tests/dialects/test_mysql.py | 9 +++++++++
 2 files changed, 12 insertions(+), 3 deletions(-)
[assistant] `SHOW TABLES IN <schema>` now parses in the MySQL dialect and generates the `FROM` form. The full test suite passes (1089 passed) and ruff is clean.

**The cause:** the generic `IN` check at the top of `_parse_show_mysql` (`sqlglot/parsers/mysql.py`) consumed the `IN` keyword for every SHOW statement, intended only for `BINLOG EVENTS IN 'log'`. With no string after it, the schema name was left unparsed, so the parse failed.

**The fix**, in `sqlglot/parsers/mysql.py`:
- The `IN 'logfile'` check now runs only for `BINLOG EVENTS` and `RELAYLOG EVENTS`, where it belongs.
- The database branch accepts `FROM` or `IN`, so `SHOW TABLES IN x`, `SHOW FULL TABLES IN x LIKE ...`, and `SHOW COLUMNS FROM t IN db` all parse. MySQL documents the `IN` form of the database argument for `COLUMNS` as well.

**Tests:** I added two cases to `test_show_tables` in `tests/dialects/test_mysql.py`, checking that `SHOW TABLES IN test` and `SHOW FULL TABLES IN test LIKE '%foo%'` both generate the `FROM` form. The existing binlog tests cover the `IN 'logfile'` path and still pass.
