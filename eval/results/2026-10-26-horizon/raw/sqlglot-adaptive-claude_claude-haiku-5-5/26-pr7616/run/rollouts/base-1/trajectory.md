# trajectory base-1

final message:
`CREATE TYPE` now parses into a real AST for enum and composite types in the Postgres dialect, and round-trips. The full suite passes (1106 tests) and ruff lint and format are clean. I haven't committed anything.

```python
parse_one("CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')", "postgres").sql("postgres")
# "CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')"
```

Changes:
- **`sqlglot/parsers/postgres.py`**: a `_parse_create` override handles `CREATE TYPE`. It returns a `Create` with `kind="TYPE"`, and falls back to `Command` for anything it doesn't recognise. Other `CREATE` statements go to the base parser.
- **`sqlglot/expressions/ddl.py`**: a new `EnumType` expression holding the labels.
- **`sqlglot/generators/postgres.py`**: `enumtype_sql` renders `ENUM (...)`.
- **`tests/dialects/test_postgres.py`**: `test_create_type` covers enum, empty enum, composite with a schema-qualified name, and a shell type.

Choices I made that you may want to change:
- Composite types reuse the existing `Schema` of column definitions, so `AS (attr type, ...)` needs no new node.
- An empty enum (`AS ENUM ()`) is accepted, since Postgres allows it.
- `CREATE TYPE ... AS RANGE (...)` and other forms still fall back to `Command`. The request only asked for enum and composite.

