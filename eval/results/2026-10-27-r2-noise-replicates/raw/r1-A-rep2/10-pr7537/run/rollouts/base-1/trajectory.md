# trajectory base-1

final message:
`SHOW TABLES IN test` now parses for MySQL and generates as `SHOW TABLES FROM test`. The full suite passes (1089 tests), and `SHOW BINLOG EVENTS IN 'logfile'` still round-trips unchanged.

**Cause:** in `sqlglot/parsers/mysql.py`, `_parse_show_mysql` consumed `IN` up front to look for a log-file string. For `SHOW TABLES IN test` it ate the `IN`, found no string, and left `test` unparsed. Only the `FROM` branch handled the database name.

**Change:**
- The `IN 'logfile'` check now runs only for `BINLOG EVENTS` / `RELAYLOG EVENTS`, where it belongs.
- For all other SHOW forms, `IN` is accepted as a synonym for `FROM` when reading the database name.

**Behaviour change to be aware of:** `SHOW TABLES IN 'x'` (a quoted string after a non-binlog SHOW) used to parse as a log reference and now raises a parse error. That form isn't valid MySQL, so I treated it as acceptable.

**Tests:** I added two cases to `test_show_tables` in `tests/dialects/test_mysql.py`: `SHOW TABLES IN test` and `SHOW FULL TABLES IN db_name LIKE '%foo%'`. Ruff check and format are clean.

Nothing is committed. Say if you want a commit with the Co-Authored-By line.

