# trajectory base-1

final message:
DuckDB overloaded macros now parse and round-trip, for both scalar and table macros. The full suite passes (1114 tests) and ruff and mypy are clean on the changed files. The changes are uncommitted in the worktree.

**Representation.** `CREATE MACRO name (params) AS body, (params) AS body, ...` becomes `Create(this=<name>, kind=MACRO, expression=MacroOverloads(...))`. Each entry is an `exp.MacroOverload` with its params, body and a `table` flag. The single-overload form is unchanged, so existing ASTs and tests don't move.

**Changes:**
- `sqlglot/expressions/ddl.py`: new `MacroOverloads` and `MacroOverload` nodes.
- `sqlglot/parser.py`: the macro body parser now stops at a top-level comma. Before, the generic statement parser read `, (a, b) AS (...)` after a subquery body as a comma join, so those overloads fell back to `Command`. The overload branch and a `_parse_macro_overload` helper handle the rest.
- `sqlglot/generator.py`: `macrooverloads_sql` and `macrooverload_sql`, and `create_sql` skips its extra `AS` for overloads.
- `tests/dialects/test_duckdb.py`: a new `test_macro_overloads` covering scalar, zero-arg, `OR REPLACE`, table, and subquery-body overloads.

**DuckDB constraints I verified with DuckDB 1.5.6:**
- Table overloads must use the wrapped form, `AS TABLE (SELECT ...)`. The unwrapped `AS TABLE SELECT a, (b) AS ...` is rejected by DuckDB itself.
- All overloads of one macro must be the same kind. Mixing scalar and table is rejected, so I put the `TABLE` flag per entry but it is always uniform in valid input.

**Verification.** The generated SQL executes in DuckDB. `add_x(1, 2)` returns 3 and `add_x(1, 2, 3)` returns 6. The table overloads select `a` and `a + b` as expected.

**Output shape.** Overloaded macros print a space before the parameter list, e.g. `CREATE MACRO add_x (a, b) AS ...`, while single macros print `add_x(a, b)`. Both are valid DuckDB. I left the spacing alone rather than special-case it.

