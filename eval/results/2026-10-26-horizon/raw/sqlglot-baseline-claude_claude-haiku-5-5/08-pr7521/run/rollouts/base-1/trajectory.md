# trajectory base-1

final message:
Exasol now parses `MINUS` as the set-difference operator, the same as `EXCEPT`. The full test suite passes (1088 passed), and ruff check and format are clean.

Changes:
- **`sqlglot/dialects/exasol.py`**: added `"MINUS": TokenType.EXCEPT` to the Exasol tokenizer keywords. This follows the same pattern Oracle, Snowflake, Teradata and the others already use.
- **`tests/dialects/test_exasol.py`**: added `test_minus`, which checks that `SELECT 1 MINUS SELECT 2` round-trips as `SELECT 1 EXCEPT SELECT 2`, and that `EXCEPT` still works.

I haven't committed anything. Say if you want a commit, and I'll add the model attribution line to the message as the repo requires.

## events
[tool_use Bash] {"command": "cat sqlglot/dialects/exasol.py | head -80 && grep -rn \"MINUS\" sqlglot/ tests/dialects/test_exasol.py | head -30", "description": "Read Exasol dialect and grep MINUS usages"}
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
…[1364 chars elided]…
           "SYSTIMESTAMP": TokenType.SYSTIMESTAMP,
        }
        KEYWORDS.pop("DIV")

    Parser = ExasolParser

    Generator = ExasolGenerator
sqlglot/dialects/redshift.py:40:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/hive.py:106:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/snowflake.py:148:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/oracle.py:78:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/teradata.py:63:            "MINUS": TokenType.EXCEPT,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-134555-exasol-dialect-exasol-allows-bot/base-1/sqlglot/dialects/exasol.py", "old_string": "            \"LONG VARCHAR\": TokenType.TEXT,\n            \"REGEXP_LIKE\": TokenType.RLIKE,", "new_string": "            \"LONG VARCHAR\": TokenType.TEXT,\n            \"MINUS\": TokenType.EXCEPT,\n            \"REGEXP_LIKE\": TokenType.RLIKE,"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-134555-exasol-dialect-exasol-allows-bot/base-1/sqlglot/dialects/exasol.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"def test\\|validate_all\\|validate_identity\" tests/dialects/test_exasol.py | head -20; grep -n \"EXCEPT\\|MINUS\" tests/dialects/test_oracle.py | head -5", "description": "Locate Exasol tests and an Oracle MINUS example"}
[tool_result] 9:    def test_exasol(self):
10:        self.validate_identity(
14:        self.validate_identity("SYSTIMESTAMP", "SYSTIMESTAMP()")
15:        self.validate_identity("SELECT SYSTIMESTAMP()")
16:        self.validate_identity("SELECT SYSTIMESTAMP(6)")
17:        self.validate_identity("SELECT CURDATE()", "SELECT CURRENT_DATE")
18:        self.validate_identity("SELECT USER", "SELECT CURRENT_USER")
19:        self.validate_identity("SELECT USER()", "SELECT CURRENT_USER")
20:        self.validate_i
…[131 chars elided]…
ma)
22:        self.validate_identity("SELECT NOW()", "SELECT CURRENT_TIMESTAMP()")
23:        self.validate_identity("SELECT FROM_POSIX_TIME(1234567890)")
24:        self.validate_all(
35:    def test_exasol_keywords(self):
40:                self.validate_identity(f"SELECT 1 AS {keyword}", f'SELECT 1 AS "{keyword}"')
42:    def test_qualify_unscoped_star(self):
43:        self.validate_all(
49:        self.validate_identity(
52:        self.validate_identity(
55:        self.validate_identity(
[tool_use Bash] {"command": "sed -n 35,42p tests/dialects/test_exasol.py", "description": "Show Exasol keyword test section"}
[tool_result]     def test_exasol_keywords(self):
        keywords = ["CS", "ADD", "BOOLEAN", "CALL", "CONTROL"]

        for keyword in keywords:
            with self.subTest(keyword=keyword):
                self.validate_identity(f"SELECT 1 AS {keyword}", f'SELECT 1 AS "{keyword}"')

    def test_qualify_unscoped_star(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-134555-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py", "old_string": "                self.validate_identity(f\"SELECT 1 AS {keyword}\", f'SELECT 1 AS \"{keyword}\"')\n\n    def test_qualify_unscoped_star(self):", "new_string": "                self.validate_identity(f\"SELECT 1 AS {keyword}\", f'SELECT 1 AS \"{keyword}\"')\n\n    def test_minus(self):\n        self.validate_identity(\"SELECT 1 MINUS SELECT 2\", \"SELECT 1 EXCEPT SELECT 2\")\n        self.validate_identity(\"SELECT 1 EXCEPT SELECT 2\")\n\n    def test_qualify_unscoped_star(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-134555-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -15", "description": "Run Exasol dialect tests"}
[tool_result] ................. [100%]
17 passed, 559 subtests passed in 0.38s
[assistant] Exasol tests pass. Now the full suite, plus a style check.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m ruff check sqlglot/dialects/exasol.py tests/dialects/test_exasol.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/dialects/exasol.py tests/dialects/test_exasol.py 2>&1 | tail -2", "description": "Run full test suite and ruff checks"}
[tool_result] ........................................................... [ 78%]
....................................................................................................................................... [ 90%]
............................... [ 93%]
......................................................................     [100%]
1088 passed, 17844 subtests passed in 50.37s
All checks passed!
2 files already formatted
[assistant] Exasol now parses `MINUS` as the set-difference operator, the same as `EXCEPT`. The full test suite passes (1088 passed), and ruff check and format are clean.

Changes:
- **`sqlglot/dialects/exasol.py`**: added `"MINUS": TokenType.EXCEPT` to the Exasol tokenizer keywords. This follows the same pattern Oracle, Snowflake, Teradata and the others already use.
- **`tests/dialects/test_exasol.py`**: added `test_minus`, which checks that `SELECT 1 MINUS SELECT 2` round-trips as `SELECT 1 EXCEPT SELECT 2`, and that `EXCEPT` still works.

I haven't committed anything. Say if you want a commit, and I'll add the model attribution line to the message as the repo requires.
