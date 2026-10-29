# trajectory base-1

final message:
Snowflake now parses `KEY=VALUE` properties before the column list, so `CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)` parses and generates `CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE`. The full suite passes (1127 tests), and ruff format and lint are clean. I haven't committed anything.

The change is a small override in `sqlglot/parsers/snowflake.py`. The base parser only accepts dialect-registered keywords (like `COMMENT=`) before the schema, so `CHANGE_TRACKING` was never tried there. The override falls back to the generic property parser, but only when the next token is `=`. Without that check, the first attempt broke nine existing tests: the generic parser speculatively parses the `(` as a column list and raises on types like `TIMESTAMP_NTZ(2)`.

I added `test_create_table_properties_before_schema` to `tests/dialects/test_snowflake.py`. It covers a single property and a comma-separated pair. Multiple properties come out space-separated, which matches how Snowflake's own output orders them after the column list.

## events
[tool_use Bash] {"command": "grep -n \"CHANGE_TRACKING\\|_parse_create\\|PROPERTIES_LOCATION\\|POST_SCHEMA\\|POST_EXPRESSION\\|POST_CREATE\" sqlglot/dialects/snowflake.py sqlglot/parser.py | head -80; grep -n \"CHANGE_TRACKING\" -r tests/dialects/test_snowflake.py | head", "description": "Locate create/property parsing code"}
[tool_result] sqlglot/parser.py:1089:        TokenType.CREATE: lambda self: self._parse_create(),
sqlglot/parser.py:1286:        "LIKE": lambda self: self._parse_create_like(),
sqlglot/parser.py:1381:        "LIKE": lambda self: self._parse_create_like(),
sqlglot/parser.py:2360:    def _parse_create(self) -> exp.Create | exp.Command:
sqlglot/parser.py:2389:            # exp.Properties.Location.POST_CREATE
sqlglot/parser.py:2417:            # exp.Properties.Location.POST_SCHEMA ("schema" here is the UDF's type
…[16 chars elided]…
lot/parser.py:2558:            # exp.Properties.Location.POST_SCHEMA and POST_WITH
sqlglot/parser.py:2595:                # exp.Properties.Location.POST_EXPRESSION
sqlglot/parser.py:3350:    def _parse_create_like(self) -> exp.LikeProperty | None:
tests/dialects/test_snowflake.py:5758:        self.validate_identity("ALTER TABLE foo SET CHANGE_TRACKING=FALSE")
tests/dialects/test_snowflake.py:5769:        self.validate_identity("ALTER TABLE foo UNSET DATA_RETENTION_TIME_IN_DAYS, CHANGE_TRACKING")
[tool_use Bash] {"command": "sed -n 2360,2640p sqlglot/parser.py", "description": "Read _parse_create implementation"}
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
…[10680 chars elided]…
            exp.Create(
                this=this,
                kind=self.dialect.CREATABLE_KIND_MAPPING.get(create_kind_text) or create_kind_text,
                replace=replace,
                refresh=refresh,
                unique=unique,
                expression=expression,
                exists=exists,
                properties=properties,
                indexes=indexes,
                no_schema_binding=no_schema_binding,
                begin=begin,
                clone=clone,
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)', 'CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE', 'CREATE TABLE t COMMENT=\\'x\\' (id INT)', 'CREATE TABLE t CHANGE_TRACKING=TRUE AS SELECT 1']:\n    try:\n        e = sqlglot.parse_one(s, read='snowflake'); print(type(e).__name__, '|', e.sql('snowflake'), '|', repr(e.args.get('properties'))[:200])\n    except Exception as ex: print('ERR', s, ex)\n\"; grep -n \"def _parse_properties\" -A40 sqlglot/parser.py | head -60", "description": "Reproduce parse failures for both property positions"}
[tool_result] ERR CREATE TABLE t CHANGE_TRACKING=TRUE (id INT) Expecting ). Line 1, Col: 39.
  CREATE TABLE t CHANGE_TRACKING=TRUE ([4mid[0m INT)
Create | CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE | Properties(
  expressions=[
    Property(
      this=Var(this=CHANGE_TRACKING),
      value=Boolean(this=True))])
Create | CREATE TABLE t (id INT) COMMENT='x' | Properties(
  expressions=[
    SchemaCommentProperty(
      this=Literal(this='x', is_string=True))])
Create | CREATE TABLE t CHANGE_TRACKING=TRUE A
…[1283 chars elided]…
(self) -> exp.SettingsProperty:
2899-        return self.expression(
2900-            exp.SettingsProperty(expressions=self._parse_csv(self._parse_assignment))
2901-        )
2902-
2903-    def _parse_called_on_null_input_property(self) -> exp.CalledOnNullInputProperty | None:
2904-        if not self._match_text_seq("ON", "NULL", "INPUT"):
2905-            self._retreat(self._index - 1)
2906-            return None
2907-
2908-        return self.expression(exp.CalledOnNullInputProperty())
2909-
[tool_use Bash] {"command": "grep -n \"def _parse_property_before\" -A30 sqlglot/parser.py; grep -n \"def _parse_property(self\" -A50 sqlglot/parser.py | head -80; grep -n \"PROPERTY_PARSERS\\b\" sqlglot/dialects/snowflake.py; grep -n \"CHANGE_TRACKING\\|DATA_RETENTION\\|PROPERTY_PARSERS\\|_parse_property\" sqlglot/dialects/snowflake.py | head -30", "description": "Inspect property parsing helpers"}
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
…[2879 chars elided]…
ndlerProperty(this=self._parse_var_or_string()))
2836-
2837-        self._match(TokenType.ALIAS)
2838-        input_format = self._parse_string() if self._match_text_seq("INPUTFORMAT") else None
2839-        output_format = self._parse_string() if self._match_text_seq("OUTPUTFORMAT") else None
2840-
2841-        return self.expression(
2842-            exp.FileFormatProperty(
2843-                this=(
2844-                    self.expression(
2845-                        exp.InputOutputFormat(
[assistant] The generic `KEY=VALUE` parser only runs after the schema, and the pre-name hook (`_parse_property_before`) only knows dialect-specific keywords. I'll check how Snowflake's parser is structured before deciding where to hook in.
[tool_use Bash] {"command": "grep -n \"class Parser\" -A6 sqlglot/dialects/snowflake.py; grep -n \"    def _parse_\\|    def \" sqlglot/dialects/snowflake.py | sed -n 1,60p | grep -n \"Parser\\|_parse_\" | head -40; grep -n \"CHANGE_TRACKING\\|COPY GRANTS\" tests/dialects/test_snowflake.py | head; grep -n \"def test_create\" tests/dialects/test_snowflake.py", "description": "Inspect Snowflake parser class and existing create tests"}
[tool_result] 4260:        self.validate_identity("CREATE OR REPLACE TABLE foo COPY GRANTS USING TEMPLATE (SELECT 1)")
4265:        self.validate_identity("CREATE OR REPLACE VIEW foo (uid) COPY GRANTS AS (SELECT 1)")
5758:        self.validate_identity("ALTER TABLE foo SET CHANGE_TRACKING=FALSE")
5769:        self.validate_identity("ALTER TABLE foo UNSET DATA_RETENTION_TIME_IN_DAYS, CHANGE_TRACKING")
5942:        # for normal views, 'COPY GRANTS' goes *after* the column list. ref: https://docs.snowflake.com/e
…[310 chars elided]…
ized-view#syntax
5949:            "CREATE OR REPLACE MATERIALIZED VIEW FOO COPY GRANTS (A, B) AS SELECT A, B FROM TBL"
5952:        # check that only 'COPY GRANTS' goes before the column list and other properties still go after
5954:            "CREATE OR REPLACE MATERIALIZED VIEW FOO COPY GRANTS (A, B) COMMENT='foo' TAG (a='b') AS SELECT A, B FROM TBL"
5941:    def test_create_view_copy_grants(self):
5963:    def test_create_view_row_access_policy(self):
6069:    def test_create_sequence(self):
[tool_use Bash] {"command": "grep -n \"class \\|PROPERTY_PARSERS\\|_parse_\" sqlglot/dialects/snowflake.py | sed -n 1,80p; sed -n 5938,5965p tests/dialects/test_snowflake.py", "description": "List Snowflake dialect classes and parser hooks"}
[tool_result] 16:class Snowflake(Dialect):
129:    class JSONPathTokenizer(jsonpath.JSONPathTokenizer):
135:    class Tokenizer(tokens.Tokenizer):
            },
        )

    def test_create_view_copy_grants(self):
        # for normal views, 'COPY GRANTS' goes *after* the column list. ref: https://docs.snowflake.com/en/sql-reference/sql/create-view#syntax
        self.validate_identity(
            "CREATE OR REPLACE VIEW FOO (A, B) COPY GRANTS AS SELECT A, B FROM TBL"
        )

        # for materialized
…[497 chars elided]…
COPY GRANTS (A, B) COMMENT='foo' TAG (a='b') AS SELECT A, B FROM TBL"
        )

        # no COPY GRANTS
        self.validate_identity("CREATE OR REPLACE VIEW FOO (A, B) AS SELECT A, B FROM TBL")
        self.validate_identity(
            "CREATE OR REPLACE MATERIALIZED VIEW FOO (A, B) AS SELECT A, B FROM TBL"
        )

    def test_create_view_row_access_policy(self):
        self.validate_identity(
            "CREATE VIEW v WITH ROW ACCESS POLICY mypolicy ON (col1) AS SELECT col1 FROM t1"
[assistant] Snowflake has no `Parser` subclass yet; it inherits the base one. The pre-name hook already handles registered keywords like `COMMENT=`, but `CHANGE_TRACKING` isn't registered, so it falls through to the post-schema-only path. I'll check the imports and how other dialects declare a parser before adding one.
[tool_use Bash] {"command": "sed -n 1,16p sqlglot/dialects/snowflake.py; sed -n 125,140p sqlglot/dialects/snowflake.py; grep -n \"class Parser(parser.Parser)\" -A4 sqlglot/dialects/teradata.py | head", "description": "Read Snowflake imports and sample Parser subclass"}
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


class Snowflake(Dialect):
            and not identifier.quoted
            and identifier.name.lower() == "dual"
        )

    class JSONPathTokenizer(jsonpath.JSONPathTokenizer):
        SINGLE_TOKENS = jsonpath.JSONPathTokenizer.SINGLE_TOKENS.copy()
        SINGLE_TOKENS.pop("$")

    Parser = SnowflakeParser

    class Tokenizer(tokens.Tokenizer):
        STRING_ESCAPES = ["\\", "'"]
        HEX_STRINGS = [("x'", "'"), ("X'", "'")]
        RAW_STRINGS = ["$$"]
        COMMENTS = ["--", "//", ("/*", "*/")]
        NESTED_COMMENTS = False
[assistant] The parser lives in `sqlglot/parsers/snowflake.py`. Let me read that file.
[tool_use Bash] {"command": "grep -n \"class \\|    def \" sqlglot/parsers/snowflake.py | head -80; grep -n \"^from\\|^import\" sqlglot/parsers/snowflake.py", "description": "Outline the Snowflake parser module"}
[tool_result] 82:    def _builder(args: list, dialect: Dialect) -> exp.Func:
133:    def _builder(args: list) -> B | exp.Anonymous:
232:    def _builder(args: list, dialect: Dialect) -> E:
323:    def _parse(self: SnowflakeParser) -> exp.Show:
329:class SnowflakeParser(parser.Parser):
921:    def _parse_directory(self) -> exp.DirectoryStage:
926:    def _parse_describe(self) -> exp.Describe:
952:    def _parse_use(self) -> exp.Use:
960:    def _negate_range(self, this: exp.Expr | None = None) -> exp.Expr | No
…[1479 chars elided]…
.StrPosition:
1338:    def _parse_substring(self) -> exp.Substring:
1343:    def build_cast(self, strict: bool, **kwargs) -> exp.Expr:
1355:    def _parse_window(self, this: exp.Expr | None, alias: bool = False) -> exp.Expr | None:
1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, parser
6:from sqlglot.trie import new_trie
7:from sqlglot.dialects.dialect import (
19:from sqlglot.helper import is_date_unit, is_int, seq_get
20:from sqlglot.tokens import TokenType
[tool_use Bash] {"command": "sed -n 1000,1040p sqlglot/parsers/snowflake.py", "description": "Read Snowflake _parse_with_property and _parse_create"}
[tool_result]             return self._parse_tag()

        return None

    def _parse_with_property(self) -> exp.Expr | None | list[exp.Expr]:
        if self._match(TokenType.TAG):
            return self._parse_tag()

        if self._match_text_seq("ROW", "ACCESS", "POLICY"):
            return self._parse_row_access_policy()

        return super()._parse_with_property()

    def _parse_row_access_policy(self) -> exp.RowAccessProperty:
        # GET_DDL outputs #unknown_policy when the user lacks privil
…[762 chars elided]…
r()._parse_create()
        if isinstance(expression, exp.Create) and expression.kind in self.NON_TABLE_CREATABLES:
            # Replace the Table node with the enclosed Identifier
            expression.this.replace(expression.this.this)

        return expression

    # https://docs.snowflake.com/en/sql-reference/functions/date_part.html
    # https://docs.snowflake.com/en/sql-reference/functions-date-time.html#label-supported-date-time-parts
    def _parse_date_part(self) -> exp.Expr | None:
[assistant] I'll add a Snowflake-only override of `_parse_property_before` that falls back to the generic property parser. Then I'll run the Snowflake tests and the full suite, since the hook fires for every creatable in the Snowflake dialect.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-132915-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py", "old_string": "        return expression\n\n    # https://docs.snowflake.com/en/sql-reference/functions/date_part.html", "new_string": "        return expression\n\n    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:\n        # Snowflake also accepts KEY=VALUE properties before the column definitions, e.g. CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)\n        return super()._parse_property_before() or self._parse_property()\n\n    # https://docs.snowflake.com/en/sql-reference/functions/date_part.html"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-132915-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)', 'CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE', 'CREATE TABLE t CHANGE_TRACKING=TRUE, DATA_RETENTION_TIME_IN_DAYS=5 (id INT)', 'CREATE TABLE t COMMENT=\\'x\\' (id INT)', 'CREATE SEQUENCE s START 1 INCREMENT 2']:\n    try:\n        e = sqlglot.parse_one(s, read='snowflake'); print(e.sql('snowflake'))\n    except Exception as ex: print('ERR', s, ex)\n\"; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify new parse and run full test suite"}
[tool_result] CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE DATA_RETENTION_TIME_IN_DAYS=5
CREATE TABLE t (id INT) COMMENT='x'
CREATE SEQUENCE s START WITH 1 INCREMENT BY 2
E           sqlglot.errors.ParseError: Expecting ). Line 1, Col: 35.
E             CREATE TABLE t (col1 TIMESTAMP_NTZ[4m([0m2))

sqlglot/parser.py:2007: ParseError
=========================== short test summary info ============================
SUBFAI
…[422 chars elided]…
SUBFAILED[Constraint prefix: ] tests/dialects/test_snowflake.py::TestSnowflake::test_ddl
FAILED tests/dialects/test_snowflake.py::TestSnowflake::test_ddl - sqlglot.er...
FAILED tests/dialects/test_snowflake.py::TestSnowflake::test_rely_options - s...
FAILED tests/dialects/test_snowflake.py::TestSnowflake::test_snowflake - sqlg...
SUBFAILED[snowflake -> CREATE TABLE t (col1 DATETIME2(2))] tests/dialects/test_tsql.py::TestTSQL::test_types_date
9 failed, 1122 passed, 17484 subtests passed in 56.70s
[assistant] The new parse works, but the full suite shows 9 regressions. I'll check where the fallback is reached from in the failing cases.
[tool_use Bash] {"command": "grep -n \"_parse_property_before\\|_parse_properties(before\" sqlglot/*.py sqlglot/*/*.py; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['CREATE TABLE t (col1 TIMESTAMP_NTZ(2))','CREATE TABLE t (a VECTOR(10))']:\n    try: print(sqlglot.parse_one(s, read='snowflake').sql('snowflake'))\n    except Exception as ex: print('ERR', s, str(ex)[:200])\n\"", "description": "Find callers and reproduce a failing case"}
[tool_result] sqlglot/parser.py:2554:            extend_props(self._parse_properties(before=True))
sqlglot/parser.py:2767:    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:
sqlglot/parser.py:2873:                prop = self._parse_property_before()
sqlglot/parsers/snowflake.py:1038:    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:
sqlglot/parsers/snowflake.py:1040:        return super()._parse_property_before() or self._parse_property()
ERR CREATE TABLE t (col1 TIMESTAMP_NTZ(2)) Expecting ). Line 1, Col: 35.
  CREATE TABLE t (col1 TIMESTAMP_NTZ[4m([0m2))
ERR CREATE TABLE t (a VECTOR(10)) Expecting ). Line 1, Col: 25.
  CREATE TABLE t (a VECTOR[4m([0m10))
[tool_use Bash] {"command": "grep -n \"def _parse_sequence_properties\" -A25 sqlglot/parser.py | head -40; grep -n \"def _parse_column(self\" -A12 sqlglot/parser.py | head -20", "description": "Inspect sequence property and column parsing helpers"}
[tool_result] 2646:    def _parse_sequence_properties(self) -> exp.SequenceProperties | None:
2647-        seq = exp.SequenceProperties()
2648-
2649-        options = []
2650-        index = self._index
2651-
2652-        while self._curr:
2653-            self._match(TokenType.COMMA)
2654-            if self._match_text_seq("INCREMENT"):
2655-                self._match_text_seq("BY")
2656-                self._match_text_seq("=")
2657-                seq.set("increment", self._parse_term())
2658-           
…[1018 chars elided]…
        this = self._parse_column_reference()
6579-            if not this:
6580-                this = self._parse_bracket(this)
6581-            column = self._parse_column_ops(this) if this else this
6582-
6583-        if column:
6584-            if self.dialect.SUPPORTS_COLUMN_JOIN_MARKS:
6585-                column.set("join_mark", self._match(TokenType.JOIN_MARKER))
6586-            if self.COLON_IS_VARIANT_EXTRACT:
6587-                column = self._parse_colon_as_variant_extract(column)
[tool_use Bash] {"command": "sed -n 2671,2690p sqlglot/parser.py", "description": "Read end of sequence property parser"}
[tool_result]             else:
                opt = self._parse_var_from_options(self.CREATE_SEQUENCE, raise_unmatched=False)
                if opt:
                    options.append(opt)
                else:
                    break

        seq.set("options", options if options else None)
        return None if self._index == index else seq

    def _parse_trigger_events(self) -> list[exp.TriggerEvent]:
        events = []

        while True:
            event_type = self._match_set(self.TRIGGER_EVENTS) and self._prev.text.upper()

            if not event_type:
                self.raise_error("Expected trigger event (INSERT, UPDATE, DELETE, TRUNCATE)")

            columns = (
[assistant] Found it: `_parse_property` calls `_parse_column()` on the `(` before checking for `=`. That speculatively parses the parenthesised column list and raises on `TIMESTAMP_NTZ(2)`. I'll only fall back to the generic property parser when the next token is `=`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-132915-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py", "old_string": "        return super()._parse_property_before() or self._parse_property()", "new_string": "        prop = super()._parse_property_before()\n        if prop is None and self._next and self._next.token_type == TokenType.EQ:\n            return self._parse_property()\n        return prop"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-132915-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[assistant] Now I'll add a test next to the existing Snowflake create-view tests, then rerun the suite.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-132915-snowflake-dialect-in-create-stat/base-1/tests/dialects/test_snowflake.py", "old_string": "    def test_create_view_row_access_policy(self):", "new_string": "    def test_create_table_properties_before_schema(self):\n        self.validate_identity(\"CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE\
…[126 chars elided]…
": \"CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE\"},\n        )\n        self.validate_all(\n            \"CREATE TABLE t CHANGE_TRACKING=TRUE, DATA_RETENTION_TIME_IN_DAYS=5 (id INT)\",\n            write={\n                \"snowflake\": \"CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE DATA_RETENTION_TIME_IN_DAYS=5\"\n            },\n        )\n\n    def test_create_view_row_access_policy(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-132915-snowflake-dialect-in-create-stat/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -6; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py -k properties_before 2>&1 | tail -2; git status --short", "description": "Run full suite, new test, and check git status"}
[tool_result] ............................................. [ 74%]
.......................................... [ 78%]
................................................ [ 82%]
.............................................................. [ 87%]
........................................................................................................................................                                         [100%]
1127 passed, 18273 subtests passed in 52.06s
.                                                                      [100%]
1 passed, 96 deselected, 2 subtests passed in 0.06s
 M sqlglot/parsers/snowflake.py
 M tests/dialects/test_snowflake.py
[assistant] The full suite passes (1127). Next I'll run the project's linter and formatter on the two changed files.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff --version && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/snowflake.py tests/dialects/test_snowflake.py && <work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/snowflake.py tests/dialects/test_snowflake.py) 2>&1 | tail -8; git diff", "description": "Run ruff format and lint checks on changed files"}
[tool_result] ruff 0.15.6
2 files already formatted
All checks passed!
diff --git a/sqlglot/parsers/snowflake.py b/sqlglot/parsers/snowflake.py
index c19a6c8e4..45ac7cef3 100644
--- a/sqlglot/parsers/snowflake.py
+++ b/sqlglot/parsers/snowflake.py
@@ -1035,6 +1035,13 @@ class SnowflakeParser(parser.Parser):
 
         return expression
 
+    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:
+        # Snowflake also accepts KEY=VALUE properties before the column definitions, e.g. CREATE T
…[1079 chars elided]…
t (id INT) CHANGE_TRACKING=TRUE"},
+        )
+        self.validate_all(
+            "CREATE TABLE t CHANGE_TRACKING=TRUE, DATA_RETENTION_TIME_IN_DAYS=5 (id INT)",
+            write={
+                "snowflake": "CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE DATA_RETENTION_TIME_IN_DAYS=5"
+            },
+        )
+
     def test_create_view_row_access_policy(self):
         self.validate_identity(
             "CREATE VIEW v WITH ROW ACCESS POLICY mypolicy ON (col1) AS SELECT col1 FROM t1"
[assistant] Snowflake now parses `KEY=VALUE` properties before the column list, so `CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)` parses and generates `CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE`. The full suite passes (1127 tests), and ruff format and lint are clean. I haven't committed anything.

The change is a small override in `sqlglot/parsers/snowflake.py`. The base parser only accepts dialect-registered keywords (like `COMMENT=`) before the schema, so `CHANGE_TRACKING` was never tried there. The override falls back to the generic property parser, but only when the next token is `=`. Without that check, the first attempt broke nine existing tests: the generic parser speculatively parses the `(` as a column list and raises on types like `TIMESTAMP_NTZ(2)`.

I added `test_create_table_properties_before_schema` to `tests/dialects/test_snowflake.py`. It covers a single property and a comma-separated pair. Multiple properties come out space-separated, which matches how Snowflake's own output orders them after the column list.
