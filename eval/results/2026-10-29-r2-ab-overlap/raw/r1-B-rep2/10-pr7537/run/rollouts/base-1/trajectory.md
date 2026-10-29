# trajectory base-1

final message:
`SHOW TABLES IN test` now parses in MySQL and generates `SHOW TABLES FROM test`. The full suite passes (1089 tests), and ruff check and format are clean.

**Cause:** `_parse_show_mysql` in `sqlglot/parsers/mysql.py` checked for `IN` to read the binlog `log` argument before the database branch ran. That consumed the `IN` even when no string followed, and the database branch only accepted `FROM`.

**Change:**
- The `log` argument is now parsed only for `BINLOG EVENTS` and `RELAYLOG EVENTS`, which is where it applies.
- The database branch accepts `IN` as well as `FROM`.
- `SHOW BINLOG EVENTS IN 'logfile' FROM 4 LIMIT 2` still round-trips unchanged.
- I added cases to `test_show_tables` in `tests/dialects/test_mysql.py` for `SHOW TABLES IN test` and `SHOW FULL TABLES IN test LIKE '%foo%'`.

**Not covered:** `SHOW COLUMNS IN t` and `SHOW INDEX IN t` still fail. Their table-target branch only accepts `FROM`, and they failed before this change too. Supporting them would mean extending the target branch, which is a separate change, so I left it out.

The changes are uncommitted in the worktree.

## events
[tool_use Bash] {"command": "grep -n \"_parse_show_mysql\\|def _parse_show\\|FROM\\b\" sqlglot/dialects/mysql.py | head -80", "description": "Find SHOW parsing code in mysql dialect"}
[tool_result] 0 matches for '_parse_show_mysql\|def _parse_show\|FROM\b'
[tool_use Bash] {"command": "grep -n \"SHOW\\|_parse_show\" sqlglot/dialects/mysql.py | head -60; echo ---; grep -n \"def _parse_show\\b\\|def _parse_show(\" -A 25 sqlglot/parser.py | head -60", "description": "Locate SHOW parsing in mysql dialect and base parser"}
[tool_result] 1 matches in 1 files:

sqlglot/dialects/mysql.py:154:COMMANDS = {*tokens.Tokenizer.COMMANDS, TokenType.REPLACE} - {TokenType.SHOW}
---
8987:    def _parse_show(self) -> exp.Expr | None:
8988-        parser = self._find_parser(self.SHOW_PARSERS, self.SHOW_TRIE)
8989-        if parser:
8990-            return parser(self)
8991-        return self._parse_as_command(self._prev)
8992-
8993-    def _parse_set_item_assignment(self, kind: str | None = None) -> exp.Expr | None:
8994-        index = self.
…[348 chars elided]…
       if not left or (self.SET_REQUIRES_ASSIGNMENT_DELIMITER and not assignment_delimiter):
9003-            self._retreat(index)
9004-            return None
9005-
9006-        right = self._parse_statement() or self._parse_id_var()
9007-        if isinstance(right, (exp.Column, exp.Identifier)):
9008-            right = exp.var(right.name)
9009-
9010-        this = self.expression(exp.EQ(this=left, expression=right))
9011-        return self.expression(exp.SetItem(this=this, kind=kind))
9012-
[tool_use Bash] {"command": "grep -n \"_parse_show_mysql\\|SHOW_PARSERS\\|\\\"TABLES\\\"\\|\\\"BINLOG\\|_parse_show_\\|\\\"FROM\\\"\" sqlglot/dialects/mysql.py sqlglot/parser.py | head -60", "description": "Find SHOW parser registrations"}
[tool_result] 9 matches in 1 files:

