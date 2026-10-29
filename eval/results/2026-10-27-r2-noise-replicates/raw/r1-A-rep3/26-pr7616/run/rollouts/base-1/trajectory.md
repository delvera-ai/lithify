# trajectory base-1

final message:
`CREATE TYPE` now parses into a real `Create` node with kind `TYPE`, and enum and composite bodies round-trip in Postgres. The full suite passes (1106 tests, 17,982 subtests), and ruff lint and format are clean on the changed files. Nothing is committed.

```python
parse_one("CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')", "postgres").sql("postgres")
# "CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')"
```

Changes:
- **`sqlglot/parser.py`**: `_parse_create` treats a `TYPE` word after `CREATE` as a creatable. It then parses the name, then either `AS ENUM (...)` into the new node or `AS (attr type, ...)` into a `Schema` of column defs. Shell types like `CREATE TYPE t` also parse.
- **`sqlglot/expressions/ddl.py`**: new `EnumType` expression holding the enum labels.
- **`sqlglot/generator.py`**: `enumtype_sql` emits `ENUM (...)` with the space Postgres uses.
- **`tests/dialects/test_postgres.py`**: new `test_create_type` covering enum, schema-qualified enum, composite, and shell type round-trips, plus a check on the body node types.

Choices I made that you may want to change:
- **Base parser, not a Postgres override.** `CREATE TYPE` now parses in every dialect, not only Postgres. This follows the repo's preference for the base dialect. A Postgres-only path would mean overriding the whole `_parse_create`.
- **`CREATE TYPE ... AS RANGE (...)` still falls back to a Command.** Range, base, and other less common forms are out of scope, so they keep the existing fallback.
- **`TYPE` is matched as text, not a new token.** Adding a `TYPE` keyword would break columns named `type`, and `CREATE TABLE type (...)` still parses correctly.

## events
[assistant] I'll start by finding how the Postgres dialect and the base parser handle `CREATE`.
[tool_use Bash] {"command": "git status --short && grep -n \"TYPE\\|_parse_create\\|CREATABLES\\|ENUM\" sqlglot/dialects/postgres.py | head -80 && echo ---- && grep -n \"def _parse_create\\|create_token\\|\\\"TYPE\\\"\\|ENUM\\b\" sqlglot/parser.py | head -60", "description": "Inspect repo state and locate TYPE/ENUM handling"}
[tool_result] 12:    TYPED_DIVISION = True
84:            "CSTRING": TokenType.PSEUDO_TYPE,
111:            "REGTYPE": TokenType.OBJECT_IDENTIFIER,
----
460:        TokenType.ENUM,
1629:        "TYPE": ("EVOLUTION",),
2344:    def _parse_create(self) -> exp.Create | exp.Command:
2370:        create_token = self._match_set(self.CREATABLES) and self._prev
2372:        if not create_token:
2375:            create_token = self._match_set(self.CREATABLES) and self._prev
2377:            if not properties or not cr
…[728 chars elided]…
           schema=True, is_db_reference=create_token_type == TokenType.SCHEMA
2507:            if create_token_type == TokenType.SEQUENCE:
2535:            if create_token_type == TokenType.TABLE:
2550:            elif create_token_type == TokenType.VIEW:
2553:            elif create_token_type in (TokenType.SINK, TokenType.SOURCE):
2567:        create_kind_text = create_token.text.upper()
3280:    def _parse_create_like(self) -> exp.LikeProperty | None:
8627:        self._match_text_seq("TYPE")
[assistant] Still working on the parser. The MCP docs tools that just appeared aren't relevant here; the request is a code change, so I'm not creating a doc. Next I'll read the create-parsing code and the existing create tests.
[tool_use Bash] {"command": "sed -n 2344,2600p sqlglot/parser.py", "description": "Read the _parse_create method"}
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
…[9624 chars elided]…
ties(self) -> exp.SequenceProperties | None:
        seq = exp.SequenceProperties()

        options = []
        index = self._index

        while self._curr:
            self._match(TokenType.COMMA)
            if self._match_text_seq("INCREMENT"):
                self._match_text_seq("BY")
                self._match_text_seq("=")
                seq.set("increment", self._parse_term())
            elif self._match_text_seq("MINVALUE"):
                seq.set("minvalue", self._parse_term())
