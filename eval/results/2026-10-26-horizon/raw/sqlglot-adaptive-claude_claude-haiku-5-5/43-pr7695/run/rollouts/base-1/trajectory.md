# trajectory base-1

final message:
`SHOW DATABASES` and `SHOW SCHEMAS` now transpile to Exasol as `SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS`, and the full test suite passes (1114 tests).

The change is a `DATABASES` branch in `show_sql` in `sqlglot/generators/exasol.py`, placed next to the existing `TABLES` branch. I also added `test_show_databases` in `tests/dialects/test_exasol.py`, which covers `SHOW DATABASES` read from MySQL. `SHOW SCHEMAS` is already parsed to the same node, and I checked its output directly.

Two things to note:
- **`LIKE` filters are dropped.** `SHOW DATABASES LIKE 'x%'` produces the unfiltered query. `SHOW TABLES` already drops its filters the same way, so I matched that pattern. Emitting an unsupported warning or adding a `LIKE` clause would be a small follow-up if you want it.
- **No `mariadb` dialect exists in sqlglot.** MariaDB input goes through the `mysql` dialect, so the test covers `SHOW DATABASES` from MySQL only.

I haven't committed anything.

## events
[tool_use Bash] {"command": "git status --short && grep -rn \"SHOW\\|Show\" sqlglot/dialects/exasol.py sqlglot/parsers/exasol.py sqlglot/generators/exasol.py 2>/dev/null; ls sqlglot/parsers sqlglot/generators 2>/dev/null | grep -i exasol; grep -rn \"EXA_SCHEMAS\\|EXA_ALL_TABLES\\|SHOW TABLES\\|ShowTables\\|show_tables\" sqlglot tests | head -40", "description": "Inspect Exasol dialect and SHOW handling"}
[tool_result] sqlglot/generators/exasol.py:906:    def show_sql(self, expression: exp.Show) -> str:
exasol.py
exasol.py
tests/test_transpile.py:1000:            "SHOW TABLES",
tests/dialects/test_exasol.py:987:    def test_show_tables(self):
tests/dialects/test_exasol.py:989:            "SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = 'TEST'",
tests/dialects/test_exasol.py:990:            read={"mysql": "SHOW TABLES FROM test"},
tests/dialects/test_exasol.py:992:                "exasol": "SELEC
…[1364 chars elided]…
ow)
tests/dialects/test_duckdb.py:2510:        self.validate_identity("SHOW TABLES FROM my_database.my_schema").assert_is(exp.Show)
sqlglot/generators/exasol.py:914:                .from_(exp.table_("EXA_ALL_TABLES", db="SYS"))
tests/dialects/test_mysql.py:1433:    def test_show_tables(self):
tests/dialects/test_mysql.py:1434:        show = self.validate_identity("SHOW TABLES")
tests/dialects/test_mysql.py:1444:        show = self.validate_identity("SHOW TABLES IN test", "SHOW TABLES FROM test")
[tool_use Bash] {"command": "sed -n 895,935p sqlglot/generators/exasol.py && sed -n 980,1010p tests/dialects/test_exasol.py && grep -n \"SHOW\\|show\" sqlglot/dialects/mysql.py | head -30 && grep -n \"def _parse_show_mysql\\|SHOW_PARSERS\\|def _parse_show\" -A3 sqlglot/dialects/mysql.py | head -60", "description": "Read Exasol show_sql and related tests"}
[tool_result]     # https://docs.exasol.com/db/latest/sql/open_schema.htm
    def use_sql(self, expression: exp.Use) -> str:
        kind = expression.args.get("kind")
        if kind and self.sql(kind).upper() != "SCHEMA":
            self.unsupported(f"'USE {self.sql(kind)}' is not supported in Exasol")
            return super().use_sql(expression)
        this = self.sql(expression, "this")
        return f"OPEN SCHEMA {this}"

    # https://docs.exasol.com/db/latest/sql_references/metadata/metadata_syste
…[1902 chars elided]…
 def test_group_by_alias_local(self):
        # GROUP BY bare alias -> LOCAL prefix
        self.validate_all(
            "SELECT city, COUNT(*) AS cnt FROM t GROUP BY LOCAL.cnt",
            read={"mysql": "SELECT city, COUNT(*) AS cnt FROM t GROUP BY cnt"},
            write={"exasol": "SELECT city, COUNT(*) AS cnt FROM t GROUP BY LOCAL.cnt"},
        )
        # GROUP BY expression alias -> LOCAL prefix
