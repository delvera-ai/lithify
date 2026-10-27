# trajectory base-1

final message:
Exasol now accepts `MINUS` as a set operator and parses it as `exp.Except`, the same as `EXCEPT`.

The change is one line in `sqlglot/dialects/exasol.py`: `"MINUS": TokenType.EXCEPT` in the Exasol tokenizer's keywords, matching what Oracle, Snowflake, Redshift, Hive and Teradata already do. I also added `test_minus` to `tests/dialects/test_exasol.py`. It checks that `MINUS` round-trips to `EXCEPT`, that `EXCEPT` still works, and that the parsed AST node is `exp.Except`. I didn't change or weaken any existing test.

Verification:
- `tests/dialects/test_exasol.py`: 17 passed, 559 subtests passed.
- Full suite via `run_suite.py`: `SUMMARY: 1088 passed, 17844 subtests passed in 81.34s`, `EXIT: 0`.
- `ruff check` and `ruff format --check` pass on both changed files.

Changes are uncommitted in the worktree.

## events
[tool_use Bash] {"command": "ls sqlglot/dialects/exasol.py sqlglot/parsers/exasol.py sqlglot/generators/exasol.py 2>&1; grep -rn \"MINUS\" sqlglot/tokens.py sqlglot/parser.py sqlglot/parsers/*.py sqlglot/dialects/*.py | head -30; grep -rn \"MINUS\\|EXCEPT\" tests/dialects/test_exasol.py | head"}
[tool_result] sqlglot/dialects/exasol.py
sqlglot/generators/exasol.py
sqlglot/parsers/exasol.py
sqlglot/dialects/teradata.py:63:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/hive.py:106:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/oracle.py:78:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/redshift.py:40:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/snowflake.py:148:            "MINUS": TokenType.EXCEPT,
[tool_use Bash] {"command": "cat sqlglot/dialects/exasol.py; sed -n 1,60p sqlglot/parsers/exasol.py; grep -n \"KEYWORDS\" -A3 sqlglot/dialects/oracle.py | head; sed -n 70,85p sqlglot/dialects/oracle.py"}
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
…[4455 chars elided]…
OLLECT INTO": TokenType.BULK_COLLECT_INTO,
            "COLUMNS": TokenType.COLUMN,
            "MATCH_RECOGNIZE": TokenType.MATCH_RECOGNIZE,
            "MINUS": TokenType.EXCEPT,
            "NVARCHAR2": TokenType.NVARCHAR,
            "ORDER SIBLINGS BY": TokenType.ORDER_SIBLINGS_BY,
            "SAMPLE": TokenType.TABLE_SAMPLE,
            "START": TokenType.BEGIN,
            "TOP": TokenType.TOP,
            "VARCHAR2": TokenType.VARCHAR,
            "SYSTIMESTAMP": TokenType.SYSTIMESTAMP,
