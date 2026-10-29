# trajectory base-1

final message:
Exasol now parses `MINUS` as the `EXCEPT` set operator. The full test suite passes (1088 tests, 17844 subtests).

The change is one line in `sqlglot/dialects/exasol.py`: `"MINUS": TokenType.EXCEPT` in the Exasol tokenizer's `KEYWORDS`. That is the same mapping Oracle, Snowflake, Teradata, Hive and Redshift already use. I added a `test_minus` to `tests/dialects/test_exasol.py` that checks `SELECT 1 MINUS SELECT 2` round-trips as `SELECT 1 EXCEPT SELECT 2`.

I didn't run `make style` or commit anything; the changes are uncommitted in the worktree.

## events
[tool_use Bash] {"command": "cat sqlglot/dialects/exasol.py | head -80 && grep -rn '\"MINUS\"' sqlglot/ | head && grep -n 'MINUS' tests/dialects/test_exasol.py tests/dialects/test_oracle.py | head", "description": "Inspect Exasol dialect and MINUS handling"}
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
[assistant] Other dialects map `MINUS` to `TokenType.EXCEPT` in their tokenizer, so I'll follow that pattern here. Let me check for existing Exasol tests and then make the change.
[tool_use Bash] {"command": "grep -n 'EXCEPT\\|def test_' tests/dialects/test_exasol.py | head -30", "description": "Look at existing Exasol tests"}
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
859:    def test_regexp_like(self):
877:    def test_json(self):
890:    def test_group_by_all(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-164857-exasol-dialect-exasol-allows-bot/base-1/sqlglot/dialects/exasol.py", "old_string": "            \"LONG VARCHAR\": TokenType.TEXT,\n            \"REGEXP_LIKE\": TokenType.RLIKE,", "new_string": "            \"LONG VARCHAR\": TokenType.TEXT,\n            \"MINUS\": TokenType.EXCEPT,\n            \"REGEXP_LIKE\": TokenType.RLIKE,"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-164857-exasol-dialect-exasol-allows-bot/base-1/sqlglot/dialects/exasol.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-164857-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py", "offset": 34, "limit": 8}
[tool_result] 34	
35	    def test_exasol_keywords(self):
36	        keywords = ["CS", "ADD", "BOOLEAN", "CALL", "CONTROL"]
37	
38	        for keyword in keywords:
39	            with self.subTest(keyword=keyword):
40	                self.validate_identity(f"SELECT 1 AS {keyword}", f'SELECT 1 AS "{keyword}"')
41	
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-164857-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py", "old_string": "                self.validate_identity(f\"SELECT 1 AS {keyword}\", f'SELECT 1 AS \"{keyword}\"')\n", "new_string": "                self.validate_identity(f\"SELECT 1 AS {keyword}\", f'SELECT 1 AS \"{keyword}\"')\n\n    def test_minus(self):\n        self.validate_identity(\"SELECT 1 MINUS SELECT 2\", \"SELECT 1 EXCEPT SELECT 2\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-164857-exasol-dialect-exasol-allows-bot/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite"}
[tool_result] ........ [ 17%]
................................. [ 20%]
......................................................................................................................................................................... [ 35%]
............................................................................................................................................ [ 48%]
.............................................. [ 52%]
.................................. [ 56%]
......................
…[68 chars elided]…
3%]
........... [ 64%]
....................................... [ 68%]
............................................... [ 72%]
........................................................... [ 78%]
....................................................................................................................................... [ 90%]
............................... [ 93%]
......................................................................     [100%]
1088 passed, 17844 subtests passed in 49.77s
[assistant] Exasol now parses `MINUS` as the `EXCEPT` set operator. The full test suite passes (1088 tests, 17844 subtests).

The change is one line in `sqlglot/dialects/exasol.py`: `"MINUS": TokenType.EXCEPT` in the Exasol tokenizer's `KEYWORDS`. That is the same mapping Oracle, Snowflake, Teradata, Hive and Redshift already use. I added a `test_minus` to `tests/dialects/test_exasol.py` that checks `SELECT 1 MINUS SELECT 2` round-trips as `SELECT 1 EXCEPT SELECT 2`.

I didn't run `make style` or commit anything; the changes are uncommitted in the worktree.
