# trajectory base-1

final message:
`COLLATE` now parses inside nested types and on `CAST` targets, and round-trips in the default dialect. The full suite passes (1107 tests, including a new one) and `ruff format`/`ruff check` are clean. Changes are uncommitted in the worktree.

**What changed**

- **`sqlglot/expressions/datatypes.py`**: `DataType` gets an optional `collate` arg.
- **`sqlglot/generator.py`**: `datatype_sql` appends ` COLLATE <name>` when that arg is set.
- **`sqlglot/parser.py`**:
  - New helper `_parse_type_collate`, which only attaches a collation to a `DataType`.
  - It is applied to element types in `ARRAY(...)`, `ARRAY<...>`, `MAP<...>`, and `MAP[k => v]`.
  - It is applied to the target type in `CAST(x AS ... COLLATE ...)`.
- **`tests/dialects/test_dialect.py`**: new `test_collate_in_types` covering the nested, CAST, and ordinary-expression cases.

**Behaviour**

- `CAST(x AS VARCHAR(10) COLLATE "C")` and `CAST(x AS VARCHAR COLLATE "C")` now parse. The default dialect round-trips the first unchanged.
- `ARRAY<VARCHAR COLLATE "C">` and `MAP<... COLLATE ...>` in DDL now parse and round-trip.
- Struct fields were already working and still go through the column-constraint path.
- `x COLLATE "C"` and `x::VARCHAR COLLATE "C"` are untouched. The `::` form still binds the collation to the whole cast expression, as before.
- `DataType.build("varchar(100) collate 'en-ci'")` still drops the collation, which an existing test asserts.

**Limitation**

Some dialects override `datatype_sql` without calling super, so the collation is silently dropped there. For example, `CREATE TABLE t (x ARRAY(VARCHAR(10) COLLATE "C"))` in ClickHouse becomes `Array(String)`. Those inputs used to fail to parse, so this is not a regression. I did not change the overrides, since ClickHouse and similar targets have no type-level collation to emit. Say if you want it handled per dialect.

## events
[tool_use Bash] {"command": "grep -n \"COLLATE\\|_parse_column_def\\|def _parse_types\\|def _parse_cast\\|def _parse_struct_types\\|def _parse_column_ops\\|def _parse_field_def\\|def _parse_datatype\\|def _parse_primary\\|def _parse_unary\" sqlglot/parser.py | head -80", "description": "Locate COLLATE and type-parsing code in parser"}
[tool_result] 25 matches in 15 files:

