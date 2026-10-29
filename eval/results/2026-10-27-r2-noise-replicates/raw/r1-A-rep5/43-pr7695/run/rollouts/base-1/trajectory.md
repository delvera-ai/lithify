# trajectory base-1

final message:
Exasol now transpiles `SHOW DATABASES` and `SHOW SCHEMAS` (from MySQL) to `SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS`. The full test suite passes (1114 tests), and ruff lint and format checks are clean.

The change is in `sqlglot/generators/exasol.py`. The MySQL parser already turns both statements into the same `Show` node, so the Exasol generator only needed a `DATABASES` branch beside the existing `TABLES` one. I added `test_show_databases` to `tests/dialects/test_exasol.py`, which covers both spellings.

Nothing is committed. A `SHOW DATABASES LIKE '...'` filter is dropped silently, the same as the existing `SHOW TABLES` handling. Carrying it over would mean adding a `WHERE SCHEMA_NAME LIKE ...` clause, which I left out because the spec was the bare select.

## events
[tool_use Bash] {"command": "rtk grep -n \"SHOW\\|_parse_show\\|show\" sqlglot/dialects/exasol.py sqlglot/dialects/mysql.py | head -80; rtk grep -rn \"EXA_SCHEMAS\\|EXA_TABLES\\|ShowTables\\|SHOW TABLES\\|show_tables\" sqlglot tests | head -40", "description": "Find SHOW handling in Exasol and MySQL dialects"}
[tool_result] (eval):1: command not found: rtk
(eval):1: command not found: rtk
[tool_use Bash] {"command": "grep -n \"SHOW\\|_parse_show\\|show\" sqlglot/dialects/exasol.py sqlglot/dialects/mysql.py | head -80; echo ---; grep -rn \"EXA_SCHEMAS\\|EXA_TABLES\\|ShowTables\\|SHOW TABLES\\|show_tables\\|SHOW DATABASES\" sqlglot tests | head -40", "description": "Find SHOW handling in Exasol and MySQL dialects"}
[tool_result] sqlglot/dialects/mysql.py:154:        COMMANDS = {*tokens.Tokenizer.COMMANDS, TokenType.REPLACE} - {TokenType.SHOW}
---
tests/test_transpile.py:1000:            "SHOW TABLES",
tests/dialects/test_exasol.py:987:    def test_show_tables(self):
tests/dialects/test_exasol.py:990:            read={"mysql": "SHOW TABLES FROM test"},
tests/dialects/test_exasol.py:997:            read={"mysql": "SHOW TABLES"},
tests/dialects/test_snowflake.py:5215:        ast = parse_one("SHOW DATABASES IN ACCOUNT", rea
…[873 chars elided]…
t_duckdb.py:2509:        self.validate_identity("SHOW TABLES FROM my_database").assert_is(exp.Show)
tests/dialects/test_duckdb.py:2510:        self.validate_identity("SHOW TABLES FROM my_database.my_schema").assert_is(exp.Show)
tests/dialects/test_mysql.py:1433:    def test_show_tables(self):
tests/dialects/test_mysql.py:1434:        show = self.validate_identity("SHOW TABLES")
tests/dialects/test_mysql.py:1444:        show = self.validate_identity("SHOW TABLES IN test", "SHOW TABLES FROM test")
[tool_use Bash] {"command": "sed -n 975,1010p tests/dialects/test_exasol.py; echo ---; grep -n \"show\\|Show\\|SHOW\" sqlglot/dialects/exasol.py; echo ---; grep -n \"_parse_show\\|def _parse_show_mysql\\|SHOW_PARSERS\\|show_parsers\\|class Show\\|def show_sql\\|SHOW_PARSERS\" sqlglot/dialects/mysql.py sqlglot/parser.py sqlglot/generator.py | head -40; echo ---; grep -n \"class Show\\b\" -A12 sqlglot/expressions.py; sed -n 1433,1460p tests/dialects/test_mysql.py", "description": "Inspect Exasol SHOW test and MySQL SHOW parsing"}
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
   
…[2243 chars elided]…
LL TABLES FROM test")
        self.assertTrue(show.args["full"])
        self.assertEqual(show.text("db"), "test")

    def test_set_variable(self):
        cmd = self.parse_one("SET SESSION x = 1")
        item = cmd.expressions[0]
        self.assertEqual(item.text("kind"), "SESSION")
        self.assertIsInstance(item.this, exp.EQ)
        self.assertEqual(item.this.left.name, "x")
        self.assertEqual(item.this.right.name, "1")

        cmd = self.parse_one("SET @@GLOBAL.x = @@GLOBAL.y")
[tool_use Bash] {"command": "grep -rn \"EXA_ALL_TABLES\\|EXA_\" sqlglot | head; echo ---; grep -rln \"exasol\" sqlglot | head; echo ---; grep -n \"_show_\\|def _parse_show\\|SHOW_PARSERS\\|\\\"TABLES\\\"\\|\\\"DATABASES\\\"\" sqlglot/parser.py sqlglot/dialects/mysql.py sqlglot/dialects/*.py | head -30; echo ---; sed -n 9190,9215p sqlglot/parser.py", "description": "Locate Exasol SHOW TABLES implementation"}
[tool_result] sqlglot/generators/exasol.py:914:                .from_(exp.table_("EXA_ALL_TABLES", db="SYS"))
---
sqlglot/parsers/exasol.py
sqlglot/dialects/dialect.py
sqlglot/dialects/exasol.py
sqlglot/generators/exasol.py
---
sqlglot/parser.py:1559:    SHOW_PARSERS: t.ClassVar[dict[str, t.Callable]] = {}
sqlglot/parser.py:1845:    SHOW_TRIE: t.ClassVar[dict] = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parser.py:8963:        elif self._match_text_seq("TABLES"):
sqlglot/parser.py:9194:    def _
…[675 chars elided]…
et_transaction(global_=kind == "GLOBAL")

        left = self._parse_primary() or self._parse_column()
        assignment_delimiter = self._match_texts(self.SET_ASSIGNMENT_DELIMITERS)

        if not left or (self.SET_REQUIRES_ASSIGNMENT_DELIMITER and not assignment_delimiter):
            self._retreat(index)
            return None

        right = self._parse_statement() or self._parse_id_var()
        if isinstance(right, (exp.Column, exp.Identifier)):
            right = exp.var(right.name)
[tool_use Bash] {"command": "sed -n 880,960p sqlglot/generators/exasol.py; echo ---; grep -n \"show\\|SHOW\" sqlglot/generators/exasol.py; echo ---; sed -n 8940,8990p sqlglot/parser.py; echo ---; grep -n \"def show_sql\" -A30 sqlglot/generator.py | head -50; echo; grep -n \"SHOW\" sqlglot/dialects/mysql.py sqlglot/parsers/mysql.py sqlglot/parsers/exasol.py sqlglot/generators/mysql.py 2>/dev/null", "description": "Read Exasol SHOW TABLES generator and show parsing"}
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
    
…[6370 chars elided]…
TokenType.REPLACE} - {TokenType.SHOW}
sqlglot/generators/mysql.py:744:        return f"SHOW{full}{global_}{this}{json}{target}{for_table}{types}{db}{query}{log}{position}{channel}{mutex_or_status}{like}{where}{offset}{limit}{for_group}{for_user}{for_role}{into_outfile}"
sqlglot/parsers/mysql.py:167:        TokenType.SHOW: lambda self: self._parse_show(),
sqlglot/parsers/mysql.py:170:    SHOW_PARSERS = {
sqlglot/parsers/mysql.py:240:    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
[tool_use Bash] {"command": "sed -n 165,245p sqlglot/parsers/mysql.py; echo ---; grep -n \"def _parse_show_mysql\" -A60 sqlglot/parsers/mysql.py | head -90", "description": "Read MySQL SHOW parser definitions"}
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
…[5700 chars elided]…
able = self._parse_id_var() if self._match_text_seq("FOR", "TABLE") else None
473-        for_group = self._parse_string() if self._match_text_seq("FOR", "GROUP") else None
474-        for_user = self._parse_string() if self._match_text_seq("FOR", "USER") else None
475-        for_role = self._parse_string() if self._match_text_seq("FOR", "ROLE") else None
476-        into_outfile = self._parse_string() if self._match_text_seq("INTO", "OUTFILE") else None
477-
478-        return self.expression(
[assistant] SHOW DATABASES and SHOW SCHEMAS both parse to `exp.Show` with name `DATABASES`, and the Exasol generator only handles `TABLES`, so the rest falls through to the base `show_sql`, which emits the unsupported empty string. I'll add the `DATABASES` branch next to `TABLES`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-123052-exasol-dialect-transpiling-mysql/base-1/sqlglot/generators/exasol.py", "old_string": "            return self.sql(select)\n\n        return super().show_sql(expression)", "new_string": "            return self.sql(select)\n\n        if expression.name == \"DATABASES\":\n            select = exp.select(exp.column(\"SCHEMA_NAME\")).from_(\n                exp.table_(\"EXA_SCHEMAS\", db=\"SYS\")\n            )\n            return self.sql(select)\n\n        return super().show_sql(expression)"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-123052-exasol-dialect-transpiling-mysql/base-1/sqlglot/generators/exasol.py has been updated successfully.
[assistant] Next, a test next to the existing `test_show_tables` in the Exasol test file.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-123052-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py", "old_string": "    def test_group_by_alias_local(self):", "new_string": "    def test_show_databases(self):\n        self.validate_all(\n            \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            read={\"mysql\": \"SHOW DATABASES\", \"mariadb\": \"SHOW SCHEMAS\"},\n            write={\n                \"exasol\": \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            },\n        )\n\n    def test_group_by_alias_local(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-123052-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py tests/dialects/test_mysql.py 2>&1 | tail -15; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in ['SHOW DATABASES','SHOW SCHEMAS','SHOW TABLES']:\n    print(sqlglot.transpile(q, read='mysql', write='exasol'))\n\"", "description": "Run Exasol and MySQL tests and check outputs"}
[tool_result]         possibilities: Iterable[str],
    ) -> None:
        close_matches = get_close_matches(word, possibilities, n=1)
    
        similar = seq_get(close_matches, 0) or ""
        if similar:
            similar = f" Did you mean {similar}?"
    
>       raise ValueError(f"Unknown {kind} '{word}'.{similar}")
E       ValueError: Unknown dialect 'mariadb'.

sqlglot/helper.py:64: ValueError
=========================== short test summary info ============================
SUBFAILED[mariadb -> SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS] tests/dialects/test_exasol.py::TestExasol::test_show_databases
1 failed, 71 passed, 1063 subtests passed in 0.57s
['SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS']
['SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS']
['SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = CURRENT_SCHEMA']
[assistant] There's no `mariadb` dialect in sqlglot, so the test's `SHOW SCHEMAS` case needs to read as `mysql`. The transpiled outputs are correct.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-123052-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py", "old_string": "        self.validate_all(\n            \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            read={\"mysql\": \"SHOW DATABASES\", \"mariadb\": \"SHOW SCHEMAS\"},\n            write={\n                \"
…[149 chars elided]…
CHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            read={\"mysql\": \"SHOW DATABASES\"},\n            write={\"exasol\": \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\"},\n        )\n        self.validate_all(\n            \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            read={\"mysql\": \"SHOW SCHEMAS\"},\n            write={\"exasol\": \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\"},\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-123052-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; git status --short", "description": "Run full project test suite and show changed files"}
[tool_result] ............................................................................ [ 94%]
....................... [ 96%]
.......................... [ 98%]
...............                 [100%]
1114 passed, 18166 subtests passed in 55.53s
 M sqlglot/generators/exasol.py
 M tests/dialects/test_exasol.py
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/generators/exasol.py tests/dialects/test_exasol.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generators/exasol.py tests/dialects/test_exasol.py) 2>&1 | tail -5", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
2 files already formatted
[assistant] Exasol now transpiles `SHOW DATABASES` and `SHOW SCHEMAS` (from MySQL) to `SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS`. The full test suite passes (1114 tests), and ruff lint and format checks are clean.

The change is in `sqlglot/generators/exasol.py`. The MySQL parser already turns both statements into the same `Show` node, so the Exasol generator only needed a `DATABASES` branch beside the existing `TABLES` one. I added `test_show_databases` to `tests/dialects/test_exasol.py`, which covers both spellings.

Nothing is committed. A `SHOW DATABASES LIKE '...'` filter is dropped silently, the same as the existing `SHOW TABLES` handling. Carrying it over would mean adding a `WHERE SCHEMA_NAME LIKE ...` clause, which I left out because the spec was the bare select.
