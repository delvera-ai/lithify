# trajectory base-1

final message:
`SHOW DATABASES` and `SHOW SCHEMAS` now transpile to Exasol as `SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS`.

Full suite after the last edit: `SUMMARY: 1114 passed, 18168 subtests passed in 48.93s` / `EXIT: 0`.

**Change**
- `sqlglot/generators/exasol.py`: `show_sql` gets a `DATABASES` branch next to the existing `TABLES` one. The parser already maps `SCHEMAS` to `DATABASES`, so both forms go through it.
- `tests/dialects/test_exasol.py`: new `test_show_databases` covers `SHOW DATABASES`, `SHOW SCHEMAS`, and `SHOW DATABASES LIKE 'test%'`.

**Choices I made**
- **`LIKE` is supported too.** `SHOW DATABASES LIKE 'x'` is a form that contains the named construct, so it was failing silently to `''` as well. It maps to `WHERE SCHEMA_NAME LIKE '<pattern>'`. I uppercased the pattern, matching how the `SHOW TABLES` branch uppercases its schema name, because unquoted Exasol schema names are stored in uppercase.
- **`WHERE` is not supported.** `SHOW DATABASES WHERE ...` still produces empty output with an unsupported warning. MySQL filters on a `Database` column, and I did not want to guess at a mapping to Exasol's `SCHEMA_NAME`. This is the one form still failing.
- **MariaDB has no separate dialect in sqlglot.** It goes through `mysql`, so the tests read `SHOW SCHEMAS` via `mysql`.

I did not commit the change.

