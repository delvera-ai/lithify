# trajectory base-1

final message:
`SHOW DATABASES` and `SHOW SCHEMAS` from MySQL now transpile to Exasol as `SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS`. The full test suite passes (1114 tests), and ruff lint and format checks are clean.

The change is in `sqlglot/generators/exasol.py`, in the existing `show_sql` method next to the `SHOW TABLES` branch. The MySQL parser already maps `SHOW SCHEMAS` onto the same `DATABASES` show node, so one branch covers both. I added `test_show_databases` to `tests/dialects/test_exasol.py` to cover both statements.

I left out `LIKE` and `WHERE` filters on `SHOW DATABASES`. They are currently dropped silently, the same as the `SHOW TABLES` branch already does. Say if you want them mapped onto `SCHEMA_NAME`.

Nothing has been committed.

## events
[tool_use Bash] {"command": "grep -n \"SHOW\\|_parse_show\\|show\" sqlglot/dialects/exasol.py | head -50; grep -n \"SHOW\" sqlglot/dialects/mysql.py | head -60; grep -rn \"EXA_SCHEMAS\\|EXA_ALL_TABLES\\|SHOW TABLES\\|ShowTables\" tests/dialects/test_exasol.py tests/dialects/test_mysql.py | head", "description": "Find SHOW handling in Exasol and MySQL dialects"}
[tool_result] 154:        COMMANDS = {*tokens.Tokenizer.COMMANDS, TokenType.REPLACE} - {TokenType.SHOW}
tests/dialects/test_exasol.py:989:            "SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = 'TEST'",
tests/dialects/test_exasol.py:990:            read={"mysql": "SHOW TABLES FROM test"},
tests/dialects/test_exasol.py:992:                "exasol": "SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = 'TEST'"
tests/dialects/test_exasol.py:996:            "SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = CURRENT_SCHEMA",
tests/dialects/test_exasol.py:997:            read={"mysql": "SHOW TABLES"},
tests/dialects/test_exasol.py:999:                "exasol": "SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = CURRENT_SCHEMA"
tests/dialects/test_mysql.py:1434:        show = self.validate_identity("SHOW TABLES")
tests/dialects/test_mysql.py:1444:        show = self.validate_identity("SHOW TABLES IN test", "SHOW TABLES FROM test")
[tool_use Bash] {"command": "grep -n \"_parse_show\\|def _show\\|SHOW_PARSERS\\|ShowTables\\|_show_\\|\\\"DATABASES\\\"\\|\\\"SCHEMAS\\\"\" sqlglot/dialects/mysql.py sqlglot/dialects/exasol.py sqlglot/parser.py | head -40; sed -n 960,1010p tests/dialects/test_exasol.py", "description": "Locate SHOW parser and Exasol SHOW tests"}
[tool_result] sqlglot/parser.py:1559:    SHOW_PARSERS: t.ClassVar[dict[str, t.Callable]] = {}
sqlglot/parser.py:1845:    SHOW_TRIE: t.ClassVar[dict] = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parser.py:9194:    def _parse_show(self) -> exp.Expr | None:
sqlglot/parser.py:9195:        parser = self._find_parser(self.SHOW_PARSERS, self.SHOW_TRIE)
            transpile(
                "SELECT *, COUNT(*) FROM t GROUP BY ALL",
                write="exasol",
                unsupported_level=Error
…[1351 chars elided]…
FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = CURRENT_SCHEMA"
            },
        )

    def test_group_by_alias_local(self):
        # GROUP BY bare alias -> LOCAL prefix
        self.validate_all(
            "SELECT city, COUNT(*) AS cnt FROM t GROUP BY LOCAL.cnt",
            read={"mysql": "SELECT city, COUNT(*) AS cnt FROM t GROUP BY cnt"},
            write={"exasol": "SELECT city, COUNT(*) AS cnt FROM t GROUP BY LOCAL.cnt"},
        )
        # GROUP BY expression alias -> LOCAL prefix
