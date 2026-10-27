# trajectory base-2

final message:
Exasol now accepts `MINUS` as an alias for `EXCEPT`. `SELECT 1 MINUS SELECT 2` parses to the same `exp.Except` node as `EXCEPT`, and it generates `SELECT 1 EXCEPT SELECT 2`.

The change is one keyword mapping in `sqlglot/dialects/exasol.py`: `"MINUS": TokenType.EXCEPT` in the Exasol tokenizer. I added `test_minus` to `tests/dialects/test_exasol.py`. It checks that the parsed `MINUS` tree equals the `EXCEPT` tree, that the node is `exp.Except`, and that both round-trip to `EXCEPT`.

Verification:
- `tests/dialects/test_exasol.py`: 17 passed.
- Full suite via `run_suite.py`, taken after the last edit: `SUMMARY: 1088 passed, 17844 subtests passed in 81.43s`, `EXIT: 0`.
- `ruff check` and `ruff format --check` pass on both changed files.

Nothing is committed. The base SQL parser is unchanged. `MINUS` as an identifier in Exasol is no longer tokenized as a plain name, but it was already a reserved set operator in the other dialects that map it this way.

## events
[tool_use Bash] {"command": "grep -n \"MINUS\\|EXCEPT\" sqlglot/dialects/exasol.py sqlglot/parsers/exasol.py sqlglot/generators/exasol.py sqlglot/parser.py | head -50; ls .lithify/harness/scripts/ 2>/dev/null; cat memory.md 2>/dev/null | head -20", "description": "Find MINUS/EXCEPT handling in Exasol and base parser"}
[tool_result] sqlglot/parser.py:926:        TokenType.EXCEPT,
sqlglot/parser.py:5564:        elif token_type == TokenType.EXCEPT:
sqlglot/parser.py:9427:                except_=self._parse_star_op("EXCEPT", "EXCLUDE"),
run_suite.py
[tool_use Bash] {"command": "grep -rn \"MINUS\" sqlglot/tokens.py sqlglot/parser.py sqlglot/dialects/*.py | head -30; sed -n 5550,5580p sqlglot/parser.py; ls sqlglot/parsers/ | grep -i exa; ls sqlglot/generators | grep -i exa; ls tests/dialects | grep -i exa", "description": "Inspect MINUS tokenization and set-op parsing"}
[tool_result] sqlglot/dialects/hive.py:106:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/oracle.py:78:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/redshift.py:40:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/snowflake.py:148:            "MINUS": TokenType.EXCEPT,
sqlglot/dialects/teradata.py:63:            "MINUS": TokenType.EXCEPT,
        start = self._index
        _, side_token, kind_token = self._parse_join_parts()

        side = side_token.text if side_token else None
   
