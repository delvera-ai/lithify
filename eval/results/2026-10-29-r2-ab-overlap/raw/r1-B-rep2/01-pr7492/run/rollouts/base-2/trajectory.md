# trajectory base-2

final message:
Oracle `MERGE` now accepts a `WHERE` on both the `UPDATE` and `INSERT` branches, round-trips it, and drops it with an unsupported warning when transpiling elsewhere. The full suite passed (1081 tests) before the final formatting pass; I re-ran the Oracle and dialect test files after it. Ruff lint and format are clean. I did not commit.

The changes:

- **Parser** (`sqlglot/parser.py`, `_parse_when_matched`): after an `INSERT` or `UPDATE` branch, parse an optional `WHERE` into the existing `where` arg on `Insert`/`Update`. This is in the base parser, since no other dialect's syntax conflicts with it.
- **Generator** (`sqlglot/generator.py`, `when_sql`): emits the `WHERE` only when the target generator sets `SUPPORTS_MERGE_WHEN_WHERE`. Otherwise it calls `self.unsupported(...)` and drops the clause. The flag defaults to `False`.
- **Oracle** (`sqlglot/generators/oracle.py`): sets `SUPPORTS_MERGE_WHEN_WHERE = True`.
- **Tests** (`tests/dialects/test_oracle.py`): a new `test_merge_when_where` checks the Oracle round-trip and checks that DuckDB output drops the clause and logs the warning.

