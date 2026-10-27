# trajectory base-1

final message:
DuckDB's overloaded `MACRO` definitions now parse and round-trip. The full suite passed after my last edit: `SUMMARY: 1114 passed, 18162 subtests passed in 53.77s`, `EXIT: 0`.

**Representation.** A multi-overload macro gives `Create(this=MacroOverloads(this=<name>, expressions=[MacroOverload…]))`. Each `MacroOverload` holds its parameter list (`expressions`), its body (`expression`), and a `table` flag for `AS TABLE`. Single-overload macros keep their existing shape, so existing output is unchanged.

**Changes**
- `sqlglot/expressions/ddl.py`: new `MacroOverloads` and `MacroOverload` classes.
- `sqlglot/parsers/duckdb.py`: `_parse_create` override. It only acts when a comma follows the first overload, moves that overload into the node, and parses the rest. I also changed DuckDB's macro/function body parse to try the expression parser before the statement parser. Without that, a subquery body such as `AS (SELECT 1), (a, b) AS …` was misread and fell back to `Command`. This applies to all DuckDB `CREATE MACRO`/`CREATE FUNCTION` bodies, not only overloads.
- `sqlglot/generator.py`: the printing for the new nodes lives in the base generator, next to `userdefinedfunction_sql`. I first put it in the DuckDB generator, but then transpiling to Postgres, Spark or Snowflake raised `Unsupported expression type MacroOverloads`. In the base generator, those targets print the same text DuckDB does, as they already do for single macros.
- `tests/dialects/test_duckdb.py`: new `test_macro_overloads`, covering the task's example, `OR REPLACE`, `IF NOT EXISTS`, the `FUNCTION` keyword, zero-argument overloads, table and scalar overloads mixed, and a check of the `table` flag per overload.

**Caveats**
- Output for non-DuckDB targets is DuckDB syntax, so it is not valid in those engines. That matches single-macro behaviour today. Mapping overloads onto Postgres function signatures would be a separate change.
- A table-macro body that is a bare `SELECT` list followed by `, (…) AS …` is ambiguous: the comma is read as part of the select list. Wrap such bodies in parentheses, e.g. `AS TABLE (SELECT b)`. I left this as DuckDB's grammar has it.

Ruff and mypy are clean on the changed files. The changes are not committed.

## events
[assistant] I'll start by reading the DDL skill that matches this task, then find the existing macro handling.
[tool_use Bash] {"command": "cat .lithify/harness/skills/sqlglot-ddl-statements/SKILL.md; echo ----; grep -rn -i \"macro\" sqlglot/ --include=*.py | head -80", "description": "Read DDL skill and grep macro references"}
[tool_result] ---
name: sqlglot-ddl-statements
description: Load when a task adds or changes parsing/generation of a DDL statement in sqlglot (CREATE / ALTER / DROP of a TABLE, VIEW, TYPE, SEQUENCE, FUNCTION, INDEX, TRIGGER, …), or when a statement "contains unsupported syntax. Falling back to parsing as a Command" and must become a real AST node (exp.Create, exp.Alter, …) in any dialect.
---

# DDL statements (exp.Create and friends) in sqlglot

