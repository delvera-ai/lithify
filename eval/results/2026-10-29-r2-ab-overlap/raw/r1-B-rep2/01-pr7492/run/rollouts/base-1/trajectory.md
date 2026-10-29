# trajectory base-1

final message:
Oracle now parses and round-trips the optional `WHERE` on the `UPDATE` and `INSERT` branches of a `MERGE`. Transpiling to a dialect without support emits an unsupported warning and drops the clause. The full suite passes (1081 tests), and ruff check and format are clean.

Changes:

- **Parser** (`sqlglot/parser.py`, `_parse_when_matched`): after an `INSERT` or `UPDATE` branch, parse an optional `WHERE` onto that node's existing `where` arg. The parse happens in the shared parser, so it is not Oracle-only. Other dialects can read the syntax, and the generator decides what to emit.
- **Generator** (`sqlglot/generator.py`): new flag `MERGE_WHEN_WHERE_SUPPORTED`, default `False`. `when_sql` emits the `WHERE` when the flag is set. Otherwise it calls `self.unsupported(...)` and drops the clause.
- **Oracle** (`sqlglot/generators/oracle.py`): sets `MERGE_WHEN_WHERE_SUPPORTED = True`.
- **Tests** (`tests/dialects/test_oracle.py`): `test_merge_when_where` checks the Oracle round-trip, and checks that transpiling to DuckDB drops the clause and logs the warning.

Decisions for you to review:

- **Default is `False`.** The base dialect and any dialect that doesn't opt in will drop the clause on output, including `parse_one(oracle_sql).sql()` with no dialect. I chose this because the spec says non-supporting dialects should drop it. If you would rather the base default keep it, flip the default and set the flag to `False` in the dialects that reject it.
- **The `WHERE` is stored in the existing `where` arg on `Insert` and `Update`.** On `Insert` that arg already means Databricks' `REPLACE WHERE`. The two uses don't collide, because the MERGE branch is generated only by `when_sql`. But anyone reading the AST should know the same arg name carries two meanings.
- **The `DELETE WHERE` tail is not handled.** Oracle also allows `UPDATE SET ... WHERE ... DELETE WHERE ...`. That was outside the request, so it is still unparsed.

