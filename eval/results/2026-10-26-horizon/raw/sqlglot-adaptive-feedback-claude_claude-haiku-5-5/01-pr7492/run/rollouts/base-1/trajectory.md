# trajectory base-1

final message:
Oracle now parses and round-trips the optional `WHERE` on both the `UPDATE` and `INSERT` branches of `MERGE`. Other dialects drop it with an unsupported warning. The full suite passes (1081 tests) and ruff is clean.

Changes:

- **`sqlglot/parser.py`**: `_parse_when_matched` reads an optional `WHERE` after the `UPDATE SET ...` and `INSERT ... VALUES ...` parts, storing it in the existing `where` arg on `exp.Update` / `exp.Insert`. This is parsed for every dialect, since the parser is shared.
- **`sqlglot/generator.py`**: new flag `SUPPORTS_MERGE_WHERE = False`, next to `MATCHED_BY_SOURCE`. `when_sql` emits the `WHERE` when the flag is set. Otherwise it calls `self.unsupported(...)` and drops the clause.
- **`sqlglot/generators/oracle.py`**: sets `SUPPORTS_MERGE_WHERE = True`.
- **`tests/dialects/test_oracle.py`**: new `test_merge_where` covering the Oracle round-trip, and a DuckDB transpile that asserts the warning is logged and the clause is removed.

Choices I made:

- **Flag default is `False`**, so any dialect without the flag warns. Only Oracle is enabled, which follows your "dialects that do not support it" wording.
- **Stored on the branch** (`Update.where` / `Insert.where`), not on `When`, because the clause belongs to the UPDATE/INSERT action in the grammar.
- **`WHERE` on `INSERT *`** is not parsed. Oracle doesn't have that form, so I left it alone.
- **`DELETE WHERE`** (also Oracle-only) is not handled. It wasn't in the request.

I haven't committed anything.

