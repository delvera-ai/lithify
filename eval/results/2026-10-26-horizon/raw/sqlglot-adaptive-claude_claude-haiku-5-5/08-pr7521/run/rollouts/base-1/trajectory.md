# trajectory base-1

final message:
Exasol now accepts `MINUS` as a set operator and parses it as `EXCEPT`. The full test suite passes (1088 passed, 17844 subtests).

- **Change:** in `sqlglot/dialects/exasol.py`, I added `"MINUS": TokenType.EXCEPT` to the Exasol tokenizer keywords. This is the same mapping Oracle, Snowflake, Teradata, Redshift and Hive already use.
- **Test:** I added `test_minus` to `tests/dialects/test_exasol.py`. It checks that `... MINUS ...` round-trips to `... EXCEPT ...` in Exasol, and that `EXCEPT` still works unchanged.
- **Output:** Exasol writes the set operator as `EXCEPT`. A `MINUS` query transpiled to DuckDB also comes out as `EXCEPT`.

I haven't committed anything. The project's CLAUDE.md asks for the agent model name at the end of commit messages and PR titles, so I'll include that if you want me to commit.

## events
[tool_use Bash] {"command": "grep -rn \"MINUS\" sqlglot/tokens.py sqlglot/parser.py sqlglot/dialects/*.py | head -40; echo ---; cat sqlglot/dialects/exasol.py | head -80", "description": "Find MINUS handling and read Exasol dialect"}
[tool_result] sqlglot/dialects/hive.py:106:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/teradata.py:63:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/oracle.py:78:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/snowflake.py:148:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/redshift.py:40:            "MINUS": TokenType.EXCEPT,
---
from __future__ import annotations


from sqlglot import tokens
from sqlglot.dialects.dialect import (
    Dialect,
    NormalizationStrategy,
)
…[1368 chars elided]…
  **tokens.Tokenizer.KEYWORDS,
            "USER": TokenType.CURRENT_USER,
            # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/if.htm
            "ENDIF": TokenType.END,
            "LONG VARCHAR": TokenType.TEXT,
            "REGEXP_LIKE": TokenType.RLIKE,
            "SEPARATOR": TokenType.SEPARATOR,
            "SYSTIMESTAMP": TokenType.SYSTIMESTAMP,
        }
        KEYWORDS.pop("DIV")

    Parser = ExasolParser

    Generator = ExasolGenerator
[assistant] The Exasol tokenizer is where the mapping belongs. Other dialects (Oracle, Snowflake, Teradata) map `MINUS` to `TokenType.EXCEPT` the same way, so I'll follow that pattern.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-160542-exasol-dialect-exasol-allows-bot/base-1/sqlglot/dialects/exasol.py", "old_string": "            \"LONG VARCHAR\": TokenType.TEXT,\n            \"REGEXP_LIKE\": TokenType.RLIKE,", "new_string": "            \"LONG VARCHAR\": TokenType.TEXT,\n            \"MINUS\": TokenType.EXCEPT,\n            \"REGEXP_LIKE\": TokenType.RLIKE,"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-160542-exasol-dialect-exasol-allows-bot/base-1/sqlglot/dialects/exasol.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"EXCEPT\\|MINUS\" tests/dialects/test_exasol.py | head; <work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nprint(repr(sqlglot.parse_one('SELECT a FROM t MINUS SELECT a FROM u', read='exasol')))\nprint(sqlglot.transpile('SELECT a FROM t MINUS SELECT a FROM u', read='exasol', write='exasol'))\nprint(sqlglot.transpile('SELECT a FROM t EXCEPT SELECT a FROM u', read='exasol', write='exasol'))\nprint(sqlglot.transpile('SELECT a FROM t MINUS SELECT a FROM u', read='exasol', write='duckdb'))\n\"", "description": "Check existing tests and verify MINUS parses as EXCEPT"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[assistant] The `sqlglot` package isn't installed in that venv, so I'll run against the worktree source directly.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\nprint(repr(sqlglot.parse_one('SELECT a FROM t MINUS SELECT a FROM u', read='exasol')))\nprint(sqlglot.transpile('SELECT a FROM t MINUS SELECT a FROM u', read='exasol', write='exasol'))\nprint(sqlglot.transpile('SELECT a FROM t EXCEPT SELECT a FROM u', read='exasol', write='exasol'))\nprint(sqlglot.transpile('SELECT a FROM t MINUS SELECT a FROM u', read='exasol', write='duckdb'))\n\"; grep -n \"EXCEPT\\|MINUS\" tests/dialects/test_exasol.py | head", "description": "Verify MINUS parses as EXCEPT in Exasol"}
[tool_result] Except(
  this=Select(
    expressions=[
      Column(
        this=Identifier(this=a, quoted=False))],
    from_=From(
      this=Table(
        this=Identifier(this=t, quoted=False)))),
  distinct=True,
  expression=Select(
    expressions=[
      Column(
        this=Identifier(this=a, quoted=False))],
    from_=From(
      this=Table(
        this=Identifier(this=u, quoted=False)))))
