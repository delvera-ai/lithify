# trajectory base-1

final message:
Exasol now transpiles MySQL `SHOW DATABASES` and `SHOW SCHEMAS` to `SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS`, instead of emitting an unsupported empty statement. The full suite passes (1114 passed) and the changed files are ruff-formatted.

The change is in `sqlglot/generators/exasol.py`, in `show_sql`, next to the existing `SHOW TABLES` branch. MySQL parses `SHOW SCHEMAS` as the same `DATABASES` show, so one branch covers both statements.

I added `test_show_databases` to `tests/dialects/test_exasol.py`, covering both statements. I used `mysql` as the source dialect for both because sqlglot has no MariaDB dialect.

`SHOW DATABASES LIKE '...'` and `SHOW DATABASES WHERE ...` still drop their filter silently. I kept the change to the requested mapping. If you want those filters handled, I can add a `WHERE SCHEMA_NAME LIKE ...` translation or an unsupported warning.

## events
[tool_use Bash] {"command": "grep -n -i \"show\" sqlglot/dialects/exasol.py | head -50; grep -rn -i \"SHOW.*SCHEMAS\\|SHOW DATABASES\\|ShowTables\\|SHOW_TABLES\" sqlglot/dialects/mysql.py sqlglot/dialects/exasol.py | head -30", "description": "Find SHOW handling in Exasol and MySQL dialects"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "ls sqlglot/dialects | head -50; grep -rn \"EXA_\\|SHOW\" sqlglot/dialects/exasol.py sqlglot/dialects/mysql.py | head -40", "description": "List dialect files and grep SHOW/EXA_ references"}
[tool_result] __init__.py  3.6K
athena.py  4.3K
bigquery.py  7.1K
clickhouse.py  4.6K
databricks.py  1.1K
dialect.py  91.1K
doris.py  364B
dremio.py  1.6K
drill.py  1.4K
druid.py  224B
duckdb.py  4.2K
dune.py  329B
exasol.py  2.0K
fabric.py  1.8K
hive.py  3.6K
materialize.py  305B
mysql.py  5.7K
oracle.py  3.4K
postgres.py  4.6K
presto.py  2.2K
prql.py  782B
redshift.py  1.9K
risingwave.py  618B
singlestore.py  2.1K
snowflake.py  6.5K
solr.py  535B
spark.py  927B
spark2.py  977B
sqlite.py  1.1K
starrocks.py  529B
tableau.py  432B
teradata.py  2.5K
trino.py  545B
tsql.py  5.3K
sqlglot/dialects/mysql.py:154:        COMMANDS = {*tokens.Tokenizer.COMMANDS, TokenType.REPLACE} - {TokenType.SHOW}
[tool_use Bash] {"command": "cat sqlglot/dialects/exasol.py; grep -n \"_parse_show\\|def _show\\|ShowTables\\|show_sql\\|SHOW\" sqlglot/dialects/mysql.py sqlglot/parser.py sqlglot/generator.py sqlglot/dialects/dialect.py | head -60; git log --oneline -3 -- sqlglot/dialects/exasol.py", "description": "Read Exasol dialect and grep SHOW handling"}
[tool_result] from __future__ import annotations


from sqlglot import tokens
from sqlglot.dialects.dialect import (
    Dialect,
    NormalizationStrategy,
)
from sqlglot.generators.exasol import ExasolGenerator
from sqlglot.parsers.exasol import DATE_UNITS as DATE_UNITS, ExasolParser
from sqlglot.tokens import TokenType


class Exasol(Dialect):
    # https://docs.exasol.com/db/latest/sql_references/basiclanguageelements.htm#SQLidentifier
    NORMALIZATION_STRATEGY = NormalizationStrategy.UPPERCASE
    # htt
