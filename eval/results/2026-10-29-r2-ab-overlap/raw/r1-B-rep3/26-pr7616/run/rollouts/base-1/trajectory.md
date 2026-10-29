# trajectory base-1

final message:
`CREATE TYPE` now parses into AST nodes for enum and composite types, and both round-trip in Postgres. The full test suite passed (1106 tests) before the final formatter pass. That pass only rewrapped one line, and the Postgres tests still pass after it.

```python
parse_one("CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')", "postgres").sql("postgres")
# "CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')"
parse_one("CREATE TYPE complex AS (r DOUBLE PRECISION, i TEXT)", "postgres").sql("postgres")
# "CREATE TYPE complex AS (r DOUBLE PRECISION, i TEXT)"
```

Changes:
- **`sqlglot/expressions/ddl.py`**: new `EnumType` expression holding the enum labels.
- **`sqlglot/parsers/postgres.py`**: `PostgresParser._parse_create` handles `CREATE TYPE <name> AS ENUM (...)` and `CREATE TYPE <name> AS (attr type, ...)`, producing `exp.Create(kind="TYPE", ...)`. Anything else, including shell types and `AS RANGE`, falls back to the existing behaviour.
- **`sqlglot/generators/postgres.py`**: `enumtype_sql` renders `ENUM ('a', 'b')`. Composite types reuse the existing `Schema` generation.
- **`tests/dialects/test_postgres.py`**: `test_create_type` covers enum and composite round-trips, a schema-qualified name, and checks that the enum parses to `exp.EnumType`.

Choices I made that you may want to review:
- Composite types are stored as the `Schema` of column definitions, not a new node.
- Only enum and composite are handled. `CREATE TYPE x` (shell) and `AS RANGE` still fall back to `Command`, as the task scoped.
- The changes are uncommitted in the worktree.

## events
[tool_use Bash] {"command": "git status --short | head && grep -n \"TYPE\\|ENUM\" sqlglot/dialects/postgres.py | head -60 && grep -n \"_parse_create\\b\\|def _parse_create\" sqlglot/parser.py | head && grep -n \"class Create\\b\\|class Create(\" -A12 sqlglot/expressions.py && grep -n \"class EnumColumnConstraint\\|class.*Composite\\|class DataType\\b\" sqlglot/expressions.py", "description": "Inspect postgres dialect and parser CREATE handling"}
[tool_result ERROR] Exit code 2
ok3 matches in 3 files:

111:0:TokenType.OBJECT_IDENTIFIER,
84:0:TokenType.PSEUDO_TYPE,
sqlglot/dialects/postgres.py:12:TYPED_DIVISION = True
3 matches in 3 files:

1088:0:lambda self: self._parse_create(),
2344:0:
3280:0:
grep: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "ls && grep -rn \"def _parse_create\" sqlglot/ | head; grep -n \"class Create(\" -A25 sqlglot/expressions/*.py | head -40; grep -rn \"\\\"TYPE\\\"\" sqlglot/parser.py sqlglot/dialects/postgres.py | head", "description": "Locate parser and expression files"}
[tool_result] .agents/
.claude/
.github/
.lithify/
benchmarks/
pdoc/
posts/
sqlglot/
sqlglot-integration-tests/
sqlglotc/
tests/
.gitignore  1.9K
.gitmodules  135B
.gitpod.yml  217B
.pre-commit-config.yaml  1.7K
AGENTS.md  18.1K
CHANGELOG.md  1.8M
CLAUDE.md -> AGENTS.md  9B
CONTRIBUTING.md  3.8K
LICENSE  1.0K
MANIFEST.in  70B
Makefile  3.1K
README.md  22.6K
pyproject.toml  1.3K
setup.cfg  241B
setup.py  1.2K
sqlglot.png  7.2K
sqlglot/parsers/fabric.py:8:    def _parse_create(self) -> exp.Create | exp.Command:
…[1439 chars elided]…
ns/ddl.py-57-
sqlglot/expressions/ddl.py-58-    @property
sqlglot/expressions/ddl.py-59-    def kind(self) -> str | None:
sqlglot/expressions/ddl.py-60-        kind = self.args.get("kind")
sqlglot/expressions/ddl.py-61-        return kind and kind.upper()
sqlglot/expressions/ddl.py-62-
sqlglot/expressions/ddl.py-63-
sqlglot/expressions/ddl.py-64-class SequenceProperties(Expression):
sqlglot/parser.py:1629:        "TYPE": ("EVOLUTION",),
sqlglot/parser.py:8627:        self._match_text_seq("TYPE")
[tool_use Bash] {"command": "sed -n 2344,2480p sqlglot/parser.py; ls sqlglot/parsers/ | head -80; grep -n \"CREATABLES\\|\\\"TYPE\\\"\" sqlglot/parser.py sqlglot/parsers/postgres.py sqlglot/tokens.py sqlglot/generators/postgres.py sqlglot/generator.py | head -30", "description": "Read base _parse_create implementation"}
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
…[6450 chars elided]…
ev.text.upper()
sqlglot/parser.py:2370:create_token = self._match_set(self.CREATABLES) and self._prev
sqlglot/parser.py:2375:create_token = self._match_set(self.CREATABLES) and self._prev
sqlglot/parser.py:2488:elif create_token_type in self.DB_CREATABLES:
sqlglot/parser.py:3337:kind = self._prev.text if self._match_set(self.CREATABLES) else None
sqlglot/parser.py:8627:self._match_text_seq("TYPE")
sqlglot/parser.py:9525:kind = self._prev.text.upper() if self._match_set(self.CREATABLES) else None
[tool_use Bash] {"command": "sed -n 2480,2600p sqlglot/parser.py; sed -n 615,660p sqlglot/parser.py; cat sqlglot/parsers/postgres.py | head -80; grep -n \"CREATE\\|TYPE\" sqlglot/generators/postgres.py | head -20", "description": "Read rest of _parse_create and postgres parser/generator"}
[tool_result]                     referencing=referencing,
                    for_each=for_each,
                    when=when,
                )
            )

            this = trigger_name
            extend_props(exp.Properties(expressions=[trigger_props] if trigger_props else []))
        elif create_token_type in self.DB_CREATABLES:
            table_parts = self._parse_table_parts(
                schema=True, is_db_reference=create_token_type == TokenType.SCHEMA
            )

            # exp.Prop
