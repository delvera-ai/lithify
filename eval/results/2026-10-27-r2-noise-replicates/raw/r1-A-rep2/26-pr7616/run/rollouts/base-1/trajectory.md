# trajectory base-1

final message:
`CREATE TYPE ... AS ENUM` and `CREATE TYPE ... AS (attr type, ...)` now parse into `exp.Create` nodes and round-trip in the Postgres dialect. The full suite passes (1106 tests), and ruff and mypy are clean on the changed modules. I haven't committed.

**What changed**
- **`sqlglot/parsers/postgres.py`**: a `_parse_create` override that handles `CREATE TYPE`. Enums become `Create(kind="TYPE", this=<name>, expression=DataType(ENUM, labels))`. Composites become `Create(kind="TYPE", this=<name>, expression=Schema(ColumnDefs))`. Schema-qualified names work too.
- **`sqlglot/generators/postgres.py`**: the Postgres `datatype_sql` writes `ENUM (...)` with the space Postgres expects. Before this, an enum `DataType` rendered as `ENUM('a', 'b')`.
- **`tests/dialects/test_postgres.py`**: a `test_create_type` covering the enum, a schema-qualified enum, a composite, and a shell type that should still fall back to `Command`.

**Behavior to be aware of**
- The `ENUM` spacing change applies to every Postgres enum `DataType`, not just `CREATE TYPE`. No existing test pins that output, and Postgres doesn't accept the old form anyway, but it's a wider change than the ticket asked for.
- Composite attribute types are normalized the same way they already are in `CREATE TABLE`, so `NUMERIC` comes out as `DECIMAL`. That's equivalent in Postgres.
- Shell types (`CREATE TYPE shell`) and range or base types (`AS RANGE (...)`) still fall back to `Command`. They're outside the ticket's scope.

