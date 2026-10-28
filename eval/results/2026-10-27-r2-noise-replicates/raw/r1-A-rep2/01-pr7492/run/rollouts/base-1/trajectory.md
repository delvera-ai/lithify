# trajectory base-1

final message:
Oracle now parses and round-trips the `WHERE` clause on the `UPDATE` and `INSERT` branches of a `MERGE`. Transpiling to other dialects emits an unsupported warning and drops the clause. The full suite passes (1081 tests) and ruff check and format are clean on the changed files. I haven't committed.

Changes:

- **Parser** (`sqlglot/parser.py`): `_parse_when_matched` reads an optional `WHERE` after an `Update` or `Insert` action. It lives in the base parser so Oracle SQL can be read and written by other dialects.
- **AST** (`sqlglot/expressions/dml.py`): the clause is stored as a `where` arg on `exp.When`. I didn't put it on `Update`/`Insert` because `Insert` has no `where` arg.
- **Generator** (`sqlglot/generator.py`): `when_sql` emits the clause only if the new `MERGE_ACTION_WHERE` flag is set. Otherwise it calls `self.unsupported(...)` and drops the clause. The flag defaults to `False`.
- **Oracle** (`sqlglot/generators/oracle.py`): sets `MERGE_ACTION_WHERE = True`.
- **Tests** (`tests/dialects/test_oracle.py`): `test_merge_where` checks the Oracle round-trip and the DuckDB drop-plus-warning.

Choices to review:

- The `DELETE` branch does not accept a `WHERE`. Oracle's grammar allows one there too, but the request covered only `UPDATE` and `INSERT`.
- Oracle's `IS NOT NULL` is written back as `NOT x IS NULL`, which is existing generator behaviour and not something this change affects.

