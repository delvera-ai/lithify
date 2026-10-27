# trajectory base-2

final message:
Oracle `MERGE` now accepts a `WHERE` on both the `UPDATE` and `INSERT` branches, round-trips it, and drops it with an unsupported warning when transpiling elsewhere. The full suite passes (1081 tests) and ruff is clean. I did not run mypy.

The change:

- **Parser** (`sqlglot/parser.py`, `_parse_when_matched`): after an `INSERT` or `UPDATE` branch, an optional `WHERE` is stored in that node's existing `where` arg. Both node types already had this arg, so no expression classes changed.
- **Generator** (`sqlglot/generator.py`, `when_sql`): emits ` WHERE ...` after the branch when the flag is set. Otherwise it calls `self.unsupported(...)` and omits the clause.
- **Flag**: new `SUPPORTS_MERGE_WHERE = False` on the base generator, set to `True` in `sqlglot/generators/oracle.py`. This follows the existing `MATCHED_BY_SOURCE` pattern.
- **Tests** (`tests/dialects/test_oracle.py`): a new `test_merge_when_where` covers an Oracle round-trip with WHERE on both branches. It also checks that DuckDB output drops both clauses and logs the warning.

I left the work uncommitted, since you didn't ask for a commit.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"WHEN\\|_parse_when_matched\\|MERGE\\|Merge\" sqlglot/parser.py | head -60 && grep -n \"Merge\\|merge\" sqlglot/expressions.py | head -30 && grep -n \"merge\\|Merge\\|WhenMatched\" sqlglot/generator.py | head -30", "description": "Locate MERGE handling in parser, expressions, generator"}
[tool_result] 700:        TokenType.MERGE,
830:        TokenType.MERGE,
1056:        exp.Whens: lambda self: self._parse_when_matched(),
1080:        TokenType.MERGE: lambda self: self._parse_merge(),
1271:        "MERGEBLOCKRATIO": lambda self, **kwargs: self._parse_mergeblockratio(**kwargs),
1377:        "TTL": lambda self: self.expression(exp.MergeTreeTTL(expressions=[self._parse_bitwise()])),
2194:                return self.expression(exp.MergeTreeTTLAction(this=this, delete=True))
2197:                 
…[998 chars elided]…
ation.POST_NAME,
744:        exp.MergeTreeTTL: exp.Properties.Location.POST_SCHEMA,
2032:    def mergeblockratioproperty_sql(self, expression: exp.MergeBlockRatioProperty) -> str:
3852:    def mergetreettlaction_sql(self, expression: exp.MergeTreeTTLAction) -> str:
3863:    def mergetreettl_sql(self, expression: exp.MergeTreeTTL) -> str:
4469:    def merge_sql(self, expression: exp.Merge) -> str:
4475:            # T-SQL syntax is MERGE ... <target_table> [WITH (<merge_hint>)] [[AS] table_alias]
[tool_use Bash] {"command": "grep -rn \"merge\\|Merge\\|WHEN MATCHED\" sqlglot/dialects/oracle.py sqlglot/dialects/dialect.py | head; grep -rln \"WHEN MATCHED\\|MERGE\" tests/dialects/ | head", "description": "Search Oracle dialect and tests for MERGE"}
[tool_result] sqlglot/dialects/dialect.py:238:        # Merge class-defined INVERSE_TIME_MAPPING with auto-generated mappings
sqlglot/dialects/dialect.py:2030:def merge_without_target_sql(self: Generator, expression: exp.Merge) -> str:
sqlglot/dialects/dialect.py:2043:        # only remove the target table names from certain parts of WHEN MATCHED / WHEN NOT MATCHED
sqlglot/dialects/dialect.py:2063:    return self.merge_sql(expression)
tests/dialects/test_snowflake.py
tests/dialects/test_bigquery.py
tests/dialects/test_spark.py
tests/dialects/test_oracle.py
tests/dialects/test_teradata.py
tests/dialects/test_duckdb.py
tests/dialects/test_dialect.py
tests/dialects/test_tsql.py
tests/dialects/test_mysql.py
tests/dialects/test_postgres.py
[tool_use Bash] {"command": "sed -n 8880,8950p sqlglot/parser.py && grep -n \"class Whens\\|class Merge(\" -A12 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null | head -60; sed -n 4465,4520p sqlglot/generator.py; grep -n \"def whens_sql\" -A25 sqlglot/generator.py; sed -n 2025,2065p sqlglot/dialects/dialect.py", "description": "Read MERGE parser, generator and dialect helper"}
[tool_result]                 update_options=update_options,
            )
        )

    def _parse_merge(self) -> exp.Merge:
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
…[7630 chars elided]…
s.get("table")) in targets
                    ):
                        equal_lhs.replace(exp.column(equal_lhs.this))
            if isinstance(then, exp.Insert):
                column_list = then.this
                if isinstance(column_list, exp.Tuple):
                    for column in column_list.expressions:
                        if normalize(column.args.get("table")) in targets:
                            column.replace(exp.column(column.this))

    return self.merge_sql(expression)
