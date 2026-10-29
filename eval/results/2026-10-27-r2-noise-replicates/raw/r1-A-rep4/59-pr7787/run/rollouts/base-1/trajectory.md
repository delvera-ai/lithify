# trajectory base-1

final message:
Snowflake now parses `CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)`, and the full test suite passes (1126 passed). The changes are uncommitted in the worktree.

**The fix** is a `_parse_property_before` override on `SnowflakeParser` in `sqlglot/parsers/snowflake.py`. The base version only recognised the Teradata-style keyword properties, so `CHANGE_TRACKING=TRUE` was never tried in that slot. The override falls back to the generic `KEY = VALUE` property parser, which is what already handles the post-column form.

It returns `None` when the next token is `(`. Without that guard, the generic parser tries to read `(id INT)` as an expression and raises on the missing `)`. That broke six existing Snowflake tests, including `CREATE VIEW v (COL1 COMMENT ...)`.

**Output form:** both spellings now generate the post-column form, `CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE`. That is the canonical Snowflake placement, but it means the round trip is not byte-identical. The new test asserts this with `validate_identity(sql, write_sql)`.

**Test:** I added two cases to `test_ddl` in `tests/dialects/test_snowflake.py`: the pre-column form, which normalises to the post-column form, and the post-column form, which round-trips unchanged. I did not run these against a live Snowflake instance.

I checked that `COPY GRANTS`, `CLONE`, `AS SELECT`, `LIKE`, and `CREATE SCHEMA`/`DATABASE` still parse as before. `ruff check` and `ruff format --check` pass on both files.

## events
[tool_use Bash] {"command": "grep -n \"CHANGE_TRACKING\\|def _parse_create\\|def _parse_schema\\|def _parse_properties\\|def _parse_property\\b\\|POST_SCHEMA\\|PROPERTY_PARSERS\" sqlglot/parser.py sqlglot/dialects/snowflake.py | head -80", "description": "Locate create/property parsing code"}
[tool_result] sqlglot/parser.py:1227:    PROPERTY_PARSERS: t.ClassVar[dict[str, t.Callable]] = {
sqlglot/parser.py:2360:    def _parse_create(self) -> exp.Create | exp.Command:
sqlglot/parser.py:2417:            # exp.Properties.Location.POST_SCHEMA ("schema" here is the UDF's type signature)
sqlglot/parser.py:2558:            # exp.Properties.Location.POST_SCHEMA and POST_WITH
sqlglot/parser.py:2783:        if self._match_texts(self.PROPERTY_PARSERS):
sqlglot/parser.py:2784:            parser = self.PROPERTY
…[717 chars elided]…
arser.py:7087:            if self._match_texts(self.PROPERTY_PARSERS):
sqlglot/parser.py:7088:                prop = self.PROPERTY_PARSERS[self._prev.text.upper()](self)
sqlglot/parser.py:7089:            elif self._match(TokenType.DEFAULT) and self._match_texts(self.PROPERTY_PARSERS):
sqlglot/parser.py:7090:                prop = self.PROPERTY_PARSERS[self._prev.text.upper()](self, default=True)
sqlglot/parser.py:7218:    def _parse_schema(self, this: exp.Expr | None = None) -> exp.Expr | None:
[tool_use Bash] {"command": "sed -n 2360,2470p sqlglot/parser.py && echo ----- && sed -n 2540,2600p sqlglot/parser.py && echo ---- && sed -n 2860,2900p sqlglot/parser.py && echo ---- && sed -n 7218,7240p sqlglot/parser.py", "description": "Read create and properties parsing code"}
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
…[8509 chars elided]…
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
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sqlglot\nfor s in ['CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)', 'CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE']:\n    e = sqlglot.parse_one(s, read='snowflake')\n    print(type(e).__name__, repr(e)[:400]); print(e.sql('snowflake'))\n\" ; grep -n \"_parse_property_before\" -A25 sqlglot/parser.py | head -60; grep -n \"CHANGE_TRACKING\\|ChangeTracking\" -r sqlglot | head", "description": "Reproduce the parse behavior for both forms"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
2767:    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:
2768-        # only used for teradata currently
2769-        self._match(TokenType.COMMA)
2770-
2771-        kwargs = {
2772-            "no": self._match_text_seq("NO"),
2773-            "dual": self._match_text_seq("DUAL"),
2774-            "before": self._match_text_seq("BEFORE"),
2775-          
…[1394 chars elided]…
    return self.expression(
2888-            exp.FallbackProperty(no=no, protection=self._match_text_seq("PROTECTION"))
2889-        )
2890-
2891-    def _parse_sql_security(self) -> exp.SqlSecurityProperty:
2892-        return self.expression(
2893-            exp.SqlSecurityProperty(
2894-                this=self._match_texts(self.SECURITY_PROPERTY_KEYWORDS) and self._prev.text.upper()
2895-            )
2896-        )
2897-
2898-    def _parse_settings_property(self) -> exp.SettingsProperty:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)', 'CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE']:\n    try:\n        e = sqlglot.parse_one(s, read='snowflake')\n        print(repr(e)[:600]); print(e.sql('snowflake'))\n    except Exception as ex: print('ERR', ex)\n\"; grep -n \"CHANGE_TRACKING\\|ChangeTracking\\|def _parse_property\\b\" -r sqlglot | head; grep -n \"class Properties\" -A40 sqlglot/expressions.py | grep -n \"Location\\|POST\" | head -30", "description": "Reproduce parse behavior for both forms"}
[tool_result] ERR Expecting ). Line 1, Col: 39.
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
        this=Var(this=CHANGE_TRACKING),
        value=Boolean(this=True))]),
  concurrently=False)
CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
sqlglot/parser.py:2795:    def _parse_property(self) -> exp.Expr | list[exp.Expr] | None:
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "sed -n 2795,2868p sqlglot/parser.py; echo ----; grep -n \"_parse_create\\|_parse_property\\|_parse_properties\\|class Parser\" sqlglot/dialects/snowflake.py | head -30", "description": "Read generic property parser and Snowflake parser hooks"}
[tool_result]     def _parse_property(self) -> exp.Expr | list[exp.Expr] | None:
        if self._match_texts(self.PROPERTY_PARSERS):
            return self.PROPERTY_PARSERS[self._prev.text.upper()](self)

        if self._match(TokenType.DEFAULT) and self._match_texts(self.PROPERTY_PARSERS):
            return self.PROPERTY_PARSERS[self._prev.text.upper()](self, default=True)

        if self._match_text_seq("COMPOUND", "SORTKEY"):
            return self._parse_sortkey(compound=True)

        if self._matc
…[1918 chars elided]…
mat=True,
            )
        )

    def _parse_unquoted_field(self) -> exp.Expr | None:
        field = self._parse_field()
        if isinstance(field, exp.Identifier) and not field.quoted:
            field = exp.var(field)

        return field

    def _parse_property_assignment(self, exp_class: type[E], **kwargs: t.Any) -> E:
        self._match(TokenType.EQ)
        self._match(TokenType.ALIAS)

        return self.expression(exp_class(this=self._parse_unquoted_field(), **kwargs))