[tool_use Bash] {"command": "grep -n \"SHOW_PARSERS\\|_show_\\|ShowTables\\|def _parse_show\" sqlglot/dialects/*.py | head -30; grep -n \"def _show_tables\\|TABLES\\b\" sqlglot/dialects/exasol.py sqlglot/dialects/mysql.py | head", "description": "Find SHOW_PARSERS definitions across dialects"}
[tool_result] sqlglot/dialects/mysql.py:87:            "LOCK TABLES": TokenType.COMMAND,
sqlglot/dialects/mysql.py:104:            "UNLOCK TABLES": TokenType.COMMAND,
[tool_use Bash] {"command": "grep -n \"_parse_show_mysql\\|SHOW\" sqlglot/dialects/mysql.py | head -40; grep -n \"class Show\\|Show(\" sqlglot/expressions.py | head; grep -n \"show\" sqlglot/generator.py | head -20", "description": "Search MySQL SHOW parsing and generator code"}
[tool_result] 154:        COMMANDS = {*tokens.Tokenizer.COMMANDS, TokenType.REPLACE} - {TokenType.SHOW}
ugrep: warning: sqlglot/expressions.py: No such file or directory
5968:    def show_sql(self, expression: exp.Show) -> str:
[tool_use Bash] {"command": "grep -rn \"SHOW_PARSERS\\|def _parse_show\" sqlglot/ | head; grep -rn \"\\\"DATABASES\\\"\\|\\\"SCHEMAS\\\"\\|class Show(\" sqlglot/ | head; grep -rln \"ShowTables\\|\\\"TABLES\\\"\" sqlglot/ | head", "description": "Search sqlglot package for SHOW parser pieces"}
[tool_result] sqlglot/parser.py:1559:    SHOW_PARSERS: t.ClassVar[dict[str, t.Callable]] = {}
sqlglot/parser.py:1845:    SHOW_TRIE: t.ClassVar[dict] = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parser.py:9194:    def _parse_show(self) -> exp.Expr | None:
sqlglot/parser.py:9195:        parser = self._find_parser(self.SHOW_PARSERS, self.SHOW_TRIE)
sqlglot/parsers/snowflake.py:811:    SHOW_PARSERS = {
sqlglot/parsers/snowflake.py:843:    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)

…[483 chars elided]…
y:830:        "TERSE DATABASES": _show_parser("DATABASES", terse=True),
sqlglot/parsers/snowflake.py:831:        "TERSE SCHEMAS": _show_parser("SCHEMAS", terse=True),
sqlglot/parsers/mysql.py:186:        "DATABASES": _show_parser("DATABASES"),
sqlglot/parsers/mysql.py:187:        "SCHEMAS": _show_parser("DATABASES"),
sqlglot/expressions/ddl.py:191:class Show(Expression):
sqlglot/parser.py
sqlglot/parsers/snowflake.py
sqlglot/parsers/duckdb.py
sqlglot/parsers/mysql.py
sqlglot/generators/exasol.py
[tool_use Bash] {"command": "grep -n -i \"show\" sqlglot/generators/exasol.py; grep -n -i \"_show_parser\\|def _parse_show\" -A3 sqlglot/parsers/mysql.py | head -80; grep -n \"def show_sql\" -A30 sqlglot/generator.py | head -5; sed -n 185,215p sqlglot/expressions/ddl.py", "description": "Inspect Exasol generator and MySQL SHOW parser"}
[tool_result] 906:    def show_sql(self, expression: exp.Show) -> str:
919:        return super().show_sql(expression)
47:def _show_parser(*args: t.Any, **kwargs: t.Any) -> t.Callable[[MySQLParser], exp.Show]:
48-    def _parse(self: MySQLParser) -> exp.Show:
49-        return self._parse_show_mysql(*args, **kwargs)
50-
--
171:        "BINARY LOGS": _show_parser("BINARY LOGS"),
172:        "MASTER LOGS": _show_parser("BINARY LOGS"),
173:        "BINLOG EVENTS": _show_parser("BINLOG EVENTS"),
174:        "CHAR
…[3512 chars elided]…
       "target": False,
        "offset": False,
        "starts_with": False,
        "limit": False,
        "from_": False,
        "like": False,
        "where": False,
        "db": False,
        "scope": False,
        "scope_kind": False,
        "full": False,
        "mutex": False,
        "query": False,
        "channel": False,
        "global_": False,
        "log": False,
        "position": False,
        "types": False,
        "privileges": False,
        "for_table": False,
[tool_use Bash] {"command": "sed -n 895,925p sqlglot/generators/exasol.py; sed -n 418,470p sqlglot/parsers/mysql.py; grep -n \"def _parse_show_mysql\" -B2 sqlglot/parsers/mysql.py | head -3", "description": "Read Exasol show_sql and MySQL show parser body"}
[tool_result]     # https://docs.exasol.com/db/latest/sql/open_schema.htm
    def use_sql(self, expression: exp.Use) -> str:
        kind = expression.args.get("kind")
        if kind and self.sql(kind).upper() != "SCHEMA":
            self.unsupported(f"'USE {self.sql(kind)}' is not supported in Exasol")
            return super().use_sql(expression)
        this = self.sql(expression, "this")
        return f"OPEN SCHEMA {this}"

    # https://docs.exasol.com/db/latest/sql_references/metadata/metadata_syste
