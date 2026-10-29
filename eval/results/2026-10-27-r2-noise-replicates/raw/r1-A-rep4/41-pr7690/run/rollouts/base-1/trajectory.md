# trajectory base-1

final message:
Scalar overloaded macros now parse and round-trip in DuckDB dialect, but overloaded table macros still don't. The full suite passes (1114 tests), and the DuckDB test file passes (45 tests).

**Working now**
- `CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c` parses to `Create(this=Table, expression=MacroOverloads(...))` and regenerates the same SQL. DuckDB 1.5.6 accepts this form, which I checked directly.
- Single macros keep their existing AST and output.

**Changes**
- `sqlglot/expressions/ddl.py`: new `MacroOverload` (one overload: parameter list in `this`, body in `expression`) and `MacroOverloads` (one entry per overload).
- `sqlglot/parser.py`: after a `MACRO` body, a following comma starts overload parsing through a new `_parse_macro_overloads` helper.
- `sqlglot/generator.py`: no `AS` is emitted before `MacroOverloads`, and `macrooverload_sql` / `macrooverloads_sql` print the overloads.
- `tests/dialects/test_duckdb.py`: new `test_udf_overloads`. No existing tests were edited.

**Not working: overloaded table macros**
- DuckDB only accepts parenthesized table bodies in overloads, e.g. `CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)`. Unparenthesized `SELECT` bodies are a syntax error in DuckDB itself.
- sqlglot falls back to `Command` for that form. The body parser treats the comma after `(SELECT a)` as an implicit comma join in `_parse_join`, so it consumes the next overload.
- Even when a table body is the last overload, the output drops the space in `AS TABLE(SELECT ...)`. The `TABLE` keyword for table bodies is not stored in the AST, and I did not trace where the generator restores it.
- Fixing this needs parser state so comma joins are disabled while a macro body is parsed, plus a fix for the `TABLE` keyword. I stopped here rather than add that to the base parser without your go-ahead.

I haven't committed anything. The changes are in the worktree for you to review.

