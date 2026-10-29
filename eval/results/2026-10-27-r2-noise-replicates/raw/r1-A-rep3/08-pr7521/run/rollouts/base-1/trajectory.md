# trajectory base-1

final message:
Exasol now parses `MINUS` as `EXCEPT`, so `SELECT 1 MINUS SELECT 2` transpiles to `SELECT 1 EXCEPT SELECT 2`.

The change is one line in `sqlglot/dialects/exasol.py`: `"MINUS": TokenType.EXCEPT` in the Exasol tokenizer's `KEYWORDS`. Oracle, Snowflake, Teradata, Hive and Redshift already do the same mapping.

I added one identity test to `tests/dialects/test_exasol.py`. The full suite passes (1087 tests) with the project's pytest command. I did not run the linter and did not commit.

## events
[tool_use Bash] {"command": "cat sqlglot/dialects/exasol.py && grep -rn \"MINUS\" sqlglot/ | head -30 && grep -n \"MINUS\\|EXCEPT\" tests/dialects/test_exasol.py | head", "description": "Read Exasol dialect and grep MINUS usage"}
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
sqlglot/dialects/teradata.py:63:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/oracle.py:78:            "MINUS": TokenType.EXCEPT,
[assistant] The other dialects map `MINUS` to `TokenType.EXCEPT` in their tokenizer `KEYWORDS`, so I'll follow that pattern here. Checking the existing Exasol tests first.
[tool_use Bash] {"command": "ls tests/dialects | grep -i exasol; grep -n \"def test_\\|validate_all\\|validate_identity\" tests/dialects/test_exasol.py | head -20; grep -n \"MINUS\" -A3 tests/dialects/test_oracle.py | head -10", "description": "Locate Exasol tests and MINUS examples"}
[tool_result] test_exasol.py
9:    def test_exasol(self):
10:        self.validate_identity(
14:        self.validate_identity("SYSTIMESTAMP", "SYSTIMESTAMP()")
15:        self.validate_identity("SELECT SYSTIMESTAMP()")
16:        self.validate_identity("SELECT SYSTIMESTAMP(6)")
17:        self.validate_identity("SELECT CURDATE()", "SELECT CURRENT_DATE")
18:        self.validate_identity("SELECT USER", "SELECT CURRENT_USER")
19:        self.validate_identity("SELECT USER()", "SELECT CURRENT_USER")
20:        
…[146 chars elided]…
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-112425-exasol-dialect-exasol-allows-bot/base-1/sqlglot/dialects/exasol.py", "old_string": "            \"LONG VARCHAR\": TokenType.TEXT,\n            \"REGEXP_LIKE\": TokenType.RLIKE,", "new_string": "            \"LONG VARCHAR\": TokenType.TEXT,\n            \"MINUS\": TokenType.EXCEPT,\n            \"REGEXP_LIKE\": TokenType.RLIKE,"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-112425-exasol-dialect-exasol-allows-bot/base-1/sqlglot/dialects/exasol.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-112425-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py", "limit": 12}
[tool_result] 1	from sqlglot import exp, transpile, UnsupportedError, ErrorLevel
2	from tests.dialects.test_dialect import Validator
3	
4	
5	class TestExasol(Validator):
6	    dialect = "exasol"
7	    maxDiff = None
8	
9	    def test_exasol(self):
10	        self.validate_identity(
11	            "SELECT 1 AS [x]",
12	            'SELECT 1 AS "x"',
[assistant] Adding a test next to the other set-operation-adjacent checks, then running the Exasol suite.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-112425-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py", "old_string": "        self.validate_identity(\"SELECT FROM_POSIX_TIME(1234567890)\")\n", "new_string": "        self.validate_identity(\"SELECT FROM_POSIX_TIME(1234567890)\")\n        self.validate_identity(\"SELECT 1 MINUS SELECT 2\", \"SELECT 1 EXCEPT SELECT 2\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-112425-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -15", "description": "Run Exasol dialect tests"}
[tool_result] ................  [100%]
16 passed, 559 subtests passed in 0.42s
[assistant] Exasol tests pass. Running the full project suite as the harness requires.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; git status --short", "description": "Run full test suite and show changed files"}
[tool_result] ............................................. [ 11%]
...................................................... [ 16%]
........ [ 17%]
................................. [ 20%]
............................................................................................................................................................................................................................................................... [ 43%]
........................ [ 45%]
......................... [ 48%]

…[230 chars elided]…
[ 68%]
............................................... [ 72%]
........................................................... [ 78%]
....................................................................................................................................... [ 90%]
............................... [ 93%]
.....................................................................      [100%]
1087 passed, 17844 subtests passed in 52.04s
 M sqlglot/dialects/exasol.py
 M tests/dialects/test_exasol.py
[assistant] Exasol now parses `MINUS` as `EXCEPT`, so `SELECT 1 MINUS SELECT 2` transpiles to `SELECT 1 EXCEPT SELECT 2`.

The change is one line in `sqlglot/dialects/exasol.py`: `"MINUS": TokenType.EXCEPT` in the Exasol tokenizer's `KEYWORDS`. Oracle, Snowflake, Teradata, Hive and Redshift already do the same mapping.

I added one identity test to `tests/dialects/test_exasol.py`. The full suite passes (1087 tests) with the project's pytest command. I did not run the linter and did not commit.
