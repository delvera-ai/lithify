# trajectory base-2

final message:
Oracle `MERGE` now accepts the optional `WHERE` on both the `UPDATE` and `INSERT` branches, and it round-trips. On other dialects the clause is dropped with an unsupported warning. The full suite passes (1081 tests) and `ruff check` and `ruff format` are clean. I did not commit.

Changes:
- **`sqlglot/parser.py`** (`_parse_when_matched`): after the `INSERT` and `UPDATE` branches, parse an optional `WHERE` into the branch's existing `where` arg. `Insert` and `Update` already declared that arg.
- **`sqlglot/generator.py`**: `when_sql` emits the `WHERE` when the generator flag `MERGE_WHEN_WHERE_SUPPORTED` is set. Otherwise it calls `self.unsupported(...)` and omits the clause. The flag defaults to `False`, which is the behaviour for every dialect except Oracle.
- **`sqlglot/generators/oracle.py`**: sets `MERGE_WHEN_WHERE_SUPPORTED = True`.
- **`tests/dialects/test_oracle.py`**: new `test_merge_when_where`. It checks the Oracle round-trip, and it checks that DuckDB output drops both clauses and logs the warning.

Decision for you: I put the flag in the base generator, so any dialect that later gains this syntax needs its own override. Say if you would rather have the parser accept the clause only for Oracle.

