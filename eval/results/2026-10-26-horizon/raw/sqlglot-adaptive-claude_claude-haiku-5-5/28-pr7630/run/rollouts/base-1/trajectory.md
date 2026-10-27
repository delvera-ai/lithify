# trajectory base-1

final message:
`COLLATE` now parses and round-trips inside `CAST` target types and inside nested type elements such as `ARRAY<...>`. Ordinary `COLLATE` in expressions and column definitions behaves as before. The full suite passes (1107 tests), and ruff check and format are clean.

Changes:
- **`sqlglot/parser.py`**: a new `_parse_type_collate` helper consumes an optional `COLLATE` after a type. It's applied to the `CAST` target type and to the element types inside `<...>` and `(...)` nested types. Column definitions and struct fields are untouched, since they already handle COLLATE as a column constraint.
- **`sqlglot/expressions/datatypes.py`**: `DataType` gets a `collate` arg.
- **`sqlglot/generator.py`**: the base `datatype_sql` appends ` COLLATE <name>` when that arg is set.
- **`tests/dialects/test_dialect.py`**: a new `test_collate_in_types` covering the CAST and nested cases, plus `x::VARCHAR COLLATE "C"` still working.

Before the change, `CAST(x AS TEXT COLLATE "C")` and `ARRAY<TEXT COLLATE "C">` raised a ParseError. Struct fields with COLLATE already parsed.

Caveats:
- Dialect generators that override `datatype_sql` without calling `super()` will drop the collation in their output. I didn't change those overrides. I checked that the base dialect round-trips correctly.
- Postgres output for a nested collated element is `TEXT COLLATE "C"[]`, which is probably not valid Postgres. Input parses and round-trips in the base dialect, but I didn't address the dialect-specific rendering.

I haven't committed anything. Let me know if you want a commit.

