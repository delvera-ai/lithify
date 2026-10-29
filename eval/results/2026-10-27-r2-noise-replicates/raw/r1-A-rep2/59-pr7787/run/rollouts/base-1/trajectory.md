# trajectory base-1

final message:
Snowflake now accepts `KEY = VALUE` properties before the column list in `CREATE TABLE`. Both forms parse and normalize to the trailing form:

```
CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)  ->  CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
```

**Change:** In `sqlglot/parsers/snowflake.py`, `SnowflakeParser` overrides `_parse_property_before`. The base version only matches keyword properties, so `CHANGE_TRACKING=TRUE` was left unconsumed and the parser then expected `(`. The override falls back to the generic property parser only when the next token is `=`.

I first tried falling back to the generic parser unconditionally. That broke existing `CREATE VIEW` tests with a column list, such as `CREATE VIEW v (COL1 COMMENT '...')`, so I narrowed it.

**Tests:** I added both forms to `test_snowflake` in `tests/dialects/test_snowflake.py`, next to the existing `CLUSTER BY` CREATE test.

**Results:** The full suite passes (1126 tests, 18271 subtests), and `ruff check` and `ruff format --check` are clean on both files. I haven't run `make check` or the mypyc (`testc`) variant.

Nothing is committed.

## events
[tool_use Bash] {"command": "git status --short && git log --oneline -1 && grep -n \"_parse_create\\|_parse_schema\\|def _parse_properties\\|def _parse_wrapped_csv\" sqlglot/parser.py | head -40; grep -n \"CHANGE_TRACKING\\|_parse_create\\|PROPERTY_PARSERS\\|def _parse_\" sqlglot/dialects/snowflake.py | head -60"}
[tool_result] 2b9e731c0 lithify: probe base
1089:        TokenType.CREATE: lambda self: self._parse_create(),
1281:        "INPUT": lambda self: self.expression(exp.InputModelProperty(this=self._parse_schema())),
1286:        "LIKE": lambda self: self._parse_create_like(),
1298:        "OUTPUT": lambda self: self.expression(exp.OutputModelProperty(this=self._parse_schema())),
1381:        "LIKE": lambda self: self._parse_create_like(),
2360:    def _parse_create(self) -> exp.Create | exp.Command:
2544:       
…[453 chars elided]…
_create_like(self) -> exp.LikeProperty | None:
3397:                value = self._parse_schema(exp.var("TABLE"))
4888:            return self._parse_schema(this=this)
7218:    def _parse_schema(self, this: exp.Expr | None = None) -> exp.Expr | None:
7504:                this=self._parse_schema(self._parse_unique_key()),
8615:    def _parse_wrapped_csv(
8771:            schema = self._parse_schema()
10023:        kind = self._parse_schema() if self._match(TokenType.TABLE) else self._parse_types()
[tool_use Bash] {"command": "sed -n 2360,2400p sqlglot/parser.py; echo ----; sed -n 2530,2600p sqlglot/parser.py; echo ----; sed -n 2869,2900p sqlglot/parser.py; echo ----; sed -n 7218,7250p sqlglot/parser.py"}
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
…[5997 chars elided]…
.Expr | None, computed_column: bool = True
    ) -> exp.Expr | None:
        # column defs are not really columns, they're identifiers
        if isinstance(this, exp.Column):
            this = this.this

        if not computed_column:
            self._match(TokenType.ALIAS)

        kind = self._parse_types(schema=True)

        if self._match_text_seq("FOR", "ORDINALITY"):
            return self.expression(exp.ColumnDef(this=this, ordinality=True))

        constraints: list[exp.Expr] = []
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)','CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE']:\n    try:\n        e=sqlglot.parse_one(s,read='snowflake'); print(type(e).__name__, repr(e)[:400]); print(e.sql('snowflake'))\n    except Exception as ex: print('ERR',ex)\n\"; grep -n \"CHANGE_TRACKING\\|ChangeTracking\" sqlglot/*.py sqlglot/dialects/snowflake.py | head; grep -n \"def _parse_property_before\" -A30 sqlglot/parser.py | head -50"}
[tool_result] ERR Expecting ). Line 1, Col: 39.
  CREATE TABLE t CHANGE_TRACKING=TRUE ([4mid[0m INT)
Create Create(
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
CRE
…[1076 chars elided]…
  except TypeError:
2788-                self.raise_error(f"Cannot parse property '{self._prev.text}'")
2789-
2790-        return None
2791-
2792-    def _parse_wrapped_properties(self) -> list[exp.Expr | list[exp.Expr]]:
2793-        return self._parse_wrapped_csv(self._parse_property)
2794-
2795-    def _parse_property(self) -> exp.Expr | list[exp.Expr] | None:
2796-        if self._match_texts(self.PROPERTY_PARSERS):
2797-            return self.PROPERTY_PARSERS[self._prev.text.upper()](self)
[tool_use Bash] {"command": "sed -n 2795,2868p sqlglot/parser.py; grep -n \"PROPERTY_PARSERS\\|_parse_property\\b\" sqlglot/dialects/snowflake.py | head; grep -n \"def _parse_create_like\\|_parse_as_command\" sqlglot/parser.py | head -3"}
[tool_result]     def _parse_property(self) -> exp.Expr | list[exp.Expr] | None:
        if self._match_texts(self.PROPERTY_PARSERS):
            return self.PROPERTY_PARSERS[self._prev.text.upper()](self)

        if self._match(TokenType.DEFAULT) and self._match_texts(self.PROPERTY_PARSERS):
            return self.PROPERTY_PARSERS[self._prev.text.upper()](self, default=True)

        if self._match_text_seq("COMPOUND", "SORTKEY"):
            return self._parse_sortkey(compound=True)

        if self._matc
…[2079 chars elided]…
dentifier) and not field.quoted:
            field = exp.var(field)

        return field

    def _parse_property_assignment(self, exp_class: type[E], **kwargs: t.Any) -> E:
        self._match(TokenType.EQ)
        self._match(TokenType.ALIAS)

        return self.expression(exp_class(this=self._parse_unquoted_field(), **kwargs))

2201:            return self._parse_as_command(start)
2315:            return self._parse_as_command(start)
2394:                return self._parse_as_command(start)
[tool_use Bash] {"command": "grep -rn \"_parse_property_before\" sqlglot/ | head; grep -n \"class Parser\" -A3 sqlglot/dialects/snowflake.py; grep -n \"        def _parse_\\|        def \" sqlglot/dialects/snowflake.py | head -40; grep -rn \"CHANGE_TRACKING\\|change_tracking\" tests/ | head -5"}
[tool_result] sqlglot/parser.py:2767:    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:
sqlglot/parser.py:2873:                prop = self._parse_property_before()
tests/dialects/test_snowflake.py:5758:        self.validate_identity("ALTER TABLE foo SET CHANGE_TRACKING=FALSE")
tests/dialects/test_snowflake.py:5769:        self.validate_identity("ALTER TABLE foo UNSET DATA_RETENTION_TIME_IN_DAYS, CHANGE_TRACKING")
[tool_use Bash] {"command": "grep -n \"class Parser\\|class Generator\\|class Tokenizer\" sqlglot/dialects/snowflake.py; grep -n \"PROPERTY_PARSERS\" -A3 sqlglot/dialects/snowflake.py | head; grep -n \"class Parser\" -A40 sqlglot/dialects/snowflake.py | grep -n \"def \\|PROPERTY\" | head"}
[tool_result] 135:    class Tokenizer(tokens.Tokenizer):
[tool_use Bash] {"command": "grep -n \"^    class \\|^        def \\|^        [A-Z_]* = \" sqlglot/dialects/snowflake.py | sed -n 1,80p"}
[tool_result] 129:    class JSONPathTokenizer(jsonpath.JSONPathTokenizer):
130:        SINGLE_TOKENS = jsonpath.JSONPathTokenizer.SINGLE_TOKENS.copy()
135:    class Tokenizer(tokens.Tokenizer):
136:        STRING_ESCAPES = ["\\", "'"]
137:        HEX_STRINGS = [("x'", "'"), ("X'", "'")]
138:        RAW_STRINGS = ["$$"]
139:        COMMENTS = ["--", "//", ("/*", "*/")]
140:        NESTED_COMMENTS = False
142:        KEYWORDS = {
180:        SINGLE_TOKENS = {
186:        VAR_SINGLE_TOKENS = {"$"}
188:        COMMANDS = tokens.Tokenizer.COMMANDS - {TokenType.SHOW}
[tool_use Bash] {"command": "grep -n \"Parser\\|^from\\|^import\" sqlglot/dialects/snowflake.py | head -30; sed -n 186,200p sqlglot/dialects/snowflake.py; grep -n \"class Parser(parser.Parser)\" -A12 sqlglot/dialects/teradata.py | head -20"}
[tool_result] 1:from __future__ import annotations
3:from sqlglot import exp, jsonpath, tokens
4:from sqlglot.dialects.dialect import (
8:from sqlglot.generators.snowflake import SnowflakeGenerator
9:from sqlglot.parsers.snowflake import (
10:    SnowflakeParser,
12:from sqlglot.tokens import TokenType
13:from sqlglot.typing.snowflake import EXPRESSION_METADATA
133:    Parser = SnowflakeParser
        VAR_SINGLE_TOKENS = {"$"}

        COMMANDS = tokens.Tokenizer.COMMANDS - {TokenType.SHOW}

    Generator = SnowflakeGenerator
[assistant] The Snowflake parser lives in `sqlglot/parsers/snowflake.py`. Let me look there and at how Teradata's before-properties are handled.
[tool_use Bash] {"command": "wc -l sqlglot/parsers/snowflake.py && grep -n \"    def \\|^class\\|^from\\|^import\" sqlglot/parsers/snowflake.py | head -80; ls sqlglot/parsers/ | head -50"}
[tool_result]     1399 sqlglot/parsers/snowflake.py
1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, parser
6:from sqlglot.trie import new_trie
7:from sqlglot.dialects.dialect import (
19:from sqlglot.helper import is_date_unit, is_int, seq_get
20:from sqlglot.tokens import TokenType
82:    def _builder(args: list, dialect: Dialect) -> exp.Func:
133:    def _builder(args: list) -> B | exp.Anonymous:
232:    def _builder(args: list, dialect: Dialect) -> E:
323:    def _parse
…[1890 chars elided]…
: bool, **kwargs) -> exp.Expr:
1355:    def _parse_window(self, this: exp.Expr | None, alias: bool = False) -> exp.Expr | None:
__init__.py
__pycache__
athena.py
base.py
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
[tool_use Bash] {"command": "sed -n 1000,1040p sqlglot/parsers/snowflake.py; grep -n \"PROPERTY_PARSERS\" sqlglot/parsers/snowflake.py | head -3"}
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
…[837 chars elided]…
ssion.kind in self.NON_TABLE_CREATABLES:
            # Replace the Table node with the enclosed Identifier
            expression.this.replace(expression.this.this)

        return expression

    # https://docs.snowflake.com/en/sql-reference/functions/date_part.html
    # https://docs.snowflake.com/en/sql-reference/functions-date-time.html#label-supported-date-time-parts
    def _parse_date_part(self) -> exp.Expr | None:
767:    PROPERTY_PARSERS = {
768:        **parser.Parser.PROPERTY_PARSERS,
[tool_use Bash] {"command": "sed -n 1040,1041p sqlglot/parsers/snowflake.py && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3"}
[tool_result]     def _parse_date_part(self) -> exp.Expr | None:
        this = self._parse_var() or self._parse_type()
.......................................... [ 78%]
...................................................................................................................................................................................................................................................                                            [100%]
1126 passed, 18271 subtests passed in 106.59s (0:01:46)
[assistant] Baseline is green (1126 passed). Now the change: Snowflake's `_parse_create` override is the natural place, so I'll add a `_parse_property_before` override next to it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-105331-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py", "old_string": "        return expression\n\n    # https://docs.snowflake.com/en/sql-reference/functions/date_part.html", "new_string": "        return expression\n\n    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:\n        # Snowflake also accepts KEY = VALUE properties before the column definitions\n        return super()._parse_property_before() or self._parse_property()\n\n    # https://docs.snowflake.com/en/sql-reference/functions/date_part.html"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-105331-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)','CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE','CREATE TABLE t DATA_RETENTION_TIME_IN_DAYS=1 CHANGE_TRACKING=TRUE (id INT)', 'CREATE SEQUENCE s START=1 INCREMENT=2', 'CREATE TABLE t AS SELECT 1']:\n    try:\n        print(sqlglot.transpile(s,read='snowflake',write='snowflake')[0])\n    except Exception as ex: print('ERR',s,ex)\n\""}
[tool_result] CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
CREATE TABLE t (id INT) DATA_RETENTION_TIME_IN_DAYS=1 CHANGE_TRACKING=TRUE
CREATE SEQUENCE s START WITH 1 INCREMENT BY 2
CREATE TABLE t AS SELECT 1
[assistant] Both forms now parse and normalize to the trailing form. Adding regression tests next to existing Snowflake CREATE TABLE tests.
[tool_use Bash] {"command": "grep -n \"def validate_identity\" -A3 tests/dialects/test_dialect.py; grep -n \"CREATE TABLE\" tests/dialects/test_snowflake.py | head -20; grep -n \"    def test_\" tests/dialects/test_snowflake.py | head -5"}
[tool_result] 53:    def validate_identity(
54-        self, sql, write_sql=None, pretty=False, check_command_warning=False, identify=False
55-    ):
56-        if check_command_warning:
461:        self.validate_identity("CREATE TABLE table1 CLUSTER BY (name1, name2, name3)")
783:        self.validate_identity("CREATE TABLE foo (bar DOUBLE AUTOINCREMENT START 0 INCREMENT 1)")
1010:            "CREATE TABLE foo (ID INT COMMENT $$some comment$$)",
1011:            "CREATE TABLE foo (ID INT COMMENT 'some commen
…[1166 chars elided]…
d INT PROJECTION POLICY p.q.r)",
4256:                    f"CREATE TABLE t (id INT {constraint_prefix}TAG (key1='value_1', key2='value_2'))",
4257:                    "CREATE TABLE t (id INT TAG (key1='value_1', key2='value_2'))",
4266:        self.validate_identity("CREATE TABLE geospatial_table (id INT, g GEOGRAPHY)")
15:    def test_snowflake(self):
3373:    def test_null_treatment(self):
3414:    def test_staged_files(self):
3464:    def test_sample(self):
3559:    def test_timestamps(self):
[tool_use Bash] {"command": "sed -n 458,463p tests/dialects/test_snowflake.py"}
[tool_result]         self.validate_identity("SELECT CONNECT_BY_ROOT test AS test_column_alias")
        self.validate_identity("SELECT number").selects[0].assert_is(exp.Column)
        self.validate_identity("INTERVAL '4 years, 5 months, 3 hours'")
        self.validate_identity("CREATE TABLE table1 CLUSTER BY (name1, name2, name3)")
        self.validate_identity("ALTER TABLE table1 CLUSTER BY (name)")
        self.validate_identity("SELECT rename, replace")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-105331-snowflake-dialect-in-create-stat/base-1/tests/dialects/test_snowflake.py", "old_string": "        self.validate_identity(\"CREATE TABLE table1 CLUSTER BY (name1, name2, name3)\")\n        self.validate_identity(\"ALTER TABLE table1 CLUSTER BY (name)\")", "new_string": "        self.validate_identity(\"CREATE TABLE table1 CLUSTER BY (name1, name2, name3)\")\n        self.validate_identity(\"CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE\")\n        self.validate_identity(\n            \"CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)\",\n            \"CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE\",\n        )\n        self.validate_identity(\"ALTER TABLE table1 CLUSTER BY (name)\")"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-105331-snowflake-dialect-in-create-stat/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/snowflake.py tests/dialects/test_snowflake.py 2>&1 | tail -2; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/snowflake.py tests/dialects/test_snowflake.py 2>&1 | tail -2"}
[tool_result] FAILED tests/dialects/test_snowflake.py::TestSnowflake::test_snowflake - sqlg...
SUBFAILED[snowflake -> CREATE TABLE t (col1 DATETIME2(2))] tests/dialects/test_tsql.py::TestTSQL::test_types_date
9 failed, 1122 passed, 17484 subtests passed in 70.50s (0:01:10)
All checks passed!
2 files already formatted
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | grep -B5 \"Error\\|error\" | head -60"}
[tool_result]     return self._parse_paren()
           ^^^^^^^^^^^^^^^^^^^
sqlglot/parser.py:6849: in _parse_paren
    self._match_r_paren(expression=this)
sqlglot/parser.py:9424: in _match_r_paren
    self.raise_error("Expecting )")
--

self = <sqlglot.parsers.snowflake.SnowflakeParser object at 0x10bc52690>
message = 'Expecting )'
token = <Token token_type: TokenType.STRING, text: description, line: 1, col: 41, start: 28, end: 40, comments: []>

    def raise_error(self, message: str, token: Token = SENTIN
…[1429 chars elided]…
        token = token or self._curr or self._prev or Token.string("")
        formatted_sql, start_context, highlight, end_context = highlight_sql(
            sql=self.sql,
            positions=[(token.start, token.end)],
            context_length=self.error_message_context,
        )
        formatted_message = f"{message}. Line {token.line}, Col: {token.col}.\n  {formatted_sql}"
    
        error = ParseError.new(
--
            start_context=start_context,
            highlight=highlight,
[assistant] The broad `_parse_property` fallback is too greedy: it misreads the `(`-wrapped column list in views. I'll narrow it to `KEY = VALUE` only, checking for `=` after the key.
[tool_use Bash] {"command": "grep -n \"self._next = \\|self._next=\" sqlglot/parser.py | head -3"}
[tool_result] 1891:        self._next = SENTINEL_NONE
1905:        self._next = tokens[index + 1] if index + 1 < size else SENTINEL_NONE
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-105331-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py", "old_string": "        # Snowflake also accepts KEY = VALUE properties before the column definitions\n        return super()._parse_property_before() or self._parse_property()", "new_string": "        # Snowflake also accepts KEY = VALUE properties before the column definitions\n        if self._next.token_type == TokenType.EQ:\n            return super()._parse_property_before() or self._parse_property()\n        return super()._parse_property_before()"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-105331-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/snowflake.py tests/dialects/test_snowflake.py | tail -1; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/snowflake.py tests/dialects/test_snowflake.py | tail -1"}
[tool_result] .......................................... [ 78%]
...................................................................................................................................................................................................................................................                                            [100%]
1126 passed, 18271 subtests passed in 52.40s
All checks passed!
2 files already formatted
[assistant] Snowflake now accepts `KEY = VALUE` properties before the column list in `CREATE TABLE`. Both forms parse and normalize to the trailing form:

```
CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)  ->  CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
```

**Change:** In `sqlglot/parsers/snowflake.py`, `SnowflakeParser` overrides `_parse_property_before`. The base version only matches keyword properties, so `CHANGE_TRACKING=TRUE` was left unconsumed and the parser then expected `(`. The override falls back to the generic property parser only when the next token is `=`.

I first tried falling back to the generic parser unconditionally. That broke existing `CREATE VIEW` tests with a column list, such as `CREATE VIEW v (COL1 COMMENT '...')`, so I narrowed it.

**Tests:** I added both forms to `test_snowflake` in `tests/dialects/test_snowflake.py`, next to the existing `CLUSTER BY` CREATE test.

**Results:** The full suite passes (1126 tests, 18271 subtests), and `ruff check` and `ruff format --check` are clean on both files. I haven't run `make check` or the mypyc (`testc`) variant.

Nothing is committed.