…[399 chars elided]…
e:
            operation = exp.Intersect

        comments = self._prev.comments

        if self._match(TokenType.DISTINCT):
            distinct: bool | None = True
        elif self._match(TokenType.ALL):
            distinct = False
        else:
            distinct = self.dialect.SET_OP_DISTINCT_BY_DEFAULT[operation]
            if distinct is None:
                self.raise_error(f"Expected DISTINCT or ALL for {operation.__name__}")

        by_name = (
exasol.py
exasol.py
test_exasol.py
[tool_use Bash] {"command": "cat sqlglot/dialects/exasol.py; sed -n 1,40p sqlglot/parsers/exasol.py; sed -n 95,115p sqlglot/dialects/hive.py; grep -n \"MINUS\" -B3 -A3 tests/dialects/test_oracle.py | head -30", "description": "Read Exasol dialect and a reference dialect's MINUS mapping"}
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
…[3128 chars elided]…

            "ADD FILES": TokenType.COMMAND,
            "ADD JAR": TokenType.COMMAND,
            "ADD JARS": TokenType.COMMAND,
            "MINUS": TokenType.EXCEPT,
            "MSCK REPAIR": TokenType.COMMAND,
            "REFRESH": TokenType.REFRESH,
            "TIMESTAMP AS OF": TokenType.TIMESTAMP_SNAPSHOT,
            "VERSION AS OF": TokenType.VERSION_SNAPSHOT,
            "SERDEPROPERTIES": TokenType.SERDE_PROPERTIES,
        }

        NUMERIC_LITERALS = {
            "L": "BIGINT",
[tool_use Bash] {"command": "grep -n \"EXCEPT\\|UNION\\|INTERSECT\\|def test_\" tests/dialects/test_exasol.py | head -40; sed -n 1,12p tests/dialects/test_exasol.py", "description": "Look at existing Exasol test structure"}
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
from sqlglot import exp, transpile, UnsupportedError, ErrorLevel
from tests.dialects.test_dialect import Validator


class TestExasol(Validator):
    dialect = "exasol"
    maxDiff = None

    def test_exasol(self):
        self.validate_identity(
            "SELECT 1 AS [x]",
            'SELECT 1 AS "x"',
[assistant] Exasol's tokenizer has no `MINUS` mapping yet, so I'll add one alongside `SEPARATOR` and add a test that checks the AST node, not just the round-trip.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-184539-exasol-dialect-exasol-allows-bot/base-2/sqlglot/dialects/exasol.py", "old_string": "            \"LONG VARCHAR\": TokenType.TEXT,\n            \"REGEXP_LIKE\": TokenType.RLIKE,", "new_string": "            \"LONG VARCHAR\": TokenType.TEXT,\n            \"MINUS\": TokenType.EXCEPT,\n            \"REGEXP_LIKE\": TokenType.RLIKE,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-184539-exasol-dialect-exasol-allows-bot/base-2/sqlglot/dialects/exasol.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-184539-exasol-dialect-exasol-allows-bot/base-2/tests/dialects/test_exasol.py", "offset": 888, "limit": 30}
[tool_result] 888	        )
889	
890	    def test_group_by_all(self):
891	        self.validate_all(
892	            "SELECT id, city, COUNT(*) FROM dealer GROUP BY ALL",
893	            write={
894	                "exasol": "SELECT id, city, COUNT(*) FROM dealer GROUP BY 1, 2",
895	                "databricks": "SELECT id, city, COUNT(*) FROM dealer GROUP BY ALL",
896	            },
897	        )
898	        self.validate_all(
899	            "SELECT car_model, COUNT(DISTINCT city) FROM dealer GROUP BY ALL",
…[348 chars elided]…
L",
907	            write={
908	                "exasol": "SELECT car_model, city FROM dealer GROUP BY 1, 2",
909	                "databricks": "SELECT car_model, city FROM dealer GROUP BY ALL",
910	            },
911	        )
912	        self.validate_all(
913	            "SELECT COUNT(*) FROM dealer GROUP BY ALL",
914	            write={
915	                "exasol": "SELECT COUNT(*) FROM dealer",
916	                "databricks": "SELECT COUNT(*) FROM dealer GROUP BY ALL",
917	            },
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-184539-exasol-dialect-exasol-allows-bot/base-2/tests/dialects/test_exasol.py", "old_string": "    def test_group_by_all(self):\n        self.validate_all(", "new_string": "    def test_minus(self):\n        ast = parse_one(\"SELECT 1 MINUS SELECT 2\", read=\"exasol\")\n        self.assertIsInstance(ast, exp.Except)\n        self.assertFalse(ast.args[\"distinct\"])\n        self.validate_identity(\"SELECT 1 MINUS SELECT 2\", \"SELECT 1 EXCEPT SELECT 2\")\n        self.validate_identity(\"SELECT 1 EXCEPT SELECT 2\")\n\n    def test_group_by_all(self):\n        self.validate_all("}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-184539-exasol-dialect-exasol-allows-bot/base-2/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-184539-exasol-dialect-exasol-allows-bot/base-2/tests/dialects/test_exasol.py", "old_string": "from sqlglot import exp, transpile, UnsupportedError, ErrorLevel", "new_string": "from sqlglot import exp, parse_one, transpile, UnsupportedError, ErrorLevel"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-184539-exasol-dialect-exasol-allows-bot/base-2/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nfrom sqlglot import parse_one, exp\na=parse_one('SELECT 1 MINUS SELECT 2', read='exasol'); print(type(a).__name__, a.args.get('distinct'))\nprint(parse_one('SELECT 1 MINUS ALL SELECT 2', read='exasol').args.get('distinct'))\nprint(parse_one('SELECT 1 EXCEPT SELECT 2', read='exasol').args.get('distinct'))\nprint(parse_one('SELECT 1 MINUS SELECT 2', read='exasol').sql('exasol'))\n\" ; grep -n \"SET_OP_DISTINCT_BY_DEFAULT\" -A3 sqlglot/dialects/dialect.py | head", "description": "Check AST node and distinct flag for MINUS in Exasol"}
[tool_result] Except True
False
True
SELECT 1 EXCEPT SELECT 2
672:    SET_OP_DISTINCT_BY_DEFAULT: dict[Type[exp.Expr], bool | None] = {
673-        exp.Except: True,
674-        exp.Intersect: True,
675-        exp.Union: True,
[assistant] The `MINUS` node is `exp.Except` with the same `distinct=True` default as `EXCEPT`. I'll make the test assert that equivalence directly.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-184539-exasol-dialect-exasol-allows-bot/base-2/tests/dialects/test_exasol.py", "old_string": "        ast = parse_one(\"SELECT 1 MINUS SELECT 2\", read=\"exasol\")\n        self.assertIsInstance(ast, exp.Except)\n        self.assertFalse(ast.args[\"distinct\"])\n        self.validate_identity", "new_string": "        self.assertEqual(\n            parse_one(\"SELECT 1 MINUS SELECT 2\", read=\"exasol\"),\n            parse_one(\"SELECT 1 EXCEPT SELECT 2\", read=\"exasol\"),\n        )\n        self.assertIsInstance(parse_one(\"SELECT 1 MINUS SELECT 2\", read=\"exasol\"), exp.Except)\n        self.validate_identity"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-184539-exasol-dialect-exasol-allows-bot/base-2/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -5", "description": "Run Exasol dialect tests"}
[tool_result] ................. [100%]
17 passed, 559 subtests passed in 0.22s
[assistant] Dialect tests pass. Now the full suite via the harness script, which the project requires for a completed run.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py 2>&1 | tail -30", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] WARNING: 2 other pytest process(es) running; expect slower runs:
    651       00:02 <work>/env-sqlglot/b
  34207 02-23:14:55 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-01dd5c7676.log
ELAPSED: 82s
SUMMARY: 1088 passed, 17844 subtests passed in 81.43s (0:01:21)
EXIT: 0
[tool_use Bash] {"command": "(ruff check sqlglot/dialects/exasol.py tests/dialects/test_exasol.py && ruff format --check sqlglot/dialects/exasol.py tests/dialects/test_exasol.py) 2>&1 | tail -5; git status --short", "description": "Lint and format check changed files"}
[tool_result] All checks passed!
2 files already formatted
 M sqlglot/dialects/exasol.py
 M tests/dialects/test_exasol.py
[assistant] Exasol now accepts `MINUS` as an alias for `EXCEPT`. `SELECT 1 MINUS SELECT 2` parses to the same `exp.Except` node as `EXCEPT`, and it generates `SELECT 1 EXCEPT SELECT 2`.

The change is one keyword mapping in `sqlglot/dialects/exasol.py`: `"MINUS": TokenType.EXCEPT` in the Exasol tokenizer. I added `test_minus` to `tests/dialects/test_exasol.py`. It checks that the parsed `MINUS` tree equals the `EXCEPT` tree, that the node is `exp.Except`, and that both round-trip to `EXCEPT`.

Verification:
- `tests/dialects/test_exasol.py`: 17 passed.
- Full suite via `run_suite.py`, taken after the last edit: `SUMMARY: 1088 passed, 17844 subtests passed in 81.43s`, `EXIT: 0`.
- `ruff check` and `ruff format --check` pass on both changed files.

Nothing is committed. The base SQL parser is unchanged. `MINUS` as an identifier in Exasol is no longer tokenized as a plain name, but it was already a reserved set operator in the other dialects that map it this way.
