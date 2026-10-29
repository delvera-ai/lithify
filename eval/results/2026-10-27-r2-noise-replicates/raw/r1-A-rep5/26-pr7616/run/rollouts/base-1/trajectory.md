# trajectory base-1

final message:
`CREATE TYPE` now parses into a real `Create` node in the Postgres dialect for both enum and composite types, and round-trips unchanged. The full test suite passes (1106 tests), and ruff and mypy are clean.

```python
parse_one("CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')", "postgres").sql("postgres")
# "CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')"
```

Composite types also round-trip; their attribute types get uppercased, as sqlglot does elsewhere (`r DOUBLE PRECISION`).

**Changes:**
- **`sqlglot/parsers/postgres.py`**: a `_parse_create` override that handles `CREATE TYPE <name> AS ENUM (...)` and `CREATE TYPE <name> AS (attr type, ...)`. Anything else still falls back to a Command, including `CREATE TYPE t` with no `AS` and the `AS RANGE (...)` form.
- **`sqlglot/expressions/ddl.py`**: a new `EnumType` expression holding the enum labels.
- **`sqlglot/generator.py`**: `enumtype_sql`, which emits `ENUM (...)`.
- **`tests/dialects/test_postgres.py`**: a `test_create_type` covering both forms, the schema-qualified name, and the fallback cases. I only added the `parse_one` import; no existing test was touched.

**Choices I made:**
- I scoped the parsing to Postgres rather than the base parser, so other dialects that already fall back on `CREATE TYPE` are unchanged.
- `TYPE` is not a keyword token, so I match it by text. Columns named `type` are unaffected, which the test suite confirms.

## events
[tool_use Bash] {"command": "grep -n \"CREATE\\|_parse_create\\|ENUM\\|TYPE\" sqlglot/dialects/postgres.py | head -80; echo ---; grep -n \"def _parse_create\\|\\\"TYPE\\\"\\|TYPE\\b\" sqlglot/parser.py | head -40; echo ---; grep -n \"class Create\\b\\|class Create(\" -A 40 sqlglot/expressions.py | head -80"}
[tool_result] 12:    TYPED_DIVISION = True
84:            "CSTRING": TokenType.PSEUDO_TYPE,
111:            "REGTYPE": TokenType.OBJECT_IDENTIFIER,
---
39:OPTIONS_TYPE = dict[str, Sequence[t.Union[Sequence[str], str]]]
367:            is_string=dialect.UUID_IS_STRING_TYPE or None
423:        "UUID": lambda args, dialect: exp.Uuid(is_string=dialect.UUID_IS_STRING_TYPE or None),
427:            is_string=dialect.UUID_IS_STRING_TYPE or None,
558:        TokenType.PSEUDO_TYPE,
1017:                only_json_types
…[1180 chars elided]…
TIONS_TYPE] = {
1782:    JSON_ARROWS_REQUIRE_JSON_TYPE: t.ClassVar = False
2344:    def _parse_create(self) -> exp.Create | exp.Command:
3280:    def _parse_create_like(self) -> exp.LikeProperty | None:
6151:        if type_token == TokenType.PSEUDO_TYPE:
7710:            self.raise_error("Expected TYPE after CAST")
8627:        self._match_text_seq("TYPE")
9086:        self, options: OPTIONS_TYPE, raise_unmatched: bool = True
---
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "sed -n 2344,2480p sqlglot/parser.py; echo ---; ls sqlglot | head -50; grep -rn \"class Create(\" -A 30 sqlglot/expressions/*.py | head -50"}
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
…[6754 chars elided]…
 kind = self.args.get("kind")
