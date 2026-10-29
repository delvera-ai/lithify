# trajectory base-1

final message:
Exasol now parses `MINUS` as the EXCEPT set operator, so `SELECT a FROM t MINUS SELECT a FROM u` parses and generates `SELECT a FROM t EXCEPT SELECT a FROM u`.

The change is one line in `sqlglot/dialects/exasol.py`: `"MINUS": TokenType.EXCEPT` in the Exasol tokenizer's keywords. This is the same mapping Oracle, Teradata, Snowflake, Redshift, and Hive already use. Before the change, the query failed with "Invalid expression / Unexpected token" at `SELECT`.

I added a round-trip assertion to `test_exasol` in `tests/dialects/test_exasol.py`. The Exasol tests pass (16), and the full suite passes (1087). Ruff check and format are clean on both files.

I haven't committed. Say if you want a commit with the `Co-Authored-By` line.

## events
[tool_use Bash] {"command": "cat sqlglot/dialects/exasol.py | head -80 && grep -n \"MINUS\" sqlglot/tokens.py sqlglot/parser.py sqlglot/dialects/*.py | head -40 && grep -rn \"MINUS\" tests/dialects/test_exasol.py | head", "description": "Inspect Exasol dialect and MINUS references"}
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
sqlglot/dialects/hive.py:106:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/snowflake.py:148:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/oracle.py:78:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/redshift.py:40:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/teradata.py:63:            "MINUS": TokenType.EXCEPT,
[tool_use Bash] {"command": "sed -n 55,70p sqlglot/dialects/teradata.py && grep -n \"EXCEPT\\|MINUS\" tests/dialects/test_exasol.py sqlglot/generators/exasol.py sqlglot/parsers/exasol.py; grep -n \"def test\\|validate\" tests/dialects/test_exasol.py | head -5; <work>/env-sqlglot/bin/python -c \"import sqlglot;print(sqlglot.parse_one('SELECT a FROM t MINUS SELECT a FROM u', read='oracle'))\"", "description": "Check Exasol set-op handling and existing tests"}
[tool_result]             "EQ": TokenType.EQ,
            "GE": TokenType.GTE,
            "GT": TokenType.GT,
            "HELP": TokenType.COMMAND,
            "INS": TokenType.INSERT,
            "LE": TokenType.LTE,
            "LOCKING": TokenType.LOCK,
            "LT": TokenType.LT,
            "MINUS": TokenType.EXCEPT,
            "MOD": TokenType.MOD,
            "NE": TokenType.NEQ,
            "NOT=": TokenType.NEQ,
            "SAMPLE": TokenType.TABLE_SAMPLE,
            "SEL": TokenType.SELECT,
            "ST_GEOMETRY": TokenType.GEOMETRY,
            "TOP": TokenType.TOP,
9:    def test_exasol(self):
10:        self.validate_identity(
14:        self.validate_identity("SYSTIMESTAMP", "SYSTIMESTAMP()")
15:        self.validate_identity("SELECT SYSTIMESTAMP()")
16:        self.validate_identity("SELECT SYSTIMESTAMP(6)")
SELECT a FROM t EXCEPT SELECT a FROM u
[tool_use Bash] {"command": "sed -n 1,30p tests/dialects/test_exasol.py && <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.parse_one('SELECT a FROM t MINUS SELECT a FROM u', read='exasol').sql('exasol'))\"", "description": "Show Exasol test file head and reproduce MINUS failure"}
[tool_result ERROR] Exit code 1
from sqlglot import exp, transpile, UnsupportedError, ErrorLevel
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
        self.validate_identity("SELECT SYSTIMES
…[1964 chars elided]…
o-e2b5bc4f1eee/20261029-092256-exasol-dialect-exasol-allows-bot/base-1/sqlglot/parser.py", line 2110, in _parse_batch_statements
    self.raise_error("Invalid expression / Unexpected token")
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092256-exasol-dialect-exasol-allows-bot/base-1/sqlglot/parser.py", line 1977, in raise_error
    raise error
sqlglot.errors.ParseError: Invalid expression / Unexpected token. Line 1, Col: 28.
  SELECT a FROM t MINUS [4mSELECT[0m a FROM u
[assistant] Confirmed: `MINUS` fails to parse in Exasol. I'll map it to `TokenType.EXCEPT` in the Exasol tokenizer, the same way Oracle, Teradata, and Snowflake do.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092256-exasol-dialect-exasol-allows-bot/base-1/sqlglot/dialects/exasol.py", "old_string": "            \"LONG VARCHAR\": TokenType.TEXT,\n            \"REGEXP_LIKE\": TokenType.RLIKE,", "new_string": "            \"LONG VARCHAR\": TokenType.TEXT,\n            \"MINUS\": TokenType.EXCEPT,\n            \"REGEXP_LIKE\": TokenType.RLIKE,"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092256-exasol-dialect-exasol-allows-bot/base-1/sqlglot/dialects/exasol.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092256-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py", "limit": 12}
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092256-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py", "old_string": "        self.validate_identity(\"SELECT SYSTIMESTAMP(6)\")\n", "new_string": "        self.validate_identity(\"SELECT SYSTIMESTAMP(6)\")\n        self.validate_identity(\n            \"SELECT a FROM t MINUS SELECT a FROM u\",\n            \"SELECT a FROM t EXCEPT SELECT a FROM u\",\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092256-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Run Exasol tests and full test suite"}
[tool_result] ................  [100%]
16 passed, 559 subtests passed in 0.23s
........................................................... [ 78%]
....................................................................................................................................... [ 90%]
............................... [ 93%]
.....................................................................      [100%]
1087 passed, 17844 subtests passed in 49.35s
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/dialects/exasol.py tests/dialects/test_exasol.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/dialects/exasol.py tests/dialects/test_exasol.py) 2>&1 | tail -3", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
2 files already formatted
[assistant] Exasol now parses `MINUS` as the EXCEPT set operator, so `SELECT a FROM t MINUS SELECT a FROM u` parses and generates `SELECT a FROM t EXCEPT SELECT a FROM u`.

The change is one line in `sqlglot/dialects/exasol.py`: `"MINUS": TokenType.EXCEPT` in the Exasol tokenizer's keywords. This is the same mapping Oracle, Teradata, Snowflake, Redshift, and Hive already use. Before the change, the query failed with "Invalid expression / Unexpected token" at `SELECT`.

I added a round-trip assertion to `test_exasol` in `tests/dialects/test_exasol.py`. The Exasol tests pass (16), and the full suite passes (1087). Ruff check and format are clean on both files.

I haven't committed. Say if you want a commit with the `Co-Authored-By` line.