## events
[assistant] I'll start by finding how the Postgres parser handles `CREATE` and where the fallback happens.
[tool_use Bash] {"command": "rtk git status --short | head; grep -n \"TYPE\\|ENUM\" sqlglot/dialects/postgres.py | head -60; grep -n \"_parse_create\\b\\|def _parse_create\\|\\\"TYPE\\\"\\|TYPE\" sqlglot/parser.py | head -60", "description": "Check git status and find TYPE/ENUM references"}
[tool_result] (eval):1: command not found: rtk
12:    TYPED_DIVISION = True
84:            "CSTRING": TokenType.PSEUDO_TYPE,
111:            "REGTYPE": TokenType.OBJECT_IDENTIFIER,
27:if t.TYPE_CHECKING:
39:OPTIONS_TYPE = dict[str, Sequence[t.Union[Sequence[str], str]]]
367:            is_string=dialect.UUID_IS_STRING_TYPE or None
423:        "UUID": lambda args, dialect: exp.Uuid(is_string=dialect.UUID_IS_STRING_TYPE or None),
427:            is_string=dialect.UUID_IS_STRING_TYPE or None,
441:    STRUCT_TYPE
…[2870 chars elided]…
pe.PSEUDO_TYPE:
6179:        nested = type_token in self.NESTED_TYPE_TOKENS
6180:        is_struct = type_token in self.STRUCT_TYPE_TOKENS
6181:        is_aggregate = type_token in self.AGGREGATE_TYPE_TOKENS
6199:            elif type_token in self.ENUM_TYPE_TOKENS:
6293:                unsigned_type_token = self.SIGNED_TO_UNSIGNED_TYPE_TOKEN.get(type_token)
6359:        if self.TYPE_CONVERTERS and isinstance(this.this, exp.DType):
6360:            converter = self.TYPE_CONVERTERS.get(this.this)
[tool_use Bash] {"command": "grep -n \"class Create\\b\\|class Create(\" -A 30 sqlglot/expressions.py | head -50; grep -n \"class Enum\\|class Composite\\|ENUM\\|class ColumnDef\" sqlglot/expressions.py sqlglot/dialects/postgres.py sqlglot/generators/postgres.py 2>/dev/null | head -30; ls sqlglot/generators 2>/dev/null | head -3", "description": "Inspect Create expression and enum references"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
__init__.py
athena.py
bigquery.py
[tool_use Bash] {"command": "ls sqlglot sqlglot/expressions* 2>/dev/null | head -80; sed -n 2344,2480p sqlglot/parser.py", "description": "List package layout and read _parse_create"}
[tool_result] sqlglot:
__init__.py
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

sqlglot/expressions:
__init__.py
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
    def _parse_
…[5282 chars elided]…
         return self._parse_as_command(start)

            trigger_props = self.expression(
                exp.TriggerProperties(
                    table=table,
                    timing=timing,
                    events=events,
                    execute=execute,
                    constraint=is_constraint,
                    referenced_table=referenced_table,
                    deferrable=deferrable,
                    initially=initially,
                    referencing=referencing,
[tool_use Bash] {"command": "sed -n 2480,2620p sqlglot/parser.py; grep -n \"CREATABLES\" -A 25 sqlglot/parser.py | head -40", "description": "Read rest of _parse_create and CREATABLES"}
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
…[6019 chars elided]…
      TokenType.COLUMN,
641-        TokenType.CONSTRAINT,
642-        TokenType.FOREIGN_KEY,
643-        TokenType.FUNCTION,
644-        TokenType.INDEX,
645-        TokenType.PROCEDURE,
646-        TokenType.TRIGGER,
647:        *DB_CREATABLES,
648-    }
649-
650-    TRIGGER_EVENTS: t.ClassVar = {
651-        TokenType.INSERT,
652-        TokenType.UPDATE,
653-        TokenType.DELETE,
654-        TokenType.TRUNCATE,
655-    }
656-
657-    ALTERABLES: t.ClassVar = {
658-        TokenType.INDEX,
[assistant] `TYPE` isn't in `CREATABLES`, so that's the first gap. Next I'll check whether a `TYPE` token exists and what enum-related expression classes already exist.
[tool_use Bash] {"command": "grep -n \"\\\"TYPE\\\"\\|TokenType.TYPE\\b\\|    TYPE = \" sqlglot/tokens.py sqlglot/parser.py sqlglot/dialects/*.py | head; grep -rn \"ENUM\" sqlglot/expressions/ | head -20; grep -n \"CREATABLE_KIND_MAPPING\" -A4 sqlglot/dialects/dialect.py | head; grep -rn \"class Enum\\|EnumValue\\|ENUM\" sqlglot/dialects/postgres.py sqlglot/generators/postgres.py sqlglot/parsers/postgres.py 2>/dev/null | head -20; ls sqlglot/parsers sqlglot/generators | head -50", "description": "Search for TYPE token and enum handling"}
[tool_result] sqlglot/parser.py:1629:        "TYPE": ("EVOLUTION",),
sqlglot/parser.py:8627:        self._match_text_seq("TYPE")
sqlglot/expressions/datatypes.py:62:    ENUM = auto()
sqlglot/expressions/datatypes.py:63:    ENUM8 = auto()
sqlglot/expressions/datatypes.py:64:    ENUM16 = auto()
247:        klass.INVERSE_CREATABLE_KIND_MAPPING = {
248:            v: k for k, v in klass.CREATABLE_KIND_MAPPING.items()
249-        }
250-
251-        base = seq_get(bases, 0)
252-        base_tokenizer = (getattr(bas
…[248 chars elided]…
ena.py
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
[assistant] There's no `TYPE` token, so `TYPE` lexes as a plain var. Next I'll look at how the Postgres parser and generator override DDL, and at the `Create` generator.
[tool_use Bash] {"command": "wc -l sqlglot/parsers/postgres.py sqlglot/generators/postgres.py; grep -n \"def \\|_match_text_seq(\\\"\" sqlglot/parsers/postgres.py | head -80; grep -n \"_parse_create\\|STATEMENT_PARSERS\\|CREATABLE\" sqlglot/parsers/postgres.py sqlglot/dialects/postgres.py | head", "description": "Survey Postgres parser and generator methods"}
[tool_result]      343 sqlglot/parsers/postgres.py
     569 sqlglot/generators/postgres.py
     912 total
18:def _build_generate_series(args: list) -> exp.ExplodingGenerateSeries:
31:def _build_to_timestamp(args: list) -> exp.UnixToTime | exp.StrToTime:
41:def _build_regexp_replace(args: list, dialect: DialectType = None) -> exp.RegexpReplace:
66:def _build_levenshtein_less_equal(args: list) -> exp.Levenshtein:
205:    def _parse_parameter_mode(self) -> TokenType | None:
253:    def _create_mode_constraint(se
…[282 chars elided]…
self._match_text_seq("S")
299:    def _parse_date_part(self) -> exp.Expr:
309:    def _parse_unique_key(self) -> exp.Expr | None:
312:    def _parse_jsonb_exists(self) -> exp.JSONBExists:
321:    def _parse_generated_as_identity(
330:        if self._match_text_seq("STORED"):
335:    def _parse_user_defined_type(self, identifier: exp.Identifier) -> exp.Expr | None:
sqlglot/parsers/postgres.py:176:    STATEMENT_PARSERS = {
sqlglot/parsers/postgres.py:177:        **parser.Parser.STATEMENT_PARSERS,
[tool_use Bash] {"command": "grep -n \"def create_sql\" -A 60 sqlglot/generator.py | head -90; grep -n \"def create_sql\\|def .*_sql\" sqlglot/generators/postgres.py | head -80", "description": "Read Create generator and Postgres generator methods"}
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
…[4045 chars elided]…
-> str:
511:    def isascii_sql(self, expression: exp.IsAscii) -> str:
514:    def ignorenulls_sql(self, expression: exp.IgnoreNulls) -> str:
519:    def respectnulls_sql(self, expression: exp.RespectNulls) -> str:
525:    def currentschema_sql(self, expression: exp.CurrentSchema) -> str:
528:    def interval_sql(self, expression: exp.Interval) -> str:
538:    def placeholder_sql(self, expression: exp.Placeholder) -> str:
545:    def arraycontains_sql(self, expression: exp.ArrayContains) -> str:
[assistant] The Postgres parser has no `_parse_create` override yet. I'll read the parser class header, the `_parse_as_command` helper, and the `Schema`/`DataType` generator paths I'd be reusing.
[tool_use Bash] {"command": "sed -n 1,17p sqlglot/parsers/postgres.py; sed -n 170,205p sqlglot/parsers/postgres.py; sed -n 330,343p sqlglot/parsers/postgres.py; grep -n \"def _parse_as_command\" -A 12 sqlglot/parser.py; grep -n \"def schema_sql\" -A 12 sqlglot/generator.py; grep -n \"def datatype_sql\" -A 14 sqlglot/generators/postgres.py", "description": "Read parser header, command fallback, schema and datatype generation"}
[tool_result] from __future__ import annotations

import typing as t

from sqlglot import exp, parser
from sqlglot.dialects.dialect import (
    DialectType,
    binary_from_function,
    build_formatted_time,
    build_json_extract_path,
    build_timestamp_trunc,
)
from sqlglot.helper import is_int, seq_get
from sqlglot.parser import binary_range_parser
from sqlglot.tokens import TokenType


        TokenType.DAMP: binary_range_parser(exp.ArrayOverlaps),
        TokenType.DAT: lambda self, this: self.expres
…[3325 chars elided]…
True)}[{values}]"
482-            return "ARRAY"
483-
484-        if expression.is_type(exp.DType.DOUBLE, exp.DType.FLOAT) and expression.expressions:
485-            # Postgres doesn't support precision for REAL and DOUBLE PRECISION types
486-            return f"FLOAT({self.expressions(expression, flat=True)})"
487-
488-        return super().datatype_sql(expression)
489-
490-    def cast_sql(self, expression: exp.Cast, safe_prefix: str | None = None) -> str:
491-        this = expression.this
[assistant] Before writing anything, I'll check what the current fallback produces and how the existing `DataType` ENUM and `Schema` nodes render under Postgres.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nfrom sqlglot import parse_one, exp\ne = parse_one(\\\"CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')\\\", 'postgres'); print(type(e).__name__, repr(e)[:200])\ndt = exp.DataType.build(\\\"ENUM\\\"); dt = exp.DataType(this=exp.DType.ENUM, expressions=[exp.Literal.string('A'), exp.Literal.string('B')])\nprint(dt.sql('postgres'))\ns = exp.Schema(expressions=[exp.ColumnDef(this=exp.to_identifier('a'), kind=exp.DataType.build('int'))])\nprint(s.sql('postgres'))\n\" 2>&1 | tail -5", "description": "Check current fallback and enum/schema rendering"}
[tool_result] 'CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')' contains unsupported syntax. Falling back to parsing as a 'Command'.
Command Command(this=CREATE, expression=TYPE book_type AS ENUM ('FICTION', 'NONFICTION'))
ENUM('A', 'B')
(a INT)
[assistant] The existing `DataType(ENUM)` renders as `ENUM('A', 'B')` with no space, while Postgres needs `ENUM ('A', 'B')`. I'll check whether any existing tests pin that spacing before deciding how to emit it.
[tool_use Bash] {"command": "grep -rn \"ENUM\" tests/ | grep -v \"ENUM8\\|ENUM16\" | head -30; grep -rn \"CREATE TYPE\\|CREATE DOMAIN\" tests/ | head", "description": "Find existing ENUM and CREATE TYPE test expectations"}
[tool_result] tests/dialects/test_singlestore.py:764:            "CREATE TABLE testTypes (a ENUM('a'))",
tests/dialects/test_singlestore.py:766:                "singlestore": "CREATE TABLE testTypes (a ENUM('a'))",
tests/dialects/test_singlestore.py:771:            "CREATE TABLE testTypes (a ENUM('a'))",
tests/dialects/test_singlestore.py:773:                "singlestore": "CREATE TABLE testTypes (a ENUM('a'))",
tests/dialects/test_duckdb.py:501:        self.validate_identity("CREATE TABLE color (name ENUM('RED', 'GREEN', 'BLUE'))")
tests/dialects/test_mysql.py:417:        self.validate_identity("CAST(x AS ENUM('a', 'b'))")
[assistant] No existing Postgres test pins `ENUM` spacing, so I can change that in the Postgres generator. Before editing, I'll confirm the helper signatures I plan to use and check for any existing `_parse_create` override in other dialects.
[tool_use Bash] {"command": "grep -n \"def _parse_schema\\|def _parse_wrapped_csv\\|def _match_text_seq\\|def _parse_table_parts\\|def _parse_string\" -A 3 sqlglot/parser.py | head -40; grep -rn \"def _parse_create\\b\" sqlglot/parsers/ | head; grep -n \"def datatype_sql\" -A 12 sqlglot/generator.py | head -20", "description": "Confirm parser helper signatures and existing overrides"}
[tool_result] 1948:    def _match_text_seq(self, *texts: str, advance: bool = True) -> bool:
1949-        index = self._index
1950-        string_type = TokenType.STRING
1951-        for text in texts:
--
4579:    def _parse_table_parts_fast(self) -> exp.Table | None:
4580-        index = self._index
4581-        parts: list[exp.Identifier] | None = None
4582-        all_comments: list[str] | None = None
--
4642:    def _parse_table_parts(
4643-        self,
4644-        schema: bool = False,
4645-        is_
…[1473 chars elided]…
ql(self, expression: exp.DataType) -> str:
1684-        nested = ""
1685-        values = ""
1686-
1687-        expr_nested = expression.args.get("nested")
1688-        type_value = expression.this
1689-
1690-        if (
1691-            not expr_nested
1692-            and isinstance(type_value, exp.DType)
1693-            and (settings := self.TYPE_PARAM_SETTINGS.get(type_value))
1694-        ):
1695-            expression = self.datatype_param_bound_limiter(expression, type_value, *settings)
[assistant] Other dialects already override `_parse_create` (Snowflake, TSQL, Fabric, StarRocks), so I'll copy their pattern for the fallback path.
[tool_use Bash] {"command": "sed -n 1004,1016p sqlglot/parsers/snowflake.py; sed -n 8,20p sqlglot/parsers/fabric.py", "description": "Read existing _parse_create override pattern"}
[tool_result]     def _parse_create(self) -> exp.Create | exp.Command:
        expression = super()._parse_create()
        if isinstance(expression, exp.Create) and expression.kind in self.NON_TABLE_CREATABLES:
            # Replace the Table node with the enclosed Identifier
            expression.this.replace(expression.this.this)

        return expression

    # https://docs.snowflake.com/en/sql-reference/functions/date_part.html
    # https://docs.snowflake.com/en/sql-reference/functions-date-time.html#
…[342 chars elided]…
CHAR(1)/CHAR(1)
            if create.kind == "TABLE" and isinstance(create.this, exp.Schema):
                for column in create.this.expressions:
                    if isinstance(column, exp.ColumnDef):
                        column_type = column.kind
                        if (
                            isinstance(column_type, exp.DataType)
                            and column_type.this in (exp.DType.VARCHAR, exp.DType.CHAR)
                            and not column_type.expressions
[assistant] I have what I need. The plan:

- **Parser:** a Postgres `_parse_create` override that handles `CREATE TYPE name AS ENUM (...)` and `CREATE TYPE name AS (attr type, ...)` as `exp.Create(kind="TYPE")`, and falls back to a command for anything else (shell types, ranges, base types).
- **Generator:** Postgres writes `AS ENUM (...)` with the space Postgres expects.

Starting with the parser:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-090151-postgres-dialect-create-type-fal/base-1/sqlglot/parsers/postgres.py", "old_string": "        return exp.DataType.build(udt_type, udt=True)", "new_string": "        return exp.DataType.build(udt_type, udt=True)\n\n    def _parse_create(self) -> exp.Create | exp.Command:\n        start = self._p
…[309 chars elided]…
.DataType(\n                    this=exp.DType.ENUM, expressions=self._parse_wrapped_csv(self._parse_string)\n                )\n            else:\n                expression = self._parse_schema()\n\n        if not this or not expression or self._curr:\n            return self._parse_as_command(start)\n\n        return self.expression(exp.Create(this=this, kind=\"TYPE\", expression=expression))"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-090151-postgres-dialect-create-type-fal/base-1/sqlglot/parsers/postgres.py has been updated successfully.
[assistant] Now the generator. I'll add an `ENUM` branch to the Postgres `datatype_sql`, next to the existing FLOAT/DOUBLE special case:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-090151-postgres-dialect-create-type-fal/base-1/sqlglot/generators/postgres.py", "old_string": "            return f\"FLOAT({self.expressions(expression, flat=True)})\"\n\n        return super().datatype_sql(expression)", "new_string": "            return f\"FLOAT({self.expressions(expression, flat=True)})\"\n\n        if expression.is_type(exp.DType.ENUM) and expression.expressions:\n            return f\"ENUM ({self.expressions(expression, flat=True)})\"\n\n        return super().datatype_sql(expression)"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-090151-postgres-dialect-create-type-fal/base-1/sqlglot/generators/postgres.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nfrom sqlglot import parse_one, exp\ncases = [\n \\\"CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')\\\",\n \\\"CREATE TYPE public.book_type AS ENUM ('FICTION')\\\",\n 'CREATE TYPE complex AS (r DOUBLE PRECISION, i DOUBLE PRECISION)',\n 'CREATE TYPE inventory_item AS (name TEXT, supplier_id INT, price NUMERIC)',\n 'CREATE TYPE shell',\n 'CREATE TYPE float8_range AS RANGE (subtype = float8, subtype_diff = float8mi)',\n]\nfor c in cases:\n    e = parse_one(c, 'postgres')\n    print(type(e).__name__, '|', e.sql('postgres'))\nprint(repr(parse_one(cases[0], 'postgres'))[:300])\n\" 2>&1", "description": "Round-trip CREATE TYPE cases in Postgres"}
[tool_result] 'CREATE TYPE shell' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE TYPE float8_range AS RANGE (subtype = float8, subtype_diff = float8mi)' contains unsupported syntax. Falling back to parsing as a 'Command'.
Create | CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')
Create | CREATE TYPE public.book_type AS ENUM ('FICTION')
Create | CREATE TYPE complex AS (r DOUBLE PRECISION, i DOUBLE PRECISION)
Create | CREATE TYPE inventory_item AS (name TEXT, supplier_id INT, price DECIMAL)
Command | CREATE TYPE shell
Command | CREATE TYPE float8_range AS RANGE (subtype = float8, subtype_diff = float8mi)
Create(
  this=Table(
    this=Identifier(this=book_type, quoted=False)),
  kind=TYPE,
  expression=DataType(
    this=DType.ENUM,
    expressions=[
      Literal(this='FICTION', is_string=True),
      Literal(this='NONFICTION', is_string=True)]))
[assistant] All four supported forms now round-trip as `Create` nodes, and the unsupported forms (shell and range types) still fall back to `Command`. Next I'll add tests to the Postgres dialect test file, finding a nearby DDL test to sit beside.
[tool_use Bash] {"command": "grep -n \"def test_\\|CREATE DOMAIN\\|CREATE EXTENSION\" tests/dialects/test_postgres.py | head -60", "description": "List test methods in Postgres dialect tests"}
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
[tool_use Bash] {"command": "sed -n 1675,1690p tests/dialects/test_postgres.py", "description": "Read the udt test for style"}
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
        self.validate_identity("ROUND(x)")
        self.validate_identity("ROUND(x, y)")
        self.validate_identity("ROUND(CAST(x AS DOUBLE PRECISION))")
        self.validate_identity("ROUND(CAST(x AS DECIMAL), 4)")
[assistant] I'll add a `test_create_type` next to `test_udt`, covering enum, schema-qualified enum, composite, and a shell type that should still fall back to `Command`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-090151-postgres-dialect-create-type-fal/base-1/tests/dialects/test_postgres.py", "old_string": "        _validate_udt('CAST(5 AS \"MyCatalog\".\"MySchema\".\"MyType\")')\n\n    def test_round(self):", "new_string": "        _validate_udt('CAST(5 AS \"MyCatalog\".\"MySchema\".\"MyType\")')\n\n    def 
…[114 chars elided]…
").assert_is(\n            exp.Create\n        )\n        self.validate_identity(\"CREATE TYPE public.book_type AS ENUM ('FICTION')\")\n        self.validate_identity(\n            \"CREATE TYPE inventory_item AS (name TEXT, supplier_id INT, price DECIMAL)\"\n        ).assert_is(exp.Create)\n        self.validate_identity(\"CREATE TYPE shell\").assert_is(exp.Command)\n\n    def test_round(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-090151-postgres-dialect-create-type-fal/base-1/tests/dialects/test_postgres.py has been updated successfully.
[assistant] Next I'll run the Postgres dialect tests, then the full suite using the project's check command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -15", "description": "Run Postgres dialect tests"}
[tool_result] ..........................                             [100%]
26 passed, 378 subtests passed in 0.27s
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run full test suite"}
[tool_result] ................................................................ [  5%]
........................... [  8%]
............. [  9%]
........................................................................................................................................ [ 21%]
............................................................................................ [ 30%]
.......................... [ 32%]
.......................................... [ 36%]
............................................
…[358 chars elided]…
........................................... [ 73%]
............................................................................................................. [ 83%]
............................................ [ 87%]
........................... [ 89%]
............................... [ 92%]
............................................................. [ 98%]
.....................                                                                 [100%]
1106 passed, 17982 subtests passed in 54.32s
[assistant] The full suite passes: 1106 tests. The project also runs ruff, so I'll lint and format-check the three changed files.
[tool_use Bash] {"command": "F=\"sqlglot/parsers/postgres.py sqlglot/generators/postgres.py tests/dialects/test_postgres.py\"; <work>/env-sqlglot/bin/python -m ruff check $F 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m ruff format --check $F 2>&1 | tail -5; git status --short", "description": "Lint and format-check changed files"}
[tool_result] E902 No such file or directory (os error 2)
--> sqlglot/parsers/postgres.py sqlglot/generators/postgres.py tests/dialects/test_postgres.py:1:1

Found 1 error.
error: Failed to format sqlglot/parsers/postgres.py sqlglot/generators/postgres.py tests/dialects/test_postgres.py: No such file or directory (os error 2)
 M sqlglot/generators/postgres.py
 M sqlglot/parsers/postgres.py
 M tests/dialects/test_postgres.py
[assistant] Ruff reported "No such file" on paths that exist, so the invocation itself is probably wrong. I'll check which ruff binary is available.
[tool_use Bash] {"command": "which ruff; ruff --version 2>&1; ruff check sqlglot/parsers/postgres.py sqlglot/generators/postgres.py tests/dialects/test_postgres.py 2>&1 | tail -3; ruff format --check sqlglot/parsers/postgres.py sqlglot/generators/postgres.py tests/dialects/test_postgres.py 2>&1 | tail -3", "description": "Run ruff using the system binary"}
[tool_result] <work>/env-sqlglot/bin/ruff
ruff 0.15.6
All checks passed!
3 files already formatted
[assistant] Ruff passes on the three files. The pre-commit config also runs mypy, so I'll run it on the parser and generator modules as a final check.
[tool_use Bash] {"command": "timeout 170 <work>/env-sqlglot/bin/python -m mypy sqlglot/parsers/postgres.py sqlglot/generators/postgres.py 2>&1 | tail -4", "description": "Type-check the changed Postgres modules"}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m mypy sqlglot/parsers/postgres.py sqlglot/generators/postgres.py 2>&1 | tail -4", "description": "Type-check the changed Postgres modules"}
[tool_result] Success: no issues found in 2 source files
[assistant] `CREATE TYPE ... AS ENUM` and `CREATE TYPE ... AS (attr type, ...)` now parse into `exp.Create` nodes and round-trip in the Postgres dialect. The full suite passes (1106 tests), and ruff and mypy are clean on the changed modules. I haven't committed.

**What changed**
- **`sqlglot/parsers/postgres.py`**: a `_parse_create` override that handles `CREATE TYPE`. Enums become `Create(kind="TYPE", this=<name>, expression=DataType(ENUM, labels))`. Composites become `Create(kind="TYPE", this=<name>, expression=Schema(ColumnDefs))`. Schema-qualified names work too.
- **`sqlglot/generators/postgres.py`*
…[287 chars elided]…
should still fall back to `Command`.

**Behavior to be aware of**
- The `ENUM` spacing change applies to every Postgres enum `DataType`, not just `CREATE TYPE`. No existing test pins that output, and Postgres doesn't accept the old form anyway, but it's a wider change than the ticket asked for.
- Composite attribute types are normalized the same way they already are in `CREATE TABLE`, so `NUMERIC` comes out as `DECIMAL`. That's equivalent in Postgres.
- Shell types (`CREATE TYPE shell`) and range or base types (`AS RANGE (...)`) still fall back to `Command`. They're outside the ticket's scope.
