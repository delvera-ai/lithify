# trajectory base-1

final message:
`CREATE TYPE ... AS ENUM (...)` and `CREATE TYPE ... AS (attr type, ...)` now parse into `exp.Create(kind="TYPE")` and round-trip in Postgres. The full suite passes (1106 tests), and ruff check and format are clean.

**Change** (`sqlglot/parser.py`):
- `_parse_create` now checks for `TYPE` right after the `OR REPLACE` handling and hands off to a new `_parse_create_type`.
- `_parse_create_type` parses the name, then either an enum (a `DataType` of `ENUM` with string values) or a composite (a `Schema` of column definitions). Anything else falls back to `Command` as before.
- Because the change is in the base parser, it applies to every dialect that parses `CREATE`, not just Postgres.

**Test** (`tests/dialects/test_postgres.py`): new `test_create_type` covering an enum, a schema-qualified enum, and a composite type.

Things to know:
- **Enum output has no space before the parenthesis.** It comes out as `AS ENUM('FICTION', 'NONFICTION')`, not `AS ENUM ('FICTION', 'NONFICTION')`. That matches how sqlglot renders the `ENUM` data type elsewhere, and Postgres accepts it. The test asserts that form, so an exact-text round-trip of the spaced input will not match.
- **Empty composites still fall back to `Command`.** `CREATE TYPE t AS ()` is valid Postgres, but I left it on the fallback path, which keeps the original text.
- **Not handled:** `AS RANGE (...)` and `CREATE TYPE` without `AS` still fall back to `Command`, since they were not in scope.
- I did not commit anything.

