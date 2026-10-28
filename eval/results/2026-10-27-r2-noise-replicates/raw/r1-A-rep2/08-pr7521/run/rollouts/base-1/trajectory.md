# trajectory base-1

final message:
Exasol now parses `MINUS` as the `EXCEPT` set operation. `SELECT a FROM t MINUS SELECT a FROM u` round-trips to `SELECT a FROM t EXCEPT SELECT a FROM u`.

The change is one line in `sqlglot/dialects/exasol.py`: `"MINUS": TokenType.EXCEPT` in the Exasol tokenizer keywords. That is the same mapping Oracle, Snowflake, Redshift, Hive and Teradata already use. I also added one assertion to `test_exasol` in `tests/dialects/test_exasol.py`.

The full suite passes with the project's pytest command: 1087 passed, 17844 subtests passed. I haven't committed anything; the changes are in the working tree.

## events
[tool_use Bash] {"command": "cat sqlglot/dialects/exasol.py | head -80 && grep -n \"MINUS\\|EXCEPT\" sqlglot/dialects/exasol.py sqlglot/parser.py sqlglot/tokens.py | head -40 && grep -rn \"MINUS\" tests/dialects/test_exasol.py | head", "description": "Inspect Exasol dialect and MINUS/EXCEPT handling"}
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
…[1275 chars elided]…
          "REGEXP_LIKE": TokenType.RLIKE,
            "SEPARATOR": TokenType.SEPARATOR,
            "SYSTIMESTAMP": TokenType.SYSTIMESTAMP,
        }
        KEYWORDS.pop("DIV")

    Parser = ExasolParser

    Generator = ExasolGenerator
sqlglot/tokens.py:275:        "EXCEPT": TokenType.EXCEPT,
sqlglot/parser.py:926:        TokenType.EXCEPT,
sqlglot/parser.py:5564:        elif token_type == TokenType.EXCEPT:
sqlglot/parser.py:9427:                except_=self._parse_star_op("EXCEPT", "EXCLUDE"),
[tool_use Bash] {"command": "cat sqlglot/parsers/exasol.py | head -60; grep -rn \"MINUS\" sqlglot/*.py sqlglot/dialects/*.py sqlglot/parsers/*.py | head -30; grep -n \"MINUS\" tests/dialects/test_exasol.py | head", "description": "Look for MINUS handling across the codebase"}
[tool_result] from __future__ import annotations


from sqlglot import exp, parser
from sqlglot.dialects.dialect import (
    binary_from_function,
    build_date_delta,
    build_formatted_time,
    build_timetostr_or_tochar,
    build_trunc,
)
from sqlglot.helper import seq_get
from sqlglot.tokens import TokenType

DATE_UNITS = {"DAY", "WEEK", "MONTH", "YEAR", "HOUR", "MINUTE", "SECOND"}


# https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/zeroifnull.htm
def _build_zeroif
…[1867 chars elided]…
       "DATE_TRUNC": lambda args: exp.TimestampTrunc(this=seq_get(args, 1), unit=seq_get(args, 0)),
        "DIV": binary_from_function(exp.IntDiv),
sqlglot/dialects/snowflake.py:148:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/oracle.py:78:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/redshift.py:40:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/hive.py:106:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/teradata.py:63:            "MINUS": TokenType.EXCEPT,
[assistant] The pattern used by Oracle, Snowflake, Redshift, Hive and Teradata is a tokenizer keyword mapping `MINUS` to `TokenType.EXCEPT`. I'll follow that in the Exasol tokenizer.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-161028-exasol-dialect-exasol-allows-bot/base-1/sqlglot/dialects/exasol.py", "old_string": "            \"LONG VARCHAR\": TokenType.TEXT,\n            \"REGEXP_LIKE\": TokenType.RLIKE,", "new_string": "            \"LONG VARCHAR\": TokenType.TEXT,\n            \"MINUS\": TokenType.EXCEPT,\n            \"REGEXP_LIKE\": TokenType.RLIKE,"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-161028-exasol-dialect-exasol-allows-bot/base-1/sqlglot/dialects/exasol.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"def test_\\|validate_all\\|validate_identity\" tests/dialects/test_exasol.py | head -20 && grep -n \"EXCEPT\" tests/dialects/test_exasol.py | head", "description": "Review Exasol tests for set-operator coverage"}
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-161028-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py", "limit": 60}
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
13	        )
14	        self.validate_identity("SYSTIMESTAMP", "SYSTIMESTAMP()")
15	        self.validate_identity("SELECT SYSTIMESTAMP()")
16	        self.validat
…[1303 chars elided]…
    "SELECT TEST.*, 1 FROM TEST",
45	            read={
46	                "": "SELECT *, 1 FROM TEST",
47	            },
48	        )
49	        self.validate_identity(
50	            "SELECT t.*, 1 FROM t",
51	        )
52	        self.validate_identity(
53	            "SELECT t.* FROM t",
54	        )
55	        self.validate_identity(
56	            "SELECT * FROM t",
57	        )
58	        self.validate_identity(
59	            "WITH t AS (SELECT 1 AS x) SELECT t.*, 3 FROM t",
60	        )
[assistant] I'll add a test next to the existing Exasol tests, then run the suite with the project's checks command.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-161028-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py", "old_string": "        self.validate_identity(\"SELECT FROM_POSIX_TIME(1234567890)\")\n        self.validate_all(", "new_string": "        self.validate_identity(\"SELECT FROM_POSIX_TIME(1234567890)\")\n        self.validate_identity(\"SELECT 1 MINUS SELECT 2\", \"SELECT 1 EXCEPT SELECT 2\")\n        self.validate_all("}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-161028-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -15; <work>/env-sqlglot/bin/python -c \"import sqlglot;print(sqlglot.transpile('SELECT a FROM t MINUS SELECT a FROM u', read='exasol', write='exasol'))\"", "description": "Run Exasol tests and a MINUS transpile check"}
[tool_result] ................  [100%]
16 passed, 559 subtests passed in 0.54s
['SELECT a FROM t EXCEPT SELECT a FROM u']
[assistant] The Exasol tests pass. Running the full project suite now, since that's the project's check.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8", "description": "Run full test suite"}
[tool_result] ................................................... [ 52%]
.......................................................................................................................................................................... [ 68%]
............................................... [ 72%]
........................................................... [ 78%]
....................................................................................................................................... [ 90%]
............................... [ 93%]
.....................................................................      [100%]
1087 passed, 17844 subtests passed in 52.77s
[assistant] Exasol now parses `MINUS` as the `EXCEPT` set operation. `SELECT a FROM t MINUS SELECT a FROM u` round-trips to `SELECT a FROM t EXCEPT SELECT a FROM u`.

The change is one line in `sqlglot/dialects/exasol.py`: `"MINUS": TokenType.EXCEPT` in the Exasol tokenizer keywords. That is the same mapping Oracle, Snowflake, Redshift, Hive and Teradata already use. I also added one assertion to `test_exasol` in `tests/dialects/test_exasol.py`.

The full suite passes with the project's pytest command: 1087 passed, 17844 subtests passed. I haven't committed anything; the changes are in the working tree.
