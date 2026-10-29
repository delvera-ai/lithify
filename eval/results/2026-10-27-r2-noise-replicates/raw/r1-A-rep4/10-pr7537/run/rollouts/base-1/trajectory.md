# trajectory base-1

final message:
`SHOW TABLES IN test` now parses in the MySQL dialect and generates `SHOW TABLES FROM test`. The full suite passes (1089 tests) and ruff is clean.

**Cause:** `_parse_show_mysql` in `sqlglot/parsers/mysql.py` consumed `IN` up front to read a binlog file name. For non-binlog statements it then never saw `FROM`, so the parse failed.

**Fix:**
- `IN 'logfile'` is now read only for `BINLOG EVENTS` and `RELAYLOG EVENTS`, so `SHOW BINLOG EVENTS IN 'logfile' FROM 1` round-trips unchanged.
- For every other SHOW form, `IN` is accepted as a synonym for `FROM` before the database name.

**Test:** I added two round-trip checks to `test_show_tables` in `tests/dialects/test_mysql.py`: `SHOW TABLES IN test` and `SHOW FULL TABLES IN db_name LIKE '%foo%'`. No existing test was changed.

One side effect: `SHOW COLUMNS FROM tbl IN db` now parses and generates `SHOW COLUMNS FROM tbl FROM db`. That was previously a parse error, and it is valid MySQL.

Not covered: `SHOW COLUMNS IN tbl` (with `IN` in place of the first `FROM`) still fails. Those entries parse their target with `target="FROM"`, which only matches `FROM`. I left it alone since it was outside the request.

## events
[tool_use Bash] {"command": "grep -n \"SHOW\\|_parse_show\" sqlglot/dialects/mysql.py | head -80", "description": "Find SHOW handling in MySQL dialect"}
[tool_result] 154:        COMMANDS = {*tokens.Tokenizer.COMMANDS, TokenType.REPLACE} - {TokenType.SHOW}
[tool_use Bash] {"command": "grep -n \"def _parse_show\\|SHOW_PARSERS\\|_parse_show_mysql\\|\\\"FROM\\\"\\|\\\"IN\\\"\" sqlglot/dialects/mysql.py sqlglot/parser.py | head -60", "description": "Locate SHOW parser definitions"}
[tool_result] sqlglot/parser.py:1543:    SHOW_PARSERS: t.ClassVar[dict[str, t.Callable]] = {}
sqlglot/parser.py:1824:    SHOW_TRIE: t.ClassVar[dict] = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parser.py:3131:            for_or_in = "IN"
sqlglot/parser.py:3573:                    files=self._match_text_seq("FROM", "FILES")
sqlglot/parser.py:4744:            if self._match_text_seq("ROWS", "FROM")
sqlglot/parser.py:4830:        elif self._match_text_seq("CONTAINED", "IN"):
sqlglot/parser.py:5517:
…[117 chars elided]…
M"):
sqlglot/parser.py:7952:        if self._match_text_seq("IN", "NATURAL", "LANGUAGE", "MODE"):
sqlglot/parser.py:7956:        elif self._match_text_seq("IN", "BOOLEAN", "MODE"):
sqlglot/parser.py:8987:    def _parse_show(self) -> exp.Expr | None:
sqlglot/parser.py:8988:        parser = self._find_parser(self.SHOW_PARSERS, self.SHOW_TRIE)
sqlglot/parser.py:9518:        if not securable or not self._match_text_seq("FROM"):
sqlglot/parser.py:9553:                from_=_parse_overlay_arg("FROM"),
[tool_use Bash] {"command": "grep -n \"_parse_show_mysql\\|SHOW_PARSERS\\|def _parse_show\" sqlglot/dialects/mysql.py; grep -n \"def _parse_show_mysql\" -A 60 sqlglot/dialects/mysql.py | head -90", "description": "Read MySQL SHOW parser implementation"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -rn \"_parse_show_mysql\\|\\\"TABLES\\\"\\|SHOW_PARSERS\\[\" sqlglot/ | head; grep -n \"def _parse_show_mysql\" -A 70 sqlglot/dialects/mysql.py | head -100", "description": "Find MySQL SHOW TABLES parsing code"}
[tool_result] sqlglot/parser.py:8756:        elif self._match_text_seq("TABLES"):
sqlglot/parsers/snowflake.py:809:        "TABLES": _show_parser("TABLES"),
sqlglot/parsers/snowflake.py:822:        "ICEBERG TABLES": _show_parser("TABLES", iceberg=True),
sqlglot/parsers/snowflake.py:823:        "TERSE ICEBERG TABLES": _show_parser("TABLES", terse=True, iceberg=True),
sqlglot/parsers/snowflake.py:827:        "TERSE TABLES": _show_parser("TABLES", terse=True),
sqlglot/parsers/snowflake.py:855:    SCHEMA_KINDS = {"OBJECTS", "TABLES", "VIEWS", "SEQUENCES", "UNIQUE KEYS", "IMPORTED KEYS"}
sqlglot/parsers/duckdb.py:98:        "TABLES": _show_parser("TABLES"),
sqlglot/parsers/mysql.py:49:        return self._parse_show_mysql(*args, **kwargs)
sqlglot/parsers/mysql.py:216:        "FULL TABLES": _show_parser("TABLES", full=True),
sqlglot/parsers/mysql.py:217:        "TABLES": _show_parser("TABLES"),
[tool_use Bash] {"command": "sed -n 40,60p sqlglot/parsers/mysql.py; grep -n \"def _parse_show_mysql\" -A 80 sqlglot/parsers/mysql.py", "description": "Read MySQL SHOW parsing functions"}
[tool_result]     if mysql_date_format and _has_time_specifier(mysql_date_format.name):
        return exp.StrToTime(this=this, format=date_format)

    return exp.StrToDate(this=this, format=date_format)


