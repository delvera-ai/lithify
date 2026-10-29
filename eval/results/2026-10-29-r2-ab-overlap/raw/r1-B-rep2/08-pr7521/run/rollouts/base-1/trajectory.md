# trajectory base-1

final message:
Exasol now parses `MINUS` as the `EXCEPT` set operation. `SELECT 1 MINUS SELECT 2` transpiles to `SELECT 1 EXCEPT SELECT 2`. The full suite passes (1087 tests).

The change is one line in `sqlglot/dialects/exasol.py`: `"MINUS": TokenType.EXCEPT` in the Exasol tokenizer's keywords. This is the same mapping Redshift, Oracle, Snowflake, Hive and Teradata already use. I also added a round-trip assertion to `tests/dialects/test_exasol.py` next to the existing Exasol identity checks.

The edits are uncommitted in the worktree. I didn't commit because you didn't ask for one.

## events
[tool_use Bash] {"command": "grep -n \"MINUS\\|EXCEPT\" sqlglot/dialects/exasol.py sqlglot/dialects/dialect.py | head -40; grep -n \"MINUS\" sqlglot/tokens.py sqlglot/parser.py | head -20", "description": "Find MINUS and EXCEPT handling in dialects and parser"}
[tool_result] 0 matches for 'MINUS\|EXCEPT'
0 matches for 'MINUS'
[tool_use Bash] {"command": "ls sqlglot/dialects/ | grep -i exa; grep -rn \"MINUS\" sqlglot/ | head -20; grep -n \"TokenType.EXCEPT\" sqlglot/parser.py | head", "description": "Search for MINUS token and EXCEPT parser usage"}
[tool_result] exasol.py  2.0K
sqlglot/dialects/redshift.py:40:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/hive.py:106:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/snowflake.py:148:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/oracle.py:78:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/teradata.py:63:            "MINUS": TokenType.EXCEPT,
2 matches in 2 files:

5564:0:
sqlglot/parser.py:926:TokenType.EXCEPT,
[tool_use Bash] {"command": "cat sqlglot/dialects/exasol.py; sed -n 30,50p sqlglot/dialects/redshift.py; grep -rn \"MINUS\" tests/dialects/test_oracle.py tests/dialects/test_exasol.py tests/dialects/test_redshift.py 2>/dev/null | head", "description": "Read Exasol dialect and MINUS usage in tests"}
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
…[1714 chars elided]…
     "(+)": TokenType.JOIN_MARKER,
            "HLLSKETCH": TokenType.HLLSKETCH,
            "MINUS": TokenType.EXCEPT,
            "SUPER": TokenType.SUPER,
            "TOP": TokenType.TOP,
            "UNLOAD": TokenType.COMMAND,
            "VARBYTE": TokenType.VARBINARY,
            "BINARY VARYING": TokenType.VARBINARY,
        }
        KEYWORDS.pop("VALUES")

        # Redshift allows # to appear as a table identifier prefix
        SINGLE_TOKENS = Postgres.Tokenizer.SINGLE_TOKENS.copy()
[assistant] The Exasol tokenizer inherits base keywords, so adding `MINUS` there mirrors how Redshift, Oracle and Teradata do it. I'll make the change and add a test.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-135100-exasol-dialect-exasol-allows-bot/base-1/sqlglot/dialects/exasol.py", "old_string": "            \"LONG VARCHAR\": TokenType.TEXT,\n            \"REGEXP_LIKE\": TokenType.RLIKE,", "new_string": "            \"LONG VARCHAR\": TokenType.TEXT,\n            \"MINUS\": TokenType.EXCEPT,\n            \"REGEXP_LIKE\": TokenType.RLIKE,"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-135100-exasol-dialect-exasol-allows-bot/base-1/sqlglot/dialects/exasol.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"def test\\|validate_all\\|validate_identity\" tests/dialects/test_exasol.py | head -30", "description": "List existing Exasol dialect tests"}
[tool_result] 157 matches in 18 files:

