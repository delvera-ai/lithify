# trajectory base-1

final message:
`COLLATE` now parses and round-trips inside CAST targets and inside `<...>` nested types. Ordinary `COLLATE` expressions are unchanged. The full suite passes (1106 tests, 17998 subtests), and ruff and mypy are clean on the changed files. I haven't committed anything.

**What changed**
- `sqlglot/expressions/datatypes.py`: `DataType` gets an optional `collate` arg.
- `sqlglot/parser.py`: a new `_parse_type_with_collate` helper reads an optional `COLLATE <identifier or column>` after a type. It's used for the CAST target and for non-struct `<...>` element types. The parenthesized form (e.g. `Nullable(...)`) is untouched.
- `sqlglot/generator.py`: `datatype_sql` appends ` COLLATE ...` when the arg is set.
- Tests: identity checks added to `tests/dialects/test_postgres.py` and `tests/dialects/test_dialect.py`.

**Choices I made**
- I didn't consume `COLLATE` inside general `_parse_types`. Doing so would turn `x::TEXT COLLATE "C"` into a `DataType` collation instead of the current `Collate(Cast(...))`, which changes existing behavior.
- Struct fields already worked (`STRUCT<a TEXT COLLATE "C">`) through the column-definition constraint path, so I left that alone.

**Known limitation**
- `ARRAY<TEXT COLLATE "C">` parses and round-trips in the base dialect. Postgres output is `TEXT COLLATE "C"[]`, which Postgres itself doesn't accept. This is a dialect rendering issue I didn't try to fix.

