# trajectory base-1

final message:
Snowflake now accepts `KEY = VALUE` properties before the column list, and both forms produce the same SQL. The full project test suite passes (1127 tests, up from 1126 with the new test), and ruff check and format are clean on the changed files.

**Cause:** The parser has a hook for properties that appear before the schema, but it only recognised keywords from the property table. The generic `KEY = VALUE` fallback was never reached in that position, so `CHANGE_TRACKING=TRUE` before `(id INT)` failed.

**Fix** (`sqlglot/parsers/snowflake.py`): Snowflake's parser now overrides that hook and falls back to the generic property parser, but only when the next token is `=`. My first version tried the fallback on any token. That broke nine existing column-definition tests, because the generic parser treated the column list's opening `(` as an expression and raised. The `=` guard fixed all nine. The change is scoped to Snowflake, so other dialects are unaffected.

**Test** (`tests/dialects/test_snowflake.py`): `test_create_table_properties_before_schema` round-trips the after-schema form and checks that the before-schema form normalises to it.

Both forms now give:
```
CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
```

I haven't committed. The diff is two files.

## events
[assistant] I'll start by reproducing the failure and finding where CREATE properties are parsed.
[tool_use Bash] {"command": "python -c \"\nimport sqlglot\nfor s in ['CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)', 'CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE']:\n    try:\n        print(repr(sqlglot.parse_one(s, read='snowflake')))\n    except Exception as e:\n        print('ERR', type(e).__name__, str(e)[:200])\n\"; grep -n \"CHANGE_TRACKING\\|_parse_property\\b\\|def _parse_create\\|def _parse_schema\\|def _parse_properties\" sqlglot/dialects/snowflake.py sqlglot/parser.py | head -50", "description": "Reproduce parse failure and locate create parsing code"}
[tool_result] ERR ParseError Expecting ). Line 1, Col: 39.
  CREATE TABLE t CHANGE_TRACKING=TRUE ([4mid[0m INT)
Create(
  this=Schema(
    this=Table(
      this=Identifier(this=t, quoted=False)),
    expressions=[
      ColumnDef(
        this=Identifier(this=id, quoted=False),
        kind=DataType(this=DType.INT, nested=False))]),
  kind=TABLE,
  replace=False,
  refresh=False,
  unique=False,
  exists=False,
  properties=Properties(
    expressions=[
      Property(
        this=Var(this=CHANGE_TRACKING
…[631 chars elided]…
roperty() if self._match(TokenType.FORMAT, advance=False) else None
sqlglot/parser.py:7082:        # Skip the generic `key = value` fallback in _parse_property since this
sqlglot/parser.py:7218:    def _parse_schema(self, this: exp.Expr | None = None) -> exp.Expr | None:
sqlglot/parser.py:8761:                        and self._parse_property(),
sqlglot/parser.py:8943:            options = self._parse_csv(self._parse_property)
sqlglot/parser.py:9531:                option = self._parse_property()
[assistant] The first form fails with `Expecting )`, and the second parses. Next I'll read `_parse_create` and the property helpers.
[tool_use Bash] {"command": "sed -n 2360,2480p sqlglot/parser.py", "description": "Read _parse_create implementation"}
[tool_result]     def _parse_create(self) -> exp.Create | exp.Command:
        # Note: this can't be None because we've matched a statement parser
        start = self._prev

        replace = (
            start.token_type == TokenType.REPLACE
            or self._match_pair(TokenType.OR, TokenType.REPLACE)
            or self._match_pair(TokenType.OR, TokenType.ALTER)
        )
        refresh = self._match_pair(TokenType.OR, TokenType.REFRESH)

        unique = self._match(TokenType.UNIQUE)

        if sel
…[3907 chars elided]…

                expression = self._parse_macro_overloads(
                    t.cast(exp.UserDefinedFunction, this), expression, is_table
                )
        elif create_token_type == TokenType.INDEX:
            # Postgres allows anonymous indexes, eg. CREATE INDEX IF NOT EXISTS ON t(c)
            if not self._match(TokenType.ON):
                index = self._parse_id_var()
                anonymous = False
            else:
                index = None
                anonymous = True
[tool_use Bash] {"command": "sed -n 2795,2900p sqlglot/parser.py && echo ---- && sed -n 7218,7240p sqlglot/parser.py", "description": "Read property parsing helpers and _parse_schema"}
[tool_result]     def _parse_property(self) -> exp.Expr | list[exp.Expr] | None:
        if self._match_texts(self.PROPERTY_PARSERS):
            return self.PROPERTY_PARSERS[self._prev.text.upper()](self)

        if self._match(TokenType.DEFAULT) and self._match_texts(self.PROPERTY_PARSERS):
            return self.PROPERTY_PARSERS[self._prev.text.upper()](self, default=True)

        if self._match_text_seq("COMPOUND", "SORTKEY"):
            return self._parse_sortkey(compound=True)

        if self._matc
…[4066 chars elided]…
arse_field_def())
        self._match_r_paren()
        return self.expression(exp.Schema(this=this, expressions=args))

    def _parse_field_def(self) -> exp.Expr | None:
        return self._parse_column_def(self._parse_field(any_token=True))

    def _parse_column_def(
        self, this: exp.Expr | None, computed_column: bool = True
    ) -> exp.Expr | None:
        # column defs are not really columns, they're identifiers
        if isinstance(this, exp.Column):
            this = this.this
[assistant] Now the TABLE branch of `_parse_create`, where the table name and schema get parsed.
[tool_use Bash] {"command": "sed -n 2480,2600p sqlglot/parser.py", "description": "Read rest of _parse_create table branch"}
[tool_result]                 anonymous = True

            this = self._parse_index(index=index, anonymous=anonymous)
        elif (
            create_token_type == TokenType.CONSTRAINT and self._match(TokenType.TRIGGER)
        ) or create_token_type == TokenType.TRIGGER:
            if is_constraint := (create_token_type == TokenType.CONSTRAINT):
                create_token = self._prev

            trigger_name = self._parse_id_var()
            if not trigger_name:
                return self._parse_as
…[4136 chars elided]…
g a table as an alias instead of a SELECT.
                # Here we fallback to this as an alternative.
                if not expression and has_alias:
                    expression = self._try_parse(self._parse_table_parts)

            if create_token_type == TokenType.TABLE:
                # exp.Properties.Location.POST_EXPRESSION
                extend_props(self._parse_properties())

                indexes = []
                while True:
                    index = self._parse_index()
[assistant] The `before=True` hook already exists (`_parse_property_before`). I'll check what it accepts and whether Snowflake's `KEY=VALUE` fallback is reachable from it.
[tool_use Bash] {"command": "grep -n \"_parse_property_before\" -A30 sqlglot/parser.py | sed -n 1,60p; echo ----; grep -n \"PROPERTY_PARSERS\\|PROPERTY_PARSERS_BEFORE\" sqlglot/dialects/snowflake.py; grep -n \"def _parse_sequence_properties\\|PROPERTY_PARSERS_BEFORE\" sqlglot/parser.py | head; echo ----; git log --oneline -3 -- sqlglot/parser.py | cat; git log -S\"_parse_property_before\" --oneline | head -3", "description": "Inspect _parse_property_before and Snowflake property config"}
[tool_result] 2767:    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:
2768-        # only used for teradata currently
2769-        self._match(TokenType.COMMA)
2770-
2771-        kwargs = {
2772-            "no": self._match_text_seq("NO"),
2773-            "dual": self._match_text_seq("DUAL"),
2774-            "before": self._match_text_seq("BEFORE"),
2775-            "default": self._match_text_seq("DEFAULT"),
2776-            "local": (self._match_text_seq("LOCAL") and "LOCAL")
2777-
…[2060 chars elided]…
      return self.expression(
2900-            exp.SettingsProperty(expressions=self._parse_csv(self._parse_assignment))
----
2646:    def _parse_sequence_properties(self) -> exp.SequenceProperties | None:
----
9f18b7705 feat(parser): support `CALLED ON NULL INPUT` function property (#7792)
d4c74a2b6 Feat(bigquery): reject connected adjacent string literals closes #7780
499d1321d fix(postgres): preserve contained-by operator direction CODEX (#7768)
81d5e91a2 Teradata CREATE TABLE options (#1033)
[assistant] The before-schema hook only matches keywords in `PROPERTY_PARSERS` (Teradata-only per the comment). The generic `KEY = VALUE` fallback lives in `_parse_property`, which isn't called before the schema. I'll check where Snowflake's parser is defined and whether `TABLE` goes through this branch.
[tool_use Bash] {"command": "grep -n \"DB_CREATABLES\" -A12 sqlglot/parser.py | head -20; echo ----; grep -n \"class Parser\" -A3 sqlglot/dialects/snowflake.py; grep -n \"    def _parse_\\|PROPERTY\" sqlglot/dialects/snowflake.py | head -40", "description": "Check DB_CREATABLES and Snowflake parser overrides"}
[tool_result] 618:    DB_CREATABLES: t.ClassVar = {
619-        TokenType.DATABASE,
620-        TokenType.DICTIONARY,
621-        TokenType.FILE_FORMAT,
622-        TokenType.MODEL,
623-        TokenType.NAMESPACE,
624-        TokenType.SCHEMA,
625-        TokenType.SEMANTIC_VIEW,
626-        TokenType.SEQUENCE,
627-        TokenType.SINK,
628-        TokenType.SOURCE,
629-        TokenType.STAGE,
630-        TokenType.STORAGE_INTEGRATION,
--
647:        *DB_CREATABLES,
648-    }
649-
650-    TRIGGER_EVENTS: t.ClassVar = {
651-        TokenType.INSERT,
652-        TokenType.UPDATE,
----
[tool_use Bash] {"command": "grep -n \"class Parser\" -A40 sqlglot/dialects/snowflake.py | head -60; echo ----; grep -n \"_parse_property\\|class Parser\" sqlglot/dialects/snowflake.py; echo ----; sed -n 630,647p sqlglot/parser.py", "description": "Inspect Snowflake Parser class and CREATABLES"}
[tool_result] ----
----
        TokenType.STORAGE_INTEGRATION,
        TokenType.STREAMLIT,
        TokenType.TABLE,
        TokenType.TAG,
        TokenType.VIEW,
        TokenType.WAREHOUSE,
    }

    CREATABLES: t.ClassVar = {
        TokenType.COLUMN,
        TokenType.CONSTRAINT,
        TokenType.FOREIGN_KEY,
        TokenType.FUNCTION,
        TokenType.INDEX,
        TokenType.PROCEDURE,
        TokenType.TRIGGER,
        TokenType.TYPE,
        *DB_CREATABLES,
[tool_use Bash] {"command": "cd ~/.cache/lithify/work/repo-b63a38b63828/20261026-195628-snowflake-dialect-in-create-stat/base-1 2>/dev/null || cd ~/.cache/lithify/work/repo-b63a38b63828/20261026-195628-snowflake-dialect-in-create-stat/base-1; pwd; grep -n \"class Parser\" -A30 sqlglot/dialects/snowflake.py | head -45; grep -n \"_parse_property\\|PROPERTY_PARSERS\" sqlglot/dialects/snowflake.py", "description": "Locate Snowflake Parser class definition"}
[tool_result] ~/.cache/lithify/work/repo-b63a38b63828/20261026-195628-snowflake-dialect-in-create-stat/base-1
[assistant] The Snowflake dialect file has no `class Parser` at all. I'll list its classes to see where its parser overrides live.
[tool_use Bash] {"command": "grep -n \"^class \\|^    class \" sqlglot/dialects/snowflake.py; wc -l sqlglot/dialects/snowflake.py; grep -n \"Parser\" sqlglot/dialects/snowflake.py | head", "description": "List classes in Snowflake dialect module"}
[tool_result] 16:class Snowflake(Dialect):
129:    class JSONPathTokenizer(jsonpath.JSONPathTokenizer):
135:    class Tokenizer(tokens.Tokenizer):
     190 sqlglot/dialects/snowflake.py
10:    SnowflakeParser,
133:    Parser = SnowflakeParser
[tool_use Bash] {"command": "sed -n 1,15p sqlglot/dialects/snowflake.py; grep -rn \"class SnowflakeParser\" sqlglot/ ; ls sqlglot/dialects/ | grep -i snow", "description": "Find SnowflakeParser definition"}
[tool_result] from __future__ import annotations

from sqlglot import exp, jsonpath, tokens
from sqlglot.dialects.dialect import (
    Dialect,
    NormalizationStrategy,
)
from sqlglot.generators.snowflake import SnowflakeGenerator
from sqlglot.parsers.snowflake import (
    SnowflakeParser,
)
from sqlglot.tokens import TokenType
from sqlglot.typing.snowflake import EXPRESSION_METADATA


sqlglot/parsers/snowflake.py:329:class SnowflakeParser(parser.Parser):
snowflake.py
[assistant] The Snowflake parser lives in `sqlglot/parsers/snowflake.py`. I'll check it for existing property or create overrides.
[tool_use Bash] {"command": "grep -n \"_parse_property\\|_parse_create\\|def _parse_schema\\|PROPERTY_PARSERS\\|CREATE\" sqlglot/parsers/snowflake.py | head -40; echo ----; grep -rn \"_parse_property_before\\|properties(before=True)\" sqlglot/ | head", "description": "Search Snowflake parser for property/create hooks"}
[tool_result] 767:    PROPERTY_PARSERS = {
768:        **parser.Parser.PROPERTY_PARSERS,
977:        return self.expression(exp.Tags(expressions=self._parse_wrapped_csv(self._parse_property)))
1030:    def _parse_create(self) -> exp.Create | exp.Command:
1031:        expression = super()._parse_create()
----
sqlglot/parser.py:2554:            extend_props(self._parse_properties(before=True))
sqlglot/parser.py:2767:    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:
sqlglot/parser.py:2873:                prop = self._parse_property_before()
[tool_use Bash] {"command": "sed -n 1025,1060p sqlglot/parsers/snowflake.py; echo ----; sed -n 765,780p sqlglot/parsers/snowflake.py", "description": "Read Snowflake _parse_create override and PROPERTY_PARSERS"}
[tool_result]                 self.raise_error("Expected ON after ROW ACCESS POLICY name")
            expressions = self._parse_wrapped_csv(self._parse_id_var)

        return self.expression(exp.RowAccessProperty(this=policy, expressions=expressions))

    def _parse_create(self) -> exp.Create | exp.Command:
        expression = super()._parse_create()
        if isinstance(expression, exp.Create) and expression.kind in self.NON_TABLE_CREATABLES:
            # Replace the Table node with the enclosed Identi
…[1435 chars elided]…
bda self: self._parse_file_format_property(),
        "LOCATION": lambda self: self._parse_location_property(),
        "ROW": lambda self: (
            self._parse_row_access_policy()
            if self._match_text_seq("ACCESS", "POLICY")
            else self._parse_row()
        ),
        "TAG": lambda self: self._parse_tag(),
        "USING": lambda self: (
            self._match_text_seq("TEMPLATE")
            and self.expression(exp.UsingTemplateProperty(this=self._parse_statement()))
[assistant] Root cause: the Snowflake parser has no override for the before-schema hook, so the `KEY = VALUE` fallback in `_parse_property` never runs there. Before editing, I'll confirm the current output for both forms and check the baseline test state.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile('CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE', read='snowflake', write='snowflake'))\n\" ; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Check baseline output and run test suite"}
[tool_result] ['CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE']
.......................................... [ 78%]
...................................................................................................................................................................................................................................................                                            [100%]
1126 passed, 18271 subtests passed in 71.74s (0:01:11)
[assistant] Baseline is green (1126 passed). I'll add a Snowflake-only override of the before-schema hook that falls back to the generic `KEY = VALUE` property parser.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-195628-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py", "old_string": "    def _parse_create(self) -> exp.Create | exp.Command:\n        expression = super()._parse_create()", "new_string": "    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:\n        # Snowflake accepts `KEY = VALUE` properties before the column definitions too\n        return super()._parse_property_before() or self._parse_property()\n\n    def _parse_create(self) -> exp.Create | exp.Command:\n        expression = super()._parse_create()"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-195628-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfor s in ['CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)', 'CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE', 'CREATE TABLE t CHANGE_TRACKING=TRUE, DATA_RETENTION_TIME_IN_DAYS=5 (id INT, name TEXT) COMMENT=\\'x\\'', 'CREATE TABLE t (id INT)', 'CREATE TABLE t AS SELECT 1', 'CREATE TABLE t LIKE u', 'CREATE SEQUENCE s START=1 INCREMENT=2']:\n    try:\n        print(sqlglot.transpile(s, read='snowflake', write='snowflake')[0])\n    except Exception as e:\n        print('ERR', s, type(e).__name__, str(e).splitlines()[0])\n\"", "description": "Verify both forms and edge cases parse"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[assistant] `-I` drops the working directory from `sys.path`, so `sqlglot` wasn't importable. I'll point `PYTHONPATH` at the worktree instead.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)', 'CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE', 'CREATE TABLE t CHANGE_TRACKING=TRUE, DATA_RETENTION_TIME_IN_DAYS=5 (id INT, name TEXT) COMMENT=\\'x\\'', 'CREATE TABLE t (id INT)', 'CREATE TABLE t AS SELECT 1', 'CREATE TABLE t LIKE u', 'CREATE SEQUENCE s START=1 INCREMENT=2']:\n    try:\n        print(sqlglot.transpile(s, read='snowflake', write='snowflake')[0])\n    except Exception as e:\n        print('ERR', s, type(e).__name__, str(e).splitlines()[0])\n\"", "description": "Verify both forms and edge cases parse"}
[tool_result] CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
CREATE TABLE t (id INT, name VARCHAR) COMMENT='x' CHANGE_TRACKING=TRUE DATA_RETENTION_TIME_IN_DAYS=5
CREATE TABLE t (id INT)
CREATE TABLE t AS SELECT 1
CREATE TABLE t LIKE u
CREATE SEQUENCE s START WITH 1 INCREMENT BY 2
[assistant] Both forms now parse and generate the same SQL, and the other edge cases still work. Next I'll add a regression test next to the existing Snowflake CREATE tests.
[tool_use Bash] {"command": "grep -n \"CHANGE_TRACKING\\|def test_ddl\\|def test_create\" tests/dialects/test_snowflake.py | head -20", "description": "Find Snowflake DDL test methods"}
[tool_result] 4240:    def test_ddl(self):
5758:        self.validate_identity("ALTER TABLE foo SET CHANGE_TRACKING=FALSE")
5769:        self.validate_identity("ALTER TABLE foo UNSET DATA_RETENTION_TIME_IN_DAYS, CHANGE_TRACKING")
5941:    def test_create_view_copy_grants(self):
5963:    def test_create_view_row_access_policy(self):
6069:    def test_create_sequence(self):
[tool_use Bash] {"command": "sed -n 5941,5963p tests/dialects/test_snowflake.py", "description": "Read a neighboring Snowflake CREATE test for style"}
[tool_result]     def test_create_view_copy_grants(self):
        # for normal views, 'COPY GRANTS' goes *after* the column list. ref: https://docs.snowflake.com/en/sql-reference/sql/create-view#syntax
        self.validate_identity(
            "CREATE OR REPLACE VIEW FOO (A, B) COPY GRANTS AS SELECT A, B FROM TBL"
        )

        # for materialized views, 'COPY GRANTS' must go *before* the column list or an error will be thrown. ref: https://docs.snowflake.com/en/sql-reference/sql/create-materialized-vie
…[213 chars elided]…
ist and other properties still go after
        self.validate_identity(
            "CREATE OR REPLACE MATERIALIZED VIEW FOO COPY GRANTS (A, B) COMMENT='foo' TAG (a='b') AS SELECT A, B FROM TBL"
        )

        # no COPY GRANTS
        self.validate_identity("CREATE OR REPLACE VIEW FOO (A, B) AS SELECT A, B FROM TBL")
        self.validate_identity(
            "CREATE OR REPLACE MATERIALIZED VIEW FOO (A, B) AS SELECT A, B FROM TBL"
        )

    def test_create_view_row_access_policy(self):
[assistant] I'll add a focused test that checks the before-schema form normalizes to the same SQL as the after-schema form, and that the after-schema form round-trips.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-195628-snowflake-dialect-in-create-stat/base-1/tests/dialects/test_snowflake.py", "old_string": "    def test_create_view_copy_grants(self):", "new_string": "    def test_create_table_properties_before_schema(self):\n        self.validate_identity(\"CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE\")\n        self.validate_all(\n            \"CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE\",\n            read={\n                \"snowflake\": \"CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)\",\n            },\n        )\n\n    def test_create_view_copy_grants(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-195628-snowflake-dialect-in-create-stat/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py -k properties_before_schema 2>&1 | tail -3; git stash list >/dev/null; $PY -m pytest -q -p no:cacheprovider --color=no tests/ 2>&1 | tail -3", "description": "Run new test, then full suite"}
[tool_result] .                                                                       [100%]
1 passed, 96 deselected, 1 subtests passed in 0.08s
FAILED tests/dialects/test_snowflake.py::TestSnowflake::test_snowflake - sqlg...
SUBFAILED[snowflake -> CREATE TABLE t (col1 DATETIME2(2))] tests/dialects/test_tsql.py::TestTSQL::test_types_date
9 failed, 1123 passed, 17485 subtests passed in 61.35s (0:01:01)
[assistant] The new test passes, but the full suite has 9 failures that the baseline didn't have. I'll look at all of them before deciding anything.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/ 2>&1 | grep -E \"^(FAILED|SUBFAILED|E  )\" | head -60", "description": "List failing tests and error lines"}
[tool_result] E           sqlglot.errors.ParseError: Expecting ). Line 1, Col: 25.
E             CREATE TABLE t (a VECTOR[4m([0mINT, 10))
E           sqlglot.errors.ParseError: Expecting ). Line 1, Col: 25.
E             CREATE TABLE t (a VECTOR[4m([0m10))
E           sqlglot.errors.ParseError: Expecting ). Line 1, Col: 41.
E             CREATE VIEW v (COL1 COMMENT [4m'description'[0m) WITH ROW ACCESS POLICY db.schema.policy ON (COL1) COMMENT='some comment' AS (SELECT a FROM t1 LEFT
E           sqlglot.
…[1387 chars elided]…
ts/dialects/test_snowflake.py::TestSnowflake::test_ddl
SUBFAILED[Constraint prefix: ] tests/dialects/test_snowflake.py::TestSnowflake::test_ddl
FAILED tests/dialects/test_snowflake.py::TestSnowflake::test_ddl - sqlglot.er...
FAILED tests/dialects/test_snowflake.py::TestSnowflake::test_rely_options - s...
FAILED tests/dialects/test_snowflake.py::TestSnowflake::test_snowflake - sqlg...
SUBFAILED[snowflake -> CREATE TABLE t (col1 DATETIME2(2))] tests/dialects/test_tsql.py::TestTSQL::test_types_date
[assistant] The regressions come from one bug in my override. The generic `_parse_property` fallback calls `_parse_column` on the `(` that opens the column list, which parses the whole schema as an expression and raises. I'll restrict the fallback to a key followed directly by `=`, so it never runs on the `(`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-195628-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py", "old_string": "    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:\n        # Snowflake accepts `KEY = VALUE` properties before the column definitions too\n        return super()._parse_property_before() or self._parse_property()", "new_string": "    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:\n        prop = super()._parse_property_before()\n        if prop or self._next.token_type != TokenType.EQ:\n            return prop\n\n        # Snowflake also accepts `KEY = VALUE` properties before the column definitions\n        return self._parse_property()"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-195628-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"^from sqlglot.tokens\\|TokenType\" sqlglot/parsers/snowflake.py | head -3; PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfor s in ['CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)', 'CREATE TABLE t CHANGE_TRACKING=TRUE, DATA_RETENTION_TIME_IN_DAYS=5 (id INT, name TEXT) COMMENT=\\'x\\'', 'CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE']:\n    print(sqlglot.transpile(s, read='snowflake', write='snowflake')[0])\n\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/ 2>&1 | tail -3", "description": "Check edge cases and rerun full test suite"}
[tool_result] 20:from sqlglot.tokens import TokenType
336:    TYPE_TOKENS = {*parser.Parser.TYPE_TOKENS, TokenType.FILE}
337:    STRUCT_TYPE_TOKENS = {*parser.Parser.STRUCT_TYPE_TOKENS, TokenType.FILE}
CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
CREATE TABLE t (id INT, name VARCHAR) COMMENT='x' CHANGE_TRACKING=TRUE DATA_RETENTION_TIME_IN_DAYS=5
CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
.............................................................. [ 88%]
.......................................................................................................................................                                          [100%]
1127 passed, 18272 subtests passed in 57.83s
[assistant] All 1127 tests pass: the 1126 baseline plus the new test. I'll run the project's exact check command and the linter on the two changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; ($PY -m ruff check sqlglot/parsers/snowflake.py tests/dialects/test_snowflake.py && $PY -m ruff format --check sqlglot/parsers/snowflake.py tests/dialects/test_snowflake.py) 2>&1 | tail -4; git status --short; git diff", "description": "Run project test command, lint, and show diff"}
[tool_result] Command did not complete within its 120s timeout and was moved to the background (ID: bqcifm2r1). Output is being written to: /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-b63a38b63828-20261026-195628-snowflake-dialect-in-create-stat-base-1/b4ab36ec-90fe-422a-9b6d-89da7be5a54f/tasks/bqcifm2r1.output. You will be notified when it completes. If it is still running after 10m in the background, it will be stopped and you will be notified. To check interim output, use Read on that file path.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff check sqlglot/parsers/snowflake.py tests/dialects/test_snowflake.py && $PY -m ruff format --check sqlglot/parsers/snowflake.py tests/dialects/test_snowflake.py) 2>&1 | tail -4; git status --short; git diff", "description": "Lint changed files and show diff"}
[tool_result] All checks passed!
2 files already formatted
 M sqlglot/parsers/snowflake.py
 M tests/dialects/test_snowflake.py
diff --git a/sqlglot/parsers/snowflake.py b/sqlglot/parsers/snowflake.py
index c19a6c8e4..475d194d3 100644
--- a/sqlglot/parsers/snowflake.py
+++ b/sqlglot/parsers/snowflake.py
@@ -1027,6 +1027,14 @@ class SnowflakeParser(parser.Parser):
 
         return self.expression(exp.RowAccessProperty(this=policy, expressions=expressions))
 
+    def _parse_property_before(self) -> exp.Expr | 
…[829 chars elided]…
date_identity("CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE")
+        self.validate_all(
+            "CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE",
+            read={
+                "snowflake": "CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)",
+            },
+        )
+
     def test_create_view_copy_grants(self):
         # for normal views, 'COPY GRANTS' goes *after* the column list. ref: https://docs.snowflake.com/en/sql-reference/sql/create-view#syntax
         self.validate_identity(
[assistant] Lint and formatting pass. The full-suite run was moved to the background, so I'll check its output file.
[tool_use Bash] {"command": "sleep 60; tail -3 /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-b63a38b63828-20261026-195628-snowflake-dialect-in-create-stat-base-1/b4ab36ec-90fe-422a-9b6d-89da7be5a54f/tasks/bqcifm2r1.output", "description": "Wait briefly and read background test output"}
[tool_result ERROR] <tool_use_error>Blocked: sleep 60 followed by: tail -3 /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-b63a38b63828-20261026-195628-snowflake-dialect-in-create-stat-base-1/b4ab36ec-90fe-422a-9b6d-89da7be5a54f/tasks/bqcifm2r1.output. To wait for a condition, use Monitor with an until-loop (e.g. `until <check>; do sleep 2; done`). To wait for a command you started, use run_in_background: true. Do not chain shorter sleeps to work around this block.</tool_use_error>
[tool_use Read] {"file_path": "/private/tmp/claude-501/-Users-user--cache-lithify-work-repo-b63a38b63828-20261026-195628-snowflake-dialect-in-create-stat-base-1/b4ab36ec-90fe-422a-9b6d-89da7be5a54f/tasks/bqcifm2r1.output", "description": "Read background test output"}
[tool_result] <system-reminder>Warning: the file exists but the contents are empty.</system-reminder>
[assistant] The background output is still empty, which is normal for `-q` until the run finishes. The code hasn't changed since the 1127-pass run, but I'll run the exact project command in the foreground with a longer timeout so the result is confirmed.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2", "description": "Run full project test command in foreground", "timeout": 400000}
[tool_result] .......................................................................................................................................                                          [100%]
1127 passed, 18272 subtests passed in 52.59s
[assistant] Snowflake now accepts `KEY = VALUE` properties before the column list, and both forms produce the same SQL. The full project test suite passes (1127 tests, up from 1126 with the new test), and ruff check and format are clean on the changed files.

**Cause:** The parser has a hook for properties that appear before the schema, but it only recognised keywords from the property table. The generic `KEY = VALUE` fallback was never reached in that position, so `CHANGE_TRACKING=TRUE` before `(id INT)` failed.

**Fix** (`sqlglot/parsers/snowflake.py`): Snowflake's parser now overrides that hook and fal
…[73 chars elided]…
=`. My first version tried the fallback on any token. That broke nine existing column-definition tests, because the generic parser treated the column list's opening `(` as an expression and raised. The `=` guard fixed all nine. The change is scoped to Snowflake, so other dialects are unaffected.

**Test** (`tests/dialects/test_snowflake.py`): `test_create_table_properties_before_schema` round-trips the after-schema form and checks that the before-schema form normalises to it.

Both forms now give:
```
CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
```

I haven't committed. The diff is two files.