## events
[assistant] I'll start by finding how the DuckDB dialect and parser currently handle `CREATE MACRO`.
[tool_use Bash] {"command": "grep -rn -i \"macro\" sqlglot/ --include=*.py | grep -v \"^sqlglot/optimizer\" | head -60; echo ---; grep -rn -i \"macro\" tests/ --include=*.py | head -30; echo ---; cat .lithify/harness/scripts/probe_parse.py | head -40", "description": "Search codebase for macro references"}
[tool_result] (eval):1: no matches found: --include=*.py
---
(eval):1: no matches found: --include=*.py
---
"""Probe SQL statements for parse and round-trip failures with sqlglot.

Reads one SQL statement per line from stdin. Blank lines and lines starting with
`--` are skipped. Each statement is transpiled from --read to --write (--write
defaults to --read), then the output is transpiled again to check it is stable.

Prints, per statement:
  OK       output is stable; the next line is the output
  ERR      t
…[438 chars elided]…
ef probe(sql, read, write):
    try:
        out = sqlglot.transpile(sql, read=read, write=write)[0]
    except Exception as e:
        return "ERR", f"{type(e).__name__}: {str(e).splitlines()[0]}"

    try:
        again = sqlglot.transpile(out, read=write, write=write)[0]
    except Exception as e:
        return "ERR", f"output does not re-parse: {type(e).__name__}: {str(e).splitlines()[0]}"

    if again != out:
        return "UNSTABLE", f"{out}\n           -> {again}"

    return "OK", out
[tool_use Bash] {"command": "grep -rn -i \"macro\" sqlglot/ --include='*.py' | grep -v \"^sqlglot/optimizer\" ; echo ---; grep -rn -i \"macro\" tests/ --include='*.py'", "description": "Search sqlglot and tests for macro references"}
[tool_result] sqlglot/dialects/duckdb.py:95:            "MACRO": TokenType.FUNCTION,
sqlglot/dialects/mysql.py:138:            "_MACROMAN": TokenType.INTRODUCER,
---
tests/dialects/test_duckdb.py:2589:        for keyword in ("FUNCTION", "MACRO"):
tests/dialects/test_clickhouse.py:57:        self.validate_identity("@macro").assert_is(exp.Parameter).this.assert_is(exp.Var)
[tool_use Bash] {"command": "sed -n 2570,2640p tests/dialects/test_duckdb.py; echo ---; grep -n \"FUNCTION\\|MACRO\\|def _parse_create\\|CreateMacro\\|_parse_user_defined_function\" sqlglot/dialects/duckdb.py sqlglot/parser.py sqlglot/generator.py | head -40", "description": "View existing macro tests and related parser code"}
[tool_result]         ast.assert_is(exp.Install).name == "httpfs"
        assert isinstance(ast.this, exp.Identifier)

        self.validate_identity("INSTALL httpfs FROM community")
        self.validate_identity("INSTALL httpfs FROM 'https://extensions.duckdb.org'")
        self.validate_identity("FORCE INSTALL httpfs").assert_is(exp.Install).name == "httpfs"
        self.validate_identity("FORCE INSTALL httpfs FROM community")
        self.validate_identity("FORCE INSTALL httpfs FROM 'https://extensions.du
…[4658 chars elided]…
t/parser.py:2719:self.raise_error("Expected FUNCTION or PROCEDURE after EXECUTE")
sqlglot/parser.py:3296:def _parse_create_like(self) -> exp.LikeProperty | None:
sqlglot/parser.py:3450:is_function = self._match(TokenType.FUNCTION)
sqlglot/parser.py:5366:self.NO_PAREN_FUNCTION_PARSERS["PRIOR"] = lambda self: self.expression(
sqlglot/parser.py:5370:self.NO_PAREN_FUNCTION_PARSERS.pop("PRIOR")
sqlglot/parser.py:6549:if parts is None and token.text.upper() in self.NO_PAREN_FUNCTION_PARSERS:
[+8 more]
[tool_use Bash] {"command": "sed -n 2346,2440p sqlglot/parser.py; echo ---; grep -n \"def _parse_user_defined_function\" -A40 sqlglot/parser.py | head -80", "description": "Read CREATE and UDF parsing code in parser"}
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
…[4985 chars elided]…
 _parse_lambda_arg(self) -> exp.Expr | None:
7061-        return self._parse_id_var()
7062-
7063-    def _parse_lambda(self, alias: bool = False) -> exp.Expr | None:
7064-        next_token_type = self._next.token_type
7065-
7066-        # Fast path: simple atom (column, literal, null, bool) followed by , or )
7067-        if (
7068-            next_token_type in self.LAMBDA_ARG_TERMINATORS
7069-            and (atom := self._parse_atom()) is not None
7070-        ):
7071-            return atom
[assistant] Next I'll look at how the failing input parses today and where the DuckDB generator emits macro/function output.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; printf '%s\\n' \"CREATE OR REPLACE MACRO add_2(a, b) AS a + b;\" \"CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c;\" \"CREATE MACRO t(a) AS TABLE SELECT a;\" \"CREATE MACRO t(a) AS TABLE SELECT a, (b) AS TABLE SELECT a + b;\" \"CREATE MACRO m() AS 1, (a) AS a;\" | $PY -I .lithify/harness/scripts/probe_parse.py --read duckdb; echo; grep -n \"UserDefinedFunction\\|class Create(\" -A6 sqlglot/expressions/*.py sqlglot/*.py 2>/dev/null | head -40; echo ---; grep -n \"def create_sql\\|def userdefinedfunction_sql\\|def _create_sql\\|UserDefinedFunction\" sqlglot/generator.py sqlglot/dialects/duckdb.py", "description": "Probe current DuckDB macro parsing and find generator code"}
[tool_result] Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-160649-duckdb-dialect-overloaded-macro/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'

sqlglot/expressions/ddl.py:39:class Create(Expression, DDL):
sqlglot/expressions/ddl.py-40-    arg_types = {
sqlglot/expressions/ddl.py-41-        "with_": False,
sqlglot/expressions/ddl.py-42-        "this": True,
sqlg
…[1368 chars elided]…
ntroducer(self, token: Token) -> exp.Introducer | exp.Identifier:
sqlglot/parser.py-7044-        literal = self._parse_primary()
sqlglot/parser.py-7045-        if literal:
sqlglot/parser.py-7046-            return self.expression(exp.Introducer(this=token.text, expression=literal), token)
---
2 matches in 1 files:

sqlglot/generator.py:1287:def create_sql(self, expression: exp.Create) -> str:
sqlglot/generator.py:4585:def userdefinedfunction_sql(self, expression: exp.UserDefinedFunction) -> str:
[assistant] The probe script can't import `sqlglot` under `-I`. I'll check which `sqlglot` the harness env resolves to before using it.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"import sys; print(sys.path[:3])\"; $PY -I -c \"import sqlglot\" 2>&1 | tail -1; PYTHONPATH=$PWD $PY -I -c \"import sqlglot,sys; print(sqlglot.__file__, sqlglot.__version__)\"; cat .lithify/harness/memory.md 2>/dev/null | head -30; ls .lithify/harness/", "description": "Check which sqlglot the harness Python imports"}
[tool_result] ['', '~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python312.zip', '~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python3.12']
ModuleNotFoundError: No module named 'sqlglot'
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'sqlglot'
- The project's checks run with `<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no`.
scripts/
skills/
guardrails.md  147B
memory.md  153B
system.md  260B
tool_guidance.md  535B
[assistant] The env has no installed `sqlglot`, so I'll point `PYTHONPATH` at the worktree and run the probe that way.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; printf '%s\\n' \"CREATE OR REPLACE MACRO add_2(a, b) AS a + b;\" \"CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c;\" \"CREATE MACRO t(a) AS TABLE SELECT a;\" \"CREATE MACRO m() AS 1, (a) AS a;\" | PYTHONPATH=$PWD $PY .lithify/harness/scripts/probe_parse.py --read duckdb; echo; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\nprint(repr(sqlglot.parse_one('CREATE OR REPLACE MACRO add_2(a, b) AS a + b', read='duckdb')))\" | head -c 1500", "description": "Probe macro statements with worktree on PYTHONPATH"}
[tool_result] OK        CREATE OR REPLACE MACRO add_2(a, b) AS a + b;
          CREATE OR REPLACE MACRO add_2(a, b) AS a + b
ERR       CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c;
          ParseError: Invalid expression / Unexpected token. Line 1, Col: 35.
OK        CREATE MACRO t(a) AS TABLE SELECT a;
          CREATE MACRO t(a) AS TABLE SELECT a
ERR       CREATE MACRO m() AS 1, (a) AS a;
          ParseError: Invalid expression / Unexpected token. Line 1, Col: 22.

Create(
  this=UserDefinedFunction(
    this=Table(
      this=Identifier(this=add_2, quoted=False)),
    expressions=[
      Identifier(this=a, quoted=False),
      Identifier(this=b, quoted=False)],
    wrapped=True),
  kind=MACRO,
  replace=True,
  refresh=False,
  unique=False,
  expression=Add(
    this=Column(
      this=Identifier(this=a, quoted=False)),
    expression=Column(
      this=Identifier(this=b, quoted=False))),
  exists=False,
  begin=False,
  concurrently=False)
[assistant] The single-overload form already round-trips, so the gap is the comma-separated overload list. Next I'll read how `create_sql` emits the function body and where `AS TABLE` comes from, and check whether a DuckDB binary is available to verify syntax.
[tool_use Bash] {"command": "sed -n 1287,1300p sqlglot/generator.py; echo ...; sed -n 1320,1375p sqlglot/generator.py; echo ---; grep -n \"TABLE\" sqlglot/dialects/duckdb.py | head; echo ---; which duckdb; <work>/env-sqlglot/bin/python -c \"import duckdb; print(duckdb.__version__)\" 2>&1 | tail -1; git log --oneline -3 -- sqlglot/dialects/duckdb.py | cat", "description": "Read create_sql function body generation and DuckDB TABLE handling"}
[tool_result]     def create_sql(self, expression: exp.Create) -> str:
        kind = self.sql(expression, "kind")
        kind = self.dialect.INVERSE_CREATABLE_KIND_MAPPING.get(kind) or kind

        properties = expression.args.get("properties")

        if (
            kind == "TRIGGER"
            and properties
            and properties.expressions
            and isinstance(properties.expressions[0], exp.TriggerProperties)
            and properties.expressions[0].args.get("constraint")
        ):
   
…[2282 chars elided]…
ostcreate_props_sql = self.properties(
                exp.Properties(expressions=properties_locs[exp.Properties.Location.POST_CREATE]),
                sep=" ",
                prefix=" ",
                wrapped=False,
            )

---
0 matches for 'TABLE'
---
duckdb not found
1.5.6
cd06eb60a fix(sqlite)!: support INSERT IGNORE and offset-only limits [CODEX] (#7674)
b828e3044 feat(snowflake): add UUID_IS_STRING_TYPE flag and UUID_STRING parser
f3871121d fix(parser): robust CONCAT_WS (#7544)
[assistant] DuckDB 1.5.6 is installed in the harness env, so I can check real DuckDB behaviour. I'll look at the AST for a table macro and confirm DuckDB accepts the overload forms.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\nprint(repr(sqlglot.parse_one('CREATE MACRO t(a) AS TABLE SELECT a', read='duckdb')))\" | tail -12; echo ---; $PY -c \"\nimport duckdb\nc=duckdb.connect()\nfor s in [\n 'CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c',\n 'CREATE MACRO m() AS 1, (a) AS a',
…[446 chars elided]…
S a + b',\n]:\n  try:\n    c.execute(s); print('OK  ', s)\n  except Exception as e: print('ERR ', s, '->', str(e).splitlines()[0])\nprint(c.execute(\\\"select function_name, function_type, parameters, macro_definition from duckdb_functions() where function_type='macro' or function_type='table_macro'\\\").fetchall())\n\"", "description": "Inspect table macro AST and test overload syntax in DuckDB"}
[tool_result]     expressions=[
      Column(
        this=Identifier(this=a, quoted=False))]),
  exists=False,
  properties=Properties(
    expressions=[
      ReturnsProperty(
        this=Schema(
          this=Var(this=TABLE)),
        is_table=True)]),
  begin=False,
  concurrently=False)
---
OK   CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c
OK   CREATE MACRO m() AS 1, (a) AS a
ERR  CREATE MACRO t1(a, b) AS TABLE SELECT a, b, (a, b, c) AS TABLE SELECT 1 -> Parser Error: syntax error at or n
…[15509 chars elided]…
))SELECT unnest(map_keys(histogram)) AS bin, unnest(map_values(histogram)) AS count FROM (SELECT CASE  WHEN ((((NOT (can_cast_implicitly(min(col_name), CAST(NULL AS BIGINT)) OR can_cast_implicitly(min(col_name), CAST(NULL AS "DOUBLE")) OR can_cast_implicitly(min(col_name), CAST(NULL AS TIMESTAMP)))) AND (technique = \'auto\')) OR (technique = \'sample\'))) THEN (histogram_exact(col_name, bins)) ELSE histogram(col_name, bins) END AS histogram FROM query_table(CAST("source" AS VARCHAR)) , bins)')]
[assistant] DuckDB rejects table-macro overloads written as `AS TABLE SELECT ..., (...) AS TABLE SELECT ...`. Before deciding the table form, I'll test other spellings to see which ones DuckDB accepts.
[tool_use Bash] {"command": "cd /tmp && PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport duckdb\nc=duckdb.connect()\nfor s in [\n 'CREATE MACRO t1(a) AS TABLE SELECT a',\n 'CREATE MACRO t2(a) AS (TABLE SELECT a), (a, b) AS (TABLE SELECT a + b)',\n 'CREATE MACRO t3(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)',\n 'CREATE MACRO t4(a) AS (SELECT a), (a, b) AS 
…[414 chars elided]…
a + b)',\n]:\n  try:\n    c.execute(s); print('OK  ', s)\n  except Exception as e: print('ERR ', s, '->', str(e).splitlines()[0])\nprint(c.execute(\\\"select function_name, function_type, parameters from duckdb_functions() where function_name like 't%' and function_type like '%macro%'\\\").fetchall())\n\" 2>&1 | cut -c1-400", "description": "Test alternative DuckDB table macro overload spellings"}
[tool_result] OK   CREATE MACRO t1(a) AS TABLE SELECT a
ERR  CREATE MACRO t2(a) AS (TABLE SELECT a), (a, b) AS (TABLE SELECT a + b) -> Parser Error: syntax error at or near "SELECT"
OK   CREATE MACRO t3(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)
OK   CREATE MACRO t4(a) AS (SELECT a), (a, b) AS (SELECT a + b)
ERR  CREATE MACRO t5(a) AS TABLE SELECT a, (a, b) AS TABLE SELECT a + b -> Parser Error: syntax error at or near "SELECT"
ERR  CREATE MACRO t6(a) AS TABLE SELECT a; CREATE MACRO t6(a, b) AS TA
…[288 chars elided]…
 SELECT a + b) -> Parser Error: syntax error at or near "SELECT"
ERR  CREATE MACRO t9(a) AS (TABLE SELECT a), (a, b) AS (TABLE SELECT a + b) -> Parser Error: syntax error at or near "SELECT"
[('t4', 'macro', ['a']), ('t4', 'macro', ['a', 'b']), ('t6', 'table_macro', ['a']), ('t3', 'table_macro', ['a']), ('t3', 'table_macro', ['a', 'b']), ('t1', 'table_macro', ['a'])]
Shell cwd was reset to ~/.cache/lithify/work/repo-3abf279ffb90/20261029-160649-duckdb-dialect-overloaded-macro/base-1
[assistant] DuckDB accepts table overloads only in the wrapped form `AS TABLE (SELECT ...)`, and scalar overloads with `AS (SELECT ...)` too. Next I'll check how `TABLE` is parsed and generated, and whether mixing scalar and table overloads is allowed.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport duckdb\nc=duckdb.connect()\nfor s in [\n 'CREATE MACRO mx1(a) AS (SELECT a), (a, b) AS TABLE (SELECT a + b)',\n 'CREATE MACRO mx2(a) AS TABLE (SELECT a), (a, b) AS (SELECT a + b)',\n 'CREATE MACRO mx3(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)',\n 'CREATE MACRO mx4(a) AS TABLE (
…[320 chars elided]…
ELECT a']:\n  e=sqlglot.parse_one(s, read='duckdb'); print(e.sql('duckdb'))\n  print([ (type(x).__name__) for x in e.args.get('properties').expressions] if e.args.get('properties') else None, type(e.expression).__name__, e.expression.args.get('wrapped') if e.expression else None)\n\"; sed -n 3440,3470p sqlglot/parser.py", "description": "Check mixed overloads in DuckDB and TABLE parse/generation"}
[tool_result] ERR  CREATE MACRO mx1(a) AS (SELECT a), (a, b) AS TABLE (SELECT a + b) -> Parser Error: syntax error at or near "TABLE"
ERR  CREATE MACRO mx2(a) AS TABLE (SELECT a), (a, b) AS (SELECT a + b) -> Parser Error: syntax error at or near "("
OK   CREATE MACRO mx3(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)
ERR  CREATE MACRO mx4(a) AS TABLE (SELECT a), (a, b) AS TABLE SELECT a + b -> Parser Error: syntax error at or near "SELECT"
---
CREATE MACRO t(a) AS TABLE (SELECT a)
['ReturnsProperty'] 
…[1140 chars elided]…
self._match_pair(TokenType.REPLACE, TokenType.WHERE)
                and self._parse_disjunction(),
                partition=self._match(TokenType.PARTITION_BY) and self._parse_partitioned_by(),
                settings=self._match_text_seq("SETTINGS") and self._parse_settings_property(),
                default=self._match_text_seq("DEFAULT", "VALUES"),
                expression=self._parse_derived_table_values() or self._parse_ddl_select(),
                conflict=self._parse_on_conflict(),
[assistant] DuckDB requires every overload of a table macro to be a table body, and a scalar/table mix is rejected. Next I'll read how `TABLE` is consumed (`_parse_function_properties`) and how `ReturnsProperty` is emitted, to pick where the flag goes.
[tool_use Bash] {"command": "grep -n \"def _parse_function_properties\\|def _parse_heredoc\\|def _parse_returns\" -A22 sqlglot/parser.py | head -90; echo ---; grep -n \"def returnsproperty_sql\" -A14 sqlglot/generator.py; grep -n \"class ReturnsProperty\" -A3 sqlglot/expressions/*.py; grep -n \"class MacroOverload\\|class Return(\" sqlglot/expressions/*.py", "description": "Read function properties and returns property parsing"}
[tool_result ERROR] Exit code 2
3330:    def _parse_returns(self) -> exp.ReturnsProperty:
3331-        value: exp.Expr | None
3332-        null = None
3333-        is_table = self._match(TokenType.TABLE)
3334-
3335-        if is_table:
3336-            if self._match(TokenType.LT):
3337-                value = self.expression(
3338-                    exp.Schema(this="TABLE", expressions=self._parse_csv(self._parse_struct_types))
3339-                )
3340-                if not self._match(TokenType.GT):
3341-   
…[2288 chars elided]…
            else:
9271-                self.raise_error("No closing $ found")
9272-
---
sqlglot/expressions/properties.py:385:class ReturnsProperty(Property):
sqlglot/expressions/properties.py-386-    arg_types = {"this": False, "is_table": False, "table": False, "null": False}
sqlglot/expressions/properties.py-387-
sqlglot/expressions/properties.py-388-
rg: regex parse error:
    (?:class MacroOverload|class Return()
    ^
error: unclosed group
0 matches for 'class MacroOverload\|class Return('
[tool_use Bash] {"command": "grep -n \"_parse_returns\\|TokenType.TABLE: \\|\\\"TABLE\\\"\" sqlglot/parser.py sqlglot/dialects/duckdb.py | head; grep -n \"def returnsproperty_sql\" -A12 sqlglot/generator.py | head -20; grep -n \"class Return\\b\\|class Return(\" -A3 sqlglot/expressions/*.py", "description": "Locate TABLE property parser and returns generator"}
[tool_result] 11 matches in 1 files:

sqlglot/parser.py:1306:"RETURNS": lambda self: self._parse_returns(),
sqlglot/parser.py:2300:if not kind or (iceberg and kind and kind != "TABLE"):
sqlglot/parser.py:2679:if not self._match_text_seq("TABLE"):
sqlglot/parser.py:3143:kind = "TABLE"
sqlglot/parser.py:3153:if kind in ("DATABASE", "TABLE", "VIEW"):
sqlglot/parser.py:3330:def _parse_returns(self) -> exp.ReturnsProperty:
sqlglot/parser.py:3338:exp.Schema(this="TABLE", expressions=self._parse_csv(self._parse_struct_types))
sqlglot/parser.py:3343:value = self._parse_schema(exp.var("TABLE"))
sqlglot/expressions/query.py:882:class Return(Expression):
sqlglot/expressions/query.py-883-    pass
sqlglot/expressions/query.py-884-
sqlglot/expressions/query.py-885-
[tool_use Bash] {"command": "grep -n \"ReturnsProperty\\|TABLE\" sqlglot/dialects/duckdb.py sqlglot/generator.py | head -20; grep -n \"ReturnsProperty\" -B2 -A14 sqlglot/generator.py | head -60", "description": "Find DuckDB and generator handling of ReturnsProperty"}
[tool_result] 80 matches in 1 files:

sqlglot/generator.py:243:exp.ReturnsProperty: lambda self, e: (
sqlglot/generator.py:286:exp.WithJournalTableProperty: lambda self, e: f"WITH JOURNAL TABLE={self.sql(...
sqlglot/generator.py:340:RENAME_TABLE_WITH_DB = True
sqlglot/generator.py:358:TABLE_HINTS = True
sqlglot/generator.py:393:VALUES_AS_TABLE = True
sqlglot/generator.py:395:# Whether the word COLUMN is included when adding a column with ALTER TABLE
sqlglot/generator.py:396:ALTER_TABLE_INCLUDE_COLUMN_KEYWORD 
…[2612 chars elided]…
POST_SCHEMA,
740-        exp.SecureProperty: exp.Properties.Location.POST_CREATE,
741-        exp.SecurityIntegrationProperty: exp.Properties.Location.POST_CREATE,
742-        exp.SerdeProperties: exp.Properties.Location.POST_SCHEMA,
743-        exp.Set: exp.Properties.Location.POST_SCHEMA,
744-        exp.SettingsProperty: exp.Properties.Location.POST_SCHEMA,
745-        exp.SetProperty: exp.Properties.Location.POST_CREATE,
746-        exp.SetConfigProperty: exp.Properties.Location.POST_SCHEMA,
[assistant] I have enough context to settle the design. Summary of the plan:

- `TABLE` is a per-macro property parsed into `ReturnsProperty`. For overloads I'll record it per entry on `MacroOverload`, moving it off the Create's properties, since DuckDB requires all entries to match.
- Overloads go in `Create.expression` as one `exp.MacroOverloads` node. Its entries are `exp.MacroOverload` (params, body, table flag).
- The single-overload path stays unchanged, so existing AST and tests don't move.

Now I'll look at the expression definitions and the generator helpers I'll reuse.
[tool_use Bash] {"command": "sed -n 218,228p sqlglot/expressions/ddl.py; echo ---; sed -n 4580,4592p sqlglot/generator.py; echo ---; grep -n \"    def expressions(\\|    def no_identify(\\|    def wrap(\" -A4 sqlglot/generator.py | head -30; echo ---; sed -n 1326,1334p sqlglot/generator.py", "description": "Read expression, generator helpers and create_sql AS logic"}
[tool_result]         "for_role": False,
        "into_outfile": False,
        "json": False,
        "iceberg": False,
    }


class UserDefinedFunction(Expression):
    arg_types = {"this": True, "expressions": False, "wrapped": False}


---
        return f"{expression.args.get('prefix')}{self.sql(expression.this)}{expression.args.get('postfix')}"

    def token_sql(self, token_type: TokenType) -> str:
        return self.TOKEN_MAPPING.get(token_type, token_type.name)

    def userdefinedfunction_sql(self
…[984 chars elided]…

4514-        sqls: t.Collection[str | exp.Expr] | None = None,
---

        expression_sql = self.sql(expression, "expression")
        if expression_sql:
            expression_sql = f"{begin}{self.sep()}{expression_sql}"

            if self.CREATE_FUNCTION_RETURN_AS or not isinstance(expression.expression, exp.Return):
                postalias_props_sql = ""
                if properties_locs.get(exp.Properties.Location.POST_ALIAS):
                    postalias_props_sql = self.properties(
[assistant] I'll make the changes now: the two expression classes, the parser overload branch, the generator methods, and the `create_sql` tweak so the overloads aren't prefixed with a second `AS`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-160649-duckdb-dialect-overloaded-macro/base-1/sqlglot/expressions/ddl.py", "old_string": "class UserDefinedFunction(Expression):\n    arg_types = {\"this\": True, \"expressions\": False, \"wrapped\": False}\n", "new_string": "class UserDefinedFunction(Expression):\n    arg_types = {\"this\": True, \"expressions\": False, \"wrapped\": False}\n\n\nclass MacroOverloads(Expression):\n    arg_types = {\"expressions\": True}\n\n\nclass MacroOverload(Expression):\n    arg_types = {\"expressions\": True, \"expression\": True, \"table\": False}\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-160649-duckdb-dialect-overloaded-macro/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"def _parse_wrapped_csv\\|def _parse_csv\\|def raise_error\" sqlglot/parser.py; grep -n \"    def expressions(\" -A12 sqlglot/generator.py | grep -n \"flat\"; grep -n \"__all__\" sqlglot/expressions/ddl.py | head -2", "description": "Confirm parser and generator helper signatures"}
[tool_result] 3 matches in 2 files:

1973:0:str, token: Token = SENTINEL_NONE) -> None:
sqlglot/parser.py:8489:def _parse_csv(
sqlglot/parser.py:8507:def _parse_wrapped_csv(
6:4515-        flat: bool = False,
0 matches for '__all__'
[tool_use Bash] {"command": "grep -n \"_parse_wrapped_csv\\|_parse_csv = \\|    _parse_csv\\b\" sqlglot/parser.py | head -5; grep -n \"def _parse_csv\\|def _parse_wrapped_csv\\|def _parse_wrapped\\b\" -A3 sqlglot/parser.py | head; grep -n \"raise_error(\\\"Expecting\" sqlglot/parser.py | head -3", "description": "Locate parser helper methods for CSV parsing"}
[tool_result] 33 matches in 2 files:

1421:0:self._parse_primary() or self._parse_column())
sqlglot/parser.py:1263:exp.EnviromentProperty(expressions=self._parse_wrapped_csv(self._parse_assign...
sqlglot/parser.py:1278:exp.InheritsProperty(expressions=self._parse_wrapped_csv(self._parse_table))
8489:    def _parse_csv(
8490-        self, parse_method: t.Callable[[], T | None], sep: TokenType = TokenType.COMMA
8491-    ) -> list[T]:
8492-        parse_result = parse_method()
--
8507:    def _parse_wrapped_csv(
8508-        self,
8509-        parse_method: t.Callable[[], T | None],
8510-        sep: TokenType = TokenType.COMMA,
--
rg: regex parse error:
    (?:raise_error("Expecting)
    ^
error: unclosed group
0 matches for 'raise_error("Expecting'
[assistant] Both helpers are already used as `self._parse_*` methods in this file, so I can call them directly. Now the parser edit.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-160649-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "old_string": "                    if return_:\n                        expression = self.expression(exp.Return(this=expression))\n        elif create_token_type == TokenType.INDEX:", "new_string": "                    if return_:\n   
…[536 chars elided]…
              expression=expression,\n                            table=bool(returns),\n                        )\n                    ),\n                    *self._parse_csv(self._parse_macro_overload),\n                ]\n                this = this.this\n                expression = self.expression(exp.MacroOverloads(expressions=overloads))\n        elif create_token_type == TokenType.INDEX:"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-160649-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Next, the `_parse_macro_overload` helper, placed beside the existing UDF parsers.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-160649-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "old_string": "        return self.expression(\n            exp.UserDefinedFunction(this=this, expressions=expressions, wrapped=True)\n        )\n\n    def _parse_introducer(", "new_string": "        return self.expression(\n          
…[211 chars elided]…
tion_parameter)\n        if not self._match(TokenType.ALIAS):\n            self.raise_error(\"Expecting AS\")\n\n        table = bool(self._match(TokenType.TABLE))\n        expression = self._parse_user_defined_function_expression()\n        return self.expression(\n            exp.MacroOverload(expressions=expressions, expression=expression, table=table)\n        )\n\n    def _parse_introducer("}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-160649-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Now the generator: the two node methods, and the `create_sql` guard so overloads aren't prefixed with `AS`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-160649-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py", "old_string": "        return f\"{this}{expressions}\" if expressions.strip() != \"\" else this\n", "new_string": "        return f\"{this}{expressions}\" if expressions.strip() != \"\" else this\n\n    def macrooverloads_sql(self, 
…[9 chars elided]…
n: exp.MacroOverloads) -> str:\n        return self.expressions(expression, flat=True)\n\n    def macrooverload_sql(self, expression: exp.MacroOverload) -> str:\n        params = self.no_identify(self.expressions, expression, flat=True)\n        table = \" TABLE\" if expression.args.get(\"table\") else \"\"\n        return f\"{self.wrap(params)} AS{table} {self.sql(expression, 'expression')}\"\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-160649-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-160649-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py", "old_string": "            if self.CREATE_FUNCTION_RETURN_AS or not isinstance(expression.expression, exp.Return):\n                postalias_props_sql = \"\"", "new_string": "            if (\n                self.CREATE_FUNCTION_RETURN_AS or not isinstance(expression.expression, exp.Return)\n            ) and not isinstance(expression.expression, exp.MacroOverloads):\n                postalias_props_sql = \"\""}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-160649-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now I'll probe the failing statement and the other shapes: scalar, table, zero-arg, `OR REPLACE`, and lowercase keyword.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; printf '%s\\n' \"CREATE OR REPLACE MACRO add_2(a, b) AS a + b;\" \"CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c;\" \"CREATE MACRO m() AS 1, (a) AS a;\" \"CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b);\" \"create macro t2(a) as table (select a), (a, b) as table (select a 
…[69 chars elided]…
 \"CREATE OR REPLACE MACRO x(a) AS a + 1, (a, b) AS a + b\" | PYTHONPATH=$PWD $PY .lithify/harness/scripts/probe_parse.py --read duckdb; echo \"exit=$?\"; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\ne=sqlglot.parse_one('CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c', read='duckdb')\nprint(repr(e))\" | tail -30", "description": "Probe overload parsing and round-trip for several shapes"}
[tool_result] 'CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
'create macro t2(a) as table (select a), (a, b) as table (select a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
'create macro t2(a) as table (select a), (a, b) as table (select a + b)' con
…[1788 chars elided]…
          Identifier(this=a, quoted=False),
          Identifier(this=b, quoted=False),
          Identifier(this=c, quoted=False)],
        expression=Add(
          this=Add(
            this=Column(
              this=Identifier(this=a, quoted=False)),
            expression=Column(
              this=Identifier(this=b, quoted=False))),
          expression=Column(
            this=Identifier(this=c, quoted=False))),
        table=False)]),
  exists=False,
  begin=False,
  concurrently=False)
[assistant] Scalar overloads now parse. Two problems remain: zero-arg macros fail because an empty `expressions` list counts as missing, and the subquery-body overloads fall back to `Command`. I'll check the real error for the second.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\nfrom sqlglot.errors import ErrorLevel\nfor s in ['CREATE MACRO s(a) AS (SELECT a), (a, b) AS (SELECT a + b)', 'CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)']:\n  try:\n    print(repr(sqlglot.parse_one(s, read='duckdb', error_level=ErrorLevel.RAISE))[:200])\n  except Exception as e: print(type(e).__name__, str(e)[:400])\n\"", "description": "Get the underlying parse error for subquery overloads"}
[tool_result] 'CREATE MACRO s(a) AS (SELECT a), (a, b) AS (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
Command(this=CREATE, expression=MACRO s(a) AS (SELECT a), (a, b) AS (SELECT a + b))
Command(this=CREATE, expression=MACRO t(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b))
[assistant] The fallback message hides the real cause. I'll instrument the parser to see where the body parse stops for the subquery case.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\nfrom sqlglot.parser import Parser\nfrom sqlglot.dialects.duckdb import DuckDB\norig = Parser._parse_user_defined_function_expression\ndef spy(self):\n    r = orig(self)\n    print('body ->', repr(r)[:120].replace(chr(10),' '), '| next:', self._curr and self._curr.text, self._next and self._next.text)\n    return r\nParser._parse_user_defined_function_expression = spy\nfor s in ['CREATE MACRO s(a) AS (SELECT a), (a, b) AS (SELECT a + b)']:\n  print(DuckDB().parse(s))\n\" 2>&1 | head -30", "description": "Trace body parse boundaries for subquery overloads"}
[tool_result] 'CREATE MACRO s(a) AS (SELECT a), (a, b) AS (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
body -> Subquery(   this=Select(     expressions=[       Column(         this=Identifier(this=a, quoted=False))]),   joins=[     | next: ( SELECT
[Command(this=CREATE, expression=MACRO s(a) AS (SELECT a), (a, b) AS (SELECT a + b))]
[assistant] The body parse for `(SELECT a)` appears to consume the following comma, so the overload branch never sees it. I'll confirm by checking the token position before and after the body parse.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\nfrom sqlglot.parser import Parser\nfrom sqlglot.dialects.duckdb import DuckDB\norig = Parser._parse_statement\ndef spy(self):\n    i = self._index\n    r = orig(self)\n    print('stmt from', i, 'to', self._index, 'cur=', self._curr and self._curr.text, '|', repr(r)[:60].replace(chr(10),' '))\n    return r\nParser._parse_statement = spy\nprint(DuckDB().parse('CREATE MACRO s(a) AS (SELECT a), (a, b) AS (SELECT a + b)'))\n\" 2>&1 | head -30; grep -n \"def _parse_statement\" -A12 sqlglot/parser.py | head -30", "description": "Trace statement parse index to find comma consumption"}
[tool_result] 'CREATE MACRO s(a) AS (SELECT a), (a, b) AS (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
stmt from 7 to 18 cur= ( | Subquery(   this=Select(     expressions=[       Column(    
stmt from 0 to 24 cur= <Token token_type: TokenType.SENTINEL, text: SENTINEL, line: 1, col: 1, start: 0, end: 0, comments: []> | Command(this=CREATE, expression=MACRO s(a) AS (SELECT a), (a
[Command(this=CREATE, expression=MACRO s(a) AS (SELECT a), (a, b) AS (SELECT a + b))]
2269:  
…[14 chars elided]…
tatement(self) -> exp.Expr | None:
2270-        if not self._curr:
2271-            return None
2272-
2273-        if self._match_set(self.STATEMENT_PARSERS):
2274-            comments = self._prev_comments
2275-            stmt = self.STATEMENT_PARSERS[self._prev.token_type](self)
2276-            stmt.add_comments(comments, prepend=True)
2277-            return stmt
2278-
2279-        if self._match_set(self.dialect.tokenizer_class.COMMANDS):
2280-            return self._parse_command()
2281-
[assistant] The body's statement parse runs from token 7 to 18, past the comma and into the next overload's `(a, b) AS`. The statement-level parser is too greedy for a parenthesized subquery. I'll compare which expression-level parse methods stop at the comma.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\nfrom sqlglot.dialects.duckdb import DuckDB\nd = DuckDB()\nsrc = '(SELECT a), (a, b) AS (SELECT a + b)'\nfor m in ['_parse_statement', '_parse_expression', '_parse_assignment', '_parse_primary']:\n    toks = d.tokenize(src)\n    p = d.parser()\n    p.reset(); p._tokens = toks; p._index = -1; p._advance()\n    try:\n        r = getattr(p, m)()\n        print(m, '-> index', p._index, 'cur', p._curr and p._curr.text, repr(r)[:50].replace(chr(10),' '))\n    except Exception as e: print(m, 'ERR', str(e)[:100])\n\" 2>&1 | head", "description": "Compare expression parse methods on subquery body"}
[tool_result] _parse_statement -> index 0 cur <Token token_type: TokenType.SENTINEL, text: SENTINEL, line: 1, col: 1, start: 0, end: 0, comments: []> None
_parse_expression -> index 0 cur <Token token_type: TokenType.SENTINEL, text: SENTINEL, line: 1, col: 1, start: 0, end: 0, comments: []> None
_parse_assignment -> index 0 cur <Token token_type: TokenType.SENTINEL, text: SENTINEL, line: 1, col: 1, start: 0, end: 0, comments: []> None
_parse_primary -> index 0 cur <Token token_type: TokenType.SENTINEL, text: SENTINEL, line: 1, col: 1, start: 0, end: 0, comments: []> None
[assistant] My standalone harness set up the token stream wrong. I'll instead swap the body method inside the real statement parse and check whether the statement parses.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nfrom sqlglot.parser import Parser\nfrom sqlglot.dialects.duckdb import DuckDB\nfrom sqlglot.errors import ErrorLevel\nimport sqlglot\nfor name in ['_parse_statement', '_parse_expression', '_parse_assignment', '_parse_disjunction']:\n    Parser._parse_user_defined_function_expressio
…[176 chars elided]…
b) AS TABLE (SELECT a + b)', 'CREATE MACRO u(a) AS a + 1, (a, b) AS a + b']:\n        try:\n            e = sqlglot.parse_one(s, read='duckdb', error_level=ErrorLevel.RAISE)\n            print(name, 'OK', e.sql('duckdb'))\n        except Exception as ex: print(name, 'ERR', str(ex).splitlines()[0][:120])\n\" 2>&1 | head -30", "description": "Test alternative body parse methods for overload bodies"}
[tool_result] 'CREATE MACRO s(a) AS (SELECT a), (a, b) AS (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
_parse_statement OK CREATE MACRO s(a) AS (SELECT a), (a, b) AS (SELECT a + b)
_parse_statement OK CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)
_parse_statement OK CREATE MACRO u (a) AS a + 1, (a, b) AS a +
…[219 chars elided]…
 + 1, (a, b) AS a + b
_parse_assignment OK CREATE MACRO s (a) AS (SELECT a), (a, b) AS (SELECT a + b)
_parse_assignment OK CREATE MACRO t (a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)
_parse_assignment OK CREATE MACRO u (a) AS a + 1, (a, b) AS a + b
_parse_disjunction OK CREATE MACRO s (a) AS (SELECT a), (a, b) AS (SELECT a + b)
_parse_disjunction OK CREATE MACRO t (a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)
_parse_disjunction OK CREATE MACRO u (a) AS a + 1, (a, b) AS a + b
[assistant] With `_parse_statement` the overload path now parses, but the earlier default run fell back to `Command`. That contradicts the trace, so I'll rerun the default path in a fresh process to see which result is real.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\nfrom sqlglot.errors import ErrorLevel\nfor s in ['CREATE MACRO s(a) AS (SELECT a), (a, b) AS (SELECT a + b)', 'CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)']:\n    e = sqlglot.parse_one(s, read='duckdb', error_level=ErrorLevel.RAISE)\n    print(type(e).__name__, e.sql('duckdb'))\n\" 2>&1 | head; echo ---; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\nfrom sqlglot.dialects.duckdb import DuckDB\nprint(DuckDB().parse('CREATE MACRO s(a) AS (SELECT a), (a, b) AS (SELECT a + b)'))\" 2>&1 | head -4", "description": "Rerun default parse of subquery overloads in clean processes"}
[tool_result] 'CREATE MACRO s(a) AS (SELECT a), (a, b) AS (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
Command CREATE MACRO s(a) AS (SELECT a), (a, b) AS (SELECT a + b)
Command CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)
---
'CREATE MACRO s(a) AS (SELECT a), (a, b) AS (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
[Command(this=CREATE, expression=MACRO s(a) AS (SELECT a), (a, b) AS (SELECT a + b))]
[assistant] The default parse really does fall back to `Command`. The earlier "OK" came from a patched run, so I'll test that patch alone in a fresh process to find what differs.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\nfrom sqlglot.parser import Parser\nfrom sqlglot.dialects.duckdb import DuckDB\nprint('override in duckdb parser:', '_parse_user_defined_function_expression' in DuckDB.Parser.__dict__, '_parse_statement' in DuckDB.Parser.__dict__)\nParser._parse_user_defined_function_expression = lambda self: self._parse_statement()\nprint(DuckDB().parse('CREATE MACRO s(a) AS (SELECT a), (a, b) AS (SELECT a + b)')[0].__class__.__name__)\n\" 2>&1 | head -5; grep -n \"_parse_user_defined_function_expression\" sqlglot/dialects/*.py | head", "description": "Check whether DuckDB overrides body parse method"}
[tool_result] 'CREATE MACRO s(a) AS (SELECT a), (a, b) AS (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
override in duckdb parser: False False
Command
0 matches for '_parse_user_defined_function_expression'
[assistant] Those "OK" results were `Command` fallbacks too, since `Command` rebuilds text from tokens and inserts spaces. So the real issue is that a parenthesized-subquery body consumes the comma. I'll find which parser step eats it.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\nfrom sqlglot.parser import Parser\nfrom sqlglot.dialects.duckdb import DuckDB\ndef wrap(name):\n    orig = getattr(Parser, name)\n    def spy(self, *a, **k):\n        i = self._index\n        r = orig(self, *a, **k)\n        if self._index != i and 7 <= i <= 12:\n  
…[252 chars elided]…
lect','_parse_subquery','_parse_expression','_parse_alias','_parse_table_alias','_parse_statement','_parse_column_ops','_parse_unary','_parse_range','_parse_bitwise','_parse_term','_parse_factor']:\n    if hasattr(Parser, n): wrap(n)\nDuckDB().parse('CREATE MACRO s(a) AS (SELECT a), (a, b) AS (SELECT a + b)')\n\" 2>&1 | head -40", "description": "Trace which parser method consumes overload comma"}
[tool_result] 'CREATE MACRO s(a) AS (SELECT a), (a, b) AS (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
_parse_unary: 9->10 result=Column
_parse_factor: 9->10 result=Column
_parse_term: 9->10 result=Column
_parse_bitwise: 9->10 result=Column
_parse_range: 9->10 result=Column
_parse_expression: 9->10 result=Column
_parse_select: 8->10 result=Select
_parse_paren: 7->11 result=Subquery
_parse_primary: 7->11 result=Subquery
_parse_unary: 9->10 result=Column
_parse_factor: 9-
…[116 chars elided]…
lumn
_parse_expression: 9->10 result=Column
_parse_select: 8->10 result=Select
_parse_paren: 7->11 result=Subquery
_parse_primary: 7->11 result=Subquery
_parse_unary: 7->11 result=Subquery
_parse_factor: 7->11 result=Subquery
_parse_term: 7->11 result=Subquery
_parse_bitwise: 7->11 result=Subquery
_parse_range: 7->11 result=Subquery
_parse_expression: 7->11 result=Subquery
_parse_select: 12->18 result=Subquery
_parse_query_modifiers: 11->18 result=Subquery
_parse_statement: 7->18 result=Subquery
[assistant] The trace shows the cause. `_parse_statement` runs `_parse_query_modifiers` on the parenthesized subquery, and that treats the following `, (a, b) AS ...` as a comma join. I'll read the rest of `_parse_statement` to decide the narrowest fix.
[tool_use Bash] {"command": "sed -n 2282,2300p sqlglot/parser.py", "description": "Read the rest of _parse_statement"}
[tool_result]         if self._match_text_seq("WHILE"):
            return self._parse_whileblock()

        expression = self._parse_expression()
        expression = self._parse_set_operations(expression) if expression else self._parse_select()

        if isinstance(expression, exp.Subquery) and self._match(TokenType.PIPE_GT, advance=False):
            expression = self._parse_pipe_syntax_query(expression)

        return self._parse_query_modifiers(expression)

    def _parse_drop(self, exists: bool = False) -> exp.Drop | exp.Command:
        start = self._prev
        temporary = self._match(TokenType.TEMPORARY)
        materialized = self._match_text_seq("MATERIALIZED")
        iceberg = self._match_text_seq("ICEBERG")

        kind = self._match_set(self.CREATABLES) and self._prev.text.upper()
        if not kind or (iceberg and kind and kind != "TABLE"):
[assistant] `_parse_statement` always runs `_parse_query_modifiers`, so the comma after a query body is read as a comma join. I'll look at how the comma join is matched before choosing a fix.
[tool_use Bash] {"command": "grep -n \"def _parse_joins\\|def _parse_join(\" -A12 sqlglot/parser.py | grep -n \"COMMA\" ; grep -n \"def _parse_join(\" -A30 sqlglot/parser.py | grep -n \"COMMA\" ", "description": "Locate comma-join handling in the parser"}
[tool_result] 7:4426-        if self._match(TokenType.COMMA):
7:4426-        if self._match(TokenType.COMMA):
[tool_use Bash] {"command": "sed -n 4418,4436p sqlglot/parser.py", "description": "Read comma-join branch in _parse_join"}
[tool_result]         return self._parse_wrapped_csv(_parse_column_as_identifier, optional=True)

    def _parse_join(
        self,
        skip_join_token: bool = False,
        parse_bracket: bool = False,
        alias_tokens: t.Collection[TokenType] | None = None,
    ) -> exp.Join | None:
        if self._match(TokenType.COMMA):
            table = self._try_parse(lambda: self._parse_table(alias_tokens=alias_tokens))
            cross_join = self.expression(exp.Join(this=table)) if table else None

            if cross_join and self.JOINS_HAVE_EQUAL_PRECEDENCE:
                cross_join.set("kind", "CROSS")

            return cross_join

        index = self._index
        method, side, kind = self._parse_join_parts()
[assistant] The comma join comes from `_parse_join`, which reads `, (a, b) AS (...)` as a table. Macro bodies come in through the generic `_parse_statement`, so the first body is affected too. I'll check whether query modifiers on a bare `SELECT` body matter before I change the body parser for macros.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\nfor s in ['CREATE MACRO t(a) AS TABLE SELECT a FROM x ORDER BY a LIMIT 1', 'CREATE MACRO t(a) AS TABLE SELECT a UNION SELECT b', 'CREATE MACRO t(a) AS (SELECT a) ORDER BY a', 'CREATE MACRO t(a) AS TABLE SELECT a FROM x, y', 'CREATE MACRO t(a) AS TABLE (SELECT a) LIMIT 2']:\n    e = sqlglot.parse_one(s, read='duckdb'); print(type(e.expression).__name__ if e.expression is not None else None, '|', e.sql('duckdb'))\n\" 2>&1 | head -12; echo ---; grep -n \"def _parse_select(\" -A3 sqlglot/parser.py | head -5", "description": "Check query-modifier behaviour on current single macro bodies"}
[tool_result] Select | CREATE MACRO t(a) AS TABLE SELECT a FROM x ORDER BY a LIMIT 1
Union | CREATE MACRO t(a) AS TABLE SELECT a UNION SELECT b
Subquery | CREATE MACRO t(a) AS (SELECT a) ORDER BY a
Select | CREATE MACRO t(a) AS TABLE SELECT a FROM x, y
Subquery | CREATE MACRO t(a) AS TABLE (SELECT a) LIMIT 2
---
3792:    def _parse_select(
3793-        self,
3794-        nested: bool = False,
3795-        table: bool = False,
[assistant] Query modifiers do matter for single bodies (`ORDER BY`, `LIMIT`, `UNION`), so I won't drop them. Instead, the macro body parser will skip query modifiers when the next token is a comma, because that comma is always an overload separator. I'll also make `MacroOverload.expressions` optional so zero-argument overloads validate.
[tool_use Bash] {"command": "grep -n \"if not expression:\" -A12 sqlglot/parser.py | head -16", "description": "Show the function body branch in _parse_create"}
[tool_result] 2409:            if not expression:
2410-                if self._match(TokenType.COMMAND):
2411-                    expression = self._parse_as_command(self._prev)
2412-                else:
2413-                    begin = self._match(TokenType.BEGIN)
2414-                    return_ = self._match_text_seq("RETURN")
2415-
2416-                    if self._match(TokenType.STRING, advance=False):
2417-                        # Takes care of BigQuery's JavaScript UDF definitions that end in an OPTIONS property
2418-                        # # https://cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language#create_function_statement
2419-                        expression = self._parse_string()
2420-                        extend_props(self._parse_properties())
2421-                    else:
--
5531:                elif not expression:
5532-                    expression = self._parse_factor()
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-160649-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "old_string": "                        expression = (\n                            self._parse_user_defined_function_expression()\n                            if create_token_type == TokenType.FUNCTION\n                            else
…[54 chars elided]…
_string": "                        if create_token_type == TokenType.PROCEDURE:\n                            expression = self._parse_block()\n                        elif create_token.text.upper() == \"MACRO\":\n                            expression = self._parse_macro_body()\n                        else:\n                            expression = self._parse_user_defined_function_expression()"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-160649-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Next, the body helper, and `_parse_macro_overload` switched to use it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-160649-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "old_string": "    def _parse_macro_overload(self) -> exp.MacroOverload:\n        expressions = self._parse_wrapped_csv(self._parse_function_parameter)\n        if not self._match(TokenType.ALIAS):\n            self.raise_error(\"Expec
…[801 chars elided]…
pressions = self._parse_wrapped_csv(self._parse_function_parameter)\n        if not self._match(TokenType.ALIAS):\n            self.raise_error(\"Expecting AS\")\n\n        table = bool(self._match(TokenType.TABLE))\n        expression = self._parse_macro_body()\n        return self.expression(\n            exp.MacroOverload(expressions=expressions, expression=expression, table=table)\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-160649-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "sed -i 's/    arg_types = {\"expressions\": True, \"expression\": True, \"table\": False}/    arg_types = {\"expressions\": False, \"expression\": True, \"table\": False}/' sqlglot/expressions/ddl.py && grep -n \"class MacroOverload\" -A1 sqlglot/expressions/ddl.py && PY=<work>/env-sqlglot/bin/python; printf '%s\\n' \"CREATE OR REPLACE MACRO
…[395 chars elided]…
\" \"CREATE MACRO t(a) AS TABLE SELECT a FROM x ORDER BY a LIMIT 1\" \"CREATE MACRO t(a) AS TABLE SELECT a UNION SELECT b\" \"CREATE MACRO t(a) AS (SELECT a) ORDER BY a\" \"CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)\" | PYTHONPATH=$PWD $PY .lithify/harness/scripts/probe_parse.py --read duckdb; echo \"exit=$?\"", "description": "Apply arg fix and rerun macro probe batch"}
[tool_result] sed: 1: "sqlglot/expressions/ddl ...": unterminated substitute pattern
(eval):1: permission denied: .lithify/harness/scripts/probe_parse.py
exit=126
[assistant] The `sed` failed and the `&&` chain skipped the `PY=` assignment, so the probe tried to run the script directly. I'll make the `arg_types` edit with the Edit tool and rerun the probe.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-160649-duckdb-dialect-overloaded-macro/base-1/sqlglot/expressions/ddl.py", "old_string": "    arg_types = {\"expressions\": True, \"expression\": True, \"table\": False}", "new_string": "    arg_types = {\"expressions\": False, \"expression\": True, \"table\": False}"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-160649-duckdb-dialect-overloaded-macro/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; printf '%s\\n' \"CREATE OR REPLACE MACRO add_2(a, b) AS a + b;\" \"CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c;\" \"CREATE MACRO m() AS 1, (a) AS a;\" \"CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b);\" \"create macro t2(a) as table (select a), (a, b) as table (select a 
…[53 chars elided]…
SELECT a + b);\" \"CREATE OR REPLACE MACRO x(a) AS a + 1, (a, b) AS a + b\" \"CREATE MACRO t(a) AS TABLE SELECT a FROM x ORDER BY a LIMIT 1\" \"CREATE MACRO t(a) AS TABLE SELECT a UNION SELECT b\" \"CREATE MACRO t(a) AS (SELECT a) ORDER BY a\" | PYTHONPATH=$PWD $PY .lithify/harness/scripts/probe_parse.py --read duckdb; echo \"exit=$?\"", "description": "Rerun macro probe batch after parser fixes"}
[tool_result] OK        CREATE OR REPLACE MACRO add_2(a, b) AS a + b;
          CREATE OR REPLACE MACRO add_2(a, b) AS a + b
OK        CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c;
          CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c
OK        CREATE MACRO m() AS 1, (a) AS a;
          CREATE MACRO m () AS 1, (a) AS a
OK        CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b);
          CREATE MACRO t (a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)
OK
…[308 chars elided]…
 CREATE OR REPLACE MACRO x(a) AS a + 1, (a, b) AS a + b
          CREATE OR REPLACE MACRO x (a) AS a + 1, (a, b) AS a + b
OK        CREATE MACRO t(a) AS TABLE SELECT a FROM x ORDER BY a LIMIT 1
          CREATE MACRO t(a) AS TABLE SELECT a FROM x ORDER BY a LIMIT 1
OK        CREATE MACRO t(a) AS TABLE SELECT a UNION SELECT b
          CREATE MACRO t(a) AS TABLE SELECT a UNION SELECT b
OK        CREATE MACRO t(a) AS (SELECT a) ORDER BY a
          CREATE MACRO t(a) AS (SELECT a) ORDER BY a
exit=0
[assistant] All the probed shapes now parse and round-trip. Next I'll add the regression tests to `tests/dialects/test_duckdb.py`, next to the existing `test_udf`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-160649-duckdb-dialect-overloaded-macro/base-1/tests/dialects/test_duckdb.py", "old_string": "    def test_bitwise_agg(self):", "new_string": "    def test_macro_overloads(self):\n        ast = self.validate_identity(\"CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c\")\n        ast.expressi
…[120 chars elided]…
identity(\"CREATE OR REPLACE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c\")\n        self.validate_identity(\"CREATE MACRO no_args () AS 1, (a) AS a\")\n        self.validate_identity(\"CREATE MACRO t (a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)\")\n        self.validate_identity(\"CREATE MACRO s (a) AS (SELECT a), (a, b) AS (SELECT a + b)\")\n\n    def test_bitwise_agg(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-160649-duckdb-dialect-overloaded-macro/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py 2>&1 | tail -25", "description": "Run DuckDB dialect test file"}
[tool_result] ........................ [ 53%]
.....................    [100%]
45 passed, 600 subtests passed in 0.31s
[assistant] The DuckDB dialect tests pass. Next I'll confirm the generated SQL actually executes in DuckDB and that the overloads resolve to the right bodies, including the table macro.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot, duckdb\nc = duckdb.connect()\nstmts = [\n 'CREATE OR REPLACE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c',\n 'CREATE MACRO no_args() AS 1, (a) AS a',\n 'CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)',\n]\nfor s in stmts:\n    out = sqlglot.transpile(s, read='duckdb', write='duckdb')[0]\n    c.execute(out)\n    print('executed:', out)\nprint(c.execute('SELECT add_x(1, 2), add_x(1, 2, 3), no_args(), no_args(5)').fetchall())\nprint(c.execute('SELECT * FROM t(7)').fetchall(), c.execute('SELECT * FROM t(1, 2)').fetchall())\n\" 2>&1 | tail -12", "description": "Execute generated overload SQL in DuckDB and check results"}
[tool_result] executed: CREATE OR REPLACE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c
executed: CREATE MACRO no_args () AS 1, (a) AS a
executed: CREATE MACRO t (a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)
[(3, 6, 1, 5)]
[(7,)] [(3,)]
[assistant] The generated SQL executes in DuckDB, and the overloads resolve correctly (`add_x(1,2)=3`, `add_x(1,2,3)=6`, the table overloads return `a` and `a+b`). Now the full test suite, plus style checks on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; echo \"== ruff\"; $PY -m ruff --version 2>&1 | tail -1; $PY -m ruff check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/ddl.py tests/dialects/test_duckdb.py 2>&1 | tail -5; $PY -m ruff format --check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/ddl.py tests/dialects/test_duckdb.py 2>&1 | tail -5", "description": "Run full test suite and ruff lint and format checks"}
[tool_result] .................................................................................................................................................................................................................................................................................. [ 24%]
.................................... [ 27%]
............................................................................................................................................ [ 40%]
..........................
…[406 chars elided]…
............................................................................................................ [ 85%]
................................................................................................ [ 94%]
....................... [ 96%]
.....................................                     [100%]
1114 passed, 18162 subtests passed in 55.60s
== ruff
ruff 0.15.6
All checks passed!
Would reformat: tests/dialects/test_duckdb.py
1 file would be reformatted, 3 files already formatted
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format tests/dialects/test_duckdb.py && git diff --stat && git diff tests/dialects/test_duckdb.py | head -30; $PY -m mypy --version 2>/dev/null && $PY -m mypy sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/ddl.py 2>&1 | tail -3", "description": "Format test file and check diff plus mypy"}
[tool_result] 1 file reformatted
sqlglot/expressions/ddl.py    |  8 +++++++
 sqlglot/generator.py          | 12 ++++++++++-
 sqlglot/parser.py             | 50 ++++++++++++++++++++++++++++++++++++++-----
 tests/dialects/test_duckdb.py | 14 ++++++++++++
 4 files changed, 78 insertions(+), 6 deletions(-)
tests/dialects/test_duckdb.py | 14 ++++++++++++++
 1 file changed, 14 insertions(+)

--- Changes ---

tests/dialects/test_duckdb.py
  @@ -2608,6 +2608,20 @@ class TestDuckDB(Validator):
  +    def test_macro_ov
…[709 chars elided]…
se_agg(self):
           self.validate_all(
               "SELECT BIT_OR(int_value) FROM t",
  +14 -0
mypy 2.3.0.post2 (compiled: yes)
sqlglot/parser.py:2440: error: Item "None" of "Expr | None" has no attribute "expressions"  [union-attr]
sqlglot/parser.py:2447: error: Item "None" of "Expr | None" has no attribute "this"  [union-attr]
Found 3 errors in 1 file (checked 3 source files)
[This command modified 1 file you've previously read: tests/dialects/test_duckdb.py. Call Read before editing.]
[assistant] Ruff format fixed the test file. mypy reports three errors in my new block, so I'll look at them.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m mypy sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/ddl.py 2>&1 | head -4; sed -n 2434,2452p sqlglot/parser.py; git stash list | head -0; git show HEAD:sqlglot/parser.py > /tmp/parser_head.py; echo; $PY -m mypy sqlglot/parser.py 2>&1 | tail -1", "description": "Show mypy errors and the overload block"}
[tool_result] sqlglot/parser.py:2435: error: Item "None" of "Properties | None" has no attribute "expressions"  [union-attr]
sqlglot/parser.py:2440: error: Item "None" of "Expr | None" has no attribute "expressions"  [union-attr]
sqlglot/parser.py:2447: error: Item "None" of "Expr | None" has no attribute "this"  [union-attr]
Found 3 errors in 1 file (checked 3 source files)
                if returns:
                    properties.expressions.remove(returns)

                overloads = [
                  
…[536 chars elided]…
 # Postgres allows anonymous indexes, eg. CREATE INDEX IF NOT EXISTS ON t(c)
            if not self._match(TokenType.ON):
                index = self._parse_id_var()
head: illegal line count -- 0

thread 'main' (43091511) panicked at /rustc/59807616e1fa2540724bfbac14d7976d7e4a3860/library/std/src/io/stdio.rs:1165:9:
failed printing to stdout: Broken pipe (os error 32)
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace

Found 3 errors in 1 file (checked 1 source file)
[assistant] All three are Optional-narrowing errors: `properties` and `this` can be `None` by type. I'll narrow with an `isinstance` check on the UDF, which also documents what a macro head must be.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-160649-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "old_string": "            if create_token.text.upper() == \"MACRO\" and self._match(TokenType.COMMA):\n                returns = properties.find(exp.ReturnsProperty) if properties else None\n                if returns:\n              
…[57 chars elided]…
g": "            if (\n                isinstance(this, exp.UserDefinedFunction)\n                and create_token.text.upper() == \"MACRO\"\n                and self._match(TokenType.COMMA)\n            ):\n                returns = properties.find(exp.ReturnsProperty) if properties else None\n                if properties and returns:\n                    properties.expressions.remove(returns)"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-160649-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m mypy sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/ddl.py 2>&1 | tail -2; $PY -m ruff check sqlglot tests/dialects/test_duckdb.py 2>&1 | tail -1; $PY -m ruff format --check sqlglot tests/dialects/test_duckdb.py 2>&1 | tail -1; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py 2>&1 | tail -1; git diff sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/ddl.py | head -150", "description": "Recheck mypy, ruff, DuckDB tests and review diff"}
[tool_result] Success: no issues found in 3 source files
All checks passed!
177 files already formatted
45 passed, 600 subtests passed in 0.32s
sqlglot/expressions/ddl.py |  8 +++++++
 sqlglot/generator.py       | 12 ++++++++++-
 sqlglot/parser.py          | 54 +++++++++++++++++++++++++++++++++++++++++-----
 3 files changed, 68 insertions(+), 6 deletions(-)

--- Changes ---

sqlglot/expressions/ddl.py
  @@ -226,6 +226,14 @@ class UserDefinedFunction(Expression):
  +class MacroOverloads(Expression):
  +    arg
…[4175 chars elided]…
   if not self._match(TokenType.ALIAS):
  +            self.raise_error("Expecting AS")
  +
  +        table = bool(self._match(TokenType.TABLE))
  +        expression = self._parse_macro_body()
  +        return self.expression(
  +            exp.MacroOverload(expressions=expressions, expression=expression, table=table)
  +        )
  +
       def _parse_introducer(self, token: Token) -> exp.Introducer | exp.Identifier:
           literal = self._parse_primary()
           if literal:
  +49 -5
[assistant] The diff looks right: the single-macro path is unchanged apart from the body parser, which the full suite already covered. I'll run the full suite once more as the final gate after the last edit, and remove my scratch file in `/tmp`.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; rm -f /tmp/parser_head.py; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; git status --short", "description": "Run final full test suite and check git status"}
[tool_result] .....................................                     [100%]
1114 passed, 18162 subtests passed in 58.35s
 M sqlglot/expressions/ddl.py
 M sqlglot/generator.py
 M sqlglot/parser.py
 M tests/dialects/test_duckdb.py
[assistant] DuckDB overloaded macros now parse and round-trip, for both scalar and table macros. The full suite passes (1114 tests) and ruff and mypy are clean on the changed files. The changes are uncommitted in the worktree.

**Representation.** `CREATE MACRO name (params) AS body, (params) AS body, ...` becomes `Create(this=<name>, kind=MACRO, expression=MacroOverloads(...))`. Each entry is an `exp.MacroOverload` with its params, body and a `table` flag. The single-overload form is unchanged, so existing ASTs and tests don't move.

**Changes:**
- `sqlglot/expressions/ddl.py`: new `MacroOverloads` and `
…[754 chars elided]…
s rejected by DuckDB itself.
- All overloads of one macro must be the same kind. Mixing scalar and table is rejected, so I put the `TABLE` flag per entry but it is always uniform in valid input.

**Verification.** The generated SQL executes in DuckDB. `add_x(1, 2)` returns 3 and `add_x(1, 2, 3)` returns 6. The table overloads select `a` and `a + b` as expected.

**Output shape.** Overloaded macros print a space before the parameter list, e.g. `CREATE MACRO add_x (a, b) AS ...`, while single macros print `add_x(a, b)`. Both are valid DuckDB. I left the spacing alone rather than special-case it.
