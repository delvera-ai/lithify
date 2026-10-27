# trajectory base-1

final message:
Oracle `MERGE` now accepts the `WHERE` clause on both the `UPDATE` and `INSERT` branches. It round-trips in Oracle, and transpiling to other dialects warns and drops it. The full suite passes (1081 tests) and ruff check and format are clean. I left the changes uncommitted in the worktree.

Choices I made:

- **Where the clause lives:** on `exp.When` as a new `where` arg, not on `Update` or `Insert`. `Insert` already has a `where` arg that generates `REPLACE WHERE`, which would be wrong here.
- **Parsing:** the base parser accepts the clause for any dialect, so Oracle SQL can be read and transpiled. It is only attached to `UPDATE` and `INSERT` branches; `WHEN MATCHED THEN DELETE ... WHERE` is still not parsed as a clause.
- **Dialect support:** a new `MERGE_WHEN_WHERE` generator flag, default `False`, set to `True` in the Oracle generator. Other dialects, including the base `sqlglot` dialect, emit `MERGE WHEN ... WHERE clause is not supported.` as an unsupported warning and omit the clause. Under `ErrorLevel.RAISE` it raises instead.

Changes are in `sqlglot/expressions/dml.py`, `sqlglot/parser.py` (`_parse_when_matched`), `sqlglot/generator.py` (`when_sql` and the flag), `sqlglot/generators/oracle.py`, and a new `test_merge_when_where` in `tests/dialects/test_oracle.py`. The test covers the Oracle round-trip and the warning-and-drop path for Postgres.

One thing to be aware of: in `pretty=True` output the clause is placed on its own line after the branch, which is how the existing `WHERE` formatting behaves.