## events
[tool_use Bash] {"command": "git status --short | head && grep -n \"Merge\\|merge\" sqlglot/dialects/oracle.py | head -30; grep -n \"class Merge\\|class When\" -A 12 sqlglot/expressions.py | head -60; grep -n \"_parse_when_matched\\|def _parse_merge\\|def merge_sql\\|def whens_sql\\|def when_sql\" -A 3 sqlglot/parser.py sqlglot/generator.py | head -80"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:4443:    def when_sql(self, expression: exp.When) -> str:
sqlglot/generator.py-4444-        matched = "MATCHED" if expression.args["matched"] else "NOT MATCHED"
sqlglot/generator.py-4445-        source = " BY SOURCE" if self.MATCHED_BY_SOURCE and expression.args.get("source") else ""
sqlglot/generator.py-4446-        condition = self.sql(expression, "condition")
--
sqlglot/generator.py:4466:    def whens_sql(s
…[1082 chars elided]…
arser.py-8886-        target = self._parse_table()
sqlglot/parser.py-8887-
--
sqlglot/parser.py:8900:                whens=self._parse_when_matched(),
sqlglot/parser.py-8901-                returning=self._parse_returning(),
sqlglot/parser.py-8902-            )
sqlglot/parser.py-8903-        )
--
sqlglot/parser.py:8905:    def _parse_when_matched(self) -> exp.Whens:
sqlglot/parser.py-8906-        whens = []
sqlglot/parser.py-8907-
sqlglot/parser.py-8908-        while self._match(TokenType.WHEN):
[tool_use Bash] {"command": "sed -n 8884,8960p sqlglot/parser.py; echo ----; sed -n 4440,4500p sqlglot/generator.py; echo ----; grep -n \"class When(\" -A 12 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null | head -30"}
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
…[5016 chars elided]…
t")
----
sqlglot/expressions/dml.py:517:class When(Expression):
sqlglot/expressions/dml.py-518-    arg_types = {"matched": True, "source": False, "condition": False, "then": True}
sqlglot/expressions/dml.py-519-
sqlglot/expressions/dml.py-520-
sqlglot/expressions/dml.py-521-class Whens(Expression):
sqlglot/expressions/dml.py-522-    """Wraps around one or more WHEN [NOT] MATCHED [...] clauses."""
sqlglot/expressions/dml.py-523-
sqlglot/expressions/dml.py-524-    arg_types = {"expressions": True}
[tool_use Bash] {"command": "grep -n \"class Insert(\\|class Update(\" -A 8 sqlglot/expressions/dml.py; grep -n \"MATCHED_BY_SOURCE\\|MERGE_\" sqlglot/generator.py sqlglot/dialects/*.py | head; grep -n \"MERGE\" -i tests/dialects/test_oracle.py | head -20; grep -n \"MERGE\" -i tests/dialects/test_dialect.py | head; grep -n \"self.unsupported(\" sqlglot/generator.py | head -3; grep -n \"def unsupported\" -A3 sqlglot/generator.py"}
[tool_result] 194:class Insert(Expression, DDL, DML):
195-    arg_types = {
196-        "hint": False,
197-        "with_": False,
198-        "is_function": False,
199-        "this": False,
200-        "expression": False,
201-        "conflict": False,
202-        "returning": False,
--
293:class Update(Expression, DML):
294-    arg_types = {
295-        "with_": False,
296-        "this": False,
297-        "expressions": False,
298-        "from_": False,
299-        "where": False,
300-        "returnin
…[2204 chars elided]…
rted("Named columns are not supported in table alias.")
1558:                self.unsupported("Unsupported transpilation from BINARY/BLOB hex string")
30:def unsupported_args(
31-    *args: str | tuple[str, str],
32-) -> t.Callable[[GeneratorMethod], GeneratorMethod]:
33-    """
--
953:    def unsupported(self, message: str) -> None:
954-        if self.unsupported_level == ErrorLevel.IMMEDIATE:
955-            raise UnsupportedError(message)
956-        self.unsupported_messages.append(message)
[tool_use Bash] {"command": "sed -n 300,330p sqlglot/generator.py; grep -n \"    SUPPORTS_\" sqlglot/generator.py | head -5; grep -n \"class Generator\" -A 3 sqlglot/dialects/oracle.py; grep -n \"SUPPORTS_\\|MATCHED_BY\" sqlglot/dialects/oracle.py; grep -n \"def where_sql\" -A3 sqlglot/generator.py; sed -n 8,12p tests/dialects/test_oracle.py"}
[tool_result]     # Whether ignore nulls is inside the agg or outside.
    # FIRST(x IGNORE NULLS) OVER vs FIRST (x) IGNORE NULLS OVER
    IGNORE_NULLS_IN_FUNC = False

    # Whether IGNORE NULLS is placed before ORDER BY in the agg.
    # FIRST(x IGNORE NULLS ORDER BY y) vs FIRST(x ORDER BY y IGNORE NULLS)
    IGNORE_NULLS_BEFORE_ORDER = True

    # Whether locking reads (i.e. SELECT ... FOR UPDATE/SHARE) are supported
    LOCKING_READS_SUPPORTED = False

    # Whether the EXCEPT and INTERSECT operations can
…[765 chars elided]…
UPPORTS_SINGLE_ARG_CONCAT = True
443:    SUPPORTS_TABLE_ALIAS_COLUMNS = True
455:    SUPPORTS_SELECT_INTO = False
458:    SUPPORTS_UNLOGGED_TABLES = False
3221:    def where_sql(self, expression: exp.Where) -> str:
3222-        this = self.indent(self.sql(expression, "this"))
3223-        return f"{self.seg('WHERE')}{self.sep()}{this}"
3224-

    def test_oracle(self):
        self.validate_identity("1 /* /* */", "1 /* / * */")
        self.validate_all(
            "SELECT CONNECT_BY_ROOT x y",
[tool_use Bash] {"command": "sed -n 514,520p sqlglot/expressions/dml.py && grep -n \"class Oracle\" -A 3 sqlglot/dialects/oracle.py && grep -n \"class Generator\" -A 12 sqlglot/dialects/oracle.py | head -20 && grep -n \"def _parse_where\" -A 4 sqlglot/parser.py"}
[tool_result]     }


class When(Expression):
    arg_types = {"matched": True, "source": False, "condition": False, "then": True}


15:class Oracle(Dialect):
16-    ALIAS_POST_TABLESAMPLE = True
17-    LOCKING_READS_SUPPORTED = True
18-    TABLESAMPLE_SIZE_IS_PERCENT = True
5183:    def _parse_where(self, skip_where_token: bool = False) -> exp.Where | None:
5184-        if not skip_where_token and not self._match(TokenType.WHERE):
5185-            return None
5186-
5187-        comments = self._prev_comments
[tool_use Bash] {"command": "grep -n \"class Generator\" -A 25 sqlglot/dialects/oracle.py | grep -n \"=\" | head -20"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -n \"Generator\\|^    [A-Z_]* = \" sqlglot/dialects/oracle.py | head -40"}
[tool_result] 10:from sqlglot.generators.oracle import OracleGenerator
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
90:    Generator = OracleGenerator
[tool_use Bash] {"command": "grep -n \"^class OracleGenerator\" -A 30 sqlglot/generators/oracle.py | grep \"= \" | head -20"}
[tool_result] 24-    SELECT_KINDS: tuple[str, ...] = ()
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
36-    TZ_TO_WITH_TIME_ZONE = True
37-    SUPPORTS_WINDOW_EXCLUDE = True
38-    QUERY_HINT_SEP = " "
39-    SUPPORTS_DECODE_CASE = True
41-    AFTER_HAVING_MODIFIER_TRANSFORMS = generator.AFTER_HAVING_MODIFIER_TRANSFORMS
43-    TYPE_MAPPING = {
[assistant] Now the edits: the `When` arg, the parser, the generator flag and `when_sql`, and the Oracle flag.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-154910-oracle-dialect-support-the-optio/base-1/sqlglot/expressions/dml.py", "old_string": "    arg_types = {\"matched\": True, \"source\": False, \"condition\": False, \"then\": True}", "new_string": "    arg_types = {\"matched\": True, \"source\": False, \"condition\": False, \"then\": True, \"where\": False}"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-154910-oracle-dialect-support-the-optio/base-1/sqlglot/expressions/dml.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-154910-oracle-dialect-support-the-optio/base-1/sqlglot/parser.py", "old_string": "                then = self._parse_var_from_options(self.CONFLICT_ACTIONS)\n\n            whens.append(\n                self.expression(\n                    exp.When(matched=matched, source=source, condition=condition
…[91 chars elided]…
._parse_var_from_options(self.CONFLICT_ACTIONS)\n\n            where = self._parse_where() if isinstance(then, (exp.Insert, exp.Update)) else None\n\n            whens.append(\n                self.expression(\n                    exp.When(\n                        matched=matched, source=source, condition=condition, then=then, where=where\n                    )\n                )\n            )"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-154910-oracle-dialect-support-the-optio/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-154910-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "    MATCHED_BY_SOURCE = True\n", "new_string": "    MATCHED_BY_SOURCE = True\n\n    # Whether MERGE ... WHEN [NOT] MATCHED THEN UPDATE/INSERT can have a trailing WHERE clause\n    MERGE_ACTION_WHERE = False\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-154910-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-154910-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "        else:\n            then = self.sql(then_expression)\n        return f\"WHEN {matched}{source}{condition} THEN {then}\"", "new_string": "        else:\n            then = self.sql(then_expression)\n\n        where = self.sql(expression, \"where\")\n        if where and not self.MERGE_ACTION_WHERE:\n            self.unsupported(\"WHERE clause in MERGE WHEN actions is not supported.\")\n            where = \"\"\n\n        return f\"WHEN {matched}{source}{condition} THEN {then}{where}\""}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-154910-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-154910-oracle-dialect-support-the-optio/base-1/sqlglot/generators/oracle.py", "old_string": "    SUPPORTS_DECODE_CASE = True\n", "new_string": "    SUPPORTS_DECODE_CASE = True\n    MERGE_ACTION_WHERE = True\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-154910-oracle-dialect-support-the-optio/base-1/sqlglot/generators/oracle.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ns='MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.v = s.v WHERE s.v > 0 DELETE WHERE 1 = 1 WHEN NOT MATCHED THEN INSERT (id, v) VALUES (s.id, s.v) WHERE s.id IS NOT NULL'\nprint(sqlglot.transpile(s, read='oracle', write='oracle')[0])\nprint(sqlglot.transpile(s, read='oracle', write='oracle', pretty=True)[0])\nprint(sqlglot.transpile('MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.v = s.v WHERE s.v > 0', read='oracle', write='duckdb')[0])\nprint(sqlglot.transpile('MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.v = s.v WHERE s.v > 0', read='oracle', write='duckdb')[0])\n\" 2>&1"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 4, in <module>
  File "~/.cache/lithify/work/repo-fdb04f649b80/20261027-154910-oracle-dialect-support-the-optio/base-1/sqlglot/__init__.py", line 212, in transpile
    for expression in parse(sql, read, error_level=error_level)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-fdb04f649b80/20261027-154910-oracle-dialect-support-the-optio/base-1/sqlglot
…[1207 chars elided]…
("Invalid expression / Unexpected token")
  File "~/.cache/lithify/work/repo-fdb04f649b80/20261027-154910-oracle-dialect-support-the-optio/base-1/sqlglot/parser.py", line 1969, in raise_error
    raise error
sqlglot.errors.ParseError: Invalid expression / Unexpected token. Line 1, Col: 95.
  MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.v = s.v WHERE s.v > 0 [4mDELETE[0m WHERE 1 = 1 WHEN NOT MATCHED THEN INSERT (id, v) VALUES (s.id, s.v) WHERE s.id IS NOT NULL
[assistant] That failure was my test SQL, not the change: I put a `DELETE` after the `WHERE`, which is out of scope. Retrying without it.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ns='MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.v = s.v WHERE s.v > 0 WHEN NOT MATCHED THEN INSERT (id, v) VALUES (s.id, s.v) WHERE s.id IS NOT NULL'\nprint(sqlglot.transpile(s, read='oracle', write='oracle')[0])\nprint(sqlglot.transpile(s, read='oracle', write='oracle', pretty=True)[0])\nprint(sqlglot.transpile(s, read='oracle', write='duckdb')[0])\n\" 2>&1"}
[tool_result] WHERE clause in MERGE WHEN actions is not supported.
WHERE clause in MERGE WHEN actions is not supported.
MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.v = s.v WHERE s.v > 0 WHEN NOT MATCHED THEN INSERT (id, v) VALUES (s.id, s.v) WHERE NOT s.id IS NULL
MERGE INTO t
USING s
ON t.id = s.id
WHEN MATCHED THEN UPDATE SET
  t.v = s.v
WHERE
  s.v > 0
WHEN NOT MATCHED THEN INSERT (id, v) VALUES (s.id, s.v)
WHERE
  NOT s.id IS NULL
MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.v = s.v WHEN NOT MATCHED THEN INSERT (id, v) VALUES (s.id, s.v)
[assistant] Two things to check: Oracle→Oracle is still emitting the unsupported warning, and the `IS NOT NULL` → `NOT ... IS NULL` rewrite is just existing generator normalization. Checking where my Oracle flag landed.
[tool_use Bash] {"command": "grep -n \"MERGE_ACTION_WHERE\\|^class \\|SUPPORTS_DECODE_CASE\" sqlglot/generators/oracle.py | head; grep -rn \"MERGE_ACTION_WHERE\" sqlglot | head"}
[tool_result] 23:class OracleGenerator(generator.Generator):
39:    SUPPORTS_DECODE_CASE = True
40:    MERGE_ACTION_WHERE = True
sqlglot/generator.py:324:    MERGE_ACTION_WHERE = False
sqlglot/generator.py:4469:        if where and not self.MERGE_ACTION_WHERE:
sqlglot/generators/oracle.py:40:    MERGE_ACTION_WHERE = True
[assistant] The flag is set correctly, but the Oracle output is the warning text rather than SQL. Running it directly to see why.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ns='MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.v = s.v WHERE s.v > 0 WHEN NOT MATCHED THEN INSERT (id, v) VALUES (s.id, s.v) WHERE s.id IS NOT NULL'\ne=sqlglot.parse_one(s, read='oracle')\nprint(repr(e.sql('oracle')))\nprint(repr(e.sql('duckdb')))\n\" 2>&1; sed -n 4466,4480p sqlglot/generator.py"}
[tool_result] WHERE clause in MERGE WHEN actions is not supported.
WHERE clause in MERGE WHEN actions is not supported.
'MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.v = s.v WHERE s.v > 0 WHEN NOT MATCHED THEN INSERT (id, v) VALUES (s.id, s.v) WHERE NOT s.id IS NULL'
'MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.v = s.v WHEN NOT MATCHED THEN INSERT (id, v) VALUES (s.id, s.v)'
            then = self.sql(then_expression)

        where = self.sql(expression, "where")
        if where and not self.MERGE_ACTION_WHERE:
            self.unsupported("WHERE clause in MERGE WHEN actions is not supported.")
            where = ""

        return f"WHEN {matched}{source}{condition} THEN {then}{where}"

    def whens_sql(self, expression: exp.Whens) -> str:
        return self.expressions(expression, sep=" ", indent=False)

    def merge_sql(self, expression: exp.Merge) -> str:
        table = expression.this
        table_alias = ""
[assistant] Oracle output is correct. The warnings are the two DuckDB outputs (one per WHEN branch carrying a WHERE), and stderr simply printed ahead of stdout. Now the tests. Checking the existing conventions for unsupported-level assertions.
[tool_use Bash] {"command": "grep -n \"unsupported_level\\|ErrorLevel\" tests/dialects/test_oracle.py | head -5; grep -n \"def test_merge\" -A 4 tests/dialects/test_dialect.py | head -20; grep -n \"def test_\" tests/dialects/test_oracle.py | tail -3; tail -5 tests/dialects/test_oracle.py"}
[tool_result] 3040:    def test_merge(self):
3041-        self.validate_all(
3042-            """
3043-            MERGE INTO target USING source ON target.id = source.id
3044-                WHEN NOT MATCHED THEN INSERT (id) values (source.id)
912:    def test_chr(self):
916:    def test_full_procedure(self):
958:    def test_create_trigger(self):

        self.validate_identity(
            "CREATE TRIGGER view_insert INSTEAD OF INSERT ON employee_view FOR EACH ROW BEGIN INSERT INTO employees (id, name, dept_id) VALUES (:NEW.id, :NEW.name, :NEW.dept_id) END",
            check_command_warning=True,
        )
[tool_use Bash] {"command": "grep -n \"def validate_all\" -A 12 tests/dialects/test_dialect.py | head -30; grep -rn \"assertLogs\\|unsupported_level=ErrorLevel.RAISE\" tests/dialects/test_dialect.py | head -3"}
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
79-            identify (bool): quote identifiers in both read and write
80-        """
tests/dialects/test_dialect.py:57:            with self.assertLogs(parser_logger) as cm:
tests/dialects/test_dialect.py:99:                        expression.sql(write_dialect, unsupported_level=ErrorLevel.RAISE)
tests/dialects/test_dialect.py:5058:                with self.assertLogs(generator_logger, level="WARNING") as cm:
[tool_use Bash] {"command": "sed -n 5050,5066p tests/dialects/test_dialect.py; grep -n \"^from\\|^import\" tests/dialects/test_oracle.py tests/dialects/test_dialect.py | head -20"}
[tool_result]             "INITCAP(col, (SELECT delimiter FROM settings LIMIT 1))",
            includes=("SELECT delimiter FROM settings", "REPLACE("),
        )

    def test_initcap_custom_delimiter_warning(self):
        expression = parse_one("INITCAP(col, '_')", read="bigquery")
        for dialect in ("postgres", "presto"):
            with self.subTest(f"INITCAP unsupported custom delimiters warning for {dialect}"):
                with self.assertLogs(generator_logger, level="WARNING") as cm:
       
…[946 chars elided]…
ialects/test_dialect.py:16:from sqlglot.dialects.duckdb import WS_CONTROL_CHARS_TO_DUCK
tests/dialects/test_dialect.py:17:from sqlglot.generator import logger as generator_logger
tests/dialects/test_dialect.py:18:from sqlglot.parser import logger as parser_logger
tests/dialects/test_dialect.py:19:from sqlglot.parsers.snowflake import SnowflakeParser
tests/dialects/test_dialect.py:20:from collections.abc import Iterable
tests/dialects/test_dialect.py:21:import sqlglot.parsers.base as _base_module
[tool_use Bash] {"command": "cat >> tests/dialects/test_oracle.py <<'EOF'\n\n    def test_merge_where(self):\n        sql = \"MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.v = s.v WHERE s.v > 0 WHEN NOT MATCHED THEN INSERT (id, v) VALUES (s.id, s.v) WHERE s.v > 0\"\n        self.validate_identity(sql)\n\n        expression = parse_one(sql, read=\"oracle\")\n        with self.assertLogs(\"sqlg
…[159 chars elided]…
s.id WHEN MATCHED THEN UPDATE SET t.v = s.v WHEN NOT MATCHED THEN INSERT (id, v) VALUES (s.id, s.v)\",\n            )\n        self.assertIn(\"WHERE clause in MERGE WHEN actions is not supported\", cm.output[0])\nEOF\nPY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py -k merge 2>&1 | tail -15"}
[tool_result] ..                                                                       [100%]
2 passed, 22 deselected in 0.13s
[assistant] Both new merge tests pass. Running the full project test suite, per the repo's check command.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15"}
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
1081 passed, 17834 subtests passed in 48.52s
[assistant] All 1081 tests pass. Running the linter and formatter on the changed files.
[tool_use Bash] {"command": "R=<work>/env-sqlglot/bin; ls $R | grep -i ruff; F=\"sqlglot/parser.py sqlglot/generator.py sqlglot/generators/oracle.py sqlglot/expressions/dml.py tests/dialects/test_oracle.py\"; ($R/ruff check $F && $R/ruff format --check $F) 2>&1 | tail -5; git diff --stat"}
[tool_result] ruff
E902 No such file or directory (os error 2)
--> sqlglot/parser.py sqlglot/generator.py sqlglot/generators/oracle.py sqlglot/expressions/dml.py tests/dialects/test_oracle.py:1:1

Found 1 error.
 sqlglot/expressions/dml.py    |  2 +-
 sqlglot/generator.py          | 11 ++++++++++-
 sqlglot/generators/oracle.py  |  1 +
 sqlglot/parser.py             |  6 +++++-
 tests/dialects/test_oracle.py | 12 ++++++++++++
 5 files changed, 29 insertions(+), 3 deletions(-)
[assistant] The file list didn't split (the shell is likely zsh), so ruff got one bogus path. Running it again with explicit paths.
[tool_use Bash] {"command": "R=<work>/env-sqlglot/bin; $R/ruff check sqlglot/parser.py sqlglot/generator.py sqlglot/generators/oracle.py sqlglot/expressions/dml.py tests/dialects/test_oracle.py && $R/ruff format --check sqlglot/parser.py sqlglot/generator.py sqlglot/generators/oracle.py sqlglot/expressions/dml.py tests/dialects/test_oracle.py"}
[tool_result] All checks passed!
5 files already formatted
[assistant] Oracle now parses and round-trips the `WHERE` clause on the `UPDATE` and `INSERT` branches of a `MERGE`. Transpiling to other dialects emits an unsupported warning and drops the clause. The full suite passes (1081 tests) and ruff check and format are clean on the changed files. I haven't committed.

Changes:

- **Parser** (`sqlglot/parser.py`): `_parse_when_matched` reads an optional `WHERE` after an `Update` or `Insert` action. It lives in the base parser so Oracle SQL can be read and written by other dialects.
- **AST** (`sqlglot/expressions/dml.py`): the clause is stored as a `where` arg on
…[210 chars elided]…
erwise it calls `self.unsupported(...)` and drops the clause. The flag defaults to `False`.
- **Oracle** (`sqlglot/generators/oracle.py`): sets `MERGE_ACTION_WHERE = True`.
- **Tests** (`tests/dialects/test_oracle.py`): `test_merge_where` checks the Oracle round-trip and the DuckDB drop-plus-warning.

Choices to review:

- The `DELETE` branch does not accept a `WHERE`. Oracle's grammar allows one there too, but the request covered only `UPDATE` and `INSERT`.
- Oracle's `IS NOT NULL` is written back as `NOT x IS NULL`, which is existing generator behaviour and not something this change affects.
