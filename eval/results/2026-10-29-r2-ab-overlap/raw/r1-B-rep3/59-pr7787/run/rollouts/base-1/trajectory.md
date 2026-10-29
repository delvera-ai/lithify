# trajectory base-1

final message:
Snowflake now accepts `KEY=VALUE` properties between the table name and the column list. Both forms parse and round-trip to `CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE`. The full suite passes (1126 tests) and ruff is clean.

The base parser only tried `PROPERTY_PARSERS` in that position, a path that exists for Teradata. I added an override in `sqlglot/parsers/snowflake.py` that falls back to the generic property parser:

```python
def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:
    # Snowflake allows KEY=VALUE properties between the table name and its column definitions
    return super()._parse_property_before() or self._try_parse(self._parse_property)
```

The fallback is wrapped in `_try_parse`. Without it, the speculative property parse on `(` recorded errors and broke existing column-type tests such as `TIMESTAMP_NTZ(2)`.

I added two `validate_identity` assertions to `test_ddl` in `tests/dialects/test_snowflake.py`: the before-column form and the after-column form. Nothing is committed.

## events
[tool_use Bash] {"command": "grep -n \"_parse_create\\|_parse_properties\\|POST_SCHEMA\\|POST_EXPRESSION\\|POST_CREATE\\|def _parse_schema\\|PROPERTY_PARSERS\" sqlglot/parser.py | head -80; echo ---; grep -n \"CHANGE_TRACKING\\|POST_\\|PROPERTY\\|_parse_create\" sqlglot/dialects/snowflake.py | head -60", "description": "Locate create/property parsing code"}
[tool_result] 36 matches in 15 files:

1066:0:lambda self: self._parse_properties(),
1089:0:lambda self: self._parse_create(),
1227:0:t.ClassVar[dict[str, t.Callable]] = {
1286:0:lambda self: self._parse_create_like(),
1381:0:lambda self: self._parse_create_like(),
2360:0:
2783:0:
2796:0:
2799:0:
2869:0:bool | None = None) -> exp.Properties | None:
3350:0:
7087:0:
7089:0:
7218:0:exp.Expr | None = None) -> exp.Expr | None:
sqlglot/parser.py:2389:# exp.Properties.Location.POST_CREATE
sqlglot/parser.py:2390:prop
…[1064 chars elided]…
v.text.upper()](self, default=True)
sqlglot/parser.py:3422:properties = self._parse_properties()
sqlglot/parser.py:7088:prop = self.PROPERTY_PARSERS[self._prev.text.upper()](self)
sqlglot/parser.py:7090:prop = self.PROPERTY_PARSERS[self._prev.text.upper()](self, default=True)
sqlglot/parser.py:8896:properties = self._parse_wrapped(self._parse_properties, optional=True)
sqlglot/parser.py:9017:properties = self._parse_properties()
---
0 matches for 'CHANGE_TRACKING\|POST_\|PROPERTY\|_parse_create'
[tool_use Bash] {"command": "sed -n 2370,2470p sqlglot/parser.py; echo ----; sed -n 2530,2625p sqlglot/parser.py", "description": "Read the CREATE parsing section"}
[tool_result]         unique = self._match(TokenType.UNIQUE)

        if self._match_text_seq("CLUSTERED", "COLUMNSTORE"):
            clustered = True
        elif self._match_text_seq("NONCLUSTERED", "COLUMNSTORE") or self._match_text_seq(
            "COLUMNSTORE"
        ):
            clustered = False
        else:
            clustered = None

        if self._match_pair(TokenType.TABLE, TokenType.FUNCTION, advance=False):
            self._advance()

        properties = None
        create_token = se
…[7163 chars elided]…
ps(self._parse_properties())

            shallow = self._match_text_seq("SHALLOW")

            if self._match_texts(self.CLONE_KEYWORDS):
                copy = self._prev.text.lower() == "copy"
                clone = self.expression(
                    exp.Clone(this=self._parse_table(schema=True), shallow=shallow, copy=copy)
                )

        if self._curr and not self._match_set((TokenType.R_PAREN, TokenType.COMMA), advance=False):
            return self._parse_as_command(start)