## events
[tool_use Bash] {"command": "git status --short | head && grep -n -i \"merge\" sqlglot/dialects/oracle.py | head -40 && grep -n -i \"merge\\|whenmatched\\|WhenMatched\" sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -80", "description": "Check status and find MERGE handling code"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:320:    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed
sqlglot/generator.py:700:        exp.MergeBlockRatioProperty: exp.Properties.Location.POST_NAME,
sqlglot/generator.py:744:        exp.MergeTreeTTL: exp.Properties.Location.POST_SCHEMA,
sqlglot/generator.py:2032:    def mergeblockratioproperty_sql(self, expression: exp.MergeBlockRatioProperty) -> str:
sqlglot/generator.py:2034:            return "NO 
…[1805 chars elided]…
ion(this=this, to_volume=self._parse_string())
sqlglot/parser.py:2219:            exp.MergeTreeTTL(
sqlglot/parser.py:3037:    def _parse_mergeblockratio(
sqlglot/parser.py:3039:    ) -> exp.MergeBlockRatioProperty:
sqlglot/parser.py:3042:                exp.MergeBlockRatioProperty(
sqlglot/parser.py:3047:        return self.expression(exp.MergeBlockRatioProperty(no=no, default=default))
sqlglot/parser.py:8884:    def _parse_merge(self) -> exp.Merge:
sqlglot/parser.py:8895:            exp.Merge(
[tool_use Bash] {"command": "sed -n 8880,8990p sqlglot/parser.py; echo ----; sed -n 4465,4500p sqlglot/generator.py; echo ----; grep -n \"def merge_sql\\|def whens_sql\\|class When\\|class Merge\" -A3 sqlglot/generator.py sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null | head -40; echo ----; grep -n \"whens_sql\\|MERGE\" sqlglot/generator.py | head -30; echo; ls sqlglot | head -80", "description": "Read MERGE parser and generator code"}
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
…[7185 chars elided]…
xpression: exp.Whens) -> str:
4475:            # T-SQL syntax is MERGE ... <target_table> [WITH (<merge_hint>)] [[AS] table_alias]
4497:            f"MERGE INTO {this}{table_alias}{sep}{using}{sep}{on}{sep}{whens}",

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
[tool_use Bash] {"command": "sed -n 500,530p sqlglot/expressions/dml.py; grep -n \"^class Update\\|^class Insert\" -A12 sqlglot/expressions/dml.py; echo ----; grep -rn \"MERGE\" tests/dialects/test_oracle.py | head -20; echo ----; grep -rn \"MERGE_\\|merge\" sqlglot/generator.py | grep -i \"support\\|flag\" ; grep -rn \"def update_sql\\|def insert_sql\" -A25 sqlglot/generator.py | head -80; echo ----; grep -rn \"WHEN MATCHED.*WHERE\\|WHEN NOT MATCHED.*WHERE\\|UNSUPPORTED.*MERGE\\|Merge\" tests/dialects/*.py | grep -i where | head", "description": "Inspect DML expression classes, merge tests, and generator helpers"}
[tool_result]             copy=copy,
            **opts,
        )


class Merge(Expression, DML):
    arg_types = {
        "this": True,
        "using": True,
        "on": False,
        "using_cond": False,
        "whens": True,
        "with_": False,
        "returning": False,
    }


class When(Expression):
    arg_types = {"matched": True, "source": False, "condition": False, "then": True}


class Whens(Expression):
    """Wraps around one or more WHEN [NOT] MATCHED [...] clauses."""

    arg_types
…[5416 chars elided]…
h.OrderDate BETWEEN '20030701' AND '20030731' GROUP BY ProductID) AS src(ProductID, OrderQty) ON pi.ProductID = src.ProductID WHEN MATCHED AND pi.Quantity - src.OrderQty >= 0 THEN UPDATE SET pi.Quantity = pi.Quantity - src.OrderQty WHEN MATCHED AND pi.Quantity - src.OrderQty <= 0 THEN DELETE OUTPUT $action, Inserted.ProductID, Inserted.LocationID, Inserted.Quantity AS NewQty, Deleted.Quantity AS PreviousQty) AS Changes(Action, ProductID, LocationID, NewQty, PreviousQty) WHERE Action = 'UPDATE'",
[tool_use Bash] {"command": "sed -n 316,324p sqlglot/generator.py; grep -rn \"MERGE_WHEN_MATCHED_BY_SOURCE\\|SUPPORTS_MERGE\\|exp.When\\b\\|exp.Whens\\|MERGE_CONDITION\" sqlglot/ | head -20; echo ----; grep -n \"def _parse_where\\b\" -A8 sqlglot/parser.py; echo ----; grep -n \"def unsupported\\b\" -A3 sqlglot/generator.py; echo ---; grep -n \"^class Oracle\\|class Generator\\|class Parser\\|TRANSFORMS = {\\|    SUPPORTS\" sqlglot/dialects/oracle.py | head -30; echo ---; grep -rn \"unsupported_level\\|UNSUPPORTED\" tests/dialects/test_oracle.py | head -5", "description": "Look up merge-related generator flags and helpers"}
[tool_result]     # Whether create function uses an AS before the RETURN
    CREATE_FUNCTION_RETURN_AS = True

    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed
    MATCHED_BY_SOURCE = True

    # Whether the INTERVAL expression works only with values like '1 day'
    SINGLE_STRING_INTERVAL = False
sqlglot/generator.py:4443:    def when_sql(self, expression: exp.When) -> str:
sqlglot/generator.py:4466:    def whens_sql(self, expression: exp.Whens) -> str:
sqlglot/parser.py:1056:        exp.Whens: lamb
…[456 chars elided]…
okenType.WHERE):
5185-            return None
5186-
5187-        comments = self._prev_comments
5188-        return self.expression(
5189-            exp.Where(this=self._parse_disjunction()),
5190-            comments=comments,
5191-        )
----
953:    def unsupported(self, message: str) -> None:
954-        if self.unsupported_level == ErrorLevel.IMMEDIATE:
955-            raise UnsupportedError(message)
956-        self.unsupported_messages.append(message)
---
15:class Oracle(Dialect):
---
[tool_use Bash] {"command": "sed -n 4443,4466p sqlglot/generator.py; grep -rn \"MATCHED_BY_SOURCE\" sqlglot/ | head; echo ----; sed -n 880,910p tests/dialects/test_oracle.py; echo ----; grep -n \"class Generator\\|class Parser\\|Parser\\b\" sqlglot/dialects/oracle.py | head", "description": "Read when_sql and existing flag usage"}
[tool_result]     def when_sql(self, expression: exp.When) -> str:
        matched = "MATCHED" if expression.args["matched"] else "NOT MATCHED"
        source = " BY SOURCE" if self.MATCHED_BY_SOURCE and expression.args.get("source") else ""
        condition = self.sql(expression, "condition")
        condition = f" AND {condition}" if condition else ""

        then_expression = expression.args.get("then")
        if isinstance(then_expression, exp.Insert):
            this = self.sql(then_expression, "this
…[2149 chars elided]…
l, ROWID FROM t WHERE ROWNUM = 1"
        )
        self.assertIsNone(ast.find(exp.Pseudocolumn))

        qualified = qualify(ast, dialect="oracle")
        self.assertIsNotNone(qualified.find(exp.Pseudocolumn))

        self.assertEqual(
            qualified.sql(dialect="oracle"),
            'WITH "T" AS (SELECT 1 AS "COL") SELECT "T"."COL" AS "COL", ROWID AS "ROWID" FROM "T" "T" WHERE ROWNUM = 1',
        )