[tool_use Bash] {"command": "grep -n \"CREATABLES\\|DB_CREATABLES\\|CREATE_\" sqlglot/parser.py | head -30 && grep -n \"TYPE\\b\" sqlglot/tokens.py | head; grep -rn \"CREATE TYPE\\|create type\" tests/ | head -20; grep -n \"class Create\\b\" -A 30 sqlglot/expressions.py | head -50", "description": "Find creatable token sets and existing CREATE TYPE tests"}
[tool_result] 619:    DB_CREATABLES: t.ClassVar = {
639:    CREATABLES: t.ClassVar = {
647:        *DB_CREATABLES,
765:        *CREATABLES,
1596:    CREATE_SEQUENCE: t.ClassVar[OPTIONS_TYPE] = {
2183:        kind = self._match_set(self.CREATABLES) and self._prev
2297:        kind = self._match_set(self.CREATABLES) and self._prev.text.upper()
2370:        create_token = self._match_set(self.CREATABLES) and self._prev
2375:            create_token = self._match_set(self.CREATABLES) and self._prev
2488:        elif create_token_type in self.DB_CREATABLES:
2613:                opt = self._parse_var_from_options(self.CREATE_SEQUENCE, raise_unmatched=False)
3337:        kind = self._prev.text if self._match_set(self.CREATABLES) else None
9525:        kind = self._prev.text.upper() if self._match_set(self.CREATABLES) else None
ugrep: warning: sqlglot/expressions.py: No such file or directory
[assistant] The grep hit a path error, so `expressions` is probably a package now. I'll check that, plus the creatable token sets and any existing `CREATE TYPE` tests.
[tool_use Bash] {"command": "sed -n 615,660p sqlglot/parser.py && ls sqlglot/expressions* -d && grep -rn \"class Create(\" -A 25 sqlglot/expressions/ | head -40 && grep -rn \"TYPE\" tests/dialects/test_postgres.py | grep -i \"create\" | head; grep -rln \"CREATE TYPE\" tests/ | head; grep -rn \"ENUM\" sqlglot/dialects/postgres.py sqlglot/generator.py | head", "description": "Inspect creatable sets, expressions package, existing tests"}
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
…[351 chars elided]…
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
        TokenType.VIEW,
ls: -d: No such file or directory
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
[assistant] No `CREATE TYPE` tests exist yet. Next I'll look at the `Create` node in `ddl.py` and check how `TYPE` and `ENUM` are tokenized.
[tool_use Bash] {"command": "grep -n \"class Create\" -A 30 sqlglot/expressions/ddl.py | head -45; grep -n \"\\\"TYPE\\\"\\|\\\"ENUM\\\"\\|TokenType.TYPE\\|TokenType.ENUM\\|DOMAIN\" sqlglot/tokens.py sqlglot/dialects/postgres.py sqlglot/parser.py | head -20; grep -n \"CREATABLE_KIND_MAPPING\" -A6 sqlglot/dialects/dialect.py | head -12; grep -n \"def _parse_types\\|def _parse_column_def\\|def _parse_schema\\|def _parse_field_def\" sqlglot/parser.py", "description": "Inspect Create node, TYPE/ENUM tokens, parse helpers"}
[tool_result] 39:class Create(Expression, DDL):
40-    arg_types = {
41-        "with_": False,
42-        "this": True,
43-        "kind": True,
44-        "expression": False,
45-        "exists": False,
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
56-
…[991 chars elided]…
izer),)
254-        base_parser = (getattr(base, "parser_class", Parser),)
--
685:    CREATABLE_KIND_MAPPING: dict[str, str] = {}
686-    """
687-    Helper for dialects that use a different name for the same creatable kind. For example, the Clickhouse
6121:    def _parse_types(
7043:    def _parse_schema(self, this: exp.Expr | None = None) -> exp.Expr | None:
7057:    def _parse_field_def(self) -> exp.Expr | None:
7060:    def _parse_column_def(
8526:    def _parse_column_def_with_exists(self):
[assistant] `TYPE` isn't a keyword token, so it tokenizes as a plain var and `CREATE TYPE` falls through `_parse_as_command`. Before choosing a node shape, I'll check for an existing enum expression and for the generator's `create_sql`.
[tool_use Bash] {"command": "grep -rn -i \"enum\" sqlglot/expressions/*.py | head -20; grep -n \"def create_sql\" -A 70 sqlglot/generator.py | head -110; grep -n \"def _match_text_seq\" -A3 sqlglot/parser.py", "description": "Find enum expressions and the generator create_sql"}
[tool_result] sqlglot/expressions/datatypes.py:6:from enum import auto
sqlglot/expressions/datatypes.py:62:    ENUM = auto()
sqlglot/expressions/datatypes.py:63:    ENUM8 = auto()
sqlglot/expressions/datatypes.py:64:    ENUM16 = auto()
sqlglot/expressions/core.py:1097:            for i, v in enumerate(value):
sqlglot/expressions/properties.py:6:from enum import auto
sqlglot/expressions/string.py:581:class ParseNumeric(Expression, Func):
1284:    def create_sql(self, expression: exp.Create) -> str:
1285-      
…[3121 chars elided]…
" if indexes else ""
1350-        index_sql = indexes + postindex_props_sql
1351-
1352-        replace = " OR REPLACE" if expression.args.get("replace") else ""
1353-        refresh = " OR REFRESH" if expression.args.get("refresh") else ""
1354-        unique = " UNIQUE" if expression.args.get("unique") else ""
1948:    def _match_text_seq(self, *texts: str, advance: bool = True) -> bool:
1949-        index = self._index
1950-        string_type = TokenType.STRING
1951-        for text in texts:
[assistant] Plan so far: `CREATE TYPE` becomes `exp.Create(kind="TYPE")` with the body in `expression`. Enum bodies need a small new node, since `ENUM (...)` has no existing class. Composite bodies can reuse `exp.Schema` of column defs. Before writing it, I'll check the parser and generator helpers I plan to call.
[tool_use Bash] {"command": "sed -n 7043,7060p sqlglot/parser.py; grep -n \"def _try_parse\" -A12 sqlglot/parser.py | head -20; grep -n \"def wrap\\b\\|def wrap(\" -A6 sqlglot/generator.py; grep -n \"def schema_sql\\|def tuple_sql\" -A8 sqlglot/generator.py | head -30; grep -n \"Create\" sqlglot/dialects/postgres.py; head -30 sqlglot/expressions/__init__.py | grep -n import; grep -n \"__all__\" sqlglot/expressions/__init__.py | head -3", "description": "Check parser/generator helpers and expression exports"}
[tool_result]     def _parse_schema(self, this: exp.Expr | None = None) -> exp.Expr | None:
        index = self._index
        if not self._match(TokenType.L_PAREN):
            return this

        # Disambiguate between schema and subquery/CTE, e.g. in INSERT INTO table (<expr>),
        # expr can be of both types
        if self._match_set(self.SELECT_START_TOKENS):
            self._retreat(index)
            return this
        args = self._parse_csv(lambda: self._parse_constraint() or self._parse_fiel
…[2590 chars elided]…
xpressions.string import *  # noqa: F401,F403
23:from sqlglot.expressions.temporal import *  # noqa: F401,F403
24:from sqlglot.expressions.aggregate import *  # noqa: F401,F403
25:from sqlglot.expressions.array import *  # noqa: F401,F403
26:from sqlglot.expressions.json import *  # noqa: F401,F403
27:from sqlglot.expressions.functions import *  # noqa: F401,F403
28:from sqlglot.expressions.builders import *  # noqa: F401,F403
30:# Explicitly import private helpers (not exported by star imports)
[assistant] I have what I need. The plan:

1. **Parser** (`sqlglot/parser.py`): treat a `TYPE` word after `CREATE` as a creatable of kind `TYPE`, then parse the name and an optional `AS ENUM (...)` or `AS (attr type, ...)` body. Anything else falls back to a Command as before.
2. **AST** (`sqlglot/expressions/ddl.py`): a new `EnumType` node for the enum body. Composite bodies use the existing `Schema` node.
3. **Generator** (`sqlglot/generator.py`): an `enumtype_sql` method, which the generator discovers by name.

I'll start with the new expression node.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-123139-postgres-dialect-create-type-fal/base-1/sqlglot/expressions/ddl.py", "old_string": "    @property\n    def kind(self) -> str | None:\n        kind = self.args.get(\"kind\")\n        return kind and kind.upper()\n\n\nclass SequenceProperties(Expression):", "new_string": "    @property\n    def kind(self) -> str | None:\n        kind = self.args.get(\"kind\")\n        return kind and kind.upper()\n\n\nclass EnumType(Expression):\n    arg_types = {\"expressions\": True}\n\n\nclass SequenceProperties(Expression):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-123139-postgres-dialect-create-type-fal/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"    def expressions(\" -A12 sqlglot/generator.py | head -20", "description": "Check generator expressions() helper signature"}
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
[assistant] Next, the parser change. I'm adding the `TYPE` match only on the first creatable lookup, so `CREATE TYPE` is caught before the properties fallback.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-123139-postgres-dialect-create-type-fal/base-1/sqlglot/parser.py", "old_string": "        properties = None\n        create_token = self._match_set(self.CREATABLES) and self._prev\n\n        if not create_token:", "new_string": "        properties = None\n        create_token = self._match_set(self.CREATABLES) and self._prev\n\n        if not create_token and self._match_text_seq(\"TYPE\"):\n            create_token = self._prev\n\n        if not create_token:"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-123139-postgres-dialect-create-type-fal/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-123139-postgres-dialect-create-type-fal/base-1/sqlglot/parser.py", "old_string": "            this = self._parse_user_defined_function(kind=create_token_type)\n\n            # exp.Properties.Location.POST_SCHEMA (\"schema\" here is the UDF's type signature)", "new_string": "            this = self._parse_user_defined_function(kind=create_token_type)\n\n            # exp.Properties.Location.POST_SCHEMA (\"schema\" here is the UDF's type signature)"}
[tool_result ERROR] <tool_use_error>No changes to make: old_string and new_string are exactly the same.</tool_use_error>
[assistant] That second edit was a no-op by mistake, and nothing changed. Now I'll add the `TYPE` branch just before the `DB_CREATABLES` branch.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-123139-postgres-dialect-create-type-fal/base-1/sqlglot/parser.py", "old_string": "            this = self._parse_index(index=index, anonymous=anonymous)\n        elif (\n            create_token_type == TokenType.CONSTRAINT and self._match(TokenType.TRIGGER)", "new_string": "            this = self._
…[211 chars elided]…
f self._match(TokenType.ENUM):\n                    expression = self.expression(\n                        exp.EnumType(expressions=self._parse_wrapped_csv(self._parse_string))\n                    )\n                else:\n                    expression = self._try_parse(self._parse_schema)\n        elif (\n            create_token_type == TokenType.CONSTRAINT and self._match(TokenType.TRIGGER)"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-123139-postgres-dialect-create-type-fal/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Now the generator method for the enum body. It's auto-discovered by name, so no `TRANSFORMS` entry is needed.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-123139-postgres-dialect-create-type-fal/base-1/sqlglot/generator.py", "old_string": "    def schema_sql(self, expression: exp.Schema) -> str:\n        this = self.sql(expression, \"this\")", "new_string": "    def enumtype_sql(self, expression: exp.EnumType) -> str:\n        return f\"ENUM ({self.expressions(expression, flat=True)})\"\n\n    def schema_sql(self, expression: exp.Schema) -> str:\n        this = self.sql(expression, \"this\")"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-123139-postgres-dialect-create-type-fal/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Next I'll test the round trips and the fallback cases: enum, composite, shell type, a `RANGE` form the parser doesn't handle, and an unrelated `type` identifier.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c '\nimport sqlglot\nfrom sqlglot import parse_one, exp\ncases = [\n \"CREATE TYPE book_type AS ENUM (\\x27FICTION\\x27, \\x27NONFICTION\\x27)\",\n \"CREATE TYPE public.mood AS ENUM (\\x27sad\\x27, \\x27ok\\x27, \\x27happy\\x27)\",\n \"CREATE TYPE complex AS (r DOUBLE PRECISION, i DOUBLE PRECISION)\",\n \"CREAT
…[93 chars elided]…
e INT)\",\n \"CREATE TYPE book_type AS ENUM (\\x27A\\x27)\",\n]\nfor c in cases:\n    e = parse_one(c, read=\"postgres\")\n    print(type(e).__name__, \"|\", e.sql(\"postgres\"), \"| ok\" if e.sql(\"postgres\")==c else \"| DIFF\")\nprint(repr(parse_one(\"CREATE TYPE x AS (a INT)\", read=\"postgres\")))\n' 2>&1 | head -60", "description": "Round-trip CREATE TYPE cases through the Postgres dialect"}
[tool_result] 'CREATE TYPE r AS RANGE (SUBTYPE = float8)' contains unsupported syntax. Falling back to parsing as a 'Command'.
Create | CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION') | ok
Create | CREATE TYPE public.mood AS ENUM ('sad', 'ok', 'happy') | ok
Create | CREATE TYPE complex AS (r DOUBLE PRECISION, i DOUBLE PRECISION) | ok
Create | CREATE TYPE shell_t | ok
Command | CREATE TYPE r AS RANGE (SUBTYPE = float8) | ok
Create | CREATE TABLE type (type INT) | ok
Create | CREATE TYPE book_type AS ENUM ('A') | ok
Create(
  this=Table(
    this=Identifier(this=x, quoted=False)),
  kind=TYPE,
  replace=False,
  refresh=False,
  unique=False,
  expression=Schema(
    expressions=[
      ColumnDef(
        this=Identifier(this=a, quoted=False),
        kind=DataType(this=DType.INT, nested=False))]),
  exists=False,
  concurrently=False)
[assistant] All cases round-trip, and `RANGE` still falls back to a Command as before. Next I'll add regression tests to the Postgres dialect test file, then run the suite.
[tool_use Bash] {"command": "grep -n \"    def test_\" tests/dialects/test_postgres.py | head -30 && grep -n \"def test_ddl\" -A6 tests/dialects/test_postgres.py", "description": "Find a test method in test_postgres.py to extend"}
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
1643:    
…[233 chars elided]…
def test_revoke(self):
1788:    def test_begin_transaction(self):
1811:    def test_interval_span(self):
1833:    def test_postgres_create_trigger(self):
1087:    def test_ddl(self):
1088-        # Checks that user-defined types are parsed into DataType instead of Identifier
1089-        self.parse_one("CREATE TABLE t (a udt)").this.expressions[0].args["kind"].assert_is(
1090-            exp.DataType
1091-        )
1092-
1093-        # Checks that OID is parsed into a DataType (ObjectIdentifier)
[tool_use Bash] {"command": "sed -n 1675,1686p tests/dialects/test_postgres.py", "description": "Read the test_udt method for placement"}
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-123139-postgres-dialect-create-type-fal/base-1/tests/dialects/test_postgres.py", "old_string": "        _validate_udt('CAST(5 AS \"MyCatalog\".\"MySchema\".\"MyType\")')\n\n    def test_round(self):", "new_string": "        _validate_udt('CAST(5 AS \"MyCatalog\".\"MySchema\".\"MyType\")')\n\n    def 
…[309 chars elided]…
\n        self.validate_identity(\"CREATE TYPE shell_type\")\n\n        self.assertIsInstance(\n            self.parse_one(\"CREATE TYPE book_type AS ENUM ('FICTION')\").args[\"expression\"],\n            exp.EnumType,\n        )\n        self.assertIsInstance(\n            self.parse_one(\"CREATE TYPE complex AS (r INT)\").args[\"expression\"], exp.Schema\n        )\n\n    def test_round(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-123139-postgres-dialect-create-type-fal/base-1/tests/dialects/test_postgres.py has been updated successfully.
[assistant] Next, the project's test command from the harness instructions, run against the whole suite so I can catch any regressions in other dialects.
[tool_use Bash] {"command": "timeout 900 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run the full pytest suite", "timeout": 900000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run the full pytest suite", "timeout": 900000}
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
1106 passed, 17982 subtests passed in 49.55s
[assistant] The full suite passes: 1106 tests and 17,982 subtests. Last, a lint and format check on the changed files, if the env has ruff.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/ddl.py tests/dialects/test_postgres.py 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/ddl.py tests/dialects/test_postgres.py 2>&1 | tail -5; git status --short", "description": "Run ruff lint and format checks on changed files"}
[tool_result] All checks passed!
4 files already formatted
 M sqlglot/expressions/ddl.py
 M sqlglot/generator.py
 M sqlglot/parser.py
 M tests/dialects/test_postgres.py
[assistant] `CREATE TYPE` now parses into a real `Create` node with kind `TYPE`, and enum and composite bodies round-trip in Postgres. The full suite passes (1106 tests, 17,982 subtests), and ruff lint and format are clean on the changed files. Nothing is committed.

```python
parse_one("CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')", "postgres").sql("postgres")
# "CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')"
```

Changes:
- **`sqlglot/parser.py`**: `_parse_create` treats a `TYPE` word after `CREATE` as a creatable. It then parses the name, then either `AS ENUM (...)` into the new no
…[468 chars elided]…
ices I made that you may want to change:
- **Base parser, not a Postgres override.** `CREATE TYPE` now parses in every dialect, not only Postgres. This follows the repo's preference for the base dialect. A Postgres-only path would mean overriding the whole `_parse_create`.
- **`CREATE TYPE ... AS RANGE (...)` still falls back to a Command.** Range, base, and other less common forms are out of scope, so they keep the existing fallback.
- **`TYPE` is matched as text, not a new token.** Adding a `TYPE` keyword would break columns named `type`, and `CREATE TABLE type (...)` still parses correctly.