[tool_use Bash] {"command": "sed -n 2865,2920p sqlglot/parser.py; echo ----; grep -n \"CHANGE_TRACKING\\|ChangeTracking\\|change_tracking\" -ri sqlglot | head; echo ----; grep -n \"before=True\\|before:\" sqlglot/parser.py sqlglot/dialects/*.py | head -20; echo; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)','CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE']:\n    try: print(repr(sqlglot.parse_one(s, read='snowflake')))\n    except Exception as e: print('ERR', e)\n\"", "description": "Inspect _parse_properties and reproduce the failure"}
[tool_result]         self._match(TokenType.ALIAS)

        return self.expression(exp_class(this=self._parse_unquoted_field(), **kwargs))

    def _parse_properties(self, before: bool | None = None) -> exp.Properties | None:
        properties = []
        while True:
            if before:
                prop = self._parse_property_before()
            else:
                prop = self._parse_property()
            if not prop:
                break
            for p in ensure_list(prop):
                p
…[1871 chars elided]…
 CHANGE_TRACKING=TRUE ([4mid[0m INT)
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
[tool_use Bash] {"command": "grep -n \"def _parse_property_before\" -A 40 sqlglot/parser.py; echo ----; grep -n \"def _parse_property(self\" -A 50 sqlglot/parser.py | head -80", "description": "Read property parsing helpers"}
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
…[3365 chars elided]…
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
[tool_use Bash] {"command": "grep -n \"class Parser\" -A 3 sqlglot/dialects/snowflake.py; grep -n \"    def _parse_\\|PROPERTY_PARSERS\" sqlglot/dialects/snowflake.py | head -60; echo ----; grep -n \"CHANGE_TRACKING\\|TABLE .* (id INT) \\|TRUE (id\" tests/dialects/test_snowflake.py | head; grep -n \"def test_ddl\" -A 3 tests/dialects/test_snowflake.py | head", "description": "Inspect Snowflake parser overrides and existing tests"}
[tool_result] 0 matches for '    def _parse_\|PROPERTY_PARSERS'
----
rg: regex parse error:
    (?:CHANGE_TRACKING|TABLE .* (id INT) |TRUE (id)
    ^
error: unclosed group
0 matches for 'CHANGE_TRACKING\|TABLE .* (id INT) \|TRUE (id'
4240:    def test_ddl(self):
4241-        for constraint_prefix in ("WITH ", ""):
4242-            with self.subTest(f"Constraint prefix: {constraint_prefix}"):
4243-                self.validate_identity(
[tool_use Bash] {"command": "grep -n \"class Parser\" sqlglot/dialects/snowflake.py; grep -n \"_parse_\" sqlglot/dialects/snowflake.py | head -40", "description": "Find Snowflake Parser class and overrides"}
[tool_result] 0 matches for 'class Parser'
0 matches for '_parse_'
[tool_use Bash] {"command": "ls sqlglot/dialects/ | head -50 && wc -l sqlglot/dialects/snowflake.py && which grep && type grep", "description": "Check file presence and grep alias"}
[tool_result] __init__.py  3.6K
athena.py  4.3K
bigquery.py  7.3K
clickhouse.py  4.6K
databricks.py  1.1K
dialect.py  91.3K
doris.py  364B
dremio.py  1.6K
drill.py  1.4K
druid.py  224B
duckdb.py  4.2K
dune.py  329B
exasol.py  2.0K
fabric.py  1.8K
hive.py  3.6K
materialize.py  305B
mysql.py  5.7K
oracle.py  3.4K
postgres.py  4.6K
presto.py  2.2K
prql.py  782B
redshift.py  1.9K
risingwave.py  618B
singlestore.py  2.1K
snowflake.py  6.6K
solr.py  535B
spark.py  927B
spark2.py  977B
sqlite.py  1.1K
starrocks.py  
…[807 chars elided]…
== "win32" ]]
	then
		ARGV0=ugrep "$_cc_bin" -G --ignore-files --hidden -I --exclude-dir=.git --exclude-dir=.svn --exclude-dir=.hg --exclude-dir=.bzr --exclude-dir=.jj --exclude-dir=.sl ${1+"$@"}
	else
		(
			exec -a ugrep "$_cc_bin" -G --ignore-files --hidden -I --exclude-dir=.git --exclude-dir=.svn --exclude-dir=.hg --exclude-dir=.bzr --exclude-dir=.jj --exclude-dir=.sl ${1+"$@"}
		)
	fi
}
grep is a shell function from ~/.claude/shell-snapshots/snapshot-zsh-1793299418400-lf45t6.sh
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-204334-snowflake-dialect-in-create-stat/base-1/sqlglot/dialects/snowflake.py"}
[tool_result] 1	from __future__ import annotations
2	
3	from sqlglot import exp, jsonpath, tokens
4	from sqlglot.dialects.dialect import (
5	    Dialect,
6	    NormalizationStrategy,
7	)
8	from sqlglot.generators.snowflake import SnowflakeGenerator
9	from sqlglot.parsers.snowflake import (
10	    SnowflakeParser,
11	)
12	from sqlglot.tokens import TokenType
13	from sqlglot.typing.snowflake import EXPRESSION_METADATA
14	
15	
16	class Snowflake(Dialect):
17	    # https://docs.snowflake.com/en/sql-reference/iden
…[6445 chars elided]…

175	            # FLOAT is a synonym for DOUBLE in Snowflake
176	            "FLOAT": TokenType.DOUBLE,
177	        }
178	        KEYWORDS.pop("/*+")
179	
180	        SINGLE_TOKENS = {
181	            **tokens.Tokenizer.SINGLE_TOKENS,
182	            "$": TokenType.PARAMETER,
183	            "!": TokenType.EXCLAMATION,
184	        }
185	
186	        VAR_SINGLE_TOKENS = {"$"}
187	
188	        COMMANDS = tokens.Tokenizer.COMMANDS - {TokenType.SHOW}
189	
190	    Generator = SnowflakeGenerator
191	
[assistant] The Snowflake parser lives in `sqlglot/parsers/snowflake.py`. Let me look at it and check how the generator emits table properties.
[tool_use Bash] {"command": "python3 -c \"\nimport re,sys\nsrc=open('sqlglot/parsers/snowflake.py').read().splitlines()\nfor i,l in enumerate(src,1):\n    if re.search(r'def _parse_|PROPERTY|class SnowflakeParser', l): print(i,l)\n\"; echo; python3 -c \"\nsrc=open('sqlglot/parsers/snowflake.py').read().splitlines()\nprint(len(src))\"", "description": "List parser method definitions in Snowflake parser"}
[tool_result] 329 class SnowflakeParser(parser.Parser):
767     PROPERTY_PARSERS = {
768         **parser.Parser.PROPERTY_PARSERS,
921     def _parse_directory(self) -> exp.DirectoryStage:
926     def _parse_describe(self) -> exp.Describe:
952     def _parse_use(self) -> exp.Use:
976     def _parse_tag(self) -> exp.Tags:
979     def _parse_with_constraint(self) -> exp.Expr | None:
1004     def _parse_with_property(self) -> exp.Expr | None | list[exp.Expr]:
1013     def _parse_row_access_policy(self) -> exp.Ro
…[912 chars elided]…
-> exp.FileFormatProperty:
1304     def _parse_credentials_property(self) -> exp.CredentialsProperty:
1307     def _parse_semantic_view(self) -> exp.SemanticView:
1324     def _parse_set(self, unset: bool = False, tag: bool = False) -> exp.Set | exp.Command:
1333     def _parse_position(self, haystack_first: bool = False) -> exp.StrPosition:
1338     def _parse_substring(self) -> exp.Substring:
1355     def _parse_window(self, this: exp.Expr | None, alias: bool = False) -> exp.Expr | None:

1399
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-204334-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py", "offset": 1000, "limit": 42}
[tool_result] 1000	            return self._parse_tag()
1001	
1002	        return None
1003	
1004	    def _parse_with_property(self) -> exp.Expr | None | list[exp.Expr]:
1005	        if self._match(TokenType.TAG):
1006	            return self._parse_tag()
1007	
1008	        if self._match_text_seq("ROW", "ACCESS", "POLICY"):
1009	            return self._parse_row_access_policy()
1010	
1011	        return super()._parse_with_property()
1012	
1013	    def _parse_row_access_policy(self) -> exp.RowAccessProperty
…[1027 chars elided]…
BLE_CREATABLES:
1033	            # Replace the Table node with the enclosed Identifier
1034	            expression.this.replace(expression.this.this)
1035	
1036	        return expression
1037	
1038	    # https://docs.snowflake.com/en/sql-reference/functions/date_part.html
1039	    # https://docs.snowflake.com/en/sql-reference/functions-date-time.html#label-supported-date-time-parts
1040	    def _parse_date_part(self) -> exp.Expr | None:
1041	        this = self._parse_var() or self._parse_type()
[assistant] The base parser's `before=True` path only consults `PROPERTY_PARSERS` (it's Teradata-only), so generic `KEY=VALUE` properties are never tried before the schema. I'll add a Snowflake override that falls back to the generic property parser.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-204334-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py", "old_string": "    def _parse_create(self) -> exp.Create | exp.Command:\n        expression = super()._parse_create()", "new_string": "    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:\n        # Snowflake allows KEY=VALUE properties between the table name and its column definitions\n        return super()._parse_property_before() or self._parse_property()\n\n    def _parse_create(self) -> exp.Create | exp.Command:\n        expression = super()._parse_create()"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-204334-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0, '.')\nimport sqlglot\nfor s in ['CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)','CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE','CREATE TABLE t CHANGE_TRACKING=TRUE, DATA_RETENTION_TIME_IN_DAYS=5 (id INT, b TEXT) COMMENT=\\'x\\'','CREATE TABLE t AS SELECT 1 AS a','CREATE TABLE t (id INT)']:\n    e = sqlglot.parse_one(s, read='snowflake')\n    print(e.sql('snowflake'))\n    print(' ->', repr(e.sql('duckdb')))\n\" ; <work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); import sqlglot; print(sqlglot.__file__)\"", "description": "Verify both property placements parse in Snowflake"}
[tool_result] Unsupported property property
Unsupported property property
Unsupported property property
Unsupported property property
Unsupported property schemacommentproperty
CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
 -> 'CREATE TABLE t (id INT)'
CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
 -> 'CREATE TABLE t (id INT)'
CREATE TABLE t (id INT, b VARCHAR) COMMENT='x' CHANGE_TRACKING=TRUE DATA_RETENTION_TIME_IN_DAYS=5
 -> 'CREATE TABLE t (id INT, b TEXT)'
CREATE TABLE t AS SELECT 1 AS a
 -> 'CREATE TABLE t AS SELECT 1 AS a'
CREATE TABLE t (id INT)
 -> 'CREATE TABLE t (id INT)'
~/.cache/lithify/work/repo-6e430de19896/20261029-204334-snowflake-dialect-in-create-stat/base-1/sqlglot/__init__.py
[assistant] Both placements now parse and round-trip to the same Snowflake SQL. The "Unsupported property" messages come from DuckDB generation, which is existing behavior for these properties. Next I'll add a regression test next to the existing DDL tests.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-204334-snowflake-dialect-in-create-stat/base-1/tests/dialects/test_snowflake.py", "offset": 4240, "limit": 30}
[tool_result] 4240	    def test_ddl(self):
4241	        for constraint_prefix in ("WITH ", ""):
4242	            with self.subTest(f"Constraint prefix: {constraint_prefix}"):
4243	                self.validate_identity(
4244	                    f"CREATE TABLE t (id INT {constraint_prefix}MASKING POLICY p.q.r)",
4245	                    "CREATE TABLE t (id INT MASKING POLICY p.q.r)",
4246	                )
4247	                self.validate_identity(
4248	                    f"CREATE TABLE t (id INT {constrain
…[1022 chars elided]…
IEW table1 AS (SELECT a FROM table2)")
4265	        self.validate_identity("CREATE OR REPLACE VIEW foo (uid) COPY GRANTS AS (SELECT 1)")
4266	        self.validate_identity("CREATE TABLE geospatial_table (id INT, g GEOGRAPHY)")
4267	        self.validate_identity("CREATE MATERIALIZED VIEW a COMMENT='...' AS SELECT 1 FROM x")
4268	        self.validate_identity("CREATE DATABASE mytestdb_clone CLONE mytestdb")
4269	        self.validate_identity("CREATE SCHEMA mytestschema_clone CLONE testschema")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-204334-snowflake-dialect-in-create-stat/base-1/tests/dialects/test_snowflake.py", "old_string": "        self.validate_identity(\"CREATE OR REPLACE TABLE foo COPY GRANTS USING TEMPLATE (SELECT 1)\")\n        self.validate_identity(\"USE SECONDARY ROLES ALL\")", "new_string": "        self.validate_identity(\"CREATE OR REPLACE TABLE foo COPY GRANTS USING TEMPLATE (SELECT 1)\")\n        self.validate_identity(\n            \"CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)\",\n            \"CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE\",\n        )\n        self.validate_identity(\"CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE\")\n        self.validate_identity(\"USE SECONDARY ROLES ALL\")"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-204334-snowflake-dialect-in-create-stat/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[assistant] Now the project's check command, run from the worktree.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | tail -15; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run Snowflake tests then full test suite", "timeout": 900000}
[tool_result] E           sqlglot.errors.ParseError: Expecting ). Line 1, Col: 42.
E             CREATE TABLE foo (bar DOUBLE [4mAUTOINCREMENT[0m START 0 INCREMENT 1)

sqlglot/parser.py:2007: ParseError
----------------------------- Captured stdout call -----------------------------
uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu [ 80%]
uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu
=========================== short test summary info ============================
FAILED tests/dialects/test_snowflake
…[1206 chars elided]…
SUBFAILED[Constraint prefix: ] tests/dialects/test_snowflake.py::TestSnowflake::test_ddl
FAILED tests/dialects/test_snowflake.py::TestSnowflake::test_ddl - sqlglot.er...
FAILED tests/dialects/test_snowflake.py::TestSnowflake::test_rely_options - s...
FAILED tests/dialects/test_snowflake.py::TestSnowflake::test_snowflake - sqlg...
SUBFAILED[snowflake -> CREATE TABLE t (col1 DATETIME2(2))] tests/dialects/test_tsql.py::TestTSQL::test_types_date
9 failed, 1122 passed, 17484 subtests passed in 50.50s
[assistant] My change broke existing tests: the generic property fallback runs on the `(` before the column list, and the speculative `_parse_column` call records a parse error even though it backs off. Let me check how `_try_parse` handles this.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport inspect,sys; sys.path.insert(0,'.')\nfrom sqlglot.parser import Parser\nprint(inspect.getsource(Parser._try_parse))\n\"", "description": "Read _try_parse helper source"}
[tool_result]     def _try_parse(self, parse_method: t.Callable[[], T], retreat: bool = False) -> T | None:
        index = self._index
        error_level = self.error_level
        this: T | None = None

        self.error_level = ErrorLevel.IMMEDIATE
        try:
            this = parse_method()
        except ParseError:
            this = None
        finally:
            if not this or retreat:
                self._retreat(index)
            self.error_level = error_level

        return this
[assistant] `_try_parse` switches to immediate error mode and rewinds on failure, which is what this speculative fallback needs.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-204334-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py", "old_string": "        return super()._parse_property_before() or self._parse_property()", "new_string": "        return super()._parse_property_before() or self._try_parse(self._parse_property)"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-204334-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Run full test suite after fix", "timeout": 900000}
[tool_result] ............................................................................................................. [ 70%]
............................................. [ 74%]
.......................................... [ 78%]
...................................................................................................................................................................................................................................................                                            [100%]
1126 passed, 18271 subtests passed in 47.30s
[assistant] Full suite passes (1126 tests, including the new assertions). I'll re-check the earlier examples and run the linter on the two changed files.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0, '.')\nimport sqlglot\nfor s in ['CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)','CREATE TABLE t CHANGE_TRACKING=TRUE, DATA_RETENTION_TIME_IN_DAYS=5 (id INT, b TEXT) COMMENT=\\'x\\'','CREATE TABLE t (col1 TIMESTAMP_NTZ(2))']:\n    print(sqlglot.parse_one(s, read='snowflake'
…[152 chars elided]…
ialects/test_snowflake.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/parsers/snowflake.py tests/dialects/test_snowflake.py) 2>&1 | tail -5; cd ~/.cache/lithify/work/repo-6e430de19896/20261029-204334-snowflake-dialect-in-create-stat/base-1 && git status --short && git diff", "description": "Recheck examples, lint, and review diff"}
[tool_result] CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
CREATE TABLE t (id INT, b VARCHAR) COMMENT='x' CHANGE_TRACKING=TRUE DATA_RETENTION_TIME_IN_DAYS=5
CREATE TABLE t (col1 TIMESTAMPNTZ(2))
All checks passed!
2 files already formatted
 M sqlglot/parsers/snowflake.py
 M tests/dialects/test_snowflake.pysqlglot/parsers/snowflake.py     | 4 ++++
 tests/dialects/test_snowflake.py | 5 +++++
 2 files changed, 9 insertions(+)