…[1973 chars elided]…
_TRIE: t.ClassVar[dict] = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parser.py:4283:if self._match_text_seq("SHOW", "EMPTY", "MATCHES"):
sqlglot/parser.py:4284:text += " SHOW EMPTY MATCHES"
sqlglot/parser.py:9194:def _parse_show(self) -> exp.Expr | None:
sqlglot/parser.py:9195:parser = self._find_parser(self.SHOW_PARSERS, self.SHOW_TRIE)
998b42b4e fix(exasol): enable minus (#7521)
53d56d42e refactor(exasol)!: Extract and compile generator (#7369)
ea76ca554 Chore: unpin ruff (#7287)
[tool_use Bash] {"command": "grep -rn -i \"show\" sqlglot/generators/exasol.py sqlglot/parsers/exasol.py sqlglot/parsers/mysql.py sqlglot/generators/mysql.py; grep -rn \"SHOW\" sqlglot/parsers/mysql.py | head; grep -rn \"ShowTables\\|SHOW_TABLES\\|\\\"TABLES\\\"\" sqlglot/ | head; sed -n 5960,5975p sqlglot/generator.py; grep -n \"class Show\" -A12 sqlglot/expressions/*.py | head -30", "description": "Search Exasol and MySQL parser/generator for SHOW support"}
[tool_result] sqlglot/generators/exasol.py:906:    def show_sql(self, expression: exp.Show) -> str:
sqlglot/generators/exasol.py:919:        return super().show_sql(expression)
sqlglot/parsers/mysql.py:47:def _show_parser(*args: t.Any, **kwargs: t.Any) -> t.Callable[[MySQLParser], exp.Show]:
sqlglot/parsers/mysql.py:48:    def _parse(self: MySQLParser) -> exp.Show:
sqlglot/parsers/mysql.py:49:        return self._parse_show_mysql(*args, **kwargs)
sqlglot/parsers/mysql.py:167:        TokenType.SHOW: lambda sel
…[7116 chars elided]…
,
sqlglot/expressions/ddl.py-195-        "terse": False,
sqlglot/expressions/ddl.py-196-        "target": False,
sqlglot/expressions/ddl.py-197-        "offset": False,
sqlglot/expressions/ddl.py-198-        "starts_with": False,
sqlglot/expressions/ddl.py-199-        "limit": False,
sqlglot/expressions/ddl.py-200-        "from_": False,
sqlglot/expressions/ddl.py-201-        "like": False,
sqlglot/expressions/ddl.py-202-        "where": False,
sqlglot/expressions/ddl.py-203-        "db": False,
[tool_use Bash] {"command": "sed -n 895,925p sqlglot/generators/exasol.py; grep -n \"SHOW\\|show\" tests/dialects/test_exasol.py tests/dialects/test_mysql.py | head -30", "description": "Read Exasol show_sql and existing SHOW tests"}
[tool_result]     # https://docs.exasol.com/db/latest/sql/open_schema.htm
    def use_sql(self, expression: exp.Use) -> str:
        kind = expression.args.get("kind")
        if kind and self.sql(kind).upper() != "SCHEMA":
            self.unsupported(f"'USE {self.sql(kind)}' is not supported in Exasol")
            return super().use_sql(expression)
        this = self.sql(expression, "this")
        return f"OPEN SCHEMA {this}"

    # https://docs.exasol.com/db/latest/sql_references/metadata/metadata_syste
…[2524 chars elided]…
ite_key))
tests/dialects/test_mysql.py:1282:self.assertIsInstance(show, exp.Show)
tests/dialects/test_mysql.py:1283:self.assertEqual(show.name, expected_name)
tests/dialects/test_mysql.py:1285:template = "SHOW {} LIKE '%foo%'"
tests/dialects/test_mysql.py:1286:show = self.validate_identity(template.format(key), template.format(write_key))
tests/dialects/test_mysql.py:1287:self.assertIsInstance(show, exp.Show)
tests/dialects/test_mysql.py:1288:self.assertIsInstance(show.args["like"], exp.Literal)
[tool_use Bash] {"command": "sed -n 985,1005p tests/dialects/test_exasol.py; ls .lithify/harness/scripts/ && printf 'SHOW DATABASES\\nSHOW SCHEMAS\\n' | ~/.cache/lithify/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py 2>&1 | head -20", "description": "View existing Exasol SHOW TABLES test and probe current output"}
[tool_result]             )

    def test_show_tables(self):
        self.validate_all(
            "SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = 'TEST'",
            read={"mysql": "SHOW TABLES FROM test"},
            write={
                "exasol": "SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = 'TEST'"
            },
        )
        self.validate_all(
            "SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = CURRENT_SCHEMA",
            read={"mysql": "SHOW TABLES"},
            write={
                "exasol": "SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = CURRENT_SCHEMA"
            },
        )

    def test_group_by_alias_local(self):
        # GROUP BY bare alias -> LOCAL prefix
        self.validate_all(
probe_parse.py  2.2K
(eval):1: no such file or directory: ~/.cache/lithify/env-sqlglot/bin/python
[tool_use Bash] {"command": "printf 'SHOW DATABASES\\nSHOW SCHEMAS\\n' | <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py 2>&1 | head -30", "description": "Probe current SHOW DATABASES/SCHEMAS output"}
[tool_result] Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-162047-exasol-dialect-transpiling-mysql/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "printf 'SHOW DATABASES\\nSHOW SCHEMAS\\n' | PYTHONPATH=. <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py 2>&1 | head -30", "description": "Probe current SHOW output with repo on path"}
[tool_result] 'SHOW DATABASES' contains unsupported syntax. Falling back to parsing as a 'Command'.
'SHOW DATABASES' contains unsupported syntax. Falling back to parsing as a 'Command'.
'SHOW SCHEMAS' contains unsupported syntax. Falling back to parsing as a 'Command'.
'SHOW SCHEMAS' contains unsupported syntax. Falling back to parsing as a 'Command'.
OK        SHOW DATABASES
          SHOW DATABASES