[assistant] The Exasol tokenizer doesn't map `MINUS` yet, while Oracle, Snowflake and others do. I'll add the same mapping to Exasol's tokenizer, then check the existing Exasol tests for a place to add coverage.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-184539-exasol-dialect-exasol-allows-bot/base-1/sqlglot/dialects/exasol.py", "old_string": "            \"LONG VARCHAR\": TokenType.TEXT,\n            \"REGEXP_LIKE\": TokenType.RLIKE,", "new_string": "            \"LONG VARCHAR\": TokenType.TEXT,\n            \"MINUS\": TokenType.EXCEPT,\n            \"REGEXP_LIKE\": TokenType.RLIKE,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-184539-exasol-dialect-exasol-allows-bot/base-1/sqlglot/dialects/exasol.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"def test_\\|validate_identity\\|validate_all\" tests/dialects/test_exasol.py | head -60; wc -l tests/dialects/test_exasol.py; grep -n \"EXCEPT\" tests/dialects/test_exasol.py"}
[tool_result] 9:    def test_exasol(self):
10:        self.validate_identity(
14:        self.validate_identity("SYSTIMESTAMP", "SYSTIMESTAMP()")
15:        self.validate_identity("SELECT SYSTIMESTAMP()")
16:        self.validate_identity("SELECT SYSTIMESTAMP(6)")
17:        self.validate_identity("SELECT CURDATE()", "SELECT CURRENT_DATE")
18:        self.validate_identity("SELECT USER", "SELECT CURRENT_USER")
19:        self.validate_identity("SELECT USER()", "SELECT CURRENT_USER")
20:        self.validate_i
…[2491 chars elided]…
AS DATE)")
107:        self.validate_identity("CAST(x AS DATETIME)", "CAST(x AS TIMESTAMP)")
108:        self.validate_identity("CAST(x AS TIMESTAMP)")
109:        self.validate_all(
118:        self.validate_all(
127:        self.validate_identity("CAST(x AS BOOLEAN)")
128:        self.validate_identity(
131:        self.validate_identity(
136:    def test_mod(self):
137:        self.validate_all(
147:    def test_bits(self):
148:        self.validate_all(
     952 tests/dialects/test_exasol.py
[assistant] I'll add a round-trip test and an AST check for `MINUS` next to the existing Exasol identity tests.
[tool_use Bash] {"command": "sed -n 1,8p tests/dialects/test_exasol.py && sed -n 22,42p tests/dialects/test_exasol.py"}
[tool_result] from sqlglot import exp, transpile, UnsupportedError, ErrorLevel
from tests.dialects.test_dialect import Validator


class TestExasol(Validator):
    dialect = "exasol"
    maxDiff = None

        self.validate_identity("SELECT NOW()", "SELECT CURRENT_TIMESTAMP()")
        self.validate_identity("SELECT FROM_POSIX_TIME(1234567890)")
        self.validate_all(
            "SELECT FROM_POSIX_TIME(col)",
            read={
                "mysql": "SELECT FROM_UNIXTIME(col)",
            },
            write={
                "exasol": "SELECT FROM_POSIX_TIME(col)",
                "mysql": "SELECT FROM_UNIXTIME(col)",
            },
        )

    def test_exasol_keywords(self):
        keywords = ["CS", "ADD", "BOOLEAN", "CALL", "CONTROL"]

        for keyword in keywords:
            with self.subTest(keyword=keyword):
                self.validate_identity(f"SELECT 1 AS {keyword}", f'SELECT 1 AS "{keyword}"')

    def test_qualify_unscoped_star(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-184539-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py", "old_string": "    def test_exasol_keywords(self):", "new_string": "    def test_minus(self):\n        self.validate_identity(\"SELECT a FROM t MINUS SELECT a FROM u\", \"SELECT a FROM t EXCEPT SELECT a FROM u\")\n        self.validate_identity(\"SELECT a FROM t EXCEPT SELECT a FROM u\")\n        self.assertIsInstance(\n            parse_one(\"SELECT a FROM t MINUS SELECT a FROM u\", read=\"exasol\"), exp.Except\n        )\n\n    def test_exasol_keywords(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-184539-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py has been updated successfully.
[assistant] The new test uses `parse_one`, which the file doesn't import yet, and the first line is probably over the length limit. Fixing both.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-184539-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py", "old_string": "from sqlglot import exp, transpile, UnsupportedError, ErrorLevel", "new_string": "from sqlglot import exp, parse_one, transpile, UnsupportedError, ErrorLevel"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-184539-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-184539-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py", "old_string": "        self.validate_identity(\"SELECT a FROM t MINUS SELECT a FROM u\", \"SELECT a FROM t EXCEPT SELECT a FROM u\")\n        self.validate_identity(\"SELECT a FROM t EXCEPT SELECT a FROM u\")\n        self
…[99 chars elided]…
"), exp.Except\n        )", "new_string": "        self.validate_identity(\n            \"SELECT a FROM t MINUS SELECT a FROM u\", \"SELECT a FROM t EXCEPT SELECT a FROM u\"\n        )\n        self.validate_identity(\"SELECT a FROM t EXCEPT SELECT a FROM u\")\n        self.assertIsInstance(\n            parse_one(\"SELECT a FROM t MINUS SELECT a FROM u\", read=\"exasol\"), exp.Except\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-184539-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py has been updated successfully.
[assistant] Now the Exasol test file, using the project's interpreter from the harness notes.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls -la $PY; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -15", "description": "Run Exasol dialect tests"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 26 08:58 <work>/env-sqlglot/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
................. [100%]
17 passed, 559 subtests passed in 0.35s
[assistant] The Exasol tests pass. Next, the full suite through the harness runner, as its notes require.
[tool_use Bash] {"command": "ls .lithify/harness/scripts/ && <work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py 2>&1 | tail -30", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] run_suite.py
WARNING: 1 other pytest process(es) running; expect slower runs:
  34207 02-23:14:53 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-c4822ee66d.log
ELAPSED: 82s
SUMMARY: 1088 passed, 17844 subtests passed in 81.34s (0:01:21)
EXIT: 0
[assistant] The full suite passed. Last, a lint and format check on the two changed files.
[tool_use Bash] {"command": "R=<work>/env-sqlglot/bin; ($R/ruff --version && $R/ruff check sqlglot/dialects/exasol.py tests/dialects/test_exasol.py && $R/ruff format --check sqlglot/dialects/exasol.py tests/dialects/test_exasol.py) 2>&1 | tail -5; git status --short; git diff --stat", "description": "Lint and format check changed files"}
[tool_result] ruff 0.15.6
All checks passed!
2 files already formatted
 M sqlglot/dialects/exasol.py
 M tests/dialects/test_exasol.py
 sqlglot/dialects/exasol.py    |  1 +
 tests/dialects/test_exasol.py | 11 ++++++++++-
 2 files changed, 11 insertions(+), 1 deletion(-)
[assistant] Exasol now accepts `MINUS` as a set operator and parses it as `exp.Except`, the same as `EXCEPT`.

The change is one line in `sqlglot/dialects/exasol.py`: `"MINUS": TokenType.EXCEPT` in the Exasol tokenizer's keywords, matching what Oracle, Snowflake, Redshift, Hive and Teradata already do. I also added `test_minus` to `tests/dialects/test_exasol.py`. It checks that `MINUS` round-trips to `EXCEPT`, that `EXCEPT` still works, and that the parsed AST node is `exp.Except`. I didn't change or weaken any existing test.

Verification:
- `tests/dialects/test_exasol.py`: 17 passed, 559 subtests passed.
- Full suite via `run_suite.py`: `SUMMARY: 1088 passed, 17844 subtests passed in 81.34s`, `EXIT: 0`.
- `ruff check` and `ruff format --check` pass on both changed files.

Changes are uncommitted in the worktree.
