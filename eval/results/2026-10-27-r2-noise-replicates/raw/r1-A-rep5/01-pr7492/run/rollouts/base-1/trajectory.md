# trajectory base-1

final message:
Oracle now parses and round-trips the `WHERE` clause on both the `UPDATE` and `INSERT ... VALUES` branches of `MERGE`. On other dialects the clause is dropped with an unsupported warning. The full suite passes (1081 tests) and ruff lint and format are clean. I left the changes uncommitted.

Changes:
- **`sqlglot/parser.py`**: `_parse_when_matched` reads an optional `WHERE` after the `UPDATE SET ...` and `INSERT ... VALUES ...` branches. The parser is shared, so the syntax parses in every dialect; only generation is gated.
- **`sqlglot/generator.py`**: new flag `MERGE_WHERE_SUPPORTED`, default `False`. `when_sql` emits the clause when the flag is set, otherwise it calls `self.unsupported(...)` and drops it.
- **`sqlglot/generators/oracle.py`**: sets `MERGE_WHERE_SUPPORTED = True`.
- **`tests/dialects/test_oracle.py`**: new `test_merge_where` covering the Oracle round-trip, the error when transpiling to Postgres with the default unsupported level, and the clause being dropped from the Postgres output.

Decisions to check:
- The default is `False`, so the base `sqlglot` dialect and every non-Oracle dialect will warn if they see the clause. If you want the base dialect to round-trip silently, flip the default to `True` and set it to `False` in each dialect that lacks support.
- The `INSERT *` branch does not take a `WHERE`. The spec only mentioned `VALUES`, so I left it alone.

