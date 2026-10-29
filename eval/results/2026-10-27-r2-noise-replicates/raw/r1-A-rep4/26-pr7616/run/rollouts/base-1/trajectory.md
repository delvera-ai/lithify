# trajectory base-1

final message:
`CREATE TYPE` now parses into a real `Create` node for both enum and composite types, and round-trips in Postgres. The issue's example prints `CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')` with no fallback warning. The full suite passes (1106 passed) and ruff is clean. I did not commit.

**What changed**

- **`sqlglot/parsers/postgres.py`**: a `_parse_create` override handles `CREATE TYPE`. Enum bodies become the existing `DataType(ENUM, ...)` node, and composite bodies become the existing `Schema` of column definitions. Anything else (`CREATE TYPE shell`, `AS RANGE (...)`, trailing garbage) still falls back to `Command`, and non-`TYPE` creates go through the unchanged base parser.
- **`sqlglot/generators/postgres.py`**: enum values render as `ENUM (...)` with a space, which is the Postgres form and matches the issue's example. Composite output needed no change.
- **`tests/dialects/test_postgres.py`**: added `test_create_type` covering enum, schema-qualified enum, composite, and the fallback cases. No existing test was edited.

**Decisions to review**

- The enum spacing change applies to every Postgres-targeted `ENUM` datatype, not just `CREATE TYPE`. No existing test depended on the old form, but it is a visible change to `ENUM` output when generating Postgres.
- I did not add `CREATE DOMAIN`, `RANGE`, or shell types. The issue asked for enum and composite only.

## events
[assistant] I'll start by finding how the parser handles `CREATE` today and where the Postgres dialect hooks in.
[tool_use Bash] {"command": "git status --short | head && grep -n \"TYPE\\b\" sqlglot/dialects/postgres.py | head -40 && grep -n \"def _parse_create\\|CREATABLES\\|\\\"TYPE\\\"\\|TYPE:\" sqlglot/parser.py | head -30 && grep -n \"class Create\\b\\|class Create(\" -A 40 sqlglot/expressions.py | head -60 && grep -n \"TYPE\\b\" sqlglot/tokens.py | head", "description": "Inspect git state and locate CREATE TYPE handling"}
[tool_result] 84:            "CSTRING": TokenType.PSEUDO_TYPE,
111:            "REGTYPE": TokenType.OBJECT_IDENTIFIER,
619:    DB_CREATABLES: t.ClassVar = {
639:    CREATABLES: t.ClassVar = {
647:        *DB_CREATABLES,
765:        *CREATABLES,
1629:        "TYPE": ("EVOLUTION",),
1782:    JSON_ARROWS_REQUIRE_JSON_TYPE: t.ClassVar = False
2183:        kind = self._match_set(self.CREATABLES) and self._prev
2297:        kind = self._match_set(self.CREATABLES) and self._prev.text.upper()
2344:    def _parse_crea
…[151 chars elided]…
_match_set(self.CREATABLES) and self._prev
2488:        elif create_token_type in self.DB_CREATABLES:
3280:    def _parse_create_like(self) -> exp.LikeProperty | None:
3337:        kind = self._prev.text if self._match_set(self.CREATABLES) else None
6151:        if type_token == TokenType.PSEUDO_TYPE:
8627:        self._match_text_seq("TYPE")
9525:        kind = self._prev.text.upper() if self._match_set(self.CREATABLES) else None
ugrep: warning: sqlglot/expressions.py: No such file or directory
[assistant] Those Docs tools aren't relevant to this task, so I'll stick to the code. The `expressions.py` lookup failed, so I'll check the package layout and read `_parse_create`.
[tool_use Bash] {"command": "ls sqlglot | head -80 && sed -n 2344,2520p sqlglot/parser.py", "description": "Read the parser's CREATE statement handling"}
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
    def _parse_create(self) -> exp.Create | exp.Command:
        # Note: this can't be None because we've matched a statement parser
        start = self._prev

        replace = (
            start.token_type == Tok
…[6779 chars elided]…
quence_props = exp.SequenceProperties()
                    options = []
                    for prop in props:
                        if isinstance(prop, exp.SequenceProperties):
                            for arg, value in prop.args.items():
                                if arg == "options":
                                    options.extend(value)
                                else:
                                    sequence_props.set(arg, value)
                            prop.pop()
[tool_use Bash] {"command": "sed -n 2520,2620p sqlglot/parser.py && sed -n 635,660p sqlglot/parser.py && grep -rn \"TYPE\" sqlglot/parsers/*.py | grep -i \"create\\|CREATABLE\" | head; ls sqlglot/parsers sqlglot/generators sqlglot/expressions; grep -rn \"TokenType.ENUM\\|ENUM\\b\" sqlglot/dialects/postgres.py | head", "description": "Read remaining CREATE parsing and find enum references"}
[tool_result]                             prop.pop()

                    if options:
                        sequence_props.set("options", options)

                    props.append("expressions", sequence_props)
                    extend_props(props)
            else:
                expression = self._parse_ddl_select()

                # Some dialects also support using a table as an alias instead of a SELECT.
                # Here we fallback to this as an alternative.
                if not expression
…[4703 chars elided]…
.py
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
[assistant] The repo has been split into `parsers/` and `generators/` packages, and `TYPE` isn't in `CREATABLES`. Next I'll check the Postgres parser/generator, the existing ENUM datatype support, and the `create_sql` generator.
[tool_use Bash] {"command": "grep -n \"ENUM\" sqlglot/expressions/datatypes.py sqlglot/parsers/base.py sqlglot/generators/base.py sqlglot/parsers/postgres.py sqlglot/generators/postgres.py sqlglot/dialects/postgres.py | head -40; echo ---; grep -n \"def create_sql\" -A 60 sqlglot/generators/base.py | head -120; echo ---; grep -n \"class Create(\" -A 25 sqlglot/expressions/ddl.py", "description": "Find ENUM support and Create generation code"}
[tool_result] ugrep: warning: sqlglot/generators/base.py: No such file or directory
sqlglot/expressions/datatypes.py:62:    ENUM = auto()
sqlglot/expressions/datatypes.py:63:    ENUM8 = auto()
sqlglot/expressions/datatypes.py:64:    ENUM16 = auto()
---
ugrep: warning: sqlglot/generators/base.py: No such file or directory
---
39:class Create(Expression, DDL):
40-    arg_types = {
41-        "with_": False,
42-        "this": True,
43-        "kind": True,
44-        "expression": False,
45-        "exists": Fa
…[5 chars elided]…
46-        "properties": False,
47-        "replace": False,
48-        "refresh": False,
49-        "unique": False,
50-        "indexes": False,
51-        "no_schema_binding": False,
52-        "begin": False,
53-        "clone": False,
54-        "concurrently": False,
55-        "clustered": False,
56-    }
57-
58-    @property
59-    def kind(self) -> str | None:
60-        kind = self.args.get("kind")
61-        return kind and kind.upper()
62-
63-
64-class SequenceProperties(Expression):
[tool_use Bash] {"command": "ls sqlglot/generator.py && grep -n \"def create_sql\" -A 80 sqlglot/generator.py | head -130; echo ---; grep -n \"ENUM\" sqlglot/generator.py sqlglot/parser.py sqlglot/dialects/postgres.py sqlglot/tokens.py sqlglot/tokenizer_core.py | head -30; echo ---; cat sqlglot/parsers/postgres.py | head -80; echo; wc -l sqlglot/parsers/postgres.py sqlglot/generators/postgres.py sqlglot/dialects/postgres.py", "description": "Locate create_sql generator and ENUM references"}
[tool_result] sqlglot/generator.py
1284:    def create_sql(self, expression: exp.Create) -> str:
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
129
…[6665 chars elided]…
ual(source, target, ins_cost, del_cost, sub_cost, max_d)
    # levenshtein_less_equal(source, target, max_d)
    max_dist = args.pop()

    return exp.Levenshtein(
        this=seq_get(args, 0),
        expression=seq_get(args, 1),
        ins_cost=seq_get(args, 2),
        del_cost=seq_get(args, 3),
        sub_cost=seq_get(args, 4),
        max_dist=max_dist,
    )

     343 sqlglot/parsers/postgres.py
     569 sqlglot/generators/postgres.py
     129 sqlglot/dialects/postgres.py
    1041 total
[assistant] Next I'll check the existing ENUM type parsing, whether any test pins `CREATE TYPE` as a Command, and the Postgres generator's create handling.
[tool_use Bash] {"command": "grep -rn \"CREATE TYPE\\|create type\" tests/ sqlglot/ | head -20; echo ---; sed -n 6190,6215p sqlglot/parser.py; echo ---; grep -n \"STATEMENT_PARSERS\\|TokenType.TYPE\\|def _parse_create\\|create_sql\\|CREATABLE_KIND\" sqlglot/parsers/postgres.py sqlglot/generators/postgres.py sqlglot/dialects/postgres.py sqlglot/parser.py sqlglot/dialects/dialect.py | head -30; echo ---; grep -n \"\\\"TYPE\\\"\\|TYPE = \\|TokenType.TYPE\\b\" sqlglot/tokens.py sqlglot/tokenizer_core.py sqlglot/parser.py | head", "description": "Check existing CREATE TYPE tests and ENUM/TYPE token handling"}
[tool_result] ---
                    lambda: self._parse_types(
                        check_func=check_func, schema=schema, allow_identifiers=allow_identifiers
                    )
                )
                if type_token == TokenType.NULLABLE and len(expressions) == 1:
                    this = expressions[0]
                    this.set("nullable", True)
                    self._match_r_paren()
                    return this
            elif type_token in self.ENUM_TYPE_TOKENS:
               
…[1814 chars elided]…
t.CREATABLE_KIND_MAPPING.get(create_kind_text) or create_kind_text,
sqlglot/parser.py:3280:    def _parse_create_like(self) -> exp.LikeProperty | None:
sqlglot/parser.py:3347:        if self._match_set(self.STATEMENT_PARSERS, advance=False):
---
sqlglot/tokenizer_core.py:383:    PSEUDO_TYPE = auto()
sqlglot/parser.py:39:OPTIONS_TYPE = dict[str, Sequence[t.Union[Sequence[str], str]]]
sqlglot/parser.py:1629:        "TYPE": ("EVOLUTION",),
sqlglot/parser.py:8627:        self._match_text_seq("TYPE")
[assistant] No existing test pins `CREATE TYPE` as a Command, and there's no `TokenType.TYPE`, so `TYPE` is lexed as a plain VAR. Before choosing an AST shape I want to see how `ENUM` datatypes and `_parse_schema` render and parse today, and whether any dialect already overrides `_parse_create`.
[tool_use Bash] {"command": "grep -rn \"def _parse_create\\b\\|def _parse_create(\" sqlglot/ ; echo ---; grep -n \"def _parse_schema\" -A 22 sqlglot/parser.py; echo ---; grep -n \"def _match_text_seq\" -A 3 sqlglot/parser.py; echo ---; grep -n \"ENUM\" sqlglot/generator.py sqlglot/generators/postgres.py sqlglot/expressions/datatypes.py | head; grep -n \"def datatype_sql\" -A 30 sqlglot/generator.py | head -50; echo ---; sed -n 170,200p sqlglot/parsers/postgres.py; echo ---; grep -rn \"ENUM\" tests/dialects/test_postgres.py | head", "description": "Read schema parser, datatype generation, and Postgres statement parsers"}
[tool_result] sqlglot/parser.py:2344:    def _parse_create(self) -> exp.Create | exp.Command:
sqlglot/parsers/fabric.py:8:    def _parse_create(self) -> exp.Create | exp.Command:
sqlglot/parsers/snowflake.py:1004:    def _parse_create(self) -> exp.Create | exp.Command:
sqlglot/parsers/tsql.py:664:    def _parse_create(self) -> exp.Create | exp.Command:
sqlglot/parsers/starrocks.py:61:    def _parse_create(self) -> exp.Create | exp.Command:
---
7043:    def _parse_schema(self, this: exp.Expr | None = None) -> 
…[3442 chars elided]…
PERATORS,
        TokenType.ARROW: lambda self, this, path: self.validate_expression(
            build_json_extract_path(
                exp.JSONExtract, arrow_req_json_type=self.JSON_ARROWS_REQUIRE_JSON_TYPE
            )([this, path])
        ),
        TokenType.DARROW: lambda self, this, path: self.validate_expression(
            build_json_extract_path(
                exp.JSONExtractScalar, arrow_req_json_type=self.JSON_ARROWS_REQUIRE_JSON_TYPE
            )([this, path])
        ),
---
[assistant] Snowflake, Fabric, StarRocks, and T-SQL already override `_parse_create`, so I'll follow their pattern. Next I'll read those overrides and how the generic `create_sql` renders the body.
[tool_use Bash] {"command": "sed -n 1,25p sqlglot/parsers/fabric.py; echo ---; sed -n 1000,1020p sqlglot/parsers/snowflake.py; echo ---; sed -n 1,20p sqlglot/parsers/postgres.py >/dev/null; sed -n 1,30p sqlglot/parsers/postgres.py | grep -n import; echo ---; grep -n \"^from\\|^import\" sqlglot/parsers/fabric.py; echo ---; sed -n 1364,1420p sqlglot/generator.py", "description": "Read existing _parse_create overrides and rest of create_sql"}
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
         
…[4161 chars elided]…
     minvalue = self.sql(expression, "minvalue")
        minvalue = f" MINVALUE {minvalue}" if minvalue else ""
        maxvalue = self.sql(expression, "maxvalue")
        maxvalue = f" MAXVALUE {maxvalue}" if maxvalue else ""
        owned = self.sql(expression, "owned")
        owned = f" OWNED BY {owned}" if owned else ""

        cache = expression.args.get("cache")
        if cache is None:
            cache_str = ""
        elif cache is True:
            cache_str = " CACHE"
        else:
[assistant] The generic `create_sql` already emits `CREATE <kind> <name> AS <body>`, so the parser can build a `Create` node and let the body render through existing expression classes. Before deciding the body shape I'll record a baseline and check how an `ENUM` DataType and a `Schema` currently render in Postgres.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -3; $PY -c \"\nfrom sqlglot import exp, parse_one\nfrom sqlglot.dialects.postgres import Postgres\ne = exp.DataType.build('ENUM')\ne = exp.DataType(this=exp.DType.ENUM, expressions=[exp.Literal.string('FICTION'), exp.
…[97 chars elided]…
ions=[exp.ColumnDef(this=exp.to_identifier('a'), kind=exp.DataType.build('INT'))])\nprint(repr(s.sql('postgres')))\nprint(parse_one('CREATE TYPE book_type AS ENUM (\\'FICTION\\', \\'NONFICTION\\')', read='postgres').sql('postgres'))\n\"; grep -n \"def create_sql\\|def datatype_sql\\|ENUM\" sqlglot/generators/postgres.py | head", "description": "Run baseline Postgres tests and probe AST rendering"}
[tool_result] .........................                              [100%]
25 passed, 378 subtests passed in 0.36s
'CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')' contains unsupported syntax. Falling back to parsing as a 'Command'.
"ENUM('FICTION', 'NONFICTION')"
'(a INT)'
CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')
477:    def datatype_sql(self, expression: exp.DataType) -> str:
[assistant] Baseline is green (25 passed). A bare `ENUM` DataType renders as `ENUM('a', 'b')` with no space, which would break an exact round-trip of the issue's example. I'll check the Postgres `datatype_sql` override and the surrounding generator to decide where the spacing belongs.
[tool_use Bash] {"command": "sed -n 470,500p sqlglot/generators/postgres.py; grep -n \"def .*_sql\" sqlglot/generators/postgres.py | head -80; grep -n \"TRANSFORMS = {\" -A 3 sqlglot/generators/postgres.py | head; sed -n 1713,1760p sqlglot/generator.py", "description": "Inspect Postgres generator datatype handling and generic datatype rendering"}
[tool_result]         access_method = f"ACCESS METHOD {access_method}" if access_method else ""
        tablespace = self.sql(expression, "tablespace")
        tablespace = f"TABLESPACE {tablespace}" if tablespace else ""
        option = self.sql(expression, "option")

        return f"SET {exprs}{access_method}{tablespace}{option}"

    def datatype_sql(self, expression: exp.DataType) -> str:
        if expression.is_type(exp.DType.ARRAY):
            if expression.expressions:
                values = self
…[4732 chars elided]…
"hint")
        this = self.sql(expression, "this")
        this = f" FROM {this}" if this else ""
        using = self.expressions(expression, key="using")
        using = f" USING {using}" if using else ""
        cluster = self.sql(expression, "cluster")
        cluster = f" {cluster}" if cluster else ""
        where = self.sql(expression, "where")
        returning = self.sql(expression, "returning")
        order = self.sql(expression, "order")
        limit = self.sql(expression, "limit")
[assistant] The generic `Create` path already renders `AS (a INT)` for a `Schema` body, so composite types need no generator changes. Enum bodies are the open question: a bare `ENUM` DataType prints without the space the issue uses. I'll check whether any test depends on that `ENUM(` rendering and look at the Postgres parser's method layout before editing.
[tool_use Bash] {"command": "grep -rn \"ENUM\" tests/ | grep -v \"ENUM8\\|ENUM16\" | head -20; echo ---; grep -n \"^class \\|    def \" sqlglot/parsers/postgres.py | head -60; echo ---; grep -n \"def _parse_as_command\" -A 12 sqlglot/parser.py | head -20", "description": "Check ENUM test coverage and Postgres parser structure"}
[tool_result] tests/dialects/test_singlestore.py:764:            "CREATE TABLE testTypes (a ENUM('a'))",
tests/dialects/test_singlestore.py:766:                "singlestore": "CREATE TABLE testTypes (a ENUM('a'))",
tests/dialects/test_singlestore.py:771:            "CREATE TABLE testTypes (a ENUM('a'))",
tests/dialects/test_singlestore.py:773:                "singlestore": "CREATE TABLE testTypes (a ENUM('a'))",
tests/dialects/test_duckdb.py:501:        self.validate_identity("CREATE TABLE color (name ENUM('R
…[761 chars elided]…
_as_command(self, start: Token) -> exp.Command:
9115-        while self._curr:
9116-            self._advance()
9117-        text = self._find_sql(start, self._prev)
9118-        size = len(start.text)
9119-        self._warn_unsupported()
9120-        return exp.Command(this=text[:size], expression=text[size:])
9121-
9122-    def _parse_dict_property(self, this: str) -> exp.DictProperty:
9123-        settings = []
9124-
9125-        self._match_l_paren()
9126-        kind = self._parse_id_var()
[assistant] No Postgres test depends on the `ENUM(` form, so a Postgres-only spacing change is low risk. I'll read the end of the Postgres parser class to place the override.
[tool_use Bash] {"command": "sed -n 333,343p sqlglot/parsers/postgres.py", "description": "Read end of Postgres parser class"}
[tool_result]         return this

    def _parse_user_defined_type(self, identifier: exp.Identifier) -> exp.Expr | None:
        udt_type: exp.Identifier | exp.Dot = identifier

        while self._match(TokenType.DOT):
            part = self._parse_id_var()
            if part:
                udt_type = exp.Dot(this=udt_type, expression=part)

        return exp.DataType.build(udt_type, udt=True)
[assistant] I have what I need. The plan:

- **Parser (`sqlglot/parsers/postgres.py`):** override `_parse_create` so `CREATE TYPE` is matched before the generic path. Enum bodies become an existing `DataType(ENUM, ...)`, and composite bodies become an existing `Schema` of column defs. Anything else falls back to `Command`, as before.
- **Generator (`sqlglot/generators/postgres.py`):** the generic `create_sql` already emits `CREATE TYPE name AS <body>`, so the only change is spacing enum values as `ENUM (...)`, the Postgres form.

I'll add the parser override first.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-180317-postgres-dialect-create-type-fal/base-1/sqlglot/parsers/postgres.py", "old_string": "        return exp.DataType.build(udt_type, udt=True)", "new_string": "        return exp.DataType.build(udt_type, udt=True)\n\n    def _parse_create(self) -> exp.Create | exp.Command:\n        start = self._p
…[366 chars elided]…
            expression = exp.DataType(\n                this=exp.DType.ENUM, expressions=self._parse_wrapped_csv(self._parse_string)\n            )\n        else:\n            expression = self._parse_schema()\n\n        if not expression or self._curr:\n            return self._parse_as_command(start)\n\n        return self.expression(exp.Create(this=this, kind=\"TYPE\", expression=expression))"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-180317-postgres-dialect-create-type-fal/base-1/sqlglot/parsers/postgres.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-180317-postgres-dialect-create-type-fal/base-1/sqlglot/generators/postgres.py", "offset": 477, "limit": 14}
[tool_result] 477	    def datatype_sql(self, expression: exp.DataType) -> str:
478	        if expression.is_type(exp.DType.ARRAY):
479	            if expression.expressions:
480	                values = self.expressions(expression, key="values", flat=True)
481	                return f"{self.expressions(expression, flat=True)}[{values}]"
482	            return "ARRAY"
483	
484	        if expression.is_type(exp.DType.DOUBLE, exp.DType.FLOAT) and expression.expressions:
485	            # Postgres doesn't support precision for REAL and DOUBLE PRECISION types
486	            return f"FLOAT({self.expressions(expression, flat=True)})"
487	
488	        return super().datatype_sql(expression)
489	
490	    def cast_sql(self, expression: exp.Cast, safe_prefix: str | None = None) -> str:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-180317-postgres-dialect-create-type-fal/base-1/sqlglot/generators/postgres.py", "old_string": "            return f\"FLOAT({self.expressions(expression, flat=True)})\"\n\n        return super().datatype_sql(expression)", "new_string": "            return f\"FLOAT({self.expressions(expression, flat=True)})\"\n\n        if expression.is_type(exp.DType.ENUM) and expression.expressions:\n            return f\"ENUM ({self.expressions(expression, flat=True)})\"\n\n        return super().datatype_sql(expression)"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-180317-postgres-dialect-create-type-fal/base-1/sqlglot/generators/postgres.py has been updated successfully.
[assistant] Now I'll exercise the new paths directly: the enum and composite examples, a schema-qualified name, and fallbacks for a shell type and a `RANGE` type.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nfrom sqlglot import parse_one, exp\ncases = [\n \\\"CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')\\\",\n 'CREATE TYPE s.mood AS ENUM (\\'sad\\')',\n 'CREATE TYPE complex AS (r DOUBLE PRECISION, i DOUBLE PRECISION)',\n 'CREATE TYPE pair AS (a INT, b TEXT COLLATE \\\"C\\\")',\n 'CREATE TYP
…[77 chars elided]…
ENUM (\\'a\\') garbage',\n]\nfor c in cases:\n    e = parse_one(c, read='postgres')\n    print(type(e).__name__, '|', e.sql('postgres'))\ne = parse_one(cases[0], read='postgres'); print(repr(e.args['expression']), e.kind)\n\" 2>&1; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -2", "description": "Probe CREATE TYPE parsing, round-trips, and fallbacks"}
[tool_result] 'CREATE TYPE shell' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE TYPE r AS RANGE (subtype = float8)' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE TYPE t AS ENUM ('a') garbage' contains unsupported syntax. Falling back to parsing as a 'Command'.
Create | CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')
Create | CREATE TYPE s.mood AS ENUM ('sad')
Create | CREATE TYPE complex AS (r DOUBLE PRECISION, i DOUBLE PRECISION)
Create | CREATE TYPE pair AS (a INT, b TEXT COLLATE "C")
Command | CREATE TYPE shell
Command | CREATE TYPE r AS RANGE (subtype = float8)
Command | CREATE TYPE t AS ENUM ('a') garbage
DataType(
  this=DType.ENUM,
  expressions=[
    Literal(this='FICTION', is_string=True),
    Literal(this='NONFICTION', is_string=True)]) TYPE
.........................                              [100%]
25 passed, 378 subtests passed in 0.16s
[assistant] All seven probes behave as intended: the enum and composite forms round-trip, and shell/`RANGE`/trailing-garbage inputs still fall back to `Command`. Next I'll add regression tests to the Postgres test file, placed near the existing `CREATE` tests.
[tool_use Bash] {"command": "grep -n \"    def test_\" tests/dialects/test_postgres.py | head -40", "description": "List Postgres test methods to pick insertion point"}
[tool_result] 10:    def test_postgres(self):
1087:    def test_ddl(self):
1403:    def test_unnest(self):
1428:    def test_array_offset(self):
1451:    def test_bool_or(self):
1457:    def test_string_concat(self):
1481:    def test_variance(self):
1505:    def test_corr(self):
1535:    def test_regexp_binary(self):
1540:    def test_unnest_json_array(self):
1568:    def test_rows_from(self):
1577:    def test_array_length(self):
1623:    def test_xmlelement(self):
1637:    def test_analyze(self):
1643:    def test_recursive_cte(self):
1653:    def test_json_extract(self):
1675:    def test_udt(self):
1686:    def test_round(self):
1704:    def test_datatype(self):
1708:    def test_locks(self):
1713:    def test_grant(self):
1749:    def test_revoke(self):
1788:    def test_begin_transaction(self):
1811:    def test_interval_span(self):
1833:    def test_postgres_create_trigger(self):
[tool_use Bash] {"command": "sed -n 1675,1686p tests/dialects/test_postgres.py", "description": "Read test_udt for placement and style"}
[tool_result]     def test_udt(self):
        def _validate_udt(sql: str):
            self.validate_identity(sql).to.assert_is(exp.DataType)

        _validate_udt("CAST(5 AS MyType)")
        _validate_udt('CAST(5 AS "MyType")')
        _validate_udt("CAST(5 AS MySchema.MyType)")
        _validate_udt('CAST(5 AS "MySchema"."MyType")')
        _validate_udt('CAST(5 AS MySchema."MyType")')
        _validate_udt('CAST(5 AS "MyCatalog"."MySchema"."MyType")')

    def test_round(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-180317-postgres-dialect-create-type-fal/base-1/tests/dialects/test_postgres.py", "old_string": "        _validate_udt('CAST(5 AS \"MyCatalog\".\"MySchema\".\"MyType\")')\n\n    def test_round(self):", "new_string": "        _validate_udt('CAST(5 AS \"MyCatalog\".\"MySchema\".\"MyType\")')\n\n    def 
…[299 chars elided]…
    \"CREATE TYPE complex AS (r DOUBLE PRECISION, i DOUBLE PRECISION)\"\n        ).assert_is(exp.Create)\n        self.validate_identity('CREATE TYPE pair AS (a INT, b TEXT COLLATE \"C\")')\n        self.validate_identity(\"CREATE TYPE shell\").assert_is(exp.Command)\n        self.validate_identity(\"CREATE TYPE r AS RANGE (subtype = float8)\").assert_is(exp.Command)\n\n    def test_round(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-180317-postgres-dialect-create-type-fal/base-1/tests/dialects/test_postgres.py has been updated successfully.
[assistant] I'll run the Postgres tests, then the full suite as the project's checks specify.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -15", "description": "Run Postgres dialect tests with new test added"}
[tool_result] ..........................                             [100%]
26 passed, 378 subtests passed in 0.17s
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; ls $PY >/dev/null && ($PY -m ruff --version 2>/dev/null && $PY -m ruff format --check sqlglot/parsers/postgres.py sqlglot/generators/postgres.py tests/dialects/test_postgres.py; $PY -m ruff check sqlglot/parsers/postgres.py sqlglot/generators/postgres.py tests/dialects/test_postgres.py) 2>&1 | tail -10", "description": "Run full test suite and ruff format/lint on changed files"}
[tool_result] ............................................................................................ [ 30%]
.......................... [ 32%]
.......................................... [ 36%]
..................................................................................................................................................................................................... [ 53%]
....................... [ 56%]
................................................................................
…[220 chars elided]…
.......................... [ 83%]
............................................ [ 87%]
........................... [ 89%]
............................... [ 92%]
............................................................. [ 98%]
.....................                                                                 [100%]
1106 passed, 17982 subtests passed in 50.56s
ruff 0.15.6
Would reformat: tests/dialects/test_postgres.py
1 file would be reformatted, 2 files already formatted
All checks passed!
[assistant] The full suite passes (1106 passed). Ruff wants to reformat the test file, so I'll check that its diff touches only my new lines before applying it.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format --diff tests/dialects/test_postgres.py 2>&1 | head -30", "description": "Preview ruff formatting diff for the test file"}
[tool_result] --- tests/dialects/test_postgres.py
+++ tests/dialects/test_postgres.py
@@ -1684,9 +1684,9 @@
         _validate_udt('CAST(5 AS "MyCatalog"."MySchema"."MyType")')
 
     def test_create_type(self):
-        self.validate_identity(
-            "CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')"
-        ).assert_is(exp.Create)
+        self.validate_identity("CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')").assert_is(
+            exp.Create
+        )
         self.validate_identity("CREATE TYPE myschema.mood AS ENUM ('sad', 'ok', 'happy')")
         self.validate_identity(
             "CREATE TYPE complex AS (r DOUBLE PRECISION, i DOUBLE PRECISION)"

1 file would be reformatted
[assistant] The diff only touches my new lines, so I'll apply it and re-verify.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format tests/dialects/test_postgres.py && $PY -m ruff format --check sqlglot tests/dialects/test_postgres.py | tail -1 && $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -1 && git status --short && git diff --stat", "description": "Apply ruff formatting and confirm tests and diff stat"}
[tool_result] 1 file reformatted
176 files already formatted
26 passed, 378 subtests passed in 0.16s
 M sqlglot/generators/postgres.py
 M sqlglot/parsers/postgres.py
 M tests/dialects/test_postgres.py
 sqlglot/generators/postgres.py  |  3 +++
 sqlglot/parsers/postgres.py     | 22 ++++++++++++++++++++++
 tests/dialects/test_postgres.py | 12 ++++++++++++
 3 files changed, 37 insertions(+)
[This command modified 1 file you've previously read: tests/dialects/test_postgres.py. Call Read before editing.]
[assistant] `CREATE TYPE` now parses into a real `Create` node for both enum and composite types, and round-trips in Postgres. The issue's example prints `CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')` with no fallback warning. The full suite passes (1106 passed) and ruff is clean. I did not commit.

**What changed**

- **`sqlglot/parsers/postgres.py`**: a `_parse_create` override handles `CREATE TYPE`. Enum bodies become the existing `DataType(ENUM, ...)` node, and composite bodies become the existing `Schema` of column definitions. Anything else (`CREATE TYPE shell`, `AS RANGE (...)`, trailing
…[197 chars elided]…
is the Postgres form and matches the issue's example. Composite output needed no change.
- **`tests/dialects/test_postgres.py`**: added `test_create_type` covering enum, schema-qualified enum, composite, and the fallback cases. No existing test was edited.

**Decisions to review**

- The enum spacing change applies to every Postgres-targeted `ENUM` datatype, not just `CREATE TYPE`. No existing test depended on the old form, but it is a visible change to `ENUM` output when generating Postgres.
- I did not add `CREATE DOMAIN`, `RANGE`, or shell types. The issue asked for enum and composite only.
