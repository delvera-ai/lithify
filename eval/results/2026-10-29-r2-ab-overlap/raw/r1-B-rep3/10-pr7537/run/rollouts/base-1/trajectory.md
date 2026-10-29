# trajectory base-1

final message:
MySQL's `SHOW TABLES IN <schema>` now parses and generates as `SHOW TABLES FROM <schema>`. The full suite passes (1089 tests), and ruff is clean.

**Cause:** the parser consumed `IN` as the log-file slot before checking for `FROM`. For `SHOW TABLES IN test`, `IN` was eaten, `test` was not a string, and the leftover token caused the error.

**Fix** (`sqlglot/parsers/mysql.py`, `_parse_show_mysql`):
- The log-file `IN` is only taken when a string literal follows. Otherwise the parser rewinds, so `IN` stays available.
- The database clause now accepts `FROM` or `IN`.
- `BINLOG EVENTS` / `RELAYLOG EVENTS` still take `IN '<file>'` as before.

**Results checked:**
- `SHOW TABLES IN test` → `SHOW TABLES FROM test`
- `SHOW FULL TABLES IN test LIKE 'a%'` → `SHOW FULL TABLES FROM test LIKE 'a%'`
- `SHOW BINLOG EVENTS IN 'logfile'` and `... FROM 1 LIMIT 2, 3` round-trip unchanged.
- `SHOW COLUMNS FROM t IN db` now parses too, generating `SHOW COLUMNS FROM t FROM db`. That form was also a parse error before.

**Tests:** I added `IN` cases to `test_show_tables` in `tests/dialects/test_mysql.py`, covering the plain and `FULL` forms. The existing binlog test still covers the `IN '<file>'` path.

The changes are uncommitted in the worktree.