## events
[tool_use Bash] {"command": "grep -rn \"COLLATE\" sqlglot/parser.py sqlglot/parsers/*.py | head -60; grep -n \"def _parse_types\\|def _parse_struct_types\\|def _parse_column_def\\|def _parse_cast\\|def _parse_column_ops\\|def _parse_field_def\\|def _parse_datatype\" sqlglot/parser.py", "description": "Find COLLATE and datatype parsing code"}
[tool_result] sqlglot/parser.py:680:        TokenType.COLLATE,
sqlglot/parser.py:827:        TokenType.COLLATE,
sqlglot/parser.py:913:        TokenType.COLLATE: exp.Collate,
sqlglot/parser.py:1242:        "COLLATE": lambda self, **kwargs: self._parse_property_assignment(
sqlglot/parser.py:1349:        "COLLATE": lambda self: self.expression(
sqlglot/parser.py:8137:        if self._match(TokenType.COLLATE):
sqlglot/parser.py:8653:                collate=self._match(TokenType.COLLATE) and self._parse_term(),
sqlglot/parsers/mysql.py:529:        if self._match_text_seq("COLLATE"):
6136:    def _parse_types(
6410:    def _parse_struct_types(self, type_required: bool = False) -> exp.Expr | None:
6659:    def _parse_column_ops(self, this: exp.Expr | None) -> exp.Expr | None:
7078:    def _parse_field_def(self) -> exp.Expr | None:
7081:    def _parse_column_def(
7689:    def _parse_cast(self, strict: bool, safe: bool | None = None) -> exp.Expr:
8547:    def _parse_column_def_with_exists(self):
[tool_use Bash] {"command": "sed -n 6136,6150p sqlglot/parser.py; echo ----; sed -n 6230,6330p sqlglot/parser.py; echo ----; sed -n 6410,6440p sqlglot/parser.py; echo ----; sed -n 8125,8150p sqlglot/parser.py; echo ----; sed -n 7689,7730p sqlglot/parser.py", "description": "Read datatype, struct, collate, cast parsing code"}
[tool_result]     def _parse_types(
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
            if isi
…[7653 chars elided]…
,
                                self.dialect.FORMAT_MAPPING or self.dialect.TIME_MAPPING,
                                self.dialect.FORMAT_TRIE or self.dialect.TIME_TRIE,
                            )
                        ),
                        safe=safe,
                    )
                )

                if isinstance(fmt, exp.AtTimeZone) and isinstance(this, exp.StrToTime):
                    this.set("zone", fmt.args["zone"])
                return this
        elif not to:
[assistant] Let me reproduce the failures before deciding where the fix belongs.
[tool_use Bash] {"command": "PYTHONPATH=. python -c \"\nimport sqlglot\ncases = [\n ('SELECT CAST(x AS VARCHAR(10) COLLATE \\\"C\\\")', None),\n ('SELECT CAST(x AS TEXT COLLATE \\\"C\\\")', None),\n ('SELECT x::VARCHAR COLLATE \\\"C\\\"', None),\n ('CREATE TABLE t (a STRUCT<b TEXT COLLATE \\\"C\\\">)', None),\n ('CREATE TABLE t (a ARRAY<TEXT COLLATE \\\"C\\\">)', None),\n ('CREATE TABLE t (a STRUCT<b VARCHAR(10) 
…[189 chars elided]…
sql, '->', sqlglot.transpile(sql, read=d, write=d)[0])\n    except Exception as e:\n        print('ERR', sql, '->', type(e).__name__, str(e).splitlines()[0])\n\" 2>&1 | head -40; ls <work>/env-sqlglot/bin/python 2>/dev/null", "description": "Reproduce COLLATE parsing failures"}
[tool_result] ERR SELECT CAST(x AS VARCHAR(10) COLLATE "C") -> ParseError Invalid expression / Unexpected token. Line 1, Col: 41.
ERR SELECT CAST(x AS TEXT COLLATE "C") -> ParseError Invalid expression / Unexpected token. Line 1, Col: 34.
OK  SELECT x::VARCHAR COLLATE "C" -> SELECT CAST(x AS VARCHAR) COLLATE "C"
OK  CREATE TABLE t (a STRUCT<b TEXT COLLATE "C">) -> CREATE TABLE t (a STRUCT<b TEXT COLLATE "C">)
ERR CREATE TABLE t (a ARRAY<TEXT COLLATE "C">) -> ParseError Expecting >. Line 1, Col: 36.
OK  CREATE TABLE t (a STRUCT<b VARCHAR(10) COLLATE "C">) -> CREATE TABLE t (a STRUCT<b VARCHAR(10) COLLATE "C">)
OK  SELECT x COLLATE "C" FROM t -> SELECT x COLLATE "C" FROM t
OK  SELECT CAST(x AS STRING) COLLATE "C" -> SELECT CAST(x AS TEXT) COLLATE "C"
<work>/env-sqlglot/bin/python
[assistant] Failures confirmed: `CAST(... COLLATE)` and `ARRAY<TEXT COLLATE ...>`. Struct fields already work through `_parse_column_def`, so I'll check how that path handles COLLATE.
[tool_use Bash] {"command": "sed -n 1345,1355p sqlglot/parser.py; echo ----; sed -n 7078,7130p sqlglot/parser.py; echo ----; sed -n 6330,6345p sqlglot/parser.py; echo ---; grep -n \"_parse_column_constraint\\b\\|def _parse_column_constraint\" sqlglot/parser.py | head; grep -n \"CollateColumnConstraint\" sqlglot/expressions/*.py", "description": "Inspect column-def and collate constraint code"}
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
…[2512 chars elided]…
   # Postgres supports the INT ARRAY[3] syntax as a synonym for INT[3]
        matched_array = self._match(TokenType.ARRAY)

        while self._curr:
            datatype_token = self._prev.token_type
            matched_l_bracket = self._match(TokenType.L_BRACKET)

