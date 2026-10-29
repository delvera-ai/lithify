# trajectory base-1

final message:
Exasol now parses `MINUS` as the set operation `EXCEPT`, so `SELECT a FROM x MINUS SELECT a FROM y` reads as `EXCEPT`.

The change is one line in `sqlglot/dialects/exasol.py`: `"MINUS": TokenType.EXCEPT` in the Exasol tokenizer's keywords. Oracle, Teradata, Snowflake, Redshift, and Hive already map `MINUS` the same way.

I also added `test_minus` to `tests/dialects/test_exasol.py`. It checks that Exasol and Oracle `MINUS` queries read as `EXCEPT`, and that Exasol writes `EXCEPT`.

The full suite passes with the project's pytest command: 1088 passed, 17847 subtests passed.

Oracle's generator still writes `EXCEPT` rather than `MINUS`. That was already true before this change and is outside this task, so I left it alone and did not assert it in the test.

I did not commit anything.

## events
[tool_use Bash] {"command": "cat sqlglot/dialects/exasol.py && grep -rn \"MINUS\" sqlglot/tokens.py sqlglot/parser.py sqlglot/dialects/oracle.py sqlglot/dialects/teradata.py sqlglot/dialects/dialect.py | head -30 && ls tests/dialects | grep -i exasol && grep -n \"MINUS\\|EXCEPT\" tests/dialects/test_exasol.py"}
[tool_result ERROR] Exit code 1
from __future__ import annotations


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
    NORMALIZATION_STRATEGY = NormalizationStrategy.UPPERCA
…[1216 chars elided]…
 "ENDIF": TokenType.END,
            "LONG VARCHAR": TokenType.TEXT,
            "REGEXP_LIKE": TokenType.RLIKE,
            "SEPARATOR": TokenType.SEPARATOR,
            "SYSTIMESTAMP": TokenType.SYSTIMESTAMP,
        }
        KEYWORDS.pop("DIV")

    Parser = ExasolParser

    Generator = ExasolGenerator
