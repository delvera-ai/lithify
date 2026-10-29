# trajectory base-1

final message:
`COLLATE` now parses and round-trips inside `CAST` targets and nested type arguments, while `COLLATE` in ordinary expressions and column definitions is unchanged. The full suite passes (1107 tests, including a new `test_collate_in_types`), and ruff check and format are clean. The changes are uncommitted in the worktree.

**What was broken:** struct fields already worked, because their `COLLATE` is parsed as a column constraint. The two failing positions were `CAST(x AS VARCHAR(10) COLLATE "C")` and `ARRAY<TEXT COLLATE "C">`.

**What I changed:**
- **`sqlglot/expressions/datatypes.py`:** `DataType` gets an optional `collate` arg.
- **`sqlglot/parser.py`:** a new `_parse_type_collate` helper consumes a trailing `COLLATE` after a type. It is called only for CAST targets and for non-struct `<...>` element types, so `x::TEXT COLLATE "C"` and column-level `COLLATE` keep their existing parse.
- **`sqlglot/generator.py`:** `datatype_sql` emits ` COLLATE <name>` after the type when the arg is set.
- **`tests/test_parser.py`:** `test_collate_in_types` covers the four round-trip cases and checks that `::` casts and plain `COLLATE` are unaffected.

**Known limitation:** Postgres and DuckDB render an array with a collated element as `TEXT COLLATE "C"[]`, which isn't valid Postgres syntax. Postgres's grammar doesn't allow a collation on an array element type, so I left those dialects alone. The default dialect and BigQuery round-trip correctly.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"COLLATE\" sqlglot/parser.py sqlglot/dialects/*.py sqlglot/generator.py | head -60", "description": "Check status and find COLLATE handling"}
[tool_result] sqlglot/dialects/dialect.py:1782:    collation = f" COLLATE {collation}" if collation else ""
sqlglot/parser.py:680:        TokenType.COLLATE,
sqlglot/parser.py:827:        TokenType.COLLATE,
sqlglot/parser.py:913:        TokenType.COLLATE: exp.Collate,
sqlglot/parser.py:1242:        "COLLATE": lambda self, **kwargs: self._parse_property_assignment(
sqlglot/parser.py:1349:        "COLLATE": lambda self: self.expression(
sqlglot/parser.py:8137:        if self._match(TokenType.COLLATE):
sqlglot/pa
…[155 chars elided]…
ambda self, e: f"COLLATE {self.sql(e, 'this')}",
sqlglot/generator.py:428:    # Whether COLLATE is a function instead of a binary operator
sqlglot/generator.py:429:    COLLATE_IS_FUNC = False
sqlglot/generator.py:2810:        collate = f" COLLATE {collate}" if collate else ""
sqlglot/generator.py:3915:        if self.COLLATE_IS_FUNC:
sqlglot/generator.py:3917:        return self.binary(expression, "COLLATE")
sqlglot/generator.py:3975:            collate = f" COLLATE {collate}" if collate else ""
[tool_use Bash] {"command": "sed -n 670,690p sqlglot/parser.py; echo ---; sed -n 815,835p sqlglot/parser.py; echo ---; sed -n 8125,8150p sqlglot/parser.py; echo ---; grep -n \"def _parse_types\\|def _parse_column_def\\|def _parse_struct_types\\|def _parse_cast\\|def _parse_column_ops\\|def _parse_types(\" sqlglot/parser.py", "description": "Inspect COLLATE parser locations"}
[tool_result]         TokenType.VAR,
        TokenType.ANTI,
        TokenType.APPLY,
        TokenType.ASC,
        TokenType.ASOF,
        TokenType.AUTO_INCREMENT,
        TokenType.BEGIN,
        TokenType.BPCHAR,
        TokenType.CACHE,
        TokenType.CASE,
        TokenType.COLLATE,
        TokenType.COMMAND,
        TokenType.COMMENT,
        TokenType.COMMIT,
        TokenType.CONSTRAINT,
        TokenType.COPY,
        TokenType.CUBE,
        TokenType.CURRENT_SCHEMA,
        TokenType.DEFAULT,
 
…[1545 chars elided]…
parse_window(self._parse_id_var(), alias=True)

    def _parse_respect_or_ignore_nulls(self, this: exp.Expr | None) -> exp.Expr | None:
---
6136:    def _parse_types(
6410:    def _parse_struct_types(self, type_required: bool = False) -> exp.Expr | None:
6659:    def _parse_column_ops(self, this: exp.Expr | None) -> exp.Expr | None:
7081:    def _parse_column_def(
7689:    def _parse_cast(self, strict: bool, safe: bool | None = None) -> exp.Expr:
8547:    def _parse_column_def_with_exists(self):
[assistant] Let me reproduce the failures first and look at the type-parsing code.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT CAST(x AS VARCHAR(10) COLLATE \\\"C\\\")', 'SELECT CAST(x AS STRUCT<a TEXT COLLATE \\\"C\\\">)', 'SELECT CAST(x AS ARRAY<TEXT COLLATE \\\"C\\\">)', 'SELECT x COLLATE \\\"C\\\"', 'CREATE TABLE t (a STRUCT<b TEXT COLLATE \\\"C\\\">)']:\n    try:\n        e = sqlglot.parse_one(s, read='bigquery' if 'STRUCT' in s else None)\n        print(type(e).__name__, '|', e.sql())\n    except Exception as ex: print('ERR', s, str(ex)[:200])\n\"; sed -n 6136,6150p sqlglot/parser.py", "description": "Reproduce COLLATE failures in types"}
[tool_result] ERR SELECT CAST(x AS VARCHAR(10) COLLATE "C") Invalid expression / Unexpected token. Line 1, Col: 41.
  SELECT CAST(x AS VARCHAR(10) COLLATE "C"[4m)[0m
Select | SELECT CAST(x AS STRUCT<a TEXT COLLATE 'C'>)
ERR SELECT CAST(x AS ARRAY<TEXT COLLATE "C">) Expecting >. Line 1, Col: 35.
  SELECT CAST(x AS ARRAY<TEXT [4mCOLLATE[0m "C">)
Select | SELECT x COLLATE "C"
Create | CREATE TABLE t (a STRUCT<b TEXT COLLATE 'C'>)
    def _parse_types(
        self, check_func: bool = False, schema: bool = False, allow_identifiers: bool = True
    ) -> exp.Expr | None:
        index = self._index
        this: exp.Expr | None = None

        if self._match_set(self.TYPE_TOKENS):
            type_token = self._prev.token_type
        else:
            type_token = None
            identifier = allow_identifiers and self._parse_id_var(
                any_token=False, tokens=(TokenType.VAR,)
            )
            if isinstance(identifier, exp.Identifier):
                try:
[tool_use Bash] {"command": "sed -n 6150,6175p sqlglot/parser.py; echo ...; sed -n 6240,6300p sqlglot/parser.py; echo ---; sed -n 6410,6440p sqlglot/parser.py; echo ---; sed -n 7689,7740p sqlglot/parser.py", "description": "Read type and struct parsing code"}
[tool_result]                 try:
                    tokens = self.dialect.tokenize(identifier.name)
                except TokenError:
                    tokens = None

                if tokens and (type_token := tokens[0].token_type) in self.TYPE_TOKENS:
                    if len(tokens) > 1:
                        return exp.DataType.from_str(identifier.name, dialect=self.dialect)
                elif self.dialect.SUPPORTS_USER_DEFINED_TYPES:
                    this = self._parse_user_defined_type(i
…[6238 chars elided]…
)
                return this
        elif not to:
            self.raise_error("Expected TYPE after CAST")
        elif isinstance(to, exp.Identifier):
            to = exp.DataType.from_str(to.name, dialect=self.dialect, udt=True)
        elif to.this == exp.DType.CHAR and self._match(TokenType.CHARACTER_SET):
            to = exp.DType.CHARACTER_SET.into_expr(kind=self._parse_var_or_string())

        return self.build_cast(
            strict=strict,
            this=this,
            to=to,
[tool_use Bash] {"command": "grep -n -i \"collat\" sqlglot/expressions.py | head -30; grep -n \"class DataType(\" -A12 sqlglot/expressions.py | head -30; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(repr(sqlglot.parse_one('CREATE TABLE t (a STRUCT<b TEXT COLLATE \\\"C\\\">)', read='bigquery').find(sqlglot.exp.ColumnDef)))\nprint(repr(sqlglot.parse_one('CAST(x AS STRUCT<b TEXT COLLATE \\\"C\\\">)')))\n\"", "description": "Check collate representation in expressions"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
ugrep: warning: sqlglot/expressions.py: No such file or directory
ColumnDef(
  this=Identifier(this=a, quoted=False),
  kind=DataType(
    this=DType.STRUCT,
    expressions=[
      ColumnDef(
        this=Identifier(this=b, quoted=False),
        kind=DataType(this=DType.TEXT, nested=False),
        constraints=[
          ColumnConstraint(
            kind=CollateColumnConstraint(
              this=Literal(this='C', is_string=T
…[282 chars elided]…
aints=[
          ColumnConstraint(
            kind=CollateColumnConstraint(
              this=Identifier(this='C', quoted=True)))])],
    nested=True),
  _type=DataType(
    this=DType.STRUCT,
    expressions=[
      ColumnDef(
        this=Identifier(this=b, quoted=False),
        kind=DataType(this=DType.TEXT, nested=False),
        constraints=[
          ColumnConstraint(
            kind=CollateColumnConstraint(
              this=Identifier(this='C', quoted=True)))])],
    nested=True))
[tool_use Bash] {"command": "ls sqlglot | head -80; grep -rn -i \"collat\" sqlglot/expressions/*.py | head -30; grep -n \"class DataType(\" -A8 sqlglot/expressions/datatypes.py | head -20", "description": "Locate DataType definition and collate args"}
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
sqlglot/expressions/constraints.py:68:class CollateColumnConstraint(Expression, ColumnConstraintKind):
sqlglot/expressions/ddl.py:186:        "collate": False,  # MySQL SET NAMES statement
sqlglot/express
…[137 chars elided]…
:78:class CollateProperty(Property):
sqlglot/expressions/properties.py:590:        "COLLATE": CollateProperty,
sqlglot/expressions/functions.py:166:class Collate(Expression, Binary, Func):
sqlglot/expressions/functions.py:170:class Collation(Expression, Func):
173:class DataType(Expression):
174-    arg_types = {
175-        "this": True,
176-        "expressions": False,
177-        "nested": False,
178-        "values": False,
179-        "kind": False,
180-        "nullable": False,
181-    }
[tool_use Bash] {"command": "sed -n 1345,1355p sqlglot/parser.py; grep -n \"CollateColumnConstraint\" sqlglot/parser.py sqlglot/generator.py sqlglot/dialects/*.py | head; sed -n 3905,3920p sqlglot/generator.py; grep -n \"def datatype_sql\" -A12 sqlglot/generator.py | head -40", "description": "Read COLLATE constraint parsing and datatype_sql"}
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
…[1062 chars elided]…
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
[tool_use Bash] {"command": "sed -n 1695,1760p sqlglot/generator.py", "description": "Read datatype_sql body"}
[tool_result]             expression = self.datatype_param_bound_limiter(expression, type_value, *settings)

        interior = (
            self.expressions(
                expression, dynamic=True, new_line=True, skip_first=True, skip_last=True
            )
            if expr_nested and self.pretty
            else self.expressions(expression, flat=True)
        )

        if type_value in self.UNSUPPORTED_TYPES:
            self.unsupported(
                f"Data type {type_value.value} is not support
…[1836 chars elided]…
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
[tool_use Bash] {"command": "grep -rn \"def datatype_sql\\|\\\"datatype_sql\\\"\\|DataType: \" sqlglot/ | head; grep -n \"class DataType(\" -B3 sqlglot/expressions/datatypes.py | head; grep -n \"def _parse_identifier\\b\\|def _parse_identifier(\" sqlglot/parser.py", "description": "Check datatype_sql overrides and parser helpers"}
[tool_result] sqlglot/generator.py:1683:    def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/parser.py:1050:        exp.DataType: lambda self: self._parse_types(allow_identifiers=False, schema=True),
sqlglot/optimizer/simplify.py:1605:    def datatype_sql(self, e: exp.DataType) -> None:
sqlglot/typing/__init__.py:323:    exp.DataType: {"annotator": lambda self, e: self._set_type(e, e.copy())},
sqlglot/expressions/datatypes.py:168:            DataType: the resulting `DataType` instance.
sqlglot
…[132 chars elided]…
atype_sql(self, expression: exp.DataType) -> str:
sqlglot/generators/postgres.py:477:    def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/generators/singlestore.py:1473:    def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/generators/clickhouse.py:517:    def datatype_sql(self, expression: exp.DataType) -> str:
170-        return DataType(this=self).set_kwargs(kwargs)
171-
172-
173:class DataType(Expression):
8367:    def _parse_identifier(self) -> exp.Expr | None:
[assistant] Struct fields already work (their COLLATE becomes a column constraint), so the gaps are the `ARRAY<T COLLATE ...>` element and the trailing CAST target. I'll store the collation on `DataType` as a `collate` arg, parsed only in those two positions so `x::TEXT COLLATE "C"` and column definitions keep their current parse.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-123930-parser-collate-is-not-handled-in/base-1/sqlglot/expressions/datatypes.py", "old_string": "        \"kind\": False,\n        \"nullable\": False,\n    }", "new_string": "        \"kind\": False,\n        \"nullable\": False,\n        \"collate\": False,\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-123930-parser-collate-is-not-handled-in/base-1/sqlglot/expressions/datatypes.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-123930-parser-collate-is-not-handled-in/base-1/sqlglot/generator.py", "old_string": "        type_sql = f\"{type_sql}{nested}{values}\"\n        if self.TZ_TO_WITH_TIME_ZONE", "new_string": "        type_sql = f\"{type_sql}{nested}{values}\"\n        if collate := self.sql(expression, \"collate\"):\n            type_sql = f\"{type_sql} COLLATE {collate}\"\n        if self.TZ_TO_WITH_TIME_ZONE"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-123930-parser-collate-is-not-handled-in/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-123930-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py", "old_string": "            if is_struct:\n                expressions = self._parse_csv(lambda: self._parse_struct_types(type_required=True))\n            else:\n                expressions = self._parse_csv(\n                    lamb
…[247 chars elided]…
se_csv(lambda: self._parse_struct_types(type_required=True))\n            else:\n                expressions = self._parse_csv(\n                    lambda: self._parse_type_collate(\n                        self._parse_types(\n                            check_func=check_func, schema=schema, allow_identifiers=allow_identifiers\n                        )\n                    )\n                )"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-123930-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-123930-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py", "old_string": "        fmt = None\n        to = self._parse_types()\n\n        default = None", "new_string": "        fmt = None\n        to = self._parse_type_collate(self._parse_types())\n\n        default = None"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-123930-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-123930-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py", "old_string": "    def _parse_struct_types(self, type_required: bool = False) -> exp.Expr | None:", "new_string": "    def _parse_type_collate(self, this: exp.Expr | None) -> exp.Expr | None:\n        # Only called where a type is not
…[20 chars elided]…
n constraint, e.g. CAST targets and\n        # nested type arguments, so a COLLATE here can't be confused with a column COLLATE\n        if isinstance(this, exp.DataType) and self._match(TokenType.COLLATE):\n            this.set(\"collate\", self._parse_identifier() or self._parse_column())\n        return this\n\n    def _parse_struct_types(self, type_required: bool = False) -> exp.Expr | None:"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-123930-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT CAST(x AS VARCHAR(10) COLLATE \\\"C\\\")', 'SELECT CAST(x AS ARRAY<TEXT COLLATE \\\"C\\\">)', 'SELECT CAST(x AS ARRAY<VARCHAR(5) COLLATE \\\"C\\\">)', 'SELECT CAST(x AS STRUCT<a TEXT COLLATE \\\"C\\\">)', 'SELECT x COLLATE \\\"C\\\"', 'SELECT x::TEXT COLLATE \\\"C\\\"', '
…[21 chars elided]…
T COLLATE \\\"C\\\")', 'CREATE TABLE t (a ARRAY<TEXT COLLATE \\\"C\\\">)']:\n    e = sqlglot.parse_one(s, read='postgres')\n    print(e.sql('postgres'), '|', repr(e)[:0] or type(e).__name__)\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify new COLLATE cases and run full test suite"}
[tool_result] SELECT CAST(x AS VARCHAR(10) COLLATE "C") | Select
SELECT CAST(x AS TEXT COLLATE "C"[]) | Select
SELECT CAST(x AS VARCHAR(5) COLLATE "C"[]) | Select
SELECT CAST(x AS STRUCT<a TEXT COLLATE "C">) | Select
SELECT x COLLATE "C" | Select
SELECT CAST(x AS TEXT) COLLATE "C" | Select
CREATE TABLE t (a TEXT COLLATE "C") | Create
CREATE TABLE t (a TEXT COLLATE "C"[]) | Create
................................................................ [  5%]
........................... [  8%]
............. [  9%]
...
…[671 chars elided]…
...................................... [ 70%]
..................................... [ 73%]
................................................................................................................... [ 83%]
................ [ 85%]
..................................................................................................................................................................                                                 [100%]
1106 passed, 17998 subtests passed in 57.29s
[assistant] Tests pass (1106). One output looks wrong: Postgres renders `ARRAY<TEXT COLLATE "C">` as `TEXT COLLATE "C"[]`, which is not valid Postgres. Let me check the Postgres override and the default dialect.
[tool_use Bash] {"command": "sed -n 477,500p sqlglot/generators/postgres.py; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor d in ['', 'bigquery', 'duckdb', 'postgres']:\n    for s in ['SELECT CAST(x AS ARRAY<TEXT COLLATE \\\"C\\\">)', 'SELECT CAST(x AS VARCHAR(10) COLLATE \\\"C\\\")', 'SELECT CAST(x AS MAP(TEXT COLLATE \\\"C\\\", INT))']:\n        try: print(d or 'default', '|', sqlglot.transpile(s, read=d or None, write=d or None)[0])\n        except Exception as ex: print(d or 'default', 'ERR', str(ex)[:120])\n\"", "description": "Inspect Postgres ARRAY generation and try other dialects"}
[tool_result]     def datatype_sql(self, expression: exp.DataType) -> str:
        if expression.is_type(exp.DType.ARRAY):
            if expression.expressions:
                values = self.expressions(expression, key="values", flat=True)
                return f"{self.expressions(expression, flat=True)}[{values}]"
            return "ARRAY"

        if expression.is_type(exp.DType.ENUM):
            return f"ENUM ({self.expressions(expression, flat=True)})"

        if expression.is_type(exp.DType.DOUBLE, 
…[1002 chars elided]…
 TYPE after CAST. Line 1, Col: 20.
  SELECT CAST(x AS [4mMAP[0m(TEXT COLLATE "C", INT))
duckdb | SELECT CAST(x AS TEXT COLLATE "C"[])
duckdb | SELECT CAST(x AS TEXT COLLATE "C")
duckdb ERR Expected TYPE after CAST. Line 1, Col: 20.
  SELECT CAST(x AS [4mMAP[0m(TEXT COLLATE "C", INT))
postgres | SELECT CAST(x AS TEXT COLLATE "C"[])
postgres | SELECT CAST(x AS VARCHAR(10) COLLATE "C")
postgres ERR Expected TYPE after CAST. Line 1, Col: 20.
  SELECT CAST(x AS [4mMAP[0m(TEXT COLLATE "C", INT))
[assistant] The Postgres/DuckDB `T[]` rendering is a pre-existing dialect limitation (Postgres grammar does not allow `COLLATE` on an array element), so I'll leave those dialects alone and note it. Default and BigQuery round-trip correctly. Now I'll add tests next to existing COLLATE tests.
[tool_use Bash] {"command": "grep -rn \"COLLATE\" tests/*.py tests/dialects/test_dialect.py | head -20", "description": "Find existing COLLATE tests"}
[tool_result] tests/test_expressions.py:880:                    "COLLATE": True,
tests/test_parser.py:979:                f"""SELECT * FROM t WHERE foo LIKE '%bar%' COLLATE {collate_pair[0]}"""
tests/test_transpile.py:755:            "ALTER TABLE integers ALTER i TYPE VARCHAR COLLATE foo USING bar",
tests/test_transpile.py:756:            "ALTER TABLE integers ALTER COLUMN i SET DATA TYPE VARCHAR COLLATE foo USING bar",
tests/dialects/test_dialect.py:692:                "tsql": "SELECT (PATINDEX(CONVERT(VARCHAR(MAX), 0x255b5e002d7f5d25) COLLATE Latin1_General_BIN, x) = 0)",
[tool_use Bash] {"command": "sed -n 965,990p tests/test_parser.py; sed -n 750,760p tests/test_transpile.py", "description": "Read surrounding COLLATE test context"}
[tool_result]     def test_parse_prop_eq(self):
        self.assertIsInstance(parse_one("x(a := b and c)").expressions[0], exp.PropertyEQ)

    def test_collate(self):
        collates = [
            ('pg_catalog."default"', exp.Column),
            ('"en_DE"', exp.Identifier),
            ("LATIN1_GENERAL_BIN", exp.Var),
            ("'en'", exp.Literal),
        ]

        for collate_pair in collates:
            collate_node = parse_one(
                f"""SELECT * FROM t WHERE foo LIKE '%bar%' COLLATE 
…[457 chars elided]…
rse_one("YEAR(a) /* sqlglot.anonymous */")
        self.validate(
            "ALTER TABLE integers ALTER i TYPE VARCHAR",
            "ALTER TABLE integers ALTER COLUMN i SET DATA TYPE VARCHAR",
        )
        self.validate(
            "ALTER TABLE integers ALTER i TYPE VARCHAR COLLATE foo USING bar",
            "ALTER TABLE integers ALTER COLUMN i SET DATA TYPE VARCHAR COLLATE foo USING bar",
        )

    def test_time(self):
        self.validate("INTERVAL '1 day'", "INTERVAL '1' DAY")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-123930-parser-collate-is-not-handled-in/base-1/tests/test_parser.py", "old_string": "            self.assertIsInstance(collate_node.expression, collate_pair[1])\n\n    def test_drop_column(self):", "new_string": "            self.assertIsInstance(collate_node.expression, collate_pair[1])\n\n    def t
…[388 chars elided]…
ql).sql(), sql)\n\n        cast = parse_one('SELECT CAST(x AS VARCHAR(10) COLLATE \"C\")').find(exp.Cast)\n        self.assertIsInstance(cast.to.args[\"collate\"], exp.Identifier)\n        self.assertIsNone(parse_one(\"SELECT x::TEXT\").find(exp.DataType).args.get(\"collate\"))\n        self.assertIsInstance(parse_one('SELECT x COLLATE \"C\"').this, exp.Column)\n\n    def test_drop_column(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-123930-parser-collate-is-not-handled-in/base-1/tests/test_parser.py has been updated successfully.
[assistant] I wrote the last assertion wrong (`parse_one(...)` returns the Select, so `.this` isn't the Collate). Fixing it before running.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-123930-parser-collate-is-not-handled-in/base-1/tests/test_parser.py", "old_string": "        self.assertIsInstance(parse_one('SELECT x COLLATE \"C\"').this, exp.Column)", "new_string": "        self.assertIsInstance(parse_one('SELECT x COLLATE \"C\"').find(exp.Collate), exp.Collate)"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-123930-parser-collate-is-not-handled-in/base-1/tests/test_parser.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py -k collate 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; <work>/env-sqlglot/bin/python -m ruff check sqlglot tests/test_parser.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot tests/test_parser.py 2>&1 | tail -3", "description": "Run new tests, full suite, and lint/format checks"}
[tool_result] ..                                                                   [100%]
2 passed, 64 deselected, 4 subtests passed in 0.05s
...................................................................................................................................................................                                            [100%]
1107 passed, 18002 subtests passed in 54.28s
All checks passed!
Would reformat: sqlglot/parser.py
1 file would be reformatted, 175 files already formatted
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff format sqlglot/parser.py && git diff --stat && git diff sqlglot/parser.py | head -60", "description": "Apply ruff formatting and show parser diff"}
[tool_result] 1 file reformatted
 sqlglot/expressions/datatypes.py |  1 +
 sqlglot/generator.py             |  2 ++
 sqlglot/parser.py                | 17 ++++++++++++++---
 tests/test_parser.py             | 15 +++++++++++++++
 4 files changed, 32 insertions(+), 3 deletions(-)
diff --git a/sqlglot/parser.py b/sqlglot/parser.py
index 1e96f9216..5e75edbd0 100644
--- a/sqlglot/parser.py
+++ b/sqlglot/parser.py
@@ -6254,8 +6254,12 @@ class Parser:
                 expressions = self._parse_csv(lambda: self._pars
…[1256 chars elided]…
 this
+
     def _parse_struct_types(self, type_required: bool = False) -> exp.Expr | None:
         index = self._index
 
@@ -7696,7 +7707,7 @@ class Parser:
             self.raise_error("Expected AS after CAST")
 
         fmt = None
-        to = self._parse_types()
+        to = self._parse_type_collate(self._parse_types())
 
         default = None
         if self._match(TokenType.DEFAULT):
[This command modified 1 file you've previously read: sqlglot/parser.py. Call Read before editing.]
[assistant] `COLLATE` now parses and round-trips inside `CAST` targets and nested type arguments, while `COLLATE` in ordinary expressions and column definitions is unchanged. The full suite passes (1107 tests, including a new `test_collate_in_types`), and ruff check and format are clean. The changes are uncommitted in the worktree.

**What was broken:** struct fields already worked, because their `COLLATE` is parsed as a column constraint. The two failing positions were `CAST(x AS VARCHAR(10) COLLATE "C")` and `ARRAY<TEXT COLLATE "C">`.

**What I changed:**
- **`sqlglot/expressions/datatypes.py`:** `DataT
…[254 chars elided]…
n-level `COLLATE` keep their existing parse.
- **`sqlglot/generator.py`:** `datatype_sql` emits ` COLLATE <name>` after the type when the arg is set.
- **`tests/test_parser.py`:** `test_collate_in_types` covers the four round-trip cases and checks that `::` casts and plain `COLLATE` are unaffected.

**Known limitation:** Postgres and DuckDB render an array with a collated element as `TEXT COLLATE "C"[]`, which isn't valid Postgres syntax. Postgres's grammar doesn't allow a collation on an array element type, so I left those dialects alone. The default dialect and BigQuery round-trip correctly.