---
7141:            constraint = self._parse_column_constraint()
7279:    def _parse_column_constraint(self) -> exp.Expr | None:
sqlglot/expressions/constraints.py:68:class CollateColumnConstraint(Expression, ColumnConstraintKind):
[assistant] The struct-field path already works because `_parse_column_def` consumes COLLATE as a column constraint. The array path and CAST don't go through that. Next I'll check whether `DataType` can carry a collation, and how the generator renders it.
[tool_use Bash] {"command": "grep -rn \"class DataType(\" -A 25 sqlglot/expressions/*.py | head -50; grep -n \"def datatype_sql\" -A 30 sqlglot/generator.py | head -50; grep -n \"def collate_sql\\|def columnconstraint_sql\\|def collatecolumnconstraint_sql\" -A6 sqlglot/generator.py sqlglot/generators/*.py | head -30; grep -rn \"collate\" tests/dialects/test_*.py | grep -i \"cast\\|array\\|struct\" | head -20", "description": "Inspect DataType args and collate generation"}
[tool_result] sqlglot/expressions/datatypes.py:173:class DataType(Expression):
sqlglot/expressions/datatypes.py-174-    arg_types = {
sqlglot/expressions/datatypes.py-175-        "this": True,
sqlglot/expressions/datatypes.py-176-        "expressions": False,
sqlglot/expressions/datatypes.py-177-        "nested": False,
sqlglot/expressions/datatypes.py-178-        "values": False,
sqlglot/expressions/datatypes.py-179-        "kind": False,
sqlglot/expressions/datatypes.py-180-        "nullable": False,
sqlglo
…[4033 chars elided]…
9-        return self.sql(expression.this)
sqlglot/generators/exasol.py-920-
sqlglot/generators/exasol.py-921-    def jsonextract_sql(self, expression: exp.JSONExtract) -> str:
sqlglot/generators/exasol.py-922-        sql = self.func(
sqlglot/generators/exasol.py-923-            "JSON_EXTRACT", expression.this, expression.expression, *expression.expressions
sqlglot/generators/exasol.py-924-        )
sqlglot/generators/singlestore.py:1517:    def collate_sql(self, expression: exp.Collate) -> str:
[assistant] The cleanest fix is to attach the collation to the `DataType` itself, so it renders as the type's suffix. That keeps `CAST(... AS TEXT COLLATE "C")` and `ARRAY<TEXT COLLATE "C">` in one AST shape. First I need the nested-type call sites and the end of `datatype_sql`.
[tool_use Bash] {"command": "sed -n 6150,6230p sqlglot/parser.py; echo ----; sed -n 1710,1760p sqlglot/generator.py; echo ----; grep -rn \"def datatype_sql\" sqlglot/generators/ | head; grep -n \"def cast_sql\" -A8 sqlglot/generator.py", "description": "Read nested type parsing and datatype generation"}
[tool_result]                 try:
                    tokens = self.dialect.tokenize(identifier.name)
                except TokenError:
                    tokens = None

                if tokens and (type_token := tokens[0].token_type) in self.TYPE_TOKENS:
                    if len(tokens) > 1:
                        return exp.DataType.from_str(identifier.name, dialect=self.dialect)
                elif self.dialect.SUPPORTS_USER_DEFINED_TYPES:
                    this = self._parse_user_defined_type(i
…[6399 chars elided]…
r | None = None) -> str:
3896-        format_sql = self.sql(expression, "format")
3897-        format_sql = f" FORMAT {format_sql}" if format_sql else ""
3898-        to_sql = self.sql(expression, "to")
3899-        to_sql = f" {to_sql}" if to_sql else ""
3900-        action = self.sql(expression, "action")
3901-        action = f" {action}" if action else ""
3902-        default = self.sql(expression, "default")
3903-        default = f" DEFAULT {default} ON CONVERSION ERROR" if default else ""
[assistant] Many dialects override `datatype_sql`, so a base-generator suffix might not reach them. I'll check whether those overrides delegate to `super()`.
[tool_use Bash] {"command": "grep -rn \"def datatype_sql\" -A4 sqlglot/generators/ | grep -n \"super\\|def \" | head -40; grep -rn \"def cast_sql\" sqlglot/generators/ | wc -l", "description": "Check datatype_sql overrides calling super"}
[tool_result] 1:sqlglot/generators/redshift.py:334:    def datatype_sql(self, expression: exp.DataType) -> str:
6:sqlglot/generators/dremio.py:75:    def datatype_sql(self, expression: exp.DataType) -> str:
11:sqlglot/generators/clickhouse.py:517:    def datatype_sql(self, expression: exp.DataType) -> str:
16:sqlglot/generators/materialize.py:35:    def datatype_sql(self, expression: exp.DataType) -> str:
21:sqlglot/generators/singlestore.py:1473:    def datatype_sql(self, expression: exp.DataType) -> str:
26
…[189 chars elided]…
tr:
36:sqlglot/generators/snowflake.py:686:    def datatype_sql(self, expression: exp.DataType) -> str:
41:sqlglot/generators/risingwave.py:27:    def datatype_sql(self, expression: exp.DataType) -> str:
46:sqlglot/generators/exasol.py:306:    def datatype_sql(self, expression: exp.DataType) -> str:
51:sqlglot/generators/mysql.py:628:    def datatype_sql(self, expression: exp.DataType) -> str:
56:sqlglot/generators/hive.py:432:    def datatype_sql(self, expression: exp.DataType) -> str:
      11
[assistant] Most dialect overrides don't call `super()`, so a base-generator suffix would silently drop the collation in those dialects. Before choosing an AST shape, I'll check whether existing tests pin any COLLATE-in-type output.
[tool_use Bash] {"command": "grep -rn \"COLLATE\" tests/ | grep -i \"cast\\|<\\|struct\\|array\" | head -30; grep -rn \"CollateColumnConstraint\" sqlglot/ | head", "description": "Search tests and code for COLLATE in types"}
[tool_result] sqlglot/parser.py:1350:            exp.CollateColumnConstraint(this=self._parse_identifier() or self._parse_column())
sqlglot/generator.py:158:        exp.CollateColumnConstraint: lambda self, e: f"COLLATE {self.sql(e, 'this')}",
sqlglot/expressions/constraints.py:68:class CollateColumnConstraint(Expression, ColumnConstraintKind):
[assistant] No existing tests pin this, and no code consumes a collation on a type. I'll store it as a `collate` arg on `DataType` and render it as a suffix, parsing it only in the two positions that need it (CAST target and nested type elements). Column definitions keep the existing `CollateColumnConstraint`.
[tool_use Bash] {"command": "grep -n \"self._parse_types(\" sqlglot/parser.py | head -40; sed -n 6255,6262p sqlglot/parser.py", "description": "List _parse_types call sites in parser"}
[tool_result] 1050:        exp.DataType: lambda self: self._parse_types(allow_identifiers=False, schema=True),
2523:                expression = self._parse_types()
3347:            value = self._parse_types()
6062:        data_type = self._parse_types(check_func=True, allow_identifiers=False)
6174:            key_type = self._parse_types(
6181:            value_type = self._parse_types(
6205:                    lambda: self._parse_types(
6230:                            lambda: self._parse_types(
6257:      
…[538 chars elided]…
ifiers=False)
8054:            kind = self._parse_types()
8652:                dtype=self._parse_types(),
9856:        kind = self._parse_schema() if self._match(TokenType.TABLE) else self._parse_types()
            else:
                expressions = self._parse_csv(
                    lambda: self._parse_types(
                        check_func=check_func, schema=schema, allow_identifiers=allow_identifiers
                    )
                )

            if not self._match(TokenType.GT):
[assistant] I'll make the edits: the `DataType` arg, a small helper, the two nested-element call sites, and the CAST target.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-204106-parser-collate-is-not-handled-in/base-1/sqlglot/expressions/datatypes.py", "old_string": "        \"kind\": False,\n        \"nullable\": False,\n    }\n\n    Type: t.ClassVar[Type[DType]] = DType", "new_string": "        \"kind\": False,\n        \"nullable\": False,\n        \"collate\": False,\n    }\n\n    Type: t.ClassVar[Type[DType]] = DType"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-204106-parser-collate-is-not-handled-in/base-1/sqlglot/expressions/datatypes.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-204106-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py", "old_string": "            elif nested:\n                expressions = self._parse_csv(\n                    lambda: self._parse_types(\n                        check_func=check_func, schema=schema, allow_identifiers=allow_identifiers
…[64 chars elided]…
        elif nested:\n                expressions = self._parse_csv(\n                    lambda: self._parse_type_collate(\n                        self._parse_types(\n                            check_func=check_func,\n                            schema=schema,\n                            allow_identifiers=allow_identifiers,\n                        )\n                    )\n                )"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-204106-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-204106-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py", "old_string": "            else:\n                expressions = self._parse_csv(\n                    lambda: self._parse_types(\n                        check_func=check_func, schema=schema, allow_identifiers=allow_identifiers\n     
…[148 chars elided]…
 = self._parse_csv(\n                    lambda: self._parse_type_collate(\n                        self._parse_types(\n                            check_func=check_func,\n                            schema=schema,\n                            allow_identifiers=allow_identifiers,\n                        )\n                    )\n                )\n\n            if not self._match(TokenType.GT):"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-204106-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-204106-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py", "old_string": "    def _parse_struct_types(self, type_required: bool = False) -> exp.Expr | None:", "new_string": "    def _parse_type_collate(self, this: exp.Expr | None) -> exp.Expr | None:\n        if isinstance(this, exp.DataType) and self._match(TokenType.COLLATE):\n            this.set(\"collate\", self._parse_identifier() or self._parse_column())\n\n        return this\n\n    def _parse_struct_types(self, type_required: bool = False) -> exp.Expr | None:"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-204106-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-204106-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py", "old_string": "        fmt = None\n        to = self._parse_types()\n\n        default = None", "new_string": "        fmt = None\n        to = self._parse_type_collate(self._parse_types())\n\n        default = None"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-204106-parser-collate-is-not-handled-in/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-204106-parser-collate-is-not-handled-in/base-1/sqlglot/generator.py", "old_string": "            type_sql = f\"{type_sql} WITH TIME ZONE\"\n\n        return type_sql", "new_string": "            type_sql = f\"{type_sql} WITH TIME ZONE\"\n\n        collate = self.sql(expression, \"collate\")\n        collate = f\" COLLATE {collate}\" if collate else \"\"\n\n        return f\"{type_sql}{collate}\""}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-204106-parser-collate-is-not-handled-in/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now I'll re-run the reproduction cases, plus a few neighbours to confirm the outer-COLLATE and plain-type paths are unchanged.
[tool_use Bash] {"command": "PYTHONPATH=. python -c \"\nimport sqlglot\ncases = [\n 'SELECT CAST(x AS VARCHAR(10) COLLATE \\\"C\\\")',\n 'SELECT CAST(x AS TEXT COLLATE \\\"C\\\")',\n 'SELECT x::VARCHAR COLLATE \\\"C\\\"',\n 'SELECT CAST(x AS STRING) COLLATE \\\"C\\\"',\n 'CREATE TABLE t (a STRUCT<b TEXT COLLATE \\\"C\\\">)',\n 'CREATE TABLE t (a ARRAY<TEXT COLLATE \\\"C\\\">)',\n 'CREATE TABLE t (a STRUCT<b ARRAY
…[289 chars elided]…
ql else '| DIFF')\n    except Exception as e:\n        print('ERR', sql, '->', type(e).__name__, str(e).splitlines()[0])\n\"; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests 2>&1 | tail -15", "description": "Verify fixes and run full test suite"}
[tool_result] OK  SELECT CAST(x AS VARCHAR(10) COLLATE "C") -> SELECT CAST(x AS VARCHAR(10) COLLATE "C") | rt-ok
OK  SELECT CAST(x AS TEXT COLLATE "C") -> SELECT CAST(x AS TEXT COLLATE "C") | rt-ok
OK  SELECT x::VARCHAR COLLATE "C" -> SELECT CAST(x AS VARCHAR) COLLATE "C" | DIFF
OK  SELECT CAST(x AS STRING) COLLATE "C" -> SELECT CAST(x AS TEXT) COLLATE "C" | DIFF
OK  CREATE TABLE t (a STRUCT<b TEXT COLLATE "C">) -> CREATE TABLE t (a STRUCT<b TEXT COLLATE "C">) | rt-ok
OK  CREATE TABLE t (a ARRAY<TEXT COLLATE 
…[1153 chars elided]…
............................ [ 70%]
..................................... [ 73%]
................................................................................................................... [ 83%]
................ [ 85%]
..................................................................................................................................................................                                                 [100%]
1106 passed, 17998 subtests passed in 65.61s (0:01:05)
[assistant] The full suite passes (1106 tests). The "DIFF" lines are postgres generator normalization (`::`→`CAST`, `STRING`→`TEXT`, `ARRAY<>`→`[]`), not regressions. Now I'll add regression tests next to the existing identity tests.
[tool_use Bash] {"command": "grep -n \"^class \\|COLLATE\" tests/dialects/test_dialect.py | head -30; grep -n \"def test_\" tests/dialects/test_dialect.py | head -5", "description": "Locate test class for base dialect"}
[tool_result] 26:class Validator(unittest.TestCase):
112:class TestDialect(Validator):
692:                "tsql": "SELECT (PATINDEX(CONVERT(VARCHAR(MAX), 0x255b5e002d7f5d25) COLLATE Latin1_General_BIN, x) = 0)",
115:    def test_enum(self):
124:    def test_lazy_load(self):
131:    def test_get_or_raise(self):
186:    def test_compare_dialects(self):
212:    def test_compare_dialect_versions(self):
[tool_use Bash] {"command": "sed -n 112,116p tests/dialects/test_dialect.py", "description": "Read start of TestDialect class"}
[tool_result] class TestDialect(Validator):
    maxDiff = None

    def test_enum(self):
        dialect_by_key = Dialect.classes
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-204106-parser-collate-is-not-handled-in/base-1/tests/dialects/test_dialect.py", "old_string": "class TestDialect(Validator):\n    maxDiff = None\n\n    def test_enum(self):", "new_string": "class TestDialect(Validator):\n    maxDiff = None\n\n    def test_collate_in_types(self):\n        self.validat
…[46 chars elided]…
TE \"C\")')\n        self.validate_identity('SELECT CAST(x AS TEXT COLLATE \"C\")')\n        self.validate_identity('CREATE TABLE t (a ARRAY<TEXT COLLATE \"C\">)')\n        self.validate_identity('CREATE TABLE t (a STRUCT<b ARRAY<VARCHAR(10) COLLATE \"C\">>)')\n        self.validate_identity('SELECT x::VARCHAR COLLATE \"C\"', 'SELECT CAST(x AS VARCHAR) COLLATE \"C\"')\n\n    def test_enum(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-204106-parser-collate-is-not-handled-in/base-1/tests/dialects/test_dialect.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_dialect.py -k collate 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no tests 2>&1 | tail -2; (ruff check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/datatypes.py tests/dialects/test_dialect.py && ruff format --check sqlglot/parser.py sqlglot/generator.py tests/dialects/test_dialect.py sqlglot/expressions/datatypes.py) 2>&1 | tail -5", "description": "Run new test, full suite, and lint"}
[tool_result] .                                                                        [100%]
1 passed, 98 deselected in 0.07s
........................................................                                                [100%]
1107 passed, 17998 subtests passed in 61.22s (0:01:01)
All checks passed!
Would reformat: tests/dialects/test_dialect.py
1 file would be reformatted, 3 files already formatted
[tool_use Bash] {"command": "ruff format tests/dialects/test_dialect.py && git diff --stat && git diff tests/dialects/test_dialect.py | head -20", "description": "Format test file and show diff stats"}
[tool_result] 1 file reformatted
 sqlglot/expressions/datatypes.py |  1 +
 sqlglot/generator.py             |  5 ++++-
 sqlglot/parser.py                | 24 +++++++++++++++++++-----
 tests/dialects/test_dialect.py   |  9 +++++++++
 4 files changed, 33 insertions(+), 6 deletions(-)
diff --git a/tests/dialects/test_dialect.py b/tests/dialects/test_dialect.py
index b4d63a477..1ae52676d 100644
--- a/tests/dialects/test_dialect.py
+++ b/tests/dialects/test_dialect.py
@@ -112,6 +112,15 @@ class Validator(unittest.
…[268 chars elided]…
ate_identity('CREATE TABLE t (a ARRAY<TEXT COLLATE "C">)')
+        self.validate_identity('CREATE TABLE t (a STRUCT<b ARRAY<VARCHAR(10) COLLATE "C">>)')
+        self.validate_identity(
+            'SELECT x::VARCHAR COLLATE "C"', 'SELECT CAST(x AS VARCHAR) COLLATE "C"'
+        )
+
     def test_enum(self):
         dialect_by_key = Dialect.classes
         for dialect in Dialects:
[This command modified 1 file you've previously read: tests/dialects/test_dialect.py. Call Read before editing.]
[assistant] `COLLATE` now parses and round-trips inside `CAST` target types and inside nested type elements such as `ARRAY<...>`. Ordinary `COLLATE` in expressions and column definitions behaves as before. The full suite passes (1107 tests), and ruff check and format are clean.

Changes:
- **`sqlglot/parser.py`**: a new `_parse_type_collate` helper consumes an optional `COLLATE` after a type. It's applied to the `CAST` target type and to the element types inside `<...>` and `(...)` nested types. Column definitions and struct fields are untouched, since they already handle COLLATE as a column constraint.
-
…[364 chars elided]…
OLLATE "C")` and `ARRAY<TEXT COLLATE "C">` raised a ParseError. Struct fields with COLLATE already parsed.

Caveats:
- Dialect generators that override `datatype_sql` without calling `super()` will drop the collation in their output. I didn't change those overrides. I checked that the base dialect round-trips correctly.
- Postgres output for a nested collated element is `TEXT COLLATE "C"[]`, which is probably not valid Postgres. Input parses and round-trips in the base dialect, but I didn't address the dialect-specific rendering.

I haven't committed anything. Let me know if you want a commit.