## Who owns what (verified in the source)
- `Parser._parse_crea
…[4049 chars elided]…
ad from output after your last edit
- For every form the task names, `repr()` of the parsed `exp.Create` shows `this` = the name
  (`Table`, no Schema unless the columns precede `AS`) and `expression` = the body node.
- Each form round-trips in the dialect, and transpiling to one other dialect still prints
  `AS <body>`, not the body glued onto the name.
- Unsupported variants still parse as `exp.Command`, and existing CREATE TABLE/VIEW tests pass.
----
(eval):1: no matches found: --include=*.py
[tool_use Grep] {"pattern": "[Mm]acro", "path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-102257-duckdb-dialect-overloaded-macro/base-1/sqlglot", "output_mode": "content", "-n": "true"}
[tool_result ERROR] <tool_use_error>Error: No such tool available: Grep. Grep is not available in this session — search file contents with `grep` via the Bash tool instead.</tool_use_error>
[tool_use Bash] {"command": "cat .lithify/harness/memory.md 2>/dev/null; ls .lithify/harness/; git log --oneline -1", "description": "Check harness memory and repo state"}
[tool_result] - The project's checks run with `<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no`.
- Layout: expression classes live in `sqlglot/expressions/*.py` (there is no `expressions.py`). A dialect's parser is `sqlglot/parsers/<d>.py` and its generator is `sqlglot/generators/<d>.py`; `sqlglot/dialects/<d>.py` only wires them together.
- The full suite (~1100 tests) takes 60–80 s alone; `tests/test_executor.py::TestExecutor::test_execute_tpcds`
  is slowest and looks hung under CPU contention. Run the dialect's own test file first (<1 s).
guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
b41fc50ed lithify: probe base
[tool_use Bash] {"command": "grep -rn -i \"macro\" sqlglot/ | grep -v \"\\.pyc\"; echo ----; grep -rn -i \"macro\" tests/dialects/test_duckdb.py | head -30; echo ----; ls <work>/env-sqlglot/bin/python && echo PY_OK", "description": "Search sqlglot and tests for macro references"}
[tool_result] sqlglot/dialects/duckdb.py:95:            "MACRO": TokenType.FUNCTION,
sqlglot/dialects/mysql.py:138:            "_MACROMAN": TokenType.INTRODUCER,
----
tests/dialects/test_duckdb.py:2589:        for keyword in ("FUNCTION", "MACRO"):
----
<work>/env-sqlglot/bin/python
PY_OK
[tool_use Bash] {"command": "sed -n 2570,2640p tests/dialects/test_duckdb.py; echo ----; grep -n \"FUNCTION\\|_parse_create\\|CREATABLE\\|def \\|class \" sqlglot/parsers/duckdb.py | head -80", "description": "Read existing macro tests and duckdb parser"}
[tool_result]         ast.assert_is(exp.Install).name == "httpfs"
        assert isinstance(ast.this, exp.Identifier)

        self.validate_identity("INSTALL httpfs FROM community")
        self.validate_identity("INSTALL httpfs FROM 'https://extensions.duckdb.org'")
        self.validate_identity("FORCE INSTALL httpfs").assert_is(exp.Install).name == "httpfs"
        self.validate_identity("FORCE INSTALL httpfs FROM community")
        self.validate_identity("FORCE INSTALL httpfs FROM 'https://extensions.du
…[4386 chars elided]…
e) -> exp.Expr | None:
343:    def _pivot_column_names(self, aggregations: list[exp.Expr]) -> list[str]:
348:    def _parse_attach_detach(self, is_attach: bool = True) -> exp.Attach | exp.Detach:
349:        def _parse_attach_option() -> exp.AttachOption:
372:    def _parse_show_duckdb(self, this: str) -> exp.Show:
376:    def _parse_force(self) -> exp.Install | exp.Command:
384:    def _parse_install(self, force: bool = False) -> exp.Install:
393:    def _parse_primary(self) -> exp.Expr | None:
[assistant] Existing `MACRO` support rides on the `FUNCTION` token. Next I'll reproduce the failure and read the base `_parse_create` path.
[tool_use Bash] {"command": "cat > /tmp/probe_macro.py <<'EOF'\nimport sqlglot\nfor s in [\"CREATE OR REPLACE MACRO add_2(a, b) AS a + b\", \"\"\"\nCREATE MACRO add_x\n    (a, b) AS a + b,\n    (a, b, c) AS a + b + c\"\"\"]:\n    try:\n        e = sqlglot.parse_one(s, read=\"duckdb\")\n        print(type(e).__name__, repr(e)[:300])\n        print(e.sql(\"duckdb\"))\n    except Exception as ex:\n        print(\"ER
…[87 chars elided]…
oding-delvera-foundational-lithify/f0ecd001-19e9-4b3c-8461-34bf1f0fcf2a/scratchpad/hwork/env-sqlglot/bin/python /tmp/probe_macro.py; echo; grep -n \"def _parse_create\\|FUNCTION\\b\\|_parse_user_defined_function\\|def _parse_ddl_select\\|def _parse_user_defined\\|CREATABLES = \\|DB_CREATABLES\" sqlglot/parser.py | head -40", "description": "Reproduce macro parse failure and locate create parsing"}
[tool_result] Create Create(
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
CREATE OR REPLACE MACRO add_2(a, b) AS a + b
ERR ParseError Invalid expression / Unexpected token. Line 3, Col: 20.
  
CREATE MACRO add_x
    (a, b) AS a + b[4m,[0m
    (a, b, c) AS a + b + 
…[989 chars elided]…
pected FUNCTION or PROCEDURE after EXECUTE")
3296:    def _parse_create_like(self) -> exp.LikeProperty | None:
3450:            is_function = self._match(TokenType.FUNCTION)
6164:    def _parse_user_defined_type(self, identifier: exp.Identifier) -> exp.Expr | None:
7025:    def _parse_user_defined_function_expression(self) -> exp.Expr | None:
7031:    def _parse_user_defined_function(self, kind: TokenType | None = None) -> exp.Expr | None:
8539:    def _parse_ddl_select(self) -> exp.Expr | None:
[tool_use Bash] {"command": "sed -n 2346,2460p sqlglot/parser.py; echo ----; sed -n 7025,7060p sqlglot/parser.py", "description": "Read base _parse_create function branch"}
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
…[5298 chars elided]…
.text, expression=literal), token)

        return self._identifier_expression(token)

    def _parse_session_parameter(self) -> exp.SessionParameter:
        kind = None
        this = self._parse_id_var() or self._parse_primary()

        if this and self._match(TokenType.DOT):
            kind = this.name
            this = self._parse_var() or self._parse_primary()

        return self.expression(exp.SessionParameter(this=this, kind=kind))

    def _parse_lambda_arg(self) -> exp.Expr | None:
[assistant] The base parser stops after the first overload, so the trailing `, (a, b, c) AS ...` becomes a parse error. Next I'll check how DuckDB handles the `AS TABLE` body, how `UserDefinedFunction` is generated, and whether the repo already hints at an overload node.
[tool_use Bash] {"command": "grep -rn \"MacroOverload\\|Overload\" sqlglot tests posts 2>/dev/null | head; echo ----; grep -n \"TABLE\" sqlglot/parsers/duckdb.py | head; echo ----; grep -n \"userdefinedfunction\\|UserDefinedFunction\\|def create_sql\" -A12 sqlglot/generators/duckdb.py sqlglot/generator.py | head -120; echo ----; grep -n \"class UserDefinedFunction\" -A8 sqlglot/expressions/*.py; grep -n \"class Create(\" -A25 sqlglot/expressions/ddl.py", "description": "Look for overload hints and UDF/Create generation code"}
[tool_result] ----
103:        "TABLES": _show_parser("TABLES"),
104:        "ALL TABLES": _show_parser("ALL TABLES"),
238:        if self._match(TokenType.TABLE):
242:                        this=exp.Schema(this=exp.var("TABLE")),
290:            alias = self._parse_table_alias(alias_tokens=alias_tokens or self.TABLE_ALIAS_TOKENS)
----
sqlglot/generator.py:1287:    def create_sql(self, expression: exp.Create) -> str:
sqlglot/generator.py-1288-        kind = self.sql(expression, "kind")
sqlglot/generator.py-1
…[2311 chars elided]…
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
56-    }
57-
58-    @property
59-    def kind(self) -> str | None:
60-        kind = self.args.get("kind")
61-        return kind and kind.upper()
62-
63-
64-class SequenceProperties(Expression):
[assistant] Next I'll dump the AST for the existing single-overload forms, including the table-macro body, so I can match its shape.
[tool_use Bash] {"command": "cat > /tmp/probe2.py <<'EOF'\nimport sqlglot\nfor s in [\"CREATE MACRO m(a, b) AS TABLE SELECT a, b\", \"CREATE MACRO add(a, b) AS a + b\", \"CREATE MACRO f() AS 1\"]:\n    e = sqlglot.parse_one(s, read=\"duckdb\")\n    print(repr(e)); print(e.sql(\"duckdb\")); print()\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe2.py 2>&1 | head -120", "description": "Probe AST shape of single-overload macros"}
[tool_result] Create(
  this=UserDefinedFunction(
    this=Table(
      this=Identifier(this=m, quoted=False)),
    expressions=[
      Identifier(this=a, quoted=False),
      Identifier(this=b, quoted=False)],
    wrapped=True),
  kind=MACRO,
  replace=False,
  refresh=False,
  unique=False,
  expression=Select(
    expressions=[
      Column(
        this=Identifier(this=a, quoted=False)),
      Column(
        this=Identifier(this=b, quoted=False))]),
  exists=False,
  properties=Properties(
    expression
…[508 chars elided]…
  this=Identifier(this=a, quoted=False)),
    expression=Column(
      this=Identifier(this=b, quoted=False))),
  exists=False,
  begin=False,
  concurrently=False)
CREATE MACRO add(a, b) AS a + b

Create(
  this=UserDefinedFunction(
    this=Table(
      this=Identifier(this=f, quoted=False)),
    wrapped=True),
  kind=MACRO,
  replace=False,
  refresh=False,
  unique=False,
  expression=Literal(this=1, is_string=False),
  exists=False,
  begin=False,
  concurrently=False)
CREATE MACRO f() AS 1
[assistant] The table form stores `AS TABLE` as a `ReturnsProperty(is_table=True)` in `properties`. Next I'll read how that's parsed and generated, plus the `_match` signature.
[tool_use Bash] {"command": "grep -n \"def _parse_function_properties\" -A22 sqlglot/parser.py; echo ----; grep -n \"def _match(\\|def _match_pair\\|def _parse_wrapped_csv\\|def _parse_csv\" -A3 sqlglot/parser.py; echo ----; grep -n \"is_table\" sqlglot/generator.py sqlglot/generators/duckdb.py sqlglot/parser.py sqlglot/parsers/duckdb.py sqlglot/expressions/*.py | head -20; echo ----; sed -n 230,250p sqlglot/parsers/duckdb.py; grep -n \"def create_sql\" -A60 sqlglot/generators/duckdb.py | head -5", "description": "Read function properties parsing and is_table handling"}
[tool_result] 7022:    def _parse_function_properties(self) -> exp.Properties | None:
7023-        return self._parse_properties()
7024-
7025-    def _parse_user_defined_function_expression(self) -> exp.Expr | None:
7026-        return self._parse_statement()
7027-
7028-    def _parse_function_parameter(self) -> exp.Expr | None:
7029-        return self._parse_column_def(this=self._parse_id_var(), computed_column=False)
7030-
7031-    def _parse_user_defined_function(self, kind: TokenType | None = None) -> ex
…[2034 chars elided]…
on_properties(self) -> exp.Properties | None:
        if self._match(TokenType.TABLE):
            return exp.Properties(
                expressions=[
                    exp.ReturnsProperty(
                        this=exp.Schema(this=exp.var("TABLE")),
                        is_table=True,
                    ),
                ]
            )
        return super()._parse_function_properties()

    def _parse_lambda(self, alias: bool = False) -> exp.Expr | None:
        index = self._index
[assistant] DuckDB already handles `AS TABLE` in `_parse_function_properties`, so the overload loop can reuse it. Before writing code I'll check the generator helpers, how `create_sql` prints `this`, and how the expression modules are exported.
[tool_use Bash] {"command": "sed -n 1287,1340p sqlglot/generator.py; echo ----; grep -n \"    def expressions\" -A12 sqlglot/generator.py | head -20; echo ----; grep -n \"import\" sqlglot/expressions/__init__.py | head; echo ----; grep -n \"^from\\|^import\" sqlglot/generators/duckdb.py sqlglot/parsers/duckdb.py; echo ----; grep -n \"def _parse_as_command\" sqlglot/parser.py; grep -n \"    def wrap\" -A3 sqlglot/generator.py", "description": "Read create_sql and generator helper signatures"}
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
   
…[3954 chars elided]…
ect import (
sqlglot/generators/duckdb.py:40:from sqlglot.generator import unsupported_args
sqlglot/generators/duckdb.py:41:from sqlglot.helper import is_date_unit, seq_get
sqlglot/generators/duckdb.py:42:from builtins import type as Type
----
9188:    def _parse_as_command(self, start: Token) -> exp.Command:
1027:    def wrap(self, expression: exp.Expr | str) -> str:
1028-        this_sql = (
1029-            self.sql(expression)
1030-            if isinstance(expression, exp.UNWRAPPED_QUERIES)
[assistant] I have what I need. The plan:

- **AST** (`expressions/ddl.py`): `MacroOverloads(this=<name>, expressions=[MacroOverload…])`, where each `MacroOverload` holds its parameter list, body and a `table` flag.
- **Parser** (`parsers/duckdb.py`): after the base parses the first overload, if a comma follows, move that overload into the node and parse the rest.
- **Generator** (`generators/duckdb.py`): print each overload as `(params) AS [TABLE] body`.

I'll start with the expression classes.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-102257-duckdb-dialect-overloaded-macro/base-1/sqlglot/expressions/ddl.py", "old_string": "class UserDefinedFunction(Expression):\n    arg_types = {\"this\": True, \"expressions\": False, \"wrapped\": False}\n\n\n", "new_string": "class UserDefinedFunction(Expression):\n    arg_types = {\"this\": True, \"expressions\": False, \"wrapped\": False}\n\n\nclass MacroOverloads(Expression):\n    arg_types = {\"this\": True, \"expressions\": True}\n\n\nclass MacroOverload(Expression):\n    arg_types = {\"expressions\": False, \"expression\": True, \"table\": False}\n\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-102257-duckdb-dialect-overloaded-macro/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[assistant] Next, the parser. I'm adding a `_parse_create` override to `DuckDBParser` that only acts when the base parse of a function/macro is followed by a comma, and a helper for each extra overload.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-102257-duckdb-dialect-overloaded-macro/base-1/sqlglot/parsers/duckdb.py", "old_string": "        return super()._parse_function_properties()\n\n    def _parse_lambda(", "new_string": "        return super()._parse_function_properties()\n\n    def _parse_create(self) -> exp.Create | exp.Command:\n    
…[1123 chars elided]…
_wrapped_csv(self._parse_function_parameter)\n        if not self._match(TokenType.ALIAS):\n            self.raise_error(\"Expected AS after macro parameters\")\n\n        table = self._match(TokenType.TABLE)\n        body = self._parse_user_defined_function_expression()\n        return self.expression(exp.MacroOverload(expressions=params, expression=body, table=table))\n\n    def _parse_lambda("}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-102257-duckdb-dialect-overloaded-macro/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[assistant] Next I'll route the `MacroOverloads` construction through `self.expression` for consistency, then add the generator methods.
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\np=\"sqlglot/parsers/duckdb.py\"\ns=open(p).read()\nold='        create.set(\"this\", exp.MacroOverloads(this=create.this.this, expressions=overloads))\\n'\nnew='        create.set(\\n            \"this\", self.expression(exp.MacroOverloads(this=create.this.this, expressions=overloads))\\n        )\\n'\nassert s.count(old)==1\nopen(p,\"w\").write(s.replace(old,new))\nEOF\ngrep -n \"    def \\(userdefined\\|create\\|cast\\|tablesample\\)\" sqlglot/generators/duckdb.py | head; grep -n \"^    def \" sqlglot/generators/duckdb.py | head -5", "description": "Wrap MacroOverloads construction and find generator anchor"}
[tool_result] 2976:    def tablesample_sql(
334:    def _duckdb_date_delta_sql(self: DuckDBGenerator, expression: DATETIME_DELTA) -> str:
704:    def replace_seq(node: exp.Expr) -> exp.Expr:
2184:    def _array_bag_sql(self, condition: exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:
2190:    def timeslice_sql(self, expression: exp.TimeSlice) -> str:
2226:    def bitmapbucketnumber_sql(self, expression: exp.BitmapBucketNumber) -> str:
[assistant] The `parsers/duckdb.py` notice is from my own scripted edit a moment ago, so that's expected. Next I'll add the generator methods just before `tablesample_sql`.
[tool_use Bash] {"command": "python3 - <<'EOF'\np=\"sqlglot/generators/duckdb.py\"\ns=open(p).read()\nanchor=\"    def tablesample_sql(\\n\"\nassert s.count(anchor)==1\nnew='''    def macrooverloads_sql(self, expression: exp.MacroOverloads) -> str:\n        this = self.sql(expression, \"this\")\n        return f\"{this} {self.expressions(expression, flat=True)}\"\n\n    def macrooverload_sql(self, expression: exp
…[155 chars elided]…
else \"\"\n        return f\"{params} AS{table} {self.sql(expression, 'expression')}\"\n\n'''\nopen(p,\"w\").write(s.replace(anchor,new+anchor))\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_macro.py", "description": "Add DuckDB generator methods and rerun probe"}
[tool_result] Create Create(
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
CREATE OR REPLACE MACRO add_2(a, b) AS a + b
Create Create(
  this=MacroOverloads(
    this=Table(
      this=Identifier(this=add_x, quoted=False)),
    expressions=[
      MacroOverload(
        expressions=[
          Identifier(this=a, quoted=False),
          Identifier(this=b, quoted=False)],
        expression=Add(
          this=Column(
      
CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c
[assistant] The probe case now round-trips. Next I'll check the harder forms: table overloads, mixed scalar and table, `FUNCTION` keyword, three overloads, zero-arg, and `OR REPLACE`.
[tool_use Bash] {"command": "cat > /tmp/probe3.py <<'EOF'\nimport sqlglot\nfrom sqlglot import exp\ncases = [\n \"CREATE MACRO m(a, b) AS TABLE SELECT a, b, (a, b, c) AS TABLE SELECT 1\",\n \"CREATE MACRO m(a) AS TABLE SELECT a, (a, b) AS TABLE SELECT b\",\n \"CREATE OR REPLACE FUNCTION m(a) AS a + 1, (a, b) AS a + b, () AS 0\",\n \"CREATE MACRO m(a) AS a, (b) AS TABLE SELECT b, (c) AS c * 2\",\n \"CREATE MACRO m
…[495 chars elided]…
se_one(out, read=\"duckdb\").sql(\"duckdb\") == out)\n    except Exception as ex:\n        print(\"ERR\", s, \"->\", type(ex).__name__, ex)\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe3.py", "description": "Probe overload variants for round-trip and entry shape"}
[tool_result] 'CREATE MACRO m(a, b) AS TABLE SELECT a, b, (a, b, c) AS TABLE SELECT 1' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO m(a, b) AS TABLE SELECT a, b, (a, b, c) AS TABLE SELECT 1' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO m(a) AS TABLE SELECT a, (a, b) AS TABLE SELECT b' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO m(a) AS TABLE SELECT a, (a, b) AS TABLE SELECT b' contains unsupporte
…[756 chars elided]…
e)] props: None expr: None
  roundtrip: True
ERR CREATE MACRO m(a) AS a, (b) AS TABLE SELECT b, (c) AS c * 2 -> ParseError Invalid expression / Unexpected token. Line 1, Col: 57.
  CREATE MACRO m(a) AS a, (b) AS TABLE SELECT b, (c) AS c [4m*[0m 2
CREATE MACRO m () AS 1, (x) AS x
  entries: [(0, False), (1, False)] props: None expr: None
  roundtrip: True
CREATE MACRO m(a) AS (SELECT 1), (a, b) AS a + b
  entries: [] props: None expr:  MACRO m(a) AS (SELECT 1), (a, b) AS a + b
  roundtrip: True
[assistant] Two of the failures come from my test inputs, not the parser: a comma inside a `SELECT` projection is ambiguous with the overload separator, so those inputs aren't valid DuckDB. The real findings are:

1. My generator prints a space after the name (`m (a)`), but DuckDB's canonical form is `m(a)`. That needs fixing.
2. `AS (SELECT 1), (a, b) AS a + b` falls back to `Command`, which needs investigating.
[tool_use Bash] {"command": "python3 - <<'EOF'\np=\"sqlglot/generators/duckdb.py\"\ns=open(p).read()\nold='        return f\"{this} {self.expressions(expression, flat=True)}\"\\n'\nassert s.count(old)==1\ns=s.replace(old,'        return f\"{this}{self.expressions(expression, flat=True)}\"\\n')\nopen(p,\"w\").write(s)\nEOF\ncat > /tmp/probe4.py <<'EOF'\nimport sqlglot\nfor s in [\"CREATE MACRO m(a) AS (SELECT 1), 
…[248 chars elided]…
= sqlglot.parse_one(s, read=\"duckdb\"); print(e.sql(\"duckdb\"))\n    except Exception as ex: print(\"ERR\", type(ex).__name__, str(ex)[:200])\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe4.py", "description": "Fix overload spacing and probe subquery body cases"}
[tool_result] 'CREATE MACRO m(a) AS (SELECT 1), (a, b) AS a + b' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO m(a) AS TABLE (SELECT 1), (b) AS TABLE (SELECT b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
CREATE MACRO m(a) AS (SELECT 1), (a, b) AS a + b
CREATE MACRO m(a) AS (a), (a, b) AS a + b
CREATE MACRO m(a) AS a + 1, (b) AS TABLE SELECT b
CREATE MACRO m(a) AS (SELECT 1)
CREATE MACRO m(a) AS TABLE (SELECT 1), (b) AS TABLE (SELECT b)
[assistant] Subquery bodies like `(SELECT 1)` fall back to `Command` while `(a)` parses. I'll trace where the fallback gets triggered.
[tool_use Bash] {"command": "cat > /tmp/probe5.py <<'EOF'\nimport sqlglot, traceback\nfrom sqlglot.parsers.duckdb import DuckDBParser\norig = DuckDBParser._parse_as_command\ndef spy(self, start):\n    traceback.print_stack(limit=8)\n    return orig(self, start)\nDuckDBParser._parse_as_command = spy\nsqlglot.parse_one(\"CREATE MACRO m(a) AS (SELECT 1), (a, b) AS a + b\", read=\"duckdb\")\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe5.py 2>&1 | head -40", "description": "Trace which parse step falls back to Command"}
[tool_result]   File "~/.cache/lithify/work/repo-55c905b0df68/20261027-102257-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", line 2036, in parse
    return self._parse(
  File "~/.cache/lithify/work/repo-55c905b0df68/20261027-102257-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", line 2156, in _parse
    return self._parse_batch_statements(parse_method=parse_method, sep_first_statement=False)
  File "~/.cache/lithify/work/repo-55c905b0df68/20261027
…[701 chars elided]…
o/base-1/sqlglot/parsers/duckdb.py", line 250, in _parse_create
    create = super()._parse_create()
  File "~/.cache/lithify/work/repo-55c905b0df68/20261027-102257-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", line 2581, in _parse_create
    return self._parse_as_command(start)
  File "/tmp/probe5.py", line 5, in spy
    traceback.print_stack(limit=8)
'CREATE MACRO m(a) AS (SELECT 1), (a, b) AS a + b' contains unsupported syntax. Falling back to parsing as a 'Command'.
[tool_use Bash] {"command": "sed -n 2560,2585p sqlglot/parser.py", "description": "Read base _parse_create tail that falls back"}
[tool_result]                     extend_props(self._parse_properties())
                    if not index:
                        break
                    else:
                        self._match(TokenType.COMMA)
                        indexes.append(index)
            elif create_token_type == TokenType.VIEW:
                if self._match_text_seq("WITH", "NO", "SCHEMA", "BINDING"):
                    no_schema_binding = True
            elif create_token_type in (TokenType.SINK, TokenType.SOURCE):
   
…[133 chars elided]…
h_texts(self.CLONE_KEYWORDS):
                copy = self._prev.text.lower() == "copy"
                clone = self.expression(
                    exp.Clone(this=self._parse_table(schema=True), shallow=shallow, copy=copy)
                )

        if self._curr and not self._match_set((TokenType.R_PAREN, TokenType.COMMA), advance=False):
            return self._parse_as_command(start)

        create_kind_text = create_token.text.upper()
        return self.expression(
            exp.Create(
[assistant] The base `_parse_create` falls back when the token after the body isn't a comma or `)`. So the body parse is consuming more than it should. I'll check what `_parse_statement` returns for a parenthesized subquery followed by a comma.
[tool_use Bash] {"command": "cat > /tmp/probe6.py <<'EOF'\nimport sqlglot\nfrom sqlglot.dialects.duckdb import DuckDB\np = DuckDB().parser()\nfor sql in [\"(SELECT 1), (a, b) AS a + b\", \"(SELECT 1), 2\", \"(a), (a, b) AS a + b\"]:\n    toks = DuckDB().tokenize(sql)\n    p.reset(); p.sql = sql; p._tokens = toks; p._index = -1; p._advance()\n    try:\n        r = p._parse_statement()\n        print(repr(sql), \"-
…[2 chars elided]…
", type(r).__name__, r.sql(\"duckdb\"), \"| curr:\", p._curr and p._curr.text)\n    except Exception as ex: print(\"ERR\", ex)\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe6.py 2>&1 | tail -8", "description": "Probe _parse_statement on subquery followed by comma"}
[tool_result] ERR 'NoneType' object has no attribute 'sql'
ERR 'NoneType' object has no attribute 'sql'
ERR 'NoneType' object has no attribute 'sql'
[assistant] My harness was wrong (it skipped the parser's setup). I'll instead spy on the body parse inside the real `CREATE` path.
[tool_use Bash] {"command": "cat > /tmp/probe7.py <<'EOF'\nimport sqlglot\nfrom sqlglot.parsers.duckdb import DuckDBParser\norig = DuckDBParser._parse_user_defined_function_expression\ndef spy(self):\n    r = orig(self)\n    print(\"BODY:\", r.sql(\"duckdb\") if r else None, type(r).__name__, \"| next:\", self._curr and self._curr.text)\n    return r\nDuckDBParser._parse_user_defined_function_expression = spy\nfo
…[44 chars elided]…
a, b) AS a + b\", \"CREATE MACRO m(a) AS (a), (a, b) AS a + b\"]:\n    print(sqlglot.parse_one(s, read=\"duckdb\").sql(\"duckdb\"))\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe7.py 2>&1 | tail -12", "description": "Spy on macro body parse to see consumed tokens"}
[tool_result] 'CREATE MACRO m(a) AS (SELECT 1), (a, b) AS a + b' contains unsupported syntax. Falling back to parsing as a 'Command'.
BODY: (SELECT 1), (a, b) AS a Subquery | next: +
CREATE MACRO m(a) AS (SELECT 1), (a, b) AS a + b
BODY: (a) Paren | next: ,
BODY: a + b Add | next: <Token token_type: TokenType.SENTINEL, text: SENTINEL, line: 1, col: 1, start: 0, end: 0, comments: []>
CREATE MACRO m(a) AS (a), (a, b) AS a + b
[assistant] The body parse is the problem: `_parse_statement` reads `(SELECT 1), (a, b) AS a` as one subquery with an alias. Scalar macro bodies are expressions, so I'll have DuckDB parse them with `_parse_expression` and fall back to `_parse_statement` for `SELECT`/`TABLE` bodies. I'll check that `_parse_expression` returns `None` cleanly on `SELECT`.
[tool_use Bash] {"command": "python3 - <<'EOF'\np=\"sqlglot/parsers/duckdb.py\"\ns=open(p).read()\nold=\"    def _parse_macro_overload(self) -> exp.MacroOverload:\\n\"\nnew='''    def _parse_user_defined_function_expression(self) -> exp.Expr | None:\n        return self._parse_expression() or self._parse_statement()\n\n    def _parse_macro_overload(self) -> exp.MacroOverload:\n'''\nassert s.count(old)==1\nopen(p,
…[116 chars elided]…
al-lithify/f0ecd001-19e9-4b3c-8461-34bf1f0fcf2a/scratchpad/hwork/env-sqlglot/bin/python /tmp/probe4.py; PYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_macro.py | grep -v \"^ \\|^Create\\|^  \" ", "description": "Route macro bodies through expression parser and re-probe"}
[tool_result] CREATE MACRO m(a) AS (SELECT 1), (a, b) AS a + b
CREATE MACRO m(a) AS (a), (a, b) AS a + b
CREATE MACRO m(a) AS a + 1, (b) AS TABLE SELECT b
CREATE MACRO m(a) AS (SELECT 1)
CREATE MACRO m(a) AS TABLE (SELECT 1), (b) AS TABLE (SELECT b)
CREATE OR REPLACE MACRO add_2(a, b) AS a + b
CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c
[assistant] Subquery bodies now parse, and the mixed scalar/table case round-trips. Next I'll re-run the variant matrix with valid inputs, checking each entry's `table` flag and that the first overload's `TABLE` moved off `properties`.
[tool_use Bash] {"command": "cat > /tmp/probe8.py <<'EOF'\nimport sqlglot\nfrom sqlglot import exp\ncases = [\n \"CREATE MACRO m(a) AS TABLE (SELECT a), (b) AS (SELECT b)\",\n \"CREATE MACRO m(a) AS (SELECT a), (b) AS TABLE (SELECT b)\",\n \"CREATE OR REPLACE FUNCTION m(a) AS a + 1, (a, b) AS a + b, () AS 0\",\n \"CREATE MACRO m() AS 1, (x) AS x\",\n \"CREATE MACRO m(a) AS a + 1, (b) AS TABLE SELECT b\",\n \"CREA
…[474 chars elided]…
lglot.parse_one(out, read=\"duckdb\").sql(\"duckdb\") == out)\n    except Exception as ex:\n        print(\"ERR\", s, \"->\", type(ex).__name__, ex)\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe8.py", "description": "Probe valid overload variants and entry flags"}
[tool_result] CREATE MACRO m(a) AS TABLE (SELECT a), (b) AS (SELECT b)
  entries: [(1, True), (1, False)] props:  expr: None kind: MACRO
  roundtrip: True
CREATE MACRO m(a) AS (SELECT a), (b) AS TABLE (SELECT b)
  entries: [(1, False), (1, True)] props: None expr: None kind: MACRO
  roundtrip: True
CREATE OR REPLACE FUNCTION m(a) AS a + 1, (a, b) AS a + b, () AS 0
  entries: [(1, False), (2, False), (0, False)] props: None expr: None kind: FUNCTION
  roundtrip: True
CREATE MACRO m() AS 1, (x) AS x
  entries: [(0, False), (1, False)] props: None expr: None kind: MACRO
  roundtrip: True
CREATE MACRO m(a) AS a + 1, (b) AS TABLE SELECT b
  entries: [(1, False), (1, True)] props: None expr: None kind: MACRO
  roundtrip: True
CREATE MACRO IF NOT EXISTS m(a) AS a, (b) AS b
  entries: [(1, False), (1, False)] props: None expr: None kind: MACRO
  roundtrip: True
[assistant] Every variant round-trips, and the `table` flags land on the right entries. One leftover: after moving `TABLE` off the first overload, an empty `Properties` node stays on the `Create`. I'll drop it when it's empty.
[tool_use Bash] {"command": "python3 - <<'EOF'\np=\"sqlglot/parsers/duckdb.py\"\ns=open(p).read()\nold='''        properties = create.args.get(\"properties\")\n        returns = properties.find(exp.ReturnsProperty) if properties else None\n        is_table = bool(returns)\n        if returns:\n            returns.pop()\n'''\nnew='''        properties = create.args.get(\"properties\")\n        returns = properties
…[163 chars elided]…
.expressions:\n                create.set(\"properties\", None)\n'''\nassert s.count(old)==1\nopen(p,\"w\").write(s.replace(old,new))\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe8.py 2>&1 | head -4", "description": "Drop empty Properties after moving TABLE flag"}
[tool_result] CREATE MACRO m(a) AS TABLE (SELECT a), (b) AS (SELECT b)
  entries: [(1, True), (1, False)] props: None expr: None kind: MACRO
  roundtrip: True
CREATE MACRO m(a) AS (SELECT a), (b) AS TABLE (SELECT b)
[assistant] The AST shape is right now. Next I'll add DuckDB tests next to the existing `test_udf`. First I'll check the test file's imports and helper API.
[tool_use Bash] {"command": "sed -n 1,12p tests/dialects/test_duckdb.py; grep -n \"def validate_identity\" -A12 tests/dialects/test_dialect.py | head -30", "description": "Check duckdb test imports and validate_identity helper"}
[tool_result] from unittest import mock

from sqlglot import ParseError, UnsupportedError, exp, parse_one
from sqlglot.generator import logger as generator_logger
from sqlglot.helper import logger as helper_logger
from sqlglot.optimizer.annotate_types import annotate_types
from tests.dialects.test_dialect import Validator


class TestDuckDB(Validator):
    dialect = "duckdb"

53:    def validate_identity(
54-        self, sql, write_sql=None, pretty=False, check_command_warning=False, identify=False
55-    ):
56-        if check_command_warning:
57-            with self.assertLogs(parser_logger) as cm:
58-                expression = self.parse_one(sql)
59-                assert f"'{sql[:100]}' contains unsupported syntax" in cm.output[0]
60-        else:
61-            expression = self.parse_one(sql)
62-
63-        self.assertEqual(
64-            write_sql or sql, expression.sql(dialect=self.dialect, pretty=pretty, identify=identify)
65-        )
[tool_use Bash] {"command": "python3 - <<'EOF'\np=\"tests/dialects/test_duckdb.py\"\ns=open(p).read()\nanchor=\"    def test_bitwise_agg(self):\\n\"\nassert s.count(anchor)==1\nnew='''    def test_macro_overloads(self):\n        ast = self.validate_identity(\n            \"CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c\"\n        ).assert_is(exp.Create)\n        self.assertIsInstance(ast.this, exp.Macr
…[1202 chars elided]…
   )\n\n'''\ns=s.replace(anchor,new+anchor)\nopen(p,\"w\").write(s)\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py 2>&1 | tail -30", "description": "Add overload tests and run DuckDB dialect test file"}
[tool_result] ........................ [ 53%]
.....................    [100%]
45 passed, 600 subtests passed in 0.33s
[assistant] All 45 DuckDB tests pass. Next I'll confirm the new test actually ran, and run the lint/format tools the project uses on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; $PY/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py -k \"macro or udf\" -v 2>&1 | tail -5; ls $PY | grep -i \"ruff\\|mypy\"; grep -n \"^style\" -A6 Makefile", "description": "Confirm new test runs and find lint tools"}
[tool_result] collected 45 items / 43 deselected / 2 selected

tests/dialects/test_duckdb.py ..                                         [100%]

======================= 2 passed, 43 deselected in 0.07s =======================
dmypy
mypy
mypyc
ruff
96:style:
97-	pre-commit run --all-files
98-	@if [ -f sqlglot-integration-tests/Makefile ]; then \
99-		MYPYPATH=$(abspath .) $(MAKE) -C sqlglot-integration-tests style && \
100-		$(MAKE) -C sqlglot-integration-tests check-submodule; \
101-	fi
102-
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; F=\"sqlglot/expressions/ddl.py sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py tests/dialects/test_duckdb.py\"; $PY/ruff format $F && $PY/ruff check $F; git diff --stat; $PY/mypy sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py sqlglot/expressions/ddl.py 2>&1 | tail -15", "description": "Format, lint, and type-check changed files"}
[tool_result] error: Failed to format sqlglot/expressions/ddl.py sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py tests/dialects/test_duckdb.py: No such file or directory (os error 2)
 sqlglot/expressions/ddl.py    |  8 ++++++++
 sqlglot/generators/duckdb.py  |  9 +++++++++
 sqlglot/parsers/duckdb.py     | 47 +++++++++++++++++++++++++++++++++++++++++++
 tests/dialects/test_duckdb.py | 33 ++++++++++++++++++++++++++++++
 4 files changed, 97 insertions(+)
sqlglot/parsers/duckdb.py:263: error: Item "None" of "Any | None" has no attribute "expressions"  [union-attr]
Found 1 error in 1 file (checked 3 source files)
[assistant] Two things to fix. The `ruff` binary in the env is failing to start (likely a stale shebang), so I'll try it via `python -m ruff`. Mypy flags a real `Optional` narrowing issue in my parser code, so I'll fix that first.
[tool_use Bash] {"command": "python3 - <<'EOF'\np=\"sqlglot/parsers/duckdb.py\"\ns=open(p).read()\nold='''        is_table = bool(returns)\n        if returns:\n            returns.pop()\n'''\nnew='''        is_table = returns is not None\n        if properties and returns:\n            returns.pop()\n'''\nassert s.count(old)==1\nopen(p,\"w\").write(s.replace(old,new))\nEOF\nPY=/private/tmp/claude-501/-Users-dono
…[78 chars elided]…
cratchpad/hwork/env-sqlglot/bin; F=\"sqlglot/expressions/ddl.py sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py tests/dialects/test_duckdb.py\"; $PY/python -m ruff format $F; $PY/python -m ruff check $F; $PY/mypy sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py sqlglot/expressions/ddl.py 2>&1 | tail -3; git diff --stat", "description": "Fix optional narrowing, then run ruff and mypy"}
[tool_result] error: Failed to format sqlglot/expressions/ddl.py sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py tests/dialects/test_duckdb.py: No such file or directory (os error 2)
E902 No such file or directory (os error 2)
--> sqlglot/expressions/ddl.py sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py tests/dialects/test_duckdb.py:1:1

Found 1 error.
Success: no issues found in 3 source files
 sqlglot/expressions/ddl.py    |  8 ++++++++
 sqlglot/generators/duckdb.py  |  9 +++++++++
 sqlglot/parsers/duckdb.py     | 47 +++++++++++++++++++++++++++++++++++++++++++
 tests/dialects/test_duckdb.py | 33 ++++++++++++++++++++++++++++++
 4 files changed, 97 insertions(+)
[This command modified 1 file you've previously read: sqlglot/parsers/duckdb.py. Call Read before editing.]
[assistant] Mypy passes. The `ruff` failure is from my shell: zsh doesn't word-split `$F`, so I'll list the files literally. I'll also re-read the parser region to confirm its current content.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; $PY/python -m ruff format sqlglot/expressions/ddl.py sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py tests/dialects/test_duckdb.py; $PY/python -m ruff check sqlglot/expressions/ddl.py sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py tests/dialects/test_duckdb.py; git diff", "description": "Run ruff format and check, then review full diff"}
[tool_result] 1 file reformatted, 3 files left unchanged
All checks passed!
diff --git a/sqlglot/expressions/ddl.py b/sqlglot/expressions/ddl.py
index 829c917ac..d9321dd20 100644
--- a/sqlglot/expressions/ddl.py
+++ b/sqlglot/expressions/ddl.py
@@ -226,6 +226,14 @@ class UserDefinedFunction(Expression):
     arg_types = {"this": True, "expressions": False, "wrapped": False}
 
 
+class MacroOverloads(Expression):
+    arg_types = {"this": True, "expressions": True}
+
+
+class MacroOverload(Expression):
+    ar
…[4679 chars elided]…
)")
+
+        ast = self.validate_identity(
+            "CREATE MACRO m(a) AS (SELECT a), (b) AS TABLE (SELECT b)"
+        ).assert_is(exp.Create)
+        self.assertEqual(
+            [overload.args.get("table") for overload in ast.this.expressions], [False, True]
+        )
+
     def test_bitwise_agg(self):
         self.validate_all(
             "SELECT BIT_OR(int_value) FROM t",
[This command modified 1 file you've previously read: sqlglot/parsers/duckdb.py. Call Read before editing.]
[assistant] The diff reads cleanly. Before running the full suite I'll check what happens when an overloaded macro is transpiled to another dialect, since the harness requires target-valid output.
[tool_use Bash] {"command": "cat > /tmp/probe9.py <<'EOF'\nimport sqlglot\ns = \"CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c\"\nfor d in [\"postgres\", \"duckdb\", \"spark\", \"snowflake\"]:\n    try: print(d, \"->\", sqlglot.transpile(s, read=\"duckdb\", write=d))\n    except Exception as ex: print(d, \"ERR\", type(ex).__name__, str(ex)[:150])\nEOF\nPYTHONPATH=. /private/tmp/claude-501/-Users-donov
…[147 chars elided]…
| head -2 >/dev/null; PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint('single postgres ->', sqlglot.transpile('CREATE MACRO add(a, b) AS a + b', read='duckdb', write='postgres'))\"", "description": "Check transpile output of overloads to other dialects"}
[tool_result] postgres ERR ValueError Unsupported expression type MacroOverloads
duckdb -> ['CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c']
spark ERR ValueError Unsupported expression type MacroOverloads
snowflake ERR ValueError Unsupported expression type MacroOverloads
single postgres -> ['CREATE MACRO add(a, b) AS a + b']
[assistant] Overloads crash on every non-DuckDB target with `Unsupported expression type`, while a single macro transpiles (to the same DuckDB syntax). That inconsistency is a bug. I'll move the two generator methods into the base `Generator` beside `userdefinedfunction_sql`, so every target prints the same as DuckDB does for single macros.
[tool_use Bash] {"command": "python3 - <<'EOF'\nd=\"sqlglot/generators/duckdb.py\"\ns=open(d).read()\nblock='''    def macrooverloads_sql(self, expression: exp.MacroOverloads) -> str:\n        this = self.sql(expression, \"this\")\n        return f\"{this}{self.expressions(expression, flat=True)}\"\n\n    def macrooverload_sql(self, expression: exp.MacroOverload) -> str:\n        params = self.wrap(self.expressio
…[715 chars elided]…
ff check sqlglot/generator.py sqlglot/generators/duckdb.py; PYTHONPATH=. $PY/python /tmp/probe9.py; $PY/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py 2>&1 | tail -2; $PY/mypy sqlglot/generator.py sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py sqlglot/expressions/ddl.py 2>&1 | tail -1", "description": "Move macro generator to base Generator and re-verify"}
[tool_result] All checks passed!
postgres -> ['CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c']
duckdb -> ['CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c']
spark -> ['CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c']
snowflake -> ['CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c']
.....................    [100%]
45 passed, 600 subtests passed in 0.28s
Success: no issues found in 4 source files
[assistant] Overloads now transpile on every target and match the single-macro behaviour. DuckDB tests, ruff, and mypy are clean. Next is the full suite, run in the foreground as the harness requires.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py", "description": "Run full test suite in foreground", "timeout": 600000}
[tool_result] WARNING: 1 other pytest process(es) running; expect slower runs:
  34207 03-14:55:15 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-2ad45fcb40.log
ELAPSED: 54s
SUMMARY: 1114 passed, 18162 subtests passed in 53.77s
EXIT: 0
[assistant] DuckDB's overloaded `MACRO` definitions now parse and round-trip. The full suite passed after my last edit: `SUMMARY: 1114 passed, 18162 subtests passed in 53.77s`, `EXIT: 0`.

**Representation.** A multi-overload macro gives `Create(this=MacroOverloads(this=<name>, expressions=[MacroOverload…]))`. Each `MacroOverload` holds its parameter list (`expressions`), its body (`expression`), and a `table` flag for `AS TABLE`. Single-overload macros keep their existing shape, so existing output is unchanged.

**Changes**
- `sqlglot/expressions/ddl.py`: new `MacroOverloads` and `MacroOverload` classes.
…[1034 chars elided]…
 overloads mixed, and a check of the `table` flag per overload.

**Caveats**
- Output for non-DuckDB targets is DuckDB syntax, so it is not valid in those engines. That matches single-macro behaviour today. Mapping overloads onto Postgres function signatures would be a separate change.
- A table-macro body that is a bare `SELECT` list followed by `, (…) AS …` is ambiguous: the comma is read as part of the select list. Wrap such bodies in parentheses, e.g. `AS TABLE (SELECT b)`. I left this as DuckDB's grammar has it.

Ruff and mypy are clean on the changed files. The changes are not committed.