## events
[tool_use Bash] {"command": "grep -n \"Merge\\|merge\" sqlglot/dialects/oracle.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -80; grep -rn \"MERGE\" tests/dialects/test_oracle.py | head -20", "description": "Find MERGE handling across parser, generator, expressions"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:700:        exp.MergeBlockRatioProperty: exp.Properties.Location.POST_NAME,
sqlglot/generator.py:744:        exp.MergeTreeTTL: exp.Properties.Location.POST_SCHEMA,
sqlglot/generator.py:2032:    def mergeblockratioproperty_sql(self, expression: exp.MergeBlockRatioProperty) -> str:
sqlglot/generator.py:3852:    def mergetreettlaction_sql(self, expression: exp.MergeTreeTTLAction) -> str:
sqlglot/generator.py:3863
…[1597 chars elided]…
   return self.expression(exp.MergeBlockRatioProperty(no=no, default=default))
sqlglot/parser.py:8884:    def _parse_merge(self) -> exp.Merge:
sqlglot/parser.py:8895:            exp.Merge(
tests/dialects/test_oracle.py:895:            "MERGE INTO my_table USING (SELECT * FROM something) source_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1 WHEN NOT MATCHED THEN INSERT (my_table.id, my_table.col1) VALUES (source_table.id, source_table.col1)",
[tool_use Bash] {"command": "sed -n 8884,8990p sqlglot/parser.py; echo ----; sed -n 4469,4530p sqlglot/generator.py; echo ----; grep -n \"class Merge\\|class When\" -A 25 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null | head -80", "description": "Read merge parser, generator, and expression definitions"}
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
…[10156 chars elided]…
: False,
sqlglot/expressions/dml.py-514-    }
sqlglot/expressions/dml.py-515-
sqlglot/expressions/dml.py-516-
sqlglot/expressions/dml.py:517:class When(Expression):
sqlglot/expressions/dml.py-518-    arg_types = {"matched": True, "source": False, "condition": False, "then": True}
sqlglot/expressions/dml.py-519-
sqlglot/expressions/dml.py-520-
sqlglot/expressions/dml.py:521:class Whens(Expression):
sqlglot/expressions/dml.py-522-    """Wraps around one or more WHEN [NOT] MATCHED [...] clauses."""
[tool_use Bash] {"command": "grep -n \"class Insert(\\|class Update(\" -A 22 sqlglot/expressions/dml.py | head -60; grep -n \"def when_sql\\|def whens_sql\\|def update_sql\\|def insert_sql\" -A 40 sqlglot/generator.py | head -200", "description": "Inspect Insert/Update expression args and generator methods"}
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
…[7575 chars elided]…
end_ctes(
4496-            expression,
4497-            f"MERGE INTO {this}{table_alias}{sep}{using}{sep}{on}{sep}{whens}",
4498-        )
4499-
4500-    @unsupported_args("format")
4501-    def tochar_sql(self, expression: exp.ToChar) -> str:
4502-        return self.sql(exp.cast(expression.this, exp.DType.TEXT))
4503-
4504-    def tonumber_sql(self, expression: exp.ToNumber) -> str:
4505-        if not self.SUPPORTS_TO_NUMBER:
4506-            self.unsupported("Unsupported TO_NUMBER function")
[tool_use Bash] {"command": "grep -n \"MATCHED\\|MERGE\" sqlglot/dialects/*.py sqlglot/generator.py | grep -v \"MergeTree\\|MergeBlock\" | head -30; grep -n \"^    SUPPORTS_\\w* = \\|^    [A-Z_]*_SUPPORTED = \" sqlglot/generator.py | head -20; grep -n \"class Oracle\" -A3 sqlglot/dialects/oracle.py | head; grep -n \"class Generator\" sqlglot/dialects/oracle.py", "description": "Check existing MERGE and generator feature flag conventions"}
[tool_result] sqlglot/dialects/athena.py:40:        - SELECT, INSERT, UPDATE, DELETE, MERGE
sqlglot/dialects/dialect.py:2043:        # only remove the target table names from certain parts of WHEN MATCHED / WHEN NOT MATCHED
sqlglot/generator.py:320:    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed
sqlglot/generator.py:321:    MATCHED_BY_SOURCE = True
sqlglot/generator.py:2034:            return "NO MERGEBLOCKRATIO"
sqlglot/generator.py:2036:            return "DEFAULT MERGEBLOCKRATIO"
sqlglot/generato
…[961 chars elided]…
_WINDOW_EXCLUDE = False
506:    TRY_SUPPORTED = True
509:    SUPPORTS_UESCAPE = True
530:    SUPPORTS_EXPLODING_PROJECTIONS = True
536:    SUPPORTS_CONVERT_TIMEZONE = False
539:    SUPPORTS_MEDIAN = True
542:    SUPPORTS_UNIX_SECONDS = False
568:    SUPPORTS_DECODE_CASE = True
571:    SUPPORTS_BETWEEN_FLAGS = False
574:    SUPPORTS_LIKE_QUANTIFIERS = True
15:class Oracle(Dialect):
16-    ALIAS_POST_TABLESAMPLE = True
17-    LOCKING_READS_SUPPORTED = True
18-    TABLESAMPLE_SIZE_IS_PERCENT = True
[tool_use Bash] {"command": "grep -n \"Generator\\|^    class \\|^class \" sqlglot/dialects/oracle.py | head -30; sed -n 315,325p sqlglot/generator.py; sed -n 885,900p tests/dialects/test_oracle.py; git status --short | head", "description": "Inspect Oracle generator class and generator flag location"}
[tool_result] 10:from sqlglot.generators.oracle import OracleGenerator
15:class Oracle(Dialect):
59:    class Tokenizer(tokens.Tokenizer):
90:    Generator = OracleGenerator
    WRAP_DERIVED_VALUES = True

    # Whether create function uses an AS before the RETURN
    CREATE_FUNCTION_RETURN_AS = True

    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed
    MATCHED_BY_SOURCE = True

    # Whether the INTERVAL expression works only with values like '1 day'
    SINGLE_STRING_INTERVAL = False

        merge
…[399 chars elided]…
self.assertEqual(
            merge_stmt.sql("oracle"),
            "MERGE INTO my_table USING (SELECT * FROM something) source_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1 WHEN NOT MATCHED THEN INSERT (my_table.id, my_table.col1) VALUES (source_table.id, source_table.col1)",
        )

    def test_pseudocolumns(self):
        ast = self.validate_identity(
            "WITH t AS (SELECT 1 AS COL) SELECT col, ROWID FROM t WHERE ROWNUM = 1"
[tool_use Bash] {"command": "sed -n 1,40p sqlglot/generators/oracle.py; grep -n \"^    [A-Z_]* = \" sqlglot/generators/oracle.py | head -30; grep -n \"MATCHED_BY_SOURCE\" -r sqlglot | head", "description": "Inspect OracleGenerator class flags"}
[tool_result] from __future__ import annotations


from sqlglot import exp, generator, transforms
from sqlglot.dialects.dialect import (
    no_ilike_sql,
    rename_func,
    strposition_sql,
    to_number_with_nls_param,
    trim_sql,
)


def _trim_sql(self: OracleGenerator, expression: exp.Trim) -> str:
    position = expression.args.get("position")

    if position and position.upper() in ("LEADING", "TRAILING"):
        return self.trim_sql(expression)

    return trim_sql(self, expression)


class Oracl
…[988 chars elided]…
SUPPORTS_WINDOW_EXCLUDE = True
38:    QUERY_HINT_SEP = " "
39:    SUPPORTS_DECODE_CASE = True
41:    AFTER_HAVING_MODIFIER_TRANSFORMS = generator.AFTER_HAVING_MODIFIER_TRANSFORMS
43:    TYPE_MAPPING = {
64:    TRANSFORMS = {
105:    PROPERTIES_LOCATION = {
sqlglot/generator.py:321:    MATCHED_BY_SOURCE = True
sqlglot/generator.py:4445:        source = " BY SOURCE" if self.MATCHED_BY_SOURCE and expression.args.get("source") else ""
sqlglot/generators/snowflake.py:378:    MATCHED_BY_SOURCE = False
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-090210-oracle-dialect-support-the-optio/base-1/sqlglot/parser.py", "old_string": "            if self._match(TokenType.INSERT):\n                this = self._parse_star()\n                if this:\n                    then: exp.Expr | None = self.expression(exp.Insert(this=this))\n                els
…[1865 chars elided]…
ere=self._parse_where())\n                    )\n                else:\n                    then = self.expression(\n                        exp.Update(\n                            expressions=self._match(TokenType.SET)\n                            and self._parse_csv(self._parse_equality),\n                            where=self._parse_where(),\n                        )\n                    )"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-090210-oracle-dialect-support-the-optio/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Now the generator: a feature flag, defaulting off, that Oracle turns on, and the `WHERE` emitted or dropped with a warning in `when_sql`.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python - <<'EOF'\nimport re\np=\"sqlglot/generator.py\"\ns=open(p).read()\ns=s.replace(\"\"\"    MATCHED_BY_SOURCE = True\n\"\"\",\"\"\"    MATCHED_BY_SOURCE = True\n\n    # Whether MERGE ... WHEN [NOT] MATCHED THEN UPDATE/INSERT can be followed by a WHERE clause\n    MERGE_WHERE_SUPPORTED = False\n\"\"\",1)\nold=\"\"\
…[806 chars elided]…
 return f\"WHEN {matched}{source}{condition} THEN {then}{where}\"\n\"\"\")\nopen(p,\"w\").write(s)\np=\"sqlglot/generators/oracle.py\"\ns=open(p).read()\ns=s.replace(\"    SUPPORTS_DECODE_CASE = True\\n\",\"    SUPPORTS_DECODE_CASE = True\\n    MERGE_WHERE_SUPPORTED = True\\n\",1)\nopen(p,\"w\").write(s)\nEOF\ngit diff --stat", "description": "Apply generator flag and when_sql changes via script"}
[tool_result]  sqlglot/generator.py         | 14 +++++++++++++-
 sqlglot/generators/oracle.py |  1 +
 sqlglot/parser.py            |  8 ++++++--
 3 files changed, 20 insertions(+), 3 deletions(-)
[tool_use Bash] {"command": "grep -n \"def validate_all\\|def validate_identity\" -A12 tests/dialects/test_dialect.py | head -50; grep -rn \"unsupported_level=ErrorLevel\" tests/dialects/test_oracle.py | head -3", "description": "Check test helper signatures for validate_all and identity"}
[tool_result] 53:    def validate_identity(
54-        self, sql, write_sql=None, pretty=False, check_command_warning=False, identify=False
55-    ):
56-        if check_command_warning:
57-            with self.assertLogs(parser_logger) as cm:
58-                expression = self.parse_one(sql)
59-                assert f"'{sql[:100]}' contains unsupported syntax" in cm.output[0]
60-        else:
61-            expression = self.parse_one(sql)
62-
63-        self.assertEqual(
64-            write_sql or sql,
…[151 chars elided]…
y=False, identify=False):
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
79-            identify (bool): quote identifiers in both read and write
80-        """
[tool_use Bash] {"command": "sed -n 80,100p tests/dialects/test_dialect.py; grep -n \"assertLogs\\|unsupported\" tests/dialects/test_oracle.py | head -5", "description": "Read validate_all body and existing unsupported-test patterns"}
[tool_result]         """
        expression = self.parse_one(sql)

        for read_dialect, read_sql in (read or {}).items():
            with self.subTest(f"{read_dialect} -> {sql}"):
                self.assertEqual(
                    parse_one(read_sql, read_dialect).sql(
                        self.dialect,
                        unsupported_level=ErrorLevel.IGNORE,
                        pretty=pretty,
                        identify=identify,
                    ),
                    sql,
                )

        for write_dialect, write_sql in (write or {}).items():
            with self.subTest(f"{sql} -> {write_dialect}"):
                if write_sql is UnsupportedError:
                    with self.assertRaises(UnsupportedError):
                        expression.sql(write_dialect, unsupported_level=ErrorLevel.RAISE)
                else:
[tool_use Bash] {"command": "sed -n 1,12p tests/dialects/test_oracle.py && <work>/env-sqlglot/bin/python - <<'EOF'\np=\"tests/dialects/test_oracle.py\"\ns=open(p).read()\nanchor=\"\"\"    def test_pseudocolumns(self):\"\"\"\nassert s.count(anchor)==1\nnew='''    def test_merge_where(self):\n        self.validate_identity(\n            \"MERGE INTO my_table USING source_
…[635 chars elided]…
EN UPDATE SET my_table.col1 = source_table.col1 WHERE source_table.col1 IS NOT NULL\",\n                \"postgres\": UnsupportedError,\n            },\n        )\n\n'''\ns=s.replace(anchor,new+anchor,1)\nopen(p,\"w\").write(s)\nEOF\ngrep -n \"UnsupportedError\" tests/dialects/test_oracle.py tests/dialects/test_dialect.py | head -3", "description": "Add Oracle MERGE WHERE tests to test_oracle.py"}
[tool_result] from sqlglot import exp, UnsupportedError, ParseError, parse, parse_one
from tests.dialects.test_dialect import Validator
from sqlglot.optimizer.qualify import qualify


class TestOracle(Validator):
    dialect = "oracle"

    def test_oracle(self):
        self.validate_identity("1 /* /* */", "1 /* / * */")
        self.validate_all(
            "SELECT CONNECT_BY_ROOT x y",
tests/dialects/test_oracle.py:1:from sqlglot import exp, UnsupportedError, ParseError, parse, parse_one
tests/dialects/test_oracle.py:167:                "postgres": UnsupportedError,
tests/dialects/test_oracle.py:168:                "tsql": UnsupportedError,
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python - <<'EOF'\np=\"tests/dialects/test_oracle.py\"\ns=open(p).read()\nold='''                \"postgres\": UnsupportedError,\n            },\n        )\n\n    def test_pseudocolumns(self):'''\nnew='''                \"postgres\": UnsupportedError,\n            },\n        )\n        self.assertEqual(\n            pa
…[590 chars elided]…
t exp, UnsupportedError, ParseError, parse, parse_one\",\"from sqlglot import exp, ErrorLevel, UnsupportedError, ParseError, parse, parse_one\",1)\nopen(p,\"w\").write(s)\nEOF\n<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py -k merge 2>&1 | tail -30", "description": "Run the new Oracle MERGE tests"}
[tool_result] .F                                                                       [100%]
=================================== FAILURES ===================================
_________________________ TestOracle.test_merge_where __________________________

self = <tests.dialects.test_oracle.TestOracle testMethod=test_merge_where>

    def test_merge_where(self):
>       self.validate_identity(
            "MERGE INTO my_table USING source_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SET my_
…[357 chars elided]…
: in validate_identity
    self.assertEqual(
E   AssertionError: 'MERG[126 chars]col1 WHERE source_table.col1 IS NOT NULL WHEN [118 chars] > 0' != 'MERG[126 chars]col1  WHERE NOT source_table.col1 IS NULL WHEN[120 chars] > 0'
E   Diff is 1051 characters long. Set self.maxDiff to None to see it.
=========================== short test summary info ============================
FAILED tests/dialects/test_oracle.py::TestOracle::test_merge_where - Assertio...
1 failed, 1 passed, 22 deselected in 0.29s
[tool_use Bash] {"command": "grep -n \"def where_sql\" -A4 sqlglot/generator.py", "description": "Check where_sql spacing behavior"}
[tool_result] 3224:    def where_sql(self, expression: exp.Where) -> str:
3225-        this = self.indent(self.sql(expression, "this"))
3226-        return f"{self.seg('WHERE')}{self.sep()}{this}"
3227-
3228-    def window_sql(self, expression: exp.Window) -> str:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python - <<'EOF'\np=\"sqlglot/generator.py\"\ns=open(p).read()\ns=s.replace(\"\"\"                where = f\" {self.sql(then_expression, 'where')}\"\n\"\"\",\"\"\"                where = self.sql(then_expression, \"where\")\n\"\"\",1)\nopen(p,\"w\").write(s)\np=\"tests/dialects/test_oracle.py\"\ns=open(p).read()\ns=s.replace(\"WHERE source_table.col1 IS NOT NULL\",\"WHERE source_table.col1 > 0\")\nopen(p,\"w\").write(s)\nEOF\n<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py -k merge 2>&1 | tail -30", "description": "Fix WHERE spacing and rerun Oracle MERGE tests"}
[tool_result]     def test_merge_where(self):
        self.validate_identity(
            "MERGE INTO my_table USING source_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1 WHERE source_table.col1 > 0 WHEN NOT MATCHED THEN INSERT (my_table.id, my_table.col1) VALUES (source_table.id, source_table.col1) WHERE source_table.id > 0"
        )
        self.validate_all(
            "MERGE INTO my_table USING source_table ON my_table.id = source_table.id WHEN MATC
…[1312 chars elided]…
S (source_table.id)
E       ?                                                                                                       +++++++++

tests/dialects/test_oracle.py:909: AssertionError
----------------------------- Captured stdout call -----------------------------
uu
=========================== short test summary info ============================
FAILED tests/dialects/test_oracle.py::TestOracle::test_merge_where - Assertio...
1 failed, 1 passed, 22 deselected, 2 subtests passed in 0.16s
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python - <<'EOF'\np=\"tests/dialects/test_oracle.py\"\ns=open(p).read()\ns=s.replace('''            \"MERGE INTO my_table USING source_table ON my_table.id = source_table.id WHEN NOT MATCHED THEN INSERT (my_table.id) VALUES (source_table.id)\",''','''            \"MERGE INTO my_table USING source_table ON my_table.id =
…[27 chars elided]…
ATCHED THEN INSERT (id) VALUES (source_table.id)\",''')\nopen(p,\"w\").write(s)\nEOF\n<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py -k merge 2>&1 | tail -3; grep -rn \"print(\\\"uu\\|print('uu\\|\\\"uu\\\"\" sqlglot tests | head", "description": "Fix expected output and rerun; locate stray print"}
[tool_result] ..                                                                     [100%]
2 passed, 22 deselected, 2 subtests passed in 0.05s
[assistant] Targeted tests pass. Running the full project suite with the configured command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full project test suite", "timeout": 900000}
[tool_result] ................................................................................. [  7%]
................................ [ 10%]
................................................................................................................................... [ 22%]
..................................................... [ 27%]
................ [ 28%]
.................................................................................................. [ 38%]
.........................................
…[256 chars elided]…
................................................................................ [ 70%]
..................................... [ 74%]
........................................................................................................................................................................................................................... [ 94%]
....................... [ 96%]
......................................                    [100%]
1081 passed, 17836 subtests passed in 47.27s
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot tests/dialects/test_oracle.py 2>&1; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot tests/dialects/test_oracle.py 2>&1) | tail -5; git diff", "description": "Run ruff lint and format checks, show diff"}
[tool_result] All checks passed!
174 files already formatted
diff --git a/sqlglot/generator.py b/sqlglot/generator.py
index d9f08c480..115a34153 100644
--- a/sqlglot/generator.py
+++ b/sqlglot/generator.py
@@ -320,6 +320,9 @@ class Generator:
     # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed
     MATCHED_BY_SOURCE = True
 
+    # Whether MERGE ... WHEN [NOT] MATCHED THEN UPDATE/INSERT can be followed by a WHERE clause
+    MERGE_WHERE_SUPPORTED = False
+
     # Whether the INTERVAL expression works o
…[4776 chars elided]…
D THEN INSERT (my_table.id) VALUES (source_table.id) WHERE source_table.id > 0",
+                read="oracle",
+            ).sql("postgres", unsupported_level=ErrorLevel.IGNORE),
+            "MERGE INTO my_table USING source_table ON my_table.id = source_table.id WHEN NOT MATCHED THEN INSERT (id) VALUES (source_table.id)",
+        )
+
     def test_pseudocolumns(self):
         ast = self.validate_identity(
             "WITH t AS (SELECT 1 AS COL) SELECT col, ROWID FROM t WHERE ROWNUM = 1"
[assistant] Oracle now parses and round-trips the `WHERE` clause on both the `UPDATE` and `INSERT ... VALUES` branches of `MERGE`. On other dialects the clause is dropped with an unsupported warning. The full suite passes (1081 tests) and ruff lint and format are clean. I left the changes uncommitted.

Changes:
- **`sqlglot/parser.py`**: `_parse_when_matched` reads an optional `WHERE` after the `UPDATE SET ...` and `INSERT ... VALUES ...` branches. The parser is shared, so the syntax parses in every dialect; only generation is gated.
- **`sqlglot/generator.py`**: new flag `MERGE_WHERE_SUPPORTED`, default 
…[195 chars elided]…
`tests/dialects/test_oracle.py`**: new `test_merge_where` covering the Oracle round-trip, the error when transpiling to Postgres with the default unsupported level, and the clause being dropped from the Postgres output.

Decisions to check:
- The default is `False`, so the base `sqlglot` dialect and every non-Oracle dialect will warn if they see the clause. If you want the base dialect to round-trip silently, flip the default to `True` and set it to `False` in each dialect that lacks support.
- The `INSERT *` branch does not take a `WHERE`. The spec only mentioned `VALUES`, so I left it alone.
