# trajectory base-1

final message:
`CREATE TYPE` now parses into a real AST node for enum and composite types, and both round-trip in Postgres. The full suite passed after my last edit: `SUMMARY: 1106 passed, 17982 subtests passed in 60.06s (0:01:00)`, `EXIT: 0`. I haven't committed anything.

```python
parse_one("CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')", "postgres").sql("postgres")
# "CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')"
```

**What changed**
- `sqlglot/parsers/postgres.py`: a `_parse_create` override. It claims `CREATE TYPE` and hands every other `CREATE` to the base parser. It produces `exp.Create(kind="TYPE")`:
  - Enum: `expression` is an `exp.DataType` of `DType.ENUM` holding the string literals.
  - Composite: `this` is an `exp.Schema` whose expressions are `ColumnDef`s.
  - Anything else (shell types, `AS RANGE (...)`, trailing tokens) still falls back to `exp.Command`, as before.
- `sqlglot/generators/postgres.py`: a `create_sql` override that emits `AS ENUM (...)` or `AS (...)` for `kind == "TYPE"` and defers to the base generator otherwise.
- `tests/dialects/test_postgres.py`: a new `test_create_type` covering round-trips and AST shape (kind, node types, enum values, attribute names). I kept the existing `test_datatype` as its own method.

**Limitations**
- Other dialects: the enum output is valid for DuckDB, but the composite output (`CREATE TYPE c (a INT, b TEXT)`) isn't valid DuckDB or MySQL. DuckDB would need `AS STRUCT(...)`. I didn't add that because the task is Postgres round-trip. Before this change, those statements passed through as raw Postgres text, which was also invalid in those engines, so this isn't a regression in validity. Say if you want the cross-dialect output handled.
- Composite `FLOAT` attributes print as `DOUBLE PRECISION`. That's the existing Postgres generator behaviour for `FLOAT`, and it's equivalent in Postgres.

## events
[assistant] I'll start by finding the current `CREATE` handling in the Postgres parser and how the base parser treats `TYPE`.
[tool_use Bash] {"command": "git status --short | head && cat .lithify/memory.md 2>/dev/null | head -30; grep -n \"TYPE\\|ENUM\" sqlglot/parsers/postgres.py | head -40; grep -n \"_parse_create\\b\\|def _parse_create\" sqlglot/parser.py | head; grep -n \"CREATE TYPE\\|enum\\|ENUM\" tests/dialects/test_postgres.py | head -20"}
[tool_result] 57:            if last.is_type(*exp.DataType.TEXT_TYPES):
187:    JSON_ARROWS_REQUIRE_JSON_TYPE = True
193:                exp.JSONExtract, arrow_req_json_type=self.JSON_ARROWS_REQUIRE_JSON_TYPE
198:                exp.JSONExtractScalar, arrow_req_json_type=self.JSON_ARROWS_REQUIRE_JSON_TYPE
210:        - MODE TYPE      -> keyword is identifier (e.g., "out INT")
211:        - MODE NAME TYPE -> keyword is mode (e.g., "OUT x INT")
221:        # Check Pattern 1: MODE TYPE
234:        # Check Pattern 2: MODE NAME TYPE
1088:        TokenType.CREATE: lambda self: self._parse_create(),
2344:    def _parse_create(self) -> exp.Create | exp.Command:
3280:    def _parse_create_like(self) -> exp.LikeProperty | None:
[tool_use Bash] {"command": "sed -n 2344,2480p sqlglot/parser.py"}
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
…[4797 chars elided]…
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
[tool_use Bash] {"command": "sed -n 2480,2620p sqlglot/parser.py; grep -n \"CREATABLES\" sqlglot/parser.py | head -3; grep -rn \"TokenType.TYPE\\b\\|\\\"TYPE\\\"\" sqlglot/tokens.py sqlglot/parser.py sqlglot/dialects/postgres.py sqlglot/parsers/postgres.py | head"}
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
…[5098 chars elided]…
var_from_options(self.CREATE_SEQUENCE, raise_unmatched=False)
                if opt:
                    options.append(opt)
                else:
                    break

        seq.set("options", options if options else None)
        return None if self._index == index else seq