----
[tool_use Bash] {"command": "grep -n \"class Parser\" -A6 sqlglot/dialects/snowflake.py; grep -n \"    def \\|PROPERTY_PARSERS\" sqlglot/dialects/snowflake.py | sed -n 1,60p; grep -rn \"before=True\" sqlglot | head", "description": "Inspect Snowflake parser class structure"}
[tool_result] 120:    def can_quote(self, identifier: exp.Identifier, identify: str | bool = "safe") -> bool:
sqlglot/parser.py:2554:            extend_props(self._parse_properties(before=True))
[tool_use Bash] {"command": "grep -n \"^class \\|^    class \\|PROPERTY_PARSERS\\|_parse_\" sqlglot/dialects/snowflake.py | head -80", "description": "List classes and parser hooks in Snowflake dialect"}
[tool_result] 16:class Snowflake(Dialect):
129:    class JSONPathTokenizer(jsonpath.JSONPathTokenizer):
135:    class Tokenizer(tokens.Tokenizer):
[tool_use Bash] {"command": "ls sqlglot/dialects/ | head -50; ls sqlglot/dialects/snowflake* 2>/dev/null; grep -rln \"class Snowflake\" sqlglot", "description": "Find where Snowflake parser is defined"}
[tool_result] __init__.py
__pycache__
athena.py
bigquery.py
clickhouse.py
databricks.py
dialect.py
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
sqlglot/dialects/snowflake.py
sqlglot/parsers/snowflake.py
sqlglot/dialects/snowflake.py
sqlglot/generators/snowflake.py
[tool_use Bash] {"command": "grep -n \"^class \\|    def \\|PROPERTY_PARSERS\" sqlglot/parsers/snowflake.py | head -80", "description": "List Snowflake parser methods"}
[tool_result] 82:    def _builder(args: list, dialect: Dialect) -> exp.Func:
133:    def _builder(args: list) -> B | exp.Anonymous:
232:    def _builder(args: list, dialect: Dialect) -> E:
323:    def _parse(self: SnowflakeParser) -> exp.Show:
329:class SnowflakeParser(parser.Parser):
767:    PROPERTY_PARSERS = {
768:        **parser.Parser.PROPERTY_PARSERS,
921:    def _parse_directory(self) -> exp.DirectoryStage:
926:    def _parse_describe(self) -> exp.Describe:
952:    def _parse_use(self) -> exp.Use:
960
…[1285 chars elided]…
operty(self) -> exp.CredentialsProperty:
1307:    def _parse_semantic_view(self) -> exp.SemanticView:
1324:    def _parse_set(self, unset: bool = False, tag: bool = False) -> exp.Set | exp.Command:
1333:    def _parse_position(self, haystack_first: bool = False) -> exp.StrPosition:
1338:    def _parse_substring(self) -> exp.Substring:
1343:    def build_cast(self, strict: bool, **kwargs) -> exp.Expr:
1355:    def _parse_window(self, this: exp.Expr | None, alias: bool = False) -> exp.Expr | None:
[tool_use Bash] {"command": "sed -n 1000,1040p sqlglot/parsers/snowflake.py; sed -n 1,20p sqlglot/parsers/snowflake.py | grep import", "description": "Read Snowflake _parse_create override"}
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
…[1015 chars elided]…
rn expression

    # https://docs.snowflake.com/en/sql-reference/functions/date_part.html
    # https://docs.snowflake.com/en/sql-reference/functions-date-time.html#label-supported-date-time-parts
    def _parse_date_part(self) -> exp.Expr | None:
from __future__ import annotations
import typing as t
from sqlglot import exp, parser
from sqlglot.trie import new_trie
from sqlglot.dialects.dialect import (
from sqlglot.helper import is_date_unit, is_int, seq_get
from sqlglot.tokens import TokenType
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\np='sqlglot/parsers/snowflake.py'\ns=open(p).read()\nold=\"\"\"    def _parse_create(self) -> exp.Create | exp.Command:\n        expression = super()._parse_create()\"\"\"\nnew=\"\"\"    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:\n        return self._parse_property()\n\n    def _parse_create(self) -> exp.Create | exp.Command:\n 
…[530 chars elided]…
YS=1 (id INT, b TEXT)',\n 'CREATE SCHEMA s', 'CREATE DATABASE d', 'CREATE TABLE t LIKE x', 'CREATE TABLE t (a INT) COMMENT=\\'x\\'']\nfor s in cases:\n    try:\n        e = sqlglot.parse_one(s, read='snowflake')\n        print(e.sql('snowflake'))\n    except Exception as ex: print('ERR', s, '->', str(ex).splitlines()[0])\n\"", "description": "Add Snowflake pre-schema property hook and test cases"}
[tool_result] CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
CREATE TABLE t (id INT)
CREATE TABLE t AS SELECT 1
CREATE TABLE t CLONE s.x
CREATE TABLE t (id INT) COPY GRANTS
CREATE OR REPLACE TABLE t (id INT, b VARCHAR) CHANGE_TRACKING=TRUE DATA_RETENTION_TIME_IN_DAYS=1
CREATE SCHEMA s
CREATE DATABASE d
CREATE TABLE t LIKE x
CREATE TABLE t (a INT) COMMENT='x'
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot.parsers.snowflake import SnowflakeParser as P\nfrom sqlglot import parser\nP._parse_property_before = parser.Parser._parse_property_before\nfor s in ['CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)','CREATE TABLE t COPY GRANTS (id INT)']:\n    try: print(sqlglot.parse_one(s, read='snowflake').sql('snowflake'))\n    except Exception as ex: print('ERR', str(ex).splitlines()[0])\n\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | tail -5", "description": "Compare COPY GRANTS against base behavior and run Snowflake tests"}
[tool_result] ERR Expecting ). Line 1, Col: 39.
CREATE TABLE t (id INT) COPY GRANTS
SUBFAILED[Constraint prefix: ] tests/dialects/test_snowflake.py::TestSnowflake::test_ddl
FAILED tests/dialects/test_snowflake.py::TestSnowflake::test_ddl - sqlglot.er...
FAILED tests/dialects/test_snowflake.py::TestSnowflake::test_rely_options - s...
FAILED tests/dialects/test_snowflake.py::TestSnowflake::test_snowflake - sqlg...
6 failed, 92 passed, 784 subtests passed in 3.07s
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | grep -E \"Error|^E |sqlglot/.*py:[0-9]+|test_snowflake.py:[0-9]+\" | head -40", "description": "Show Snowflake test failure details"}
[tool_result] tests/dialects/test_snowflake.py:5970: 
sqlglot/__init__.py:160: in parse_one
sqlglot/dialects/dialect.py:1129: in parse
sqlglot/parser.py:2050: in parse
sqlglot/parser.py:2170: in _parse
sqlglot/parser.py:2137: in _parse_batch_statements
sqlglot/parser.py:2289: in _parse_statement
sqlglot/parser.py:1089: in <lambda>
sqlglot/parsers/snowflake.py:1034: in _parse_create
sqlglot/parser.py:2554: in _parse_create
sqlglot/parser.py:2873: in _parse_properties
sqlglot/parsers/snowflake.py:1031: in _pars
…[862 chars elided]…
lot/parser.py:2137: in _parse_batch_statements
sqlglot/parser.py:2289: in _parse_statement
sqlglot/parser.py:1089: in <lambda>
sqlglot/parsers/snowflake.py:1034: in _parse_create
sqlglot/parser.py:2554: in _parse_create
sqlglot/parser.py:2873: in _parse_properties
sqlglot/parsers/snowflake.py:1031: in _parse_property_before
sqlglot/parser.py:2815: in _parse_property
sqlglot/parser.py:6578: in _parse_column
sqlglot/parser.py:6665: in _parse_column_reference
sqlglot/parser.py:6896: in _parse_field
[tool_use Bash] {"command": "python3 - <<'EOF'\np='sqlglot/parsers/snowflake.py'\ns=open(p).read()\nold=\"\"\"    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:\n        return self._parse_property()\n\"\"\"\nnew=\"\"\"    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:\n        if self._match(TokenType.L_PAREN, advance=False):\n            return None\n\n        retur
…[353 chars elided]…
d INT)','CREATE TABLE t COPY GRANTS (id INT)','CREATE OR REPLACE TABLE t CHANGE_TRACKING=TRUE DATA_RETENTION_TIME_IN_DAYS=1 (id INT, b TEXT)','CREATE TABLE t CHANGE_TRACKING=TRUE AS SELECT 1']:\n    try: print(sqlglot.parse_one(s, read='snowflake').sql('snowflake'))\n    except Exception as ex: print('ERR', str(ex).splitlines()[0])\n\"", "description": "Guard against paren, rerun Snowflake tests"}
[tool_result] ............................... [ 32%]
.................................................................                                                                 [100%]
96 passed, 1568 subtests passed in 0.45s
CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
CREATE TABLE t (id INT) COPY GRANTS
CREATE OR REPLACE TABLE t (id INT, b VARCHAR) CHANGE_TRACKING=TRUE DATA_RETENTION_TIME_IN_DAYS=1
CREATE TABLE t CHANGE_TRACKING=TRUE AS SELECT 1
[assistant] Snowflake tests pass now. Next I'll add a regression test next to the existing DDL tests.
[tool_use Bash] {"command": "grep -n \"CHANGE_TRACKING\\|COPY GRANTS\" tests/dialects/test_snowflake.py | head; grep -n \"    def test_ddl\" -A4 tests/dialects/test_snowflake.py", "description": "Find existing DDL test location"}
[tool_result] 4260:        self.validate_identity("CREATE OR REPLACE TABLE foo COPY GRANTS USING TEMPLATE (SELECT 1)")
4265:        self.validate_identity("CREATE OR REPLACE VIEW foo (uid) COPY GRANTS AS (SELECT 1)")
5758:        self.validate_identity("ALTER TABLE foo SET CHANGE_TRACKING=FALSE")
5769:        self.validate_identity("ALTER TABLE foo UNSET DATA_RETENTION_TIME_IN_DAYS, CHANGE_TRACKING")
5942:        # for normal views, 'COPY GRANTS' goes *after* the column list. ref: https://docs.snowflake.com/e
…[464 chars elided]…
Y GRANTS' goes before the column list and other properties still go after
5954:            "CREATE OR REPLACE MATERIALIZED VIEW FOO COPY GRANTS (A, B) COMMENT='foo' TAG (a='b') AS SELECT A, B FROM TBL"
4240:    def test_ddl(self):
4241-        for constraint_prefix in ("WITH ", ""):
4242-            with self.subTest(f"Constraint prefix: {constraint_prefix}"):
4243-                self.validate_identity(
4244-                    f"CREATE TABLE t (id INT {constraint_prefix}MASKING POLICY p.q.r)",
[tool_use Bash] {"command": "sed -n 4256,4268p tests/dialects/test_snowflake.py; grep -n \"def validate_identity\" -A3 tests/dialects/test_dialect.py", "description": "View surrounding test lines and validate_identity signature"}
[tool_result]                     f"CREATE TABLE t (id INT {constraint_prefix}TAG (key1='value_1', key2='value_2'))",
                    "CREATE TABLE t (id INT TAG (key1='value_1', key2='value_2'))",
                )

        self.validate_identity("CREATE OR REPLACE TABLE foo COPY GRANTS USING TEMPLATE (SELECT 1)")
        self.validate_identity("USE SECONDARY ROLES ALL")
        self.validate_identity("USE SECONDARY ROLES NONE")
        self.validate_identity("USE SECONDARY ROLES a, b, c")
        self.v