--- Changes ---

sqlglot/parsers/snowflake.py
  @@ -1027,6 +1027,10 @@ class Snowflake
…[554 chars elided]…
58,6 +4258,11 @@ class TestSnowflake(Validator):
  +        self.validate_identity(
  +            "CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)",
  +            "CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE",
  +        )
  +        self.validate_identity("CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE")
           self.validate_identity("USE SECONDARY ROLES ALL")
           self.validate_identity("USE SECONDARY ROLES NONE")
           self.validate_identity("USE SECONDARY ROLES a, b, c")
  +5 -0
[assistant] Snowflake now accepts `KEY=VALUE` properties between the table name and the column list. Both forms parse and round-trip to `CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE`. The full suite passes (1126 tests) and ruff is clean.

The base parser only tried `PROPERTY_PARSERS` in that position, a path that exists for Teradata. I added an override in `sqlglot/parsers/snowflake.py` that falls back to the generic property parser:

```python
def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:
    # Snowflake allows KEY=VALUE properties between the table name and its column definitions
    return super()._parse_property_before() or self._try_parse(self._parse_property)
```

The fallback is wrapped in `_try_parse`. Without it, the speculative property parse on `(` recorded errors and broke existing column-type tests such as `TIMESTAMP_NTZ(2)`.

I added two `validate_identity` assertions to `test_ddl` in `tests/dialects/test_snowflake.py`: the before-column form and the after-column form. Nothing is committed.