## events
[tool_use Bash] {"command": "git status --short | head && ls sqlglot/parsers/ | head -50 && grep -rn \"TYPE\" sqlglot/parsers/postgres.py | head -40 && grep -rn \"ENUM\\|enum\" sqlglot/parser.py sqlglot/parsers/postgres.py sqlglot/generators/postgres.py | head -40", "description": "Inspect repo state and Postgres parser for TYPE/ENUM handling"}
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
sqlglot/parsers/postgres.py:57:            if last.is_type(*exp.DataType.TEXT_TYPES):
sqlglot/parsers/postgres.py:187:    JSON_ARROWS_REQUI
…[658 chars elided]…
r = {
sqlglot/parser.py:460:        TokenType.ENUM,
sqlglot/parser.py:461:        TokenType.ENUM8,
sqlglot/parser.py:462:        TokenType.ENUM16,
sqlglot/parser.py:586:        *ENUM_TYPE_TOKENS,
sqlglot/parser.py:2142:        for i, token in enumerate(raw_tokens):
sqlglot/parser.py:4063:        for i, join in enumerate(this.args.get("joins") or []):
sqlglot/parser.py:6199:            elif type_token in self.ENUM_TYPE_TOKENS:
sqlglot/parser.py:6933:        for index, e in enumerate(expressions):
[tool_use Bash] {"command": "grep -n \"_parse_create\\b\\|def _parse_create\" sqlglot/parser.py | head && grep -n \"CREATABLES\\|\\\"TYPE\\\"\\|TYPE\" sqlglot/parser.py | head -40 && grep -n \"class Create\\b\" -A 40 sqlglot/expressions/*.py | head -60", "description": "Find CREATE parsing and Create expression definitions"}
[tool_result] 1088:        TokenType.CREATE: lambda self: self._parse_create(),
2344:    def _parse_create(self) -> exp.Create | exp.Command:
3280:    def _parse_create_like(self) -> exp.LikeProperty | None:
27:if t.TYPE_CHECKING:
39:OPTIONS_TYPE = dict[str, Sequence[t.Union[Sequence[str], str]]]
367:            is_string=dialect.UUID_IS_STRING_TYPE or None
423:        "UUID": lambda args, dialect: exp.Uuid(is_string=dialect.UUID_IS_STRING_TYPE or None),
427:            is_string=dialect.UUID_IS_STRING_TYPE o
…[3513 chars elided]…
 "cache": False,
sqlglot/expressions/ddl.py-70-        "start": False,
sqlglot/expressions/ddl.py-71-        "owned": False,
sqlglot/expressions/ddl.py-72-        "options": False,
sqlglot/expressions/ddl.py-73-    }
sqlglot/expressions/ddl.py-74-
sqlglot/expressions/ddl.py-75-
sqlglot/expressions/ddl.py-76-class TriggerProperties(Expression):
sqlglot/expressions/ddl.py-77-    arg_types = {
sqlglot/expressions/ddl.py-78-        "table": True,
sqlglot/expressions/ddl.py-79-        "timing": True,
[tool_use Bash] {"command": "sed -n 2344,2480p sqlglot/parser.py && sed -n 615,650p sqlglot/parser.py", "description": "Read the _parse_create implementation and creatable sets"}
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
…[5706 chars elided]…
OURCE,
        TokenType.STAGE,
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
        *DB_CREATABLES,
    }

    TRIGGER_EVENTS: t.ClassVar = {
[tool_use Bash] {"command": "grep -n \"TYPE\" sqlglot/parsers/postgres.py | head; grep -rn \"CREATE TYPE\\|create type\" tests/ | head -20; grep -n \"class Type\\b\\|class Enum\\|class CompositeType\\|EnumType\" sqlglot/expressions/*.py | head", "description": "Look for existing CREATE TYPE tests and expression classes"}
[tool_result] 57:            if last.is_type(*exp.DataType.TEXT_TYPES):
187:    JSON_ARROWS_REQUIRE_JSON_TYPE = True
193:                exp.JSONExtract, arrow_req_json_type=self.JSON_ARROWS_REQUIRE_JSON_TYPE
198:                exp.JSONExtractScalar, arrow_req_json_type=self.JSON_ARROWS_REQUIRE_JSON_TYPE
210:        - MODE TYPE      -> keyword is identifier (e.g., "out INT")
211:        - MODE NAME TYPE -> keyword is mode (e.g., "OUT x INT")
221:        # Check Pattern 1: MODE TYPE
234:        # Check Pattern 2: MODE NAME TYPE
[tool_use Bash] {"command": "sed -n 2480,2600p sqlglot/parser.py; grep -n '\"TYPE\"\\|TokenType.TYPE\\|ENUM' sqlglot/tokens.py | head; grep -n \"def _parse_as_command\" -A3 sqlglot/parser.py | head", "description": "Read rest of _parse_create and token definitions for TYPE"}
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
…[4092 chars elided]…
._match_text_seq("INCREMENT"):
                self._match_text_seq("BY")
                self._match_text_seq("=")
                seq.set("increment", self._parse_term())
            elif self._match_text_seq("MINVALUE"):
                seq.set("minvalue", self._parse_term())
288:        "ENUM": TokenType.ENUM,
9114:    def _parse_as_command(self, start: Token) -> exp.Command:
9115-        while self._curr:
9116-            self._advance()
9117-        text = self._find_sql(start, self._prev)
[tool_use Bash] {"command": "grep -rn \"def _parse_create\\b\" sqlglot/ ; grep -n \"def create_sql\" -A60 sqlglot/generator.py | head -90; grep -rn \"class .*Enum\\w*(Expression\\|class .*Enum\\w*(Func\" sqlglot/expressions/ | head; grep -n \"ENUM\" sqlglot/generators/postgres.py sqlglot/generator.py | head", "description": "Find _parse_create overrides, create_sql, and Enum expression classes"}
[tool_result] sqlglot/parser.py:2344:    def _parse_create(self) -> exp.Create | exp.Command:
sqlglot/parsers/fabric.py:8:    def _parse_create(self) -> exp.Create | exp.Command:
sqlglot/parsers/snowflake.py:1004:    def _parse_create(self) -> exp.Create | exp.Command:
sqlglot/parsers/tsql.py:664:    def _parse_create(self) -> exp.Create | exp.Command:
sqlglot/parsers/starrocks.py:61:    def _parse_create(self) -> exp.Create | exp.Command:
1284:    def create_sql(self, expression: exp.Create) -> str:
1285-   
…[2440 chars elided]…
      )