## events
[tool_use Bash] {"command": "grep -n \"TYPE\\|ENUM\" sqlglot/dialects/postgres.py | head -60; echo ---; grep -n \"def _parse_create\\|\\\"TYPE\\\"\\|TYPE:\" sqlglot/parser.py | head; echo ---; grep -n \"class Create\\b\\|class Create(\" -A 30 sqlglot/expressions.py | head -50; echo ---; grep -rn \"ENUM\\|EnumType\\|enum\" sqlglot/tokens.py sqlglot/expressions.py | head -20", "description": "Locate CREATE TYPE and enum handling in sources"}
[tool_result] 12:    TYPED_DIVISION = True
84:            "CSTRING": TokenType.PSEUDO_TYPE,
111:            "REGTYPE": TokenType.OBJECT_IDENTIFIER,
---
1629:        "TYPE": ("EVOLUTION",),
1782:    JSON_ARROWS_REQUIRE_JSON_TYPE: t.ClassVar = False
2344:    def _parse_create(self) -> exp.Create | exp.Command:
3280:    def _parse_create_like(self) -> exp.LikeProperty | None:
6151:        if type_token == TokenType.PSEUDO_TYPE:
8627:        self._match_text_seq("TYPE")
---
ugrep: warning: sqlglot/expressions.py: No such file or directory
---
ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/tokens.py:288:        "ENUM": TokenType.ENUM,
[tool_use Bash] {"command": "ls sqlglot/expressions* -d; sed -n 2344,2420p sqlglot/parser.py; echo ---; grep -n \"CREATABLES\\|\\\"TYPE\\\"\" sqlglot/parser.py sqlglot/dialects/*.py | head -20", "description": "Read CREATE parsing logic and creatable tokens"}
[tool_result] ls: -d: No such file or directory
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
    def _parse_create(self) -> exp.Create | exp.Command:
        # Note: this can't be None because we've matched a statement parser
        start = self._prev

        replace = (
            start.token_type == TokenType.REPLACE
            or self._match_pair(TokenType.OR
…[3364 chars elided]…
e_token = self._match_set(self.CREATABLES) and self._prev
sqlglot/parser.py:2375:            create_token = self._match_set(self.CREATABLES) and self._prev
sqlglot/parser.py:2488:        elif create_token_type in self.DB_CREATABLES:
sqlglot/parser.py:3337:        kind = self._prev.text if self._match_set(self.CREATABLES) else None
sqlglot/parser.py:8627:        self._match_text_seq("TYPE")
sqlglot/parser.py:9525:        kind = self._prev.text.upper() if self._match_set(self.CREATABLES) else None
[tool_use Bash] {"command": "sed -n 615,660p sqlglot/parser.py; echo ---; sed -n 2420,2560p sqlglot/parser.py", "description": "Read CREATABLES sets and rest of _parse_create"}
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
…[6147 chars elided]…
elif create_token_type == TokenType.VIEW:
                if self._match_text_seq("WITH", "NO", "SCHEMA", "BINDING"):
                    no_schema_binding = True
            elif create_token_type in (TokenType.SINK, TokenType.SOURCE):
                extend_props(self._parse_properties())

            shallow = self._match_text_seq("SHALLOW")

            if self._match_texts(self.CLONE_KEYWORDS):
                copy = self._prev.text.lower() == "copy"
                clone = self.expression(
[tool_use Bash] {"command": "grep -n \"TYPE\\b\" sqlglot/tokens.py | head; echo ---; sed -n 2560,2600p sqlglot/parser.py; echo ---; grep -n \"ENUM\" sqlglot/expressions/datatypes.py sqlglot/parser.py sqlglot/generator.py sqlglot/dialects/postgres.py | head -30; echo ---; grep -n \"def create_sql\" -A 60 sqlglot/generator.py | head -90", "description": "Inspect tokens, enum handling, and create_sql generator"}
[tool_result] ---
                clone = self.expression(
                    exp.Clone(this=self._parse_table(schema=True), shallow=shallow, copy=copy)
                )

        if self._curr and not self._match_set((TokenType.R_PAREN, TokenType.COMMA), advance=False):
            return self._parse_as_command(start)

        create_kind_text = create_token.text.upper()
        return self.expression(
            exp.Create(
                this=this,
                kind=self.dialect.CREATABLE_KIND_MAPPIN
…[4040 chars elided]…
      )
1337-                postalias_props_sql = f" {postalias_props_sql}" if postalias_props_sql else ""
1338-                expression_sql = f" AS{postalias_props_sql}{expression_sql}"
1339-
1340-        postindex_props_sql = ""
1341-        if properties_locs.get(exp.Properties.Location.POST_INDEX):
1342-            postindex_props_sql = self.properties(
1343-                exp.Properties(expressions=properties_locs[exp.Properties.Location.POST_INDEX]),
1344-                wrapped=False,
[tool_use Bash] {"command": "grep -rn \"CREATE TYPE\" tests/ | head; echo ---; sed -n 6190,6215p sqlglot/parser.py; echo ---; grep -n \"def _parse_schema\\b\" -A 25 sqlglot/parser.py | head -40; echo ---; grep -n \"def schema_sql\" -A 12 sqlglot/generator.py; echo; grep -n \"def _parse_wrapped_csv\\|def _parse_table_parts\" sqlglot/parser.py", "description": "Check existing tests and helper parser signatures"}
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
               
…[2396 chars elided]…
xpression.expressions:
3215-            return f"({self.sep('')}{self.expressions(expression)}{self.seg(')', sep='')}"
3216-        return ""
3217-
3218-    def star_sql(self, expression: exp.Star) -> str:
3219-        except_ = self.expressions(expression, key="except_", flat=True)
3220-        except_ = f"{self.seg(self.STAR_EXCEPT)} ({except_})" if except_ else ""

4579:    def _parse_table_parts_fast(self) -> exp.Table | None:
4642:    def _parse_table_parts(
8435:    def _parse_wrapped_csv(
[tool_use Bash] {"command": "ls <work>/env-sqlglot/bin/python 2>&1; python3 -c \"\nimport sqlglot\nfrom sqlglot import exp\nprint(sqlglot.__file__)\nprint(exp.DataType(this=exp.DataType.Type.ENUM, expressions=[exp.Literal.string('a'), exp.Literal.string('b')]).sql('postgres'))\nprint(exp.Schema(expressions=[exp.ColumnDef(this=exp.to_identifier('a'), kind=exp.DataType.build('int'))]).sql('postgres'))\nprint(repr(sqlglot.parse_one(\\\"CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')\\\", read='postgres')))\n\"", "description": "Check sqlglot import and ENUM/Schema generation"}
[tool_result] <work>/env-sqlglot/bin/python
'CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')' contains unsupported syntax. Falling back to parsing as a 'Command'.
~/.cache/lithify/work/repo-b63a38b63828/20261026-145758-postgres-dialect-create-type-fal/base-1/sqlglot/__init__.py
ENUM('a', 'b')
(a INT)
Command(this=CREATE, expression=TYPE book_type AS ENUM ('FICTION', 'NONFICTION'))
[tool_use Bash] {"command": "sed -n 8435,8450p sqlglot/parser.py; grep -n \"def _parse_string(\" sqlglot/parser.py; grep -n \"^from\\|^import\\|Token\\b\" sqlglot/parser.py | head -20", "description": "Check _parse_wrapped_csv signature and Token import"}
[tool_result]     def _parse_wrapped_csv(
        self,
        parse_method: t.Callable[[], T | None],
        sep: TokenType = TokenType.COMMA,
        optional: bool = False,
    ) -> list[T]:
        return self._parse_wrapped(
            lambda: self._parse_csv(parse_method, sep=sep), optional=optional
        )

    def _parse_wrapped(self, parse_method: t.Callable[[], T], optional: bool = False) -> T:
        wrapped = self._match(TokenType.L_PAREN)
        if not wrapped and not optional:
           
…[418 chars elided]…
lper import ensure_list, i64, seq_get
20:from sqlglot.trie import new_trie
21:from sqlglot.time import format_time
22:from sqlglot.tokens import Token, Tokenizer, TokenType
23:from sqlglot.trie import TrieResult, in_trie
24:from collections.abc import Sequence
25:from builtins import type as Type
287:SENTINEL_NONE: Token = Token(TokenType.SENTINEL, "SENTINEL")
1856:        self._tokens: list[Token] = []
1859:        self._curr: Token = SENTINEL_NONE
1860:        self._next: Token = SENTINEL_NONE
[tool_use Bash] {"command": "grep -n \"def _try_parse\" -A 14 sqlglot/parser.py", "description": "Read _try_parse helper"}
[tool_result] 2005:    def _try_parse(self, parse_method: t.Callable[[], T], retreat: bool = False) -> T | None:
2006-        index = self._index
2007-        error_level = self.error_level
2008-        this: T | None = None
2009-
2010-        self.error_level = ErrorLevel.IMMEDIATE
2011-        try:
2012-            this = parse_method()
2013-        except ParseError:
2014-            this = None
2015-        finally:
2016-            if not this or retreat:
2017-                self._retreat(index)
2018-            self.error_level = error_level
2019-
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-145758-postgres-dialect-create-type-fal/base-1/sqlglot/parser.py", "old_string": "        properties = None\n        create_token = self._match_set(self.CREATABLES) and self._prev\n\n        if not create_token:", "new_string": "        if self._match_text_seq(\"TYPE\"):\n            return self._parse_create_type(start, replace)\n\n        properties = None\n        create_token = self._match_set(self.CREATABLES) and self._prev\n\n        if not create_token:"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-145758-postgres-dialect-create-type-fal/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Now the helper method, placed right after `_parse_create`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-145758-postgres-dialect-create-type-fal/base-1/sqlglot/parser.py", "old_string": "                concurrently=concurrently,\n                clustered=clustered,\n            )\n        )\n\n    def _parse_sequence_properties(self) -> exp.SequenceProperties | None:", "new_string": "                c
…[541 chars elided]…
pe.ENUM, expressions=values)\n        else:\n            expression = self._parse_schema()\n\n        if not expression or self._curr:\n            return self._parse_as_command(start)\n\n        return self.expression(\n            exp.Create(this=this, kind=\"TYPE\", replace=replace, expression=expression)\n        )\n\n    def _parse_sequence_properties(self) -> exp.SequenceProperties | None:"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-145758-postgres-dialect-create-type-fal/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "python3 -I -c \"\nimport sys; sys.path.insert(0, '.')\nimport sqlglot\nfrom sqlglot import parse_one\ncases = [\n \\\"CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')\\\",\n \\\"CREATE TYPE public.mood AS ENUM ('sad', 'ok', 'happy')\\\",\n \\\"CREATE TYPE complex AS (r DOUBLE PRECISION, i DOUBLE PRECISION)\\\",\n \\\"CREATE TYPE empty_t AS ()\\\",\n \\\"CREATE TYPE t AS ENUM\\\
…[311 chars elided]…
om sqlglot import parse_one\nprint(parse_one(\\\"CREATE TYPE t AS ENUM ('a','b')\\\", read='postgres').sql('postgres', pretty=True))\nprint(parse_one(\\\"CREATE TYPE t AS (a INT, b TEXT)\\\", read='postgres').sql('postgres', pretty=True))\nprint(parse_one(\\\"CREATE TYPE t AS (a INT, b TEXT)\\\", read='postgres').sql('duckdb'))\n\"", "description": "Smoke-test CREATE TYPE parsing and round-trips"}
[tool_result] 'CREATE TYPE t AS ENUM' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE TYPE t' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE TYPE t AS RANGE (subtype = float8)' contains unsupported syntax. Falling back to parsing as a 'Command'.
Create | CREATE TYPE book_type AS ENUM('FICTION', 'NONFICTION')
Create | CREATE TYPE public.mood AS ENUM('sad', 'ok', 'happy')
Create | CREATE TYPE complex AS (r DOUBLE PRECISION, i DOUBLE PRECISION)
Create | CREATE TYPE empty_t
Command | CREATE TYPE t AS ENUM
Command | CREATE TYPE t
Command | CREATE TYPE t AS RANGE (subtype = float8)
Create | CREATE OR REPLACE TYPE t AS ENUM('a')

CREATE TYPE t AS
ENUM('a', 'b')
CREATE TYPE t AS
(
  a INT,
  b TEXT
)
CREATE TYPE t AS (a INT, b TEXT)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-145758-postgres-dialect-create-type-fal/base-1/sqlglot/parser.py", "old_string": "        if not expression or self._curr:\n            return self._parse_as_command(start)\n\n        return self.expression(\n            exp.Create(this=this, kind=\"TYPE\", replace=replace, expression=expression)", "new_string": "        if not expression or not expression.expressions or self._curr:\n            return self._parse_as_command(start)\n\n        return self.expression(\n            exp.Create(this=this, kind=\"TYPE\", replace=replace, expression=expression)"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-145758-postgres-dialect-create-type-fal/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"def test_\" tests/dialects/test_postgres.py | head -20; grep -n \"def test_ddl\" -A 6 tests/dialects/test_postgres.py", "description": "Find a Postgres test method to extend"}
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
…[39 chars elided]…
def test_json_extract(self):
1675:    def test_udt(self):
1686:    def test_round(self):
1704:    def test_datatype(self):
1708:    def test_locks(self):
1087:    def test_ddl(self):
1088-        # Checks that user-defined types are parsed into DataType instead of Identifier
1089-        self.parse_one("CREATE TABLE t (a udt)").this.expressions[0].args["kind"].assert_is(
1090-            exp.DataType
1091-        )
1092-
1093-        # Checks that OID is parsed into a DataType (ObjectIdentifier)
[tool_use Bash] {"command": "sed -n 1675,1686p tests/dialects/test_postgres.py", "description": "View test_udt to place a new test near it"}
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-145758-postgres-dialect-create-type-fal/base-1/tests/dialects/test_postgres.py", "old_string": "        _validate_udt('CAST(5 AS \"MyCatalog\".\"MySchema\".\"MyType\")')\n\n    def test_round(self):", "new_string": "        _validate_udt('CAST(5 AS \"MyCatalog\".\"MySchema\".\"MyType\")')\n\n    def 
…[130 chars elided]…
n            \"CREATE TYPE book_type AS ENUM('FICTION', 'NONFICTION')\",\n        )\n        self.validate_identity(\"CREATE TYPE public.mood AS ENUM('sad', 'ok', 'happy')\")\n        self.validate_identity(\"CREATE TYPE complex AS (r DOUBLE PRECISION, i DOUBLE PRECISION)\")\n        self.validate_identity(\"CREATE TYPE empty_type AS ()\", check_command_warning=True)\n\n    def test_round(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-145758-postgres-dialect-create-type-fal/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\np='tests/dialects/test_postgres.py'\ns=open(p).read()\nold='''        self.validate_identity(\n            \"CREATE TYPE book_type AS ENUM('FICTION', 'NONFICTION')\",\n            \"CREATE TYPE book_type AS ENUM('FICTION', 'NONFICTION')\",\n        )\n        self.validate_identity(\"CREATE TYPE public.mood AS ENUM('sad', 'ok', 'happy')\")\n        self.v
…[282 chars elided]…
)\n        self.validate_identity(\"CREATE TYPE public.mood AS ENUM('sad', 'ok', 'happy')\")\n        self.validate_identity(\"CREATE TYPE complex AS (r DOUBLE PRECISION, i DOUBLE PRECISION)\")\n'''\nassert s.count(old)==1\nopen(p,'w').write(s.replace(old,new))\nEOF\ngrep -n \"def validate_identity\" -A 3 tests/dialects/test_dialect.py", "description": "Simplify the new Postgres CREATE TYPE test"}
[tool_result] 53:    def validate_identity(
54-        self, sql, write_sql=None, pretty=False, check_command_warning=False, identify=False
55-    ):
56-        if check_command_warning:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run full project test suite"}
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
1106 passed, 17982 subtests passed in 53.72s
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"import sqlglot;print(sqlglot.__file__)\"; <work>/env-sqlglot/bin/python -m ruff check sqlglot/parser.py tests/dialects/test_postgres.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parser.py tests/dialects/test_postgres.py 2>&1 | tail -3; git status --short", "description": "Verify imported sqlglot path, lint, and format"}
[tool_result] ~/.cache/lithify/work/repo-b63a38b63828/20261026-145758-postgres-dialect-create-type-fal/base-1/sqlglot/__init__.py
All checks passed!
2 files already formatted
 M sqlglot/parser.py
 M tests/dialects/test_postgres.py
[assistant] `CREATE TYPE ... AS ENUM (...)` and `CREATE TYPE ... AS (attr type, ...)` now parse into `exp.Create(kind="TYPE")` and round-trip in Postgres. The full suite passes (1106 tests), and ruff check and format are clean.

**Change** (`sqlglot/parser.py`):
- `_parse_create` now checks for `TYPE` right after the `OR REPLACE` handling and hands off to a new `_parse_create_type`.
- `_parse_create_type` parses the name, then either an enum (a `DataType` of `ENUM` with string values) or a composite (a `Schema` of column definitions). Anything else falls back to `Command` as before.
- Because the change i
…[289 chars elided]…
hesis.** It comes out as `AS ENUM('FICTION', 'NONFICTION')`, not `AS ENUM ('FICTION', 'NONFICTION')`. That matches how sqlglot renders the `ENUM` data type elsewhere, and Postgres accepts it. The test asserts that form, so an exact-text round-trip of the spaced input will not match.
- **Empty composites still fall back to `Command`.** `CREATE TYPE t AS ()` is valid Postgres, but I left it on the fallback path, which keeps the original text.
- **Not handled:** `AS RANGE (...)` and `CREATE TYPE` without `AS` still fall back to `Command`, since they were not in scope.
- I did not commit anything.