## events
[tool_use Bash] {"command": "grep -n \"MERGE\\|Merge\\|whens\\|When(\" sqlglot/dialects/oracle.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -80; grep -rn \"class When\" -A12 sqlglot/expressions.py", "description": "Locate MERGE and When handling code"}
[tool_result ERROR] Exit code 2
ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:320:    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed
sqlglot/generator.py:700:        exp.MergeBlockRatioProperty: exp.Properties.Location.POST_NAME,
sqlglot/generator.py:744:        exp.MergeTreeTTL: exp.Properties.Location.POST_SCHEMA,
sqlglot/generator.py:2032:    def mergeblockratioproperty_sql(self, expression: exp.MergeBlockRatioProperty) -> str:
sqlglot/generator.py:2034:           
…[2108 chars elided]…
erge(self) -> exp.Merge:
sqlglot/parser.py:8895:            exp.Merge(
sqlglot/parser.py:8900:                whens=self._parse_when_matched(),
sqlglot/parser.py:8906:        whens = []
sqlglot/parser.py:8949:            whens.append(
sqlglot/parser.py:8951:                    exp.When(matched=matched, source=source, condition=condition, then=then)
sqlglot/parser.py:8954:        return self.expression(exp.Whens(expressions=whens))
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "sed -n 8884,8960p sqlglot/parser.py; ls sqlglot | head -50; grep -rn \"class When(\" -A14 sqlglot/expressions/*.py; grep -n \"def whens_sql\" -A3 sqlglot/generator.py; sed -n 4466,4500p sqlglot/generator.py", "description": "Read merge parser, When expression, generator"}
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
…[4188 chars elided]…
on")
        on = f"ON {on}" if on else ""

        if not on:
            on = self.expressions(expression, key="using_cond")
            on = f"USING ({on})" if on else ""

        returning = self.sql(expression, "returning")
        if returning:
            whens = f"{whens}{returning}"

        sep = self.sep()

        return self.prepend_ctes(
            expression,
            f"MERGE INTO {this}{table_alias}{sep}{using}{sep}{on}{sep}{whens}",
        )

    @unsupported_args("format")
[tool_use Bash] {"command": "grep -n \"class Update(\\|class Insert(\" -A22 sqlglot/expressions/dml.py | head -70; sed -n 312,330p sqlglot/generator.py; grep -n \"def update_sql\\|def insert_sql\" -A30 sqlglot/generator.py | head -90; grep -rn \"MERGE\" tests/dialects/test_oracle.py | head; git log --oneline -1", "description": "Inspect Update/Insert expression and generator code"}
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
…[4692 chars elided]…
AP_DERIVED_VALUES
2493-                and (alias or isinstance(expression.parent, (exp.From, exp.Table)))
2494-                else values
2495-            )
tests/dialects/test_oracle.py:895:            "MERGE INTO my_table USING (SELECT * FROM something) source_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1 WHEN NOT MATCHED THEN INSERT (my_table.id, my_table.col1) VALUES (source_table.id, source_table.col1)",
08f2107b5 lithify: probe base
[tool_use Bash] {"command": "grep -n \"def when_sql\" -A40 sqlglot/generator.py; grep -n \"unsupported(\" sqlglot/generator.py | head -5; grep -n \"def merge\\|MERGE\" sqlglot/dialects/oracle.py; grep -n \"Merge\\|WHEN\" tests/dialects/test_oracle.py | head -20", "description": "Read when_sql generator and oracle merge handling"}
[tool_result] 4443:    def when_sql(self, expression: exp.When) -> str:
4444-        matched = "MATCHED" if expression.args["matched"] else "NOT MATCHED"
4445-        source = " BY SOURCE" if self.MATCHED_BY_SOURCE and expression.args.get("source") else ""
4446-        condition = self.sql(expression, "condition")
4447-        condition = f" AND {condition}" if condition else ""
4448-
4449-        then_expression = expression.args.get("then")
4450-        if isinstance(then_expression, exp.Insert):
4451-     
…[2614 chars elided]…
HEN INTO emp4 "
886:            "WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1",
887:            "WHEN NOT MATCHED THEN INSERT (my_table.id, my_table.col1) VALUES (source_table.id, source_table.col1)",
895:            "MERGE INTO my_table USING (SELECT * FROM something) source_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1 WHEN NOT MATCHED THEN INSERT (my_table.id, my_table.col1) VALUES (source_table.id, source_table.col1)",
[tool_use Bash] {"command": "grep -n \"^    [A-Z_]* = \" sqlglot/generator.py | head -80; grep -n \"class Generator\" -A12 sqlglot/dialects/oracle.py; grep -n \"def _parse_where\\b\" -A6 sqlglot/parser.py; grep -rn \"MATCHED_BY_SOURCE\" sqlglot | head", "description": "List generator flags and where parsing helper"}
[tool_result] 21:    G = t.TypeVar("G", bound="Generator")
302:    IGNORE_NULLS_IN_FUNC = False
306:    IGNORE_NULLS_BEFORE_ORDER = True
309:    LOCKING_READS_SUPPORTED = False
312:    EXCEPT_INTERSECT_SUPPORT_ALL_CLAUSE = True
315:    WRAP_DERIVED_VALUES = True
318:    CREATE_FUNCTION_RETURN_AS = True
321:    MATCHED_BY_SOURCE = True
324:    SINGLE_STRING_INTERVAL = False
327:    INTERVAL_ALLOWS_PLURAL_FORM = True
330:    LIMIT_FETCH = "ALL"
333:    LIMIT_ONLY_LITERALS = False
336:    RENAME_TABLE_WITH_DB = 
…[2603 chars elided]…
None:
5184-        if not skip_where_token and not self._match(TokenType.WHERE):
5185-            return None
5186-
5187-        comments = self._prev_comments
5188-        return self.expression(
5189-            exp.Where(this=self._parse_disjunction()),
sqlglot/generator.py:321:    MATCHED_BY_SOURCE = True
sqlglot/generator.py:4445:        source = " BY SOURCE" if self.MATCHED_BY_SOURCE and expression.args.get("source") else ""
sqlglot/generators/snowflake.py:378:    MATCHED_BY_SOURCE = False
[tool_use Bash] {"command": "ls sqlglot/generators | head -50; grep -n \"class Generator\" -A25 sqlglot/generators/oracle.py | head -40; sed -n 560,575p sqlglot/generator.py", "description": "Locate Oracle generator class and flag block end"}
[tool_result] __init__.py
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

    # Whether exp.ArraySize should generate the dimension arg too (valid for Postgres & DuckDB)
    # None -> Doesn't support it at all
    # Fals
…[46 chars elided]…
, but preferably generated without
    # True (Postgres) -> Explicitly requires it
    ARRAY_SIZE_DIM_REQUIRED: bool | None = None

    # Whether a multi-argument DECODE(...) function is supported. If not, a CASE expression is generated
    SUPPORTS_DECODE_CASE = True

    # Whether SYMMETRIC and ASYMMETRIC flags are supported with BETWEEN expression
    SUPPORTS_BETWEEN_FLAGS = False

    # Whether LIKE and ILIKE support quantifiers such as LIKE ANY/ALL/SOME
    SUPPORTS_LIKE_QUANTIFIERS = True
[tool_use Bash] {"command": "grep -n \"class Generator\" -A30 sqlglot/generators/oracle.py | head -45; sed -n 576,600p sqlglot/generator.py", "description": "Read Oracle generator class header and flag section"}
[tool_result]     # Prefix which is appended to exp.Table expressions in MATCH AGAINST
    MATCH_AGAINST_TABLE_PREFIX: str | None = None

    # Whether to include the VARIABLE keyword for SET assignments
    SET_ASSIGNMENT_REQUIRES_VARIABLE_KEYWORD = False

    # The keyword to use for default value assignment in DECLARE statements
    DECLARE_DEFAULT_ASSIGNMENT = "="

    # Whether FROM is supported in UPDATE statements or if joins must be generated instead, e.g:
    # Supported (Postgres, Doris etc): UPDATE
…[110 chars elided]…
    UPDATE_STATEMENT_SUPPORTS_FROM = True

    # Whether SELECT *, ... EXCLUDE requires wrapping in a subquery for transpilation.
    STAR_EXCLUDE_REQUIRES_DERIVED_TABLE = True

    # Whether DROP and ALTER statements against Iceberg tables include 'ICEBERG', e.g.:
    # - Snowflake: DROP ICEBERG TABLE a.b;
    # - DuckDB:    DROP TABLE a.b;
    SUPPORTS_DROP_ALTER_ICEBERG_PROPERTY = True

    TYPE_MAPPING: t.ClassVar = {
        exp.DType.DATETIME2: "TIMESTAMP",
        exp.DType.NCHAR: "CHAR",
[tool_use Bash] {"command": "grep -n \"^class \\|^    class \\|^from\\|^import\" sqlglot/generators/oracle.py sqlglot/dialects/oracle.py | head -30; grep -n \"UPDATE_STATEMENT_SUPPORTS_FROM\" -r sqlglot | head", "description": "Find Oracle generator class definition"}
[tool_result] sqlglot/generators/oracle.py:1:from __future__ import annotations
sqlglot/generators/oracle.py:4:from sqlglot import exp, generator, transforms
sqlglot/generators/oracle.py:5:from sqlglot.dialects.dialect import (
sqlglot/generators/oracle.py:23:class OracleGenerator(generator.Generator):
sqlglot/dialects/oracle.py:1:from __future__ import annotations
sqlglot/dialects/oracle.py:3:import typing as t
sqlglot/dialects/oracle.py:5:from sqlglot import exp, tokens
sqlglot/dialects/oracle.py:6:from sql
…[298 chars elided]…
acle(Dialect):
sqlglot/dialects/oracle.py:59:    class Tokenizer(tokens.Tokenizer):
sqlglot/generator.py:588:    UPDATE_STATEMENT_SUPPORTS_FROM = True
sqlglot/generator.py:2440:        if self.UPDATE_STATEMENT_SUPPORTS_FROM or not (from_expr := expression.args.get("from_")):
sqlglot/generators/doris.py:28:    UPDATE_STATEMENT_SUPPORTS_FROM = True
sqlglot/generators/mysql.py:136:    UPDATE_STATEMENT_SUPPORTS_FROM = False
sqlglot/generators/starrocks.py:60:    UPDATE_STATEMENT_SUPPORTS_FROM = True
[tool_use Bash] {"command": "sed -n 20,40p sqlglot/generators/oracle.py && sed -n 580,590p sqlglot/generator.py && grep -n \"^    UPDATE_STATEMENT\\|^    MATCHED\" -B3 sqlglot/generator.py | head", "description": "Check Oracle generator class start and flag context"}
[tool_result]     return trim_sql(self, expression)


class OracleGenerator(generator.Generator):
    SELECT_KINDS: tuple[str, ...] = ()
    TRY_SUPPORTED = False
    SUPPORTS_UESCAPE = False
    LOCKING_READS_SUPPORTED = True
    JOIN_HINTS = False
    TABLE_HINTS = False
    DATA_TYPE_SPECIFIERS_ALLOWED = True
    ALTER_TABLE_INCLUDE_COLUMN_KEYWORD = False
    LIMIT_FETCH = "FETCH"
    TABLESAMPLE_KEYWORDS = "SAMPLE"
    LAST_DAY_SUPPORTS_DATE_PART = False
    SUPPORTS_SELECT_INTO = True
    TZ_TO_WITH_TIME
…[609 chars elided]…
ires wrapping in a subquery for transpilation.
318-    CREATE_FUNCTION_RETURN_AS = True
319-
320-    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed
321:    MATCHED_BY_SOURCE = True
--
585-    # Whether FROM is supported in UPDATE statements or if joins must be generated instead, e.g:
586-    # Supported (Postgres, Doris etc): UPDATE t1 SET t1.a = t2.b FROM t2
587-    # Unsupported (MySQL, SingleStore): UPDATE t1 JOIN t2 ON TRUE SET t1.a = t2.b
588:    UPDATE_STATEMENT_SUPPORTS_FROM = True
[assistant] Now the edits: parser, generator flag and `when_sql`, and the Oracle opt-in.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-111417-oracle-dialect-support-the-optio/base-1/sqlglot/parser.py", "old_string": "            elif self._match(TokenType.DELETE):\n                then = self.expression(exp.Var(this=self._prev.text))\n            else:\n                then = self._parse_var_from_options(self.CONFLICT_ACTIONS)\n\n  
…[5 chars elided]…
     whens.append(", "new_string": "            elif self._match(TokenType.DELETE):\n                then = self.expression(exp.Var(this=self._prev.text))\n            else:\n                then = self._parse_var_from_options(self.CONFLICT_ACTIONS)\n\n            if isinstance(then, (exp.Insert, exp.Update)):\n                then.set(\"where\", self._parse_where())\n\n            whens.append("}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-111417-oracle-dialect-support-the-optio/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-111417-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed\n    MATCHED_BY_SOURCE = True\n", "new_string": "    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed\n    MATCHED_BY_SOURCE = True\n\n    # Whether the WHERE clause of a MERGE's WHEN [NOT] MATCHED ... UPDATE / INSERT branch is allowed\n    MERGE_WHEN_WHERE_SUPPORTED = False\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-111417-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-111417-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "        then_expression = expression.args.get(\"then\")\n        if isinstance(then_expression, exp.Insert):", "new_string": "        then_expression = expression.args.get(\"then\")\n        where = \"\"\n        if 
…[15 chars elided]…
_expression, (exp.Insert, exp.Update)) and then_expression.args.get(\n            \"where\"\n        ):\n            if self.MERGE_WHEN_WHERE_SUPPORTED:\n                where = f\" {self.sql(then_expression, 'where')}\"\n            else:\n                self.unsupported(\"MERGE ... WHEN ... THEN UPDATE/INSERT ... WHERE is not supported\")\n\n        if isinstance(then_expression, exp.Insert):"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-111417-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-111417-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "        return f\"WHEN {matched}{source}{condition} THEN {then}\"", "new_string": "        return f\"WHEN {matched}{source}{condition} THEN {then}{where}\""}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-111417-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-111417-oracle-dialect-support-the-optio/base-1/sqlglot/generators/oracle.py", "old_string": "    SUPPORTS_DECODE_CASE = True\n", "new_string": "    SUPPORTS_DECODE_CASE = True\n    MERGE_WHEN_WHERE_SUPPORTED = True\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-111417-oracle-dialect-support-the-optio/base-1/sqlglot/generators/oracle.py has been updated successfully.
[assistant] Now the tests. Let me look at the existing MERGE test and how unsupported warnings are asserted.
[tool_use Bash] {"command": "sed -n 880,905p tests/dialects/test_oracle.py; grep -rn \"assertLogs\" tests/dialects/*.py | head -3; grep -n \"unsupported_level\" tests/dialects/test_dialect.py | head -3", "description": "View existing Oracle MERGE test and warning test patterns"}
[tool_result]         self.validate_identity("UTC_TIME(6)").assert_is(exp.UtcTime)
        self.validate_identity("UTC_TIMESTAMP()").assert_is(exp.UtcTimestamp)
        self.validate_identity("UTC_TIMESTAMP(6)").assert_is(exp.UtcTimestamp)

    def test_merge_builder_alias(self):
        merge_stmt = exp.merge(
            "WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1",
            "WHEN NOT MATCHED THEN INSERT (my_table.id, my_table.col1) VALUES (source_table.id, source_table.col1)",
      
…[850 chars elided]…
column))
tests/dialects/test_clickhouse.py:1729:        with self.assertLogs(helper_logger) as cm:
tests/dialects/test_bigquery.py:2130:        with self.assertLogs(helper_logger) as cm:
tests/dialects/test_bigquery.py:2139:        with self.assertLogs(helper_logger) as cm:
88:                        unsupported_level=ErrorLevel.IGNORE,
99:                        expression.sql(write_dialect, unsupported_level=ErrorLevel.RAISE)
104:                            unsupported_level=ErrorLevel.IGNORE,
[tool_use Bash] {"command": "sed -n 2125,2145p tests/dialects/test_bigquery.py; grep -n \"helper_logger\" tests/dialects/test_bigquery.py | head -2; grep -n \"^from\\|^import\\|logger\" tests/dialects/test_oracle.py | head", "description": "Check warning-assert test pattern and imports"}
[tool_result]         with self.assertRaises(ParseError):
            transpile("DATE_ADD(x, day)", read="bigquery")

    def test_warnings(self):
        with self.assertLogs(helper_logger) as cm:
            self.validate_identity(
                "WITH cte(c) AS (SELECT * FROM t) SELECT * FROM cte",
                "WITH cte AS (SELECT * FROM t) SELECT * FROM cte",
            )

            self.assertIn("Can't push down CTE column names for star queries.", cm.output[0])
            self.assertIn("Named c
…[122 chars elided]…
elf.validate_identity(
                "SELECT * FROM t AS t(c1, c2)",
                "SELECT * FROM t AS t",
            )

            self.assertIn("Named columns are not supported in table alias.", cm.output[0])
15:from sqlglot.helper import logger as helper_logger
2130:        with self.assertLogs(helper_logger) as cm:
1:from sqlglot import exp, UnsupportedError, ParseError, parse, parse_one
2:from tests.dialects.test_dialect import Validator
3:from sqlglot.optimizer.qualify import qualify
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-111417-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py", "old_string": "    def test_pseudocolumns(self):", "new_string": "    def test_merge_when_where(self):\n        sql = \"MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.a = s.a WHERE s.a > 0 WHEN NOT MATC
…[124 chars elided]…
ertLogs(helper_logger) as cm:\n            self.assertEqual(\n                parse_one(sql, read=\"oracle\").sql(\"duckdb\"),\n                \"MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.a = s.a WHEN NOT MATCHED THEN INSERT (t.id, t.a) VALUES (s.id, s.a)\",\n            )\n            self.assertIn(\"is not supported\", cm.output[0])\n\n    def test_pseudocolumns(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-111417-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-111417-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py", "old_string": "from sqlglot.optimizer.qualify import qualify\n", "new_string": "from sqlglot.helper import logger as helper_logger\nfrom sqlglot.optimizer.qualify import qualify\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-111417-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py -k merge 2>&1 | tail -30", "description": "Run Oracle merge tests"}
[tool_result] .F                                                                       [100%]
=================================== FAILURES ===================================
_______________________ TestOracle.test_merge_when_where _______________________

self = <tests.dialects.test_oracle.TestOracle testMethod=test_merge_when_where>

    def test_merge_when_where(self):
        sql = "MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.a = s.a WHERE s.a > 0 WHEN NOT MATCHED THEN INSERT (t.id,
…[650 chars elided]…
id = s.id WHEN MATCHED THEN UPDATE SET t.a = s.a  WHERE s.a > 0 WHEN NOT MATCHED THEN INSERT (t.id, t.a) VALUES (s.id, s.a)  WHERE s.a > 0
E   ?                                                                           +                                                                          +
=========================== short test summary info ============================
FAILED tests/dialects/test_oracle.py::TestOracle::test_merge_when_where - Ass...
1 failed, 1 passed, 22 deselected in 0.36s
[assistant] The `Where` node already emits its own leading space, so I'll drop my extra one.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-111417-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "                where = f\" {self.sql(then_expression, 'where')}\"", "new_string": "                where = self.sql(then_expression, \"where\")"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-111417-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py -k merge 2>&1 | tail -15; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8", "description": "Run merge tests then full test suite"}
[tool_result] ..                                                                       [100%]
2 passed, 22 deselected in 0.10s
.................................................................................................... [ 38%]
................................................................ [ 44%]
............................................................................................................. [ 54%]
..........................................................................................
…[2 chars elided]…
................ [ 64%]
........................................................................................................................................................................................................................................................................................................................................ [ 94%]
....................... [ 96%]
....................................                      [100%]
1081 passed, 17834 subtests passed in 55.13s
[assistant] Full suite passes (1081 tests). Let me run the linter on the changed files.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff --version && <work>/env-sqlglot/bin/python -m ruff check sqlglot/parser.py sqlglot/generator.py sqlglot/generators/oracle.py tests/dialects/test_oracle.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parser.py sqlglot/generator.py sqlglot/generators/oracle.py tests/dialects/test_oracle.py) 2>&1 | tail -10; git status --short", "description": "Lint and format-check changed files"}
[tool_result] ruff 0.15.6
All checks passed!
4 files already formatted
 M sqlglot/generator.py
 M sqlglot/generators/oracle.py
 M sqlglot/parser.py
 M tests/dialects/test_oracle.py
[assistant] Oracle now parses and round-trips the optional `WHERE` on the `UPDATE` and `INSERT` branches of a `MERGE`. Transpiling to a dialect without support emits an unsupported warning and drops the clause. The full suite passes (1081 tests), and ruff check and format are clean.

Changes:

- **Parser** (`sqlglot/parser.py`, `_parse_when_matched`): after an `INSERT` or `UPDATE` branch, parse an optional `WHERE` onto that node's existing `where` arg. The parse happens in the shared parser, so it is not Oracle-only. Other dialects can read the syntax, and the generator decides what to emit.
- **Generator
…[740 chars elided]…
. If you would rather the base default keep it, flip the default and set the flag to `False` in the dialects that reject it.
- **The `WHERE` is stored in the existing `where` arg on `Insert` and `Update`.** On `Insert` that arg already means Databricks' `REPLACE WHERE`. The two uses don't collide, because the MERGE branch is generated only by `when_sql`. But anyone reading the AST should know the same arg name carries two meanings.
- **The `DELETE WHERE` tail is not handled.** Oracle also allows `UPDATE SET ... WHERE ... DELETE WHERE ...`. That was outside the request, so it is still unparsed.