----
11:from sqlglot.parsers.oracle import OracleParser
88:    Parser = OracleParser
[tool_use Bash] {"command": "ls sqlglot/generators | grep -i oracle; grep -n \"class OracleGenerator\\|class Generator\" -A12 sqlglot/generators/oracle.py | head -40; grep -n \"unsupported(\" sqlglot/generator.py | head -5", "description": "Locate Oracle generator and unsupported call style"}
[tool_result] oracle.py
23:class OracleGenerator(generator.Generator):
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
55:                    generator.unsupported(diagnostic)
953:    def unsupported(self, message: str) -> None:
1125:            self.unsupported("Outer join syntax using the (+) operator is not supported.")
1524:            self.unsupported("Named columns are not supported in table alias.")
1558:                self.unsupported("Unsupported transpilation from BINARY/BLOB hex string")
[assistant] Now the edits. First the expression arg, then the parser, then the generator flag and `when_sql`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-153659-oracle-dialect-support-the-optio/base-1/sqlglot/expressions/dml.py", "old_string": "    arg_types = {\"matched\": True, \"source\": False, \"condition\": False, \"then\": True}", "new_string": "    arg_types = {\"matched\": True, \"source\": False, \"condition\": False, \"then\": True, \"where\": False}"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-153659-oracle-dialect-support-the-optio/base-1/sqlglot/expressions/dml.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-153659-oracle-dialect-support-the-optio/base-1/sqlglot/parser.py", "old_string": "                then = self.expression(exp.Var(this=self._prev.text))\n            else:\n                then = self._parse_var_from_options(self.CONFLICT_ACTIONS)\n\n            whens.append(\n                self.exp
…[372 chars elided]…
nce(then, (exp.Insert, exp.Update)) else None\n\n            whens.append(\n                self.expression(\n                    exp.When(\n                        matched=matched,\n                        source=source,\n                        condition=condition,\n                        then=then,\n                        where=where,\n                    )\n                )\n            )"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-153659-oracle-dialect-support-the-optio/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-153659-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed\n    MATCHED_BY_SOURCE = True\n", "new_string": "    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed\n    MATCHED_BY_SOURCE = True\n\n    # Whether MERGE ... WHEN [NOT] MATCHED THEN UPDATE | INSERT ... WHERE is allowed\n    MERGE_WHEN_WHERE = False\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-153659-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-153659-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "        else:\n            then = self.sql(then_expression)\n        return f\"WHEN {matched}{source}{condition} THEN {then}\"", "new_string": "        else:\n            then = self.sql(then_expression)\n\n        where = self.sql(expression, \"where\")\n        if where and not self.MERGE_WHEN_WHERE:\n            self.unsupported(\"MERGE WHEN ... WHERE clause is not supported.\")\n            where = \"\"\n        where = f\" {where}\" if where else \"\"\n        return f\"WHEN {matched}{source}{condition} THEN {then}{where}\""}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-153659-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-153659-oracle-dialect-support-the-optio/base-1/sqlglot/generators/oracle.py", "old_string": "    SUPPORTS_SELECT_INTO = True\n", "new_string": "    SUPPORTS_SELECT_INTO = True\n    MERGE_WHEN_WHERE = True\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-153659-oracle-dialect-support-the-optio/base-1/sqlglot/generators/oracle.py has been updated successfully.
[assistant] Now a quick check of parse, round-trip, and the transpile-with-warning path before writing tests.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.errors import ErrorLevel\nsql = 'MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.a = s.a WHERE s.a > 0 WHEN NOT MATCHED THEN INSERT (id, a) VALUES (s.id, s.a) WHERE s.a > 0 WHEN MA
…[175 chars elided]…
t.transpile(sql, read='oracle', write='postgres', unsupported_level=ErrorLevel.RAISE) if False else '')\ne = sqlglot.parse_one(sql, read='oracle')\nprint(e.sql('postgres'))\ntry:\n    sqlglot.transpile(sql, read='oracle', write='postgres', unsupported_level=ErrorLevel.RAISE)\nexcept Exception as ex: print('RAISE:', ex)\n\"", "description": "Verify Oracle round-trip and unsupported-dialect output"}
[tool_result] MERGE WHEN ... WHERE clause is not supported.
MERGE WHEN ... WHERE clause is not supported.
MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.a = s.a  WHERE s.a > 0 WHEN NOT MATCHED THEN INSERT (id, a) VALUES (s.id, s.a)  WHERE s.a > 0 WHEN MATCHED THEN DELETE
MERGE INTO t
USING s
ON t.id = s.id
WHEN MATCHED THEN UPDATE SET
  t.a = s.a 