## events
[tool_use Bash] {"command": "grep -n -i \"collate\" sqlglot/parser.py | head -80 && grep -n -i \"collate\" sqlglot/tokens.py | head", "description": "Find COLLATE handling in parser and tokens"}
[tool_result] 680:        TokenType.COLLATE,
827:        TokenType.COLLATE,
913:        TokenType.COLLATE: exp.Collate,
1242:        "COLLATE": lambda self, **kwargs: self._parse_property_assignment(
1243:            exp.CollateProperty, **kwargs
1349:        "COLLATE": lambda self: self.expression(
1350:            exp.CollateColumnConstraint(this=self._parse_identifier() or self._parse_column())
6004:            if isinstance(this, exp.Collate):
8137:        if self._match(TokenType.COLLATE):
8653:                collate=self._match(TokenType.COLLATE) and self._parse_term(),
262:        "COLLATE": TokenType.COLLATE,
[tool_use Bash] {"command": "sed -n 6990,7015p sqlglot/parser.py; echo ---; sed -n 8125,8150p sqlglot/parser.py; echo ---; sed -n 8630,8670p sqlglot/parser.py; echo ---; grep -n \"def _parse_types\\|def _parse_struct_types\\|def _parse_column_def\\|def _parse_cast\\|def _parse_field_def\\|def _parse_nested\\|def _parse_types\" sqlglot/parser.py", "description": "Inspect parser sections around COLLATE usage"}
[tool_result]         expressions = self._parse_csv(self._parse_function_parameter)
        self._match_r_paren()
        return self.expression(
            exp.UserDefinedFunction(this=this, expressions=expressions, wrapped=True)
        )

    def _parse_introducer(self, token: Token) -> exp.Introducer | exp.Identifier:
        literal = self._parse_primary()
        if literal:
            return self.expression(exp.Introducer(this=token.text, expression=literal), token)

        return self._identifier_e
…[3324 chars elided]…
        if compound:
            self._match_text_seq("SORTKEY")

        if self._match(TokenType.L_PAREN, advance=False):
            return self.expression(
---
6136:    def _parse_types(
6410:    def _parse_struct_types(self, type_required: bool = False) -> exp.Expr | None:
7078:    def _parse_field_def(self) -> exp.Expr | None:
7081:    def _parse_column_def(
7689:    def _parse_cast(self, strict: bool, safe: bool | None = None) -> exp.Expr:
8547:    def _parse_column_def_with_exists(self):
[tool_use Bash] {"command": "sed -n 5985,6020p sqlglot/parser.py; echo ---; sed -n 6136,6160p sqlglot/parser.py; echo ...; sed -n 6280,6300p sqlglot/parser.py; echo ---; sed -n 6410,6460p sqlglot/parser.py; echo ---; sed -n 7078,7100p sqlglot/parser.py; echo ---; sed -n 7689,7740p sqlglot/parser.py", "description": "Read relevant parser sections"}
[tool_result]             elif self._match_pair(TokenType.GT, TokenType.GT):
                this = self.expression(
                    exp.BitwiseRightShift(this=this, expression=self._parse_term())
                )
            else:
                break

        return this

    def _parse_term(self) -> exp.Expr | None:
        this = self._parse_factor()

        while self._match_set(self.TERM):
            klass = self.TERM[self._prev.token_type]
            comments = self._prev_comments
            
…[7205 chars elided]…
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
[assistant] Let me reproduce the current behavior before changing anything.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls $PY && $PY -c \"\nimport sqlglot\ncases = [\n ('SELECT CAST(x AS VARCHAR(10) COLLATE \\\"C\\\")', 'postgres'),\n ('SELECT CAST(x AS TEXT COLLATE \\\"C\\\")', 'postgres'),\n ('SELECT CAST(x AS STRUCT<a TEXT COLLATE \\\"C\\\">)', 
…[146 chars elided]…
y'),\n ('SELECT x COLLATE \\\"C\\\"', 'postgres'),\n ('SELECT a COLLATE \\\"C\\\" FROM t', 'postgres'),\n]\nfor sql, d in cases:\n    try:\n        e = sqlglot.parse_one(sql, read=d)\n        print('OK ', repr(e.sql(d)), type(e).__name__)\n    except Exception as ex:\n        print('ERR', sql, '->', str(ex).splitlines()[0])\n\" 2>&1 | head -40", "description": "Reproduce COLLATE parsing failures"}
[tool_result] <work>/env-sqlglot/bin/python
ERR SELECT CAST(x AS VARCHAR(10) COLLATE "C") -> Invalid expression / Unexpected token. Line 1, Col: 41.
ERR SELECT CAST(x AS TEXT COLLATE "C") -> Invalid expression / Unexpected token. Line 1, Col: 34.
OK  "SELECT CAST(x AS STRUCT<a STRING COLLATE 'C'>)" Select
ERR SELECT CAST(x AS ARRAY<TEXT COLLATE "C">) -> Expecting >. Line 1, Col: 35.
OK  "CREATE TABLE t (a STRUCT<b STRING COLLATE 'C'>)" Create
OK  'SELECT x COLLATE "C"' Select
OK  'SELECT a COLLATE "C" FROM t' Select
[assistant] Struct fields in BigQuery already work through column-def constraints. The failures are CAST targets and `ARRAY<...>` element types. Next I'll look at how nested types are parsed and how `DataType` is generated.
[tool_use Bash] {"command": "grep -n \"schema=True\\|def datatype_sql\\|def columndef_sql\\|def collate_sql\\|class DataType\\|class CollateColumnConstraint\\|class ColumnDef\\|class Collate(\" sqlglot/*.py | head -40; echo ---; sed -n 6240,6275p sqlglot/parser.py", "description": "Locate nested type parsing and generator hooks"}
[tool_result] sqlglot/generator.py:1153:    def columndef_sql(self, expression: exp.ColumnDef, sep: str = " ") -> str:
sqlglot/generator.py:1683:    def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/generator.py:3914:    def collate_sql(self, expression: exp.Collate) -> str:
sqlglot/parser.py:1050:        exp.DataType: lambda self: self._parse_types(allow_identifiers=False, schema=True),
sqlglot/parser.py:1445:            exp.SwapTable(this=self._match(TokenType.WITH) and self._parse_table(sche
…[3231 chars elided]…
    if self._match_set((TokenType.L_BRACKET, TokenType.L_PAREN)):
                values = self._parse_csv(self._parse_disjunction)
                if not values and is_struct:
                    values = None
                    self._retreat(self._index - 1)
                else:
                    self._match_set((TokenType.R_BRACKET, TokenType.R_PAREN))

        if type_token in self.TIMESTAMPS:
            if self._match_text_seq("WITH", "TIME", "ZONE"):
                maybe_func = False
[tool_use Bash] {"command": "sed -n 1683,1700p sqlglot/generator.py; echo ---; sed -n 1153,1175p sqlglot/generator.py; echo ---; sed -n 3914,3920p sqlglot/generator.py; echo ---; sed -n 1345,1352p sqlglot/parser.py; grep -n \"class CollateColumnConstraint\" -A4 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null; grep -rn \"def collatecolumnconstraint_sql\\|CollateColumnConstraint\" sqlglot/generator.py | head; echo ---; grep -n \"COLLATE\\|collate\" tests/dialects/test_postgres.py | head -20", "description": "Inspect generator and collate tests"}
[tool_result]     def datatype_sql(self, expression: exp.DataType) -> str:
        nested = ""
        values = ""

        expr_nested = expression.args.get("nested")
        type_value = expression.this

        if (
            not expr_nested
            and isinstance(type_value, exp.DType)
            and (settings := self.TYPE_PARAM_SETTINGS.get(type_value))
        ):
            expression = self.datatype_param_bound_limiter(expression, type_value, *settings)

        interior = (
            self.ex
…[2622 chars elided]…
 OPERATOR(pg_catalog.~) '^(courses)$' COLLATE pg_catalog.default AND "
804:            """SELECT TRIM(LEADING ' XXX ' COLLATE "de_DE")""",
805:            """SELECT LTRIM(' XXX ' COLLATE "de_DE")""",
808:            """SELECT TRIM(TRAILING ' XXX ' COLLATE "de_DE")""",
809:            """SELECT RTRIM(' XXX ' COLLATE "de_DE")""",
1126:        self.validate_identity('CREATE TABLE x (a TEXT COLLATE "de_DE")')
1127:        self.validate_identity('CREATE TABLE x (a TEXT COLLATE pg_catalog."default")')
[assistant] The cleanest fix is a `collate` arg on `DataType`, consumed only in CAST targets and nested `<...>` element types. Consuming COLLATE in general `_parse_types` would change `x::TEXT COLLATE "C"`, which currently parses as `Collate(Cast(...))`. Let me check the `DataType` args and the end of `datatype_sql`.
[tool_use Bash] {"command": "grep -rn \"class DataType(\" -A12 sqlglot/expressions/*.py | grep -n \"arg_types\\|nested\\|class DataType\" ; sed -n 1700,1730p sqlglot/generator.py; echo ---; sed -n 6300,6320p sqlglot/parser.py", "description": "Inspect DataType args and datatype_sql tail"}
[tool_result] 1:sqlglot/expressions/datatypes.py:173:class DataType(Expression):
2:sqlglot/expressions/datatypes.py-174-    arg_types = {
5:sqlglot/expressions/datatypes.py-177-        "nested": False,
            )
            if expr_nested and self.pretty
            else self.expressions(expression, flat=True)
        )

        if type_value in self.UNSUPPORTED_TYPES:
            self.unsupported(
                f"Data type {type_value.value} is not supported when targeting {self.dialect.__class__.__nam
…[1345 chars elided]…
t(type_token)
                if not unsigned_type_token:
                    self.raise_error(f"Cannot convert {type_token.name} to unsigned.")

                type_token = unsigned_type_token or type_token

            # NULLABLE without parentheses can be a column (Presto/Trino)
            if type_token == TokenType.NULLABLE and not expressions:
                self._retreat(index)
                return None

            this = exp.DataType(
                this=exp.DType[type_token.name],
[tool_use Bash] {"command": "sed -n 173,190p sqlglot/expressions/datatypes.py; echo ---; sed -n 1730,1760p sqlglot/generator.py", "description": "Read DataType arg_types and generator tail"}
[tool_result] class DataType(Expression):
    arg_types = {
        "this": True,
        "expressions": False,
        "nested": False,
        "values": False,
        "kind": False,
        "nullable": False,
    }

    Type: t.ClassVar[Type[DType]] = DType

    STRUCT_TYPES: t.ClassVar[set[DType]] = {
        DType.FILE,
        DType.NESTED,
        DType.OBJECT,
        DType.STRUCT,
        DType.UNION,
---
                nested = f" {interior}"
            else:
                nested = f"({interior}
…[680 chars elided]…
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
[assistant] The plan:

1. Add a `collate` arg to `DataType`.
2. Emit it at the end of `datatype_sql`.
3. Add a small parser helper that reads `COLLATE <identifier or column>` after a type. Use it for CAST targets and non-struct nested element types.

Struct fields already round-trip through column-def constraints, so I'll leave that path alone.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-150556-parser-collate-is-not-handled-in/base-1/sqlglot/expressions/datatypes.py", "old_string": "        \"kind\": False,\n        \"nullable\": False,\n    }\n\n    Type: t.ClassVar[Type[DType]] = DType", "new_string": "        \"kind\": False,\n        \"nullable\": False,\n        \"collate\": False,\n    }\n\n    Type: t.ClassVar[Type[DType]] = DType"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-150556-parser-collate-is-not-handled-in/base-1/sqlglot/expressions/datatypes.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-150556-parser-collate-is-not-handled-in/base-1/sqlglot/generator.py", "old_string": "            type_sql = f\"{type_sql} WITH TIME ZONE\"\n\n        return type_sql", "new_string": "            type_sql = f\"{type_sql} WITH TIME ZONE\"\n\n        collate = self.sql(expression, \"collate\")\n        collate = f\" COLLATE {collate}\" if collate else \"\"\n\n        return f\"{type_sql}{collate}\""}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-150556-parser-collate-is-not-handled-in/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-150556-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py", "old_string": "    def _parse_types(\n        self, check_func: bool = False, schema: bool = False, allow_identifiers: bool = True\n    ) -> exp.Expr | None:", "new_string": "    def _parse_type_with_collate(\n        self, check_func
…[161 chars elided]…
func, schema=schema, allow_identifiers=allow_identifiers\n        )\n        if isinstance(this, exp.DataType) and self._match(TokenType.COLLATE):\n            this.set(\"collate\", self._parse_identifier() or self._parse_column())\n        return this\n\n    def _parse_types(\n        self, check_func: bool = False, schema: bool = False, allow_identifiers: bool = True\n    ) -> exp.Expr | None:"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-150556-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-150556-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py", "old_string": "                expressions = self._parse_csv(\n                    lambda: self._parse_types(\n                        check_func=check_func, schema=schema, allow_identifiers=allow_identifiers\n                    )\n                )", "new_string": "                expressions = self._parse_csv(\n                    lambda: self._parse_type_with_collate(\n                        check_func=check_func, schema=schema, allow_identifiers=allow_identifiers\n                    )\n                )"}
[tool_result ERROR] <tool_use_error>Found 2 matches of the string to replace, but replace_all is false. To replace all occurrences, set replace_all to true. To replace only one occurrence, please provide more context to uniquely identify the instance.
String:                 expressions = self._parse_csv(
                    lambda: self._parse_types(
                        check_func=check_func, schema=schema, allow_identifiers=allow_identifiers
                    )
                )</tool_use_error>
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-150556-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py", "old_string": "        fmt = None\n        to = self._parse_types()\n\n        default = None", "new_string": "        fmt = None\n        to = self._parse_type_with_collate()\n\n        default = None"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-150556-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py has been updated successfully.
[assistant] The nested-types snippet appears twice, so I'll check the other occurrence before deciding whether it should change too.
[tool_use Bash] {"command": "grep -n \"lambda: self._parse_types(\" -B4 -A3 sqlglot/parser.py", "description": "Find remaining nested type parse lambdas"}
[tool_result] 6211-            if is_struct:
6212-                expressions = self._parse_csv(lambda: self._parse_struct_types(type_required=True))
6213-            elif nested:
6214-                expressions = self._parse_csv(
6215:                    lambda: self._parse_types(
6216-                        check_func=check_func, schema=schema, allow_identifiers=allow_identifiers
6217-                    )
6218-                )
--
6236-                expressions = [func_or_ident]
6237-                if
…[286 chars elided]…
schema,
6243-                                allow_identifiers=allow_identifiers,
--
6263-            if is_struct:
6264-                expressions = self._parse_csv(lambda: self._parse_struct_types(type_required=True))
6265-            else:
6266-                expressions = self._parse_csv(
6267:                    lambda: self._parse_types(
6268-                        check_func=check_func, schema=schema, allow_identifiers=allow_identifiers
6269-                    )
6270-                )
[tool_use Bash] {"command": "sed -n 6200,6222p sqlglot/parser.py", "description": "Read the parenthesized nested type branch"}
[tool_result]                 expressions=[key_type, value_type],
                nested=True,
            )

        nested = type_token in self.NESTED_TYPE_TOKENS
        is_struct = type_token in self.STRUCT_TYPE_TOKENS
        is_aggregate = type_token in self.AGGREGATE_TYPE_TOKENS
        expressions = None
        maybe_func = False

        if self._match(TokenType.L_PAREN):
            if is_struct:
                expressions = self._parse_csv(lambda: self._parse_struct_types(type_required=True))
            elif nested:
                expressions = self._parse_csv(
                    lambda: self._parse_types(
                        check_func=check_func, schema=schema, allow_identifiers=allow_identifiers
                    )
                )
                if type_token == TokenType.NULLABLE and len(expressions) == 1:
                    this = expressions[0]
                    this.set("nullable", True)
                    self._match_r_paren()
[assistant] The parenthesized branch handles `Nullable(...)`-style forms, which are outside this issue. I'll change only the `<...>` branch.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-150556-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py", "old_string": "            else:\n                expressions = self._parse_csv(\n                    lambda: self._parse_types(\n                        check_func=check_func, schema=schema, allow_identifiers=allow_identifiers\n     
…[19 chars elided]…
               )\n\n            if not self._match(TokenType.GT):", "new_string": "            else:\n                expressions = self._parse_csv(\n                    lambda: self._parse_type_with_collate(\n                        check_func=check_func, schema=schema, allow_identifiers=allow_identifiers\n                    )\n                )\n\n            if not self._match(TokenType.GT):"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-150556-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ncases = [\n ('SELECT CAST(x AS VARCHAR(10) COLLATE \\\"C\\\")', 'postgres'),\n ('SELECT CAST(x AS TEXT COLLATE \\\"C\\\")', 'postgres'),\n ('SELECT CAST(x AS TEXT COLLATE pg_catalog.\\\"default\\\")', 'po
…[487 chars elided]…
 \\\"C\\\" FROM t', 'postgres'),\n]\nfor sql, d in cases:\n    try:\n        e = sqlglot.parse_one(sql, read=d)\n        print('OK ', repr(e.sql(d)), '|', type(e).__name__, '| tree:', type(e.selects[0]).__name__ if hasattr(e,'selects') else '')\n    except Exception as ex:\n        print('ERR', sql, '->', str(ex).splitlines()[0])\n\" 2>&1", "description": "Verify COLLATE parsing after the change"}
[tool_result] OK  'SELECT CAST(x AS VARCHAR(10) COLLATE "C")' | Select | tree: Cast
OK  'SELECT CAST(x AS TEXT COLLATE "C")' | Select | tree: Cast
OK  'SELECT CAST(x AS TEXT COLLATE pg_catalog."default")' | Select | tree: Cast
OK  "SELECT CAST(x AS STRUCT<a STRING COLLATE 'C'>)" | Select | tree: Cast
OK  'SELECT CAST(x AS TEXT COLLATE "C"[])' | Select | tree: Cast
OK  "SELECT CAST(x AS ARRAY<STRUCT<a STRING COLLATE 'C'>>)" | Select | tree: Cast
OK  "SELECT CAST(x AS ARRAY<STRING COLLATE 'C'>)" | Select | tree: Cast
ERR CREATE TABLE t (a STRUCT<b TEXT COLLATE "C">) -> list index out of range
OK  'SELECT CAST(x AS TEXT) COLLATE "C"' | Select | tree: Collate
OK  'SELECT x COLLATE "C"' | Select | tree: Collate
OK  'SELECT a COLLATE "C" FROM t' | Select | tree: Collate
[assistant] Most cases now parse. Two things to check:

- The `CREATE TABLE ... STRUCT` error is from my print script (`selects` is empty for a `Create`), not the parser. I'll recheck it properly.
- `ARRAY<TEXT COLLATE "C">` in Postgres renders as `TEXT COLLATE "C"[]`. That is a dialect-specific array rendering, so I'll confirm it re-parses to the same tree.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor sql, d in [\n ('CREATE TABLE t (a STRUCT<b TEXT COLLATE \\\"C\\\">)', 'bigquery'),\n ('SELECT CAST(x AS TEXT COLLATE \\\"C\\\"[])', 'postgres'),\n ('SELECT CAST(x AS ARRAY<TEX
…[158 chars elided]…
'duckdb'),\n]:\n    e = sqlglot.parse_one(sql, read=d)\n    out = e.sql(d)\n    again = sqlglot.parse_one(out, read=d)\n    print(repr(out), 'roundtrip-equal:', again == e, 'collate nodes:', len(list(e.find_all(exp.DataType))) and [dt.args.get('collate') is not None for dt in e.find_all(exp.DataType)])\n\"; git -C . status --short", "description": "Check round-trip equality and collate placement"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 11, in <module>
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-150556-parser-collate-is-not-handled-in/base-1/sqlglot/__init__.py", line 160, in parse_one
    result = dialect.parse(sql, **opts)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-150556-parser-collate-is-not-handled-in/base-1/sqlglot/dialects/dialect.py", line 1119, in parse
    return self.
…[7248 chars elided]…
rk/repo-b63a38b63828/20261026-150556-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py", line 1992, in raise_error
    raise error
sqlglot.errors.ParseError: Required keyword: 'expressions' missing for <class 'sqlglot.expressions.core.Bracket'>. Line 1, Col: 36.
  SELECT CAST(x AS TEXT COLLATE "C"[][4m)[0m
"CREATE TABLE t (a STRUCT<b STRING COLLATE 'C'>)" roundtrip-equal: True collate nodes: [False, False]
 M sqlglot/expressions/datatypes.py
 M sqlglot/generator.py
 M sqlglot/parser.py
[assistant] The Postgres `TEXT COLLATE "C"[]` failure came from my own invalid input, which Postgres doesn't accept either. The generated Postgres array form is a dialect quirk, so I won't push on it. Next I'll run the project's test command, plus a round-trip check on the default dialect.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor sql in ['SELECT CAST(x AS VARCHAR(10) COLLATE \\\"C\\\")', 'SELECT CAST(x AS ARRAY<VARCHAR COLLATE \\\"C\\\">)', 'SELECT CAST(x AS MAP<TEXT COLLATE \\\"C\\\", INT>)']:\n    try:\n        out = sqlglot.transpile(sql)[0]; print(repr(out), sqlglot.transpile(out)[0] == out)\n    except Exception as ex: print('ERR', sql, str(ex).splitlines()[0])\n\"; $PY -I -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run default-dialect round-trips and full test suite", "timeout": 600000}
[tool_result] 'SELECT CAST(x AS VARCHAR(10) COLLATE "C")' True
'SELECT CAST(x AS ARRAY<VARCHAR COLLATE "C">)' True
'SELECT CAST(x AS MAP<TEXT COLLATE "C", INT>)' True
................................................................ [  5%]
........................... [  8%]
............. [  9%]
........................................................................................................................................ [ 21%]
...........................................................................
…[455 chars elided]…
...................................... [ 70%]
..................................... [ 73%]
................................................................................................................... [ 83%]
................ [ 85%]
..................................................................................................................................................................                                                 [100%]
1106 passed, 17998 subtests passed in 50.98s
[assistant] Full suite passes: 1106 tests, 17998 subtests. Let me add regression tests next to the existing Postgres COLLATE tests.
[tool_use Bash] {"command": "sed -n 1120,1130p tests/dialects/test_postgres.py", "description": "View Postgres COLLATE test context"}
[tool_result]         expr = self.parse_one("CREATE TABLE t (x INTERVAL day)")
        cdef = expr.find(exp.ColumnDef)
        cdef.args["kind"].assert_is(exp.DataType)
        self.assertEqual(expr.sql(dialect="postgres"), "CREATE TABLE t (x INTERVAL DAY)")

        self.validate_identity('ALTER INDEX "IX_Ratings_Column1" RENAME TO "IX_Ratings_Column2"')
        self.validate_identity('CREATE TABLE x (a TEXT COLLATE "de_DE")')
        self.validate_identity('CREATE TABLE x (a TEXT COLLATE pg_catalog."default")')
        self.validate_identity("CREATE TABLE t (col INT[3][5])")
        self.validate_identity("CREATE TABLE t (col INT[3])")
        self.validate_identity("CREATE INDEX IF NOT EXISTS ON t(c)")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-150556-parser-collate-is-not-handled-in/base-1/tests/dialects/test_postgres.py", "old_string": "        self.validate_identity('CREATE TABLE x (a TEXT COLLATE pg_catalog.\"default\")')\n        self.validate_identity(\"CREATE TABLE t (col INT[3][5])\")", "new_string": "        self.validate_identity(
…[78 chars elided]…
te_identity('SELECT CAST(x AS TEXT COLLATE \"C\")')\n        self.validate_identity('SELECT CAST(x AS VARCHAR(10) COLLATE \"C\")')\n        self.validate_identity('SELECT CAST(x AS TEXT COLLATE pg_catalog.\"default\")')\n        self.validate_identity('SELECT CAST(x AS MAP<TEXT COLLATE \"C\", INT>)', check_command_warning=False)\n        self.validate_identity(\"CREATE TABLE t (col INT[3][5])\")"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-150556-parser-collate-is-not-handled-in/base-1/tests/dialects/test_postgres.py has been updated successfully.
[assistant] I made two mistakes in that edit: `check_command_warning` isn't a real argument here, and `MAP<...>` isn't valid Postgres. I'll remove that line and put the nested-type identity check in the base dialect test instead.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-150556-parser-collate-is-not-handled-in/base-1/tests/dialects/test_postgres.py", "old_string": "        self.validate_identity('SELECT CAST(x AS MAP<TEXT COLLATE \"C\", INT>)', check_command_warning=False)\n", "new_string": ""}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-150556-parser-collate-is-not-handled-in/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"ARRAY<\" tests/dialects/test_dialect.py | head -5; grep -n \"def test_\" tests/dialects/test_dialect.py | head -3", "description": "Find a spot for nested-type tests"}
[tool_result] 294:            "CAST(ARRAY(1, 2) AS ARRAY<TINYINT>)",
115:    def test_enum(self):
124:    def test_lazy_load(self):
131:    def test_get_or_raise(self):
[tool_use Bash] {"command": "sed -n 288,300p tests/dialects/test_dialect.py", "description": "Read CAST nested-type test context"}
[tool_result]             "CAST(MAP('a', '1') AS MAP(TEXT, TEXT))",
            write={
                "clickhouse": "CAST(map('a', '1') AS Map(String, Nullable(String)))",
            },
        )
        self.validate_all(
            "CAST(ARRAY(1, 2) AS ARRAY<TINYINT>)",
            write={
                "clickhouse": "CAST([1, 2] AS Array(Nullable(Int8)))",
            },
        )
        self.validate_all(
            "CAST((1, 2, 3, 4) AS STRUCT<a: TINYINT, b: SMALLINT, c: INT, d: BIGINT>)",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-150556-parser-collate-is-not-handled-in/base-1/tests/dialects/test_dialect.py", "old_string": "        self.validate_all(\n            \"CAST(ARRAY(1, 2) AS ARRAY<TINYINT>)\",\n            write={\n                \"clickhouse\": \"CAST([1, 2] AS Array(Nullable(Int8)))\",\n            },\n        )", "new_string": "        self.validate_all(\n            \"CAST(ARRAY(1, 2) AS ARRAY<TINYINT>)\",\n            write={\n                \"clickhouse\": \"CAST([1, 2] AS Array(Nullable(Int8)))\",\n            },\n        )\n        self.validate_identity('SELECT CAST(x AS ARRAY<VARCHAR(10) COLLATE \"C\">)')\n        self.validate_identity('SELECT CAST(x AS MAP<TEXT COLLATE \"C\", INT>)')"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-150556-parser-collate-is-not-handled-in/base-1/tests/dialects/test_dialect.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py tests/dialects/test_dialect.py 2>&1 | tail -5; git stash list | head -0; git diff --stat", "description": "Run targeted tests and show diff stat", "timeout": 300000}
[tool_result] ....................................... [ 31%]
......................................................... [ 78%]
........................... [100%]
123 passed, 3203 subtests passed in 0.56s
head: illegal line count -- 0
 sqlglot/expressions/datatypes.py |  1 +
 sqlglot/generator.py             |  5 ++++-
 sqlglot/parser.py                | 14 ++++++++++++--
 tests/dialects/test_dialect.py   |  2 ++
 tests/dialects/test_postgres.py  |  3 +++
 5 files changed, 22 insertions(+), 3 deletions(-)
[assistant] Targeted tests pass. Now the full suite with the project's exact command, plus lint and format on the changed files.
[tool_use Bash] {"command": "ENV=<work>/env-sqlglot/bin; $ENV/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; ls $ENV | grep -i \"ruff\\|mypy\"; ($ENV/ruff check sqlglot tests/dialects/test_postgres.py tests/dialects/test_dialect.py && $ENV/ruff format --check sqlglot tests/dialects/test_postgres.py tests/dialects/test_dialect.py) 2>&1 | tail -8", "description": "Run full test suite, ruff lint and format check", "timeout": 600000}
[tool_result] ................ [ 85%]
..................................................................................................................................................................                                                 [100%]
1106 passed, 17998 subtests passed in 56.93s
dmypy
mypy
mypyc
ruff
All checks passed!
177 files already formatted
[assistant] Tests pass, ruff lint and format are clean. The new assertions run as subtests inside existing test methods, which is why the top-level count is unchanged. Last, a type check on the changed modules since the project runs mypy in pre-commit.
[tool_use Bash] {"command": "ENV=<work>/env-sqlglot/bin; timeout 500 $ENV/mypy sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/datatypes.py 2>&1 | tail -4; git diff", "description": "Run mypy on changed modules and show diff", "timeout": 600000}
[tool_result] (eval):1: command not found: timeout
diff --git a/sqlglot/expressions/datatypes.py b/sqlglot/expressions/datatypes.py
index afe468e44..aeb5ec61b 100644
--- a/sqlglot/expressions/datatypes.py
+++ b/sqlglot/expressions/datatypes.py
@@ -178,6 +178,7 @@ class DataType(Expression):
         "values": False,
         "kind": False,
         "nullable": False,
+        "collate": False,
     }
 
     Type: t.ClassVar[Type[DType]] = DType
diff --git a/sqlglot/generator.py b/sqlglot/generator.py
index bd
…[3157 chars elided]…
te_identity('CREATE TABLE x (a TEXT COLLATE pg_catalog."default")')
+        self.validate_identity('SELECT CAST(x AS TEXT COLLATE "C")')
+        self.validate_identity('SELECT CAST(x AS VARCHAR(10) COLLATE "C")')
+        self.validate_identity('SELECT CAST(x AS TEXT COLLATE pg_catalog."default")')
         self.validate_identity("CREATE TABLE t (col INT[3][5])")
         self.validate_identity("CREATE TABLE t (col INT[3])")
         self.validate_identity("CREATE INDEX IF NOT EXISTS ON t(c)")
[tool_use Bash] {"command": "ENV=<work>/env-sqlglot/bin; $ENV/mypy sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/datatypes.py 2>&1 | tail -4", "description": "Run mypy on changed modules", "timeout": 600000}
[tool_result] Success: no issues found in 3 source files
[assistant] `COLLATE` now parses and round-trips inside CAST targets and inside `<...>` nested types. Ordinary `COLLATE` expressions are unchanged. The full suite passes (1106 tests, 17998 subtests), and ruff and mypy are clean on the changed files. I haven't committed anything.

**What changed**
- `sqlglot/expressions/datatypes.py`: `DataType` gets an optional `collate` arg.
- `sqlglot/parser.py`: a new `_parse_type_with_collate` helper reads an optional `COLLATE <identifier or column>` after a type. It's used for the CAST target and for non-struct `<...>` element types. The parenthesized form (e.g. `Nul
…[204 chars elided]…
_dialect.py`.

**Choices I made**
- I didn't consume `COLLATE` inside general `_parse_types`. Doing so would turn `x::TEXT COLLATE "C"` into a `DataType` collation instead of the current `Collate(Cast(...))`, which changes existing behavior.
- Struct fields already worked (`STRUCT<a TEXT COLLATE "C">`) through the column-definition constraint path, so I left that alone.

**Known limitation**
- `ARRAY<TEXT COLLATE "C">` parses and round-trips in the base dialect. Postgres output is `TEXT COLLATE "C"[]`, which Postgres itself doesn't accept. This is a dialect rendering issue I didn't try to fix.