Decision for you: I gave the flag a default of `False`, so every non-Oracle dialect warns and drops the clause. If any other dialect supports this syntax, set its flag to `True` in that dialect's generator.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"Merge\\|MERGE\\|_merge\" sqlglot/dialects/oracle.py sqlglot/parser.py sqlglot/generator.py | head -80 && grep -n \"class Merge\\|class When\" -A 20 sqlglot/expressions.py | head -60", "description": "Check git state and find MERGE handling code"}
[tool_result] sqlglot/generator.py:320:    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed
sqlglot/generator.py:700:        exp.MergeBlockRatioProperty: exp.Properties.Location.POST_NAME,
sqlglot/generator.py:744:        exp.MergeTreeTTL: exp.Properties.Location.POST_SCHEMA,
sqlglot/generator.py:2032:    def mergeblockratioproperty_sql(self, expression: exp.MergeBlockRatioProperty) -> str:
sqlglot/generator.py:2034:            return "NO MERGEBLOCKRATIO"
sqlglot/generator.py:2036:            return "DEF
…[1500 chars elided]…
219:            exp.MergeTreeTTL(
sqlglot/parser.py:3037:    def _parse_mergeblockratio(
sqlglot/parser.py:3039:    ) -> exp.MergeBlockRatioProperty:
sqlglot/parser.py:3042:                exp.MergeBlockRatioProperty(
sqlglot/parser.py:3047:        return self.expression(exp.MergeBlockRatioProperty(no=no, default=default))
sqlglot/parser.py:8884:    def _parse_merge(self) -> exp.Merge:
sqlglot/parser.py:8895:            exp.Merge(
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "sed -n 8884,8990p sqlglot/parser.py && grep -n \"class Merge(\" -A 25 sqlglot/expressions/*.py && sed -n 4469,4500p sqlglot/generator.py && grep -n \"def merge_sql\\|def whens_sql\\|def when_sql\" -A 60 sqlglot/generator.py | sed -n 1,140p", "description": "Read MERGE parser, expression, and generator code"}
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
…[9583 chars elided]…

4520-        args = f"({self.sep('')}{settings_sql}{self.seg(')', sep='')}" if settings_sql else "()"
4521-        return f"{this}({kind}{args})"
4522-
4523-    def dictrange_sql(self, expression: exp.DictRange) -> str:
4524-        this = self.sql(expression, "this")
4525-        max = self.sql(expression, "max")
4526-        min = self.sql(expression, "min")
4527-        return f"{this}(MIN {min} MAX {max})"
4528-
4529-    def dictsubproperty_sql(self, expression: exp.DictSubProperty) -> str:
[tool_use Bash] {"command": "grep -n \"class Update(\\|class Insert(\" -A 22 sqlglot/expressions/dml.py | head -60; grep -n \"def _parse_where\" -A 3 sqlglot/parser.py; sed -n 315,325p sqlglot/generator.py; grep -n \"MATCHED\\|MERGE\" sqlglot/dialects/oracle.py sqlglot/dialects/dialect.py | head; grep -rn \"MERGE\" tests/dialects/test_oracle.py | head -20; grep -n \"def unsupported\" -A3 sqlglot/generator.py", "description": "Inspect Insert/Update expressions, Oracle MERGE tests, unsupported helper"}
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
…[1565 chars elided]…
N UPDATE SET my_table.col1 = source_table.col1 WHEN NOT MATCHED THEN INSERT (my_table.id, my_table.col1) VALUES (source_table.id, source_table.col1)",
30:def unsupported_args(
31-    *args: str | tuple[str, str],
32-) -> t.Callable[[GeneratorMethod], GeneratorMethod]:
33-    """
--
953:    def unsupported(self, message: str) -> None:
954-        if self.unsupported_level == ErrorLevel.IMMEDIATE:
955-            raise UnsupportedError(message)
956-        self.unsupported_messages.append(message)
[tool_use Bash] {"command": "sed -n 885,905p tests/dialects/test_oracle.py; grep -n \"class Generator\" -A 30 sqlglot/dialects/oracle.py | head -50; grep -rn \"MATCHED_BY_SOURCE\" sqlglot | head; grep -n \"WHEN MATCHED\\|WHEN NOT MATCHED\" tests/dialects/*.py | head -30", "description": "Inspect Oracle merge test and generator class"}
[tool_result]         merge_stmt = exp.merge(
            "WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1",
            "WHEN NOT MATCHED THEN INSERT (my_table.id, my_table.col1) VALUES (source_table.id, source_table.col1)",
            into="my_table",
            using="(SELECT * FROM something) source_table",
            on="my_table.id = source_table.id",
            dialect="oracle",
        )
        self.assertEqual(
            merge_stmt.sql("oracle"),
            "MERGE INTO my_table
…[5735 chars elided]…
9:                "trino": """MERGE INTO foo AS target USING (SELECT a, b FROM tbl) AS src ON src.a = target.a WHEN MATCHED THEN UPDATE SET b = COALESCE(src.b, target.b) WHEN NOT MATCHED THEN INSERT (a, b) VALUES (src.a, src.b)""",
tests/dialects/test_dialect.py:3110:                "postgres": """MERGE INTO foo AS target USING (SELECT a, b FROM tbl) AS src ON src.a = target.a WHEN MATCHED THEN UPDATE SET b = COALESCE(src.b, target.b) WHEN NOT MATCHED THEN INSERT (a, b) VALUES (src.a, src.b)""",
[tool_use Bash] {"command": "ls sqlglot/generators sqlglot/parsers 2>/dev/null | head -80; grep -n \"class Generator\" -A 12 sqlglot/generators/oracle.py; grep -n \"SUPPORTS\\|class .*Generator\" sqlglot/generators/oracle.py | head -20; grep -n \"^class\\|class Parser\" sqlglot/dialects/oracle.py | head", "description": "Locate Oracle generator and parser modules"}
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
…[7 chars elided]…

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
23:class OracleGenerator(generator.Generator):
26:    SUPPORTS_UESCAPE = False
34:    LAST_DAY_SUPPORTS_DATE_PART = False
35:    SUPPORTS_SELECT_INTO = True
37:    SUPPORTS_WINDOW_EXCLUDE = True
39:    SUPPORTS_DECODE_CASE = True
15:class Oracle(Dialect):
[tool_use Bash] {"command": "grep -rln \"def _parse_when_matched\\|def when_sql\" sqlglot; ls sqlglot | head -80; cat sqlglot/parser.py 2>/dev/null | head -5; sed -n 20,45p sqlglot/generators/oracle.py", "description": "Find which files define the MERGE parse and generate methods"}
[tool_result] sqlglot/parser.py
sqlglot/generator.py
__init__.py
__main__.py
_typing.py
_version.py
dialects
diff.py
errors.py
executor
expressions
generator.py
generators
helper.py
jsonpath.py
lineage.py
optimizer
parser.py
parsers
planner.py
py.typed
schema.py
serde.py
time.py
tokenizer_core.py
tokens.py
transforms.py
trie.py
typing
from __future__ import annotations

import itertools
import logging
import re
    return trim_sql(self, expression)


class OracleGenerator(generator.Generator):
    SELECT_KIND
…[186 chars elided]…
ALLOWED = True
    ALTER_TABLE_INCLUDE_COLUMN_KEYWORD = False
    LIMIT_FETCH = "FETCH"
    TABLESAMPLE_KEYWORDS = "SAMPLE"
    LAST_DAY_SUPPORTS_DATE_PART = False
    SUPPORTS_SELECT_INTO = True
    TZ_TO_WITH_TIME_ZONE = True
    SUPPORTS_WINDOW_EXCLUDE = True
    QUERY_HINT_SEP = " "
    SUPPORTS_DECODE_CASE = True

    AFTER_HAVING_MODIFIER_TRANSFORMS = generator.AFTER_HAVING_MODIFIER_TRANSFORMS

    TYPE_MAPPING = {
        **generator.Generator.TYPE_MAPPING,
        exp.DType.BLOB: "BLOB",
[tool_use Bash] {"command": "sed -n 2030,2065p sqlglot/dialects/dialect.py; grep -n \"def whereclause\\|def where_sql\" -A 4 sqlglot/generator.py", "description": "Check related merge transform and where generator"}
[tool_result] def merge_without_target_sql(self: Generator, expression: exp.Merge) -> str:
    """Remove table refs from columns in when statements."""
    alias = expression.this.args.get("alias")

    def normalize(identifier: exp.Identifier | None) -> str | None:
        return self.dialect.normalize_identifier(identifier).name if identifier else None

    targets = {normalize(expression.this.this)}

    if alias:
        targets.add(normalize(alias.this))

    for when in expression.args["whens"].expressi
…[871 chars elided]…
uple):
                    for column in column_list.expressions:
                        if normalize(column.args.get("table")) in targets:
                            column.replace(exp.column(column.this))

    return self.merge_sql(expression)


3221:    def where_sql(self, expression: exp.Where) -> str:
3222-        this = self.indent(self.sql(expression, "this"))
3223-        return f"{self.seg('WHERE')}{self.sep()}{this}"
3224-
3225-    def window_sql(self, expression: exp.Window) -> str:
[assistant] Parser, generator, and Oracle flag are the three touch points. `Insert` and `Update` already have a `where` arg, so no expression change is needed.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-111417-oracle-dialect-support-the-optio/base-2/sqlglot/parser.py", "old_string": "            else:\n                then = self._parse_var_from_options(self.CONFLICT_ACTIONS)\n\n            whens.append(", "new_string": "            else:\n                then = self._parse_var_from_options(self.CONFLICT_ACTIONS)\n\n            if isinstance(then, (exp.Insert, exp.Update)):\n                then.set(\"where\", self._parse_where())\n\n            whens.append("}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-111417-oracle-dialect-support-the-optio/base-2/sqlglot/parser.py has been updated successfully.
[assistant] Now the generator: emit the clause when the target dialect supports it, otherwise warn and drop it.
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\np=\"sqlglot/generator.py\"\ns=open(p).read()\nold_flag=\"\"\"    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed\n    MATCHED_BY_SOURCE = True\n\"\"\"\nnew_flag=old_flag+\"\"\"\n    # Whether MERGE ... WHEN [NOT] MATCHED THEN UPDATE / INSERT ... WHERE <condition> is allowed\n    SUPPORTS_MERGE_WHEN_WHERE = False\n\"\"\"\nassert s.count(old_flag)==1\
…[2175 chars elided]…
\"\n\"\"\"\nassert s.count(old)==1\ns=s.replace(old,new)\nopen(p,\"w\").write(s)\n\np=\"sqlglot/generators/oracle.py\"\ns=open(p).read()\nold=\"    SUPPORTS_DECODE_CASE = True\\n\"\nassert s.count(old)==1\ns=s.replace(old, old+\"    SUPPORTS_MERGE_WHEN_WHERE = True\\n\")\nopen(p,\"w\").write(s)\nEOF\ngit diff --stat", "description": "Apply generator flag, when_sql WHERE handling, and Oracle flag"}
[tool_result]  sqlglot/generator.py         | 13 ++++++++++++-
 sqlglot/generators/oracle.py |  1 +
 sqlglot/parser.py            |  3 +++
 3 files changed, 16 insertions(+), 1 deletion(-)
[assistant] Quick check of the output before writing tests:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfrom sqlglot.errors import ErrorLevel\nq='MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.a = s.a WHERE s.a > 1 DELETE WHERE s.a < 0 WHEN NOT MATCHED THEN INSERT (id, a) VALUES (s.id, s.a) WHERE s.id > 0'\nprint(sqlglot.transpile(q, read='oracle', write='oracle'))\npr
…[12 chars elided]…
transpile(q, read='oracle', write='oracle', pretty=True)[0])\nprint(sqlglot.transpile(q, read='oracle', write='duckdb', unsupported_level=ErrorLevel.WARN))\nprint(sqlglot.transpile('MERGE INTO t USING s ON t.id = s.id WHEN NOT MATCHED THEN INSERT (id) VALUES (s.id) WHERE s.id > 0', read='oracle', write='snowflake'))\n\" 2>&1", "description": "Sanity-check Oracle round-trip and transpile warnings"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.errors import ErrorLevel\nq='MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.a = s.a WHERE s.a > 1 WHEN NOT MATCHED THEN INSERT (id, a) VALUES (s.id, s.a) WHERE s.id > 0'\nprint(sqlglot.transpile(q, read='oracle', write='oracle'))\nprint(sqlglot.transpile(q,
…[45 chars elided]…
0])\nprint(sqlglot.transpile(q, read='oracle', write='duckdb', unsupported_level=ErrorLevel.WARN))\nprint(sqlglot.transpile('MERGE INTO t USING s ON t.id = s.id WHEN NOT MATCHED THEN INSERT (id) VALUES (s.id) WHERE s.id > 0', read='oracle', write='snowflake', unsupported_level=ErrorLevel.RAISE) if False else 'skip')\n\" 2>&1", "description": "Sanity-check Oracle round-trip and transpile warnings"}
[tool_result] WHERE clause in MERGE WHEN MATCHED / NOT MATCHED is not supported
WHERE clause in MERGE WHEN MATCHED / NOT MATCHED is not supported
['MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.a = s.a WHERE s.a > 1 WHEN NOT MATCHED THEN INSERT (id, a) VALUES (s.id, s.a) WHERE s.id > 0']
MERGE INTO t
USING s
ON t.id = s.id
WHEN MATCHED THEN UPDATE SET
  t.a = s.a
WHERE
  s.a > 1
WHEN NOT MATCHED THEN INSERT (id, a) VALUES (s.id, s.a)
WHERE
  s.id > 0
['MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.a = s.a WHEN NOT MATCHED THEN INSERT (id, a) VALUES (s.id, s.a)']
skip
[assistant] Oracle round-trips and the clause is dropped for other targets. Next, tests. Let me check how existing tests assert unsupported warnings.
[tool_use Bash] {"command": "grep -rn \"unsupported_level=ErrorLevel.IGNORE\\|assertLogs\\|expected_unsupported\\|unsupported_level=ErrorLevel.RAISE\" tests/dialects/test_dialect.py | head -8; grep -n \"def validate_all\" -A 25 tests/dialects/test_dialect.py | head -40; sed -n 880,884p tests/dialects/test_oracle.py", "description": "Find unsupported-warning test conventions"}
[tool_result] tests/dialects/test_dialect.py:57:            with self.assertLogs(parser_logger) as cm:
tests/dialects/test_dialect.py:88:                        unsupported_level=ErrorLevel.IGNORE,
tests/dialects/test_dialect.py:99:                        expression.sql(write_dialect, unsupported_level=ErrorLevel.RAISE)
tests/dialects/test_dialect.py:104:                            unsupported_level=ErrorLevel.IGNORE,
tests/dialects/test_dialect.py:5058:                with self.assertLogs(generator_logger, l
…[893 chars elided]…
alect,
88-                        unsupported_level=ErrorLevel.IGNORE,
89-                        pretty=pretty,
90-                        identify=identify,
91-                    ),
92-                    sql,
93-                )
        self.validate_identity("UTC_TIME(6)").assert_is(exp.UtcTime)
        self.validate_identity("UTC_TIMESTAMP()").assert_is(exp.UtcTimestamp)
        self.validate_identity("UTC_TIMESTAMP(6)").assert_is(exp.UtcTimestamp)

    def test_merge_builder_alias(self):
[tool_use Bash] {"command": "sed -n 5050,5070p tests/dialects/test_dialect.py; grep -n \"^from\\|^import\" tests/dialects/test_oracle.py; grep -n \"def test_merge\" tests/dialects/test_oracle.py; grep -n \"MERGE\" tests/dialects/test_dialect.py | sed -n 1,3p", "description": "Look at assertLogs usage and oracle test imports"}
[tool_result]             "INITCAP(col, (SELECT delimiter FROM settings LIMIT 1))",
            includes=("SELECT delimiter FROM settings", "REPLACE("),
        )

    def test_initcap_custom_delimiter_warning(self):
        expression = parse_one("INITCAP(col, '_')", read="bigquery")
        for dialect in ("postgres", "presto"):
            with self.subTest(f"INITCAP unsupported custom delimiters warning for {dialect}"):
                with self.assertLogs(generator_logger, level="WARNING") as cm:
       
…[745 chars elided]…
tests.dialects.test_dialect import Validator
3:from sqlglot.optimizer.qualify import qualify
884:    def test_merge_builder_alias(self):
3043:            MERGE INTO target USING source ON target.id = source.id
3047:                "bigquery": "MERGE INTO target USING source ON target.id = source.id WHEN NOT MATCHED THEN INSERT (id) VALUES (source.id)",
3048:                "snowflake": "MERGE INTO target USING source ON target.id = source.id WHEN NOT MATCHED THEN INSERT (id) VALUES (source.id)",
[tool_use Bash] {"command": "grep -n \"generator_logger\" tests/dialects/test_dialect.py | head -2; grep -n \"^from\\|^import\" tests/dialects/test_dialect.py | head -20", "description": "Find generator logger import used by tests"}
[tool_result] 17:from sqlglot.generator import logger as generator_logger
5058:                with self.assertLogs(generator_logger, level="WARNING") as cm:
1:import typing as t
2:import unittest
5:from sqlglot import (
15:from sqlglot.dialects import BigQuery, Hive, Snowflake, Spark2
16:from sqlglot.dialects.duckdb import WS_CONTROL_CHARS_TO_DUCK
17:from sqlglot.generator import logger as generator_logger
18:from sqlglot.parser import logger as parser_logger
19:from sqlglot.parsers.snowflake import SnowflakeParser
20:from collections.abc import Iterable
21:import sqlglot.parsers.base as _base_module
[tool_use Bash] {"command": "/Usersuser=0 2>/dev/null; python3 - <<'EOF'\np=\"tests/dialects/test_oracle.py\"\ns=open(p).read()\ns=s.replace(\"from sqlglot.optimizer.qualify import qualify\\n\",\"from sqlglot.generator import logger as generator_logger\\nfrom sqlglot.optimizer.qualify import qualify\\n\",1)\nanchor=\"    def test_pseudocolumns(self):\\n\"\nassert s.count(anchor)==1\nnew='''    def test_merge_w
…[830 chars elided]…
In(\"WHERE clause in MERGE WHEN MATCHED / NOT MATCHED is not supported\", cm.output[0])\n\n'''\ns=s.replace(anchor,new+anchor,1)\nopen(p,\"w\").write(s)\nEOF\n<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py -k merge 2>&1 | tail -15", "description": "Add Oracle MERGE WHERE tests and run merge tests"}
[tool_result] ..                                                                       [100%]
2 passed, 22 deselected in 0.15s
[assistant] Merge tests pass. Running the full suite with the project's check command:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite"}
[tool_result] ................................................................................. [  7%]
................................ [ 10%]
................................................................................................................................... [ 22%]
..................................................... [ 27%]
................ [ 28%]
.................................................................................................... [ 38%]
.......................................
…[242 chars elided]…
................ [ 64%]
........................................................................................................................................................................................................................................................................................................................................ [ 94%]
....................... [ 96%]
....................................                      [100%]
1081 passed, 17834 subtests passed in 52.60s
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot tests/dialects/test_oracle.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot tests/dialects/test_oracle.py) 2>&1 | tail -5; git diff", "description": "Run ruff lint and format check and show diff"}
[tool_result] All checks passed!
Would reformat: tests/dialects/test_oracle.py
1 file would be reformatted, 173 files already formatted
diff --git a/sqlglot/generator.py b/sqlglot/generator.py
index d9f08c480..0ee9c6358 100644
--- a/sqlglot/generator.py
+++ b/sqlglot/generator.py
@@ -320,6 +320,9 @@ class Generator:
     # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed
     MATCHED_BY_SOURCE = True
 
+    # Whether MERGE ... WHEN [NOT] MATCHED THEN UPDATE / INSERT ... WHERE <condition> is allowed
+    SU
…[4023 chars elided]…
       self.assertEqual(
+                expression.sql("duckdb"),
+                "MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.a = s.a WHEN NOT MATCHED THEN INSERT (id, a) VALUES (s.id, s.a)",
+            )
+        self.assertIn("WHERE clause in MERGE WHEN MATCHED / NOT MATCHED is not supported", cm.output[0])
+
     def test_pseudocolumns(self):
         ast = self.validate_identity(
             "WITH t AS (SELECT 1 AS COL) SELECT col, ROWID FROM t WHERE ROWNUM = 1"
[assistant] Lint passes; the test file needs formatting. Applying the formatter and re-running the affected tests:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff format tests/dialects/test_oracle.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot tests/dialects/test_oracle.py && git diff --stat && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py tests/dialects/test_dialect.py 2>&1 | tail -2", "description": "Format test file and rerun Oracle and dialect tests"}
[tool_result] 1 file reformatted
174 files already formatted
 sqlglot/generator.py          | 13 ++++++++++++-
 sqlglot/generators/oracle.py  |  1 +
 sqlglot/parser.py             |  3 +++
 tests/dialects/test_oracle.py | 19 +++++++++++++++++++
 4 files changed, 35 insertions(+), 1 deletion(-)
................                    [100%]
122 passed, 3027 subtests passed in 0.56s
[assistant] Oracle `MERGE` now accepts a `WHERE` on both the `UPDATE` and `INSERT` branches, round-trips it, and drops it with an unsupported warning when transpiling elsewhere. The full suite passed (1081 tests) before the final formatting pass; I re-ran the Oracle and dialect test files after it. Ruff lint and format are clean. I did not commit.

The changes:

- **Parser** (`sqlglot/parser.py`, `_parse_when_matched`): after an `INSERT` or `UPDATE` branch, parse an optional `WHERE` into the existing `where` arg on `Insert`/`Update`. This is in the base parser, since no other dialect's syntax conflicts wi
…[109 chars elided]…
 sets `SUPPORTS_MERGE_WHEN_WHERE`. Otherwise it calls `self.unsupported(...)` and drops the clause. The flag defaults to `False`.
- **Oracle** (`sqlglot/generators/oracle.py`): sets `SUPPORTS_MERGE_WHEN_WHERE = True`.
- **Tests** (`tests/dialects/test_oracle.py`): a new `test_merge_when_where` checks the Oracle round-trip and checks that DuckDB output drops the clause and logs the warning.

Decision for you: I gave the flag a default of `False`, so every non-Oracle dialect warns and drops the clause. If any other dialect supports this syntax, set its flag to `True` in that dialect's generator.