WHERE
  s.a > 0
WHEN NOT MATCHED THEN INSERT (id, a) VALUES (s.id, s.a) 
WHERE
  s.a > 0
WHEN MATCHED THEN DELETE

MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET a = s.a WHEN NOT MATCHED THEN INSERT (id, a) VALUES (s.id, s.a) WHEN MATCHED THEN DELETE
RAISE: MERGE WHEN ... WHERE clause is not supported.

MERGE WHEN ... WHERE clause is not supported.
[assistant] The clause round-trips, but there is a double space because `Where` already emits its own leading space. Fixing that:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-153659-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "        where = self.sql(expression, \"where\")\n        if where and not self.MERGE_WHEN_WHERE:\n            self.unsupported(\"MERGE WHEN ... WHERE clause is not supported.\")\n            where = \"\"\n        whe
…[8 chars elided]…
 {where}\" if where else \"\"\n        return f\"WHEN {matched}{source}{condition} THEN {then}{where}\"", "new_string": "        where = self.sql(expression, \"where\")\n        if where and not self.MERGE_WHEN_WHERE:\n            self.unsupported(\"MERGE WHEN ... WHERE clause is not supported.\")\n            where = \"\"\n        return f\"WHEN {matched}{source}{condition} THEN {then}{where}\""}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-153659-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"unsupported_level=ErrorLevel.RAISE\\|assertLogs\" tests/dialects/test_oracle.py tests/dialects/test_dialect.py | head -5; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nsql = 'MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.a = s.a WHERE s.a > 0 WHEN NOT MATCHED THEN INSERT (id, a) VALUES (s.id, s.a) WHERE s.a > 0'\nprint(sqlglot.transpile(sql, read='oracle', write='oracle')[0])\nprint(sqlglot.transpile(sql, read='oracle', write='postgres')[0])\n\"", "description": "Recheck spacing and dropped-clause output"}