…[97 chars elided]…
ntity("CREATE OR REPLACE VIEW foo (uid) COPY GRANTS AS (SELECT 1)")
        self.validate_identity("CREATE TABLE geospatial_table (id INT, g GEOGRAPHY)")
        self.validate_identity("CREATE MATERIALIZED VIEW a COMMENT='...' AS SELECT 1 FROM x")
        self.validate_identity("CREATE DATABASE mytestdb_clone CLONE mytestdb")
53:    def validate_identity(
54-        self, sql, write_sql=None, pretty=False, check_command_warning=False, identify=False
55-    ):
56-        if check_command_warning:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-084913-snowflake-dialect-in-create-stat/base-1/tests/dialects/test_snowflake.py", "old_string": "        self.validate_identity(\"CREATE OR REPLACE TABLE foo COPY GRANTS USING TEMPLATE (SELECT 1)\")\n        self.validate_identity(\"USE SECONDARY ROLES ALL\")", "new_string": "        self.validate_identity(\"CREATE OR REPLACE TABLE foo COPY GRANTS USING TEMPLATE (SELECT 1)\")\n        self.validate_identity(\n            \"CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)\",\n            \"CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE\",\n        )\n        self.validate_identity(\"CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE\")\n        self.validate_identity(\"USE SECONDARY ROLES ALL\")"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-084913-snowflake-dialect-in-create-stat/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[assistant] Now the full project check suite, plus a lint pass on the changed file.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; ($PY -m ruff check sqlglot/parsers/snowflake.py tests/dialects/test_snowflake.py && $PY -m ruff format --check sqlglot/parsers/snowflake.py tests/dialects/test_snowflake.py) 2>&1 | tail -3; git status --short", "description": "Run full test suite and lint changed files"}
[tool_result] .......................................... [ 78%]
...................................................................................................................................................................................................................................................                                            [100%]
1126 passed, 18271 subtests passed in 50.21s
All checks passed!
2 files already formatted
 M sqlglot/parsers/snowflake.py
 M tests/dialects/test_snowflake.py
[assistant] Snowflake now parses `CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)`, and the full test suite passes (1126 passed). The changes are uncommitted in the worktree.

**The fix** is a `_parse_property_before` override on `SnowflakeParser` in `sqlglot/parsers/snowflake.py`. The base version only recognised the Teradata-style keyword properties, so `CHANGE_TRACKING=TRUE` was never tried in that slot. The override falls back to the generic `KEY = VALUE` property parser, which is what already handles the post-column form.

It returns `None` when the next token is `(`. Without that guard, the generic par
…[270 chars elided]…
NG=TRUE`. That is the canonical Snowflake placement, but it means the round trip is not byte-identical. The new test asserts this with `validate_identity(sql, write_sql)`.

**Test:** I added two cases to `test_ddl` in `tests/dialects/test_snowflake.py`: the pre-column form, which normalises to the post-column form, and the post-column form, which round-trips unchanged. I did not run these against a live Snowflake instance.

I checked that `COPY GRANTS`, `CLONE`, `AS SELECT`, `LIKE`, and `CREATE SCHEMA`/`DATABASE` still parse as before. `ruff check` and `ruff format --check` pass on both files.