sqlglot/expressions/ddl.py-61-        return kind and kind.upper()
sqlglot/expressions/ddl.py-62-
sqlglot/expressions/ddl.py-63-
sqlglot/expressions/ddl.py-64-class SequenceProperties(Expression):
sqlglot/expressions/ddl.py-65-    arg_types = {
sqlglot/expressions/ddl.py-66-        "increment": False,
sqlglot/expressions/ddl.py-67-        "minvalue": False,
sqlglot/expressions/ddl.py-68-        "maxvalue": False,
sqlglot/expressions/ddl.py-69-        "cache": False,
[tool_use Bash] {"command": "sed -n 2480,2620p sqlglot/parser.py; echo ---; grep -n \"CREATABLES\" -A 25 sqlglot/parser.py | head -40; echo ---; grep -rn \"TokenType.TYPE\\b\\|\\\"TYPE\\\"\" sqlglot/tokens.py sqlglot/parser.py sqlglot/parsers/*.py sqlglot/dialects/postgres.py sqlglot/generator.py sqlglot/generators/*.py | head; echo ---; grep -n \"ENUM\" sqlglot/parser.py sqlglot/generator.py sqlglot/generators/*.py sqlglot/dialects/postgres.py | head -30"}
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
…[7237 chars elided]…
 TokenType.ENUM16,
sqlglot/parser.py:586:        *ENUM_TYPE_TOKENS,
sqlglot/parser.py:6199:            elif type_token in self.ENUM_TYPE_TOKENS:
sqlglot/generators/clickhouse.py:240:        exp.DType.ENUM: "Enum",
sqlglot/generators/clickhouse.py:241:        exp.DType.ENUM8: "Enum8",
sqlglot/generators/clickhouse.py:242:        exp.DType.ENUM16: "Enum16",
sqlglot/generators/singlestore.py:351:        exp.DType.ENUM8: "ENUM",
sqlglot/generators/singlestore.py:352:        exp.DType.ENUM16: "ENUM",
[tool_use Bash] {"command": "grep -n \"\\\"TYPE\\|TYPE\\\":\" sqlglot/tokens.py | head; grep -n \"def create_sql\" -A 30 sqlglot/generators/*.py sqlglot/generator.py | head -80; echo ---; grep -rn \"CREATE TYPE\\|TYPE \" tests/dialects/test_postgres.py | head; grep -rn \"CREATABLE_KIND_MAPPING\" -A5 sqlglot/dialects/dialect.py | head -20"}
[tool_result] sqlglot/generators/databricks.py:75:    def create_sql(self, expression: exp.Create) -> str:
sqlglot/generators/databricks.py-76-        body = expression.expression
sqlglot/generators/databricks.py-77-        if (
sqlglot/generators/databricks.py-78-            body
sqlglot/generators/databricks.py-79-            and not isinstance(body, exp.Return)
sqlglot/generators/databricks.py-80-            and expression.kind == "FUNCTION"
sqlglot/generators/databricks.py-81-            and any(p.args.ge
…[6715 chars elided]…
or example, the Clickhouse
sqlglot/dialects/dialect.py-688-    equivalent of CREATE SCHEMA is CREATE DATABASE.
sqlglot/dialects/dialect.py-689-    """
sqlglot/dialects/dialect.py-690-
--
sqlglot/dialects/dialect.py:775:    INVERSE_CREATABLE_KIND_MAPPING: dict[str, str] = {}
sqlglot/dialects/dialect.py-776-
sqlglot/dialects/dialect.py-777-    ESCAPED_SEQUENCES: dict[str, str] = {}
sqlglot/dialects/dialect.py-778-
sqlglot/dialects/dialect.py-779-    # Delimiters for string literals and identifiers
[tool_use Bash] {"command": "grep -rn \"CREATE TYPE\\|create type\" -i tests/ | head; echo ---; grep -n \"def create_sql\" -A 110 sqlglot/generator.py | head -150; echo ---; grep -n \"class Enum\\|Enum(\" sqlglot/expressions/*.py | head"}
[tool_result] ---
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
1295-            and
…[4217 chars elided]…
",
1383-                wrapped=False,
1384-            )
1385-
1386-        concurrently = " CONCURRENTLY" if expression.args.get("concurrently") else ""
1387-        exists_sql = " IF NOT EXISTS" if expression.args.get("exists") else ""
1388-        no_schema_binding = (
1389-            " WITH NO SCHEMA BINDING" if expression.args.get("no_schema_binding") else ""
1390-        )
1391-
1392-        clone = self.sql(expression, "clone")
1393-        clone = f" {clone}" if clone else ""
1394-
---
[tool_use Bash] {"command": "ls sqlglot/parsers/ | head -50; grep -n \"class Parser\\|def _parse_\\|STATEMENT_PARSERS\\|import\" sqlglot/parsers/postgres.py | head -60; echo ---; grep -n \"def wrap\\|def expressions\" -A3 sqlglot/generator.py | head; grep -rn \"class Enum\\|EnumType\\|CreateType\" sqlglot/ | head"}
[tool_result] __init__.py
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
1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, parser
6:from sqlglot.dialects.dialect import (
13:fro
…[594 chars elided]…
_jsonb_exists(self) -> exp.JSONBExists:
321:    def _parse_generated_as_identity(
335:    def _parse_user_defined_type(self, identifier: exp.Identifier) -> exp.Expr | None:
---
1024:    def wrap(self, expression: exp.Expr | str) -> str:
1025-        this_sql = (
1026-            self.sql(expression)
1027-            if isinstance(expression, exp.UNWRAPPED_QUERIES)
--
4443:    def expressions(
4444-        self,
4445-        expression: exp.Expr | None = None,
4446-        key: str | None = None,
[tool_use Bash] {"command": "sed -n 170,205p sqlglot/parsers/postgres.py; sed -n 330,360p sqlglot/parsers/postgres.py; echo ---; grep -n \"def _parse_as_command\" -A12 sqlglot/parser.py; grep -n \"def _parse_table_parts\" -A3 sqlglot/parser.py; echo ---; grep -n \"class Create\\b\\|class Create(\" -B2 sqlglot/expressions/ddl.py; grep -n \"^class \\(Tuple\\|Schema\\|ColumnDef\\)\" sqlglot/expressions/*.py; cat sqlglot/parsers/__init__.py | head -5; cat <work>/env-sqlglot/bin/python >/dev/null 2>&1 && echo env-ok"}
[tool_result]         TokenType.DAMP: binary_range_parser(exp.ArrayOverlaps),
        TokenType.DAT: lambda self, this: self.expression(
            exp.MatchAgainst(this=self._parse_bitwise(), expressions=[this])
        ),
    }

    STATEMENT_PARSERS = {
        **parser.Parser.STATEMENT_PARSERS,
        TokenType.END: lambda self: self._parse_commit_or_rollback(),
    }

    UNARY_PARSERS = {
        **parser.Parser.UNARY_PARSERS,
        # The `~` token is remapped from TILDE to RLIKE in Postgres due to 
…[2090 chars elided]…
None
4582-        all_comments: list[str] | None = None
--
4642:    def _parse_table_parts(
4643-        self,
4644-        schema: bool = False,
4645-        is_db_reference: bool = False,
---
37-
38-
39:class Create(Expression, DDL):
sqlglot/expressions/properties.py:430:class SchemaCommentProperty(Property):
sqlglot/expressions/query.py:502:class ColumnDef(Expression):
sqlglot/expressions/query.py:886:class Tuple(Expression):
sqlglot/expressions/query.py:1115:class Schema(Expression):

env-ok
[tool_use Bash] {"command": "grep -n \"TokenType.CREATE:\" sqlglot/parser.py; sed -n 1024,1032p sqlglot/generator.py; grep -n \"def _parse_schema\" -A22 sqlglot/parser.py | head -40; grep -n \"def _parse_wrapped_csv\" -A3 sqlglot/parser.py; sed -n 39,40p sqlglot/expressions/ddl.py; sed -n 1,12p sqlglot/expressions/ddl.py"}
[tool_result] 1088:        TokenType.CREATE: lambda self: self._parse_create(),
    def wrap(self, expression: exp.Expr | str) -> str:
        this_sql = (
            self.sql(expression)
            if isinstance(expression, exp.UNWRAPPED_QUERIES)
            else self.sql(expression, "this")
        )
        if not this_sql:
            return "()"

7043:    def _parse_schema(self, this: exp.Expr | None = None) -> exp.Expr | None:
7044-        index = self._index
7045-        if not self._match(TokenType.
…[953 chars elided]…
:    def _parse_wrapped_csv(
8436-        self,
8437-        parse_method: t.Callable[[], T | None],
8438-        sep: TokenType = TokenType.COMMA,
class Create(Expression, DDL):
    arg_types = {
"""sqlglot expressions DDL."""

from __future__ import annotations

import typing as t

from sqlglot.helper import trait
from sqlglot.expressions.core import Expression, Expr, Func
from sqlglot.expressions.query import Query, Selectable

if t.TYPE_CHECKING:
    from sqlglot.expressions.query import CTE
[tool_use Bash] {"command": "grep -n \"def expressions\" -A12 sqlglot/generator.py | head -16; grep -n \"def schema_sql\" -A12 sqlglot/generator.py | head -14; grep -n \"def _parse_create_like\\|    def _parse_user_defined_type\" sqlglot/parsers/postgres.py; tail -5 sqlglot/parsers/postgres.py; grep -n \"^class Create\" -A3 sqlglot/expressions/ddl.py | head -3; sed -n 60,63p sqlglot/expressions/ddl.py"}
[tool_result] 4443:    def expressions(
4444-        self,
4445-        expression: exp.Expr | None = None,
4446-        key: str | None = None,
4447-        sqls: t.Collection[str | exp.Expr] | None = None,
4448-        flat: bool = False,
4449-        indent: bool = True,
4450-        skip_first: bool = False,
4451-        skip_last: bool = False,
4452-        sep: str = ", ",
4453-        prefix: str = "",
4454-        dynamic: bool = False,
4455-        new_line: bool = False,
3208:    def schema_sql(self
…[597 chars elided]…
cept_ = f"{self.seg(self.STAR_EXCEPT)} ({except_})" if except_ else ""
335:    def _parse_user_defined_type(self, identifier: exp.Identifier) -> exp.Expr | None:
            part = self._parse_id_var()
            if part:
                udt_type = exp.Dot(this=udt_type, expression=part)

        return exp.DataType.build(udt_type, udt=True)
39:class Create(Expression, DDL):
40-    arg_types = {
41-        "with_": False,
        kind = self.args.get("kind")
        return kind and kind.upper()
[assistant] Parser, expression, and generator changes: I'll override `_parse_create` in the Postgres parser for `TYPE`, add an `EnumType` expression, and generate it in the base generator.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-103150-postgres-dialect-create-type-fal/base-1/sqlglot/parsers/postgres.py", "old_string": "        return exp.DataType.build(udt_type, udt=True)\n", "new_string": "        return exp.DataType.build(udt_type, udt=True)\n\n    def _parse_create(self) -> exp.Create | exp.Command:\n        start = self.
…[326 chars elided]…
 self.expression(\n                exp.EnumType(expressions=self._parse_wrapped_csv(self._parse_string))\n            )\n        else:\n            expression = self._parse_schema()\n\n        if not isinstance(expression, (exp.EnumType, exp.Schema)):\n            return self._parse_as_command(start)\n\n        return self.expression(exp.Create(this=this, kind=\"TYPE\", expression=expression))\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-103150-postgres-dialect-create-type-fal/base-1/sqlglot/parsers/postgres.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-103150-postgres-dialect-create-type-fal/base-1/sqlglot/parsers/postgres.py", "old_string": "        if not isinstance(expression, (exp.EnumType, exp.Schema)):\n            return self._parse_as_command(start)", "new_string": "        if not expression or self._curr:\n            return self._parse_as_command(start)"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-103150-postgres-dialect-create-type-fal/base-1/sqlglot/parsers/postgres.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-103150-postgres-dialect-create-type-fal/base-1/sqlglot/expressions/ddl.py", "old_string": "        kind = self.args.get(\"kind\")\n        return kind and kind.upper()\n\n\nclass SequenceProperties(Expression):", "new_string": "        kind = self.args.get(\"kind\")\n        return kind and kind.upper()\n\n\nclass EnumType(Expression):\n    arg_types = {\"expressions\": True}\n\n\nclass SequenceProperties(Expression):"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-103150-postgres-dialect-create-type-fal/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"ddl\" sqlglot/expressions/__init__.py | head -3; grep -n \"    def createable_sql\\|    def encode_sql\\|    def enum\" sqlglot/generator.py"}
[tool_result] 19:from sqlglot.expressions.ddl import *  # noqa: F401,F403
1281:    def createable_sql(self, expression: exp.Create, locations: defaultdict) -> str:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-103150-postgres-dialect-create-type-fal/base-1/sqlglot/generator.py", "old_string": "    def createable_sql(self, expression: exp.Create, locations: defaultdict) -> str:", "new_string": "    def enumtype_sql(self, expression: exp.EnumType) -> str:\n        return f\"ENUM ({self.expressions(expression, flat=True)})\"\n\n    def createable_sql(self, expression: exp.Create, locations: defaultdict) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-103150-postgres-dialect-create-type-fal/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now let me check the round-trips, including the composite form and a few edge cases.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nfrom sqlglot import parse_one, exp\nfor s in [\\\"CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')\\\",\n          'CREATE TYPE complex AS (r double precision, i double precision)',\n          'CREATE TYPE public.mood AS ENUM (\\'sad\\')',\n          'CREATE TYPE t',\n          'CREATE TYPE t AS RANGE (subtype = int4)',\n          'CREATE TABLE type (type INT)']:\n    e = parse_one(s, 'postgres')\n    print(type(e).__name__, '|', e.sql('postgres'))\n\" 2>&1"}
[tool_result] 'CREATE TYPE t' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE TYPE t AS RANGE (subtype = int4)' contains unsupported syntax. Falling back to parsing as a 'Command'.
Create | CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')
Create | CREATE TYPE complex AS (r DOUBLE PRECISION, i DOUBLE PRECISION)
Create | CREATE TYPE public.mood AS ENUM ('sad')
Command | CREATE TYPE t
Command | CREATE TYPE t AS RANGE (subtype = int4)
Create | CREATE TABLE type (type INT)
[assistant] Round-trips work, and `CREATE TYPE` without `AS` and the unsupported `RANGE` form still fall back to a Command. Now I'll add tests and run the suite.
[tool_use Bash] {"command": "grep -n \"    def test_\" tests/dialects/test_postgres.py | tail -3; tail -3 tests/dialects/test_postgres.py"}
[tool_result] 1788:    def test_begin_transaction(self):
1811:    def test_interval_span(self):
1833:    def test_postgres_create_trigger(self):
        self.validate_identity(
            'CREATE TRIGGER "MyTrigger" BEFORE INSERT ON "MyTable" FOR EACH ROW EXECUTE FUNCTION MYFUNCTION()'
        )
[tool_use Bash] {"command": "cat >> tests/dialects/test_postgres.py <<'EOF'\n\n    def test_create_type(self):\n        self.validate_identity(\"CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')\")\n        self.validate_identity(\"CREATE TYPE public.mood AS ENUM ('sad', 'ok', 'happy')\")\n        self.validate_identity(\"CREATE TYPE complex AS (r DOUBLE PRECISION, i DOUBLE PRECISION)\")\n\n        self.ass
…[33 chars elided]…
TYPE t AS ENUM ('a')\", read=\"postgres\"), exp.Create)\n        self.assertIsInstance(parse_one(\"CREATE TYPE t AS (a INT)\", read=\"postgres\"), exp.Create)\n        self.assertIsInstance(\n            parse_one(\"CREATE TYPE t AS RANGE (subtype = int4)\", read=\"postgres\"), exp.Command\n        )\nEOF\ngrep -n \"^from sqlglot import\\|^from sqlglot\" tests/dialects/test_postgres.py | head -3"}
[tool_result] 1:from sqlglot import ParseError, UnsupportedError, exp, transpile
2:from sqlglot.helper import logger as helper_logger
[tool_use Bash] {"command": "sed -i '1s/.*/from sqlglot import ParseError, UnsupportedError, exp, parse_one, transpile/' tests/dialects/test_postgres.py && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5"}
[tool_result] sed: 2: "tests/dialects/test_pos ...": undefined label 'ests/dialects/test_postgres.py'

tests/dialects/test_postgres.py:1892: NameError
=========================== short test summary info ============================
FAILED tests/dialects/test_postgres.py::TestPostgres::test_create_type - Name...
1 failed, 1105 passed, 17982 subtests passed in 59.54s
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-103150-postgres-dialect-create-type-fal/base-1/tests/dialects/test_postgres.py", "old_string": "from sqlglot import ParseError, UnsupportedError, exp, transpile\n", "new_string": "from sqlglot import ParseError, UnsupportedError, exp, parse_one, transpile\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-103150-postgres-dialect-create-type-fal/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff check sqlglot tests/dialects/test_postgres.py 2>&1 | tail -2; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot tests/dialects/test_postgres.py 2>&1 | tail -2; git status --short"}
[tool_result] ............................................................. [ 98%]
.....................                                                                 [100%]
1106 passed, 17982 subtests passed in 57.91s
All checks passed!
176 files already formatted
 M sqlglot/expressions/ddl.py
 M sqlglot/generator.py
 M sqlglot/parsers/postgres.py
 M tests/dialects/test_postgres.py
[assistant] The full suite passes and ruff is clean. I'll also run mypy, since the project's pre-commit includes it.
[tool_use Bash] {"command": "timeout 300 <work>/env-sqlglot/bin/python -m mypy sqlglot/parsers/postgres.py sqlglot/expressions/ddl.py sqlglot/generator.py 2>&1 | tail -3"}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m mypy sqlglot/parsers/postgres.py sqlglot/expressions/ddl.py sqlglot/generator.py 2>&1 | tail -3"}
[tool_result] Success: no issues found in 3 source files
[assistant] `CREATE TYPE` now parses into a real `Create` node in the Postgres dialect for both enum and composite types, and round-trips unchanged. The full test suite passes (1106 tests), and ruff and mypy are clean.

```python
parse_one("CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')", "postgres").sql("postgres")
# "CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')"
```

Composite types also round-trip; their attribute types get uppercased, as sqlglot does elsewhere (`r DOUBLE PRECISION`).

**Changes:**
- **`sqlglot/parsers/postgres.py`**: a `_parse_create` override that handles `CREATE 
…[231 chars elided]…
EnumType` expression holding the enum labels.
- **`sqlglot/generator.py`**: `enumtype_sql`, which emits `ENUM (...)`.
- **`tests/dialects/test_postgres.py`**: a `test_create_type` covering both forms, the schema-qualified name, and the fallback cases. I only added the `parse_one` import; no existing test was touched.

**Choices I made:**
- I scoped the parsing to Postgres rather than the base parser, so other dialects that already fall back on `CREATE TYPE` are unchanged.
- `TYPE` is not a keyword token, so I match it by text. Columns named `type` are unaffected, which the test suite confirms.
