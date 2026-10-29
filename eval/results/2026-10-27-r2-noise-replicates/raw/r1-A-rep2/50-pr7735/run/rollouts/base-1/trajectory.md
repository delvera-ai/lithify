# trajectory base-1

final message:
Snowflake `UNDROP` now parses and regenerates for all twelve object types you listed, including the `IDENTIFIER(...)` form. The full suite passes (1121 tests) and ruff is clean. I did not commit.

**What changed**
- **Tokenizer:** `UNDROP` is a Snowflake keyword mapping to a new `TokenType.UNDROP`, following the `GET`/`PUT` pattern. It is also added to the base `ID_VAR_TOKENS`, so `undrop` still works as an identifier (`SELECT undrop FROM undrop` round-trips).
- **Parser:** `_parse_undrop` in `sqlglot/parsers/snowflake.py` matches one of the twelve kinds in `UNDROP_KINDS`, then parses the target with `_parse_table_parts`. That is also what makes `IDENTIFIER(123)` and `IDENTIFIER('"abc"')` work. Unknown kinds fall back to `exp.Command`, the same as before.
- **AST:** new `exp.Undrop(this, kind)` in `sqlglot/expressions/ddl.py`.
- **Generator:** `undrop_sql` in `sqlglot/generators/snowflake.py` emits `UNDROP <kind> <name>`.
- **Tests:** `test_undrop` in `tests/dialects/test_snowflake.py` covers every kind, multi-part names, both `IDENTIFIER` forms, and the identifier case.

**Decisions to check**
- I made `Undrop` Snowflake-only: the generator method lives in the Snowflake generator. Other dialects can't emit it. Moving `undrop_sql` into the base generator is a one-line change if you want it available everywhere.
- `UNDROP` is now a reserved-ish keyword in the Snowflake tokenizer. It is still usable as an identifier via `ID_VAR_TOKENS`.

## events
[tool_use Bash] {"command": "grep -rn -i \"undrop\" sqlglot/ tests/ | head -50; grep -n \"DROP\\|Drop\" sqlglot/dialects/snowflake.py | head -40", "description": "Search for UNDROP and DROP handling in Snowflake"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "pwd && ls && grep -n \"_parse_drop\\|STATEMENT_PARSERS\\|def _parse_show\\|ALTER\\b\" sqlglot/dialects/snowflake.py | head; grep -n \"class Drop\\|class Alter\\b\\|class Command\" sqlglot/expressions.py; grep -n \"def _parse_drop\\|def _parse_create\\|\\\"DROP\\\"\" sqlglot/parser.py | head", "description": "Locate parser and dialect source files"}
[tool_result] ~/.cache/lithify/work/repo-fdb04f649b80/20261028-102538-snowflake-dialect-snowflake-s-ti/base-1
AGENTS.md
CHANGELOG.md
CLAUDE.md
CONTRIBUTING.md
LICENSE
MANIFEST.in
Makefile
README.md
benchmarks
pdoc
posts
pyproject.toml
setup.cfg
setup.py
sqlglot
sqlglot-integration-tests
sqlglot.png
sqlglotc
tests
ugrep: warning: sqlglot/expressions.py: No such file or directory
1442:        "DROP": lambda self: self._parse_alter_table_drop(),
1734:        "DROP": lambda self: self._parse_analyze_histogram(),
2298:    def _parse_drop(self, exists: bool = False) -> exp.Drop | exp.Command:
2351:    def _parse_create(self) -> exp.Create | exp.Command:
3334:    def _parse_create_like(self) -> exp.LikeProperty | None:
8709:    def _parse_drop_column(self) -> exp.Drop | exp.Command | None:
8719:    def _parse_drop_partition(self, exists: bool | None = None) -> exp.DropPartition:
8778:        if self._match_text_seq("DROP", "NOT", "NULL"):
[tool_use Bash] {"command": "sed -n 2290,2360p sqlglot/parser.py; grep -n \"STATEMENT_PARSERS\" sqlglot/parser.py | head -3; grep -n \"TokenType.UNDROP\\|UNDROP\" sqlglot/tokens.py; grep -n \"def drop_sql\\|def command_sql\" sqlglot/generator.py", "description": "Read _parse_drop and statement parser setup"}
[tool_result]         expression = self._parse_expression()
        expression = self._parse_set_operations(expression) if expression else self._parse_select()

        if isinstance(expression, exp.Subquery) and self._match(TokenType.PIPE_GT, advance=False):
            expression = self._parse_pipe_syntax_query(expression)

        return self._parse_query_modifiers(expression)

    def _parse_drop(self, exists: bool = False) -> exp.Drop | exp.Command:
        start = self._prev
        temporary = self._ma
…[2171 chars elided]…
         or self._match_pair(TokenType.OR, TokenType.REPLACE)
            or self._match_pair(TokenType.OR, TokenType.ALTER)
        )
        refresh = self._match_pair(TokenType.OR, TokenType.REFRESH)