## events
[tool_use Bash] {"command": "git status --short && grep -rn \"SHOW\" sqlglot/dialects/exasol.py sqlglot/parsers/exasol.py sqlglot/generators/exasol.py sqlglot/parsers/mysql.py sqlglot/generators/mysql.py | head -60; grep -rn \"EXA_\\|SHOW TABLES\\|ShowTables\\|show_tables\" sqlglot tests/dialects/test_exasol.py | head -30; ls .lithify/harness/skills/ 2>/dev/null; cat .lithify/harness/memory.md 2>/dev/null | head -20", "description": "Inspect repo state and SHOW handling"}
[tool_result] sqlglot/parsers/mysql.py:167:        TokenType.SHOW: lambda self: self._parse_show(),
sqlglot/parsers/mysql.py:170:    SHOW_PARSERS = {
sqlglot/parsers/mysql.py:240:    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/generators/mysql.py:744:        return f"SHOW{full}{global_}{this}{json}{target}{for_table}{types}{db}{query}{log}{position}{channel}{mutex_or_status}{like}{where}{offset}{limit}{for_group}{for_user}{for_role}{into_outfile}"
tests/dialects/test_exasol.py:987:   
…[1172 chars elided]…
on -m pytest -q -p no:cacheprovider --color=no`.
- Layout: expression classes live in `sqlglot/expressions/*.py` (there is no `expressions.py`). A dialect's parser is `sqlglot/parsers/<d>.py` and its generator is `sqlglot/generators/<d>.py`; `sqlglot/dialects/<d>.py` only wires them together.
- The full suite (~1100 tests) takes 60–80 s alone; `tests/test_executor.py::TestExecutor::test_execute_tpcds`
  is slowest and looks hung under CPU contention. Run the dialect's own test file first (<1 s).
[tool_use Bash] {"command": "sed -n 160,240p sqlglot/parsers/mysql.py; grep -n \"_parse_show\\b\\|def _parse_show\" -A25 sqlglot/parsers/mysql.py | sed -n 1,60p; sed -n 895,935p sqlglot/generators/exasol.py; sed -n 980,1010p tests/dialects/test_exasol.py", "description": "Read MySQL SHOW parser and Exasol SHOW TABLES code"}
[tool_result]         ),
        "JSON_VALUE": lambda self: self._parse_json_value(),
        "SUBSTR": lambda self: self._parse_substring(),
    }

    STATEMENT_PARSERS = {
        **parser.Parser.STATEMENT_PARSERS,
        TokenType.SHOW: lambda self: self._parse_show(),
    }

    SHOW_PARSERS = {
        "BINARY LOGS": _show_parser("BINARY LOGS"),
        "MASTER LOGS": _show_parser("BINARY LOGS"),
        "BINLOG EVENTS": _show_parser("BINLOG EVENTS"),
        "CHARACTER SET": _show_parser("CHARACTER SE
…[8097 chars elided]…
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
[tool_use Bash] {"command": "cat > /tmp/probe_show.py <<'EOF'\nimport sqlglot\nfrom sqlglot import exp\nfor q in [\"SHOW DATABASES\", \"SHOW SCHEMAS\", \"SHOW TABLES FROM test\", \"SHOW DATABASES LIKE 'a%'\"]:\n    e = sqlglot.parse_one(q, read=\"mysql\")\n    print(repr(e)[:300])\n    print(q, \"->\", repr(e.sql(\"exasol\")))\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_show.py", "description": "Probe current SHOW DATABASES output for Exasol"}
[tool_result] Unsupported SHOW statement
Unsupported SHOW statement
Unsupported SHOW statement
Show(this=DATABASES, json=False)
SHOW DATABASES -> ''
Show(this=DATABASES, json=False)
SHOW SCHEMAS -> ''
Show(
  this=TABLES,
  db=Identifier(this=test, quoted=False),
  json=False)
SHOW TABLES FROM test -> "SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = 'TEST'"
Show(
  this=DATABASES,
  like=Literal(this='a%', is_string=True),
  json=False)
SHOW DATABASES LIKE 'a%' -> ''
[tool_use Bash] {"command": "sed -n 443,475p sqlglot/parsers/mysql.py; grep -n \"def _show_parser\" -A20 sqlglot/parsers/mysql.py | head -30; grep -n \"def show_sql\" -A12 sqlglot/generators/base.py sqlglot/generators/mysql.py | head -40", "description": "Read SHOW like/where parsing and base show generation"}
[tool_result]             position = self._parse_number() if self._match_text_seq("FROM") else None
            db = None
        else:
            position = None
            db = None

            if self._match(TokenType.FROM) or self._match_text_seq("IN"):
                db = self._parse_id_var()
            elif self._match(TokenType.DOT):
                db = target_id
                target_id = self._parse_id_var()

        channel = self._parse_id_var() if self._match_text_seq("FOR", "CHANNEL") else
…[2023 chars elided]…
ull") else ""
698-        global_ = " GLOBAL" if expression.args.get("global_") else ""
699-
700-        target = self.sql(expression, "target")
701-        target = f" {target}" if target else ""
702-        if expression.name in ("COLUMNS", "INDEX"):
703-            target = f" FROM{target}"
704-        elif expression.name == "GRANTS":
705-            target = f" FOR{target}"
706-        elif expression.name in ("LINKS", "PARTITIONS"):
707-            target = f" ON{target}" if target else ""
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-103454-exasol-dialect-transpiling-mysql/base-1/sqlglot/generators/exasol.py", "old_string": "            return self.sql(select)\n\n        return super().show_sql(expression)", "new_string": "            return self.sql(select)\n\n        if expression.name == \"DATABASES\":\n            select = ex
…[21 chars elided]…
"SCHEMA_NAME\")).from_(\n                exp.table_(\"EXA_SCHEMAS\", db=\"SYS\")\n            )\n            like = expression.args.get(\"like\")\n            if like:\n                pattern = exp.Literal.string(like.name.upper())\n                select = select.where(exp.column(\"SCHEMA_NAME\").like(pattern))\n            return self.sql(select)\n\n        return super().show_sql(expression)"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-103454-exasol-dialect-transpiling-mysql/base-1/sqlglot/generators/exasol.py has been updated successfully.
[assistant] Now the tests, next to the existing `SHOW TABLES` test.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-103454-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py", "old_string": "    def test_group_by_alias_local(self):", "new_string": "    def test_show_databases(self):\n        self.validate_all(\n            \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            read={\"mysql\"
…[155 chars elided]…
       },\n        )\n        self.validate_all(\n            \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS WHERE SCHEMA_NAME LIKE 'TEST%'\",\n            read={\"mysql\": \"SHOW DATABASES LIKE 'test%'\"},\n            write={\n                \"exasol\": \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS WHERE SCHEMA_NAME LIKE 'TEST%'\",\n            },\n        )\n\n    def test_group_by_alias_local(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-103454-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_show.py; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py tests/dialects/test_mysql.py 2>&1 | tail -15", "description": "Rerun probe and Exasol/MySQL dialect tests"}
[tool_result] Show(this=DATABASES, json=False)
SHOW DATABASES -> 'SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS'
Show(this=DATABASES, json=False)
SHOW SCHEMAS -> 'SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS'
Show(
  this=TABLES,
  db=Identifier(this=test, quoted=False),
  json=False)
SHOW TABLES FROM test -> "SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = 'TEST'"
Show(
  this=DATABASES,
  like=Literal(this='a%', is_string=True),
  json=False)
SHOW DATABASES LIKE 'a%' -> "SELECT SCHEMA_NAME FROM SYS.EXA_
…[188 chars elided]…
(close_matches, 0) or ""
        if similar:
            similar = f" Did you mean {similar}?"
    
>       raise ValueError(f"Unknown {kind} '{word}'.{similar}")
E       ValueError: Unknown dialect 'mariadb'.

sqlglot/helper.py:64: ValueError
=========================== short test summary info ============================
SUBFAILED[mariadb -> SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS] tests/dialects/test_exasol.py::TestExasol::test_show_databases
1 failed, 71 passed, 1065 subtests passed in 0.44s
[assistant] MariaDB isn't a separate dialect in sqlglot (it goes through `mysql`), so I'll fix the test to read `SHOW SCHEMAS` via `mysql`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-103454-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py", "old_string": "            read={\"mysql\": \"SHOW DATABASES\", \"mariadb\": \"SHOW SCHEMAS\"},", "new_string": "            read={\"mysql\": \"SHOW DATABASES\"},"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-103454-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-103454-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py", "old_string": "        self.validate_all(\n            \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS WHERE SCHEMA_NAME LIKE 'TEST%'\",", "new_string": "        self.validate_all(\n            \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            read={\"mysql\": \"SHOW SCHEMAS\"},\n            write={\n                \"exasol\": \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            },\n        )\n        self.validate_all(\n            \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS WHERE SCHEMA_NAME LIKE 'TEST%'\","}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-103454-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py has been updated successfully.
[assistant] Now the dialect file, then the full suite via the harness script as its own call.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -3; <work>/env-sqlglot/bin/
…[12 chars elided]…
ff check sqlglot/generators/exasol.py tests/dialects/test_exasol.py 2>&1 | tail -2; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generators/exasol.py tests/dialects/test_exasol.py 2>&1 | tail -2", "description": "Run Exasol dialect tests and lint/format checks"}
[tool_result] ....................                                                [100%]
20 passed, 581 subtests passed in 0.16s
All checks passed!
2 files already formatted
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] WARNING: 1 other pytest process(es) running; expect slower runs:
  34207 03-15:04:24 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-3dbaab1723.log
ELAPSED: 49s
SUMMARY: 1114 passed, 18168 subtests passed in 48.93s
EXIT: 0
[assistant] `SHOW DATABASES` and `SHOW SCHEMAS` now transpile to Exasol as `SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS`.

Full suite after the last edit: `SUMMARY: 1114 passed, 18168 subtests passed in 48.93s` / `EXIT: 0`.

**Change**
- `sqlglot/generators/exasol.py`: `show_sql` gets a `DATABASES` branch next to the existing `TABLES` one. The parser already maps `SCHEMAS` to `DATABASES`, so both forms go through it.
- `tests/dialects/test_exasol.py`: new `test_show_databases` covers `SHOW DATABASES`, `SHOW SCHEMAS`, and `SHOW DATABASES LIKE 'test%'`.

**Choices I made**
- **`LIKE` is supported too.** `SHOW D
…[119 chars elided]…
`WHERE SCHEMA_NAME LIKE '<pattern>'`. I uppercased the pattern, matching how the `SHOW TABLES` branch uppercases its schema name, because unquoted Exasol schema names are stored in uppercase.
- **`WHERE` is not supported.** `SHOW DATABASES WHERE ...` still produces empty output with an unsupported warning. MySQL filters on a `Database` column, and I did not want to guess at a mapping to Exasol's `SCHEMA_NAME`. This is the one form still failing.
- **MariaDB has no separate dialect in sqlglot.** It goes through `mysql`, so the tests read `SHOW SCHEMAS` via `mysql`.

I did not commit the change.
