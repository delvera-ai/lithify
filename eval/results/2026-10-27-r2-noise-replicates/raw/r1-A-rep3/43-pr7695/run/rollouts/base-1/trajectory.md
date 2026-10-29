# trajectory base-1

final message:
`SHOW DATABASES` and `SHOW SCHEMAS` from MySQL now transpile to Exasol as `SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS`, mirroring the existing `SHOW TABLES` branch.

- **Change:** `show_sql` in `sqlglot/generators/exasol.py` gets a `DATABASES` branch. MySQL parses `SHOW SCHEMAS` to the same `DATABASES` node, so both forms are covered.
- **Test:** `test_show_databases` in `tests/dialects/test_exasol.py` covers `SHOW DATABASES`. It doesn't cover `SHOW SCHEMAS` because the test helper takes one entry per dialect; I checked that form by hand and it produces the same output.
- **Checks:** the full suite passes (1114 passed) and `ruff check` is clean.

Two notes:
- The repo has no `mariadb` dialect, so MariaDB input goes through `mysql`.
- As with `SHOW TABLES`, any `LIKE` or `WHERE` filter on `SHOW DATABASES` is dropped. I kept it consistent with the existing branch rather than adding filter support.

I haven't committed anything.

## events
[tool_use Bash] {"command": "grep -rn -i \"show\" sqlglot/dialects/mysql.py | head -60; echo ---; grep -n -i \"show\\|SHOW\" sqlglot/dialects/exasol.py; echo ---; grep -rn -i \"exasol\" tests/dialects/*.py | grep -i show", "description": "Find SHOW handling in MySQL and Exasol dialects"}
[tool_result] sqlglot/dialects/mysql.py:154:        COMMANDS = {*tokens.Tokenizer.COMMANDS, TokenType.REPLACE} - {TokenType.SHOW}
---
---
[tool_use Bash] {"command": "grep -rn \"_parse_show\\|ShowTables\\|EXA_ALL_TABLES\\|EXA_\\|SYS\\.\" sqlglot/dialects/mysql.py sqlglot/dialects/exasol.py | head -40; echo ---; grep -rn -i \"show\" tests/dialects/test_exasol.py | head; echo ---; grep -rn -i \"SHOW DATABASES\\|SHOW SCHEMAS\" tests/ | head", "description": "Locate SHOW parsing and Exasol SYS tables usage"}
[tool_result] ---
tests/dialects/test_exasol.py:987:    def test_show_tables(self):
tests/dialects/test_exasol.py:990:            read={"mysql": "SHOW TABLES FROM test"},
tests/dialects/test_exasol.py:997:            read={"mysql": "SHOW TABLES"},
---
tests/dialects/test_snowflake.py:5215:        ast = parse_one("SHOW DATABASES IN ACCOUNT", read="snowflake")
tests/dialects/test_snowflake.py:5267:        ast = parse_one("SHOW SCHEMAS IN DATABASE db1", read="snowflake")
[tool_use Bash] {"command": "sed -n 975,1010p tests/dialects/test_exasol.py; echo ---; grep -n \"SHOW\\|Show\" sqlglot/dialects/exasol.py sqlglot/dialects/mysql.py sqlglot/parser.py | head -40; echo ---; grep -n \"class Show\" -A6 sqlglot/expressions.py | head -20; echo ---; grep -n \"_show_sql\\|def show\" -A30 sqlglot/generator.py | head -60", "description": "Inspect existing SHOW TABLES test and SHOW generation code"}
[tool_result]             read={"mysql": "USE `my_database`"},
            write={"exasol": 'OPEN SCHEMA "my_database"'},
        )
        # USE ROLE / USE WAREHOUSE have no Exasol equivalent — emit unsupported
        with self.assertRaises(UnsupportedError):
            transpile(
                "USE ROLE admin",
                read="snowflake",
                write="exasol",
                unsupported_level=ErrorLevel.RAISE,
            )

    def test_show_tables(self):
        self.validate_all(
   
…[2699 chars elided]…
rs_sql(self, expression: exp.TranslateCharacters) -> str:
5991-        this = self.sql(expression, "this")
5992-        expr = self.sql(expression, "expression")
5993-        with_error = " WITH ERROR" if expression.args.get("with_error") else ""
5994-        return f"TRANSLATE({this} USING {expr}{with_error})"
5995-
5996-    def decodecase_sql(self, expression: exp.DecodeCase) -> str:
5997-        if self.SUPPORTS_DECODE_CASE:
5998-            return self.func("DECODE", *expression.expressions)
[tool_use Bash] {"command": "ls sqlglot/dialects | grep -i exa; grep -rn \"EXA_ALL_TABLES\\|EXA_SCHEMAS\\|SHOW_PARSERS\\|_parse_show\" sqlglot/ | head -30", "description": "Find where Exasol SHOW TABLES is generated"}
[tool_result] exasol.py
sqlglot/parser.py:1559:    SHOW_PARSERS: t.ClassVar[dict[str, t.Callable]] = {}
sqlglot/parser.py:1845:    SHOW_TRIE: t.ClassVar[dict] = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parser.py:9194:    def _parse_show(self) -> exp.Expr | None:
sqlglot/parser.py:9195:        parser = self._find_parser(self.SHOW_PARSERS, self.SHOW_TRIE)
sqlglot/parsers/singlestore.py:193:    SHOW_PARSERS = {
sqlglot/parsers/singlestore.py:194:        **MySQLParser.SHOW_PARSERS,
sqlglot/parsers
…[853 chars elided]…
uckdb(self, this: str) -> exp.Show:
sqlglot/parsers/mysql.py:49:        return self._parse_show_mysql(*args, **kwargs)
sqlglot/parsers/mysql.py:167:        TokenType.SHOW: lambda self: self._parse_show(),
sqlglot/parsers/mysql.py:170:    SHOW_PARSERS = {
sqlglot/parsers/mysql.py:240:    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parsers/mysql.py:418:    def _parse_show_mysql(
sqlglot/generators/exasol.py:914:                .from_(exp.table_("EXA_ALL_TABLES", db="SYS"))
[tool_use Bash] {"command": "sed -n 880,960p sqlglot/generators/exasol.py; echo ---; sed -n 165,245p sqlglot/parsers/mysql.py; echo ---; sed -n 415,470p sqlglot/parsers/mysql.py", "description": "Read Exasol SHOW generator and MySQL SHOW parser"}
[tool_result]     }

    def converttimezone_sql(self, expression: exp.ConvertTimezone) -> str:
        from_tz = expression.args.get("source_tz")
        to_tz = expression.args.get("target_tz")
        datetime = expression.args.get("timestamp")
        options = expression.args.get("options")

        return self.func("CONVERT_TZ", datetime, from_tz, to_tz, options)

    def if_sql(self, expression: exp.If) -> str:
        this = self.sql(expression, "this")
        true = self.sql(expression, "true")
    
…[7937 chars elided]…
           query = self._parse_number() if self._match_text_seq("FOR", "QUERY") else None
            offset = self._parse_number() if self._match_text_seq("OFFSET") else None
            limit = self._parse_number() if self._match_text_seq("LIMIT") else None
        else:
            types, query = None, None
            offset, limit = self._parse_oldstyle_limit()

        mutex = True if self._match_text_seq("MUTEX") else None
        mutex = False if self._match_text_seq("STATUS") else mutex
[assistant] The Exasol `show_sql` already handles `SHOW TABLES` by building a `SELECT` against `SYS`. I'll add the same branch for `DATABASES`, which covers `SHOW SCHEMAS` too since MySQL parses both to `DATABASES`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-133543-exasol-dialect-transpiling-mysql/base-1/sqlglot/generators/exasol.py", "old_string": "            return self.sql(select)\n\n        return super().show_sql(expression)", "new_string": "            return self.sql(select)\n\n        if expression.name == \"DATABASES\":\n            select = (\n                exp.select(exp.column(\"SCHEMA_NAME\"))\n                .from_(exp.table_(\"EXA_SCHEMAS\", db=\"SYS\"))\n            )\n            return self.sql(select)\n\n        return super().show_sql(expression)"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-133543-exasol-dialect-transpiling-mysql/base-1/sqlglot/generators/exasol.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-133543-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py", "old_string": "    def test_group_by_alias_local(self):", "new_string": "    def test_show_databases(self):\n        self.validate_all(\n            \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            read={\"mysql\": \"SHOW DATABASES\", \"mariadb\": \"SHOW SCHEMAS\"},\n            write={\"exasol\": \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\"},\n        )\n\n    def test_group_by_alias_local(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-133543-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py has been updated successfully.
[assistant] Now I'll run the Exasol tests with the project's interpreter, then the style check.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -30; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generators/exasol.py tests/dialects/test_exasol.py 2>&1 | tail -3", "description": "Run Exasol dialect tests and format check"}
[tool_result]     parse_one(read_sql, read_dialect).sql(
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlglot/__init__.py:155: in parse_one
    dialect = Dialect.get_or_raise(read or dialect)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlglot/dialects/dialect.py:961: in get_or_raise
    suggest_closest_match_and_fail("dialect", dialect_name, all_dialects)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

kind = 'dialect', word = 'mariadb'
possibilities = {'', 'athena', 'bigqu
…[376 chars elided]…
 
>       raise ValueError(f"Unknown {kind} '{word}'.{similar}")
E       ValueError: Unknown dialect 'mariadb'.

sqlglot/helper.py:64: ValueError
=========================== short test summary info ============================
SUBFAILED[mariadb -> SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS] tests/dialects/test_exasol.py::TestExasol::test_show_databases
1 failed, 20 passed, 577 subtests passed in 0.41s
Would reformat: sqlglot/generators/exasol.py
1 file would be reformatted, 1 file already formatted
[assistant] There is no `mariadb` dialect in this repo; MariaDB input goes through the `mysql` dialect. I'll drop that read key, keep `SHOW SCHEMAS` under `mysql`, and apply the formatter.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-133543-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py", "old_string": "            read={\"mysql\": \"SHOW DATABASES\", \"mariadb\": \"SHOW SCHEMAS\"},", "new_string": "            read={\"mysql\": \"SHOW DATABASES\"},"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-133543-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff format sqlglot/generators/exasol.py && git diff --stat && <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SHOW DATABASES','SHOW SCHEMAS']:\n    print(sqlglot.transpile(s, read='mysql', write='exasol', unsupported_level=sqlglot.ErrorLevel.RAISE))\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -3", "description": "Format, verify both SHOW forms, rerun Exasol tests"}
[tool_result] 1 file reformatted
 sqlglot/generators/exasol.py  | 6 ++++++
 tests/dialects/test_exasol.py | 7 +++++++
 2 files changed, 13 insertions(+)
['SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS']
['SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS']
....................                                                    [100%]
20 passed, 577 subtests passed in 0.14s
[This command modified 1 file you've previously read: sqlglot/generators/exasol.py. Call Read before editing.]
[assistant] Both forms now transpile correctly and the Exasol tests pass. The file change notice is from my own `ruff format` run. I'll check the diff and run the full suite the project harness specifies.
[tool_use Bash] {"command": "git diff && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5 && <work>/env-sqlglot/bin/python -m ruff check sqlglot/generators/exasol.py tests/dialects/test_exasol.py | tail -2", "description": "Review diff, run full test suite and lint"}
[tool_result] diff --git a/sqlglot/generators/exasol.py b/sqlglot/generators/exasol.py
index 644619941..5806f6293 100644
--- a/sqlglot/generators/exasol.py
+++ b/sqlglot/generators/exasol.py
@@ -916,6 +916,12 @@ class ExasolGenerator(generator.Generator):
             )
             return self.sql(select)
 
+        if expression.name == "DATABASES":
+            select = exp.select(exp.column("SCHEMA_NAME")).from_(
+                exp.table_("EXA_SCHEMAS", db="SYS")
+            )
+            return self.
…[758 chars elided]…
..................................................................................................................................................................................................................................................................................................................................... [ 94%]
....................... [ 96%]
.......................... [ 98%]
.............                   [100%]
1114 passed, 18164 subtests passed in 51.08s
All checks passed!
[assistant] `SHOW DATABASES` and `SHOW SCHEMAS` from MySQL now transpile to Exasol as `SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS`, mirroring the existing `SHOW TABLES` branch.

- **Change:** `show_sql` in `sqlglot/generators/exasol.py` gets a `DATABASES` branch. MySQL parses `SHOW SCHEMAS` to the same `DATABASES` node, so both forms are covered.
- **Test:** `test_show_databases` in `tests/dialects/test_exasol.py` covers `SHOW DATABASES`. It doesn't cover `SHOW SCHEMAS` because the test helper takes one entry per dialect; I checked that form by hand and it produces the same output.
- **Checks:** the full suite passes (1114 passed) and `ruff check` is clean.

Two notes:
- The repo has no `mariadb` dialect, so MariaDB input goes through `mysql`.
- As with `SHOW TABLES`, any `LIKE` or `WHERE` filter on `SHOW DATABASES` is dropped. I kept it consistent with the existing branch rather than adding filter support.

I haven't committed anything.