619:    DB_CREATABLES: t.ClassVar = {
639:    CREATABLES: t.ClassVar = {
647:        *DB_CREATABLES,
sqlglot/parser.py:1629:        "TYPE": ("EVOLUTION",),
sqlglot/parser.py:8627:        self._match_text_seq("TYPE")
[tool_use Bash] {"command": "sed -n 615,660p sqlglot/parser.py; grep -n \"CREATABLE_KIND_MAPPING\" -A4 sqlglot/dialects/*.py | head -20; grep -n \"TYPE\" sqlglot/tokens.py | head; grep -n \"class Create(\\|class ColumnDef\\|class DataType(\" -A3 sqlglot/expressions/*.py | head -30; grep -n \"def create_sql\" -A40 sqlglot/generators/base.py | head -80"}
[tool_result]         *Tokenizer.SINGLE_TOKENS.values(),
        TokenType.SELECT,
    } - {TokenType.IDENTIFIER}

    DB_CREATABLES: t.ClassVar = {
        TokenType.DATABASE,
        TokenType.DICTIONARY,
        TokenType.FILE_FORMAT,
        TokenType.MODEL,
        TokenType.NAMESPACE,
        TokenType.SCHEMA,
        TokenType.SEMANTIC_VIEW,
        TokenType.SEQUENCE,
        TokenType.SINK,
        TokenType.SOURCE,
        TokenType.STAGE,
        TokenType.STORAGE_INTEGRATION,
        TokenType.STR
…[2187 chars elided]…
expressions/ddl.py:39:class Create(Expression, DDL):
sqlglot/expressions/ddl.py-40-    arg_types = {
sqlglot/expressions/ddl.py-41-        "with_": False,
sqlglot/expressions/ddl.py-42-        "this": True,
sqlglot/expressions/query.py:502:class ColumnDef(Expression):
sqlglot/expressions/query.py-503-    arg_types = {
sqlglot/expressions/query.py-504-        "this": True,
sqlglot/expressions/query.py-505-        "kind": False,
ugrep: warning: sqlglot/generators/base.py: No such file or directory
[tool_use Bash] {"command": "sed -n 39,70p sqlglot/expressions/ddl.py; grep -rn \"def create_sql\" sqlglot/generators/ | head; grep -n \"TokenType.TYPE\\|\\\"TYPE\\\"\\|'TYPE'\" sqlglot/*.py sqlglot/parsers/*.py sqlglot/dialects/*.py | head"}
[tool_result] class Create(Expression, DDL):
    arg_types = {
        "with_": False,
        "this": True,
        "kind": True,
        "expression": False,
        "exists": False,
        "properties": False,
        "replace": False,
        "refresh": False,
        "unique": False,
        "indexes": False,
        "no_schema_binding": False,
        "begin": False,
        "clone": False,
        "concurrently": False,
        "clustered": False,
    }

    @property
    def kind(self) -> str | None:
…[621 chars elided]…
> str:
sqlglot/generators/starrocks.py:276:    def create_sql(self, expression: exp.Create) -> str:
sqlglot/parsers/tsql.py:98:            "TYPE",
sqlglot/parser.py:1629:        "TYPE": ("EVOLUTION",),
sqlglot/parser.py:8627:        self._match_text_seq("TYPE")
sqlglot/parsers/clickhouse.py:795:        index_type = self._match_text_seq("TYPE") and (self._parse_function() or self._parse_var())
sqlglot/parsers/hive.py:235:        if self.CHANGE_COLUMN_ALTER_SYNTAX and self._match_text_seq("TYPE"):
[assistant] The base `_parse_create` only dispatches on `CREATABLES` token types, and `TYPE` is a plain VAR token, so I'll need a Postgres-specific branch. Next I'm checking the existing ENUM and column-def helpers, and where the generator's `create_sql` lives.
[tool_use Bash] {"command": "ls sqlglot/generators | head -50; grep -rn \"Type.ENUM\" sqlglot/ | head -20; grep -n \"def _parse_column_def\\|def _parse_wrapped_csv\\|def _parse_table_parts\\|def _parse_as_command\\|def _parse_string\\b\" sqlglot/parser.py; grep -n \"def create_sql\" -A12 sqlglot/generator.py | head -30; grep -n \"def datatype_sql\" -A30 sqlglot/generator.py | head -50"}
[tool_result] __init__.py
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
sqlglot/tokens.py:288:        "ENUM": TokenType.ENUM,
sqlglot/parser.py:460:        TokenType.ENUM,
sqlglot/parser.py:461:        TokenTy
…[2254 chars elided]…
n, flat=True)
1703-        )
1704-
1705-        if type_value in self.UNSUPPORTED_TYPES:
1706-            self.unsupported(
1707-                f"Data type {type_value.value} is not supported when targeting {self.dialect.__class__.__name__}"
1708-            )
1709-
1710-        type_sql: t.Any = ""
1711-        if type_value == exp.DType.USERDEFINED and expression.args.get("kind"):
1712-            type_sql = self.sql(expression, "kind")
1713-        elif type_value == exp.DType.CHARACTER_SET:
[tool_use Bash] {"command": "sed -n 7060,7075p sqlglot/parser.py; sed -n 1,40p sqlglot/parsers/postgres.py; grep -n \"    def \\|^class \" sqlglot/parsers/postgres.py | head -60; grep -n \"^class \\|    def \\|TRANSFORMS = {\" sqlglot/generators/postgres.py | head -30; grep -n \"ENUM\" sqlglot/generators/postgres.py sqlglot/dialects/postgres.py"}
[tool_result]     def _parse_column_def(
        self, this: exp.Expr | None, computed_column: bool = True
    ) -> exp.Expr | None:
        # column defs are not really columns, they're identifiers
        if isinstance(this, exp.Column):
            this = this.this

        if not computed_column:
            self._match(TokenType.ALIAS)

        kind = self._parse_types(schema=True)

        if self._match_text_seq("FOR", "ORDINALITY"):
            return self.expression(exp.ColumnDef(this=this, ordinalit
…[3223 chars elided]…
-> str:
511:    def isascii_sql(self, expression: exp.IsAscii) -> str:
514:    def ignorenulls_sql(self, expression: exp.IgnoreNulls) -> str:
519:    def respectnulls_sql(self, expression: exp.RespectNulls) -> str:
525:    def currentschema_sql(self, expression: exp.CurrentSchema) -> str:
528:    def interval_sql(self, expression: exp.Interval) -> str:
538:    def placeholder_sql(self, expression: exp.Placeholder) -> str:
545:    def arraycontains_sql(self, expression: exp.ArrayContains) -> str:
[tool_use Bash] {"command": "sed -n 335,350p sqlglot/parsers/postgres.py; sed -n 400,420p sqlglot/generators/postgres.py; sed -n 477,490p sqlglot/generators/postgres.py; sed -n 1,12p sqlglot/generators/postgres.py; grep -n \"def _parse_as_command\" -A12 sqlglot/parser.py | head -20; grep -n \"class Create\\b\\|DType.ENUM\\|DDL\" sqlglot/expressions/ddl.py | head -5"}
[tool_result]     def _parse_user_defined_type(self, identifier: exp.Identifier) -> exp.Expr | None:
        udt_type: exp.Identifier | exp.Dot = identifier

        while self._match(TokenType.DOT):
            part = self._parse_id_var()
            if part:
                udt_type = exp.Dot(this=udt_type, expression=part)

        return exp.DataType.build(udt_type, udt=True)

    def schemacommentproperty_sql(self, expression: exp.SchemaCommentProperty) -> str:
        self.unsupported("Table comments ar
…[1890 chars elided]…
   self._advance()
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
1:"""sqlglot expressions DDL."""
16:class DDL(Selectable):
39:class Create(Expression, DDL):
[assistant] I have the shape of the change. Before writing it, I'm checking the generator's `wrap` helper and whether the parser already uses lambda-based `_parse_csv` calls.
[tool_use Bash] {"command": "grep -n \"    def wrap\\b\\|    def wrap(\" -A3 sqlglot/generator.py; grep -n \"_parse_wrapped_csv(lambda\\|_parse_csv(lambda\" sqlglot/parser.py sqlglot/parsers/*.py | head -3; grep -n \"_parse_wrapped_csv(\" sqlglot/parser.py | head -3; sed -n 8435,8445p sqlglot/parser.py; ls tests/dialects | grep postgres; grep -n \"CREATE TYPE\\|CREATE DOMAIN\" tests/dialects/test_postgres.py | head"}
[tool_result] 1024:    def wrap(self, expression: exp.Expr | str) -> str:
1025-        this_sql = (
1026-            self.sql(expression)
1027-            if isinstance(expression, exp.UNWRAPPED_QUERIES)
sqlglot/parsers/doris.py:110:        values = self._parse_csv(lambda: self._parse_wrapped_csv(self._parse_expression))
sqlglot/parser.py:1419:        args = self._parse_wrapped_csv(lambda: self._parse_primary() or self._parse_column())
sqlglot/parser.py:3613:                and self._parse_csv(lambda: self._p
…[240 chars elided]…
.TransformModelProperty(expressions=self._parse_wrapped_csv(self._parse_expression))
    def _parse_wrapped_csv(
        self,
        parse_method: t.Callable[[], T | None],
        sep: TokenType = TokenType.COMMA,
        optional: bool = False,
    ) -> list[T]:
        return self._parse_wrapped(
            lambda: self._parse_csv(parse_method, sep=sep), optional=optional
        )

    def _parse_wrapped(self, parse_method: t.Callable[[], T], optional: bool = False) -> T:
test_postgres.py
[tool_use Bash] {"command": "sed -n 346,360p sqlglot/parsers/postgres.py; sed -n 545,560p sqlglot/generators/postgres.py; wc -l sqlglot/generators/postgres.py"}
[tool_result]     def arraycontains_sql(self, expression: exp.ArrayContains) -> str:
        # Convert DuckDB's LIST_CONTAINS(array, value) to PostgreSQL
        # DuckDB behavior:
        #   - LIST_CONTAINS([1,2,3], 2) -> true
        #   - LIST_CONTAINS([1,2,3], 4) -> false
        #   - LIST_CONTAINS([1,2,NULL], 4) -> false (not NULL)
        #   - LIST_CONTAINS([1,2,3], NULL) -> NULL
        #
        # PostgreSQL equivalent: CASE WHEN value IS NULL THEN NULL
        #                            ELSE COALESCE(value = ANY(array), FALSE) END
        value = expression.expression
        array = expression.this

        coalesce_expr = exp.Coalesce(
            this=value.eq(exp.Any(this=exp.paren(expression=array, copy=False))),
            expressions=[exp.false()],
     569 sqlglot/generators/postgres.py
[assistant] Now the parser change: a `_parse_create` override that claims `CREATE TYPE` and defers everything else to the base class.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-005847-postgres-dialect-create-type-fal/base-1/sqlglot/parsers/postgres.py", "old_string": "        return exp.DataType.build(udt_type, udt=True)\n", "new_string": "        return exp.DataType.build(udt_type, udt=True)\n\n    def _parse_create(self) -> exp.Create | exp.Command:\n        start = self.
…[731 chars elided]…
   lambda: self._parse_column_def(self._parse_id_var())\n            )\n            this = exp.Schema(this=this, expressions=attributes)\n        else:\n            return self._parse_as_command(start)\n\n        if self._curr:\n            return self._parse_as_command(start)\n\n        return self.expression(\n            exp.Create(this=this, kind=\"TYPE\", expression=expression)\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-005847-postgres-dialect-create-type-fal/base-1/sqlglot/parsers/postgres.py has been updated successfully.
[assistant] The `expression` annotation is wrong: only the enum branch sets it, so it should be `DataType | None`. Fixing that, then the generator.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-005847-postgres-dialect-create-type-fal/base-1/sqlglot/parsers/postgres.py", "old_string": "        expression: exp.DataType | exp.Schema | None = None", "new_string": "        expression: exp.DataType | None = None"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-005847-postgres-dialect-create-type-fal/base-1/sqlglot/parsers/postgres.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-005847-postgres-dialect-create-type-fal/base-1/sqlglot/generators/postgres.py", "old_string": "    def cast_sql(self, expression: exp.Cast, safe_prefix: str | None = None) -> str:", "new_string": "    def create_sql(self, expression: exp.Create) -> str:\n        if expression.kind != \"TYPE\":\n     
…[108 chars elided]…
exp.Schema):\n            attributes = self.wrap(self.expressions(this, flat=True))\n            return f\"CREATE TYPE {self.sql(this, 'this')} AS {attributes}\"\n\n        values = self.wrap(self.expressions(expression.expression, flat=True))\n        return f\"CREATE TYPE {self.sql(this)} AS ENUM {values}\"\n\n    def cast_sql(self, expression: exp.Cast, safe_prefix: str | None = None) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-005847-postgres-dialect-create-type-fal/base-1/sqlglot/generators/postgres.py has been updated successfully.
[assistant] Now a probe of the parse tree and round-trip, using the project's Python env from the harness notes.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls $PY && cat > /tmp/probe_ct.py <<'EOF'\nfrom sqlglot import parse_one, exp\nfor sql in [\n    \"CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')\",\n    \"CREATE TYPE book_type AS ENUM ()\",\n    \"CREATE TYPE public.compl
…[355 chars elided]…
e, exp.Create):\n        print(\"   this:\", type(e.this).__name__, \"| kind:\", e.kind, \"| expr:\", repr(e.expression)[:120])\nfor sql in [\"CREATE TYPE book_type AS ENUM ('a')\", \"CREATE TYPE c AS (a INT, b TEXT)\"]:\n    print(\"duckdb:\", parse_one(sql, \"postgres\").sql(\"duckdb\"))\n    print(\"mysql:\", parse_one(sql, \"postgres\").sql(\"mysql\"))\nEOF\nPYTHONPATH=. $PY /tmp/probe_ct.py"}
[tool_result] <work>/env-sqlglot/bin/python
'CREATE TYPE shell_t' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE TYPE range_t AS RANGE (subtype = int4)' contains unsupported syntax. Falling back to parsing as a 'Command'.
Create | CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')
   this: Table | kind: TYPE | expr: DataType(
  this=DType.ENUM,
  expressi
…[242 chars elided]…
ON, i DOUBLE PRECISION)
   this: Schema | kind: TYPE | expr: None
Create | CREATE TYPE complex AS (r DOUBLE PRECISION COLLATE "C", i INT)
   this: Schema | kind: TYPE | expr: None
Command | CREATE TYPE shell_t
Command | CREATE TYPE range_t AS RANGE (subtype = int4)
Create | CREATE TABLE t (a INT)
   this: Schema | kind: TABLE | expr: None
duckdb: CREATE TYPE book_type AS ENUM('a')
mysql: CREATE TYPE book_type AS ENUM('a')
duckdb: CREATE TYPE c (a INT, b TEXT)
mysql: CREATE TYPE c (a INT, b TEXT)
[assistant] Postgres round-trips now. Composite output for DuckDB/MySQL (`CREATE TYPE c (a INT, b TEXT)`) isn't valid there. Enum output is valid for DuckDB. I'll flag that in the summary rather than expand scope. Next, the tests: I'm finding the Postgres DDL test method to extend.
[tool_use Bash] {"command": "grep -n \"    def test_\" tests/dialects/test_postgres.py | head -80 | grep -i \"ddl\\|create\\|enum\\|type\"; grep -n \"def test_ddl\" -A6 tests/dialects/test_postgres.py"}
[tool_result] 1087:    def test_ddl(self):
1704:    def test_datatype(self):
1833:    def test_postgres_create_trigger(self):
1087:    def test_ddl(self):
1088-        # Checks that user-defined types are parsed into DataType instead of Identifier
1089-        self.parse_one("CREATE TABLE t (a udt)").this.expressions[0].args["kind"].assert_is(
1090-            exp.DataType
1091-        )
1092-
1093-        # Checks that OID is parsed into a DataType (ObjectIdentifier)
[tool_use Bash] {"command": "sed -n 1093,1100p tests/dialects/test_postgres.py"}
[tool_result]         # Checks that OID is parsed into a DataType (ObjectIdentifier)
        self.assertIsInstance(
            self.parse_one("CREATE TABLE p.t (c oid)").find(exp.DataType), exp.ObjectIdentifier
        )

        expr = self.parse_one("CREATE TABLE t (x INTERVAL day)")
        cdef = expr.find(exp.ColumnDef)
        cdef.args["kind"].assert_is(exp.DataType)
[assistant] I'll add a focused test method that checks both the round-trip and the AST node shape.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-005847-postgres-dialect-create-type-fal/base-1/tests/dialects/test_postgres.py", "old_string": "    def test_datatype(self):", "new_string": "    def test_create_type(self):\n        self.validate_identity(\"CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')\")\n        self.validate_identity(\"
…[584 chars elided]…
        composite = self.parse_one(\"CREATE TYPE complex AS (r INT, i TEXT)\")\n        self.assertIsInstance(composite.this, exp.Schema)\n        self.assertEqual(\n            [cdef.name for cdef in composite.this.expressions], [\"r\", \"i\"]\n        )\n        self.assertIsNone(composite.expression)\n\n        self.assertIsInstance(self.parse_one(\"CREATE TYPE shell_type\"), exp.Command)\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-005847-postgres-dialect-create-type-fal/base-1/tests/dialects/test_postgres.py has been updated successfully.
[assistant] Running the Postgres dialect test file first (it's fast), then lint and format.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -30; $PY -m ruff format sqlglot/parsers/postgres.py sqlglot/generators/postgres.py tests/dialects/test_postgres.py; $PY -m ruff check sqlglot/parsers/postgres.py sqlglot/generators/postgres.py tests/dialects/test_postgres.py; git diff --stat"}
[tool_result] .........................                              [100%]
25 passed, 378 subtests passed in 0.25s
2 files reformatted, 1 file left unchanged
All checks passed!
 sqlglot/generators/postgres.py  | 12 ++++++++++++
 sqlglot/parsers/postgres.py     | 30 ++++++++++++++++++++++++++++++
 tests/dialects/test_postgres.py | 22 +++++++++++++++++++++-
 3 files changed, 63 insertions(+), 1 deletion(-)
[This command modified 2 files you've previously read: sqlglot/parsers/postgres.py, tests/dialects/test_postgres.py. Call Read before editing.]
[assistant] Ruff reformatted two files I'd edited, and the test diff shows one deleted line I didn't mean to change. Checking the diff to see what it touched.
[tool_use Bash] {"command": "git diff"}
[tool_result] diff --git a/sqlglot/generators/postgres.py b/sqlglot/generators/postgres.py
index 15baf8b7e..b53e6bf46 100644
--- a/sqlglot/generators/postgres.py
+++ b/sqlglot/generators/postgres.py
@@ -487,6 +487,18 @@ class PostgresGenerator(generator.Generator):
 
         return super().datatype_sql(expression)
 
+    def create_sql(self, expression: exp.Create) -> str:
+        if expression.kind != "TYPE":
+            return super().create_sql(expression)
+
+        this = expression.this
+        if i
…[3149 chars elided]…
f.parse_one("CREATE TYPE complex AS (r INT, i TEXT)")
+        self.assertIsInstance(composite.this, exp.Schema)
+        self.assertEqual([cdef.name for cdef in composite.this.expressions], ["r", "i"])
+        self.assertIsNone(composite.expression)
+
+        self.assertIsInstance(self.parse_one("CREATE TYPE shell_type"), exp.Command)
+
         self.assertEqual(exp.DataType.build("XML", dialect="postgres").sql("postgres"), "XML")
         self.validate_identity("CREATE TABLE foo (data XML)")
[assistant] The test edit dropped the `def test_datatype(self):` header: my replacement ate it, so the existing `test_datatype` body would have been folded into my new method. Restoring the header.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-005847-postgres-dialect-create-type-fal/base-1/tests/dialects/test_postgres.py", "old_string": "        self.assertIsInstance(self.parse_one(\"CREATE TYPE shell_type\"), exp.Command)\n\n        self.assertEqual(exp.DataType.build(\"XML\"", "new_string": "        self.assertIsInstance(self.parse_one(\"CREATE TYPE shell_type\"), exp.Command)\n\n    def test_datatype(self):\n        self.assertEqual(exp.DataType.build(\"XML\""}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-005847-postgres-dialect-create-type-fal/base-1/tests/dialects/test_postgres.py has been updated successfully.
[assistant] Re-running the Postgres tests and lint after that fix, then starting the full suite through the harness script.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -3; $PY -m ruff format --check sqlglot/parsers/postgres.py sqlglot/generators/postgres.py tests/dialects/test_postgres.py; $PY -m ruff check sqlglot/parsers/postgres.py sqlglot/generators/postgres.py tests/dialects/test_postgres.py; $PY -m mypy sqlglot/parsers/postgres.py sqlglot/generators/postgres.py 2>&1 | tail -3; git diff --stat"}
[tool_result] ..........................                             [100%]
26 passed, 378 subtests passed in 0.17s
3 files already formatted
All checks passed!
sqlglot/parsers/postgres.py:366: error: Incompatible types in assignment (expression has type "Schema", variable has type "Table | Dot | None")  [assignment]
Found 1 error in 1 file (checked 2 source files)
 sqlglot/generators/postgres.py  | 12 ++++++++++++
 sqlglot/parsers/postgres.py     | 30 ++++++++++++++++++++++++++++++
 tests/dialects/test_postgres.py | 21 +++++++++++++++++++++
 3 files changed, 63 insertions(+)
[assistant] The new code passes tests and lint, but mypy flags reassigning `this` from `Table` to `Schema`. Annotating `this` as a general `Expr` fixes it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-005847-postgres-dialect-create-type-fal/base-1/sqlglot/parsers/postgres.py", "old_string": "        this = self._parse_table_parts()\n        if not this or not self._match(TokenType.ALIAS):", "new_string": "        this: exp.Expr | None = self._parse_table_parts()\n        if not this or not self._match(TokenType.ALIAS):"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-005847-postgres-dialect-create-type-fal/base-1/sqlglot/parsers/postgres.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m mypy sqlglot/parsers/postgres.py sqlglot/generators/postgres.py 2>&1 | tail -2; $PY -m ruff check sqlglot/parsers/postgres.py && $PY -m ruff format --check sqlglot/parsers/postgres.py; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -1; PYTHONPATH=. $PY /tmp/probe_ct.py 2>/dev/null | head -4; ls .lithify/harness/scripts/"}
[tool_result] Success: no issues found in 2 source files
All checks passed!
1 file already formatted
26 passed, 378 subtests passed in 0.16s
Create | CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')
   this: Table | kind: TYPE | expr: DataType(
  this=DType.ENUM,
  expressions=[
run_suite.py
[assistant] Mypy, ruff, and the dialect tests are clean. Now the full suite, which is the completion gate in the project harness.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/scripts/run_suite.py", "description": "Run full pytest suite via harness script", "timeout": 600000}
[tool_result] WARNING: 1 other pytest process(es) running; expect slower runs:
  34207 03-05:59:59 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-a8767f994e.log
ELAPSED: 60s
SUMMARY: 1106 passed, 17982 subtests passed in 60.06s (0:01:00)
EXIT: 0
[assistant] `CREATE TYPE` now parses into a real AST node for enum and composite types, and both round-trip in Postgres. The full suite passed after my last edit: `SUMMARY: 1106 passed, 17982 subtests passed in 60.06s (0:01:00)`, `EXIT: 0`. I haven't committed anything.

```python
parse_one("CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')", "postgres").sql("postgres")
# "CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')"
```

**What changed**
- `sqlglot/parsers/postgres.py`: a `_parse_create` override. It claims `CREATE TYPE` and hands every other `CREATE` to the base parser. It produces `ex
…[685 chars elided]…
**
- Other dialects: the enum output is valid for DuckDB, but the composite output (`CREATE TYPE c (a INT, b TEXT)`) isn't valid DuckDB or MySQL. DuckDB would need `AS STRUCT(...)`. I didn't add that because the task is Postgres round-trip. Before this change, those statements passed through as raw Postgres text, which was also invalid in those engines, so this isn't a regression in validity. Say if you want the cross-dialect output handled.
- Composite `FLOAT` attributes print as `DOUBLE PRECISION`. That's the existing Postgres generator behaviour for `FLOAT`, and it's equivalent in Postgres.