## events
[tool_use Bash] {"command": "grep -n \"SHOW\\|_parse_show_mysql\\|def _parse_show\" sqlglot/dialects/mysql.py | head -80", "description": "Find SHOW parsing code in MySQL dialect"}
[tool_result] 154:        COMMANDS = {*tokens.Tokenizer.COMMANDS, TokenType.REPLACE} - {TokenType.SHOW}
[tool_use Bash] {"command": "grep -n \"SHOW\" sqlglot/dialects/mysql.py | head -60; grep -n \"_parse_show_mysql\\|def _parse_show\\b\\|SHOW_PARSERS\\|def _parse_show\" sqlglot/parser.py | head; grep -n \"\\\"TABLES\\\"\\|\\\"BINLOG\\\"\\|\\\"EVENTS\\\"\" sqlglot/dialects/mysql.py", "description": "Locate SHOW-related parser code"}
[tool_result] 154:        COMMANDS = {*tokens.Tokenizer.COMMANDS, TokenType.REPLACE} - {TokenType.SHOW}
1543:    SHOW_PARSERS: t.ClassVar[dict[str, t.Callable]] = {}
1824:    SHOW_TRIE: t.ClassVar[dict] = new_trie(key.split(" ") for key in SHOW_PARSERS)
8987:    def _parse_show(self) -> exp.Expr | None:
8988:        parser = self._find_parser(self.SHOW_PARSERS, self.SHOW_TRIE)
[tool_use Bash] {"command": "grep -rn \"SHOW_PARSERS\\|_parse_show_mysql\\|def _parse_show\" sqlglot/dialects/mysql.py; grep -n \"def _parse_show_mysql\" -A 60 sqlglot/dialects/mysql.py; grep -n \"def _parse_show\\b\" -A 8 sqlglot/parser.py; grep -n \"\\\"TABLES\\\"\\|\\\"BINLOG\\\"\\|\\\"EVENTS\\\"\" sqlglot/parser.py", "description": "Read MySQL SHOW parser implementation"}
[tool_result] 8987:    def _parse_show(self) -> exp.Expr | None:
8988-        parser = self._find_parser(self.SHOW_PARSERS, self.SHOW_TRIE)
8989-        if parser:
8990-            return parser(self)
8991-        return self._parse_as_command(self._prev)
8992-
8993-    def _parse_set_item_assignment(self, kind: str | None = None) -> exp.Expr | None:
8994-        index = self._index
8995-
8756:        elif self._match_text_seq("TABLES"):
[tool_use Bash] {"command": "grep -rn \"SHOW_PARSERS\\|_show_parser\\|def _parse_show\" sqlglot/ | head -30; grep -n \"class Show\\b\" -A 30 sqlglot/expressions/*.py | head -5", "description": "Find SHOW parser definitions across sqlglot"}
[tool_result] sqlglot/parser.py:1543:    SHOW_PARSERS: t.ClassVar[dict[str, t.Callable]] = {}
sqlglot/parser.py:1824:    SHOW_TRIE: t.ClassVar[dict] = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parser.py:8987:    def _parse_show(self) -> exp.Expr | None:
sqlglot/parser.py:8988:        parser = self._find_parser(self.SHOW_PARSERS, self.SHOW_TRIE)
sqlglot/parsers/snowflake.py:318:def _show_parser(*args: t.Any, **kwargs: t.Any) -> t.Callable[[SnowflakeParser], exp.Show]:
sqlglot/parsers/snowflake.p
…[1863 chars elided]…
LES": _show_parser("TABLES", terse=True),
sqlglot/parsers/snowflake.py:828:        "TERSE VIEWS": _show_parser("VIEWS", terse=True),
sqlglot/parsers/snowflake.py:829:        "TERSE SEQUENCES": _show_parser("SEQUENCES", terse=True),
sqlglot/expressions/ddl.py:191:class Show(Expression):
sqlglot/expressions/ddl.py-192-    arg_types = {
sqlglot/expressions/ddl.py-193-        "this": True,
sqlglot/expressions/ddl.py-194-        "history": False,
sqlglot/expressions/ddl.py-195-        "terse": False,
[tool_use Bash] {"command": "ls sqlglot/parsers/ | head -50; grep -n \"SHOW\\|_parse_show\" sqlglot/parsers/mysql.py | head -60; grep -n \"_parse_show\\|def _show_parser\\|def _parse_show\" -n sqlglot/parsers/*.py | head -40", "description": "Inspect MySQL parser and show-related helpers"}
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
49:        return self._parse_show_mysql(*args, **kwargs)
167:        TokenType.SHOW: lambda self: self._parse_show(),
170:    SHOW_PARSERS
…[694 chars elided]…
rs/mysql.py:167:        TokenType.SHOW: lambda self: self._parse_show(),
sqlglot/parsers/mysql.py:395:    def _parse_show_mysql(
sqlglot/parsers/snowflake.py:318:def _show_parser(*args: t.Any, **kwargs: t.Any) -> t.Callable[[SnowflakeParser], exp.Show]:
sqlglot/parsers/snowflake.py:320:        return self._parse_show_snowflake(*args, **kwargs)
sqlglot/parsers/snowflake.py:753:        TokenType.SHOW: lambda self: self._parse_show(),
sqlglot/parsers/snowflake.py:1129:    def _parse_show_snowflake(
[tool_use Bash] {"command": "sed -n 40,55p sqlglot/parsers/mysql.py; sed -n 165,245p sqlglot/parsers/mysql.py; sed -n 390,470p sqlglot/parsers/mysql.py", "description": "Read MySQL SHOW parser details"}
[tool_result]     if mysql_date_format and _has_time_specifier(mysql_date_format.name):
        return exp.StrToTime(this=this, format=date_format)

    return exp.StrToDate(this=this, format=date_format)


def _show_parser(*args: t.Any, **kwargs: t.Any) -> t.Callable[[MySQLParser], exp.Show]:
    def _parse(self: MySQLParser) -> exp.Show:
        return self._parse_show_mysql(*args, **kwargs)

    return _parse


class MySQLParser(parser.Parser):
    NO_PAREN_FUNCTIONS = {
    STATEMENT_PARSERS = {
        *
…[6494 chars elided]…
         position=position,
                db=db,
                channel=channel,
                like=like,
                where=where,
                types=types,
                query=query,
                offset=offset,
                limit=limit,
                mutex=mutex,
                for_table=for_table,
                for_group=for_group,
                for_user=for_user,
                for_role=for_role,
                into_outfile=into_outfile,
                json=json,
[tool_use Bash] {"command": "grep -n \"SHOW\" tests/dialects/test_mysql.py | head -80; grep -n \"def show_sql\" -A 60 sqlglot/generators/mysql.py | head -90", "description": "Check MySQL SHOW tests and generator"}
[tool_result] 1213:            show = self.validate_identity(f"SHOW {key}", f"SHOW {write_key}")
1219:            show = self.validate_identity(f"SHOW {key} EVENTS")
1223:            show = self.validate_identity(f"SHOW {key} EVENTS IN 'log' FROM 1 LIMIT 2, 3")
1229:            show = self.validate_identity(f"SHOW {key} EVENTS LIMIT 1")
1250:            template = "SHOW {}"
1255:            template = "SHOW {} LIKE '%foo%'"
1261:            template = "SHOW {} WHERE Column_name LIKE '%foo%'"
1268:        show
…[4455 chars elided]…
ename, include_to: bool = True) -> str:
708-        """To avoid TO keyword in ALTER ... RENAME statements.
709-        It's moved from Doris, because it's the same for all MySQL, Doris, and StarRocks.
710-        """
711-        return super().alterrename_sql(expression, include_to=False)
712-
713-    def altercolumn_sql(self, expression: exp.AlterColumn) -> str:
714-        dtype = self.sql(expression, "dtype")
715-        if not dtype:
716-            return super().altercolumn_sql(expression)
[tool_use Bash] {"command": "grep -n \"def _match_text_seq\" -A 15 sqlglot/parser.py; grep -n \"def _match_texts\" -A 6 sqlglot/parser.py; sed -n 1205,1232p tests/dialects/test_mysql.py", "description": "Check token matching helpers and binlog tests"}
[tool_result] 1934:    def _match_text_seq(self, *texts: str, advance: bool = True) -> bool:
1935-        index = self._index
1936-        string_type = TokenType.STRING
1937-        for text in texts:
1938-            if self._curr.token_type != string_type and self._curr.text.upper() == text:
1939-                self._advance()
1940-            else:
1941-                self._retreat(index)
1942-                return False
1943-
1944-        if not advance:
1945-            self._retreat(index)
1946-
194
…[1089 chars elided]…
ENTS")

            show = self.validate_identity(f"SHOW {key} EVENTS IN 'log' FROM 1 LIMIT 2, 3")
            self.assertEqual(show.text("log"), "log")
            self.assertEqual(show.text("position"), "1")
            self.assertEqual(show.text("limit"), "3")
            self.assertEqual(show.text("offset"), "2")

            show = self.validate_identity(f"SHOW {key} EVENTS LIMIT 1")
            self.assertEqual(show.text("limit"), "1")
            self.assertIsNone(show.args.get("offset"))
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-161607-mysql-mariadb-show-tables-in-sch/base-1/sqlglot/parsers/mysql.py", "old_string": "        log = self._parse_string() if self._match_text_seq(\"IN\") else None\n\n        if this in (\"BINLOG EVENTS\", \"RELAYLOG EVENTS\"):\n            position = self._parse_number() if self._match_text_seq(\"
…[198 chars elided]…
OG EVENTS\", \"RELAYLOG EVENTS\"):\n            log = self._parse_string() if self._match_text_seq(\"IN\") else None\n            position = self._parse_number() if self._match_text_seq(\"FROM\") else None\n            db = None\n        else:\n            log = None\n            position = None\n            db = None\n\n            if self._match(TokenType.FROM) or self._match_text_seq(\"IN\"):"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-161607-mysql-mariadb-show-tables-in-sch/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[assistant] Now a test in the MySQL dialect file, next to the existing `SHOW TABLES` assertions.
[tool_use Bash] {"command": "sed -n 1402,1416p tests/dialects/test_mysql.py", "description": "View SHOW TABLES tests"}
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
        cmd = self.parse_one("SET SESSION x = 1")
        item = cmd.expressions[0]
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-161607-mysql-mariadb-show-tables-in-sch/base-1/tests/dialects/test_mysql.py", "old_string": "        self.assertEqual(show.text(\"like\"), \"%foo%\")\n\n    def test_set_variable(self):", "new_string": "        self.assertEqual(show.text(\"like\"), \"%foo%\")\n\n        show = self.validate_identity(\"SHOW TABLES IN test\", \"SHOW TABLES FROM test\")\n        self.assertEqual(show.text(\"db\"), \"test\")\n\n        show = self.validate_identity(\"SHOW FULL TABLES IN db_name LIKE '%foo%'\", \"SHOW FULL TABLES FROM db_name LIKE '%foo%'\")\n        self.assertTrue(show.args[\"full\"])\n        self.assertEqual(show.text(\"db\"), \"db_name\")\n\n    def test_set_variable(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-161607-mysql-mariadb-show-tables-in-sch/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -30", "description": "Run MySQL dialect tests"}
[tool_result] .............................. [ 60%]
....................                                              [100%]
50 passed, 481 subtests passed in 0.54s
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SHOW TABLES IN test', \\\"SHOW BINLOG EVENTS IN 'logfile'\\\", 'SHOW FULL TABLES IN db LIKE \\'%x%\\'']:\n    print(sqlglot.transpile(s, read='mysql', write='mysql'))\n\"; (ruff --version >/dev/null 2>&1 && ruff check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py && ruff format --check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py) 2>&1 | tail -5", "description": "Run full test suite, spot-check output, lint"}
[tool_result] ......................................................................................................................................................................... [ 35%]
.......................................................................................................................................... [ 48%]
.............................................. [ 52%]
.................... [ 54%]
...................................................... [ 59%]
.......... [ 60%]
...............
…[245 chars elided]…
..................... [ 83%]
.............................................................................. [ 90%]
............................... [ 93%]
.......................................................................... [100%]
1089 passed, 17847 subtests passed in 58.44s
['SHOW TABLES FROM test']
["SHOW BINLOG EVENTS IN 'logfile'"]
["SHOW FULL TABLES FROM db LIKE '%x%'"]
All checks passed!
Would reformat: tests/dialects/test_mysql.py
1 file would be reformatted, 1 file already formatted
[tool_use Bash] {"command": "ruff format tests/dialects/test_mysql.py && git diff --stat && git diff", "description": "Apply formatting and review final diff"}
[tool_result] 1 file reformatted
 sqlglot/parsers/mysql.py     | 6 +++---
 tests/dialects/test_mysql.py | 9 +++++++++
 2 files changed, 12 insertions(+), 3 deletions(-)
diff --git a/sqlglot/parsers/mysql.py b/sqlglot/parsers/mysql.py
index d8abbea52..bc2a54985 100644
--- a/sqlglot/parsers/mysql.py
+++ b/sqlglot/parsers/mysql.py
@@ -408,16 +408,16 @@ class MySQLParser(parser.Parser):
         else:
             target_id = None
 
-        log = self._parse_string() if self._match_text_seq("IN") else None
-
   
…[1040 chars elided]…
"db"), "test")
+
+        show = self.validate_identity(
+            "SHOW FULL TABLES IN db_name LIKE '%foo%'", "SHOW FULL TABLES FROM db_name LIKE '%foo%'"
+        )
+        self.assertTrue(show.args["full"])
+        self.assertEqual(show.text("db"), "db_name")
+
     def test_set_variable(self):
         cmd = self.parse_one("SET SESSION x = 1")
         item = cmd.expressions[0]
[This command modified 1 file you've previously read: tests/dialects/test_mysql.py. Call Read before editing.]
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -2", "description": "Re-run MySQL dialect tests after formatting"}
[tool_result] ....................                                              [100%]
50 passed, 481 subtests passed in 0.22s
[assistant] `SHOW TABLES IN test` now parses for MySQL and generates as `SHOW TABLES FROM test`. The full suite passes (1089 tests), and `SHOW BINLOG EVENTS IN 'logfile'` still round-trips unchanged.

**Cause:** in `sqlglot/parsers/mysql.py`, `_parse_show_mysql` consumed `IN` up front to look for a log-file string. For `SHOW TABLES IN test` it ate the `IN`, found no string, and left `test` unparsed. Only the `FROM` branch handled the database name.

**Change:**
- The `IN 'logfile'` check now runs only for `BINLOG EVENTS` / `RELAYLOG EVENTS`, where it belongs.
- For all other SHOW forms, `IN` is accepted as a synonym for `FROM` when reading the database name.

**Behaviour change to be aware of:** `SHOW TABLES IN 'x'` (a quoted string after a non-binlog SHOW) used to parse as a log reference and now raises a parse error. That form isn't valid MySQL, so I treated it as acceptable.

**Tests:** I added two cases to `test_show_tables` in `tests/dialects/test_mysql.py`: `SHOW TABLES IN test` and `SHOW FULL TABLES IN db_name LIKE '%foo%'`. Ruff check and format are clean.

Nothing is committed. Say if you want a commit with the Co-Authored-By line.