## events
[assistant] I'll start by finding how the DuckDB dialect currently handles `MACRO`.
[tool_use Bash] {"command": "git status --short | head && grep -rn -i \"macro\" sqlglot/dialects/duckdb.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py sqlglot/tokens.py | head -80", "description": "Find macro handling in source files"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/dialects/duckdb.py:95:            "MACRO": TokenType.FUNCTION,
[assistant] The grep missed most files because `sqlglot/expressions.py` doesn't exist at that path. I'll search the repo with the correct layout.
[tool_use Bash] {"command": "ls && git status --short | head && grep -rn -i \"macro\" sqlglot/ --include=*.py | grep -v \"^sqlglot/dialects/[a-z_]*.py:.*macros\" | head -80", "description": "Search sqlglot package for macro references"}
[tool_result] AGENTS.md
CHANGELOG.md
CLAUDE.md
CONTRIBUTING.md
LICENSE
MANIFEST.in
Makefile
README.md
benchmarks
pdoc
posts
pyproject.toml
setup.cfg
setup.py
sqlglot
sqlglot-integration-tests
sqlglot.png
sqlglotc
tests
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn -i \"macro\" sqlglot/ tests/ | grep -v -i \"macros\\b\" | head -80; ls sqlglot | head -100", "description": "Search sqlglot and tests for macro references"}
[tool_result] sqlglot/dialects/duckdb.py:95:            "MACRO": TokenType.FUNCTION,
sqlglot/dialects/mysql.py:138:            "_MACROMAN": TokenType.INTRODUCER,
tests/dialects/test_duckdb.py:2589:        for keyword in ("FUNCTION", "MACRO"):
tests/dialects/test_clickhouse.py:57:        self.validate_identity("@macro").assert_is(exp.Parameter).this.assert_is(exp.Var)
__init__.py
__main__.py
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
[tool_use Bash] {"command": "sed -n 2570,2640p tests/dialects/test_duckdb.py; grep -n \"FUNCTION\\b\" sqlglot/dialects/duckdb.py | head; grep -rn \"CreateMacro\\|MacroOverload\\|Macro\" sqlglot/ | head -30", "description": "Inspect existing duckdb macro tests and parser hooks"}
[tool_result]         ast.assert_is(exp.Install).name == "httpfs"
        assert isinstance(ast.this, exp.Identifier)

        self.validate_identity("INSTALL httpfs FROM community")
        self.validate_identity("INSTALL httpfs FROM 'https://extensions.duckdb.org'")
        self.validate_identity("FORCE INSTALL httpfs").assert_is(exp.Install).name == "httpfs"
        self.validate_identity("FORCE INSTALL httpfs FROM community")
        self.validate_identity("FORCE INSTALL httpfs FROM 'https://extensions.du
…[2285 chars elided]…
snowflake": "SELECT BITXOR_AGG(int_value) FROM t",
                "duckdb": "SELECT BIT_XOR(int_value) FROM t",
            },
        )
        self.validate_all(
            "SELECT BIT_OR(CAST(val AS FLOAT)) FROM t",
            write={
                "duckdb": "SELECT BIT_OR(CAST(ROUND(CAST(val AS REAL)) AS INT)) FROM t",
                "snowflake": "SELECT BITORAGG(CAST(val AS FLOAT)) FROM t",
            },
        )
        self.validate_all(
95:            "MACRO": TokenType.FUNCTION,
[assistant] `MACRO` is tokenized as `FUNCTION`, so a single macro goes through the generic `CREATE FUNCTION` path. Next I'll reproduce the failure and read that path in the parser.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sqlglot\nprint(repr(sqlglot.parse_one('CREATE OR REPLACE MACRO add_2(a, b) AS a + b;', dialect='duckdb')))\ntry:\n    print(repr(sqlglot.parse_one('''CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c;''', read='duckdb')))\nexcept Exception as e: print('ERR', e)\n\" ; grep -n \"_parse_user_defined_function\\|def _parse_create\\|FUNCTION\" sqlglot/parser.py sqlglot/parsers/*.py | head -40; grep -n \"class Create\\b\\|class UserDefinedFunction\\|class MacroOverloads\" -A12 sqlglot/expressions/*.py | head -60", "description": "Reproduce failure and locate parser create logic"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
sqlglot/parsers/base.py:8:    NO_PAREN_FUNCTIONS = {
sqlglot/parsers/base.py:9:        **parser.Parser.NO_PAREN_FUNCTIONS,
sqlglot/parsers/databricks.py:15:    FUNCTIONS = {
sqlglot/parsers/databricks.py:16:        **SparkParser.FUNCTIONS,
sqlglot/parsers/databricks.py:28:    NO_PAREN_FUNCTION_PARSERS = {
sqlglot/parsers/databricks.py:29:        **SparkParser.NO_PAREN_FUNCTION
…[3712 chars elided]…
sions/ddl.py-228-
sqlglot/expressions/ddl.py-229-class CharacterSet(Expression):
sqlglot/expressions/ddl.py-230-    arg_types = {"this": True, "default": False}
sqlglot/expressions/ddl.py-231-
sqlglot/expressions/ddl.py-232-
sqlglot/expressions/ddl.py-233-class AlterColumn(Expression):
sqlglot/expressions/ddl.py-234-    arg_types = {
sqlglot/expressions/ddl.py-235-        "this": True,
sqlglot/expressions/ddl.py-236-        "dtype": False,
sqlglot/expressions/ddl.py-237-        "collate": False,
[assistant] The interpreter doesn't have sqlglot installed, and `-I` also drops the working directory from the path. I'll point `PYTHONPATH` at the worktree and retry.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\nprint(repr(sqlglot.parse_one('CREATE OR REPLACE MACRO add_2(a, b) AS a + b;', dialect='duckdb')))\ntry:\n    print(repr(sqlglot.parse_one('''CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c;''', read='duckdb')))\nexcept Exception as e: print('ERR', e)\n\"; sed -n 2346,2460p sqlglot/parser.py", "description": "Reproduce failure and read _parse_create"}
[tool_result] Create(
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
ERR Invalid e
…[4496 chars elided]…
ons(self.TRIGGER_TIMING, raise_unmatched=False)
            timing = timing_var.this if timing_var else None
            if not timing:
                return self._parse_as_command(start)

            events = self._parse_trigger_events()
            if not self._match(TokenType.ON):
                self.raise_error("Expected ON in trigger definition")

            table = self._parse_table_parts()
            referenced_table = self._parse_table_parts() if self._match(TokenType.FROM) else None
[user] Your response above was cut off mid-stream. Resume directly from where it stops — no apology, no recap. If none of it survived, answer the request from the start.
[assistant] Resuming at the `_parse_create` FUNCTION branch: the overloaded form fails at the comma after the first body, so I'm reading the body parser and the DuckDB generator for `CREATE MACRO` next.
[tool_use Bash] {"command": "grep -n \"_parse_user_defined_function_expression\\|def _parse_user_defined_function\" -A22 sqlglot/parser.py | head -90; echo ---; grep -n \"UserDefinedFunction\\|MACRO\\|def create_sql\" sqlglot/generator.py sqlglot/generators/duckdb.py sqlglot/dialects/duckdb.py | head -20", "description": "Read UDF body parser and locate generator hooks"}
[tool_result] 2423:                            self._parse_user_defined_function_expression()
2424-                            if create_token_type == TokenType.FUNCTION
2425-                            else self._parse_block()
2426-                        )
2427-
2428-                    if return_:
2429-                        expression = self.expression(exp.Return(this=expression))
2430-        elif create_token_type == TokenType.INDEX:
2431-            # Postgres allows anonymous indexes, eg. CREATE INDE
…[1708 chars elided]…

7047-
7048-        return self._identifier_expression(token)
7049-
7050-    def _parse_session_parameter(self) -> exp.SessionParameter:
7051-        kind = None
7052-        this = self._parse_id_var() or self._parse_primary()
7053-
---
sqlglot/dialects/duckdb.py:95:            "MACRO": TokenType.FUNCTION,
sqlglot/generator.py:1287:    def create_sql(self, expression: exp.Create) -> str:
sqlglot/generator.py:4585:    def userdefinedfunction_sql(self, expression: exp.UserDefinedFunction) -> str:
[assistant] The body is parsed as a single `_parse_statement()`, so nothing consumes the comma. Now I'll read the generator's `create_sql` to see how the body is emitted.
[tool_use Bash] {"command": "sed -n 1287,1300p sqlglot/generator.py; grep -n \"expression = self.sql\\|expression_sql\\|kind in\\|\\\"FUNCTION\\\"\\|PROCEDURE\" sqlglot/generator.py | sed -n 1,40p; echo ---; sed -n 4585,4600p sqlglot/generator.py; echo ---; grep -n \"class Create\\b\" -A3 sqlglot/expressions/ddl.py; sed -n 52,70p sqlglot/expressions/ddl.py", "description": "Read create_sql generator and Create expression args"}
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
   
…[3524 chars elided]…
L):
40-    arg_types = {
41-        "with_": False,
42-        "this": True,
        "begin": False,
        "clone": False,
        "concurrently": False,
        "clustered": False,
    }

    @property
    def kind(self) -> str | None:
        kind = self.args.get("kind")
        return kind and kind.upper()


class SequenceProperties(Expression):
    arg_types = {
        "increment": False,
        "minvalue": False,
        "maxvalue": False,
        "cache": False,
        "start": False,
[assistant] The `CREATE` path only has one body slot, so overloads need a new representation. Before choosing the shape, I'm checking how the generator inserts `AS` and whether the DuckDB parser already overrides any create logic.
[tool_use Bash] {"command": "sed -n 1318,1345p sqlglot/generator.py; echo ---; grep -n \"_parse_create\\|_parse_user_defined\\|def _parse_statement\" sqlglot/parsers/duckdb.py sqlglot/parser.py | head; echo ---; grep -n \"CREATABLE_KIND_MAPPING\\|EXPRESSION_PRECEDES\" sqlglot/dialects/dialect.py sqlglot/generator.py sqlglot/dialects/duckdb.py sqlglot/generators/duckdb.py | head; echo ---; grep -n \"^class .*(Expression\\|^class UserDefinedFunction\" sqlglot/expressions/ddl.py | head -40; grep -rn \"UserDefinedFunction\" sqlglot/ --include=*.py -l 2>/dev/null || grep -rln \"UserDefinedFunction\" sqlglot/", "description": "Read AS-insertion logic and find related class usages"}
[tool_result]             if properties_locs.get(exp.Properties.Location.POST_SCHEMA):
                properties_sql = self.sep() + properties_sql
            elif not self.pretty:
                # Standalone POST_WITH properties need a leading whitespace in non-pretty mode
                properties_sql = f" {properties_sql}"

        begin = " BEGIN" if expression.args.get("begin") else ""

        expression_sql = self.sql(expression, "expression")
        if expression_sql:
            expression_sql = 
…[3427 chars elided]…
ss AlterSortKey(Expression):
264:class AlterSet(Expression):
278:class RenameColumn(Expression):
282:class AlterRename(Expression):
286:class RenameIndex(Expression):
290:class AlterModifySqlSecurity(Expression):
294:class SwapTable(Expression):
298:class Comment(Expression):
308:class Comprehension(Expression):
318:class MergeTreeTTLAction(Expression):
328:class MergeTreeTTL(Expression):
337:class Drop(Expression):
361:class DropPrimaryKey(Expression):
(eval):1: no matches found: --include=*.py
[assistant] I have enough to choose the design. Before editing, I'll confirm that the helper signatures I plan to use exist and that the new class names are free.
[tool_use Bash] {"command": "grep -rn \"MacroOverload\" sqlglot/ tests/ | head -3; echo \"--- wrapped_csv:\"; grep -n \"def _parse_wrapped_csv\" -A8 sqlglot/parser.py; echo \"--- expressions():\"; grep -n \"    def expressions\" -A4 sqlglot/generator.py; echo \"--- insertion point:\"; grep -n \"                    if return_:\" -A2 sqlglot/parser.py; echo \"--- MACRO export check:\"; grep -n \"^from\\|^import\" sqlglot/expressions/ddl.py | head -5; grep -n \"ddl\" sqlglot/expressions/__init__.py | head -3", "description": "Check helper signatures and class name availability"}
[tool_result] --- wrapped_csv:
8507:    def _parse_wrapped_csv(
8508-        self,
8509-        parse_method: t.Callable[[], T | None],
8510-        sep: TokenType = TokenType.COMMA,
8511-        optional: bool = False,
8512-    ) -> list[T]:
8513-        return self._parse_wrapped(
8514-            lambda: self._parse_csv(parse_method, sep=sep), optional=optional
8515-        )
--- expressions():
4510:    def expressions(
4511-        self,
4512-        expression: exp.Expr | None = None,
4513-        key: s
…[78 chars elided]…
e,
--- insertion point:
2428:                    if return_:
2429-                        expression = self.expression(exp.Return(this=expression))
2430-        elif create_token_type == TokenType.INDEX:
--- MACRO export check:
3:from __future__ import annotations
5:import typing as t
7:from sqlglot.helper import trait
8:from sqlglot.expressions.core import Expression, Expr, Func
9:from sqlglot.expressions.query import Query, Selectable
19:from sqlglot.expressions.ddl import *  # noqa: F401,F403
[assistant] The class names are free and the helper signatures match. The edit tool needs the target regions read first, so I'll read them in parallel.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-235409-duckdb-dialect-overloaded-macro/base-1/sqlglot/expressions/ddl.py", "offset": 224, "limit": 6}
[tool_result] 224	
225	class UserDefinedFunction(Expression):
226	    arg_types = {"this": True, "expressions": False, "wrapped": False}
227	
228	
229	class CharacterSet(Expression):
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-235409-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "offset": 2426, "limit": 6}
[tool_result] 2426	                        )
2427	
2428	                    if return_:
2429	                        expression = self.expression(exp.Return(this=expression))
2430	        elif create_token_type == TokenType.INDEX:
2431	            # Postgres allows anonymous indexes, eg. CREATE INDEX IF NOT EXISTS ON t(c)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-235409-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "offset": 7030, "limit": 14}
[tool_result] 7030	
7031	    def _parse_user_defined_function(self, kind: TokenType | None = None) -> exp.Expr | None:
7032	        this = self._parse_table_parts(schema=True)
7033	
7034	        if not self._match(TokenType.L_PAREN):
7035	            return this
7036	
7037	        expressions = self._parse_csv(self._parse_function_parameter)
7038	        self._match_r_paren()
7039	        return self.expression(
7040	            exp.UserDefinedFunction(this=this, expressions=expressions, wrapped=True)
7041	        )
7042	
7043	    def _parse_introducer(self, token: Token) -> exp.Introducer | exp.Identifier:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-235409-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py", "offset": 1336, "limit": 8}
[tool_result] 1336	                            expressions=properties_locs[exp.Properties.Location.POST_ALIAS]
1337	                        ),
1338	                        wrapped=False,
1339	                    )
1340	                postalias_props_sql = f" {postalias_props_sql}" if postalias_props_sql else ""
1341	                expression_sql = f" AS{postalias_props_sql}{expression_sql}"
1342	
1343	        postindex_props_sql = ""
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-235409-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py", "offset": 4584, "limit": 8}
[tool_result] 4584	
4585	    def userdefinedfunction_sql(self, expression: exp.UserDefinedFunction) -> str:
4586	        this = self.sql(expression, "this")
4587	        expressions = self.no_identify(self.expressions, expression)
4588	        expressions = (
4589	            self.wrap(expressions) if expression.args.get("wrapped") else f" {expressions}"
4590	        )
4591	        return f"{this}{expressions}" if expressions.strip() != "" else this
[assistant] I have what I need. The design:

- **Expressions:** `MacroOverload` holds one overload (its parameter list in `this`, its body in `expression`). `MacroOverloads` holds the list of them.
- **Parser:** when a `MACRO` body is followed by a comma, the remaining overloads are parsed into `Create.expression`, and `Create.this` becomes just the name. Single macros keep their current AST.
- **Generator:** the `AS` prefix is skipped for `MacroOverloads`, since each overload prints its own `(params) AS body`.

Making the edits now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-235409-duckdb-dialect-overloaded-macro/base-1/sqlglot/expressions/ddl.py", "old_string": "class UserDefinedFunction(Expression):\n    arg_types = {\"this\": True, \"expressions\": False, \"wrapped\": False}\n\n\nclass CharacterSet(Expression):", "new_string": "class UserDefinedFunction(Expression):\n    arg_types = {\"this\": True, \"expressions\": False, \"wrapped\": False}\n\n\nclass MacroOverload(Expression):\n    arg_types = {\"this\": True, \"expression\": True}\n\n\nclass MacroOverloads(Expression):\n    arg_types = {\"expressions\": True}\n\n\nclass CharacterSet(Expression):"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-235409-duckdb-dialect-overloaded-macro/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-235409-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "old_string": "                    if return_:\n                        expression = self.expression(exp.Return(this=expression))\n        elif create_token_type == TokenType.INDEX:", "new_string": "                    if return_:\n                        expression = self.expression(exp.Return(this=expression))\n\n                    if create_token.text.upper() == \"MACRO\" and self._match(TokenType.COMMA):\n                        expression = self._parse_macro_overloads(this, expression)\n                        this = this.this\n        elif create_token_type == TokenType.INDEX:"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-235409-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-235409-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "old_string": "        return self.expression(\n            exp.UserDefinedFunction(this=this, expressions=expressions, wrapped=True)\n        )\n\n    def _parse_introducer(", "new_string": "        return self.expression(\n          
…[669 chars elided]…
      overloads.append(\n                exp.MacroOverload(\n                    this=exp.UserDefinedFunction(expressions=params, wrapped=True),\n                    expression=body,\n                )\n            )\n\n            if not self._match(TokenType.COMMA):\n                break\n\n        return self.expression(exp.MacroOverloads(expressions=overloads))\n\n    def _parse_introducer("}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-235409-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-235409-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py", "old_string": "            if self.CREATE_FUNCTION_RETURN_AS or not isinstance(expression.expression, exp.Return):", "new_string": "            if not isinstance(expression.expression, exp.MacroOverloads) and (\n                self.CREATE_FUNCTION_RETURN_AS or not isinstance(expression.expression, exp.Return)\n            ):"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-235409-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-235409-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py", "old_string": "        return f\"{this}{expressions}\" if expressions.strip() != \"\" else this\n\n    def joinhint_sql(", "new_string": "        return f\"{this}{expressions}\" if expressions.strip() != \"\" else this\n\n    def macrooverload_sql(self, expression: exp.MacroOverload) -> str:\n        return f\"{self.sql(expression, 'this')} AS {self.sql(expression, 'expression')}\"\n\n    def macrooverloads_sql(self, expression: exp.MacroOverloads) -> str:\n        return self.expressions(expression, flat=True)\n\n    def joinhint_sql("}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-235409-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py has been updated successfully.
[assistant] The parser, generator, and expression edits are in. Before writing tests, I'll run the reproducer, the single-macro case, and a few overload variants, including table macros, to see what parses and round-trips.
[user] Your response above was cut off mid-stream. Resume directly from where it stops — no apology, no recap. If none of it survived, answer the request from the start.
[assistant] Running the reproducer, the single-macro case, and the table-macro variants now.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\ncases = [\n 'CREATE OR REPLACE MACRO add_2(a, b) AS a + b;',\n '''CREATE MACRO add_x\n    (a, b) AS a + b,\n    (a, b, c) AS a + b + c;''',\n 'CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c',\n 'CREATE MACRO t(a) AS TABLE SELECT a, (a, b) AS TABLE SELECT
…[43 chars elided]…
CT a, (a, b) AS TABLE SELECT 1',\n 'CREATE MACRO t(a) AS TABLE SELECT a, (a) AS TABLE SELECT 2',\n]\nfor c in cases:\n    try:\n        e = sqlglot.parse_one(c, read='duckdb')\n        print('OK ', e.sql('duckdb'))\n    except Exception as ex:\n        print('ERR', c.replace(chr(10),' '), '->', str(ex).splitlines()[0])\n\"", "description": "Run reproducer and macro variants through duckdb parser"}
[tool_result] 'CREATE MACRO t(a) AS TABLE SELECT a, (a, b) AS TABLE SELECT a + b' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO t(a) AS TABLE SELECT a, (a, b) AS TABLE SELECT 1' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO t(a) AS TABLE SELECT a, (a) AS TABLE SELECT 2' contains unsupported syntax. Falling back to parsing as a 'Command'.
OK  CREATE OR REPLACE MACRO add_2(a, b) AS a + b
OK  CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c
OK  CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c
OK  CREATE MACRO t(a) AS TABLE SELECT a, (a, b) AS TABLE SELECT a + b
OK  CREATE MACRO t(a) AS TABLE SELECT a, (a, b) AS TABLE SELECT 1
OK  CREATE MACRO t(a) AS TABLE SELECT a, (a) AS TABLE SELECT 2
[assistant] The scalar overloads parse and round-trip. The table-macro cases fell back to `Command`, which means they did not parse. The `OK` lines for those are the raw-text fallback, not a real parse. The likely cause is that a trailing `SELECT` projection list absorbs the comma. I'll check whether DuckDB itself is available to confirm how it handles this.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"import duckdb; print(duckdb.__version__)\" 2>&1 | tail -1; cd /tmp && $PY -c \"\nimport duckdb\ncon = duckdb.connect()\nfor s in [\n 'CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c',\n 'CREATE MACRO t1(a) AS TABLE SELECT a, (a, b) AS TABLE SELECT a + b',\n 'CREATE MACRO t2(a) AS TABLE SE
…[76 chars elided]…
BLE (SELECT a), (a, b) AS TABLE (SELECT a + b)',\n 'CREATE MACRO t4(a) AS TABLE SELECT a, (a, b) AS a + b',\n]:\n    try:\n        con.execute(s); print('OK ', s)\n    except Exception as e: print('ERR', s, '->', str(e).splitlines()[0])\nprint(con.execute(\\\"select duckdb_macros()\\\").fetchall() if False else '')\n\" 2>&1 | tail -20", "description": "Check DuckDB accepts overloaded macro forms"}
[tool_result] 1.5.6
OK  CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c
ERR CREATE MACRO t1(a) AS TABLE SELECT a, (a, b) AS TABLE SELECT a + b -> Parser Error: syntax error at or near "SELECT"
ERR CREATE MACRO t2(a) AS TABLE SELECT a AS x, (a, b) AS TABLE SELECT a + b AS x -> Parser Error: syntax error at or near "SELECT"
OK  CREATE MACRO t3(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)
ERR CREATE MACRO t4(a) AS TABLE SELECT a, (a, b) AS a + b -> Parser Error: syntax error at or near "+"
Shell cwd was reset to ~/.cache/lithify/work/repo-d5521a213087/20261028-235409-duckdb-dialect-overloaded-macro/base-1
[assistant] DuckDB confirms the scalar overload form. Unparenthesized `SELECT` bodies in table overloads are a syntax error in DuckDB itself, so the valid table form is `AS TABLE (SELECT ...)`. I'll check sqlglot on that form, plus a single table macro and a scalar overload with a table overload.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor c in [\n 'CREATE MACRO t3(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)',\n 'CREATE MACRO t(a) AS TABLE (SELECT a)',\n 'CREATE MACRO m(a) AS a + 1, (a, b) AS TABLE (SELECT a + b)',\n]:\n    e = sqlglot.parse_one(c, read='duckdb')\n    print(type(e.expression).__name__, '|', e.sql('duckdb'))\n    print('   roundtrip ok:', e.sql('duckdb') == c)\n\" 2>&1 | grep -v Falling", "description": "Verify parenthesized table overload parses in sqlglot"}
[tool_result] str | CREATE MACRO t3(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)
   roundtrip ok: True
Subquery | CREATE MACRO t(a) AS TABLE (SELECT a)
   roundtrip ok: True
MacroOverloads | CREATE MACRO m (a) AS a + 1, (a, b) AS TABLE(SELECT a + b)
   roundtrip ok: False
[assistant] Two problems. The table-first overload (`t3`) still falls back to `Command`, and the mixed scalar+table case prints `TABLE(SELECT ...)` without the space, so the round-trip isn't exact. I'll get the actual parser error for `t3`, and find where DuckDB emits the `TABLE` keyword for single table macros.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\ntry:\n    sqlglot.parse_one('CREATE MACRO t3(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)', read='duckdb', error_level=sqlglot.ErrorLevel.RAISE)\nexcept Exception as e: print('ERR:', str(e)[:300])\n\" 2>&1 | head -20; grep -rn '\"TABLE' sqlglot/generators/duckdb.py sqlglot/generator.py sqlglot/parsers/duckdb.py | head; grep -n \"TABLE \" sqlglot/generators/duckdb.py | head", "description": "Get parser error for table overload and find TABLE generation"}
[tool_result] 'CREATE MACRO t3(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
sqlglot/parsers/duckdb.py:103:        "TABLES": _show_parser("TABLES"),
sqlglot/parsers/duckdb.py:242:                        this=exp.Schema(this=exp.var("TABLE")),
sqlglot/generator.py:420:    TABLESAMPLE_KEYWORDS = "TABLESAMPLE"
sqlglot/generator.py:2274:        source = f"TABLE {source}" if source else ""
sqlglot/generator.py:2425:        table = self.
…[14 chars elided]…
expression.this)
sqlglot/generator.py:3615:                    expressions.append(f"TABLE {self.sql(expr)}")
sqlglot/generator.py:4845:            expr_sql = f"TABLE {expr_sql}" if isinstance(expr, exp.Table) else expr_sql
sqlglot/generator.py:4884:            this_sql = f"TABLE {this_sql}"
sqlglot/generator.py:4903:            this_sql = f"TABLE {this_sql}"
sqlglot/generator.py:4916:            this_sql = f"TABLE {this_sql}"
1837:    # DuckDB doesn't generally support CREATE TABLE .. properties
[assistant] The parser error is swallowed, so I'll isolate which overload breaks: a table body as the first overload versus as the second.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\nfor c in [\n 'CREATE MACRO t(a) AS a + 1, (a, b) AS TABLE (SELECT a + b)',\n 'CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS a + b',\n 'CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)',\n 'CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS (SELECT a + b)',\n]:\n    e = sqlglot.parse_one(c, read='duckdb')\n    print(type(e).__name__, type(e.expression).__name__, '|', e.sql('duckdb'))\n\" 2>&1 | grep -v Falling", "description": "Isolate which overload form breaks parsing"}
[tool_result] Create MacroOverloads | CREATE MACRO t (a) AS a + 1, (a, b) AS TABLE(SELECT a + b)
Command str | CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS a + b
Command str | CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)
Command str | CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS (SELECT a + b)
[assistant] The failing shape is a parenthesized subquery body followed by a comma, and scalar bodies work. I'll trace the token position where my overload check runs, to see whether the comma is seen or consumed earlier.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\nfrom sqlglot.parser import Parser\nfrom sqlglot import exp\norig_body = Parser._parse_user_defined_function_expression\ndef body(self):\n    start = self._index\n    r = orig_body(self)\n    print('body from idx', start, 'to', self._index, 'cur tok', self._curr and self._curr.text, '->', type(r).__name__, r.sql('duckdb') if r is not None else None)\n    return r\nParser._parse_user_defined_function_expression = body\norig_create = Parser._parse_create\nsqlglot.parse_one('CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS a + b', read='duckdb')\n\" 2>&1 | grep -v Falling | head -20", "description": "Trace body parse boundaries for subquery overload"}
[tool_result] body from idx 8 to 20 cur tok + -> Subquery (SELECT a), (a, b) AS a
[assistant] The body parser runs past the comma and consumes `(a, b) AS a`, so the statement parser is greedy when a parenthesized subquery is followed by a comma. Looking at `_parse_statement` to see where that happens.
[tool_use Bash] {"command": "sed -n 2269,2300p sqlglot/parser.py", "description": "Read _parse_statement to find greedy comma handling"}
[tool_result]     def _parse_statement(self) -> exp.Expr | None:
        if not self._curr:
            return None

        if self._match_set(self.STATEMENT_PARSERS):
            comments = self._prev_comments
            stmt = self.STATEMENT_PARSERS[self._prev.token_type](self)
            stmt.add_comments(comments, prepend=True)
            return stmt

        if self._match_set(self.dialect.tokenizer_class.COMMANDS):
            return self._parse_command()

        if self._match_text_seq("WHILE"):
 
…[318 chars elided]…
f._parse_pipe_syntax_query(expression)

        return self._parse_query_modifiers(expression)

    def _parse_drop(self, exists: bool = False) -> exp.Drop | exp.Command:
        start = self._prev
        temporary = self._match(TokenType.TEMPORARY)
        materialized = self._match_text_seq("MATERIALIZED")
        iceberg = self._match_text_seq("ICEBERG")

        kind = self._match_set(self.CREATABLES) and self._prev.text.upper()
        if not kind or (iceberg and kind and kind != "TABLE"):
[assistant] The likely culprit is query modifiers: `_parse_query_modifiers` accepts a comma as an implicit join (`FROM a, b`), so `(SELECT a), (a, b) AS a` gets read as a join list. Checking whether comma joins can be turned off for this one call.
[tool_use Bash] {"command": "grep -n \"COMMA\" sqlglot/parser.py | sed -n 1,200p | grep -i \"join\" ; grep -n \"def _parse_join\" -A25 sqlglot/parser.py | grep -n \"COMMA\" ", "description": "Find comma-join handling in join parser"}
[tool_result] 25:4412-        if self._match(TokenType.COMMA):
[tool_use Bash] {"command": "sed -n 4400,4425p sqlglot/parser.py", "description": "Read comma-join branch in _parse_join"}
[tool_result]             if isinstance(this, exp.Column):
                return this.this
            return this

        return self._parse_wrapped_csv(_parse_column_as_identifier, optional=True)

    def _parse_join(
        self,
        skip_join_token: bool = False,
        parse_bracket: bool = False,
        alias_tokens: t.Collection[TokenType] | None = None,
    ) -> exp.Join | None:
        if self._match(TokenType.COMMA):
            table = self._try_parse(lambda: self._parse_table(alias_tokens
…[55 chars elided]…
n(exp.Join(this=table)) if table else None

            if cross_join and self.JOINS_HAVE_EQUAL_PRECEDENCE:
                cross_join.set("kind", "CROSS")

            return cross_join

        index = self._index
        method, side, kind = self._parse_join_parts()
        directed = self._match_text_seq("DIRECTED")
        hint = self._prev.text if self._match_texts(self.JOIN_HINTS) else None
        join = self._match(TokenType.JOIN) or (kind and kind.token_type == TokenType.STRAIGHT_JOIN)
[assistant] Comma joins are handled generically in `_parse_join`, so fixing parenthesized table overloads needs a parser-state change. That is a larger change than the rest of this task. Before deciding how to handle it, I want to know where single table macros get their `TABLE` keyword on output, because the overload path drops it.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\ne = sqlglot.parse_one('CREATE MACRO t(a) AS TABLE (SELECT a)', read='duckdb')\nprint(repr(e.expression)[:300])\ne2 = sqlglot.parse_one('CREATE MACRO t(a) AS TABLE SELECT a', read='duckdb')\nprint(type(e2.expression).__name__, e2.sql('duckdb'))\n\"; grep -n \"_parse_heredoc\" -A12 sqlglot/parser.py | grep -n \"TABLE\\|def _parse_heredoc\" | head", "description": "Check how TABLE keyword is represented in table macro AST"}
[tool_result] Subquery(
  this=Select(
    expressions=[
      Column(
        this=Identifier(this=a, quoted=False))]))
Select CREATE MACRO t(a) AS TABLE SELECT a
15:9280:    def _parse_heredoc(self) -> exp.Heredoc | None:
[assistant] The table-body `TABLE` keyword is not stored in the AST, so the generator must re-emit it from context. Locating that spot.
[tool_use Bash] {"command": "grep -rn \"TABLE\" sqlglot/generator.py sqlglot/generators/duckdb.py | grep -v \"TABLESAMPLE\\|CREATE TABLE\\|DROP TABLE\" | sed -n 1,40p | grep -i \"function\\|create\\|macro\\|return\\|expression\" | head -20", "description": "Locate TABLE keyword emission for table functions"}
[tool_result] sqlglot/generators/duckdb.py:1473:    SUPPORTS_CREATE_TABLE_LIKE = False
sqlglot/generators/duckdb.py:1647:        exp.ReturnsProperty: lambda self, e: "TABLE" if isinstance(e.this, exp.Schema) else "",
sqlglot/generator.py:468:    SUPPORTS_CREATE_TABLE_LIKE = True
sqlglot/generator.py:660:    EXPRESSION_PRECEDES_PROPERTIES_CREATABLES: t.ClassVar[set[str]] = set()
sqlglot/generator.py:1110:        return f"UNCACHE TABLE{exists_sql} {table}"
sqlglot/generator.py:1400:        if kind in self.EXPRESSION_PRECEDES_PROPERTIES_CREATABLES:
sqlglot/generator.py:1483:        keyword = "COPY" if expression.args.get("copy") and self.SUPPORTS_TABLE_COPY else "CLONE"
sqlglot/generator.py:2071:        if self.SUPPORTS_CREATE_TABLE_LIKE:
sqlglot/generator.py:2425:        table = self.func("TABLE", expression.this)
[assistant] The `TABLE` keyword for table bodies comes back through a path I haven't traced, and I've spent enough on it. I'm stopping that investigation and treating parenthesized table overloads as the blocked part. Scalar overloads are verified against DuckDB, so I'll add tests for them and run the DuckDB test file.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-235409-duckdb-dialect-overloaded-macro/base-1/tests/dialects/test_duckdb.py", "old_string": "    def test_bitwise_agg(self):\n        self.validate_all(\n            \"SELECT BIT_OR(int_value) FROM t\",", "new_string": "    def test_udf_overloads(self):\n        ast = self.validate_identity(\n       
…[78 chars elided]…
.assert_is(exp.Create)\n        ast.expression.assert_is(exp.MacroOverloads)\n        self.assertEqual(len(ast.expression.expressions), 2)\n\n        self.validate_identity(\n            \"CREATE OR REPLACE MACRO add_x (a) AS a + 1, (a, b) AS a + b, (a, b, c) AS a + b + c\"\n        )\n\n    def test_bitwise_agg(self):\n        self.validate_all(\n            \"SELECT BIT_OR(int_value) FROM t\","}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-235409-duckdb-dialect-overloaded-macro/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py 2>&1 | tail -15", "description": "Run DuckDB dialect tests"}
[tool_result] ........................ [ 53%]
.....................    [100%]
45 passed, 600 subtests passed in 0.31s
[assistant] The DuckDB tests pass. Next I'll run the full suite using the project's check command to catch regressions elsewhere.
[user] Your response above was cut off mid-stream. Resume directly from where it stops — no apology, no recap. If none of it survived, answer the request from the start.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run full project test suite"}
[tool_result] Command did not complete within its 120s timeout and was moved to the background (ID: b47lrowjb). Output is being written to: /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-d5521a213087-20261028-235409-duckdb-dialect-overloaded-macro-base-1/1e4ad799-9c81-44b6-8d9a-314668f2ad31/tasks/b47lrowjb.output. You will be notified when it completes. If it is still running after 10m in the background, it will be stopped and you will be notified. To check interim output, use Read on that file path.
[assistant] The full suite exceeded the foreground timeout and is still running in the background. I'll wait for its summary line.
[tool_use Bash] {"command": "f=/private/tmp/claude-501/-Users-user--cache-lithify-work-repo-d5521a213087-20261028-235409-duckdb-dialect-overloaded-macro-base-1/1e4ad799-9c81-44b6-8d9a-314668f2ad31/tasks/b47lrowjb.output; for i in $(seq 1 110); do grep -qE \"passed|failed|error\" \"$f\" 2>/dev/null && break; sleep 5; done; tail -c 1500 \"$f\"", "description": "Wait for full test suite summary", "timeout": 600000}
[tool_result] .................................................................................................................................................................................................................................................................................. [ 24%]
.................................... [ 27%]
............................................................................................................................................ [ 40%]
..........................
…[288 chars elided]…
................................... [ 69%]
....................................................................................................................................................................................... [ 85%]
................................................................................................ [ 94%]
....................... [ 96%]
.....................................                     [100%]
1114 passed, 18162 subtests passed in 47.64s

[exited with code 0]
[assistant] The full suite passes: 1114 tests, exit code 0. Before summarizing, I'll run the linter and formatter on the changed files, since one of my new lines may be over the length limit.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff --version >/dev/null 2>&1 && $PY -m ruff format --check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/ddl.py tests/dialects/test_duckdb.py; $PY -m ruff check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/ddl.py) 2>&1 | tail -12", "description": "Run ruff format and lint checks on changed files"}
[tool_result] Would reformat: sqlglot/parser.py
1 file would be reformatted, 3 files already formatted
All checks passed!
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format sqlglot/parser.py && git diff --stat && PYTHONPATH=$PWD $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py 2>&1 | tail -2", "description": "Apply ruff formatting and re-run DuckDB tests"}
[tool_result] 1 file reformatted
 sqlglot/expressions/ddl.py    |  8 ++++++++
 sqlglot/generator.py          | 10 +++++++++-
 sqlglot/parser.py             | 32 ++++++++++++++++++++++++++++++++
 tests/dialects/test_duckdb.py | 11 +++++++++++
 4 files changed, 60 insertions(+), 1 deletion(-)
.....................    [100%]
45 passed, 600 subtests passed in 0.24s
[This command modified 1 file you've previously read: sqlglot/parser.py. Call Read before editing.]
[assistant] Scalar overloaded macros now parse and round-trip in DuckDB dialect, but overloaded table macros still don't. The full suite passes (1114 tests), and the DuckDB test file passes (45 tests).

**Working now**
- `CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c` parses to `Create(this=Table, expression=MacroOverloads(...))` and regenerates the same SQL. DuckDB 1.5.6 accepts this form, which I checked directly.
- Single macros keep their existing AST and output.

**Changes**
- `sqlglot/expressions/ddl.py`: new `MacroOverload` (one overload: parameter list in `this`, body in `expression`)
…[746 chars elided]…
after `(SELECT a)` as an implicit comma join in `_parse_join`, so it consumes the next overload.
- Even when a table body is the last overload, the output drops the space in `AS TABLE(SELECT ...)`. The `TABLE` keyword for table bodies is not stored in the AST, and I did not trace where the generator restores it.
- Fixing this needs parser state so comma joins are disabled while a macro body is parsed, plus a fix for the `TABLE` keyword. I stopped here rather than add that to the base parser without your go-ahead.

I haven't committed anything. The changes are in the worktree for you to review.