## events
[tool_use Bash] {"command": "git status --short | head && grep -n \"_parse_merge\\|WHEN_MATCHED\\|MergeTreeCondition\\|whens\\|def merge_sql\" sqlglot/parser.py sqlglot/generator.py sqlglot/dialects/oracle.py | head -60 && grep -n \"class When\\|class Merge\" -A 12 sqlglot/expressions.py | head -60", "description": "Check status and locate MERGE handling code"}
[tool_result] sqlglot/generator.py:4466:    def whens_sql(self, expression: exp.Whens) -> str:
sqlglot/generator.py:4469:    def merge_sql(self, expression: exp.Merge) -> str:
sqlglot/generator.py:4480:        whens = self.sql(expression, "whens")
sqlglot/generator.py:4491:            whens = f"{whens}{returning}"
sqlglot/generator.py:4497:            f"MERGE INTO {this}{table_alias}{sep}{using}{sep}{on}{sep}{whens}",
sqlglot/parser.py:1080:        TokenType.MERGE: lambda self: self._parse_merge(),
sqlglot/pa
…[34 chars elided]…
TIO": lambda self, **kwargs: self._parse_mergeblockratio(**kwargs),
sqlglot/parser.py:3037:    def _parse_mergeblockratio(
sqlglot/parser.py:8884:    def _parse_merge(self) -> exp.Merge:
sqlglot/parser.py:8900:                whens=self._parse_when_matched(),
sqlglot/parser.py:8906:        whens = []
sqlglot/parser.py:8949:            whens.append(
sqlglot/parser.py:8954:        return self.expression(exp.Whens(expressions=whens))
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "sed -n 8884,8960p sqlglot/parser.py && sed -n 4460,4500p sqlglot/generator.py && grep -rn \"def merge_sql\\|def when_sql\\|whens\" sqlglot/generator.py sqlglot/dialects/*.py | head -30 && grep -n \"class When(\" -A 10 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null | head -30", "description": "Read MERGE parser and generator code"}
[tool_result]     def _parse_merge(self) -> exp.Merge:
        self._match(TokenType.INTO)
        target = self._parse_table()

        if target and self._match(TokenType.ALIAS, advance=False):
            target.set("alias", self._parse_table_alias())

        self._match(TokenType.USING)
        using = self._parse_table()

        return self.expression(
            exp.Merge(
                this=target,
                using=using,
                on=self._match(TokenType.ON) and self._parse_disjunctio
…[4504 chars elided]…
essions:
sqlglot/expressions/dml.py:517:class When(Expression):
sqlglot/expressions/dml.py-518-    arg_types = {"matched": True, "source": False, "condition": False, "then": True}
sqlglot/expressions/dml.py-519-
sqlglot/expressions/dml.py-520-
sqlglot/expressions/dml.py-521-class Whens(Expression):
sqlglot/expressions/dml.py-522-    """Wraps around one or more WHEN [NOT] MATCHED [...] clauses."""
sqlglot/expressions/dml.py-523-
sqlglot/expressions/dml.py-524-    arg_types = {"expressions": True}
[tool_use Bash] {"command": "sed -n 4436,4466p sqlglot/generator.py && sed -n 2030,2060p sqlglot/dialects/dialect.py && grep -n \"unsupported_args\\|def unsupported(\" sqlglot/generator.py | head -5 && grep -n \"MERGE\\|merge\" sqlglot/dialects/oracle.py | head; grep -rn \"Merge\\|merge\" tests/dialects/test_oracle.py | head -20; grep -n \"WHEN NOT MATCHED\\|WHEN MATCHED\" tests/dialects/*.py | head -30", "description": "Inspect when_sql, unsupported helpers, Oracle merge tests"}
[tool_result]         this = self.sql(expression, "this")
        expressions = self.expressions(expression, flat=True)
        return f"{this}({expressions})"

    def kwarg_sql(self, expression: exp.Kwarg) -> str:
        return self.binary(expression, "=>")

    def when_sql(self, expression: exp.When) -> str:
        matched = "MATCHED" if expression.args["matched"] else "NOT MATCHED"
        source = " BY SOURCE" if self.MATCHED_BY_SOURCE and expression.args.get("source") else ""
        condition = self
…[7819 chars elided]…
sts/dialects/test_bigquery.py:2480:                "bigquery": "MERGE INTO dataset.Inventory AS T USING dataset.NewArrivals AS S ON FALSE WHEN NOT MATCHED AND product LIKE '%a%' THEN DELETE WHEN NOT MATCHED BY SOURCE AND product LIKE '%b%' THEN DELETE",
tests/dialects/test_bigquery.py:2481:                "snowflake": "MERGE INTO dataset.Inventory AS T USING dataset.NewArrivals AS S ON FALSE WHEN NOT MATCHED AND product LIKE '%a%' THEN DELETE WHEN NOT MATCHED AND product LIKE '%b%' THEN DELETE",
[tool_use Bash] {"command": "grep -n \"class Insert(\\|class Update(\" -A 22 sqlglot/expressions/dml.py | head -60; grep -n \"MATCHED_BY_SOURCE\" sqlglot/generator.py sqlglot/dialects/*.py; grep -n \"def _parse_where\\b\" -A3 sqlglot/parser.py; grep -n \"class Generator\" -A3 sqlglot/dialects/oracle.py; sed -n 880,900p tests/dialects/test_oracle.py", "description": "Inspect Insert/Update classes and generator flags"}
[tool_result] 194:class Insert(Expression, DDL, DML):
195-    arg_types = {
196-        "hint": False,
197-        "with_": False,
198-        "is_function": False,
199-        "this": False,
200-        "expression": False,
201-        "conflict": False,
202-        "returning": False,
203-        "overwrite": False,
204-        "exists": False,
205-        "alternative": False,
206-        "where": False,
207-        "ignore": False,
208-        "by_name": False,
209-        "stored": False,
210-        "pa
…[1802 chars elided]…
self.assertEqual(
            merge_stmt.sql("oracle"),
            "MERGE INTO my_table USING (SELECT * FROM something) source_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1 WHEN NOT MATCHED THEN INSERT (my_table.id, my_table.col1) VALUES (source_table.id, source_table.col1)",
        )

    def test_pseudocolumns(self):
        ast = self.validate_identity(
            "WITH t AS (SELECT 1 AS COL) SELECT col, ROWID FROM t WHERE ROWNUM = 1"
[tool_use Bash] {"command": "grep -n \"class \\|SUPPORTS_\" sqlglot/dialects/oracle.py | head -40; grep -n \"^    SUPPORTS_[A-Z_]* = \" sqlglot/generator.py | head -20; grep -n \"def insert_sql\" -A 12 sqlglot/generator.py | grep -n where; grep -n \"self.unsupported(\" sqlglot/generator.py | head -3", "description": "Check Oracle generator and flag conventions"}
[tool_result] 15:class Oracle(Dialect):
59:    class Tokenizer(tokens.Tokenizer):
407:    SUPPORTS_TABLE_COPY = True
437:    SUPPORTS_SINGLE_ARG_CONCAT = True
443:    SUPPORTS_TABLE_ALIAS_COLUMNS = True
455:    SUPPORTS_SELECT_INTO = False
458:    SUPPORTS_UNLOGGED_TABLES = False
461:    SUPPORTS_CREATE_TABLE_LIKE = True
486:    SUPPORTS_TO_NUMBER = True
489:    SUPPORTS_WINDOW_EXCLUDE = False
509:    SUPPORTS_UESCAPE = True
530:    SUPPORTS_EXPLODING_PROJECTIONS = True
536:    SUPPORTS_CONVERT_TIMEZONE = Fal
…[15 chars elided]…
ORTS_MEDIAN = True
542:    SUPPORTS_UNIX_SECONDS = False
568:    SUPPORTS_DECODE_CASE = True
571:    SUPPORTS_BETWEEN_FLAGS = False
574:    SUPPORTS_LIKE_QUANTIFIERS = True
596:    SUPPORTS_DROP_ALTER_ICEBERG_PROPERTY = True
1125:            self.unsupported("Outer join syntax using the (+) operator is not supported.")
1524:            self.unsupported("Named columns are not supported in table alias.")
1558:                self.unsupported("Unsupported transpilation from BINARY/BLOB hex string")
[tool_use Bash] {"command": "sed -n 400,412p sqlglot/dialects/oracle.py; grep -n \"SUPPORTS_TABLE_COPY\\|SUPPORTS_UESCAPE\" sqlglot/generator.py sqlglot/dialects/oracle.py; grep -n \"    SUPPORTS_UESCAPE\" -B3 -A2 sqlglot/generator.py; grep -n \"class Generator\" sqlglot/dialects/oracle.py; sed -n 1,30p sqlglot/dialects/oracle.py | grep -n import", "description": "Inspect Oracle generator flag placement"}
[tool_result] sqlglot/generator.py:407:    SUPPORTS_TABLE_COPY = True
sqlglot/generator.py:509:    SUPPORTS_UESCAPE = True
sqlglot/generator.py:1463:        keyword = "COPY" if expression.args.get("copy") and self.SUPPORTS_TABLE_COPY else "CLONE"
sqlglot/generator.py:1601:            escape_sql = f" UESCAPE {self.sql(escape)}" if self.SUPPORTS_UESCAPE else ""
sqlglot/generator.py:1606:        if not self.dialect.UNICODE_START or (escape and not self.SUPPORTS_UESCAPE):
506-    TRY_SUPPORTED = True
507-
508-    # Whether the UESCAPE syntax in unicode strings is supported
509:    SUPPORTS_UESCAPE = True
510-
511-    # Function used to replace escaped unicode codes in unicode strings
1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, tokens
6:from sqlglot.dialects.dialect import (
10:from sqlglot.generators.oracle import OracleGenerator
11:from sqlglot.parsers.oracle import OracleParser
12:from sqlglot.tokens import TokenType
[tool_use Bash] {"command": "grep -n \"SUPPORTS_TABLE_COPY\\|SUPPORTS_UESCAPE\\|MATCHED_BY_SOURCE\\|^    [A-Z_]* = \" sqlglot/generators/oracle.py | head -30; sed -n 500,512p sqlglot/generator.py; grep -n \"MATCHED_BY_SOURCE\" -B2 -A1 sqlglot/generator.py | head; grep -n \"\\(Merge\\|merge\\)\" sqlglot/parsers/oracle.py sqlglot/generators/oracle.py | head", "description": "Check Oracle generator class and flags"}
[tool_result] 25:    TRY_SUPPORTED = False
26:    SUPPORTS_UESCAPE = False
27:    LOCKING_READS_SUPPORTED = True
28:    JOIN_HINTS = False
29:    TABLE_HINTS = False
30:    DATA_TYPE_SPECIFIERS_ALLOWED = True
31:    ALTER_TABLE_INCLUDE_COLUMN_KEYWORD = False
32:    LIMIT_FETCH = "FETCH"
33:    TABLESAMPLE_KEYWORDS = "SAMPLE"
34:    LAST_DAY_SUPPORTS_DATE_PART = False
35:    SUPPORTS_SELECT_INTO = True
36:    TZ_TO_WITH_TIME_ZONE = True
37:    SUPPORTS_WINDOW_EXCLUDE = True
38:    QUERY_HINT_SEP = " "
39:    S
…[525 chars elided]…
 escaped unicode codes in unicode strings
    UNICODE_SUBSTITUTE: t.ClassVar[t.Any] = None
319-
320-    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed
321:    MATCHED_BY_SOURCE = True
322-
--
4443-    def when_sql(self, expression: exp.When) -> str:
4444-        matched = "MATCHED" if expression.args["matched"] else "NOT MATCHED"
4445:        source = " BY SOURCE" if self.MATCHED_BY_SOURCE and expression.args.get("source") else ""
4446-        condition = self.sql(expression, "condition")
[tool_use Bash] {"command": "sed -n 316,323p sqlglot/generator.py && sed -n 22,27p sqlglot/generators/oracle.py && grep -rn \"assertLogs\\|unsupported_level\" tests/dialects/test_oracle.py | head -5; grep -rn \"unsupported\" tests/dialects/test_dialect.py | head -5", "description": "View flag context and existing unsupported test patterns"}
[tool_result]     # Whether create function uses an AS before the RETURN
    CREATE_FUNCTION_RETURN_AS = True

    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed
    MATCHED_BY_SOURCE = True

    # Whether the INTERVAL expression works only with values like '1 day'

class OracleGenerator(generator.Generator):
    SELECT_KINDS: tuple[str, ...] = ()
    TRY_SUPPORTED = False
    SUPPORTS_UESCAPE = False
    LOCKING_READS_SUPPORTED = True
tests/dialects/test_dialect.py:59:                assert f"'{sql[:100]}' contains unsupported syntax" in cm.output[0]
tests/dialects/test_dialect.py:88:                        unsupported_level=ErrorLevel.IGNORE,
tests/dialects/test_dialect.py:99:                        expression.sql(write_dialect, unsupported_level=ErrorLevel.RAISE)
tests/dialects/test_dialect.py:104:                            unsupported_level=ErrorLevel.IGNORE,
tests/dialects/test_dialect.py:3439:    def test_unsupported_null_ordering(self):
[assistant] Now I'll make the edits: a generator flag, the parser change, the `when_sql` change, and the Oracle override.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-2/sqlglot/generator.py", "old_string": "    MATCHED_BY_SOURCE = True\n", "new_string": "    MATCHED_BY_SOURCE = True\n\n    # Whether MERGE ... WHEN MATCHED THEN UPDATE / WHEN NOT MATCHED THEN INSERT can have a WHERE clause\n    MERGE_WHEN_WHERE_SUPPORTED = False\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-2/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-2/sqlglot/generator.py", "old_string": "        else:\n            then = self.sql(then_expression)\n        return f\"WHEN {matched}{source}{condition} THEN {then}\"", "new_string": "        else:\n            then = self.sql(then_expression)\n\n        i
…[30 chars elided]…
(exp.Insert, exp.Update)) and then_expression.args.get(\"where\"):\n            if self.MERGE_WHEN_WHERE_SUPPORTED:\n                then = f\"{then} {self.sql(then_expression, 'where')}\"\n            else:\n                self.unsupported(\"WHERE clause in MERGE WHEN MATCHED/NOT MATCHED THEN UPDATE/INSERT is not supported\")\n\n        return f\"WHEN {matched}{source}{condition} THEN {then}\""}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-2/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-2/sqlglot/generators/oracle.py", "old_string": "    SUPPORTS_UESCAPE = False\n    LOCKING_READS_SUPPORTED = True", "new_string": "    SUPPORTS_UESCAPE = False\n    MERGE_WHEN_WHERE_SUPPORTED = True\n    LOCKING_READS_SUPPORTED = True"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-2/sqlglot/generators/oracle.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-2/sqlglot/parser.py", "old_string": "                            expression=self._match_text_seq(\"VALUES\") and self._parse_value(),\n                        )\n                    )\n            elif self._match(TokenType.UPDATE):\n                expres
…[823 chars elided]…
xpression(exp.Update(expressions=expressions))\n                else:\n                    then = self.expression(\n                        exp.Update(\n                            expressions=self._match(TokenType.SET)\n                            and self._parse_csv(self._parse_equality)\n                        )\n                    )\n                then.set(\"where\", self._parse_where())"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-2/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "sed -n 1,12p tests/dialects/test_oracle.py && sed -n 50,60p tests/dialects/test_dialect.py", "description": "Check test imports and logging assertion pattern"}
[tool_result] from sqlglot import exp, UnsupportedError, ParseError, parse, parse_one
from tests.dialects.test_dialect import Validator
from sqlglot.optimizer.qualify import qualify


class TestOracle(Validator):
    dialect = "oracle"

    def test_oracle(self):
        self.validate_identity("1 /* /* */", "1 /* / * */")
        self.validate_all(
            "SELECT CONNECT_BY_ROOT x y",

        return duckdb_sql

    def validate_identity(
        self, sql, write_sql=None, pretty=False, check_command_warning=False, identify=False
    ):
        if check_command_warning:
            with self.assertLogs(parser_logger) as cm:
                expression = self.parse_one(sql)
                assert f"'{sql[:100]}' contains unsupported syntax" in cm.output[0]
        else:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-2/tests/dialects/test_oracle.py", "old_string": "    def test_pseudocolumns(self):", "new_string": "    def test_merge_when_where(self):\n        self.validate_identity(\n            \"MERGE INTO target USING source ON target.id = source.id \"\n           
…[660 chars elided]…
          \"MERGE INTO target USING source ON target.id = source.id \"\n                \"WHEN MATCHED THEN UPDATE SET target.val = source.val \"\n                \"WHEN NOT MATCHED THEN INSERT (id, val) VALUES (source.id, source.val)\",\n            )\n        self.assertEqual(len(cm.output), 2)\n        self.assertIn(\"WHERE clause in MERGE\", cm.output[0])\n\n    def test_pseudocolumns(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-2/tests/dialects/test_oracle.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"^logger\\|getLogger\" sqlglot/generator.py sqlglot/*.py | head -5; grep -n \"generator_logger\\|logger\" tests/dialects/test_dialect.py | head -3", "description": "Find generator logger name"}
[tool_result] sqlglot/__init__.py:78:logger = logging.getLogger("sqlglot")
sqlglot/generator.py:24:logger = logging.getLogger("sqlglot")
sqlglot/generator.py:24:logger = logging.getLogger("sqlglot")
sqlglot/helper.py:38:logger = logging.getLogger("sqlglot")
sqlglot/lineage.py:19:logger = logging.getLogger("sqlglot")
17:from sqlglot.generator import logger as generator_logger
18:from sqlglot.parser import logger as parser_logger
57:            with self.assertLogs(parser_logger) as cm:
[tool_use Bash] {"command": "sed -i 's/^from sqlglot.optimizer.qualify import qualify$/from sqlglot.generator import logger as generator_logger\\nfrom sqlglot.optimizer.qualify import qualify/' tests/dialects/test_oracle.py && head -5 tests/dialects/test_oracle.py && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py tests/dialects/test_dialect.py 2>&1 | tail -30", "description": "Add logger import and run Oracle and dialect tests"}
[tool_result ERROR] Exit code 1
sed: 2: "tests/dialects/test_ora ...": undefined label 'ests/dialects/test_oracle.py'
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-2/tests/dialects/test_oracle.py", "old_string": "from sqlglot import exp, UnsupportedError, ParseError, parse, parse_one\nfrom tests.dialects.test_dialect import Validator\nfrom sqlglot.optimizer.qualify import qualify", "new_string": "from sqlglot import exp, UnsupportedError, ParseError, parse, parse_one\nfrom tests.dialects.test_dialect import Validator\nfrom sqlglot.generator import logger as generator_logger\nfrom sqlglot.optimizer.qualify import qualify"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-2/tests/dialects/test_oracle.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py tests/dialects/test_dialect.py 2>&1 | tail -30", "description": "Run Oracle and dialect test files"}
[tool_result] .............F............................................................................................ [ 86%]
................                    [100%]
=================================== FAILURES ===================================
_______________________ TestOracle.test_merge_when_where _______________________

self = <tests.dialects.test_oracle.TestOracle testMethod=test_merge_when_where>

    def test_merge_when_where(self):
>       self.validate_identity(
            "MERGE INTO target
…[401 chars elided]…
alidate_identity
    self.assertEqual(
E   AssertionError: 'MERG[100 chars].val WHERE source.val > 0 WHEN NOT MATCHED THE[65 chars] > 0' != 'MERG[100 chars].val  WHERE source.val > 0 WHEN NOT MATCHED TH[67 chars] > 0'
E   Diff is 885 characters long. Set self.maxDiff to None to see it.
=========================== short test summary info ============================
FAILED tests/dialects/test_oracle.py::TestOracle::test_merge_when_where - Ass...
1 failed, 121 passed, 3027 subtests passed in 1.02s
[assistant] The `where_sql` helper already adds its own leading space, so my extra space doubled it. Fixing that:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-2/sqlglot/generator.py", "old_string": "                then = f\"{then} {self.sql(then_expression, 'where')}\"", "new_string": "                then = f\"{then}{self.sql(then_expression, 'where')}\""}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-2/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py tests/dialects/test_dialect.py 2>&1 | tail -15; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; $PY -m ruff check sqlglot tests 2>&1 | tail -3; $PY -m ruff format --check sqlglot tests 2>&1 | tail -3", "description": "Fix spacing, run full test suite and lint"}
[tool_result] .......................................................................................................... [ 86%]
................                    [100%]
122 passed, 3027 subtests passed in 1.32s
............................................................................................................ [ 64%]
........................................................................................................................................................................................................................................................................................................................................ [ 94%]
....................... [ 96%]
....................................                      [100%]
1081 passed, 17834 subtests passed in 85.80s (0:01:25)
All checks passed!
Would reformat: sqlglot/generator.py
1 file would be reformatted, 231 files already formatted
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format sqlglot/generator.py && git diff --stat && git diff sqlglot/generator.py | head -60", "description": "Format generator and show resulting diff"}
[tool_result] 1 file reformatted
 sqlglot/generator.py          | 14 ++++++++++++++
 sqlglot/generators/oracle.py  |  1 +
 sqlglot/parser.py             |  2 ++
 tests/dialects/test_oracle.py | 23 +++++++++++++++++++++++
 4 files changed, 40 insertions(+)
diff --git a/sqlglot/generator.py b/sqlglot/generator.py
index d9f08c480..fe3fab24f 100644
--- a/sqlglot/generator.py
+++ b/sqlglot/generator.py
@@ -320,6 +320,9 @@ class Generator:
     # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed
     MATCHED_BY_S
…[534 chars elided]…
E_WHEN_WHERE_SUPPORTED:
+                then = f"{then}{self.sql(then_expression, 'where')}"
+            else:
+                self.unsupported(
+                    "WHERE clause in MERGE WHEN MATCHED/NOT MATCHED THEN UPDATE/INSERT is not supported"
+                )
+
         return f"WHEN {matched}{source}{condition} THEN {then}"
 
     def whens_sql(self, expression: exp.Whens) -> str:
[This command modified 1 file you've previously read: sqlglot/generator.py. Call Read before editing.]
[assistant] The formatter wrapped the condition awkwardly. I'll restructure it so it reads more cleanly:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-2/sqlglot/generator.py", "old_string": "        if isinstance(then_expression, (exp.Insert, exp.Update)) and then_expression.args.get(\n            \"where\"\n        ):\n            if self.MERGE_WHEN_WHERE_SUPPORTED:\n                then = f\"{then}{sel
…[227 chars elided]…
return", "new_string": "        if isinstance(then_expression, (exp.Insert, exp.Update)):\n            where = self.sql(then_expression, \"where\")\n            if where and self.MERGE_WHEN_WHERE_SUPPORTED:\n                then = f\"{then}{where}\"\n            elif where:\n                self.unsupported(\"WHERE clause in MERGE WHEN ... THEN UPDATE/INSERT is not supported\")\n\n        return"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-2/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format sqlglot tests && $PY -m ruff check sqlglot tests | tail -1 && $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2 && git status --short", "description": "Reformat, lint, and rerun the full test suite"}
[tool_result] 1 file reformatted, 232 files left unchanged
All checks passed!
....................................                      [100%]
1081 passed, 17834 subtests passed in 66.02s (0:01:06)
 M sqlglot/generator.py
 M sqlglot/generators/oracle.py
 M sqlglot/parser.py
 M tests/dialects/test_oracle.py
[This command modified 1 file you've previously read: sqlglot/generator.py. Call Read before editing.]
[tool_use Bash] {"command": "git diff sqlglot/generator.py | tail -20 && git diff --stat", "description": "Show final generator diff and stats"}
[tool_result]      # Whether the INTERVAL expression works only with values like '1 day'
     SINGLE_STRING_INTERVAL = False
 
@@ -4461,6 +4464,16 @@ class Generator:
 
         else:
             then = self.sql(then_expression)
+
+        if isinstance(then_expression, (exp.Insert, exp.Update)):
+            where = self.sql(then_expression, "where")
+            if where and self.MERGE_WHEN_WHERE_SUPPORTED:
+                then = f"{then}{where}"
+            elif where:
+                self.unsupported(
+                    "WHERE clause in MERGE WHEN ... THEN UPDATE/INSERT is not supported"
+                )
+
         return f"WHEN {matched}{source}{condition} THEN {then}"
 
     def whens_sql(self, expression: exp.Whens) -> str:
 sqlglot/generator.py          | 13 +++++++++++++
 sqlglot/generators/oracle.py  |  1 +
 sqlglot/parser.py             |  2 ++
 tests/dialects/test_oracle.py | 23 +++++++++++++++++++++++
 4 files changed, 39 insertions(+)
[assistant] Oracle `MERGE` now accepts the optional `WHERE` on both the `UPDATE` and `INSERT` branches, and it round-trips. On other dialects the clause is dropped with an unsupported warning. The full suite passes (1081 tests) and `ruff check` and `ruff format` are clean. I did not commit.

Changes:
- **`sqlglot/parser.py`** (`_parse_when_matched`): after the `INSERT` and `UPDATE` branches, parse an optional `WHERE` into the branch's existing `where` arg. `Insert` and `Update` already declared that arg.
- **`sqlglot/generator.py`**: `when_sql` emits the `WHERE` when the generator flag `MERGE_WHEN_WHERE_S
…[23 chars elided]…
wise it calls `self.unsupported(...)` and omits the clause. The flag defaults to `False`, which is the behaviour for every dialect except Oracle.
- **`sqlglot/generators/oracle.py`**: sets `MERGE_WHEN_WHERE_SUPPORTED = True`.
- **`tests/dialects/test_oracle.py`**: new `test_merge_when_where`. It checks the Oracle round-trip, and it checks that DuckDB output drops both clauses and logs the warning.

Decision for you: I put the flag in the base generator, so any dialect that later gains this syntax needs its own override. Say if you would rather have the parser accept the clause only for Oracle.
