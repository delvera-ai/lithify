# trajectory base-1

final message:
Oracle now parses and round-trips the optional `WHERE` on both the `UPDATE` and `INSERT` branches of a `MERGE`. Transpiling to a dialect without support emits an unsupported warning and drops the clause. The full suite passes: 1081 tests, run with the project's pytest command.

Changes:

- **Parser** (`sqlglot/parser.py`, `_parse_when_matched`): after the `UPDATE SET` list and after the non-star `INSERT ... VALUES` list, an optional `WHERE <condition>` is stored on the existing `where` arg of `exp.Update` / `exp.Insert`. This is in the shared parser, so other dialects also accept the syntax.
- **Generator** (`sqlglot/generator.py`, `when_sql`): a new flag `SUPPORTS_MERGE_WHEN_WHERE`, defaulting to `False`. When the clause is present and the flag is off, the generator calls `self.unsupported(...)` and omits the clause. This is the "warn and drop" path.
- **Oracle** (`sqlglot/generators/oracle.py`): sets `SUPPORTS_MERGE_WHEN_WHERE = True`.
- **Tests** (`tests/dialects/test_oracle.py`, new `test_merge_when_where`): round-trip identity in Oracle, the Postgres output with the clause dropped, and a `RAISE` check that `UnsupportedError` is raised.

Choices I made:
- I defaulted the flag to off rather than on. Only Oracle supports this, so the base generator and every other dialect warn and drop it.
- I left `DELETE ... WHERE` alone because the request only covered UPDATE and INSERT.
- I left the `INSERT *` / `UPDATE *` forms without a WHERE, since Oracle has no such syntax.

Something I noticed but did not change: Postgres output strips table qualifiers from `MERGE` SET and INSERT column lists (`SET t.col = ...` becomes `SET col = ...`). This happens with or without the new clause, so it's existing behavior and I left it out of scope.

I did not run mypy, and nothing is committed.