sqlglot/dialects/oracle.py:78:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/teradata.py:63:            "MINUS": TokenType.EXCEPT,
test_exasol.py  41.8K
0 matches for 'MINUS\|EXCEPT'
[assistant] The Exasol dialect now lives under `sqlglot/parsers/` and `sqlglot/generators/`. Let me check how Oracle and Teradata map `MINUS`, and look at the existing Exasol tests.
[tool_use Bash] {"command": "sed -n 70,85p sqlglot/dialects/oracle.py; sed -n 58,68p sqlglot/dialects/teradata.py; grep -rn \"MINUS\" sqlglot/ | head; grep -n \"EXCEPT\\|MINUS\\|def test\" tests/dialects/test_exasol.py | head -40"}
[tool_result]         KEYWORDS = {
            **tokens.Tokenizer.KEYWORDS,
            "(+)": TokenType.JOIN_MARKER,
            "BINARY_DOUBLE": TokenType.DOUBLE,
            "BINARY_FLOAT": TokenType.FLOAT,
            "BULK COLLECT INTO": TokenType.BULK_COLLECT_INTO,
            "COLUMNS": TokenType.COLUMN,
            "MATCH_RECOGNIZE": TokenType.MATCH_RECOGNIZE,
            "MINUS": TokenType.EXCEPT,
            "NVARCHAR2": TokenType.NVARCHAR,
            "ORDER SIBLINGS BY": TokenType.ORDER_SIBLINGS_B
…[603 chars elided]…
okenType.SELECT,
sqlglot/dialects/redshift.py:40:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/hive.py:106:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/snowflake.py:148:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/oracle.py:78:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/teradata.py:63:            "MINUS": TokenType.EXCEPT,
16 matches in 16 files:

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
890:0:
9:0:
[assistant] Oracle, Teradata, Snowflake, Redshift, and Hive all map `MINUS` to `TokenType.EXCEPT` in the tokenizer. Exasol should do the same. I'll make the change, then add a test next to the existing Exasol set-operation tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-174458-exasol-dialect-exasol-allows-bot/base-1/sqlglot/dialects/exasol.py", "old_string": "            \"LONG VARCHAR\": TokenType.TEXT,\n            \"REGEXP_LIKE\": TokenType.RLIKE,", "new_string": "            \"LONG VARCHAR\": TokenType.TEXT,\n            \"MINUS\": TokenType.EXCEPT,\n            \"REGEXP_LIKE\": TokenType.RLIKE,"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-174458-exasol-dialect-exasol-allows-bot/base-1/sqlglot/dialects/exasol.py has been updated successfully.
[tool_use Bash] {"command": "rtk proxy grep -n \"EXCEPT\\|INTERSECT\\|UNION\" tests/dialects/test_exasol.py | head -20; rtk proxy grep -n \"def test_\" tests/dialects/test_exasol.py | head -5", "description": "Find existing set-operation tests in Exasol test file"}
[tool_result] 9:    def test_exasol(self):
35:    def test_exasol_keywords(self):
42:    def test_qualify_unscoped_star(self):
80:    def test_type_mappings(self):
136:    def test_mod(self):
[tool_use Bash] {"command": "sed -n 130,160p tests/dialects/test_exasol.py", "description": "Read the end of the Exasol test file"}
[tool_result]         )
        self.validate_identity(
            "CAST(x AS TIMESTAMP(3) WITH LOCAL TIME ZONE)",
            "CAST(x AS TIMESTAMP WITH LOCAL TIME ZONE)",
        )

    def test_mod(self):
        self.validate_all(
            "SELECT MOD(x, 10)",
            read={"exasol": "SELECT MOD(x, 10)"},
            write={
                "teradata": "SELECT x MOD 10",
                "mysql": "SELECT x % 10",
                "exasol": "SELECT MOD(x, 10)",
            },
        )

    def test_bits(self):
        self.validate_all(
            "SELECT BIT_AND(x, 1)",
            read={
                "exasol": "SELECT BIT_AND(x, 1)",
                "duckdb": "SELECT x & 1",
                "presto": "SELECT BITWISE_AND(x, 1)",
                "spark": "SELECT x & 1",
            },
            write={
                "exasol": "SELECT BIT_AND(x, 1)",
                "duckdb": "SELECT x & 1",
                "hive": "SELECT x & 1",
                "presto": "SELECT BITWISE_AND(x, 1)",
[assistant] I'll add a test that reads `MINUS` as `EXCEPT` in Exasol and checks the cross-dialect output.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-174458-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py", "old_string": "    def test_bits(self):\n        self.validate_all(", "new_string": "    def test_minus(self):\n        self.validate_all(\n            \"SELECT a FROM x EXCEPT SELECT a FROM y\",\n            read={\n     
…[4 chars elided]…
       \"exasol\": \"SELECT a FROM x MINUS SELECT a FROM y\",\n                \"oracle\": \"SELECT a FROM x MINUS SELECT a FROM y\",\n            },\n            write={\n                \"exasol\": \"SELECT a FROM x EXCEPT SELECT a FROM y\",\n                \"oracle\": \"SELECT a FROM x MINUS SELECT a FROM y\",\n            },\n        )\n\n    def test_bits(self):\n        self.validate_all("}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-174458-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py has been updated successfully.
[assistant] Now I'll run the Exasol tests with the project's pytest command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -30", "description": "Run the Exasol dialect test file"}
[tool_result] ................. [100%]
=================================== FAILURES ===================================
___ TestExasol.test_minus [SELECT a FROM x EXCEPT SELECT a FROM y -> oracle] ___
tests/dialects/test_dialect.py:101: in validate_all
    self.assertEqual(
E   AssertionError: 'SELECT a FROM x EXCEPT SELECT a FROM y' != 'SELECT a FROM x MINUS SELECT a FROM y'
E   - SELECT a FROM x EXCEPT SELECT a FROM y
E   ?                 ^^^^^^
E   + SELECT a FROM x MINUS SELECT a FROM y
E   ?                 ^^^^^
=========================== short test summary info ============================
SUBFAILED[SELECT a FROM x EXCEPT SELECT a FROM y -> oracle] tests/dialects/test_exasol.py::TestExasol::test_minus
1 failed, 17 passed, 562 subtests passed in 0.43s
[assistant] The one failure is my own test's expectation, not the change. Oracle's generator emits `EXCEPT`, not `MINUS`, which is existing behavior outside this task. I'll drop that Oracle write assertion and keep the read check.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-174458-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py", "old_string": "            write={\n                \"exasol\": \"SELECT a FROM x EXCEPT SELECT a FROM y\",\n                \"oracle\": \"SELECT a FROM x MINUS SELECT a FROM y\",\n            },\n        )\n\n    def test_bits(self):", "new_string": "            write={\n                \"exasol\": \"SELECT a FROM x EXCEPT SELECT a FROM y\",\n            },\n        )\n\n    def test_bits(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-174458-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -3 && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Rerun Exasol tests and then the full test suite"}
[tool_result] ................. [100%]
17 passed, 562 subtests passed in 0.14s
........................................................... [ 78%]
....................................................................................................................................... [ 90%]
............................... [ 93%]
.........................................................................  [100%]
1088 passed, 17847 subtests passed in 48.50s
[assistant] Exasol now parses `MINUS` as the set operation `EXCEPT`, so `SELECT a FROM x MINUS SELECT a FROM y` reads as `EXCEPT`.

The change is one line in `sqlglot/dialects/exasol.py`: `"MINUS": TokenType.EXCEPT` in the Exasol tokenizer's keywords. Oracle, Teradata, Snowflake, Redshift, and Hive already map `MINUS` the same way.

I also added `test_minus` to `tests/dialects/test_exasol.py`. It checks that Exasol and Oracle `MINUS` queries read as `EXCEPT`, and that Exasol writes `EXCEPT`.

The full suite passes with the project's pytest command: 1088 passed, 17847 subtests passed.

Oracle's generator still writes `EXCEPT` rather than `MINUS`. That was already true before this change and is outside this task, so I left it alone and did not assert it in the test.

I did not commit anything.