## events
[tool_use Bash] {"command": "grep -n \"_parse_show_mysql\\|def _parse_show\\b\\|\\\"FROM\\\"\\|\\\"IN\\\"\" sqlglot/dialects/mysql.py | head -50", "description": "Locate SHOW parsing in MySQL dialect"}
[tool_result] 0 matches for '_parse_show_mysql\|def _parse_show\b\|"FROM"\|"IN"'
[tool_use Bash] {"command": "grep -rn \"SHOW\\|_parse_show\" sqlglot/dialects/mysql.py | head -40; echo ---; grep -n \"def _parse_show\\b\\|def _parse_show(\" -A30 sqlglot/parser.py | head -60; echo ---; grep -n \"class Show\\b\" -A30 sqlglot/expressions.py | head -40", "description": "Find SHOW parsing code and Show expression"}
[tool_result] sqlglot/dialects/mysql.py:154:        COMMANDS = {*tokens.Tokenizer.COMMANDS, TokenType.REPLACE} - {TokenType.SHOW}
---
8987:    def _parse_show(self) -> exp.Expr | None:
8988-        parser = self._find_parser(self.SHOW_PARSERS, self.SHOW_TRIE)
8989-        if parser:
8990-            return parser(self)
8991-        return self._parse_as_command(self._prev)
8992-
8993-    def _parse_set_item_assignment(self, kind: str | None = None) -> exp.Expr | None:
8994-        index = self._index
8995-
89
…[671 chars elided]…
.name)
9009-
9010-        this = self.expression(exp.EQ(this=left, expression=right))
9011-        return self.expression(exp.SetItem(this=this, kind=kind))
9012-
9013-    def _parse_set_transaction(self, global_: bool = False) -> exp.Expr:
9014-        self._match_text_seq("TRANSACTION")
9015-        characteristics = self._parse_csv(
9016-            lambda: self._parse_var_from_options(self.TRANSACTION_CHARACTERISTICS)
9017-        )
---
grep: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "grep -rn \"SHOW_PARSERS\\|def _parse_show_mysql\\|_parse_show_mysql\\|\\\"TABLES\\\"\" sqlglot/ | head -30", "description": "Find SHOW_PARSERS definitions"}
[tool_result] sqlglot/parsers/singlestore.py:193:    SHOW_PARSERS = {
sqlglot/parsers/singlestore.py:194:        **MySQLParser.SHOW_PARSERS,
sqlglot/parsers/singlestore.py:234:    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parsers/snowflake.py:805:    SHOW_PARSERS = {
sqlglot/parsers/snowflake.py:809:        "TABLES": _show_parser("TABLES"),
sqlglot/parsers/snowflake.py:822:        "ICEBERG TABLES": _show_parser("TABLES", iceberg=True),
sqlglot/parsers/snowflake.py:823:        "TERSE
…[890 chars elided]…
"),
sqlglot/parsers/mysql.py:240:    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parsers/mysql.py:395:    def _parse_show_mysql(
sqlglot/parser.py:1543:    SHOW_PARSERS: t.ClassVar[dict[str, t.Callable]] = {}
sqlglot/parser.py:1824:    SHOW_TRIE: t.ClassVar[dict] = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parser.py:8756:        elif self._match_text_seq("TABLES"):
sqlglot/parser.py:8988:        parser = self._find_parser(self.SHOW_PARSERS, self.SHOW_TRIE)
[tool_use Bash] {"command": "sed -n 395,470p sqlglot/parsers/mysql.py; echo ---; grep -n \"def _show_parser\" -A40 sqlglot/parsers/mysql.py | head -5; grep -n \"^def _show_parser\" -A40 sqlglot/parser.py | head -60", "description": "Read MySQL SHOW parsing logic"}
[tool_result]     def _parse_show_mysql(
        self,
        this: str,
        target: bool | str = False,
        full: bool | None = None,
        global_: bool | None = None,
    ) -> exp.Show:
        json = self._match_text_seq("JSON")

        if target:
            if isinstance(target, str):
                self._match_text_seq(*target.split(" "))
            target_id = self._parse_id_var()
        else:
            target_id = None

        log = self._parse_string() if self._match_text_seq("IN")
…[2148 chars elided]…

                limit=limit,
                mutex=mutex,
                for_table=for_table,
                for_group=for_group,
                for_user=for_user,
                for_role=for_role,
                into_outfile=into_outfile,
                json=json,
---
47:def _show_parser(*args: t.Any, **kwargs: t.Any) -> t.Callable[[MySQLParser], exp.Show]:
48-    def _parse(self: MySQLParser) -> exp.Show:
49-        return self._parse_show_mysql(*args, **kwargs)
50-
51-    return _parse
[tool_use Bash] {"command": "grep -rn \"SHOW.* IN \\|SHOW.* IN'\" tests/ | head -40; echo ---; sed -n 170,240p sqlglot/parsers/mysql.py", "description": "Find existing SHOW IN tests and parser table"}
[tool_result] tests/dialects/test_snowflake.py:5200:        ast = parse_one("SHOW DATABASES IN ACCOUNT", read="snowflake")
tests/dialects/test_snowflake.py:5206:        self.validate_identity("SHOW FILE FORMATS LIKE 'foo' IN DATABASE db1")
tests/dialects/test_snowflake.py:5207:        self.validate_identity("SHOW FILE FORMATS LIKE 'foo' IN SCHEMA db1.schema1")
tests/dialects/test_snowflake.py:5209:        ast = parse_one("SHOW FILE FORMATS IN ACCOUNT", read="snowflake")
tests/dialects/test_snowflake.py:5215: 
…[7056 chars elided]…
S = {
        **parser.Parser.SET_PARSERS,
        "PERSIST": lambda self: self._parse_set_item_assignment("PERSIST"),
        "PERSIST_ONLY": lambda self: self._parse_set_item_assignment("PERSIST_ONLY"),
        "CHARACTER SET": lambda self: self._parse_set_item_charset("CHARACTER SET"),
        "CHARSET": lambda self: self._parse_set_item_charset("CHARACTER SET"),
        "NAMES": lambda self: self._parse_set_item_names(),
    }

    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
[tool_use Bash] {"command": "grep -n \"def show_sql\" -A60 sqlglot/generators/mysql.py | head -80; echo ---; grep -rn \"BINLOG EVENTS IN\\|RELAYLOG EVENTS IN\\|SHOW.*IN '\" tests/dialects/test_mysql.py | head", "description": "Read MySQL show generator and related tests"}
[tool_result] 656:    def show_sql(self, expression: exp.Show) -> str:
657-        this = f" {expression.name}"
658-        full = " FULL" if expression.args.get("full") else ""
659-        global_ = " GLOBAL" if expression.args.get("global_") else ""
660-
661-        target = self.sql(expression, "target")
662-        target = f" {target}" if target else ""
663-        if expression.name in ("COLUMNS", "INDEX"):
664-            target = f" FROM{target}"
665-        elif expression.name == "GRANTS":
666-     
…[2250 chars elided]…
 from Doris, because it's the same for all MySQL, Doris, and StarRocks.
710-        """
711-        return super().alterrename_sql(expression, include_to=False)
712-
713-    def altercolumn_sql(self, expression: exp.AlterColumn) -> str:
714-        dtype = self.sql(expression, "dtype")
715-        if not dtype:
716-            return super().altercolumn_sql(expression)
---
tests/dialects/test_mysql.py:1223:            show = self.validate_identity(f"SHOW {key} EVENTS IN 'log' FROM 1 LIMIT 2, 3")
[tool_use Bash] {"command": "grep -n \"def _match_set\\|def _match_text_seq\\|def _retreat\" -A3 sqlglot/parser.py | head -20; grep -n \"TokenType.IN\\b\" sqlglot/tokens.py | head -3", "description": "Check parser helper signatures"}
[tool_result] 1892:    def _retreat(self, index: i64) -> None:
1893-        if index != self._index:
1894-            self._advance(index - self._index)
1895-
--
1911:    def _match_set(self, types: t.Collection[TokenType], advance: bool = True) -> bool:
1912-        if self._curr.token_type in types:
1913-            if advance:
1914-                self._advance()
--
1934:    def _match_text_seq(self, *texts: str, advance: bool = True) -> bool:
1935-        index = self._index
1936-        string_type = TokenType.STRING
1937-        for text in texts:
1 matches in 1 files:

296:0:TokenType.IN,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-175009-mysql-mariadb-show-tables-in-sch/base-1/sqlglot/parsers/mysql.py", "old_string": "        log = self._parse_string() if self._match_text_seq(\"IN\") else None\n\n        if this in (\"BINLOG EVENTS\", \"RELAYLOG EVENTS\"):\n            position = self._parse_number() if self._match_text_seq(\"
…[248 chars elided]…
ch_text_seq(\"IN\") else None\n        if log is None:\n            self._retreat(index)\n\n        if this in (\"BINLOG EVENTS\", \"RELAYLOG EVENTS\"):\n            position = self._parse_number() if self._match_text_seq(\"FROM\") else None\n            db = None\n        else:\n            position = None\n            db = None\n\n            if self._match_set((TokenType.FROM, TokenType.IN)):"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-175009-mysql-mariadb-show-tables-in-sch/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[assistant] Now let me verify the behavior across the cases in the request, and add tests.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SHOW TABLES IN test','SHOW FULL TABLES IN test','SHOW TABLES FROM test','SHOW COLUMNS FROM t IN db','SHOW BINLOG EVENTS IN \\'logfile\\'','SHOW BINLOG EVENTS IN \\'logfile\\' FROM 1 LIMIT 2, 3','SHOW TABLES IN test LIKE \\'a%\\'']:\n    print(repr(sqlglot.parse_one(s, dialect='mysql').sql('mysql')))\n\"; grep -n \"SHOW TABLES\" tests/dialects/test_mysql.py | head", "description": "Check SHOW IN behavior for several forms"}
[tool_result] 'SHOW TABLES FROM test'
'SHOW FULL TABLES FROM test'
'SHOW TABLES FROM test'
'SHOW COLUMNS FROM t FROM db'
"SHOW BINLOG EVENTS IN 'logfile'"
"SHOW BINLOG EVENTS IN 'logfile' FROM 1 LIMIT 2, 3"
"SHOW TABLES FROM test LIKE 'a%'"
1 matches in 1 files:

tests/dialects/test_mysql.py:1404:show = self.validate_identity("SHOW TABLES")
[tool_use Bash] {"command": "sed -n 1400,1415p tests/dialects/test_mysql.py", "description": "View existing SHOW TABLES test"}
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

    def test_set_variable(self):
        cmd = self.parse_one("SET SESSION x = 1")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-175009-mysql-mariadb-show-tables-in-sch/base-1/tests/dialects/test_mysql.py", "old_string": "        self.assertEqual(show.text(\"like\"), \"%foo%\")\n\n    def test_set_variable(self):", "new_string": "        self.assertEqual(show.text(\"like\"), \"%foo%\")\n\n        show = self.validate_identity(\"SHOW TABLES IN db_name\", \"SHOW TABLES FROM db_name\")\n        self.assertEqual(show.text(\"db\"), \"db_name\")\n\n        show = self.validate_identity(\"SHOW FULL TABLES IN db_name LIKE '%foo%'\", \"SHOW FULL TABLES FROM db_name LIKE '%foo%'\")\n        self.assertTrue(show.args[\"full\"])\n        self.assertEqual(show.text(\"db\"), \"db_name\")\n\n    def test_set_variable(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-175009-mysql-mariadb-show-tables-in-sch/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full project test suite"}
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
1089 passed, 17847 subtests passed in 47.02s
[assistant] All 1089 tests pass. Now the formatter and linter, since the new test line is long.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff format sqlglot/parsers/mysql.py tests/dialects/test_mysql.py && <work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py) 2>&1 | tail -5; git diff --stat", "description": "Format and lint changed files"}
[tool_result] 1 file reformatted, 1 file left unchanged
All checks passed!
sqlglot/parsers/mysql.py     | 5 ++++-
 tests/dialects/test_mysql.py | 9 +++++++++
 2 files changed, 13 insertions(+), 1 deletion(-)
[This command modified 1 file you've previously read: tests/dialects/test_mysql.py. Call Read before editing.]
[tool_use Bash] {"command": "git diff && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -2", "description": "Review final diff and rerun MySQL tests"}
[tool_result] sqlglot/parsers/mysql.py     | 5 ++++-
 tests/dialects/test_mysql.py | 9 +++++++++
 2 files changed, 13 insertions(+), 1 deletion(-)

--- Changes ---

sqlglot/parsers/mysql.py
  @@ -408,7 +408,10 @@ class MySQLParser(parser.Parser):
  +        index = self._index
           log = self._parse_string() if self._match_text_seq("IN") else None
  +        if log is None:
  +            self._retreat(index)
   
           if this in ("BINLOG EVENTS", "RELAYLOG EVENTS"):
               position = self.
…[603 chars elided]…
show = self.validate_identity(
  +            "SHOW FULL TABLES IN db_name LIKE '%foo%'", "SHOW FULL TABLES FROM db_name LIKE '%foo%'"
  +        )
  +        self.assertTrue(show.args["full"])
  +        self.assertEqual(show.text("db"), "db_name")
  +
       def test_set_variable(self):
           cmd = self.parse_one("SET SESSION x = 1")
           item = cmd.expressions[0]
  +9 -0
....................                                              [100%]
50 passed, 481 subtests passed in 0.16s
[assistant] MySQL's `SHOW TABLES IN <schema>` now parses and generates as `SHOW TABLES FROM <schema>`. The full suite passes (1089 tests), and ruff is clean.

**Cause:** the parser consumed `IN` as the log-file slot before checking for `FROM`. For `SHOW TABLES IN test`, `IN` was eaten, `test` was not a string, and the leftover token caused the error.

**Fix** (`sqlglot/parsers/mysql.py`, `_parse_show_mysql`):
- The log-file `IN` is only taken when a string literal follows. Otherwise the parser rewinds, so `IN` stays available.
- The database clause now accepts `FROM` or `IN`.
- `BINLOG EVENTS` / `RELAYLOG
…[44 chars elided]…


**Results checked:**
- `SHOW TABLES IN test` → `SHOW TABLES FROM test`
- `SHOW FULL TABLES IN test LIKE 'a%'` → `SHOW FULL TABLES FROM test LIKE 'a%'`
- `SHOW BINLOG EVENTS IN 'logfile'` and `... FROM 1 LIMIT 2, 3` round-trip unchanged.
- `SHOW COLUMNS FROM t IN db` now parses too, generating `SHOW COLUMNS FROM t FROM db`. That form was also a parse error before.

**Tests:** I added `IN` cases to `test_show_tables` in `tests/dialects/test_mysql.py`, covering the plain and `FULL` forms. The existing binlog test still covers the `IN '<file>'` path.

The changes are uncommitted in the worktree.