1048:0:lambda self: self._parse_column_def(self._parse_column()),
1242:0:lambda self, **kwargs: self._parse_property_assignment(
1349:0:lambda self: self.expression(
6047:0:
6410:0:bool = False) -> exp.Expr | None:
6659:0:exp.Expr | None) -> exp.Expr | None:
6757:0:
7078:0:
7435:0:
7689:0:bool, safe: bool | None = None) -> exp.Expr:
8137:0:
8397:0:
8547:0:
913:0:exp.Collate,
sqlglot/parser.py:680:TokenType.COLLATE,
sqlglot/parser.py:827:TokenType.COLLATE,
sqlglot/parser.
…[101 chars elided]…
y:6983:return self._parse_column_def(this=self._parse_id_var(), computed_column=False)
sqlglot/parser.py:7079:return self._parse_column_def(self._parse_field(any_token=True))
sqlglot/parser.py:7081:def _parse_column_def(
sqlglot/parser.py:7450:def _parse_primary_key(
sqlglot/parser.py:8566:return self._parse_column_def_with_exists()
sqlglot/parser.py:8617:else self._parse_csv(self._parse_column_def_with_exists)
sqlglot/parser.py:8653:collate=self._match(TokenType.COLLATE) and self._parse_term(),
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-190039-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py", "offset": 6136, "limit": 150}
[tool_result] 6136	    def _parse_types(
6137	        self, check_func: bool = False, schema: bool = False, allow_identifiers: bool = True
6138	    ) -> exp.Expr | None:
6139	        index = self._index
6140	        this: exp.Expr | None = None
6141	
6142	        if self._match_set(self.TYPE_TOKENS):
6143	            type_token = self._prev.token_type
6144	        else:
6145	            type_token = None
6146	            identifier = allow_identifiers and self._parse_id_var(
6147	                any_token=Fal
…[6324 chars elided]…
     elif self._match_text_seq("WITH", "LOCAL", "TIME", "ZONE"):
6279	                maybe_func = False
6280	                this = exp.DataType(this=exp.DType.TIMESTAMPLTZ, expressions=expressions)
6281	            elif self._match_text_seq("WITHOUT", "TIME", "ZONE"):
6282	                maybe_func = False
6283	        elif type_token == TokenType.INTERVAL:
6284	            if self._curr.text.upper() in self.dialect.VALID_INTERVAL_UNITS:
6285	                unit = self._parse_var(upper=True)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-190039-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py", "offset": 7081, "limit": 50}
[tool_result] 7081	    def _parse_column_def(
7082	        self, this: exp.Expr | None, computed_column: bool = True
7083	    ) -> exp.Expr | None:
7084	        # column defs are not really columns, they're identifiers
7085	        if isinstance(this, exp.Column):
7086	            this = this.this
7087	
7088	        if not computed_column:
7089	            self._match(TokenType.ALIAS)
7090	
7091	        kind = self._parse_types(schema=True)
7092	
7093	        if self._match_text_seq("FOR", "ORDINALITY"):
7094
…[1275 chars elided]…
nt)
7118	            kind = self._parse_types()
7119	        elif (
7120	            kind
7121	            and self._match(TokenType.ALIAS, advance=False)
7122	            and (
7123	                not self.WRAPPED_TRANSFORM_COLUMN_CONSTRAINT
7124	                or self._next.token_type == TokenType.L_PAREN
7125	            )
7126	        ):
7127	            self._advance()
7128	            constraints.append(
7129	                self.expression(
7130	                    exp.ColumnConstraint(
[tool_use Bash] {"command": "grep -n \"COLLATE\\|collate\" sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -60", "description": "Find COLLATE references across core modules"}
[tool_result] 19 matches in 2 files:

sqlglot/generator.py:158:exp.CollateColumnConstraint: lambda self, e: f"COLLATE {self.sql(e, 'this')}",
sqlglot/generator.py:428:# Whether COLLATE is a function instead of a binary operator
sqlglot/generator.py:429:COLLATE_IS_FUNC = False
sqlglot/generator.py:2809:collate = self.sql(expression, "collate")
sqlglot/generator.py:2810:collate = f" COLLATE {collate}" if collate else ""
sqlglot/generator.py:2812:return f"{global_}{kind}{this}{expressions}{collate}"
sqlglot/gene
…[362 chars elided]…
urn f"ALTER COLUMN {this} {alter_set_type}{dtype}{collate}{using}"
sqlglot/parser.py:680:TokenType.COLLATE,
sqlglot/parser.py:827:TokenType.COLLATE,
sqlglot/parser.py:913:TokenType.COLLATE: exp.Collate,
sqlglot/parser.py:1242:"COLLATE": lambda self, **kwargs: self._parse_property_assignment(
sqlglot/parser.py:1349:"COLLATE": lambda self: self.expression(
sqlglot/parser.py:8137:if self._match(TokenType.COLLATE):
sqlglot/parser.py:8653:collate=self._match(TokenType.COLLATE) and self._parse_term(),
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -I -c \"\nimport sqlglot\ncases = [\n ('SELECT CAST(x AS VARCHAR(10) COLLATE \\\"C\\\")', 'duckdb'),\n ('SELECT CAST(x AS STRUCT<a VARCHAR COLLATE \\\"C\\\">)', 'bigquery'),\n ('SELECT CAST(x AS STRUCT<a STRING COLLATE \\\"C\\\">)', 'bigquery'),\n ('CREATE TABLE t (x STRUCT<a VARCHAR COLLATE \\\"C\\\">)', 
…[159 chars elided]…
x COLLATE \\\"C\\\" FROM t', 'duckdb'),\n ('SELECT CAST(x AS VARCHAR COLLATE \\\"C\\\")', 'duckdb'),\n]\nfor s, d in cases:\n    try:\n        e = sqlglot.parse_one(s, read=d)\n        print('OK  ', s, '->', e.sql(d))\n    except Exception as ex:\n        print('FAIL', s, type(ex).__name__, str(ex).splitlines()[0])\n\"\n", "description": "Reproduce COLLATE parse failures in nested and cast types"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=. $P -c \"\nimport sqlglot\ncases = [\n ('SELECT CAST(x AS VARCHAR(10) COLLATE \\\"C\\\")', 'duckdb'),\n ('SELECT CAST(x AS STRUCT<a VARCHAR COLLATE \\\"C\\\">)', 'bigquery'),\n ('CREATE TABLE t (x STRUCT<a VARCHAR COLLATE \\\"C\\\">)', 'duckdb'),\n ('CREATE TABLE t (x ARRAY<VARCHAR COLLATE \\\"C\\
…[136 chars elided]…
\n ('SELECT CAST(x AS VARCHAR COLLATE \\\"C\\\")', 'duckdb'),\n]\nfor s, d in cases:\n    try:\n        e = sqlglot.parse_one(s, read=d)\n        print('OK  ', s, '->', e.sql(d))\n    except Exception as ex:\n        print('FAIL', s, type(ex).__name__, str(ex).splitlines()[0])\n\"; sed -n 6285,6330p sqlglot/parser.py", "description": "Reproduce COLLATE parse failures and read rest of type parser"}
[tool_result] FAIL SELECT CAST(x AS VARCHAR(10) COLLATE "C") ParseError Invalid expression / Unexpected token. Line 1, Col: 41.
OK   SELECT CAST(x AS STRUCT<a VARCHAR COLLATE "C">) -> SELECT CAST(x AS STRUCT<a STRING COLLATE 'C'>)
OK   CREATE TABLE t (x STRUCT<a VARCHAR COLLATE "C">) -> CREATE TABLE t (x STRUCT(a TEXT COLLATE "C"))
FAIL CREATE TABLE t (x ARRAY<VARCHAR COLLATE "C">) ParseError Expecting >. Line 1, Col: 39.
OK   CREATE TABLE t (x VARCHAR(10) COLLATE "C") -> CREATE TABLE t (x TEXT COLLATE "C")
O
…[1417 chars elided]…
and not expressions:
                self._retreat(index)
                return None

            this = exp.DataType(
                this=exp.DType[type_token.name],
                expressions=expressions,
                nested=nested,
            )

            # Empty arrays/structs are allowed
            if values is not None:
                cls = exp.Struct if is_struct else exp.Array
                this = exp.cast(cls(expressions=values), this, copy=False)

        elif expressions:
[tool_use Bash] {"command": "sed -n 1345,1356p sqlglot/parser.py; echo ----; sed -n 8128,8150p sqlglot/parser.py; echo ----; grep -n \"class DataType\\b\\|class DataType(\" -A 12 sqlglot/expressions.py | head -30; echo ----; grep -n \"class CollateColumnConstraint\\|class Collate(\" -A 4 sqlglot/expressions.py; echo ----; grep -n \"def datatype_sql\" -A 40 sqlglot/generator.py | head -60; echo ----; grep -n \"def _parse_cast\" -A 40 sqlglot/parser.py | head -70", "description": "Inspect collate constraint, DataType class, datatype generator, cast parser"}
[tool_result]         "CHARACTER SET": lambda self: self.expression(
            exp.CharacterSetColumnConstraint(this=self._parse_var_or_string())
        ),
        "CHECK": lambda self: self._parse_check_constraint(),
        "COLLATE": lambda self: self.expression(
            exp.CollateColumnConstraint(this=self._parse_identifier() or self._parse_column())
        ),
        "COMMENT": lambda self: self.expression(
            exp.CommentColumnConstraint(this=self._parse_string())
        ),
        "CO
…[4261 chars elided]…
     self.dialect.FORMAT_MAPPING or self.dialect.TIME_MAPPING,
7720-                                self.dialect.FORMAT_TRIE or self.dialect.TIME_TRIE,
7721-                            )
7722-                        ),
7723-                        safe=safe,
7724-                    )
7725-                )
7726-
7727-                if isinstance(fmt, exp.AtTimeZone) and isinstance(this, exp.StrToTime):
7728-                    this.set("zone", fmt.args["zone"])
7729-                return this
[tool_use Bash] {"command": "grep -rn \"^class DataType(\\|^class CollateColumnConstraint\\|^class Collate(\" sqlglot/ ; F=$(grep -rln \"^class DataType(\" sqlglot/); grep -n \"^class DataType(\" -A 30 $F | head -45; sed -n 1723,1745p sqlglot/generator.py; git log --oneline -3 -- tests/dialects/test_dialect.py | head -3", "description": "Locate DataType class and read its args and generator tail"}
[tool_result] sqlglot/expressions/functions.py:166:class Collate(Expression, Binary, Func):
sqlglot/expressions/datatypes.py:173:class DataType(Expression):
sqlglot/expressions/constraints.py:68:class CollateColumnConstraint(Expression, ColumnConstraintKind):
173:class DataType(Expression):
174-    arg_types = {
175-        "this": True,
176-        "expressions": False,
177-        "nested": False,
178-        "values": False,
179-        "kind": False,
180-        "nullable": False,
181-    }
182-
183-    T
…[1230 chars elided]…
METZ,
            exp.DType.TIMESTAMPTZ,
        ):
            type_sql = f"{type_sql} WITH TIME ZONE"

        return type_sql

    def directory_sql(self, expression: exp.Directory) -> str:
        local = "LOCAL " if expression.args.get("local") else ""
        row_format = self.sql(expression, "row_format")