1337-                postalias_props_sql = f" {postalias_props_sql}" if postalias_props_sql else ""
1338-                expression_sql = f" AS{postalias_props_sql}{expression_sql}"
1339-
1340-        postindex_props_sql = ""
1341-        if properties_locs.get(exp.Properties.Location.POST_INDEX):
1342-            postindex_props_sql = self.properties(
1343-                exp.Properties(expressions=properties_locs[exp.Properties.Location.POST_INDEX]),
1344-                wrapped=False,
[tool_use Bash] {"command": "sed -n 55,80p sqlglot/parsers/starrocks.py; sed -n 1,40p sqlglot/parsers/postgres.py; grep -n \"class Parser\\|STATEMENT_PARSERS\\|def _parse_\" sqlglot/parsers/postgres.py | head -40; grep -n \"class Generator\" -A5 sqlglot/generators/postgres.py | head; grep -n \"def \\w*_sql\" sqlglot/generators/postgres.py | head -80", "description": "Study starrocks create override and postgres parser/generator layout"}
[tool_result]             )

        return self.expression(
            exp.RollupProperty(expressions=self._parse_wrapped_csv(parse_rollup_index))
        )

    def _parse_create(self) -> exp.Create | exp.Command:
        create = super()._parse_create()

        # Starrocks' primary key is defined outside of the schema, so we need to move it there
        # https://docs.starrocks.io/docs/table_design/table_types/primary_key_table/#usage
        if isinstance(create, exp.Create) and isinstance(create.this,
…[3990 chars elided]…
-> str:
511:    def isascii_sql(self, expression: exp.IsAscii) -> str:
514:    def ignorenulls_sql(self, expression: exp.IgnoreNulls) -> str:
519:    def respectnulls_sql(self, expression: exp.RespectNulls) -> str:
525:    def currentschema_sql(self, expression: exp.CurrentSchema) -> str:
528:    def interval_sql(self, expression: exp.Interval) -> str:
538:    def placeholder_sql(self, expression: exp.Placeholder) -> str:
545:    def arraycontains_sql(self, expression: exp.ArrayContains) -> str:
[tool_use Bash] {"command": "sed -n 330,360p sqlglot/parsers/postgres.py; grep -n \"^class \\|^from\\|^import\" sqlglot/expressions/ddl.py | head -40; sed -n 395,425p sqlglot/generators/postgres.py; grep -n \"CREATABLE_KIND_MAPPING\" -A6 sqlglot/dialects/dialect.py | head -20; ls <work>/env-sqlglot/bin/python 2>&1", "description": "Read postgres parser tail, ddl.py structure, and test env path"}
[tool_result]         if self._match_text_seq("STORED"):
            this = self.expression(exp.ComputedColumnConstraint(this=this.expression))

        return this

    def _parse_user_defined_type(self, identifier: exp.Identifier) -> exp.Expr | None:
        udt_type: exp.Identifier | exp.Dot = identifier

        while self._match(TokenType.DOT):
            part = self._parse_id_var()
            if part:
                udt_type = exp.Dot(this=udt_type, expression=part)

        return exp.DataType.build
…[3371 chars elided]…
 """
687-    Helper for dialects that use a different name for the same creatable kind. For example, the Clickhouse
688-    equivalent of CREATE SCHEMA is CREATE DATABASE.
689-    """
690-
691-    ALTER_TABLE_SUPPORTS_CASCADE = False
--
775:    INVERSE_CREATABLE_KIND_MAPPING: dict[str, str] = {}
776-
777-    ESCAPED_SEQUENCES: dict[str, str] = {}
<work>/env-sqlglot/bin/python
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-203309-postgres-dialect-create-type-fal/base-1/sqlglot/expressions/ddl.py", "old_string": "class SequenceProperties(Expression):", "new_string": "class EnumType(Expression):\n    arg_types = {\"expressions\": True}\n\n\nclass SequenceProperties(Expression):"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-203309-postgres-dialect-create-type-fal/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-203309-postgres-dialect-create-type-fal/base-1/sqlglot/parsers/postgres.py", "old_string": "    def _parse_user_defined_type(self, identifier: exp.Identifier) -> exp.Expr | None:", "new_string": "    def _parse_create(self) -> exp.Create | exp.Command:\n        start = self._prev\n\n        if not se
…[453 chars elided]…
vance=False):\n                expression = self._parse_schema()\n            else:\n                return self._parse_as_command(start)\n\n        if self._curr:\n            return self._parse_as_command(start)\n\n        return self.expression(exp.Create(this=this, kind=\"TYPE\", expression=expression))\n\n    def _parse_user_defined_type(self, identifier: exp.Identifier) -> exp.Expr | None:"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-203309-postgres-dialect-create-type-fal/base-1/sqlglot/parsers/postgres.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-203309-postgres-dialect-create-type-fal/base-1/sqlglot/generators/postgres.py", "old_string": "    def schemacommentproperty_sql(self, expression: exp.SchemaCommentProperty) -> str:", "new_string": "    def enumtype_sql(self, expression: exp.EnumType) -> str:\n        return f\"ENUM ({self.expressions(expression, flat=True)})\"\n\n    def schemacommentproperty_sql(self, expression: exp.SchemaCommentProperty) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-203309-postgres-dialect-create-type-fal/base-1/sqlglot/generators/postgres.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nfrom sqlglot import parse_one, exp\nfor s in [\n \\\"CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')\\\",\n 'CREATE TYPE public.complex AS (r double precision, i double precision)',\n 'CREATE TYPE foo',\n 'CREATE TYPE foo AS RANGE (subtype = float8)',\n 'CREATE TYPE foo AS (a INT, b TEXT)',\n 'CREATE TYPE e AS ENUM ()',\n]:\n    e = parse_one(s, 'postgres')\n    print(type(e).__name__, '|', e.sql('postgres'))\nprint(repr(parse_one(\\\"CREATE TYPE book_type AS ENUM ('A')\\\", 'postgres')))\n\" 2>&1 | head -60", "description": "Smoke-test CREATE TYPE parsing and round-tripping in Postgres"}
[tool_result] 'CREATE TYPE foo AS RANGE (subtype = float8)' contains unsupported syntax. Falling back to parsing as a 'Command'.
Traceback (most recent call last):
  File "<string>", line 11, in <module>
  File "~/.cache/lithify/work/repo-161bf5b46800/20261026-203309-postgres-dialect-create-type-fal/base-1/sqlglot/__init__.py", line 160, in parse_one
    result = dialect.parse(sql, **opts)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-161bf5b46800/2026102
…[2425 chars elided]…
e-1/sqlglot/parser.py", line 1991, in raise_error
    raise error
sqlglot.errors.ParseError: Required keyword: 'expressions' missing for <class 'sqlglot.expressions.ddl.EnumType'>. Line 1, Col: 24.
  CREATE TYPE e AS ENUM ([4m)[0m
Create | CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')
Create | CREATE TYPE public.complex AS (r DOUBLE PRECISION, i DOUBLE PRECISION)
Create | CREATE TYPE foo
Command | CREATE TYPE foo AS RANGE (subtype = float8)
Create | CREATE TYPE foo AS (a INT, b TEXT)
[tool_use Bash] {"command": "sed -i 's/class EnumType(Expression):\\n    arg_types = {\"expressions\": True}//' sqlglot/expressions/ddl.py && python3 - <<'EOF'\nimport re\np='sqlglot/expressions/ddl.py'\ns=open(p).read()\ns=s.replace('class EnumType(Expression):\\n    arg_types = {\"expressions\": True}','class EnumType(Expression):\\n    arg_types = {\"expressions\": False}',1)\nopen(p,'w').write(s)\nEOF\nPY=/pr
…[266 chars elided]…
N')\\\",\n 'CREATE TYPE public.complex AS (r double precision, i double precision)',\n 'CREATE TYPE foo',\n 'CREATE TYPE e AS ENUM ()',\n]:\n    e = parse_one(s, 'postgres')\n    print(type(e).__name__, '|', e.sql('postgres'))\nprint(repr(parse_one(\\\"CREATE TYPE book_type AS ENUM ('A')\\\", 'postgres')))\n\" 2>&1 | head -30", "description": "Relax EnumType arg and re-run round-trip smoke tests"}
[tool_result] sed: 1: "sqlglot/expressions/ddl ...": unterminated substitute pattern
Traceback (most recent call last):
  File "<string>", line 9, in <module>
  File "~/.cache/lithify/work/repo-161bf5b46800/20261026-203309-postgres-dialect-create-type-fal/base-1/sqlglot/__init__.py", line 160, in parse_one
    result = dialect.parse(sql, **opts)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-161bf5b46800/20261026-203309-postgres-dialect-create-type-fal/bas
…[1730 chars elided]…
    expression = self.expression(
                 ^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-161bf5b46800/20261026-203309-postgres-dialect-create-type-fal/base-1/sqlglot/parser.py", line 2095, in expression
    instance = self.validate_expression(instance)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-161bf5b46800/20261026-203309-postgres-dialect-create-type-fal/base-1/sqlglot/parser.py", line 2002, in validate_expression
[assistant] My stray `sed` was a no-op mistake; the Python replacement is what I want. I'll apply it on its own and re-run.
[tool_use Bash] {"command": "python3 -c \"\np='sqlglot/expressions/ddl.py'\ns=open(p).read()\ns=s.replace('class EnumType(Expression):\\n    arg_types = {\\\"expressions\\\": True}','class EnumType(Expression):\\n    arg_types = {\\\"expressions\\\": False}',1)\nopen(p,'w').write(s)\n\" && grep -n \"class EnumType\" -A2 sqlglot/expressions/ddl.py && PY=/private/tmp/claude-501/-Users-user-Coding-delvera-foundat
…[115 chars elided]…
 import parse_one\nfor s in [\n \\\"CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')\\\",\n 'CREATE TYPE public.complex AS (r double precision, i double precision)',\n 'CREATE TYPE foo',\n 'CREATE TYPE e AS ENUM ()',\n]:\n    e = parse_one(s, 'postgres')\n    print(type(e).__name__, '|', e.sql('postgres'))\n\" 2>&1 | tail -12", "description": "Apply EnumType arg fix and re-run smoke tests"}
[tool_result] 64:class EnumType(Expression):
65-    arg_types = {"expressions": False}
66-
Create | CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')
Create | CREATE TYPE public.complex AS (r DOUBLE PRECISION, i DOUBLE PRECISION)
Create | CREATE TYPE foo
Create | CREATE TYPE e AS ENUM ()
[assistant] Round-trips work. The ddl.py note is just my own edit landing, but I'll confirm the file state before running the suite and adding tests.
[tool_use Bash] {"command": "git diff --stat && grep -n \"def test_ddl\" -A12 tests/dialects/test_postgres.py | head -30", "description": "Check diff stat and find DDL test location in postgres tests"}
[tool_result]  sqlglot/expressions/ddl.py     |  4 ++++
 sqlglot/generators/postgres.py |  3 +++
 sqlglot/parsers/postgres.py    | 24 ++++++++++++++++++++++++
 3 files changed, 31 insertions(+)
1087:    def test_ddl(self):
1088-        # Checks that user-defined types are parsed into DataType instead of Identifier
1089-        self.parse_one("CREATE TABLE t (a udt)").this.expressions[0].args["kind"].assert_is(
1090-            exp.DataType
1091-        )
1092-
1093-        # Checks that OID is parsed into a DataType (ObjectIdentifier)
1094-        self.assertIsInstance(
1095-            self.parse_one("CREATE TABLE p.t (c oid)").find(exp.DataType), exp.ObjectIdentifier
1096-        )
1097-
1098-        expr = self.parse_one("CREATE TABLE t (x INTERVAL day)")
1099-        cdef = expr.find(exp.ColumnDef)
[tool_use Bash] {"command": "python3 -c \"\np='tests/dialects/test_postgres.py'\ns=open(p).read()\nanchor='    def test_ddl(self):\\n'\nnew='''    def test_create_type(self):\n        self.validate_identity(\"CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')\")\n        self.validate_identity(\"CREATE TYPE empty_enum AS ENUM ()\")\n        self.validate_identity(\"CREATE TYPE public.complex AS (r DOUBLE PRE
…[135 chars elided]…
ce(anchor,new+anchor,1)\nopen(p,'w').write(s)\n\" && PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py -k create_type 2>&1 | tail -15", "description": "Add CREATE TYPE tests to postgres dialect tests and run them"}
[tool_result ERROR] Exit code 1
(eval):1: no matches found: (FICTION, NONFICTION))\n        self.validate_identity(CREATE
[assistant] The shell choked on the parentheses inside the inline script, so nothing was written. I'll make the edit with the Edit tool instead.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-203309-postgres-dialect-create-type-fal/base-1/tests/dialects/test_postgres.py", "old_string": "    def test_ddl(self):\n        # Checks that user-defined types are parsed into DataType instead of Identifier", "new_string": "    def test_create_type(self):\n        self.validate_identity(\"CREATE TY
…[30 chars elided]…
', 'NONFICTION')\")\n        self.validate_identity(\"CREATE TYPE empty_enum AS ENUM ()\")\n        self.validate_identity(\n            \"CREATE TYPE public.complex AS (r DOUBLE PRECISION, i DOUBLE PRECISION)\"\n        )\n        self.validate_identity(\"CREATE TYPE shell_type\")\n\n    def test_ddl(self):\n        # Checks that user-defined types are parsed into DataType instead of Identifier"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-203309-postgres-dialect-create-type-fal/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py -k create_type 2>&1 | tail -5; $PY -m pytest -q -p no:cacheprovider --color=no tests/ 2>&1 | tail -15", "description": "Run new CREATE TYPE test, then full test suite"}
[tool_result] .                                                                        [100%]
1 passed, 25 deselected in 0.10s
............................................................................................ [ 30%]
.......................... [ 32%]
.......................................... [ 36%]
..................................................................................................................................................................................................... [ 53%
…[199 chars elided]…
........................................... [ 73%]
............................................................................................................. [ 83%]
............................................ [ 87%]
........................... [ 89%]
............................... [ 92%]
............................................................. [ 98%]
.....................                                                                 [100%]
1106 passed, 17982 subtests passed in 48.93s
[assistant] The full suite passes (1106 tests). Next, lint and format the changed files.
[tool_use Bash] {"command": "(ruff --version && ruff check sqlglot/parsers/postgres.py sqlglot/generators/postgres.py sqlglot/expressions/ddl.py tests/dialects/test_postgres.py && ruff format --check sqlglot/parsers/postgres.py sqlglot/generators/postgres.py sqlglot/expressions/ddl.py tests/dialects/test_postgres.py) 2>&1 | tail -8; git diff --stat", "description": "Run ruff lint and format check on changed files"}
[tool_result] ruff 0.15.6
All checks passed!
4 files already formatted
 sqlglot/expressions/ddl.py      |  4 ++++
 sqlglot/generators/postgres.py  |  3 +++
 sqlglot/parsers/postgres.py     | 24 ++++++++++++++++++++++++
 tests/dialects/test_postgres.py |  8 ++++++++
 4 files changed, 39 insertions(+)
[assistant] `CREATE TYPE` now parses into a real AST for enum and composite types in the Postgres dialect, and round-trips. The full suite passes (1106 tests) and ruff lint and format are clean. I haven't committed anything.

```python
parse_one("CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')", "postgres").sql("postgres")
# "CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')"
```

Changes:
- **`sqlglot/parsers/postgres.py`**: a `_parse_create` override handles `CREATE TYPE`. It returns a `Create` with `kind="TYPE"`, and falls back to `Command` for anything it doesn't recognise. Other `CREATE
…[95 chars elided]…
sion holding the labels.
- **`sqlglot/generators/postgres.py`**: `enumtype_sql` renders `ENUM (...)`.
- **`tests/dialects/test_postgres.py`**: `test_create_type` covers enum, empty enum, composite with a schema-qualified name, and a shell type.

Choices I made that you may want to change:
- Composite types reuse the existing `Schema` of column definitions, so `AS (attr type, ...)` needs no new node.
- An empty enum (`AS ENUM ()`) is accepted, since Postgres allows it.
- `CREATE TYPE ... AS RANGE (...)` and other forms still fall back to `Command`. The request only asked for enum and composite.