sqlglot/parser.py:1543:SHOW_PARSERS: t.ClassVar[dict[str, t.Callable]] = {}
sqlglot/parser.py:1824:SHOW_TRIE: t.ClassVar[dict] = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parser.py:3573:files=self._match_text_seq("FROM", "FILES")
sqlglot/parser.py:4744:if self._match_text_seq("ROWS", "FROM")
sqlglot/parser.py:5737:if self._match_text_seq("DISTINCT", "FROM"):
sqlglot/parser.py:8756:elif self._match_text_seq("TABLES"):
sqlglot/parser.py:8988:parser = self._find_parser(self.SHOW_PARSERS, self.SHOW_TRIE)
sqlglot/parser.py:9518:if not securable or not self._match_text_seq("FROM"):
sqlglot/parser.py:9553:from_=_parse_overlay_arg("FROM"),
[tool_use Bash] {"command": "grep -rn \"SHOW_PARSERS\\|_parse_show_\\|def _parse_show\" sqlglot/ | head -40; echo ---; grep -n \"def _parse_show_mysql\" -A 80 sqlglot/dialects/mysql.py | head -150", "description": "Find MySQL SHOW parser implementations"}
[tool_result] sqlglot/parsers/singlestore.py:193:    SHOW_PARSERS = {
sqlglot/parsers/singlestore.py:194:        **MySQLParser.SHOW_PARSERS,
sqlglot/parsers/singlestore.py:234:    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parsers/snowflake.py:320:        return self._parse_show_snowflake(*args, **kwargs)
sqlglot/parsers/snowflake.py:805:    SHOW_PARSERS = {
sqlglot/parsers/snowflake.py:837:    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parsers/snowflake.py:
…[487 chars elided]…
qlglot/parsers/mysql.py:240:    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parsers/mysql.py:395:    def _parse_show_mysql(
sqlglot/parser.py:1543:    SHOW_PARSERS: t.ClassVar[dict[str, t.Callable]] = {}
sqlglot/parser.py:1824:    SHOW_TRIE: t.ClassVar[dict] = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parser.py:8987:    def _parse_show(self) -> exp.Expr | None:
sqlglot/parser.py:8988:        parser = self._find_parser(self.SHOW_PARSERS, self.SHOW_TRIE)
---
[tool_use Bash] {"command": "sed -n 165,245p sqlglot/parsers/mysql.py; echo ----; sed -n 390,480p sqlglot/parsers/mysql.py", "description": "Read MySQL SHOW parser code"}
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
…[6272 chars elided]…
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
[tool_use Bash] {"command": "grep -rn \"SHOW.* IN \\|SHOW.*\\bIN\\b\" tests/dialects/test_mysql.py | head -30; echo ---; grep -n \"def show_sql\" -A 30 sqlglot/generator.py sqlglot/generators/mysql.py 2>/dev/null | head -60; grep -rn \"def _match_set\\b\\|def _match_set(\" sqlglot/parser.py", "description": "Inspect existing MySQL SHOW IN tests and generator"}
[tool_result] tests/dialects/test_mysql.py:1223:            show = self.validate_identity(f"SHOW {key} EVENTS IN 'log' FROM 1 LIMIT 2, 3")
---
sqlglot/generator.py:5728:    def show_sql(self, expression: exp.Show) -> str:
sqlglot/generator.py-5729-        self.unsupported("Unsupported SHOW statement")
sqlglot/generator.py-5730-        return ""
sqlglot/generator.py-5731-
sqlglot/generator.py-5732-    def install_sql(self, expression: exp.Install) -> str:
sqlglot/generator.py-5733-        self.unsupported("Uns
…[3539 chars elided]…
ql.py-679-        query = self._prefixed_sql("FOR QUERY", expression, "query")
sqlglot/generators/mysql.py-680-
sqlglot/generators/mysql.py-681-        if expression.name == "PROFILE":
sqlglot/generators/mysql.py-682-            offset = self._prefixed_sql("OFFSET", expression, "offset")
sqlglot/generators/mysql.py-683-            limit = self._prefixed_sql("LIMIT", expression, "limit")
sqlglot/parser.py:1911:    def _match_set(self, types: t.Collection[TokenType], advance: bool = True) -> bool:
[assistant] The root cause is in `_parse_show_mysql`: the `IN` check for the binlog `log` argument runs before the database branch and consumes the `IN` token even when no string follows, and the database branch only accepts `FROM`. I'll limit the `log` parse to the binlog statements and let the database branch accept `IN`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-135649-mysql-mariadb-show-tables-in-sch/base-1/sqlglot/parsers/mysql.py", "old_string": "        log = self._parse_string() if self._match_text_seq(\"IN\") else None\n\n        if this in (\"BINLOG EVENTS\", \"RELAYLOG EVENTS\"):\n            position = self._parse_number() if self._match_text_seq(\"
…[186 chars elided]…
s in (\"BINLOG EVENTS\", \"RELAYLOG EVENTS\"):\n            log = self._parse_string() if self._match_text_seq(\"IN\") else None\n            position = self._parse_number() if self._match_text_seq(\"FROM\") else None\n            db = None\n        else:\n            log = None\n            position = None\n            db = None\n\n            if self._match_set((TokenType.FROM, TokenType.IN)):"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-135649-mysql-mariadb-show-tables-in-sch/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[assistant] Now let me verify the behavior and run the project's test suite.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SHOW TABLES IN test','SHOW FULL TABLES IN test LIKE \\'a%\\'','SHOW TABLES FROM test','SHOW BINLOG EVENTS IN \\'logfile\\'','SHOW BINLOG EVENTS IN \\'logfile\\' FROM 4 LIMIT 2','SHOW COLUMNS IN t IN db','SHOW INDEX IN t']:\n    e = sqlglot.parse_one(s, dialect='mysql'); print(repr(s), '->', e.sql('mysql'))\nprint(sqlglot.parse_one('SHOW TABLES IN test', dialect='mysql').sql('mysql'))\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Check SHOW IN parsing and run the test suite"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 4, in <module>
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-135649-mysql-mariadb-show-tables-in-sch/base-1/sqlglot/__init__.py", line 176, in parse_one
    result = dialect.parse(sql, **opts)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-135649-mysql-mariadb-show-tables-in-sch/base-1/sqlglot/dialects/dialect.py", line 1116, in parse
    r
…[1043 chars elided]…
 line 1977, in raise_error
    raise error
sqlglot.errors.ParseError: Invalid expression / Unexpected token. Line 1, Col: 17.
  SHOW COLUMNS IN [4mt[0m IN db
'SHOW TABLES IN test' -> SHOW TABLES FROM test
"SHOW FULL TABLES IN test LIKE 'a%'" -> SHOW FULL TABLES FROM test LIKE 'a%'
'SHOW TABLES FROM test' -> SHOW TABLES FROM test
"SHOW BINLOG EVENTS IN 'logfile'" -> SHOW BINLOG EVENTS IN 'logfile'
"SHOW BINLOG EVENTS IN 'logfile' FROM 4 LIMIT 2" -> SHOW BINLOG EVENTS IN 'logfile' FROM 4 LIMIT 2
[assistant] The four requested cases work, and the binlog form is unchanged. `SHOW COLUMNS IN t` still fails because the table-target branch only accepts `FROM`. That was already true before this change and falls outside the `SHOW TABLES` request, so I'm leaving it alone. Next I'll check the remaining `SHOW` forms and run the suite.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SHOW INDEX IN t','SHOW COLUMNS FROM t','SHOW TABLE STATUS IN db LIKE \\'x%\\'']:\n    print(repr(s), '->', sqlglot.parse_one(s, dialect='mysql').sql('mysql'))\n\" ; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Check other SHOW forms and run the test suite"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 4, in <module>
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-135649-mysql-mariadb-show-tables-in-sch/base-1/sqlglot/__init__.py", line 176, in parse_one
    result = dialect.parse(sql, **opts)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-135649-mysql-mariadb-show-tables-in-sch/base-1/sqlglot/dialects/dialect.py", line 1116, in parse
    return self.p
…[1708 chars elided]…
[ 63%]
.......... [ 64%]
..................................... [ 68%]
............................................... [ 72%]
.................................................................................................................... [ 83%]
.............................................................................. [ 90%]
............................... [ 93%]
.......................................................................... [100%]
1089 passed, 17847 subtests passed in 53.91s
[assistant] The full suite passes (1089 tests). `SHOW INDEX IN t` fails in the same place as `SHOW COLUMNS IN t`, which is the table-target limitation noted above. Next I'll add a regression test next to the existing `SHOW` tests.
[tool_use Bash] {"command": "grep -n \"SHOW TABLES\\|SHOW FULL TABLES\" tests/dialects/test_mysql.py | head; sed -n 1215,1230p tests/dialects/test_mysql.py", "description": "Find existing SHOW TABLES tests for placement"}
[tool_result] 2 matches in 1 files:

tests/dialects/test_mysql.py:1404:show = self.validate_identity("SHOW TABLES")
tests/dialects/test_mysql.py:1408:show = self.validate_identity("SHOW FULL TABLES FROM db_name LIKE '%foo%'")
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
[tool_use Bash] {"command": "sed -n 1400,1412p tests/dialects/test_mysql.py", "description": "Read SHOW TABLES test block"}
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-135649-mysql-mariadb-show-tables-in-sch/base-1/tests/dialects/test_mysql.py", "old_string": "        show = self.validate_identity(\"SHOW FULL TABLES FROM db_name LIKE '%foo%'\")\n        self.assertTrue(show.args[\"full\"])\n        self.assertEqual(show.text(\"db\"), \"db_name\")\n        self.asse
…[414 chars elided]…
"like\"), \"%foo%\")\n\n        show = self.validate_identity(\"SHOW TABLES IN test\", \"SHOW TABLES FROM test\")\n        self.assertEqual(show.text(\"db\"), \"test\")\n\n        show = self.validate_identity(\"SHOW FULL TABLES IN test LIKE '%foo%'\", \"SHOW FULL TABLES FROM test LIKE '%foo%'\")\n        self.assertTrue(show.args[\"full\"])\n        self.assertEqual(show.text(\"db\"), \"test\")"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-135649-mysql-mariadb-show-tables-in-sch/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -3; (<work>/env-sqlglot/bin/ruff format --check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py && <work>/env-sqlglot/bin/ruff check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py) 2>&1 | tail -5", "description": "Run MySQL tests and ruff format/lint checks"}
[tool_result] .............................. [ 60%]
....................                                              [100%]
50 passed, 481 subtests passed in 0.19s
Would reformat: tests/dialects/test_mysql.py
1 file would be reformatted, 1 file already formatted
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/ruff format tests/dialects/test_mysql.py && git diff --stat && <work>/env-sqlglot/bin/ruff check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2", "description": "Apply ruff formatting, lint, and rerun full suite"}
[tool_result] 1 file reformatted
sqlglot/parsers/mysql.py     | 6 +++---
 tests/dialects/test_mysql.py | 9 +++++++++
 2 files changed, 12 insertions(+), 3 deletions(-)
All checks passed!
.......................................................................... [100%]
1089 passed, 17847 subtests passed in 55.88s
[This command modified 1 file you've previously read: tests/dialects/test_mysql.py. Call Read before editing.]
[tool_use Bash] {"command": "git diff", "description": "Review the final diff"}
[tool_result] sqlglot/parsers/mysql.py     | 6 +++---
 tests/dialects/test_mysql.py | 9 +++++++++
 2 files changed, 12 insertions(+), 3 deletions(-)

--- Changes ---

sqlglot/parsers/mysql.py
  @@ -408,16 +408,16 @@ class MySQLParser(parser.Parser):
  -        log = self._parse_string() if self._match_text_seq("IN") else None
  -
           if this in ("BINLOG EVENTS", "RELAYLOG EVENTS"):
  +            log = self._parse_string() if self._match_text_seq("IN") else None
               position = self._parse_nu
…[535 chars elided]…
ntity("SHOW TABLES IN test", "SHOW TABLES FROM test")
  +        self.assertEqual(show.text("db"), "test")
  +
  +        show = self.validate_identity(
  +            "SHOW FULL TABLES IN test LIKE '%foo%'", "SHOW FULL TABLES FROM test LIKE '%foo%'"
  +        )
  +        self.assertTrue(show.args["full"])
  +        self.assertEqual(show.text("db"), "test")
  +
       def test_set_variable(self):
           cmd = self.parse_one("SET SESSION x = 1")
           item = cmd.expressions[0]
  +9 -0
[assistant] `SHOW TABLES IN test` now parses in MySQL and generates `SHOW TABLES FROM test`. The full suite passes (1089 tests), and ruff check and format are clean.

**Cause:** `_parse_show_mysql` in `sqlglot/parsers/mysql.py` checked for `IN` to read the binlog `log` argument before the database branch ran. That consumed the `IN` even when no string followed, and the database branch only accepted `FROM`.

**Change:**
- The `log` argument is now parsed only for `BINLOG EVENTS` and `RELAYLOG EVENTS`, which is where it applies.
- The database branch accepts `IN` as well as `FROM`.
- `SHOW BINLOG EVENTS IN 'logfile' FROM 4 LIMIT 2` still round-trips unchanged.
- I added cases to `test_show_tables` in `tests/dialects/test_mysql.py` for `SHOW TABLES IN test` and `SHOW FULL TABLES IN test LIKE '%foo%'`.

**Not covered:** `SHOW COLUMNS IN t` and `SHOW INDEX IN t` still fail. Their table-target branch only accepts `FROM`, and they failed before this change too. Supporting them would mean extending the target branch, which is a separate change, so I left it out.

The changes are uncommitted in the worktree.