['SELECT a FROM t EXCEPT SELECT a FROM u']
['SELECT a FROM t EXCEPT SELECT a FROM u']
['SELECT a FROM t EXCEPT SELECT a FROM u']
[assistant] `MINUS` now parses to the same `Except` node as `EXCEPT`. Next I'll add a regression test, so I need the structure of the Exasol test file first.
[tool_use Bash] {"command": "grep -n \"def test_\" tests/dialects/test_exasol.py | head -30; sed -n 1,25p tests/dialects/test_exasol.py", "description": "Inspect Exasol test file structure"}
[tool_result] 9:    def test_exasol(self):
35:    def test_exasol_keywords(self):
42:    def test_qualify_unscoped_star(self):
80:    def test_type_mappings(self):
136:    def test_mod(self):
147:    def test_bits(self):
248:    def test_aggregateFunctions(self):
298:    def test_stringFunctions(self):
430:    def test_datetime_functions(self):
617:    def test_number_functions(self):
666:    def test_scalar(self):
801:    def test_odbc_date_literals(self):
808:    def test_local_prefix_for_alias(self):
859: 
…[679 chars elided]…
lf.validate_identity("SELECT USER", "SELECT CURRENT_USER")
        self.validate_identity("SELECT USER()", "SELECT CURRENT_USER")
        self.validate_identity("SELECT CURRENT_USER", "SELECT CURRENT_USER")
        self.validate_identity("CURRENT_SCHEMA").assert_is(exp.CurrentSchema)
        self.validate_identity("SELECT NOW()", "SELECT CURRENT_TIMESTAMP()")
        self.validate_identity("SELECT FROM_POSIX_TIME(1234567890)")
        self.validate_all(
            "SELECT FROM_POSIX_TIME(col)",
[tool_use Bash] {"command": "sed -n 35,41p tests/dialects/test_exasol.py", "description": "Read keywords test to place new test"}
[tool_result]     def test_exasol_keywords(self):
        keywords = ["CS", "ADD", "BOOLEAN", "CALL", "CONTROL"]

        for keyword in keywords:
            with self.subTest(keyword=keyword):
                self.validate_identity(f"SELECT 1 AS {keyword}", f'SELECT 1 AS "{keyword}"')
[assistant] I'll add a small test right after the keywords test, using the existing `validate_identity` helper so `MINUS` round-trips to `EXCEPT`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-160542-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py", "old_string": "                self.validate_identity(f\"SELECT 1 AS {keyword}\", f'SELECT 1 AS \"{keyword}\"')\n", "new_string": "                self.validate_identity(f\"SELECT 1 AS {keyword}\", f'SELECT 1 AS \"{keyword}\"')\n\n    def test_minus(self):\n        self.validate_identity(\n            \"SELECT a FROM t MINUS SELECT a FROM u\",\n            \"SELECT a FROM t EXCEPT SELECT a FROM u\",\n        )\n        self.validate_identity(\"SELECT a FROM t EXCEPT SELECT a FROM u\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-160542-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Run Exasol tests and full test suite"}
[tool_result] ................. [100%]
17 passed, 559 subtests passed in 0.51s
........................................................... [ 78%]
....................................................................................................................................... [ 90%]
............................... [ 93%]
......................................................................     [100%]
1088 passed, 17844 subtests passed in 55.06s
[assistant] Exasol now accepts `MINUS` as a set operator and parses it as `EXCEPT`. The full test suite passes (1088 passed, 17844 subtests).

- **Change:** in `sqlglot/dialects/exasol.py`, I added `"MINUS": TokenType.EXCEPT` to the Exasol tokenizer keywords. This is the same mapping Oracle, Snowflake, Teradata, Redshift and Hive already use.
- **Test:** I added `test_minus` to `tests/dialects/test_exasol.py`. It checks that `... MINUS ...` round-trips to `... EXCEPT ...` in Exasol, and that `EXCEPT` still works unchanged.
- **Output:** Exasol writes the set operator as `EXCEPT`. A `MINUS` query transpiled to DuckDB also comes out as `EXCEPT`.

I haven't committed anything. The project's CLAUDE.md asks for the agent model name at the end of commit messages and PR titles, so I'll include that if you want me to commit.