def _show_parser(*args: t.Any, **kwargs: t.Any) -> t.Callable[[MySQLParser], exp.Show]:
    def _parse(self: MySQLParser) -> exp.Show:
        return self._parse_show_mysql(*args, **kwargs)

    return _parse


class MySQLParser(parser.Parser):
    NO_PAREN_FUNCTIONS = {
        **parser.Parser.NO_PAREN_FU
…[2947 chars elided]…
       types=types,
461-                query=query,
462-                offset=offset,
463-                limit=limit,
464-                mutex=mutex,
465-                for_table=for_table,
466-                for_group=for_group,
467-                for_user=for_user,
468-                for_role=for_role,
469-                into_outfile=into_outfile,
470-                json=json,
471-                global_=global_,
472-            )
473-        )
474-
475-    def _parse_oldstyle_limit(
[tool_use Bash] {"command": "grep -n \"def show_sql\" -A 60 sqlglot/generators/mysql.py; grep -rn \"IN '\\|IN \\w* \\|SHOW.* IN \" tests/dialects/test_mysql.py | grep -i show", "description": "Read MySQL show generator and IN-form tests"}
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
…[2246 chars elided]…
oved from Doris, because it's the same for all MySQL, Doris, and StarRocks.
710-        """
711-        return super().alterrename_sql(expression, include_to=False)
712-
713-    def altercolumn_sql(self, expression: exp.AlterColumn) -> str:
714-        dtype = self.sql(expression, "dtype")
715-        if not dtype:
716-            return super().altercolumn_sql(expression)
tests/dialects/test_mysql.py:1223:            show = self.validate_identity(f"SHOW {key} EVENTS IN 'log' FROM 1 LIMIT 2, 3")
[tool_use Bash] {"command": "sed -n 200,260p sqlglot/parsers/mysql.py", "description": "Read MySQL SHOW_PARSERS table"}
[tool_result]         "PROCEDURE CODE": _show_parser("PROCEDURE CODE", target=True),
        "PROCEDURE STATUS": _show_parser("PROCEDURE STATUS"),
        "PRIVILEGES": _show_parser("PRIVILEGES"),
        "FULL PROCESSLIST": _show_parser("PROCESSLIST", full=True),
        "PROCESSLIST": _show_parser("PROCESSLIST"),
        "PROFILE": _show_parser("PROFILE"),
        "PROFILES": _show_parser("PROFILES"),
        "RELAYLOG EVENTS": _show_parser("RELAYLOG EVENTS"),
        "REPLICAS": _show_parser("REPLICAS"),
 
…[1874 chars elided]…
traint(kind="SPATIAL"),
        "ZEROFILL": lambda self: self.expression(exp.ZeroFillColumnConstraint()),
        "INVISIBLE": lambda self: self.expression(exp.InvisibleColumnConstraint()),
    }

    ALTER_PARSERS = {
        **parser.Parser.ALTER_PARSERS,
        "MODIFY": lambda self: self._parse_alter_table_alter(),
        "AUTO_INCREMENT": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),
    }

    ALTER_ALTER_PARSERS = {
        **parser.Parser.ALTER_ALTER_PARSERS,
[tool_use Bash] {"command": "grep -n '\"COLUMNS\"\\|\"INDEX\"\\|\"TABLES\"\\|\"BINLOG' sqlglot/parsers/mysql.py; grep -n \"IN \\|SHOW\" tests/dialects/test_mysql.py | grep -i \"show\" | head -40", "description": "Check SHOW COLUMNS/INDEX entries and existing show tests"}
[tool_result] 173:        "BINLOG EVENTS": _show_parser("BINLOG EVENTS"),
177:        "FULL COLUMNS": _show_parser("COLUMNS", target="FROM", full=True),
178:        "COLUMNS": _show_parser("COLUMNS", target="FROM"),
196:        "INDEX": _show_parser("INDEX", target="FROM"),
216:        "FULL TABLES": _show_parser("TABLES", full=True),
217:        "TABLES": _show_parser("TABLES"),
246:        "INDEX": lambda self: self._parse_index_constraint(),
261:        "INDEX": lambda self: self._parse_alter_table_alter_i
…[2027 chars elided]…
y("SHOW PROFILE BLOCK IO")
1383:            "SHOW PROFILE BLOCK IO, PAGE FAULTS FOR QUERY 1 OFFSET 2 LIMIT 3"
1392:        show = self.validate_identity("SHOW REPLICA STATUS")
1396:        show = self.validate_identity("SHOW SLAVE STATUS", "SHOW REPLICA STATUS")
1400:        show = self.validate_identity("SHOW REPLICA STATUS FOR CHANNEL channel_name")
1404:        show = self.validate_identity("SHOW TABLES")
1408:        show = self.validate_identity("SHOW FULL TABLES FROM db_name LIKE '%foo%'")
[assistant] The cause is in `_parse_show_mysql`: it consumes `IN` up front to read a binlog file name (`IN 'logfile'`), then never sees `FROM` for `SHOW TABLES IN test`. I'll limit the `IN 'log'` read to binlog/relaylog events and let `IN` act as a database synonym everywhere else.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-165309-mysql-mariadb-show-tables-in-sch/base-1/sqlglot/parsers/mysql.py", "old_string": "        log = self._parse_string() if self._match_text_seq(\"IN\") else None\n\n        if this in (\"BINLOG EVENTS\", \"RELAYLOG EVENTS\"):\n            position = self._parse_number() if self._match_text_seq(\"
…[198 chars elided]…
OG EVENTS\", \"RELAYLOG EVENTS\"):\n            log = self._parse_string() if self._match_text_seq(\"IN\") else None\n            position = self._parse_number() if self._match_text_seq(\"FROM\") else None\n            db = None\n        else:\n            log = None\n            position = None\n            db = None\n\n            if self._match(TokenType.FROM) or self._match_text_seq(\"IN\"):"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-165309-mysql-mariadb-show-tables-in-sch/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[assistant] Now a test next to the existing `SHOW TABLES` tests.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-165309-mysql-mariadb-show-tables-in-sch/base-1/tests/dialects/test_mysql.py", "offset": 1403, "limit": 12}
[tool_result] 1403	    def test_show_tables(self):
1404	        show = self.validate_identity("SHOW TABLES")
1405	        self.assertIsInstance(show, exp.Show)
1406	        self.assertEqual(show.name, "TABLES")
1407	
1408	        show = self.validate_identity("SHOW FULL TABLES FROM db_name LIKE '%foo%'")
1409	        self.assertTrue(show.args["full"])
1410	        self.assertEqual(show.text("db"), "db_name")
1411	        self.assertIsInstance(show.args["like"], exp.Literal)
1412	        self.assertEqual(show.text("like"), "%foo%")
1413	
1414	    def test_set_variable(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-165309-mysql-mariadb-show-tables-in-sch/base-1/tests/dialects/test_mysql.py", "old_string": "        self.assertEqual(show.text(\"like\"), \"%foo%\")\n\n    def test_set_variable(self):", "new_string": "        self.assertEqual(show.text(\"like\"), \"%foo%\")\n\n        self.validate_identity(\"SHOW TABLES IN test\", \"SHOW TABLES FROM test\")\n        self.validate_identity(\"SHOW FULL TABLES IN db_name LIKE '%foo%'\", \"SHOW FULL TABLES FROM db_name LIKE '%foo%'\")\n\n    def test_set_variable(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-165309-mysql-mariadb-show-tables-in-sch/base-1/tests/dialects/test_mysql.py has been updated successfully.
[assistant] Running the MySQL dialect tests and the binlog `IN` check with the project's interpreter.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -15; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in ['SHOW TABLES IN test', \\\"SHOW BINLOG EVENTS IN 'logfile'\\\", \\\"SHOW BINLOG EVENTS IN 'logfile' FROM 1\\\", 'SHOW COLUMNS FROM tbl IN db']:\n    print(repr(sqlglot.transpile(q, read='mysql', write='mysql')[0]))\n\"", "description": "Run MySQL tests and spot-check SHOW statements"}
[tool_result] .............................. [ 60%]
....................                                              [100%]
50 passed, 481 subtests passed in 0.37s
'SHOW TABLES FROM test'
"SHOW BINLOG EVENTS IN 'logfile'"
"SHOW BINLOG EVENTS IN 'logfile' FROM 1"
'SHOW COLUMNS FROM tbl FROM db'
[assistant] MySQL tests pass and the binlog forms are unchanged. Now the full suite and the linter, since my test line may be over the length limit.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4; (<work>/env-sqlglot/bin/python -m ruff --version && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py && <work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py) 2>&1 | tail -8", "description": "Run full test suite and ruff checks"}
[tool_result] .............................................................................. [ 90%]
............................... [ 93%]
.......................................................................... [100%]
1089 passed, 17847 subtests passed in 50.22s
ruff 0.15.6
Would reformat: tests/dialects/test_mysql.py
1 file would be reformatted, 1 file already formatted
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff format tests/dialects/test_mysql.py && <work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py && git diff --stat && git diff -- sqlglot/ tests/ | head -80", "description": "Format test file, lint, and show diff"}
[tool_result] 1 file reformatted
All checks passed!
 sqlglot/parsers/mysql.py     | 6 +++---
 tests/dialects/test_mysql.py | 5 +++++
 2 files changed, 8 insertions(+), 3 deletions(-)
diff --git a/sqlglot/parsers/mysql.py b/sqlglot/parsers/mysql.py
index d8abbea52..bc2a54985 100644
--- a/sqlglot/parsers/mysql.py
+++ b/sqlglot/parsers/mysql.py
@@ -408,16 +408,16 @@ class MySQLParser(parser.Parser):
         else:
             target_id = None
 
-        log = self._parse_string() if self._match_text_seq("IN") e
…[889 chars elided]…
assertEqual(show.text("like"), "%foo%")
 
+        self.validate_identity("SHOW TABLES IN test", "SHOW TABLES FROM test")
+        self.validate_identity(
+            "SHOW FULL TABLES IN db_name LIKE '%foo%'", "SHOW FULL TABLES FROM db_name LIKE '%foo%'"
+        )
+
     def test_set_variable(self):
         cmd = self.parse_one("SET SESSION x = 1")
         item = cmd.expressions[0]
[This command modified 1 file you've previously read: tests/dialects/test_mysql.py. Call Read before editing.]
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -1", "description": "Re-run MySQL dialect tests after formatting"}
[tool_result] 50 passed, 481 subtests passed in 0.18s
[assistant] `SHOW TABLES IN test` now parses in the MySQL dialect and generates `SHOW TABLES FROM test`. The full suite passes (1089 tests) and ruff is clean.

**Cause:** `_parse_show_mysql` in `sqlglot/parsers/mysql.py` consumed `IN` up front to read a binlog file name. For non-binlog statements it then never saw `FROM`, so the parse failed.

**Fix:**
- `IN 'logfile'` is now read only for `BINLOG EVENTS` and `RELAYLOG EVENTS`, so `SHOW BINLOG EVENTS IN 'logfile' FROM 1` round-trips unchanged.
- For every other SHOW form, `IN` is accepted as a synonym for `FROM` before the database name.

**Test:** I added two round-trip checks to `test_show_tables` in `tests/dialects/test_mysql.py`: `SHOW TABLES IN test` and `SHOW FULL TABLES IN db_name LIKE '%foo%'`. No existing test was changed.

One side effect: `SHOW COLUMNS FROM tbl IN db` now parses and generates `SHOW COLUMNS FROM tbl FROM db`. That was previously a parse error, and it is valid MySQL.

Not covered: `SHOW COLUMNS IN tbl` (with `IN` in place of the first `FROM`) still fails. Those entries parse their target with `target="FROM"`, which only matches `FROM`. I left it alone since it was outside the request.