[tool_use Bash] {"command": "sed -n 8950,8965p sqlglot/parser.py; sed -n 517,530p sqlglot/expressions/dml.py; grep -n \"def when_sql\" -A25 sqlglot/generator.py; grep -n \"MERGE\" -B2 -A12 tests/dialects/test_oracle.py | head -80; grep -n \"Merge\\|merge\" sqlglot/dialects/oracle.py; grep -rn \"unsupported_args\\|def unsupported\" sqlglot/generator.py | head -3", "description": "Read When construction, when_sql, and Oracle MERGE tests"}
[tool_result]                 self.expression(
                    exp.When(matched=matched, source=source, condition=condition, then=then)
                )
            )
        return self.expression(exp.Whens(expressions=whens))

    def _parse_show(self) -> exp.Expr | None:
        parser = self._find_parser(self.SHOW_PARSERS, self.SHOW_TRIE)
        if parser:
            return parser(self)
        return self._parse_as_command(self._prev)

    def _parse_set_item_assignment(self, kind: str | None = No
…[2288 chars elided]…
            "WITH t AS (SELECT 1 AS COL) SELECT col, ROWID FROM t WHERE ROWNUM = 1"
901-        )
902-        self.assertIsNone(ast.find(exp.Pseudocolumn))
903-
904-        qualified = qualify(ast, dialect="oracle")
905-        self.assertIsNotNone(qualified.find(exp.Pseudocolumn))
906-
907-        self.assertEqual(
sqlglot/generator.py:30:def unsupported_args(
sqlglot/generator.py:953:    def unsupported(self, message: str) -> None:
sqlglot/generator.py:2529:    @unsupported_args("expressions")
[tool_use Bash] {"command": "grep -n \"^class Insert(\\|^class Update(\" -A22 sqlglot/expressions/dml.py | head -70; grep -n \"SUPPORTS_\\w* = \" sqlglot/generator.py | head -5; grep -n \"SUPPORTS_\\|MATCHED_BY_SOURCE\" sqlglot/dialects/oracle.py | head; grep -n \"^def unsupported_args\" -A3 sqlglot/generator.py", "description": "Inspect Insert/Update arg_types and generator flags"}
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
…[579 chars elided]…
ype = None,
310-        copy: bool = True,
311-        **opts: Unpack[ParserNoDialectArgs],
312-    ) -> Update:
313-        """
314-        Set the table to update.
315-
407:    SUPPORTS_TABLE_COPY = True
437:    SUPPORTS_SINGLE_ARG_CONCAT = True
440:    LAST_DAY_SUPPORTS_DATE_PART = True
443:    SUPPORTS_TABLE_ALIAS_COLUMNS = True
455:    SUPPORTS_SELECT_INTO = False
30:def unsupported_args(
31-    *args: str | tuple[str, str],
32-) -> t.Callable[[GeneratorMethod], GeneratorMethod]:
33-    """
[tool_use Bash] {"command": "grep -n \"MATCHED_BY_SOURCE\" sqlglot/generator.py sqlglot/dialects/*.py | head; grep -n \"    def sql(\" -A12 sqlglot/generator.py | head -30; grep -rn \"assertLogs\\|unsupported_level=ErrorLevel.RAISE\" tests/dialects/test_oracle.py | head -3; grep -n \"^class Generator\" -A3 sqlglot/dialects/oracle.py", "description": "Check flag conventions, sql() None handling, and test idioms"}
[tool_result] sqlglot/generator.py:321:    MATCHED_BY_SOURCE = True
sqlglot/generator.py:4445:        source = " BY SOURCE" if self.MATCHED_BY_SOURCE and expression.args.get("source") else ""
1058:    def sql(
1059-        self,
1060-        expression: str | exp.Expr | None,
1061-        key: str | None = None,
1062-        comment: bool = True,
1063-    ) -> str:
1064-        if not expression:
1065-            return ""
1066-
1067-        if isinstance(expression, str):
1068-            return expression
1069-
1070-        if key:
[tool_use Bash] {"command": "sed -n 315,325p sqlglot/generator.py; grep -n \"class Generator\" -A12 sqlglot/dialects/oracle.py; grep -rn \"unsupported_level\" tests/dialects/test_oracle.py | head -3; grep -rn \"assertLogs\" tests/dialects/*.py | head -3; sed -n 880,893p tests/dialects/test_oracle.py", "description": "Inspect MATCHED_BY_SOURCE, Oracle generator, test idioms"}
[tool_result]     WRAP_DERIVED_VALUES = True

    # Whether create function uses an AS before the RETURN
    CREATE_FUNCTION_RETURN_AS = True

    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed
    MATCHED_BY_SOURCE = True

    # Whether the INTERVAL expression works only with values like '1 day'
    SINGLE_STRING_INTERVAL = False

tests/dialects/test_clickhouse.py:1729:        with self.assertLogs(helper_logger) as cm:
tests/dialects/test_bigquery.py:2130:        with self.assertLogs(helper_logger) as
…[289 chars elided]…
).assert_is(exp.UtcTimestamp)

    def test_merge_builder_alias(self):
        merge_stmt = exp.merge(
            "WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1",
            "WHEN NOT MATCHED THEN INSERT (my_table.id, my_table.col1) VALUES (source_table.id, source_table.col1)",
            into="my_table",
            using="(SELECT * FROM something) source_table",
            on="my_table.id = source_table.id",
            dialect="oracle",
        )
        self.assertEqual(
[tool_use Bash] {"command": "grep -n \"class \\|    [A-Z_]* = \" sqlglot/dialects/oracle.py | head -60; grep -n \"MERGE\\|merge\" sqlglot/dialects/*.py | grep -i \"generator\\|TRANSFORMS\\|merge_sql\" | head", "description": "List Oracle dialect classes and flags"}
[tool_result] 15:class Oracle(Dialect):
16:    ALIAS_POST_TABLESAMPLE = True
17:    LOCKING_READS_SUPPORTED = True
18:    TABLESAMPLE_SIZE_IS_PERCENT = True
19:    NULL_ORDERING = "nulls_are_large"
20:    ON_CONDITION_EMPTY_BEFORE_ERROR = False
21:    ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN = False
22:    DISABLES_ALIAS_REF_EXPANSION = True
25:    NORMALIZATION_STRATEGY = NormalizationStrategy.UPPERCASE
29:    TIME_MAPPING = {
50:    PSEUDOCOLUMNS = {"ROWNUM", "ROWID", "OBJECT_ID", "OBJECT_VALUE", "LEVEL"}
59:    class Tokenizer(tokens.Tokenizer):
60:        VAR_SINGLE_TOKENS = {"@", "$", "#"}
62:        UNICODE_STRINGS = [
68:        NESTED_COMMENTS = False
70:        KEYWORDS = {
sqlglot/dialects/dialect.py:2030:def merge_without_target_sql(self: Generator, expression: exp.Merge) -> str:
sqlglot/dialects/dialect.py:2063:    return self.merge_sql(expression)
[tool_use Bash] {"command": "grep -n \"class Generator\" -A40 sqlglot/dialects/oracle.py | head -60; sed -n 2,14p sqlglot/dialects/oracle.py", "description": "Read Oracle Generator class"}
[tool_result] import typing as t

from sqlglot import exp, tokens
from sqlglot.dialects.dialect import (
    Dialect,
    NormalizationStrategy,
)
from sqlglot.generators.oracle import OracleGenerator
from sqlglot.parsers.oracle import OracleParser
from sqlglot.tokens import TokenType
[tool_use Bash] {"command": "ls sqlglot/generators sqlglot/parsers; grep -n \"MATCHED_BY_SOURCE\\|def when_sql\\|def merge_sql\" -r sqlglot/ | head; grep -n \"class OracleGenerator\" -A30 sqlglot/generators/oracle.py | head -50", "description": "Locate generator and parser module files"}
[tool_result] sqlglot/generators:
__init__.py
athena.py
bigquery.py
clickhouse.py
databricks.py
doris.py
dremio.py
drill.py
druid.py
duckdb.py
dune.py
exasol.py
fabric.py
hive.py
materialize.py
mysql.py
oracle.py
postgres.py
presto.py
prql.py
redshift.py
risingwave.py
singlestore.py
snowflake.py
solr.py
spark.py
spark2.py
sqlite.py
starrocks.py
tableau.py
teradata.py
trino.py
tsql.py

sqlglot/parsers:
__init__.py
athena.py
base.py
bigquery.py
clickhouse.py
databricks.py
doris.py
dremio.py
drill.py
druid.py
du
…[1299 chars elided]…
IFIER_TRANSFORMS = generator.AFTER_HAVING_MODIFIER_TRANSFORMS
42-
43-    TYPE_MAPPING = {
44-        **generator.Generator.TYPE_MAPPING,
45-        exp.DType.BLOB: "BLOB",
46-        exp.DType.TINYINT: "SMALLINT",
47-        exp.DType.SMALLINT: "SMALLINT",
48-        exp.DType.INT: "INT",
49-        exp.DType.BIGINT: "INT",
50-        exp.DType.DECIMAL: "NUMBER",
51-        exp.DType.DOUBLE: "DOUBLE PRECISION",
52-        exp.DType.VARCHAR: "VARCHAR2",
53-        exp.DType.NVARCHAR: "NVARCHAR2",
[tool_use Bash] {"command": "grep -rn \"_parse_when_matched\\|def when_sql\\|def merge_sql\" sqlglot/ | head; wc -l sqlglot/parser.py sqlglot/parsers/base.py sqlglot/generator.py; head -20 sqlglot/parser.py", "description": "Confirm which module defines MERGE parsing and generation"}
[tool_result] sqlglot/generator.py:4443:    def when_sql(self, expression: exp.When) -> str:
sqlglot/generator.py:4469:    def merge_sql(self, expression: exp.Merge) -> str:
sqlglot/parser.py:1056:        exp.Whens: lambda self: self._parse_when_matched(),
sqlglot/parser.py:8900:                whens=self._parse_when_matched(),
sqlglot/parser.py:8905:    def _parse_when_matched(self) -> exp.Whens:
    9863 sqlglot/parser.py
      17 sqlglot/parsers/base.py
    5911 sqlglot/generator.py
   15791 total
from __future__ import annotations

import itertools
import logging
import re
import typing as t
from collections import defaultdict

from sqlglot import exp
from sqlglot.errors import (
    ErrorLevel,
    ParseError,
    TokenError,
    concat_messages,
    highlight_sql,
    merge_errors,
)
from sqlglot.expressions import apply_index_offset
from sqlglot.helper import ensure_list, i64, seq_get
from sqlglot.trie import new_trie
[assistant] Now the edits. Parser first: attach the optional `WHERE` to the UPDATE/INSERT branch.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-153659-oracle-dialect-support-the-optio/base-2/sqlglot/parser.py", "old_string": "            else:\n                then = self._parse_var_from_options(self.CONFLICT_ACTIONS)\n\n            whens.append(", "new_string": "            else:\n                then = self._parse_var_from_options(self.CONFLICT_ACTIONS)\n\n            if isinstance(then, (exp.Insert, exp.Update)) and self._match(TokenType.WHERE):\n                then.set(\"where\", self._parse_disjunction())\n\n            whens.append("}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-153659-oracle-dialect-support-the-optio/base-2/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-153659-oracle-dialect-support-the-optio/base-2/sqlglot/generator.py", "old_string": "    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed\n    MATCHED_BY_SOURCE = True\n", "new_string": "    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed\n    MATCHED_BY_SOURCE = True\n\n    # Whether the WHERE clause of a MERGE ... WHEN MATCHED / NOT MATCHED branch is allowed\n    SUPPORTS_MERGE_WHERE = False\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-153659-oracle-dialect-support-the-optio/base-2/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-153659-oracle-dialect-support-the-optio/base-2/sqlglot/generator.py", "old_string": "        else:\n            then = self.sql(then_expression)\n        return f\"WHEN {matched}{source}{condition} THEN {then}\"", "new_string": "        else:\n            then = self.sql(then_expression)\n\n        w
…[61 chars elided]…
rt, exp.Update)) and then_expression.args.get(\n            \"where\"\n        ):\n            if self.SUPPORTS_MERGE_WHERE:\n                where = f\" WHERE {self.sql(then_expression, 'where')}\"\n            else:\n                self.unsupported(\"WHERE clause in MERGE WHEN MATCHED / NOT MATCHED is not supported\")\n\n        return f\"WHEN {matched}{source}{condition} THEN {then}{where}\""}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-153659-oracle-dialect-support-the-optio/base-2/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-153659-oracle-dialect-support-the-optio/base-2/sqlglot/generators/oracle.py", "old_string": "    SUPPORTS_DECODE_CASE = True\n", "new_string": "    SUPPORTS_DECODE_CASE = True\n    SUPPORTS_MERGE_WHERE = True\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-153659-oracle-dialect-support-the-optio/base-2/sqlglot/generators/oracle.py has been updated successfully.
[assistant] Now a test in the Oracle test file, then a check of the behavior across the parser and generator paths.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-153659-oracle-dialect-support-the-optio/base-2/tests/dialects/test_oracle.py", "old_string": "    def test_merge_builder_alias(self):", "new_string": "    def test_merge_when_where(self):\n        self.validate_identity(\n            \"MERGE INTO my_table USING source_table ON my_table.id = source_ta
…[651 chars elided]…
\"duckdb\",\n                    unsupported_level=ErrorLevel.WARN,\n                ),\n                [\n                    \"MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.c = s.c WHEN NOT MATCHED THEN INSERT (t.id) VALUES (s.id)\"\n                ],\n            )\n        self.assertIn(\"WHERE clause in MERGE\", cm.output[0])\n\n    def test_merge_builder_alias(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-153659-oracle-dialect-support-the-optio/base-2/tests/dialects/test_oracle.py has been updated successfully.
[tool_use Bash] {"command": "sed -n 1,12p tests/dialects/test_oracle.py; grep -n \"helper_logger\" tests/dialects/test_clickhouse.py | head -2; ls <work>/env-sqlglot/bin/python 2>&1", "description": "Check test imports and project venv existence"}
[tool_result] from sqlglot import exp, UnsupportedError, ParseError, parse, parse_one
from tests.dialects.test_dialect import Validator
from sqlglot.optimizer.qualify import qualify


class TestOracle(Validator):
    dialect = "oracle"

    def test_oracle(self):
        self.validate_identity("1 /* /* */", "1 /* / * */")
        self.validate_all(
            "SELECT CONNECT_BY_ROOT x y",
5:from sqlglot.helper import logger as helper_logger
1729:        with self.assertLogs(helper_logger) as cm:
<work>/env-sqlglot/bin/python
[tool_use Bash] {"command": "grep -n \"def validate_all\" -A30 tests/dialects/test_dialect.py | head -45", "description": "Read validate_all helper signature"}
[tool_result] 68:    def validate_all(self, sql, read=None, write=None, pretty=False, identify=False):
69-        """
70-        Validate that:
71-        1. Everything in `read` transpiles to `sql`
72-        2. `sql` transpiles to everything in `write`
73-
74-        Args:
75-            sql (str): Main SQL expression
76-            read (dict): Mapping of dialect -> SQL
77-            write (dict): Mapping of dialect -> SQL
78-            pretty (bool): prettify both read and write
79-            identify 
…[354 chars elided]…
         self.dialect,
88-                        unsupported_level=ErrorLevel.IGNORE,
89-                        pretty=pretty,
90-                        identify=identify,
91-                    ),
92-                    sql,
93-                )
94-
95-        for write_dialect, write_sql in (write or {}).items():
96-            with self.subTest(f"{sql} -> {write_dialect}"):
97-                if write_sql is UnsupportedError:
98-                    with self.assertRaises(UnsupportedError):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-153659-oracle-dialect-support-the-optio/base-2/tests/dialects/test_oracle.py", "old_string": "        with self.assertLogs(helper_logger) as cm:\n            self.assertEqual(\n                transpile(\n                    \"MERGE INTO t USING s ON t.id = s.id \"\n                    \"WHEN MATCHED
…[834 chars elided]…
\",\n        )\n        with self.assertLogs(helper_logger) as cm:\n            self.assertEqual(\n                merge.sql(\"duckdb\", unsupported_level=ErrorLevel.WARN),\n                \"MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.c = s.c WHEN NOT MATCHED THEN INSERT (t.id) VALUES (s.id)\",\n            )\n        self.assertIn(\"WHERE clause in MERGE\", cm.output[0])"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-153659-oracle-dialect-support-the-optio/base-2/tests/dialects/test_oracle.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-153659-oracle-dialect-support-the-optio/base-2/tests/dialects/test_oracle.py", "old_string": "from sqlglot import exp, UnsupportedError, ParseError, parse, parse_one\nfrom tests.dialects.test_dialect import Validator", "new_string": "from sqlglot import exp, UnsupportedError, ParseError, parse, parse_one\nfrom sqlglot.errors import ErrorLevel\nfrom sqlglot.helper import logger as helper_logger\nfrom tests.dialects.test_dialect import Validator"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-153659-oracle-dialect-support-the-optio/base-2/tests/dialects/test_oracle.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py 2>&1 | tail -30", "description": "Run Oracle dialect tests"}
[tool_result] ........................                                                      [100%]
24 passed, 211 subtests passed in 0.36s
[assistant] Oracle tests pass. Running the full suite and the project's style checks next.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; (ruff check sqlglot tests/dialects/test_oracle.py && ruff format --check sqlglot tests/dialects/test_oracle.py) 2>&1 | tail -8", "description": "Run full test suite and ruff checks"}
[tool_result] ................................................................................. [  7%]
................................ [ 10%]
................................................................................................................................... [ 22%]
..................................................... [ 27%]
................ [ 28%]
.................................................................................................... [ 38%]
.......................................
…[365 chars elided]…
..................................................................................................................................................................................................................................... [ 94%]
....................... [ 96%]
....................................                      [100%]
1081 passed, 17834 subtests passed in 80.19s (0:01:20)
All checks passed!
Would reformat: sqlglot/generator.py
1 file would be reformatted, 173 files already formatted
[tool_use Bash] {"command": "ruff format sqlglot/generator.py && git diff sqlglot/generator.py && ruff format --check sqlglot tests/dialects/test_oracle.py | tail -1", "description": "Apply ruff formatting and show generator diff"}
[tool_result] 1 file reformatted
diff --git a/sqlglot/generator.py b/sqlglot/generator.py
index d9f08c480..66045ff68 100644
--- a/sqlglot/generator.py
+++ b/sqlglot/generator.py
@@ -320,6 +320,9 @@ class Generator:
     # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed
     MATCHED_BY_SOURCE = True
 
+    # Whether the WHERE clause of a MERGE ... WHEN MATCHED / NOT MATCHED branch is allowed
+    SUPPORTS_MERGE_WHERE = False
+
     # Whether the INTERVAL expression works only with values like '1 day'
     
…[459 chars elided]…
ere')}"
+            else:
+                self.unsupported(
+                    "WHERE clause in MERGE WHEN MATCHED / NOT MATCHED is not supported"
+                )
+
+        return f"WHEN {matched}{source}{condition} THEN {then}{where}"
 
     def whens_sql(self, expression: exp.Whens) -> str:
         return self.expressions(expression, sep=" ", indent=False)
174 files already formatted
[This command modified 1 file you've previously read: sqlglot/generator.py. Call Read before editing.]
[assistant] Oracle `MERGE` now accepts a `WHERE` on both the `UPDATE` and `INSERT` branches, round-trips it, and drops it with an unsupported warning when transpiling elsewhere. The full suite passes (1081 tests) and ruff is clean. I did not run mypy.

The change:

- **Parser** (`sqlglot/parser.py`, `_parse_when_matched`): after an `INSERT` or `UPDATE` branch, an optional `WHERE` is stored in that node's existing `where` arg. Both node types already had this arg, so no expression classes changed.
- **Generator** (`sqlglot/generator.py`, `when_sql`): emits ` WHERE ...` after the branch when the flag is set. Otherwise it calls `self.unsupported(...)` and omits the clause.
- **Flag**: new `SUPPORTS_MERGE_WHERE = False` on the base generator, set to `True` in `sqlglot/generators/oracle.py`. This follows the existing `MATCHED_BY_SOURCE` pattern.
- **Tests** (`tests/dialects/test_oracle.py`): a new `test_merge_when_where` covers an Oracle round-trip with WHERE on both branches. It also checks that DuckDB output drops both clauses and logs the warning.

I left the work uncommitted, since you didn't ask for a commit.