4bd7d1d02 fix(postgres)!: preserve NOT LIKE quantifiers during generation (#7611)
fd4810018 Fix(presto)!: generate "SUBSTR" instead of "SUBSTRING" for Substr expr (#7583)
dc461daa9 Fixup
[tool_use Bash] {"command": "grep -rn \"def datatype_sql\" sqlglot/ ; grep -n \"_parse_types(\" sqlglot/parser.py | wc -l; grep -n \"collate\" tests/dialects/*.py tests/test_*.py | head -30", "description": "Check datatype_sql overrides and existing collate tests"}
[tool_result] sqlglot/optimizer/simplify.py:1605:    def datatype_sql(self, e: exp.DataType) -> None:
sqlglot/generator.py:1683:    def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/generators/redshift.py:334:    def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/generators/clickhouse.py:517:    def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/generators/dremio.py:75:    def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/generators/fabric.py:78:    de
…[1255 chars elided]…
r(100) collate 'en-ci'").sql(), "VARCHAR(100)")
tests/test_parser.py:969:def test_collate(self):
tests/test_parser.py:970:collates = [
tests/test_parser.py:977:for collate_pair in collates:
tests/test_parser.py:978:collate_node = parse_one(
tests/test_parser.py:979:f"""SELECT * FROM t WHERE foo LIKE '%bar%' COLLATE {collate_pair[0]}"""
tests/test_parser.py:981:self.assertIsInstance(collate_node, exp.Collate)
tests/test_parser.py:982:self.assertIsInstance(collate_node.expression, collate_pair[1])
[tool_use Bash] {"command": "sed -n 1120,1135p tests/test_expressions.py; sed -n 1,5p tests/test_expressions.py >/dev/null; grep -n \"def build\" -A 3 sqlglot/expressions/datatypes.py | head; grep -n \"collate\" sqlglot/generators/mysql.py sqlglot/generators/postgres.py sqlglot/generators/snowflake.py | head; sed -n 960,990p tests/test_parser.py", "description": "Read existing collate test around DataType.build"}
[tool_result]         self.assertEqual(exp.DataType.build("HSTORE", dialect="postgres").sql(), "HSTORE")
        self.assertEqual(exp.DataType.build("NULL").sql(), "NULL")
        self.assertEqual(exp.DataType.build("NULL", dialect="bigquery").sql(), "NULL")
        self.assertEqual(exp.DataType.build("UNKNOWN").sql(), "UNKNOWN")
        self.assertEqual(exp.DataType.build("UNKNOWN", dialect="bigquery").sql(), "UNKNOWN")
        self.assertEqual(exp.DataType.build("UNKNOWN", dialect="snowflake").sql(), "UNKNO
…[1635 chars elided]…
 {collate_pair[0]}"""
            ).find(exp.Collate)
            self.assertIsInstance(collate_node, exp.Collate)
            self.assertIsInstance(collate_node.expression, collate_pair[1])

    def test_drop_column(self):
        ast = parse_one("ALTER TABLE tbl DROP COLUMN col")
        self.assertEqual(len(list(ast.find_all(exp.Table))), 1)
        self.assertEqual(len(list(ast.find_all(exp.Column))), 1)

    def test_udf_meta(self):
        ast = parse_one("YEAR(a) /* sqlglot.anonymous */")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-190039-parser-collate-is-not-handled-in/base-1/sqlglot/expressions/datatypes.py", "old_string": "        \"kind\": False,\n        \"nullable\": False,\n    }\n\n    Type: t.ClassVar[Type[DType]] = DType", "new_string": "        \"kind\": False,\n        \"nullable\": False,\n        \"collate\": False,\n    }\n\n    Type: t.ClassVar[Type[DType]] = DType"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-190039-parser-collate-is-not-handled-in/base-1/sqlglot/expressions/datatypes.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-190039-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py", "offset": 6330, "limit": 25}
[tool_result] 6330	        elif expressions:
6331	            this.set("expressions", expressions)
6332	
6333	        # https://materialize.com/docs/sql/types/list/#type-name
6334	        while self._match(TokenType.LIST):
6335	            this = exp.DataType(this=exp.DType.LIST, expressions=[this], nested=True)
6336	
6337	        index = self._index
6338	
6339	        # Postgres supports the INT ARRAY[3] syntax as a synonym for INT[3]
6340	        matched_array = self._match(TokenType.ARRAY)
6341	
6342	     
…[142 chars elided]…
KET)
6345	
6346	            if (not matched_l_bracket and not matched_array) or (
6347	                datatype_token == TokenType.ARRAY and self._match(TokenType.R_BRACKET)
6348	            ):
6349	                # Postgres allows casting empty arrays such as ARRAY[]::INT[],
6350	                # not to be confused with the fixed size array parsing
6351	                break
6352	
6353	            matched_array = False
6354	            values = self._parse_csv(self._parse_disjunction) or None
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-190039-parser-collate-is-not-handled-in/base-1/sqlglot/generator.py", "old_string": "            type_sql = f\"{type_sql} WITH TIME ZONE\"\n\n        return type_sql", "new_string": "            type_sql = f\"{type_sql} WITH TIME ZONE\"\n\n        collate = self.sql(expression, \"collate\")\n        if collate:\n            type_sql = f\"{type_sql} COLLATE {collate}\"\n\n        return type_sql"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-190039-parser-collate-is-not-handled-in/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-190039-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py", "old_string": "    def _parse_types(\n        self, check_func: bool = False, schema: bool = False, allow_identifiers: bool = True\n    ) -> exp.Expr | None:\n        index = self._index", "new_string": "    def _parse_type_collate(se
…[8 chars elided]…
: exp.Expr | None) -> exp.Expr | None:\n        if isinstance(this, exp.DataType) and self._match(TokenType.COLLATE):\n            this.set(\"collate\", self._parse_identifier() or self._parse_column())\n        return this\n\n    def _parse_types(\n        self, check_func: bool = False, schema: bool = False, allow_identifiers: bool = True\n    ) -> exp.Expr | None:\n        index = self._index"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-190039-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\np = \"sqlglot/parser.py\"\ns = open(p).read()\n\ndef rep(old, new, count=1):\n    global s\n    n = s.count(old)\n    assert n == count, (n, old[:80])\n    s = s.replace(old, new)\n\n# MAP[key => value]\nrep(\"\"\"            key_type = self._parse_types(\n                check_func=check_func, schema=schema, allow_identifiers=allow_identifiers\n         
…[2213 chars elided]…
         )\n\n            if not self._match(TokenType.GT):\"\"\")\n\n# CAST(x AS type COLLATE ...)\nrep(\"\"\"        fmt = None\n        to = self._parse_types()\n\"\"\", \"\"\"        fmt = None\n        to = self._parse_type_collate(self._parse_types())\n\"\"\")\nopen(p, \"w\").write(s)\nprint(\"ok\")\nEOF\ngit diff --stat", "description": "Apply parser edits for nested and CAST type COLLATE"}
[tool_result] ok
 sqlglot/expressions/datatypes.py |  1 +
 sqlglot/generator.py             |  4 ++++
 sqlglot/parser.py                | 31 ++++++++++++++++++++++---------
 3 files changed, 27 insertions(+), 9 deletions(-)
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=. $P -c \"\nimport sqlglot\ncases = [\n ('SELECT CAST(x AS VARCHAR(10) COLLATE \\\"C\\\")', 'duckdb'),\n ('SELECT CAST(x AS VARCHAR COLLATE \\\"C\\\")', 'duckdb'),\n ('SELECT CAST(x AS STRUCT<a VARCHAR COLLATE \\\"C\\\">)', 'bigquery'),\n ('CREATE TABLE t (x STRUCT<a VARCHAR COLLATE \\\"C\\\">)', '
…[641 chars elided]…
e(s, read=d)\n        print('OK  ', s, '->', e.sql(d))\n    except Exception as ex:\n        print('FAIL', s, type(ex).__name__, str(ex).splitlines()[0])\n\"; PYTHONPATH=. $P -c \"\nimport sqlglot\nprint(repr(sqlglot.parse_one('SELECT CAST(x AS VARCHAR(10) COLLATE \\\"C\\\")', read='duckdb').find(sqlglot.exp.DataType).args))\n\"", "description": "Verify new COLLATE parse and round-trip behaviour"}
[tool_result] OK   SELECT CAST(x AS VARCHAR(10) COLLATE "C") -> SELECT CAST(x AS TEXT COLLATE "C")
OK   SELECT CAST(x AS VARCHAR COLLATE "C") -> SELECT CAST(x AS TEXT COLLATE "C")
OK   SELECT CAST(x AS STRUCT<a VARCHAR COLLATE "C">) -> SELECT CAST(x AS STRUCT<a STRING COLLATE 'C'>)
OK   CREATE TABLE t (x STRUCT<a VARCHAR COLLATE "C">) -> CREATE TABLE t (x STRUCT(a TEXT COLLATE "C"))
OK   CREATE TABLE t (x ARRAY<VARCHAR COLLATE "C">) -> CREATE TABLE t (x ARRAY<STRING COLLATE 'C'>)
OK   CREATE TABLE t (x ARRAY(
…[222 chars elided]…
CHAR(10) COLLATE "C") -> CREATE TABLE t (x TEXT COLLATE "C")
OK   SELECT x COLLATE "C" FROM t -> SELECT x COLLATE "C" FROM t
OK   SELECT x::VARCHAR COLLATE "C" FROM t -> SELECT CAST(x AS VARCHAR) COLLATE "C" FROM t
OK   SELECT CAST(x AS ARRAY<VARCHAR COLLATE "C">) FROM t -> SELECT CAST(x AS ARRAY<STRING COLLATE 'C'>) FROM t
OK   SELECT CAST(x AS VARCHAR COLLATE "C") FROM t -> SELECT CAST(x AS VARCHAR COLLATE "C") FROM t
{'this': <DType.TEXT: 'TEXT'>, 'collate': Identifier(this='C', quoted=True)}
[tool_use Bash] {"command": "for f in redshift clickhouse dremio fabric singlestore risingwave hive materialize snowflake postgres exasol mysql; do echo \"== $f\"; awk '/def datatype_sql/{p=1} p{print} /return/{if(p){p=0}}' sqlglot/generators/$f.py | head -12 | grep -n \"super\\|return\\|def \" ; done", "description": "Check which dialect datatype_sql overrides call super"}
[tool_result] == redshift
1:    def datatype_sql(self, expression: exp.DataType) -> str:
== clickhouse
1:    def datatype_sql(self, expression: exp.DataType) -> str:
9:            dtype = super().datatype_sql(expression)
== dremio
1:    def datatype_sql(self, expression: exp.DataType) -> str:
11:        return super().datatype_sql(expression)
== fabric
1:    def datatype_sql(self, expression: exp.DataType) -> str:
8:        return super().datatype_sql(expression)
== singlestore
1:    def datatype_sql(self, ex
…[426 chars elided]…
e)} LIST"
== snowflake
1:    def datatype_sql(self, expression: exp.DataType) -> str:
9:                return "FLOAT"
== postgres
1:    def datatype_sql(self, expression: exp.DataType) -> str:
5:                return f"{self.expressions(expression, flat=True)}[{values}]"
== exasol
1:    def datatype_sql(self, expression: exp.DataType) -> str:
5:            return "TIMESTAMP WITH LOCAL TIME ZONE"
== mysql
1:    def datatype_sql(self, expression: exp.DataType) -> str:
8:            return "TEXT"
[tool_use Bash] {"command": "timeout 900 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no -x 2>&1 | tail -30", "description": "Run full pytest suite against the change", "timeout": 900000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run full pytest suite against the change", "timeout": 900000}
[tool_result] ................................................................ [  5%]
........................... [  8%]
............. [  9%]
........................................................................................................................................ [ 21%]
............................................................................................ [ 30%]
.......................... [ 32%]
.......................................... [ 36%]
............................................
…[302 chars elided]…
...................................... [ 70%]
..................................... [ 73%]
................................................................................................................... [ 83%]
................ [ 85%]
..................................................................................................................................................................                                                 [100%]
1106 passed, 17998 subtests passed in 46.34s
[tool_use Bash] {"command": "grep -n \"    def test_\" tests/dialects/test_dialect.py | head -80 | tail -50; grep -n \"def test_cast\" -A 6 tests/dialects/test_dialect.py | head -12", "description": "Locate test method layout in dialect tests"}
[tool_result] 3295:0:
3324:0:
3436:0:
3483:0:
3520:0:
3549:0:
3555:0:
3589:0:
3604:0:
3634:0:
3685:0:
3708:0:
3727:0:
3750:0:
3871:0:
3902:0:
3993:0:
4020:0:
4036:0:
4059:0:
4086:0:
4156:0:
4214:0:
4230:0:
4243:0:
4287:0:
4317:0:
4355:0:
4388:0:
4419:0:
4450:0:
4481:0:
4512:0:
4543:0:
4574:0:
4611:0:
4649:0:
4701:0:
4717:0:
4747:0:
4833:0:
4852:0:
4865:0:
4878:0:
4892:0:
4907:0:
4920:0:
4950:0:
4970:0:
4983:0:
226:    def test_cast(self):
227-        self.validate_all(
228-            "CAST(a AS TEXT)",
229-            write={
230-                "bigquery": "CAST(a AS STRING)",
231-                "clickhouse": "CAST(a AS Nullable(String))",
232-                "drill": "CAST(a AS VARCHAR)",
--
3251:    def test_cast_to_user_defined_type(self):
3252-        self.validate_identity("CAST(x AS some_udt(1234))")
3253-
3254-        self.validate_all(
[tool_use Bash] {"command": "sed -n 3251,3275p tests/dialects/test_dialect.py", "description": "Read nearby test method for style"}
[tool_result]     def test_cast_to_user_defined_type(self):
        self.validate_identity("CAST(x AS some_udt(1234))")

        self.validate_all(
            "CAST(x AS some_udt)",
            write={
                "": "CAST(x AS some_udt)",
                "oracle": "CAST(x AS some_udt)",
                "postgres": "CAST(x AS some_udt)",
                "presto": "CAST(x AS some_udt)",
                "teradata": "CAST(x AS some_udt)",
                "tsql": "CAST(x AS some_udt)",
            },
        )

        with self.assertRaises(ParseError):
            parse_one("CAST(x AS some_udt)", read="bigquery")

    def test_qualify(self):
        self.validate_all(
            "SELECT * FROM t QUALIFY COUNT(*) OVER () > 1",
            write={
                "duckdb": "SELECT * FROM t QUALIFY COUNT(*) OVER () > 1",
                "snowflake": "SELECT * FROM t QUALIFY COUNT(*) OVER () > 1",
                "clickhouse": "SELECT * FROM t QUALIFY COUNT(*) OVER () > 1",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-190039-parser-collate-is-not-handled-in/base-1/tests/dialects/test_dialect.py", "old_string": "        with self.assertRaises(ParseError):\n            parse_one(\"CAST(x AS some_udt)\", read=\"bigquery\")\n\n    def test_qualify(self):", "new_string": "        with self.assertRaises(ParseError):\n  
…[366 chars elided]…
 t (x MAP(TEXT COLLATE \"C\", TEXT COLLATE \"en\"))')\n        self.validate_identity('SELECT x COLLATE \"C\" FROM t')\n        self.validate_identity('SELECT CAST(x AS TEXT) COLLATE \"C\" FROM t')\n\n        self.assertEqual(\n            parse_one('SELECT CAST(x AS VARCHAR(10) COLLATE \"C\")').sql(),\n            'SELECT CAST(x AS TEXT COLLATE \"C\")',\n        )\n\n    def test_qualify(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-190039-parser-collate-is-not-handled-in/base-1/tests/dialects/test_dialect.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin; $P/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_dialect.py -k collate 2>&1 | tail -15; ls $P | grep -i \"ruff\\|mypy\"; $P/ruff format --check sqlglot tests 2>&1 | tail -5; $P/ruff check sqlglot tests 2>&1 | tail -3", "description": "Run new collate test and lint/format checks"}
[tool_result]         self.validate_identity('CREATE TABLE t (x ARRAY<TEXT COLLATE "C">)')
>       self.validate_identity('CREATE TABLE t (x MAP(TEXT COLLATE "C", TEXT COLLATE "en"))')

tests/dialects/test_dialect.py:3273: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/dialects/test_dialect.py:63: in validate_identity
    self.assertEqual(
E   AssertionError: 'CREATE TABLE t (x MAP(TEXT COLLATE "C", TEXT COLLATE "en"))' != 'CREATE TABLE t (x MAP<TEXT COLLATE "C", TEXT 
…[129 chars elided]…
                ^
E   + CREATE TABLE t (x MAP<TEXT COLLATE "C", TEXT COLLATE "en">)
E   ?                      ^                                   ^
=========================== short test summary info ============================
FAILED tests/dialects/test_dialect.py::TestDialect::test_collate_in_types - A...
1 failed, 98 deselected in 0.08s
dmypy  374B
mypy  370B
mypyc  353B
ruff  22.5M
Would reformat: sqlglot/parser.py
1 file would be reformatted, 235 files already formatted
All checks passed!
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-190039-parser-collate-is-not-handled-in/base-1/tests/dialects/test_dialect.py", "old_string": "        self.validate_identity('CREATE TABLE t (x MAP(TEXT COLLATE \"C\", TEXT COLLATE \"en\"))')", "new_string": "        self.validate_identity('CREATE TABLE t (x MAP<TEXT COLLATE \"C\", TEXT COLLATE \"en\">)')"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-190039-parser-collate-is-not-handled-in/base-1/tests/dialects/test_dialect.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin; $P/ruff format sqlglot/parser.py && git diff --stat && $P/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_dialect.py -k collate 2>&1 | tail -3 && $P/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; $P/ruff format --check sqlglot tests | tail -1; $P/ruff check sqlglot tests | tail -1; git diff sqlglot/parser.py | head -120", "description": "Format parser, rerun collate and full tests, show diff", "timeout": 900000}
[tool_result] 1 file reformatted
sqlglot/expressions/datatypes.py |  1 +
 sqlglot/generator.py             |  4 ++++
 sqlglot/parser.py                | 35 ++++++++++++++++++++++++++---------
 tests/dialects/test_dialect.py   | 13 +++++++++++++
 4 files changed, 44 insertions(+), 9 deletions(-)
=========================== short test summary info ============================
FAILED tests/dialects/test_dialect.py::TestDialect::test_collate_in_types - A...
1 failed, 98 deselected in 0.11s
FAILED tests/dialects/t
…[2739 chars elided]…
                  schema=schema,
  +                            allow_identifiers=allow_identifiers,
  +                        )
                       )
                   )
   
  @@ -7696,7 +7713,7 @@ class Parser:
  -        to = self._parse_types()
  +        to = self._parse_type_collate(self._parse_types())
   
           default = None
           if self._match(TokenType.DEFAULT):
  +26 -9
[This command modified 1 file you've previously read: sqlglot/parser.py. Call Read before editing.]
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_dialect.py -k collate 2>&1 | grep -B2 \"^E \" | head -20", "description": "Show failing assertion detail for collate test"}
[tool_result]             'SELECT CAST(x AS TEXT COLLATE "C")',
        )
E       AssertionError: 'SELECT CAST(x AS VARCHAR(10) COLLATE "C")' != 'SELECT CAST(x AS TEXT COLLATE "C")'
E       - SELECT CAST(x AS VARCHAR(10) COLLATE "C")
E       ?                  ^^^^^^^^^^^
E       + SELECT CAST(x AS TEXT COLLATE "C")
E       ?                  ^^^^
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-190039-parser-collate-is-not-handled-in/base-1/tests/dialects/test_dialect.py", "old_string": "        self.validate_identity('CAST(x AS TEXT COLLATE \"C\")')\n        self.validate_identity('CAST(x AS ARRAY<TEXT COLLATE \"C\">)')", "new_string": "        self.validate_identity('CAST(x AS VARCHAR(10) COLLATE \"C\")')\n        self.validate_identity('CAST(x AS ARRAY<TEXT COLLATE \"C\">)')"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-190039-parser-collate-is-not-handled-in/base-1/tests/dialects/test_dialect.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"def test_collate_in_types\" -A 12 tests/dialects/test_dialect.py", "description": "Show edited test block"}
[tool_result] 3269:    def test_collate_in_types(self):
3270-        self.validate_identity('CAST(x AS VARCHAR(10) COLLATE "C")')
3271-        self.validate_identity('CAST(x AS ARRAY<TEXT COLLATE "C">)')
3272-        self.validate_identity('CREATE TABLE t (x ARRAY<TEXT COLLATE "C">)')
3273-        self.validate_identity('CREATE TABLE t (x MAP<TEXT COLLATE "C", TEXT COLLATE "en">)')
3274-        self.validate_identity('SELECT x COLLATE "C" FROM t')
3275-        self.validate_identity('SELECT CAST(x AS TEXT) COLLATE "C" FROM t')
3276-
3277-        self.assertEqual(
3278-            parse_one('SELECT CAST(x AS VARCHAR(10) COLLATE "C")').sql(),
3279-            'SELECT CAST(x AS TEXT COLLATE "C")',
3280-        )
3281-
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-190039-parser-collate-is-not-handled-in/base-1/tests/dialects/test_dialect.py", "old_string": "        self.validate_identity('SELECT CAST(x AS TEXT) COLLATE \"C\" FROM t')\n\n        self.assertEqual(\n            parse_one('SELECT CAST(x AS VARCHAR(10) COLLATE \"C\")').sql(),\n            'SELECT CAST(x AS TEXT COLLATE \"C\")',\n        )\n", "new_string": "        self.validate_identity('SELECT CAST(x AS TEXT) COLLATE \"C\" FROM t')\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-190039-parser-collate-is-not-handled-in/base-1/tests/dialects/test_dialect.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin; $P/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; $P/ruff format --check sqlglot tests | tail -1; $P/ruff check sqlglot tests | tail -1; mkdir -p /tmp/orig_sqlglot_cmp && git archive HEAD sqlglot | tar -x -C /tmp/orig_sqlglot_cmp && cd /tmp/orig_sqlglot_cmp && PYTHONPATH=. $P/python -c \"\nimport sqlglot\nfor s,d in [('SELECT x::VARCHAR COLLATE \\\"C\\\" FROM t','postgres'),('SELECT x COLLATE \\\"C\\\" FROM t','duckdb'),('SELECT CAST(x AS VARCHAR) COLLATE \\\"C\\\" FROM t','duckdb')]:\n    print(sqlglot.parse_one(s, read=d).sql(d))\n\"", "description": "Rerun tests, lint, and compare ordinary COLLATE against original HEAD", "timeout": 900000}
[tool_result] ........................................................                                                [100%]
1107 passed, 17998 subtests passed in 47.97s
236 files already formatted
All checks passed!
SELECT CAST(x AS VARCHAR) COLLATE "C" FROM t
SELECT x COLLATE "C" FROM t
SELECT CAST(x AS TEXT) COLLATE "C" FROM t
Shell cwd was reset to ~/.cache/lithify/work/repo-6e430de19896/20261029-190039-parser-collate-is-not-handled-in/base-1
[tool_use Bash] {"command": "rm -rf /tmp/orig_sqlglot_cmp; cd ~/.cache/lithify/work/repo-6e430de19896/20261029-190039-parser-collate-is-not-handled-in/base-1 && git status --short", "description": "Remove temp comparison copy and show changed files"}
[tool_result]  M sqlglot/expressions/datatypes.py
 M sqlglot/generator.py
 M sqlglot/parser.py
 M tests/dialects/test_dialect.py
[assistant] `COLLATE` now parses inside nested types and on `CAST` targets, and round-trips in the default dialect. The full suite passes (1107 tests, including a new one) and `ruff format`/`ruff check` are clean. Changes are uncommitted in the worktree.

**What changed**

- **`sqlglot/expressions/datatypes.py`**: `DataType` gets an optional `collate` arg.
- **`sqlglot/generator.py`**: `datatype_sql` appends ` COLLATE <name>` when that arg is set.
- **`sqlglot/parser.py`**:
  - New helper `_parse_type_collate`, which only attaches a collation to a `DataType`.
  - It is applied to element types in `ARRAY(.
…[670 chars elided]…
e collation to the whole cast expression, as before.
- `DataType.build("varchar(100) collate 'en-ci'")` still drops the collation, which an existing test asserts.

**Limitation**

Some dialects override `datatype_sql` without calling super, so the collation is silently dropped there. For example, `CREATE TABLE t (x ARRAY(VARCHAR(10) COLLATE "C"))` in ClickHouse becomes `Array(String)`. Those inputs used to fail to parse, so this is not a regression. I did not change the overrides, since ClickHouse and similar targets have no type-level collation to emit. Say if you want it handled per dialect.