136:0:
147:0:
248:0:
298:0:
35:0:
42:0:
430:0:
617:0:
666:0:
80:0:
801:0:
808:0:
859:0:
877:0:
878:0:"a"}', '$.d' NULL ON ERROR) AS x""")
890:0:
9:0:
tests/dialects/test_exasol.py:10:self.validate_identity(
tests/dialects/test_exasol.py:14:self.validate_identity("SYSTIMESTAMP", "SYSTIMESTAMP()")
tests/dialects/test_exasol.py:15:self.validate_identity("SELECT SYSTIMESTAMP()")
tests/dialects/test_exasol.py:16:self.validate_identity("SELECT SYSTIMESTAMP(6)")
tests/dialects
…[175 chars elided]…
R")
tests/dialects/test_exasol.py:19:self.validate_identity("SELECT USER()", "SELECT CURRENT_USER")
tests/dialects/test_exasol.py:20:self.validate_identity("SELECT CURRENT_USER", "SELECT CURRENT_USER")
tests/dialects/test_exasol.py:21:self.validate_identity("CURRENT_SCHEMA").assert_is(exp.CurrentSchema)
tests/dialects/test_exasol.py:22:self.validate_identity("SELECT NOW()", "SELECT CURRENT_TIMESTAMP()")
tests/dialects/test_exasol.py:23:self.validate_identity("SELECT FROM_POSIX_TIME(1234567890)")
[tool_use Bash] {"command": "sed -n 1,30p tests/dialects/test_exasol.py", "description": "Read the start of the Exasol test file"}
[tool_result] from sqlglot import exp, transpile, UnsupportedError, ErrorLevel
from tests.dialects.test_dialect import Validator


class TestExasol(Validator):
    dialect = "exasol"
    maxDiff = None

    def test_exasol(self):
        self.validate_identity(
            "SELECT 1 AS [x]",
            'SELECT 1 AS "x"',
        )
        self.validate_identity("SYSTIMESTAMP", "SYSTIMESTAMP()")
        self.validate_identity("SELECT SYSTIMESTAMP()")
        self.validate_identity("SELECT SYSTIMESTAMP(6)")
  
…[247 chars elided]…
ECT CURRENT_USER", "SELECT CURRENT_USER")
        self.validate_identity("CURRENT_SCHEMA").assert_is(exp.CurrentSchema)
        self.validate_identity("SELECT NOW()", "SELECT CURRENT_TIMESTAMP()")
        self.validate_identity("SELECT FROM_POSIX_TIME(1234567890)")
        self.validate_all(
            "SELECT FROM_POSIX_TIME(col)",
            read={
                "mysql": "SELECT FROM_UNIXTIME(col)",
            },
            write={
                "exasol": "SELECT FROM_POSIX_TIME(col)",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-135100-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py", "old_string": "        self.validate_identity(\"SELECT FROM_POSIX_TIME(1234567890)\")\n", "new_string": "        self.validate_identity(\"SELECT FROM_POSIX_TIME(1234567890)\")\n        self.validate_identity(\"SELECT 1 MINUS SELECT 2\", \"SELECT 1 EXCEPT SELECT 2\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-135100-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py tests/dialects/test_oracle.py tests/dialects/test_redshift.py 2>&1 | tail -15", "description": "Run Exasol and related dialect tests"}
[tool_result] ................. [ 29%]
........................................      [100%]
57 passed, 946 subtests passed in 0.60s
[assistant] Targeted tests pass. Next I'll run the full suite, the project's check command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite"}
[tool_result] ............................................. [ 11%]
...................................................... [ 16%]
........ [ 17%]
................................. [ 20%]
............................................................................................................................................................................................................................................................... [ 43%]
........................ [ 45%]
......................... [ 48%]

…[167 chars elided]…
.............................................................. [ 68%]
............................................... [ 72%]
........................................................... [ 78%]
....................................................................................................................................... [ 90%]
............................... [ 93%]
.....................................................................      [100%]
1087 passed, 17844 subtests passed in 54.14s
[assistant] Exasol now parses `MINUS` as the `EXCEPT` set operation. `SELECT 1 MINUS SELECT 2` transpiles to `SELECT 1 EXCEPT SELECT 2`. The full suite passes (1087 tests).

The change is one line in `sqlglot/dialects/exasol.py`: `"MINUS": TokenType.EXCEPT` in the Exasol tokenizer's keywords. This is the same mapping Redshift, Oracle, Snowflake, Hive and Teradata already use. I also added a round-trip assertion to `tests/dialects/test_exasol.py` next to the existing Exasol identity checks.

The edits are uncommitted in the worktree. I didn't commit because you didn't ask for one.