## events
[tool_use Bash] {"command": "git status --short | head && grep -n \"Merge\\|merge\" sqlglot/dialects/oracle.py sqlglot/generator.py sqlglot/parser.py sqlglot/expressions.py | head -80", "description": "Find MERGE handling across the codebase"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:700:        exp.MergeBlockRatioProperty: exp.Properties.Location.POST_NAME,
sqlglot/generator.py:744:        exp.MergeTreeTTL: exp.Properties.Location.POST_SCHEMA,
sqlglot/generator.py:2032:    def mergeblockratioproperty_sql(self, expression: exp.MergeBlockRatioProperty) -> str:
sqlglot/generator.py:3852:    def mergetreettlaction_sql(self, expression: exp.MergeTreeTTLAction) -> str:
sqlglot/generator.py:3863
…[1285 chars elided]…
ion(this=this, to_volume=self._parse_string())
sqlglot/parser.py:2219:            exp.MergeTreeTTL(
sqlglot/parser.py:3037:    def _parse_mergeblockratio(
sqlglot/parser.py:3039:    ) -> exp.MergeBlockRatioProperty:
sqlglot/parser.py:3042:                exp.MergeBlockRatioProperty(
sqlglot/parser.py:3047:        return self.expression(exp.MergeBlockRatioProperty(no=no, default=default))
sqlglot/parser.py:8884:    def _parse_merge(self) -> exp.Merge:
sqlglot/parser.py:8895:            exp.Merge(
[tool_use Bash] {"command": "git status --short | head; sed -n 8880,8940p sqlglot/parser.py; sed -n 4465,4520p sqlglot/generator.py; grep -n \"class Merge\\b\\|class Merge(\\|class When(\\|class Whens\" -A12 sqlglot/expressions/*.py | head -60", "description": "Read MERGE parser, generator, and expression defs"}
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
…[4553 chars elided]…
.py-516-
sqlglot/expressions/dml.py:517:class When(Expression):
sqlglot/expressions/dml.py-518-    arg_types = {"matched": True, "source": False, "condition": False, "then": True}
sqlglot/expressions/dml.py-519-
sqlglot/expressions/dml.py-520-
sqlglot/expressions/dml.py:521:class Whens(Expression):
sqlglot/expressions/dml.py-522-    """Wraps around one or more WHEN [NOT] MATCHED [...] clauses."""
sqlglot/expressions/dml.py-523-
sqlglot/expressions/dml.py-524-    arg_types = {"expressions": True}
[tool_use Bash] {"command": "sed -n 8940,8975p sqlglot/parser.py; grep -n \"class Insert(\\|class Update(\" -A22 sqlglot/expressions/dml.py | head -60; grep -n \"def when_sql\\|def update_sql\\|def insert_sql\" -A25 sqlglot/generator.py | head -90; grep -rn \"WHEN MATCHED.*WHERE\\|when_matched.*where\\|THEN UPDATE.*WHERE\" tests | head", "description": "Read rest of when parser, expr defs, generator"}
[tool_result]                             expressions=self._match(TokenType.SET)
                            and self._parse_csv(self._parse_equality)
                        )
                    )
            elif self._match(TokenType.DELETE):
                then = self.expression(exp.Var(this=self._prev.text))
            else:
                then = self._parse_var_from_options(self.CONFLICT_ACTIONS)

            whens.append(
                self.expression(
                    exp.When(matched=matched
…[6933 chars elided]…
h.OrderDate BETWEEN '20030701' AND '20030731' GROUP BY ProductID) AS src(ProductID, OrderQty) ON pi.ProductID = src.ProductID WHEN MATCHED AND pi.Quantity - src.OrderQty >= 0 THEN UPDATE SET pi.Quantity = pi.Quantity - src.OrderQty WHEN MATCHED AND pi.Quantity - src.OrderQty <= 0 THEN DELETE OUTPUT $action, Inserted.ProductID, Inserted.LocationID, Inserted.Quantity AS NewQty, Deleted.Quantity AS PreviousQty) AS Changes(Action, ProductID, LocationID, NewQty, PreviousQty) WHERE Action = 'UPDATE'",
[tool_use Bash] {"command": "grep -rn \"MATCHED_BY_SOURCE\\|SUPPORTS_MERGE\\|MERGE\" sqlglot/generator.py sqlglot/dialects/*.py | grep -v \"MergeTree\\|MergeBlock\" | head -30; grep -n \"MERGE\" tests/dialects/test_oracle.py | head -20; grep -n \"unsupported\" tests/dialects/test_oracle.py | head -5", "description": "Find generator flags and Oracle merge tests"}
[tool_result] sqlglot/dialects/athena.py:40:        - SELECT, INSERT, UPDATE, DELETE, MERGE
sqlglot/generator.py:320:    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed
sqlglot/generator.py:321:    MATCHED_BY_SOURCE = True
sqlglot/generator.py:2034:            return "NO MERGEBLOCKRATIO"
sqlglot/generator.py:2036:            return "DEFAULT MERGEBLOCKRATIO"
sqlglot/generator.py:2039:        return f"MERGEBLOCKRATIO={self.sql(expression, 'this')}{percent}"
sqlglot/generator.py:4445:        source = " BY 
…[85 chars elided]…
enerator.py:4475:            # T-SQL syntax is MERGE ... <target_table> [WITH (<merge_hint>)] [[AS] table_alias]
sqlglot/generator.py:4497:            f"MERGE INTO {this}{table_alias}{sep}{using}{sep}{on}{sep}{whens}",
895:            "MERGE INTO my_table USING (SELECT * FROM something) source_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1 WHEN NOT MATCHED THEN INSERT (my_table.id, my_table.col1) VALUES (source_table.id, source_table.col1)",
[tool_use Bash] {"command": "sed -n 312,326p sqlglot/generator.py; grep -rn \"MATCHED_BY_SOURCE\" sqlglot tests | head; sed -n 885,905p tests/dialects/test_oracle.py; grep -n \"class Generator\" -A12 sqlglot/dialects/oracle.py | head -30", "description": "Inspect feature flag pattern and Oracle generator"}
[tool_result]     EXCEPT_INTERSECT_SUPPORT_ALL_CLAUSE = True

    # Wrap derived values in parens, usually standard but spark doesn't support it
    WRAP_DERIVED_VALUES = True

    # Whether create function uses an AS before the RETURN
    CREATE_FUNCTION_RETURN_AS = True

    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed
    MATCHED_BY_SOURCE = True

    # Whether the INTERVAL expression works only with values like '1 day'
    SINGLE_STRING_INTERVAL = False

    # Whether the plural form of date part
…[886 chars elided]…
 THEN UPDATE SET my_table.col1 = source_table.col1 WHEN NOT MATCHED THEN INSERT (my_table.id, my_table.col1) VALUES (source_table.id, source_table.col1)",
        )

    def test_pseudocolumns(self):
        ast = self.validate_identity(
            "WITH t AS (SELECT 1 AS COL) SELECT col, ROWID FROM t WHERE ROWNUM = 1"
        )
        self.assertIsNone(ast.find(exp.Pseudocolumn))

        qualified = qualify(ast, dialect="oracle")
        self.assertIsNotNone(qualified.find(exp.Pseudocolumn))
[tool_use Bash] {"command": "ls sqlglot/generators | head -50; grep -n \"class Generator\" -A30 sqlglot/generators/oracle.py | head -45; sed -n 370,382p sqlglot/generators/snowflake.py; grep -n \"def unsupported\" -A3 sqlglot/generator.py", "description": "Locate Oracle generator and unsupported helper"}
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
                        c.replace(bracket)

    return expression


class SnowflakeGenerator(generator.Generator):
    SELECT_KINDS: tuple[str, ...
…[17 chars elided]…
TER_TOKEN = "$"
    MATCHED_BY_SOURCE = False
    SINGLE_STRING_INTERVAL = True
    JOIN_HINTS = False
    TABLE_HINTS = False
    QUERY_HINTS = False
30:def unsupported_args(
31-    *args: str | tuple[str, str],
32-) -> t.Callable[[GeneratorMethod], GeneratorMethod]:
33-    """
--
953:    def unsupported(self, message: str) -> None:
954-        if self.unsupported_level == ErrorLevel.IMMEDIATE:
955-            raise UnsupportedError(message)
956-        self.unsupported_messages.append(message)
[tool_use Bash] {"command": "grep -n \"class OracleGenerator\" -A25 sqlglot/generators/oracle.py | head -40; grep -n \"MATCHED\\|def merge\\|_parse_when\" sqlglot/parser.py sqlglot/parsers/*.py 2>/dev/null | head; ls sqlglot/parsers 2>/dev/null | head -3", "description": "Read Oracle generator class header"}
[tool_result] 23:class OracleGenerator(generator.Generator):
24-    SELECT_KINDS: tuple[str, ...] = ()
25-    TRY_SUPPORTED = False
26-    SUPPORTS_UESCAPE = False
27-    LOCKING_READS_SUPPORTED = True
28-    JOIN_HINTS = False
29-    TABLE_HINTS = False
30-    DATA_TYPE_SPECIFIERS_ALLOWED = True
31-    ALTER_TABLE_INCLUDE_COLUMN_KEYWORD = False
32-    LIMIT_FETCH = "FETCH"
33-    TABLESAMPLE_KEYWORDS = "SAMPLE"
34-    LAST_DAY_SUPPORTS_DATE_PART = False
35-    SUPPORTS_SELECT_INTO = True
36-    TZ_TO_WITH_TI
…[417 chars elided]…
ype.INT: "INT",
sqlglot/parser.py:1056:        exp.Whens: lambda self: self._parse_when_matched(),
sqlglot/parser.py:4183:            elif self._match_text_seq("WITH", "UNMATCHED", "ROWS"):
sqlglot/parser.py:4184:                text += " WITH UNMATCHED ROWS"
sqlglot/parser.py:8900:                whens=self._parse_when_matched(),
sqlglot/parser.py:8905:    def _parse_when_matched(self) -> exp.Whens:
sqlglot/parser.py:8910:            self._match_text_seq("MATCHED")
__init__.py
athena.py
base.py
[tool_use Bash] {"command": "grep -rn \"unsupported_level\" tests/dialects/test_dialect.py | head -5; grep -rn \"assertLogs\\|self.assertRaises(UnsupportedError)\" tests/dialects/test_oracle.py | head -3; grep -n \"WHERE\\b\" sqlglot/tokens.py | head -3; ls <work>/env-sqlglot/bin/python 2>&1", "description": "Check test helpers and project venv"}
[tool_result] tests/dialects/test_dialect.py:88:                        unsupported_level=ErrorLevel.IGNORE,
tests/dialects/test_dialect.py:99:                        expression.sql(write_dialect, unsupported_level=ErrorLevel.RAISE)
tests/dialects/test_dialect.py:104:                            unsupported_level=ErrorLevel.IGNORE,
394:        "WHERE": TokenType.WHERE,
<work>/env-sqlglot/bin/python
[assistant] Now the parser change: accept an optional `WHERE` after the `UPDATE SET` list and after the `INSERT ... VALUES` list.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-132437-oracle-dialect-support-the-optio/base-1/sqlglot/parser.py", "old_string": "                    then = self.expression(\n                        exp.Insert(\n                            this=exp.var(\"ROW\")\n                            if self._match_text_seq(\"ROW\")\n                        
…[1422 chars elided]…
ssions))\n                else:\n                    then = self.expression(\n                        exp.Update(\n                            expressions=self._match(TokenType.SET)\n                            and self._parse_csv(self._parse_equality),\n                            where=self._match(TokenType.WHERE) and self._parse_disjunction(),\n                        )\n                    )"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-132437-oracle-dialect-support-the-optio/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Next, the generator: a feature flag defaulting to off (only Oracle enables it), and `when_sql` emits the clause or warns and drops it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-132437-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "    MATCHED_BY_SOURCE = True\n\n    # Whether the INTERVAL", "new_string": "    MATCHED_BY_SOURCE = True\n\n    # Whether MERGE ... WHEN [NOT] MATCHED THEN UPDATE/INSERT ... WHERE <cond> is allowed\n    SUPPORTS_MERGE_WHEN_WHERE = False\n\n    # Whether the INTERVAL"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-132437-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-132437-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "        then_expression = expression.args.get(\"then\")\n        if isinstance(then_expression, exp.Insert):\n            this = self.sql(then_expression, \"this\")\n            this = f\"INSERT {this}\" if this else
…[1592 chars elided]…
 exp.Update)) and then_expression.args.get(\n            \"where\"\n        ):\n            if self.SUPPORTS_MERGE_WHEN_WHERE:\n                where = f\" WHERE {self.sql(then_expression, 'where')}\"\n            else:\n                self.unsupported(\"WHERE clause in MERGE WHEN MATCHED/NOT MATCHED is not supported\")\n\n        return f\"WHEN {matched}{source}{condition} THEN {then}{where}\""}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-132437-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now enable the flag for Oracle.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-132437-oracle-dialect-support-the-optio/base-1/sqlglot/generators/oracle.py", "old_string": "    SUPPORTS_DECODE_CASE = True\n", "new_string": "    SUPPORTS_DECODE_CASE = True\n    SUPPORTS_MERGE_WHEN_WHERE = True\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-132437-oracle-dialect-support-the-optio/base-1/sqlglot/generators/oracle.py has been updated successfully.
[assistant] Now tests. I'll check how existing dialect tests assert on unsupported warnings before writing mine.
[tool_use Bash] {"command": "grep -rn \"UnsupportedError\\|assertLogs\" tests/dialects/*.py | head -5; grep -n \"def test_merge\\|def test_\" tests/dialects/test_oracle.py | head -5; grep -n \"^from\\|^import\" tests/dialects/test_oracle.py", "description": "Find how tests assert unsupported warnings"}
[tool_result] tests/dialects/test_clickhouse.py:1729:        with self.assertLogs(helper_logger) as cm:
tests/dialects/test_bigquery.py:9:    UnsupportedError,
tests/dialects/test_bigquery.py:493:                "clickhouse": UnsupportedError,
tests/dialects/test_bigquery.py:494:                "databricks": UnsupportedError,
tests/dialects/test_bigquery.py:495:                "drill": UnsupportedError,
9:    def test_oracle(self):
378:    def test_join_marker(self):
393:    def test_hints(self):
468:    def test_xml_table(self):
532:    def test_match_recognize(self):
1:from sqlglot import exp, UnsupportedError, ParseError, parse, parse_one
2:from tests.dialects.test_dialect import Validator
3:from sqlglot.optimizer.qualify import qualify
[tool_use Bash] {"command": "sed -n 1725,1740p tests/dialects/test_clickhouse.py; sed -n 880,896p tests/dialects/test_oracle.py", "description": "Look at example warning test and Oracle merge test context"}
[tool_result]             "SELECT TRANSFORM(foo, [1, 2], ['first', 'second'], 'default') FROM table"
        )

    def test_array_offset(self):
        with self.assertLogs(helper_logger) as cm:
            self.validate_all(
                "SELECT col[1]",
                write={
                    "bigquery": "SELECT col[0]",
                    "duckdb": "SELECT col[1]",
                    "hive": "SELECT col[0]",
                    "clickhouse": "SELECT col[1]",
                    "presto": "SELECT 
…[565 chars elided]…

            using="(SELECT * FROM something) source_table",
            on="my_table.id = source_table.id",
            dialect="oracle",
        )
        self.assertEqual(
            merge_stmt.sql("oracle"),
            "MERGE INTO my_table USING (SELECT * FROM something) source_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1 WHEN NOT MATCHED THEN INSERT (my_table.id, my_table.col1) VALUES (source_table.id, source_table.col1)",
        )
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-132437-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py", "old_string": "            \"MERGE INTO my_table USING (SELECT * FROM something) source_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1 WHEN NOT MATCHED THEN INSERT (my
…[779 chars elided]…
")\n        self.assertEqual(\n            ast.sql(\"postgres\", unsupported_level=ErrorLevel.IGNORE),\n            \"MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.col = s.col WHEN NOT MATCHED THEN INSERT (t.id, t.col) VALUES (s.id, s.col)\",\n        )\n        with self.assertRaises(UnsupportedError):\n            ast.sql(\"postgres\", unsupported_level=ErrorLevel.RAISE)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-132437-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py has been updated successfully.
[tool_use Bash] {"command": "sed -i '' '1s/.*/from sqlglot import exp, UnsupportedError, ParseError, parse, parse_one\\nfrom sqlglot.errors import ErrorLevel/' tests/dialects/test_oracle.py && head -4 tests/dialects/test_oracle.py && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py 2>&1 | tail -30", "description": "Add ErrorLevel import and run Oracle dialect tests"}
[tool_result] from sqlglot import exp, UnsupportedError, ParseError, parse, parse_one
from sqlglot.errors import ErrorLevel
from tests.dialects.test_dialect import Validator
from sqlglot.optimizer.qualify import qualify
.............F..........                                                      [100%]
=================================== FAILURES ===================================
_______________________ TestOracle.test_merge_when_where _______________________

self = <tests.dialects.test_oracle.TestOracle 
…[1155 chars elided]…
      ?                                                                  ++                                          ++    ++

tests/dialects/test_oracle.py:908: AssertionError
=========================== short test summary info ============================
FAILED tests/dialects/test_oracle.py::TestOracle::test_merge_when_where - Ass...
1 failed, 23 passed, 211 subtests passed in 0.39s
[This command modified 1 file you've previously read: tests/dialects/test_oracle.py. Call Read before editing.]
[assistant] The one failure is my expected string, not the feature: Postgres strips the target qualifiers from the SET/INSERT columns. I'll confirm that happens without a WHERE too, so I know it's existing behavior.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nprint(sqlglot.transpile('MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.col = s.col WHEN NOT MATCHED THEN INSERT (t.id, t.col) VALUES (s.id, s.col)', read='oracle', write='postgres')[0])\np
…[24 chars elided]…
MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.col = s.col WHERE s.active = 1 WHEN NOT MATCHED THEN INSERT (t.id, t.col) VALUES (s.id, s.col) WHERE s.active = 1', read='oracle', write='postgres', unsupported_level=sqlglot.ErrorLevel.WARN)[0])\n\" 2>&1; grep -n \"\" tests/dialects/test_oracle.py | sed -n 1,3p", "description": "Check Postgres MERGE output with and without WHERE"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
1:from sqlglot import exp, UnsupportedError, ParseError, parse, parse_one
2:from sqlglot.errors import ErrorLevel
3:from tests.dialects.test_dialect import Validator
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile('MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.col = s.col WHEN NOT MATCHED THEN INSERT (t.id, t.col) VALUES (s.id, s.col)', read='oracle', write='postgres')[0])\nprint(sqlglot.transpile('MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.col = s.col WHERE s.active = 1 WHEN NOT MATCHED THEN INSERT (t.id, t.col) VALUES (s.id, s.col) WHERE s.active = 1', read='oracle', write='postgres')[0])\n\" 2>&1", "description": "Check Postgres MERGE output with and without WHERE"}
[tool_result] WHERE clause in MERGE WHEN MATCHED/NOT MATCHED is not supported
WHERE clause in MERGE WHEN MATCHED/NOT MATCHED is not supported
MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET col = s.col WHEN NOT MATCHED THEN INSERT (id, col) VALUES (s.id, s.col)
MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET col = s.col WHEN NOT MATCHED THEN INSERT (id, col) VALUES (s.id, s.col)
[assistant] Confirmed: the qualifier stripping is pre-existing Postgres behavior, and the unsupported warning fires as intended. I'll make the test SQL unqualified so the expected string is clean.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-132437-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py", "old_string": "        sql = (\n            \"MERGE INTO t USING s ON t.id = s.id \"\n            \"WHEN MATCHED THEN UPDATE SET t.col = s.col WHERE s.active = 1 \"\n            \"WHEN NOT MATCHED THEN INSERT (t.id, t.col)
…[637 chars elided]…
 (s.id, s.col) WHERE s.active = 1\"\n        )\n        self.validate_identity(sql)\n\n        ast = parse_one(sql, read=\"oracle\")\n        self.assertEqual(\n            ast.sql(\"postgres\", unsupported_level=ErrorLevel.IGNORE),\n            \"MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET col = s.col WHEN NOT MATCHED THEN INSERT (id, col) VALUES (s.id, s.col)\",\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-132437-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py has been updated successfully.
[assistant] Now I'll run the formatter and linter the repo uses, then the full test suite with the project's command.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; ls $PY/ | grep -i \"ruff\\|mypy\"; $PY/ruff format sqlglot/generator.py sqlglot/parser.py sqlglot/generators/oracle.py tests/dialects/test_oracle.py 2>&1 | tail -2; $PY/ruff check sqlglot tests/dialects/test_oracle.py 2>&1 | tail -3; git diff --stat", "description": "Run ruff format and check on changed files"}
[tool_result] dmypy
mypy
mypyc
ruff
4 files left unchanged
All checks passed!
 sqlglot/generator.py          | 15 ++++++++++++++-
 sqlglot/generators/oracle.py  |  1 +
 sqlglot/parser.py             |  4 +++-
 tests/dialects/test_oracle.py | 17 +++++++++++++++++
 4 files changed, 35 insertions(+), 2 deletions(-)
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; $PY/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite with project command"}
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
1081 passed, 17834 subtests passed in 41.47s
[assistant] Oracle now parses and round-trips the optional `WHERE` on both the `UPDATE` and `INSERT` branches of a `MERGE`. Transpiling to a dialect without support emits an unsupported warning and drops the clause. The full suite passes: 1081 tests, run with the project's pytest command.

Changes:

- **Parser** (`sqlglot/parser.py`, `_parse_when_matched`): after the `UPDATE SET` list and after the non-star `INSERT ... VALUES` list, an optional `WHERE <condition>` is stored on the existing `where` arg of `exp.Update` / `exp.Insert`. This is in the shared parser, so other dialects also accept the syntax.
-
…[604 chars elided]…
f rather than on. Only Oracle supports this, so the base generator and every other dialect warn and drop it.
- I left `DELETE ... WHERE` alone because the request only covered UPDATE and INSERT.
- I left the `INSERT *` / `UPDATE *` forms without a WHERE, since Oracle has no such syntax.

Something I noticed but did not change: Postgres output strips table qualifiers from `MERGE` SET and INSERT column lists (`SET t.col = ...` becomes `SET col = ...`). This happens with or without the new clause, so it's existing behavior and I left it out of scope.

I did not run mypy, and nothing is committed.