[tool_result] tests/dialects/test_dialect.py:57:            with self.assertLogs(parser_logger) as cm:
tests/dialects/test_dialect.py:99:                        expression.sql(write_dialect, unsupported_level=ErrorLevel.RAISE)
tests/dialects/test_dialect.py:5058:                with self.assertLogs(generator_logger, level="WARNING") as cm:
MERGE WHEN ... WHERE clause is not supported.
MERGE WHEN ... WHERE clause is not supported.
MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.a = s.a WHERE s.a > 0 WHEN NOT MATCHED THEN INSERT (id, a) VALUES (s.id, s.a) WHERE s.a > 0
MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET a = s.a WHEN NOT MATCHED THEN INSERT (id, a) VALUES (s.id, s.a)
[assistant] Output is correct now. Let me look at an existing unsupported-warning test to match its pattern.
[tool_use Bash] {"command": "sed -n 5050,5068p tests/dialects/test_dialect.py; grep -n \"generator_logger\\|^from\\|^import\" tests/dialects/test_oracle.py tests/dialects/test_dialect.py | head; grep -n \"def test_merge\" tests/dialects/test_oracle.py", "description": "Read existing unsupported-warning test pattern"}
[tool_result]             "INITCAP(col, (SELECT delimiter FROM settings LIMIT 1))",
            includes=("SELECT delimiter FROM settings", "REPLACE("),
        )

    def test_initcap_custom_delimiter_warning(self):
        expression = parse_one("INITCAP(col, '_')", read="bigquery")
        for dialect in ("postgres", "presto"):
            with self.subTest(f"INITCAP unsupported custom delimiters warning for {dialect}"):
                with self.assertLogs(generator_logger, level="WARNING") as cm:
       
…[829 chars elided]…
test_dialect.py:2:import unittest
tests/dialects/test_dialect.py:5:from sqlglot import (
tests/dialects/test_dialect.py:15:from sqlglot.dialects import BigQuery, Hive, Snowflake, Spark2
tests/dialects/test_dialect.py:16:from sqlglot.dialects.duckdb import WS_CONTROL_CHARS_TO_DUCK
tests/dialects/test_dialect.py:17:from sqlglot.generator import logger as generator_logger
tests/dialects/test_dialect.py:18:from sqlglot.parser import logger as parser_logger
884:    def test_merge_builder_alias(self):
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python - <<'EOF'\nimport re\np = \"tests/dialects/test_oracle.py\"\ns = open(p).read()\ns = s.replace(\n    \"from sqlglot.optimizer.qualify import qualify\\n\",\n    \"from sqlglot.generator import logger as generator_logger\\nfrom sqlglot.o
…[1245 chars elided]…
\").write(s)\nEOF\n<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py tests/test_transpile.py tests/test_generator.py tests/test_parser.py 2>&1 | tail -15", "description": "Add Oracle MERGE WHERE test and run related suites"}
[tool_result] .............................................................................................. [ 77%]
...........................              [100%]
121 passed, 1306 subtests passed in 0.52s
[assistant] Targeted suites pass. Running the project's full test command and the linter next.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; (ruff check sqlglot tests/dialects/test_oracle.py && ruff format --check sqlglot tests/dialects/test_oracle.py) 2>&1 | tail -5", "description": "Run full test suite and ruff checks"}
[tool_result] ................................................................................. [  7%]
................................ [ 10%]
................................................................................................................................... [ 22%]
..................................................... [ 27%]
................ [ 28%]
.................................................................................................... [ 38%]
.......................................
…[299 chars elided]…
....................................................................................................................................................................................................................................................................................................... [ 94%]
....................... [ 96%]
....................................                      [100%]
1081 passed, 17834 subtests passed in 81.00s (0:01:21)
All checks passed!
174 files already formatted
[assistant] Oracle `MERGE` now accepts the `WHERE` clause on both the `UPDATE` and `INSERT` branches. It round-trips in Oracle, and transpiling to other dialects warns and drops it. The full suite passes (1081 tests) and ruff check and format are clean. I left the changes uncommitted in the worktree.

Choices I made:

- **Where the clause lives:** on `exp.When` as a new `where` arg, not on `Update` or `Insert`. `Insert` already has a `where` arg that generates `REPLACE WHERE`, which would be wrong here.
- **Parsing:** the base parser accepts the clause for any dialect, so Oracle SQL can be read and transp
…[333 chars elided]…
lause is not supported.` as an unsupported warning and omit the clause. Under `ErrorLevel.RAISE` it raises instead.

Changes are in `sqlglot/expressions/dml.py`, `sqlglot/parser.py` (`_parse_when_matched`), `sqlglot/generator.py` (`when_sql` and the flag), `sqlglot/generators/oracle.py`, and a new `test_merge_when_where` in `tests/dialects/test_oracle.py`. The test covers the Oracle round-trip and the warning-and-drop path for Postgres.

One thing to be aware of: in `pretty=True` output the clause is placed on its own line after the branch, which is how the existing `WHERE` formatting behaves.