1082:    STATEMENT_PARSERS: t.ClassVar = {
2278:        if self._match_set(self.STATEMENT_PARSERS):
2280:            stmt = self.STATEMENT_PARSERS[self._prev.token_type](self)
1784:    def drop_sql(self, expression: exp.Drop) -> str:
4076:    def command_sql(self, expression: exp.Command) -> str:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfor s in ['UNDROP TABLE t','UNDROP SCHEMA s','UNDROP DATABASE d','UNDROP DYNAMIC TABLE t','UNDROP TABLE IDENTIFIER(123)']:\n    try: print(repr(sqlglot.parse_one(s, read='snowflake')))\n    except Exception as e: print('ERR', s, type(e).__name__, str(e)[:200])\n\"; sed -n 1082,1090p sqlglot/parser.py; grep -n \"\\\"DROP\\\"\\|\\\"ALTER\\\"\\|\\\"CREATE\\\"\" sqlglot/tokens.py sqlglot/dialects/snowflake.py | head", "description": "Check current UNDROP parse behavior in Snowflake"}
[tool_result] ERR UNDROP TABLE t ParseError Invalid expression / Unexpected token. Line 1, Col: 14.
  UNDROP TABLE [4mt[0m
ERR UNDROP SCHEMA s ParseError Invalid expression / Unexpected token. Line 1, Col: 15.
  UNDROP SCHEMA [4ms[0m
ERR UNDROP DATABASE d ParseError Invalid expression / Unexpected token. Line 1, Col: 17.
  UNDROP DATABASE [4md[0m
ERR UNDROP DYNAMIC TABLE t ParseError Invalid expression / Unexpected token. Line 1, Col: 20.
  UNDROP DYNAMIC [4mTABLE[0m t
ERR UNDROP TABLE IDENTIFIER(123)
…[312 chars elided]…
arse_transaction(),
        TokenType.CACHE: lambda self: self._parse_cache(),
        TokenType.COMMENT: lambda self: self._parse_comment(),
        TokenType.COMMIT: lambda self: self._parse_commit_or_rollback(),
        TokenType.COPY: lambda self: self._parse_copy(),
        TokenType.CREATE: lambda self: self._parse_create(),
sqlglot/tokens.py:269:        "CREATE": TokenType.CREATE,
sqlglot/tokens.py:286:        "DROP": TokenType.DROP,
sqlglot/tokens.py:518:        "ALTER": TokenType.ALTER,
[tool_use Bash] {"command": "grep -n \"STATEMENT_PARSERS\\|KEYWORDS = {\\|\\\"SHOW\\\"\\|\\\"USE\\\"\\|\\\"PUT\\\"\\|\\\"REMOVE\\\"\\|\\\"LIST\\\"\\|class Tokenizer\\|class Parser\\|class Generator\\|IDENTIFIER\\|_parse_identifier\\|def _parse_show\" sqlglot/dialects/snowflake.py | head -60; grep -n \"class Undrop\\|class Use\\b\\|class Show\\|class Describe\" sqlglot/expressions.py", "description": "Survey Snowflake dialect parser/tokenizer hooks"}
[tool_result ERROR] Exit code 2
133:    class Tokenizer(tokens.Tokenizer):
140:        KEYWORDS = {
154:            "PUT": TokenType.PUT,
155:            "REMOVE": TokenType.COMMAND,
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "ls sqlglot | head -80; sed -n 125,200p sqlglot/dialects/snowflake.py", "description": "List sqlglot package and Snowflake tokenizer section"}
[tool_result] __init__.py
__main__.py
__pycache__
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
        )

    class JSONPathTokenizer(jsonpath.JSONPathTokenizer):
        SINGLE_TOKENS = jsonpath.JSONPathTokenizer.SINGLE_TOKENS.copy()
        SINGLE_TOKENS.pop("$")

    Parser = SnowflakeParser

  
…[1572 chars elided]…
 https://docs.snowflake.com/en/sql-reference/data-types-numeric#float
            # FLOAT is a synonym for DOUBLE in Snowflake
            "FLOAT": TokenType.DOUBLE,
        }
        KEYWORDS.pop("/*+")

        SINGLE_TOKENS = {
            **tokens.Tokenizer.SINGLE_TOKENS,
            "$": TokenType.PARAMETER,
            "!": TokenType.EXCLAMATION,
        }

        VAR_SINGLE_TOKENS = {"$"}

        COMMANDS = tokens.Tokenizer.COMMANDS - {TokenType.SHOW}

    Generator = SnowflakeGenerator
[tool_use Bash] {"command": "ls sqlglot/parsers sqlglot/generators; grep -n \"STATEMENT_PARSERS\\|_parse_undrop\\|UNDROP\\|\\\"TAG\\\"\\|CREATABLES\\|CREATABLE_KIND\" -r sqlglot/ | grep -v __pycache__ | head -40", "description": "Survey parsers, generators and creatable kinds"}
[tool_result] sqlglot/generators:
__init__.py
__pycache__
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
python.py
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

sqlglot/parsers:
__init__.py
__pycache__
athena.py
base.py
bigquery.py
clickhouse.py
databricks.py
doris
…[3167 chars elided]…
869:        *parser.Parser.CREATABLES,
sqlglot/parsers/snowflake.py:911:                kind = self._match_set(self.CREATABLES) and self._prev.text.upper()
sqlglot/parsers/snowflake.py:1010:        if isinstance(expression, exp.Create) and expression.kind in self.NON_TABLE_CREATABLES:
sqlglot/parsers/snowflake.py:1159:            elif self._match_set(self.DB_CREATABLES):
sqlglot/parsers/sqlite.py:46:    STATEMENT_PARSERS = {
sqlglot/parsers/sqlite.py:47:        **parser.Parser.STATEMENT_PARSERS,
[tool_use Bash] {"command": "sed -n 740,900p sqlglot/parsers/snowflake.py; sed -n 615,660p sqlglot/parser.py", "description": "Read Snowflake parser statement and creatable sections"}
[tool_result]     }
    FUNCTION_PARSERS = {k: v for k, v in FUNCTION_PARSERS.items() if k != "TRIM"}

    TIMESTAMPS = parser.Parser.TIMESTAMPS - {TokenType.TIME}

    ALTER_PARSERS = {
        **parser.Parser.ALTER_PARSERS,
        "MODIFY": lambda self: self._parse_alter_table_alter(),
        "SESSION": lambda self: self._parse_alter_session(),
        "UNSET": lambda self: self.expression(
            exp.Set(
                tag=self._match_text_seq("TAG"),
                expressions=self._parse_csv(se
…[6570 chars elided]…
BLES: t.ClassVar = {
        TokenType.COLUMN,
        TokenType.CONSTRAINT,
        TokenType.FOREIGN_KEY,
        TokenType.FUNCTION,
        TokenType.INDEX,
        TokenType.PROCEDURE,
        TokenType.TRIGGER,
        TokenType.TYPE,
        *DB_CREATABLES,
    }

    TRIGGER_EVENTS: t.ClassVar = {
        TokenType.INSERT,
        TokenType.UPDATE,
        TokenType.DELETE,
        TokenType.TRUNCATE,
    }

    ALTERABLES: t.ClassVar = {
        TokenType.INDEX,
        TokenType.TABLE,
[tool_use Bash] {"command": "grep -rn \"\\bGET\\b\\|TokenType.PUT\\b\" sqlglot/ --include=*.py | grep -v __pycache__ | head; grep -rn \"class Put\\b\\|class Get\\b\\|class Drop\\b\" -A12 sqlglot/expressions/*.py | head -60; ls sqlglot/expressions", "description": "Find TokenType GET/PUT usage and Drop expression"}
[tool_result] (eval):1: no matches found: --include=*.py
sqlglot/expressions/ddl.py:345:class Drop(Expression):
sqlglot/expressions/ddl.py-346-    arg_types = {
sqlglot/expressions/ddl.py-347-        "this": False,
sqlglot/expressions/ddl.py-348-        "kind": False,
sqlglot/expressions/ddl.py-349-        "expressions": False,
sqlglot/expressions/ddl.py-350-        "exists": False,
sqlglot/expressions/ddl.py-351-        "temporary": False,
sqlglot/expressions/ddl.py-352-        "materialized": False,
sqlglot
…[934 chars elided]…
py-946-        "alias": False,
sqlglot/expressions/query.py-947-        "db": False,
sqlglot/expressions/query.py-948-        "catalog": False,
sqlglot/expressions/query.py-949-        "laterals": False,
sqlglot/expressions/query.py-950-        "joins": False,
sqlglot/expressions/query.py-951-        "pivots": False,
__init__.py
__pycache__
aggregate.py
array.py
builders.py
constraints.py
core.py
datatypes.py
ddl.py
dml.py
functions.py
json.py
math.py
properties.py
query.py
string.py
temporal.py
[tool_use Bash] {"command": "grep -rn \"TokenType.GET\\b\\|TokenType.PUT\\b\\|GET = \\|PUT = \\|UNDROP\" sqlglot/ | grep -v __pycache__; grep -n \"def _parse_put\\|def _parse_get\" -A12 sqlglot/parsers/snowflake.py | head -40; grep -n \"def put_sql\\|def get_sql\\|def put_sql\" -A8 sqlglot/generators/snowflake.py sqlglot/generator.py | head -30; grep -n \"class Get\\|class Put\" -B2 sqlglot/expressions/query.py | head", "description": "Trace GET/PUT token and generator handling"}
[tool_result] sqlglot/tokenizer_core.py:306:    GET = auto()
sqlglot/tokenizer_core.py:386:    PUT = auto()
sqlglot/parser.py:706:        TokenType.GET,
sqlglot/parser.py:732:        TokenType.PUT,
sqlglot/parser.py:839:        TokenType.GET,
sqlglot/parsers/snowflake.py:760:        TokenType.GET: lambda self: self._parse_get(),
sqlglot/parsers/snowflake.py:761:        TokenType.PUT: lambda self: self._parse_put(),
sqlglot/dialects/snowflake.py:145:            "GET": TokenType.GET,
sqlglot/dialects/snowflake.
…[611 chars elided]…
n we need to parse a function, not a statement
1200-        if self._match(TokenType.L_PAREN):
1201-            self._retreat(self._index - 2)
1202-            return self._parse_expression()
1203-
1204-        target = self._parse_location_path()
1205-
1206-        # Parse as command if unquoted file path
1207-        if self._curr.token_type == TokenType.URI_START:
1208-            return self._parse_as_command(start)
933-
934-
935:class Put(Expression):
--
937-
938-
939:class Get(Expression):
[tool_use Bash] {"command": "sed -n 300,312p sqlglot/tokenizer_core.py; sed -n 380,390p sqlglot/tokenizer_core.py; sed -n 700,710p sqlglot/parser.py; sed -n 728,734p sqlglot/parser.py; sed -n 835,842p sqlglot/parser.py; <work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfor s in [\\\"DROP TABLE IDENTIFIER('x')\\\",\\\"DROP TABLE IDENTIFIER('\\\\\\\"abc\\\\\\\"')\\\", 'DROP DYNAMIC TABLE t', 'DROP ICEBERG TABLE t','DROP EXTERNAL VOLUME v','DROP SNAPSHOT s','DROP NOTEBOOK n','DROP ACCOUNT a']:\n    try: print(repr(sqlglot.parse_one(s, read='snowflake')))\n    except Exception as e: print('ERR', s, str(e)[:120])\n\"", "description": "Inspect tokens and how DROP forms parse today"}
[tool_result]     FORCE = auto()
    FOREIGN_KEY = auto()
    FORMAT = auto()
    FROM = auto()
    FULL = auto()
    FUNCTION = auto()
    GET = auto()
    GLOB = auto()
    GLOBAL = auto()
    GRANT = auto()
    GROUP_BY = auto()
    GROUPING_SETS = auto()
    HAVING = auto()
    PRAGMA = auto()
    PREWHERE = auto()
    PRIMARY_KEY = auto()
    PROCEDURE = auto()
    PROPERTIES = auto()
    PSEUDO_TYPE = auto()
    PUT = auto()
    QUALIFY = auto()
    QUOTE = auto()
    QDCOLON = auto()
    RANGE = auto()
…[1751 chars elided]…
lse,
  iceberg=False)
Command(this=DROP, expression=DYNAMIC TABLE t)
Drop(
  exists=False,
  this=Table(
    this=Identifier(this=t, quoted=False)),
  kind=TABLE,
  temporary=False,
  materialized=False,
  cascade=False,
  restrict=False,
  constraints=False,
  purge=False,
  concurrently=False,
  sync=False,
  iceberg=True)
Command(this=DROP, expression=EXTERNAL VOLUME v)
Command(this=DROP, expression=SNAPSHOT s)
Command(this=DROP, expression=NOTEBOOK n)
Command(this=DROP, expression=ACCOUNT a)
[tool_use Bash] {"command": "grep -n \"def _match_text_seq\" -A22 sqlglot/parser.py | head -30; grep -n \"def drop_sql\" -A25 sqlglot/generator.py sqlglot/generators/*.py | head -40; grep -n \"class Drop\" -A30 sqlglot/expressions/ddl.py | sed -n 14,30p; sed -n 700,706p sqlglot/parser.py; grep -n \"^    [A-Z_]* = \\|^    [A-Z_]*: t.ClassVar\" sqlglot/parser.py | sed -n 1,20p", "description": "Inspect text-seq matching, drop generator, and token sets"}
[tool_result] 1955:    def _match_text_seq(self, *texts: str, advance: bool = True) -> bool:
1956-        index = self._index
1957-        string_type = TokenType.STRING
1958-        for text in texts:
1959-            if self._curr.token_type != string_type and self._curr.text.upper() == text:
1960-                self._advance()
1961-            else:
1962-                self._retreat(index)
1963-                return False
1964-
1965-        if not advance:
1966-            self._retreat(index)
1967-
196
…[4714 chars elided]…
ClassVar = {
601:    SUBQUERY_PREDICATES: t.ClassVar = {
608:    SUBQUERY_TOKENS: t.ClassVar = {
614:    RESERVED_TOKENS: t.ClassVar = {
619:    DB_CREATABLES: t.ClassVar = {
639:    CREATABLES: t.ClassVar = {
651:    TRIGGER_EVENTS: t.ClassVar = {
658:    ALTERABLES: t.ClassVar = {
666:    ID_VAR_TOKENS: t.ClassVar[set] = {
772:    TABLE_ALIAS_TOKENS: t.ClassVar[set] = ID_VAR_TOKENS - {
784:    ALIAS_TOKENS: t.ClassVar = ID_VAR_TOKENS
786:    COLON_PLACEHOLDER_TOKENS: t.ClassVar = ID_VAR_TOKENS
[tool_use Bash] {"command": "grep -n \"def \\(put\\|get\\|show\\|describe\\|use\\)\\w*_sql\\|def _parse_show\\|def \\w*_sql\" sqlglot/generators/snowflake.py | head -30; sed -n 645,660p sqlglot/parser.py | head -3; sed -n 666,668p sqlglot/parser.py; grep -n \"TokenType.GET,\\|TokenType.UNION\\|TokenType.UNNEST\" sqlglot/parser.py | head; grep -n \"    UNION\\|    UNNEST\\|    UNKNOWN\\|    UNIQUE\\|    UPDATE\" sqlglot/tokenizer_core.py", "description": "Find Snowflake generator statement methods and token layout"}
[tool_result] 63:def _regexpilike_sql(self: SnowflakeGenerator, expression: exp.RegexpILike) -> str:
202:def _regexpextract_sql(
229:def _json_extract_value_array_sql(
619:    def sortarray_sql(self, expression: exp.SortArray) -> str:
626:    def nthvalue_sql(self, expression: exp.NthValue) -> str:
680:    def values_sql(self, expression: exp.Values, values_as_table: bool = True) -> str:
686:    def datatype_sql(self, expression: exp.DataType) -> str:
717:    def tonumber_sql(self, expression: exp.ToNumber) -
…[1611 chars elided]…
TokenType.ALL,
        TokenType.ANALYZE,
445:        TokenType.UNION,
706:        TokenType.GET,
754:        TokenType.UNNEST,
770:    } - {TokenType.UNION}
839:        TokenType.GET,
858:        TokenType.UNNEST,
940:        TokenType.UNION,
4983:        if not self._match_pair(TokenType.UNNEST, TokenType.L_PAREN, advance=False):
5694:        if token_type == TokenType.UNION:
232:    UNKNOWN = auto()
434:    UNION = auto()
435:    UNNEST = auto()
437:    UPDATE = auto()
450:    UNIQUE = auto()
[assistant] Snowflake has no existing UNDROP support, and `IDENTIFIER(...)` already parses through `_parse_table_parts`. I'll follow the GET/PUT pattern: a new `TokenType.UNDROP`, a `STATEMENT_PARSERS` entry, an `exp.Undrop` node, and a generator method.
[tool_use Bash] {"command": "sed -n 430,436p sqlglot/tokenizer_core.py && sed -n 704,708p sqlglot/parser.py && sed -n 366,372p sqlglot/expressions/ddl.py && sed -n 836,870p sqlglot/generators/snowflake.py && grep -n \"def test_\\|Snowflake\\|snowflake\" tests/dialects/test_snowflake.py | head -5", "description": "Read insertion points for token, expression, generator"}
[tool_result]     TRUNCATE = auto()
    TRIGGER = auto()
    TYPE = auto()
    UNCACHE = auto()
    UNION = auto()
    UNNEST = auto()
    UNPIVOT = auto()
        TokenType.FORMAT,
        TokenType.FULL,
        TokenType.GET,
        TokenType.IDENTIFIER,
        TokenType.INOUT,
        return kind and kind.upper()


class DropPrimaryKey(Expression):
    arg_types = {}


        )

        return f"{value}{explode}{alias}"

    def show_sql(self, expression: exp.Show) -> str:
        terse = "TERSE " if e
…[910 chars elided]…
 privileges else ""

        return f"SHOW {terse}{iceberg}{expression.name}{history}{like}{scope_kind}{scope}{starts_with}{limit}{from_}{privileges}"

    def rowaccessproperty_sql(self, expression: exp.RowAccessProperty) -> str:
        if not expression.this:
11:class TestSnowflake(Validator):
13:    dialect = "snowflake"
15:    def test_snowflake(self):
35:        self.assertEqual(ast.sql("snowflake"), "DATEADD(MONTH, n, d)")
102:                "snowflake": "SELECT BITMAP_BIT_POSITION(10)",
[assistant] Now the edits.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-102538-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/tokenizer_core.py", "old_string": "    TYPE = auto()\n    UNCACHE = auto()\n    UNION = auto()", "new_string": "    TYPE = auto()\n    UNCACHE = auto()\n    UNDROP = auto()\n    UNION = auto()"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-102538-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/tokenizer_core.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-102538-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/dialects/snowflake.py", "old_string": "            \"TOP\": TokenType.TOP,\n            \"VOLUME\": TokenType.VOLUME,", "new_string": "            \"TOP\": TokenType.TOP,\n            \"UNDROP\": TokenType.UNDROP,\n            \"VOLUME\": TokenType.VOLUME,"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-102538-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/dialects/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-102538-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parser.py", "old_string": "        TokenType.FULL,\n        TokenType.GET,\n        TokenType.IDENTIFIER,\n        TokenType.INOUT,", "new_string": "        TokenType.FULL,\n        TokenType.GET,\n        TokenType.IDENTIFIER,\n        TokenType.INOUT,\n        TokenType.UNDROP,"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-102538-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-102538-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/expressions/ddl.py", "old_string": "class DropPrimaryKey(Expression):\n    arg_types = {}\n", "new_string": "class Undrop(Expression):\n    arg_types = {\"this\": True, \"kind\": True}\n\n\nclass DropPrimaryKey(Expression):\n    arg_types = {}\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-102538-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-102538-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/generators/snowflake.py", "old_string": "    def rowaccessproperty_sql(self, expression: exp.RowAccessProperty) -> str:", "new_string": "    def undrop_sql(self, expression: exp.Undrop) -> str:\n        return f\"UNDROP {expression.kind} {self.sql(expression, 'this')}\"\n\n    def rowaccessproperty_sql(self, expression: exp.RowAccessProperty) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-102538-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-102538-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "        TokenType.SHOW: lambda self: self._parse_show(),\n    }", "new_string": "        TokenType.SHOW: lambda self: self._parse_show(),\n        TokenType.UNDROP: lambda self: self._parse_undrop(),\n    }\n\n    UNDROP_KINDS = (\n        \"ACCOUNT\",\n        \"DATABASE\",\n        \"DYNAMIC TABLE\",\n        \"EXTERNAL VOLUME\",\n        \"ICEBERG TABLE\",\n        \"NOTEBOOK\",\n        \"SCHEMA\",\n        \"SNAPSHOT\",\n        \"STREAMLIT\",\n        \"TABLE\",\n        \"TAG\",\n        \"TYPE\",\n    )"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-102538-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[assistant] Now the parse method, placed next to `_parse_put`/`_parse_get`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-102538-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "    def _parse_get(self) -> exp.Expr | None:", "new_string": "    def _parse_undrop(self) -> exp.Undrop | exp.Command:\n        start = self._prev\n        kind = next((k for k in self.UNDROP_KINDS if self._match_text_seq(*k.split())), None)\n        if not kind:\n            return self._parse_as_command(start)\n\n        return self.expression(exp.Undrop(this=self._parse_table_parts(), kind=kind))\n\n    def _parse_get(self) -> exp.Expr | None:"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-102538-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\ncases = ['UNDROP TABLE t','UNDROP TABLE db.s.t','UNDROP SCHEMA s','UNDROP DATABASE d','UNDROP ACCOUNT a','UNDROP DYNAMIC TABLE t','UNDROP ICEBERG TABLE t','UNDROP EXTERNAL VOLUME v','UNDROP NOTEBOOK n','UNDROP SNAPSHOT s','UNDROP STREAMLIT st','UNDROP
…[24 chars elided]…
','UNDROP TABLE IDENTIFIER(123)',\\\"UNDROP TABLE IDENTIFIER('\\\\\\\"abc\\\\\\\"')\\\", 'UNDROP FOO x', 'SELECT undrop FROM undrop']\nfor s in cases:\n    try:\n        e = sqlglot.parse_one(s, read='snowflake'); print(type(e).__name__, '|', e.sql('snowflake'))\n    except Exception as ex: print('ERR', s, str(ex)[:150])\n\"", "description": "Smoke-test UNDROP parsing and generation across kinds"}
[tool_result] 'UNDROP FOO x' contains unsupported syntax. Falling back to parsing as a 'Command'.
ERR UNDROP TABLE t 'Undrop' object has no attribute 'kind'
ERR UNDROP TABLE db.s.t 'Undrop' object has no attribute 'kind'
ERR UNDROP SCHEMA s 'Undrop' object has no attribute 'kind'
ERR UNDROP DATABASE d 'Undrop' object has no attribute 'kind'
ERR UNDROP ACCOUNT a 'Undrop' object has no attribute 'kind'
ERR UNDROP DYNAMIC TABLE t 'Undrop' object has no attribute 'kind'
ERR UNDROP ICEBERG TABLE t 'Undrop' object 
…[105 chars elided]…
OTEBOOK n 'Undrop' object has no attribute 'kind'
ERR UNDROP SNAPSHOT s 'Undrop' object has no attribute 'kind'
ERR UNDROP STREAMLIT st 'Undrop' object has no attribute 'kind'
ERR UNDROP TAG tg 'Undrop' object has no attribute 'kind'
ERR UNDROP TYPE ty 'Undrop' object has no attribute 'kind'
ERR UNDROP TABLE IDENTIFIER(123) 'Undrop' object has no attribute 'kind'
ERR UNDROP TABLE IDENTIFIER('"abc"') 'Undrop' object has no attribute 'kind'
Command | UNDROP FOO x
Select | SELECT undrop FROM undrop
[assistant] The generator used a `.kind` attribute that `Undrop` doesn't have. I'll read it via `expression.text("kind")`, which is the accessor the rest of the generator uses.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-102538-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/generators/snowflake.py", "old_string": "        return f\"UNDROP {expression.kind} {self.sql(expression, 'this')}\"", "new_string": "        return f\"UNDROP {expression.text('kind')} {self.sql(expression, 'this')}\""}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-102538-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\ncases = ['UNDROP TABLE t','UNDROP TABLE db.s.t','UNDROP SCHEMA s','UNDROP DATABASE d','UNDROP ACCOUNT a','UNDROP DYNAMIC TABLE t','UNDROP ICEBERG TABLE t','UNDROP EXTERNAL VOLUME v','UNDROP NOTEBOOK n','UNDROP SNAPSHOT s','UNDROP STREAMLIT st','UNDROP
…[15 chars elided]…
P TYPE ty','UNDROP TABLE IDENTIFIER(123)',\\\"UNDROP TABLE IDENTIFIER('\\\\\\\"abc\\\\\\\"')\\\"]\nfor s in cases:\n    try:\n        e = sqlglot.parse_one(s, read='snowflake'); print(type(e).__name__, '|', e.sql('snowflake'), '|', e.sql('duckdb'))\n    except Exception as ex: print('ERR', s, str(ex)[:150])\n\" 2>&1 | grep -v Falling", "description": "Re-run UNDROP smoke test after generator fix"}
[tool_result] ERR UNDROP TABLE t Unsupported expression type Undrop
ERR UNDROP TABLE db.s.t Unsupported expression type Undrop
ERR UNDROP SCHEMA s Unsupported expression type Undrop
ERR UNDROP DATABASE d Unsupported expression type Undrop
ERR UNDROP ACCOUNT a Unsupported expression type Undrop
ERR UNDROP DYNAMIC TABLE t Unsupported expression type Undrop
ERR UNDROP ICEBERG TABLE t Unsupported expression type Undrop
ERR UNDROP EXTERNAL VOLUME v Unsupported expression type Undrop
ERR UNDROP NOTEBOOK n Unsupported expression type Undrop
ERR UNDROP SNAPSHOT s Unsupported expression type Undrop
ERR UNDROP STREAMLIT st Unsupported expression type Undrop
ERR UNDROP TAG tg Unsupported expression type Undrop
ERR UNDROP TYPE ty Unsupported expression type Undrop
ERR UNDROP TABLE IDENTIFIER(123) Unsupported expression type Undrop
ERR UNDROP TABLE IDENTIFIER('"abc"') Unsupported expression type Undrop
[assistant] Expected: `Undrop` is Snowflake-only, so other dialects can't generate it. I'll drop the duckdb call from the smoke test.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\ncases = ['UNDROP TABLE t','UNDROP TABLE db.s.t','UNDROP SCHEMA s','UNDROP DATABASE d','UNDROP ACCOUNT a','UNDROP DYNAMIC TABLE t','UNDROP ICEBERG TABLE t','UNDROP EXTERNAL VOLUME v','UNDROP NOTEBOOK n','UNDROP SNAPSHOT s','UNDROP STREAMLIT st','UNDROP TAG tg','UNDROP TYPE ty','UNDROP TABLE IDENTIFIER(123)',\\\"UNDROP TABLE IDENTIFIER('\\\\\\\"abc\\\\\\\"')\\\"]\nfor s in cases:\n    try:\n        e = sqlglot.parse_one(s, read='snowflake'); print(type(e).__name__, '|', e.sql('snowflake'))\n    except Exception as ex: print('ERR', s, str(ex)[:150])\n\" 2>&1 | grep -v Falling", "description": "Smoke-test UNDROP round-trip for all kinds"}
[tool_result] Undrop | UNDROP TABLE t
Undrop | UNDROP TABLE db.s.t
Undrop | UNDROP SCHEMA s
Undrop | UNDROP DATABASE d
Undrop | UNDROP ACCOUNT a
Undrop | UNDROP DYNAMIC TABLE t
Undrop | UNDROP ICEBERG TABLE t
Undrop | UNDROP EXTERNAL VOLUME v
Undrop | UNDROP NOTEBOOK n
Undrop | UNDROP SNAPSHOT s
Undrop | UNDROP STREAMLIT st
Undrop | UNDROP TAG tg
Undrop | UNDROP TYPE ty
Undrop | UNDROP TABLE IDENTIFIER(123)
Undrop | UNDROP TABLE IDENTIFIER('"abc"')
[assistant] All kinds round-trip. Now I'll add tests next to the existing Snowflake statement tests.
[tool_use Bash] {"command": "grep -n \"    def test_\" tests/dialects/test_snowflake.py | head -80 | tail -60; grep -n \"PUT '\\|def test_ddl\\|def test_.*show\" tests/dialects/test_snowflake.py | head", "description": "Find test method layout in Snowflake test file"}
[tool_result] 4807:    def test_regexp_functions(self, logger):
5046:    def test_regexp_replace(self, logger):
5138:    def test_replace(self):
5166:    def test_match_recognize(self):
5204:    def test_show_users(self):
5209:    def test_show_databases(self):
5219:    def test_show_file_formats(self):
5228:    def test_show_functions(self):
5236:    def test_show_procedures(self):
5245:    def test_show_stages(self):
5254:    def test_show_warehouses(self):
5261:    def test_show_schemas(self):
5271:    def
…[1745 chars elided]…
27:    def test_float_interval(self):
6360:    def test_transpile_bitwise_ops(self):
6391:    def test_quoting(self):
4238:    def test_ddl(self):
5204:    def test_show_users(self):
5209:    def test_show_databases(self):
5219:    def test_show_file_formats(self):
5228:    def test_show_functions(self):
5236:    def test_show_procedures(self):
5245:    def test_show_stages(self):
5254:    def test_show_warehouses(self):
5261:    def test_show_schemas(self):
5271:    def test_show_objects(self):
[tool_use Bash] {"command": "sed -n 5351,5358p tests/dialects/test_snowflake.py", "description": "View existing drop iceberg test for style"}
[tool_result]     def test_drop_iceberg_table(self):
        ast = self.validate_identity("DROP ICEBERG TABLE t")
        self.assertTrue(ast.args["iceberg"])
        self.validate_identity("DROP ICEBERG TABLE IF EXISTS t")
        ast = self.validate_identity("DROP ICEBERG TABLE t RESTRICT")
        self.assertTrue(ast.args["restrict"])
        self.validate_identity("DROP ICEBERG TABLE IF EXISTS t RESTRICT")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-102538-snowflake-dialect-snowflake-s-ti/base-1/tests/dialects/test_snowflake.py", "old_string": "    def test_drop_iceberg_table(self):\n        ast = self.validate_identity(\"DROP ICEBERG TABLE t\")", "new_string": "    def test_undrop(self):\n        for kind in (\n            \"TABLE\",\n         
…[498 chars elided]…
al(ast.text(\"kind\"), kind)\n\n        self.validate_identity(\"UNDROP TABLE db.s.t\")\n        self.validate_identity(\"UNDROP TABLE IDENTIFIER(123)\")\n        self.validate_identity(\"UNDROP TABLE IDENTIFIER('\\\"abc\\\"')\")\n        self.validate_identity(\"SELECT undrop FROM undrop\")\n\n    def test_drop_iceberg_table(self):\n        ast = self.validate_identity(\"DROP ICEBERG TABLE t\")"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-102538-snowflake-dialect-snowflake-s-ti/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"^from\\|^import\" tests/dialects/test_snowflake.py | head -5; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | tail -15", "description": "Run Snowflake dialect tests"}
[tool_result] 1:from unittest import mock
3:from sqlglot import ParseError, UnsupportedError, exp, parse_one
4:from sqlglot.parser import logger as parser_logger
5:from sqlglot.optimizer.annotate_types import annotate_types
6:from sqlglot.optimizer.normalize_identifiers import normalize_identifiers
............................... [ 32%]
.................................................................                                                     [100%]
96 passed, 1580 subtests passed in 0.56s
[assistant] Snowflake tests pass. Now the full suite, plus a lint pass.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; <work>/env-sqlglot/bin/python -m ruff check sqlglot tests/dialects/test_snowflake.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot tests/dialects/test_snowflake.py 2>&1 | tail -3", "description": "Run full test suite and ruff lint/format checks"}
[tool_result] ........................................................... [ 77%]
............................................ [ 81%]
...................................................................... [ 87%]
........................ [ 89%]
.................................................................. [ 95%]
............................................ [ 99%]
........                                                            [100%]
1121 passed, 18188 subtests passed in 50.72s
All checks passed!
177 files already formatted
[tool_use Bash] {"command": "git status --short && git diff --stat", "description": "Show changed files summary"}
[tool_result]  M sqlglot/dialects/snowflake.py
 M sqlglot/expressions/ddl.py
 M sqlglot/generators/snowflake.py
 M sqlglot/parser.py
 M sqlglot/parsers/snowflake.py
 M sqlglot/tokenizer_core.py
 M tests/dialects/test_snowflake.py
 sqlglot/dialects/snowflake.py    |  1 +
 sqlglot/expressions/ddl.py       |  4 ++++
 sqlglot/generators/snowflake.py  |  3 +++
 sqlglot/parser.py                |  1 +
 sqlglot/parsers/snowflake.py     | 24 ++++++++++++++++++++++++
 sqlglot/tokenizer_core.py        |  1 +
 tests/dialects/test_snowflake.py | 25 +++++++++++++++++++++++++
 7 files changed, 59 insertions(+)
[assistant] Snowflake `UNDROP` now parses and regenerates for all twelve object types you listed, including the `IDENTIFIER(...)` form. The full suite passes (1121 tests) and ruff is clean. I did not commit.

**What changed**
- **Tokenizer:** `UNDROP` is a Snowflake keyword mapping to a new `TokenType.UNDROP`, following the `GET`/`PUT` pattern. It is also added to the base `ID_VAR_TOKENS`, so `undrop` still works as an identifier (`SELECT undrop FROM undrop` round-trips).
- **Parser:** `_parse_undrop` in `sqlglot/parsers/snowflake.py` matches one of the twelve kinds in `UNDROP_KINDS`, then parses the targ
…[258 chars elided]…
ndrop_sql` in `sqlglot/generators/snowflake.py` emits `UNDROP <kind> <name>`.
- **Tests:** `test_undrop` in `tests/dialects/test_snowflake.py` covers every kind, multi-part names, both `IDENTIFIER` forms, and the identifier case.

**Decisions to check**
- I made `Undrop` Snowflake-only: the generator method lives in the Snowflake generator. Other dialects can't emit it. Moving `undrop_sql` into the base generator is a one-line change if you want it available everywhere.
- `UNDROP` is now a reserved-ish keyword in the Snowflake tokenizer. It is still usable as an identifier via `ID_VAR_TOKENS`.