## events
[tool_use Bash] {"command": "git status --short | head && grep -n -i \"merge\" sqlglot/dialects/oracle.py | head -40 && grep -n -i \"whens\\|class Merge\\|class When\" sqlglot/expressions.py | head -30", "description": "Inspect oracle dialect and MERGE expression definitions"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "grep -n \"_parse_merge\\|def _parse_when_matched\\|WHEN\\b\" sqlglot/parser.py | head -20 && grep -n \"def merge_sql\" -A 60 sqlglot/generator.py | head -90", "description": "Find MERGE parsing and generation code"}
[tool_result] 1080:        TokenType.MERGE: lambda self: self._parse_merge(),
1271:        "MERGEBLOCKRATIO": lambda self, **kwargs: self._parse_mergeblockratio(**kwargs),
2436:            when = self._match_text_seq("WHEN") and self._parse_wrapped(
3037:    def _parse_mergeblockratio(
3346:            if self._match(TokenType.WHEN):
7500:        while self._match(TokenType.WHEN):
8884:    def _parse_merge(self) -> exp.Merge:
8905:    def _parse_when_matched(self) -> exp.Whens:
8908:        while self._match(
…[2213 chars elided]…

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
[tool_use Bash] {"command": "ls sqlglot | head -50; sed -n 8884,8960p sqlglot/parser.py; grep -rn \"class When(\" -A 12 sqlglot/expressions/*.py sqlglot/*.py 2>/dev/null | head -30", "description": "Read MERGE parser and When expression definition"}
[tool_result] __init__.py
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
    def _parse_merge(self) -> exp.Merge:
        self._match(TokenType.INTO)
        target = self._parse_table()

        if target and self._match(TokenType.ALIAS, advance=False):
            target.set("alias", se
…[2797 chars elided]…
f._prev)
sqlglot/expressions/dml.py:517:class When(Expression):
sqlglot/expressions/dml.py-518-    arg_types = {"matched": True, "source": False, "condition": False, "then": True}
sqlglot/expressions/dml.py-519-
sqlglot/expressions/dml.py-520-
sqlglot/expressions/dml.py-521-class Whens(Expression):
sqlglot/expressions/dml.py-522-    """Wraps around one or more WHEN [NOT] MATCHED [...] clauses."""
sqlglot/expressions/dml.py-523-
sqlglot/expressions/dml.py-524-    arg_types = {"expressions": True}
[tool_use Bash] {"command": "grep -n \"^class Update\\|^class Insert\\|^class Merge\" -A 22 sqlglot/expressions/dml.py | head -120; grep -rn \"def when_sql\\|def whens_sql\\|def update_sql\\|def insert_sql\" -A 30 sqlglot/generator.py | head -150", "description": "Read Update, Insert, Merge classes and their generators"}
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
…[9179 chars elided]…
nerator.py-4487-            on = f"USING ({on})" if on else ""
sqlglot/generator.py-4488-
sqlglot/generator.py-4489-        returning = self.sql(expression, "returning")
sqlglot/generator.py-4490-        if returning:
sqlglot/generator.py-4491-            whens = f"{whens}{returning}"
sqlglot/generator.py-4492-
sqlglot/generator.py-4493-        sep = self.sep()
sqlglot/generator.py-4494-
sqlglot/generator.py-4495-        return self.prepend_ctes(
sqlglot/generator.py-4496-            expression,
[tool_use Bash] {"command": "grep -n \"MATCHED\\|MERGE\" sqlglot/generator.py sqlglot/generators/*.py sqlglot/dialects/oracle.py | head -30; grep -n \"def _parse_where\\b\" sqlglot/parser.py; grep -n -i \"merge\" tests/dialects/test_oracle.py | head; grep -n \"def unsupported\" -A3 sqlglot/generator.py | head", "description": "Find MERGE-related generator flags, tests, and helpers"}
[tool_result] sqlglot/generator.py:320:    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed
sqlglot/generator.py:321:    MATCHED_BY_SOURCE = True
sqlglot/generator.py:2034:            return "NO MERGEBLOCKRATIO"
sqlglot/generator.py:2036:            return "DEFAULT MERGEBLOCKRATIO"
sqlglot/generator.py:2039:        return f"MERGEBLOCKRATIO={self.sql(expression, 'this')}{percent}"
sqlglot/generator.py:4444:        matched = "MATCHED" if expression.args["matched"] else "NOT MATCHED"
sqlglot/generator.py:44
…[733 chars elided]…
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
[tool_use Bash] {"command": "sed -n 312,326p sqlglot/generator.py; ls sqlglot/generators/ | head -50; grep -n \"class Generator\" -A 25 sqlglot/generators/oracle.py | head -45; grep -n \"SUPPORTS_\\|= False\\|= True\" sqlglot/generators/oracle.py | head -20; sed -n 5183,5186p sqlglot/parser.py", "description": "Read generator flag area and Oracle generator class"}
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
…[508 chars elided]…
  JOIN_HINTS = False
29:    TABLE_HINTS = False
30:    DATA_TYPE_SPECIFIERS_ALLOWED = True
31:    ALTER_TABLE_INCLUDE_COLUMN_KEYWORD = False
34:    LAST_DAY_SUPPORTS_DATE_PART = False
35:    SUPPORTS_SELECT_INTO = True
36:    TZ_TO_WITH_TIME_ZONE = True
37:    SUPPORTS_WINDOW_EXCLUDE = True
39:    SUPPORTS_DECODE_CASE = True
    def _parse_where(self, skip_where_token: bool = False) -> exp.Where | None:
        if not skip_where_token and not self._match(TokenType.WHERE):
            return None
[tool_use Bash] {"command": "sed -n 880,900p tests/dialects/test_oracle.py; grep -rn \"assertLogs\\|unsupported_level\" tests/dialects/test_oracle.py | head -5; grep -n \"def validate_all\" -A 25 tests/dialects/test_dialect.py | head -40; grep -rn \"MERGE\" tests/dialects/test_*.py | grep -i \"where\" | head -5", "description": "Read Oracle merge test and validate_all helper"}
[tool_result]         self.validate_identity("UTC_TIME(6)").assert_is(exp.UtcTime)
        self.validate_identity("UTC_TIMESTAMP()").assert_is(exp.UtcTimestamp)
        self.validate_identity("UTC_TIMESTAMP(6)").assert_is(exp.UtcTimestamp)

    def test_merge_builder_alias(self):
        merge_stmt = exp.merge(
            "WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1",
            "WHEN NOT MATCHED THEN INSERT (my_table.id, my_table.col1) VALUES (source_table.id, source_table.col1)",
      
…[2387 chars elided]…
h.OrderDate BETWEEN '20030701' AND '20030731' GROUP BY ProductID) AS src(ProductID, OrderQty) ON pi.ProductID = src.ProductID WHEN MATCHED AND pi.Quantity - src.OrderQty >= 0 THEN UPDATE SET pi.Quantity = pi.Quantity - src.OrderQty WHEN MATCHED AND pi.Quantity - src.OrderQty <= 0 THEN DELETE OUTPUT $action, Inserted.ProductID, Inserted.LocationID, Inserted.Quantity AS NewQty, Deleted.Quantity AS PreviousQty) AS Changes(Action, ProductID, LocationID, NewQty, PreviousQty) WHERE Action = 'UPDATE'",
[assistant] Plan: parse an optional `WHERE` onto the UPDATE/INSERT branch (reusing the existing `where` arg on `Update`/`Insert`), gate emission behind a `SUPPORTS_MERGE_WHERE` generator flag that only Oracle enables, and warn-and-drop elsewhere.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-1/sqlglot/parser.py", "old_string": "                    then: exp.Expr | None = self.expression(exp.Insert(this=this))\n                else:\n                    then = self.expression(\n                        exp.Insert(\n                            th
…[1633 chars elided]…
ere=self._parse_where())\n                    )\n                else:\n                    then = self.expression(\n                        exp.Update(\n                            expressions=self._match(TokenType.SET)\n                            and self._parse_csv(self._parse_equality),\n                            where=self._parse_where(),\n                        )\n                    )"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Now the generator: the flag, and the `when_sql` emission with the warn-and-drop path.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "    MATCHED_BY_SOURCE = True\n\n    # Whether the INTERVAL", "new_string": "    MATCHED_BY_SOURCE = True\n\n    # Whether MERGE ... WHEN MATCHED THEN UPDATE / WHEN NOT MATCHED THEN INSERT can be followed by a WHERE\n    SUPPORTS_MERGE_WHERE = False\n\n    # Whether the INTERVAL"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "        else:\n            then = self.sql(then_expression)\n        return f\"WHEN {matched}{source}{condition} THEN {then}\"", "new_string": "        else:\n            then = self.sql(then_expression)\n\n        where = self.sql(then_expression, \"where\")\n        if where and not self.SUPPORTS_MERGE_WHERE:\n            self.unsupported(\"WHERE clause in MERGE WHEN clauses is not supported\")\n            where = \"\"\n        where = f\" {where}\" if where else \"\"\n        return f\"WHEN {matched}{source}{condition} THEN {then}{where}\""}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-1/sqlglot/generators/oracle.py", "old_string": "    SUPPORTS_SELECT_INTO = True\n", "new_string": "    SUPPORTS_SELECT_INTO = True\n    SUPPORTS_MERGE_WHERE = True\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-1/sqlglot/generators/oracle.py has been updated successfully.
[assistant] Now tests. Let me check how existing tests assert unsupported warnings before writing them.
[tool_use Bash] {"command": "grep -rn \"unsupported_level=ErrorLevel.WARN\" -B3 -A6 tests/dialects/test_oracle.py | head -30; grep -n \"^from\\|^import\" tests/dialects/test_oracle.py", "description": "Check unsupported-warning assertion pattern in tests"}
[tool_result] 1:from sqlglot import exp, UnsupportedError, ParseError, parse, parse_one
2:from tests.dialects.test_dialect import Validator
3:from sqlglot.optimizer.qualify import qualify
[tool_use Bash] {"command": "grep -rn \"assertLogs\\|ErrorLevel.RAISE\\|UnsupportedError\" tests/dialects/*.py | head -8", "description": "Find how tests assert unsupported errors"}
[tool_result] tests/dialects/test_clickhouse.py:788:        for error_level in [ErrorLevel.IGNORE, ErrorLevel.RAISE, ErrorLevel.IMMEDIATE]:
tests/dialects/test_clickhouse.py:1729:        with self.assertLogs(helper_logger) as cm:
tests/dialects/test_bigquery.py:9:    UnsupportedError,
tests/dialects/test_bigquery.py:493:                "clickhouse": UnsupportedError,
tests/dialects/test_bigquery.py:494:                "databricks": UnsupportedError,
tests/dialects/test_bigquery.py:495:                "drill": UnsupportedError,
tests/dialects/test_bigquery.py:497:                "hive": UnsupportedError,
tests/dialects/test_bigquery.py:499:                "presto": UnsupportedError,
[tool_use Bash] {"command": "sed -n 1720,1740p tests/dialects/test_clickhouse.py; grep -n \"helper_logger\" tests/dialects/test_clickhouse.py | head -3", "description": "Read clickhouse logging assertion example"}
[tool_result]         )

    def test_functions(self):
        self.validate_identity("SELECT TRANSFORM(foo, [1, 2], ['first', 'second']) FROM table")
        self.validate_identity(
            "SELECT TRANSFORM(foo, [1, 2], ['first', 'second'], 'default') FROM table"
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
                    "presto": "SELECT col[1]",
                },
            )

5:from sqlglot.helper import logger as helper_logger
1729:        with self.assertLogs(helper_logger) as cm:
[tool_use Bash] {"command": "grep -n \"logger\" sqlglot/generator.py | head -5; grep -n \"^logger\" sqlglot/helper.py", "description": "Find logger used by generator for unsupported messages"}
[tool_result] 24:logger = logging.getLogger("sqlglot")
928:                logger.warning(msg)
38:logger = logging.getLogger("sqlglot")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py", "old_string": "    def test_pseudocolumns(self):", "new_string": "    def test_merge_where(self):\n        self.validate_identity(\n            \"MERGE INTO my_table USING source_table ON my_table.id = source_table.id WHEN
…[520 chars elided]…
                    read=\"oracle\",\n                ).sql(\"duckdb\", unsupported_level=ErrorLevel.WARN),\n                \"MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.a = s.a WHEN NOT MATCHED THEN INSERT (id) VALUES (s.id)\",\n            )\n        self.assertIn(\"WHERE clause in MERGE WHEN clauses is not supported\", cm.output[0])\n\n    def test_pseudocolumns(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py", "old_string": "from sqlglot import exp, UnsupportedError, ParseError, parse, parse_one\nfrom tests.dialects.test_dialect import Validator", "new_string": "from sqlglot import exp, UnsupportedError, ParseError, parse, parse_one\nfrom sqlglot.errors import ErrorLevel\nfrom sqlglot.helper import logger as helper_logger\nfrom tests.dialects.test_dialect import Validator"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py tests/dialects/test_dialect.py tests/test_transpile.py tests/test_expressions.py 2>&1 | tail -30", "description": "Run Oracle and related test files"}
[tool_result] .............F............................................................................................ [ 48%]
............................................................................. [ 83%]
....................................                          [100%]
=================================== FAILURES ===================================
_________________________ TestOracle.test_merge_where __________________________

self = <tests.dialects.test_oracle.TestOracle testMethod=test_merge_w
…[546 chars elided]…
date_identity
    self.assertEqual(
E   AssertionError: 'MERG[126 chars]col1 WHERE source_table.col1 > 0 WHEN NOT MATC[110 chars] > 0' != 'MERG[126 chars]col1  WHERE source_table.col1 > 0 WHEN NOT MAT[112 chars] > 0'
E   Diff is 1169 characters long. Set self.maxDiff to None to see it.
=========================== short test summary info ============================
FAILED tests/dialects/test_oracle.py::TestOracle::test_merge_where - Assertio...
1 failed, 218 passed, 4076 subtests passed in 1.54s
[assistant] The `Where` generator already emits a leading separator, so my extra space doubled it. Fixing that.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "        where = self.sql(then_expression, \"where\")\n        if where and not self.SUPPORTS_MERGE_WHERE:\n            self.unsupported(\"WHERE clause in MERGE WHEN clauses is not supported\")\n            where = \"
…[38 chars elided]…
here else \"\"\n        return f\"WHEN {matched}{source}{condition} THEN {then}{where}\"", "new_string": "        where = self.sql(then_expression, \"where\")\n        if where and not self.SUPPORTS_MERGE_WHERE:\n            self.unsupported(\"WHERE clause in MERGE WHEN clauses is not supported\")\n            where = \"\"\n        return f\"WHEN {matched}{source}{condition} THEN {then}{where}\""}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-153659-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py tests/dialects/test_dialect.py tests/test_transpile.py tests/test_expressions.py 2>&1 | tail -15; $PY -c \"\nimport sqlglot\nfrom sqlglot import parse_one\ns='MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.a = s.a WHERE s.a > 0 WHEN NOT MATCHED THEN INSERT (id) VALUES (s.id) WHERE s.id > 0'\nprint(parse_one(s, read='oracle').sql('oracle', pretty=True))\nprint(parse_one(s, read='oracle').sql('duckdb'))\n\"", "description": "Rerun targeted tests and check pretty and transpiled output"}
[tool_result] .......................................................................................................... [ 48%]
............................................................................. [ 83%]
....................................                          [100%]
219 passed, 4076 subtests passed in 1.17s
WHERE clause in MERGE WHEN clauses is not supported
WHERE clause in MERGE WHEN clauses is not supported
MERGE INTO t
USING s
ON t.id = s.id
WHEN MATCHED THEN UPDATE SET
  t.a = s.a
WHERE
  s.a > 0
WHEN NOT MATCHED THEN INSERT (id) VALUES (s.id)
WHERE
  s.id > 0
MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.a = s.a WHEN NOT MATCHED THEN INSERT (id) VALUES (s.id)
[assistant] Targeted tests pass and the output is right in both directions. Now the full suite with the project's command, and lint on the touched files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; ($PY -m ruff check sqlglot/parser.py sqlglot/generator.py sqlglot/generators/oracle.py tests/dialects/test_oracle.py && $PY -m ruff format --check sqlglot/parser.py sqlglot/generator.py sqlglot/generators/oracle.py tests/dialects/test_oracle.py) 2>&1 | tail -5", "description": "Run full test suite and ruff lint/format checks"}
[tool_result] .................................................................................................... [ 38%]
................................................................ [ 44%]
............................................................................................................. [ 54%]
............................................................................................................ [ 64%]
........................................................................................................................................................................................................................................................................................................................................ [ 94%]
....................... [ 96%]
....................................                      [100%]
1081 passed, 17834 subtests passed in 90.51s (0:01:30)
All checks passed!
4 files already formatted
[assistant] Oracle now parses and round-trips the optional `WHERE` on both the `UPDATE` and `INSERT` branches of `MERGE`. Other dialects drop it with an unsupported warning. The full suite passes (1081 tests) and ruff is clean.

Changes:

- **`sqlglot/parser.py`**: `_parse_when_matched` reads an optional `WHERE` after the `UPDATE SET ...` and `INSERT ... VALUES ...` parts, storing it in the existing `where` arg on `exp.Update` / `exp.Insert`. This is parsed for every dialect, since the parser is shared.
- **`sqlglot/generator.py`**: new flag `SUPPORTS_MERGE_WHERE = False`, next to `MATCHED_BY_SOURCE`. `wh
…[294 chars elided]…
transpile that asserts the warning is logged and the clause is removed.

Choices I made:

- **Flag default is `False`**, so any dialect without the flag warns. Only Oracle is enabled, which follows your "dialects that do not support it" wording.
- **Stored on the branch** (`Update.where` / `Insert.where`), not on `When`, because the clause belongs to the UPDATE/INSERT action in the grammar.
- **`WHERE` on `INSERT *`** is not parsed. Oracle doesn't have that form, so I left it alone.
- **`DELETE WHERE`** (also Oracle-only) is not handled. It wasn't in the request.

I haven't committed anything.