…[8693 chars elided]…
ON_EXTRACT_TYPE) -> str:
sqlglot/generators/postgres.py:8:JSON_EXTRACT_TYPE,
sqlglot/generators/postgres.py:245:JSON_TYPE_REQUIRED_FOR_EXTRACTION = True
sqlglot/generators/postgres.py:272:TYPE_MAPPING = {
sqlglot/generators/postgres.py:273:**generator.Generator.TYPE_MAPPING,
sqlglot/generators/postgres.py:402:self.unsupported("Table comments are not supported in the CREATE statement")
sqlglot/generators/postgres.py:406:self.unsupported("Column comments are not supported in the CREATE statement")
[tool_use Bash] {"command": "grep -rn \"ENUM\\b\" sqlglot/tokens.py sqlglot/parser.py sqlglot/parsers/*.py sqlglot/generators/*.py | head -30; grep -n \"^    TYPE\\b\\|\\\"TYPE\\\"\\|TokenType.TYPE\\b\" sqlglot/tokens.py sqlglot/parsers/*.py | head; grep -rn \"class.*Enum\\|class .*Type(\" sqlglot/expressions/*.py | head -20; grep -n \"AS ENUM\\|CREATE TYPE\" -ri tests/ | head", "description": "Search for enum, TYPE token, and existing tests"}
[tool_result] sqlglot/tokens.py:288:        "ENUM": TokenType.ENUM,
sqlglot/parser.py:460:        TokenType.ENUM,
sqlglot/generators/clickhouse.py:240:        exp.DType.ENUM: "Enum",
sqlglot/generators/singlestore.py:351:        exp.DType.ENUM8: "ENUM",
sqlglot/generators/singlestore.py:352:        exp.DType.ENUM16: "ENUM",
3 matches in 3 files:

sqlglot/parsers/clickhouse.py:795:index_type = self._match_text_seq("TYPE") and (self._parse_function() or self...
sqlglot/parsers/hive.py:235:if self.CHANGE_COLUMN_
…[522 chars elided]…
:        self.validate_identity("CAST(x AS ENUM('a', 'b'))")
tests/dialects/test_clickhouse.py:73:        self.validate_identity("CAST(x AS Enum('hello' = 1, 'world' = 2))")
tests/dialects/test_clickhouse.py:74:        self.validate_identity("CAST(x AS Enum('hello', 'world'))")
tests/dialects/test_clickhouse.py:75:        self.validate_identity("CAST(x AS Enum('hello' = 1, 'world'))")
tests/dialects/test_clickhouse.py:76:        self.validate_identity("CAST(x AS Enum8('hello' = -123, 'world'))")
[tool_use Bash] {"command": "grep -n \"def create_sql\" -A75 sqlglot/generator.py | head -120; grep -n \"ENUM\\|STRUCT\\|def datatype_sql\" sqlglot/generators/postgres.py sqlglot/generator.py | head -20", "description": "Read create_sql generator and postgres type mappings"}
[tool_result] 1284:    def create_sql(self, expression: exp.Create) -> str:
1285-        kind = self.sql(expression, "kind")
1286-        kind = self.dialect.INVERSE_CREATABLE_KIND_MAPPING.get(kind) or kind
1287-
1288-        properties = expression.args.get("properties")
1289-
1290-        if (
1291-            kind == "TRIGGER"
1292-            and properties
1293-            and properties.expressions
1294-            and isinstance(properties.expressions[0], exp.TriggerProperties)
1295-            and pro
…[3160 chars elided]…
clustered:
6 matches in 2 files:

sqlglot/generator.py:388:SELECT_KINDS: tuple[str, ...] = ("STRUCT", "VALUE")
sqlglot/generator.py:652:STRUCT_DELIMITER: t.ClassVar = ("<", ">")
sqlglot/generator.py:1683:def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/generator.py:1724:nested = f"{self.STRUCT_DELIMITER[0]}{interior}{self.STRUCT_DELIMITER[1]}"
sqlglot/generator.py:3147:if kind == "STRUCT":
sqlglot/generators/postgres.py:477:def datatype_sql(self, expression: exp.DataType) -> str:
[tool_use Bash] {"command": "grep -n \"class Parser\\|class PostgresParser\\|class Postgres\\|^    FUNCTIONS\\|^    def \" sqlglot/parsers/postgres.py | head -40; grep -n \"^class \\|^    def .*_sql\" sqlglot/generators/postgres.py | head -60; grep -n \"def _try_parse\\|def _parse_wrapped_csv\\|def _parse_column_def\\|def _parse_table_parts\\|def _parse_schema\\|def _parse_as_command\" sqlglot/parser.py; grep -n \"class Schema\\|class ColumnDef\" -A3 sqlglot/expressions/*.py; grep -n \"^class DDL\\|^class EnumColumn\" sqlglot/expressions/*.py", "description": "Inspect postgres parser/generator structure and helpers"}
[tool_result] 11 matches in 10 files:

205:0:
253:0:TokenType) -> exp.InOutColumnConstraint:
271:0:
290:0:
299:0:
309:0:
312:0:
335:0:exp.Identifier) -> exp.Expr | None:
83:0:
sqlglot/parsers/postgres.py:97:FUNCTIONS = {
sqlglot/parsers/postgres.py:321:def _parse_generated_as_identity(
20 matches in 20 files:

225:0:
264:0:exp.Lateral) -> str:
401:0:exp.SchemaCommentProperty) -> str:
405:0:exp.CommentColumnConstraint) -> str:
409:0:exp.ColumnDef, sep: str = " ") -> str:
421:0:exp.Unnest) -> str:
452:0:exp.Bra
…[1011 chars elided]…
query.py:502:class ColumnDef(Expression):
sqlglot/expressions/query.py-503-    arg_types = {
sqlglot/expressions/query.py-504-        "this": True,
sqlglot/expressions/query.py-505-        "kind": False,
--
sqlglot/expressions/query.py:1115:class Schema(Expression):
sqlglot/expressions/query.py-1116-    arg_types = {"this": False, "expressions": False}
sqlglot/expressions/query.py-1117-
sqlglot/expressions/query.py-1118-
1 matches in 1 files:

sqlglot/expressions/ddl.py:16:class DDL(Selectable):
[tool_use Bash] {"command": "ls sqlglot/dialects | head -50; grep -n \"^class \\|    class \\|_parse_create\\|PARSERS\\|STATEMENT\" sqlglot/dialects/postgres.py | head -30; grep -n \"class Parser\\|_parse_create\\|def _parse_statement\" -n sqlglot/parsers/*.py | head -20; sed -n 2000,2025p sqlglot/parser.py; sed -n 20,40p sqlglot/expressions/ddl.py", "description": "Locate postgres dialect class and parser hooks"}
[tool_result] __init__.py  3.6K
athena.py  4.3K
bigquery.py  7.1K
clickhouse.py  4.6K
databricks.py  1.1K
dialect.py  90.8K
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
oracle.py  3.3K
postgres.py  4.4K
presto.py  2.1K
prql.py  782B
redshift.py  1.8K
risingwave.py  618B
singlestore.py  2.1K
snowflake.py  6.5K
solr.py  535B
spark.py  897B
spark2.py  977B
sqlite.py  1.1K
starrocks.py  
…[2112 chars elided]…
rojections."""
        expression = self.expression
        return expression.selects if isinstance(expression, Query) else []

    @property
    def named_selects(self) -> list[str]:
        """
        If this statement contains a query (e.g. a CTAS), this returns the output
        names of the query's projections.
        """
        expression = self.expression
        return expression.named_selects if isinstance(expression, Query) else []


class Create(Expression, DDL):
    arg_types = {
[tool_use Bash] {"command": "sed -n 1,20p sqlglot/parsers/fabric.py; sed -n 1,30p sqlglot/parsers/postgres.py | grep -n import; grep -n \"class PostgresParser\\|PostgresParser\\|class Parser\" sqlglot/parsers/postgres.py sqlglot/dialects/postgres.py sqlglot/generators/postgres.py; sed -n 1,25p sqlglot/dialects/postgres.py; sed -n 60,80p sqlglot/dialects/postgres.py; sed -n 1,30p sqlglot/generators/postgres.py | head -40; sed -n 1,30p sqlglot/parsers/fabric.py | head -3", "description": "Read fabric parser example and postgres dialect wiring"}
[tool_result] from __future__ import annotations

from sqlglot import exp
from sqlglot.parsers.tsql import TSQLParser


class FabricParser(TSQLParser):
    def _parse_create(self) -> exp.Create | exp.Command:
        create = super()._parse_create()

        if isinstance(create, exp.Create):
            # Transform VARCHAR/CHAR without precision to VARCHAR(1)/CHAR(1)
            if create.kind == "TABLE" and isinstance(create.this, exp.Schema):
                for column in create.this.expressions:
         
…[2554 chars elided]…
,
    count_if_to_sum,
    datestrtodate_sql,
    filter_array_using_unnest,
    generate_series_sql,
    getbit_sql,
    groupconcat_sql,
    inline_array_sql,
    json_extract_segments,
    json_path_key_only_name,
    max_or_greatest,
    merge_without_target_sql,
    min_or_least,
    no_last_day_sql,
    no_map_from_entries_sql,
    no_paren_current_date_sql,
    no_pivot_sql,
    no_trycast_sql,
    regexp_replace_global_modifier,
from __future__ import annotations

from sqlglot import exp
[tool_use Bash] {"command": "grep -n \"    def wrap\\|    def schema_sql\\|    def _parse_schema\\|    def _parse_schema(\" -A8 sqlglot/generator.py sqlglot/parser.py | head -60; grep -n \"def test_\" tests/dialects/test_postgres.py | head -5; grep -n \"CREATE TYPE\\|CREATE.*TYPE\" tests/dialects/test_postgres.py | head", "description": "Check helper signatures for wrap, schema, and tests"}
[tool_result] sqlglot/generator.py:1024:    def wrap(self, expression: exp.Expr | str) -> str:
sqlglot/generator.py-1025-        this_sql = (
sqlglot/generator.py-1026-            self.sql(expression)
sqlglot/generator.py-1027-            if isinstance(expression, exp.UNWRAPPED_QUERIES)
sqlglot/generator.py-1028-            else self.sql(expression, "this")
sqlglot/generator.py-1029-        )
sqlglot/generator.py-1030-        if not this_sql:
sqlglot/generator.py-1031-            return "()"
sqlglot/generator
…[861 chars elided]…
t self._match(TokenType.L_PAREN):
sqlglot/parser.py-7046-            return this
sqlglot/parser.py-7047-
sqlglot/parser.py-7048-        # Disambiguate between schema and subquery/CTE, e.g. in INSERT INTO table (<expr>),
sqlglot/parser.py-7049-        # expr can be of both types
sqlglot/parser.py-7050-        if self._match_set(self.SELECT_START_TOKENS):
sqlglot/parser.py-7051-            self._retreat(index)
25 matches in 25 files:

10:0:
1087:0:
1403:0:
0 matches for 'CREATE TYPE\|CREATE.*TYPE'
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-185353-postgres-dialect-create-type-fal/base-1/sqlglot/expressions/ddl.py", "old_string": "class SequenceProperties(Expression):", "new_string": "class EnumType(Expression):\n    arg_types = {\"expressions\": True}\n\n\nclass SequenceProperties(Expression):"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-185353-postgres-dialect-create-type-fal/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-185353-postgres-dialect-create-type-fal/base-1/sqlglot/parsers/postgres.py", "offset": 80, "limit": 30}
[tool_result] 80	    )
81	
82	
83	class PostgresParser(parser.Parser):
84	    SUPPORTS_OMITTED_INTERVAL_SPAN_UNIT = True
85	
86	    PROPERTY_PARSERS = {
87	        **{k: v for k, v in parser.Parser.PROPERTY_PARSERS.items() if k != "INPUT"},
88	        "SET": lambda self: self.expression(exp.SetConfigProperty(this=self._parse_set())),
89	    }
90	
91	    PLACEHOLDER_PARSERS = {
92	        **parser.Parser.PLACEHOLDER_PARSERS,
93	        TokenType.PLACEHOLDER: lambda self: self.expression(exp.Placeholder(jdbc=Tr
…[264 chars elided]…
(args, 0)
101	        ),
102	        "BIT_AND": exp.BitwiseAndAgg.from_arg_list,
103	        "BIT_OR": exp.BitwiseOrAgg.from_arg_list,
104	        "BIT_XOR": exp.BitwiseXorAgg.from_arg_list,
105	        "VERSION": exp.CurrentVersion.from_arg_list,
106	        "DATE_TRUNC": build_timestamp_trunc,
107	        "DIV": lambda args: exp.cast(binary_from_function(exp.IntDiv)(args), exp.DType.DECIMAL),
108	        "GENERATE_SERIES": _build_generate_series,
109	        "GET_BIT": lambda args: exp.Getbit(
[tool_use Bash] {"command": "grep -n \"^    def \\|^    [A-Z_]* = \\|^    [A-Z_]*: \" sqlglot/parsers/postgres.py | tail -30; tail -5 sqlglot/parsers/postgres.py", "description": "List PostgresParser members and end of file"}
[tool_result] 24 matches in 10 files:

203:0:t.ClassVar = {TokenType.IN, TokenType.OUT, TokenType.INOUT, TokenType.VARIADIC}
205:0:
253:0:TokenType) -> exp.InOutColumnConstraint:
271:0:
290:0:
299:0:
309:0:
312:0:
335:0:exp.Identifier) -> exp.Expr | None:
sqlglot/parsers/postgres.py:84:SUPPORTS_OMITTED_INTERVAL_SPAN_UNIT = True
sqlglot/parsers/postgres.py:86:PROPERTY_PARSERS = {
sqlglot/parsers/postgres.py:91:PLACEHOLDER_PARSERS = {
sqlglot/parsers/postgres.py:97:FUNCTIONS = {
sqlglot/parsers/postgres.py:136:
…[251 chars elided]…
.py:168:RANGE_PARSERS = {
sqlglot/parsers/postgres.py:176:STATEMENT_PARSERS = {
sqlglot/parsers/postgres.py:181:UNARY_PARSERS = {
sqlglot/parsers/postgres.py:187:JSON_ARROWS_REQUIRE_JSON_TYPE = True
sqlglot/parsers/postgres.py:189:COLUMN_OPERATORS = {
sqlglot/parsers/postgres.py:321:def _parse_generated_as_identity(
            part = self._parse_id_var()
            if part:
                udt_type = exp.Dot(this=udt_type, expression=part)

        return exp.DataType.build(udt_type, udt=True)
[tool_use Bash] {"command": "sed -n 176,186p sqlglot/parsers/postgres.py; grep -n \"    def _parse_\" sqlglot/parsers/postgres.py", "description": "View statement parsers and method list in postgres parser"}
[tool_result]     STATEMENT_PARSERS = {
        **parser.Parser.STATEMENT_PARSERS,
        TokenType.END: lambda self: self._parse_commit_or_rollback(),
    }

    UNARY_PARSERS = {
        **parser.Parser.UNARY_PARSERS,
        # The `~` token is remapped from TILDE to RLIKE in Postgres due to the binary REGEXP LIKE operator
        TokenType.RLIKE: lambda self: self.expression(exp.BitwiseNot(this=self._parse_unary())),
    }

8 matches in 8 files:

205:0:
271:0:
290:0:
299:0:
309:0:
312:0:
335:0:exp.Identifier) -> exp.Expr | None:
sqlglot/parsers/postgres.py:321:def _parse_generated_as_identity(
[tool_use Bash] {"command": "sed -n 286,322p sqlglot/parsers/postgres.py", "description": "View end of PostgresParser class"}
[tool_result]             column_def.args["constraints"].insert(0, constraint)

        return column_def

    def _parse_query_parameter(self) -> exp.Expr | None:
        this = (
            self._parse_wrapped(self._parse_id_var)
            if self._match(TokenType.L_PAREN, advance=False)
            else None
        )
        self._match_text_seq("S")
        return self.expression(exp.Placeholder(this=this))

    def _parse_date_part(self) -> exp.Expr:
        part = self._parse_type()
        self._ma
…[166 chars elided]…
      return self.expression(exp.Extract(this=part, expression=value))

    def _parse_unique_key(self) -> exp.Expr | None:
        return None

    def _parse_jsonb_exists(self) -> exp.JSONBExists:
        return self.expression(
            exp.JSONBExists(
                this=self._parse_bitwise(),
                path=self._match(TokenType.COMMA)
                and self.dialect.to_json_path(self._parse_bitwise()),
            )
        )

    def _parse_generated_as_identity(
        self,
[assistant] Now I'll add the parser override after `_parse_query_parameter`, and the Postgres generator method.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-185353-postgres-dialect-create-type-fal/base-1/sqlglot/parsers/postgres.py", "old_string": "    def _parse_date_part(self) -> exp.Expr:\n        part = self._parse_type()", "new_string": "    def _parse_create(self) -> exp.Create | exp.Command:\n        index = self._index\n        if self._match_tex
…[345 chars elided]…
tch_text_seq(\"AS\") and self._parse_schema()\n\n            if this and expression and not self._curr:\n                return self.expression(\n                    exp.Create(this=this, kind=\"TYPE\", expression=expression)\n                )\n\n        self._retreat(index)\n        return super()._parse_create()\n\n    def _parse_date_part(self) -> exp.Expr:\n        part = self._parse_type()"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-185353-postgres-dialect-create-type-fal/base-1/sqlglot/parsers/postgres.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-185353-postgres-dialect-create-type-fal/base-1/sqlglot/generators/postgres.py", "old_string": "def datatype_sql(self, expression: exp.DataType) -> str:", "new_string": "def enumtype_sql(self, expression: exp.EnumType) -> str:\n    return f\"ENUM {self.wrap(self.expressions(expression, flat=True))}\"\n\n\ndef datatype_sql(self, expression: exp.DataType) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-185353-postgres-dialect-create-type-fal/base-1/sqlglot/generators/postgres.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"^class \\|^    def \\|^    [A-Z_]* = \\|^def \" sqlglot/generators/postgres.py | head -80; grep -n \"datatype_sql\" sqlglot/generators/postgres.py", "description": "Inspect generator structure for postgres"}
[tool_result] 63 matches in 33 files:

106:0:PostgresGenerator, expression: exp.Substring) -> str:
117:0:exp.Expr) -> exp.Expr:
134:0:exp.Expr) -> exp.Expr:
167:0:PostgresGenerator, expression: JSON_EXTRACT_TYPE) -> str:
175:0:PostgresGenerator, expression: exp.UnixToTime) -> str:
189:0:PostgresGenerator, expression: exp.Levenshtein) -> str:
195:0:PostgresGenerator, expression: exp.AnyValue) -> str:
204:0:PostgresGenerator, expression: exp.Round) -> str:
225:0:
264:0:exp.Lateral) -> str:
401:0:exp.SchemaComme
…[2093 chars elided]…
ostgres.py:248:MULTI_ARG_DISTINCT = False
sqlglot/generators/postgres.py:249:CAN_IMPLEMENT_ARRAY_ANY = True
sqlglot/generators/postgres.py:250:SUPPORTS_WINDOW_EXCLUDE = True
sqlglot/generators/postgres.py:251:COPY_HAS_INTO_KEYWORD = False
sqlglot/generators/postgres.py:252:ARRAY_CONCAT_IS_VAR_LEN = False
sqlglot/generators/postgres.py:253:SUPPORTS_MEDIAN = False
[+6 more]
2 matches in 2 files:

481:0:exp.DataType) -> str:
sqlglot/generators/postgres.py:492:return super().datatype_sql(expression)
[tool_use Bash] {"command": "sed -n 474,495p sqlglot/generators/postgres.py; grep -n \"class PostgresGenerator\" -A3 sqlglot/generators/postgres.py; grep -n \"exp.Lateral\\|exp.Unnest:\\|TRANSFORMS = \" sqlglot/generators/postgres.py | head", "description": "View generator region and class wiring"}
[tool_result]         return f"SET {exprs}{access_method}{tablespace}{option}"

    def enumtype_sql(self, expression: exp.EnumType) -> str:
    return f"ENUM {self.wrap(self.expressions(expression, flat=True))}"


def datatype_sql(self, expression: exp.DataType) -> str:
        if expression.is_type(exp.DType.ARRAY):
            if expression.expressions:
                values = self.expressions(expression, key="values", flat=True)
                return f"{self.expressions(expression, flat=True)}[{values}]
…[313 chars elided]…
ql(expression)

    def cast_sql(self, expression: exp.Cast, safe_prefix: str | None = None) -> str:
        this = expression.this
225:class PostgresGenerator(generator.Generator):
226-    SELECT_KINDS: tuple[str, ...] = ()
227-    TRY_SUPPORTED = False
228-    SUPPORTS_UESCAPE = False
3 matches in 2 files:

264:0:exp.Lateral) -> str:
sqlglot/generators/postgres.py:231:AFTER_HAVING_MODIFIER_TRANSFORMS = generator.AFTER_HAVING_MODIFIER_TRANSFORMS
sqlglot/generators/postgres.py:285:TRANSFORMS = {
[assistant] My edit mangled indentation: the old string matched after the leading spaces, so the new function's second line lost its indent. Fixing that now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-185353-postgres-dialect-create-type-fal/base-1/sqlglot/generators/postgres.py", "old_string": "    def enumtype_sql(self, expression: exp.EnumType) -> str:\n    return f\"ENUM {self.wrap(self.expressions(expression, flat=True))}\"\n\n\ndef datatype_sql(self, expression: exp.DataType) -> str:\n        if expression.is_type(exp.DType.ARRAY):", "new_string": "    def enumtype_sql(self, expression: exp.EnumType) -> str:\n        return f\"ENUM {self.wrap(self.expressions(expression, flat=True))}\"\n\n    def datatype_sql(self, expression: exp.DataType) -> str:\n        if expression.is_type(exp.DType.ARRAY):"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-185353-postgres-dialect-create-type-fal/base-1/sqlglot/generators/postgres.py has been updated successfully.
[assistant] Now a quick check of the round-trips and the AST shape, using the project's Python.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nfrom sqlglot import parse_one, exp\nfor s in [\\\"CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')\\\", 'CREATE TYPE complex AS (r DOUBLE PRECISION, i TEXT)', 'CREATE TYPE shell', 'CREATE TYPE x AS RANGE (subtype = float8)', 'CREATE TABLE type (a INT)']:\n    e = parse_one(s, 'postgres')\n    print(type(e).__name__, '|', e.sql('postgres'))\ne = parse_one(\\\"CREATE TYPE book_type AS ENUM ('a')\\\", 'postgres'); print(repr(e.expression)[:200])\n\"", "description": "Smoke-test CREATE TYPE parsing and round-trip"}
[tool_result] 'CREATE TYPE shell' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE TYPE x AS RANGE (subtype = float8)' contains unsupported syntax. Falling back to parsing as a 'Command'.
Create | CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')
Create | CREATE TYPE complex AS (r DOUBLE PRECISION, i TEXT)
Command | CREATE TYPE shell
Command | CREATE TYPE x AS RANGE (subtype = float8)
Create | CREATE TABLE type (a INT)
EnumType(
  expressions=[
    Literal(this='a', is_string=True)])
[assistant] Round-trips work and the fallback is unchanged for `CREATE TYPE shell` and `RANGE`. Next, tests in the Postgres test file.
[tool_use Bash] {"command": "grep -n \"    def test_\" tests/dialects/test_postgres.py | tail -3; tail -5 tests/dialects/test_postgres.py", "description": "Find insertion point in postgres tests"}
[tool_result] 1788:0:
1811:0:
1833:0:
            "CREATE TRIGGER proc_trigger BEFORE INSERT ON users FOR EACH ROW EXECUTE FUNCTION LOG_CHANGES()",
        )
        self.validate_identity(
            'CREATE TRIGGER "MyTrigger" BEFORE INSERT ON "MyTable" FOR EACH ROW EXECUTE FUNCTION MYFUNCTION()'
        )
[tool_use Bash] {"command": "cat >> tests/dialects/test_postgres.py <<'EOF'\n\n    def test_create_type(self):\n        self.validate_identity(\"CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')\")\n        self.validate_identity(\"CREATE TYPE complex AS (r DOUBLE PRECISION, i TEXT)\")\n        self.validate_identity(\"CREATE TYPE myschema.book_type AS ENUM ('FICTION')\")\n        self.assertIsInstance(\n            parse_one(\"CREATE TYPE book_type AS ENUM ('FICTION')\", read=\"postgres\").expression,\n            exp.EnumType,\n        )\nEOF\ngrep -n \"^from\\|^import\" tests/dialects/test_postgres.py | head", "description": "Append CREATE TYPE test to postgres tests"}
[tool_result] 1:from sqlglot import ParseError, UnsupportedError, exp, transpile
2:from sqlglot.helper import logger as helper_logger
3:from tests.dialects.test_dialect import Validator
[tool_use Bash] {"command": "sed -i '1s/.*/from sqlglot import ParseError, UnsupportedError, exp, parse_one, transpile/' tests/dialects/test_postgres.py && PY=<work>/env-sqlglot/bin/python && $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -15", "description": "Run postgres dialect tests"}
[tool_result ERROR] Exit code 1
sed: 2: "tests/dialects/test_pos ...": undefined label 'ests/dialects/test_postgres.py'
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-185353-postgres-dialect-create-type-fal/base-1/tests/dialects/test_postgres.py", "old_string": "from sqlglot import ParseError, UnsupportedError, exp, transpile", "new_string": "from sqlglot import ParseError, UnsupportedError, exp, parse_one, transpile"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-185353-postgres-dialect-create-type-fal/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -15", "description": "Run postgres dialect tests"}
[tool_result] ..........................                             [100%]
26 passed, 378 subtests passed in 0.25s
[assistant] Postgres tests pass. Now the full suite, which is the project's check command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite", "timeout": 600000}
[tool_result] ............................................................................................ [ 30%]
.......................... [ 32%]
.......................................... [ 36%]
..................................................................................................................................................................................................... [ 53%]
....................... [ 56%]
................................................................................
…[86 chars elided]…
........................................... [ 73%]
............................................................................................................. [ 83%]
............................................ [ 87%]
........................... [ 89%]
............................... [ 92%]
............................................................. [ 98%]
.....................                                                                 [100%]
1106 passed, 17982 subtests passed in 46.83s
[assistant] The full suite passes (1106 tests). I'll run the linter and formatter on the touched files too.
[tool_use Bash] {"command": "F=\"sqlglot/parsers/postgres.py sqlglot/generators/postgres.py sqlglot/expressions/ddl.py tests/dialects/test_postgres.py\"; (ruff --version && ruff check $F && ruff format --check $F) 2>&1 | tail -8; git status --short", "description": "Lint and format-check changed files"}
[tool_result] Ruff: 1 issues in 1 files
═══════════════════════════════════════
Top rules:
  E902 (1x)

Top files:
  test_postgres.py (1 issues)
    E902 (1)
 M sqlglot/expressions/ddl.py
 M sqlglot/generators/postgres.py
 M sqlglot/parsers/postgres.py
 M tests/dialects/test_postgres.py
[tool_use Bash] {"command": "ruff check tests/dialects/test_postgres.py 2>&1 | head -8; git stash list | head -2 >/dev/null; git show HEAD:tests/dialects/test_postgres.py > /tmp/orig_tp.py && ruff check /tmp/orig_tp.py 2>&1 | head -3; ruff format --check sqlglot/parsers/postgres.py sqlglot/generators/postgres.py sqlglot/expressions/ddl.py tests/dialects/test_postgres.py 2>&1 | tail -3", "description": "Investigate E902 lint result and formatting"}
[tool_result] Ruff: No issues found
Ruff: No issues found
1. postgres.py

[hint] Run `ruff format` to format these files
[assistant] The E902 was spurious; ruff now reports no issues. The formatter wants a change in `parsers/postgres.py`, so I'll apply it and confirm it touches only my lines.
[tool_use Bash] {"command": "ruff format sqlglot/parsers/postgres.py && git diff --stat && git diff sqlglot/parsers/postgres.py && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -1", "description": "Apply ruff format and show parser diff"}
[tool_result] 1 file reformatted
sqlglot/expressions/ddl.py      |  4 ++++
 sqlglot/generators/postgres.py  |  3 +++
 sqlglot/parsers/postgres.py     | 17 +++++++++++++++++
 tests/dialects/test_postgres.py | 11 ++++++++++-
 4 files changed, 34 insertions(+), 1 deletion(-)
sqlglot/parsers/postgres.py | 17 +++++++++++++++++
 1 file changed, 17 insertions(+)

--- Changes ---

sqlglot/parsers/postgres.py
  @@ -296,6 +296,23 @@ class PostgresParser(parser.Parser):
  +    def _parse_create(self) -> exp.Create | exp
…[494 chars elided]…
and expression and not self._curr:
  +                return self.expression(exp.Create(this=this, kind="TYPE", expression=expression))
  +
  +        self._retreat(index)
  +        return super()._parse_create()
  +
       def _parse_date_part(self) -> exp.Expr:
           part = self._parse_type()
           self._match(TokenType.COMMA)
  +17 -0
26 passed, 378 subtests passed in 0.15s
[This command modified 1 file you've previously read: sqlglot/parsers/postgres.py. Call Read before editing.]
[assistant] `CREATE TYPE` now parses into AST nodes for enum and composite types, and both round-trip in Postgres. The full test suite passed (1106 tests) before the final formatter pass. That pass only rewrapped one line, and the Postgres tests still pass after it.

```python
parse_one("CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')", "postgres").sql("postgres")
# "CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')"
parse_one("CREATE TYPE complex AS (r DOUBLE PRECISION, i TEXT)", "postgres").sql("postgres")
# "CREATE TYPE complex AS (r DOUBLE PRECISION, i TEXT)"
```

Changes:
- **`sqlglot/e
…[379 chars elided]…
erators/postgres.py`**: `enumtype_sql` renders `ENUM ('a', 'b')`. Composite types reuse the existing `Schema` generation.
- **`tests/dialects/test_postgres.py`**: `test_create_type` covers enum and composite round-trips, a schema-qualified name, and checks that the enum parses to `exp.EnumType`.

Choices I made that you may want to review:
- Composite types are stored as the `Schema` of column definitions, not a new node.
- Only enum and composite are handled. `CREATE TYPE x` (shell) and `AS RANGE` still fall back to `Command`, as the task scoped.
- The changes are uncommitted in the worktree.