154:        COMMANDS = {*tokens.Tokenizer.COMMANDS, TokenType.REPLACE} - {TokenType.SHOW}
[tool_use Bash] {"command": "PYTHONPATH=. python3 -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor q in ['SHOW DATABASES','SHOW SCHEMAS','SHOW TABLES','SHOW DATABASES LIKE \\'x%\\'']:\n    e = sqlglot.parse_one(q, read='mysql')\n    print(repr(q), type(e).__name__, e.name, e.args.get('db'), repr(e.sql('exasol')))\n\" ; grep -n \"DATABASES\\|SCHEMAS\" sqlglot/dialects/mysql.py sqlglot/parsers/mysql.py | head", "description": "Check current MySQL SHOW parsing and Exasol output"}
[tool_result] Unsupported SHOW statement
Unsupported SHOW statement
Unsupported SHOW statement
'SHOW DATABASES' Show DATABASES None ''
'SHOW SCHEMAS' Show DATABASES None ''
'SHOW TABLES' Show TABLES None 'SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = CURRENT_SCHEMA'
"SHOW DATABASES LIKE 'x%'" Show DATABASES None ''
sqlglot/parsers/mysql.py:186:        "DATABASES": _show_parser("DATABASES"),
sqlglot/parsers/mysql.py:187:        "SCHEMAS": _show_parser("DATABASES"),
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-091934-exasol-dialect-transpiling-mysql/base-1/sqlglot/generators/exasol.py", "old_string": "            return self.sql(select)\n\n        return super().show_sql(expression)", "new_string": "            return self.sql(select)\n\n        if expression.name == \"DATABASES\":\n            select = exp.select(exp.column(\"SCHEMA_NAME\")).from_(\n                exp.table_(\"EXA_SCHEMAS\", db=\"SYS\")\n            )\n            return self.sql(select)\n\n        return super().show_sql(expression)"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-091934-exasol-dialect-transpiling-mysql/base-1/sqlglot/generators/exasol.py has been updated successfully.
[assistant] Now a test next to the existing `SHOW TABLES` test.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-091934-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py", "old_string": "                \"exasol\": \"SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = CURRENT_SCHEMA\"\n            },\n        )\n\n    def test_group_by_alias_local(self):", "new_string": "         
…[174 chars elided]…
 self.validate_all(\n            \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            read={\"mysql\": \"SHOW DATABASES\", \"mariadb\": \"SHOW SCHEMAS\"},\n            write={\n                \"exasol\": \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n                \"mysql\": \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            },\n        )\n\n    def test_group_by_alias_local(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-091934-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-091934-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py", "old_string": "            write={\n                \"exasol\": \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n                \"mysql\": \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            },\n        )", "new_string": "            write={\"exasol\": \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\"},\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-091934-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "(ls <work>/env-sqlglot/bin/python >/dev/null 2>&1 && PY=<work>/env-sqlglot/bin/python || PY=python3; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py tests/dialects/test_mysql.py 2>&1 | tail -15; $PY -m pytest -q -p no:cacheprovider --color=no tests 2>&1 | tail -5)", "description": "Run Exasol, MySQL, and full test suites"}
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
1 failed, 71 passed, 1063 subtests passed in 0.39s

sqlglot/helper.py:64: ValueError
=========================== short test summary info ============================
SUBFAILED[mariadb -> SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS] tests/dialects/test_exasol.py::TestExasol::test_show_databases
1 failed, 1114 passed, 18164 subtests passed in 49.84s
[assistant] There's no `mariadb` dialect in sqlglot, so I'll cover `SHOW SCHEMAS` through the `mysql` dialect instead.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-091934-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py", "old_string": "            read={\"mysql\": \"SHOW DATABASES\", \"mariadb\": \"SHOW SCHEMAS\"},", "new_string": "            read={\"mysql\": \"SHOW DATABASES\"},"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-091934-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests 2>&1 | tail -3; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfor q in ['SHOW DATABASES','SHOW SCHEMAS']:\n    print(sqlglot.transpile(q, read='mysql', write='exasol'))\n\" 2>&1; $PY -m ruff check sqlglot/generators/exasol.py tests/dialects/test_exasol.py 2>&1 | tail -2; $PY -m ruff format --check sqlglot/generators/exasol.py tests/dialects/test_exasol.py 2>&1 | tail -2", "description": "Rerun full suite, check SHOW outputs, lint"}
[tool_result] .......................... [ 98%]
.............                   [100%]
1114 passed, 18164 subtests passed in 50.05s
['SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS']
['SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS']
All checks passed!
2 files already formatted
[assistant] `SHOW DATABASES` and `SHOW SCHEMAS` now transpile to Exasol as `SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS`, and the full test suite passes (1114 tests).

The change is a `DATABASES` branch in `show_sql` in `sqlglot/generators/exasol.py`, placed next to the existing `TABLES` branch. I also added `test_show_databases` in `tests/dialects/test_exasol.py`, which covers `SHOW DATABASES` read from MySQL. `SHOW SCHEMAS` is already parsed to the same node, and I checked its output directly.

Two things to note:
- **`LIKE` filters are dropped.** `SHOW DATABASES LIKE 'x%'` produces the unfiltered query. `SHOW TABLES` already drops its filters the same way, so I matched that pattern. Emitting an unsupported warning or adding a `LIKE` clause would be a small follow-up if you want it.
- **No `mariadb` dialect exists in sqlglot.** MariaDB input goes through the `mysql` dialect, so the test covers `SHOW DATABASES` from MySQL only.

I haven't committed anything.