…[2294 chars elided]…
atch_text_seq("FOR", "QUERY") else None
            offset = self._parse_number() if self._match_text_seq("OFFSET") else None
            limit = self._parse_number() if self._match_text_seq("LIMIT") else None
        else:
            types, query = None, None
            offset, limit = self._parse_oldstyle_limit()

        mutex = True if self._match_text_seq("MUTEX") else None
        mutex = False if self._match_text_seq("STATUS") else mutex
416-        )
417-
418:    def _parse_show_mysql(
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-160348-exasol-dialect-transpiling-mysql/base-1/sqlglot/generators/exasol.py", "old_string": "            return self.sql(select)\n\n        return super().show_sql(expression)", "new_string": "            return self.sql(select)\n\n        if expression.name == \"DATABASES\":\n            select = exp.select(exp.column(\"SCHEMA_NAME\")).from_(\n                exp.table_(\"EXA_SCHEMAS\", db=\"SYS\")\n            )\n            return self.sql(select)\n\n        return super().show_sql(expression)"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-160348-exasol-dialect-transpiling-mysql/base-1/sqlglot/generators/exasol.py has been updated successfully.
[assistant] Now a test next to the existing `SHOW TABLES` test, then a check of the output.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-160348-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py", "old_string": "    def test_group_by_alias_local(self):", "new_string": "    def test_show_databases(self):\n        self.validate_all(\n            \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            read={\"mysql\": \"SHOW DATABASES\", \"mariadb\": \"SHOW SCHEMAS\"},\n            write={\"exasol\": \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\"},\n        )\n\n    def test_group_by_alias_local(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-160348-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py tests/dialects/test_mysql.py tests/dialects/test_mariadb.py 2>&1 | tail -15; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SHOW DATABASES','SHOW SCHEMAS']:\n    print(sqlglot.transpile(s, read='mysql', write='exasol'))\nprint(sqlglot.transpile('SHOW TABLES', read='mysql', write='exasol'))\n\" 2>&1", "description": "Run exasol, mysql, mariadb tests and check output"}
[tool_result] ERROR: file or directory not found: tests/dialects/test_mariadb.py


no tests ran in 0.00s
['SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS']
['SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS']
['SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = CURRENT_SCHEMA']
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/ 2>&1 | tail -15", "description": "Run full test suite"}
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
1 failed, 1114 passed, 18164 subtests passed in 55.65s
[assistant] MariaDB isn't a sqlglot dialect (it reads as MySQL), so I'll drop that read key and use MySQL for both statements.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-160348-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py", "old_string": "            read={\"mysql\": \"SHOW DATABASES\", \"mariadb\": \"SHOW SCHEMAS\"},", "new_string": "            read={\"mysql\": \"SHOW DATABASES\"},"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-160348-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-160348-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py", "old_string": "            read={\"mysql\": \"SHOW DATABASES\"},\n            write={\"exasol\": \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\"},\n        )", "new_string": "            read={\"mysql\": \"SHOW DATABASES\"},\n            write={\"exasol\": \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\"},\n        )\n        self.validate_all(\n            \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            read={\"mysql\": \"SHOW SCHEMAS\"},\n            write={\"exasol\": \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\"},\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-160348-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/ 2>&1 | tail -3; git status --short", "description": "Rerun full test suite and show git status"}
[tool_result] .......................... [ 98%]
...............                 [100%]
1114 passed, 18166 subtests passed in 49.89s
 M sqlglot/generators/exasol.py
 M tests/dialects/test_exasol.py
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/generators/exasol.py tests/dialects/test_exasol.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generators/exasol.py tests/dialects/test_exasol.py) 2>&1 | tail -5", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
2 files already formatted
[assistant] `SHOW DATABASES` and `SHOW SCHEMAS` from MySQL now transpile to Exasol as `SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS`. The full test suite passes (1114 tests), and ruff lint and format checks are clean.

The change is in `sqlglot/generators/exasol.py`, in the existing `show_sql` method next to the `SHOW TABLES` branch. The MySQL parser already maps `SHOW SCHEMAS` onto the same `DATABASES` show node, so one branch covers both. I added `test_show_databases` to `tests/dialects/test_exasol.py` to cover both statements.

I left out `LIKE` and `WHERE` filters on `SHOW DATABASES`. They are currently dropped silently, the same as the `SHOW TABLES` branch already does. Say if you want them mapped onto `SCHEMA_NAME`.

Nothing has been committed.