OK        SHOW SCHEMAS
          SHOW SCHEMAS
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-162047-exasol-dialect-transpiling-mysql/base-1/sqlglot/generators/exasol.py", "old_string": "            return self.sql(select)\n\n        return super().show_sql(expression)", "new_string": "            return self.sql(select)\n\n        if expression.name == \"DATABASES\":\n            select = exp.select(exp.column(\"SCHEMA_NAME\")).from_(\n                exp.table_(\"EXA_SCHEMAS\", db=\"SYS\")\n            )\n            return self.sql(select)\n\n        return super().show_sql(expression)"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-162047-exasol-dialect-transpiling-mysql/base-1/sqlglot/generators/exasol.py has been updated successfully.
[assistant] Now I'll add a test next to `test_show_tables`, mirroring its style.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-162047-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py", "old_string": "                \"exasol\": \"SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = CURRENT_SCHEMA\"\n            },\n        )\n\n    def test_group_by_alias_local(self):", "new_string": "         
…[101 chars elided]…
n            },\n        )\n\n    def test_show_databases(self):\n        self.validate_all(\n            \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            read={\"mysql\": \"SHOW DATABASES\", \"mariadb\": \"SHOW SCHEMAS\"},\n            write={\n                \"exasol\": \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            },\n        )\n\n    def test_group_by_alias_local(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-162047-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -15", "description": "Run Exasol dialect tests"}
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
1 failed, 20 passed, 577 subtests passed in 0.29s
[assistant] MariaDB isn't a separate sqlglot dialect; MySQL covers both statements, so I'll point the test at `mysql` for each.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-162047-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py", "old_string": "        self.validate_all(\n            \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            read={\"mysql\": \"SHOW DATABASES\", \"mariadb\": \"SHOW SCHEMAS\"},\n            write={\n                \"
…[149 chars elided]…
CHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            read={\"mysql\": \"SHOW DATABASES\"},\n            write={\"exasol\": \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\"},\n        )\n        self.validate_all(\n            \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            read={\"mysql\": \"SHOW SCHEMAS\"},\n            write={\"exasol\": \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\"},\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-162047-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py tests/dialects/test_mysql.py 2>&1 | tail -3 && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Run Exasol and MySQL tests, then full suite", "timeout": 300000}
[tool_result] .......................................................................                 [100%]
71 passed, 1065 subtests passed in 0.25s
.......................... [ 98%]
...............                 [100%]
1114 passed, 18166 subtests passed in 50.04s
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/ruff format --check sqlglot/generators/exasol.py tests/dialects/test_exasol.py 2>&1 || true) | tail -3; git diff --stat", "description": "Check formatting and show diff stat"}
[tool_result] 2 files already formatted
sqlglot/generators/exasol.py  |  6 ++++++
 tests/dialects/test_exasol.py | 12 ++++++++++++
 2 files changed, 18 insertions(+)
[assistant] Exasol now transpiles MySQL `SHOW DATABASES` and `SHOW SCHEMAS` to `SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS`, instead of emitting an unsupported empty statement. The full suite passes (1114 passed) and the changed files are ruff-formatted.

The change is in `sqlglot/generators/exasol.py`, in `show_sql`, next to the existing `SHOW TABLES` branch. MySQL parses `SHOW SCHEMAS` as the same `DATABASES` show, so one branch covers both statements.

I added `test_show_databases` to `tests/dialects/test_exasol.py`, covering both statements. I used `mysql` as the source dialect for both because sqlglot has no MariaDB dialect.

`SHOW DATABASES LIKE '...'` and `SHOW DATABASES WHERE ...` still drop their filter silently. I kept the change to the requested mapping. If you want those filters handled, I can add a `WHERE SCHEMA_NAME LIKE ...` translation or an unsupported warning.
